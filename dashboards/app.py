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

# Shared styling — applied once, inherited by all pages
from shared.styles import apply_styles

apply_styles()

# Auth gate — runs before any page renders
from shared.auth_gate import require_login

user = require_login()
st.session_state["auth_user"] = user

# ---------------------------------------------------------------------------
# Page definitions — grouped by strategic pillar
# ---------------------------------------------------------------------------

_DIR = Path(__file__).resolve().parent

# Pillar metadata for the navigation header
_PILLARS = [
    {"name": "Greater Goodness", "icon": "\U0001f331", "color": "#16a34a",
     "pages": [("Greater Goodness", "greater-goodness")]},
    {"name": "Customer", "icon": "\U0001f465", "color": "#7c3aed",
     "pages": [("Customers", "customers"), ("Market Share", "market-share")]},
    {"name": "People", "icon": "\U0001f393", "color": "#059669",
     "pages": [("Learning Centre", "learning-centre"), ("Hub Assistant", "hub-assistant")]},
    {"name": "Operations", "icon": "\U0001f4ca", "color": "#d97706",
     "pages": [("Sales", "sales"), ("Profitability", "profitability"),
      ("Transport", "transport"), ("Store Ops", "store-ops"),
      ("Buying Hub", "buying-hub"), ("Product Intel", "product-intel")]},
    {"name": "Digital & AI", "icon": "\U0001f680", "color": "#4ba021",
     "pages": [("Prompt Builder", "prompt-builder"), ("The Rubric", "the-rubric"),
      ("Trending", "trending"), ("Revenue Bridge", "revenue-bridge"),
      ("Hub Portal", "hub-portal")]},
]

# Build a slug -> pillar lookup
_SLUG_TO_PILLAR = {}
for p in _PILLARS:
    for _label, _slug in p["pages"]:
        _SLUG_TO_PILLAR[_slug] = p

nav = st.navigation(
    {
        "": [
            st.Page(str(_DIR / "landing.py"), title="Home", icon="\U0001f34e", default=True),
        ],
        "For The Greater Goodness": [
            st.Page(str(_DIR / "greater_goodness.py"), title="Greater Goodness", icon="\U0001f331", url_path="greater-goodness"),
        ],
        "Smashing It for the Customer": [
            st.Page(str(_DIR / "customer_dashboard.py"), title="Customers", icon="\U0001f465", url_path="customers"),
            st.Page(str(_DIR / "market_share_dashboard.py"), title="Market Share", icon="\U0001f5fa\ufe0f", url_path="market-share"),
        ],
        "Growing Legendary Leadership": [
            st.Page(str(_DIR / "learning_centre.py"), title="Learning Centre", icon="\U0001f393", url_path="learning-centre"),
            st.Page(str(_DIR / "chatbot_dashboard.py"), title="Hub Assistant", icon="\U0001f4ac", url_path="hub-assistant"),
        ],
        "Today's Business, Done Better": [
            st.Page(str(_DIR / "sales_dashboard.py"), title="Sales", icon="\U0001f4ca", url_path="sales"),
            st.Page(str(_DIR / "profitability_dashboard.py"), title="Profitability", icon="\U0001f4b0", url_path="profitability"),
            st.Page(str(_DIR / "transport_dashboard.py"), title="Transport", icon="\U0001f69a", url_path="transport"),
            st.Page(str(_DIR / "store_ops_dashboard.py"), title="Store Ops", icon="\U0001f3ea", url_path="store-ops"),
            st.Page(str(_DIR / "buying_hub_dashboard.py"), title="Buying Hub", icon="\U0001f6d2", url_path="buying-hub"),
            st.Page(str(_DIR / "product_intel_dashboard.py"), title="Product Intel", icon="\U0001f50d", url_path="product-intel"),
        ],
        "Tomorrow's Business, Built Better": [
            st.Page(str(_DIR / "prompt_builder.py"), title="Prompt Builder", icon="\U0001f527", url_path="prompt-builder"),
            st.Page(str(_DIR / "rubric_dashboard.py"), title="The Rubric", icon="\u2696\ufe0f", url_path="the-rubric"),
            st.Page(str(_DIR / "trending_dashboard.py"), title="Trending", icon="\U0001f4c8", url_path="trending"),
            st.Page(str(_DIR / "revenue_bridge_dashboard.py"), title="Revenue Bridge", icon="\U0001f4c9", url_path="revenue-bridge"),
            st.Page(str(_DIR / "hub_portal.py"), title="Hub Portal", icon="\U0001f310", url_path="hub-portal"),
        ],
    }
)

# ---------------------------------------------------------------------------
# Persistent navigation header — shows on every page
# ---------------------------------------------------------------------------

current_slug = nav.url_path  # "" for Home, "sales" for Sales, etc.
active_pillar = _SLUG_TO_PILLAR.get(current_slug)

# Logo
_logo = _DIR.parent / "assets" / "logo.png"
if _logo.exists():
    st.image(str(_logo), width=180)

# Row 1: Home + 5 pillar tabs
_home_active = current_slug == ""
cols = st.columns(1 + len(_PILLARS))

with cols[0]:
    if _home_active:
        st.markdown(
            "<div style='text-align:center;padding:10px 6px;background:#4ba021;"
            "color:white;border-radius:6px;font-weight:600;font-size:1.05em;'>"
            "\U0001f34e Home</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<a href='/' style='display:block;text-align:center;padding:10px 6px;"
            "background:#f0f2f6;color:#4ba021;border-radius:6px;"
            "text-decoration:none;font-size:1.05em;font-weight:600;'>"
            "\U0001f34e Home</a>",
            unsafe_allow_html=True,
        )

for i, pillar in enumerate(_PILLARS):
    with cols[i + 1]:
        is_active = active_pillar is not None and pillar["name"] == active_pillar["name"]
        color = pillar["color"]
        icon = pillar["icon"]
        name = pillar["name"]
        first_slug = pillar["pages"][0][1]

        if is_active:
            st.markdown(
                f"<div style='text-align:center;padding:10px 6px;background:{color};"
                f"color:white;border-radius:6px;font-weight:600;font-size:1.05em;'>"
                f"{icon} {name}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<a href='/{first_slug}' style='display:block;text-align:center;"
                f"padding:10px 6px;background:#f0f2f6;color:{color};border-radius:6px;"
                f"text-decoration:none;font-size:1.05em;font-weight:600;'>"
                f"{icon} {name}</a>",
                unsafe_allow_html=True,
            )

# Row 2: Pages within the active pillar (only if pillar has multiple pages)
if active_pillar and len(active_pillar["pages"]) > 1:
    page_list = active_pillar["pages"]
    color = active_pillar["color"]
    dash_cols = st.columns(len(page_list))

    for j, (label, slug) in enumerate(page_list):
        with dash_cols[j]:
            if slug == current_slug:
                st.markdown(
                    f"<div style='text-align:center;padding:8px 6px;"
                    f"border-bottom:3px solid {color};"
                    f"font-weight:600;font-size:1em;color:{color};'>"
                    f"{label}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<a href='/{slug}' style='display:block;text-align:center;"
                    f"padding:8px 6px;color:#6b7280;text-decoration:none;"
                    f"font-size:1em;'>{label}</a>",
                    unsafe_allow_html=True,
                )

st.markdown("---")

# ---------------------------------------------------------------------------
# Run the selected page
# ---------------------------------------------------------------------------

nav.run()
