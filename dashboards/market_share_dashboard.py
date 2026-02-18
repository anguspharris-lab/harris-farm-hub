"""
Harris Farm Hub — Market Share Dashboard
Analyses market share by postcode/region, customer penetration, and spend metrics.
Port 8508.

Data source: market_share table in harris_farm.db
  - Channels: Instore, Online, Total
  - Grain: region_code x channel x period (YYYYMM)
  - Metrics: market_size_dollars, market_share_pct, customer_penetration_pct,
             spend_per_customer, spend_per_transaction, transactions_per_customer
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

from nav import render_nav
from shared.styles import apply_styles, render_header, render_footer
from shared.auth_gate import require_login
from shared.ask_question import render_ask_question

st.set_page_config(
    page_title="Market Share | Harris Farm Hub",
    page_icon="🗺️",
    layout="wide",
)

apply_styles()
user = require_login()
render_nav(8508, auth_token=st.session_state.get("auth_token"))

render_header("🗺️ Market Share Intelligence", "**Harris Farm Markets** | Postcode-level share, penetration & customer spend")


# --- Data Loading ---

def _get_db_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "harris_farm.db"


@st.cache_data(ttl=300)
def load_market_data(channel: str = "Total",
                     period_from: int = None,
                     period_to: int = None,
                     regions: list = None) -> pd.DataFrame:
    db = _get_db_path()
    if not db.exists():
        return pd.DataFrame()

    query = """
        SELECT period, region_code, region_name, channel,
               market_size_dollars, market_share_pct,
               customer_penetration_pct, spend_per_customer,
               spend_per_transaction, transactions_per_customer
        FROM market_share
        WHERE channel = ?
    """
    params = [channel]

    if period_from:
        query += " AND period >= ?"
        params.append(period_from)
    if period_to:
        query += " AND period <= ?"
        params.append(period_to)
    if regions:
        placeholders = ",".join("?" * len(regions))
        query += f" AND region_name IN ({placeholders})"
        params.extend(regions)

    query += " ORDER BY period, region_name"

    with sqlite3.connect(str(db)) as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if not df.empty:
        # Convert period YYYYMM to date for charting
        df["period_date"] = pd.to_datetime(
            df["period"].astype(str), format="%Y%m"
        )
    return df


@st.cache_data(ttl=300)
def get_region_names() -> list:
    db = _get_db_path()
    with sqlite3.connect(str(db)) as conn:
        rows = conn.execute(
            "SELECT DISTINCT region_name FROM market_share ORDER BY region_name"
        ).fetchall()
    return [r[0] for r in rows]


@st.cache_data(ttl=300)
def get_period_range() -> tuple:
    db = _get_db_path()
    with sqlite3.connect(str(db)) as conn:
        row = conn.execute(
            "SELECT MIN(period), MAX(period) FROM market_share"
        ).fetchone()
    return row


# --- Filters ---

min_period, max_period = get_period_range()

col_f1, col_f2, col_f3 = st.columns([1, 1, 3])

with col_f1:
    channel = st.selectbox("Channel", ["Total", "Instore", "Online"])

with col_f2:
    period_options = ["Latest Period", "Last 6 Months", "Last 12 Months", "All Data"]
    period_choice = st.selectbox("Period", period_options)

with col_f3:
    all_regions = get_region_names()
    selected_regions = st.multiselect(
        "Regions (search to filter)", all_regions,
        help=f"{len(all_regions)} regions available. Leave empty for all."
    )

# Compute period range using proper date arithmetic for YYYYMM
def _subtract_months(yyyymm: int, months: int) -> int:
    y, m = divmod(yyyymm, 100)
    total = y * 12 + (m - 1) - months
    return (total // 12) * 100 + (total % 12) + 1

if period_choice == "Latest Period":
    p_from = max_period
elif period_choice == "Last 6 Months":
    p_from = _subtract_months(max_period, 6)
elif period_choice == "Last 12 Months":
    p_from = _subtract_months(max_period, 12)
else:
    p_from = min_period

df = load_market_data(
    channel=channel,
    period_from=p_from,
    period_to=max_period,
    regions=selected_regions if selected_regions else None,
)

if df.empty:
    st.warning("No market share data found for the selected filters.")
    st.stop()


# --- KPIs ---

latest = df[df["period"] == df["period"].max()]

avg_share = latest["market_share_pct"].mean()
avg_penetration = latest["customer_penetration_pct"].mean()
avg_spend = latest["spend_per_customer"].mean()
avg_txn = latest["transactions_per_customer"].mean()
total_market = latest["market_size_dollars"].sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Avg Market Share", f"{avg_share:.1f}%")
k2.metric("Avg Penetration", f"{avg_penetration:.1f}%")
k3.metric("Avg Spend/Customer", f"${avg_spend:.0f}")
k4.metric("Txn/Customer", f"{avg_txn:.1f}")
k5.metric("Total Market Size", f"${total_market/1e6:.0f}M")


# --- Market Share Trend ---

if df["period"].nunique() > 1:
    st.subheader("Market Share Trend")

    if selected_regions and len(selected_regions) <= 10:
        trend = df.groupby(["period_date", "region_name"]).agg(
            share=("market_share_pct", "mean"),
        ).reset_index()
        fig_trend = px.line(
            trend, x="period_date", y="share", color="region_name",
            labels={"period_date": "Period", "share": "Market Share %",
                    "region_name": "Region"},
        )
    else:
        trend = df.groupby("period_date").agg(
            share=("market_share_pct", "mean"),
            penetration=("customer_penetration_pct", "mean"),
        ).reset_index()
        fig_trend = px.line(
            trend, x="period_date", y="share",
            labels={"period_date": "Period", "share": "Avg Market Share %"},
        )
        fig_trend.update_traces(line_color="#7c3aed")

    fig_trend.update_layout(height=400)
    st.plotly_chart(fig_trend, key="mktshare_trend")


# --- Top / Bottom Regions ---

st.subheader("Region Rankings")

region_avg = latest.groupby("region_name").agg(
    share=("market_share_pct", "mean"),
    penetration=("customer_penetration_pct", "mean"),
    spend=("spend_per_customer", "mean"),
    market_size=("market_size_dollars", "sum"),
).reset_index().sort_values("share", ascending=False)

col_top, col_bot = st.columns(2)

with col_top:
    st.markdown("**Top 15 by Market Share**")
    top15 = region_avg.head(15)
    fig_top = px.bar(
        top15.sort_values("share"), x="share", y="region_name",
        orientation="h", labels={"share": "Market Share %", "region_name": ""},
        color_discrete_sequence=["#059669"],
    )
    fig_top.update_layout(height=450)
    st.plotly_chart(fig_top, key="mktshare_top15")

with col_bot:
    st.markdown("**Bottom 15 by Market Share**")
    # Only show regions with non-zero share
    nonzero = region_avg[region_avg["share"] > 0]
    bot15 = nonzero.tail(15)
    fig_bot = px.bar(
        bot15.sort_values("share"), x="share", y="region_name",
        orientation="h", labels={"share": "Market Share %", "region_name": ""},
        color_discrete_sequence=["#dc2626"],
    )
    fig_bot.update_layout(height=450)
    st.plotly_chart(fig_bot, key="mktshare_bottom15")


# --- Competitive Scatter ---

st.subheader("Penetration vs Spend per Customer")
st.caption("Bubble size = market size ($ value)")

fig_scatter = px.scatter(
    region_avg, x="penetration", y="spend",
    size="market_size", hover_name="region_name",
    color="share",
    labels={
        "penetration": "Customer Penetration %",
        "spend": "Spend per Customer ($)",
        "share": "Market Share %",
        "market_size": "Market Size ($)",
    },
    color_continuous_scale="Viridis",
    size_max=40,
)
fig_scatter.update_layout(height=500)
st.plotly_chart(fig_scatter, key="mktshare_penetration_scatter")


# --- Channel Comparison ---

if channel == "Total":
    st.subheader("Instore vs Online Comparison")

    @st.cache_data(ttl=300)
    def load_channel_comparison():
        db = _get_db_path()
        with sqlite3.connect(str(db)) as conn:
            return pd.read_sql_query(
                """SELECT period, channel,
                          AVG(market_share_pct) as share,
                          AVG(customer_penetration_pct) as penetration,
                          AVG(spend_per_customer) as spend
                   FROM market_share
                   WHERE channel != 'Total'
                   GROUP BY period, channel ORDER BY period""",
                conn,
            )

    ch_df = load_channel_comparison()
    if not ch_df.empty:
        ch_df["period_date"] = pd.to_datetime(ch_df["period"].astype(str), format="%Y%m")

        c1, c2 = st.columns(2)
        with c1:
            fig_ch_share = px.line(
                ch_df, x="period_date", y="share", color="channel",
                labels={"period_date": "", "share": "Avg Share %", "channel": ""},
                color_discrete_map={"Instore": "#1e3a8a", "Online": "#7c3aed"},
                title="Market Share by Channel",
            )
            fig_ch_share.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig_ch_share, key="mktshare_channel_share")

        with c2:
            fig_ch_spend = px.line(
                ch_df, x="period_date", y="spend", color="channel",
                labels={"period_date": "", "spend": "Avg Spend ($)", "channel": ""},
                color_discrete_map={"Instore": "#1e3a8a", "Online": "#7c3aed"},
                title="Spend per Customer by Channel",
            )
            fig_ch_spend.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig_ch_spend, key="mktshare_channel_spend")


# --- Data Table ---

with st.expander("Full Region Data Table"):
    display_cols = ["region_name", "share", "penetration", "spend", "market_size"]
    table_df = region_avg[display_cols].copy()
    table_df.columns = ["Region", "Share %", "Penetration %", "Spend/Customer", "Market Size $"]
    st.dataframe(
        table_df.style.format({
            "Share %": "{:.2f}",
            "Penetration %": "{:.1f}",
            "Spend/Customer": "${:.0f}",
            "Market Size $": "${:,.0f}",
        }),
        height=500,
        key="mktshare_region_table",
    )

# ============================================================================
# ASK A QUESTION
# ============================================================================

render_ask_question("market_share")

render_footer("Market Share", f"Period {min_period} to {max_period}", user=user)
