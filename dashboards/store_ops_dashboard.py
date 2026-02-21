"""
Harris Farm Hub — Store Operations Intelligence Dashboard
Real item-level POS transactions (383M rows, FY24-FY26 via DuckDB/parquet).
Store-level KPIs, trading patterns, category mix, anomaly detection.
Enhanced: product hierarchy filters, period comparison, like-for-like stores.
Data source: Microsoft Fabric retail fact_pos_sales.
"""

from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

from transaction_layer import TransactionStore, STORE_NAMES
from transaction_queries import run_query
from product_hierarchy import get_departments, get_major_groups, get_minor_groups
from fiscal_calendar import get_current_fiscal_period

# Shared components
from shared.hierarchy_filter import (
    render_hierarchy_filter, render_searchable_hierarchy_filter,
    hierarchy_filter_summary,
)
from shared.hourly_charts import render_hourly_analysis
from shared.time_filter import (
    render_time_filter, time_filter_summary,
    render_quick_period, resolve_quick_period,
)
from shared.styles import render_header, render_footer
from shared.ask_question import render_ask_question
from shared.voice_realtime import render_voice_data_box
from shared.fiscal_selector import render_fiscal_selector

user = st.session_state.get("auth_user")
render_header(
    "Store Operations Intelligence",
    "**Item-level POS transaction analysis** | 383M transactions across 34 stores (FY24-FY26)",
    goals=["G2", "G4"],
    strategy_context="Operational efficiency at store level — reducing waste and improving on-shelf availability.",
)


# ============================================================================
# DATA ACCESS
# ============================================================================

@st.cache_resource
def get_store():
    """Initialise TransactionStore (cached across reruns)."""
    return TransactionStore()


@st.cache_data(ttl=300)
def query_named(name, **kwargs):
    ts = get_store()
    return run_query(ts, name, **kwargs)


@st.cache_data(ttl=300)
def query_summary_kpis(store_id, start, end, dept_code=None,
                       major_code=None, minor_code=None,
                       hfm_item_code=None, product_number=None,
                       day_of_week_names=None, hour_start=None,
                       hour_end=None, season_names=None,
                       quarter_nos=None, month_nos=None):
    """KPI summary — uses hierarchy-filtered query when filters active."""
    ts = get_store()
    has_time_filter = (day_of_week_names or hour_start is not None
                       or season_names or quarter_nos or month_nos)
    if dept_code or has_time_filter:
        return run_query(ts, "filtered_kpis",
                         start=start, end=end,
                         store_id=store_id,
                         dept_code=dept_code,
                         major_code=major_code,
                         minor_code=minor_code,
                         hfm_item_code=hfm_item_code,
                         product_number=product_number,
                         day_of_week_names=day_of_week_names,
                         hour_start=hour_start,
                         hour_end=hour_end,
                         season_names=season_names,
                         quarter_nos=quarter_nos,
                         month_nos=month_nos)
    sql = """
        SELECT COUNT(*) AS line_items,
               COUNT(DISTINCT Reference2) AS transactions,
               SUM(SalesIncGST) AS revenue,
               SUM(Quantity) AS quantity,
               SUM(EstimatedCOGS) AS cogs,
               SUM(SalesIncGST) + COALESCE(SUM(EstimatedCOGS), 0) AS gp
        FROM transactions
        WHERE Store_ID = ?
          AND SaleDate >= CAST(? AS TIMESTAMP)
          AND SaleDate < CAST(? AS TIMESTAMP)
    """
    return ts.query(sql, [store_id, start, end])


@st.cache_data(ttl=300)
def query_lfl_stores(start, end, prior_start, prior_end):
    """Find stores with transactions in both periods."""
    ts = get_store()
    return run_query(ts, "like_for_like_stores",
                     start=start, end=end,
                     prior_start=prior_start, prior_end=prior_end)



def calc_delta(current_val, prior_val):
    """Calculate percentage change. Returns formatted string or None."""
    if prior_val and prior_val != 0:
        pct = (current_val - prior_val) / abs(prior_val) * 100
        return f"{pct:+.1f}%"
    return None


# ============================================================================
# SIDEBAR — PRODUCT HIERARCHY FILTERS (shared component)
# ============================================================================

