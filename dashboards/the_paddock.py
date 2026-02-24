"""
The Paddock -- Progressive Difficulty AI Skills Challenge
How far can you go? One wrong answer and it's game over.
"""

import os
import time
from datetime import datetime
from typing import Optional

import pandas as pd
import requests
import streamlit as st

from shared.styles import render_header, render_footer
from shared.strategic_framing import growing_legends_banner

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Tier constants (duplicated from paddock_engine for display only)
TIER_MAP = {
    0: "Unranked",
    1: "Seed", 2: "Seed",
    3: "Sprout", 4: "Sprout",
    5: "Grower", 6: "Grower",
    7: "Harvester", 8: "Harvester",
    9: "Cultivator",
    10: "Legend",
}
TIER_ICONS = {
    "Unranked": "\u2753",
    "Seed": "\U0001f331",
    "Sprout": "\U0001f33f",
    "Grower": "\U0001f33b",
    "Harvester": "\U0001f9d1\u200d\U0001f33e",
    "Cultivator": "\U0001f30d",
    "Legend": "\U0001f3c6",
}
TIER_ORDER = ["Unranked", "Seed", "Sprout", "Grower", "Harvester", "Cultivator", "Legend"]

BRAND_GREEN = "#2ECC71"


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _api_post(path, json_body=None):
    # type: (str, Optional[dict]) -> Optional[dict]
    """Fire a POST request to the backend. Returns JSON dict or None."""
    try:
        url = "{}/api/paddock{}".format(API_URL, path)
        resp = requests.post(url, json=json_body or {}, timeout=5)
        if resp.ok:
            return resp.json()
        return None
    except Exception:
        return None


def _api_get(path):
    # type: (str) -> Optional[dict]
    """Fire a GET request to the backend. Returns JSON dict/list or None."""
    try:
        url = "{}/api/paddock{}".format(API_URL, path)
        resp = requests.get(url, timeout=5)
        if resp.ok:
            return resp.json()
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _tier_for_level(level):
    # type: (int) -> str
    return TIER_MAP.get(level, "Unranked")


def _icon_for_tier(tier_name):
    # type: (str) -> str
    return TIER_ICONS.get(tier_name, "\u2753")


def _format_time(seconds):
    # type: (Optional[int]) -> str
    if not seconds or seconds <= 0:
        return "--"
    mins = seconds // 60
    secs = seconds % 60
    if mins > 0:
        return "{}m {}s".format(mins, secs)
    return "{}s".format(secs)


def _tier_colour(tier_name):
    # type: (str) -> str
    colours = {
        "Unranked": "#94a3b8",
        "Seed": "#84cc16",
        "Sprout": "#22c55e",
        "Grower": "#f59e0b",
        "Harvester": "#f97316",
        "Cultivator": "#8b5cf6",
        "Legend": "#eab308",
    }
    return colours.get(tier_name, "#94a3b8")


def _reset_playing_state():
    """Clear all playing-related session state."""
    keys_to_clear = [
        "paddock_attempt_id",
        "paddock_current_level",
        "paddock_current_question",
        "paddock_answered_questions",
        "paddock_result",
        "paddock_answer_result",
        "paddock_start_time",
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]


# ---------------------------------------------------------------------------
# State initialisation
# ---------------------------------------------------------------------------

user = st.session_state.get("auth_user")
user_email = (user or {}).get("email", "")

if "paddock_state" not in st.session_state:
    st.session_state["paddock_state"] = "welcome"


# ===================================================================
# WELCOME SCREEN
# ===================================================================

