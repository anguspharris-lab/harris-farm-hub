"""
Harris Farm Hub — Product Intelligence Dashboard
Buying & merchandising analytics from 383M POS transactions (DuckDB/parquet).
Top items, PLU deep dive, basket analysis, slow movers.
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
from plu_lookup import resolve_plu, enrich_items, load_plu_names, load_plu_details, plu_coverage_stats
from product_hierarchy import get_departments, get_major_groups, get_minor_groups

from shared.styles import render_header, render_footer
from shared.ask_question import render_ask_question
from shared.fiscal_selector import render_fiscal_selector
from shared.hierarchy_filter import render_hierarchy_filter, hierarchy_filter_summary
from shared.hourly_charts import render_hourly_analysis
from shared.time_filter import (
    render_time_filter, time_filter_summary, render_quick_period,
)

user = st.session_state.get("auth_user")
render_header(
    "Product Intelligence",
    "**Item-level performance analytics** | Top items, basket analysis, PLU deep dive",
)


# ============================================================================
# DATA ACCESS
# ============================================================================

@st.cache_resource
def get_store():
    return TransactionStore()


@st.cache_data(ttl=300)
def query_named(name, **kwargs):
    ts = get_store()
    return run_query(ts, name, **kwargs)


@st.cache_data(ttl=300)
def query_top_items(start, end, store_id=None, limit=20):
    ts = get_store()
    kwargs = {"start": start, "end": end, "limit": limit}
    if store_id:
        kwargs["store_id"] = store_id
    items = run_query(ts, "top_items_by_revenue", **kwargs)
    return enrich_items(items, plu_key="pluitem_id")


@st.cache_data(ttl=300)
def query_kpis(start, end, store_id=None):
    ts = get_store()
    store_filter = f"AND Store_ID = '{store_id}'" if store_id else ""
    sql = f"""
        SELECT COUNT(DISTINCT PLUItem_ID) AS unique_plus,
               SUM(SalesIncGST) AS total_revenue,
               AVG(SalesIncGST) AS avg_item_price,
               SUM(CASE WHEN GST = 0 THEN SalesIncGST ELSE 0 END) AS fresh_revenue,
               SUM(CASE WHEN GST > 0 THEN SalesIncGST ELSE 0 END) AS packaged_revenue
        FROM transactions
        WHERE SaleDate >= CAST(? AS TIMESTAMP)
          AND SaleDate < CAST(? AS TIMESTAMP)
          {store_filter}
    """
    return ts.query(sql, [start, end])


# ============================================================================
# SIDEBAR — PRODUCT HIERARCHY FILTERS (shared component)
# ============================================================================

hierarchy = render_hierarchy_filter(key_prefix="pi")
selected_dept_code = hierarchy["dept_code"]
selected_major_code = hierarchy["major_code"]
selected_minor_code = hierarchy["minor_code"]
selected_hfm_item_code = hierarchy["hfm_item_code"]
selected_product_number = hierarchy["product_number"]

# Quick period shortcuts (shared component with QTD)
qp_start, qp_end, qp_label = render_quick_period(key_prefix="pi")


# ============================================================================
# FILTERS (Fiscal Period Selector)
# ============================================================================

col_sel, col_limit = st.columns([4, 1])

with col_sel:
    filters = render_fiscal_selector(
        key_prefix="product_intel",
        show_store=True,
        store_names=STORE_NAMES,
        allowed_fys=[2024, 2025, 2026],
    )

with col_limit:
    item_limit = st.selectbox("Top N Items", [10, 20, 50], index=1)

if not filters["start_date"]:
    st.stop()

start_str = filters["start_date"]
end_str = filters["end_date"]

# Override with quick period if selected
if qp_start and qp_end:
    start_str = qp_start
    end_str = qp_end

store_id = filters["store_id"]
store_label = STORE_NAMES.get(store_id, "All Stores") if store_id else "All Stores"
selected_store = store_id or "28"  # Default Mosman for store-specific queries

# Time dimension filters (sidebar)
time_filters = render_time_filter(key_prefix="pi_time",
                                  fin_year=filters.get("fin_year"))

# Active filter summary
filter_parts = [store_label]
h_label = hierarchy_filter_summary(hierarchy)
if h_label:
    filter_parts.append(h_label)
tf_label = time_filter_summary(time_filters)
if tf_label:
    filter_parts.append(tf_label)
st.markdown(f"**Filters:** {' | '.join(filter_parts)}")


# ============================================================================
# KPI ROW
# ============================================================================

try:
    kpi_data = query_kpis(start_str, end_str, store_id)
except Exception as e:
    st.error(f"Failed to load KPIs: {e}")
    st.stop()

if not kpi_data:
    st.warning("No transaction data found for this selection.")
    st.stop()

kpi = kpi_data[0]
unique_plus = kpi["unique_plus"] or 0
total_revenue = kpi["total_revenue"] or 0
avg_price = kpi["avg_item_price"] or 0
fresh_rev = kpi["fresh_revenue"] or 0
packaged_rev = kpi["packaged_revenue"] or 0
fresh_ratio = (fresh_rev / (fresh_rev + packaged_rev) * 100) if (fresh_rev + packaged_rev) > 0 else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Unique PLUs", f"{unique_plus:,}")
k2.metric("Total Revenue", f"${total_revenue:,.0f}")
k3.metric("Fresh:Packaged", f"{fresh_ratio:.0f}:{100 - fresh_ratio:.0f}")
k4.metric("Avg Item Price", f"${avg_price:.2f}")


# ============================================================================
# TABBED ANALYSIS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Top Items", "PLU Deep Dive", "Basket Analysis", "Slow Movers",
    "Trading Patterns",
])


# --- Tab 1: Top Items ---
with tab1:
    st.subheader("Top Items by Revenue")

    coverage = plu_coverage_stats()
    st.caption(coverage["coverage_note"])

    try:
        _dow = time_filters.get("day_of_week_names")
        _has_tf = (_dow or time_filters.get("hour_start") is not None
                   or time_filters.get("season_names")
                   or time_filters.get("quarter_nos")
                   or time_filters.get("month_nos"))
        if selected_dept_code or _has_tf:
            # Use hierarchy-filtered query
            items = query_named(
                "top_items_filtered",
                start=start_str, end=end_str,
                store_id=store_id,
                dept_code=selected_dept_code,
                major_code=selected_major_code,
                minor_code=selected_minor_code,
                hfm_item_code=selected_hfm_item_code,
                product_number=selected_product_number,
                day_of_week_names=_dow,
                hour_start=time_filters.get("hour_start"),
                hour_end=time_filters.get("hour_end"),
                season_names=time_filters.get("season_names"),
                quarter_nos=time_filters.get("quarter_nos"),
                month_nos=time_filters.get("month_nos"),
                limit=item_limit,
            )
        else:
            items = query_top_items(start_str, end_str, store_id, item_limit)
        if items:
            df_items = pd.DataFrame(items)
            df_items.insert(0, "rank", range(1, len(df_items) + 1))

            display_cols = ["rank", "pluitem_id", "product_name",
                            "total_revenue", "total_qty", "transaction_count",
                            "avg_price"]
            available_cols = [c for c in display_cols if c in df_items.columns]

            st.dataframe(
                df_items[available_cols].style.format({
                    "total_revenue": "${:,.0f}",
                    "total_qty": "{:,.0f}",
                    "transaction_count": "{:,}",
                    "avg_price": "${:.2f}",
                }),
                height=min(40 * len(df_items) + 40, 600),
                key="prodintel_top_items_table",
            )
        else:
            st.info("No items found.")
    except Exception as e:
        st.error(f"Top items query failed: {e}")


# --- Tab 2: PLU Deep Dive ---
with tab2:
    st.subheader("PLU Deep Dive")

    plu_input = st.text_input(
        "Enter PLU ID",
        value="4322",
        help="Enter a numeric PLU/item code to see its performance",
    )

    if plu_input:
        plu_name = resolve_plu(plu_input)
        details = load_plu_details()
        plu_detail = details.get(plu_input.strip(), {})
        dept_label = plu_detail.get("department", "")
        major_label = plu_detail.get("major_group", "")
        lifecycle_label = plu_detail.get("lifecycle", "")
        context_parts = [f"**{plu_name}** (PLU {plu_input})"]
        if dept_label:
            context_parts.append(f"{dept_label} > {major_label}")
        if lifecycle_label:
            context_parts.append(f"Status: {lifecycle_label}")
        st.markdown(" | ".join(context_parts))

        col_trend, col_stores = st.columns(2)

        with col_trend:
            st.markdown("**Monthly Trend**")
            try:
                plu_trend = query_named("plu_monthly_trend", plu_id=plu_input)
                if plu_trend:
                    df_pt = pd.DataFrame(plu_trend)
                    df_pt["period"] = pd.to_datetime(df_pt["period"])
                    fig_pt = px.line(
                        df_pt, x="period", y="revenue",
                        labels={"period": "Month", "revenue": "Revenue ($)"},
                        color_discrete_sequence=["#0d9488"],
                    )
                    fig_pt.update_layout(height=350)
                    st.plotly_chart(fig_pt, key="prodintel_plu_trend")
                else:
                    st.info("No trend data for this PLU.")
            except Exception as e:
                st.error(f"PLU trend failed: {e}")

        with col_stores:
            st.markdown("**Performance by Store**")
            try:
                plu_stores = query_named(
                    "plu_across_stores",
                    plu_id=plu_input, start=start_str, end=end_str)
                if plu_stores:
                    df_ps = pd.DataFrame(plu_stores)
                    df_ps["store_name"] = df_ps["store_id"].apply(
                        lambda x: STORE_NAMES.get(str(x), str(x)))
                    fig_ps = px.bar(
                        df_ps.sort_values("revenue", ascending=True).tail(15),
                        x="revenue", y="store_name", orientation="h",
                        labels={"revenue": "Revenue ($)", "store_name": "Store"},
                        color_discrete_sequence=["#0d9488"],
                    )
                    fig_ps.update_layout(height=400)
                    st.plotly_chart(fig_ps, key="prodintel_plu_stores")
                else:
                    st.info("No store data for this PLU.")
            except Exception as e:
                st.error(f"PLU store data failed: {e}")

        st.markdown("**Price Dispersion Across Stores**")
        try:
            price_data = query_named(
                "price_dispersion",
                plu_id=plu_input, start=start_str, end=end_str)
            if price_data:
                df_price = pd.DataFrame(price_data)
                df_price["store_name"] = df_price["store_id"].apply(
                    lambda x: STORE_NAMES.get(str(x), str(x)))
                st.dataframe(
                    df_price[["store_name", "avg_unit_price", "min_unit_price",
                              "max_unit_price", "line_items"]].style.format({
                        "avg_unit_price": "${:.2f}",
                        "min_unit_price": "${:.2f}",
                        "max_unit_price": "${:.2f}",
                    }),
                    key="prodintel_price_dispersion_table",
                )
            else:
                st.info("Insufficient price data (requires >= 10 transactions per store).")
        except Exception as e:
            st.error(f"Price dispersion failed: {e}")

        # PLU Weekly Performance from PLU Intelligence (27.3M rows)
        try:
            from plu_layer import db_available as plu_ok, plu_weekly_trend, plu_store_breakdown
            if plu_ok():
                st.markdown("---")
                st.markdown("**PLU Weekly Performance** *(from PLU Intelligence — 27.3M rows)*")
                trend = plu_weekly_trend(plu_input)
                if trend:
                    tdf = pd.DataFrame(trend)
                    tdf["label"] = tdf.apply(lambda r: f"FY{r['fiscal_year']} W{r['fiscal_week']}", axis=1)
                    # Make wastage positive for display
                    tdf["wastage_abs"] = tdf["wastage"].abs()

                    col_w, col_m = st.columns(2)
                    with col_w:
                        st.markdown("**Weekly Wastage Trend**")
                        fig_w = px.bar(
                            tdf, x="label", y="wastage_abs",
                            labels={"label": "Week", "wastage_abs": "Wastage ($)"},
                            color_discrete_sequence=["#ef4444"],
                        )
                        fig_w.update_layout(height=300, xaxis_tickangle=-45, showlegend=False)
                        st.plotly_chart(fig_w, key="prodintel_plu_wastage_trend")
                    with col_m:
                        st.markdown("**Weekly Margin Trend**")
                        fig_m = px.bar(
                            tdf, x="label", y="gm",
                            labels={"label": "Week", "gm": "Gross Margin ($)"},
                            color_discrete_sequence=["#10b981"],
                        )
                        fig_m.update_layout(height=300, xaxis_tickangle=-45, showlegend=False)
                        st.plotly_chart(fig_m, key="prodintel_plu_gm_trend")

                    # Store breakdown
                    breakdown = plu_store_breakdown(plu_input)
                    if breakdown:
                        st.markdown("**PLU Performance by Store** *(wastage, margin, stocktake)*")
                        bdf = pd.DataFrame(breakdown)
                        bdf = bdf.sort_values("sales", ascending=False)
                        disp = bdf[["store_name", "sales", "gm", "wastage", "stocktake"]].copy()
                        disp["wastage"] = disp["wastage"].abs()
                        disp["stocktake"] = disp["stocktake"].abs()
                        disp.columns = ["Store", "Sales $", "Margin $", "Wastage $", "Stocktake $"]
                        st.dataframe(disp, hide_index=True, key="prodintel_plu_store_breakdown")

                    st.page_link("dashboards/plu_intel_dashboard.py", label="Full PLU Intelligence", icon="📊")
                else:
                    st.info("No PLU Intelligence data for this item.")
        except ImportError:
            pass


# --- Tab 3: Basket Analysis ---
with tab3:
    st.subheader("Basket Analysis")

    col_dist, col_store = st.columns(2)

    with col_dist:
        st.markdown("**Basket Size Distribution**")
        basket_store = selected_store or "28"  # Default Mosman for basket query
        try:
            basket_data = query_named(
                "basket_size_distribution",
                store_id=basket_store, start=start_str, end=end_str)
            if basket_data:
                df_basket = pd.DataFrame(basket_data)
                fig_basket = px.bar(
                    df_basket, x="basket_size", y="frequency",
                    labels={"basket_size": "Items per Basket",
                            "frequency": "Basket Count"},
                    color_discrete_sequence=["#0d9488"],
                )
                fig_basket.update_layout(height=400)
                st.plotly_chart(fig_basket, key="prodintel_basket_dist")
                st.caption(
                    f"Store: {STORE_NAMES.get(basket_store, basket_store)}"
                )
            else:
                st.info("No basket data available.")
        except Exception as e:
            st.error(f"Basket distribution failed: {e}")

    with col_store:
        st.markdown("**Average Basket by Store**")
        try:
            avg_basket = query_named(
                "avg_basket_by_store", start=start_str, end=end_str)
            if avg_basket:
                df_ab = pd.DataFrame(avg_basket)
                df_ab["store_name"] = df_ab["store_id"].apply(
                    lambda x: STORE_NAMES.get(str(x), str(x)))
                fig_ab = px.bar(
                    df_ab.sort_values("avg_basket_value", ascending=True).tail(20),
                    x="avg_basket_value", y="store_name", orientation="h",
                    labels={"avg_basket_value": "Avg Basket Value ($)",
                            "store_name": "Store"},
                    color_discrete_sequence=["#7c3aed"],
                )
                fig_ab.update_layout(height=500)
                st.plotly_chart(fig_ab, key="prodintel_avg_basket_bar")
            else:
                st.info("No basket comparison data.")
        except Exception as e:
            st.error(f"Avg basket query failed: {e}")


# --- Tab 4: Slow Movers ---
with tab4:
    st.subheader("Slow Movers")
    st.caption(
        "Items with fewer than the threshold number of transactions in the period. "
        "Useful for range review and buying decisions."
    )

    threshold = st.slider("Transaction Threshold", 5, 50, 10)

    try:
        _dow = time_filters.get("day_of_week_names")
        _has_tf = (_dow or time_filters.get("hour_start") is not None
                   or time_filters.get("season_names")
                   or time_filters.get("quarter_nos")
                   or time_filters.get("month_nos"))
        if selected_dept_code or _has_tf:
            slow = query_named(
                "slow_movers_filtered",
                start=start_str, end=end_str,
                store_id=store_id,
                dept_code=selected_dept_code,
                major_code=selected_major_code,
                minor_code=selected_minor_code,
                hfm_item_code=selected_hfm_item_code,
                product_number=selected_product_number,
                day_of_week_names=_dow,
                hour_start=time_filters.get("hour_start"),
                hour_end=time_filters.get("hour_end"),
                season_names=time_filters.get("season_names"),
                quarter_nos=time_filters.get("quarter_nos"),
                month_nos=time_filters.get("month_nos"),
                threshold=threshold, limit=50)
        else:
            slow = query_named(
                "slow_movers",
                start=start_str, end=end_str,
                store_id=store_id,
                threshold=threshold, limit=50)
        if slow:
            if not selected_dept_code:
                slow = enrich_items(slow, plu_key="pluitem_id")
            df_slow = pd.DataFrame(slow)
            show_cols = ["pluitem_id", "product_name", "transaction_count",
                         "total_qty", "total_revenue", "stores_stocked"]
            show_cols = [c for c in show_cols if c in df_slow.columns]
            st.dataframe(
                df_slow[show_cols].style.format({
                    "total_revenue": "${:,.0f}",
                    "total_qty": "{:,.0f}",
                }),
                key="prodintel_slow_movers_table",
            )
            st.info(f"{len(slow)} items with < {threshold} transactions found.")
        else:
            st.success(f"No items with < {threshold} transactions. Range looks healthy.")
    except Exception as e:
        st.error(f"Slow movers query failed: {e}")


# --- Tab 5: Trading Patterns (shared component) ---
with tab5:
    st.subheader(f"Trading Patterns — {store_label}")
    render_hourly_analysis(query_named, selected_store, start_str, end_str,
                           key_prefix="pi", hierarchy=hierarchy,
                           time_filters=time_filters)


# ============================================================================
# ASK A QUESTION
# ============================================================================

render_ask_question("product_intel")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(
    "Data: 383M POS transactions from Microsoft Fabric (Jul 2023 - Feb 2026) | "
    f"Product names: {len(load_plu_names()):,} products from hierarchy | "
    "98.3% PLU match rate"
)

render_footer("Product Intelligence", user=user)
