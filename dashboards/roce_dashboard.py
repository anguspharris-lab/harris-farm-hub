"""
Harris Farm Hub -- ROCE Analysis Dashboard
Return on Capital Employed at store level.
Capital efficiency, DuPont decomposition, investment simulator.
Data source: Store P&L History (GL) via store_pl_service.

IMPORTANT: Capital employed values are ESTIMATES. Replace with Finance actuals
when available. Default proxy = revenue * 0.25.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

# ---------------------------------------------------------------------------
# Backend import — backend/ is already on sys.path via app.py, but add it
# defensively in case this page is ever run standalone.
# ---------------------------------------------------------------------------
_PROJECT = Path(__file__).resolve().parent.parent
_BACKEND = str(_PROJECT / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from store_pl_service import (
    get_store_pl_annual,
    get_ebit_by_store,
    get_available_fy_years,
    get_network_monthly_trend,
    get_store_monthly_trend,
    get_stores_list,
    get_store_cost_breakdown,
    get_summary_df,
)
from shared.styles import (
    render_header,
    render_footer,
    glass_card,
    plotly_dark_template,
    GREEN,
    GOLD,
    RED,
    ORANGE,
    BLUE,
    CYAN,
    PURPLE,
    NAVY,
    NAVY_CARD,
    NAVY_MID,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    BORDER,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROCE_TARGET = 20.0  # Board target for Year 2 — 20% ROCE

# Capital employed estimates (AUD). These are PLACEHOLDERS.
# Replace with Finance-supplied values when available.
# Key = store_id, Value = estimated capital employed ($)
CAPITAL_ESTIMATES = {}  # Empty — we fall back to the revenue proxy below

# Default proxy: capital employed ~ 25% of annual revenue
CAPITAL_PROXY_RATIO = 0.25

# Chart theming
_DARK = plotly_dark_template()

user = st.session_state.get("auth_user")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

render_header(
    "ROCE Analysis",
    "Return on Capital Employed -- store-level capital efficiency and investment decision support",
    goals=["G1", "G3"],
    strategy_context=(
        "'Fewer, Bigger, Better' demands disciplined capital allocation. "
        "Every store must earn its keep."
    ),
)
st.caption(
    "Source: Store P&L History (GL) | Capital employed values are "
    "**ESTIMATES** -- replace with Finance actuals."
)

# ---------------------------------------------------------------------------
# Cached data loaders
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300)
def load_fy_years():
    """Return available fiscal years, most recent first."""
    years = get_available_fy_years()
    return sorted(years, reverse=True) if years else []


@st.cache_data(ttl=300)
def load_ebit_data(fy_year, channel="Retail"):
    """Load annual EBIT data for all stores in a fiscal year."""
    return get_ebit_by_store(fy_year, channel)


@st.cache_data(ttl=300)
def load_stores():
    """Return list of store dicts."""
    return get_stores_list()


@st.cache_data(ttl=300)
def load_summary(fy_years=None, channel="Retail"):
    """Load monthly summary data (used for trend analysis)."""
    return get_summary_df(fy_years=fy_years, channel=channel)


@st.cache_data(ttl=300)
def load_annual(fy_year, channel="Retail"):
    """Load annual P&L data."""
    return get_store_pl_annual(fy_year, channel)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def estimate_capital_employed(store_id, revenue):
    """Return estimated capital employed for a store.

    Uses the CAPITAL_ESTIMATES dict if a value exists for the store,
    otherwise falls back to revenue * CAPITAL_PROXY_RATIO.
    """
    if store_id in CAPITAL_ESTIMATES and CAPITAL_ESTIMATES[store_id] > 0:
        return float(CAPITAL_ESTIMATES[store_id])
    if revenue and revenue > 0:
        return float(revenue) * CAPITAL_PROXY_RATIO
    return 0.0


def compute_roce(ebit, capital_employed):
    """ROCE = EBIT / Capital Employed * 100."""
    if capital_employed and capital_employed > 0:
        return (ebit / capital_employed) * 100.0
    return 0.0


def roce_colour(roce_val):
    """Traffic-light colour for ROCE value."""
    if roce_val >= ROCE_TARGET:
        return GREEN
    elif roce_val >= 10.0:
        return ORANGE
    else:
        return RED


def roce_label(roce_val):
    """Human-readable verdict."""
    if roce_val >= ROCE_TARGET:
        return "Above target"
    elif roce_val >= 10.0:
        return "Below target"
    else:
        return "Critical"


def fmt_dollar(val):
    """Format a dollar value with commas."""
    if val is None or pd.isna(val):
        return "$0"
    return f"${val:,.0f}"


def fmt_pct(val):
    """Format a percentage."""
    if val is None or pd.isna(val):
        return "0.0%"
    return f"{val:.1f}%"


def build_roce_df(ebit_df):
    """Add capital_employed, roce, roce_colour columns to an EBIT dataframe."""
    df = ebit_df.copy()
    df["capital_employed"] = df.apply(
        lambda r: estimate_capital_employed(r["store_id"], r["revenue"]), axis=1
    )
    df["roce"] = df.apply(
        lambda r: compute_roce(r["ebit"], r["capital_employed"]), axis=1
    )
    df["roce_colour"] = df["roce"].apply(roce_colour)
    df["roce_label"] = df["roce"].apply(roce_label)
    return df


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

fy_years = load_fy_years()

if not fy_years:
    st.warning(
        "No Store P&L data found. Please ingest data via the backend first."
    )
    render_footer("ROCE Analysis", "Store P&L History -- GL Data", user=user)
    st.stop()

# Default to the most recent FY
col_f1, col_f2 = st.columns([2, 6])
with col_f1:
    selected_fy = st.selectbox(
        "Fiscal Year",
        fy_years,
        index=0,
        key="roce_fy_select",
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Load data for selected FY
# ---------------------------------------------------------------------------

ebit_df = load_ebit_data(selected_fy)

if ebit_df.empty:
    st.info(f"No P&L data available for FY{selected_fy}.")
    render_footer("ROCE Analysis", "Store P&L History -- GL Data", user=user)
    st.stop()

roce_df = build_roce_df(ebit_df)

# ---------------------------------------------------------------------------
# Warning banner — capital estimates
# ---------------------------------------------------------------------------

st.warning(
    "**Capital employed figures are ESTIMATES** (revenue x 25% proxy). "
    "Do not use for board-level reporting. Replace with Finance actuals "
    "when available. ROCE magnitudes will change; relative rankings "
    "are directionally useful."
)

# ===================================================================
# TABS
# ===================================================================

tab_overview, tab_by_store, tab_trend, tab_dupont, tab_simulator = st.tabs([
    "Overview",
    "ROCE by Store",
    "ROCE Trend",
    "DuPont Decomposition",
    "Investment Simulator",
])

# ===================================================================
# TAB 1: Overview
# ===================================================================

with tab_overview:
    st.subheader(f"Network ROCE Overview -- FY{selected_fy}")

    # Compute summary metrics
    network_avg_roce = roce_df["roce"].mean() if not roce_df.empty else 0.0
    best_row = roce_df.loc[roce_df["roce"].idxmax()] if not roce_df.empty else None
    worst_row = roce_df.loc[roce_df["roce"].idxmin()] if not roce_df.empty else None

    # Metric cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            "Network Avg ROCE",
            fmt_pct(network_avg_roce),
            delta=f"{'Above' if network_avg_roce >= ROCE_TARGET else 'Below'} {ROCE_TARGET:.0f}% target",
            delta_color="normal" if network_avg_roce >= ROCE_TARGET else "inverse",
        )
    with m2:
        if best_row is not None:
            st.metric(
                "Best Store ROCE",
                fmt_pct(best_row["roce"]),
                delta=str(best_row["store_name"]),
                delta_color="off",
            )
        else:
            st.metric("Best Store ROCE", "N/A")
    with m3:
        if worst_row is not None:
            st.metric(
                "Worst Store ROCE",
                fmt_pct(worst_row["roce"]),
                delta=str(worst_row["store_name"]),
                delta_color="off",
            )
        else:
            st.metric("Worst Store ROCE", "N/A")
    with m4:
        st.metric(
            "Board Target ROCE",
            fmt_pct(ROCE_TARGET),
            delta="Year 2 target",
            delta_color="off",
        )

    st.markdown("")

    # ROCE formula explanation
    st.info(
        "**ROCE = EBIT / Capital Employed x 100**\n\n"
        "- **EBIT** = Earnings Before Interest and Tax (EBITDA + Depreciation)\n"
        "- **Capital Employed** = Total assets minus current liabilities "
        "(estimated here as revenue x 25%)\n\n"
        "ROCE measures how efficiently a store generates profit from the "
        "capital invested in it. Higher is better. Board target is 20% by Year 2."
    )

    st.markdown("")

    # Top 5 / Bottom 5 tables
    col_top, col_bot = st.columns(2)

    with col_top:
        st.markdown("**Top 5 Stores by ROCE**")
        top5 = roce_df.nlargest(5, "roce")[
            ["store_name", "revenue", "ebit", "capital_employed", "roce"]
        ].copy()
        top5["revenue"] = top5["revenue"].apply(fmt_dollar)
        top5["ebit"] = top5["ebit"].apply(fmt_dollar)
        top5["capital_employed"] = top5["capital_employed"].apply(fmt_dollar)
        top5["roce"] = top5["roce"].apply(fmt_pct)
        top5.columns = ["Store", "Revenue", "EBIT", "Capital Employed", "ROCE"]
        st.dataframe(top5, hide_index=True, key="roce_top5")

    with col_bot:
        st.markdown("**Bottom 5 Stores by ROCE**")
        bot5 = roce_df.nsmallest(5, "roce")[
            ["store_name", "revenue", "ebit", "capital_employed", "roce"]
        ].copy()
        bot5["revenue"] = bot5["revenue"].apply(fmt_dollar)
        bot5["ebit"] = bot5["ebit"].apply(fmt_dollar)
        bot5["capital_employed"] = bot5["capital_employed"].apply(fmt_dollar)
        bot5["roce"] = bot5["roce"].apply(fmt_pct)
        bot5.columns = ["Store", "Revenue", "EBIT", "Capital Employed", "ROCE"]
        st.dataframe(bot5, hide_index=True, key="roce_bot5")

# ===================================================================
# TAB 2: ROCE by Store
# ===================================================================

with tab_by_store:
    st.subheader(f"ROCE by Store -- FY{selected_fy}")

    # Horizontal bar chart
    plot_df = roce_df.sort_values("roce", ascending=True).copy()

    fig_bar = go.Figure()

    fig_bar.add_trace(go.Bar(
        y=plot_df["store_name"],
        x=plot_df["roce"],
        orientation="h",
        marker_color=plot_df["roce_colour"],
        text=plot_df["roce"].apply(lambda v: f"{v:.1f}%"),
        textposition="auto",
        textfont=dict(color=TEXT_PRIMARY, size=12),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "ROCE: %{x:.1f}%<br>"
            "<extra></extra>"
        ),
    ))

    # Target line at 20%
    fig_bar.add_vline(
        x=ROCE_TARGET,
        line_dash="dash",
        line_color=GOLD,
        line_width=2,
        annotation_text=f"Target {ROCE_TARGET:.0f}%",
        annotation_position="top right",
        annotation_font_color=GOLD,
    )

    fig_bar.update_layout(
        **_DARK,
        height=max(500, len(plot_df) * 28),
        xaxis_title="ROCE (%)",
        yaxis_title="",
        showlegend=False,
        margin=dict(l=200, r=40, t=40, b=40),
    )

    st.plotly_chart(fig_bar, use_container_width=True, key="roce_bar_chart")

    # Colour legend
    col_l1, col_l2, col_l3, col_l4 = st.columns(4)
    with col_l1:
        st.markdown(
            glass_card(
                f"<span style='color:{GREEN};font-weight:700;font-size:1.1em;'>"
                f"Green: >= {ROCE_TARGET:.0f}%</span>"
                f"<br><span style='color:{TEXT_MUTED};'>Above board target</span>"
            ),
            unsafe_allow_html=True,
        )
    with col_l2:
        st.markdown(
            glass_card(
                f"<span style='color:{ORANGE};font-weight:700;font-size:1.1em;'>"
                f"Amber: 10-{ROCE_TARGET:.0f}%</span>"
                f"<br><span style='color:{TEXT_MUTED};'>Needs improvement</span>"
            ),
            unsafe_allow_html=True,
        )
    with col_l3:
        st.markdown(
            glass_card(
                f"<span style='color:{RED};font-weight:700;font-size:1.1em;'>"
                f"Red: < 10%</span>"
                f"<br><span style='color:{TEXT_MUTED};'>Critical -- review investment</span>"
            ),
            unsafe_allow_html=True,
        )
    with col_l4:
        st.markdown(
            glass_card(
                f"<span style='color:{GOLD};font-weight:700;font-size:1.1em;'>"
                f"Dashed Line: {ROCE_TARGET:.0f}%</span>"
                f"<br><span style='color:{TEXT_MUTED};'>Board Year 2 target</span>"
            ),
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Full sortable data table
    st.markdown("**Full Store Data**")
    tbl = roce_df[[
        "store_name", "revenue", "ebit", "ebit_pct",
        "capital_employed", "roce", "roce_label",
    ]].copy()
    tbl = tbl.sort_values("roce", ascending=False)

    # Format for display
    display_tbl = tbl.copy()
    display_tbl["revenue"] = display_tbl["revenue"].apply(fmt_dollar)
    display_tbl["ebit"] = display_tbl["ebit"].apply(fmt_dollar)
    display_tbl["ebit_pct"] = display_tbl["ebit_pct"].apply(fmt_pct)
    display_tbl["capital_employed"] = display_tbl["capital_employed"].apply(fmt_dollar)
    display_tbl["roce"] = display_tbl["roce"].apply(fmt_pct)
    display_tbl.columns = [
        "Store", "Revenue", "EBIT", "EBIT %",
        "Capital Employed", "ROCE", "Status",
    ]
    st.dataframe(display_tbl, hide_index=True, key="roce_full_table")


# ===================================================================
# TAB 3: ROCE Trend
# ===================================================================

with tab_trend:
    st.subheader("Quarterly ROCE Trend")

    # Load multi-year monthly summary data for trend analysis
    all_fy_years = load_fy_years()
    summary_df = load_summary(fy_years=all_fy_years, channel="Retail")

    if summary_df.empty:
        st.info("No monthly trend data available.")
    else:
        # Aggregate to quarterly level per store
        # Fiscal quarters: Q1 = periods 1-3 (Jul-Sep), Q2 = 4-6, Q3 = 7-9, Q4 = 10-12
        summary_df["fy_quarter"] = ((summary_df["fy_period"] - 1) // 3) + 1
        summary_df["quarter_label"] = (
            "FY" + summary_df["fy_year"].astype(str) + " Q" + summary_df["fy_quarter"].astype(str)
        )

        quarterly = summary_df.groupby(
            ["store_id", "store_name", "fy_year", "fy_quarter", "quarter_label"]
        ).agg(
            revenue=("revenue", "sum"),
            ebitda=("ebitda", "sum"),
            depreciation=("depreciation", "sum"),
        ).reset_index()

        quarterly["ebit"] = quarterly["ebitda"] + quarterly["depreciation"]
        quarterly["capital_employed"] = quarterly.apply(
            lambda r: estimate_capital_employed(r["store_id"], r["revenue"]),
            axis=1,
        )
        quarterly["roce"] = quarterly.apply(
            lambda r: compute_roce(r["ebit"], r["capital_employed"]),
            axis=1,
        )

        # Identify top 5 and bottom 5 by most recent FY average ROCE
        latest_fy = max(all_fy_years)
        latest_avg = quarterly[quarterly["fy_year"] == latest_fy].groupby(
            "store_name"
        )["roce"].mean().reset_index()

        if len(latest_avg) >= 10:
            top5_names = latest_avg.nlargest(5, "roce")["store_name"].tolist()
            bot5_names = latest_avg.nsmallest(5, "roce")["store_name"].tolist()
        elif len(latest_avg) >= 2:
            half = max(1, len(latest_avg) // 2)
            top5_names = latest_avg.nlargest(half, "roce")["store_name"].tolist()
            bot5_names = latest_avg.nsmallest(half, "roce")["store_name"].tolist()
        else:
            top5_names = latest_avg["store_name"].tolist()
            bot5_names = []

        selected_names = list(set(top5_names + bot5_names))
        trend_df = quarterly[quarterly["store_name"].isin(selected_names)].copy()

        # Sort by FY then quarter for proper time ordering
        trend_df = trend_df.sort_values(["fy_year", "fy_quarter"])

        # Network average per quarter
        net_quarterly = quarterly.groupby("quarter_label").agg(
            roce=("roce", "mean"),
            fy_year=("fy_year", "first"),
            fy_quarter=("fy_quarter", "first"),
        ).reset_index()
        net_quarterly = net_quarterly.sort_values(["fy_year", "fy_quarter"])

        # Build chart
        fig_trend = go.Figure()

        # Add traces for each store
        colour_map = {}
        top_colours = [GREEN, CYAN, BLUE, PURPLE, "#A3E635"]
        bot_colours = [RED, ORANGE, GOLD, "#EC4899", "#818CF8"]

        for i, name in enumerate(top5_names):
            colour_map[name] = top_colours[i % len(top_colours)]
        for i, name in enumerate(bot5_names):
            if name not in colour_map:
                colour_map[name] = bot_colours[i % len(bot_colours)]

        for store_name in selected_names:
            sdf = trend_df[trend_df["store_name"] == store_name]
            fig_trend.add_trace(go.Scatter(
                x=sdf["quarter_label"],
                y=sdf["roce"],
                mode="lines+markers",
                name=store_name,
                line=dict(color=colour_map.get(store_name, TEXT_MUTED), width=2),
                marker=dict(size=6),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "%{x}<br>"
                    "ROCE: %{y:.1f}%<extra></extra>"
                ),
            ))

        # Network average line
        fig_trend.add_trace(go.Scatter(
            x=net_quarterly["quarter_label"],
            y=net_quarterly["roce"],
            mode="lines",
            name="Network Average",
            line=dict(color=TEXT_MUTED, width=3, dash="dash"),
            hovertemplate="Network Avg<br>%{x}<br>ROCE: %{y:.1f}%<extra></extra>",
        ))

        # Target line
        fig_trend.add_hline(
            y=ROCE_TARGET,
            line_dash="dot",
            line_color=GOLD,
            line_width=1,
            annotation_text=f"Target {ROCE_TARGET:.0f}%",
            annotation_position="bottom right",
            annotation_font_color=GOLD,
        )

        fig_trend.update_layout(
            **_DARK,
            height=550,
            xaxis_title="Quarter",
            yaxis_title="ROCE (%)",
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(color=TEXT_SECONDARY, size=11),
                orientation="h",
                yanchor="bottom",
                y=-0.35,
                xanchor="center",
                x=0.5,
            ),
            margin=dict(t=40, r=40, b=120, l=60),
        )

        st.plotly_chart(fig_trend, use_container_width=True, key="roce_trend_chart")

        # Legend note
        st.caption(
            "Showing top 5 (green/blue tones) and bottom 5 (red/amber tones) "
            f"stores by average ROCE in FY{latest_fy}. Dashed grey = network average."
        )


# ===================================================================
# TAB 4: DuPont Decomposition
# ===================================================================

with tab_dupont:
    st.subheader("DuPont Decomposition")
    st.markdown(
        "Break ROCE into its two drivers: **Profit Margin** (how much profit per "
        "dollar of revenue) and **Capital Turnover** (how efficiently capital "
        "generates revenue)."
    )
    st.info(
        "**ROCE = Profit Margin x Capital Turnover**\n\n"
        "- Profit Margin = EBIT / Revenue\n"
        "- Capital Turnover = Revenue / Capital Employed\n\n"
        "A store can achieve high ROCE by having high margins, high turnover, or both."
    )

    st.markdown("")

    stores_for_select = roce_df[["store_id", "store_name"]].drop_duplicates()
    store_options = stores_for_select["store_name"].tolist()

    if not store_options:
        st.info("No store data available for DuPont analysis.")
    else:
        selected_store_name = st.selectbox(
            "Select Store",
            store_options,
            index=0,
            key="dupont_store_select",
        )

        # Store data
        store_row = roce_df[roce_df["store_name"] == selected_store_name].iloc[0]
        store_revenue = float(store_row["revenue"]) if store_row["revenue"] else 0.0
        store_ebit = float(store_row["ebit"]) if store_row["ebit"] else 0.0
        store_ce = float(store_row["capital_employed"]) if store_row["capital_employed"] else 0.0
        store_roce = float(store_row["roce"])

        store_margin = (store_ebit / store_revenue * 100) if store_revenue > 0 else 0.0
        store_turnover = (store_revenue / store_ce) if store_ce > 0 else 0.0

        # Network averages
        net_revenue = roce_df["revenue"].sum()
        net_ebit = roce_df["ebit"].sum()
        net_ce = roce_df["capital_employed"].sum()

        net_margin = (net_ebit / net_revenue * 100) if net_revenue > 0 else 0.0
        net_turnover = (net_revenue / net_ce) if net_ce > 0 else 0.0
        net_roce_calc = net_margin * net_turnover / 100.0

        # Metric cards
        d1, d2, d3 = st.columns(3)
        with d1:
            delta_margin = store_margin - net_margin
            st.metric(
                "Profit Margin (EBIT / Revenue)",
                fmt_pct(store_margin),
                delta=f"{delta_margin:+.1f}pp vs network",
                delta_color="normal" if delta_margin >= 0 else "inverse",
            )
        with d2:
            delta_turn = store_turnover - net_turnover
            st.metric(
                "Capital Turnover (Revenue / CE)",
                f"{store_turnover:.2f}x",
                delta=f"{delta_turn:+.2f}x vs network",
                delta_color="normal" if delta_turn >= 0 else "inverse",
            )
        with d3:
            delta_roce = store_roce - (net_margin * net_turnover / 100.0)
            st.metric(
                "ROCE",
                fmt_pct(store_roce),
                delta=f"{delta_roce:+.1f}pp vs network",
                delta_color="normal" if delta_roce >= 0 else "inverse",
            )

        st.markdown("")

        # DuPont comparison chart — grouped bar
        dupont_data = pd.DataFrame({
            "Metric": [
                "Profit Margin (%)", "Profit Margin (%)",
                "Capital Turnover (x)", "Capital Turnover (x)",
            ],
            "Entity": [
                selected_store_name, "Network Average",
                selected_store_name, "Network Average",
            ],
            "Value": [
                store_margin, net_margin,
                store_turnover, net_turnover,
            ],
        })

        fig_dupont = go.Figure()

        # Store bars
        store_vals = dupont_data[dupont_data["Entity"] == selected_store_name]
        fig_dupont.add_trace(go.Bar(
            x=store_vals["Metric"],
            y=store_vals["Value"],
            name=selected_store_name,
            marker_color=GREEN,
            text=store_vals["Value"].apply(lambda v: f"{v:.1f}" if v < 10 else f"{v:.1f}"),
            textposition="auto",
            textfont=dict(color=TEXT_PRIMARY),
        ))

        # Network bars
        net_vals = dupont_data[dupont_data["Entity"] == "Network Average"]
        fig_dupont.add_trace(go.Bar(
            x=net_vals["Metric"],
            y=net_vals["Value"],
            name="Network Average",
            marker_color=BLUE,
            text=net_vals["Value"].apply(lambda v: f"{v:.1f}" if v < 10 else f"{v:.1f}"),
            textposition="auto",
            textfont=dict(color=TEXT_PRIMARY),
        ))

        fig_dupont.update_layout(
            **_DARK,
            barmode="group",
            height=420,
            yaxis_title="Value",
            showlegend=True,
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(color=TEXT_SECONDARY),
            ),
        )

        st.plotly_chart(fig_dupont, use_container_width=True, key="dupont_chart")

        # Insight text
        st.markdown("")
        margin_stronger = abs(store_margin - net_margin) > abs(
            (store_turnover - net_turnover) * 10
        )
        if store_roce >= ROCE_TARGET:
            if margin_stronger:
                insight = (
                    f"**{selected_store_name}** achieves strong ROCE primarily "
                    f"through **superior profit margins** ({store_margin:.1f}% vs "
                    f"network {net_margin:.1f}%). Capital turnover is "
                    f"{'above' if store_turnover > net_turnover else 'near'} average."
                )
            else:
                insight = (
                    f"**{selected_store_name}** achieves strong ROCE primarily "
                    f"through **efficient capital utilisation** ({store_turnover:.2f}x vs "
                    f"network {net_turnover:.2f}x). Margins are "
                    f"{'above' if store_margin > net_margin else 'near'} average."
                )
        else:
            if store_margin < net_margin and store_turnover < net_turnover:
                insight = (
                    f"**{selected_store_name}** underperforms on BOTH levers: "
                    f"margin ({store_margin:.1f}% vs {net_margin:.1f}%) and "
                    f"turnover ({store_turnover:.2f}x vs {net_turnover:.2f}x). "
                    f"A comprehensive review of pricing, cost structure, and "
                    f"asset utilisation is recommended."
                )
            elif store_margin < net_margin:
                insight = (
                    f"**{selected_store_name}**'s ROCE gap is driven by "
                    f"**weaker margins** ({store_margin:.1f}% vs network "
                    f"{net_margin:.1f}%). Focus on revenue mix, pricing, "
                    f"and cost control."
                )
            elif store_turnover < net_turnover:
                insight = (
                    f"**{selected_store_name}**'s ROCE gap is driven by "
                    f"**lower capital turnover** ({store_turnover:.2f}x vs "
                    f"network {net_turnover:.2f}x). The capital base may be "
                    f"too large relative to revenue — review asset utilisation."
                )
            else:
                insight = (
                    f"**{selected_store_name}** is near network averages on both "
                    f"levers. Incremental improvement on either margin or turnover "
                    f"could push ROCE above the {ROCE_TARGET:.0f}% target."
                )

        st.markdown(
            glass_card(
                f"<div style='font-size:1.05em;color:{TEXT_SECONDARY};'>"
                f"{insight}</div>",
                border_color=roce_colour(store_roce),
            ),
            unsafe_allow_html=True,
        )

        # Scatter plot: all stores on Margin vs Turnover axes
        st.markdown("")
        st.markdown("**All Stores: Margin vs Turnover**")

        scatter_df = roce_df.copy()
        scatter_df["profit_margin"] = scatter_df.apply(
            lambda r: (r["ebit"] / r["revenue"] * 100) if r["revenue"] and r["revenue"] > 0 else 0.0,
            axis=1,
        )
        scatter_df["capital_turnover"] = scatter_df.apply(
            lambda r: (r["revenue"] / r["capital_employed"]) if r["capital_employed"] and r["capital_employed"] > 0 else 0.0,
            axis=1,
        )

        fig_scatter = go.Figure()

        fig_scatter.add_trace(go.Scatter(
            x=scatter_df["capital_turnover"],
            y=scatter_df["profit_margin"],
            mode="markers+text",
            text=scatter_df["store_name"].apply(
                lambda n: n.replace("HFM ", "") if n.startswith("HFM ") else n
            ),
            textposition="top center",
            textfont=dict(color=TEXT_MUTED, size=9),
            marker=dict(
                size=12,
                color=scatter_df["roce_colour"],
                line=dict(color=TEXT_MUTED, width=1),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Margin: %{y:.1f}%<br>"
                "Turnover: %{x:.2f}x<br>"
                "<extra></extra>"
            ),
        ))

        # Add reference lines for network averages
        fig_scatter.add_vline(
            x=net_turnover, line_dash="dash", line_color=TEXT_MUTED, line_width=1,
            annotation_text=f"Avg turnover {net_turnover:.2f}x",
            annotation_position="top",
            annotation_font_color=TEXT_MUTED,
            annotation_font_size=10,
        )
        fig_scatter.add_hline(
            y=net_margin, line_dash="dash", line_color=TEXT_MUTED, line_width=1,
            annotation_text=f"Avg margin {net_margin:.1f}%",
            annotation_position="right",
            annotation_font_color=TEXT_MUTED,
            annotation_font_size=10,
        )

        fig_scatter.update_layout(
            **_DARK,
            height=500,
            xaxis_title="Capital Turnover (Revenue / CE)",
            yaxis_title="Profit Margin (EBIT / Revenue %)",
            showlegend=False,
            margin=dict(t=40, r=40, b=40, l=60),
        )

        st.plotly_chart(fig_scatter, use_container_width=True, key="dupont_scatter")
        st.caption(
            "Top-right = high margin AND high turnover (best). "
            "Bottom-left = low on both (needs attention). "
            "Colours match ROCE traffic lights."
        )


# ===================================================================
# TAB 5: Investment Simulator
# ===================================================================

with tab_simulator:
    st.subheader("New Investment ROCE Simulator")
    st.markdown(
        "Model a new store fit-out or refurbishment. Enter your assumptions below "
        "to see whether the investment meets the board's ROCE target."
    )

    st.markdown("")

    # Input fields
    col_in1, col_in2 = st.columns(2)

    with col_in1:
        sim_store_name = st.text_input(
            "Store / Project Name",
            value="New Store",
            key="sim_store_name",
        )
        sim_fitout_cost = st.number_input(
            "Estimated Fit-out Cost ($)",
            min_value=0,
            max_value=50_000_000,
            value=3_000_000,
            step=100_000,
            key="sim_fitout",
            help="Total capital expenditure for the project",
        )

    with col_in2:
        sim_working_capital = st.number_input(
            "Working Capital Requirement ($)",
            min_value=0,
            max_value=10_000_000,
            value=500_000,
            step=50_000,
            key="sim_wc",
            help="Inventory, receivables, etc. less payables",
        )

    total_capital = sim_fitout_cost + sim_working_capital

    st.markdown("")
    st.markdown("**Revenue and EBIT Assumptions by Year**")

    cy1, cy2, cy3 = st.columns(3)

    with cy1:
        st.markdown("**Year 1** (ramp-up)")
        sim_rev_y1 = st.number_input(
            "Revenue ($)", min_value=0, value=8_000_000, step=500_000,
            key="sim_rev_y1",
        )
        sim_ebit_margin_y1 = st.number_input(
            "EBIT Margin (%)", min_value=-50.0, max_value=50.0,
            value=5.0, step=0.5, key="sim_margin_y1",
        )

    with cy2:
        st.markdown("**Year 2** (target year)")
        sim_rev_y2 = st.number_input(
            "Revenue ($)", min_value=0, value=12_000_000, step=500_000,
            key="sim_rev_y2",
        )
        sim_ebit_margin_y2 = st.number_input(
            "EBIT Margin (%)", min_value=-50.0, max_value=50.0,
            value=8.0, step=0.5, key="sim_margin_y2",
        )

    with cy3:
        st.markdown("**Year 3** (mature)")
        sim_rev_y3 = st.number_input(
            "Revenue ($)", min_value=0, value=15_000_000, step=500_000,
            key="sim_rev_y3",
        )
        sim_ebit_margin_y3 = st.number_input(
            "EBIT Margin (%)", min_value=-50.0, max_value=50.0,
            value=10.0, step=0.5, key="sim_margin_y3",
        )

    st.markdown("---")

    # Calculate projected ROCE
    years = ["Year 1", "Year 2", "Year 3"]
    revenues = [sim_rev_y1, sim_rev_y2, sim_rev_y3]
    margins = [sim_ebit_margin_y1, sim_ebit_margin_y2, sim_ebit_margin_y3]
    ebit_vals = [r * m / 100.0 for r, m in zip(revenues, margins)]
    roce_vals = [
        (e / total_capital * 100.0) if total_capital > 0 else 0.0
        for e in ebit_vals
    ]

    # Results
    st.markdown(f"**Projected ROCE for '{sim_store_name}'**")
    st.markdown(f"Total Capital Employed: **{fmt_dollar(total_capital)}** "
                f"(Fit-out: {fmt_dollar(sim_fitout_cost)} + "
                f"Working Capital: {fmt_dollar(sim_working_capital)})")

    st.markdown("")

    rc1, rc2, rc3 = st.columns(3)

    for col, year, rev, margin, ebit, roce_val in zip(
        [rc1, rc2, rc3], years, revenues, margins, ebit_vals, roce_vals
    ):
        with col:
            colour = roce_colour(roce_val)
            meets_target = roce_val >= ROCE_TARGET

            st.markdown(
                glass_card(
                    f"<div style='text-align:center;'>"
                    f"<div style='color:{TEXT_MUTED};font-size:0.9em;'>{year}</div>"
                    f"<div style='color:{colour};font-size:2.2em;font-weight:700;"
                    f"font-family:Georgia,serif;'>{roce_val:.1f}%</div>"
                    f"<div style='color:{TEXT_SECONDARY};font-size:0.9em;'>"
                    f"Rev: {fmt_dollar(rev)} | EBIT: {fmt_dollar(ebit)}</div>"
                    f"<div style='margin-top:8px;padding:4px 12px;border-radius:6px;"
                    f"background:{colour};color:white;display:inline-block;"
                    f"font-weight:600;font-size:0.85em;'>"
                    f"{'MEETS TARGET' if meets_target else 'BELOW TARGET'}</div>"
                    f"</div>",
                    border_color=colour,
                ),
                unsafe_allow_html=True,
            )

    st.markdown("")

    # ROCE projection chart
    fig_sim = go.Figure()

    fig_sim.add_trace(go.Bar(
        x=years,
        y=roce_vals,
        marker_color=[roce_colour(v) for v in roce_vals],
        text=[f"{v:.1f}%" for v in roce_vals],
        textposition="auto",
        textfont=dict(color=TEXT_PRIMARY, size=14),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "ROCE: %{y:.1f}%<br>"
            "<extra></extra>"
        ),
    ))

    fig_sim.add_hline(
        y=ROCE_TARGET,
        line_dash="dash",
        line_color=GOLD,
        line_width=2,
        annotation_text=f"Board Target {ROCE_TARGET:.0f}%",
        annotation_position="top right",
        annotation_font_color=GOLD,
    )

    fig_sim.update_layout(
        **_DARK,
        height=380,
        yaxis_title="ROCE (%)",
        showlegend=False,
        margin=dict(t=40, r=40, b=40, l=60),
    )

    st.plotly_chart(fig_sim, use_container_width=True, key="sim_roce_chart")

    # Year 2 verdict
    y2_meets = roce_vals[1] >= ROCE_TARGET
    if y2_meets:
        st.success(
            f"Year 2 projected ROCE of {roce_vals[1]:.1f}% **MEETS** the board "
            f"target of {ROCE_TARGET:.0f}%. This investment passes the capital "
            f"allocation hurdle."
        )
    else:
        gap = ROCE_TARGET - roce_vals[1]
        # Calculate what EBIT margin would be needed
        needed_ebit = total_capital * ROCE_TARGET / 100.0
        needed_margin = (needed_ebit / sim_rev_y2 * 100.0) if sim_rev_y2 > 0 else 0.0
        st.error(
            f"Year 2 projected ROCE of {roce_vals[1]:.1f}% is **{gap:.1f}pp below** "
            f"the board target of {ROCE_TARGET:.0f}%. To meet the target at "
            f"Year 2 revenue of {fmt_dollar(sim_rev_y2)}, you would need an "
            f"EBIT margin of **{needed_margin:.1f}%** "
            f"(currently modelled at {sim_ebit_margin_y2:.1f}%)."
        )

    # Sensitivity table
    st.markdown("")
    with st.expander("Sensitivity Analysis -- How EBIT Margin Affects ROCE"):
        margin_range = [float(m) for m in range(-5, 21)]
        sens_data = []
        for m in margin_range:
            for yr_label, yr_rev in zip(years, revenues):
                ebit_s = yr_rev * m / 100.0
                roce_s = (ebit_s / total_capital * 100.0) if total_capital > 0 else 0.0
                sens_data.append({
                    "EBIT Margin (%)": f"{m:.0f}%",
                    "Year": yr_label,
                    "Revenue": yr_rev,
                    "EBIT": ebit_s,
                    "ROCE": roce_s,
                })

        sens_df = pd.DataFrame(sens_data)

        fig_sens = go.Figure()
        for yr_label, yr_colour in zip(years, [BLUE, GREEN, CYAN]):
            yr_data = sens_df[sens_df["Year"] == yr_label]
            fig_sens.add_trace(go.Scatter(
                x=yr_data["EBIT Margin (%)"],
                y=yr_data["ROCE"],
                mode="lines+markers",
                name=yr_label,
                line=dict(color=yr_colour, width=2),
                marker=dict(size=4),
            ))

        fig_sens.add_hline(
            y=ROCE_TARGET,
            line_dash="dash",
            line_color=GOLD,
            line_width=1,
            annotation_text=f"Target {ROCE_TARGET:.0f}%",
            annotation_font_color=GOLD,
        )

        fig_sens.update_layout(
            **_DARK,
            height=380,
            xaxis_title="EBIT Margin (%)",
            yaxis_title="ROCE (%)",
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(color=TEXT_SECONDARY),
            ),
        )

        st.plotly_chart(fig_sens, use_container_width=True, key="sens_chart")
        st.caption(
            "Each line shows how ROCE changes as EBIT margin improves, "
            "at the revenue level you entered for that year."
        )


# ===================================================================
# Footer
# ===================================================================

render_footer("ROCE Analysis", "Store P&L History -- GL Data", user=user)