def render_welcome():
    """Welcome screen with hero banner, start button, history & leaderboard."""

    # --- Hero banner ---
    st.markdown("### 🌱 The Paddock")
    st.markdown("*This isn't a quiz. It's the first step in your Growing Legends journey.*")
    st.markdown("Show us what you can do with AI — and we'll show you where to go next. One wrong answer and it's game over!")

    # --- Tier progression strip ---
    tier_labels = [
        ("\U0001f331", "Seed", "1-2"),
        ("\U0001f33f", "Sprout", "3-4"),
        ("\U0001f33b", "Grower", "5-6"),
        ("\U0001f9d1\u200d\U0001f33e", "Harvester", "7-8"),
        ("\U0001f30d", "Cultivator", "9"),
        ("\U0001f3c6", "Legend", "10"),
    ]
    cols = st.columns(len(tier_labels))
    for i, (icon, name, levels) in enumerate(tier_labels):
        with cols[i]:
            st.markdown(
                "<div style='text-align:center;'>"
                "<div style='font-size:1.8em;'>{}</div>"
                "<div style='font-weight:700;font-size:0.9em;'>{}</div>"
                "<div style='color:#888;font-size:0.75em;'>Lv {}</div>"
                "</div>".format(icon, name, levels),
                unsafe_allow_html=True,
            )

    st.markdown("")

    # --- Personal best ---
    if user_email:
        best = _api_get("/user/{}/best".format(user_email))
        if best:
            tier_name = best.get("tier_name", "Unranked")
            tier_icon = _icon_for_tier(tier_name)
            best_level = best.get("max_level_reached", 0)
            st.markdown(
                "<div style='text-align:center;padding:16px;background:#f0f7ed;"
                "border-radius:10px;border:2px solid {};margin-bottom:20px;'>"
                "<div style='font-size:0.85em;color:#666;'>Your Personal Best</div>"
                "<div style='font-size:1.6em;font-weight:800;margin:4px 0;'>"
                "{} {} &mdash; Level {}</div>"
                "</div>".format(BRAND_GREEN, tier_icon, tier_name, best_level),
                unsafe_allow_html=True,
            )

    # --- Start button ---
    col_l, col_mid, col_r = st.columns([1, 2, 1])
    with col_mid:
        if st.button(
            "\U0001f331 Start Challenge",
            use_container_width=True,
            type="primary",
            key="btn_start_challenge",
        ):
            _start_new_attempt()
            return

    st.markdown("")

    # --- Tabs: History & Leaderboard ---
    if user_email:
        tab_hist, tab_lb = st.tabs(["My History", "Leaderboard"])
        with tab_hist:
            _render_history_tab()
        with tab_lb:
            _render_leaderboard()
    else:
        _render_leaderboard()


def _start_new_attempt():
    """Call API to start an attempt, transition to playing state."""
    _reset_playing_state()
    data = _api_post("/attempt/start", {"user_id": user_email})
    if not data or "attempt_id" not in data:
        st.error("Could not start the challenge. Please try again.")
        return

    st.session_state["paddock_attempt_id"] = data["attempt_id"]
    st.session_state["paddock_current_level"] = data.get("current_level", 1)
    st.session_state["paddock_current_question"] = data.get("question")
    st.session_state["paddock_answered_questions"] = []
    st.session_state["paddock_answer_result"] = None
    st.session_state["paddock_start_time"] = time.time()
    st.session_state["paddock_state"] = "playing"
    st.rerun()


# ===================================================================
# PLAYING SCREEN
# ===================================================================

def render_playing():
    """Active quiz: one question at a time with progressive difficulty."""
    attempt_id = st.session_state.get("paddock_attempt_id")
    current_level = st.session_state.get("paddock_current_level", 1)
    question = st.session_state.get("paddock_current_question")
    answer_result = st.session_state.get("paddock_answer_result")

    if not attempt_id or not question:
        st.error("Something went wrong. Returning to welcome.")
        st.session_state["paddock_state"] = "welcome"
        _reset_playing_state()
        st.rerun()
        return

    # --- Progress header ---
    tier_name = _tier_for_level(current_level)
    tier_icon = _icon_for_tier(tier_name)
    st.markdown(
        "<div style='text-align:center;margin-bottom:4px;'>"
        "<span style='font-size:1.3em;font-weight:700;'>"
        "Level {} &mdash; {} Zone {}</span>"
        "</div>".format(current_level, tier_name, tier_icon),
        unsafe_allow_html=True,
    )
    st.progress(current_level / 10)

    # --- Show answer feedback if we just answered ---
    if answer_result is not None:
        _render_answer_feedback(answer_result)
        return

    # --- Question card ---
    _render_question_card(question, attempt_id, current_level)