# Cascading dropdown filter (Department → Category → Sub-Category → ...)
dropdown_hierarchy = render_hierarchy_filter(key_prefix="so")

# Searchable product filter (PLU / product name / category name)
search_hierarchy_result = render_searchable_hierarchy_filter(key_prefix="so_search")

# Merge both filters — dropdown takes precedence at each level;
# search fills in any levels the dropdown doesn't set.
# If both set a value and they conflict, the query's AND clauses
# naturally produce zero rows (correct intersection behaviour).
hierarchy = {"day_type": "all"}
for _hk in ["dept_code", "major_code", "minor_code",
             "hfm_item_code", "product_number"]:
    hierarchy[_hk] = dropdown_hierarchy.get(_hk) or search_hierarchy_result.get(_hk)

selected_dept_code = hierarchy["dept_code"]
selected_major_code = hierarchy["major_code"]
selected_minor_code = hierarchy["minor_code"]
selected_hfm_item_code = hierarchy["hfm_item_code"]
selected_product_number = hierarchy["product_number"]

# Quick period shortcuts (shared component with QTD)
qp_start, qp_end, qp_label = render_quick_period(key_prefix="so")


# ============================================================================
# FILTERS (Fiscal Period Selector)
# ============================================================================

filters = render_fiscal_selector(
    key_prefix="store_ops",
    show_store=True,
    show_comparison=True,
    store_names=STORE_NAMES,
    allowed_fys=[2024, 2025, 2026],
)

if not filters["start_date"]:
    st.stop()

start_str = filters["start_date"]
end_str = filters["end_date"]
period_label = filters.get("period_label", "")

# Override with quick period if selected
if qp_start and qp_end:
    start_str = qp_start
    end_str = qp_end
    period_label = qp_label

# Store Ops requires a specific store — default to Mosman if none selected
selected_store = filters["store_id"] or "28"
store_name = STORE_NAMES.get(selected_store, selected_store)

# Time dimension filters (sidebar)
time_filters = render_time_filter(key_prefix="so_time",
                                  fin_year=filters.get("fin_year"))

# Build reusable filter kwargs for all queries
filter_kwargs = {"store_id": selected_store, "start": start_str, "end": end_str}
for _fk in ["dept_code", "major_code", "minor_code", "hfm_item_code", "product_number"]:
    _fv = hierarchy.get(_fk)
    if _fv:
        filter_kwargs[_fk] = _fv
for _fk in ["day_of_week_names", "hour_start", "hour_end",
            "season_names", "quarter_nos", "month_nos"]:
    _fv = time_filters.get(_fk)
    if _fv is not None:
        filter_kwargs[_fk] = _fv

# Comparison period
comparison = filters.get("comparison")


# ============================================================================
# LIKE-FOR-LIKE STORE TOGGLE
# ============================================================================

lfl_stores = None
if comparison:
    lfl_enabled = st.checkbox(
        "Like-for-like stores only",
        value=False,
        key="so_lfl_toggle",
        help="Restrict to stores with transactions in both current and comparison periods",
    )
    if lfl_enabled:
        with st.spinner("Finding like-for-like stores..."):
            try:
                lfl_data = query_lfl_stores(
                    start_str, end_str,
                    comparison["start"], comparison["end"],
                )
                lfl_stores = [r["Store_ID"] for r in lfl_data] if lfl_data else []
                total_stores = len(STORE_NAMES)
                st.caption(
                    f"Like-for-like: {len(lfl_stores)} of {total_stores} stores "
                    f"active in both periods"
                )
                # If selected store is not in LFL set, warn
                if selected_store not in lfl_stores:
                    st.warning(
                        f"{store_name} has no data in the comparison period. "
                        f"Showing data anyway."
                    )
            except Exception as e:
                st.error(f"LFL query failed: {e}")
                lfl_stores = None


# ============================================================================
# ACTIVE FILTER SUMMARY
# ============================================================================

filter_parts = [store_name, period_label]
hierarchy_label = hierarchy_filter_summary(hierarchy)
if hierarchy_label:
    filter_parts.append(hierarchy_label)
tf_label = time_filter_summary(time_filters)
if tf_label:
    filter_parts.append(tf_label)
