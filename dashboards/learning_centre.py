"""Harris Farm Hub — Learning Centre Dashboard

Pillar 3: Growing Legendary Leadership | Pillar 5: AI Centre of Excellence
Structured around the Prosci ADKAR change management framework:
  Awareness → Desire → Knowledge → Ability → Reinforcement

Learning across 3 core skill areas:
  1. AI Prompting Skills — master effective prompting techniques
  2. Data Prompting — query and analyse Harris Farm transactional data
  3. Company Knowledge — access policies, procedures, and operations info

Role-based personalisation and progress tracking.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st

from shared.styles import render_header, render_footer
from shared.learning_content import (
    MODULES,
    LESSONS,
    PILLARS,
    DIFFICULTY_META,
    RUBRIC_EVALUATOR_PROMPT,
    get_role_priorities,
)
from shared.training_content import (
    BUILDING_BLOCKS,
    CHALLENGES,
    COACH_SYSTEM_PROMPT,
    check_prompt_quality,
)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

user = st.session_state.get("auth_user")
render_header(
    "Learning Centre",
    "**Prompt Academy** — AI & Data Skills for Every Harris Farmer"
)

API_BASE = os.getenv("API_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------

if "lc_user_id" not in st.session_state:
    st.session_state.lc_user_id = "default_user"
if "lc_role" not in st.session_state:
    st.session_state.lc_role = {"function": "", "department": "", "job": ""}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def api_get(path, params=None):
    """GET from the Hub API (cached via wrapper)."""
    # Convert dict params to hashable tuple for caching
    params_key = tuple(sorted(params.items())) if params else ()
    return _api_get_cached(path, params_key)


@st.cache_data(ttl=300, show_spinner=False)
def _api_get_cached(path, params_key):
    try:
        params_dict = dict(params_key) if params_key else None
        resp = requests.get(
            f"{API_BASE}{path}", params=params_dict, timeout=10)
        return resp.json()
    except Exception:
        return {}


def api_post(path, params=None):
    """POST to the Hub API."""
    try:
        resp = requests.post(f"{API_BASE}{path}", params=params, timeout=10)
        return resp.json()
    except Exception:
        return {}


def render_module_card(mod, priority=None):
    """Render a single module info block (no expander)."""
    pillar_info = PILLARS.get(mod.get("pillar", ""), {})
    diff_info = DIFFICULTY_META.get(mod.get("difficulty", "beginner"), {})

    priority_badge = ""
    if priority == "essential":
        priority_badge = " **Essential for your role**"
    elif priority == "recommended":
        priority_badge = " *Recommended*"

    icon = mod.get("icon", pillar_info.get("icon", ""))

    st.markdown(
        f"**{icon} {mod['code']}: {mod['name']}** "
        f"({diff_info.get('label', 'Beginner')} · {mod.get('duration_minutes', 30)} min)"
        f"{priority_badge}"
    )
    st.caption(mod.get("description", ""))

    prereqs = json.loads(mod.get("prerequisites", "[]"))
    if prereqs:
        st.caption(f"Prerequisites: {', '.join(prereqs)}")


def render_lesson_content(lesson, key_prefix="lesson"):
    """Render a lesson's content sections.

    Uses checkboxes instead of expanders for hints/criteria to avoid
    nested-expander errors when rendered inside Streamlit containers.
    """
    content = json.loads(lesson["content"]) if isinstance(lesson["content"], str) else lesson["content"]
    lesson_key = f"{key_prefix}_L{lesson.get('lesson_number', 0)}"

    for i, section in enumerate(content.get("sections", [])):
        stype = section.get("type", "theory")

        if stype == "theory":
            st.markdown(f"### {section.get('title', '')}")
            st.markdown(section.get("body", ""))

        elif stype == "example":
            st.markdown(f"### {section.get('title', '')}")
            col1, col2 = st.columns(2)
            with col1:
                st.error(f"**Weak prompt:**\n\n{section.get('bad', '')}")
            with col2:
                st.success(f"**Strong prompt:**\n\n{section.get('good', '')}")
            st.info(f"**Why?** {section.get('explanation', '')}")

        elif stype == "exercise":
            st.markdown(f"### {section.get('title', '')}")
            st.markdown(section.get("scenario", ""))

            hints = section.get("hints", [])
            if hints:
                if st.checkbox("Show hints", key=f"{lesson_key}_hints_{i}"):
                    for h in hints:
                        st.markdown(f"- {h}")

            criteria = section.get("criteria", [])
            if criteria:
                if st.checkbox("Show success criteria", key=f"{lesson_key}_criteria_{i}"):
                    for c in criteria:
                        st.markdown(f"- {c}")


def render_module_tab(pillar_key, tab_key_prefix):
    """Render a pillar's modules using selectbox navigation.

    This is the shared pattern for the 3 goal tabs. Modules are selected via
    st.selectbox, and lessons render inline at the tab level.
    render_lesson_content() uses checkboxes (not expanders) for hints/criteria.
    """
    modules_data = api_get("/api/learning/modules", {"pillar": pillar_key})
    module_list = modules_data.get("modules", [])

    if not module_list:
        st.info("No modules available yet.")
        return

    # Build labels for the selectbox
    mod_labels = []
    for m in module_list:
        diff_label = DIFFICULTY_META.get(m.get("difficulty", ""), {}).get("label", "")
        mod_labels.append(
            f"{m.get('icon', '')} {m['code']}: {m['name']} "
            f"({diff_label} · {m.get('duration_minutes', 30)} min)"
        )

    selected_idx = st.selectbox(
        "Select a module:",
        range(len(mod_labels)),
        format_func=lambda i: mod_labels[i],
        key=f"{tab_key_prefix}_mod_select",
    )
    mod = module_list[selected_idx]

    st.markdown("---")

    # Module info (inline, not in an expander)
    render_module_card(mod)

    # Fetch and render lessons
    mod_detail = api_get(f"/api/learning/modules/{mod['code']}")
    lessons = mod_detail.get("lessons", [])

    if not lessons:
        st.info("Content coming soon.")
        return

    for lesson in lessons:
        st.markdown("---")
        st.markdown(f"#### Lesson {lesson['lesson_number']}: {lesson['title']}")
        st.caption(
            f"{lesson.get('content_type', 'theory').title()} · "
            f"{lesson.get('duration_minutes', 15)} min"
        )
        render_lesson_content(lesson, key_prefix=f"{tab_key_prefix}_{mod['code']}")

    # Mark complete button
    user_id = st.session_state.lc_user_id
    if st.button(f"Mark {mod['code']} as completed", key=f"complete_{mod['code']}"):
        api_post(
            f"/api/learning/progress/{user_id}/{mod['code']}",
            {"status": "completed", "completion_pct": 100},
        )
        st.success(f"{mod['code']} marked as completed!")
        st.rerun()


# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------

# --- ADKAR Change Management Banner ---
st.markdown(
    "<div style='background:linear-gradient(135deg, #059669 0%, #047857 100%);"
    "color:white;padding:18px 24px;border-radius:10px;margin-bottom:16px;'>"
    "<div style='font-size:1.15em;font-weight:700;margin-bottom:6px;'>"
    "AI Is Your Job Partner — Not Your Replacement</div>"
    "<div style='font-size:0.9em;opacity:0.95;'>"
    "The Prompt Academy follows the <strong>Prosci ADKAR</strong> model: "
    "we help you build <strong>Awareness</strong> of why AI matters, "
    "<strong>Desire</strong> to learn, <strong>Knowledge</strong> of how it works, "
    "<strong>Ability</strong> to use it in your role, and <strong>Reinforcement</strong> "
    "to keep improving. Start wherever you are — we'll help you get better.</div>"
    "</div>",
    unsafe_allow_html=True,
)

# --- ADKAR Stage Indicators ---
adkar_cols = st.columns(5)
adkar_stages = [
    ("Awareness", "Why AI matters", "My Dashboard"),
    ("Desire", "I want to learn", "Company Knowledge"),
    ("Knowledge", "How it works", "AI & Data Skills"),
    ("Ability", "I can do it", "Practice Lab"),
    ("Reinforcement", "Keep improving", "Badges & Progress"),
]
for i, (stage, desc, maps_to) in enumerate(adkar_stages):
    with adkar_cols[i]:
        st.markdown(
            f"<div style='text-align:center;padding:8px;background:#f0fdf4;"
            f"border-radius:8px;border:1px solid #bbf7d0;'>"
            f"<div style='font-weight:700;color:#059669;font-size:0.9em;'>{stage}</div>"
            f"<div style='font-size:0.75em;color:#6b7280;'>{desc}</div>"
            f"<div style='font-size:0.7em;color:#9ca3af;'>{maps_to}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown("")

tab_dashboard, tab_ai, tab_data, tab_kb, tab_lab = st.tabs([
    "My Dashboard",
    "AI Prompting Skills",
    "Data Prompting",
    "Company Knowledge",
    "Practice Lab",
])


# ===== TAB 1: MY DASHBOARD =====
with tab_dashboard:
    st.subheader("My Learning Dashboard")

    # Prompt Academy Level Guide
    with st.expander("Prompt Academy Levels — Your Path"):
        st.markdown("""
