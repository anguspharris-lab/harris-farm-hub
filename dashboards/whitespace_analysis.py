"""
Harris Farm Hub — Whitespace Analysis Dashboard
Store network performance, ideal store profile, and expansion opportunities
based on CBAS (CommBank iQ) data — 31 active stores, 16 whitespace targets.

Source: Harris Farm Store Network Analysis - 20 Feb 2026.xlsx
Methodology: Ideal Profile → Coverage Gaps → Score → Cannibalisation → Prioritise
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared.styles import render_header, render_footer, HFM_GREEN
from shared.whitespace_data import (
    get_stores_df,
    get_opportunities_df,
    get_ideal_profile,
    get_catchments,
    get_reconciliation,
    get_meta,
    get_postcode_coords,
    score_breakdown_chart,
    performance_tier_summary,
    TIER_COLOURS,
    PHASE_COLOURS,
    CONFIDENCE_COLOURS,
)

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_OK = True
except ImportError:
    FOLIUM_OK = False

user = st.session_state.get("auth_user")

# ── Header ────────────────────────────────────────────────────────────────────

render_header(
    "Whitespace Analysis",
    "Store network performance | Ideal store profile | Expansion opportunities",
    goals=["G1", "G3"],
    strategy_context=(
        "'Fewer, Bigger, Better' — identify the right locations for "
        "profitable growth using CBAS store network data."
    ),
)
st.caption(
    "CBAS data is directional. Low share does not equal opportunity. "
    "Always validate with demographics, site visits, and cannibalisation modelling."
)

# ── Load data ─────────────────────────────────────────────────────────────────

stores_df = get_stores_df()
opps_df = get_opportunities_df()
profile = get_ideal_profile()
meta = get_meta()

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_exec, tab_network, tab_profile, tab_opps, tab_map, tab_recon = st.tabs([
    "Executive Summary",
    "Store Network",
    "Ideal Profile",
    "Whitespace Opportunities",
    "Map",
    "Store Reconciliation",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

with tab_exec:
    st.subheader("Network at a Glance")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Stores", meta.get("store_count", 31))
    c2.metric("Whitespace Targets", meta.get("opportunity_count", 16))
    c3.metric("Phase 1 Priorities", len(opps_df[opps_df["phase"] == 1]))
    c4.metric("States Covered", len(meta.get("states_covered", [])))

    st.markdown("---")

    # Top 5 opportunities
    st.subheader("Top 5 Expansion Opportunities")
    top5 = opps_df.head(5)[["rank", "suburb", "state", "score", "phase",
                             "recommended_format", "addressable_revenue_m",
                             "data_confidence"]].copy()
    top5.columns = ["Rank", "Suburb", "State", "Score", "Phase",
                     "Format", "Revenue ($M)", "Confidence"]
    st.dataframe(top5, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Ideal store profile summary
    st.subheader("Ideal Store Profile")
    tq = profile.get("top_quartile_metrics", {})
    top_stores = profile.get("top_quartile_stores", [])
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("**Top Quartile Benchmarks**")
            st.markdown(f"- **Size:** {profile.get('sqm_range', [900, 1500])[0]}-{profile.get('sqm_range', [900, 1500])[1]} sqm")
            st.markdown(f"- **Revenue/sqm:** ${tq.get('avg_rev_per_sqm', 0):,.0f}")
            st.markdown(f"- **Market Share:** {tq.get('avg_share', 0):.1%}")
            st.markdown(f"- **Share of Wallet:** {tq.get('avg_sow', 0):.1%}")
            st.markdown(f"- **Spend/Customer:** ${tq.get('avg_spend_per_customer', 0):,.0f}")
            st.markdown(f"- **Customer Growth:** {tq.get('avg_customer_growth', 0):.1f}%")
    with col2:
        with st.container(border=True):
            st.markdown("**Top 7 Stores**")
            for s in top_stores:
                st.markdown(f"- {s}")
            st.caption("These stores average $28.9K/sqm — 2.1x the network median")

    st.markdown("---")

    # Phased rollout
    st.subheader("3-Year Phased Rollout")
    for phase_num in [1, 2, 3]:
        phase_stores = opps_df[opps_df["phase"] == phase_num]
        colour = PHASE_COLOURS.get(phase_num, "#FFFFFF")
        year_label = f"Year {phase_num}"
        suburbs = ", ".join(phase_stores["suburb"].tolist())
        st.markdown(
            f"**{year_label}** ({len(phase_stores)} locations): {suburbs}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: STORE NETWORK
# ═══════════════════════════════════════════════════════════════════════════════

with tab_network:
    st.subheader("All 31 CBAS Stores")

    # State summary
    state_counts = stores_df["State"].value_counts()
    cols = st.columns(len(state_counts))
    for i, (state, count) in enumerate(state_counts.items()):
        cols[i].metric(state, f"{count} stores")

    st.markdown("---")

    # Full table
    display_cols = [
        "Short Name", "Locality", "State", "Store Size (SQM)",
        "Annual Sales ($M)", "Rev per SQM", "Performance Tier",
        "Profitability Tier", "Market Share", "Share of Wallet",
        "Customer Growth (%)", "Top Competitor",
    ]
    available_cols = [c for c in display_cols if c in stores_df.columns]
    display_df = stores_df[available_cols].copy()

    # Format percentages
    if "Market Share" in display_df.columns:
        display_df["Market Share"] = display_df["Market Share"].apply(
            lambda x: f"{float(x):.1%}" if pd.notna(x) and x is not None else "N/A"
        )
    if "Share of Wallet" in display_df.columns:
        display_df["Share of Wallet"] = display_df["Share of Wallet"].apply(
            lambda x: f"{float(x):.1%}" if pd.notna(x) and x is not None else "N/A"
        )

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=600)

    st.markdown("---")

    # Revenue per SQM chart
    st.subheader("Revenue per SQM by Store")
    chart_df = stores_df[["Short Name", "Rev per SQM"]].dropna().sort_values("Rev per SQM")
    fig = px.bar(
        chart_df, x="Rev per SQM", y="Short Name",
        orientation="h",
        color="Rev per SQM",
        color_continuous_scale=["#dc2626", "#d97706", "#2ECC71"],
    )
    fig.update_layout(
        height=max(400, len(chart_df) * 22),
        margin=dict(l=0, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FFFFFF"),
        coloraxis_showscale=False,
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title="Revenue per SQM ($)"),
        yaxis=dict(showgrid=False, title=""),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Performance tier summary
    st.markdown("---")
    st.subheader("Performance Tier Summary")
    tier_df = performance_tier_summary()
    st.dataframe(tier_df, use_container_width=True, hide_index=True)
    st.caption("Tier 1 = Top performer, Tier 5 = Needs improvement")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: IDEAL PROFILE
# ═══════════════════════════════════════════════════════════════════════════════

with tab_profile:
    st.subheader("What Makes a Winning Harris Farm Store?")

    tq_m = profile.get("top_quartile_metrics", {})
    avg_m = profile.get("network_average_metrics", {})
    bq_m = profile.get("bottom_quartile_metrics", {})

    # Comparison table
    comparison_data = {
        "Metric": [
            "Avg Sales ($M)", "Avg SQM", "Rev/SQM ($)",
            "Market Share", "Share of Wallet",
            "Spend/Customer ($)", "Visits/Customer", "Customer Growth (%)"
        ],
        "Top Quartile": [
            f"${tq_m.get('avg_sales_m', 0):.1f}M",
            f"{tq_m.get('avg_sqm', 0):,.0f}",
            f"${tq_m.get('avg_rev_per_sqm', 0):,.0f}",
            f"{tq_m.get('avg_share', 0):.1%}",
            f"{tq_m.get('avg_sow', 0):.1%}",
            f"${tq_m.get('avg_spend_per_customer', 0):,.0f}",
            f"{tq_m.get('avg_visits_per_customer', 0):.1f}",
            f"{tq_m.get('avg_customer_growth', 0):.1f}%",
        ],
        "Network Average": [
            f"${avg_m.get('avg_sales_m', 0):.1f}M",
            f"{avg_m.get('avg_sqm', 0):,.0f}",
            f"${avg_m.get('avg_rev_per_sqm', 0):,.0f}",
            f"{avg_m.get('avg_share', 0):.1%}",
            f"{avg_m.get('avg_sow', 0):.1%}",
            f"${avg_m.get('avg_spend_per_customer', 0):,.0f}",
            f"{avg_m.get('avg_visits_per_customer', 0):.1f}",
            f"{avg_m.get('avg_customer_growth', 0):.1f}%",
        ],
        "Bottom Quartile": [
            f"${bq_m.get('avg_sales_m', 0):.1f}M",
            f"{bq_m.get('avg_sqm', 0):,.0f}",
            f"${bq_m.get('avg_rev_per_sqm', 0):,.0f}",
            f"{bq_m.get('avg_share', 0):.1%}",
            f"{bq_m.get('avg_sow', 0):.1%}",
            f"${bq_m.get('avg_spend_per_customer', 0):,.0f}",
            f"{bq_m.get('avg_visits_per_customer', 0):.1f}",
            f"{bq_m.get('avg_customer_growth', 0):.1f}%",
        ],
    }
    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Radar chart — top quartile vs network average
    st.subheader("Profile Comparison")
    radar_labels = ["Rev/SQM", "Share", "SoW", "Spend/Cust", "Visits/Cust", "Cust Growth"]
    # Normalise to 0-1 scale using top quartile as max
    tq_vals = [
        tq_m.get("avg_rev_per_sqm", 0),
        tq_m.get("avg_share", 0),
        tq_m.get("avg_sow", 0),
        tq_m.get("avg_spend_per_customer", 0),
        tq_m.get("avg_visits_per_customer", 0),
        tq_m.get("avg_customer_growth", 0),
    ]
    avg_vals = [
        avg_m.get("avg_rev_per_sqm", 0),
        avg_m.get("avg_share", 0),
        avg_m.get("avg_sow", 0),
        avg_m.get("avg_spend_per_customer", 0),
        avg_m.get("avg_visits_per_customer", 0),
        avg_m.get("avg_customer_growth", 0),
    ]
    bq_vals = [
        bq_m.get("avg_rev_per_sqm", 0),
        bq_m.get("avg_share", 0),
        bq_m.get("avg_sow", 0),
        bq_m.get("avg_spend_per_customer", 0),
        bq_m.get("avg_visits_per_customer", 0),
        bq_m.get("avg_customer_growth", 0),
    ]
    # Normalise
    max_vals = [max(t, 0.001) for t in tq_vals]
    tq_norm = [v / m for v, m in zip(tq_vals, max_vals)]
    avg_norm = [v / m for v, m in zip(avg_vals, max_vals)]
    bq_norm = [v / m for v, m in zip(bq_vals, max_vals)]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=tq_norm + [tq_norm[0]], theta=radar_labels + [radar_labels[0]],
        fill="toself", fillcolor="rgba(46,204,113,0.15)",
        line=dict(color="#2ECC71", width=2), name="Top Quartile",
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=avg_norm + [avg_norm[0]], theta=radar_labels + [radar_labels[0]],
        fill="toself", fillcolor="rgba(59,130,246,0.1)",
        line=dict(color="#3B82F6", width=2), name="Network Avg",
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=bq_norm + [bq_norm[0]], theta=radar_labels + [radar_labels[0]],
        fill="toself", fillcolor="rgba(220,38,38,0.08)",
        line=dict(color="#dc2626", width=1, dash="dot"), name="Bottom Quartile",
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 1.1], showticklabels=False,
                            gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        ),
        height=420,
        margin=dict(l=60, r=60, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FFFFFF"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")

    # Key success factors
    st.subheader("Key Success Factors")
    with st.container(border=True):
        st.markdown("""