def _render_question_card(question, attempt_id, current_level):
    """Render the question and submit button."""
    q_id = question.get("id")
    q_text = question.get("question_text", "")
    q_type = question.get("question_type", "multiple_choice")
    options = question.get("options", [])
    topic = question.get("topic", "")

    # Difficulty badge
    diff_level = question.get("difficulty_level", current_level)
    tier_for_q = _tier_for_level(diff_level)
    badge_colour = _tier_colour(tier_for_q)
    st.markdown(
        "<div style='margin-bottom:12px;'>"
        "<span style='background:{};color:white;padding:4px 12px;"
        "border-radius:12px;font-size:0.8em;font-weight:600;'>"
        "Level {} &bull; {}</span>"
        "</div>".format(badge_colour, diff_level, topic.replace("_", " ").title() if topic else "General"),
        unsafe_allow_html=True,
    )

    # Question text
    st.markdown(
        "<div style='font-size:1.25em;font-weight:600;line-height:1.5;"
        "margin-bottom:16px;'>{}</div>".format(q_text),
        unsafe_allow_html=True,
    )

    # Widget key includes level to avoid DuplicateWidgetID
    widget_key = "paddock_answer_lv{}_q{}".format(current_level, q_id)

    answer = None

    if q_type == "multiple_choice" and options:
        opt_values = [o["value"] for o in options]
        opt_labels = {o["value"]: o["label"] for o in options}
        answer = st.radio(
            "Select your answer:",
            opt_values,
            format_func=lambda v, lbl=opt_labels: lbl.get(v, v),
            key=widget_key,
            label_visibility="collapsed",
        )
    else:
        # Fallback for any other type — text input
        answer = st.text_input("Your answer:", key=widget_key)

    st.markdown("")
    if st.button(
        "Submit Answer",
        use_container_width=True,
        type="primary",
        key="btn_submit_lv{}_q{}".format(current_level, q_id),
    ):
        if not answer:
            st.warning("Please select an answer before submitting.")
            return
        _submit_answer(attempt_id, q_id, answer)


def _submit_answer(attempt_id, question_id, answer):
    """Submit answer to API and handle result."""
    path = "/attempt/{}/answer/{}".format(attempt_id, question_id)
    data = _api_post(path, {"answer": answer})

    if not data:
        st.error("Could not submit your answer. Please try again.")
        return

    # Build record for the answered-questions list
    current_q = st.session_state.get("paddock_current_question", {})
    record = {
        "level": st.session_state.get("paddock_current_level", 1),
        "question_text": current_q.get("question_text", ""),
        "topic": current_q.get("topic", ""),
        "user_answer": answer,
        "correct_answer": data.get("correct_answer", ""),
        "correct": data.get("correct", False),
        "explanation": data.get("explanation", ""),
    }
    answered = st.session_state.get("paddock_answered_questions", [])
    answered.append(record)
    st.session_state["paddock_answered_questions"] = answered

    # Store the answer result for feedback display
    st.session_state["paddock_answer_result"] = data
    st.rerun()


