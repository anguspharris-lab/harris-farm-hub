"""
Harris Farm Hub — Customer Analytics Dashboard
Analyses customer counts, channel mix, RFM segmentation, cohort retention,
lifetime value, and basket composition.
Port 8507.

Data sources:
  - SQLite customers table: store x channel x measure x week (17K rows)
  - DuckDB transactions: 383M POS rows, ~12% with loyalty CustomerCode
"""

import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, date

from transaction_layer import TransactionStore, STORE_NAMES
from transaction_queries import run_query

from shared.styles import render_header, render_footer
from shared.ask_question import render_ask_question
from shared.fiscal_selector import render_fiscal_selector
from shared.time_filter import render_time_filter, time_filter_summary, render_quick_period

user = st.session_state.get("auth_user")

render_header(
    "Customer Analytics",
    "**Harris Farm Markets** | Customer intelligence, segmentation & retention",
)


# ============================================================================
# DATA LOADING — SQLite (aggregate counts)
# ============================================================================

def _get_db_path():
    return Path(__file__).resolve().parent.parent / "data" / "harris_farm.db"


def store_display_name(full_name):
    """'10 - HFM Pennant Hills' -> 'Pennant Hills'"""
    if " - HFM " in full_name:
        return full_name.split(" - HFM ", 1)[1]
    if " - " in full_name:
        return full_name.split(" - ", 1)[1]
    return full_name


@st.cache_data(ttl=300)
def load_customer_data(date_from, date_to, stores=None, channel=None):
    """Load customer data from SQLite, pivoted to wide format."""
    db = _get_db_path()
    if not db.exists():
        return pd.DataFrame()

    query = """
        SELECT store, channel, measure, week_ending, value
        FROM customers
        WHERE week_ending >= ? AND week_ending <= ?
    """
    params = [date_from, date_to]

    if stores:
        placeholders = ",".join("?" * len(stores))
        query += " AND store IN ({})".format(placeholders)
        params.extend(stores)

    if channel:
        query += " AND channel = ?"
        params.append(channel)

    with sqlite3.connect(str(db)) as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if df.empty:
        return df

    df["week_ending"] = pd.to_datetime(df["week_ending"])
    df["store_short"] = df["store"].apply(store_display_name)
    return df


@st.cache_data(ttl=300)
def get_store_list():
    db = _get_db_path()
    if not db.exists():
        return []
    with sqlite3.connect(str(db)) as conn:
        rows = conn.execute(
            "SELECT DISTINCT store FROM customers ORDER BY store"
        ).fetchall()
    return [r[0] for r in rows]


@st.cache_data(ttl=300)
def get_date_range():
    db = _get_db_path()
    with sqlite3.connect(str(db)) as conn:
        row = conn.execute(
            "SELECT MIN(week_ending), MAX(week_ending) FROM customers"
        ).fetchone()
    return row


# ============================================================================
# DATA LOADING — DuckDB (transaction-level)
# ============================================================================

@st.cache_resource
def get_store():
    """Initialise TransactionStore (cached across reruns)."""
    return TransactionStore()


@st.cache_data(ttl=300, show_spinner="Querying transactions...")
def query_named(name, **kwargs):
    ts = get_store()
    return run_query(ts, name, **kwargs)


# ============================================================================
# BRAND COLORS
# ============================================================================

COLORS = {
    "green": "#2d8659",
    "dark_blue": "#1e3a8a",
    "purple": "#7c3aed",
    "teal": "#0d9488",
    "amber": "#d97706",
    "red": "#dc2626",
}

SEGMENT_COLORS = {
    "Champion": "#059669",
    "High-Value": "#0d9488",
    "Regular": "#3b82f6",
    "Occasional": "#f59e0b",
    "Lapsed": "#ef4444",
}


# ============================================================================
# FILTERS — Fiscal Period Selector (matching Store Operations dashboard)
# ============================================================================

# Floor: no data before July 2024 (FY25 baseline)
DATA_START = "2024-07-01"

# Quick period shortcuts (sidebar: Today / WTD / MTD / QTD / YTD)
qp_start, qp_end, qp_label = render_quick_period(key_prefix="ca")

# Main fiscal selector (FY, Period Type, Store)
filters = render_fiscal_selector(
    key_prefix="ca",
    show_store=True,
    show_comparison=False,
    store_names=STORE_NAMES,
    allowed_fys=[2025, 2026],
)

if not filters["start_date"]:
    st.stop()

date_from = filters["start_date"]
date_to = filters["end_date"]
period_label = filters.get("period_label", "")

# Override with quick period if selected
if qp_start and qp_end:
    date_from = qp_start
    date_to = qp_end
    period_label = qp_label

# Enforce July 2024 floor
if date_from < DATA_START:
    date_from = DATA_START

# Time dimension filters (sidebar: Season, Quarter, Month)
time_filters = render_time_filter(key_prefix="ca_time",
                                  fin_year=filters.get("fin_year"))
time_label = time_filter_summary(time_filters)