**What the top quartile stores have in common:**
- **Smaller footprint:** 900-1,500 sqm (not the biggest stores)
- **Standalone or mixed-use:** Not reliant on shopping centre foot traffic
- **Affluent catchments:** 60%+ of shoppers in Affluence Q4+Q5
- **High wallet share:** 17%+ Share of Wallet — customers shop regularly
- **Strong customer loyalty:** 7.8 visits/customer vs 6.5 network average
- **Growing customer base:** 3.9% growth vs 2.6% average

**What underperformers share:**
- Larger format in shopping centres (high rent, low differentiation)
- Brand new stores still maturing (Dural, Marrickville, Miranda, Redfern)
- Low SoW (<10%) — customers visit occasionally, not habitually
""")

    # Top 7 store details
    st.subheader("Top 7 Stores — Detail")
    top_names = profile.get("top_quartile_stores", [])
    for name in top_names:
        row = stores_df[stores_df["Short Name"] == name]
        if row.empty:
            continue
        r = row.iloc[0]
        rev_sqm = r.get("Rev per SQM")
        rev_sqm_str = f"${rev_sqm:,.0f}" if pd.notna(rev_sqm) else "N/A"
        share = r.get("Market Share")
        share_str = f"{float(share):.1%}" if pd.notna(share) and share is not None else "N/A"
        sow = r.get("Share of Wallet")
        sow_str = f"{float(sow):.1%}" if pd.notna(sow) and sow is not None else "N/A"
        st.markdown(
            f"**{name}** — {r.get('Locality', '')} | "
            f"{r.get('Store Size (SQM)', 'N/A')} sqm | "
            f"${r.get('Annual Sales ($M)', 'N/A')}M | "
            f"Rev/sqm: {rev_sqm_str} | "
            f"Share: {share_str} | SoW: {sow_str}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: WHITESPACE OPPORTUNITIES
# ═══════════════════════════════════════════════════════════════════════════════

with tab_opps:
    st.subheader("16 Expansion Opportunities — Scored & Ranked")

    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    states_available = sorted(opps_df["state"].unique().tolist())
    state_filter = col_f1.selectbox("State", ["All"] + states_available, key="ws_state")
    phase_filter = col_f2.selectbox("Phase", ["All", 1, 2, 3], key="ws_phase")
    confidence_filter = col_f3.selectbox(
        "Confidence", ["All", "High", "Medium", "Low"], key="ws_conf"
    )

    filtered = opps_df.copy()
    if state_filter != "All":
        filtered = filtered[filtered["state"] == state_filter]
    if phase_filter != "All":
        filtered = filtered[filtered["phase"] == int(phase_filter)]
    if confidence_filter != "All":
        filtered = filtered[filtered["data_confidence"] == confidence_filter]

    # Summary table
    summary_cols = ["rank", "suburb", "state", "score", "phase",
                    "recommended_format", "addressable_revenue_m",
                    "nearest_hfm", "distance_km", "data_confidence"]
    summary = filtered[summary_cols].copy()
    summary.columns = ["Rank", "Suburb", "State", "Score", "Phase",
                        "Format", "Revenue ($M)", "Nearest HFM",
                        "Dist (km)", "Confidence"]
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Expandable detail per opportunity
    st.subheader("Opportunity Detail")
    for _, opp in filtered.iterrows():
        suburb = opp["suburb"]
        score = opp["score"]
        phase = opp["phase"]
        conf_colour = CONFIDENCE_COLOURS.get(opp["data_confidence"], "#FFFFFF")

        with st.expander(f"#{opp['rank']} {suburb}, {opp['state']} — Score: {score}/100 (Phase {phase})"):
            det_c1, det_c2 = st.columns([1, 1])
            with det_c1:
                st.markdown(f"**Recommended Format:** {opp['recommended_format']}")
                st.markdown(f"**Addressable Revenue:** ${opp['addressable_revenue_m']}M")
                st.markdown(f"**Nearest HFM Store:** {opp['nearest_hfm']}")
                dist = opp["distance_km"]
                if dist and dist > 0:
                    st.markdown(f"**Distance:** {dist:.1f} km")
                else:
                    st.markdown("**Distance:** Greenfield (no nearby store)")
                st.markdown(f"**Key Risk:** {opp['key_risk']}")
                st.markdown(f"**Data Confidence:** {opp['data_confidence']}")
            with det_c2:
                chart = score_breakdown_chart(opp.to_dict())
                if chart:
                    st.plotly_chart(chart, use_container_width=True)

    st.markdown("---")

    # Phased rollout
    st.subheader("Phased Rollout Plan")
    for phase_num, year_label, desc in [
        (1, "Year 1 (Immediate)", "Proven markets, low risk, high confidence"),
        (2, "Year 2 (Near-term)", "Adjacent markets, moderate risk"),
        (3, "Year 3 (Strategic)", "New markets, greenfield, higher risk"),
    ]:
        phase_locs = opps_df[opps_df["phase"] == phase_num]
        with st.container(border=True):
            st.markdown(f"**Phase {phase_num}: {year_label}**")
            st.caption(desc)
            for _, loc in phase_locs.iterrows():
                st.markdown(
                    f"- **{loc['suburb']}** ({loc['state']}) — "
                    f"Score {loc['score']}, {loc['recommended_format']}, "
                    f"${loc['addressable_revenue_m']}M"
                )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: MAP
# ═══════════════════════════════════════════════════════════════════════════════

with tab_map:
    st.subheader("Store Network & Whitespace Map")

    if not FOLIUM_OK:
        st.info(
            "Install `folium` and `streamlit-folium` for the interactive map. "
            "The data tables above contain all opportunity details."
        )
    else:
        # State filter
        map_state = st.selectbox(
            "Focus state", ["All", "NSW", "QLD", "VIC", "ACT", "WA"], key="ws_map_state"
        )

        show_catchments = st.checkbox("Show 5km catchment rings", value=False, key="ws_rings")

        # Centre map on Australia
        centre_lat, centre_lon, zoom = -33.8688, 151.2093, 5
        if map_state == "NSW":
            centre_lat, centre_lon, zoom = -33.8688, 151.2093, 8
        elif map_state == "QLD":
            centre_lat, centre_lon, zoom = -27.4698, 153.0251, 8
        elif map_state == "VIC":
            centre_lat, centre_lon, zoom = -37.8136, 144.9631, 10
        elif map_state == "ACT":
            centre_lat, centre_lon, zoom = -35.2809, 149.1300, 10
        elif map_state == "WA":
            centre_lat, centre_lon, zoom = -31.9505, 115.8605, 10

        m = folium.Map(
            location=[centre_lat, centre_lon],
            zoom_start=zoom,
            tiles="CartoDB dark_matter",
        )

        # Existing stores (green markers)
        coords = get_postcode_coords()
        catchments = get_catchments()

        for _, store in stores_df.iterrows():
            full_name = store["Store Name"]
            short_name = store["Short Name"]
            catch = catchments.get(full_name, {})
            postcodes_str = catch.get("postcodes", "")
            lat, lon = None, None
            if postcodes_str:
                first_pc = postcodes_str.split(",")[0].strip()
                if first_pc in coords:
                    lat = coords[first_pc]["lat"]
                    lon = coords[first_pc]["lon"]

            if lat is None or lon is None:
                continue

            state = store.get("State", "")
            if map_state != "All":
                state_abbr = {"New South Wales": "NSW", "Queensland": "QLD",
                              "Australian Capital Territory": "ACT",
                              "Victoria": "VIC", "Western Australia": "WA"}.get(state, state)
                if state_abbr != map_state:
                    continue

            sales = store.get("Annual Sales ($M)", "N/A")
            tier = store.get("Performance Tier", "N/A")
            share = store.get("Market Share")
            share_str = f"{float(share):.1%}" if pd.notna(share) and share is not None else "N/A"

            popup_html = (
                f"<div style='font-family:sans-serif;min-width:180px;'>"
                f"<h4 style='margin:0 0 4px;color:#2ECC71;'>{short_name}</h4>"
                f"<div style='font-size:0.85em;color:#666;'>{catch.get('locality', '')}</div>"
                f"<hr style='margin:4px 0;'>"
                f"<table style='font-size:0.85em;width:100%;'>"
                f"<tr><td>Sales</td><td style='text-align:right;'>${sales}M</td></tr>"
                f"<tr><td>Perf Tier</td><td style='text-align:right;'>{tier}</td></tr>"
                f"<tr><td>Share</td><td style='text-align:right;'>{share_str}</td></tr>"
                f"</table></div>"
            )

            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                color="#2ECC71",
                fill=True,
                fill_color="#2ECC71",
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=short_name,
            ).add_to(m)

            if show_catchments:
                folium.Circle(
                    location=[lat, lon],
                    radius=5000,
                    color="#2ECC71",
                    fill=False,
                    weight=1,
                    opacity=0.3,
                ).add_to(m)

        # Whitespace opportunities (blue markers)
        for _, opp in opps_df.iterrows():
            lat = opp.get("lat")
            lon = opp.get("lon")
            if lat is None or lon is None:
                continue

            opp_state = opp["state"]
            if map_state != "All" and opp_state != map_state:
                continue

            phase_col = PHASE_COLOURS.get(opp["phase"], "#3B82F6")

            popup_html = (
                f"<div style='font-family:sans-serif;min-width:200px;'>"
                f"<h4 style='margin:0 0 4px;color:{phase_col};'>"
                f"#{opp['rank']} {opp['suburb']}</h4>"
                f"<div style='font-size:0.85em;color:#666;'>Phase {opp['phase']} | "
                f"Score: {opp['score']}/100</div>"
                f"<hr style='margin:4px 0;'>"
                f"<table style='font-size:0.85em;width:100%;'>"
                f"<tr><td>Format</td><td style='text-align:right;'>"
                f"{opp['recommended_format']}</td></tr>"
                f"<tr><td>Revenue</td><td style='text-align:right;'>"
                f"${opp['addressable_revenue_m']}M</td></tr>"
                f"<tr><td>Nearest HFM</td><td style='text-align:right;'>"
                f"{opp['nearest_hfm']}</td></tr>"
                f"<tr><td>Risk</td><td style='text-align:right;'>"
                f"{opp['key_risk']}</td></tr>"
                f"</table></div>"
            )

            folium.CircleMarker(
                location=[lat, lon],
                radius=10,
                color=phase_col,
                fill=True,
                fill_color=phase_col,
                fill_opacity=0.8,
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"#{opp['rank']} {opp['suburb']} ({opp['score']})",
            ).add_to(m)

        st_folium(m, width=None, height=600, returned_objects=[])

        # Legend
        st.markdown(
            "**Legend:** "
            '<span style="color:#2ECC71;">&#9679;</span> Existing Store | '
            '<span style="color:#2ECC71;">&#9679;</span> Phase 1 | '
            '<span style="color:#3B82F6;">&#9679;</span> Phase 2 | '
            '<span style="color:#8B5CF6;">&#9679;</span> Phase 3',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6: STORE RECONCILIATION
# ═══════════════════════════════════════════════════════════════════════════════

with tab_recon:
    st.subheader("CBAS vs Hub Store Reconciliation")
    st.caption(
        "The CBAS file (31 stores) is the single source of truth for active stores. "
        "Stores in the Hub that are NOT in CBAS are likely closed or non-retail."
    )

    recon = get_reconciliation()

    # New stores in CBAS not in Hub
    st.markdown("### Stores in CBAS — Missing from Hub Master")
    new_stores = recon.get("in_cbas_not_hub", [])
    if new_stores:
        st.dataframe(
            pd.DataFrame(new_stores).rename(columns={"store": "Store", "note": "Note"}),
            use_container_width=True, hide_index=True,
        )
        st.info(f"{len(new_stores)} stores need to be added to Hub store_master.csv")
    else:
        st.success("All CBAS stores are in the Hub.")

    st.markdown("---")

    # Hub stores not in CBAS
    st.markdown("### Hub Stores — Not in CBAS (Likely Closed)")
    old_stores = recon.get("in_hub_not_cbas", [])
    if old_stores:
        st.dataframe(
            pd.DataFrame(old_stores).rename(
                columns={"store": "Store", "likely_reason": "Likely Reason"}
            ),
            use_container_width=True, hide_index=True,
        )
        st.warning(f"{len(old_stores)} Hub entries are not in CBAS — review and remove if closed")
    else:
        st.success("All Hub stores appear in CBAS.")

    st.markdown("---")

    # Name mismatches
    st.markdown("### Name Mismatches")
    mismatches = recon.get("name_mismatches", [])
    if mismatches:
        st.dataframe(
            pd.DataFrame(mismatches).rename(
                columns={"cbas": "CBAS Name", "hub": "Hub Name", "resolution": "Resolution"}
            ),
            use_container_width=True, hide_index=True,
        )
    else:
        st.success("No naming mismatches found.")


# ── Footer ────────────────────────────────────────────────────────────────────

render_footer("Whitespace Analysis", "CBAS Store Network Analysis — Feb 2026", user=user)