def _render_answer_feedback(data):
    """Show correct/wrong feedback with explanation and next action."""
    is_correct = data.get("correct", False)
    explanation = data.get("explanation", "")
    assessment_complete = data.get("assessment_complete", False)
    result = data.get("result")

    if is_correct and not assessment_complete:
        # Correct — continue
        st.success("Correct!")
        if explanation:
            st.markdown("**Explanation:** {}".format(explanation))

        next_level = data.get("current_level")
        next_question = data.get("question")

        st.markdown("")
        if st.button(
            "Next Level \u2192",
            use_container_width=True,
            type="primary",
            key="btn_next_lv{}".format(next_level),
        ):
            st.session_state["paddock_current_level"] = next_level
            st.session_state["paddock_current_question"] = next_question
            st.session_state["paddock_answer_result"] = None
            st.rerun()

    elif is_correct and assessment_complete:
        # Answered level 10 — Legend!
        st.markdown(
            "<div style='text-align:center;padding:24px;background:"
            "linear-gradient(135deg, #eab308 0%, #f59e0b 100%);"
            "border-radius:14px;color:white;margin-bottom:16px;'>"
            "<div style='font-size:3em;'>\U0001f3c6</div>"
            "<div style='font-size:1.6em;font-weight:800;margin:8px 0;'>"
            "LEGENDARY!</div>"
            "<div>You answered every level correctly. Absolute legend.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        if explanation:
            st.markdown("**Explanation:** {}".format(explanation))
        _show_result_button(result)

    else:
        # Wrong answer — game over
        correct_answer = data.get("correct_answer", "")
        st.error("Incorrect! The correct answer was: **{}**".format(correct_answer))
        if explanation:
            st.markdown("**Explanation:** {}".format(explanation))
        _show_result_button(result)


def _show_result_button(result):
    """Store result and show 'See Results' button."""
    if result:
        st.session_state["paddock_result"] = result

    st.markdown("")
    if st.button(
        "See Results",
        use_container_width=True,
        type="primary",
        key="btn_see_results",
    ):
        st.session_state["paddock_state"] = "result"
        st.session_state["paddock_answer_result"] = None
        st.rerun()


# ===================================================================
# RESULT SCREEN
# ===================================================================

def render_result():
    """Post-attempt result screen with tier badge, stats, and review."""
    result = st.session_state.get("paddock_result")
    attempt_id = st.session_state.get("paddock_attempt_id")

    # If we don't have a result cached, fetch from API
    if not result and attempt_id:
        detail = _api_get("/attempt/{}".format(attempt_id))
        if detail:
            result = {
                "attempt_id": attempt_id,
                "max_level_reached": detail.get("max_level_reached", 0),
                "tier_name": detail.get("tier_name", "Unranked"),
                "tier_icon": _icon_for_tier(detail.get("tier_name", "Unranked")),
                "total_correct": detail.get("total_correct", 0),
                "total_questions": detail.get("total_questions", 0),
                "time_seconds": detail.get("time_seconds", 0),
            }

    if not result:
        st.error("Could not load results. Returning to welcome.")
        st.session_state["paddock_state"] = "welcome"
        _reset_playing_state()
        st.rerun()
        return

    max_level = result.get("max_level_reached", 0)
    tier_name = result.get("tier_name", _tier_for_level(max_level))
    tier_icon = _icon_for_tier(tier_name)
    total_correct = result.get("total_correct", 0)
    total_questions = result.get("total_questions", 0)
    time_seconds = result.get("time_seconds", 0)

    # Calculate elapsed from session if API time is 0
    if time_seconds == 0:
        start_t = st.session_state.get("paddock_start_time")
        if start_t:
            time_seconds = int(time.time() - start_t)

    # --- Hero card ---
    tier_bg = _tier_colour(tier_name)
    st.markdown(
        "<div style='text-align:center;padding:40px 24px;"
        "background:linear-gradient(135deg, {} 0%, {} 80%);"
        "color:white;border-radius:14px;margin-bottom:24px;'>"
        "<div style='font-size:4em;'>{}</div>"
        "<div style='font-size:2em;font-weight:800;margin:8px 0;'>"
        "You reached Level {} &mdash; {}!</div>"
        "<div style='font-size:1.05em;opacity:0.9;'>Well played.</div>"
        "</div>".format(BRAND_GREEN, tier_bg, tier_icon, max_level, tier_name),
        unsafe_allow_html=True,
    )

    # --- Stats ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Correct Answers", "{} / {}".format(total_correct, total_questions))
    c2.metric("Level Reached", str(max_level))
    c3.metric("Time Taken", _format_time(time_seconds))

    # --- Personal best comparison ---
    if user_email:
        best = _api_get("/user/{}/best".format(user_email))
        if best:
            best_level = best.get("max_level_reached", 0)
            if max_level > best_level:
                st.success(
                    "New personal best! You beat your previous best of Level {} ({}).".format(
                        best_level, _tier_for_level(best_level)
                    )
                )
            elif max_level == best_level:
                st.info("You matched your personal best: Level {}.".format(best_level))
            else:
                best_tier = _tier_for_level(best_level)
                st.info(
                    "Your personal best is still Level {} ({} {}).".format(
                        best_level, _icon_for_tier(best_tier), best_tier
                    )
                )

    # --- Question review ---
    st.markdown("---")
    st.markdown("### Question Review")

    answered = st.session_state.get("paddock_answered_questions", [])

    if answered:
        for i, q in enumerate(answered):
            level_num = q.get("level", i + 1)
            q_text = q.get("question_text", "")
            was_correct = q.get("correct", False)
            status_icon = "\u2705" if was_correct else "\u274c"
            tier_at_level = _tier_for_level(level_num)
            summary = "Level {} ({}) {} {}".format(
                level_num, tier_at_level, status_icon,
                "Correct" if was_correct else "Incorrect"
            )
            with st.expander(summary, expanded=not was_correct):
                st.markdown("**Q:** {}".format(q_text))
                user_ans = q.get("user_answer", "")
                correct_ans = q.get("correct_answer", "")
                st.markdown("**Your answer:** {}".format(user_ans))
                if not was_correct:
                    st.markdown("**Correct answer:** {}".format(correct_ans))
                expl = q.get("explanation", "")
                if expl:
                    st.markdown("**Explanation:** {}".format(expl))
    else:
        # Fallback: fetch from API
        if attempt_id:
            detail = _api_get("/attempt/{}".format(attempt_id))
            if detail and detail.get("responses"):
                for resp in detail["responses"]:
                    level_num = resp.get("difficulty_level", 0)
                    was_correct = bool(resp.get("is_correct", 0))
                    status_icon = "\u2705" if was_correct else "\u274c"
                    tier_at_level = _tier_for_level(level_num)
                    summary = "Level {} ({}) {} {}".format(
                        level_num, tier_at_level, status_icon,
                        "Correct" if was_correct else "Incorrect"
                    )
                    with st.expander(summary, expanded=not was_correct):
                        st.markdown("**Q:** {}".format(resp.get("question_text", "")))
                        st.markdown("**Your answer:** {}".format(resp.get("answer", "")))
                        if not was_correct:
                            st.markdown("**Correct answer:** {}".format(
                                resp.get("correct_answer", "")
                            ))
                        expl = resp.get("explanation", "")
                        if expl:
                            st.markdown("**Explanation:** {}".format(expl))

    # --- AI-First Method Profile ---
    st.markdown("---")
    st.subheader("Your AI-First Method Profile")

    TOPIC_TO_STEPS = {
        "basics": [1, 5],
        "prompting": [2, 4],
        "data": [2],
        "workflow": [1, 6],
        "ethics": [5],
        "rubric": [3],
    }
    METHOD_STEPS = [
        (1, "Define the Whole Outcome"),
        (2, "Flood It With Context"),
        (3, "Run It Through The Rubric"),
        (4, "Ask AI What's Missing"),
        (5, "Review, Add Your Judgment"),
        (6, "Ship It & Share the Prompt"),
    ]

    # Calculate scores per step from answered questions
    step_correct = {i: 0 for i in range(1, 7)}
    step_total = {i: 0 for i in range(1, 7)}
    for q in answered:
        topic = q.get("topic", "basics")
        steps = TOPIC_TO_STEPS.get(topic, [1])
        for s in steps:
            step_total[s] += 1
            if q.get("correct", False):
                step_correct[s] += 1

    for step_num, step_name in METHOD_STEPS:
        total = step_total.get(step_num, 0)
        correct = step_correct.get(step_num, 0)
        pct = correct / total if total > 0 else 0
        col_label, col_bar = st.columns([2, 3])
        with col_label:
            st.markdown("**Step {}:** {}".format(step_num, step_name))
        with col_bar:
            st.progress(min(pct, 1.0))
            if total > 0 and pct < 0.5:
                st.caption("← This is your growth edge")
            elif total == 0:
                st.caption("Not yet tested")

    # --- Role-specific challenge preview ---
    st.markdown("---")
    try:
        from shared.challenge_bank import get_challenge_for_user
        _user_tier = tier_name.lower() if tier_name else "seed"
        _user_role = (st.session_state.get("auth_user") or {}).get("hub_role", "user")
        _challenge = get_challenge_for_user(_user_tier, _user_role)
        if _challenge:
            with st.container(border=True):
                st.markdown("### 🎯 Your First {} Challenge".format(tier_name))
                st.markdown("**{}**".format(_challenge["title"]))
                st.markdown(_challenge["description"])
                st.caption("⏱ {} min · {} XP · Steps {}".format(
                    _challenge["estimated_minutes"],
                    _challenge["xp_reward"],
                    ", ".join(str(s) for s in _challenge["method_steps"]),
                ))
    except ImportError:
        pass

    # --- What Happens Next bridge ---
    NEXT_TIER = {
        "Unranked": "Seed",
        "Seed": "Sprout",
        "Sprout": "Grower",
        "Grower": "Harvester",
        "Harvester": "Cultivator",
        "Cultivator": "Legend",
        "Legend": "Legend",
    }
    next_tier = NEXT_TIER.get(tier_name, "Sprout")

    st.success("🎯 You're a {}! Here's your path:".format(tier_name))
    st.markdown(
        "**Right now:** Try your first challenge above\n\n"
        "**This week:** Complete 2 more challenges to build your streak\n\n"
        "**Your goal:** Reach {} by shipping a reusable prompt template\n\n"
        "**Your superpower:** You already think in systems — AI amplifies that".format(next_tier)
    )
    _pages = st.session_state.get("_pages", {})
    if "skills-academy" in _pages:
        st.page_link(
            _pages["skills-academy"],
            label="→ Go to Growing Legends",
            use_container_width=True,
        )

    # --- Action buttons ---
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(
            "\U0001f504 Try Again",
            use_container_width=True,
            key="btn_try_again",
        ):
            st.session_state["paddock_state"] = "welcome"
            _reset_playing_state()
            st.rerun()
    with col_b:
        if st.button(
            "\U0001f3c6 View Leaderboard",
            use_container_width=True,
            key="btn_view_lb_result",
        ):
            st.session_state["paddock_show_result_lb"] = True
            st.rerun()

    # --- Inline leaderboard on result page ---
    if st.session_state.get("paddock_show_result_lb"):
        st.markdown("---")
        _render_leaderboard()


# ===================================================================
# LEADERBOARD
# ===================================================================

def _render_leaderboard():
    """Show the Jedi Council (top 5) + full ranked table."""
    lb_data = _api_get("/leaderboard")
    if not lb_data:
        st.info("No leaderboard data yet. Be the first to take the challenge!")
        return

    st.markdown("### \U0001f3c6 Leaderboard")

    # --- Jedi Council: Top 5 ---
    top5 = lb_data[:5]
    if top5:
        st.markdown(
            "<div style='text-align:center;margin-bottom:8px;'>"
            "<span style='font-size:1.1em;font-weight:700;color:{};"
            "'>The Jedi Council</span></div>".format(BRAND_GREEN),
            unsafe_allow_html=True,
        )
        cols = st.columns(len(top5))
        for i, entry in enumerate(top5):
            with cols[i]:
                rank = entry.get("rank", i + 1)
                name = entry.get("display_name", "Unknown")
                t_icon = entry.get("tier_icon", "\u2753")
                t_name = entry.get("tier_name", "Unranked")
                level = entry.get("best_level", 0)
                medal = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}.get(rank, "")

                border_col = BRAND_GREEN if rank <= 3 else "#ddd"
                st.markdown(
                    "<div style='text-align:center;padding:16px 8px;"
                    "border:2px solid {};border-radius:12px;"
                    "background:#fafafa;'>"
                    "<div style='font-size:0.8em;color:#888;'>#{}{}</div>"
                    "<div style='font-size:2.2em;margin:4px 0;'>{}</div>"
                    "<div style='font-weight:700;font-size:0.95em;'>{}</div>"
                    "<div style='color:#666;font-size:0.8em;'>{} &bull; Lv {}</div>"
                    "</div>".format(
                        border_col, rank,
                        " " + medal if medal else "",
                        t_icon, name, t_name, level
                    ),
                    unsafe_allow_html=True,
                )

    # --- Full table ---
    if lb_data:
        st.markdown("")
        rows = []
        for entry in lb_data:
            t_icon = entry.get("tier_icon", "")
            t_name = entry.get("tier_name", "Unranked")
            rows.append({
                "Rank": entry.get("rank", 0),
                "Name": entry.get("display_name", ""),
                "Tier": "{} {}".format(t_icon, t_name),
                "Level": entry.get("best_level", 0),
                "Attempts": entry.get("total_attempts", 0),
                "Time": _format_time(entry.get("time_seconds")),
            })
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn(width="small"),
                "Level": st.column_config.NumberColumn(width="small"),
                "Attempts": st.column_config.NumberColumn(width="small"),
            },
        )


