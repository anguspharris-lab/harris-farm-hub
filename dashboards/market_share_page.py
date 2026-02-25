"""
Harris Farm Hub — Market Share Dashboard
CBAS postcode-level competitive analysis — share by distance tier, store health,
catchment performance, growth frontiers, and interactive map.

This is the standalone Market Share page under the Property section.
It wraps the existing market share tab renderers from customer_hub/ms_*.py.
"""

import streamlit as st

from shared.styles import render_header, render_footer
from shared.ask_question import render_ask_question
from shared.voice_realtime import render_voice_data_box

user = st.session_state.get("auth_user")

render_header(
    "Market Share",
    "Postcode-level competitive analysis | Distance tiers | Store health | Trends",
    goals=["G1", "G2"],
    strategy_context=(
        "Where we're winning and losing market position — CBAS modelled share "
        "by postcode, essential for 'Fewer, Bigger' expansion decisions."
    ),
)
st.caption(
    "CBAS data is directional. Share % is the primary metric — "
    "dollar values are estimates, not actual revenue."
)

# ── Tabs — reuse existing market share renderers ──────────────────────────────

tab_names = ["Overview", "Store Performance", "Catchment Tiers",
             "Growth Frontiers", "Map"]
tabs = st.tabs(tab_names)

from customer_hub.ms_overview import render as render_ms_overview
from customer_hub.ms_store_perf import render as render_ms_store
from customer_hub.ms_catchment import render as render_ms_catch
from customer_hub.ms_growth import render as render_ms_growth
from customer_hub.ms_map import render as render_ms_map

with tabs[0]:
    render_ms_overview()
with tabs[1]:
    render_ms_store()
with tabs[2]:
    render_ms_catch()
with tabs[3]:
    render_ms_growth()
with tabs[4]:
    render_ms_map()

# ── Cross-dashboard links ────────────────────────────────────────────────────

st.markdown("---")
st.markdown("**Related**")
_pages = st.session_state.get("_pages", {})
c1, c2, c3 = st.columns(3)
if "whitespace" in _pages:
    c1.page_link(_pages["whitespace"], label="Whitespace Analysis", icon="\U0001f5fa\ufe0f")
if "store-network" in _pages:
    c2.page_link(_pages["store-network"], label="Store Network", icon="\U0001f3ec")
if "customers" in _pages:
    c3.page_link(_pages["customers"], label="Customer Hub", icon="\U0001f465")

# ── Footer ───────────────────────────────────────────────────────────────────

render_voice_data_box("market_share")
render_ask_question("market_share")
render_footer("Market Share", "CBAS Layer 2 — modelled estimates", user=user)
