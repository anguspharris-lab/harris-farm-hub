"""
Customer Hub — Market Share > Map (Folium)
Interactive map with store markers, concentric catchment rings,
rich HTML popups, and frontier markers for opportunity postcodes.
"""

import pandas as pd
import streamlit as st

from customer_hub.components import (
    HEALTH_COLOURS, HEALTH_ORDER, section_header, insight_callout,
    fmt_period, filter_by_state,
)
from market_share_layer import (
    get_latest_period, get_postcode_coords,
    postcode_map_data_with_trend, STORE_LOCATIONS, TRADE_AREA_RADII,
    haversine_km,
)

try:
    import folium
    from folium.plugins import MarkerCluster
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False


def _make_popup_html(row):
    """Build rich HTML popup for a postcode marker."""
    health_color = HEALTH_COLOURS.get(row.get("health", "New"), "#9ca3af")
    yoy = row.get("yoy_change_pp")
    yoy_str = "{:+.2f}pp".format(yoy) if yoy is not None else "N/A"
    slope = row.get("trend_slope_annual")
    slope_str = "{:+.2f}pp/yr".format(slope) if slope is not None else "N/A"

    return """
    <div style="font-family:sans-serif;min-width:200px;">
      <h4 style="margin:0 0 4px 0;">{name}</h4>
      <div style="font-size:0.85em;color:#6b7280;">Postcode {pc}</div>
      <hr style="margin:6px 0;">
      <table style="font-size:0.85em;width:100%;">
        <tr><td>Market Share</td><td style="text-align:right;font-weight:600;">{share:.1f}%</td></tr>
        <tr><td>YoY Change</td><td style="text-align:right;">{yoy}</td></tr>
        <tr><td>Trend</td><td style="text-align:right;">{slope}</td></tr>
        <tr><td>Penetration</td><td style="text-align:right;">{pen:.1f}%</td></tr>
        <tr><td>Spend/Customer</td><td style="text-align:right;">${spend:.0f}</td></tr>
        <tr><td>Nearest Store</td><td style="text-align:right;">{store}</td></tr>
        <tr><td>Distance</td><td style="text-align:right;">{dist:.1f}km</td></tr>
      </table>
      <div style="margin-top:6px;text-align:center;padding:3px 8px;border-radius:4px;
                  background:{health_color};color:white;font-weight:600;font-size:0.8em;">
        {health}
      </div>
    </div>
    """.format(
        name=row.get("region_name", ""),
        pc=row.get("postcode", ""),
        share=row.get("market_share_pct", 0),
        yoy=yoy_str,
        slope=slope_str,
        pen=row.get("penetration_pct", 0),
        spend=row.get("spend_per_customer", 0),
        store=row.get("nearest_store", "Unknown"),
        dist=row.get("distance_km", 0),
        health=row.get("health", "New"),
        health_color=health_color,
    )


def _health_marker_color(health):
    """Map health category to marker colour."""
    return HEALTH_COLOURS.get(health, "#9ca3af")


