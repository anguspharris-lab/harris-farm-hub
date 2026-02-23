"""
Customer Hub — Customer Insights > Channel Analysis
Retail vs Online performance, penetration trends, basket analysis,
department breakdown by channel.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from customer_hub.components import (
    PALETTE, section_header, insight_callout, store_display_name,
)
from transaction_layer import TransactionStore, STORE_NAMES
from transaction_queries import run_query


def _get_db_path():
    return Path(__file__).resolve().parent.parent.parent / "data" / "harris_farm.db"


@st.cache_data(ttl=300)
def _load_customer_data(date_from, date_to, stores=None):
    db = _get_db_path()
    if not db.exists():
        return pd.DataFrame()
    query = """
        SELECT store, channel, measure, week_ending, value
        FROM customers WHERE week_ending >= ? AND week_ending <= ?
    """
    params = [date_from, date_to]
    if stores:
        placeholders = ",".join("?" * len(stores))
        query += " AND store IN ({})".format(placeholders)
        params.extend(stores)
    with sqlite3.connect(str(db)) as conn:
        df = pd.read_sql_query(query, conn, params=params)
    if df.empty:
        return df
    df["week_ending"] = pd.to_datetime(df["week_ending"])
    df["store_short"] = df["store"].apply(store_display_name)
    return df


@st.cache_resource
def _get_store():
    return TransactionStore()


@st.cache_data(ttl=300, show_spinner="Querying transactions...")
def _query(name, **kwargs):
    return run_query(_get_store(), name, **kwargs)


def render():
    date_from = st.session_state.get("ch_date_from")
    date_to = st.session_state.get("ch_date_to")
    selected_stores = st.session_state.get("ch_selected_stores")
    txn_start = st.session_state.get("ch_txn_start")
    txn_end = st.session_state.get("ch_txn_end")
    if not date_from or not date_to:
        st.info("Select a period in the Overview tab first.")
        return

    section_header(
        "Channel Performance",
        "Retail vs Online — how the two channels contribute, "
        "and where online is gaining traction.",
    )

    df_ch = _load_customer_data(date_from, date_to, stores=selected_stores)
    if df_ch.empty:
        st.info("No channel data available for the selected period.")
        return

    # ── KPIs ──
    retail_ct = df_ch[
        (df_ch["measure"] == "Customer Count") & (df_ch["channel"] == "Retail")
    ]["value"].sum()
    online_ct = df_ch[
        (df_ch["measure"] == "Customer Count") & (df_ch["channel"] == "Online")
    ]["value"].sum()
    total_ct = retail_ct + online_ct
    online_pct = online_ct / total_ct * 100 if total_ct > 0 else 0

    # Growth calc (last 13w vs prior 13w)
    end_dt = pd.to_datetime(date_to)
    recent_start = (end_dt - pd.Timedelta(weeks=13)).strftime("%Y-%m-%d")
    prior_end = (end_dt - pd.Timedelta(weeks=13)).strftime("%Y-%m-%d")
    prior_start = (end_dt - pd.Timedelta(weeks=26)).strftime("%Y-%m-%d")

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

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Retail Customers", "{:,.0f}".format(retail_ct))
    k2.metric("Online Customers", "{:,.0f}".format(online_ct))
    k3.metric("Online Penetration", "{:.1f}%".format(online_pct))
    k4.metric("Online Growth (13W)", "{:+.1f}%".format(online_growth))

    if online_growth > 5:
        insight_callout(
            "Online is growing at <b>{:+.1f}%</b> over the last quarter. "
            "Cross-channel customers spend more — are we nudging retail-only "
            "shoppers to try online?".format(online_growth),
            style="success",
        )

    # ── Channel Mix Over Time ──
    st.markdown("---")
    st.subheader("Channel Mix Over Time")
    ch_trend = df_ch[df_ch["measure"] == "Customer Count"].groupby(
        ["week_ending", "channel"]
    )["value"].sum().reset_index()

    if not ch_trend.empty:
        fig_area = px.area(
            ch_trend, x="week_ending", y="value", color="channel",
            labels={"week_ending": "Week", "value": "Customers",
                    "channel": "Channel"},
            color_discrete_map={"Retail": PALETTE["dark_blue"],
                                "Online": PALETTE["purple"]},
        )
        fig_area.update_layout(height=400, legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig_area, use_container_width=True, key="ch_channel_area")

    # Online penetration trend
    ch_weekly = df_ch[df_ch["measure"] == "Customer Count"].pivot_table(
        index="week_ending", columns="channel", values="value", aggfunc="sum",
    ).fillna(0)
    if not ch_weekly.empty and "Online" in ch_weekly.columns and "Retail" in ch_weekly.columns:
        ch_weekly["Online %"] = (
            ch_weekly["Online"]
            / (ch_weekly["Online"] + ch_weekly["Retail"]) * 100
        )
        fig_pen = px.line(
            ch_weekly.reset_index(), x="week_ending", y="Online %",
            labels={"week_ending": "Week", "Online %": "Online Penetration %"},
            color_discrete_sequence=[PALETTE["purple"]],
        )
        fig_pen.update_layout(height=300)
        st.plotly_chart(fig_pen, use_container_width=True,
                        key="ch_online_pen_trend")

    # ── Online Penetration by Store ──
    st.markdown("---")
    st.subheader("Online Penetration by Store")
    store_channel = df_ch[df_ch["measure"] == "Customer Count"].groupby(
        ["store_short", "channel"]
    )["value"].sum().unstack(fill_value=0)

    if not store_channel.empty and "Online" in store_channel.columns:
        store_channel["Online %"] = (
            store_channel["Online"] / store_channel.sum(axis=1) * 100
        )
        store_pen = store_channel["Online %"].sort_values(
            ascending=True).reset_index()
        fig_spen = px.bar(
            store_pen, x="Online %", y="store_short", orientation="h",
            labels={"store_short": "", "Online %": "Online Penetration %"},
            color="Online %",
            color_continuous_scale=[PALETTE["dark_blue"], PALETTE["purple"]],
        )
        fig_spen.update_layout(height=max(400, len(store_pen) * 25))
        st.plotly_chart(fig_spen, use_container_width=True,
                        key="ch_store_online_pen")

    # ── Basket Analysis ──
    st.markdown("---")
    st.subheader("Basket Analysis by Store")
    try:
        basket_data = _query("avg_basket_by_store",
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
                color_discrete_sequence=[PALETTE["green"]],
            )
            fig_basket.update_layout(height=450)
            st.plotly_chart(fig_basket, use_container_width=True,
                            key="ch_basket_scatter")
    except Exception:
        st.info("Basket analysis data unavailable.")

    # ── Revenue & Loyalty by Dept ──
    st.markdown("---")
    st.subheader("Revenue & Loyalty by Department")
    try:
        ch_hier_data = _query("channel_by_department",
                              start=txn_start, end=txn_end)
        if ch_hier_data:
            df_ch_hier = pd.DataFrame(ch_hier_data)
            df_ch_hier["loyalty_rate"] = (
                df_ch_hier["loyalty_revenue"]
                / df_ch_hier["revenue"].replace(0, 1) * 100
            )
            fig_ch_hier = px.bar(
                df_ch_hier, x="revenue", y="Department", orientation="h",
                color="loyalty_rate",
                color_continuous_scale=[PALETTE["dark_blue"], PALETTE["green"]],
                labels={"revenue": "Total Revenue ($)", "Department": "",
                        "loyalty_rate": "Loyalty %"},
                text=df_ch_hier["revenue"].apply(lambda x: "${:,.0f}".format(x)),
            )
            fig_ch_hier.update_layout(
                height=max(350, len(df_ch_hier) * 30),
                yaxis=dict(autorange="reversed"),
            )
            fig_ch_hier.update_traces(textposition="outside")
            st.plotly_chart(fig_ch_hier, use_container_width=True,
                            key="ch_hier_chart")

            display_cols = ["Department", "revenue", "transactions",
                            "loyalty_customers", "loyalty_revenue", "loyalty_rate"]
            ch_hier_tbl = df_ch_hier[
                [c for c in display_cols if c in df_ch_hier.columns]
            ].copy()
            rename = {
                "revenue": "Revenue", "transactions": "Transactions",
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
                ch_hier_tbl["Loyalty Revenue"] = ch_hier_tbl["Loyalty Revenue"].apply(
                    lambda x: "${:,.0f}".format(x)
                    if isinstance(x, (int, float)) else x)
            if "Loyalty Rate" in ch_hier_tbl.columns:
                ch_hier_tbl["Loyalty Rate"] = ch_hier_tbl["Loyalty Rate"].apply(
                    lambda x: "{:.1f}%".format(x)
                    if isinstance(x, (int, float)) else x)
            st.dataframe(ch_hier_tbl, hide_index=True, use_container_width=True,
                         key="ch_hier_table")
    except Exception:
        st.info("Department breakdown unavailable.")

    # ── Store Loyalty ──
    st.markdown("---")
    st.subheader("Customer Store Loyalty")
    try:
        cross_data = _query("customer_channel_crossover",
                            start=txn_start, end=txn_end)
        if cross_data:
            df_cross = pd.DataFrame(cross_data)
            fig_cross = px.pie(
                df_cross, values="customer_count", names="store_loyalty",
                color="store_loyalty",
                color_discrete_map={
                    "Single Store": PALETTE["dark_blue"],
                    "2-3 Stores": PALETTE["teal"],
                    "4+ Stores": PALETTE["green"],
                },
                hole=0.4,
            )
            fig_cross.update_layout(height=350)
            st.plotly_chart(fig_cross, use_container_width=True,
                            key="ch_store_loyalty_pie")

            cross_display = df_cross.copy()
            cross_display.columns = [
                "Store Loyalty", "Customers", "Avg Visits",
                "Avg Spend ($)", "Total Spend ($)",
            ]
            cross_display["Avg Spend ($)"] = cross_display["Avg Spend ($)"].apply(
                lambda x: "${:,.0f}".format(x))
            cross_display["Total Spend ($)"] = cross_display["Total Spend ($)"].apply(
                lambda x: "${:,.0f}".format(x))
            cross_display["Avg Visits"] = cross_display["Avg Visits"].apply(
                lambda x: "{:.1f}".format(x))
            st.dataframe(cross_display, hide_index=True, use_container_width=True,
                         key="ch_store_loyalty_tbl")
    except Exception:
        st.info("Store loyalty data unavailable.")
