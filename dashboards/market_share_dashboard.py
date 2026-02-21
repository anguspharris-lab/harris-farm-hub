"""
Harris Farm Hub — Market Share Intelligence Dashboard
Postcode-level market share analysis with spatial mapping, trade area analysis,
trend detection, opportunity scoring, and issue flagging.

Data: 1,040 postcodes × 37 months × 3 channels (CBAS modelled estimates)
Primary metric: Market Share % (reliable). Dollar values are directional only.
"""

import sqlite3
import traceback
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from market_share_layer import (
    db_available, get_periods, get_latest_period, get_period_range,
    get_regions, postcode_map_data, postcode_map_data_with_trend,
    store_trade_area, store_trade_area_trend,
    store_cumulative_summary, TRADE_AREA_RADII,
    yoy_comparison, detect_shifts, flag_issues, opportunity_analysis,
    state_summary, state_trend, postcode_trend, nearest_store,
    store_health_scorecard, store_channel_comparison, network_macro_view,
    haversine_km, STORE_LOCATIONS, get_postcode_coords,
)
from shared.styles import render_header, render_footer, HFM_GREEN
from shared.ask_question import render_ask_question
from shared.voice_realtime import render_voice_data_box

user = st.session_state.get("auth_user")


# Cached wrappers for expensive store health queries
@st.cache_data(ttl=3600, show_spinner="Computing store health scores...")
def _cached_scorecard(period):
    return store_health_scorecard(period)


@st.cache_data(ttl=3600, show_spinner="Loading channel data...")
def _cached_channel_comparison(store_name, period):
    return store_channel_comparison(store_name, period)


@st.cache_data(ttl=3600, show_spinner="Building regional view...")
def _cached_macro_view(period, channel):
    return network_macro_view(period, channel)

render_header(
    "Market Share Intelligence",
    "Postcode-level competitive analysis | Spatial mapping | Trade areas | Trends",
    goals=["G1", "G2"],
    strategy_context="Where we're winning and losing market position — essential for 'Fewer, Bigger' expansion decisions.",
)

if not db_available():
    st.error("Database not found.")
    st.stop()


def _safe_int(pc, default=0):
    """Safely convert a postcode to int, returning default on failure."""
    try:
        return int(pc)
    except (ValueError, TypeError):
        return default


_STATE_RANGES = {
    "NSW": lambda pc: 2000 <= _safe_int(pc) <= 2999,
    "QLD": lambda pc: 4000 <= _safe_int(pc) <= 4999,
    "ACT": lambda pc: 2600 <= _safe_int(pc) <= 2618 or _safe_int(pc) in range(2900, 2915),
}


def _filter_by_state(df, state, postcode_col="postcode"):
    """Filter DataFrame by Australian state based on postcode ranges. Returns df unchanged if state is 'All'."""
    if state == "All":
        return df
    fn = _STATE_RANGES.get(state)
    if fn and not df.empty:
        return df[df[postcode_col].apply(fn)]
    return df


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