if comparison:
    comp_label = comparison.get("label", "vs Prior")
    if lfl_stores is not None:
        comp_label += " (LFL)"
    filter_parts.append(comp_label)

st.markdown(f"**Filters:** {' | '.join(filter_parts)}")


# ============================================================================
# KPI ROW
# ============================================================================

with st.spinner("Loading KPIs..."):
    try:
        kpi_data = query_summary_kpis(
            selected_store, start_str, end_str,
            dept_code=selected_dept_code,
            major_code=selected_major_code,
            minor_code=selected_minor_code,
            hfm_item_code=selected_hfm_item_code,
            product_number=selected_product_number,
            day_of_week_names=time_filters.get("day_of_week_names"),
            hour_start=time_filters.get("hour_start"),
            hour_end=time_filters.get("hour_end"),
            season_names=time_filters.get("season_names"),
            quarter_nos=time_filters.get("quarter_nos"),
            month_nos=time_filters.get("month_nos"),
        )
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

if not kpi_data:
    st.warning("No transaction data found for this store and date range.")
    st.stop()

kpi = kpi_data[0]
revenue = kpi["revenue"] or 0
transactions = kpi["transactions"] or 0
line_items = kpi["line_items"] or 0
gp = kpi["gp"] or 0

avg_basket = revenue / transactions if transactions > 0 else 0
items_per_txn = line_items / transactions if transactions > 0 else 0
gp_pct = (gp / revenue * 100) if revenue > 0 else 0

# Comparison KPIs
comp_revenue = comp_transactions = comp_gp = None
comp_avg_basket = comp_items_per_txn = comp_gp_pct = None

if comparison:
    try:
        comp_data = query_summary_kpis(
            selected_store, comparison["start"], comparison["end"],
            dept_code=selected_dept_code,
            major_code=selected_major_code,
            minor_code=selected_minor_code,
            hfm_item_code=selected_hfm_item_code,
            product_number=selected_product_number,
            day_of_week_names=time_filters.get("day_of_week_names"),
            hour_start=time_filters.get("hour_start"),
            hour_end=time_filters.get("hour_end"),
            season_names=time_filters.get("season_names"),
            quarter_nos=time_filters.get("quarter_nos"),
            month_nos=time_filters.get("month_nos"),
        )
        if comp_data and comp_data[0]["revenue"]:
            ck = comp_data[0]
            comp_revenue = ck["revenue"] or 0
            comp_transactions = ck["transactions"] or 0
            comp_line_items = ck["line_items"] or 0
            comp_gp = ck["gp"] or 0
            comp_avg_basket = (comp_revenue / comp_transactions
                               if comp_transactions > 0 else 0)
            comp_items_per_txn = (comp_line_items / comp_transactions
                                  if comp_transactions > 0 else 0)
            comp_gp_pct = (comp_gp / comp_revenue * 100
                           if comp_revenue > 0 else 0)
    except Exception:
        pass  # Comparison data unavailable — show current only

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Revenue", f"${revenue:,.0f}",
          delta=calc_delta(revenue, comp_revenue))
k2.metric("Transactions", f"{transactions:,.0f}",
          delta=calc_delta(transactions, comp_transactions))
k3.metric("Avg Basket", f"${avg_basket:,.2f}",
          delta=calc_delta(avg_basket, comp_avg_basket))
k4.metric("Items/Txn", f"{items_per_txn:.1f}",
          delta=calc_delta(items_per_txn, comp_items_per_txn))
k5.metric("Est GP%", f"{gp_pct:.1f}%",
          delta=calc_delta(gp_pct, comp_gp_pct))

if comparison and comp_revenue is not None:
    st.caption(f"Compared to: {comparison.get('label', 'Prior Period')}")


# ============================================================================
# TABBED ANALYSIS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Daily Trend", "Trading Patterns", "Category Mix",
    "Anomaly Detection", "Out of Stock",
])


