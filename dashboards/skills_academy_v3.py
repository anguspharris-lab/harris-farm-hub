"""
Harris Farm Hub -- Skills Academy v3
=====================================
Pillar 3: Growing Legendary Leadership

A structured AI skills training programme with adaptive difficulty,
placement testing, peer battles, daily micro-challenges, and enterprise
capstone modules.

Two learning series:
  L-Series (L1-L5): Core AI Skills -- prompting, role application, advanced
  D-Series (D1-D5): Applied Data + AI -- querying, analysis, reporting

7 tabs:
  My Progress | Placement Challenge | L-Series | D-Series |
  Level 6 Enterprise | Daily & Social | Leaderboard

Python 3.9 compatible.
"""

import os
import time
from typing import Optional

import requests
import streamlit as st
import plotly.graph_objects as go

from shared.styles import render_header, render_footer, HFM_GREEN
from shared.skills_content import (
    SKILLS_MODULES,
    SKILLS_MODULE_MAP,
    ASSESSMENT_RUBRIC,
    SERIES_INFO,
    PREREQUISITE_GRAPH,
    SCORING_SYSTEM_PROMPT,
    ADAPTIVE_EXERCISES,
    L6_ENTERPRISE_CHALLENGES,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_URL = os.getenv("API_URL", "http://localhost:8000")
PASS_THRESHOLD = ASSESSMENT_RUBRIC["pass_threshold"]  # 18
MAX_SCORE = ASSESSMENT_RUBRIC["max_score"]  # 25
CRITERIA = ASSESSMENT_RUBRIC["criteria"]
BRAND_GREEN = "#2ECC71"
PEOPLE_GREEN = "#059669"

L_MODULES = [m for m in SKILLS_MODULES if m["series"] == "L"]
D_MODULES = [m for m in SKILLS_MODULES if m["series"] == "D"]

DIFFICULTY_COLOURS = {
    "beginner": "#22c55e",
    "intermediate": "#eab308",
    "advanced": "#ef4444",
}

TIER_COLOURS = {
    "Standard": "#6b7280",
    "Stretch": "#d97706",
    "Elite": "#7c3aed",
}

TIER_ICONS = {
    "Standard": "⚪",
    "Stretch": "🟡",
    "Elite": "🟣",
}

LEVEL_DISPLAY = [
    {"name": "Seed", "icon": "🌱", "min_xp": 0, "max_xp": 49},
    {"name": "Sprout", "icon": "🌿", "min_xp": 50, "max_xp": 149},
    {"name": "Growing", "icon": "🌻", "min_xp": 150, "max_xp": 399},
    {"name": "Harvest", "icon": "🌾", "min_xp": 400, "max_xp": 799},
    {"name": "Canopy", "icon": "🌳", "min_xp": 800, "max_xp": 1499},
    {"name": "Root System", "icon": "🏆", "min_xp": 1500, "max_xp": None},
]


# ---------------------------------------------------------------------------
# Auth + page context
# ---------------------------------------------------------------------------

user = st.session_state.get("auth_user", {})
_pages = st.session_state.get("_pages", {})
user_email = (user or {}).get("email", "")
uid = user_email if user_email else "anonymous"
is_admin = (user or {}).get("is_admin", False)

render_header(
    "Skills Academy",
    "**Harris Farm Markets** | AI Skills Training Programme",
    goals=["G3"],
    strategy_context=(
        "Train every Harris Farmer to use AI effectively "
        "-- from first prompt to advanced analysis."
    ),
)


# ---------------------------------------------------------------------------
# Hero banner
# ---------------------------------------------------------------------------

st.markdown(
    "<div style='background:linear-gradient(135deg, #059669 0%, #047857 50%, "
    "#065f46 100%);color:white;padding:36px 32px;border-radius:14px;"
    "margin-bottom:24px;'>"
    "<div style='font-size:2.2em;font-weight:800;margin-bottom:8px;'>"
    "Skills Academy v3</div>"
    "<div style='font-size:1.15em;opacity:0.95;max-width:800px;line-height:1.6;'>"
    "Adaptive learning across two tracks. Take the placement challenge, "
    "learn at your level, compete with peers, and earn your AI certification. "
    "Now with adaptive difficulty, daily micro-challenges, and peer battles."
    "</div>"
    "<div style='margin-top:16px;font-size:0.9em;opacity:0.8;'>"
    "L-Series: Core AI Skills &bull; D-Series: Applied Data + AI &bull; "
    "Level 6: Enterprise Capstone &bull; 18/25 to pass</div>"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================================
# API HELPERS
# ============================================================================

def _api_get(path):
    """GET from /api/skills{path}; returns parsed JSON or None on failure."""
    try:
        resp = requests.get(
            "{}/api/skills{}".format(API_URL, path), timeout=5,
        )
        if resp.ok:
            return resp.json()
        return None
    except Exception:
        return None


def _api_post(path, json_body=None):
    """POST to /api/skills{path}; returns parsed JSON or None on failure."""
    try:
        resp = requests.post(
            "{}/api/skills{}".format(API_URL, path),
            json=json_body or {},
            timeout=5,
        )
        if resp.ok:
            return resp.json()
        return None
    except Exception:
        return None


def _academy_get(path):
    """GET from /api/academy{path}; returns parsed JSON or None on failure."""
    try:
        resp = requests.get(
            "{}/api/academy{}".format(API_URL, path), timeout=5,
        )
        if resp.ok:
            return resp.json()
        return None
    except Exception:
        return None


def _raw_api_get(full_path):
    """GET from a full API path (e.g. /api/paddock/leaderboard)."""
    try:
        resp = requests.get(
            "{}{}".format(API_URL, full_path), timeout=5,
        )
        if resp.ok:
            return resp.json()
        return None
    except Exception:
        return None


# ============================================================================
# DATA LOADERS (session-cached)
# ============================================================================

def _load_profile():
    """Load XP profile from Academy API. Cached in session_state."""
    cache_key = "sa_profile"
    if cache_key not in st.session_state:
        result = _academy_get("/profile/{}".format(uid))
        st.session_state[cache_key] = result if result else {}
    return st.session_state[cache_key]


def _load_progress():
    """Load module progress from Skills API. Cached in session_state."""
    cache_key = "sa_progress"
    if cache_key not in st.session_state:
        data = _api_get("/progress/{}".format(uid))
        if data and isinstance(data, dict):
            st.session_state[cache_key] = data.get("progress", [])
        else:
            st.session_state[cache_key] = []
    return st.session_state[cache_key]


def _load_badges():
    """Load badges from Academy API. Cached in session_state."""
    cache_key = "sa_badges"
    if cache_key not in st.session_state:
        result = _academy_get("/badges/{}".format(uid))
        st.session_state[cache_key] = result if result else {}
    return st.session_state[cache_key]


def _load_placement():
    """Load placement result. Returns dict or None."""
    cache_key = "sa_placement"
    if cache_key not in st.session_state:
        result = _api_get("/placement/{}".format(uid))
        if result and isinstance(result, dict) and "detail" not in result:
            st.session_state[cache_key] = result
        else:
            st.session_state[cache_key] = None
    return st.session_state[cache_key]


def _load_adaptive(module_code):
    """Load adaptive tier for a module."""
    result = _api_get("/adaptive/{}/{}".format(uid, module_code))
    if result and isinstance(result, dict):
        return result
    return {"current_tier": "Standard", "consecutive_elite": 0}


def _load_mindset():
    """Load mindset assessments."""
    cache_key = "sa_mindset"
    if cache_key not in st.session_state:
        result = _api_get("/mindset/{}".format(uid))
        if result and isinstance(result, dict):
            st.session_state[cache_key] = result.get("assessments", [])
        else:
            st.session_state[cache_key] = []
    return st.session_state[cache_key]


def _progress_map():
    """Return dict mapping module code -> progress record."""
    progress = _load_progress()
    return {p["module_code"]: p for p in progress if "module_code" in p}


def _module_status(code, pmap):
    """Determine module status: locked, available, in-progress, or passed."""
    prereqs = PREREQUISITE_GRAPH.get(code, [])
    for pr in prereqs:
        pr_rec = pmap.get(pr)
        if not pr_rec or pr_rec.get("status") != "passed":
            return "locked"
    rec = pmap.get(code)
    if not rec:
        return "available"
    return rec.get("status", "available")


def _best_score(code, pmap):
    """Return best score for a module or None."""
    rec = pmap.get(code)
    if rec:
        return rec.get("best_score")
    return None


def _xp_level_info(total_xp):
    """Return current level info and progress to next."""
    current = LEVEL_DISPLAY[0]
    for lv in LEVEL_DISPLAY:
        if total_xp >= lv["min_xp"]:
            current = lv
    # Progress to next level
    idx = LEVEL_DISPLAY.index(current)
    if idx < len(LEVEL_DISPLAY) - 1:
        next_lv = LEVEL_DISPLAY[idx + 1]
        range_size = next_lv["min_xp"] - current["min_xp"]
        progress_in = total_xp - current["min_xp"]
        pct = min(progress_in / max(range_size, 1), 1.0)
        return current, next_lv, pct
    return current, None, 1.0


def _display_name(email_str):
    """Extract display name from email."""
    if "@" in email_str:
        return email_str.split("@")[0]
    return email_str


# ============================================================================
# RENDERING HELPERS
# ============================================================================

def _render_card(content_html, bg="#ffffff", border="#e2e8f0", padding="16px"):
    """Render a styled card."""
    st.markdown(
        "<div style='background:{bg};border:1px solid {bd};border-radius:10px;"
        "padding:{pd};margin-bottom:12px;'>{content}</div>".format(
            bg=bg, bd=border, pd=padding, content=content_html,
        ),
        unsafe_allow_html=True,
    )


def _render_tier_badge(tier):
    """Render an inline tier badge."""
    colour = TIER_COLOURS.get(tier, "#6b7280")
    icon = TIER_ICONS.get(tier, "")
    return (
        "<span style='background:{c};color:white;padding:2px 10px;"
        "border-radius:12px;font-size:0.78em;font-weight:600;'>"
        "{icon} {tier}</span>".format(c=colour, icon=icon, tier=tier)
    )


def _render_radar_chart(scores, title="Assessment Scores"):
    """Render a plotly scatterpolar radar chart for the 5 criteria."""
    labels = [c["name"] for c in CRITERIA]
    values = [scores.get(c["key"], 0) for c in CRITERIA]
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(75, 160, 33, 0.2)",
        line=dict(color=BRAND_GREEN, width=2),
        name="Your Score",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 5], tickvals=[1, 2, 3, 4, 5],
            ),
        ),
        title=dict(text=title, font=dict(size=14)),
        showlegend=False,
        height=350,
        margin=dict(l=60, r=60, t=50, b=40),
    )
    return fig