| Level | Name | Who It's For | What You'll Learn |
|-------|------|-------------|-------------------|
| 1 | **AI Explorer** | Everyone | What is AI, basic prompting, 5 building blocks |
| 2 | **Prompt Practitioner** | Regular users | Advanced techniques, chain-of-thought, few-shot |
| 3 | **Data Navigator** | Analysts & buyers | HFM data queries, dashboard interpretation |
| 4 | **AI Champion** | Power users | Multi-LLM comparison, template creation |
| 5 | **Citizen Developer** | Innovators | Build automations, create agents, vibe coding |

*Every Harris Farm job is a customer job — AI helps you do it better.*
        """)

    # Role selector
    col_func, col_dept = st.columns(2)
    with col_func:
        function = st.selectbox(
            "Your function:",
            ["", "Retail", "Support Office", "Wholesale"],
            key="lc_function",
        )
    with col_dept:
        department = st.text_input(
            "Your department:",
            placeholder="e.g. Store Management, Buying, Finance",
            key="lc_department",
        )

    if function:
        st.session_state.lc_role["function"] = function
    if department:
        st.session_state.lc_role["department"] = department

    # Fetch progress
    user_id = st.session_state.lc_user_id
    progress_data = api_get(f"/api/learning/progress/{user_id}")
    progress_list = progress_data.get("progress", [])
    progress_by_code = {p["module_code"]: p for p in progress_list}

    # KPI row
    total_modules = 12
    completed = sum(1 for p in progress_list if p.get("status") == "completed")
    in_progress = sum(1 for p in progress_list if p.get("status") == "in_progress")
    completion_pct = (completed / total_modules * 100) if total_modules > 0 else 0
    time_spent = sum(p.get("time_spent_minutes", 0) for p in progress_list)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Completed", f"{completed}/{total_modules}")
    k2.metric("In Progress", in_progress)
    k3.metric("Completion", f"{completion_pct:.0f}%")
    k4.metric("Time Invested", f"{time_spent} min")

    # Per-goal progress bars
    st.markdown("### Progress by Goal")
    all_mods = api_get("/api/learning/modules").get("modules", [])
    for pillar_key, goal_label in [
        ("core_ai", "AI Prompting Skills"),
        ("data", "Data Prompting"),
        ("knowledge", "Company Knowledge"),
    ]:
        pillar_mods = [m for m in all_mods if m.get("pillar") == pillar_key]
        done = sum(
            1 for m in pillar_mods
            if progress_by_code.get(m["code"], {}).get("status") == "completed"
        )
        total = len(pillar_mods)
        pct = done / total if total > 0 else 0
        st.progress(pct, text=f"{goal_label}: {done}/{total} modules completed")

    # Role-based recommendations
    if function:
        st.markdown("### Recommended for Your Role")
        priorities = get_role_priorities(function, department)

        for priority_level in ["essential", "recommended", "optional"]:
            codes = priorities.get(priority_level, [])
            if not codes:
                continue

            label = priority_level.title()
            st.markdown(f"**{label}:**")
            for code in codes:
                status = progress_by_code.get(code, {}).get("status", "not_started")
                icon = {"completed": "done", "in_progress": "hourglass", "not_started": "square"}.get(status, "square")
                mod_info = next((m for m in all_mods if m.get("code") == code), {})
                st.markdown(f":{icon}: **{code}**: {mod_info.get('name', code)}")

    # Quick links
    st.markdown("---")
    st.markdown("### Quick Links")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("[The Rubric — Compare AI Models](/the-rubric)")
    with col2:
        st.markdown("[Prompt Builder — Design Prompts](/prompt-builder)")
    with col3:
        st.markdown("[Hub Assistant — Ask Questions](/hub-assistant)")


# ===== TAB 2: AI PROMPTING SKILLS =====
with tab_ai:
    st.subheader("AI Prompting Skills")
    st.caption("Master prompting techniques from fundamentals to advanced applications")

    # Quick Reference: 5 Building Blocks (from training_content.py)
    with st.expander("Quick Reference: The 5 Building Blocks of Good Prompts"):
        for block in BUILDING_BLOCKS:
            st.markdown(
                f"**{block['icon']}. {block['name']}** — {block['short']}"
            )
            st.caption(f"Tip: {block['tip']}")

    st.markdown("---")
    render_module_tab("core_ai", "ai")


# ===== TAB 3: DATA PROMPTING =====
with tab_data:
    st.subheader("Data Prompting")
    st.caption("Query, analyse, and interpret Harris Farm transactional data with AI assistance")

    render_module_tab("data", "data")


# ===== TAB 4: COMPANY KNOWLEDGE =====
with tab_kb:
    st.subheader("Company Knowledge")
    st.caption("Company policies, procedures, and operational standards")

    # KB search
    st.markdown("**Search the Knowledge Base:**")
    kb_query = st.text_input("Search for policies, procedures, or information...", key="kb_search")

    if kb_query:
        results = api_get("/api/knowledge/search", {"q": kb_query, "limit": 10})
        docs = results.get("results", [])
        if docs:
            st.markdown(f"**{len(docs)} results found:**")
            for doc in docs:
                with st.expander(
                    f"📄 {doc.get('filename', 'Document')} ({doc.get('category', 'General')})"
                ):
                    st.markdown(doc.get("content", "")[:1000])
                    if len(doc.get("content", "")) > 1000:
                        st.caption("... (showing first 1000 characters)")
        else:
            st.info("No results found. Try different keywords or ask the Hub Assistant for help.")

    st.markdown("---")
    render_module_tab("knowledge", "kb")

    # Link to Hub Assistant
    st.markdown("---")
    st.info(
        "**Can't find what you need?** "
        "[Ask the Hub Assistant](/hub-assistant) "
        "— it searches the full Knowledge Base and gives you answers with source references."
    )


# ===== TAB 5: PRACTICE LAB =====
with tab_lab:
    st.subheader("Practice Lab")
    st.caption("Build your prompting skills with challenges, rubric evaluation, and a sandbox")

    lab_mode = st.radio(
        "Choose a tool:",
        ["Practice Challenges", "Rubric Evaluator", "Prompt Sandbox"],
        horizontal=True,
        key="lab_mode",
    )

    # --- Practice Challenges ---
    if lab_mode == "Practice Challenges":
        st.markdown("### Practice Challenges")
        st.markdown(
            "Pick a challenge, write a prompt, and get instant feedback on your "
            "use of the 5 Building Blocks. Optionally get AI coach scoring."
        )

        difficulty = st.radio(
            "Difficulty:", list(CHALLENGES.keys()),
            horizontal=True, key="challenge_difficulty",
        )

        challenge_list = CHALLENGES[difficulty]
        challenge_labels = [f"{c['id']}: {c['title']}" for c in challenge_list]
        challenge_idx = st.selectbox(
            "Select a challenge:", range(len(challenge_labels)),
            format_func=lambda i: challenge_labels[i],
            key="challenge_select",
        )
        challenge = challenge_list[challenge_idx]

        st.markdown(f"**Scenario:** {challenge['scenario']}")

        with st.expander("Hints"):
            for h in challenge.get("hints", []):
                st.markdown(f"- {h}")

        user_prompt = st.text_area(
            "Write your prompt here:",
            height=150,
            placeholder="Apply the 5 Building Blocks: Role, Context, Task, Format, Constraints...",
            key="challenge_prompt",
        )

        col_check, col_coach = st.columns(2)

        with col_check:
            if st.button("Quick Check (instant)", key="quick_check", disabled=not user_prompt):
                result = check_prompt_quality(user_prompt)
                st.markdown(f"### Score: {result['score']}/5 — {result['level']}")
                for block_name, check in result["checks"].items():
                    icon = "white_check_mark" if check["present"] else "x"
                    st.markdown(f":{icon}: **{block_name}**: {check['tip']}")

        with col_coach:
            if st.button("AI Coach (detailed)", key="ai_coach", disabled=not user_prompt):
                with st.spinner("Getting AI coach feedback..."):
                    try:
                        coach_msg = COACH_SYSTEM_PROMPT + f"\n\nChallenge: {challenge['scenario']}\n\nUser's prompt:\n{user_prompt}"
                        resp = requests.post(
                            f"{API_BASE}/api/chat",
                            json={
                                "message": coach_msg,
                                "provider": "claude",
                                "session_id": f"coach_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                "history": [],
                            },
                            timeout=30,
                        )
                        data = resp.json()
                        st.markdown("### AI Coach Feedback")
                        st.markdown(data.get("response", "No response received."))
                    except Exception as e:
                        st.error(f"Could not get coach feedback. ({e})")

        # Success criteria
        with st.expander("Success criteria for this challenge"):
            for c in challenge.get("criteria", []):
                st.markdown(f"- {c}")

    # --- Rubric Evaluator ---
    elif lab_mode == "Rubric Evaluator":
        st.markdown("### Rubric Evaluator")
        st.markdown(
            "Write a prompt and get it scored against 5 criteria. "
            "Each criterion is scored 1-5 for a total out of 25."
        )

        with st.expander("View the 5 scoring criteria"):
            st.markdown("""
