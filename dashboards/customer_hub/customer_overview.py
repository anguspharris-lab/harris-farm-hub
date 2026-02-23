"""
Customer Hub — Customer Insights > Overview
KPIs, weekly trend, budget variance from SQLite aggregate data.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from customer_hub.components import (
    PALETTE, section_header, insight_callout, one_thing_box,
    metric_row, store_display_name,
)
from shared.fiscal_selector import render_fiscal_selector
from shared.time_filter import render_time_filter, time_filter_summary, render_quick_period
from transaction_layer import STORE_NAMES


# ── Data helpers ─────────────────────────────────────────────────────────────

def _get_db_path():
    return Path(__file__).resolve().parent.parent.parent / "data" / "harris_farm.db"


@st.cache_data(ttl=300)
def _load_customer_data(date_from, date_to, stores=None, channel=None):
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
def _get_store_list():
    db = _get_db_path()
    if not db.exists():
        return []
    with sqlite3.connect(str(db)) as conn:
        rows = conn.execute(
            "SELECT DISTINCT store FROM customers ORDER BY store"
        ).fetchall()
    return [r[0] for r in rows]


# ── Shared filter state (stored in session_state for other tabs) ─────────

DATA_START = "2024-07-01"


def _get_filters():
    """Return shared filter values, creating sidebar widgets on first call."""
    if "ch_filters_init" not in st.session_state:
        st.session_state["ch_filters_init"] = True

    qp_start, qp_end, qp_label = render_quick_period(key_prefix="ch")
    filters = render_fiscal_selector(
        key_prefix="ch",
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

    if qp_start and qp_end:
        date_from = qp_start
        date_to = qp_end
        period_label = qp_label

    if date_from < DATA_START:
        date_from = DATA_START

    time_filters = render_time_filter(
        key_prefix="ch_time", fin_year=filters.get("fin_year"))
    time_label = time_filter_summary(time_filters)

    selected_store_id = filters.get("store_id")
    selected_stores = None
    if selected_store_id:
        all_stores = _get_store_list()
        matched = [s for s in all_stores
                   if s.startswith("{} ".format(selected_store_id))]
        if matched:
            selected_stores = matched

    channel_filter = st.sidebar.selectbox(
        "Channel", ["All", "Retail", "Online"], key="ch_channel")
    channel_arg = None if channel_filter == "All" else channel_filter
    st.sidebar.markdown("---")

    # Store in session state for sibling tabs
    st.session_state["ch_date_from"] = date_from
    st.session_state["ch_date_to"] = date_to
    st.session_state["ch_period_label"] = period_label
    st.session_state["ch_time_label"] = time_label
    st.session_state["ch_selected_stores"] = selected_stores
    st.session_state["ch_channel_arg"] = channel_arg
    st.session_state["ch_txn_start"] = date_from
    st.session_state["ch_txn_end"] = date_to

    return date_from, date_to, selected_stores, channel_arg


# ── Render ───────────────────────────────────────────────────────────────────

def render():
    date_from, date_to, selected_stores, channel_arg = _get_filters()

    section_header(
        "Customer Overview",
        "How many customers are walking through our doors — and are we hitting budget?",
    )

    df = _load_customer_data(date_from, date_to, stores=selected_stores,
                             channel=channel_arg)
    if df.empty:
        st.warning("No customer data found for the selected filters.")
        return

    # ── KPIs ──
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

    metric_row([
        ("Total Customers", "{:,.0f}".format(total_customers)),
        ("Retail", "{:,.0f}".format(retail_customers)),
        ("Online", "{:,.0f}".format(online_customers),
         "{:.1f}% of total".format(online_pct)),
        ("Budget Variance", "{:+.1f}%".format(budget_var)),
    ])

    # ── Strategic insight ──
    if budget_var > 0:
        insight_callout(
            "We're <b>{:+.1f}%</b> ahead of budget on customer count. "
            "The question is: are these the <i>right</i> customers?".format(budget_var),
            style="success",
        )
    else:
        insight_callout(
            "We're <b>{:+.1f}%</b> behind budget. Dig into the store-level view "
            "to find where footfall is slipping.".format(budget_var),
            style="warning",
        )

    # ── Weekly Trend ──
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
            color_discrete_map={"Retail": PALETTE["dark_blue"],
                                "Online": PALETTE["purple"]},
        )
        budget_trend = df[df["measure"] == "Budget Customers"].groupby(
            "week_ending"
        )["value"].sum().reset_index()
        if not budget_trend.empty:
            fig_trend.add_trace(go.Scatter(
                x=budget_trend["week_ending"], y=budget_trend["value"],
                mode="lines", name="Budget",
                line=dict(color=PALETTE["amber"], dash="dash", width=1),
            ))
        fig_trend.update_layout(height=400, legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig_trend, use_container_width=True, key="ch_weekly_trend")

    # ── Budget Variance by Store ──
    st.subheader("Budget Variance by Store")
    actual_by_store = df[df["measure"] == "Customer Count"].groupby(
        "store_short")["value"].sum()
    budget_by_store = df[df["measure"] == "Budget Customers"].groupby(
        "store_short")["value"].sum()
    variance_df = pd.DataFrame({
        "Actual": actual_by_store, "Budget": budget_by_store,
    }).dropna()

    if not variance_df.empty:
        variance_df["Variance %"] = (
            (variance_df["Actual"] - variance_df["Budget"])
            / variance_df["Budget"].replace(0, float("nan")) * 100
        ).fillna(0)
        variance_df = variance_df.sort_values("Variance %")
        fig_var = px.bar(
            variance_df.reset_index(), x="Variance %", y="store_short",
            orientation="h",
            labels={"store_short": "", "Variance %": "Variance vs Budget (%)"},
            color="Variance %",
            color_continuous_scale=["#dc2626", "#fbbf24", "#059669"],
            color_continuous_midpoint=0,
        )
        fig_var.update_layout(height=max(400, len(variance_df) * 25))
        st.plotly_chart(fig_var, use_container_width=True, key="ch_budget_var")

    # ── One Thing ──
    one_thing_box(
        "Customer count tells you <i>traffic</i>. Pair it with basket size "
        "(Channel Analysis tab) and loyalty penetration (Known Customers tab) "
        "to understand <i>value</i>."
    )