def render():
    latest = st.session_state.get("ms_latest") or get_latest_period()
    channel = st.session_state.get("ms_channel", "Total")
    state_filter = st.session_state.get("ms_state", "All")

    section_header(
        "Market Share Map",
        "Explore every postcode on the map — with store markers, "
        "catchment rings, and health indicators.",
    )

    if not FOLIUM_AVAILABLE:
        insight_callout(
            "Folium is not installed. Install with "
            "<code>pip install folium streamlit-folium</code> to enable "
            "the interactive map.",
            style="warning",
        )
        st.stop()

    # ── Controls ──
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        show_rings = st.checkbox("Show catchment rings", value=True,
                                 key="ms_map_rings")
    with mc2:
        show_postcodes = st.checkbox("Show postcode markers", value=True,
                                     key="ms_map_postcodes")
    with mc3:
        ring_store = st.selectbox(
            "Catchment rings for",
            ["All Stores"] + sorted(STORE_LOCATIONS.keys()),
            key="ms_map_ring_store",
        )

    radius_filter = st.selectbox(
        "Max Distance from Store",
        ["All"] + ["Within {}km".format(r) for r in TRADE_AREA_RADII],
        key="ms_map_radius",
    )

    # ── Load data ──
    map_raw = postcode_map_data_with_trend(latest, channel)
    if not map_raw:
        st.warning("No spatial data available.")
        return

    mdf = pd.DataFrame(map_raw)
    mdf["lat"] = pd.to_numeric(mdf["lat"], errors="coerce")
    mdf["lon"] = pd.to_numeric(mdf["lon"], errors="coerce")
    mdf = mdf.dropna(subset=["lat", "lon"])
    mdf = filter_by_state(mdf, state_filter)

    # Radius filter
    if radius_filter != "All":
        max_km = int(radius_filter.replace("Within ", "").replace("km", ""))
        if ring_store != "All Stores":
            si = STORE_LOCATIONS.get(ring_store)
            if si:
                mdf["_dist"] = mdf.apply(
                    lambda r: haversine_km(
                        si["lat"], si["lon"], r["lat"], r["lon"]),
                    axis=1,
                )
                mdf = mdf[mdf["_dist"] <= max_km]
        else:
            mdf = mdf[mdf["distance_km"] <= max_km]

    if mdf.empty:
        st.info("No postcodes match the selected filters.")
        return

    # ── Build Folium map ──
    center_lat = mdf["lat"].mean()
    center_lon = mdf["lon"].mean()
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="CartoDB positron",
    )

    # ── Catchment rings ──
    if show_rings:
        ring_radii = [3, 5, 10, 20]
        ring_colors = ["#2ECC71", "#2563eb", "#d97706", "#94a3b8"]

        stores_to_ring = (
            {ring_store: STORE_LOCATIONS[ring_store]}
            if ring_store != "All Stores" and ring_store in STORE_LOCATIONS
            else STORE_LOCATIONS
        )

        for store_name, store_info in stores_to_ring.items():
            for radius_km, color in zip(ring_radii, ring_colors):
                folium.Circle(
                    location=[store_info["lat"], store_info["lon"]],
                    radius=radius_km * 1000,
                    color=color,
                    weight=1,
                    fill=False,
                    opacity=0.4,
                    tooltip="{}km from {}".format(radius_km, store_name),
                ).add_to(m)

    # ── Store markers ──
    for store_name, store_info in STORE_LOCATIONS.items():
        folium.Marker(
            location=[store_info["lat"], store_info["lon"]],
            popup="<b>{}</b>".format(store_name),
            tooltip=store_name.replace("HFM ", ""),
            icon=folium.Icon(color="red", icon="shopping-cart", prefix="fa"),
        ).add_to(m)

    # ── Postcode markers ──
    if show_postcodes:
        for _, row in mdf.iterrows():
            health = row.get("health", "New")
            color = _health_marker_color(health)
            share = row.get("market_share_pct", 0)
            radius = max(3, min(share * 1.5, 20))

            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                weight=1,
                popup=folium.Popup(
                    _make_popup_html(row.to_dict()), max_width=280),
                tooltip="{} — {:.1f}%".format(
                    row.get("region_name", ""), share),
            ).add_to(m)

    # ── Render map ──
    st_folium(m, width=None, height=650, key="ms_folium_map",
              returned_objects=[])

    # ── Summary KPIs below map ──
    st.markdown("---")

    # Health distribution
    mdf["health"] = mdf["health"].fillna("New")
    health_counts = mdf["health"].value_counts()
    hk = st.columns(6)
    for i, h in enumerate(HEALTH_ORDER):
        cnt = health_counts.get(h, 0)
        hk[i].markdown(
            "<div style='text-align:center;'>"
            "<span style='color:{color};font-size:1.5rem;"
            "font-weight:700;'>{cnt}</span><br>"
            "<span style='font-size:0.75rem;'>{label}</span></div>".format(
                color=HEALTH_COLOURS[h], cnt=cnt, label=h,
            ),
            unsafe_allow_html=True,
        )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Postcodes Shown", len(mdf))
    c2.metric("Avg Share ({})".format(channel),
              "{:.1f}%".format(mdf["market_share_pct"].mean()))
    avg_chg = mdf["yoy_change_pp"].fillna(0).mean()
    c3.metric("Avg YoY Change", "{:+.2f}pp".format(avg_chg))
    c4.metric("Avg Penetration",
              "{:.1f}%".format(mdf["penetration_pct"].mean()))

    # ── Legend ──
    st.caption(
        "Circle size = market share %. "
        "Colour = health indicator (based on 6-month trend slope). "
        "Red markers = HFM stores. "
        "Concentric rings = catchment tiers (3/5/10/20km)."
    )
