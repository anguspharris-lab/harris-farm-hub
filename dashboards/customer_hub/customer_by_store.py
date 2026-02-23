"""
Customer Hub — Customer Insights > By Store
Store-level customer comparison with colour-coded performance table.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from customer_hub.components import (
    PALETTE, section_header, insight_callout, store_display_name,
)


def _get_db_path():
    return Path(__file__).resolve().parent.parent.parent / "data" / "harris_farm.db"


@st.cache_data(ttl=300)
def _load_customer_data(date_from, date_to, channel=None):
    db = _get_db_path()
    if not db.exists():
        return pd.DataFrame()
    query = """
        SELECT store, channel, measure, week_ending, value
        FROM customers WHERE week_ending >= ? AND week_ending <= ?
    """
    params = [date_from, date_to]
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


def render():
    date_from = st.session_state.get("ch_date_from")
    date_to = st.session_state.get("ch_date_to")
    channel_arg = st.session_state.get("ch_channel_arg")
    if not date_from or not date_to:
        st.info("Select a period in the Overview tab first.")
        return

    section_header(
        "Customers by Store",
        "Side-by-side store comparison — total customers, channel split, "
        "and budget performance at a glance.",
    )

    df = _load_customer_data(date_from, date_to, channel=channel_arg)
    if df.empty:
        st.warning("No customer data for the selected period.")
        return

    # ── Build store summary table ──
    cust_by_store = df[df["measure"] == "Customer Count"].groupby(
        ["store_short", "channel"]
    )["value"].sum().unstack(fill_value=0)

    if cust_by_store.empty:
        st.info("No store-level data available.")
        return

    # Ensure columns exist
    for col in ["Retail", "Online"]:
        if col not in cust_by_store.columns:
            cust_by_store[col] = 0

    cust_by_store["Total"] = cust_by_store["Retail"] + cust_by_store["Online"]
    cust_by_store["Online %"] = (
        cust_by_store["Online"] / cust_by_store["Total"].replace(0, 1) * 100
    )

    # Budget variance
    budget_by_store = df[df["measure"] == "Budget Customers"].groupby(
        "store_short"
    )["value"].sum()
    cust_by_store["Budget"] = budget_by_store
    cust_by_store["Var %"] = (
        (cust_by_store["Total"] - cust_by_store["Budget"])
        / cust_by_store["Budget"].replace(0, float("nan")) * 100
    ).fillna(0)

    summary = cust_by_store.reset_index().sort_values("Total", ascending=False)

    # ── KPIs ──
    top_store = summary.iloc[0]["store_short"]
    top_count = summary.iloc[0]["Total"]
    avg_online = summary["Online %"].mean()
    above_budget = (summary["Var %"] > 0).sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Stores", len(summary))
    k2.metric("Top Store", top_store, "{:,.0f} customers".format(top_count))
    k3.metric("Avg Online %", "{:.1f}%".format(avg_online))
    k4.metric("Above Budget", "{}/{}".format(above_budget, len(summary)))

    # ── Horizontal bar: Total customers by store ──
    st.subheader("Total Customers by Store")
    bar_df = summary.sort_values("Total", ascending=True)
    fig = px.bar(
        bar_df, x="Total", y="store_short", orientation="h",
        labels={"Total": "Total Customers", "store_short": ""},
        color_discrete_sequence=[PALETTE["green"]],
    )
    fig.update_layout(height=max(400, len(bar_df) * 25))
    st.plotly_chart(fig, use_container_width=True, key="ch_store_bar")

    # ── Channel split stacked bar ──
    st.subheader("Retail vs Online by Store")
    channel_by_store = df[df["measure"] == "Customer Count"].groupby(
        ["store_short", "channel"]
    )["value"].sum().reset_index()

    if not channel_by_store.empty:
        fig_ch = px.bar(
            channel_by_store, x="value", y="store_short", color="channel",
            orientation="h", barmode="stack",
            labels={"value": "Customers", "store_short": "", "channel": "Channel"},
            color_discrete_map={"Retail": PALETTE["dark_blue"],
                                "Online": PALETTE["purple"]},
        )
        fig_ch.update_layout(height=max(400, len(bar_df) * 25))
        st.plotly_chart(fig_ch, use_container_width=True, key="ch_store_channel")

    # ── Colour-coded comparison table ──
    st.subheader("Store Performance Table")
    display = summary[["store_short", "Total", "Retail", "Online",
                        "Online %", "Budget", "Var %"]].copy()
    display.columns = ["Store", "Total", "Retail", "Online",
                       "Online %", "Budget", "Var %"]

    def _color_var(val):
        if val > 5:
            return "background-color: #dcfce7"
        elif val < -5:
            return "background-color: #fee2e2"
        return ""

    styled = display.style.format({
        "Total": "{:,.0f}", "Retail": "{:,.0f}", "Online": "{:,.0f}",
        "Online %": "{:.1f}%", "Budget": "{:,.0f}", "Var %": "{:+.1f}%",
    }).applymap(_color_var, subset=["Var %"])

    st.dataframe(styled, use_container_width=True, hide_index=True,
                 height=min(600, 40 + len(display) * 35),
                 key="ch_store_table")

    # Insight
    below_budget = summary[summary["Var %"] < -5]
    if not below_budget.empty:
        stores = ", ".join(below_budget["store_short"].head(3).tolist())
        insight_callout(
            "Stores significantly below budget: <b>{}</b>. "
            "Investigate local factors — construction, competition, "
            "or seasonal shifts.".format(stores),
            style="warning",
        )

    # ── Detail table ──
    with st.expander("Detailed Weekly Data"):
        detail = df[df["measure"] == "Customer Count"].pivot_table(
            index=["store_short", "channel"],
            columns=pd.Grouper(key="week_ending", freq="4W"),
            values="value", aggfunc="sum",
        )
        if not detail.empty:
            detail.columns = [c.strftime("%d %b %Y") for c in detail.columns]
            st.dataframe(detail.style.format("{:,.0f}"),
                         key="ch_store_detail")