# ===================================================================
# HISTORY TAB
# ===================================================================

def _render_history_tab():
    """Show the user's past attempts with expandable detail."""
    if not user_email:
        st.info("Log in to see your history.")
        return

    data = _api_get("/user/{}/history".format(user_email))
    history = data.get("history", []) if isinstance(data, dict) else (data or [])
    if not history:
        st.info("You haven't attempted The Paddock yet. Show us what you can do!")
        return

    st.markdown("### My Attempts")

    rows = []
    for h in history:
        created = h.get("created_at", "")
        # Parse ISO date for display
        try:
            dt = datetime.fromisoformat(created)
            date_str = dt.strftime("%d %b %Y %H:%M")
        except (ValueError, TypeError):
            date_str = created[:16] if created else "--"

        tier_name = h.get("tier_name", "Unranked")
        t_icon = _icon_for_tier(tier_name)
        rows.append({
            "Date": date_str,
            "Tier": "{} {}".format(t_icon, tier_name),
            "Level": h.get("max_level_reached", 0),
            "Questions": "{}/{}".format(
                h.get("total_correct", 0), h.get("total_questions", 0)
            ),
            "Time": _format_time(h.get("time_seconds")),
            "Status": h.get("status", ""),
            "_attempt_id": h.get("id"),
        })

    df = pd.DataFrame(rows)
    display_df = df.drop(columns=["_attempt_id"])
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Expandable detail per attempt
    st.markdown("#### Attempt Detail")
    for i, row in enumerate(rows):
        a_id = row.get("_attempt_id")
        if not a_id:
            continue
        label = "{} | {} | Level {}".format(row["Date"], row["Tier"], row["Level"])
        with st.expander(label):
            detail = _api_get("/attempt/{}".format(a_id))
            if detail and detail.get("responses"):
                for resp in detail["responses"]:
                    lv = resp.get("difficulty_level", 0)
                    was_correct = bool(resp.get("is_correct", 0))
                    icon = "\u2705" if was_correct else "\u274c"
                    q_text = resp.get("question_text", "")
                    st.markdown(
                        "**Lv {}** {} {} &mdash; {}".format(
                            lv, icon,
                            "Correct" if was_correct else "Incorrect",
                            q_text
                        ),
                        unsafe_allow_html=True,
                    )
                    if not was_correct:
                        st.caption("Correct answer: {}".format(
                            resp.get("correct_answer", "")
                        ))
            else:
                st.caption("No detail available for this attempt.")


# ===================================================================
# MAIN ROUTER
# ===================================================================

render_header(
    "The Paddock",
    "**The AI Challenge Arena** | How far can you go?",
    goals=["G3"],
    strategy_context="Legends aren't made in training rooms. They're forged in The Paddock \u2014 real questions, real pressure, real growth.",
)

st.caption("This isn't a quiz — it's the start of your Growing Legends journey.")

state = st.session_state.get("paddock_state", "welcome")

if state == "playing":
    render_playing()
elif state == "result":
    render_result()
else:
    render_welcome()

render_footer("The Paddock", user=user)
