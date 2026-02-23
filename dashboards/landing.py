"""
Harris Farm Hub — Mission Control
Front page for the AI Centre of Excellence.
Strategy pillars, 5 goals, quick launch, activity, WATCHDOG trust.
"""

import os
from datetime import datetime

import streamlit as st

from shared.styles import render_footer, HFM_GREEN, HFM_DARK
from shared.goals_config import (
    goal_badge_html,
    fetch_watchdog_scores,
)
from shared.growth_engine import render_growth_engine

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1 — Mission Statement + Personalised Greeting
# ═══════════════════════════════════════════════════════════════════════════

# Time-based greeting
_hour = datetime.now().hour
if _hour < 12:
    _greeting = "Good morning"
elif _hour < 17:
    _greeting = "Good afternoon"
else:
    _greeting = "Good evening"

_user_name = ""
if user and user.get("name"):
    _user_name = f", {user['name'].split()[0]}"

st.markdown(
    f"<div style='background:linear-gradient(135deg, #0F1D35 0%, #132240 50%, #1A2D50 100%);"
    f"border:1px solid rgba(46,204,113,0.2);border-top:3px solid #2ECC71;"
    f"color:white;padding:32px 36px;border-radius:14px;margin-bottom:20px;'>"
    f"<div style='font-size:1em;color:#B0BEC5;margin-bottom:4px;"
    f"font-family:Trebuchet MS,sans-serif;'>"
    f"{_greeting}{_user_name}</div>"
    f"<div style='font-size:2em;font-weight:700;margin-bottom:4px;"
    f"font-family:Georgia,serif;color:white;'>"
    f"Harris Farm Hub</div>"
    f"<div style='font-size:1.2em;font-weight:500;color:#2ECC71;margin-bottom:8px;"
    f"font-family:Trebuchet MS,sans-serif;'>"
    f"AI Centre of Excellence &mdash; For The Greater Goodness</div>"
    f"<div style='font-size:0.95em;color:#B0BEC5;max-width:700px;"
    f"font-family:Trebuchet MS,sans-serif;'>"
    f"Accelerating Harris Farm's strategy through AI that works alongside our "
    f"people &mdash; safely, transparently, and always improving.</div>"
    f"</div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1B — Search Bar ("What are you looking for?")
# ═══════════════════════════════════════════════════════════════════════════

_search_query = st.text_input(
    "What are you looking for?",
    placeholder="Search pages, knowledge base, features...",
    key="home_search",
    label_visibility="collapsed",
)

if _search_query and len(_search_query) >= 2:
    _q_lower = _search_query.lower()

    # 1. Page matches — fuzzy match on title and slug
    _page_matches = []
    for _slug, _pg in _pages.items():
        _title_lower = _pg.title.lower()
        _slug_words = _slug.replace("-", " ")
        if _q_lower in _title_lower or _q_lower in _slug_words:
            _page_matches.append((_slug, _pg))

    # 2. Knowledge base matches (via existing API)
    _kb_results = []
    try:
        import requests as _search_req
        _search_api = os.getenv("API_URL", "http://localhost:8000")
        _kb_resp = _search_req.get(
            f"{_search_api}/api/knowledge/search",
            params={"q": _search_query, "limit": 5},
            timeout=3,
        )
        if _kb_resp.status_code == 200:
            _kb_results = _kb_resp.json().get("results", [])
    except Exception:
        pass

    # Render results
    if _page_matches or _kb_results:
        if _page_matches:
            st.markdown(f"**Pages** ({len(_page_matches)} match{'es' if len(_page_matches) != 1 else ''})")
            _sr_cols = st.columns(min(len(_page_matches), 4))
            for _si, (_s_slug, _s_pg) in enumerate(_page_matches[:8]):
                with _sr_cols[_si % 4]:
                    st.page_link(_s_pg, label=f"{_s_pg.icon} {_s_pg.title}" if hasattr(_s_pg, "icon") else _s_pg.title, use_container_width=True)

        if _kb_results:
            st.markdown(f"**Knowledge Base** ({len(_kb_results)} result{'s' if len(_kb_results) != 1 else ''})")
            for _kb in _kb_results:
                _kb_title = _kb.get("filename", "Untitled")
                _kb_cat = _kb.get("category", "")
                _kb_snippet = _kb.get("snippet", "")[:200]
                with st.expander(f"{_kb_cat} | {_kb_title}"):
                    st.caption(_kb_snippet)

        st.markdown("---")
    else:
        st.caption("No results found. Try different keywords.")
        st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1C — Orientation ("What The Hub is for")
# ═══════════════════════════════════════════════════════════════════════════

_ORI_CARDS = [
    {
        "icon": "\U0001f3af", "title": "Strategy",
        "subtitle": "Where we're going",
        "desc": "Five pillars, 100+ initiatives, live progress "
                "from Monday.com. Track our path to Vision 2030.",
        "slug": "strategy-overview", "cta": "View Strategy",
        "color": "#2ECC71",
    },
    {
        "icon": "\u2b50", "title": "AI Skills",
        "subtitle": "Level up your capability",
        "desc": "Academy, Prompt Engine, The Paddock, Hub Assistant "
                "\u2014 everything you need to build AI confidence.",
        "slug": "skills-academy", "cta": "Start Learning",
        "color": "#8B5CF6",
    },
    {
        "icon": "\U0001f4ca", "title": "Operations",
        "subtitle": "Tools that make us better",
        "desc": "Sales, profitability, customers, supply chain, "
                "PLU intelligence \u2014 data-driven decision making.",
        "slug": "sales", "cta": "Open Tools",
        "color": "#F1C40F",
    },
]

_ori_cols = st.columns(3)
for _oi, _oc in enumerate(_ORI_CARDS):
    with _ori_cols[_oi]:
        st.markdown(
            f"<div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);"
            f"border-radius:12px;padding:20px;"
            f"border-top:3px solid {_oc['color']};min-height:180px;'>"
            f"<div style='font-size:1.6em;margin-bottom:4px;'>{_oc['icon']}</div>"
            f"<div style='font-weight:700;font-size:1.1em;color:white;"
            f"font-family:Georgia,serif;'>"
            f"{_oc['title']}</div>"
            f"<div style='color:{_oc['color']};font-size:0.85em;"
            f"font-weight:600;margin-bottom:8px;'>{_oc['subtitle']}</div>"
            f"<div style='font-size:0.82em;color:#8899AA;line-height:1.5;'>"
            f"{_oc['desc']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        _ori_page = _pages.get(_oc["slug"])
        if _ori_page:
            st.page_link(
                _ori_page,
                label=f"{_oc['cta']} \u2192",
                use_container_width=True,
            )

st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2 — Growth Engine (Four Lessons + Gamification + Workflow)
# ═══════════════════════════════════════════════════════════════════════════

# Fetch user's Academy XP/level from backend
_ge_level = "Seed"
_ge_xp = 0
_ge_xp_to_next = 100
try:
    import requests as _req
    _api_url = os.getenv("API_URL", "http://localhost:8000")
    _user_email = ""
    if user and isinstance(user, dict):
        _user_email = user.get("email", "")
    elif user and isinstance(user, str):
        _user_email = user
    if _user_email:
        _profile = _req.get(
            f"{_api_url}/api/academy/profile/{_user_email}", timeout=3
        ).json()
        _ge_level = _profile.get("name", "Seed")
        _ge_xp = _profile.get("total_xp", 0)
        _ge_xp_to_next = _profile.get("xp_to_next", 100)
except Exception:
    pass

render_growth_engine(user_level=_ge_level, user_xp=_ge_xp, xp_to_next=_ge_xp_to_next)

# Navigation links for the four lesson cards (st.page_link, not HTML anchors)
_ge_links = [
    ("hub-assistant", "\U0001f4a1 Open Hub Assistant"),
    ("skills-academy", "\U0001f31f Open Academy"),
    ("prompt-builder", "\u26a1 Open Prompt Engine"),
    ("the-paddock", "\U0001f680 Open The Paddock"),
]
_ge_cols = st.columns(4)
for idx, (slug, label) in enumerate(_ge_links):
    with _ge_cols[idx]:
        _pg = _pages.get(slug)
        if _pg:
            st.page_link(_pg, label=label, use_container_width=True)

st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4 — Quick Launch
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    "<h2 style='color:white;margin-bottom:4px;font-family:Georgia,serif;'>Quick Launch</h2>"
    "<p style='color:#8899AA;margin-top:0;'>Jump straight into what matters.</p>",
    unsafe_allow_html=True,
)

_QUICK_LAUNCH = [
    {"label": "Hub Assistant", "icon": "\U0001f4ac", "slug": "hub-assistant",
     "desc": "Ask about policies, procedures, and golden rules", "goal": "G2"},
    {"label": "Prompt Engine", "icon": "\u26a1", "slug": "prompt-builder",
     "desc": "Build analytical prompts, score with rubric, submit for approval", "goal": "G2"},
    {"label": "Buying Hub", "icon": "\U0001f69a", "slug": "buying-hub",
     "desc": "Category buying, demand forecasting, weather analysis", "goal": "G4"},
    {"label": "Strategy Tracker", "icon": "\U0001f4ca", "slug": "way-of-working",
     "desc": "Drill into all 100+ initiatives across the 5 pillars", "goal": "G1"},
]

ql_cols = st.columns(4)

for idx, ql in enumerate(_QUICK_LAUNCH):
    with ql_cols[idx]:
        badge = goal_badge_html(ql["goal"])
        st.markdown(
            f"<div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);"
            f"border-radius:10px;padding:16px;min-height:110px;'>"
            f"<div style='font-size:1.5em;'>{ql['icon']}</div>"
            f"<div style='font-weight:700;color:white;margin:4px 0 2px;"
            f"font-family:Georgia,serif;'>"
            f"{ql['label']}</div>"
            f"<div style='font-size:0.8em;color:#8899AA;margin-bottom:6px;'>"
            f"{ql['desc']}</div>"
            f"{badge}"
            f"</div>",
            unsafe_allow_html=True,
        )
        page = _pages.get(ql["slug"])
        if page:
            st.page_link(page, label=f"Open {ql['label']} \u2192", use_container_width=True)

st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5 — AI Ninjas (compact inline badge)
# ═══════════════════════════════════════════════════════════════════════════

try:
    import requests as _req
    _api = os.getenv("API_URL", "http://localhost:8000")
    _radar = _req.get(f"{_api}/api/workflow/talent-radar", timeout=3).json()
    _ninja_count = _radar.get("total_ninjas", 0)
    _active_users = _radar.get("total_active_users", 0)
except Exception:
    _ninja_count = 0
    _active_users = 0

_prompt_page = _pages.get("prompt-builder")
st.markdown(
    f"<div style='background:linear-gradient(135deg, #0F1D35 0%, #132240 100%);"
    f"border:1px solid rgba(255,255,255,0.08);"
    f"border-radius:10px;padding:16px 24px;display:flex;align-items:center;"
    f"justify-content:space-between;flex-wrap:wrap;gap:12px;'>"
    f"<div style='display:flex;align-items:center;gap:12px;'>"
    f"<span style='font-size:1.6em;'>\U0001f977</span>"
    f"<div>"
    f"<div style='color:white;font-weight:700;font-size:1em;'>"
    f"The Search for AI Ninjas</div>"
    f"<div style='color:#8899AA;font-size:0.82em;'>"
    f"We're looking for the curious, the driven, the learners "
    f"&mdash; they could be YOU.</div>"
    f"</div></div>"
    f"<div style='display:flex;gap:16px;align-items:center;'>"
    f"<div style='text-align:center;'>"
    f"<div style='color:#E040FB;font-size:1.2em;font-weight:700;'>"
    f"{_ninja_count}</div>"
    f"<div style='color:#8899AA;font-size:0.7em;'>Ninjas</div></div>"
    f"<div style='text-align:center;'>"
    f"<div style='color:white;font-size:1.2em;font-weight:700;'>"
    f"{_active_users}</div>"
    f"<div style='color:#8899AA;font-size:0.7em;'>Active</div></div>"
    f"</div></div>",
    unsafe_allow_html=True,
)
if _prompt_page:
    _cta_cols = st.columns([1, 2, 1])
    with _cta_cols[1]:
        st.page_link(
            _prompt_page,
            label="\U0001f680 Start Your First Prompt",
            use_container_width=True,
        )

st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6 — WATCHDOG Trust Badge (compact)
# ═══════════════════════════════════════════════════════════════════════════

_wd_scores = fetch_watchdog_scores()
_wd_avg = sum(_wd_scores) / len(_wd_scores) if _wd_scores else 0
_wd_labels = ["H", "R", "S", "C", "D", "U", "X"]
_wd_pills = " ".join(
    f"<span style='background:rgba(46,204,113,0.1);border:1px solid rgba(46,204,113,0.25);"
    f"border-radius:12px;padding:2px 8px;font-size:0.78em;color:#2ECC71;'>"
    f"{lbl}:{v:.0f}</span>"
    for lbl, v in zip(_wd_labels, _wd_scores)
)
st.markdown(
    f"<div style='display:flex;align-items:center;gap:12px;padding:12px 16px;"
    f"background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);"
    f"border-radius:10px;flex-wrap:wrap;'>"
    f"<span style='font-size:1.1em;'>\U0001f6e1\ufe0f</span>"
    f"<span style='font-weight:600;color:white;font-size:0.9em;'>"
    f"WATCHDOG Governance</span>"
    f"<span style='color:#8899AA;font-size:0.82em;'>"
    f"Avg {_wd_avg:.1f}/10</span>"
    f"<span style='display:flex;gap:4px;flex-wrap:wrap;'>{_wd_pills}</span>"
    f"</div>",
    unsafe_allow_html=True,
)

st.markdown("")

# --- About (compact) ---
with st.expander("About Harris Farm Markets"):
    st.markdown(
        "**Founded in 1971** by David and Cathy Harris. 100% family-owned for over "
        "fifty years. 30+ stores across NSW, Queensland, and the ACT.\n\n"
        "**Our Purpose:** Living the Greater Goodness \u2014 good food does good things for people.\n\n"
        "**Our Strategy:** *Fewer, Bigger, Better* \u2014 Vision 2030: Australia's most loved "
        "fresh food retailer, inside and out.\n\n"
        "*Co-CEOs: Angus Harris & Luke Harris*"
    )

render_footer("Harris Farm Hub", "Mission Control \u2014 AI Centre of Excellence", user)
