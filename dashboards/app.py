"""
Harris Farm Hub — Single Multi-Page Streamlit App
Entry point for all 22 dashboards, consolidated via st.navigation().
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
    # Strategy overview (all 5 pillars, initiatives, goals)
    "strategy-overview": st.Page(str(_DIR / "strategy_overview.py"), title="Strategy Overview", icon="\U0001f3af", url_path="strategy-overview"),
    # Pillar intro pages (strategic front doors)
    "intro-people": st.Page(str(_DIR / "intro_p3_people.py"), title="Growing Legends", icon="\U0001f393", url_path="intro-people"),
    "intro-operations": st.Page(str(_DIR / "intro_p4_operations.py"), title="Operations HQ", icon="\U0001f4ca", url_path="intro-operations"),
    "intro-digital": st.Page(str(_DIR / "intro_p5_digital.py"), title="Digital & AI HQ", icon="\U0001f680", url_path="intro-digital"),
    # Way of Working
    "way-of-working": st.Page(str(_DIR / "way_of_working" / "dashboard.py"), title="Way of Working", icon="\U0001f4cb", url_path="way-of-working"),
    # Marketing Assets
    "marketing-assets": st.Page(str(_DIR / "marketing_assets.py"), title="Marketing Assets", icon="\U0001f4c1", url_path="marketing-assets"),
    # P1 Greater Goodness
    "greater-goodness": st.Page(str(_DIR / "greater_goodness.py"), title="Greater Goodness", icon="\U0001f331", url_path="greater-goodness"),
    # P2 Customer
    "customers": st.Page(str(_DIR / "customer_hub" / "dashboard.py"), title="Customer Hub", icon="\U0001f465", url_path="customers"),
    # P3 People
    "skills-academy": st.Page(str(_DIR / "skills_academy.py"), title="Growing Legends Academy", icon="\U0001f4da", url_path="skills-academy"),
    "hub-assistant": st.Page(str(_DIR / "chatbot_dashboard.py"), title="Hub Assistant", icon="\U0001f4ac", url_path="hub-assistant"),
    "the-paddock": st.Page(str(_DIR / "the_paddock.py"), title="The Paddock", icon="\U0001f331", url_path="the-paddock"),
    "prompt-builder": st.Page(str(_DIR / "prompt_builder.py"), title="Prompt Engine", icon="\U0001f680", url_path="prompt-builder"),
    "approvals": st.Page(str(_DIR / "approvals_dashboard.py"), title="Approvals", icon="\u2705", url_path="approvals"),
    "the-rubric": st.Page(str(_DIR / "rubric_dashboard.py"), title="The Rubric", icon="\u2696\ufe0f", url_path="the-rubric"),
    # P4 Operations
    "sales": st.Page(str(_DIR / "sales_dashboard.py"), title="Sales", icon="\U0001f4ca", url_path="sales"),
    "profitability": st.Page(str(_DIR / "profitability_dashboard.py"), title="Profitability", icon="\U0001f4b0", url_path="profitability"),
    "revenue-bridge": st.Page(str(_DIR / "revenue_bridge_dashboard.py"), title="Revenue Bridge", icon="\U0001f4c9", url_path="revenue-bridge"),
    "store-ops": st.Page(str(_DIR / "store_ops_dashboard.py"), title="Store Ops", icon="\U0001f3ea", url_path="store-ops"),
    "buying-hub": st.Page(str(_DIR / "buying_hub_dashboard.py"), title="Buying Hub", icon="\U0001f6d2", url_path="buying-hub"),
    "product-intel": st.Page(str(_DIR / "product_intel_dashboard.py"), title="Product Intel", icon="\U0001f50d", url_path="product-intel"),
    "plu-intel": st.Page(str(_DIR / "plu_intel_dashboard.py"), title="PLU Intelligence", icon="\U0001f4ca", url_path="plu-intel"),
    "transport": st.Page(str(_DIR / "transport_dashboard.py"), title="Transport", icon="\U0001f69a", url_path="transport"),
    # Property
    "store-network": st.Page(str(_DIR / "store_network_page.py"), title="Store Network", icon="\U0001f3ec", url_path="store-network"),
    "market-share": st.Page(str(_DIR / "market_share_page.py"), title="Market Share", icon="\U0001f4ca", url_path="market-share"),
    "demographics": st.Page(str(_DIR / "demographics_page.py"), title="Demographics", icon="\U0001f4e8", url_path="demographics"),
    "whitespace": st.Page(str(_DIR / "whitespace_analysis.py"), title="Whitespace Analysis", icon="\U0001f5fa\ufe0f", url_path="whitespace"),
    "competitor-map": st.Page(str(_DIR / "competitor_map_page.py"), title="Competitor Map", icon="\U0001f4cd", url_path="competitor-map"),
    "roce": st.Page(str(_DIR / "roce_dashboard.py"), title="ROCE Analysis", icon="\U0001f4b9", url_path="roce"),
    "cannibalisation": st.Page(str(_DIR / "cannibalisation_dashboard.py"), title="Cannibalisation", icon="\U0001f50d", url_path="cannibalisation"),
    # MDHE — Master Data Health Engine
    "mdhe-dashboard": st.Page(str(_DIR / "mdhe" / "dashboard.py"), title="MDHE Dashboard", icon="\U0001f3e5", url_path="mdhe-dashboard"),
    "mdhe-upload": st.Page(str(_DIR / "mdhe" / "upload.py"), title="MDHE Upload", icon="\U0001f4e4", url_path="mdhe-upload"),
    "mdhe-issues": st.Page(str(_DIR / "mdhe" / "issues.py"), title="MDHE Issues", icon="\U0001f4cb", url_path="mdhe-issues"),
    "mdhe-guide": st.Page(str(_DIR / "mdhe" / "guide.py"), title="MDHE Guide", icon="\U0001f4d6", url_path="mdhe-guide"),
    # P5 Digital & AI
    "workflow-engine": st.Page(str(_DIR / "workflow_engine.py"), title="Workflow Engine", icon="\u2699\ufe0f", url_path="workflow-engine"),
    "analytics-engine": st.Page(str(_DIR / "analytics_engine.py"), title="Analytics Engine", icon="\U0001f52c", url_path="analytics-engine"),
    "agent-hub": st.Page(str(_DIR / "agent_hub.py"), title="Agent Hub", icon="\U0001f916", url_path="agent-hub"),
    "agent-ops": st.Page(str(_DIR / "agent_operations.py"), title="Agent Operations", icon="\U0001f6e1\ufe0f", url_path="agent-ops"),
    "ai-adoption": st.Page(str(_DIR / "ai_adoption" / "dashboard.py"), title="AI Adoption", icon="\U0001f4ca", url_path="ai-adoption"),
    "trending": st.Page(str(_DIR / "trending_dashboard.py"), title="Trending", icon="\U0001f4c8", url_path="trending"),
    "mission-control": st.Page(str(_DIR / "hub_portal.py"), title="Mission Control", icon="\U0001f3af", url_path="mission-control"),
    "adoption": st.Page(str(_DIR / "adoption_dashboard.py"), title="Adoption", icon="\U0001f4c8", url_path="adoption"),
    # Admin
    "user-management": st.Page(str(_DIR / "mdhe" / "user_management.py"), title="User Management", icon="\U0001f465", url_path="user-management"),
}

# Section groupings for navigation (purpose-based, not pillar-based)
_SECTIONS = [
    {"name": "Strategy", "icon": "\U0001f3af", "color": "#2ECC71",
     "slugs": ["strategy-overview", "greater-goodness", "intro-people",
               "intro-operations", "intro-digital", "way-of-working"]},
    {"name": "Growing Legends", "icon": "\U0001f331", "color": "#8B5CF6",
     "slugs": ["skills-academy", "the-paddock", "prompt-builder", "hub-assistant"]},
    {"name": "Operations", "icon": "\U0001f4ca", "color": "#F1C40F",
     "slugs": ["customers", "sales", "profitability", "revenue-bridge",
               "store-ops", "buying-hub", "product-intel", "plu-intel",
               "transport", "analytics-engine"]},
    {"name": "Property", "icon": "\U0001f3d8\ufe0f", "color": "#06B6D4",
     "slugs": ["store-network", "market-share", "demographics",
               "whitespace", "competitor-map", "roce", "cannibalisation"]},
    {"name": "MDHE", "icon": "\U0001f3e5", "color": "#E74C3C",
     "slugs": ["mdhe-dashboard", "mdhe-upload", "mdhe-issues", "mdhe-guide"]},
    {"name": "Back of House", "icon": "\u2699\ufe0f", "color": "#8899AA",
     "is_muted": True,
     "slugs": ["the-rubric", "approvals", "workflow-engine", "agent-ops",
               "mission-control", "ai-adoption", "adoption", "trending",
               "agent-hub", "marketing-assets", "user-management"]},
]

# Store page objects and sections in session_state so landing.py can use them
st.session_state["_pages"] = _pages
st.session_state["_home"] = _home
st.session_state["_sections"] = _SECTIONS

# ---------------------------------------------------------------------------
# Role-based navigation filtering
# ---------------------------------------------------------------------------
from shared.role_config import get_role_pages

_hub_role = user.get("hub_role", "user") if isinstance(user, dict) else "user"

_allowed_slugs = get_role_pages(_hub_role)  # None means "all"

if _allowed_slugs is not None:
    _allowed_set = set(_allowed_slugs)
    _visible_pages = {k: v for k, v in _pages.items() if k in _allowed_set}
else:
    _visible_pages = _pages

# Build nav dict — only include sections that have at least one visible page
_full_nav = {
    "": [_home],
    "Strategy": [
        "strategy-overview", "greater-goodness",
        "intro-people", "intro-operations", "intro-digital",
        "way-of-working",
    ],
    "Growing Legends": [
        "skills-academy", "the-paddock", "prompt-builder", "hub-assistant",
    ],
    "Operations": [
        "customers", "sales", "profitability", "revenue-bridge",
        "store-ops", "buying-hub", "product-intel", "plu-intel",
        "transport", "analytics-engine",
    ],
    "Property": [
        "store-network", "market-share", "demographics",
        "whitespace", "competitor-map", "roce", "cannibalisation",
    ],
    "MDHE": [
        "mdhe-dashboard", "mdhe-upload", "mdhe-issues", "mdhe-guide",
    ],
    "Back of House": [
        "the-rubric", "approvals", "workflow-engine", "agent-ops",
        "mission-control", "ai-adoption", "adoption", "trending",
        "agent-hub", "marketing-assets", "user-management",
    ],
}

_nav_dict = {}
for section, slugs_or_pages in _full_nav.items():
    if section == "":
        _nav_dict[""] = [_home]
        continue
    filtered = [_visible_pages[s] for s in slugs_or_pages if s in _visible_pages]
    if filtered:
        _nav_dict[section] = filtered

nav = st.navigation(_nav_dict)

# ---------------------------------------------------------------------------
# Navigation header — uses st.page_link (preserves session, no page reload)
# ---------------------------------------------------------------------------

current_slug = nav.url_path

# Log page view (fire-and-forget — never block rendering)
_auth_user = st.session_state.get("auth_user")
if _auth_user and current_slug:
    try:
        import requests as _pv_req
        _pv_api = os.getenv("API_URL", "http://localhost:8000")
        _pv_req.post(
            f"{_pv_api}/api/analytics/pageview",
            json={
                "user_id": _auth_user.get("email", ""),
                "user_email": _auth_user.get("email", ""),
                "page_slug": current_slug or "home",
                "user_role": _auth_user.get("hub_role", "user"),
            },
            timeout=1,
        )
    except Exception:
        pass

# Build slug-to-section lookup
_slug_to_section = {}
for _sec in _SECTIONS:
    for s in _sec["slugs"]:
        _slug_to_section[s] = _sec

active_section = _slug_to_section.get(current_slug)

# Logo
_logo = _DIR.parent / "assets" / "logo.png"
if _logo.exists():
    st.image(str(_logo), width=180)

# Row 1: Home + section tabs (only those with visible pages)
_visible_sections = [s for s in _SECTIONS if any(slug in _visible_pages for slug in s["slugs"])]

cols = st.columns(1 + len(_visible_sections))

with cols[0]:
    st.page_link(_home, label="\U0001f34e Home", use_container_width=True)

for i, section in enumerate(_visible_sections):
    with cols[i + 1]:
        first_slug = next((s for s in section["slugs"] if s in _visible_pages), section["slugs"][0])
        label = f"{section['icon']} {section['name']}"
        st.page_link(_visible_pages.get(first_slug, _pages[first_slug]), label=label, use_container_width=True)

# De-emphasize Back of House tab (last muted section)
if _visible_sections and _visible_sections[-1].get("is_muted"):
    _n = 1 + len(_visible_sections)
    st.markdown(
        f"<style>"
        f"[data-testid='stHorizontalBlock']:first-of-type "
        f"> [data-testid='column']:nth-child({_n}) button {{"
        f"  color: #8899AA !important;"
        f"  font-size: 0.88em !important;"
        f"  opacity: 0.5;"
        f"}}"
        f"[data-testid='stHorizontalBlock']:first-of-type "
        f"> [data-testid='column']:nth-child({_n}) button:hover {{"
        f"  opacity: 1;"
        f"  color: #B0BEC5 !important;"
        f"}}"
        f"</style>",
        unsafe_allow_html=True,
    )

# Row 2: Sub-pages within active section (only visible ones)
if active_section:
    _visible_sub = [s for s in active_section["slugs"] if s in _visible_pages]
    # Hide marketing-assets from sub-nav (URL-only access)
    _visible_sub = [s for s in _visible_sub if s != "marketing-assets"]
    if len(_visible_sub) > 1:
        sub_cols = st.columns(len(_visible_sub))
        _sec_color = active_section["color"]
        for j, slug in enumerate(_visible_sub):
            with sub_cols[j]:
                page = _visible_pages[slug]
                is_current = slug == current_slug
                # Truncate long titles when many sub-tabs
                _title = page.title
                if len(_visible_sub) > 7 and len(_title) > 12:
                    _title = _title[:11] + "\u2026"
                if is_current:
                    st.markdown(
                        f"<div style='text-align:center;padding:8px 6px;"
                        f"border-bottom:3px solid {_sec_color};"
                        f"font-weight:600;color:{_sec_color};'>"
                        f"{_title}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.page_link(page, label=_title, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Sidebar: Role selector + Academy XP widget
# ---------------------------------------------------------------------------

_auth_user = st.session_state.get("auth_user")

# Role selector — shown when user has default role
if _auth_user and _auth_user.get("hub_role", "user") == "user":
    with st.sidebar:
        from shared.role_config import get_all_roles, get_role_display_name
        _role_options = get_all_roles()
        _role_keys = [k for k, _ in _role_options]
        _role_labels = [n for _, n in _role_options]
        st.markdown(
            "<div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);"
            "border-radius:8px;padding:10px 12px;margin-bottom:10px;'>"
            "<div style='font-weight:600;font-size:0.85em;color:#2ECC71;'>"
            "Personalise your Hub</div>"
            "<div style='font-size:0.78em;color:#8899AA;'>"
            "Select your role to see relevant pages only.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        _chosen_idx = st.selectbox(
            "I am a...", range(len(_role_labels)),
            format_func=lambda i: _role_labels[i],
            key="role_selector",
        )
        if st.button("Set My Role", key="set_role_btn", use_container_width=True):
            _chosen_role = _role_keys[_chosen_idx]
            try:
                import requests as _role_req
                _role_api = os.getenv("API_URL", "http://localhost:8000")
                _role_req.put(
                    f"{_role_api}/api/auth/role",
                    json={"email": _auth_user["email"], "hub_role": _chosen_role},
                    timeout=3,
                )
                _auth_user["hub_role"] = _chosen_role
                st.session_state["auth_user"] = _auth_user
                st.rerun()
            except Exception:
                st.error("Could not save role. Try again.")
if _auth_user:
    _uid = _auth_user.get("email", "")
    if _uid:
        import requests as _req
        _API = os.getenv("API_URL", "http://localhost:8000")

        # Streak check-in (once per session)
        if "academy_checkin_done" not in st.session_state:
            try:
                _req.post(f"{_API}/api/academy/streak/checkin",
                          params={"user_id": _uid}, timeout=3)
                st.session_state["academy_checkin_done"] = True
            except Exception:
                pass

        # Load XP summary
        if "academy_sidebar_xp" not in st.session_state:
            try:
                _r = _req.get(f"{_API}/api/academy/xp/{_uid}", timeout=3)
                st.session_state["academy_sidebar_xp"] = _r.json() if _r.status_code == 200 else {}
            except Exception:
                st.session_state["academy_sidebar_xp"] = {}

        _xp = st.session_state.get("academy_sidebar_xp", {})
        if _xp.get("total_xp") is not None:
            _lvl_icon = _xp.get("icon", "\U0001f331")
            _lvl_name = _xp.get("name", "Seed")
            _total = _xp.get("total_xp", 0)
            with st.sidebar:
                st.markdown(
                    f"<div style='background:rgba(46,204,113,0.12);"
                    f"border:1px solid rgba(46,204,113,0.25);"
                    f"color:white;border-radius:10px;padding:10px 14px;margin-bottom:12px;'>"
                    f"<div style='font-weight:700;font-size:0.95em;color:#2ECC71;'>"
                    f"{_lvl_icon} {_lvl_name}</div>"
                    f"<div style='font-size:0.8em;color:#B0BEC5;'>"
                    f"{_total:,} XP</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

# ---------------------------------------------------------------------------
# Run the selected page
# ---------------------------------------------------------------------------

nav.run()
