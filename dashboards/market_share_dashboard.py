"""
Harris Farm Hub — Market Share Intelligence Dashboard
Postcode-level market share analysis with spatial mapping, trade area analysis,
trend detection, opportunity scoring, and issue flagging.

Data: 1,040 postcodes × 37 months × 3 channels (CBAS modelled estimates)
Primary metric: Market Share % (reliable). Dollar values are directional only.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from market_share_layer import (
    db_available, get_periods, get_latest_period, get_period_range,
    get_regions, postcode_map_data, store_trade_area, store_trade_area_trend,
    yoy_comparison, detect_shifts, flag_issues, opportunity_analysis,
    state_summary, state_trend, postcode_trend, nearest_store,
    STORE_LOCATIONS, get_postcode_coords,
)
from shared.styles import render_header, render_footer, HFM_GREEN
from shared.ask_question import render_ask_question

user = st.session_state.get("auth_user")

render_header(
    "Market Share Intelligence",
    "Postcode-level competitive analysis | Spatial mapping | Trade areas | Trends"
)

if not db_available():
    st.error("Database not found.")
    st.stop()

# ── Sidebar Filters ──────────────────────────────────────────────────────────

periods = get_periods()
latest = get_latest_period()
min_p, max_p = get_period_range()

# Period display helper
def _fmt_period(p):
    s = str(p)
    return f"{s[:4]}-{s[4:]}"

col_f1, col_f2 = st.columns([1, 1])
with col_f1:
    channel = st.selectbox("Channel", ["Total", "Instore", "Online"],
                           help="Total = Instore + Online combined")
with col_f2:
    state_filter = st.selectbox("State", ["All", "NSW", "QLD", "ACT"])

# ── Tab Layout ────────────────────────────────────────────────────────────────

tab_overview, tab_map, tab_store, tab_trends, tab_opps, tab_issues, tab_data = st.tabs([
    "Overview", "Spatial Map", "Store Trade Areas",
    "Trends & Shifts", "Opportunities", "Issues", "Data Explorer"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

with tab_overview:
    # State-level KPIs
    states = state_summary(latest, channel)
    aus = next((s for s in states if s["state"] == "AUS"), None)

    if aus:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("National Share", f"{aus['market_share_pct']:.1f}%")
        k2.metric("Penetration", f"{aus['customer_penetration_pct']:.1f}%")
        k3.metric("Spend/Customer", f"${aus['spend_per_customer']:.0f}")
        k4.metric("Market Size", f"${aus['market_size_dollars']/1e6:.0f}M")

    # State breakdown
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
            use_container_width=True, hide_index=True,
        )

    # State trend chart
    st.subheader("State Market Share Trends")
    strend = state_trend(channel)
    if strend:
        stdf = pd.DataFrame(strend)
        stdf["period_date"] = pd.to_datetime(stdf["period"].astype(str), format="%Y%m")
        fig_st = px.line(
            stdf, x="period_date", y="share", color="state",
            labels={"period_date": "", "share": "Market Share %", "state": "State"},
            color_discrete_map={"NSW": "#4ba021", "QLD": "#7c3aed", "ACT": "#d97706"},
        )
        fig_st.update_layout(height=400, legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig_st, use_container_width=True, key="overview_state_trend")

    # Top/Bottom postcodes
    map_data = postcode_map_data(latest, channel)
    if map_data:
        mdf = pd.DataFrame(map_data)
        if state_filter != "All":
            # Filter by state using postcode ranges
            state_ranges = {
                "NSW": lambda pc: 2000 <= int(pc) <= 2999,
                "QLD": lambda pc: 4000 <= int(pc) <= 4999,
                "ACT": lambda pc: 2600 <= int(pc) <= 2618 or int(pc) in (2900, 2901, 2902, 2903, 2904, 2905, 2906, 2911, 2912, 2913, 2914),
            }
            fn = state_ranges.get(state_filter)
            if fn:
                mdf = mdf[mdf["postcode"].apply(lambda x: fn(x))]

        if not mdf.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Top 15 Postcodes by Share**")
                top = mdf.nlargest(15, "market_share_pct")
                fig_top = px.bar(
                    top.sort_values("market_share_pct"),
                    x="market_share_pct", y="region_name", orientation="h",
                    labels={"market_share_pct": "Share %", "region_name": ""},
                    color_discrete_sequence=["#4ba021"],
                    hover_data={"nearest_store": True, "distance_km": True},
                )
                fig_top.update_layout(height=450)
                st.plotly_chart(fig_top, use_container_width=True, key="overview_top15")

            with c2:
                st.markdown("**Bottom 15 Postcodes (with stores nearby)**")
                within_reach = mdf[mdf["distance_km"] <= 10]
                if not within_reach.empty:
                    bot = within_reach.nsmallest(15, "market_share_pct")
                    fig_bot = px.bar(
                        bot.sort_values("market_share_pct"),
                        x="market_share_pct", y="region_name", orientation="h",
                        labels={"market_share_pct": "Share %", "region_name": ""},
                        color_discrete_sequence=["#dc2626"],
                        hover_data={"nearest_store": True, "distance_km": True},
                    )
                    fig_bot.update_layout(height=450)
                    st.plotly_chart(fig_bot, use_container_width=True, key="overview_bot15")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: SPATIAL MAP
# ══════════════════════════════════════════════════════════════════════════════

with tab_map:
    st.subheader(f"Market Share Map — {_fmt_period(latest)}")
    st.caption("Bubble size = market share %. Click postcodes for details. Store markers in green.")

    map_data = postcode_map_data(latest, channel)
    if not map_data:
        st.warning("No spatial data available.")
    else:
        mdf = pd.DataFrame(map_data)

        # Filter by state if selected
        if state_filter != "All":
            state_ranges = {
                "NSW": lambda pc: 2000 <= int(pc) <= 2999,
                "QLD": lambda pc: 4000 <= int(pc) <= 4999,
                "ACT": lambda pc: 2600 <= int(pc) <= 2618 or int(pc) in range(2900, 2915),
            }
            fn = state_ranges.get(state_filter)
            if fn:
                mdf = mdf[mdf["postcode"].apply(lambda x: fn(x))]

        # Map metric selector
        col_metric, col_tier = st.columns(2)
        with col_metric:
            map_metric = st.selectbox("Colour by", [
                "Market Share %", "Penetration %", "Spend/Customer", "Distance Tier"
            ], key="map_metric")
        with col_tier:
            tier_filter = st.selectbox("Distance Tier", [
                "All", "Core (0-3km)", "Primary (3-5km)", "Secondary (5-10km)",
                "Extended (10-20km)"
            ], key="map_tier")

        if tier_filter != "All":
            mdf = mdf[mdf["distance_tier"] == tier_filter]

        if mdf.empty:
            st.info("No postcodes match the selected filters.")
        else:
            # Build hover text
            mdf["hover"] = (
                mdf["region_name"] + " (" + mdf["postcode"] + ")<br>" +
                "Share: " + mdf["market_share_pct"].apply(lambda x: f"{x:.1f}%") + "<br>" +
                "Penetration: " + mdf["penetration_pct"].apply(lambda x: f"{x:.1f}%") + "<br>" +
                "Spend: " + mdf["spend_per_customer"].apply(lambda x: f"${x:.0f}") + "<br>" +
                "Nearest: " + mdf["nearest_store"] + " (" + mdf["distance_km"].apply(lambda x: f"{x:.0f}km") + ")"
            )

            # Determine color column
            if map_metric == "Market Share %":
                color_col = "market_share_pct"
                color_scale = "Greens"
            elif map_metric == "Penetration %":
                color_col = "penetration_pct"
                color_scale = "Blues"
            elif map_metric == "Spend/Customer":
                color_col = "spend_per_customer"
                color_scale = "Oranges"
            else:
                color_col = "distance_tier"
                color_scale = None

            # Size by market share (minimum size for visibility)
            mdf["bubble_size"] = mdf["market_share_pct"].clip(lower=0.3) * 2

            if color_col == "distance_tier":
                fig = px.scatter_mapbox(
                    mdf, lat="lat", lon="lon",
                    color="distance_tier",
                    size="bubble_size",
                    hover_name="region_name",
                    custom_data=["postcode", "market_share_pct", "penetration_pct",
                                 "spend_per_customer", "nearest_store", "distance_km"],
                    color_discrete_map={
                        "Core (0-3km)": "#16a34a",
                        "Primary (3-5km)": "#2563eb",
                        "Secondary (5-10km)": "#d97706",
                        "Extended (10-20km)": "#9333ea",
                        "No Presence (20km+)": "#6b7280",
                    },
                    zoom=8, size_max=20,
                )
            else:
                fig = px.scatter_mapbox(
                    mdf, lat="lat", lon="lon",
                    color=color_col,
                    size="bubble_size",
                    hover_name="region_name",
                    custom_data=["postcode", "market_share_pct", "penetration_pct",
                                 "spend_per_customer", "nearest_store", "distance_km"],
                    color_continuous_scale=color_scale,
                    zoom=8, size_max=20,
                )

            # Update hover template
            fig.update_traces(
                hovertemplate=(
                    "<b>%{hovertext}</b> (%{customdata[0]})<br>"
                    "Share: %{customdata[1]:.1f}%<br>"
                    "Penetration: %{customdata[2]:.1f}%<br>"
                    "Spend: $%{customdata[3]:.0f}<br>"
                    "Nearest: %{customdata[4]} (%{customdata[5]:.0f}km)"
                    "<extra></extra>"
                )
            )

            # Add store markers
            store_lats = [s["lat"] for s in STORE_LOCATIONS.values()]
            store_lons = [s["lon"] for s in STORE_LOCATIONS.values()]
            store_names = list(STORE_LOCATIONS.keys())

            fig.add_trace(go.Scattermapbox(
                lat=store_lats, lon=store_lons,
                mode="markers+text",
                marker=dict(size=12, color="#4ba021", symbol="circle"),
                text=[n.replace("HFM ", "") for n in store_names],
                textposition="top center",
                textfont=dict(size=9, color="#4ba021"),
                name="HFM Stores",
                hovertemplate="<b>%{text}</b><extra>HFM Store</extra>",
            ))

            # Center map
            center_lat = mdf["lat"].mean()
            center_lon = mdf["lon"].mean()
            fig.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(center=dict(lat=center_lat, lon=center_lon), zoom=9),
                height=650,
                margin=dict(l=0, r=0, t=0, b=0),
                legend=dict(orientation="h", y=-0.02),
            )
            st.plotly_chart(fig, use_container_width=True, key="spatial_map")

            # Summary stats below map
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Postcodes Shown", len(mdf))
            c2.metric("Avg Share", f"{mdf['market_share_pct'].mean():.1f}%")
            c3.metric("Avg Penetration", f"{mdf['penetration_pct'].mean():.1f}%")
            c4.metric("Avg Spend", f"${mdf['spend_per_customer'].mean():.0f}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: STORE TRADE AREAS
# ══════════════════════════════════════════════════════════════════════════════

with tab_store:
    st.subheader("Store Trade Area Analysis")
    st.caption("Select a store to see surrounding postcodes with performance data.")

    store_names = sorted(STORE_LOCATIONS.keys())
    selected_store = st.selectbox("Select Store", store_names, key="trade_area_store")

    if selected_store:
        store_info = STORE_LOCATIONS[selected_store]

        # Get trade area postcodes
        ta_data = store_trade_area(selected_store, latest, channel)
        if not ta_data:
            st.info(f"No market share data for postcodes near {selected_store}.")
        else:
            tdf = pd.DataFrame(ta_data)

            # Trade area summary by tier
            tier_summary = tdf.groupby("tier").agg(
                postcodes=("postcode", "count"),
                avg_share=("market_share_pct", "mean"),
                avg_penetration=("penetration_pct", "mean"),
                avg_spend=("spend_per_customer", "mean"),
                total_market=("market_size", "sum"),
            ).reset_index()

            # KPIs
            core = tdf[tdf["tier"] == "Core (0-3km)"]
            primary = tdf[tdf["tier"] == "Primary (3-5km)"]

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Trade Area Postcodes", len(tdf))
            if not core.empty:
                k2.metric("Core Avg Share", f"{core['market_share_pct'].mean():.1f}%")
            else:
                k2.metric("Core Avg Share", "N/A")
            if not primary.empty:
                k3.metric("Primary Avg Share", f"{primary['market_share_pct'].mean():.1f}%")
            else:
                k3.metric("Primary Avg Share", "N/A")
            k4.metric("Total Market", f"${tdf['market_size'].sum()/1e6:.1f}M")

            # Tier breakdown table
            st.markdown("**Performance by Distance Tier**")
            tier_display = tier_summary.rename(columns={
                "tier": "Tier", "postcodes": "Postcodes", "avg_share": "Avg Share %",
                "avg_penetration": "Avg Penetration %", "avg_spend": "Avg Spend $",
                "total_market": "Total Market $",
            })
            st.dataframe(tier_display, use_container_width=True, hide_index=True)

            # Map of trade area
            st.markdown("**Trade Area Map**")
            tdf["hover"] = (
                tdf["region_name"] + " (" + tdf["postcode"] + ")<br>" +
                "Share: " + tdf["market_share_pct"].apply(lambda x: f"{x:.1f}%") + "<br>" +
                tdf["distance_km"].apply(lambda x: f"{x:.1f}km") + " — " + tdf["tier"]
            )
            tdf["size"] = tdf["market_share_pct"].clip(lower=0.5) * 2

            fig_ta = px.scatter_mapbox(
                tdf, lat="postcode", lon="postcode",  # placeholder
                hover_name="region_name",
                color="tier",
                color_discrete_map={
                    "Core (0-3km)": "#16a34a",
                    "Primary (3-5km)": "#2563eb",
                    "Secondary (5-10km)": "#d97706",
                    "Extended (10-20km)": "#9333ea",
                },
            )
            # Actually need lat/lon — join with coords
            coords = get_postcode_coords()
            tdf["lat"] = tdf["postcode"].map(lambda x: coords.get(x, {}).get("lat"))
            tdf["lon"] = tdf["postcode"].map(lambda x: coords.get(x, {}).get("lon"))
            tdf = tdf.dropna(subset=["lat", "lon"])

            fig_ta = px.scatter_mapbox(
                tdf, lat="lat", lon="lon",
                color="tier",
                size="size",
                hover_name="region_name",
                custom_data=["postcode", "market_share_pct", "penetration_pct", "distance_km", "tier"],
                color_discrete_map={
                    "Core (0-3km)": "#16a34a",
                    "Primary (3-5km)": "#2563eb",
                    "Secondary (5-10km)": "#d97706",
                    "Extended (10-20km)": "#9333ea",
                },
                zoom=11, size_max=18,
            )
            fig_ta.update_traces(
                hovertemplate=(
                    "<b>%{hovertext}</b> (%{customdata[0]})<br>"
                    "Share: %{customdata[1]:.1f}%<br>"
                    "Penetration: %{customdata[2]:.1f}%<br>"
                    "Distance: %{customdata[3]:.1f}km (%{customdata[4]})"
                    "<extra></extra>"
                )
            )

            # Add store marker
            fig_ta.add_trace(go.Scattermapbox(
                lat=[store_info["lat"]], lon=[store_info["lon"]],
                mode="markers+text",
                marker=dict(size=16, color="#dc2626", symbol="circle"),
                text=[selected_store.replace("HFM ", "")],
                textposition="top center",
                textfont=dict(size=11, color="#dc2626", family="Arial Black"),
                name=selected_store,
                hovertemplate=f"<b>{selected_store}</b><extra>Store</extra>",
            ))

            fig_ta.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(center=dict(lat=store_info["lat"], lon=store_info["lon"]), zoom=12),
                height=550,
                margin=dict(l=0, r=0, t=0, b=0),
                legend=dict(orientation="h", y=-0.02),
            )
            st.plotly_chart(fig_ta, use_container_width=True, key="trade_area_map")

            # Trade area trend
            st.markdown("**Trade Area Share Trend**")
            ta_tier = st.selectbox("Trend by Tier", ["All Tiers", "Core (0-3km)", "Primary (3-5km)",
                                                      "Secondary (5-10km)", "Extended (10-20km)"],
                                   key="ta_trend_tier")
            tier_val = None if ta_tier == "All Tiers" else ta_tier
            ta_trend = store_trade_area_trend(selected_store, channel, tier_val)
            if ta_trend:
                ttdf = pd.DataFrame(ta_trend)
                ttdf["period_date"] = pd.to_datetime(ttdf["period"].astype(str), format="%Y%m")
                fig_tt = px.line(
                    ttdf, x="period_date", y="avg_share",
                    labels={"period_date": "", "avg_share": "Avg Market Share %"},
                    color_discrete_sequence=["#4ba021"],
                )
                fig_tt.update_layout(height=350)
                st.plotly_chart(fig_tt, use_container_width=True, key="ta_trend_chart")

            # Postcode detail table
            st.markdown("**All Postcodes in Trade Area**")
            display = tdf[["postcode", "region_name", "distance_km", "tier",
                           "market_share_pct", "penetration_pct", "spend_per_customer",
                           "market_size"]].copy()
            display.columns = ["Postcode", "Region", "Distance (km)", "Tier",
                              "Share %", "Penetration %", "Spend $", "Market Size $"]
            st.dataframe(display, use_container_width=True, hide_index=True, height=400)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: TRENDS & SHIFTS
# ══════════════════════════════════════════════════════════════════════════════

with tab_trends:
    st.subheader("Year-on-Year Share Changes")

    # Period selection for YoY
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        current_period = st.selectbox("Current Period", periods[::-1], key="yoy_current")
    with col_p2:
        # Default to same month last year
        default_prior = current_period - 100
        prior_options = [p for p in periods if p < current_period]
        if default_prior in prior_options:
            prior_idx = prior_options[::-1].index(default_prior)
        else:
            prior_idx = 0
        prior_period = st.selectbox("Compare To", prior_options[::-1], index=prior_idx, key="yoy_prior")

    yoy_data = yoy_comparison(current_period, prior_period, channel)
    if not yoy_data:
        st.info("No comparison data available for selected periods.")
    else:
        ydf = pd.DataFrame(yoy_data)

        # Filter by state
        if state_filter != "All":
            state_ranges = {
                "NSW": lambda pc: 2000 <= int(pc) <= 2999,
                "QLD": lambda pc: 4000 <= int(pc) <= 4999,
                "ACT": lambda pc: 2600 <= int(pc) <= 2618 or int(pc) in range(2900, 2915),
            }
            fn = state_ranges.get(state_filter)
            if fn:
                ydf = ydf[ydf["region_code"].apply(lambda x: fn(x))]

        # Filter out no-presence postcodes
        ydf = ydf[ydf["distance_tier"] != "No Presence (20km+)"]

        if not ydf.empty:
            # Summary KPIs
            gainers = len(ydf[ydf["share_change"] > 0])
            losers = len(ydf[ydf["share_change"] < 0])
            avg_change = ydf["share_change"].mean()
            worst_decline = ydf["share_change"].min()

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Avg Share Change", f"{avg_change:+.2f}pp")
            k2.metric("Postcodes Gaining", gainers, delta=f"{gainers}/{len(ydf)}")
            k3.metric("Postcodes Losing", losers, delta=f"-{losers}", delta_color="inverse")
            k4.metric("Worst Decline", f"{worst_decline:+.1f}pp")

            # Top gainers and losers
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Top 15 Share Gainers**")
                top_gain = ydf.nlargest(15, "share_change")
                fig_gain = px.bar(
                    top_gain.sort_values("share_change"),
                    x="share_change", y="region_name", orientation="h",
                    labels={"share_change": "Share Change (pp)", "region_name": ""},
                    color_discrete_sequence=["#16a34a"],
                    hover_data={"nearest_store": True, "distance_tier": True},
                )
                fig_gain.update_layout(height=450)
                st.plotly_chart(fig_gain, use_container_width=True, key="yoy_gainers")

            with c2:
                st.markdown("**Top 15 Share Losers**")
                top_loss = ydf.nsmallest(15, "share_change")
                fig_loss = px.bar(
                    top_loss.sort_values("share_change", ascending=False),
                    x="share_change", y="region_name", orientation="h",
                    labels={"share_change": "Share Change (pp)", "region_name": ""},
                    color_discrete_sequence=["#dc2626"],
                    hover_data={"nearest_store": True, "distance_tier": True},
                )
                fig_loss.update_layout(height=450)
                st.plotly_chart(fig_loss, use_container_width=True, key="yoy_losers")

            # Share change map
            st.markdown("**Share Change Map**")
            ydf_map = ydf.dropna(subset=["lat", "lon"])
            if not ydf_map.empty:
                ydf_map["abs_change"] = ydf_map["share_change"].abs().clip(lower=0.3) * 3
                fig_yoy_map = px.scatter_mapbox(
                    ydf_map, lat="lat", lon="lon",
                    color="share_change",
                    size="abs_change",
                    hover_name="region_name",
                    custom_data=["region_code", "current_share", "prior_share",
                                 "share_change", "nearest_store", "distance_tier"],
                    color_continuous_scale="RdYlGn",
                    color_continuous_midpoint=0,
                    zoom=9, size_max=18,
                )
                fig_yoy_map.update_traces(
                    hovertemplate=(
                        "<b>%{hovertext}</b> (%{customdata[0]})<br>"
                        "Current: %{customdata[1]:.1f}% | Prior: %{customdata[2]:.1f}%<br>"
                        "Change: %{customdata[3]:+.1f}pp<br>"
                        "Store: %{customdata[4]} (%{customdata[5]})"
                        "<extra></extra>"
                    )
                )
                # Add store markers
                store_lats = [s["lat"] for s in STORE_LOCATIONS.values()]
                store_lons = [s["lon"] for s in STORE_LOCATIONS.values()]
                fig_yoy_map.add_trace(go.Scattermapbox(
                    lat=store_lats, lon=store_lons,
                    mode="markers", marker=dict(size=10, color="#000000", symbol="circle"),
                    name="HFM Stores",
                    hovertemplate="<b>%{text}</b><extra>Store</extra>",
                    text=list(STORE_LOCATIONS.keys()),
                ))
                fig_yoy_map.update_layout(
                    mapbox_style="open-street-map",
                    mapbox=dict(center=dict(lat=ydf_map["lat"].mean(), lon=ydf_map["lon"].mean()), zoom=9),
                    height=550,
                    margin=dict(l=0, r=0, t=0, b=0),
                )
                st.plotly_chart(fig_yoy_map, use_container_width=True, key="yoy_map")

    # Sudden shifts section
    st.markdown("---")
    st.subheader("Sudden Shifts (Month-on-Month)")
    st.caption("Postcodes with >2pp month-on-month share change — may indicate data anomaly or real market event.")

    shift_threshold = st.slider("Shift Threshold (pp)", 1.0, 5.0, 2.0, 0.5, key="shift_threshold")
    shifts = detect_shifts(channel, shift_threshold)
    if shifts:
        sdf = pd.DataFrame(shifts[:100])  # Limit display
        sdf["period_label"] = sdf["current_period"].apply(_fmt_period)
        st.dataframe(
            sdf[["period_label", "region_name", "region_code", "prior_share", "current_share", "shift"]].rename(
                columns={
                    "period_label": "Period", "region_name": "Region", "region_code": "Postcode",
                    "prior_share": "Prior %", "current_share": "Current %", "shift": "Shift (pp)",
                }
            ),
            use_container_width=True, hide_index=True, height=400,
        )
    else:
        st.info(f"No shifts above {shift_threshold}pp threshold found.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: OPPORTUNITIES
# ══════════════════════════════════════════════════════════════════════════════

with tab_opps:
    st.subheader("Opportunity Analysis")
    st.caption("Quadrant analysis: Penetration vs Share identifies strategic opportunity types.")

    opps = opportunity_analysis(latest, channel)
    if not opps:
        st.info("No opportunity data.")
    else:
        odf = pd.DataFrame(opps)

        # Filter by state
        if state_filter != "All":
            state_ranges = {
                "NSW": lambda pc: 2000 <= int(pc) <= 2999,
                "QLD": lambda pc: 4000 <= int(pc) <= 4999,
                "ACT": lambda pc: 2600 <= int(pc) <= 2618 or int(pc) in range(2900, 2915),
            }
            fn = state_ranges.get(state_filter)
            if fn:
                odf = odf[odf["postcode"].apply(lambda x: fn(x))]

        # Quadrant scatter
        fig_quad = px.scatter(
            odf, x="penetration_pct", y="market_share_pct",
            color="opportunity_type",
            size="market_size",
            hover_name="region_name",
            custom_data=["postcode", "spend_per_customer", "nearest_store",
                         "distance_km", "distance_tier", "opportunity_type"],
            labels={
                "penetration_pct": "Customer Penetration %",
                "market_share_pct": "Market Share %",
                "opportunity_type": "Type",
            },
            color_discrete_map={
                "Stronghold": "#16a34a",
                "Growth Opportunity": "#2563eb",
                "Basket Opportunity": "#d97706",
                "Retention Risk": "#dc2626",
                "Monitor": "#9ca3af",
            },
            size_max=30,
        )
        fig_quad.update_traces(
            hovertemplate=(
                "<b>%{hovertext}</b> (%{customdata[0]})<br>"
                "Share: %{y:.1f}% | Penetration: %{x:.1f}%<br>"
                "Spend: $%{customdata[1]:.0f}<br>"
                "Store: %{customdata[2]} (%{customdata[3]:.0f}km, %{customdata[4]})<br>"
                "Type: %{customdata[5]}"
                "<extra></extra>"
            )
        )

        # Add quadrant reference lines
        fig_quad.add_hline(y=5, line_dash="dash", line_color="#d1d5db", annotation_text="5% share")
        fig_quad.add_vline(x=15, line_dash="dash", line_color="#d1d5db", annotation_text="15% penetration")

        fig_quad.update_layout(height=600, legend=dict(orientation="h", y=-0.12))
        st.plotly_chart(fig_quad, use_container_width=True, key="opportunity_scatter")

        # Summary counts
        type_counts = odf["opportunity_type"].value_counts()
        cols = st.columns(5)
        for i, (opp_type, count) in enumerate(type_counts.items()):
            if i < 5:
                cols[i].metric(opp_type, count)

        # Detailed tables by opportunity type
        for opp_type in ["Stronghold", "Growth Opportunity", "Basket Opportunity", "Retention Risk"]:
            subset = odf[odf["opportunity_type"] == opp_type]
            if not subset.empty:
                with st.expander(f"{opp_type} — {len(subset)} postcodes"):
                    display = subset[["region_name", "postcode", "market_share_pct",
                                      "penetration_pct", "spend_per_customer",
                                      "nearest_store", "distance_km", "distance_tier"]].copy()
                    display.columns = ["Region", "Postcode", "Share %", "Penetration %",
                                       "Spend $", "Nearest Store", "Distance km", "Tier"]
                    st.dataframe(
                        display.sort_values("Share %", ascending=False),
                        use_container_width=True, hide_index=True,
                    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6: ISSUES
# ══════════════════════════════════════════════════════════════════════════════

with tab_issues:
    st.subheader("Issue Radar")
    st.caption("Postcodes with concerning trends — Core and Primary trade areas prioritised.")

    issues = flag_issues(latest, channel)
    if not issues:
        st.success("No significant issues detected for the current period.")
    else:
        # Filter by state
        if state_filter != "All":
            state_ranges = {
                "NSW": lambda pc: 2000 <= int(pc) <= 2999,
                "QLD": lambda pc: 4000 <= int(pc) <= 4999,
                "ACT": lambda pc: 2600 <= int(pc) <= 2618 or int(pc) in range(2900, 2915),
            }
            fn = state_ranges.get(state_filter)
            if fn:
                issues = [i for i in issues if fn(i["postcode"])]

        urgent = [i for i in issues if i["severity"] == "Urgent"]
        warnings = [i for i in issues if i["severity"] == "Warning"]

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Issues", len(issues))
        k2.metric("Urgent", len(urgent), delta=f"{len(urgent)} need attention", delta_color="inverse")
        k3.metric("Warnings", len(warnings))

        if urgent:
            st.markdown("### Urgent Issues")
            st.caption("Core and Primary trade area postcodes losing share — requires immediate investigation.")
            for issue in urgent:
                flags_str = " | ".join(issue["flags"])
                st.markdown(
                    f"**{issue['region_name']}** ({issue['postcode']}) — "
                    f"Share: {issue['current_share']:.1f}% ({issue['share_change']:+.1f}pp YoY) — "
                    f"*{issue['nearest_store']}* ({issue['distance_km']:.0f}km, {issue['distance_tier']})\n\n"
                    f"> {flags_str}"
                )

        if warnings:
            with st.expander(f"Warnings — {len(warnings)} postcodes"):
                wdf = pd.DataFrame(warnings)
                wdf["flags_str"] = wdf["flags"].apply(lambda x: " | ".join(x))
                display = wdf[["region_name", "postcode", "current_share", "share_change",
                               "nearest_store", "distance_tier", "flags_str"]].copy()
                display.columns = ["Region", "Postcode", "Share %", "Change pp",
                                   "Nearest Store", "Tier", "Flags"]
                st.dataframe(display, use_container_width=True, hide_index=True)

    # Postcode deep-dive
    st.markdown("---")
    st.subheader("Postcode Deep-Dive")
    pc_input = st.text_input("Enter postcode for trend analysis", placeholder="e.g. 2070",
                             key="issue_postcode")
    if pc_input:
        trend_data = postcode_trend(pc_input, channel)
        if not trend_data:
            st.info(f"No data for postcode {pc_input}.")
        else:
            pcdf = pd.DataFrame(trend_data)
            pcdf["period_date"] = pd.to_datetime(pcdf["period"].astype(str), format="%Y%m")

            store_name, dist_km, tier = nearest_store(pc_input)
            if store_name:
                st.caption(f"Nearest store: **{store_name}** ({dist_km:.1f}km, {tier})")

            c1, c2 = st.columns(2)
            with c1:
                fig_pc_share = px.line(
                    pcdf, x="period_date", y="market_share_pct",
                    labels={"period_date": "", "market_share_pct": "Market Share %"},
                    color_discrete_sequence=["#4ba021"],
                    title="Market Share Trend",
                )
                fig_pc_share.update_layout(height=300)
                st.plotly_chart(fig_pc_share, use_container_width=True, key="pc_share_trend")
            with c2:
                fig_pc_pen = px.line(
                    pcdf, x="period_date", y="customer_penetration_pct",
                    labels={"period_date": "", "customer_penetration_pct": "Penetration %"},
                    color_discrete_sequence=["#7c3aed"],
                    title="Customer Penetration Trend",
                )
                fig_pc_pen.update_layout(height=300)
                st.plotly_chart(fig_pc_pen, use_container_width=True, key="pc_pen_trend")

            c3, c4 = st.columns(2)
            with c3:
                fig_pc_spend = px.line(
                    pcdf, x="period_date", y="spend_per_customer",
                    labels={"period_date": "", "spend_per_customer": "Spend ($)"},
                    color_discrete_sequence=["#d97706"],
                    title="Spend per Customer Trend",
                )
                fig_pc_spend.update_layout(height=300)
                st.plotly_chart(fig_pc_spend, use_container_width=True, key="pc_spend_trend")
            with c4:
                fig_pc_mkt = px.line(
                    pcdf, x="period_date", y="market_size_dollars",
                    labels={"period_date": "", "market_size_dollars": "Market Size ($)"},
                    color_discrete_sequence=["#6366f1"],
                    title="Market Size Trend (directional only)",
                )
                fig_pc_mkt.update_layout(height=300)
                st.plotly_chart(fig_pc_mkt, use_container_width=True, key="pc_mkt_trend")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7: DATA EXPLORER
# ══════════════════════════════════════════════════════════════════════════════

with tab_data:
    st.subheader("Full Data Explorer")

    # Period picker
    data_period = st.selectbox("Period", periods[::-1], key="data_period")

    map_data = postcode_map_data(data_period, channel)
    if map_data:
        edf = pd.DataFrame(map_data)

        # Filter by state
        if state_filter != "All":
            state_ranges = {
                "NSW": lambda pc: 2000 <= int(pc) <= 2999,
                "QLD": lambda pc: 4000 <= int(pc) <= 4999,
                "ACT": lambda pc: 2600 <= int(pc) <= 2618 or int(pc) in range(2900, 2915),
            }
            fn = state_ranges.get(state_filter)
            if fn:
                edf = edf[edf["postcode"].apply(lambda x: fn(x))]

        # Tier filter
        data_tier = st.selectbox("Distance Tier", ["All", "Core (0-3km)", "Primary (3-5km)",
                                                    "Secondary (5-10km)", "Extended (10-20km)"],
                                  key="data_tier")
        if data_tier != "All":
            edf = edf[edf["distance_tier"] == data_tier]

        # Sort options
        sort_col = st.selectbox("Sort by", ["market_share_pct", "penetration_pct",
                                              "spend_per_customer", "market_size", "distance_km"],
                                 format_func=lambda x: {
                                     "market_share_pct": "Market Share %",
                                     "penetration_pct": "Penetration %",
                                     "spend_per_customer": "Spend/Customer",
                                     "market_size": "Market Size $",
                                     "distance_km": "Distance to Store",
                                 }[x], key="data_sort")

        edf = edf.sort_values(sort_col, ascending=False)

        st.metric("Total Postcodes", len(edf))

        display = edf[["postcode", "region_name", "market_share_pct", "penetration_pct",
                        "spend_per_customer", "txn_per_customer", "market_size",
                        "nearest_store", "distance_km", "distance_tier"]].copy()
        display.columns = ["Postcode", "Region", "Share %", "Penetration %", "Spend $",
                           "Txn/Customer", "Market Size $", "Nearest Store", "Distance km", "Tier"]

        st.dataframe(display, use_container_width=True, hide_index=True, height=600)

        # Download button
        csv = display.to_csv(index=False)
        st.download_button(
            "Download CSV", csv, file_name=f"market_share_{data_period}_{channel}.csv",
            mime="text/csv", key="data_download",
        )


# ── Footer ────────────────────────────────────────────────────────────────────

# ── Cross-Dashboard Links ────────────────────────────────────────────────────

st.markdown("---")
st.markdown("**Dig Deeper**")
c1, c2, c3 = st.columns(3)
c1.page_link("dashboards/customer_dashboard.py", label="Customer Analytics", icon="👥")
c2.page_link("dashboards/sales_dashboard.py", label="Sales by Store", icon="📈")
c3.page_link("dashboards/plu_intel_dashboard.py", label="PLU Intelligence", icon="📊")

render_ask_question("market_share")
render_footer("Market Share Intelligence", f"{_fmt_period(min_p)} to {_fmt_period(max_p)}", user=user)
