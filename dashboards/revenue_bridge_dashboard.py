"""
Harris Farm Hub — Revenue Bridge Dashboard
Revenue decomposition, monthly trends, store rankings, year-over-year.
Real item-level POS transactions (383M rows, FY24-FY26 via DuckDB/parquet).
Data source: Microsoft Fabric retail fact_pos_sales.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

# Ensure backend is importable
_BACKEND = str(Path(__file__).resolve().parent.parent / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from transaction_layer import TransactionStore, STORE_NAMES
from transaction_queries import run_query
from product_hierarchy import get_departments, get_major_groups, get_minor_groups

# Page configuration
st.set_page_config(
    page_title="Revenue Bridge | Harris Farm Hub",
    page_icon="\U0001f4c9",
    layout="wide",
)

from nav import render_nav
from shared.styles import apply_styles, render_header, render_footer
from shared.auth_gate import require_login
from shared.ask_question import render_ask_question
from shared.fiscal_selector import render_fiscal_selector
from shared.hierarchy_filter import render_hierarchy_filter, hierarchy_filter_summary
from shared.hourly_charts import render_hourly_analysis
from shared.time_filter import (
    render_time_filter, time_filter_summary, render_quick_period,
)

apply_styles()
user = require_login()
render_nav(8513, auth_token=st.session_state.get("auth_token"))
render_header(
    "Revenue Bridge",
    "**Revenue decomposition & financial trends** | Network and store-level analysis",
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
def query_network_kpis(start, end, store_id=None):
    ts = get_store()
    store_clause = f"AND Store_ID = '{store_id}'" if store_id else ""
    sql = f"""
        SELECT COUNT(DISTINCT Store_ID) AS active_stores,
               SUM(SalesIncGST) AS revenue,
               COUNT(DISTINCT Reference2) AS transactions,
               SUM(CASE WHEN GST = 0 THEN SalesIncGST ELSE 0 END) AS fresh_revenue,
               SUM(CASE WHEN SalesIncGST < 0 THEN ABS(SalesIncGST) ELSE 0 END) AS returns_value
        FROM transactions
        WHERE SaleDate >= CAST(? AS TIMESTAMP)
          AND SaleDate < CAST(? AS TIMESTAMP)
          {store_clause}
    """
    return ts.query(sql, [start, end])


@st.cache_data(ttl=300)
def query_prior_year_revenue(start, end, store_id=None):
    """Get revenue for same period 1 year earlier."""
    ts = get_store()
    store_clause = f"AND Store_ID = '{store_id}'" if store_id else ""
    sql = f"""
        SELECT SUM(SalesIncGST) AS revenue
        FROM transactions
        WHERE SaleDate >= CAST(? AS TIMESTAMP) - INTERVAL '1' YEAR
          AND SaleDate < CAST(? AS TIMESTAMP) - INTERVAL '1' YEAR
          {store_clause}
    """
    return ts.query(sql, [start, end])


# ============================================================================
# SIDEBAR — PRODUCT HIERARCHY FILTERS (shared component)
# ============================================================================

hierarchy = render_hierarchy_filter(key_prefix="rb")
selected_dept_code = hierarchy["dept_code"]
selected_major_code = hierarchy["major_code"]
selected_minor_code = hierarchy["minor_code"]
selected_hfm_item_code = hierarchy["hfm_item_code"]
selected_product_number = hierarchy["product_number"]

# Quick period shortcuts (shared component with QTD)
qp_start, qp_end, qp_label = render_quick_period(key_prefix="rb")


# ============================================================================
# FILTERS (Fiscal Period Selector)
# ============================================================================

filters = render_fiscal_selector(
    key_prefix="rev_bridge",
    show_comparison=True,
    show_store=True,
    store_names=STORE_NAMES,
    allowed_fys=[2024, 2025, 2026],
)

if not filters["start_date"]:
    st.stop()

start_str = filters["start_date"]
end_str = filters["end_date"]

# Override with quick period if selected
if qp_start and qp_end:
    start_str = qp_start
    end_str = qp_end

store_id = filters["store_id"]
store_label = STORE_NAMES.get(store_id, "All Network") if store_id else "All Network"
selected_store = store_id or "28"  # Default Mosman for store-specific queries
compare_mode = "vs Prior Year" if filters.get("comparison") else "None"

# Time dimension filters (sidebar)
time_filters = render_time_filter(key_prefix="rb_time",
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
    kpi_data = query_network_kpis(start_str, end_str, store_id)
    prior_data = query_prior_year_revenue(start_str, end_str, store_id)
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

if not kpi_data:
    st.warning("No data found for this selection.")
    st.stop()

kpi = kpi_data[0]
revenue = kpi["revenue"] or 0
active_stores = kpi["active_stores"] or 0
fresh_rev = kpi["fresh_revenue"] or 0
returns_val = kpi["returns_value"] or 0

prior_rev = prior_data[0]["revenue"] if prior_data and prior_data[0]["revenue"] else 0
yoy_growth = ((revenue - prior_rev) / prior_rev * 100) if prior_rev > 0 else 0
fresh_pct = (fresh_rev / revenue * 100) if revenue > 0 else 0
returns_pct = (returns_val / revenue * 100) if revenue > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Revenue", f"${revenue:,.0f}")
if prior_rev > 0:
    k2.metric("YoY Growth", f"{yoy_growth:+.1f}%",
              delta=f"${revenue - prior_rev:+,.0f}")
else:
    k2.metric("YoY Growth", "N/A", help="No prior year data for comparison")
k3.metric("Active Stores", f"{active_stores}")
k4.metric("Fresh Revenue %", f"{fresh_pct:.1f}%")
k5.metric("Returns %", f"{returns_pct:.2f}%")


# ============================================================================
# TABBED ANALYSIS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Monthly Revenue", "Revenue Decomposition", "Department Breakdown",
    "Store Rankings", "Year-over-Year", "Trading Patterns",
])


# --- Tab 1: Monthly Revenue ---
with tab1:
    st.subheader("Monthly Revenue Trend")

    try:
        if store_id:
            trend = query_named("store_monthly_trend",
                                store_id=store_id, start=start_str, end=end_str)
        else:
            trend = query_named("network_monthly_trend",
                                start=start_str, end=end_str)

        if trend:
            df_trend = pd.DataFrame(trend)
            df_trend["period"] = pd.to_datetime(df_trend["period"])

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_trend["period"], y=df_trend["revenue"],
                name="Revenue", fill="tozeroy",
                line=dict(color="#0d9488", width=2),
                fillcolor="rgba(13, 148, 136, 0.1)",
            ))

            if compare_mode == "vs Prior Year" and "gp" in df_trend.columns:
                fig.add_trace(go.Scatter(
                    x=df_trend["period"], y=df_trend["gp"],
                    name="Est Gross Profit",
                    line=dict(color="#059669", width=2, dash="dot"),
                ))

            fig.update_layout(
                height=450,
                yaxis_title="Amount ($)",
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(fig, key="revbridge_monthly_revenue")

            with st.expander("View monthly data"):
                display_df = df_trend.copy()
                display_df["period"] = display_df["period"].dt.strftime("%Y-%m")
                st.dataframe(display_df, key="revbridge_monthly_data")
        else:
            st.info("No monthly data for this selection.")
    except Exception as e:
        st.error(f"Monthly trend failed: {e}")


# --- Tab 2: Revenue Decomposition ---
with tab2:
    st.subheader("Revenue Decomposition")
    st.caption("Fresh = GST-free (fruit, veg, meat, bread). Packaged = GST items. Returns = negative SalesIncGST.")

    try:
        decomp = query_named("revenue_decomposition_monthly",
                              start=start_str, end=end_str, store_id=store_id)
        if decomp:
            df_decomp = pd.DataFrame(decomp)
            df_decomp["period"] = pd.to_datetime(df_decomp["period"])

            fig_decomp = go.Figure()
            fig_decomp.add_trace(go.Scatter(
                x=df_decomp["period"], y=df_decomp["fresh_revenue"],
                name="Fresh", stackgroup="one",
                line=dict(color="#059669"),
            ))
            fig_decomp.add_trace(go.Scatter(
                x=df_decomp["period"], y=df_decomp["packaged_revenue"],
                name="Packaged", stackgroup="one",
                line=dict(color="#7c3aed"),
            ))
            fig_decomp.add_trace(go.Scatter(
                x=df_decomp["period"], y=df_decomp["returns_value"].abs()
                if hasattr(df_decomp["returns_value"], "abs")
                else [-v for v in df_decomp["returns_value"]],
                name="Returns (abs)",
                line=dict(color="#dc2626", dash="dot"),
            ))
            fig_decomp.update_layout(
                height=450, yaxis_title="Revenue ($)",
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(fig_decomp, key="revbridge_decomposition")

            with st.expander("View decomposition data"):
                st.dataframe(df_decomp, key="revbridge_decomposition_data")
        else:
            st.info("No decomposition data.")
    except Exception as e:
        st.error(f"Revenue decomposition failed: {e}")


# --- Tab 3: Department Breakdown ---
with tab3:
    # Determine hierarchy level for display
    if selected_dept_code and selected_major_code:
        st.subheader("Revenue by Sub-Category")
        try:
            dept_kwargs = {
                "dept_code": selected_dept_code,
                "major_code": selected_major_code,
                "start": start_str, "end": end_str,
            }
            if store_id:
                dept_kwargs["store_id"] = store_id
            dept_data = query_named("minor_group_revenue", **dept_kwargs)
            name_col = "MinorGroupDesc"
        except Exception as e:
            st.error(f"Sub-category breakdown failed: {e}")
            dept_data = []
            name_col = None
    elif selected_dept_code:
        st.subheader("Revenue by Category")
        try:
            dept_kwargs = {
                "dept_code": selected_dept_code,
                "start": start_str, "end": end_str,
            }
            if store_id:
                dept_kwargs["store_id"] = store_id
            dept_data = query_named("major_group_revenue", **dept_kwargs)
            name_col = "MajorGroupDesc"
        except Exception as e:
            st.error(f"Category breakdown failed: {e}")
            dept_data = []
            name_col = None
    else:
        st.subheader("Revenue by Department")
        try:
            dept_kwargs = {"start": start_str, "end": end_str}
            if store_id:
                dept_kwargs["store_id"] = store_id
            dept_data = query_named("department_revenue", **dept_kwargs)
            name_col = "DepartmentDesc"
        except Exception as e:
            st.error(f"Department breakdown failed: {e}")
            dept_data = []
            name_col = None

    if dept_data and name_col:
        df_dept = pd.DataFrame(dept_data)

        fig_dept = px.bar(
            df_dept.sort_values("revenue"),
            x="revenue", y=name_col,
            orientation="h",
            color="revenue",
            color_continuous_scale=["#dbeafe", "#1e3a8a"],
            labels={"revenue": "Revenue ($)", name_col: ""},
        )
        fig_dept.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig_dept, key="revbridge_dept_breakdown")

        # Department monthly trend (only for department-level)
        if not selected_dept_code:
            try:
                trend_kwargs = {"start": start_str, "end": end_str}
                if store_id:
                    trend_kwargs["store_id"] = store_id
                dept_trend = query_named("department_monthly_trend", **trend_kwargs)
                if dept_trend:
                    df_dt = pd.DataFrame(dept_trend)
                    df_dt["period"] = pd.to_datetime(df_dt["period"])
                    fig_dt = px.area(
                        df_dt, x="period", y="revenue", color="DepartmentDesc",
                        labels={"period": "Month", "revenue": "Revenue ($)",
                                "DepartmentDesc": "Department"},
                    )
                    fig_dt.update_layout(height=400)
                    st.plotly_chart(fig_dt, key="revbridge_dept_monthly_trend")
            except Exception as e:
                st.error(f"Department trend failed: {e}")

        with st.expander("Detail table"):
            display_cols = [name_col, "revenue"]
            if "gp" in df_dept.columns:
                display_cols.append("gp")
            if "transactions" in df_dept.columns:
                display_cols.append("transactions")
            if "unique_skus" in df_dept.columns:
                display_cols.append("unique_skus")
            fmt = {"revenue": "${:,.0f}"}
            if "gp" in df_dept.columns:
                fmt["gp"] = "${:,.0f}"
            if "transactions" in df_dept.columns:
                fmt["transactions"] = "{:,.0f}"
            st.dataframe(
                df_dept[display_cols].style.format(fmt),
                key="revbridge_dept_detail_table",
            )

        st.caption(
            "Hierarchy breakdown uses the 72,911-product hierarchy. "
            "1.7% of PLUs are unmatched and excluded from totals."
        )
    else:
        st.info("No data available for this selection.")


# --- Tab 4: Store Rankings ---
with tab4:
    st.subheader("Store Revenue Rankings")

    try:
        stores = query_named("store_comparison_period",
                              start=start_str, end=end_str)
        if stores:
            df_stores = pd.DataFrame(stores)
            df_stores["store_name"] = df_stores["store_id"].apply(
                lambda x: STORE_NAMES.get(str(x), str(x)))

            fig_rank = px.bar(
                df_stores.sort_values("revenue", ascending=True),
                x="revenue", y="store_name", orientation="h",
                labels={"revenue": "Revenue ($)", "store_name": "Store"},
                color="revenue",
                color_continuous_scale=["#ccfbf1", "#0d9488"],
            )
            fig_rank.update_layout(
                height=max(400, 25 * len(df_stores)),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_rank, key="revbridge_store_rankings")

            with st.expander("View store data"):
                st.dataframe(
                    df_stores[["store_name", "revenue", "transactions",
                               "line_items", "gp"]].style.format({
                        "revenue": "${:,.0f}",
                        "transactions": "{:,}",
                        "line_items": "{:,}",
                        "gp": "${:,.0f}",
                    }),
                    key="revbridge_store_data",
                )
        else:
            st.info("No store comparison data.")
    except Exception as e:
        st.error(f"Store ranking failed: {e}")


# --- Tab 5: Year-over-Year (Fiscal) ---
with tab5:
    st.subheader("Year-over-Year Comparison (Fiscal Months)")
    st.caption("Compares fiscal months (5-4-4 calendar) for apples-to-apples YoY analysis.")

    yoy_fy = filters["fin_year"] or 2026
    yoy_prior = yoy_fy - 1
    yoy_store_id = store_id or "28"
    yoy_store_name = STORE_NAMES.get(yoy_store_id, yoy_store_id)
    st.caption(f"Showing: {yoy_store_name} | FY{yoy_fy} vs FY{yoy_prior}")

    try:
        yoy = query_named("fiscal_yoy_monthly",
                          fin_year=yoy_fy, fin_year_2=yoy_prior,
                          store_id=yoy_store_id)
        if yoy:
            df_yoy = pd.DataFrame(yoy)
            df_yoy["FinYear"] = df_yoy["FinYear"].astype(str)

            fig_yoy = px.bar(
                df_yoy, x="month_name", y="revenue", color="FinYear",
                barmode="group",
                labels={"month_name": "Fiscal Month", "revenue": "Revenue ($)",
                        "FinYear": "Fiscal Year"},
                color_discrete_sequence=["#94a3b8", "#0d9488"],
            )
            fig_yoy.update_layout(height=450)
            st.plotly_chart(fig_yoy, key="revbridge_yoy_comparison")

            # Pivot table
            pivot = df_yoy.pivot_table(
                index="month_name", columns="FinYear",
                values="revenue", aggfunc="sum"
            )
            with st.expander("View YoY data table"):
                st.dataframe(
                    pivot.style.format("${:,.0f}"),
                    key="revbridge_yoy_data",
                )
        else:
            st.info("No year-over-year data for this selection.")
    except Exception as e:
        st.error(f"YoY comparison failed: {e}")


# --- Tab 6: Trading Patterns (shared component) ---
with tab6:
    st.subheader(f"Trading Patterns — {store_label}")
    render_hourly_analysis(query_named, selected_store, start_str, end_str,
                           key_prefix="rb", hierarchy=hierarchy,
                           time_filters=time_filters)


# ============================================================================
# ASK A QUESTION
# ============================================================================

render_ask_question("revenue_bridge")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(
    "Data: 383M POS transactions from Microsoft Fabric (Jul 2023 - Feb 2026) | "
    "COGS 24% null in FY24 (GP estimates less reliable for FY24) | "
    "Category: GST=0 (Fresh) vs GST>0 (Packaged)"
)

render_footer("Revenue Bridge", user=user)