# --- Tab 1: Daily Trend ---
with tab1:
    st.subheader(f"Daily Revenue & Transactions — {store_name}")

    with st.spinner("Loading trend data..."):
        try:
            trend_data = query_named("filtered_daily_trend", **filter_kwargs)
        except Exception as e:
            st.error(f"Failed to load trend: {e}")
            trend_data = []

    if trend_data:
        df_trend = pd.DataFrame(trend_data)
        df_trend["period"] = pd.to_datetime(df_trend["period"])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_trend["period"], y=df_trend["revenue"],
            name="Revenue ($)", yaxis="y", line=dict(color="#0d9488", width=2),
        ))
        fig.add_trace(go.Bar(
            x=df_trend["period"], y=df_trend["transactions"],
            name="Transactions", yaxis="y2", opacity=0.3,
            marker_color="#94a3b8",
        ))

        # Comparison overlay
        if comparison:
            try:
                comp_kwargs = dict(filter_kwargs,
                                   start=comparison["start"],
                                   end=comparison["end"])
                comp_trend = query_named("filtered_daily_trend", **comp_kwargs)
                if comp_trend:
                    df_comp = pd.DataFrame(comp_trend)
                    df_comp["period"] = pd.to_datetime(df_comp["period"])
                    # Align by day offset
                    current_start = df_trend["period"].min()
                    comp_start = df_comp["period"].min()
                    df_comp["period"] = df_comp["period"] + (current_start - comp_start)

                    fig.add_trace(go.Scatter(
                        x=df_comp["period"], y=df_comp["revenue"],
                        name=f"Revenue — {comparison.get('label', 'Prior')}",
                        yaxis="y",
                        line=dict(color="#94a3b8", width=2, dash="dash"),
                    ))
            except Exception:
                pass  # Silently skip comparison overlay on error

        fig.update_layout(
            yaxis=dict(title="Revenue ($)", side="left"),
            yaxis2=dict(title="Transactions", side="right", overlaying="y"),
            height=450, legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig, key="so_trend_chart")

        with st.expander("View data table"):
            st.dataframe(df_trend[["period", "revenue", "transactions", "line_items"]])
    else:
        st.info("No daily trend data available for this selection.")


# --- Tab 2: Trading Patterns (shared component) ---
with tab2:
    st.subheader(f"Trading Patterns — {store_name}")
    render_hourly_analysis(query_named, selected_store, start_str, end_str,
                           key_prefix="so", hierarchy=hierarchy,
                           time_filters=time_filters)


