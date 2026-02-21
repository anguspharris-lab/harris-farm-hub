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
from shared.voice_realtime import render_voice_data_box
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
    "**Prompt Academy** \u2014 AI & Data Skills for Every Harris Farmer",
    goals=["G3"],
    strategy_context="Building AI capability across the business \u2014 from Seed to Legend, everyone grows.",
)

# Cross-link to Academy
_pages = st.session_state.get("_pages", {})
if "academy" in _pages:
    st.page_link(_pages["academy"], label="\U0001f31f Explore the Growing Legends Academy — your full capability journey from Seed to Legend", icon=None)

API_BASE = os.getenv("API_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------

if "lc_user_id" not in st.session_state:
    st.session_state.lc_user_id = (user or {}).get("email", "default_user")
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
    """POST to the Hub API (sends as query params for FastAPI)."""
    try:
        resp = requests.post(f"{API_BASE}{path}", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


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
        result = api_post(
            f"/api/learning/progress/{user_id}/{mod['code']}",
            {"status": "completed", "completion_pct": 100},
        )
        if "error" in result:
            st.error(f"Could not save progress: {result['error']}")
        else:
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

# ---------------------------------------------------------------------------
# START HERE — "When In Doubt, Ask AI" (the core lesson)
# ---------------------------------------------------------------------------

with st.expander("**Start Here: When In Doubt, Ask AI** — the one habit that changes everything", expanded=False):

    # --- Hero ---
    st.markdown(
        "<div style='background:linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);"
        "border:2px solid #4ba021;border-radius:12px;padding:24px;margin-bottom:20px;'>"
        "<div style='font-size:1.3em;font-weight:700;color:#166534;margin-bottom:8px;'>"
        "The one thing that changes everything</div>"
        "<div style='font-size:1em;color:#15803d;line-height:1.6;'>"
        "Whenever you're stuck, whenever you have to think hard about something, "
        "whenever you're staring at a screen wondering <em>\"how do I do this?\"</em> "
        "— <strong>just ask AI</strong>. It's sitting right there. It's fast, it's smart, "
        "and it's ready."
        "</div></div>",
        unsafe_allow_html=True,
    )

    # --- The Mindset Shift ---
    st.markdown("### The Mindset Shift")
    col_old, col_new = st.columns(2)
    with col_old:
        st.markdown(
            "<div style='background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;"
            "padding:16px;height:100%;'>"
            "<div style='font-weight:700;color:#6b7280;margin-bottom:10px;'>THE OLD WAY</div>"
            "<div style='font-size:0.9em;color:#6b7280;line-height:1.7;'>"
            "1. <em>\"How do I do this?\"</em><br>"
            "2. Google it for 20 minutes<br>"
            "3. Find 6 conflicting answers<br>"
            "4. Try one. Break something.<br>"
            "5. Ask a colleague (they're busy too)<br>"
            "6. <strong>2 hours later, maybe done</strong>"
            "</div></div>",
            unsafe_allow_html=True,
        )
    with col_new:
        st.markdown(
            "<div style='background:#f0fdf4;border:2px solid #4ba021;border-radius:10px;"
            "padding:16px;height:100%;'>"
            "<div style='font-weight:700;color:#166534;margin-bottom:10px;'>THE NEW WAY</div>"
            "<div style='font-size:0.9em;color:#15803d;line-height:1.7;'>"
            "1. <em>\"How do I do this?\"</em><br>"
            "2. Open Claude. Ask it.<br>"
            "3. Get a clear, tailored answer<br>"
            "4. Try it. It works.<br>"
            "5. If not perfect, say <em>\"change X\"</em><br>"
            "6. <strong>10 minutes later, done</strong>"
            "</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.markdown(
        "**The only thing that changes is WHEN you ask for help — and WHO you ask.** "
        "AI is a colleague who's always available, never judges your question, "
        "responds in seconds, and gets better every time you use it."
    )

    # --- The Three Gears ---
    st.markdown("### The Three Gears")
    st.markdown(
        "Once you start using AI as your default thought partner, "
        "you naturally progress through three gears:"
    )

    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown(
            "<div style='background:#eff6ff;border:2px solid #3b82f6;border-radius:10px;"
            "padding:16px;text-align:center;'>"
            "<div style='font-size:1.8em;'>1</div>"
            "<div style='font-weight:700;color:#1d4ed8;font-size:1.1em;'>ASK</div>"
            "<div style='font-size:0.8em;color:#1e40af;margin-top:4px;'>\"I'm stuck. Help.\"</div>"
            "<hr style='border-color:#bfdbfe;margin:10px 0;'>"
            "<div style='font-size:0.85em;color:#374151;text-align:left;line-height:1.6;'>"
            "You ask AI questions and use its answers. "
            "This alone saves hours every week. "
            "<strong>Most people stay here and that's FINE.</strong> "
            "This is where the majority of value comes from."
            "</div></div>",
            unsafe_allow_html=True,
        )
    with g2:
        st.markdown(
            "<div style='background:#f0fdf4;border:2px solid #22c55e;border-radius:10px;"
            "padding:16px;text-align:center;'>"
            "<div style='font-size:1.8em;'>2</div>"
            "<div style='font-weight:700;color:#166534;font-size:1.1em;'>REFINE</div>"
            "<div style='font-size:0.8em;color:#15803d;margin-top:4px;'>\"Make it better.\"</div>"
            "<hr style='border-color:#bbf7d0;margin:10px 0;'>"
            "<div style='font-size:0.85em;color:#374151;text-align:left;line-height:1.6;'>"
            "You learn that the <strong>quality of AI's output</strong> depends on the "
            "<strong>quality of your input</strong>. Rubrics teach you how to evaluate "
            "and improve both. A 5/10 becomes an 8/10."
            "</div></div>",
            unsafe_allow_html=True,
        )
    with g3:
        st.markdown(
            "<div style='background:#fef3c7;border:2px solid #f59e0b;border-radius:10px;"
            "padding:16px;text-align:center;'>"
            "<div style='font-size:1.8em;'>3</div>"
            "<div style='font-weight:700;color:#92400e;font-size:1.1em;'>BUILD</div>"
            "<div style='font-size:0.8em;color:#a16207;margin-top:4px;'>\"Automate it.\"</div>"
            "<hr style='border-color:#fde68a;margin:10px 0;'>"
            "<div style='font-size:0.85em;color:#374151;text-align:left;line-height:1.6;'>"
            "Use Claude.ai (the Brain) to <strong>design</strong> what you want. "
            "Use Claude Code (the Hands) to <strong>build</strong> it. "
            "Use Claude.ai again to <strong>review</strong>. "
            "You don't need to be technical."
            "</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.markdown("**There is no wrong gear.** Someone in Gear 1 who asks AI 10 questions a day is getting massive value.")

    # --- Real Examples (collapsed) ---
    st.markdown("### Real Harris Farm Examples")

    with st.expander("Store Manager — Gear 1 (Ask)"):
        st.markdown(
            "**Monday morning. Sales were down over the weekend. Manager doesn't know why.**\n\n"
            "**Old way:** Spend an hour pulling reports, comparing numbers, ringing head office.\n\n"
            "**New way:** *\"Here's my store's weekend sales data. What happened? "
            "What categories dropped? What should I focus on today?\"*\n\n"
            "**AI response in 30 seconds:** *\"Fruit & Veg was down 12% — looks like the avocado "
            "promotion ended but wasn't replaced. Deli held steady. Suggest featuring stone fruit "
            "this week, they're in peak season and margin is strong.\"*\n\n"
            "**Time saved:** 45 minutes. **Better insight:** Yes — AI spotted the promotion gap."
        )

    with st.expander("Buyer — Gear 2 (Refine)"):
        st.markdown(
            "**Buyer needs to negotiate with a new organic supplier.**\n\n"
            "**First attempt:** *\"Help me prepare for a supplier meeting\"* — AI gives generic advice. 5/10.\n\n"
            "**Refined attempt:** *\"I'm meeting a new organic egg supplier tomorrow. We currently pay "
            "$X per dozen. The new supplier offers free-range at $Y but minimum order is 500 dozen/week "
            "across 15 stores. Our current weekly volume is 380 dozen. Help me: "
            "1) Calculate if the volume commitment works, "
            "2) Identify negotiation leverage points, "
            "3) Draft 3 key questions, "
            "4) Flag any risks.\"*\n\n"
            "**Result:** Comprehensive prep pack. 9/10. The difference wasn't AI skill — it was **clarity of input**."
        )

    with st.expander("Finance Team — Gear 3 (Build)"):
        st.markdown(
            "**Finance spends 4 hours every Monday building a margin report from spreadsheets.**\n\n"
            "**Step 1 — Think (Claude.ai):** *\"I want to automate our Monday margin report. "
            "Here's what it looks like. Here's the data source. It needs to run automatically.\"* "
            "Claude.ai designs the complete spec.\n\n"
            "**Step 2 — Build (Claude Code):** Paste the spec. Claude Code builds it.\n\n"
            "**Step 3 — Review (Claude.ai):** *\"Does it match the spec? What's missing?\"*\n\n"
            "**Result:** 4 hours/week to 0 hours/week. The report runs itself. "
            "Finance spends Monday morning on analysis, not assembly."
        )

    # --- Call to Action ---
    st.markdown("---")
    st.markdown(
        "<div style='background:linear-gradient(135deg, #166534 0%, #059669 100%);"
        "color:white;border-radius:12px;padding:24px;text-align:center;'>"
        "<div style='font-size:1.2em;font-weight:700;margin-bottom:10px;'>"
        "Start Right Now</div>"
        "<div style='font-size:0.95em;line-height:1.7;max-width:600px;margin:0 auto;'>"
        "Think of <strong>one thing</strong> you did this week that was tedious, confusing, "
        "or took longer than it should. Open Claude. Describe it exactly as you'd tell a colleague: "
        "<em>\"Hey, I need to [thing]. I've got [context]. Can you help?\"</em><br><br>"
        "That's it. That's the whole skill. Everything else follows."
        "</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("")
    st.markdown(
        "<div style='text-align:center;padding:12px;background:#f9fafb;border-radius:8px;"
        "border:1px solid #e5e7eb;font-size:0.9em;color:#374151;'>"
        "AI is not a tool you need to learn. "
        "It's a colleague you need to <strong>remember to ask</strong>."
        "</div>",
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
    _pages = st.session_state.get("_pages", {})
    col1, col2, col3 = st.columns(3)
    with col1:
        if "the-rubric" in _pages:
            st.page_link(_pages["the-rubric"], label="The Rubric — Compare AI Models", use_container_width=True)
    with col2:
        if "prompt-builder" in _pages:
            st.page_link(_pages["prompt-builder"], label="Prompt Builder — Design Prompts", use_container_width=True)
    with col3:
        if "hub-assistant" in _pages:
            st.page_link(_pages["hub-assistant"], label="Hub Assistant — Ask Questions", use_container_width=True)


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
    st.caption("Ask questions or search company policies, procedures, and operational standards")

    kb_mode = st.radio(
        "Mode:",
        ["Ask a Question", "Search Documents"],
        horizontal=True,
        key="kb_mode",
    )

    if kb_mode == "Ask a Question":
        from shared.kb_chat import render_kb_chat

        render_kb_chat(
            key_prefix="lc_kb",
            provider="claude",
            category=None,
            show_suggestions=True,
            suggestions=[
                "What are the golden rules for Fruit & Veg?",
                "How do I process a Dayforce leave request?",
                "What are the food safety temperature rules?",
            ],
            compact=True,
        )
    else:
        st.markdown("**Search the Knowledge Base:**")
        kb_query = st.text_input(
            "Search for policies, procedures, or information...",
            key="kb_search",
        )

        if kb_query:
            results = api_get("/api/knowledge/search", {"q": kb_query, "limit": 10})
            docs = results.get("results", [])
            if docs:
                st.markdown(f"**{len(docs)} results found:**")
                for doc in docs:
                    with st.expander(
                        f"📄 {doc.get('filename', 'Document')} ({doc.get('category', 'General')})"
                    ):
                        st.markdown(doc.get("snippet", doc.get("content", "No preview available.")))
                        word_count = doc.get("word_count", 0)
                        if word_count:
                            st.caption(
                                f"{word_count} words | "
                                f"Chunk {doc.get('chunk_index', 0) + 1} of {doc.get('chunk_total', 1)}"
                            )
            else:
                st.info(
                    "No results found. Switch to **Ask a Question** mode "
                    "for AI-powered answers."
                )

    st.markdown("---")
    render_module_tab("knowledge", "kb")

    # Link to Hub Assistant (session-safe)
    st.markdown("---")
    _pages_kb = st.session_state.get("_pages", {})
    if "hub-assistant" in _pages_kb:
        st.info(
            "**Need more help?** Use the full Hub Assistant for deeper "
            "conversations with AI provider selection and conversation history."
        )
        st.page_link(
            _pages_kb["hub-assistant"],
            label="Open Hub Assistant",
            icon="\U0001f4ac",
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
                f"/api/learning/progress/{st.session_state.lc_user_id}/RUBRIC_EVAL",
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

render_voice_data_box("general")

render_footer("Learning Centre", user=user)
