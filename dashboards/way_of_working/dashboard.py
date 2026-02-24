"""
Harris Farm Hub — Way of Working
Tracks 100 strategic initiatives across 5 pillars via Monday.com integration.
Entry point for the Way of Working navigation section.
"""

import streamlit as st

from shared.styles import render_header, render_footer, HFM_GREEN, HFM_DARK
from shared.monday_connector import is_configured, fetch_all_pillar_summaries
from shared.pillar_data import get_all_pillars, BOARD_IDS
from shared.strategic_framing import coming_soon_card, one_thing_box

user = st.session_state.get("auth_user")

render_header(
    "Way of Working",
    "**Harris Farm Markets** | Strategic Initiative Tracker",
    goals=["G1", "G5"],
    strategy_context=(
        "100 strategic initiatives across 5 pillars \u2014 "
        "tracked live from Monday.com."
    ),
)
st.caption("The AI-First Method is how we work now. Six steps. End to end.")

if not is_configured():
    st.markdown(
        "<div style='text-align:center;padding:60px 20px;'>"
        "<div style='font-size:3em;margin-bottom:16px;'>\U0001f4cb</div>"
        "<h2 style='color:{};'>Way of Working</h2>"
        "<p style='color:#8899AA;max-width:500px;margin:0 auto 24px;'>"
        "This section connects to Monday.com to track Harris Farm's "
        "100 strategic initiatives across all 5 pillars.</p>"
        "<div style='background:rgba(255,255,255,0.03);border-radius:10px;padding:20px;"
        "max-width:400px;margin:0 auto;text-align:left;'>"
        "<div style='font-weight:600;margin-bottom:8px;'>"
        "\u2699\ufe0f Setup Required</div>"
        "<ol style='color:#8899AA;font-size:0.9em;margin:0;padding-left:20px;'>"
        "<li>Get your Monday.com API key from "
        "<code>monday.com > Avatar > Admin > API</code></li>"
        "<li>Add <code>MONDAY_API_KEY=your_key</code> to your "
        "<code>.env</code> file</li>"
        "<li>Restart the Hub</li>"
        "</ol></div></div>".format(HFM_DARK),
        unsafe_allow_html=True,
    )
    one_thing_box(
        "The Way of Working isn't a dashboard \u2014 it's how we hold "
        "ourselves accountable. Every initiative maps to a pillar, "
        "every pillar maps to the strategy."
    )
    render_footer("Way of Working", "", user)
    st.stop()

# ── Monday.com is configured — show live data ──

tab_overview, tab_initiatives, tab_pillar = st.tabs([
    "\U0001f4ca Overview", "\U0001f4cb All Initiatives", "\U0001f50d Pillar View"
])

with tab_overview:
    from way_of_working.overview import render as render_overview
    render_overview()

with tab_initiatives:
    from way_of_working.initiative_list import render as render_list
    render_list()

with tab_pillar:
    from way_of_working.pillar_view import render as render_pillar
    render_pillar()

one_thing_box(
    "Strategy without tracking is just a wish list. "
    "Every initiative here maps to a pillar, has an owner, "
    "and a status that's updated weekly."
)

render_footer("Way of Working", "Strategic Initiative Tracker", user)
