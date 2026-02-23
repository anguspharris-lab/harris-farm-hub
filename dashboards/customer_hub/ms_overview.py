"""
Customer Hub — Market Share > Overview
State-level KPIs, national share, top/bottom postcodes.
"David vs Goliath" framing — HFM vs the supermarket giants.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from customer_hub.components import (
    PALETTE, STATE_COLOURS, section_header, insight_callout, one_thing_box,
    metric_row, fmt_period, filter_by_state,
)
from market_share_layer import (
    db_available, get_periods, get_latest_period, get_period_range,
    state_summary, state_trend, postcode_map_data,
)


def _get_ms_filters():
    """Render market share sidebar filters and return (channel, state, latest)."""
    if not db_available():
        st.error("Market share database not found.")
        st.stop()

    latest = get_latest_period()
    min_p, max_p = get_period_range()

    col1, col2 = st.columns(2)
    with col1:
        channel = st.selectbox(
            "Channel", ["Total", "Instore", "Online"],
            help="Total = Instore + Online combined",
            key="ms_channel",
        )
    with col2:
        state_filter = st.selectbox(
            "State", ["All", "NSW", "QLD", "ACT"],
            key="ms_state",
        )

    # Store in session state for sibling MS tabs
    # NOTE: ms_channel and ms_state are NOT set here — Streamlit widgets
    # with key= automatically populate session_state. Writing after widget
    # creation causes StreamlitAPIException.
    st.session_state["ms_latest"] = latest
    st.session_state["ms_min_p"] = min_p
    st.session_state["ms_max_p"] = max_p

    return channel, state_filter, latest


def render():
    channel, state_filter, latest = _get_ms_filters()

    section_header(
        "Market Share Overview",
        "Harris Farm vs the supermarket giants — where we're winning "
        "and where we need to fight harder.",
    )

    insight_callout(
        "<b>David vs Goliath</b> — Harris Farm competes against Coles, Woolworths, "
        "and Aldi in every postcode we serve. Our weapon isn't scale — it's "
        "<i>freshness, community, and customer love</i>. This data shows where "
        "that strategy is working.",
        style="info",
    )

    # ── State KPIs ──
    states = state_summary(latest, channel)
    aus = next((s for s in states if s["state"] == "AUS"), None)

    if aus:
        metric_row([
            ("National Share", "{:.1f}%".format(aus["market_share_pct"])),
            ("Penetration", "{:.1f}%".format(aus["customer_penetration_pct"])),
            ("Spend/Customer", "${:.0f}".format(aus["spend_per_customer"])),
            ("Market Size", "${:.0f}M".format(aus["market_size_dollars"] / 1e6)),
        ])

    # ── State breakdown ──
    st.subheader("State Performance")
    state_rows = [s for s in states if s["state"] != "AUS"]
    if state_rows:
        sdf = pd.DataFrame(state_rows)
        sdf = sdf.rename(columns={
            "state": "State", "market_share_pct": "Share %",
            "customer_penetration_pct": "Penetration %",
            "spend_per_customer": "Spend/Customer",
            "market_size_dollars": "Market Size $",
        })
        st.dataframe(
            sdf[["State", "Share %", "Penetration %", "Spend/Customer", "Market Size $"]],
            use_container_width=True, hide_index=True, key="ms_state_tbl",
        )

    # Winning/struggling stores callout
    if state_rows:
        best = max(state_rows, key=lambda s: s["market_share_pct"])
        worst = min(state_rows, key=lambda s: s["market_share_pct"])
        if best["state"] != worst["state"]:
            insight_callout(
                "Strongest state: <b>{}</b> at {:.1f}% share. "
                "Most room to grow: <b>{}</b> at {:.1f}% share.".format(
                    best["state"], best["market_share_pct"],
                    worst["state"], worst["market_share_pct"],
                ),
                style="success",
            )

    # ── State trend chart ──
    st.subheader("State Market Share Trends")
    strend = state_trend(channel)
    if strend:
        stdf = pd.DataFrame(strend)
        stdf["period_date"] = pd.to_datetime(
            stdf["period"].astype(str), format="%Y%m")
        fig_st = px.line(
            stdf, x="period_date", y="share", color="state",
            labels={"period_date": "", "share": "Market Share %",
                    "state": "State"},
            color_discrete_map=STATE_COLOURS,
        )
        fig_st.update_layout(height=400, legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig_st, use_container_width=True, key="ms_state_trend")

    # ── Top / Bottom postcodes ──
    map_data = postcode_map_data(latest, channel)
    if map_data:
        mdf = pd.DataFrame(map_data)
        mdf = filter_by_state(mdf, state_filter)

        if not mdf.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Top 15 Postcodes by Share**")
                top = mdf.nlargest(15, "market_share_pct")
                fig_top = px.bar(
                    top.sort_values("market_share_pct"),
                    x="market_share_pct", y="region_name", orientation="h",
                    labels={"market_share_pct": "Share %", "region_name": ""},
                    color_discrete_sequence=["#2ECC71"],
                    hover_data={"nearest_store": True, "distance_km": True},
                )
                fig_top.update_layout(height=450)
                st.plotly_chart(fig_top, use_container_width=True,
                                key="ms_top15")

            with c2:
                st.markdown("**Bottom 15 Postcodes (with stores nearby)**")
                within_reach = mdf[mdf["distance_km"] <= 10]
                if not within_reach.empty:
                    bot = within_reach.nsmallest(15, "market_share_pct")
                    fig_bot = px.bar(
                        bot.sort_values("market_share_pct"),
                        x="market_share_pct", y="region_name", orientation="h",
                        labels={"market_share_pct": "Share %",
                                "region_name": ""},
                        color_discrete_sequence=["#dc2626"],
                        hover_data={"nearest_store": True, "distance_km": True},
                    )
                    fig_bot.update_layout(height=450)
                    st.plotly_chart(fig_bot, use_container_width=True,
                                    key="ms_bot15")

    one_thing_box(
        "Market share tells you where you're <i>winning the postcode</i>. "
        "But remember Rule 2: low share doesn't automatically mean opportunity "
        "— it might mean distance or demographic mismatch. Always check the "
        "Catchment Tiers and Growth Frontiers tabs before drawing conclusions."
    )
