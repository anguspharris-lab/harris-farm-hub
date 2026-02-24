"""
Harris Farm Hub -- Skills Academy v4
=====================================
Pillar 3: Growing Legendary Leadership

Woven Verification system with 4 mastery dimensions, adaptive difficulty,
curveball injection, placement challenge, peer battles, daily challenges,
prompt library, mentoring, and live business problems.

Two learning series:
  L-Series (L1-L5): Core AI Skills
  D-Series (D1-D5): Applied Data + AI

10 tabs:
  My Progress | My Journey | AI-First Method | Placement Challenge |
  L-Series | D-Series | Live Problems | Community | Daily & Micro | Leaderboard

Python 3.9 compatible.
"""

import os
import time
from typing import Optional

import requests
import streamlit as st

from shared.styles import render_header, render_footer, HFM_GREEN
from shared.strategic_framing import growing_legends_banner

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_BASE = "/api/skills-academy"
BRAND_GREEN = "#2ECC71"
PEOPLE_GREEN = "#059669"

LEVEL_DISPLAY = [
    {"name": "Seed", "icon": "🌱", "num": 1, "color": "#a3e635"},
    {"name": "Sprout", "icon": "🌿", "num": 2, "color": "#22c55e"},
    {"name": "Growing", "icon": "🌻", "num": 3, "color": "#2ECC71"},
    {"name": "Harvest", "icon": "🌾", "num": 4, "color": "#ca8a04"},
    {"name": "Canopy", "icon": "🌳", "num": 5, "color": "#059669"},
    {"name": "Root System", "icon": "🏆", "num": 6, "color": "#7c3aed"},
]

TIER_COLOURS = {
    "standard": "#6b7280",
    "stretch": "#d97706",
    "elite": "#7c3aed",
}

RING_COLOURS = {
    "foundation": "#3b82f6",
    "breadth": "#8b5cf6",
    "depth": "#f59e0b",
    "application": "#22c55e",
}

# ---------------------------------------------------------------------------
# Auth + page context
# ---------------------------------------------------------------------------

user = st.session_state.get("auth_user", {})
_pages = st.session_state.get("_pages", {})
user_email = (user or {}).get("email", "")
uid = user_email if user_email else "anonymous"
is_admin = (user or {}).get("is_admin", False)

render_header(
    "Growing Legends Academy",
    "**Your AI Capability Journey** | Prove what you can ship",
    goals=["G3"],
    strategy_context=(
        "You are the architect. AI is the builder. "
        "Every Harris Farmer grows from Seed to Legend "
        "\u2014 prove what you can ship at each level."
    ),
)

st.caption("You are the architect. AI is the builder. Prove what you can ship.")

# ---------------------------------------------------------------------------
# Hero banner
# ---------------------------------------------------------------------------

