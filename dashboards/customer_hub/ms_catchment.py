"""
Customer Hub — Market Share > Catchment Tiers
Trade area analysis — cumulative radius performance per store,
trend by radius, and the all-stores × all-tiers matrix.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from customer_hub.components import (
    section_header, insight_callout, fmt_period,
)
from market_share_layer import (
    get_latest_period,
    store_trade_area, store_cumulative_summary, store_trade_area_trend,
    get_postcode_coords, STORE_LOCATIONS, TRADE_AREA_RADII,
)


def render():
    latest = st.session_state.get("ms_latest") or get_latest_period()
    channel = st.session_state.get("ms_channel", "Total")

    section_header(
        "Catchment Tiers",
        "How share decays with distance — and which stores hold their "
        "ground furthest from the front door.",
    )

    insight_callout(
        "Trade areas are <b>cumulative</b>: 0-5km includes everything within 5km "
        "(not a ring from 3-5km). Core (0-3km) is where we should dominate. "
        "If we're losing Core, something fundamental is wrong.",
        style="info",
    )

    store_names = sorted(STORE_LOCATIONS.keys())
    selected_store = st.selectbox("Select Store", store_names,
                                  key="ms_catch_store")

    if not selected_store:
        return

    store_info = STORE_LOCATIONS[selected_store]
    ta_data = store_trade_area(selected_store, latest, channel, max_km=50)
    if not ta_data:
        st.info("No market share data for postcodes near {}.".format(
            selected_store))
        return

    tdf = pd.DataFrame(ta_data)
    cum_summary = store_cumulative_summary(selected_store, latest, channel)
    cum_df = pd.DataFrame(cum_summary)

    # KPIs from cumulative radii
    r3 = next((r for r in cum_summary if r["radius_km"] == 3), None)
    r5 = next((r for r in cum_summary if r["radius_km"] == 5), None)
    r10 = next((r for r in cum_summary if r["radius_km"] == 10), None)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Postcodes (50km)", len(tdf))
    k2.metric("0-3km Avg Share",
              "{:.1f}%".format(r3["avg_share"]) if r3 and r3["avg_share"] else "N/A")
    k3.metric("0-5km Avg Share",
              "{:.1f}%".format(r5["avg_share"]) if r5 and r5["avg_share"] else "N/A")
    k4.metric("0-10km Avg Share",
              "{:.1f}%".format(r10["avg_share"]) if r10 and r10["avg_share"] else "N/A")

    # Cumulative summary table
    st.markdown("**Performance by Cumulative Radius**")
    cum_display = cum_df[cum_df["postcodes"] > 0].copy()
    cum_display = cum_display[["label", "postcodes", "avg_share",
                               "avg_penetration", "avg_spend", "total_market"]]
    cum_display.columns = ["Radius", "Postcodes", "Avg Share %",
                           "Avg Penetration %", "Avg Spend $", "Total Market $"]
    st.dataframe(cum_display, use_container_width=True, hide_index=True,
                 key="ms_cum_tbl")

    # Decay bar chart
    cum_with_data = cum_df[cum_df["avg_share"].notna()].copy()
    if not cum_with_data.empty:
        fig_decay = px.bar(
            cum_with_data, x="label", y="avg_share",
            labels={"label": "Cumulative Radius",
                    "avg_share": "Avg Market Share %"},
            color="avg_share",
            color_continuous_scale=["#dc2626", "#d97706", "#2ECC71"],
            text="avg_share",
        )
        fig_decay.update_traces(texttemplate="%{text:.1f}%",
                                textposition="outside")
        fig_decay.update_layout(
            height=350, showlegend=False, coloraxis_showscale=False,
            xaxis=dict(
                categoryorder="array",
                categoryarray=["0-{}km".format(r) for r in TRADE_AREA_RADII],
            ),
        )
        st.plotly_chart(fig_decay, use_container_width=True,
                        key="ms_decay_chart")

    # ── Trade Area Map ──
    st.markdown("**Trade Area Map**")
    map_radius = st.selectbox(
        "Show postcodes within",
        ["0-{}km".format(r) for r in TRADE_AREA_RADII],
        index=3,
        key="ms_ta_map_radius",
    )
    map_km = int(map_radius.split("-")[1].replace("km", ""))
    map_df = tdf[tdf["distance_km"] <= map_km].copy()

    if not map_df.empty:
        map_df["market_share_pct"] = pd.to_numeric(
            map_df["market_share_pct"], errors="coerce").fillna(0)
        map_df["size"] = map_df["market_share_pct"].clip(lower=0.5) * 2

        coords = get_postcode_coords()
        map_df["lat"] = pd.to_numeric(
            map_df["postcode"].map(
                lambda x: coords.get(x, {}).get("lat")), errors="coerce")
        map_df["lon"] = pd.to_numeric(
            map_df["postcode"].map(
                lambda x: coords.get(x, {}).get("lon")), errors="coerce")
        map_df = map_df.dropna(subset=["lat", "lon"])

        if not map_df.empty:
            import plotly.graph_objects as go
            fig_ta = px.scatter_mapbox(
                map_df, lat="lat", lon="lon",
                color="market_share_pct", size="size",
                hover_name="region_name",
                custom_data=["postcode", "market_share_pct",
                             "penetration_pct", "distance_km", "tier"],
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
            fig_ta.add_trace(go.Scattermapbox(
                lat=[store_info["lat"]], lon=[store_info["lon"]],
                mode="markers+text",
                marker=dict(size=16, color="#dc2626", symbol="circle"),
                text=[selected_store.replace("HFM ", "")],
                textposition="top center",
                textfont=dict(size=11, color="#dc2626", family="Arial Black"),
                name=selected_store,
                hovertemplate="<b>{}</b><extra>Store</extra>".format(
                    selected_store),
            ))
            fig_ta.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(center=dict(lat=store_info["lat"],
                                        lon=store_info["lon"]), zoom=11),
                height=550, margin=dict(l=0, r=0, t=0, b=0),
            )
            st.plotly_chart(fig_ta, use_container_width=True,
                            key="ms_trade_area_map")

    # ── Trade Area Trend ──
    st.markdown("**Trade Area Share Trend by Radius**")
    ta_radius_opts = ["0-{}km".format(r) for r in TRADE_AREA_RADII]
    ta_selected = st.multiselect(
        "Compare radii", ta_radius_opts,
        default=["0-3km", "0-5km", "0-10km", "0-20km"],
        key="ms_ta_trend_radii",
    )

    if ta_selected:
        trend_frames = []
        for r_label in ta_selected:
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
                color_discrete_sequence=["#2ECC71", "#2563eb", "#d97706",
                                         "#9333ea", "#6b7280"],
            )
            fig_tt.update_layout(
                height=400, legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig_tt, use_container_width=True,
                            key="ms_ta_trend_chart")

    # ── All-stores × all-tiers matrix ──
    st.markdown("---")
    st.subheader("All Stores × All Tiers")
    st.caption("Average share at each cumulative radius for every store.")

    matrix_rows = []
    for sn in sorted(STORE_LOCATIONS.keys()):
        row = {"Store": sn.replace("HFM ", "")}
        cum = store_cumulative_summary(sn, latest, channel)
        for r in cum:
            row["0-{}km".format(r["radius_km"])] = r["avg_share"]
        matrix_rows.append(row)

    if matrix_rows:
        mdf = pd.DataFrame(matrix_rows)
        mdf = mdf.sort_values("0-3km", ascending=False, na_position="last")

        def _highlight_share(val):
            if pd.isna(val):
                return ""
            if val >= 10:
                return "background-color: #dcfce7"
            elif val >= 5:
                return "background-color: #fef9c3"
            elif val > 0:
                return "background-color: #fee2e2"
            return ""

        radius_cols = ["0-{}km".format(r) for r in TRADE_AREA_RADII]
        styled = mdf.style.format(
            {c: "{:.1f}" for c in radius_cols if c in mdf.columns},
            na_rep="—",
        ).applymap(_highlight_share, subset=[c for c in radius_cols if c in mdf.columns])

        st.dataframe(styled, use_container_width=True, hide_index=True,
                     height=min(600, 40 + len(mdf) * 35),
                     key="ms_store_tier_matrix")

    # Postcode detail table
    st.markdown("**All Postcodes in Trade Area**")
    display = tdf[["postcode", "region_name", "distance_km", "tier",
                    "market_share_pct", "penetration_pct",
                    "spend_per_customer", "market_size"]].copy()
    display.columns = ["Postcode", "Region", "Distance (km)", "Tier",
                       "Share %", "Penetration %", "Spend $", "Market Size $"]
    st.dataframe(display, use_container_width=True, hide_index=True,
                 height=400, key="ms_ta_postcode_tbl")
