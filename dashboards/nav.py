"""
Shared navigation header for all Harris Farm Hub dashboards.
Displays logo, hub-grouped navigation tabs, and consistent branding.
Import and call render_nav() at the top of each dashboard.
"""

import os

import streamlit as st

BASE_URL = os.getenv("HUB_BASE_URL", "http://localhost")

# Hub registry — aligned with Harris Farm's 5 Strategic Pillars
# "Fewer, Bigger, Better" strategy → "For The Greater Goodness"
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

# Flat lookup for convenience
_PORT_TO_HUB = {}
for hub in HUBS:
    for _label, _port, _icon, _desc in hub["dashboards"]:
        _PORT_TO_HUB[_port] = hub


def get_hub_for_port(port: int):
    """Return the hub dict that contains the given port, or None."""
    return _PORT_TO_HUB.get(port)


def _make_url(port, token=None):
    """Build a navigation URL, optionally appending an auth token."""
    url = f"{BASE_URL}:{port}"
    if token:
        url += f"?token={token}"
    return url


def render_nav(current_port: int, auth_token=None):
    """
    Render two-row hub navigation header.

    Row 1: Home + hub tabs (highlighted when active)
    Row 2: Dashboards within the active hub (highlighted when current)

    current_port: the port of the currently active dashboard.
    auth_token: optional session token to propagate across dashboards.
    """
    # Logo
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=180)

    active_hub = get_hub_for_port(current_port)

    # --- Row 1: Hub tabs ---
    hub_cols = st.columns(1 + len(HUBS))

    # Home button — Harris Farm green
    with hub_cols[0]:
        if current_port == 8500:
            st.markdown(
                "<div style='text-align:center;padding:12px 8px;background:#4ba021;"
                "color:white;border-radius:6px;font-weight:600;font-size:1.1em;'>"
                "\U0001f34e Home</div>",
                unsafe_allow_html=True,
            )
        else:
            home_url = _make_url(8500, auth_token)
            st.markdown(
                f"<a href='{home_url}' target='_top' "
                "style='display:block;text-align:center;padding:12px 8px;"
                "background:#f0f2f6;color:#4ba021;border-radius:6px;"
                "text-decoration:none;font-size:1.1em;font-weight:600;'>"
                "\U0001f34e Home</a>",
                unsafe_allow_html=True,
            )

    # Hub tabs
    for i, hub in enumerate(HUBS):
        with hub_cols[i + 1]:
            is_active = (active_hub is not None and hub["name"] == active_hub["name"])
            color = hub["color"]
            icon = hub["icon"]
            name = hub["name"]
            first_port = hub["dashboards"][0][1]

            if is_active:
                st.markdown(
                    f"<div style='text-align:center;padding:12px 8px;background:{color};"
                    f"color:white;border-radius:6px;font-weight:600;font-size:1.1em;'>"
                    f"{icon} {name}</div>",
                    unsafe_allow_html=True,
                )
            else:
                hub_url = _make_url(first_port, auth_token)
                st.markdown(
                    f"<a href='{hub_url}' target='_top' "
                    f"style='display:block;text-align:center;padding:12px 8px;"
                    f"background:#f0f2f6;color:{color};border-radius:6px;"
                    f"text-decoration:none;font-size:1.1em;'>"
                    f"{icon} {name}</a>",
                    unsafe_allow_html=True,
                )

    # --- Row 2: Dashboards within active hub ---
    if active_hub and len(active_hub["dashboards"]) > 1:
        dashboards = active_hub["dashboards"]
        dash_cols = st.columns(len(dashboards))
        color = active_hub["color"]

        for j, (label, port, icon, _desc) in enumerate(dashboards):
            with dash_cols[j]:
                if port == current_port:
                    st.markdown(
                        f"<div style='text-align:center;padding:10px 8px;"
                        f"border-bottom:3px solid {color};"
                        f"font-weight:600;font-size:1.05em;color:{color};'>"
                        f"{icon} {label}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    dash_url = _make_url(port, auth_token)
                    st.markdown(
                        f"<a href='{dash_url}' target='_top' "
                        f"style='display:block;text-align:center;padding:10px 8px;"
                        f"color:#6b7280;text-decoration:none;font-size:1.05em;'>"
                        f"{icon} {label}</a>",
                        unsafe_allow_html=True,
                    )

    st.markdown("---")