tab_overview, tab_map, tab_store, tab_health, tab_trends, tab_opps, tab_issues, tab_data = st.tabs([
    "Overview", "Spatial Map", "Store Trade Areas", "Store Health",
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
        mdf = _filter_by_state(mdf, state_filter)

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
    # ── Controls Row ──
    mc1, mc2, mc3, mc4, mc5 = st.columns([1.2, 1, 1, 1, 1])
    with mc1:
        map_channel = st.selectbox(
            "Channel", ["Total", "Instore", "Online"], key="map_channel")
    with mc2:
        map_metric = st.selectbox("Colour by", [
            "Health Indicator", "Market Share %", "Trend Slope (pp/yr)",
            "YoY Change (pp)", "Penetration %", "Spend/Customer",
        ], key="map_metric")
    with mc3:
        radius_opts = ["All"] + [f"Within {r}km" for r in TRADE_AREA_RADII]
        radius_filter = st.selectbox("Max Distance", radius_opts, key="map_radius")
    with mc4:
        map_store = st.selectbox(
            "From Store",
            ["Nearest Store"] + sorted(STORE_LOCATIONS.keys()),
            key="map_store_filter",
        )
    with mc5:
        map_state = st.selectbox("State", ["All", "NSW", "QLD", "ACT"], key="map_state")

    st.subheader(f"Market Share Map — {map_channel} — {_fmt_period(latest)}")
    st.caption("Bubble size = market share %. Includes YoY health indicators. Store markers shown.")

    # ── Load data with YoY trend ──
    map_raw = postcode_map_data_with_trend(latest, map_channel)
    if not map_raw:
        st.warning("No spatial data available.")
    else:
        mdf = pd.DataFrame(map_raw)
        mdf["lat"] = pd.to_numeric(mdf["lat"], errors="coerce")
        mdf["lon"] = pd.to_numeric(mdf["lon"], errors="coerce")
        mdf = mdf.dropna(subset=["lat", "lon"])

        # State filter
        mdf = _filter_by_state(mdf, map_state)

        # Radius filter — cumulative from selected store
        if radius_filter != "All":
            max_km = int(radius_filter.replace("Within ", "").replace("km", ""))
            if map_store != "Nearest Store":
                si = STORE_LOCATIONS.get(map_store)
                if not si:
                    st.warning(f"Store location not found for '{map_store}'.")
                    st.stop()
                mdf["_dist"] = mdf.apply(
                    lambda r: haversine_km(si["lat"], si["lon"], r["lat"], r["lon"]), axis=1)
                mdf = mdf[mdf["_dist"] <= max_km]
            else:
                mdf = mdf[mdf["distance_km"] <= max_km]

        if mdf.empty:
            st.info("No postcodes match the selected filters.")
        else:
            # Fill NaN change values for display
            mdf["yoy_change_pp"] = mdf["yoy_change_pp"].fillna(0)
            mdf["trend_slope_annual"] = mdf["trend_slope_annual"].fillna(0)
            mdf["health"] = mdf["health"].fillna("New")

            # Size by market share — ensure numeric, non-negative, no NaN
            mdf["market_share_pct"] = pd.to_numeric(mdf["market_share_pct"], errors="coerce").fillna(0)
            mdf["bubble_size"] = mdf["market_share_pct"].clip(lower=0.3) * 2

            # Health indicator colour map (based on annualised trend slope)
            _HEALTH_COLOURS = {
                "Accelerating": "#16a34a",
                "Growing": "#65a30d",
                "Stable": "#d97706",
                "Softening": "#ea580c",
                "Declining": "#dc2626",
                "New": "#9ca3af",
            }
            # Ordered for legend
            _HEALTH_ORDER = ["Accelerating", "Growing", "Stable",
                             "Softening", "Declining", "New"]

            # Build the map based on selected metric
            custom_cols = ["postcode", "market_share_pct", "yoy_change_pp",
                           "penetration_pct", "spend_per_customer",
                           "nearest_store", "distance_km", "health",
                           "trend_slope_annual", "trend_months"]

            if map_metric == "Health Indicator":
                # Categorical colour by health
                mdf["health"] = pd.Categorical(
                    mdf["health"], categories=_HEALTH_ORDER, ordered=True)
                fig = px.scatter_mapbox(
                    mdf, lat="lat", lon="lon",
                    color="health",
                    size="bubble_size",
                    hover_name="region_name",
                    custom_data=custom_cols,
                    color_discrete_map=_HEALTH_COLOURS,
                    category_orders={"health": _HEALTH_ORDER},
                    zoom=8, size_max=20,
                )
            elif map_metric == "Trend Slope (pp/yr)":
                fig = px.scatter_mapbox(
                    mdf, lat="lat", lon="lon",
                    color="trend_slope_annual",
                    size="bubble_size",
                    hover_name="region_name",
                    custom_data=custom_cols,
                    color_continuous_scale="RdYlGn",
                    color_continuous_midpoint=0,
                    zoom=8, size_max=20,
                )
            elif map_metric == "YoY Change (pp)":
                fig = px.scatter_mapbox(
                    mdf, lat="lat", lon="lon",
                    color="yoy_change_pp",
                    size="bubble_size",
                    hover_name="region_name",
                    custom_data=custom_cols,
                    color_continuous_scale="RdYlGn",
                    color_continuous_midpoint=0,
                    zoom=8, size_max=20,
                )
            else:
                if map_metric == "Market Share %":
                    color_col, color_scale = "market_share_pct", "Greens"
                elif map_metric == "Penetration %":
                    color_col, color_scale = "penetration_pct", "Blues"
                else:
                    color_col, color_scale = "spend_per_customer", "Oranges"
                fig = px.scatter_mapbox(
                    mdf, lat="lat", lon="lon",
                    color=color_col,
                    size="bubble_size",
                    hover_name="region_name",
                    custom_data=custom_cols,
                    color_continuous_scale=color_scale,
                    zoom=8, size_max=20,
                )

            # Hover template — includes YoY change + trend slope
            fig.update_traces(
                hovertemplate=(
                    "<b>%{hovertext}</b> (%{customdata[0]})<br>"
                    "Share: %{customdata[1]:.1f}% (YoY: %{customdata[2]:+.2f}pp)<br>"
                    "Trend: %{customdata[8]:+.2f}pp/yr (%{customdata[9]} months)<br>"
                    "Penetration: %{customdata[3]:.1f}%<br>"
                    "Spend: $%{customdata[4]:.0f}<br>"
                    "Nearest: %{customdata[5]} (%{customdata[6]:.0f}km)<br>"
                    "Health: %{customdata[7]}"
                    "<extra></extra>"
                )
            )

            # Add store markers
            store_lats = [s["lat"] for s in STORE_LOCATIONS.values()]
            store_lons = [s["lon"] for s in STORE_LOCATIONS.values()]
            fig.add_trace(go.Scattermapbox(
                lat=store_lats, lon=store_lons,
                mode="markers+text",
                marker=dict(size=12, color="#000000", symbol="circle"),
                text=[n.replace("HFM ", "") for n in STORE_LOCATIONS.keys()],
                textposition="top center",
                textfont=dict(size=9, color="#333333"),
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

            # ── Summary KPIs below map ──
            st.markdown("---")
            health_counts = mdf["health"].value_counts()
            hk = st.columns(6)
            for i, h in enumerate(_HEALTH_ORDER):
                cnt = health_counts.get(h, 0)
                hk[i].markdown(
                    f"<div style='text-align:center;'>"
                    f"<span style='color:{_HEALTH_COLOURS[h]};font-size:1.5rem;"
                    f"font-weight:700;'>{cnt}</span><br>"
                    f"<span style='font-size:0.75rem;'>{h}</span></div>",
                    unsafe_allow_html=True,
                )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Postcodes Shown", len(mdf))
            c2.metric(f"Avg Share ({map_channel})", f"{mdf['market_share_pct'].mean():.1f}%")
            avg_chg = mdf["yoy_change_pp"].mean()
            c3.metric("Avg YoY Change", f"{avg_chg:+.2f}pp")
            c4.metric("Avg Penetration", f"{mdf['penetration_pct'].mean():.1f}%")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: STORE TRADE AREAS
# ══════════════════════════════════════════════════════════════════════════════

with tab_store:
    st.subheader("Store Trade Area Analysis")
    st.caption(
        "Select a store to see cumulative trade area performance. "
        "Each radius includes ALL postcodes within that distance (not rings)."
    )

    store_names = sorted(STORE_LOCATIONS.keys())
    selected_store = st.selectbox("Select Store", store_names, key="trade_area_store")

    if selected_store:
        store_info = STORE_LOCATIONS[selected_store]

        # Get all trade area postcodes (up to 50km)
        ta_data = store_trade_area(selected_store, latest, channel, max_km=50)
        if not ta_data:
            st.info(f"No market share data for postcodes near {selected_store}.")
        else:
            tdf = pd.DataFrame(ta_data)

            # Cumulative summary by radius
            cum_summary = store_cumulative_summary(selected_store, latest, channel)
            cum_df = pd.DataFrame(cum_summary)

            # KPIs — use 0-3km and 0-5km cumulative
            r3 = next((r for r in cum_summary if r["radius_km"] == 3), None)
            r5 = next((r for r in cum_summary if r["radius_km"] == 5), None)
            r10 = next((r for r in cum_summary if r["radius_km"] == 10), None)

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Postcodes (50km)", len(tdf))
            k2.metric("0-3km Avg Share", f"{r3['avg_share']:.1f}%" if r3 and r3["avg_share"] else "N/A")
            k3.metric("0-5km Avg Share", f"{r5['avg_share']:.1f}%" if r5 and r5["avg_share"] else "N/A")
            k4.metric("0-10km Avg Share", f"{r10['avg_share']:.1f}%" if r10 and r10["avg_share"] else "N/A")

            # Cumulative summary table
            st.markdown("**Performance by Cumulative Radius**")
            cum_display = cum_df[cum_df["postcodes"] > 0].copy()
            cum_display = cum_display[["label", "postcodes", "avg_share", "avg_penetration",
                                       "avg_spend", "total_market"]]
            cum_display.columns = ["Radius", "Postcodes", "Avg Share %",
                                   "Avg Penetration %", "Avg Spend $", "Total Market $"]
            st.dataframe(cum_display, use_container_width=True, hide_index=True)

            # Bar chart showing share decay with distance
            cum_with_data = cum_df[cum_df["avg_share"].notna()].copy()
            if not cum_with_data.empty:
                fig_decay = px.bar(
                    cum_with_data, x="label", y="avg_share",
                    labels={"label": "Cumulative Radius", "avg_share": "Avg Market Share %"},
                    color="avg_share",
                    color_continuous_scale=["#dc2626", "#d97706", "#4ba021"],
                    text="avg_share",
                )
                fig_decay.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig_decay.update_layout(
                    height=350, showlegend=False, coloraxis_showscale=False,
                    xaxis=dict(categoryorder="array",
                               categoryarray=[f"0-{r}km" for r in TRADE_AREA_RADII]),
                )
                st.plotly_chart(fig_decay, use_container_width=True, key="ta_decay_chart")

            # Map of trade area — colour by distance band
            st.markdown("**Trade Area Map**")
            map_radius = st.selectbox(
                "Show postcodes within",
                [f"0-{r}km" for r in TRADE_AREA_RADII],
                index=3,  # Default 0-20km
                key="ta_map_radius",
            )
            map_km = int(map_radius.split("-")[1].replace("km", ""))
            map_df = tdf[tdf["distance_km"] <= map_km].copy()

            if not map_df.empty:
                map_df["market_share_pct"] = pd.to_numeric(
                    map_df["market_share_pct"], errors="coerce").fillna(0)
                map_df["size"] = map_df["market_share_pct"].clip(lower=0.5) * 2

                # Join with postcode coordinates
                coords = get_postcode_coords()
                map_df["lat"] = pd.to_numeric(
                    map_df["postcode"].map(lambda x: coords.get(x, {}).get("lat")), errors="coerce")
                map_df["lon"] = pd.to_numeric(
                    map_df["postcode"].map(lambda x: coords.get(x, {}).get("lon")), errors="coerce")
                map_df = map_df.dropna(subset=["lat", "lon"])

                if not map_df.empty:
                    fig_ta = px.scatter_mapbox(
                        map_df, lat="lat", lon="lon",
                        color="market_share_pct",
                        size="size",
                        hover_name="region_name",
                        custom_data=["postcode", "market_share_pct", "penetration_pct",
                                     "distance_km", "tier"],
                        color_continuous_scale="Greens",
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
                        mapbox=dict(center=dict(lat=store_info["lat"],
                                                lon=store_info["lon"]), zoom=11),
                        height=550,
                        margin=dict(l=0, r=0, t=0, b=0),
                    )
                    st.plotly_chart(fig_ta, use_container_width=True, key="trade_area_map")

            # Trade area trend — cumulative radii
            st.markdown("**Trade Area Share Trend by Radius**")
            ta_radius_opts = [f"0-{r}km" for r in TRADE_AREA_RADII]
            ta_selected_radii = st.multiselect(
                "Compare radii",
                ta_radius_opts,
                default=["0-3km", "0-5km", "0-10km", "0-20km"],
                key="ta_trend_radii",
            )

            if ta_selected_radii:
                trend_frames = []
                for r_label in ta_selected_radii:
                    r_km = int(r_label.split("-")[1].replace("km", ""))
                    trend = store_trade_area_trend(selected_store, channel,
                                                   max_km=50, tier_filter=r_km)
                    if trend:
                        rdf = pd.DataFrame(trend)
                        rdf["radius"] = r_label
                        trend_frames.append(rdf)

                if trend_frames:
                    all_trends = pd.concat(trend_frames, ignore_index=True)
                    all_trends["period_date"] = pd.to_datetime(
                        all_trends["period"].astype(str), format="%Y%m")
                    fig_tt = px.line(
                        all_trends, x="period_date", y="avg_share", color="radius",
                        labels={"period_date": "", "avg_share": "Avg Market Share %",
                                "radius": "Radius"},
                        color_discrete_sequence=["#16a34a", "#2563eb", "#d97706",
                                                 "#9333ea", "#6b7280"],
                    )
                    fig_tt.update_layout(
                        height=400,
                        legend=dict(orientation="h", y=-0.15),
                    )
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
# TAB 4: STORE HEALTH
# ══════════════════════════════════════════════════════════════════════════════

with tab_health:
    st.subheader("Store Health Scorecard")
    st.caption(
        "Each store graded A-F based on Core+Primary trade area share, "
        "YoY trend, and customer penetration. Channel breakdown and regional macro view below."
    )

    # --- Scorecard ---
    scorecard = _cached_scorecard(latest)
    if not scorecard:
        st.warning("No scorecard data available.")
    else:
        # Filter by state if selected
        if state_filter != "All":
            scorecard = [s for s in scorecard if s["state"] == state_filter]

        # Grade colour mapping
        _GRADE_COLOURS = {"A": "#16a34a", "B": "#65a30d", "C": "#d97706", "D": "#ea580c", "F": "#dc2626"}

        # Summary KPIs
        grades = [s["grade"] for s in scorecard]
        avg_cp = sum(s["cp_share"] for s in scorecard) / len(scorecard) if scorecard else 0
        growing = sum(1 for s in scorecard if (s["cp_share_change"] or 0) > 0)
        declining = sum(1 for s in scorecard if (s["cp_share_change"] or 0) < 0)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Stores Graded", len(scorecard))
        k2.metric("Avg Core+Primary Share", f"{avg_cp:.1f}%")
        k3.metric("Stores Growing", growing, delta=f"{growing}/{len(scorecard)}")
        k4.metric("Stores Declining", declining, delta=f"-{declining}", delta_color="inverse")

        # Grade distribution bar
        grade_counts = {}
        for g in ["A", "B", "C", "D", "F"]:
            grade_counts[g] = grades.count(g)

        grade_df = pd.DataFrame([
            {"Grade": g, "Count": c, "Colour": _GRADE_COLOURS[g]}
            for g, c in grade_counts.items() if c > 0
        ])
        if not grade_df.empty:
            fig_grades = px.bar(
                grade_df, x="Grade", y="Count", color="Grade",
                color_discrete_map=_GRADE_COLOURS,
                labels={"Count": "Stores"},
            )
            fig_grades.update_layout(height=250, showlegend=False)
            st.plotly_chart(fig_grades, use_container_width=True, key="grade_dist")

        # Scorecard table — all stores
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
            lambda x: f"{x:+.2f}" if x is not None else "N/A"
        )
        st.dataframe(sc_display, use_container_width=True, hide_index=True, height=500)

        # --- Store-level channel breakdown ---
        st.markdown("---")
        st.subheader("Store Channel Breakdown")
        st.caption("Instore vs Online market share in each store's surrounding postcodes (within 10km).")

        health_store = st.selectbox(
            "Select Store", [s["store"] for s in scorecard],
            key="health_store_select"
        )

        if health_store:
            chan_data = _cached_channel_comparison(health_store, latest)
            if not chan_data:
                st.info(f"No channel data for {health_store}.")
            else:
                cdf = pd.DataFrame(chan_data)

                # KPIs for selected store
                ck1, ck2, ck3, ck4 = st.columns(4)
                ck1.metric("Postcodes", len(cdf))
                ck2.metric("Avg Instore Share", f"{cdf['instore_share'].mean():.1f}%")
                ck3.metric("Avg Online Share", f"{cdf['online_share'].mean():.2f}%")
                ck4.metric("Online Penetration", f"{cdf['online_pen'].mean():.2f}%")

                # Stacked bar: instore vs online by postcode (top 20 by total share)
                cdf["total_share"] = cdf["instore_share"] + cdf["online_share"]
                top_chan = cdf.nlargest(20, "total_share")

                fig_chan = go.Figure()
                fig_chan.add_trace(go.Bar(
                    name="Instore", x=top_chan["region_name"], y=top_chan["instore_share"],
                    marker_color="#4ba021",
                    hovertemplate="%{x}<br>Instore: %{y:.1f}%<extra></extra>",
                ))
                fig_chan.add_trace(go.Bar(
                    name="Online", x=top_chan["region_name"], y=top_chan["online_share"],
                    marker_color="#7c3aed",
                    hovertemplate="%{x}<br>Online: %{y:.2f}%<extra></extra>",
                ))
                fig_chan.update_layout(
                    barmode="stack", height=400,
                    xaxis_title="", yaxis_title="Market Share %",
                    legend=dict(orientation="h", y=-0.25),
                )
                st.plotly_chart(fig_chan, use_container_width=True, key="store_channel_bar")

                # Channel detail table
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
                    st.dataframe(chan_display, use_container_width=True, hide_index=True, height=400)

        # --- Regional Macro View ---
        st.markdown("---")
        st.subheader("Regional Macro View")
        st.caption(
            "Stores grouped into geographic clusters. Shows aggregate performance "
            "across surrounding postcodes (within 10km of any cluster store)."
        )

        macro = _cached_macro_view(latest, channel)
        if not macro:
            st.info("No macro data available.")
        else:
            macro_df = pd.DataFrame(macro)

            if macro_df.empty:
                st.info("No macro data available.")
            else:
                # Macro KPIs
                mk1, mk2, mk3 = st.columns(3)
                mk1.metric("Clusters", len(macro_df))
                best = macro_df.iloc[0]
                mk2.metric(
                    f"Strongest: {best['cluster']}",
                    f"{best['avg_share']:.1f}%",
                )
                worst = macro_df.iloc[-1]
                mk3.metric(
                    f"Weakest: {worst['cluster']}",
                    f"{worst['avg_share']:.1f}%",
                )

            # Cluster comparison bar chart
            fig_macro = go.Figure()
            colours = [
                "#16a34a" if (r["share_change"] or 0) >= 0 else "#dc2626"
                for _, r in macro_df.iterrows()
            ]
            fig_macro.add_trace(go.Bar(
                x=macro_df["cluster"], y=macro_df["avg_share"],
                marker_color=colours,
                text=macro_df["share_change"].apply(
                    lambda x: f"{x:+.2f}pp" if x is not None else ""
                ),
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Share: %{y:.1f}%<br>"
                    "YoY: %{text}"
                    "<extra></extra>"
                ),
            ))
            fig_macro.update_layout(
                height=400, yaxis_title="Avg Market Share %",
                xaxis_title="", showlegend=False,
            )
            st.plotly_chart(fig_macro, use_container_width=True, key="macro_bar")

            # Macro detail table
            macro_display = macro_df[[
                "cluster", "stores", "postcodes", "avg_share",
                "share_change", "avg_penetration", "avg_spend",
            ]].copy()
            macro_display.columns = [
                "Cluster", "Stores", "Postcodes", "Avg Share %",
                "YoY Change (pp)", "Avg Penetration %", "Avg Spend $",
            ]
            macro_display["YoY Change (pp)"] = macro_display["YoY Change (pp)"].apply(
                lambda x: f"{x:+.2f}" if x is not None else "N/A"
            )
            st.dataframe(macro_display, use_container_width=True, hide_index=True)

            # Bubble map of clusters — one bubble per cluster, sized by share
            st.markdown("**Cluster Map**")
            _CLUSTER_STORES = {
                "Inner Sydney": ["HFM Broadway", "HFM Potts Point", "HFM Cammeray"],
                "Eastern Suburbs": ["HFM Bondi Junction", "HFM Bondi Beach", "HFM Bondi Westfield",
                                    "HFM Rose Bay", "HFM Randwick"],
                "North Shore": ["HFM Willoughby", "HFM Lane Cove", "HFM Boronia Park",
                                "HFM Lindfield", "HFM St Ives"],
                "Northern Beaches": ["HFM Mosman", "HFM Manly", "HFM Dee Why", "HFM Mona Vale"],
                "Inner West": ["HFM Drummoyne", "HFM Leichhardt"],
                "Western Sydney": ["HFM Merrylands", "HFM Baulkham Hills", "HFM Pennant Hills", "HFM Penrith"],
                "Central Coast": ["HFM Erina"],
                "Hunter": ["HFM Newcastle", "HFM Glendale"],
                "Regional NSW": ["HFM Orange", "HFM Bowral", "HFM Albury"],
                "QLD": ["HFM West End", "HFM Isle of Capri", "HFM Clayfield"],
            }
            cluster_coords = []
            for _, row in macro_df.iterrows():
                clat, clon = [], []
                for sname in _CLUSTER_STORES.get(row["cluster"], []):
                    si = STORE_LOCATIONS.get(sname)
                    if si:
                        clat.append(si["lat"])
                        clon.append(si["lon"])
                if clat:
                    cluster_coords.append({
                        "cluster": row["cluster"],
                        "lat": sum(clat) / len(clat),
                        "lon": sum(clon) / len(clon),
                        "avg_share": row["avg_share"],
                        "share_change": row["share_change"],
                        "stores": row["stores"],
                        "postcodes": row["postcodes"],
                    })

            if cluster_coords:
                ccdf = pd.DataFrame(cluster_coords)
                ccdf["avg_share"] = pd.to_numeric(ccdf["avg_share"], errors="coerce").fillna(0)
                ccdf["size"] = ccdf["avg_share"].clip(lower=1) * 3
                ccdf["change_text"] = ccdf["share_change"].apply(
                    lambda x: f"{x:+.2f}pp YoY" if x is not None else ""
                )
                fig_cmap = px.scatter_mapbox(
                    ccdf, lat="lat", lon="lon",
                    size="size", color="avg_share",
                    hover_name="cluster",
                    custom_data=["stores", "postcodes", "avg_share", "change_text"],
                    color_continuous_scale="Greens",
                    zoom=8, size_max=40,
                )
                fig_cmap.update_traces(
                    hovertemplate=(
                        "<b>%{hovertext}</b><br>"
                        "Stores: %{customdata[0]} | Postcodes: %{customdata[1]}<br>"
                        "Avg Share: %{customdata[2]:.1f}%<br>"
                        "%{customdata[3]}"
                        "<extra></extra>"
                    )
                )
                fig_cmap.update_layout(
                    mapbox_style="open-street-map",
                    mapbox=dict(center=dict(lat=-33.85, lon=151.2), zoom=9),
                    height=500,
                    margin=dict(l=0, r=0, t=0, b=0),
                )
                st.plotly_chart(fig_cmap, use_container_width=True, key="cluster_map")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: TRENDS & SHIFTS
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
        # Ensure numeric lat/lon for scatter_mapbox
        if "lat" in ydf.columns:
            ydf["lat"] = pd.to_numeric(ydf["lat"], errors="coerce")
            ydf["lon"] = pd.to_numeric(ydf["lon"], errors="coerce")

        # Filter by state
        ydf = _filter_by_state(ydf, state_filter, postcode_col="region_code")

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
            ydf_map = ydf.dropna(subset=["lat", "lon"]).copy()
            if not ydf_map.empty:
                ydf_map["share_change"] = pd.to_numeric(
                    ydf_map["share_change"], errors="coerce").fillna(0)
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
        odf = _filter_by_state(odf, state_filter)

        if odf.empty:
            st.info("No opportunity data for the selected state filter.")
        else:
            # Ensure numeric for size parameter
            odf["market_size"] = pd.to_numeric(odf["market_size"], errors="coerce").fillna(0).clip(lower=0)

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
            fn = _STATE_RANGES.get(state_filter)
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
        edf = _filter_by_state(edf, state_filter)

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
_pages = st.session_state.get("_pages", {})
c1, c2, c3 = st.columns(3)
if "customers" in _pages:
    c1.page_link(_pages["customers"], label="Customer Analytics", icon="👥")
if "sales" in _pages:
    c2.page_link(_pages["sales"], label="Sales by Store", icon="📈")
if "plu-intel" in _pages:
    c3.page_link(_pages["plu-intel"], label="PLU Intelligence", icon="📊")

render_voice_data_box("market_share")
render_ask_question("market_share")
render_footer("Market Share Intelligence", f"{_fmt_period(min_p)} to {_fmt_period(max_p)}", user=user)
