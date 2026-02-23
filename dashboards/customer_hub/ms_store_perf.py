"""
Customer Hub — Market Share > Store Performance
Store health scorecard (A-F grades), channel breakdown, regional macro view.
Tier toggle lets you compare store performance at different radii.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from customer_hub.components import (
    PALETTE, GRADE_COLOURS, section_header, insight_callout, fmt_period,
)
from market_share_layer import (
    get_latest_period,
    store_health_scorecard, store_channel_comparison, network_macro_view,
    STORE_LOCATIONS,
)


@st.cache_data(ttl=3600, show_spinner="Computing store health scores...")
def _cached_scorecard(period):
    return store_health_scorecard(period)


@st.cache_data(ttl=3600, show_spinner="Loading channel data...")
def _cached_channel_comparison(store_name, period):
    return store_channel_comparison(store_name, period)


@st.cache_data(ttl=3600, show_spinner="Building regional view...")
def _cached_macro_view(period, channel):
    return network_macro_view(period, channel)


def render():
    latest = st.session_state.get("ms_latest") or get_latest_period()
    channel = st.session_state.get("ms_channel", "Total")
    state_filter = st.session_state.get("ms_state", "All")

    section_header(
        "Store Health Scorecard",
        "Each store graded A-F based on Core+Primary trade area share, "
        "YoY trend, and customer penetration.",
    )

    # ── Scorecard ──
    scorecard = _cached_scorecard(latest)
    if not scorecard:
        st.warning("No scorecard data available.")
        return

    if state_filter != "All":
        scorecard = [s for s in scorecard if s["state"] == state_filter]

    # KPIs
    grades = [s["grade"] for s in scorecard]
    avg_cp = sum(s["cp_share"] for s in scorecard) / len(scorecard) if scorecard else 0
    growing = sum(1 for s in scorecard if (s["cp_share_change"] or 0) > 0)
    declining = sum(1 for s in scorecard if (s["cp_share_change"] or 0) < 0)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Stores Graded", len(scorecard))
    k2.metric("Avg Core+Primary Share", "{:.1f}%".format(avg_cp))
    k3.metric("Stores Growing", growing,
              delta="{}/{}".format(growing, len(scorecard)))
    k4.metric("Stores Declining", declining,
              delta="-{}".format(declining), delta_color="inverse")

    # Grade distribution
    grade_counts = {}
    for g in ["A", "B", "C", "D", "F"]:
        grade_counts[g] = grades.count(g)

    grade_df = pd.DataFrame([
        {"Grade": g, "Count": c}
        for g, c in grade_counts.items() if c > 0
    ])
    if not grade_df.empty:
        fig_grades = px.bar(
            grade_df, x="Grade", y="Count", color="Grade",
            color_discrete_map=GRADE_COLOURS,
            labels={"Count": "Stores"},
        )
        fig_grades.update_layout(height=250, showlegend=False)
        st.plotly_chart(fig_grades, use_container_width=True, key="ms_grade_dist")

    # Scorecard table
    st.markdown("**All Stores — Ranked by Health Score**")
    sc_df = pd.DataFrame(scorecard)
    sc_display = sc_df[[
        "grade", "store", "state", "cp_share", "cp_share_change",
        "cp_penetration", "cp_spend", "total_postcodes", "score",
    ]].copy()
    sc_display.columns = [
        "Grade", "Store", "State", "CP Share %", "YoY Change (pp)",
        "Penetration %", "Spend $", "Trade Area PCs", "Score",
    ]
    sc_display["YoY Change (pp)"] = sc_display["YoY Change (pp)"].apply(
        lambda x: "{:+.2f}".format(x) if x is not None else "N/A"
    )
    st.dataframe(sc_display, use_container_width=True, hide_index=True,
                 height=500, key="ms_scorecard_tbl")

    # ── Channel Breakdown ──
    st.markdown("---")
    st.subheader("Store Channel Breakdown")
    st.caption("Instore vs Online market share in each store's surrounding postcodes (within 10km).")

    # Tier toggle
    tier_km = st.select_slider(
        "Compare at radius",
        options=[3, 5, 10, 20],
        value=10,
        format_func=lambda x: "0-{}km".format(x),
        key="ms_tier_toggle",
    )

    health_store = st.selectbox(
        "Select Store", [s["store"] for s in scorecard],
        key="ms_health_store",
    )

    if health_store:
        chan_data = _cached_channel_comparison(health_store, latest)
        if not chan_data:
            st.info("No channel data for {}.".format(health_store))
        else:
            cdf = pd.DataFrame(chan_data)
            # Apply tier filter
            cdf = cdf[cdf["distance_km"] <= tier_km]

            if cdf.empty:
                st.info("No postcodes within {}km of {}.".format(
                    tier_km, health_store))
            else:
                ck1, ck2, ck3, ck4 = st.columns(4)
                ck1.metric("Postcodes", len(cdf))
                ck2.metric("Avg Instore Share",
                           "{:.1f}%".format(cdf["instore_share"].mean()))
                ck3.metric("Avg Online Share",
                           "{:.2f}%".format(cdf["online_share"].mean()))
                ck4.metric("Online Penetration",
                           "{:.2f}%".format(cdf["online_pen"].mean()))

                cdf["total_share"] = cdf["instore_share"] + cdf["online_share"]
                top_chan = cdf.nlargest(20, "total_share")

                fig_chan = go.Figure()
                fig_chan.add_trace(go.Bar(
                    name="Instore", x=top_chan["region_name"],
                    y=top_chan["instore_share"], marker_color="#2ECC71",
                    hovertemplate="%{x}<br>Instore: %{y:.1f}%<extra></extra>",
                ))
                fig_chan.add_trace(go.Bar(
                    name="Online", x=top_chan["region_name"],
                    y=top_chan["online_share"], marker_color="#7c3aed",
                    hovertemplate="%{x}<br>Online: %{y:.2f}%<extra></extra>",
                ))
                fig_chan.update_layout(
                    barmode="stack", height=400,
                    xaxis_title="", yaxis_title="Market Share %",
                    legend=dict(orientation="h", y=-0.25),
                )
                st.plotly_chart(fig_chan, use_container_width=True,
                                key="ms_store_chan_bar")

                with st.expander("Full channel data"):
                    chan_display = cdf[[
                        "region_name", "postcode", "distance_km", "tier",
                        "instore_share", "online_share", "instore_pen",
                        "online_pen", "instore_spend", "online_spend",
                    ]].copy()
                    chan_display.columns = [
                        "Region", "Postcode", "Distance km", "Tier",
                        "Instore Share %", "Online Share %", "Instore Pen %",
                        "Online Pen %", "Instore Spend $", "Online Spend $",
                    ]
                    st.dataframe(chan_display, use_container_width=True,
                                 hide_index=True, height=400,
                                 key="ms_chan_detail")

    # ── Regional Macro View ──
    st.markdown("---")
    st.subheader("Regional Macro View")
    st.caption("Stores grouped into geographic clusters with aggregate performance.")

    macro = _cached_macro_view(latest, channel)
    if not macro:
        st.info("No macro data available.")
    else:
        macro_df = pd.DataFrame(macro)
        if not macro_df.empty:
            mk1, mk2, mk3 = st.columns(3)
            mk1.metric("Clusters", len(macro_df))
            best = macro_df.iloc[0]
            mk2.metric("Strongest: {}".format(best["cluster"]),
                        "{:.1f}%".format(best["avg_share"]))
            worst = macro_df.iloc[-1]
            mk3.metric("Weakest: {}".format(worst["cluster"]),
                        "{:.1f}%".format(worst["avg_share"]))

            colours = [
                "#2ECC71" if (r["share_change"] or 0) >= 0 else "#dc2626"
                for _, r in macro_df.iterrows()
            ]
            fig_macro = go.Figure()
            fig_macro.add_trace(go.Bar(
                x=macro_df["cluster"], y=macro_df["avg_share"],
                marker_color=colours,
                text=macro_df["share_change"].apply(
                    lambda x: "{:+.2f}pp".format(x) if x is not None else ""
                ),
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>Share: %{y:.1f}%<br>"
                    "YoY: %{text}<extra></extra>"
                ),
            ))
            fig_macro.update_layout(
                height=400, yaxis_title="Avg Market Share %",
                xaxis_title="", showlegend=False,
            )
            st.plotly_chart(fig_macro, use_container_width=True,
                            key="ms_macro_bar")

            macro_display = macro_df[[
                "cluster", "stores", "postcodes", "avg_share",
                "share_change", "avg_penetration", "avg_spend",
            ]].copy()
            macro_display.columns = [
                "Cluster", "Stores", "Postcodes", "Avg Share %",
                "YoY Change (pp)", "Avg Penetration %", "Avg Spend $",
            ]
            macro_display["YoY Change (pp)"] = macro_display[
                "YoY Change (pp)"].apply(
                lambda x: "{:+.2f}".format(x) if x is not None else "N/A"
            )
            st.dataframe(macro_display, use_container_width=True,
                         hide_index=True, key="ms_macro_tbl")