# SQLite store filter — map DuckDB store_id to SQLite store names
selected_store_id = filters.get("store_id")
selected_stores = None
if selected_store_id:
    all_stores = get_store_list()
    matched = [s for s in all_stores
               if s.startswith("{} ".format(selected_store_id))]
    if matched:
        selected_stores = matched

# Channel filter (sidebar, below time filters)
channel_filter = st.sidebar.selectbox("Channel", ["All", "Retail", "Online"],
                                       key="ca_channel")
channel_arg = None if channel_filter == "All" else channel_filter
st.sidebar.markdown("---")

# Transaction date range (for DuckDB queries)
txn_start = date_from
txn_end = date_to


# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Known Customers",
    "Channel Analysis",
    "Cohort & Retention",
])


# ============================================================================
# TAB 1: OVERVIEW (existing functionality)
# ============================================================================

with tab1:
    df = load_customer_data(date_from, date_to, stores=selected_stores,
                            channel=channel_arg)

    if df.empty:
        st.warning("No customer data found for the selected filters.")
    else:
        # KPIs
        retail_customers = df[
            (df["measure"] == "Customer Count") & (df["channel"] == "Retail")
        ]["value"].sum()
        online_customers = df[
            (df["measure"] == "Customer Count") & (df["channel"] == "Online")
        ]["value"].sum()
        total_customers = retail_customers + online_customers
        budget_total = df[df["measure"] == "Budget Customers"]["value"].sum()
        budget_var = (
            (total_customers - budget_total) / budget_total * 100
        ) if budget_total > 0 else 0
        online_pct = (
            online_customers / total_customers * 100
        ) if total_customers > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Customers", "{:,.0f}".format(total_customers))
        k2.metric("Retail", "{:,.0f}".format(retail_customers))
        k3.metric("Online", "{:,.0f}".format(online_customers),
                   "{:.1f}% of total".format(online_pct))
        k4.metric("Budget Variance", "{:+.1f}%".format(budget_var))

        # Weekly Trend
        st.subheader("Weekly Customer Trend")
        trend = df[df["measure"] == "Customer Count"].groupby(
            ["week_ending", "channel"]
        )["value"].sum().reset_index()

        if trend.empty:
            st.info("No weekly trend data for the selected period.")
        else:
            fig_trend = px.line(
                trend, x="week_ending", y="value", color="channel",
                labels={"week_ending": "Week Ending", "value": "Customers",
                        "channel": "Channel"},
                color_discrete_map={"Retail": COLORS["dark_blue"],
                                    "Online": COLORS["purple"]},
            )

            budget_trend = df[df["measure"] == "Budget Customers"].groupby(
                "week_ending"
            )["value"].sum().reset_index()
            if not budget_trend.empty:
                fig_trend.add_trace(go.Scatter(
                    x=budget_trend["week_ending"], y=budget_trend["value"],
                    mode="lines", name="Budget",
                    line=dict(color=COLORS["amber"], dash="dash", width=1),
                ))

            fig_trend.update_layout(height=400,
                                    legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig_trend, use_container_width=True,
                            key="customer_weekly_trend")

        # Store Comparison
        st.subheader("Customers by Store")
        store_totals = df[df["measure"] == "Customer Count"].groupby(
            "store_short"
        )["value"].sum().sort_values(ascending=True).reset_index()

        if not store_totals.empty:
            fig_stores = px.bar(
                store_totals, x="value", y="store_short", orientation="h",
                labels={"value": "Total Customers", "store_short": ""},
                color_discrete_sequence=[COLORS["green"]],
            )
            fig_stores.update_layout(
                height=max(400, len(store_totals) * 25))
            st.plotly_chart(fig_stores, use_container_width=True,
                            key="customer_by_store")

        # Channel Split by Store
        st.subheader("Retail vs Online by Store")
        channel_by_store = df[df["measure"] == "Customer Count"].groupby(
            ["store_short", "channel"]
        )["value"].sum().reset_index()

        if not channel_by_store.empty:
            fig_channel = px.bar(
                channel_by_store, x="value", y="store_short", color="channel",
                orientation="h", barmode="stack",
                labels={"value": "Customers", "store_short": "",
                        "channel": "Channel"},
                color_discrete_map={"Retail": COLORS["dark_blue"],
                                    "Online": COLORS["purple"]},
            )
            fig_channel.update_layout(
                height=max(400, len(store_totals) * 25))
            st.plotly_chart(fig_channel, use_container_width=True,
                            key="customer_channel_split")

        # Budget Variance by Store
        st.subheader("Budget Variance by Store")
        actual_by_store = df[df["measure"] == "Customer Count"].groupby(
            "store_short"
        )["value"].sum()
        budget_by_store = df[df["measure"] == "Budget Customers"].groupby(
            "store_short"
        )["value"].sum()
        variance_df = pd.DataFrame({
            "Actual": actual_by_store,
            "Budget": budget_by_store,
        }).dropna()

        if not variance_df.empty:
            variance_df["Variance %"] = (
                (variance_df["Actual"] - variance_df["Budget"])
                / variance_df["Budget"] * 100
            )
            variance_df = variance_df.sort_values("Variance %")
            fig_var = px.bar(
                variance_df.reset_index(), x="Variance %", y="store_short",
                orientation="h",
                labels={"store_short": "",
                        "Variance %": "Variance vs Budget (%)"},
                color="Variance %",
                color_continuous_scale=["#dc2626", "#fbbf24", "#059669"],
                color_continuous_midpoint=0,
            )
            fig_var.update_layout(
                height=max(400, len(variance_df) * 25))
            st.plotly_chart(fig_var, use_container_width=True,
                            key="customer_budget_variance")

        # Detail Table
        with st.expander("Detailed Data Table"):
            detail = df[df["measure"] == "Customer Count"].pivot_table(
                index=["store_short", "channel"],
                columns=pd.Grouper(key="week_ending", freq="4W"),
                values="value",
                aggfunc="sum",
            )
            if not detail.empty:
                detail.columns = [c.strftime("%d %b %Y")
                                  for c in detail.columns]
                st.dataframe(detail.style.format("{:,.0f}"),
                             key="customer_detail_table")


