"""
Harris Farm Hub — Buying Hub Dashboard
Category & buyer intelligence powered by the full 72,911-product hierarchy
joined to 383M POS transactions via DuckDB.
Hierarchy: Department (9) → Major Group (30) → Minor Group (405) → HFM Item → SKU.
Data source: Microsoft Fabric retail fact_pos_sales + Product Hierarchy 20260215.xlsx.
"""

from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

from transaction_layer import TransactionStore, STORE_NAMES
from transaction_queries import run_query
from product_hierarchy import (
    get_departments, get_major_groups, get_minor_groups,
    hierarchy_stats, load_hierarchy,
)

from shared.styles import render_header, render_footer
from shared.ask_question import render_ask_question
from shared.voice_realtime import render_voice_data_box
from shared.fiscal_selector import render_fiscal_selector
from shared.hierarchy_filter import render_hierarchy_filter, hierarchy_filter_summary
from shared.hourly_charts import render_hourly_analysis
from shared.time_filter import (
    render_time_filter, time_filter_summary, render_quick_period,
)

user = st.session_state.get("auth_user")
render_header(
    "Buying Hub",
    "**Category & buyer intelligence** | 72,911 products across 9 departments",
    goals=["G2", "G4"],
    strategy_context="Smarter buying decisions start here — the supply chain from pay to purchase.",
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


# ============================================================================
# SIDEBAR — PRODUCT HIERARCHY FILTERS (shared component)
# ============================================================================

hierarchy = render_hierarchy_filter(key_prefix="bh")
selected_dept_code = hierarchy["dept_code"]
selected_major_code = hierarchy["major_code"]
selected_minor_code = hierarchy["minor_code"]
selected_hfm_item_code = hierarchy["hfm_item_code"]
selected_product_number = hierarchy["product_number"]

# Quick period shortcuts (shared component with QTD)
qp_start, qp_end, qp_label = render_quick_period(key_prefix="bh")


# ============================================================================
# FILTERS (Fiscal Period Selector)
# ============================================================================

filters = render_fiscal_selector(
    key_prefix="buying_hub",
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

# Time dimension filters (sidebar)
time_filters = render_time_filter(key_prefix="bh_time",
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
# TABBED ANALYSIS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Department Overview", "Category Drill-Down",
    "Buyer Dashboard", "Range Review", "Trading Patterns",
])


# --- Tab 1: Department Overview ---
with tab1:
    # Adapt view to hierarchy level
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
            dept_name_col = "MinorGroupDesc"
        except Exception as e:
            st.error(f"Failed to load sub-category data: {e}")
            dept_data = []
            dept_name_col = None
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
            dept_name_col = "MajorGroupDesc"
        except Exception as e:
            st.error(f"Failed to load category data: {e}")
            dept_data = []
            dept_name_col = None
    else:
        st.subheader("Revenue by Department")
        dept_name_col = "DepartmentDesc"
        try:
            dept_kwargs = {"start": start_str, "end": end_str}
            if store_id:
                dept_kwargs["store_id"] = store_id
            dept_data = query_named("department_revenue", **dept_kwargs)
        except Exception as e:
            st.error(f"Failed to load department data: {e}")
            dept_data = []

    if dept_data:
        df_dept = pd.DataFrame(dept_data)
        total_rev = df_dept["revenue"].sum()

        # KPI row
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Revenue", f"${total_rev:,.0f}")
        k2.metric("Departments", len(df_dept))
        k3.metric("Total SKUs Sold", f"{df_dept['unique_skus'].sum():,}")
        gp_total = df_dept["gp"].sum()
        gp_pct = (gp_total / total_rev * 100) if total_rev > 0 else 0
        k4.metric("Est GP%", f"{gp_pct:.1f}%")

        col_tree, col_bar = st.columns([1, 1])

        with col_tree:
            st.markdown("**Revenue Share (Treemap)**")
            df_dept["item_label"] = df_dept[dept_name_col].str.replace(
                r"^\d+ - ", "", regex=True)
            df_dept["revenue_label"] = df_dept["revenue"].apply(
                lambda x: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K")
            custom_cols = ["revenue_label"]
            text_tpl = "<b>%{label}</b><br>%{customdata[0]}"
            if "unique_skus" in df_dept.columns:
                custom_cols.append("unique_skus")
                text_tpl += "<br>%{customdata[1]} SKUs"
            fig_tree = px.treemap(
                df_dept,
                path=["item_label"],
                values="revenue",
                color="revenue",
                color_continuous_scale=["#ccfbf1", "#0d9488"],
                custom_data=custom_cols,
            )
            fig_tree.update_traces(texttemplate=text_tpl)
            fig_tree.update_layout(height=450, coloraxis_showscale=False)
            st.plotly_chart(fig_tree, key="buying_revenue_treemap")

        with col_bar:
            st.markdown(f"**Revenue by {dept_name_col.replace('Desc', '')}**")
            fig_bar = px.bar(
                df_dept.sort_values("revenue"),
                x="revenue", y=dept_name_col,
                orientation="h",
                color="revenue",
                color_continuous_scale=["#ccfbf1", "#0d9488"],
                labels={"revenue": "Revenue ($)", dept_name_col: ""},
            )
            fig_bar.update_layout(height=450, showlegend=False,
                                  coloraxis_showscale=False)
            st.plotly_chart(fig_bar, key="buying_revenue_bar")

        with st.expander("Detail table"):
            detail_cols = [dept_name_col, "revenue"]
            fmt = {"revenue": "${:,.0f}"}
            if "gp" in df_dept.columns:
                detail_cols.append("gp")
                fmt["gp"] = "${:,.0f}"
            if "transactions" in df_dept.columns:
                detail_cols.append("transactions")
                fmt["transactions"] = "{:,.0f}"
            if "unique_skus" in df_dept.columns:
                detail_cols.append("unique_skus")
            display_df = df_dept[detail_cols].copy()
            if "gp" in display_df.columns and "revenue" in display_df.columns:
                display_df["gp_pct"] = (display_df["gp"] / display_df["revenue"] * 100).round(1)
                fmt["gp_pct"] = "{:.1f}%"
            display_df["revenue_share"] = (display_df["revenue"] / total_rev * 100).round(1)
            fmt["revenue_share"] = "{:.1f}%"
            st.dataframe(
                display_df.style.format(fmt),
                key="buying_dept_detail_table",
            )

        st.caption(
            "1.7% of PLUs (304) are unmatched to the hierarchy and excluded "
            "from totals. See hierarchy stats for details."
        )
    else:
        st.info("No department data available for this selection.")


# --- Tab 2: Category Drill-Down ---
with tab2:
    st.subheader("Category Drill-Down")

    hierarchy_depts = get_departments()
    dept_options = {d["code"]: d["name"] for d in hierarchy_depts}

    selected_dept = st.selectbox(
        "Department",
        options=list(dept_options.keys()),
        format_func=lambda x: dept_options[x],
        key="drill_dept",
    )

    # Major groups for selected department
    st.markdown(f"### Major Groups — {dept_options[selected_dept]}")

    try:
        mg_kwargs = {"dept_code": selected_dept, "start": start_str, "end": end_str}
        if store_id:
            mg_kwargs["store_id"] = store_id
        mg_data = query_named("major_group_revenue", **mg_kwargs)
    except Exception as e:
        st.error(f"Failed to load major groups: {e}")
        mg_data = []

    if mg_data:
        df_mg = pd.DataFrame(mg_data)
        fig_mg = px.bar(
            df_mg, x="MajorGroupDesc", y="revenue",
            color="revenue",
            color_continuous_scale=["#ccfbf1", "#0d9488"],
            labels={"MajorGroupDesc": "Major Group", "revenue": "Revenue ($)"},
        )
        fig_mg.update_layout(height=350, coloraxis_showscale=False)
        st.plotly_chart(fig_mg, key="buying_major_group_bar")

        # Select major group for minor drill-down
        mg_options = {r["MajorGroupCode"]: r["MajorGroupDesc"] for r in mg_data}
        selected_mg = st.selectbox(
            "Select Major Group to drill into",
            options=list(mg_options.keys()),
            format_func=lambda x: mg_options[x],
            key="drill_mg",
        )

        # Minor groups
        st.markdown(f"### Minor Groups — {mg_options[selected_mg]}")

        try:
            minor_kwargs = {
                "dept_code": selected_dept, "major_code": selected_mg,
                "start": start_str, "end": end_str,
            }
            if store_id:
                minor_kwargs["store_id"] = store_id
            minor_data = query_named("minor_group_revenue", **minor_kwargs)
        except Exception as e:
            st.error(f"Failed to load minor groups: {e}")
            minor_data = []

        if minor_data:
            df_minor = pd.DataFrame(minor_data)
            st.dataframe(
                df_minor.style.format({
                    "revenue": "${:,.0f}",
                }),
                key="buying_minor_group_table",
            )

        # Top items in this department
        st.markdown(f"### Top Items — {dept_options[selected_dept]}")

        try:
            items_kwargs = {
                "dept_code": selected_dept,
                "start": start_str, "end": end_str,
                "limit": 20,
            }
            if store_id:
                items_kwargs["store_id"] = store_id
            items_data = query_named("top_items_by_department", **items_kwargs)
        except Exception as e:
            st.error(f"Failed to load top items: {e}")
            items_data = []

        if items_data:
            df_items = pd.DataFrame(items_data)
            st.dataframe(
                df_items[["PLUItem_ID", "ProductName", "MajorGroupDesc",
                           "MinorGroupDesc", "revenue", "total_qty",
                           "transaction_count"]]
                .style.format({
                    "revenue": "${:,.0f}",
                    "total_qty": "{:,.0f}",
                    "transaction_count": "{:,.0f}",
                }),
                key="buying_top_items_table",
            )
    else:
        st.info("No major group data available for this department and date range.")


# --- Tab 3: Buyer Dashboard ---
with tab3:
    st.subheader("Revenue by Buyer")
    st.caption(
        "BuyerId is a code from the product hierarchy (e.g., TWHITE, TOM). "
        "No buyer name mapping is available in the source data."
    )

    try:
        buyer_kwargs = {"start": start_str, "end": end_str}
        if store_id:
            buyer_kwargs["store_id"] = store_id
        buyer_data = query_named("buyer_performance", **buyer_kwargs)
    except Exception as e:
        st.error(f"Failed to load buyer data: {e}")
        buyer_data = []

    if buyer_data:
        df_buyer = pd.DataFrame(buyer_data)

        # KPIs
        b1, b2, b3 = st.columns(3)
        b1.metric("Unique Buyers", len(df_buyer))
        b2.metric("Total Revenue", f"${df_buyer['revenue'].sum():,.0f}")
        b3.metric("Total SKUs", f"{df_buyer['unique_skus'].sum():,}")

        col_chart, col_table = st.columns([1, 1])

        with col_chart:
            top_buyers = df_buyer.head(15)
            fig_buyer = px.bar(
                top_buyers.sort_values("revenue"),
                x="revenue", y="BuyerId",
                orientation="h",
                color="revenue",
                color_continuous_scale=["#dbeafe", "#1e3a8a"],
                labels={"revenue": "Revenue ($)", "BuyerId": "Buyer"},
            )
            fig_buyer.update_layout(height=450, coloraxis_showscale=False)
            st.plotly_chart(fig_buyer, key="buying_buyer_bar")

        with col_table:
            st.dataframe(
                df_buyer[["BuyerId", "departments", "unique_skus",
                           "revenue", "gp", "transactions"]]
                .style.format({
                    "revenue": "${:,.0f}",
                    "gp": "${:,.0f}",
                    "transactions": "{:,.0f}",
                }),
                height=450,
                key="buying_buyer_table",
            )
    else:
        st.info("No buyer data available for this selection.")


# --- Tab 4: Range Review ---
with tab4:
    st.subheader("Product Range & Lifecycle")

    h_stats = hierarchy_stats()
    if h_stats.get("available"):
        # Overall stats
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Total Products", f"{h_stats['total_products']:,}")
        lifecycle = h_stats.get("lifecycle", {})
        r2.metric("Active", f"{lifecycle.get('Active', 0):,}")
        r3.metric("Deleted", f"{lifecycle.get('Deleted', 0):,}")
        r4.metric("New/Inactive + Derange",
                   f"{lifecycle.get('New/Inactive', 0) + lifecycle.get('Derange', 0):,}")

        # Lifecycle by department
        st.markdown("### Lifecycle by Department")

        df_h = load_hierarchy()
        if not df_h.empty:
            lifecycle_dept = df_h.groupby(
                ["DepartmentDesc", "ProductLifecycleStateId"]
            ).size().reset_index(name="count")

            fig_lifecycle = px.bar(
                lifecycle_dept,
                x="DepartmentDesc", y="count",
                color="ProductLifecycleStateId",
                barmode="stack",
                color_discrete_map={
                    "Active": "#059669",
                    "Deleted": "#dc2626",
                    "New/Inactive": "#f59e0b",
                    "Derange": "#6b7280",
                },
                labels={
                    "DepartmentDesc": "Department",
                    "count": "Products",
                    "ProductLifecycleStateId": "Lifecycle",
                },
            )
            fig_lifecycle.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_lifecycle, key="buying_lifecycle_bar")

            # Active range by department
            st.markdown("### Active Range by Department")
            active_df = df_h[df_h["ProductLifecycleStateId"] == "Active"]
            active_dept = active_df.groupby("DepartmentDesc").agg(
                active_skus=("ProductNumber", "count"),
                major_groups=("MajorGroupDesc", "nunique"),
                minor_groups=("MinorGroupDesc", "nunique"),
            ).reset_index().sort_values("active_skus", ascending=False)

            st.dataframe(active_dept, key="buying_active_range_table")
    else:
        st.warning("Product hierarchy not available.")


# --- Tab 5: Trading Patterns (shared component) ---
with tab5:
    st.subheader(f"Trading Patterns — {store_label}")
    render_hourly_analysis(query_named, selected_store, start_str, end_str,
                           key_prefix="bh", hierarchy=hierarchy,
                           time_filters=time_filters)


# ============================================================================
# ASK A QUESTION
# ============================================================================

render_voice_data_box("buying_hub")
render_ask_question("buying_hub")

# ============================================================================
# DATA SOURCE NOTES
# ============================================================================

st.markdown("---")
st.caption(
    "Data: 383M POS transactions (Jul 2023 - Feb 2026) joined to 72,911-product "
    "hierarchy | 98.3% PLU match rate (98.4% by revenue) | "
    "BuyerId codes only — no supplier or buyer name mapping"
)

render_footer("Buying Hub", user=user)