| Criteria | What it Measures | Score 1 | Score 5 |
|----------|-----------------|---------|---------|
| **Request Clarity** | Is the prompt clear? | Vague, ambiguous | Crystal clear, specific |
| **Context Provision** | HFM-relevant details? | No context at all | Rich Harris Farm specifics |
| **Data Specification** | What data to use? | No data mentioned | Exact sources named |
| **Output Format** | Desired structure? | No format requested | Precise format defined |
| **Actionability** | Leads to action? | Theoretical only | Every point actionable |
""")

        user_prompt = st.text_area(
            "Write your prompt here:",
            height=150,
            placeholder="e.g. You are a Harris Farm buying analyst. Compare the top 5 fruit suppliers...",
            key="rubric_prompt",
        )

        if st.button("Score My Prompt", key="score_prompt", disabled=not user_prompt):
            with st.spinner("Evaluating your prompt..."):
                eval_prompt = RUBRIC_EVALUATOR_PROMPT.format(user_prompt=user_prompt)
                try:
                    resp = requests.post(
                        f"{API_BASE}/api/chat",
                        json={
                            "message": eval_prompt,
                            "provider": "claude",
                            "session_id": f"rubric_eval_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            "history": [],
                        },
                        timeout=30,
                    )
                    data = resp.json()
                    ai_response = data.get("response", "")

                    try:
                        json_start = ai_response.index("{")
                        json_end = ai_response.rindex("}") + 1
                        result = json.loads(ai_response[json_start:json_end])

                        scores = result.get("scores", {})
                        total = result.get("total", sum(scores.values()))
                        level = result.get("level", "")

                        st.markdown(f"### Score: {total}/25 — {level}")

                        score_cols = st.columns(5)
                        criteria_names = [
                            ("request_clarity", "Request Clarity"),
                            ("context_provision", "Context Provision"),
                            ("data_specification", "Data Specification"),
                            ("output_format", "Output Format"),
                            ("actionability", "Actionability"),
                        ]
                        for i, (key, label) in enumerate(criteria_names):
                            score = scores.get(key, 0)
                            color = "#22c55e" if score >= 4 else "#f59e0b" if score >= 3 else "#ef4444"
                            score_cols[i].markdown(
                                f"<div style='text-align:center;padding:8px;background:{color}20;"
                                f"border-radius:8px;border:2px solid {color};'>"
                                f"<strong>{score}/5</strong><br><small>{label}</small></div>",
                                unsafe_allow_html=True,
                            )

                        st.markdown("---")
                        st.markdown(f"**Feedback:** {result.get('feedback', '')}")

                        improved = result.get("improved_prompt", "")
                        if improved:
                            st.markdown("**Improved version:**")
                            st.success(improved)

                    except (ValueError, json.JSONDecodeError):
                        st.markdown("### AI Feedback")
                        st.markdown(ai_response)

                except Exception as e:
                    st.error(f"Could not evaluate prompt. Is the backend running? ({e})")

            # Update progress
            api_post(
                f"/api/learning/progress/{st.session_state.lc_user_id}/L2",
                {"status": "in_progress", "completion_pct": 50, "time_spent_minutes": 5},
            )

    # --- Prompt Sandbox ---
    else:
        st.markdown("### Prompt Sandbox")
        st.markdown(
            "Test any prompt against one or more AI providers. "
            "See how different models respond to the same input."
        )

        sandbox_prompt = st.text_area(
            "Your prompt:",
            height=120,
            placeholder="Enter any prompt to test...",
            key="sandbox_prompt",
        )

        provider = st.selectbox(
            "AI Provider",
            options=["claude", "chatgpt", "grok"],
            key="sandbox_provider",
        )

        if st.button("Send", key="sandbox_send", disabled=not sandbox_prompt):
            with st.spinner(f"Asking {provider}..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/api/chat",
                        json={
                            "message": sandbox_prompt,
                            "provider": provider,
                            "session_id": f"sandbox_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            "history": [],
                        },
                        timeout=30,
                    )
                    data = resp.json()
                    st.markdown("### Response")
                    st.markdown(data.get("response", "No response received."))

                    if data.get("tokens"):
                        st.caption(f"Tokens: {data['tokens']} · Latency: {data.get('latency_ms', 0):.0f}ms")
                except Exception as e:
                    st.error(f"Could not send prompt. ({e})")


# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown(
    "<div style='background:#f0fdf4;border-left:4px solid #059669;"
    "padding:12px 16px;border-radius:0 8px 8px 0;margin:10px 0;'>"
    "<div style='font-size:0.85em;color:#065f46;'>"
    "<strong>Your Learning Journey:</strong> "
    "The Prompt Academy has 5 levels — from AI Explorer to Citizen Developer. "
    "Every Harris Farmer can learn at their own pace. "
    "AI takes care of the repetitive stuff so you can focus on what matters most: "
    "great food, great service, greater goodness."
    "</div></div>",
    unsafe_allow_html=True,
)
st.caption(
    "Learning Centre | Prompt Academy | 12 modules across 3 pillars | "
    "Prosci ADKAR Change Management | Progress tracked per user"
)

render_footer("Learning Centre", user=user)
