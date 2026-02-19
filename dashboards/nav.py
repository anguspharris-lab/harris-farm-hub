"""
Shared navigation data for Harris Farm Hub dashboards.
HUBS list used by landing.py for pillar card data.
PAGE_REGISTRY used by landing.py for port-to-URL conversion.
render_nav() is a no-op (navigation handled by st.navigation in app.py).
"""

import os

import streamlit as st

BASE_URL = os.getenv("HUB_BASE_URL", "http://localhost")

# Hub registry — aligned with Harris Farm's 5 Strategic Pillars
# "Fewer, Bigger, Better" strategy -> "For The Greater Goodness"
# Dashboard tuple: (label, port, icon, description)
HUBS = [
    {
        "name": "Greater Goodness",
        "pillar": "Pillar 1",
        "pillar_title": "For The Greater Goodness",
        "icon": "\U0001f331",
        "color": "#16a34a",
        "dashboards": [
            ("Greater Goodness", 8516, "\U0001f331", "Our purpose, sustainability & community impact"),
        ],
    },
    {
        "name": "Customer",
        "pillar": "Pillar 2",
        "pillar_title": "Smashing It for the Customer",
        "icon": "\U0001f465",
        "color": "#7c3aed",
        "dashboards": [
            ("Customers", 8507, "\U0001f465", "Customer insights, trends & loyalty readiness"),
            ("Market Share", 8508, "\U0001f5fa\ufe0f", "Postcode share, penetration, competitor benchmarks"),
        ],
    },
    {
        "name": "People",
        "pillar": "Pillar 3",
        "pillar_title": "Growing Legendary Leadership",
        "icon": "\U0001f393",
        "color": "#059669",
        "dashboards": [
            ("Learning Centre", 8510, "\U0001f393", "AI & data skills — Prompt Academy"),
            ("Hub Assistant", 8509, "\U0001f4ac", "Ask questions, get guidance"),
        ],
    },
    {
        "name": "Operations",
        "pillar": "Pillar 4",
        "pillar_title": "Today's Business, Done Better",
        "icon": "\U0001f4ca",
        "color": "#d97706",
        "dashboards": [
            ("Sales", 8501, "\U0001f4ca", "Revenue, store performance, trends"),
            ("Profitability", 8502, "\U0001f4b0", "GP analysis, margins, P&L"),
            ("Transport", 8503, "\U0001f69a", "Route costs, fleet optimisation"),
            ("Store Ops", 8511, "\U0001f3ea", "Store-level transaction intelligence"),
            ("Buying Hub", 8514, "\U0001f6d2", "Category buying, demand & weather"),
            ("Product Intel", 8512, "\U0001f50d", "Item & category performance"),
        ],
    },
    {
        "name": "Digital & AI",
        "pillar": "Pillar 5",
        "pillar_title": "Tomorrow's Business, Built Better",
        "icon": "\U0001f680",
        "color": "#4ba021",
        "dashboards": [
            ("Prompt Builder", 8504, "\U0001f527", "Design analytical prompts"),
            ("The Rubric", 8505, "\u2696\ufe0f", "Compare AI models side-by-side"),
            ("Trending", 8506, "\U0001f4c8", "System analytics & usage"),
            ("Revenue Bridge", 8513, "\U0001f4c9", "Revenue decomposition & trends"),
            ("Hub Portal", 8515, "\U0001f310", "Documentation, agents, governance"),
        ],
    },
]

# ---------------------------------------------------------------------------
# PAGE_REGISTRY — maps port to page metadata for internal URL conversion
# ---------------------------------------------------------------------------

# Flat lookup for convenience
_PORT_TO_HUB = {}
for hub in HUBS:
    for _label, _port, _icon, _desc in hub["dashboards"]:
        _PORT_TO_HUB[_port] = hub

# ---------------------------------------------------------------------------
# URL helpers — explicit slug map matching app.py url_path values
# ---------------------------------------------------------------------------

_PORT_TO_SLUG = {
    8500: "",                # Home (default page = root)
    8516: "greater-goodness",
    8507: "customers",
    8508: "market-share",
    8510: "learning-centre",
    8509: "hub-assistant",
    8501: "sales",
    8502: "profitability",
    8503: "transport",
    8511: "store-ops",
    8514: "buying-hub",
    8512: "product-intel",
    8504: "prompt-builder",
    8505: "the-rubric",
    8506: "trending",
    8513: "revenue-bridge",
    8515: "hub-portal",
}


def port_to_url(port: int) -> str:
    """Convert a legacy port number to an internal st.navigation page URL path."""
    slug = _PORT_TO_SLUG.get(port)
    if slug is not None:
        return f"/{slug}" if slug else "/"
    return "/"


def get_hub_for_port(port: int):
    """Return the hub dict that contains the given port, or None."""
    return _PORT_TO_HUB.get(port)


def render_nav(current_port: int = None, auth_token=None):
    """No-op — navigation is now handled by st.navigation() in app.py."""
    pass