def _render_module_card(mod, status, best, tier_info=None, key_suffix=""):
    """Render a styled card for a single module with adaptive tier."""
    code = mod["code"]
    name = mod["name"]
    diff = mod["difficulty"]
    diff_col = DIFFICULTY_COLOURS.get(diff, "#6b7280")
    dur = mod["duration_minutes"]
    prereqs = mod["prerequisites"]

    if status == "locked":
        bg = "#f1f5f9"
        border_col = "#cbd5e1"
        opacity = "0.6"
        icon = "&#128274;"
        status_label = "Locked"
        status_bg = "#94a3b8"
    elif status == "passed":
        bg = "#f0fdf4"
        border_col = "#22c55e"
        opacity = "1"
        icon = "&#9989;"
        score_str = ""
        if best is not None:
            score_str = " ({}/25)".format(int(best))
        status_label = "Passed" + score_str
        status_bg = "#22c55e"
    elif status == "in-progress":
        bg = "#fefce8"
        border_col = "#eab308"
        opacity = "1"
        icon = "&#9997;"
        status_label = "In Progress"
        status_bg = "#eab308"
    else:
        bg = "#ffffff"
        border_col = BRAND_GREEN
        opacity = "1"
        icon = "&#9654;"
        status_label = "Available"
        status_bg = BRAND_GREEN

    prereq_html = ""
    if status == "locked" and prereqs:
        prereq_names = ", ".join(prereqs)
        prereq_html = (
            "<div style='font-size:0.8em;color:#94a3b8;margin-top:6px;'>"
            "Requires: {}</div>".format(prereq_names)
        )

    tier_html = ""
    if tier_info and status != "locked":
        tier = tier_info.get("current_tier", "Standard")
        tier_html = " " + _render_tier_badge(tier)

    st.markdown(
        "<div style='background:{bg};border-left:4px solid {bc};"
        "border-radius:0 10px 10px 0;padding:14px 16px;margin-bottom:10px;"
        "opacity:{op};'>"
        "<div style='display:flex;justify-content:space-between;align-items:center;"
        "flex-wrap:wrap;gap:6px;'>"
        "<div style='font-weight:700;font-size:1.05em;'>"
        "{icon} {code}: {name}{tier}</div>"
        "<span style='background:{sbg};color:white;padding:2px 10px;"
        "border-radius:12px;font-size:0.78em;font-weight:600;'>"
        "{sl}</span></div>"
        "<div style='display:flex;gap:10px;margin-top:6px;'>"
        "<span style='background:{dc};color:white;padding:1px 8px;"
        "border-radius:10px;font-size:0.75em;'>{diff}</span>"
        "<span style='font-size:0.8em;color:#6b7280;'>{dur} min</span>"
        "</div>"
        "<div style='font-size:0.88em;color:#555;margin-top:6px;'>"
        "{desc}</div>"
        "{prereq}"
        "</div>".format(
            bg=bg, bc=border_col, op=opacity, icon=icon,
            code=code, name=name, tier=tier_html, sbg=status_bg,
            sl=status_label, dc=diff_col, diff=diff.title(), dur=dur,
            desc=mod["description"], prereq=prereq_html,
        ),
        unsafe_allow_html=True,
    )


def _render_score_bars(result):
    """Render per-criterion score bars for an assessment result."""
    for crit in CRITERIA:
        ckey = crit["key"]
        val = result.get(ckey, 0)
        pct = val / crit["max"] * 100
        bar_col = "#22c55e" if val >= 4 else ("#eab308" if val >= 3 else "#ef4444")
        st.markdown(
            "<div style='margin:6px 0;'>"
            "<div style='display:flex;justify-content:space-between;"
            "font-size:0.9em;'>"
            "<span>{name}</span>"
            "<span style='font-weight:700;color:{col};'>{val}/{mx}</span>"
            "</div>"
            "<div style='background:#e2e8f0;border-radius:4px;"
            "height:10px;margin:2px 0;'>"
            "<div style='background:{col};width:{pct}%;"
            "height:100%;border-radius:4px;'></div>"
            "</div></div>".format(
                name=crit["name"], col=bar_col, val=val,
                mx=crit["max"], pct=pct,
            ),
            unsafe_allow_html=True,
        )


# ============================================================================
# PLACEMENT CHECK (top-level)
# ============================================================================

placement_data = _load_placement()
has_placement = placement_data is not None

if not has_placement:
    st.markdown(
        "<div style='background:linear-gradient(135deg, #fef3c7, #fde68a);"
        "border:2px solid #f59e0b;border-radius:12px;padding:20px;"
        "margin-bottom:20px;text-align:center;'>"
        "<div style='font-size:1.3em;font-weight:700;color:#92400e;'>"
        "Welcome! Start with the Placement Challenge</div>"
        "<div style='font-size:1em;color:#78350f;margin-top:8px;'>"
        "Take a 5-scenario placement test to find your starting level. "
        "It takes about 10 minutes and helps us personalise your learning path."
        "</div>"
        "<div style='margin-top:12px;font-size:0.9em;color:#92400e;'>"
        "Head to the <strong>Placement Challenge</strong> tab to begin."
        "</div></div>",
        unsafe_allow_html=True,
    )


# ============================================================================
# 7 TABS
# ============================================================================

tabs = st.tabs([
    "My Progress",
    "Placement Challenge",
    "L-Series (Core AI)",
    "D-Series (Data + AI)",
    "Level 6 Enterprise",
    "Daily & Social",
    "Leaderboard",
])


# ============================================================================
# TAB 0: MY PROGRESS
# ============================================================================