# ============================================================================
# TAB 2: KNOWN CUSTOMERS — RFM, LTV, Frequency
# ============================================================================

with tab2:
    st.subheader("Loyalty Customer Intelligence")
    st.caption(
        "Analysis of identified customers (~12% of transactions have "
        "loyalty codes). Despite the small subset, these represent "
        "high-engagement shoppers with rich behavioural data."
    )

    try:
        rfm_data = query_named("customer_rfm_segments",
                               start=txn_start, end=txn_end)
    except Exception as e:
        st.error("Could not load customer data: {}".format(e))
        rfm_data = []

    if not rfm_data:
        st.info("No loyalty customer data available for the selected period.")
    else:
        df_rfm = pd.DataFrame(rfm_data)

        # --- KPI Row ---
        total_identified = len(df_rfm)
        avg_ltv = df_rfm["monetary"].mean()
        avg_freq = df_rfm["frequency"].mean()
        multi_store = (df_rfm["stores_visited"] >= 2).sum()
        multi_store_pct = multi_store / total_identified * 100

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Identified Customers", "{:,}".format(total_identified))
        k2.metric("Avg Lifetime Value", "${:,.0f}".format(avg_ltv))
        k3.metric("Avg Visit Frequency", "{:.1f} visits".format(avg_freq))
        k4.metric("Multi-Store Shoppers",
                   "{:.1f}%".format(multi_store_pct))

        # --- RFM Segmentation ---
        st.markdown("---")
        st.subheader("Customer Segmentation (RFM)")

        seg_summary = df_rfm.groupby("segment").agg(
            customers=("CustomerCode", "count"),
            avg_spend=("monetary", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_recency=("recency_days", "mean"),
            total_revenue=("monetary", "sum"),
        ).reset_index()

        seg_order = ["Champion", "High-Value", "Regular",
                     "Occasional", "Lapsed"]
        # Sort by defined order (without pd.Categorical which crashes plotly)
        order_map = {s: i for i, s in enumerate(seg_order)}
        seg_summary["_order"] = seg_summary["segment"].map(order_map).fillna(99)
        seg_summary = seg_summary.sort_values("_order").drop(columns=["_order"])

        fig_seg = px.bar(
            seg_summary, x="customers", y="segment", orientation="h",
            color="segment",
            color_discrete_map=SEGMENT_COLORS,
            labels={"customers": "Customer Count", "segment": ""},
            text="customers",
        )
        fig_seg.update_layout(height=300, showlegend=False)
        fig_seg.update_traces(textposition="outside")
        st.plotly_chart(fig_seg, use_container_width=True,
                        key="rfm_segments")

        # Segment stats table
        seg_display = seg_summary.copy()
        seg_display.columns = [
            "Segment", "Customers", "Avg Spend ($)",
            "Avg Frequency", "Avg Recency (days)", "Total Revenue ($)",
        ]
        seg_display["Avg Spend ($)"] = seg_display["Avg Spend ($)"].apply(
            lambda x: "${:,.0f}".format(x))
        seg_display["Total Revenue ($)"] = seg_display[
            "Total Revenue ($)"].apply(lambda x: "${:,.0f}".format(x))
        seg_display["Avg Frequency"] = seg_display["Avg Frequency"].apply(
            lambda x: "{:.1f}".format(x))
        seg_display["Avg Recency (days)"] = seg_display[
            "Avg Recency (days)"].apply(lambda x: "{:.0f}".format(x))
        st.dataframe(seg_display, hide_index=True, use_container_width=True,
                     key="seg_stats_table")

        # --- Purchase Frequency Histogram ---
        st.markdown("---")
        st.subheader("Purchase Frequency Distribution")

        try:
            freq_data = query_named("customer_frequency_distribution",
                                    start=txn_start, end=txn_end)
            if freq_data:
                df_freq = pd.DataFrame(freq_data)
                fig_freq = px.bar(
                    df_freq, x="frequency_bucket", y="customer_count",
                    color_discrete_sequence=[COLORS["green"]],
                    labels={"frequency_bucket": "Visit Frequency",
                            "customer_count": "Customers"},
                    text="customer_count",
                )
                fig_freq.update_layout(height=350)
                fig_freq.update_traces(textposition="outside")
                st.plotly_chart(fig_freq, use_container_width=True,
                                key="freq_histogram")
        except Exception:
            st.info("Frequency distribution data unavailable.")

        # --- Lifetime Value Tiers ---
        st.markdown("---")
        st.subheader("Lifetime Value Tiers")

        try:
            ltv_data = query_named("customer_ltv_tiers",
                                   start=txn_start, end=txn_end)
            if ltv_data:
                df_ltv = pd.DataFrame(ltv_data)

                ltv_colors = ["#059669", "#0d9488", "#3b82f6",
                              "#f59e0b", "#94a3b8"]
                fig_ltv = px.bar(
                    df_ltv, x="customer_count", y="ltv_tier",
                    orientation="h",
                    color="ltv_tier",
                    color_discrete_sequence=ltv_colors,
                    labels={"customer_count": "Customers",
                            "ltv_tier": ""},
                    text="customer_count",
                )
                fig_ltv.update_layout(height=300, showlegend=False)
                fig_ltv.update_traces(textposition="outside")
                st.plotly_chart(fig_ltv, use_container_width=True,
                                key="ltv_tiers")

                # LTV stats table
                ltv_display = df_ltv[["ltv_tier", "customer_count",
                                      "avg_spend", "avg_visits",
                                      "avg_tenure_months",
                                      "projected_annual"]].copy()
                ltv_display.columns = [
                    "Tier", "Customers", "Avg Spend ($)",
                    "Avg Visits", "Avg Tenure (months)",
                    "Projected Annual ($)",
                ]
                ltv_display["Avg Spend ($)"] = ltv_display[
                    "Avg Spend ($)"].apply(
                    lambda x: "${:,.0f}".format(x))
                ltv_display["Projected Annual ($)"] = ltv_display[
                    "Projected Annual ($)"].apply(
                    lambda x: "${:,.0f}".format(x))
                ltv_display["Avg Visits"] = ltv_display[
                    "Avg Visits"].apply(lambda x: "{:.1f}".format(x))
                ltv_display["Avg Tenure (months)"] = ltv_display[
                    "Avg Tenure (months)"].apply(
                    lambda x: "{:.1f}".format(x))
                st.dataframe(ltv_display, hide_index=True,
                             use_container_width=True,
                             key="ltv_stats_table")
        except Exception:
            st.info("Lifetime value data unavailable.")

        # --- Top 20 Customers ---
        st.markdown("---")
        st.subheader("Top 20 Customers by Spend")

        top_20 = df_rfm.head(20)[
            ["CustomerCode", "segment", "monetary", "frequency",
             "stores_visited", "first_purchase", "last_purchase"]
        ].copy()
        top_20.columns = [
            "Customer", "Segment", "Total Spend ($)", "Visits",
            "Stores", "First Purchase", "Last Purchase",
        ]
        top_20["Total Spend ($)"] = top_20["Total Spend ($)"].apply(
            lambda x: "${:,.0f}".format(x))
        st.dataframe(top_20, hide_index=True, use_container_width=True,
                     key="top_20_table")

        # --- Department Mix ---
        st.markdown("---")
        st.subheader("Department Mix — Loyalty vs All Customers")

        try:
            dept_data = query_named("customer_top_departments",
                                    start=txn_start, end=txn_end)
            if dept_data:
                df_dept = pd.DataFrame(dept_data)
                df_dept = df_dept[df_dept["Department"].notna()]
                df_dept["loyalty_pct"] = (
                    df_dept["loyalty_revenue"]
                    / df_dept["loyalty_revenue"].sum() * 100
                )
                df_dept["total_pct"] = (
                    df_dept["total_revenue"]
                    / df_dept["total_revenue"].sum() * 100
                )
                df_dept["index_score"] = (
                    df_dept["loyalty_pct"] / df_dept["total_pct"] * 100
                ).fillna(0)

                dept_plot = df_dept.melt(
                    id_vars=["Department"],
                    value_vars=["loyalty_pct", "total_pct"],
                    var_name="Group", value_name="Share %",
                )
                dept_plot["Group"] = dept_plot["Group"].map({
                    "loyalty_pct": "Loyalty Customers",
                    "total_pct": "All Customers",
                })

                fig_dept = px.bar(
                    dept_plot, x="Share %", y="Department", color="Group",
                    orientation="h", barmode="group",
                    color_discrete_map={
                        "Loyalty Customers": COLORS["green"],
                        "All Customers": "#94a3b8",
                    },
                    labels={"Department": ""},
                )
                fig_dept.update_layout(
                    height=max(350, len(df_dept) * 40),
                    legend=dict(orientation="h", y=-0.15))
                st.plotly_chart(fig_dept, use_container_width=True,
                                key="dept_mix_chart")
        except Exception:
            st.info("Department mix data unavailable.")

        # --- Loyalty by Department ---
        st.markdown("---")
        st.subheader("Loyalty Customers by Department")

        try:
            hier_data = query_named("customer_by_department",
                                    start=txn_start, end=txn_end)
            if hier_data:
                df_hier = pd.DataFrame(hier_data)

                fig_hier = px.bar(
                    df_hier, x="revenue", y="Department",
                    orientation="h",
                    color_discrete_sequence=[COLORS["green"]],
                    labels={"revenue": "Loyalty Revenue ($)",
                            "Department": ""},
                    text=df_hier["revenue"].apply(
                        lambda x: "${:,.0f}".format(x)),
                )
                fig_hier.update_layout(
                    height=max(350, len(df_hier) * 30),
                    yaxis=dict(autorange="reversed"),
                )
                fig_hier.update_traces(textposition="outside")
                st.plotly_chart(fig_hier, use_container_width=True,
                                key="hier_loyalty_chart")

                # Stats table
                hier_display = df_hier.copy()
                hier_display["revenue"] = hier_display["revenue"].apply(
                    lambda x: "${:,.0f}".format(x))
                hier_display.columns = [
                    "Department", "Customers", "Revenue",
                    "Transactions", "Line Items",
                ]
                st.dataframe(hier_display, hide_index=True,
                             use_container_width=True,
                             key="hier_loyalty_table")
            else:
                st.info("No department data for the selected period.")
        except Exception as e:
            st.info("Department breakdown unavailable: {}".format(e))

        # --- Export ---
        st.markdown("---")
        exp1, exp2 = st.columns(2)
        with exp1:
            csv_seg = seg_summary.to_csv(index=False)
            st.download_button(
                "Download Segment Summary (CSV)",
                data=csv_seg,
                file_name="customer_segments.csv",
                mime="text/csv",
                key="dl_segments",
            )
        with exp2:
            csv_top = df_rfm.head(100).to_csv(index=False)
            st.download_button(
                "Download Top 100 Customers (CSV)",
                data=csv_top,
                file_name="top_customers.csv",
                mime="text/csv",
                key="dl_top_customers",
            )


# ============================================================================
# TAB 3: CHANNEL ANALYSIS
# ============================================================================

with tab3:
    st.subheader("Channel Performance")
    st.caption(
        "Retail vs Online performance analysis using aggregate customer "
        "counts and transaction-level basket data."
    )

    # Load channel data from SQLite
    df_ch = load_customer_data(date_from, date_to, stores=selected_stores)

    if df_ch.empty:
        st.info("No channel data available for the selected period.")
    else:
        # --- Channel KPIs ---
        retail_ct = df_ch[
            (df_ch["measure"] == "Customer Count")
            & (df_ch["channel"] == "Retail")
        ]["value"].sum()
        online_ct = df_ch[
            (df_ch["measure"] == "Customer Count")
            & (df_ch["channel"] == "Online")
        ]["value"].sum()
        total_ct = retail_ct + online_ct
        online_pct_ch = online_ct / total_ct * 100 if total_ct > 0 else 0

        # Calculate growth (last 13 weeks vs prior 13 weeks)
        end_dt = pd.to_datetime(date_to)
        recent_start = (end_dt - pd.Timedelta(weeks=13)).strftime("%Y-%m-%d")
        prior_start = (end_dt - pd.Timedelta(weeks=26)).strftime("%Y-%m-%d")
        prior_end = (end_dt - pd.Timedelta(weeks=13)).strftime("%Y-%m-%d")

        recent_online = df_ch[
            (df_ch["measure"] == "Customer Count")
            & (df_ch["channel"] == "Online")
            & (df_ch["week_ending"] >= pd.Timestamp(recent_start))
        ]["value"].sum()
        prior_online = df_ch[
            (df_ch["measure"] == "Customer Count")
            & (df_ch["channel"] == "Online")
            & (df_ch["week_ending"] >= pd.Timestamp(prior_start))
            & (df_ch["week_ending"] < pd.Timestamp(prior_end))
        ]["value"].sum()
        online_growth = (
            (recent_online - prior_online) / prior_online * 100
            if prior_online > 0 else 0
        )

        ck1, ck2, ck3, ck4 = st.columns(4)
        ck1.metric("Retail Customers", "{:,.0f}".format(retail_ct))
        ck2.metric("Online Customers", "{:,.0f}".format(online_ct))
        ck3.metric("Online Penetration", "{:.1f}%".format(online_pct_ch))
        ck4.metric("Online Growth (13W)", "{:+.1f}%".format(online_growth))

        # --- Channel Mix Over Time ---
        st.markdown("---")
        st.subheader("Channel Mix Over Time")

        ch_trend = df_ch[df_ch["measure"] == "Customer Count"].groupby(
            ["week_ending", "channel"]
        )["value"].sum().reset_index()

        if ch_trend.empty:
            st.info("No channel trend data for the selected period.")
        else:
            fig_ch_area = px.area(
                ch_trend, x="week_ending", y="value", color="channel",
                labels={"week_ending": "Week", "value": "Customers",
                        "channel": "Channel"},
                color_discrete_map={"Retail": COLORS["dark_blue"],
                                    "Online": COLORS["purple"]},
            )
            fig_ch_area.update_layout(height=400,
                                       legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig_ch_area, use_container_width=True,
                            key="channel_area_chart")

        # Online penetration trend
        ch_weekly = df_ch[df_ch["measure"] == "Customer Count"].pivot_table(
            index="week_ending", columns="channel",
            values="value", aggfunc="sum",
        ).fillna(0)
        if not ch_weekly.empty and "Online" in ch_weekly.columns and "Retail" in ch_weekly.columns:
            ch_weekly["Online %"] = (
                ch_weekly["Online"]
                / (ch_weekly["Online"] + ch_weekly["Retail"]) * 100
            )
            fig_pen = px.line(
                ch_weekly.reset_index(), x="week_ending", y="Online %",
                labels={"week_ending": "Week",
                        "Online %": "Online Penetration %"},
                color_discrete_sequence=[COLORS["purple"]],
            )
            fig_pen.update_layout(height=300)
            st.plotly_chart(fig_pen, use_container_width=True,
                            key="online_penetration_trend")

        # --- Online Penetration by Store ---
        st.markdown("---")
        st.subheader("Online Penetration by Store")

        store_channel = df_ch[df_ch["measure"] == "Customer Count"].groupby(
            ["store_short", "channel"]
        )["value"].sum().unstack(fill_value=0)

        if not store_channel.empty and "Online" in store_channel.columns:
            store_channel["Online %"] = (
                store_channel["Online"]
                / store_channel.sum(axis=1) * 100
            )
            store_pen = store_channel["Online %"].sort_values(
                ascending=True).reset_index()

            fig_spen = px.bar(
                store_pen, x="Online %", y="store_short",
                orientation="h",
                labels={"store_short": "",
                        "Online %": "Online Penetration %"},
                color="Online %",
                color_continuous_scale=[COLORS["dark_blue"],
                                        COLORS["purple"]],
            )
            fig_spen.update_layout(
                height=max(400, len(store_pen) * 25))
            st.plotly_chart(fig_spen, use_container_width=True,
                            key="store_online_pen")

        # --- Basket Analysis by Store ---
        st.markdown("---")
        st.subheader("Basket Analysis by Store")

        try:
            basket_data = query_named("avg_basket_by_store",
                                      start=txn_start, end=txn_end)
            if basket_data:
                df_basket = pd.DataFrame(basket_data)
                df_basket["Store"] = df_basket["Store_ID"].map(
                    STORE_NAMES).fillna(df_basket["Store_ID"].astype(str))

                fig_basket = px.scatter(
                    df_basket, x="avg_items", y="avg_basket_value",
                    size="total_baskets", hover_name="Store",
                    labels={"avg_items": "Avg Items per Basket",
                            "avg_basket_value": "Avg Basket Value ($)",
                            "total_baskets": "Total Baskets"},
                    color_discrete_sequence=[COLORS["green"]],
                )
                fig_basket.update_layout(height=450)
                st.plotly_chart(fig_basket, use_container_width=True,
                                key="basket_scatter")
        except Exception:
            st.info("Basket analysis data unavailable.")

        # --- Revenue & Loyalty by Department ---
        st.markdown("---")
        st.subheader("Revenue & Loyalty by Department")

        try:
            ch_hier_data = query_named("channel_by_department",
                                       start=txn_start, end=txn_end)
            if ch_hier_data:
                df_ch_hier = pd.DataFrame(ch_hier_data)
                df_ch_hier["loyalty_rate"] = (
                    df_ch_hier["loyalty_revenue"]
                    / df_ch_hier["revenue"].replace(0, 1) * 100
                )

                fig_ch_hier = px.bar(
                    df_ch_hier, x="revenue", y="Department",
                    orientation="h",
                    color="loyalty_rate",
                    color_continuous_scale=[COLORS["dark_blue"],
                                            COLORS["green"]],
                    labels={"revenue": "Total Revenue ($)",
                            "Department": "",
                            "loyalty_rate": "Loyalty %"},
                    text=df_ch_hier["revenue"].apply(
                        lambda x: "${:,.0f}".format(x)),
                )
                fig_ch_hier.update_layout(
                    height=max(350, len(df_ch_hier) * 30),
                    yaxis=dict(autorange="reversed"),
                )
                fig_ch_hier.update_traces(textposition="outside")
                st.plotly_chart(fig_ch_hier, use_container_width=True,
                                key="ch_hier_chart")

                # Stats table
                display_cols = ["Department", "revenue", "transactions",
                                "loyalty_customers", "loyalty_revenue",
                                "loyalty_rate"]
                ch_hier_tbl = df_ch_hier[
                    [c for c in display_cols if c in df_ch_hier.columns]
                ].copy()
                rename = {
                    "revenue": "Revenue",
                    "transactions": "Transactions",
                    "loyalty_customers": "Loyalty Customers",
                    "loyalty_revenue": "Loyalty Revenue",
                    "loyalty_rate": "Loyalty Rate",
                }
                ch_hier_tbl = ch_hier_tbl.rename(columns=rename)
                if "Revenue" in ch_hier_tbl.columns:
                    ch_hier_tbl["Revenue"] = ch_hier_tbl["Revenue"].apply(
                        lambda x: "${:,.0f}".format(x)
                        if isinstance(x, (int, float)) else x)
                if "Loyalty Revenue" in ch_hier_tbl.columns:
                    ch_hier_tbl["Loyalty Revenue"] = ch_hier_tbl[
                        "Loyalty Revenue"].apply(
                        lambda x: "${:,.0f}".format(x)
                        if isinstance(x, (int, float)) else x)
                if "Loyalty Rate" in ch_hier_tbl.columns:
                    ch_hier_tbl["Loyalty Rate"] = ch_hier_tbl[
                        "Loyalty Rate"].apply(
                        lambda x: "{:.1f}%".format(x)
                        if isinstance(x, (int, float)) else x)
                st.dataframe(ch_hier_tbl, hide_index=True,
                             use_container_width=True,
                             key="ch_hier_table")
            else:
                st.info("No department data for the selected period.")
        except Exception as e:
            st.info("Department breakdown unavailable: {}".format(e))

        # --- Multi-Store Loyalty ---
        st.markdown("---")
        st.subheader("Customer Store Loyalty")

        try:
            cross_data = query_named("customer_channel_crossover",
                                     start=txn_start, end=txn_end)
            if cross_data:
                df_cross = pd.DataFrame(cross_data)

                fig_cross = px.pie(
                    df_cross, values="customer_count",
                    names="store_loyalty",
                    color="store_loyalty",
                    color_discrete_map={
                        "Single Store": COLORS["dark_blue"],
                        "2-3 Stores": COLORS["teal"],
                        "4+ Stores": COLORS["green"],
                    },
                    hole=0.4,
                )
                fig_cross.update_layout(height=350)
                st.plotly_chart(fig_cross, use_container_width=True,
                                key="store_loyalty_pie")

                # Stats
                cross_display = df_cross.copy()
                cross_display.columns = [
                    "Store Loyalty", "Customers", "Avg Visits",
                    "Avg Spend ($)", "Total Spend ($)",
                ]
                cross_display["Avg Spend ($)"] = cross_display[
                    "Avg Spend ($)"].apply(
                    lambda x: "${:,.0f}".format(x))
                cross_display["Total Spend ($)"] = cross_display[
                    "Total Spend ($)"].apply(
                    lambda x: "${:,.0f}".format(x))
                cross_display["Avg Visits"] = cross_display[
                    "Avg Visits"].apply(lambda x: "{:.1f}".format(x))
                st.dataframe(cross_display, hide_index=True,
                             use_container_width=True,
                             key="store_loyalty_table")
        except Exception:
            st.info("Store loyalty data unavailable.")


# ============================================================================
# TAB 4: COHORT & RETENTION
# ============================================================================

with tab4:
    st.subheader("Cohort Retention Analysis")
    st.caption(
        "Track how cohorts of new loyalty customers retain over time. "
        "Each cohort is defined by the month of first purchase."
    )

    try:
        cohort_data = query_named("customer_cohort_retention",
                                  start=txn_start, end=txn_end)
    except Exception as e:
        st.error("Could not load cohort data: {}".format(e))
        cohort_data = []

    if not cohort_data:
        st.info("No cohort data available for the selected period.")
    else:
        df_cohort = pd.DataFrame(cohort_data)
        df_cohort["cohort_month"] = pd.to_datetime(df_cohort["cohort_month"])

        # Calculate cohort sizes (month 0)
        cohort_sizes = df_cohort[df_cohort["months_since"] == 0].set_index(
            "cohort_month"
        )["active_customers"].to_dict()

        # Calculate retention %
        df_cohort["cohort_size"] = df_cohort["cohort_month"].map(cohort_sizes)
        df_cohort["retention_pct"] = (
            df_cohort["active_customers"]
            / df_cohort["cohort_size"] * 100
        ).fillna(0)

        # --- Key Retention Metrics ---
        m1_retention = df_cohort[
            df_cohort["months_since"] == 1
        ]["retention_pct"].mean()
        m3_retention = df_cohort[
            df_cohort["months_since"] == 3
        ]["retention_pct"].mean()
        m6_retention = df_cohort[
            df_cohort["months_since"] == 6
        ]["retention_pct"].mean()

        # Average customer lifespan (months where retention > 10%)
        avg_lifespan = df_cohort.groupby("cohort_month").apply(
            lambda g: g[g["retention_pct"] >= 10]["months_since"].max()
        ).mean()

        rk1, rk2, rk3, rk4 = st.columns(4)
        rk1.metric("Month-1 Retention",
                    "{:.1f}%".format(m1_retention) if pd.notna(m1_retention)
                    else "N/A")
        rk2.metric("Month-3 Retention",
                    "{:.1f}%".format(m3_retention) if pd.notna(m3_retention)
                    else "N/A")
        rk3.metric("Month-6 Retention",
                    "{:.1f}%".format(m6_retention) if pd.notna(m6_retention)
                    else "N/A")
        rk4.metric("Avg Active Lifespan",
                    "{:.0f} months".format(avg_lifespan)
                    if pd.notna(avg_lifespan) else "N/A")

        # --- Cohort Retention Heatmap ---
        st.markdown("---")
        st.subheader("Retention Heatmap")

        # Limit to last 12 cohorts and 12 months
        recent_cohorts = sorted(cohort_sizes.keys())[-12:]
        heatmap_data = df_cohort[
            (df_cohort["cohort_month"].isin(recent_cohorts))
            & (df_cohort["months_since"] <= 12)
        ]

        if not heatmap_data.empty:
            pivot = heatmap_data.pivot_table(
                index="cohort_month", columns="months_since",
                values="retention_pct", aggfunc="mean",
            )
            pivot.index = [d.strftime("%b %Y") for d in pivot.index]
            pivot.columns = ["M{}".format(int(c)) for c in pivot.columns]

            fig_heatmap = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns.tolist(),
                y=pivot.index.tolist(),
                colorscale=[
                    [0, "#ef4444"],
                    [0.3, "#fbbf24"],
                    [0.6, "#86efac"],
                    [1, "#059669"],
                ],
                text=[["{:.0f}%".format(v) if pd.notna(v) else ""
                       for v in row] for row in pivot.values],
                texttemplate="%{text}",
                textfont={"size": 11},
                hovertemplate=(
                    "Cohort: %{y}<br>Month: %{x}<br>"
                    "Retention: %{z:.1f}%<extra></extra>"
                ),
            ))
            fig_heatmap.update_layout(
                height=max(350, len(pivot) * 35),
                xaxis_title="Months Since First Purchase",
                yaxis_title="Cohort",
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_heatmap, use_container_width=True,
                            key="cohort_heatmap")

        # --- Retention Curves ---
        st.markdown("---")
        st.subheader("Retention Curves")

        last_6 = sorted(cohort_sizes.keys())[-6:]
        curve_data = df_cohort[
            (df_cohort["cohort_month"].isin(last_6))
            & (df_cohort["months_since"] <= 12)
        ].copy()

        if not curve_data.empty:
            curve_data["cohort_label"] = curve_data["cohort_month"].dt.strftime(
                "%b %Y")

            fig_curves = px.line(
                curve_data, x="months_since", y="retention_pct",
                color="cohort_label",
                labels={"months_since": "Months Since First Purchase",
                        "retention_pct": "Retention %",
                        "cohort_label": "Cohort"},
                markers=True,
            )
            fig_curves.update_layout(height=400,
                                      legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_curves, use_container_width=True,
                            key="retention_curves")

        # --- New Customer Acquisition ---
        st.markdown("---")
        st.subheader("Monthly New Customer Acquisition")

        acq_data = pd.DataFrame([
            {"month": k, "new_customers": v}
            for k, v in sorted(cohort_sizes.items())
        ])

        if not acq_data.empty:
            acq_data["month_label"] = pd.to_datetime(
                acq_data["month"]).dt.strftime("%b %Y")

            fig_acq = go.Figure()
            fig_acq.add_trace(go.Bar(
                x=acq_data["month_label"],
                y=acq_data["new_customers"],
                marker_color=COLORS["green"],
                name="New Customers",
            ))

            # Add trend line
            if len(acq_data) >= 3:
                z = np.polyfit(range(len(acq_data)),
                               acq_data["new_customers"], 1)
                p = np.poly1d(z)
                fig_acq.add_trace(go.Scatter(
                    x=acq_data["month_label"],
                    y=p(range(len(acq_data))),
                    mode="lines",
                    line=dict(color=COLORS["amber"], dash="dash", width=2),
                    name="Trend",
                ))

            fig_acq.update_layout(
                height=350,
                xaxis_tickangle=-45,
                legend=dict(orientation="h", y=-0.25),
            )
            st.plotly_chart(fig_acq, use_container_width=True,
                            key="acquisition_chart")

        # --- Export ---
        st.markdown("---")
        csv_cohort = df_cohort.to_csv(index=False)
        st.download_button(
            "Download Cohort Data (CSV)",
            data=csv_cohort,
            file_name="cohort_retention.csv",
            mime="text/csv",
            key="dl_cohort",
        )


# ============================================================================
# ASK A QUESTION
# ============================================================================

render_ask_question("customers")

# ============================================================================
# FOOTER
# ============================================================================

footer_parts = [period_label, "{} to {}".format(date_from, date_to)]
if time_label:
    footer_parts.append(time_label)
render_footer("Customer Analytics", " | ".join(footer_parts), user=user)
