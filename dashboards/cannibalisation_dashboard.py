"""
Harris Farm Hub -- Cannibalisation Analysis Dashboard
Measures network impact when stores trade near each other.
Detects revenue shifts after new store openings, identifies
cannibalisation pairs, and simulates What-If expansion scenarios.

Data source: store_pl_summary (GL-level P&L, Jul 2016 - Jan 2026)
Coordinates: postcode_coords.json (1,040 Australian postcodes)
"""

import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Project path setup
# ---------------------------------------------------------------------------
_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT / "backend"))

from store_pl_service import get_summary_df, get_stores_list  # noqa: E402

from shared.styles import (  # noqa: E402
    render_header,
    render_footer,
    glass_card,
    NAVY_CARD,
    GREEN,
    GOLD,
    RED,
    ORANGE,
    BLUE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    BORDER,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DARK_LAYOUT = dict(
    paper_bgcolor=NAVY_CARD,
    plot_bgcolor="#0D150D",
    font=dict(color=TEXT_SECONDARY, family="Trebuchet MS, sans-serif"),
    title_font=dict(family="Georgia, serif", color=TEXT_PRIMARY),
    margin=dict(t=40, r=20, b=40, l=60),
    hoverlabel=dict(bgcolor="#1A2A1A", font_color=TEXT_PRIMARY, bordercolor=BORDER),
)

_MAPBOX_TOKEN = ""  # carto-darkmatter needs no token

# Store ID -> (suburb, postcode) mapping
_STORE_POSTCODES = {
    10: ("Pennant Hills", "2120"), 24: ("St Ives", "2075"),
    28: ("Mosman", "2088"), 32: ("Willoughby", "2068"),
    37: ("Broadway", "2007"), 40: ("Erina", "2250"),
    44: ("Orange", "2800"), 48: ("Manly", "2095"),
    49: ("Mona Vale", "2103"), 51: ("Bowral", "2576"),
    52: ("Cammeray", "2062"), 54: ("Potts Point", "2011"),
    56: ("Boronia Park", "2111"), 57: ("Bondi Beach", "2026"),
    58: ("Drummoyne", "2047"), 63: ("Randwick", "2031"),
    64: ("Leichhardt", "2040"), 65: ("Bondi Westfield", "2022"),
    66: ("Newcastle", "2300"), 67: ("Lindfield", "2070"),
    68: ("Albury", "2640"), 69: ("Rose Bay", "2029"),
    70: ("West End QLD", "4101"), 74: ("Isle of Capri QLD", "4217"),
    75: ("Clayfield QLD", "4011"), 76: ("Lane Cove", "2066"),
    77: ("Dural", "2158"), 80: ("Majura Park ACT", "2609"),
    84: ("Redfern", "2016"), 85: ("Marrickville", "2204"),
    86: ("Miranda", "2228"), 87: ("Maroubra", "2035"),
}


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def _load_postcode_coords() -> dict:
    """Load postcode -> {lat, lon} mapping."""
    path = _PROJECT / "data" / "postcode_coords.json"
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


@st.cache_data(ttl=300)
def _build_store_coords() -> Dict[int, Tuple[float, float]]:
    """Build store_id -> (lat, lon) using postcode coordinates."""
    pc = _load_postcode_coords()
    coords = {}
    for sid, (suburb, postcode) in _STORE_POSTCODES.items():
        if postcode in pc:
            coords[sid] = (pc[postcode]["lat"], pc[postcode]["lon"])
    return coords


@st.cache_data(ttl=300)
def _load_revenue_data() -> pd.DataFrame:
    """Load monthly retail revenue for all stores."""
    df = get_summary_df(channel="Retail")
    if df.empty:
        return df
    df["date"] = pd.to_datetime(
        df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01"
    )
    return df


@st.cache_data(ttl=300)
def _load_store_names() -> Dict[int, str]:
    """Map store_id -> display name."""
    stores = get_stores_list()
    mapping = {}
    for s in stores:
        name = s["store_name"]
        if name.startswith("HFM "):
            name = name[4:]
        mapping[s["store_id"]] = name
    return mapping


# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in km."""
    R = 6371.0  # Earth radius in km
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Distance matrix builder
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def _build_distance_matrix(
    coords: Dict[int, Tuple[float, float]],
) -> pd.DataFrame:
    """Pairwise distance matrix for all stores with known coordinates."""
    ids = sorted(coords.keys())
    n = len(ids)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(
                coords[ids[i]][0], coords[ids[i]][1],
                coords[ids[j]][0], coords[ids[j]][1],
            )
            matrix[i][j] = d
            matrix[j][i] = d
    return pd.DataFrame(matrix, index=ids, columns=ids)


# ---------------------------------------------------------------------------
# Detect store opening dates
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def _detect_opening_dates(df: pd.DataFrame) -> Dict[int, datetime]:
    """Detect first month of revenue data for each store (proxy for opening)."""
    openings = {}
    for sid, grp in df.groupby("store_id"):
        valid = grp[grp["revenue"].abs() > 1000]
        if not valid.empty:
            openings[int(sid)] = valid["date"].min()
    return openings


# ---------------------------------------------------------------------------
# Cannibalisation analysis helpers
# ---------------------------------------------------------------------------

def _compute_before_after(
    df: pd.DataFrame,
    target_store: int,
    nearby_stores: List[int],
    opening_date: datetime,
    months_window: int = 12,
) -> pd.DataFrame:
    """Compare nearby store revenue before vs after a store opening."""
    before_start = opening_date - pd.DateOffset(months=months_window)
    after_end = opening_date + pd.DateOffset(months=months_window)

    results = []
    for sid in nearby_stores:
        store_data = df[df["store_id"] == sid].copy()
        if store_data.empty:
            continue

        before = store_data[
            (store_data["date"] >= before_start)
            & (store_data["date"] < opening_date)
        ]
        after = store_data[
            (store_data["date"] >= opening_date)
            & (store_data["date"] < after_end)
        ]

        if before.empty or after.empty:
            continue

        before_avg = before["revenue"].mean()
        after_avg = after["revenue"].mean()
        pct_change = ((after_avg - before_avg) / abs(before_avg) * 100) if before_avg != 0 else 0.0

        results.append({
            "store_id": sid,
            "before_avg_monthly": before_avg,
            "after_avg_monthly": after_avg,
            "pct_change": round(pct_change, 2),
            "before_months": len(before),
            "after_months": len(after),
        })

    return pd.DataFrame(results)


def _network_growth_rate(df: pd.DataFrame, opening_date: datetime, months_window: int = 12) -> float:
    """Calculate average network-wide monthly revenue growth rate around a date."""
    before_start = opening_date - pd.DateOffset(months=months_window)
    after_end = opening_date + pd.DateOffset(months=months_window)

    network_before = df[
        (df["date"] >= before_start) & (df["date"] < opening_date)
    ].groupby("date")["revenue"].sum().mean()

    network_after = df[
        (df["date"] >= opening_date) & (df["date"] < after_end)
    ].groupby("date")["revenue"].sum().mean()

    if network_before and network_before != 0:
        return (network_after - network_before) / abs(network_before) * 100
    return 0.0


# ═══════════════════════════════════════════════════════════════════════════
# PAGE RENDER
# ═══════════════════════════════════════════════════════════════════════════

user = st.session_state.get("auth_user")

render_header(
    "Cannibalisation Analysis",
    "Measuring network impact when stores trade near each other",
    goals=["G1", "G3"],
    strategy_context="Network-level thinking: a new store must grow the pie, not just shuffle slices.",
)

# Load data
coords = _build_store_coords()
rev_df = _load_revenue_data()
names = _load_store_names()

if rev_df.empty:
    st.error("No store P&L data found. Please ensure store_pl_summary has been ingested.")
    render_footer("Cannibalisation Analysis", "Store P&L History \u2014 GL Data", user=user)
    st.stop()

dist_matrix = _build_distance_matrix(coords)
openings = _detect_opening_dates(rev_df)

# Earliest date in dataset — stores opening after this are "new"
data_start = rev_df["date"].min()
# Buffer: if a store's first data is > 6 months after data_start, treat as "opened during period"
new_store_cutoff = data_start + pd.DateOffset(months=6)

# Identify new stores (opened during the data period)
new_stores = {sid: dt for sid, dt in openings.items() if dt > new_store_cutoff}

# Store name helper
def _sname(sid: int) -> str:
    return names.get(sid, _STORE_POSTCODES.get(sid, (str(sid),))[0])


# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Network Overview",
    "Distance Matrix",
    "Before/After Analysis",
    "Cannibalisation Pairs",
    "What-If Simulator",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: Network Overview
# ═══════════════════════════════════════════════════════════════════════════

with tab1:
    st.subheader("Store Network Proximity Map")

    if not coords:
        st.warning("No store coordinates available.")
    else:
        # Calculate nearest-neighbour distance for each store
        nn_distances = {}
        for sid in coords:
            if sid in dist_matrix.index:
                row = dist_matrix.loc[sid].drop(sid, errors="ignore")
                row_positive = row[row > 0]
                if not row_positive.empty:
                    nn_distances[sid] = row_positive.min()

        # Classify stores
        map_rows = []
        for sid, (lat, lon) in coords.items():
            nn_dist = nn_distances.get(sid, 999)
            if nn_dist < 2:
                zone = "Heavy overlap (<2km)"
                colour = RED
            elif nn_dist < 5:
                zone = "Mild overlap (2-5km)"
                colour = ORANGE
            else:
                zone = "Isolated (>5km)"
                colour = GREEN

            map_rows.append({
                "store_id": sid,
                "store_name": _sname(sid),
                "lat": lat,
                "lon": lon,
                "nearest_km": round(nn_dist, 1),
                "zone": zone,
                "colour": colour,
            })

        map_df = pd.DataFrame(map_rows)

        # Metric cards
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Stores (with coords)", len(coords))
        with c2:
            avg_nn = np.mean(list(nn_distances.values())) if nn_distances else 0
            st.metric("Avg Nearest-Store Distance", f"{avg_nn:.1f} km")
        with c3:
            close_count = sum(1 for d in nn_distances.values() if d < 3)
            st.metric("Stores with <3km Neighbour", close_count)

        # Map
        colour_map = {
            "Heavy overlap (<2km)": RED,
            "Mild overlap (2-5km)": ORANGE,
            "Isolated (>5km)": GREEN,
        }

        fig_map = px.scatter_mapbox(
            map_df,
            lat="lat",
            lon="lon",
            color="zone",
            color_discrete_map=colour_map,
            size="nearest_km",
            size_max=18,
            hover_name="store_name",
            hover_data={"nearest_km": ":.1f", "zone": True, "lat": False, "lon": False},
            zoom=5,
            center={"lat": -33.8, "lon": 151.0},
        )
        fig_map.update_layout(
            mapbox_style="carto-darkmatter",
            height=600,
            legend_title_text="Proximity Zone",
            **_DARK_LAYOUT,
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # Summary table
        with st.expander("Store Proximity Details"):
            display_df = map_df[["store_id", "store_name", "nearest_km", "zone"]].sort_values("nearest_km")
            display_df.columns = ["Store ID", "Store Name", "Nearest (km)", "Zone"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: Distance Matrix
# ═══════════════════════════════════════════════════════════════════════════

with tab2:
    st.subheader("Pairwise Distance Heatmap")
    st.caption("Showing store pairs within 10km of each other. Red = <3km, Amber = 3-5km.")

    if dist_matrix.empty:
        st.warning("No distance data available.")
    else:
        # Filter to stores that have at least one neighbour within 10km
        close_mask = dist_matrix < 10
        np.fill_diagonal(close_mask.values, False)
        relevant_stores = close_mask.any(axis=1)
        relevant_ids = relevant_stores[relevant_stores].index.tolist()

        if not relevant_ids:
            st.info("No store pairs found within 10km of each other.")
        else:
            sub = dist_matrix.loc[relevant_ids, relevant_ids].copy()

            # Replace diagonal and >10km with NaN for cleaner display
            for sid in relevant_ids:
                sub.loc[sid, sid] = np.nan
            sub = sub.where(sub <= 10)

            # Build labels
            labels = [f"{_sname(sid)} ({sid})" for sid in relevant_ids]

            # Custom colour scale: red (<3), amber (3-5), pale (5-10)
            colorscale = [
                [0.0, RED],
                [0.3, ORANGE],
                [0.5, GOLD],
                [1.0, "#1A2A1A"],
            ]

            fig_heat = go.Figure(data=go.Heatmap(
                z=sub.values,
                x=labels,
                y=labels,
                colorscale=colorscale,
                zmin=0,
                zmax=10,
                hovertemplate="<b>%{x}</b> ↔ <b>%{y}</b><br>Distance: %{z:.1f} km<extra></extra>",
                colorbar=dict(title="km", tickfont=dict(color=TEXT_SECONDARY)),
            ))
            fig_heat.update_layout(
                height=max(500, len(relevant_ids) * 28),
                xaxis=dict(tickangle=45, tickfont=dict(color=TEXT_SECONDARY, size=10)),
                yaxis=dict(tickfont=dict(color=TEXT_SECONDARY, size=10), autorange="reversed"),
                **_DARK_LAYOUT,
            )
            st.plotly_chart(fig_heat, use_container_width=True)

            # Closest pairs table
            st.markdown("**Closest Store Pairs**")
            pairs = []
            seen = set()
            for i in relevant_ids:
                for j in relevant_ids:
                    if i >= j:
                        continue
                    pair_key = (min(i, j), max(i, j))
                    if pair_key in seen:
                        continue
                    seen.add(pair_key)
                    d = dist_matrix.loc[i, j]
                    if d <= 10:
                        pairs.append({
                            "Store A": _sname(i),
                            "Store B": _sname(j),
                            "Distance (km)": round(d, 2),
                        })

            pairs_df = pd.DataFrame(pairs).sort_values("Distance (km)")
            st.dataframe(pairs_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: Before/After Analysis
# ═══════════════════════════════════════════════════════════════════════════

with tab3:
    st.subheader("New Store Impact Analysis")
    st.caption(
        "Select a store that opened during the data period. "
        "We measure revenue changes in nearby existing stores before vs after the opening."
    )

    if not new_stores:
        st.info(
            "No stores detected as opening during the data period. "
            "All stores appear to have data from the earliest period."
        )
    else:
        # Build selection list
        new_store_options = {
            f"{_sname(sid)} (Store {sid}) — opened {dt.strftime('%b %Y')}": sid
            for sid, dt in sorted(new_stores.items(), key=lambda x: x[1])
        }

        selected_label = st.selectbox(
            "Select new store",
            list(new_store_options.keys()),
            key="cannib_new_store",
        )
        selected_sid = new_store_options[selected_label]
        opening_dt = new_stores[selected_sid]

        radius_km = st.slider("Search radius (km)", 1.0, 15.0, 5.0, 0.5, key="cannib_radius")
        months_window = st.slider("Comparison window (months before/after)", 6, 24, 12, key="cannib_window")

        # Find nearby stores that existed before the new one opened
        nearby = []
        if selected_sid in coords:
            for sid, (lat, lon) in coords.items():
                if sid == selected_sid:
                    continue
                if sid not in openings:
                    continue
                # Must have been open before the new store
                if openings[sid] >= opening_dt:
                    continue
                d = haversine(coords[selected_sid][0], coords[selected_sid][1], lat, lon)
                if d <= radius_km:
                    nearby.append(sid)

        if not nearby:
            st.info(f"No existing stores found within {radius_km:.0f}km of {_sname(selected_sid)}.")
        else:
            st.markdown(f"**{len(nearby)} existing store(s) within {radius_km:.0f}km**")

            # Network growth adjustment
            net_growth = _network_growth_rate(rev_df, opening_dt, months_window)

            # Before/after revenue comparison
            ba_df = _compute_before_after(rev_df, selected_sid, nearby, opening_dt, months_window)

            if ba_df.empty:
                st.warning("Insufficient data for before/after comparison.")
            else:
                ba_df["store_name"] = ba_df["store_id"].map(lambda x: _sname(x))
                ba_df["adjusted_change"] = (ba_df["pct_change"] - net_growth).round(2)

                # Summary metrics
                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    st.metric("Network Growth (same period)", f"{net_growth:+.1f}%")
                with mc2:
                    avg_raw = ba_df["pct_change"].mean()
                    st.metric("Avg Raw Change (nearby)", f"{avg_raw:+.1f}%")
                with mc3:
                    avg_adj = ba_df["adjusted_change"].mean()
                    st.metric("Avg Adjusted Change", f"{avg_adj:+.1f}%")

                # Revenue trajectories chart
                st.markdown("**Revenue Trajectories**")
                chart_stores = nearby + [selected_sid]
                chart_data = rev_df[rev_df["store_id"].isin(chart_stores)].copy()
                chart_data["store_label"] = chart_data["store_id"].map(lambda x: _sname(x))

                fig_traj = px.line(
                    chart_data,
                    x="date",
                    y="revenue",
                    color="store_label",
                    labels={"revenue": "Monthly Revenue ($)", "date": "Date"},
                )
                # Vertical line at opening
                fig_traj.add_vline(
                    x=opening_dt.timestamp() * 1000,
                    line_dash="dash",
                    line_color=RED,
                    annotation_text=f"{_sname(selected_sid)} opens",
                    annotation_font_color=RED,
                )
                fig_traj.update_layout(
                    height=450,
                    legend_title_text="Store",
                    yaxis_tickformat="$,.0f",
                    **_DARK_LAYOUT,
                )
                st.plotly_chart(fig_traj, use_container_width=True)

                # Impact table
                st.markdown("**Impact Breakdown**")
                impact_display = ba_df[[
                    "store_name", "before_avg_monthly", "after_avg_monthly",
                    "pct_change", "adjusted_change",
                ]].copy()
                impact_display.columns = [
                    "Store", "Before (avg monthly)", "After (avg monthly)",
                    "Raw Change %", "Adjusted Change %",
                ]
                for col in ["Before (avg monthly)", "After (avg monthly)"]:
                    impact_display[col] = impact_display[col].apply(lambda x: f"${x:,.0f}")

                st.dataframe(impact_display, use_container_width=True, hide_index=True)

                # Net impact calculation
                st.markdown("**Net Network Impact**")
                new_store_data = rev_df[
                    (rev_df["store_id"] == selected_sid)
                    & (rev_df["date"] >= opening_dt)
                    & (rev_df["date"] < opening_dt + pd.DateOffset(months=months_window))
                ]
                new_rev_avg = new_store_data["revenue"].mean() if not new_store_data.empty else 0

                cannibalised = ba_df[ba_df["adjusted_change"] < 0]["adjusted_change"].sum()
                cannibalised_dollar = sum(
                    row["before_avg_monthly"] * row["adjusted_change"] / 100
                    for _, row in ba_df[ba_df["adjusted_change"] < 0].iterrows()
                )

                n1, n2, n3 = st.columns(3)
                with n1:
                    st.metric("New Store Avg Monthly Rev", f"${new_rev_avg:,.0f}")
                with n2:
                    st.metric("Cannibalised (monthly)", f"${cannibalised_dollar:,.0f}")
                with n3:
                    net_monthly = new_rev_avg + cannibalised_dollar
                    st.metric(
                        "Net Network Gain (monthly)",
                        f"${net_monthly:,.0f}",
                        delta=f"${net_monthly:,.0f}",
                        delta_color="normal",
                    )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: Cannibalisation Pairs
# ═══════════════════════════════════════════════════════════════════════════

with tab4:
    st.subheader("Cannibalisation Pairs")
    st.caption("Store pairs within 5km, showing distance, revenue correlation, and detected impact.")

    pair_radius = st.slider("Pair radius (km)", 1.0, 10.0, 5.0, 0.5, key="pair_radius")

    # Build pairs
    pair_rows = []
    seen_pairs = set()
    store_ids_with_coords = sorted(coords.keys())

    for i, sid_a in enumerate(store_ids_with_coords):
        for sid_b in store_ids_with_coords[i + 1:]:
            if sid_a not in dist_matrix.index or sid_b not in dist_matrix.columns:
                continue
            d = dist_matrix.loc[sid_a, sid_b]
            if d > pair_radius:
                continue

            pair_key = (min(sid_a, sid_b), max(sid_a, sid_b))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            # Revenue correlation
            rev_a = rev_df[rev_df["store_id"] == sid_a][["date", "revenue"]].set_index("date")
            rev_b = rev_df[rev_df["store_id"] == sid_b][["date", "revenue"]].set_index("date")
            merged_rev = rev_a.join(rev_b, lsuffix="_a", rsuffix="_b", how="inner")

            corr = np.nan
            overlap_months = 0
            if len(merged_rev) > 3:
                corr_val = merged_rev["revenue_a"].corr(merged_rev["revenue_b"])
                corr = round(corr_val, 3) if not np.isnan(corr_val) else np.nan
                overlap_months = len(merged_rev)

            # Detect if one opened after the other
            open_a = openings.get(sid_a)
            open_b = openings.get(sid_b)
            impact_note = "Both existing"
            impact_pct = np.nan

            if open_a and open_b:
                if open_a > new_store_cutoff and open_b <= new_store_cutoff:
                    # A opened after B — check impact on B
                    ba = _compute_before_after(rev_df, sid_a, [sid_b], open_a, 12)
                    if not ba.empty:
                        net_g = _network_growth_rate(rev_df, open_a, 12)
                        impact_pct = round(ba.iloc[0]["pct_change"] - net_g, 2)
                    impact_note = f"{_sname(sid_a)} opened {open_a.strftime('%b %Y')}"
                elif open_b > new_store_cutoff and open_a <= new_store_cutoff:
                    ba = _compute_before_after(rev_df, sid_b, [sid_a], open_b, 12)
                    if not ba.empty:
                        net_g = _network_growth_rate(rev_df, open_b, 12)
                        impact_pct = round(ba.iloc[0]["pct_change"] - net_g, 2)
                    impact_note = f"{_sname(sid_b)} opened {open_b.strftime('%b %Y')}"

            pair_rows.append({
                "Store A": _sname(sid_a),
                "Store B": _sname(sid_b),
                "Distance (km)": round(d, 2),
                "Correlation": corr,
                "Overlap Months": overlap_months,
                "Impact Note": impact_note,
                "Adjusted Impact %": impact_pct,
            })

    if not pair_rows:
        st.info(f"No store pairs found within {pair_radius:.0f}km.")
    else:
        pairs_full = pd.DataFrame(pair_rows).sort_values("Distance (km)")
        st.dataframe(
            pairs_full,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Distance (km)": st.column_config.NumberColumn(format="%.2f"),
                "Correlation": st.column_config.NumberColumn(format="%.3f"),
                "Adjusted Impact %": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )

        # Summary
        pairs_with_impact = pairs_full.dropna(subset=["Adjusted Impact %"])
        if not pairs_with_impact.empty:
            st.markdown("---")
            pc1, pc2 = st.columns(2)
            with pc1:
                neg_impacts = pairs_with_impact[pairs_with_impact["Adjusted Impact %"] < 0]
                st.metric(
                    "Pairs Showing Cannibalisation",
                    f"{len(neg_impacts)} of {len(pairs_with_impact)}",
                )
            with pc2:
                avg_impact = pairs_with_impact["Adjusted Impact %"].mean()
                st.metric("Avg Adjusted Impact", f"{avg_impact:+.1f}%")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 5: What-If Simulator
# ═══════════════════════════════════════════════════════════════════════════

with tab5:
    st.subheader("What-If Expansion Simulator")
    st.caption(
        "Enter a potential new store location and expected revenue. "
        "Estimates cannibalisation based on historical patterns."
    )

    # Compute historical cannibalisation rate from Tab 3 data
    historical_rates = []
    for new_sid, open_dt in new_stores.items():
        if new_sid not in coords:
            continue
        for existing_sid, (elat, elon) in coords.items():
            if existing_sid == new_sid:
                continue
            if existing_sid not in openings or openings[existing_sid] >= open_dt:
                continue
            d = haversine(coords[new_sid][0], coords[new_sid][1], elat, elon)
            if d <= 5.0:
                ba = _compute_before_after(rev_df, new_sid, [existing_sid], open_dt, 12)
                if not ba.empty:
                    net_g = _network_growth_rate(rev_df, open_dt, 12)
                    adj = ba.iloc[0]["pct_change"] - net_g
                    historical_rates.append({"distance_km": d, "adjusted_impact_pct": adj})

    if historical_rates:
        hist_df = pd.DataFrame(historical_rates)
        avg_cannib_rate = hist_df[hist_df["adjusted_impact_pct"] < 0]["adjusted_impact_pct"].mean()
        if np.isnan(avg_cannib_rate):
            avg_cannib_rate = -3.0  # Default fallback
    else:
        avg_cannib_rate = -3.0  # Conservative estimate

    st.info(
        f"Model uses historical avg cannibalisation rate: **{avg_cannib_rate:.1f}%** "
        f"(from {len(historical_rates)} observed store-pair interactions)."
    )

    # Inputs
    pc_coords = _load_postcode_coords()
    suburb_options = sorted(_STORE_POSTCODES.values(), key=lambda x: x[0])
    all_postcodes = sorted(pc_coords.keys())

    ic1, ic2 = st.columns(2)
    with ic1:
        input_postcode = st.selectbox(
            "Postcode of new location",
            all_postcodes,
            index=all_postcodes.index("2000") if "2000" in all_postcodes else 0,
            key="whatif_postcode",
        )
    with ic2:
        expected_annual_rev = st.number_input(
            "Expected Year 1 Annual Revenue ($M)",
            min_value=1.0,
            max_value=100.0,
            value=25.0,
            step=1.0,
            key="whatif_revenue",
        )

    whatif_radius = st.slider("Impact radius (km)", 1.0, 15.0, 5.0, 0.5, key="whatif_radius")

    if input_postcode not in pc_coords:
        st.error("Selected postcode has no coordinate data.")
    else:
        new_lat = pc_coords[input_postcode]["lat"]
        new_lon = pc_coords[input_postcode]["lon"]
        expected_monthly = expected_annual_rev * 1_000_000 / 12

        # Find nearby existing stores
        affected = []
        for sid, (slat, slon) in coords.items():
            d = haversine(new_lat, new_lon, slat, slon)
            if d <= whatif_radius:
                # Get latest 12-month average revenue
                recent = rev_df[
                    (rev_df["store_id"] == sid)
                    & (rev_df["date"] >= rev_df["date"].max() - pd.DateOffset(months=12))
                ]
                avg_monthly = recent["revenue"].mean() if not recent.empty else 0

                # Distance-based cannibalisation decay: closer = more impact
                if d < 0.5:
                    distance_factor = 1.5
                elif d < 2:
                    distance_factor = 1.2
                elif d < 3:
                    distance_factor = 1.0
                elif d < 5:
                    distance_factor = 0.7
                else:
                    distance_factor = 0.4

                est_impact_pct = avg_cannib_rate * distance_factor
                est_impact_dollar = avg_monthly * est_impact_pct / 100

                affected.append({
                    "store_id": sid,
                    "store_name": _sname(sid),
                    "distance_km": round(d, 2),
                    "current_monthly_rev": avg_monthly,
                    "est_impact_pct": round(est_impact_pct, 2),
                    "est_impact_monthly": round(est_impact_dollar, 0),
                })

        if not affected:
            st.success(
                f"No existing HFM stores within {whatif_radius:.0f}km of postcode {input_postcode}. "
                "Zero cannibalisation expected."
            )
        else:
            aff_df = pd.DataFrame(affected).sort_values("distance_km")

            # Map showing proposed location and affected stores
            map_points = []
            for _, row in aff_df.iterrows():
                sid = row["store_id"]
                if sid in coords:
                    map_points.append({
                        "lat": coords[sid][0],
                        "lon": coords[sid][1],
                        "name": row["store_name"],
                        "type": "Existing Store",
                        "size": 10,
                    })
            map_points.append({
                "lat": new_lat,
                "lon": new_lon,
                "name": f"Proposed (PC {input_postcode})",
                "type": "Proposed Location",
                "size": 18,
            })

            sim_map_df = pd.DataFrame(map_points)
            sim_map_df["size"] = pd.to_numeric(sim_map_df["size"], errors="coerce").fillna(10).clip(lower=1)

            fig_sim = px.scatter_mapbox(
                sim_map_df,
                lat="lat",
                lon="lon",
                color="type",
                size="size",
                size_max=18,
                hover_name="name",
                color_discrete_map={
                    "Existing Store": BLUE,
                    "Proposed Location": RED,
                },
                zoom=11,
                center={"lat": new_lat, "lon": new_lon},
            )
            fig_sim.update_layout(
                mapbox_style="carto-darkmatter",
                height=450,
                legend_title_text="",
                **_DARK_LAYOUT,
            )
            st.plotly_chart(fig_sim, use_container_width=True)

            # Impact table
            st.markdown("**Estimated Impact on Existing Stores**")
            impact_table = aff_df[[
                "store_name", "distance_km", "current_monthly_rev",
                "est_impact_pct", "est_impact_monthly",
            ]].copy()
            impact_table.columns = [
                "Store", "Distance (km)", "Current Monthly Rev",
                "Est. Impact %", "Est. Monthly Impact ($)",
            ]
            st.dataframe(
                impact_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Current Monthly Rev": st.column_config.NumberColumn(format="$%,.0f"),
                    "Est. Monthly Impact ($)": st.column_config.NumberColumn(format="$%,.0f"),
                    "Est. Impact %": st.column_config.NumberColumn(format="%.1f%%"),
                },
            )

            # Net impact summary
            st.markdown("---")
            total_cannib_monthly = aff_df["est_impact_monthly"].sum()
            total_cannib_annual = total_cannib_monthly * 12
            net_gain_monthly = expected_monthly + total_cannib_monthly
            net_gain_annual = net_gain_monthly * 12

            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1:
                st.metric(
                    "New Store Revenue (monthly)",
                    f"${expected_monthly:,.0f}",
                )
            with sc2:
                st.metric(
                    "Total Cannibalisation (monthly)",
                    f"${total_cannib_monthly:,.0f}",
                )
            with sc3:
                st.metric(
                    "Net Network Gain (monthly)",
                    f"${net_gain_monthly:,.0f}",
                    delta=f"{net_gain_monthly / expected_monthly * 100:.0f}% retained" if expected_monthly else None,
                )
            with sc4:
                st.metric(
                    "Net Network Gain (annual)",
                    f"${net_gain_annual:,.0f}",
                )

            # Verdict
            retention_pct = (net_gain_monthly / expected_monthly * 100) if expected_monthly else 0
            if retention_pct >= 80:
                verdict_colour = GREEN
                verdict = "LOW CANNIBALISATION"
                verdict_msg = "Strong net gain. Minimal impact on existing stores."
            elif retention_pct >= 50:
                verdict_colour = ORANGE
                verdict = "MODERATE CANNIBALISATION"
                verdict_msg = "Meaningful overlap. Review individual store impacts before proceeding."
            else:
                verdict_colour = RED
                verdict = "HIGH CANNIBALISATION"
                verdict_msg = "Significant revenue transfer. Consider alternative location."

            st.markdown(
                glass_card(
                    f"<h3 style='color:{verdict_colour};margin:0;'>{verdict}</h3>"
                    f"<p style='color:{TEXT_SECONDARY};margin:4px 0 0;'>{verdict_msg}</p>"
                    f"<p style='color:{TEXT_MUTED};font-size:0.85em;margin:4px 0 0;'>"
                    f"Revenue retention: {retention_pct:.0f}% | "
                    f"Affected stores: {len(aff_df)} | "
                    f"Avg distance: {aff_df['distance_km'].mean():.1f}km</p>",
                    border_color=verdict_colour,
                ),
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════
# Footer
# ═══════════════════════════════════════════════════════════════════════════

render_footer("Cannibalisation Analysis", "Store P&L History \u2014 GL Data", user=user)