# --- Tab 3: Category Mix ---
with tab3:
    st.subheader(f"Category Mix — {store_name}")

    # Time filter kwargs for category queries
    _time_kw = {"store_id": selected_store, "start": start_str, "end": end_str}
    for _tk in ["day_of_week_names", "hour_start", "hour_end",
                "season_names", "quarter_nos", "month_nos"]:
        _tv = time_filters.get(_tk)
        if _tv is not None:
            _time_kw[_tk] = _tv

    # Determine hierarchy level for display
    if selected_dept_code and selected_major_code:
        # Show minor group breakdown
        st.markdown(f"**Revenue by Sub-Category**")
        try:
            cat_data = query_named("minor_group_revenue",
                                   dept_code=selected_dept_code,
                                   major_code=selected_major_code,
                                   **_time_kw)
            cat_name_col = "MinorGroupDesc"
        except Exception as e:
            st.error(f"Sub-category breakdown failed: {e}")
            cat_data = None
            cat_name_col = None
    elif selected_dept_code:
        # Show major group breakdown
        st.markdown(f"**Revenue by Category**")
        try:
            cat_data = query_named("major_group_revenue",
                                   dept_code=selected_dept_code,
                                   **_time_kw)
            cat_name_col = "MajorGroupDesc"
        except Exception as e:
            st.error(f"Category breakdown failed: {e}")
            cat_data = None
            cat_name_col = None
    else:
        # Default: department breakdown
        st.markdown("**Revenue by Department**")
        try:
            cat_data = query_named("department_revenue", **_time_kw)
            cat_name_col = "DepartmentDesc"
        except Exception as e:
            st.error(f"Department breakdown failed: {e}")
            cat_data = None
            cat_name_col = None

    if cat_data and cat_name_col:
        df_cat_mix = pd.DataFrame(cat_data)
        col_cpie, col_cbar = st.columns([1, 2])

        with col_cpie:
            fig_cpie = px.pie(
                df_cat_mix, values="revenue", names=cat_name_col,
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_cpie.update_layout(height=350)
            st.plotly_chart(fig_cpie,
                            key="so_cat_pie_chart")

        with col_cbar:
            fig_cbar = px.bar(
                df_cat_mix.sort_values("revenue"),
                x="revenue", y=cat_name_col,
                orientation="h",
                color="revenue",
                color_continuous_scale=["#ccfbf1", "#0d9488"],
                labels={"revenue": "Revenue ($)", cat_name_col: ""},
            )
            fig_cbar.update_layout(height=350, coloraxis_showscale=False)
            st.plotly_chart(fig_cbar,
                            key="so_cat_bar_chart")
    elif cat_data is not None:
        st.info("No category data available.")

    # GST-based split (secondary view)
    st.markdown("---")
    st.markdown("**Fresh vs Packaged (GST proxy)**")
    st.caption("Fresh = GST-free items. Packaged = GST items.")

    col_pie, col_trend = st.columns([1, 2])

    with col_pie:
        try:
            gst_data = query_named("gst_category_split", **filter_kwargs)
            if gst_data:
                df_gst = pd.DataFrame(gst_data)
                fig_pie = px.pie(
                    df_gst, values="revenue", names="category",
                    color_discrete_sequence=["#059669", "#7c3aed"],
                    hole=0.4,
                )
                fig_pie.update_layout(height=300)
                st.plotly_chart(fig_pie,
                                key="so_gst_pie_chart")
            else:
                st.info("No category data.")
        except Exception as e:
            st.error(f"Category split failed: {e}")

    with col_trend:
        try:
            cat_trend = query_named("gst_category_monthly_trend",
                                    **filter_kwargs)
            if cat_trend:
                df_gst_trend = pd.DataFrame(cat_trend)
                df_gst_trend["period"] = pd.to_datetime(df_gst_trend["period"])
                fig_gst_trend = px.bar(
                    df_gst_trend, x="period", y="revenue", color="category",
                    barmode="stack",
                    color_discrete_map={"Fresh": "#059669", "Packaged": "#7c3aed"},
                    labels={"period": "Month", "revenue": "Revenue ($)"},
                )
                fig_gst_trend.update_layout(height=300)
                st.plotly_chart(fig_gst_trend,
                                key="so_gst_trend_chart")
            else:
                st.info("No category trend data.")
        except Exception as e:
            st.error(f"Category trend failed: {e}")


# --- Tab 4: Anomaly Detection ---
with tab4:
    st.subheader(f"Revenue Anomalies — {store_name}")
    st.caption("Days where revenue deviates > 2 standard deviations from the store mean.")

    with st.spinner("Detecting anomalies..."):
        try:
            anomalies = query_named("anomaly_candidates",
                                    **filter_kwargs)
            if anomalies:
                df_anom = pd.DataFrame(anomalies)
                df_anom["sale_date"] = pd.to_datetime(df_anom["sale_date"]).dt.date
                df_anom["deviation"] = df_anom["revenue"] - df_anom["expected"]
                df_anom["direction"] = df_anom["deviation"].apply(
                    lambda x: "Above" if x > 0 else "Below")

                above = len(df_anom[df_anom["direction"] == "Above"])
                below = len(df_anom[df_anom["direction"] == "Below"])

                a1, a2, a3 = st.columns(3)
                a1.metric("Anomaly Days", len(df_anom))
                a2.metric("Above Average", above)
                a3.metric("Below Average", below)

                st.dataframe(
                    df_anom[["sale_date", "revenue", "expected", "z_score", "direction"]]
                    .style.format({
                        "revenue": "${:,.0f}",
                        "expected": "${:,.0f}",
                        "z_score": "{:.1f}",
                    }),
                )
            else:
                st.success("No anomalies detected. Daily revenue is within normal range.")
        except Exception as e:
            st.error(f"Anomaly detection failed: {e}")


# --- Tab 5: Out of Stock ---
with tab5:
    st.subheader(f"Estimated Out-of-Stock Impact — {store_name}")
    st.caption(
        "Identifies products with zero sales during periods where they "
        "normally trade. Missed revenue is estimated from 90-day baseline "
        "average daily revenue."
    )

    # Smart time grain default based on period length
    from datetime import datetime as _dt
    _period_days = (_dt.strptime(end_str, "%Y-%m-%d")
                    - _dt.strptime(start_str, "%Y-%m-%d")).days
    _default_grain = (
        "Daily" if _period_days <= 28
        else "Weekly" if _period_days <= 91
        else "Monthly"
    )
    _grain_options = ["Daily", "Weekly", "Monthly"]
    time_grain = st.radio(
        "Time Granularity", _grain_options,
        index=_grain_options.index(_default_grain),
        horizontal=True, key="oos_time_grain",
    )

    # --- KPIs ---
    with st.spinner("Calculating out-of-stock estimates..."):
        try:
            oos_kw = {"start": start_str, "end": end_str,
                      "store_id": selected_store}
            if selected_dept_code:
                oos_kw["dept_code"] = selected_dept_code
            if selected_major_code:
                oos_kw["major_code"] = selected_major_code

            summary = query_named("oos_summary", **oos_kw)
        except Exception as e:
            st.error(f"Out-of-stock analysis failed: {e}")
            summary = None

    if summary and len(summary) > 0:
        s = summary[0]
        total_missed = s.get("total_missed_revenue", 0) or 0
        oos_incidents = s.get("oos_incidents", 0) or 0
        affected = s.get("affected_products", 0) or 0
        active = s.get("active_products", 0) or 0
        analysis_days = s.get("analysis_days", 0) or 0

        # Availability rate: 1 - (oos_incidents / (active * analysis_days))
        expected_selling_days = active * analysis_days
        avail_rate = (
            (1 - oos_incidents / expected_selling_days) * 100
            if expected_selling_days > 0 else 0
        )

        ok1, ok2, ok3, ok4 = st.columns(4)
        ok1.metric("Est. Missed Revenue", "${:,.0f}".format(total_missed))
        ok2.metric("OOS Incidents", "{:,}".format(oos_incidents))
        ok3.metric("Affected Products", "{:,}".format(affected))
        ok4.metric("Availability Rate", "{:.1f}%".format(avail_rate))

        # --- Heatmap ---
        st.markdown("---")

        # Determine hierarchy level
        if selected_dept_code and selected_major_code:
            level_label = "Sub-Category"
            try:
                oos_data = query_named(
                    "oos_by_minor_group",
                    start=start_str, end=end_str,
                    store_id=selected_store,
                    dept_code=selected_dept_code,
                    major_code=selected_major_code,
                )
            except Exception as e:
                st.error(f"Sub-category OOS data failed: {e}")
                oos_data = None
        elif selected_dept_code:
            level_label = "Category"
            try:
                oos_data = query_named(
                    "oos_by_major_group",
                    start=start_str, end=end_str,
                    store_id=selected_store,
                    dept_code=selected_dept_code,
                )
            except Exception as e:
                st.error(f"Category OOS data failed: {e}")
                oos_data = None
        else:
            level_label = "Department"
            try:
                oos_data = query_named(
                    "oos_by_department",
                    start=start_str, end=end_str,
                    store_id=selected_store,
                )
            except Exception as e:
                st.error(f"Department OOS data failed: {e}")
                oos_data = None

        if oos_data:
            df_oos = pd.DataFrame(oos_data)

            # Aggregate by selected time grain
            if time_grain == "Weekly":
                st.subheader(f"Missed Revenue — {level_label} x Fiscal Week")
                pivot = (df_oos.groupby(["label", "fiscal_week"])
                         ["missed_revenue"].sum()
                         .unstack(fill_value=0))
                pivot.columns = [
                    "W{:02d}".format(int(w)) for w in pivot.columns
                ]
            elif time_grain == "Monthly":
                st.subheader(f"Missed Revenue — {level_label} x Month")
                # Group by fiscal month number for ordering
                agg = (df_oos.groupby(
                    ["label", "fiscal_month", "month_name"])
                    ["missed_revenue"].sum().reset_index())
                pivot = agg.pivot_table(
                    index="label", columns="fiscal_month",
                    values="missed_revenue", aggfunc="sum",
                    fill_value=0,
                )
                # Use month short names as column labels
                month_map = (agg.drop_duplicates("fiscal_month")
                             .set_index("fiscal_month")["month_name"]
                             .to_dict())
                pivot.columns = [
                    month_map.get(c, str(c)) for c in pivot.columns
                ]
            else:
                st.subheader(f"Missed Revenue — {level_label} x Day")
                df_oos["day_label"] = pd.to_datetime(
                    df_oos["cal_date"]
                ).dt.strftime("%d %b")
                # Sort by actual date
                df_oos = df_oos.sort_values("cal_date")
                day_order = df_oos["day_label"].unique().tolist()
                pivot = (df_oos.groupby(["label", "day_label"])
                         ["missed_revenue"].sum()
                         .unstack(fill_value=0))
                pivot = pivot[[c for c in day_order if c in pivot.columns]]

            # Format text: $1K / $1.2M for readability
            def _fmt_val(v):
                if v >= 1_000_000:
                    return "${:.1f}M".format(v / 1_000_000)
                if v >= 1_000:
                    return "${:.0f}K".format(v / 1_000)
                if v > 0:
                    return "${:.0f}".format(v)
                return ""

            fig_oos = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns.tolist(),
                y=pivot.index.tolist(),
                colorscale=[
                    [0, "#f0fdf4"],
                    [0.3, "#fbbf24"],
                    [0.7, "#ef4444"],
                    [1, "#991b1b"],
                ],
                text=[[_fmt_val(v) for v in row]
                      for row in pivot.values],
                texttemplate="%{text}",
                textfont={"size": 10},
                hovertemplate=(
                    "<b>%{y}</b><br>%{x}<br>"
                    "Missed: $%{z:,.0f}<extra></extra>"
                ),
            ))
            fig_oos.update_layout(
                height=max(350, len(pivot) * 40),
                xaxis_title=time_grain,
                yaxis_title=level_label,
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_oos, use_container_width=True,
                            key="oos_heatmap")

            # Summary table below heatmap
            totals = (df_oos.groupby("label").agg(
                missed_revenue=("missed_revenue", "sum"),
                oos_incidents=("oos_incidents", "sum"),
                affected_products=("affected_products", "max"),
            ).sort_values("missed_revenue", ascending=False)
             .reset_index())
            totals.columns = [
                level_label, "Missed Revenue ($)",
                "OOS Incidents", "Affected Products",
            ]
            totals["Missed Revenue ($)"] = totals[
                "Missed Revenue ($)"
            ].apply(lambda x: "${:,.0f}".format(x))
            st.dataframe(totals, hide_index=True,
                         use_container_width=True,
                         key="oos_summary_table")
        else:
            st.info("No out-of-stock data for the selected filters.")

        # --- Top Products ---
        st.markdown("---")
        st.subheader("Top 20 Worst-Affected Products")

        try:
            top_kw = {"start": start_str, "end": end_str,
                      "store_id": selected_store, "limit": 20}
            if selected_dept_code:
                top_kw["dept_code"] = selected_dept_code
            if selected_major_code:
                top_kw["major_code"] = selected_major_code
            top_products = query_named("oos_top_products", **top_kw)
        except Exception as e:
            st.error(f"Top products query failed: {e}")
            top_products = None

        if top_products:
            df_top = pd.DataFrame(top_products)
            df_top["avail_pct"] = (
                (1 - df_top["oos_days"] / df_top["total_days"]) * 100
            )
            display_top = df_top[[
                "PLUItem_ID", "product_name", "department",
                "category", "oos_days", "total_days",
                "missed_revenue", "avail_pct",
            ]].copy()
            display_top.columns = [
                "PLU", "Product", "Department", "Category",
                "OOS Days", "Total Days", "Est. Missed ($)",
                "Availability %",
            ]
            display_top["Est. Missed ($)"] = display_top[
                "Est. Missed ($)"
            ].apply(lambda x: "${:,.0f}".format(x))
            display_top["Availability %"] = display_top[
                "Availability %"
            ].apply(lambda x: "{:.0f}%".format(x))
            st.dataframe(display_top, hide_index=True,
                         use_container_width=True,
                         key="oos_top_products_table")
        else:
            st.info("No product-level OOS data available.")

        # --- CSV Export ---
        st.markdown("---")
        if oos_data:
            csv_oos = pd.DataFrame(oos_data).to_csv(index=False)
            st.download_button(
                "Download OOS Data (CSV)",
                data=csv_oos,
                file_name="out_of_stock_analysis.csv",
                mime="text/csv",
                key="dl_oos_data",
            )

        # --- Methodology ---
        with st.expander("Methodology"):
            st.markdown("""
**How this analysis works:**

This is a **heuristic estimate** based on zero-sales detection
from POS transaction data. We do not have actual inventory or
stock-level data.

**Algorithm:**
1. **Baseline** (90 days before analysis period): For each
   product at each store, calculate the average daily revenue
   and count of selling days.
2. **Active products**: Only products that sold on 30+ of
   the 90 baseline days are included (roughly once every
   3 days).
3. **Gap detection**: For each day in the analysis period,
   if an active product has zero sales, it is flagged as a
   potential out-of-stock event.
4. **Missed revenue**: Estimated as the product's baseline
   average daily revenue for each zero-sale day.

**Caveats:**
- Not all zero-sale days are true stock-outs (could be
  natural demand variation)
- Seasonal items may show false positives (mitigated by
  the 90-day rolling baseline)
- Discontinued items are filtered out by requiring recent
  baseline sales
- Estimated revenue is based on historical averages, not
  actual demand
- Products selling less frequently than every 3 days are
  excluded from analysis
            """)
    else:
        st.info(
            "No out-of-stock data available. Ensure the analysis "
            "period has at least 90 days of prior baseline data."
        )


