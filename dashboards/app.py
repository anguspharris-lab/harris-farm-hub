"""
Harris Farm Hub — Single Multi-Page Streamlit App
Entry point for all 17 dashboards, consolidated via st.navigation().
One process, native sidebar nav, shared session state.
"""

import os
import sys
from pathlib import Path

import streamlit as st

# Add backend/ to sys.path once — all dashboards and shared modules can now
# import backend modules (fiscal_calendar, transaction_layer, etc.) directly.
_BACKEND = str(Path(__file__).resolve().parent.parent / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Page config — single call for the whole app
st.set_page_config(
    page_title="Harris Farm Hub — Centre of Excellence",
    page_icon="\U0001f34e",
    layout="wide",
)

# Auth gate — runs before any page renders (login page has its own dark styling)
from shared.auth_gate import require_login

user = require_login()
st.session_state["auth_user"] = user

# Shared styling — applied AFTER login so it doesn't conflict with login page CSS
from shared.styles import apply_styles

apply_styles()

# ---------------------------------------------------------------------------
# Page definitions — grouped by strategic pillar
# ---------------------------------------------------------------------------

_DIR = Path(__file__).resolve().parent

# Create all page objects
_home = st.Page(str(_DIR / "landing.py"), title="Home", icon="\U0001f34e", default=True)

_pages = {
    "greater-goodness": st.Page(str(_DIR / "greater_goodness.py"), title="Greater Goodness", icon="\U0001f331", url_path="greater-goodness"),
    "customers": st.Page(str(_DIR / "customer_dashboard.py"), title="Customers", icon="\U0001f465", url_path="customers"),
    "market-share": st.Page(str(_DIR / "market_share_dashboard.py"), title="Market Share", icon="\U0001f5fa\ufe0f", url_path="market-share"),
    "learning-centre": st.Page(str(_DIR / "learning_centre.py"), title="Learning Centre", icon="\U0001f393", url_path="learning-centre"),
    "hub-assistant": st.Page(str(_DIR / "chatbot_dashboard.py"), title="Hub Assistant", icon="\U0001f4ac", url_path="hub-assistant"),
    "sales": st.Page(str(_DIR / "sales_dashboard.py"), title="Sales", icon="\U0001f4ca", url_path="sales"),
    "profitability": st.Page(str(_DIR / "profitability_dashboard.py"), title="Profitability", icon="\U0001f4b0", url_path="profitability"),
    "transport": st.Page(str(_DIR / "transport_dashboard.py"), title="Transport", icon="\U0001f69a", url_path="transport"),
    "store-ops": st.Page(str(_DIR / "store_ops_dashboard.py"), title="Store Ops", icon="\U0001f3ea", url_path="store-ops"),
    "buying-hub": st.Page(str(_DIR / "buying_hub_dashboard.py"), title="Buying Hub", icon="\U0001f6d2", url_path="buying-hub"),
    "product-intel": st.Page(str(_DIR / "product_intel_dashboard.py"), title="Product Intel", icon="\U0001f50d", url_path="product-intel"),
    "plu-intel": st.Page(str(_DIR / "plu_intel_dashboard.py"), title="PLU Intelligence", icon="\U0001f4ca", url_path="plu-intel"),
    "prompt-builder": st.Page(str(_DIR / "prompt_builder.py"), title="Prompt Builder", icon="\U0001f527", url_path="prompt-builder"),
    "the-rubric": st.Page(str(_DIR / "rubric_dashboard.py"), title="The Rubric", icon="\u2696\ufe0f", url_path="the-rubric"),
    "trending": st.Page(str(_DIR / "trending_dashboard.py"), title="Trending", icon="\U0001f4c8", url_path="trending"),
    "revenue-bridge": st.Page(str(_DIR / "revenue_bridge_dashboard.py"), title="Revenue Bridge", icon="\U0001f4c9", url_path="revenue-bridge"),
    "hub-portal": st.Page(str(_DIR / "hub_portal.py"), title="Hub Portal", icon="\U0001f310", url_path="hub-portal"),
    "ai-adoption": st.Page(str(_DIR / "ai_adoption" / "dashboard.py"), title="AI Adoption", icon="\U0001f4ca", url_path="ai-adoption"),
}

# Pillar groupings for navigation
_PILLARS = [
    {"name": "Greater Goodness", "icon": "\U0001f331", "color": "#16a34a",
     "slugs": ["greater-goodness"]},
    {"name": "Customer", "icon": "\U0001f465", "color": "#7c3aed",
     "slugs": ["customers", "market-share"]},
    {"name": "People", "icon": "\U0001f393", "color": "#059669",
     "slugs": ["learning-centre", "hub-assistant", "ai-adoption"]},
    {"name": "Operations", "icon": "\U0001f4ca", "color": "#d97706",
     "slugs": ["sales", "profitability", "transport", "store-ops", "buying-hub", "product-intel", "plu-intel"]},
    {"name": "Digital & AI", "icon": "\U0001f680", "color": "#4ba021",
     "slugs": ["prompt-builder", "the-rubric", "trending", "revenue-bridge", "hub-portal"]},
]

# Store page objects in session_state so landing.py can use st.page_link()
st.session_state["_pages"] = _pages
st.session_state["_home"] = _home

nav = st.navigation(
    {
        "": [_home],
        "For The Greater Goodness": [_pages["greater-goodness"]],
        "Smashing It for the Customer": [_pages["customers"], _pages["market-share"]],
        "Growing Legendary Leadership": [_pages["learning-centre"], _pages["hub-assistant"], _pages["ai-adoption"]],
        "Today's Business, Done Better": [_pages["sales"], _pages["profitability"], _pages["transport"], _pages["store-ops"], _pages["buying-hub"], _pages["product-intel"], _pages["plu-intel"]],
        "Tomorrow's Business, Built Better": [_pages["prompt-builder"], _pages["the-rubric"], _pages["trending"], _pages["revenue-bridge"], _pages["hub-portal"]],
    }
)

# ---------------------------------------------------------------------------
# Navigation header — uses st.page_link (preserves session, no page reload)
# ---------------------------------------------------------------------------

current_slug = nav.url_path

# Build slug-to-pillar lookup
_slug_to_pillar = {}
for p in _PILLARS:
    for s in p["slugs"]:
        _slug_to_pillar[s] = p

active_pillar = _slug_to_pillar.get(current_slug)

# Logo
_logo = _DIR.parent / "assets" / "logo.png"
if _logo.exists():
    st.image(str(_logo), width=180)

# Row 1: Home + 5 pillar tabs using st.page_link (session-safe)
cols = st.columns(1 + len(_PILLARS))

with cols[0]:
    st.page_link(_home, label="\U0001f34e Home", use_container_width=True)

for i, pillar in enumerate(_PILLARS):
    with cols[i + 1]:
        first_slug = pillar["slugs"][0]
        label = f"{pillar['icon']} {pillar['name']}"
        st.page_link(_pages[first_slug], label=label, use_container_width=True)

# Row 2: Sub-pages within active pillar
if active_pillar and len(active_pillar["slugs"]) > 1:
    sub_cols = st.columns(len(active_pillar["slugs"]))
    for j, slug in enumerate(active_pillar["slugs"]):
        with sub_cols[j]:
            page = _pages[slug]
            is_current = slug == current_slug
            if is_current:
                st.markdown(
                    f"<div style='text-align:center;padding:8px 6px;"
                    f"border-bottom:3px solid {active_pillar['color']};"
                    f"font-weight:600;color:{active_pillar['color']};'>"
                    f"{page.title}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.page_link(page, label=page.title, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Run the selected page
# ---------------------------------------------------------------------------

nav.run()
