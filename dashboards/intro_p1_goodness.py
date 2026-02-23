"""
Harris Farm Hub — Pillar 1: For The Greater Goodness (Intro Page)
Strategic front door for sustainability, community impact, and purpose.
"""

import streamlit as st

from shared.styles import render_footer, HFM_GREEN, HFM_DARK
from shared.pillar_data import get_pillar
from shared.monday_connector import is_configured, fetch_board_summary, BOARD_IDS
from shared.strategic_framing import (
    pillar_hero, coming_soon_card, one_thing_box,
    initiative_summary_card, sub_page_links,
)

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})
pillar = get_pillar("P1")

# ── Hero Banner ──
pillar_hero(
    pillar,
    metrics=[
        {"label": "Renewable Energy", "value": "100%", "delta": "Achieved"},
    ],
)

# ── Hero Metrics ──
st.subheader("Key Indicators")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        "<div style='background:rgba(255,255,255,0.05);border-radius:10px;padding:20px;"
        "text-align:center;border:1px solid rgba(255,255,255,0.08);"
        "border-top:3px solid {};min-height:120px;'>"
        "<div style='font-size:2em;font-weight:700;color:{};'>100%</div>"
        "<div style='font-size:0.85em;color:#6b7280;'>Renewable Energy</div>"
        "<div style='font-size:0.75em;color:#2ECC71;margin-top:4px;'>"
        "\u2713 Achieved</div>"
        "</div>".format(HFM_GREEN, HFM_GREEN),
        unsafe_allow_html=True,
    )

with c2:
    coming_soon_card(
        "B-Corp Certification",
        "Board approval targeted Feb/Mar 2026",
    )

with c3:
    coming_soon_card(
        "Waste Diversion %",
        "Data source not yet connected",
    )

with c4:
    coming_soon_card(
        "Community Investment",
        "Data source not yet connected",
    )

# ── Monday.com Initiatives ──
st.markdown("---")

if is_configured():
    summary = fetch_board_summary(BOARD_IDS["P1"])
    initiative_summary_card(summary)
else:
    st.markdown(
        "<div style='background:rgba(255,255,255,0.03);border-radius:8px;padding:12px 16px;"
        "color:#6b7280;font-size:0.9em;'>"
        "\U0001f4cb <strong>Initiative Tracking:</strong> Connect Monday.com "
        "to see P1 strategic initiatives here. "
        "Add <code>MONDAY_API_KEY</code> to your <code>.env</code> file."
        "</div>",
        unsafe_allow_html=True,
    )

# ── Strategic Context ──
st.markdown("---")
st.markdown(
    "<div style='background:rgba(255,255,255,0.05);border-radius:10px;padding:20px;"
    "border:1px solid rgba(255,255,255,0.08);'>"
    "<h3 style='color:{};margin-top:0;'>What Does Greater Goodness Mean?</h3>"
    "<p style='color:#B0BEC5;'>Harris Farm's purpose goes beyond selling fresh food. "
    "We're building a business that does right \u2014 from end-to-end. "
    "That means 100% renewable energy (achieved), B-Corp certification (in progress), "
    "and a supply chain that treats farmers, communities, and the planet fairly.</p>"
    "<p style='color:#6b7280;font-size:0.9em;font-style:italic;'>"
    "\"We'll do things right, from end-to-end.\"</p>"
    "</div>".format(HFM_DARK),
    unsafe_allow_html=True,
)

# ── Sub-page Navigation ──
st.markdown("---")
st.subheader("Explore Greater Goodness")
sub_page_links(["greater-goodness"])

# ── One Thing ──
one_thing_box(
    "Sustainability is a P&L line, not just a poster. "
    "When we can show the numbers \u2014 energy costs down, "
    "waste diverted, community ROI \u2014 the strategy becomes real."
)

render_footer("Greater Goodness", "Pillar 1 \u2014 For The Greater Goodness", user)