# ============================================================================
# PLU STOCKTAKE ALERTS (from PLU Intelligence — 27.3M rows)
# ============================================================================

try:
    from plu_layer import db_available as plu_db_ok, top_plus_by_stocktake
    if plu_db_ok():
        st.markdown("---")
        st.subheader("Stocktake Variance Alerts")
        st.caption("Items with largest stocktake discrepancies — from 27.3M weekly PLU records")

        stocktake_items = top_plus_by_stocktake(limit=10)
        if stocktake_items:
            import pandas as _pd
            stdf = _pd.DataFrame(stocktake_items)
            stdf["total_variance"] = stdf["total_variance"].apply(lambda x: f"${(x or 0):,.0f}")
            stdf["total_sales"] = stdf["total_sales"].apply(lambda x: f"${(x or 0):,.0f}")
            stdf["variance_pct"] = stdf["variance_pct"].apply(lambda x: f"{(x or 0):.1f}%")
            stdf = stdf.rename(columns={
                "plu_code": "PLU", "description": "Item", "department": "Dept",
                "total_variance": "Variance $", "total_sales": "Sales $",
                "variance_pct": "Variance %",
            })
            st.dataframe(
                stdf[["PLU", "Item", "Dept", "Variance $", "Sales $", "Variance %"]],
                hide_index=True, key="ops_stocktake_alert_table",
            )
            _pages = st.session_state.get("_pages", {})
            if "plu-intel" in _pages:
                st.page_link(_pages["plu-intel"], label="View full Stocktake Analysis", icon="📊")
        else:
            st.info("No significant stocktake variances found.")
except ImportError:
    pass


# ============================================================================
# ASK A QUESTION
# ============================================================================

render_voice_data_box("store_ops")
render_ask_question("store_ops")

# ============================================================================
# CROSS-DASHBOARD LINKS
# ============================================================================

st.markdown("---")
st.markdown("**Dig Deeper**")
_pages = st.session_state.get("_pages", {})
c1, c2, c3 = st.columns(3)
if "plu-intel" in _pages:
    c1.page_link(_pages["plu-intel"], label="PLU Item Detail", icon="📊")
if "product-intel" in _pages:
    c2.page_link(_pages["product-intel"], label="Product Intelligence", icon="🔍")
if "profitability" in _pages:
    c3.page_link(_pages["profitability"], label="Store Profitability", icon="💰")

# ============================================================================
# DATA SOURCE NOTES
# ============================================================================

st.markdown("---")
st.caption(
    "Data: 383M POS transactions from Microsoft Fabric (Jul 2023 - Feb 2026) | "
    "72,911-product hierarchy (98.3% PLU match) | "
    "Times shown in AEDT (UTC+11 approximation)"
)

render_footer("Store Operations", user=user)