with tabs[0]:
    profile = _load_profile()
    pmap = _progress_map()

    # -- XP Profile Card ---------------------------------------------------
    st.markdown("### Your Progress")

    total_xp = profile.get("total_xp", 0) if profile else 0
    level_name = profile.get("name", "Seed") if profile else "Seed"
    level_icon_str = profile.get("icon", "") if profile else ""
    streak_data = profile.get("streak", {}) if profile else {}
    current_streak = streak_data.get("current_streak", 0) if streak_data else 0
    multiplier = streak_data.get("streak_multiplier", 1.0) if streak_data else 1.0

    current_lv, next_lv, lv_pct = _xp_level_info(total_xp)

    # XP Card with progress bar
    next_label = next_lv["name"] if next_lv else "MAX"
    next_xp = next_lv["min_xp"] if next_lv else total_xp
    pbar_pct = int(lv_pct * 100)

    st.markdown(
        "<div style='background:linear-gradient(135deg, #f0fdf4, #dcfce7);"
        "border:2px solid #86efac;border-radius:14px;padding:20px;"
        "margin-bottom:16px;'>"
        "<div style='display:flex;justify-content:space-between;"
        "align-items:center;flex-wrap:wrap;'>"
        "<div>"
        "<div style='font-size:1.8em;font-weight:800;color:#166534;'>"
        "{icon} {name}</div>"
        "<div style='font-size:0.95em;color:#059669;margin-top:4px;'>"
        "{xp:,} XP &bull; {streak} day streak &bull; {mult:.1f}x multiplier"
        "</div></div>"
        "<div style='text-align:right;'>"
        "<div style='font-size:2em;font-weight:800;color:#059669;'>"
        "{xp:,}</div>"
        "<div style='font-size:0.8em;color:#6b7280;'>Total XP</div>"
        "</div></div>"
        "<div style='margin-top:14px;'>"
        "<div style='display:flex;justify-content:space-between;"
        "font-size:0.82em;color:#6b7280;margin-bottom:4px;'>"
        "<span>{cur_name}</span>"
        "<span>{pct}% to {nxt}</span>"
        "</div>"
        "<div style='background:#d1fae5;border-radius:6px;height:12px;'>"
        "<div style='background:linear-gradient(90deg, #059669, #10b981);"
        "width:{pct}%;height:100%;border-radius:6px;"
        "transition:width 0.3s;'></div>"
        "</div></div></div>".format(
            icon=current_lv["icon"], name=current_lv["name"],
            xp=total_xp, streak=current_streak, mult=multiplier,
            cur_name=current_lv["name"], pct=pbar_pct, nxt=next_label,
        ),
        unsafe_allow_html=True,
    )

    # -- Placement Result Card (if completed) ------------------------------
    if has_placement:
        p_level = placement_data.get("assigned_level", "")
        p_score = placement_data.get("total_score", 0)
        strengths = placement_data.get("detected_strengths", [])
        strengths_str = ", ".join(strengths) if strengths else "N/A"
        st.markdown(
            "<div style='background:#eff6ff;border:1px solid #93c5fd;"
            "border-radius:10px;padding:14px 18px;margin-bottom:16px;'>"
            "<div style='font-weight:700;color:#1e40af;font-size:1em;'>"
            "Placement Result</div>"
            "<div style='display:flex;gap:24px;margin-top:8px;flex-wrap:wrap;'>"
            "<div><span style='font-size:0.82em;color:#6b7280;'>"
            "Assigned Level</span><br/>"
            "<span style='font-weight:700;font-size:1.1em;color:#1e40af;'>"
            "{level}</span></div>"
            "<div><span style='font-size:0.82em;color:#6b7280;'>"
            "Score</span><br/>"
            "<span style='font-weight:700;font-size:1.1em;color:#1e40af;'>"
            "{score}</span></div>"
            "<div><span style='font-size:0.82em;color:#6b7280;'>"
            "Strengths</span><br/>"
            "<span style='font-size:0.95em;color:#B0BEC5;'>"
            "{strengths}</span></div>"
            "</div></div>".format(
                level=p_level, score=p_score, strengths=strengths_str,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # -- Module Completion Grid --------------------------------------------
    st.markdown("### Module Completion")

    col_l, col_d = st.columns(2)

    with col_l:
        series_info_l = SERIES_INFO["L"]
        st.markdown(
            "<div style='font-weight:700;font-size:1.1em;color:{};"
            "margin-bottom:8px;'>"
            "L-Series: {}</div>".format(
                series_info_l["colour"], series_info_l["name"],
            ),
            unsafe_allow_html=True,
        )
        for mod in L_MODULES:
            code = mod["code"]
            status = _module_status(code, pmap)
            best = _best_score(code, pmap)
            tier_info = None
            if status != "locked":
                tier_info = _load_adaptive(code)
            _render_module_card(
                mod, status, best, tier_info=tier_info,
                key_suffix="progress_l",
            )

    with col_d:
        series_info_d = SERIES_INFO["D"]
        st.markdown(
            "<div style='font-weight:700;font-size:1.1em;color:{};"
            "margin-bottom:8px;'>"
            "D-Series: {}</div>".format(
                series_info_d["colour"], series_info_d["name"],
            ),
            unsafe_allow_html=True,
        )
        for mod in D_MODULES:
            code = mod["code"]
            status = _module_status(code, pmap)
            best = _best_score(code, pmap)
            tier_info = None
            if status != "locked":
                tier_info = _load_adaptive(code)
            _render_module_card(
                mod, status, best, tier_info=tier_info,
                key_suffix="progress_d",
            )

    st.markdown("---")

    # -- Mindset Growth Chart ----------------------------------------------
    st.markdown("### Mindset Growth")
    mindset_data = _load_mindset()
    if mindset_data:
        indicators = ["first_instinct", "scope", "ambition", "breadth"]
        indicator_labels = {
            "first_instinct": "First Instinct",
            "scope": "Scope of Thinking",
            "ambition": "Ambition Level",
            "breadth": "Breadth of Application",
        }
        st.markdown(
            "<div style='background:#faf5ff;border:1px solid #d8b4fe;"
            "border-radius:10px;padding:16px;margin-bottom:12px;'>",
            unsafe_allow_html=True,
        )
        for ind in indicators:
            label = indicator_labels.get(ind, ind)
            scores_over_time = []
            for assess in mindset_data:
                s = assess.get("scores", {})
                val = s.get(ind, 0)
                scores_over_time.append(val)
            if scores_over_time:
                latest = scores_over_time[-1]
                trend = ""
                if len(scores_over_time) > 1:
                    diff = latest - scores_over_time[-2]
                    if diff > 0:
                        trend = " (+{})".format(diff)
                    elif diff < 0:
                        trend = " ({})".format(diff)
                bar_pct = min(int(latest / 10 * 100), 100)
                bar_col = "#7c3aed" if latest >= 7 else ("#d97706" if latest >= 4 else "#6b7280")
                st.markdown(
                    "<div style='margin:8px 0;'>"
                    "<div style='display:flex;justify-content:space-between;"
                    "font-size:0.88em;'>"
                    "<span>{label}</span>"
                    "<span style='font-weight:600;color:{col};'>"
                    "{val}/10{trend}</span></div>"
                    "<div style='background:#e9d5ff;border-radius:4px;"
                    "height:8px;margin-top:3px;'>"
                    "<div style='background:{col};width:{pct}%;"
                    "height:100%;border-radius:4px;'></div>"
                    "</div></div>".format(
                        label=label, col=bar_col, val=latest,
                        trend=trend, pct=bar_pct,
                    ),
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.caption(
            "No mindset assessments yet. These are auto-triggered as you "
            "progress through modules."
        )

    st.markdown("---")

    # -- Recent XP Activity ------------------------------------------------
    st.markdown("### Recent Activity")
    recent = profile.get("recent_activity", []) if profile else []
    if recent:
        action_icons = {
            "login": "&#128075;",
            "module_complete": "&#128218;",
            "daily_challenge": "&#128197;",
            "badge_earned": "&#127941;",
            "prompt_score_high": "&#128142;",
            "prompt_score_medium": "&#128221;",
            "quality_review": "&#128207;",
            "assessment_pass": "&#9989;",
            "assessment_attempt": "&#9997;",
            "exercise_complete": "&#128170;",
            "placement_complete": "&#127919;",
            "battle_won": "&#9876;",
            "micro_challenge": "&#9889;",
        }
        for act in recent[:10]:
            act_type = act.get("action_type", "")
            icon = action_icons.get(act_type, "&#10024;")
            desc = act.get("description", act_type)
            xp_amt = act.get("xp_amount", 0)
            date_str = act.get("created_at", "")[:10]
            st.markdown(
                "<div style='display:flex;align-items:center;gap:10px;"
                "padding:6px 0;border-bottom:1px solid #f1f5f9;"
                "font-size:0.9em;'>"
                "<span>{icon}</span>"
                "<span style='flex:1;'>{desc}</span>"
                "<span style='color:#059669;font-weight:600;'>"
                "+{xp} XP</span>"
                "<span style='color:#94a3b8;font-size:0.8em;'>"
                "{date}</span>"
                "</div>".format(
                    icon=icon, desc=desc, xp=xp_amt, date=date_str,
                ),
                unsafe_allow_html=True,
            )
    else:
        st.caption(
            "No activity yet. Complete a module or daily challenge to get started!"
        )

    st.markdown("---")

    # -- Badge Gallery -----------------------------------------------------
    st.markdown("### Badges")
    badges_data = _load_badges()
    earned = badges_data.get("earned", []) if badges_data else []
    locked = badges_data.get("locked", []) if badges_data else []
    total_earned = badges_data.get("total_earned", 0) if badges_data else 0
    total_available = badges_data.get("total_available", 0) if badges_data else 0

    st.caption("{} / {} badges earned".format(total_earned, total_available))

    if earned:
        num_cols = min(len(earned), 6)
        if num_cols > 0:
            badge_cols = st.columns(num_cols)
            for i, b in enumerate(earned[:12]):
                with badge_cols[i % num_cols]:
                    b_icon = b.get("badge_icon", "")
                    b_name = b.get("badge_name", "")
                    st.markdown(
                        "<div style='text-align:center;padding:8px;"
                        "background:rgba(46,204,113,0.08);border-radius:10px;"
                        "border:1px solid #bbf7d0;margin-bottom:8px;'>"
                        "<div style='font-size:1.6em;'>{}</div>"
                        "<div style='font-weight:600;font-size:0.82em;'>"
                        "{}</div></div>".format(b_icon, b_name),
                        unsafe_allow_html=True,
                    )

    if locked:
        with st.expander("Locked badges ({})".format(len(locked))):
            num_lock = min(len(locked), 6)
            if num_lock > 0:
                lock_cols = st.columns(num_lock)
                for i, b in enumerate(locked[:18]):
                    with lock_cols[i % num_lock]:
                        st.markdown(
                            "<div style='text-align:center;padding:8px;"
                            "background:#f1f5f9;border-radius:10px;"
                            "border:1px solid #e2e8f0;margin-bottom:8px;"
                            "opacity:0.5;'>"
                            "<div style='font-size:1.6em;'>&#128274;</div>"
                            "<div style='font-weight:600;font-size:0.82em;"
                            "color:#94a3b8;'>{}</div>"
                            "<div style='font-size:0.72em;color:#94a3b8;'>"
                            "{}</div></div>".format(
                                b.get("name", ""), b.get("desc", ""),
                            ),
                            unsafe_allow_html=True,
                        )


# ============================================================================
# TAB 1: PLACEMENT CHALLENGE
# ============================================================================

with tabs[1]:
    st.markdown("### Placement Challenge")

    if has_placement:
        # Already completed -- show results
        st.success("You have already completed the Placement Challenge!")

        p_level = placement_data.get("assigned_level", "N/A")
        p_score = placement_data.get("total_score", 0)
        p_responses = placement_data.get("responses", [])
        strengths = placement_data.get("detected_strengths", [])

        st.markdown(
            "<div style='background:linear-gradient(135deg, #eff6ff, #dbeafe);"
            "border:2px solid #60a5fa;border-radius:14px;padding:24px;"
            "text-align:center;margin-bottom:20px;'>"
            "<div style='font-size:1.5em;font-weight:800;color:#1e40af;'>"
            "Assigned Level: {level}</div>"
            "<div style='font-size:2em;font-weight:800;color:#2563eb;"
            "margin-top:8px;'>{score}</div>"
            "<div style='font-size:0.9em;color:#3b82f6;margin-top:4px;'>"
            "Total Placement Score</div>"
            "</div>".format(level=p_level, score=p_score),
            unsafe_allow_html=True,
        )

        if strengths:
            st.markdown("**Detected Strengths:**")
            for s in strengths:
                st.markdown("- {}".format(s))

        if p_responses:
            st.markdown("**Per-Scenario Scores:**")
            for i, resp in enumerate(p_responses):
                sc_score = resp.get("score", 0)
                sc_id = resp.get("scenario_id", "Scenario {}".format(i + 1))
                bar_col = "#22c55e" if sc_score >= 8 else ("#eab308" if sc_score >= 5 else "#ef4444")
                bar_pct = min(int(sc_score / 10 * 100), 100)
                st.markdown(
                    "<div style='display:flex;align-items:center;gap:12px;"
                    "margin:6px 0;'>"
                    "<span style='width:100px;font-size:0.9em;'>{sid}</span>"
                    "<div style='flex:1;background:#e2e8f0;border-radius:4px;"
                    "height:10px;'>"
                    "<div style='background:{col};width:{pct}%;"
                    "height:100%;border-radius:4px;'></div></div>"
                    "<span style='font-weight:700;color:{col};width:40px;"
                    "text-align:right;'>{sc}</span>"
                    "</div>".format(
                        sid=sc_id, col=bar_col, pct=bar_pct, sc=sc_score,
                    ),
                    unsafe_allow_html=True,
                )

    else:
        # Placement flow -- session-state driven
        st.markdown(
            "Take 5 real-world AI scenarios and respond with your best prompt. "
            "Your responses will be scored to determine your starting level."
        )
        st.markdown(
            "<div style='background:#fef3c7;border:1px solid #fbbf24;"
            "border-radius:8px;padding:10px 14px;font-size:0.9em;"
            "margin-bottom:16px;'>"
            "Estimated time: <strong>10 minutes</strong> &bull; "
            "5 scenarios &bull; Scored automatically"
            "</div>",
            unsafe_allow_html=True,
        )

        # Initialise placement state
        if "sa_placement_step" not in st.session_state:
            st.session_state["sa_placement_step"] = 0
        if "sa_placement_responses" not in st.session_state:
            st.session_state["sa_placement_responses"] = []
        if "sa_placement_scenarios" not in st.session_state:
            scenarios_resp = _api_get("/placement/scenarios")
            if scenarios_resp and isinstance(scenarios_resp, dict):
                st.session_state["sa_placement_scenarios"] = scenarios_resp.get(
                    "scenarios", []
                )
            else:
                st.session_state["sa_placement_scenarios"] = []
        if "sa_placement_start_time" not in st.session_state:
            st.session_state["sa_placement_start_time"] = None
        if "sa_placement_submitted" not in st.session_state:
            st.session_state["sa_placement_submitted"] = False

        scenarios = st.session_state["sa_placement_scenarios"]
        step = st.session_state["sa_placement_step"]
        submitted = st.session_state["sa_placement_submitted"]

        if not scenarios:
            st.warning(
                "Could not load placement scenarios. Please try refreshing the page."
            )
        elif submitted:
            # Show the submission result
            result = st.session_state.get("sa_placement_result")
            if result:
                st.balloons()
                r_level = result.get("assigned_level", "N/A")
                r_score = result.get("total_score", 0)
                r_strengths = result.get("detected_strengths", [])
                st.markdown(
                    "<div style='background:linear-gradient(135deg, #f0fdf4, #dcfce7);"
                    "border:2px solid #22c55e;border-radius:14px;padding:24px;"
                    "text-align:center;margin-bottom:20px;'>"
                    "<div style='font-size:1.3em;font-weight:700;color:#166534;'>"
                    "Placement Complete!</div>"
                    "<div style='font-size:2em;font-weight:800;color:#059669;"
                    "margin-top:8px;'>Level: {level}</div>"
                    "<div style='font-size:1.2em;color:#059669;margin-top:4px;'>"
                    "Score: {score}</div>"
                    "</div>".format(level=r_level, score=r_score),
                    unsafe_allow_html=True,
                )
                if r_strengths:
                    st.markdown("**Your detected strengths:**")
                    for s in r_strengths:
                        st.markdown("- {}".format(s))

                if st.button(
                    "Start Learning",
                    key="sa_placement_start_learning",
                    type="primary",
                    use_container_width=True,
                ):
                    # Clear placement cache so it reloads
                    st.session_state.pop("sa_placement", None)
                    st.session_state.pop("sa_placement_submitted", None)
                    st.session_state.pop("sa_placement_step", None)
                    st.session_state.pop("sa_placement_responses", None)
                    st.session_state.pop("sa_placement_result", None)
                    st.session_state.pop("sa_placement_scenarios", None)
                    st.session_state.pop("sa_placement_start_time", None)
                    st.rerun()
            else:
                st.error("Submission failed. Please try again.")
                if st.button("Retry", key="sa_placement_retry"):
                    st.session_state["sa_placement_submitted"] = False
                    st.rerun()

        elif step < len(scenarios):
            # Show current scenario
            scenario = scenarios[step]
            sc_title = scenario.get("title", "Scenario {}".format(step + 1))
            sc_icon = scenario.get("icon", "")
            sc_instruction = scenario.get("instruction", "")
            sc_reference = scenario.get("reference_material", "")
            sc_id = scenario.get("id", "scenario_{}".format(step + 1))

            # Start timer if not started
            if st.session_state["sa_placement_start_time"] is None:
                st.session_state["sa_placement_start_time"] = time.time()

            # Progress indicator
            st.progress(
                (step + 1) / len(scenarios),
                text="Scenario {} of {}".format(step + 1, len(scenarios)),
            )

            # Timer display
            elapsed = int(time.time() - st.session_state["sa_placement_start_time"])
            mins = elapsed // 60
            secs = elapsed % 60
            st.markdown(
                "<div style='text-align:right;font-size:0.85em;color:#6b7280;'>"
                "Time elapsed: {}:{:02d}</div>".format(mins, secs),
                unsafe_allow_html=True,
            )

            # Scenario card
            st.markdown(
                "<div style='background:#f8fafc;border:1px solid #e2e8f0;"
                "border-radius:12px;padding:20px;margin-bottom:16px;'>"
                "<div style='font-size:1.3em;font-weight:700;color:#1e293b;'>"
                "{icon} {title}</div>"
                "<div style='font-size:0.95em;color:#B0BEC5;margin-top:12px;"
                "line-height:1.7;'>{instruction}</div>"
                "</div>".format(
                    icon=sc_icon, title=sc_title, instruction=sc_instruction,
                ),
                unsafe_allow_html=True,
            )

            if sc_reference:
                with st.expander("Reference Material"):
                    st.markdown(sc_reference)

            # Response text area
            response_key = "sa_placement_response_{}".format(step)
            response_text = st.text_area(
                "Your response:",
                height=200,
                key=response_key,
                placeholder="Write your best response to this scenario...",
            )

            # Navigation
            col_prev, col_spacer, col_next = st.columns([1, 2, 1])

            with col_prev:
                if step > 0:
                    if st.button("Previous", key="sa_placement_prev"):
                        st.session_state["sa_placement_step"] = step - 1
                        st.rerun()

            with col_next:
                is_last = step == len(scenarios) - 1
                btn_label = "Submit All" if is_last else "Next Scenario"
                btn_disabled = not response_text or len(response_text.strip()) < 10

                if st.button(
                    btn_label,
                    key="sa_placement_next",
                    type="primary",
                    disabled=btn_disabled,
                ):
                    # Record timing
                    scenario_time = int(
                        time.time()
                        - st.session_state["sa_placement_start_time"]
                    )

                    # Save response
                    responses = st.session_state["sa_placement_responses"]
                    # Replace if going back and forth
                    if step < len(responses):
                        responses[step] = {
                            "scenario_id": sc_id,
                            "response": response_text.strip(),
                            "score": 0,
                            "time_seconds": scenario_time,
                        }
                    else:
                        responses.append({
                            "scenario_id": sc_id,
                            "response": response_text.strip(),
                            "score": 0,
                            "time_seconds": scenario_time,
                        })
                    st.session_state["sa_placement_responses"] = responses

                    if is_last:
                        # Submit all
                        with st.spinner("Submitting placement..."):
                            result = _api_post(
                                "/placement/submit",
                                json_body={
                                    "user_id": uid,
                                    "responses": responses,
                                },
                            )
                        if result:
                            st.session_state["sa_placement_result"] = result
                            st.session_state["sa_placement_submitted"] = True
                            st.session_state.pop("sa_placement", None)
                            st.session_state.pop("sa_profile", None)
                        else:
                            st.error("Submission failed. Please try again.")
                    else:
                        st.session_state["sa_placement_step"] = step + 1
                        st.session_state["sa_placement_start_time"] = time.time()

                    st.rerun()

        else:
            st.info("All scenarios complete. Click Submit to see your results.")


# ============================================================================
# MODULE CONTENT RENDERER (shared by L-Series and D-Series)
# ============================================================================

def _render_module_content(mod, status, pmap, tab_prefix):
    """Render the sub-tabs: Theory | Examples | Exercise | Assessment."""
    code = mod["code"]

    if status == "locked":
        prereqs = mod["prerequisites"]
        prereq_names = ", ".join(prereqs)
        st.warning(
            "This module is locked. Complete prerequisite(s): " + prereq_names
        )
        return

    # Load adaptive tier
    adaptive = _load_adaptive(code)
    current_tier = adaptive.get("current_tier", "Standard")
    consecutive_elite = adaptive.get("consecutive_elite", 0)
    skip_eligible = adaptive.get("skip_ahead_eligible", False)

    # Tier display
    st.markdown(
        "<div style='display:flex;align-items:center;gap:12px;"
        "padding:8px 14px;background:#f8fafc;border-radius:8px;"
        "margin-bottom:16px;'>"
        "<span style='font-size:0.9em;color:#B0BEC5;'>Current Tier:</span>"
        "{badge}"
        "<span style='font-size:0.82em;color:#6b7280;'>"
        "({elite} consecutive elite scores)</span>"
        "</div>".format(
            badge=_render_tier_badge(current_tier),
            elite=consecutive_elite,
        ),
        unsafe_allow_html=True,
    )

    sub_tabs = st.tabs([
        "Theory", "Examples", "Exercise", "Assessment",
    ])

    # -- Theory -----------------------------------------------------------
    with sub_tabs[0]:
        theory_sections = mod.get("theory", [])
        if not theory_sections:
            st.info("Theory content is coming soon for this module.")
        else:
            for i, section in enumerate(theory_sections):
                section_title = section.get(
                    "title", "Section {}".format(i + 1)
                )
                with st.expander(section_title, expanded=(i == 0)):
                    st.markdown(
                        section.get("body", ""), unsafe_allow_html=False,
                    )

    # -- Examples ---------------------------------------------------------
    with sub_tabs[1]:
        examples = mod.get("examples", [])
        if not examples:
            st.info("Examples are coming soon for this module.")
        else:
            for i, ex in enumerate(examples):
                st.markdown("**Example {}**".format(i + 1))
                col_weak, col_strong = st.columns(2)
                with col_weak:
                    st.markdown(
                        "<div style='background:#fef2f2;border-left:4px solid "
                        "#ef4444;padding:12px 16px;border-radius:0 8px 8px 0;"
                        "margin-bottom:8px;'>"
                        "<div style='font-weight:600;color:#b91c1c;"
                        "font-size:0.85em;margin-bottom:4px;'>Weak Prompt</div>"
                        "<div style='font-size:0.95em;'>{}</div>"
                        "</div>".format(ex.get("weak", "")),
                        unsafe_allow_html=True,
                    )
                with col_strong:
                    st.markdown(
                        "<div style='background:rgba(46,204,113,0.08);border-left:4px solid "
                        "#22c55e;padding:12px 16px;border-radius:0 8px 8px 0;"
                        "margin-bottom:8px;'>"
                        "<div style='font-weight:600;color:#166534;"
                        "font-size:0.85em;margin-bottom:4px;'>Strong Prompt</div>"
                        "<div style='font-size:0.95em;'>{}</div>"
                        "</div>".format(ex.get("strong", "")),
                        unsafe_allow_html=True,
                    )
                expl = ex.get("explanation", "")
                if expl:
                    st.caption(expl)
                if i < len(examples) - 1:
                    st.markdown("---")

    # -- Exercise (Adaptive) -----------------------------------------------
    with sub_tabs[2]:
        exercises = ADAPTIVE_EXERCISES.get(code, {})
        tier_key = current_tier.lower()
        exercise_data = exercises.get(tier_key, exercises.get("standard", {}))

        if not exercise_data:
            st.info("Exercise content is coming soon for this module.")
        else:
            st.markdown(
                "<div style='display:flex;align-items:center;gap:10px;"
                "margin-bottom:12px;'>"
                "<span style='font-size:0.95em;font-weight:600;'>"
                "Exercise Tier:</span>"
                "{badge}</div>".format(
                    badge=_render_tier_badge(current_tier),
                ),
                unsafe_allow_html=True,
            )

            st.markdown("**Instructions:**")
            st.markdown(exercise_data.get("instruction", ""))

            scenario_text = exercise_data.get("scenario", "")
            if scenario_text:
                st.markdown(
                    "<div style='background:#f0f9ff;border-left:4px solid "
                    "#3b82f6;padding:12px 16px;border-radius:0 8px 8px 0;"
                    "margin:12px 0;'>"
                    "<div style='font-weight:600;color:#1e40af;"
                    "font-size:0.85em;margin-bottom:4px;'>Scenario</div>"
                    "<div style='font-size:0.95em;'>{}</div>"
                    "</div>".format(scenario_text),
                    unsafe_allow_html=True,
                )

            exercise_key = "sa_exercise_{}_{}".format(tab_prefix, code)
            exercise_text = st.text_area(
                "Your response:",
                height=180,
                key=exercise_key,
                placeholder="Write your response to this exercise...",
            )

            submit_key = "sa_exercise_submit_{}_{}".format(tab_prefix, code)
            if st.button(
                "Submit Exercise",
                key=submit_key,
                type="primary",
                use_container_width=True,
                disabled=(
                    not exercise_text or len(exercise_text.strip()) < 20
                ),
            ):
                with st.spinner("Evaluating your exercise..."):
                    # Score via assessment endpoint
                    score_result = _api_post(
                        "/assessment/submit",
                        json_body={
                            "user_id": uid,
                            "module_code": code,
                            "prompt_text": exercise_text.strip(),
                        },
                    )

                if score_result and score_result.get("total") is not None:
                    total = score_result["total"]
                    score_pct = total / MAX_SCORE * 100

                    # Show result
                    verdict_col = "#22c55e" if total >= PASS_THRESHOLD else "#ef4444"
                    st.markdown(
                        "<div style='text-align:center;margin:16px 0;'>"
                        "<div style='font-size:2em;font-weight:800;"
                        "color:{};'>{}/{}</div>"
                        "</div>".format(verdict_col, total, MAX_SCORE),
                        unsafe_allow_html=True,
                    )
                    _render_score_bars(score_result)

                    feedback = score_result.get("feedback", "")
                    if feedback:
                        st.info(feedback)

                    # Update adaptive tier
                    with st.spinner("Updating adaptive tier..."):
                        tier_result = _api_post(
                            "/adaptive/update",
                            json_body={
                                "user_id": uid,
                                "module_code": code,
                                "score_pct": score_pct,
                            },
                        )

                    if tier_result:
                        new_tier = tier_result.get("current_tier", current_tier)
                        tier_changed = tier_result.get("tier_changed", False)
                        skip_now = tier_result.get(
                            "skip_ahead_eligible", False,
                        )

                        if tier_changed:
                            if new_tier == "Elite":
                                st.balloons()
                                st.success(
                                    "Tier upgraded to Elite! Outstanding work!"
                                )
                            elif new_tier == "Stretch":
                                st.success(
                                    "Tier upgraded to Stretch! Keep pushing!"
                                )
                            else:
                                st.info(
                                    "Tier adjusted to {}. "
                                    "Keep practising!".format(new_tier)
                                )

                        if skip_now:
                            st.markdown(
                                "<div style='background:#faf5ff;"
                                "border:2px solid #a78bfa;"
                                "border-radius:10px;padding:14px;"
                                "margin-top:12px;'>"
                                "<div style='font-weight:700;"
                                "color:#5b21b6;'>Skip Ahead Eligible!</div>"
                                "<div style='font-size:0.9em;"
                                "color:#6d28d9;margin-top:4px;'>"
                                "You scored Elite 3 times in a row. "
                                "You can skip to the next module!"
                                "</div></div>",
                                unsafe_allow_html=True,
                            )

                    # Clear cached progress
                    st.session_state.pop("sa_progress", None)
                    st.session_state.pop("sa_profile", None)
                else:
                    st.error(
                        "Could not score your exercise. "
                        "Please try again in a moment."
                    )

            # Skip-ahead option
            if skip_eligible or consecutive_elite >= 3:
                st.markdown("---")
                st.markdown("#### Skip Ahead")

                # Determine next module
                all_mods = L_MODULES if mod["series"] == "L" else D_MODULES
                cur_idx = next(
                    (i for i, m in enumerate(all_mods) if m["code"] == code),
                    -1,
                )
                if cur_idx >= 0 and cur_idx < len(all_mods) - 1:
                    next_mod = all_mods[cur_idx + 1]
                    st.markdown(
                        "You can attempt to skip ahead to **{}: {}**. "
                        "Write a response to the skip-ahead challenge below.".format(
                            next_mod["code"], next_mod["name"],
                        )
                    )

                    skip_text_key = "sa_skip_{}_{}".format(
                        tab_prefix, code,
                    )
                    skip_text = st.text_area(
                        "Skip-ahead response:",
                        height=180,
                        key=skip_text_key,
                        placeholder=(
                            "Demonstrate mastery of both this module and "
                            "the next..."
                        ),
                    )

                    skip_btn_key = "sa_skip_btn_{}_{}".format(
                        tab_prefix, code,
                    )
                    if st.button(
                        "Attempt Skip Ahead",
                        key=skip_btn_key,
                        disabled=(
                            not skip_text
                            or len(skip_text.strip()) < 20
                        ),
                    ):
                        with st.spinner("Evaluating skip-ahead..."):
                            skip_result = _api_post(
                                "/skip-ahead",
                                json_body={
                                    "user_id": uid,
                                    "from_module": code,
                                    "to_module": next_mod["code"],
                                    "response": skip_text.strip(),
                                },
                            )
                        if skip_result:
                            skip_score = skip_result.get("score", 0)
                            skip_passed = skip_result.get("passed", False)
                            if skip_passed:
                                st.balloons()
                                st.success(
                                    "Skip successful! Score: {}. "
                                    "You can now access {}.".format(
                                        skip_score, next_mod["code"],
                                    )
                                )
                                st.session_state.pop("sa_progress", None)
                                st.session_state.pop("sa_profile", None)
                            else:
                                st.warning(
                                    "Score: {}. Not quite enough to skip. "
                                    "Keep working through the current "
                                    "module.".format(skip_score)
                                )
                        else:
                            st.error("Skip-ahead evaluation failed.")
                else:
                    st.caption(
                        "You are on the final module in this series. "
                        "No skip-ahead available."
                    )

    # -- Assessment -------------------------------------------------------
    with sub_tabs[3]:
        assessment = mod.get("assessment")
        if not assessment:
            st.info("Assessment is coming soon for this module.")
            return

        st.markdown("**Assessment Instructions:**")
        st.markdown(assessment.get("instructions", ""))

        st.markdown(
            "<div style='background:#fef3c7;border:1px solid #fbbf24;"
            "border-radius:8px;padding:10px 14px;margin:12px 0;"
            "font-size:0.9em;'>"
            "Pass threshold: <strong>{}/{}</strong> &bull; "
            "Scored on 5 criteria (Clarity, Context, Data Spec, "
            "Format, Actionability)."
            "</div>".format(PASS_THRESHOLD, MAX_SCORE),
            unsafe_allow_html=True,
        )

        text_key = "sa_assessment_text_{}_{}".format(tab_prefix, code)
        prompt_text = st.text_area(
            "Write your prompt here:",
            height=200,
            key=text_key,
            placeholder=(
                "Write a detailed prompt using your actual Harris Farm role "
                "and a realistic business scenario..."
            ),
        )

        score_key = "sa_score_btn_{}_{}".format(tab_prefix, code)
        if st.button(
            "Score My Prompt",
            key=score_key,
            type="primary",
            use_container_width=True,
            disabled=(not prompt_text or len(prompt_text.strip()) < 20),
        ):
            with st.spinner("Evaluating your prompt..."):
                result = _api_post(
                    "/assessment/submit",
                    json_body={
                        "user_id": uid,
                        "module_code": code,
                        "prompt_text": prompt_text.strip(),
                    },
                )

            if result and result.get("total") is not None:
                total = result["total"]
                passed = total >= PASS_THRESHOLD

                # Radar chart
                st.plotly_chart(
                    _render_radar_chart(
                        result,
                        "Your Score: {}/{}".format(total, MAX_SCORE),
                    ),
                    use_container_width=True,
                )

                # Per-criterion breakdown
                st.markdown("**Score Breakdown:**")
                _render_score_bars(result)

                # Total + verdict
                verdict_col = "#22c55e" if passed else "#ef4444"
                verdict_text = "PASS" if passed else "NEEDS IMPROVEMENT"
                st.markdown(
                    "<div style='text-align:center;margin:16px 0;'>"
                    "<div style='font-size:2em;font-weight:800;color:{};'>"
                    "{}/{}</div>"
                    "<div style='font-size:1.2em;font-weight:700;color:{};'>"
                    "{}</div></div>".format(
                        verdict_col, total, MAX_SCORE,
                        verdict_col, verdict_text,
                    ),
                    unsafe_allow_html=True,
                )

                # Feedback
                feedback = result.get("feedback", "")
                if feedback:
                    st.markdown("**Feedback:**")
                    st.info(feedback)

                # Improved prompt
                improved = result.get("improved_prompt", "")
                if improved:
                    with st.expander("View improved prompt (23+ score version)"):
                        st.markdown(
                            "<div style='background:rgba(46,204,113,0.08);border-left:4px "
                            "solid #22c55e;padding:12px 16px;border-radius:"
                            "0 8px 8px 0;'>{}</div>".format(improved),
                            unsafe_allow_html=True,
                        )

                # Celebration on pass
                if passed:
                    st.balloons()
                    st.success(
                        "Congratulations! You passed {} with {}/{}! "
                        "Your progress has been saved.".format(
                            code, total, MAX_SCORE,
                        )
                    )
                    st.session_state.pop("sa_progress", None)
                    st.session_state.pop("sa_profile", None)
            else:
                st.error(
                    "Could not score your prompt. "
                    "Please try again in a moment."
                )

        # Attempt history
        st.markdown("---")
        st.markdown("**Attempt History**")
        hist_data = _api_get(
            "/assessment/{}/{}".format(uid, code)
        )
        if hist_data:
            results_list = hist_data.get("assessments", [])
            if not results_list:
                results_list = hist_data.get("results", [])
        else:
            results_list = []

        if results_list:
            for idx, att in enumerate(reversed(results_list)):
                att_total = att.get("total", 0)
                att_passed = att_total >= PASS_THRESHOLD
                att_date = att.get("created_at", "")[:16]
                with st.expander(
                    "Attempt {} -- {}/{}  {}  ({})".format(
                        len(results_list) - idx, att_total, MAX_SCORE,
                        "Pass" if att_passed else "Fail", att_date,
                    )
                ):
                    st.plotly_chart(
                        _render_radar_chart(
                            att,
                            "Attempt {}: {}/{}".format(
                                len(results_list) - idx,
                                att_total, MAX_SCORE,
                            ),
                        ),
                        use_container_width=True,
                        key="sa_hist_{}_{}_{}_{}".format(
                            tab_prefix, code, idx, att_total,
                        ),
                    )
                    att_feedback = att.get("feedback", "")
                    if att_feedback:
                        st.caption(att_feedback)
        else:
            st.caption(
                "No attempts yet. Write a prompt above and score it!"
            )


# ============================================================================
# TAB 2: L-SERIES (Core AI Skills)
# ============================================================================

with tabs[2]:
    series_l = SERIES_INFO["L"]
    st.markdown("### L-Series: {}".format(series_l["name"]))
    st.markdown(series_l["description"])

    pmap = _progress_map()

    # Module selector
    selected_idx = st.radio(
        "Select module:",
        range(len(L_MODULES)),
        format_func=lambda i: "{}: {}".format(
            L_MODULES[i]["code"], L_MODULES[i]["name"],
        ),
        key="sa_l_series_selector",
        horizontal=True,
    )

    selected_mod = L_MODULES[selected_idx]
    sel_status = _module_status(selected_mod["code"], pmap)

    status_labels = {
        "locked": ("&#128274; Locked", "#94a3b8"),
        "available": ("&#9654; Available", BRAND_GREEN),
        "in-progress": ("&#9997; In Progress", "#eab308"),
        "passed": ("&#9989; Passed", "#22c55e"),
    }
    s_label, s_color = status_labels.get(sel_status, ("", "#6b7280"))
    best = _best_score(selected_mod["code"], pmap)
    best_str = ""
    if best is not None:
        best_str = " &bull; Best: {}/{}".format(int(best), MAX_SCORE)

    adaptive_info = _load_adaptive(selected_mod["code"])
    tier = adaptive_info.get("current_tier", "Standard")

    st.markdown(
        "<div style='display:flex;align-items:center;gap:12px;padding:8px 14px;"
        "background:#f8fafc;border-radius:8px;margin:8px 0 16px;"
        "flex-wrap:wrap;'>"
        "<span style='color:{col};font-weight:600;'>{label}</span>"
        "{tier_badge}"
        "<span style='font-size:0.85em;color:#6b7280;'>"
        "{diff} &bull; {dur} min{best}</span>"
        "</div>".format(
            col=s_color, label=s_label,
            tier_badge=_render_tier_badge(tier),
            diff=selected_mod["difficulty"].title(),
            dur=selected_mod["duration_minutes"],
            best=best_str,
        ),
        unsafe_allow_html=True,
    )

    _render_module_content(selected_mod, sel_status, pmap, "l")


# ============================================================================
# TAB 3: D-SERIES (Data + AI Skills)
# ============================================================================

with tabs[3]:
    series_d = SERIES_INFO["D"]
    st.markdown("### D-Series: {}".format(series_d["name"]))
    st.markdown(series_d["description"])

    pmap = _progress_map()

    selected_d_idx = st.radio(
        "Select module:",
        range(len(D_MODULES)),
        format_func=lambda i: "{}: {}".format(
            D_MODULES[i]["code"], D_MODULES[i]["name"],
        ),
        key="sa_d_series_selector",
        horizontal=True,
    )

    selected_d_mod = D_MODULES[selected_d_idx]
    sel_d_status = _module_status(selected_d_mod["code"], pmap)

    status_labels_d = {
        "locked": ("&#128274; Locked", "#94a3b8"),
        "available": ("&#9654; Available", BRAND_GREEN),
        "in-progress": ("&#9997; In Progress", "#eab308"),
        "passed": ("&#9989; Passed", "#22c55e"),
    }
    s_label_d, s_color_d = status_labels_d.get(sel_d_status, ("", "#6b7280"))
    best_d = _best_score(selected_d_mod["code"], pmap)
    best_d_str = ""
    if best_d is not None:
        best_d_str = " &bull; Best: {}/{}".format(int(best_d), MAX_SCORE)

    adaptive_d = _load_adaptive(selected_d_mod["code"])
    tier_d = adaptive_d.get("current_tier", "Standard")

    st.markdown(
        "<div style='display:flex;align-items:center;gap:12px;padding:8px 14px;"
        "background:#f8fafc;border-radius:8px;margin:8px 0 16px;"
        "flex-wrap:wrap;'>"
        "<span style='color:{col};font-weight:600;'>{label}</span>"
        "{tier_badge}"
        "<span style='font-size:0.85em;color:#6b7280;'>"
        "{diff} &bull; {dur} min{best}</span>"
        "</div>".format(
            col=s_color_d, label=s_label_d,
            tier_badge=_render_tier_badge(tier_d),
            diff=selected_d_mod["difficulty"].title(),
            dur=selected_d_mod["duration_minutes"],
            best=best_d_str,
        ),
        unsafe_allow_html=True,
    )

    _render_module_content(selected_d_mod, sel_d_status, pmap, "d")


# ============================================================================
# TAB 4: LEVEL 6 -- ENTERPRISE
# ============================================================================

with tabs[4]:
    st.markdown("### Level 6: Enterprise Capstone")

    # Gate check: user must have completed L5 or D4
    pmap = _progress_map()
    l5_rec = pmap.get("L5")
    d4_rec = pmap.get("D4")
    l5_passed = l5_rec and l5_rec.get("status") == "passed"
    d4_passed = d4_rec and d4_rec.get("status") == "passed"
    l6_unlocked = l5_passed or d4_passed

    if not l6_unlocked:
        st.markdown(
            "<div style='background:#fef2f2;border:2px solid #fca5a5;"
            "border-radius:12px;padding:24px;text-align:center;"
            "margin-bottom:20px;'>"
            "<div style='font-size:1.8em;margin-bottom:8px;'>&#128274;</div>"
            "<div style='font-size:1.2em;font-weight:700;color:#991b1b;'>"
            "Level 6 is Locked</div>"
            "<div style='font-size:0.95em;color:#7f1d1d;margin-top:8px;'>"
            "Complete <strong>L5</strong> or <strong>D4</strong> to unlock "
            "the Enterprise Capstone challenges.</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        # Show progress towards unlock
        st.markdown("**Progress towards unlocking:**")
        l_completed = sum(
            1 for m in L_MODULES
            if pmap.get(m["code"], {}).get("status") == "passed"
        )
        d_completed = sum(
            1 for m in D_MODULES
            if pmap.get(m["code"], {}).get("status") == "passed"
        )
        st.markdown(
            "- L-Series: {}/5 modules passed".format(l_completed)
        )
        st.markdown(
            "- D-Series: {}/5 modules passed".format(d_completed)
        )
    else:
        st.markdown(
            "Tackle real enterprise challenges facing Harris Farm's AI adoption. "
            "Each challenge is scored by a panel rubric (AI + peer + manager). "
            "Completing a challenge earns **100 XP**."
        )

        st.markdown(
            "<div style='background:#faf5ff;border:1px solid #d8b4fe;"
            "border-radius:8px;padding:10px 14px;font-size:0.9em;"
            "margin-bottom:16px;'>"
            "6 challenges &bull; Panel rubric scored &bull; 100 XP each"
            "</div>",
            unsafe_allow_html=True,
        )

        for ch_idx, challenge in enumerate(L6_ENTERPRISE_CHALLENGES):
            ch_code = challenge["code"]
            ch_name = challenge["name"]
            ch_icon = challenge.get("icon", "")
            ch_desc = challenge["description"]
            ch_brief = challenge["brief"]
            ch_xp = challenge.get("xp_reward", 100)

            with st.expander(
                "{} {}: {} (+{} XP)".format(
                    ch_icon, ch_code, ch_name, ch_xp,
                )
            ):
                st.markdown(
                    "<div style='font-size:0.95em;color:#B0BEC5;"
                    "margin-bottom:12px;'>{}</div>".format(ch_desc),
                    unsafe_allow_html=True,
                )

                st.markdown("**Brief:**")
                st.markdown(ch_brief)

                text_key = "sa_l6_text_{}".format(ch_code)
                response = st.text_area(
                    "Your response:",
                    height=250,
                    key=text_key,
                    placeholder=(
                        "Write a comprehensive response to this enterprise "
                        "challenge..."
                    ),
                )

                btn_key = "sa_l6_submit_{}".format(ch_code)
                if st.button(
                    "Submit for Panel Review",
                    key=btn_key,
                    type="primary",
                    use_container_width=True,
                    disabled=(
                        not response or len(response.strip()) < 50
                    ),
                ):
                    with st.spinner(
                        "Submitting to panel for review..."
                    ):
                        result = _api_post(
                            "/assessment/submit",
                            json_body={
                                "user_id": uid,
                                "module_code": ch_code,
                                "prompt_text": response.strip(),
                            },
                        )

                    if result and result.get("total") is not None:
                        total = result["total"]
                        passed = total >= PASS_THRESHOLD
                        verdict_col = (
                            "#22c55e" if passed else "#ef4444"
                        )

                        st.markdown(
                            "<div style='text-align:center;margin:16px 0;'>"
                            "<div style='font-size:2em;font-weight:800;"
                            "color:{};'>{}/{}</div>"
                            "<div style='font-size:1em;color:{};'>{}</div>"
                            "</div>".format(
                                verdict_col, total, MAX_SCORE,
                                verdict_col,
                                "PASS" if passed else "NEEDS MORE WORK",
                            ),
                            unsafe_allow_html=True,
                        )

                        _render_score_bars(result)

                        fb = result.get("feedback", "")
                        if fb:
                            st.info(fb)

                        if passed:
                            st.balloons()
                            st.success(
                                "Challenge complete! +{} XP earned!".format(
                                    ch_xp,
                                )
                            )
                            st.session_state.pop("sa_progress", None)
                            st.session_state.pop("sa_profile", None)
                    else:
                        st.error(
                            "Could not score your submission. "
                            "Please try again."
                        )


# ============================================================================
# TAB 5: DAILY & SOCIAL
# ============================================================================

with tabs[5]:
    st.markdown("### Daily & Social")

    social_sub = st.tabs([
        "Daily Micro-Challenge",
        "Peer Battles",
    ])

    # -- Daily Micro-Challenge ---------------------------------------------
    with social_sub[0]:
        st.markdown("#### Daily Micro-Challenge")
        st.markdown(
            "One quick-fire question every day. Answer correctly in "
            "under 90 seconds to earn XP."
        )

        daily_data = _api_get("/daily-micro")
        if daily_data and isinstance(daily_data, dict):
            challenge = daily_data.get("challenge")
        else:
            challenge = None

        if challenge:
            ch_id = challenge.get("id", "")
            ch_question = challenge.get("question", "")
            ch_options = challenge.get("options", [])
            ch_time_limit = challenge.get("time_limit", 90)
            ch_completed = challenge.get("completed", False)

            st.markdown(
                "<div style='background:#f0f9ff;border:2px solid #93c5fd;"
                "border-radius:12px;padding:20px;margin-bottom:16px;'>"
                "<div style='font-weight:700;font-size:1.1em;color:#1e40af;'>"
                "Today's Challenge</div>"
                "<div style='margin-top:10px;font-size:1.05em;color:#1e293b;"
                "line-height:1.6;'>{q}</div>"
                "<div style='margin-top:8px;font-size:0.82em;color:#6b7280;'>"
                "Time limit: {t} seconds</div>"
                "</div>".format(q=ch_question, t=ch_time_limit),
                unsafe_allow_html=True,
            )

            if ch_completed:
                st.success(
                    "You already completed today's challenge. "
                    "Come back tomorrow!"
                )
            elif ch_options:
                # Timer tracking
                timer_key = "sa_micro_start_time"
                if timer_key not in st.session_state:
                    st.session_state[timer_key] = time.time()

                elapsed = int(
                    time.time() - st.session_state[timer_key]
                )
                remaining = max(0, ch_time_limit - elapsed)

                if remaining > 0:
                    pbar_val = remaining / ch_time_limit
                    timer_col = "#22c55e" if remaining > 30 else (
                        "#eab308" if remaining > 10 else "#ef4444"
                    )
                    st.markdown(
                        "<div style='text-align:center;font-size:1.5em;"
                        "font-weight:700;color:{};margin:8px 0;'>"
                        "{}s remaining</div>".format(timer_col, remaining),
                        unsafe_allow_html=True,
                    )
                    st.progress(pbar_val)
                else:
                    st.warning("Time is up! You can still submit an answer.")

                # Answer selection
                answer_key = "sa_micro_answer"
                selected_answer = st.radio(
                    "Select your answer:",
                    ch_options,
                    key=answer_key,
                    index=None,
                )

                submit_micro_key = "sa_micro_submit"
                if st.button(
                    "Submit Answer",
                    key=submit_micro_key,
                    type="primary",
                    use_container_width=True,
                    disabled=(selected_answer is None),
                ):
                    time_taken = int(
                        time.time() - st.session_state[timer_key]
                    )
                    with st.spinner("Checking answer..."):
                        micro_result = _api_post(
                            "/daily-micro/submit",
                            json_body={
                                "user_id": uid,
                                "challenge_id": ch_id,
                                "answer": selected_answer,
                                "time_seconds": time_taken,
                            },
                        )

                    if micro_result:
                        is_correct = micro_result.get("is_correct", False)
                        correct_ans = micro_result.get(
                            "correct_answer", ""
                        )

                        if is_correct:
                            st.balloons()
                            st.success(
                                "Correct! Well done!"
                            )
                        else:
                            st.error(
                                "Not quite. The correct answer was: "
                                "{}".format(correct_ans)
                            )

                        # Clear timer
                        st.session_state.pop(timer_key, None)
                        st.session_state.pop("sa_profile", None)
                    else:
                        st.error("Could not submit answer. Try again.")
            else:
                st.info("No options available for this challenge.")
        else:
            st.info(
                "No daily micro-challenge available right now. "
                "Check back tomorrow!"
            )

    # -- Peer Battles ------------------------------------------------------
    with social_sub[1]:
        st.markdown("#### Peer Battles")
        st.markdown(
            "Challenge your colleagues! Write a prompt for a scenario and "
            "see who scores higher."
        )

        battle_mode = st.radio(
            "Action:",
            ["Create a Battle", "Join Open Battles", "My Battle Stats"],
            key="sa_battle_mode",
            horizontal=True,
        )

        if battle_mode == "Create a Battle":
            st.markdown("##### Create a New Battle")
            st.markdown(
                "Write a scenario and your best prompt. "
                "Another team member will compete against you."
            )

            scenario_key = "sa_battle_scenario"
            prompt_key = "sa_battle_prompt"

            battle_scenario = st.text_area(
                "Scenario (the AI challenge):",
                height=100,
                key=scenario_key,
                placeholder=(
                    "E.g., Write a prompt to analyse fresh produce waste "
                    "across Sydney stores for last month..."
                ),
            )
            battle_prompt = st.text_area(
                "Your prompt (your best answer):",
                height=150,
                key=prompt_key,
                placeholder="Write your strongest prompt for this scenario...",
            )

            if st.button(
                "Create Battle",
                key="sa_battle_create_btn",
                type="primary",
                use_container_width=True,
                disabled=(
                    not battle_scenario
                    or not battle_prompt
                    or len(battle_scenario.strip()) < 20
                    or len(battle_prompt.strip()) < 20
                ),
            ):
                with st.spinner("Creating battle..."):
                    battle_result = _api_post(
                        "/battle/create",
                        json_body={
                            "challenger_id": uid,
                            "scenario_text": battle_scenario.strip(),
                            "prompt": battle_prompt.strip(),
                        },
                    )
                if battle_result:
                    b_id = battle_result.get("id", "")
                    st.success(
                        "Battle created! ID: {}. Waiting for an "
                        "opponent to join.".format(b_id)
                    )
                else:
                    st.error("Could not create battle. Try again.")

        elif battle_mode == "Join Open Battles":
            st.markdown("##### Open Battles")

            open_battles = _api_get("/battle/open")
            if open_battles and isinstance(open_battles, dict):
                battles_list = open_battles.get("battles", [])
            else:
                battles_list = []

            if battles_list:
                for b_idx, battle in enumerate(battles_list):
                    b_id = battle.get("id", "")
                    b_scenario = battle.get("scenario_text", "")
                    b_challenger = battle.get("challenger_id", "")
                    b_created = battle.get("created_at", "")[:16]

                    # Skip own battles
                    if b_challenger == uid:
                        continue

                    challenger_name = _display_name(b_challenger)

                    st.markdown(
                        "<div style='background:#fff7ed;border:1px solid "
                        "#fed7aa;border-radius:10px;padding:14px;"
                        "margin-bottom:10px;'>"
                        "<div style='display:flex;justify-content:"
                        "space-between;'>"
                        "<span style='font-weight:600;color:#9a3412;'>"
                        "vs. {name}</span>"
                        "<span style='font-size:0.82em;color:#6b7280;'>"
                        "{date}</span></div>"
                        "<div style='margin-top:6px;font-size:0.95em;'>"
                        "{scenario}</div>"
                        "</div>".format(
                            name=challenger_name, date=b_created,
                            scenario=b_scenario,
                        ),
                        unsafe_allow_html=True,
                    )

                    join_text_key = "sa_battle_join_text_{}".format(b_id)
                    join_response = st.text_area(
                        "Your prompt response:",
                        height=120,
                        key=join_text_key,
                        placeholder="Write your best prompt for this scenario...",
                    )

                    join_btn_key = "sa_battle_join_btn_{}".format(b_id)
                    if st.button(
                        "Join Battle",
                        key=join_btn_key,
                        disabled=(
                            not join_response
                            or len(join_response.strip()) < 20
                        ),
                    ):
                        with st.spinner("Joining battle..."):
                            join_result = _api_post(
                                "/battle/{}/join".format(b_id),
                                json_body={
                                    "opponent_id": uid,
                                    "prompt": join_response.strip(),
                                },
                            )
                        if join_result:
                            winner = join_result.get("winner_id", "")
                            if winner == uid:
                                st.balloons()
                                st.success("You won the battle!")
                            elif winner:
                                winner_name = _display_name(winner)
                                st.info(
                                    "Battle complete! {} won this round.".format(
                                        winner_name,
                                    )
                                )
                            else:
                                st.info("Battle complete! It was a draw.")
                            st.session_state.pop("sa_profile", None)
                        else:
                            st.error("Could not join battle. Try again.")

                    st.markdown("---")
            else:
                st.info(
                    "No open battles right now. Create one to challenge "
                    "your teammates!"
                )

        else:
            # Battle stats
            st.markdown("##### My Battle Stats")
            profile = _load_profile()
            battle_stats = profile.get("battle_stats", {}) if profile else {}
            wins = battle_stats.get("wins", 0)
            losses = battle_stats.get("losses", 0)
            draws = battle_stats.get("draws", 0)
            total_battles = wins + losses + draws

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Battles", total_battles)
            with c2:
                st.metric("Wins", wins)
            with c3:
                st.metric("Losses", losses)
            with c4:
                st.metric("Draws", draws)

            if total_battles > 0:
                win_rate = wins / total_battles * 100
                st.markdown(
                    "<div style='text-align:center;margin:12px 0;'>"
                    "<div style='font-size:1.5em;font-weight:700;"
                    "color:#059669;'>{:.0f}% Win Rate</div>"
                    "</div>".format(win_rate),
                    unsafe_allow_html=True,
                )

            # Micro challenge stats
            st.markdown("---")
            st.markdown("##### Micro-Challenge Stats")
            micro_stats = profile.get("micro_stats", {}) if profile else {}
            micro_streak = micro_stats.get("current_streak", 0)
            micro_best = micro_stats.get("best_streak", 0)
            micro_total = micro_stats.get("total_completed", 0)
            micro_correct = micro_stats.get("total_correct", 0)

            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                st.metric("Completed", micro_total)
            with mc2:
                st.metric("Correct", micro_correct)
            with mc3:
                st.metric("Current Streak", micro_streak)
            with mc4:
                st.metric("Best Streak", micro_best)


# ============================================================================
# TAB 6: LEADERBOARD
# ============================================================================

with tabs[6]:
    st.markdown("### Leaderboard")

    board_mode = st.radio(
        "View:",
        ["XP Board", "Paddock Tier Board"],
        key="sa_lb_mode",
        horizontal=True,
    )

    # -- XP Board ----------------------------------------------------------
    if board_mode == "XP Board":
        st.markdown("#### Academy XP Leaderboard")

        lb_period = st.selectbox(
            "Period",
            ["all", "month", "week"],
            format_func=lambda x: {
                "all": "All Time",
                "month": "This Month",
                "week": "This Week",
            }.get(x, x),
            key="sa_xp_lb_period",
        )

        lb_data = _academy_get(
            "/leaderboard?period={}&limit=30".format(lb_period)
        )
        leaders = []
        if lb_data and isinstance(lb_data, dict):
            leaders = lb_data.get("leaderboard", [])

        if leaders:
            # Podium for top 3
            if len(leaders) >= 3:
                pod_cols = st.columns([1, 1, 1])
                podium_order = [1, 0, 2]  # Silver, Gold, Bronze positions
                podium_labels = ["🥇", "🥈", "🥉"]
                podium_sizes = ["2em", "2.4em", "1.8em"]
                podium_bgs = ["#fef3c7", "#fefce8", "#fff7ed"]

                for col_idx, pod_idx in enumerate(podium_order):
                    if pod_idx < len(leaders):
                        entry = leaders[pod_idx]
                        with pod_cols[col_idx]:
                            e_name = _display_name(
                                entry.get("user_id", "")
                            )
                            e_xp = entry.get("total_xp", 0)
                            e_icon = entry.get("level_icon", "")
                            e_level = entry.get("level_name", "Seed")
                            st.markdown(
                                "<div style='text-align:center;background:"
                                "{bg};border-radius:12px;padding:16px;'>"
                                "<div style='font-size:{sz};'>"
                                "{medal}</div>"
                                "<div style='font-size:1.4em;'>{icon}</div>"
                                "<div style='font-weight:700;margin-top:4px;'>"
                                "{name}</div>"
                                "<div style='font-size:0.85em;color:#6b7280;'>"
                                "{level}</div>"
                                "<div style='font-weight:700;color:#059669;"
                                "font-size:1.1em;margin-top:6px;'>"
                                "{xp:,} XP</div>"
                                "</div>".format(
                                    bg=podium_bgs[pod_idx],
                                    sz=podium_sizes[pod_idx],
                                    medal=podium_labels[pod_idx],
                                    icon=e_icon, name=e_name,
                                    level=e_level, xp=e_xp,
                                ),
                                unsafe_allow_html=True,
                            )
                st.markdown("")

            # Full list
            for entry in leaders:
                is_me = entry.get("user_id") == uid
                bg = "#f0fdf4" if is_me else "#ffffff"
                border = "2px solid #22c55e" if is_me else "1px solid #f1f5f9"
                me_tag = " (You)" if is_me else ""
                raw_name = entry.get("user_id", "")
                display_name = _display_name(raw_name)
                e_icon = entry.get("level_icon", "")
                e_level = entry.get("level_name", "Seed")
                e_xp = entry.get("total_xp", 0)
                e_rank = entry.get("rank", "-")
                e_streak = entry.get("current_streak", 0)

                st.markdown(
                    "<div style='display:flex;align-items:center;"
                    "padding:10px 14px;border-radius:8px;margin-bottom:6px;"
                    "background:{bg};border:{bd};'>"
                    "<div style='width:40px;font-weight:700;font-size:1.2em;"
                    "color:#6b7280;'>#{rank}</div>"
                    "<div style='width:36px;font-size:1.4em;text-align:center;'>"
                    "{icon}</div>"
                    "<div style='flex:1;'>"
                    "<div style='font-weight:600;'>{name}{me}</div>"
                    "<div style='font-size:0.8em;color:#6b7280;'>"
                    "{level} | {streak} day streak</div>"
                    "</div>"
                    "<div style='font-weight:700;color:#059669;"
                    "font-size:1.1em;'>{xp:,} XP</div>"
                    "</div>".format(
                        bg=bg, bd=border, rank=e_rank, icon=e_icon,
                        name=display_name, me=me_tag, level=e_level,
                        streak=e_streak, xp=e_xp,
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.info("No leaderboard data yet. Be the first to earn XP!")

    # -- Paddock Tier Board ------------------------------------------------
    else:
        st.markdown("#### Paddock Tier Leaderboard")

        paddock_data = _raw_api_get("/api/paddock/leaderboard")
        paddock_leaders = []
        if paddock_data and isinstance(paddock_data, dict):
            paddock_leaders = paddock_data.get("leaderboard", [])

        if paddock_leaders:
            # Hero section: Jedi Council -- top 5
            top_5 = paddock_leaders[:5]
            top_5_html = ""
            for p in top_5:
                p_icon = p.get("tier_icon", "")
                p_name = _display_name(p.get("user_id", ""))
                p_tier = p.get("tier_name", "")
                top_5_html += (
                    "<div style='text-align:center;min-width:100px;'>"
                    "<div style='font-size:2.2em;'>{icon}</div>"
                    "<div style='font-weight:700;font-size:1em;'>{name}</div>"
                    "<div style='font-size:0.8em;opacity:0.8;'>{tier}</div>"
                    "</div>".format(icon=p_icon, name=p_name, tier=p_tier)
                )

            st.markdown(
                "<div style='background:linear-gradient(135deg, #1e1b4b, "
                "#312e81);color:white;border-radius:14px;padding:24px;"
                "margin-bottom:20px;text-align:center;'>"
                "<div style='font-size:1.4em;font-weight:800;"
                "margin-bottom:16px;'>Jedi Council</div>"
                "<div style='display:flex;justify-content:center;gap:24px;"
                "flex-wrap:wrap;'>"
                "{top5}"
                "</div></div>".format(top5=top_5_html),
                unsafe_allow_html=True,
            )

            # Full table
            st.markdown("**Full Rankings:**")
            for idx, entry in enumerate(paddock_leaders):
                is_me = entry.get("user_id") == uid
                bg = "#f0fdf4" if is_me else "#ffffff"
                border = (
                    "2px solid #22c55e" if is_me else "1px solid #f1f5f9"
                )
                me_tag = " (You)" if is_me else ""
                raw_name = entry.get("user_id", "")
                display_name = _display_name(raw_name)
                t_icon = entry.get("tier_icon", "")
                t_name = entry.get("tier_name", "")
                level_reached = entry.get("level_reached", "")
                attempts = entry.get("attempts", 0)

                st.markdown(
                    "<div style='display:flex;align-items:center;"
                    "padding:10px 14px;border-radius:8px;margin-bottom:6px;"
                    "background:{bg};border:{bd};'>"
                    "<div style='width:40px;font-weight:700;font-size:1.2em;"
                    "color:#6b7280;'>#{rank}</div>"
                    "<div style='width:36px;font-size:1.4em;text-align:center;'>"
                    "{ticon}</div>"
                    "<div style='flex:1;'>"
                    "<div style='font-weight:600;'>{name}{me}</div>"
                    "<div style='font-size:0.8em;color:#6b7280;'>"
                    "{tname} | Level: {lvl} | {att} attempts</div>"
                    "</div>"
                    "</div>".format(
                        bg=bg, bd=border, rank=idx + 1,
                        ticon=t_icon, name=display_name, me=me_tag,
                        tname=t_name, lvl=level_reached, att=attempts,
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.info(
                "No Paddock data yet. Complete The Paddock assessment "
                "to appear on the tier leaderboard."
            )

    # -- Admin-Only: HiPo Matrix ------------------------------------------
    if is_admin:
        st.markdown("---")
        st.markdown("#### HiPo Matrix (Admin View)")
        st.markdown(
            "High-potential identification matrix mapping AI skill vs "
            "engagement across all users."
        )

        hipo_data = _api_get("/hipo/matrix")

        if hipo_data and isinstance(hipo_data, dict):
            quadrants = hipo_data.get("quadrants", {})
            summary = hipo_data.get("summary", {})

            # Summary metrics
            total_users = summary.get("total_users", 0)
            avg_score = summary.get("avg_composite", 0)
            st.caption(
                "{} users assessed | Average composite: {:.1f}".format(
                    total_users, avg_score,
                )
            )

            # 2x2 grid
            q_config = [
                {
                    "key": "ai_leaders",
                    "label": "AI Leaders",
                    "icon": "🌟",
                    "desc": "High skill + High engagement",
                    "bg": "#f0fdf4",
                    "border": "#22c55e",
                },
                {
                    "key": "hidden_gems",
                    "label": "Hidden Gems",
                    "icon": "💎",
                    "desc": "High skill + Low engagement",
                    "bg": "#eff6ff",
                    "border": "#3b82f6",
                },
                {
                    "key": "solid_practitioners",
                    "label": "Solid Practitioners",
                    "icon": "🔧",
                    "desc": "Growing skill + High engagement",
                    "bg": "#fefce8",
                    "border": "#eab308",
                },
                {
                    "key": "early_stage",
                    "label": "Early Stage",
                    "icon": "🌱",
                    "desc": "Low skill + Low engagement",
                    "bg": "#f8fafc",
                    "border": "#94a3b8",
                },
            ]

            row1_col1, row1_col2 = st.columns(2)
            row2_col1, row2_col2 = st.columns(2)
            grid_cols = [row1_col1, row1_col2, row2_col1, row2_col2]

            for q_idx, qc in enumerate(q_config):
                with grid_cols[q_idx]:
                    q_users = quadrants.get(qc["key"], [])
                    user_count = len(q_users)

                    users_html = ""
                    for qu in q_users[:8]:
                        qu_name = _display_name(
                            qu.get("user_id", "")
                        )
                        qu_score = qu.get("composite_score", 0)
                        users_html += (
                            "<div style='font-size:0.85em;padding:2px 0;'>"
                            "{name} "
                            "<span style='color:#6b7280;'>({score:.0f})</span>"
                            "</div>".format(name=qu_name, score=qu_score)
                        )
                    if user_count > 8:
                        users_html += (
                            "<div style='font-size:0.8em;color:#94a3b8;'>"
                            "+{} more</div>".format(user_count - 8)
                        )

                    st.markdown(
                        "<div style='background:{bg};border:2px solid "
                        "{bd};border-radius:10px;padding:14px;"
                        "min-height:160px;'>"
                        "<div style='font-size:1.1em;font-weight:700;'>"
                        "{icon} {label}</div>"
                        "<div style='font-size:0.8em;color:#6b7280;"
                        "margin:4px 0 8px;'>{desc}</div>"
                        "<div style='font-weight:600;color:#B0BEC5;"
                        "margin-bottom:4px;'>{count} users</div>"
                        "{users}"
                        "</div>".format(
                            bg=qc["bg"], bd=qc["border"],
                            icon=qc["icon"], label=qc["label"],
                            desc=qc["desc"], count=user_count,
                            users=users_html,
                        ),
                        unsafe_allow_html=True,
                    )

            # Individual user lookup
            st.markdown("---")
            st.markdown("##### Individual HiPo Lookup")
            hipo_email = st.text_input(
                "User email:",
                key="sa_hipo_lookup_email",
                placeholder="user@harrisfarm.com.au",
            )
            if hipo_email:
                hipo_user = _api_get(
                    "/hipo/{}".format(hipo_email)
                )
                if hipo_user and isinstance(hipo_user, dict):
                    signals = hipo_user.get("signals", {})
                    composite = hipo_user.get("composite_score", 0)
                    quadrant = hipo_user.get("quadrant", "N/A")

                    st.markdown(
                        "<div style='background:#f8fafc;border:1px solid "
                        "#e2e8f0;border-radius:10px;padding:16px;'>"
                        "<div style='font-weight:700;font-size:1.05em;'>"
                        "{email}</div>"
                        "<div style='display:flex;gap:20px;margin-top:10px;"
                        "flex-wrap:wrap;'>"
                        "<div><span style='color:#6b7280;font-size:0.82em;'>"
                        "Composite</span><br/>"
                        "<span style='font-weight:700;font-size:1.2em;'>"
                        "{comp:.1f}</span></div>"
                        "<div><span style='color:#6b7280;font-size:0.82em;'>"
                        "Quadrant</span><br/>"
                        "<span style='font-weight:700;font-size:1.2em;'>"
                        "{quad}</span></div>"
                        "</div></div>".format(
                            email=hipo_email, comp=composite,
                            quad=quadrant,
                        ),
                        unsafe_allow_html=True,
                    )

                    if signals:
                        st.markdown("**Signal Breakdown:**")
                        for sig_key, sig_val in signals.items():
                            sig_label = sig_key.replace("_", " ").title()
                            sig_pct = min(
                                int(float(sig_val) / 10 * 100), 100,
                            )
                            sig_col = (
                                "#22c55e" if sig_val >= 7
                                else (
                                    "#eab308" if sig_val >= 4
                                    else "#ef4444"
                                )
                            )
                            st.markdown(
                                "<div style='margin:4px 0;'>"
                                "<div style='display:flex;"
                                "justify-content:space-between;"
                                "font-size:0.88em;'>"
                                "<span>{label}</span>"
                                "<span style='font-weight:600;"
                                "color:{col};'>{val:.1f}</span>"
                                "</div>"
                                "<div style='background:#e2e8f0;"
                                "border-radius:4px;height:8px;'>"
                                "<div style='background:{col};"
                                "width:{pct}%;height:100%;"
                                "border-radius:4px;'></div>"
                                "</div></div>".format(
                                    label=sig_label, col=sig_col,
                                    val=float(sig_val), pct=sig_pct,
                                ),
                                unsafe_allow_html=True,
                            )

                    # Recalculate button
                    if st.button(
                        "Recalculate HiPo",
                        key="sa_hipo_recalc",
                    ):
                        with st.spinner("Recalculating..."):
                            recalc = _api_post(
                                "/hipo/{}/calculate".format(hipo_email),
                            )
                        if recalc:
                            st.success("HiPo signals recalculated.")
                            st.rerun()
                        else:
                            st.error("Recalculation failed.")
                else:
                    st.info(
                        "No HiPo data found for this user. "
                        "They may need more activity first."
                    )


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "<div style='background:linear-gradient(135deg, #f0fdf4, #dcfce7);"
    "border-radius:12px;padding:20px;text-align:center;margin:16px 0;'>"
    "<div style='font-size:1.3em;font-weight:700;color:#166534;'>"
    "\"Master the prompt, master the outcome.\"</div>"
    "<div style='font-size:0.95em;color:#059669;margin-top:8px;'>"
    "10 modules + Enterprise capstone. Adaptive difficulty. Daily challenges. "
    "Peer battles. One standard. Start with the Placement Challenge and "
    "work your way to AI certification.</div>"
    "</div>",
    unsafe_allow_html=True,
)

render_footer("Skills Academy", user=user)