st.markdown(
    "<div style='background:linear-gradient(135deg, #059669 0%, #047857 50%, "
    "#065f46 100%);color:white;padding:36px 32px;border-radius:14px;"
    "margin-bottom:24px;'>"
    "<div style='font-size:2.2em;font-weight:800;margin-bottom:8px;'>"
    "Skills Academy v4</div>"
    "<div style='font-size:1.15em;opacity:0.95;max-width:800px;line-height:1.6;'>"
    "You are the architect. AI is the builder. "
    "Woven Verification tracks what you can ship, not what you memorise. "
    "Complete exercises, tackle curveballs, apply skills to real problems, "
    "and watch your verification ring fill up.</div>"
    "<div style='margin-top:16px;font-size:0.9em;opacity:0.8;'>"
    "L-Series: Core AI Skills &bull; D-Series: Applied Data + AI &bull; "
    "4 Mastery Dimensions &bull; Adaptive Difficulty</div>"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================================
# API HELPERS
# ============================================================================

def _api(method, path, json_body=None, timeout=8):
    """Call a v4 Skills Academy API endpoint."""
    url = "{}{}{}".format(API_URL, API_BASE, path)
    try:
        if method == "GET":
            resp = requests.get(url, timeout=timeout)
        else:
            resp = requests.post(url, json=json_body or {}, timeout=timeout)
        if resp.ok:
            return resp.json()
        return None
    except Exception:
        return None


def _get(path, timeout=8):
    return _api("GET", path, timeout=timeout)


def _post(path, body=None, timeout=15):
    return _api("POST", path, json_body=body, timeout=timeout)


# ============================================================================
# DATA LOADERS (session-cached)
# ============================================================================

def _load_placement():
    """Load v4 placement result."""
    key = "sav4_placement"
    if key not in st.session_state:
        result = _get("/placement/{}".format(uid))
        if result and isinstance(result, dict) and "detail" not in result:
            st.session_state[key] = result
        else:
            st.session_state[key] = None
    return st.session_state[key]


def _load_xp():
    """Load v4 XP data."""
    key = "sav4_xp"
    if key not in st.session_state:
        result = _get("/xp/{}".format(uid))
        st.session_state[key] = result if result else {}
    return st.session_state[key]


def _load_badges():
    """Load v4 badges."""
    key = "sav4_badges"
    if key not in st.session_state:
        result = _get("/badges/{}".format(uid))
        st.session_state[key] = result if result else {}
    return st.session_state[key]


def _load_verification(level=None):
    """Load verification ring data for current level."""
    if level is None:
        placement = _load_placement()
        level = placement.get("placed_level", 1) if placement else 1
    key = "sav4_verif_{}".format(level)
    if key not in st.session_state:
        result = _get("/verification/{}/{}".format(uid, level))
        st.session_state[key] = result if result else {}
    return st.session_state[key]


def _load_modules():
    """Load all modules."""
    key = "sav4_modules"
    if key not in st.session_state:
        result = _get("/modules")
        if isinstance(result, dict):
            result = result.get("modules", [])
        st.session_state[key] = result if result and isinstance(result, list) else []
    return st.session_state[key]


def _load_progress():
    """Load user progress across all modules."""
    key = "sav4_progress"
    if key not in st.session_state:
        result = _get("/progress/{}".format(uid))
        st.session_state[key] = result if result else {}
    return st.session_state[key]


def _load_gaps(level=None):
    """Load gap analysis."""
    if level is None:
        placement = _load_placement()
        level = placement.get("placed_level", 1) if placement else 1
    key = "sav4_gaps_{}".format(level)
    if key not in st.session_state:
        result = _get("/verification/{}/gaps".format(uid))
        st.session_state[key] = result if result else {}
    return st.session_state[key]


def _display_name(email_str):
    """Extract display name from email."""
    if "@" in email_str:
        return email_str.split("@")[0]
    return email_str


def _clear_caches():
    """Clear all sav4 session caches."""
    keys_to_clear = [k for k in st.session_state if k.startswith("sav4_")]
    for k in keys_to_clear:
        del st.session_state[k]


# ============================================================================
# RENDERING HELPERS
# ============================================================================

def _render_card(content_html, bg="rgba(255,255,255,0.05)", border="rgba(255,255,255,0.08)", padding="16px"):
    """Styled card container."""
    st.markdown(
        "<div style='background:{};border:1px solid {};border-radius:10px;"
        "padding:{};margin-bottom:12px;'>{}</div>".format(
            bg, border, padding, content_html
        ),
        unsafe_allow_html=True,
    )


def _render_metric_card(label, value, subtitle="", color=BRAND_GREEN):
    """Small metric card."""
    html = (
        "<div style='text-align:center;'>"
        "<div style='font-size:0.85em;color:#8899AA;margin-bottom:4px;'>{}</div>"
        "<div style='font-size:2em;font-weight:800;color:{};'>{}</div>"
        "<div style='font-size:0.8em;color:#8899AA;'>{}</div>"
        "</div>"
    ).format(label, color, value, subtitle)
    _render_card(html)


def _render_verification_rings(rings):
    """Render 4 verification dimension progress bars."""
    if not rings:
        st.info("Complete your placement to see verification progress.")
        return

    raw_rings = rings if isinstance(rings, list) else rings.get("rings", rings)
    # API returns rings as a dict keyed by dimension name — normalise to list
    if isinstance(raw_rings, dict):
        ring_list = []
        for dim_key, dim_data in raw_rings.items():
            if isinstance(dim_data, dict):
                dim_data["dimension"] = dim_data.get("label", dim_key)
                ring_list.append(dim_data)
    elif isinstance(raw_rings, list):
        ring_list = raw_rings
    else:
        ring_list = []
    if not ring_list:
        st.info("No verification data yet. Start completing exercises!")
        return

    cols = st.columns(min(len(ring_list), 4))
    for i, ring in enumerate(ring_list):
        if i >= 4:
            break
        dim = ring.get("dimension", ring.get("label", ""))
        pct = ring.get("percentage", 0)
        met = ring.get("met", False)
        color = ring.get("color", RING_COLOURS.get(dim.lower(), "#6b7280"))
        target = ring.get("target", "")

        with cols[i]:
            status_icon = "&#10003;" if met else ""
            border_style = "3px solid {}".format(color) if met else "2px solid {}".format(color)
            bg = "{}15".format(color)

            html = (
                "<div style='background:{bg};border:{border};border-radius:12px;"
                "padding:16px;text-align:center;min-height:140px;'>"
                "<div style='font-size:0.8em;color:#8899AA;text-transform:uppercase;"
                "letter-spacing:1px;margin-bottom:8px;'>{dim}</div>"
                "<div style='font-size:2em;font-weight:800;color:{color};'>"
                "{pct}%</div>"
                "<div style='background:rgba(255,255,255,0.1);border-radius:4px;height:8px;"
                "margin:8px 0;overflow:hidden;'>"
                "<div style='background:{color};height:100%;width:{pct}%;"
                "border-radius:4px;transition:width 0.3s;'></div></div>"
                "<div style='font-size:0.75em;color:#8899AA;'>{target} {icon}</div>"
                "</div>"
            ).format(
                bg=bg, border=border_style, dim=dim.title(), color=color,
                pct=min(int(pct), 100), target=target,
                icon=status_icon,
            )
            st.markdown(html, unsafe_allow_html=True)


def _render_level_badge(level_num, status="provisional"):
    """Render a level badge with provisional/confirmed styling."""
    lv = LEVEL_DISPLAY[min(level_num - 1, len(LEVEL_DISPLAY) - 1)]
    border = "3px solid {}".format(lv["color"]) if status == "confirmed" else "2px dashed {}".format(lv["color"])
    label = "Confirmed" if status == "confirmed" else "Provisional"
    badge_bg = "{}20".format(lv["color"])

    html = (
        "<div style='display:inline-block;background:{bg};border:{border};"
        "border-radius:20px;padding:8px 20px;margin:4px;'>"
        "<span style='font-size:1.3em;'>{icon}</span> "
        "<span style='font-weight:700;color:{color};'>{name}</span> "
        "<span style='font-size:0.75em;color:#8899AA;'>({label})</span>"
        "</div>"
    ).format(
        bg=badge_bg, border=border, icon=lv["icon"],
        color=lv["color"], name=lv["name"], label=label,
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_tier_badge(tier):
    """Render exercise tier badge."""
    color = TIER_COLOURS.get(tier, "#6b7280")
    return (
        "<span style='background:{}15;color:{};border:1px solid {};border-radius:12px;"
        "padding:2px 10px;font-size:0.8em;font-weight:600;'>{}</span>"
    ).format(color, color, color, tier.title())


# ---------------------------------------------------------------------------
# Progress bar + Current Challenge
# ---------------------------------------------------------------------------

_xp_top = _load_xp()
if _xp_top and _xp_top.get("total_xp") is not None:
    _top_xp = _xp_top.get("total_xp", 0)
    _top_level = _xp_top.get("name", "Seed")
    _top_icon = _xp_top.get("icon", "🌱")
    _top_pct = _xp_top.get("progress_pct", 0) / 100
    _top_next = _xp_top.get("xp_to_next", 0)
    st.progress(min(_top_pct, 1.0))
    st.markdown("**{} {}** — {} XP — {} XP to next level".format(
        _top_icon, _top_level, _top_xp, _top_next))

try:
    from shared.challenge_bank import get_challenge_for_user
    _cb_role = (user or {}).get("hub_role", "user")
    _cb_level = (_xp_top.get("name", "Seed") if _xp_top else "Seed").lower()
    _cb_challenge = get_challenge_for_user(_cb_level, _cb_role)
    if _cb_challenge:
        with st.container(border=True):
            st.markdown("### 🎯 Your Current Challenge")
            st.markdown("**{}**".format(_cb_challenge["title"]))
            st.markdown(_cb_challenge["description"])
            st.caption("Reward: {} XP · Estimated: {} min".format(
                _cb_challenge["xp_reward"], _cb_challenge["estimated_minutes"]))
except ImportError:
    pass

# ============================================================================
# 10 TABS
# ============================================================================

tabs = st.tabs([
    "My Progress",
    "My Journey",
    "AI-First Method",
    "Placement Challenge",
    "L-Series (Core AI)",
    "D-Series (Data + AI)",
    "Live Problems",
    "Community",
    "Daily & Micro",
    "Leaderboard",
])


# ============================================================================
# TAB 0: MY PROGRESS
# ============================================================================

with tabs[0]:
    placement = _load_placement()

    if not placement:
        st.warning(
            "You haven't completed the placement challenge yet. "
            "Go to the **Placement Challenge** tab to get started!"
        )
    else:
        xp_data = _load_xp()
        badges_data = _load_badges()
        level = placement.get("placed_level", 1)
        status = "provisional"

        # Try to get verification status
        verif = _load_verification(level)
        if verif and isinstance(verif, dict):
            status = verif.get("status", "provisional")

        # --- Level badge + XP summary ---
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            _render_level_badge(level, status)
            total_xp = xp_data.get("total_xp", 0) if xp_data else 0
            streak = xp_data.get("streak_days", 0) if xp_data else 0
            st.caption("Total XP: **{}** | Streak: **{} days**".format(total_xp, streak))

        with col2:
            modules_done = 0
            progress = _load_progress()
            if progress and isinstance(progress, dict):
                mods = progress.get("modules", [])
                if isinstance(mods, list):
                    modules_done = sum(1 for m in mods if m.get("status") == "complete")
            _render_metric_card("Modules", str(modules_done), "completed")

        with col3:
            badge_list = badges_data.get("badges", []) if badges_data else []
            earned = sum(1 for b in badge_list if b.get("earned"))
            _render_metric_card("Badges", str(earned), "earned", "#8b5cf6")

        with col4:
            placement_score = placement.get("total_score", 0)
            _render_metric_card("Placement", "{}/25".format(placement_score), "score", PEOPLE_GREEN)

        # --- Verification Rings ---
        st.markdown("### Verification Progress")
        st.caption(
            "Your mastery builds naturally as you ship real work. "
            "Complete all 4 dimensions to confirm your level."
        )

        rings = _load_verification(level)
        _render_verification_rings(rings)

        # --- Gap Detection ---
        gaps = _load_gaps(level)
        if gaps and isinstance(gaps, dict):
            gap_list = gaps.get("gaps", [])
            if gap_list:
                st.markdown("### Stretch Challenges")
                st.caption("Suggested activities to strengthen your mastery.")
                for gap in gap_list:
                    dim = gap.get("dimension", "")
                    suggestion = gap.get("suggestion", "")
                    color = RING_COLOURS.get(dim, "#6b7280")
                    _render_card(
                        "<div style='display:flex;align-items:center;gap:12px;'>"
                        "<div style='background:{}20;color:{};border-radius:8px;padding:6px 14px;"
                        "font-weight:700;text-transform:uppercase;font-size:0.8em;'>{}</div>"
                        "<div>{}</div></div>".format(color, color, dim, suggestion),
                        border=color,
                    )

        # --- Module Progress Grid ---
        st.markdown("### Module Progress")
        modules = _load_modules()
        if modules:
            l_mods = [m for m in modules if m.get("module_code", "").startswith("L")]
            d_mods = [m for m in modules if m.get("module_code", "").startswith("D")]

            for series_name, series_mods in [("L-Series: Core AI Skills", l_mods), ("D-Series: Applied Data + AI", d_mods)]:
                if series_mods:
                    st.markdown("**{}**".format(series_name))
                    cols = st.columns(min(len(series_mods), 5))
                    for i, mod in enumerate(series_mods):
                        code = mod.get("module_code", "")
                        name = mod.get("module_name", code)
                        with cols[i % len(cols)]:
                            # Check progress
                            mod_status = "available"
                            prog = _load_progress()
                            if prog and isinstance(prog, dict):
                                mod_list = prog.get("modules", [])
                                for mp in mod_list:
                                    if mp.get("module_code") == code:
                                        mod_status = mp.get("status", "available")
                                        break

                            if mod_status == "complete":
                                icon = "&#10003;"
                                bg = "rgba(34,197,94,0.1)"
                                border = "#22c55e"
                            elif mod_status == "in_progress":
                                icon = "&#9654;"
                                bg = "rgba(245,158,11,0.1)"
                                border = "#f59e0b"
                            else:
                                icon = "&#9711;"
                                bg = "rgba(255,255,255,0.03)"
                                border = "rgba(255,255,255,0.08)"

                            _render_card(
                                "<div style='text-align:center;'>"
                                "<div style='font-size:1.5em;'>{}</div>"
                                "<div style='font-weight:700;font-size:0.9em;'>{}</div>"
                                "<div style='font-size:0.8em;color:#8899AA;'>{}</div>"
                                "</div>".format(icon, code, name),
                                bg=bg, border=border,
                            )

        # --- Recent Activity ---
        st.markdown("### Recent Activity")
        _xp_hist_raw = _get("/xp/{}/history".format(uid))
        xp_hist = _xp_hist_raw.get("history", []) if isinstance(_xp_hist_raw, dict) else (_xp_hist_raw or [])
        if xp_hist:
            for entry in xp_hist[:8]:
                action = entry.get("action", "")
                xp = entry.get("xp_amount", 0)
                ts = entry.get("created_at", "")[:16]
                st.markdown(
                    "- **+{} XP** — {} <span style='color:#8899AA;font-size:0.8em;'>{}</span>".format(
                        xp, action, ts
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No activity yet. Start shipping work to earn XP!")


# ============================================================================
# TAB 1: MY JOURNEY
# ============================================================================

with tabs[1]:
    st.markdown("### Your Growing Legends Journey")
    st.markdown("Every challenge you complete builds your profile. Here's your story so far.")

    # Fetch XP activity history
    _journey_history = []
    if uid:
        try:
            _j_resp = _get("/xp/{}/history".format(uid))
            if _j_resp and isinstance(_j_resp, list):
                _journey_history = _j_resp
            elif _j_resp and isinstance(_j_resp, dict):
                _journey_history = _j_resp.get("history", [])
        except Exception:
            pass

    if _journey_history:
        import pandas as pd
        _j_rows = []
        for entry in _journey_history[:20]:
            _j_rows.append({
                "Activity": entry.get("action", ""),
                "XP": "+{}".format(entry.get("xp", 0)),
                "Date": entry.get("created_at", "")[:10],
            })
        if _j_rows:
            st.dataframe(pd.DataFrame(_j_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No activity yet. Complete your first challenge to start your journey!")


# ============================================================================
# TAB 2: AI-FIRST METHOD
# ============================================================================

with tabs[2]:
    st.markdown("### The AI-First Method")
    st.markdown("Six steps. One prompt. The whole process. This is how every Harris Farmer becomes 10x more effective.")

    _method_content = [
        (
            "Step 1: Define the Whole Outcome",
            "Don't ask 'what's my next task?' Ask 'what is the entire end-to-end outcome I need?' The prompt IS the work.",
            "Why: When you define the whole outcome upfront, AI can build the complete solution in one pass instead of piece by piece.",
            "Build a complete weekly performance review that compares to budget, flags problems, recommends actions, and is ready for my manager to approve.",
        ),
        (
            "Step 2: Flood It With Context",
            "AI knows everything but it needs YOUR data. The more specific context you give — role, audience, format, constraints — the better the output.",
            "Why: Context is what separates a generic answer from a Harris Farm answer. Your data, your store, your customers.",
            "Include: who it's for, what decisions it drives, what data sources to use, what format the output needs to be in.",
        ),
        (
            "Step 3: Run It Through The Rubric",
            "Every output gets scored. Our 5-tier review system catches what humans miss. Nothing ships below an 8.",
            "Why: Without a rubric, quality is subjective. With one, every output meets the same bar — every time.",
            "CTO Panel > CLO Panel > Strategic Alignment > Implementation > Presentation Quality. Score >= 8.0 to ship.",
        ),
        (
            "Step 4: Ask AI What's Missing",
            "After your first draft, ask: 'What additional context would help you improve this?' AI will tell you exactly what it needs.",
            "Why: AI can identify its own blind spots. One question unlocks the next level of quality.",
            "What am I missing? What would make this board-ready? What data would strengthen the recommendations?",
        ),
        (
            "Step 5: Review, Add Your Judgment",
            "AI builds it. You add what only a human can — context, relationships, gut feel, the Harris Farm way. Your expertise matters most.",
            "Why: Your 20 years of produce knowledge combined with AI's data analysis creates decisions nobody else can make.",
            "Your 20 years of produce knowledge + AI's data analysis = decisions nobody else can make.",
        ),
        (
            "Step 6: Ship It & Share the Prompt",
            "Built a great prompt? Save it. Share it. Your colleagues will thank you. This is how we all level up together.",
            "Why: Every shared prompt is a force multiplier. One person's work benefits the whole team.",
            "Save > Prompt Library > Tagged by role & use case > Anyone can reuse and improve it.",
        ),
    ]

    try:
        from shared.challenge_bank import get_challenges_by_step
        _has_bank = True
    except ImportError:
        _has_bank = False

    for i, (title, desc, why, example) in enumerate(_method_content):
        with st.expander(title):
            st.markdown("**What:** {}".format(desc))
            st.markdown("**{}**".format(why))
            st.code(example, language=None)
            if _has_bank:
                _step_challenges = get_challenges_by_step(i + 1)
                if _step_challenges:
                    st.caption("Challenges that practice this step: {}".format(
                        ", ".join(c["title"] for c in _step_challenges[:3])
                    ))


# ============================================================================
# TAB 3: PLACEMENT CHALLENGE
# ============================================================================

with tabs[3]:
    placement = _load_placement()

    if placement:
        st.success("Placement complete! You were placed at **Level {} — {}**".format(
            placement.get("placed_level", 1),
            placement.get("level_name", "Seed"),
        ))
        st.markdown("**Total Score:** {}/25".format(placement.get("total_score", 0)))

        responses = placement.get("responses", placement.get("challenge_scores", []))
        if responses:
            st.markdown("#### Your Responses")
            for resp in responses:
                sid = resp.get("scenario_id", 0)
                score = resp.get("score", 0)
                reasoning = resp.get("reasoning", "")
                names = {1: "Recognition", 2: "Construction", 3: "Iteration", 4: "Scope", 5: "Application"}
                name = names.get(sid, "Challenge {}".format(sid))
                color = "#22c55e" if score >= 4 else "#f59e0b" if score >= 2 else "#ef4444"
                _render_card(
                    "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                    "<div><strong>{}</strong></div>"
                    "<div style='color:{};font-weight:700;font-size:1.2em;'>{}/5</div>"
                    "</div>"
                    "<div style='font-size:0.85em;color:#8899AA;margin-top:4px;'>{}</div>".format(
                        name, color, score, reasoning
                    ),
                )

        hipo = placement.get("hipo_flags", [])
        if hipo:
            st.markdown("#### HiPo Indicators Detected")
            flag_labels = {
                "scale_thinker": "Scale Thinker — You think in systems, not steps",
                "process_reimaginer": "Process Reimaginer — You see transformation, not just automation",
                "accelerated_learner": "Accelerated Learner — Fast and accurate",
            }
            for f in hipo:
                label = flag_labels.get(f, f)
                st.markdown("- {}".format(label))

        if is_admin:
            st.markdown("---")
            if st.button("Reset Placement (Admin)", key="sav4_reset_placement"):
                result = _post("/placement/{}/reset".format(uid))
                if result:
                    _clear_caches()
                    st.success("Placement reset. Refresh the page.")
                else:
                    st.error("Failed to reset placement.")

    else:
        # --- Placement flow ---
        st.markdown("### Placement Challenge")
        st.markdown(
            "5 quick scenarios to find your starting level. "
            "Takes about 5 minutes. Show us what you can ship \u2014 your answers determine where you begin."
        )

        # Load scenarios
        _scenario_resp = _get("/placement/scenarios")
        scenarios = _scenario_resp.get("scenarios", []) if isinstance(_scenario_resp, dict) else (_scenario_resp or [])
        if not scenarios:
            st.error("Could not load placement scenarios. Is the API running?")
        else:
            # Initialise state
            if "sav4_p_step" not in st.session_state:
                st.session_state["sav4_p_step"] = 0
                st.session_state["sav4_p_responses"] = []
                st.session_state["sav4_p_start_time"] = time.time()

            step = st.session_state["sav4_p_step"]

            if step < len(scenarios):
                scenario = scenarios[step]
                sid = scenario.get("id", step + 1)
                sname = scenario.get("name", "Challenge {}".format(step + 1))
                stype = scenario.get("type", "free_text")
                instruction = scenario.get("instruction", "")
                time_limit = scenario.get("time_seconds", 60)

                # Progress bar
                progress_pct = step / len(scenarios)
                st.progress(progress_pct, text="Challenge {} of {}".format(step + 1, len(scenarios)))

                st.markdown("#### {} — {}".format(step + 1, sname))
                st.markdown(instruction)

                # Show original prompt/output for iteration challenge
                if scenario.get("original_prompt"):
                    st.markdown("**Original Prompt:**")
                    st.code(scenario["original_prompt"], language=None)
                if scenario.get("original_output"):
                    st.markdown("**Original Output:**")
                    st.code(scenario["original_output"], language=None)

                start_key = "sav4_p_timer_{}".format(step)
                if start_key not in st.session_state:
                    st.session_state[start_key] = time.time()

                if stype == "multiple_choice":
                    options = scenario.get("options", [])
                    for opt in options:
                        label = opt.get("label", "")
                        text = opt.get("text", "")
                        if st.button(
                            "{}: {}".format(label, text),
                            key="sav4_p_opt_{}_{}".format(step, label),
                            use_container_width=True,
                        ):
                            elapsed = time.time() - st.session_state[start_key]
                            st.session_state["sav4_p_responses"].append({
                                "scenario_id": sid,
                                "response": label,
                                "time_seconds": int(elapsed),
                            })
                            st.session_state["sav4_p_step"] = step + 1
                            st.rerun()

                else:
                    text_key = "sav4_p_text_{}".format(step)
                    user_text = st.text_area(
                        "Your response",
                        key=text_key,
                        height=150,
                        placeholder="Type your response here...",
                    )
                    if st.button("Submit", key="sav4_p_submit_{}".format(step)):
                        if not user_text or len(user_text.strip()) < 10:
                            st.warning("Please write at least a few sentences.")
                        else:
                            elapsed = time.time() - st.session_state[start_key]
                            st.session_state["sav4_p_responses"].append({
                                "scenario_id": sid,
                                "response": user_text.strip(),
                                "time_seconds": int(elapsed),
                            })
                            st.session_state["sav4_p_step"] = step + 1
                            st.rerun()

            else:
                # All scenarios complete — submit
                st.progress(1.0, text="All challenges complete!")
                st.markdown("#### Submitting your responses...")

                responses = st.session_state.get("sav4_p_responses", [])
                result = _post("/placement/submit", {
                    "user_id": uid,
                    "responses": responses,
                }, timeout=60)

                if result and isinstance(result, dict):
                    level = result.get("placed_level", 1)
                    level_name = result.get("level_name", "Seed")
                    total = result.get("total_score", 0)

                    st.balloons()
                    st.success("You've been placed at **Level {} — {}** (Score: {}/25)".format(
                        level, level_name, total
                    ))

                    _render_level_badge(level, "provisional")
                    st.caption("Your level is **Provisional**. As you ship real work and complete exercises, "
                               "your mastery will be verified across 4 dimensions.")

                    # Clean up state
                    for k in list(st.session_state.keys()):
                        if k.startswith("sav4_p_"):
                            del st.session_state[k]
                    _clear_caches()
                else:
                    st.error("Something went wrong submitting your placement. Please try again.")
                    if st.button("Retry", key="sav4_p_retry"):
                        st.session_state["sav4_p_step"] = 0
                        st.session_state["sav4_p_responses"] = []
                        st.rerun()


# ============================================================================
# TAB 4 & 5: L-SERIES / D-SERIES (shared renderer)
# ============================================================================

def _render_series_tab(series_prefix, series_name, tab_idx):
    """Render a learning series tab (L or D)."""
    placement = _load_placement()
    if not placement:
        st.warning("Complete the **Placement Challenge** first to unlock modules.")
        return

    modules = _load_modules()
    series_mods = [m for m in modules if m.get("module_code", "").startswith(series_prefix)]

    if not series_mods:
        st.info("No {} modules available yet.".format(series_name))
        return

    # Module selector
    mod_options = ["{} — {}".format(m.get("module_code", ""), m.get("module_name", "")) for m in series_mods]
    selected_idx = st.selectbox(
        "Select Module",
        range(len(mod_options)),
        format_func=lambda i: mod_options[i],
        key="sav4_mod_sel_{}_{}".format(series_prefix, tab_idx),
    )
    mod = series_mods[selected_idx]
    code = mod.get("module_code", "")

    # Sub-tabs within module
    sub_tabs = st.tabs(["Theory", "Examples", "Exercise", "Assessment"])

    # --- Theory sub-tab ---
    with sub_tabs[0]:
        lessons = _get("/modules/{}/lessons".format(code))
        if lessons and isinstance(lessons, list):
            for lesson in lessons:
                title = lesson.get("title", "Lesson")
                content = lesson.get("content_md", "")
                with st.expander(title, expanded=False):
                    st.markdown(content)
        elif lessons and isinstance(lessons, dict):
            lesson_list = lessons.get("lessons", [])
            for lesson in lesson_list:
                title = lesson.get("title", "Lesson")
                content = lesson.get("content_md", "")
                with st.expander(title, expanded=False):
                    st.markdown(content)
        else:
            st.info("Lesson content loading...")

    # --- Examples sub-tab ---
    with sub_tabs[1]:
        st.markdown("#### Worked Examples")
        st.markdown("Review examples of good prompts and responses for this module level.")
        # Pull from lessons that have example content
        if lessons and isinstance(lessons, list):
            for lesson in lessons:
                examples = lesson.get("examples", [])
                if examples:
                    for ex in examples:
                        _render_card(
                            "<div style='font-weight:600;margin-bottom:4px;'>{}</div>"
                            "<div style='font-size:0.9em;color:#B0BEC5;'>{}</div>".format(
                                ex.get("title", "Example"), ex.get("content", "")
                            ),
                            bg="rgba(34,197,94,0.1)",
                        )
        st.caption("Work through the theory tab first for full context.")

    # --- Exercise sub-tab ---
    with sub_tabs[2]:
        st.markdown("#### Practice Exercise")

        # Get next exercise from API (handles curveball + foundation injection)
        exercise_key = "sav4_exercise_{}_{}".format(series_prefix, code)
        if exercise_key not in st.session_state:
            ex_data = _get("/exercise/{}/{}".format(uid, code))
            st.session_state[exercise_key] = ex_data
        else:
            ex_data = st.session_state[exercise_key]

        if ex_data and isinstance(ex_data, dict):
            ex_type = ex_data.get("injection_type", "normal")
            exercise = ex_data.get("exercise", ex_data)

            # Banner for curveball / foundation check
            if ex_type == "curveball":
                st.markdown(
                    "<div style='background:#7c3aed15;border:2px solid #7c3aed;"
                    "border-radius:10px;padding:12px 16px;margin-bottom:16px;'>"
                    "<strong style='color:#7c3aed;'>Challenge Round</strong> — "
                    "This one's a curveball. Think carefully!</div>",
                    unsafe_allow_html=True,
                )
            elif ex_type == "foundation_check":
                st.markdown(
                    "<div style='background:#3b82f615;border:2px solid #3b82f6;"
                    "border-radius:10px;padding:12px 16px;margin-bottom:16px;'>"
                    "<strong style='color:#3b82f6;'>Warm-Up</strong> — "
                    "Quick refresher on the fundamentals.</div>",
                    unsafe_allow_html=True,
                )

            # Exercise instruction
            instruction = exercise.get("scenario_text", exercise.get("instruction", ""))
            tier = exercise.get("tier", "standard")
            context = exercise.get("context_tag", "")
            exercise_id = exercise.get("exercise_id", exercise.get("id", ""))

            st.markdown("**{}** {}".format(
                _render_tier_badge(tier),
                " &mdash; <span style='color:#8899AA;font-size:0.8em;'>{}</span>".format(context) if context else "",
            ), unsafe_allow_html=True)
            st.markdown(instruction)

            # Response input
            resp_key = "sav4_ex_resp_{}_{}".format(series_prefix, code)
            user_response = st.text_area(
                "Your response",
                key=resp_key,
                height=200,
                placeholder="Type your answer here...",
            )

            col_submit, col_new = st.columns([1, 1])
            with col_submit:
                if st.button("Submit", key="sav4_ex_submit_{}_{}".format(series_prefix, code)):
                    if not user_response or len(user_response.strip()) < 10:
                        st.warning("Please write a more detailed response.")
                    else:
                        with st.spinner("Scoring your response..."):
                            result = _post("/exercise/submit", {
                                "user_id": uid,
                                "exercise_id": exercise_id,
                                "module_code": code,
                                "response": user_response.strip(),
                            }, timeout=30)

                        if result and isinstance(result, dict):
                            score = result.get("score", 0)
                            max_sc = result.get("max_score", 5)
                            reasoning = result.get("reasoning", "")

                            color = "#22c55e" if score >= 4 else "#f59e0b" if score >= 2 else "#ef4444"
                            st.markdown(
                                "<div style='font-size:2em;font-weight:800;color:{};text-align:center;'>"
                                "{}/{}</div>".format(color, score, max_sc),
                                unsafe_allow_html=True,
                            )
                            if reasoning:
                                st.markdown("**Feedback:** {}".format(reasoning))

                            # Check for verification promotion
                            promotion = result.get("promotion")
                            if promotion:
                                st.balloons()
                                st.success("Level Confirmed! Your mastery has been verified.")

                            # XP award info
                            xp_earned = result.get("xp_earned", 0)
                            if xp_earned:
                                st.caption("+{} XP".format(xp_earned))

                            _clear_caches()
                        else:
                            st.error("Scoring failed. Please try again.")

            with col_new:
                if st.button("New Exercise", key="sav4_ex_new_{}_{}".format(series_prefix, code)):
                    if exercise_key in st.session_state:
                        del st.session_state[exercise_key]
                    st.rerun()

            # Exercise history
            with st.expander("Exercise History"):
                _hist_raw = _get("/exercise/history/{}/{}".format(uid, code))
                hist = _hist_raw.get("history", []) if isinstance(_hist_raw, dict) else (_hist_raw or [])
                if hist:
                    for h in hist[:10]:
                        ex_id = h.get("exercise_id", "")
                        sc = h.get("score", 0)
                        mx = h.get("max_score", 5)
                        ts = h.get("completed_at", "")[:16]
                        st.markdown(
                            "- **{}/{}** — {} <span style='color:#8899AA;font-size:0.8em;'>{}</span>".format(
                                sc, mx, ex_id, ts
                            ),
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No exercise history yet.")
        else:
            st.info("Loading exercise... If this persists, try the Theory tab first.")
            if st.button("Load Exercise", key="sav4_ex_load_{}_{}".format(series_prefix, code)):
                if exercise_key in st.session_state:
                    del st.session_state[exercise_key]
                st.rerun()

    # --- Assessment sub-tab ---
    with sub_tabs[3]:
        st.markdown("#### Module Assessment")
        st.markdown(
            "Submit a comprehensive response to demonstrate your understanding of **{}**.".format(code)
        )

        # Check if already passed
        existing = _get("/assessment/{}/{}".format(uid, code))
        if existing and isinstance(existing, dict) and existing.get("passed"):
            st.success("You've already passed this assessment with a score of **{}/{}**".format(
                existing.get("score", 0), existing.get("max_score", 25),
            ))
            if existing.get("rubric_scores"):
                st.markdown("**Rubric Breakdown:**")
                for crit, sc in existing["rubric_scores"].items():
                    st.markdown("- {}: **{}**".format(crit, sc))
        else:
            # Get the module's assessment instruction
            mod_detail = _get("/modules/{}".format(code))
            if mod_detail and isinstance(mod_detail, dict):
                assessment_prompt = mod_detail.get("assessment_instruction", "")
                if assessment_prompt:
                    st.markdown(assessment_prompt)

            assess_text_key = "sav4_assess_text_{}_{}".format(series_prefix, code)
            assess_resp = st.text_area(
                "Your assessment response",
                key=assess_text_key,
                height=250,
                placeholder="Write your comprehensive response...",
            )

            if st.button("Submit Assessment", key="sav4_assess_submit_{}_{}".format(series_prefix, code)):
                if not assess_resp or len(assess_resp.strip()) < 30:
                    st.warning("Please write a more comprehensive response (at least a paragraph).")
                else:
                    with st.spinner("Evaluating your assessment..."):
                        result = _post("/assessment/submit", {
                            "user_id": uid,
                            "module_code": code,
                            "response": assess_resp.strip(),
                        }, timeout=30)

                    if result and isinstance(result, dict):
                        score = result.get("score", 0)
                        max_sc = result.get("max_score", 25)
                        passed = result.get("passed", False)
                        reasoning = result.get("reasoning", "")

                        if passed:
                            st.success("Assessment passed! {}/{} ".format(score, max_sc))
                        else:
                            st.warning("Score: {}/{}. You need 18/25 to pass.".format(score, max_sc))

                        if reasoning:
                            st.markdown("**Feedback:** {}".format(reasoning))

                        _clear_caches()
                    else:
                        st.error("Assessment submission failed. Please try again.")


# TAB 4: L-Series
with tabs[4]:
    _render_series_tab("L", "L-Series", 4)

# TAB 5: D-Series
with tabs[5]:
    _render_series_tab("D", "D-Series", 5)


# ============================================================================
# TAB 6: LIVE PROBLEMS
# ============================================================================

with tabs[6]:
    placement = _load_placement()
    if not placement:
        st.warning("Complete the **Placement Challenge** first.")
    else:
        st.markdown("### Live Business Problems")
        st.markdown(
            "Real Harris Farm challenges that need solving. "
            "Successfully completing a live problem counts toward your **Application** dimension."
        )

        # Challenge of the Month
        cotm = _get("/live-problems")
        problems = cotm if isinstance(cotm, list) else (cotm.get("problems", []) if isinstance(cotm, dict) else [])

        if problems:
            # Feature the first one as Challenge of the Month
            featured = problems[0]
            st.markdown(
                "<div style='background:linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);"
                "color:#1a1a1a;padding:24px;border-radius:14px;margin-bottom:20px;"
                "border:3px solid #d97706;'>"
                "<div style='font-size:1.4em;font-weight:800;margin-bottom:8px;'>"
                "Challenge of the Month</div>"
                "<div style='font-size:1.05em;line-height:1.6;'>{}</div>"
                "<div style='margin-top:12px;font-size:0.85em;opacity:0.8;'>Level: {} | Category: {}</div>"
                "</div>".format(
                    featured.get("title", ""),
                    featured.get("level", "All"),
                    featured.get("category", "General"),
                ),
                unsafe_allow_html=True,
            )

            # All problems
            for prob in problems:
                prob_id = prob.get("id", prob.get("problem_id", ""))
                title = prob.get("title", "Problem")
                description = prob.get("description", "")
                level = prob.get("level", "")
                category = prob.get("category", "")

                with st.expander("{} — {} (Level {})".format(title, category, level)):
                    st.markdown(description)

                    # Context/data provided
                    context = prob.get("context", "")
                    if context:
                        st.markdown("**Context:** {}".format(context))

                    # Response
                    resp_key = "sav4_lp_resp_{}".format(prob_id)
                    user_resp = st.text_area(
                        "Your solution",
                        key=resp_key,
                        height=200,
                        placeholder="Describe your approach and solution...",
                    )
                    if st.button("Submit Solution", key="sav4_lp_submit_{}".format(prob_id)):
                        if not user_resp or len(user_resp.strip()) < 30:
                            st.warning("Please provide a detailed solution.")
                        else:
                            with st.spinner("Evaluating your solution..."):
                                result = _post(
                                    "/live-problems/{}/submit".format(prob_id),
                                    {"user_id": uid, "response": user_resp.strip()},
                                    timeout=30,
                                )
                            if result and isinstance(result, dict):
                                score = result.get("score", 0)
                                max_sc = result.get("max_score", 5)
                                reasoning = result.get("reasoning", "")
                                color = "#22c55e" if score >= 4 else "#f59e0b" if score >= 2 else "#ef4444"
                                st.markdown(
                                    "<div style='font-size:1.5em;font-weight:700;color:{};'>"
                                    "{}/{}</div>".format(color, score, max_sc),
                                    unsafe_allow_html=True,
                                )
                                if reasoning:
                                    st.markdown("**Feedback:** {}".format(reasoning))
                                _clear_caches()
                            else:
                                st.error("Submission failed.")
        else:
            st.info("No live problems available at the moment.")

        # Role Pathways
        st.markdown("---")
        st.markdown("### Role Pathways")
        st.caption("See which modules and problems map to your role.")
        _pw_raw = _get("/role-pathways")
        pathways = _pw_raw.get("pathways", []) if isinstance(_pw_raw, dict) else (_pw_raw or [])
        if pathways:
            for pw in pathways:
                name = pw.get("role_name", pw.get("name", ""))
                desc = pw.get("description", "")
                mods = pw.get("recommended_modules", "")
                with st.expander(name):
                    st.markdown(desc)
                    if mods:
                        st.markdown("**Recommended Modules:** {}".format(mods))


# ============================================================================
# TAB 7: COMMUNITY
# ============================================================================

with tabs[7]:
    placement = _load_placement()
    if not placement:
        st.warning("Complete the **Placement Challenge** first.")
    else:
        social_sub = st.tabs(["Peer Battles", "Prompt Library", "Mentoring"])

        # --- Peer Battles ---
        with social_sub[0]:
            st.markdown("### Peer Battles")
            st.markdown("Challenge a colleague to a head-to-head prompt battle!")

            # Open battles
            _battles_raw = _get("/battle/open")
            open_battles = _battles_raw.get("battles", []) if isinstance(_battles_raw, dict) else (_battles_raw or [])
            if open_battles:
                st.markdown("#### Open Challenges")
                for battle in open_battles:
                    battle_id = battle.get("id", battle.get("battle_id", ""))
                    challenger = battle.get("challenger_id", "")
                    topic = battle.get("topic", "")
                    _render_card(
                        "<div style='display:flex;justify-content:space-between;"
                        "align-items:center;'>"
                        "<div><strong>{}</strong> challenged on: {}</div>"
                        "</div>".format(_display_name(challenger), topic),
                    )
                    # Join button
                    join_key = "sav4_battle_join_{}".format(battle_id)
                    resp_key = "sav4_battle_resp_{}".format(battle_id)
                    battle_resp = st.text_area(
                        "Your response to the battle",
                        key=resp_key,
                        height=100,
                    )
                    if st.button("Accept Challenge", key=join_key):
                        if not battle_resp or len(battle_resp.strip()) < 10:
                            st.warning("Write a response first.")
                        else:
                            result = _post(
                                "/battle/{}/join".format(battle_id),
                                {"user_id": uid, "response": battle_resp.strip()},
                                timeout=20,
                            )
                            if result:
                                winner = result.get("winner_id", "")
                                if winner == uid:
                                    st.success("You won the battle!")
                                else:
                                    st.info("Your opponent won this round. Keep practicing!")
                                _clear_caches()
                            else:
                                st.error("Failed to join battle.")

            # Create battle
            st.markdown("#### Create a Challenge")
            battle_topic = st.text_input(
                "Battle topic/prompt",
                key="sav4_battle_topic",
                placeholder="e.g. Best prompt to analyse store performance...",
            )
            battle_response = st.text_area(
                "Your response",
                key="sav4_battle_create_resp",
                height=100,
            )
            if st.button("Create Battle", key="sav4_battle_create"):
                if not battle_topic or not battle_response:
                    st.warning("Fill in both the topic and your response.")
                else:
                    result = _post("/battle/create", {
                        "challenger_id": uid,
                        "topic": battle_topic.strip(),
                        "response": battle_response.strip(),
                    })
                    if result:
                        st.success("Battle created! Waiting for an opponent.")
                    else:
                        st.error("Failed to create battle.")

        # --- Prompt Library ---
        with social_sub[1]:
            st.markdown("### Prompt Library")
            st.markdown("Share your best prompts with the team. Top prompts get featured!")

            # Browse prompts
            _prompts_raw = _get("/prompt-library")
            prompts = _prompts_raw.get("prompts", []) if isinstance(_prompts_raw, dict) else (_prompts_raw or [])
            if prompts:
                for p in prompts[:20]:
                    prompt_id = p.get("id", p.get("prompt_id", ""))
                    title = p.get("title", "")
                    prompt_text = p.get("prompt_text", "")
                    author = p.get("author_id", p.get("submitted_by", ""))
                    dept = p.get("department", "")
                    rating = p.get("rating", 0)
                    p_status = p.get("status", "pending")

                    with st.expander("{} — by {} ({})".format(title, _display_name(author), dept)):
                        st.markdown(prompt_text)
                        st.caption("Rating: {}/5 | Status: {}".format(rating, p_status))

                        if is_admin and p_status == "pending":
                            col_a, col_r = st.columns(2)
                            with col_a:
                                if st.button("Approve", key="sav4_pl_approve_{}".format(prompt_id)):
                                    _post("/prompt-library/{}/review".format(prompt_id), {
                                        "reviewer_id": uid,
                                        "status": "approved",
                                        "rating": 4,
                                    })
                                    st.success("Approved!")
                            with col_r:
                                if st.button("Reject", key="sav4_pl_reject_{}".format(prompt_id)):
                                    _post("/prompt-library/{}/review".format(prompt_id), {
                                        "reviewer_id": uid,
                                        "status": "rejected",
                                        "rating": 1,
                                    })
                                    st.info("Rejected.")

            # Submit new prompt
            st.markdown("#### Submit a Prompt")
            pl_title = st.text_input("Title", key="sav4_pl_title", placeholder="e.g. Store Performance Analysis")
            pl_dept = st.selectbox("Department", ["Operations", "Commercial", "Customer", "Finance", "Supply Chain", "Data", "Other"], key="sav4_pl_dept")
            pl_text = st.text_area("Prompt", key="sav4_pl_text", height=150, placeholder="Write your prompt here...")
            if st.button("Submit to Library", key="sav4_pl_submit"):
                if not pl_title or not pl_text:
                    st.warning("Fill in the title and prompt.")
                else:
                    result = _post("/prompt-library/submit", {
                        "author_id": uid,
                        "title": pl_title.strip(),
                        "prompt_text": pl_text.strip(),
                        "department": pl_dept,
                    })
                    if result:
                        st.success("Prompt submitted for review!")
                    else:
                        st.error("Submission failed.")

        # --- Mentoring ---
        with social_sub[2]:
            st.markdown("### Mentoring")
            st.markdown("Connect with a mentor or offer to mentor others.")

            # Current relationships
            _mentor_raw = _get("/mentoring/{}".format(uid))
            mentoring = []
            if isinstance(_mentor_raw, dict):
                mentoring = _mentor_raw.get("as_mentor", []) + _mentor_raw.get("as_mentee", [])
            elif isinstance(_mentor_raw, list):
                mentoring = _mentor_raw
            if mentoring:
                for m in mentoring:
                    mentor = m.get("mentor_id", "")
                    mentee = m.get("mentee_id", "")
                    status_m = m.get("status", "active")
                    focus = m.get("focus_area", "")
                    role = "Mentoring" if mentor == uid else "Mentored by"
                    partner = mentee if mentor == uid else mentor

                    _render_card(
                        "<div><strong>{}</strong> {} "
                        "<span style='color:#8899AA;'>| Focus: {} | Status: {}</span></div>".format(
                            role, _display_name(partner), focus, status_m
                        ),
                    )
            else:
                st.caption("No mentoring relationships yet.")

            # Create mentoring pair
            st.markdown("#### Create Mentoring Pair")
            mentor_email = st.text_input("Mentor email", key="sav4_mentor_email")
            mentee_email = st.text_input("Mentee email", key="sav4_mentee_email")
            focus = st.text_input("Focus area", key="sav4_mentor_focus", placeholder="e.g. Advanced prompting techniques")
            if st.button("Create Pair", key="sav4_mentor_create"):
                if not mentor_email or not mentee_email:
                    st.warning("Fill in both emails.")
                else:
                    result = _post("/mentoring/create", {
                        "mentor_id": mentor_email.strip(),
                        "mentee_id": mentee_email.strip(),
                        "focus_area": focus.strip(),
                    })
                    if result:
                        st.success("Mentoring pair created!")
                    else:
                        st.error("Failed to create pair.")


# ============================================================================
# TAB 8: DAILY & MICRO
# ============================================================================

with tabs[8]:
    placement = _load_placement()
    if not placement:
        st.warning("Complete the **Placement Challenge** first.")
    else:
        st.markdown("### Daily Challenge")
        st.markdown("A fresh challenge every day to keep your skills sharp.")

        # Check dormancy
        dormancy = _get("/dormancy/{}".format(uid))
        if dormancy and isinstance(dormancy, dict) and dormancy.get("is_dormant"):
            days = dormancy.get("days_inactive", 30)
            st.markdown(
                "<div style='background:#fef3c7;border:2px solid #f59e0b;"
                "border-radius:12px;padding:20px;margin-bottom:20px;'>"
                "<div style='font-size:1.2em;font-weight:700;color:#92400e;'>"
                "Welcome Back!</div>"
                "<div style='color:#78350f;margin-top:8px;'>"
                "You've been away for {} days. Let's warm up with a quick refresher "
                "before jumping back in.</div></div>".format(days),
                unsafe_allow_html=True,
            )

        # Today's challenge
        daily = _get("/daily/{}".format(uid))
        if daily and isinstance(daily, dict):
            challenge = daily
            challenge_id = challenge.get("id", challenge.get("challenge_id", ""))
            question = challenge.get("question", challenge.get("challenge_text", ""))
            category = challenge.get("category", "")
            completed = challenge.get("completed", False)

            _render_card(
                "<div style='font-weight:700;font-size:1.1em;margin-bottom:8px;'>"
                "Today's Challenge</div>"
                "<div style='font-size:0.85em;color:#8899AA;margin-bottom:8px;'>"
                "Category: {}</div>"
                "<div>{}</div>".format(category, question),
                bg="rgba(59,130,246,0.1)",
                border="#3b82f6",
            )

            if completed:
                st.success("You've already completed today's challenge!")
            else:
                daily_resp_key = "sav4_daily_resp"
                daily_resp = st.text_area(
                    "Your answer",
                    key=daily_resp_key,
                    height=100,
                    placeholder="Type your answer...",
                )
                if st.button("Submit", key="sav4_daily_submit"):
                    if not daily_resp or len(daily_resp.strip()) < 5:
                        st.warning("Please write an answer.")
                    else:
                        result = _post(
                            "/daily/{}/complete".format(challenge_id),
                            {"user_id": uid, "answer": daily_resp.strip()},
                        )
                        if result:
                            xp = result.get("xp_earned", 10)
                            st.success("Challenge complete! +{} XP".format(xp))
                            _clear_caches()
                        else:
                            st.error("Submission failed.")
        else:
            st.info("No daily challenge available. Check back tomorrow!")

        # --- Mindset Micro-Assessment ---
        st.markdown("---")
        st.markdown("### Mindset Scenario")
        st.caption("Quick scenario to test your AI-first thinking.")

        mindset_key = "sav4_mindset_scenario"
        if mindset_key not in st.session_state:
            scenario = _get("/mindset/scenario")
            st.session_state[mindset_key] = scenario
        scenario = st.session_state[mindset_key]

        if scenario and isinstance(scenario, dict):
            st.markdown("**{}**".format(scenario.get("scenario_text", scenario.get("description", ""))))

            ms_resp_key = "sav4_mindset_resp"
            ms_resp = st.text_area(
                "Your approach",
                key=ms_resp_key,
                height=120,
                placeholder="How would you use AI to tackle this?",
            )
            if st.button("Evaluate", key="sav4_mindset_eval"):
                if not ms_resp or len(ms_resp.strip()) < 10:
                    st.warning("Please describe your approach.")
                else:
                    result = _post("/mindset/evaluate", {
                        "user_id": uid,
                        "scenario_id": scenario.get("id", scenario.get("scenario_id", "")),
                        "response": ms_resp.strip(),
                    })
                    if result and isinstance(result, dict):
                        score = result.get("score", 0)
                        max_sc = result.get("max_score", 5)
                        reasoning = result.get("reasoning", "")
                        color = "#22c55e" if score >= 4 else "#f59e0b" if score >= 2 else "#ef4444"
                        st.markdown(
                            "<div style='font-size:1.5em;font-weight:700;color:{};'>"
                            "{}/{}</div>".format(color, score, max_sc),
                            unsafe_allow_html=True,
                        )
                        if reasoning:
                            st.markdown("**Feedback:** {}".format(reasoning))
                    else:
                        st.error("Evaluation failed.")

            if st.button("New Scenario", key="sav4_mindset_new"):
                if mindset_key in st.session_state:
                    del st.session_state[mindset_key]
                st.rerun()
        else:
            st.info("No mindset scenarios available.")


# ============================================================================
# TAB 9: LEADERBOARD
# ============================================================================

with tabs[9]:
    lb_sub = st.tabs(["XP Leaderboard", "Verification Board", "HiPo Matrix"])

    # --- XP Leaderboard ---
    with lb_sub[0]:
        st.markdown("### XP Leaderboard")
        _lb_raw = _get("/leaderboard")
        leaderboard = _lb_raw.get("leaderboard", []) if isinstance(_lb_raw, dict) else (_lb_raw or [])
        if leaderboard:
            for idx, entry in enumerate(leaderboard[:25]):
                name = _display_name(entry.get("user_id", ""))
                xp = entry.get("total_xp", 0)
                level = entry.get("current_level", 1)
                streak = entry.get("streak_days", 0)
                lv_info = LEVEL_DISPLAY[min(level - 1, len(LEVEL_DISPLAY) - 1)]

                medal = ""
                if idx == 0:
                    medal = "&#129351; "
                elif idx == 1:
                    medal = "&#129352; "
                elif idx == 2:
                    medal = "&#129353; "

                bg = "rgba(34,197,94,0.1)" if entry.get("user_id") == uid else "rgba(255,255,255,0.05)"
                _render_card(
                    "<div style='display:flex;justify-content:space-between;"
                    "align-items:center;'>"
                    "<div>{}<strong>{}. {}</strong> "
                    "<span style='font-size:0.85em;'>{} {}</span></div>"
                    "<div style='text-align:right;'>"
                    "<span style='font-size:1.3em;font-weight:700;color:{};'>{} XP</span>"
                    "<br><span style='font-size:0.8em;color:#8899AA;'>Streak: {} days</span>"
                    "</div></div>".format(
                        medal, idx + 1, name, lv_info["icon"], lv_info["name"],
                        lv_info["color"], xp, streak,
                    ),
                    bg=bg,
                )
        else:
            st.info("No leaderboard data yet. Start shipping work to appear here!")

    # --- Verification Board ---
    with lb_sub[1]:
        st.markdown("### Verification Status Board")
        st.caption("See who's confirmed their level mastery.")

        # Re-use leaderboard data with verification info
        if leaderboard and isinstance(leaderboard, list):
            confirmed = []
            provisional = []
            for entry in leaderboard:
                v_status = entry.get("verification_status", "provisional")
                if v_status == "confirmed":
                    confirmed.append(entry)
                else:
                    provisional.append(entry)

            if confirmed:
                st.markdown("#### Confirmed")
                for entry in confirmed:
                    name = _display_name(entry.get("user_id", ""))
                    level = entry.get("current_level", 1)
                    lv_info = LEVEL_DISPLAY[min(level - 1, len(LEVEL_DISPLAY) - 1)]
                    _render_card(
                        "<div>{} <strong>{}</strong> — {} {} (Confirmed)</div>".format(
                            lv_info["icon"], name, lv_info["name"], lv_info["icon"],
                        ),
                        border=lv_info["color"],
                    )

            if provisional:
                st.markdown("#### Provisional")
                for entry in provisional[:15]:
                    name = _display_name(entry.get("user_id", ""))
                    level = entry.get("current_level", 1)
                    lv_info = LEVEL_DISPLAY[min(level - 1, len(LEVEL_DISPLAY) - 1)]
                    _render_card(
                        "<div>{} <strong>{}</strong> — {} (Provisional)</div>".format(
                            lv_info["icon"], name, lv_info["name"],
                        ),
                    )
        else:
            st.info("No data yet.")

    # --- HiPo Matrix (Admin only) ---
    with lb_sub[2]:
        if not is_admin:
            st.info("HiPo Matrix is available to administrators only.")
        else:
            st.markdown("### HiPo Signal Matrix")
            st.caption("Silent tracking of 9 behavioral indicators across all users.")

            hipo_data = _get("/admin/hipo")
            if hipo_data and isinstance(hipo_data, dict):
                quadrants = hipo_data.get("quadrants", {})
                summary = hipo_data.get("summary", {})

                # Summary cards
                q_cols = st.columns(4)
                q_names = ["AI Leaders", "Hidden Gems", "Solid Practitioners", "Early Stage"]
                q_colors = ["#059669", "#7c3aed", "#3b82f6", "#6b7280"]
                for i, (qname, qcolor) in enumerate(zip(q_names, q_colors)):
                    with q_cols[i]:
                        count = summary.get(qname, 0)
                        _render_metric_card(qname, str(count), "users", qcolor)

                # Detail per quadrant
                for qname in q_names:
                    users = quadrants.get(qname, [])
                    if users:
                        st.markdown("#### {}".format(qname))
                        for u in users:
                            name = u.get("display_name", u.get("user_id", ""))
                            composite = u.get("composite_score", 0)
                            level_name = u.get("level_name", "")
                            st.markdown(
                                "- **{}** — Composite: {}/10 | Level: {}".format(
                                    name, composite, level_name,
                                )
                            )

                # Individual user lookup
                st.markdown("---")
                lookup_uid = st.text_input("Look up user HiPo signals", key="sav4_hipo_lookup")
                if lookup_uid:
                    if st.button("Calculate Signals", key="sav4_hipo_calc"):
                        with st.spinner("Calculating..."):
                            result = _post("/hipo/{}/calculate".format(lookup_uid))
                        if result and isinstance(result, dict):
                            signals = result.get("signals", [])
                            composite = result.get("composite_score", 0)
                            quadrant = result.get("quadrant", "")

                            st.markdown("**Composite:** {}/10 | **Quadrant:** {}".format(composite, quadrant))
                            for sig in signals:
                                sname = sig.get("name", sig.get("signal_type", ""))
                                sscore = sig.get("score", 0)
                                bar_pct = int(sscore * 10)
                                color = "#22c55e" if sscore >= 7 else "#f59e0b" if sscore >= 4 else "#ef4444"
                                st.markdown(
                                    "<div style='display:flex;align-items:center;gap:8px;margin:4px 0;'>"
                                    "<div style='width:160px;font-size:0.85em;'>{}</div>"
                                    "<div style='flex:1;background:rgba(255,255,255,0.1);border-radius:4px;height:12px;'>"
                                    "<div style='background:{};height:100%;width:{}%;border-radius:4px;'>"
                                    "</div></div>"
                                    "<div style='width:40px;text-align:right;font-weight:600;'>{}</div>"
                                    "</div>".format(sname, color, bar_pct, sscore),
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.error("Could not calculate signals.")
            else:
                st.info("No HiPo data available. Users need to complete exercises first.")


# ============================================================================
# FOOTER
# ============================================================================

render_footer(
    "Skills Academy",
    extra="v4 — Woven Verification | Adaptive Difficulty | 9 HiPo Signals",
    user=user,
)
