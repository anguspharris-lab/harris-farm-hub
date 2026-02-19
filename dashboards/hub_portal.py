"""
Harris Farm Hub — Documentation Portal
Centralized documentation, data catalog, AI showcase, prompt library,
and gamified scoreboard. Port 8515.
"""

import json
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

from shared.styles import render_header, render_footer
from shared.portal_content import (
    load_doc, load_procedure, load_learning, load_rubric,
    get_doc_index, get_procedure_index, get_learning_index,
    search_all_docs, parse_audit_metrics, get_data_sources,
    MILESTONES, POINT_ACTIONS_AI, POINT_ACTIONS_HUMAN,
    SHOWCASE_IMPLEMENTATIONS,
)
from shared.agent_teams import (
    AGENT_TEAMS, DEPARTMENT_AGENTS, EVALUATION_TIERS, BUSINESS_UNITS,
    EVALUATION_MAX_SCORE, IMPLEMENTATION_THRESHOLD,
    ARENA_ACHIEVEMENTS, TEAM_POINT_ACTIONS,
    DATA_INTELLIGENCE_AGENTS, DATA_INTEL_CATEGORIES,
    get_team, get_agent, get_agents_by_unit, get_agents_by_team,
    get_data_intel_agent, calculate_proposal_score,
)
from shared.watchdog_safety import (
    RISK_LEVELS, RISK_COLORS, RISK_ICONS, SYSTEM_STATUS,
)

API_URL = "http://localhost:8000"


# ---------------------------------------------------------------------------
# CACHED API HELPERS — prevent re-fetching on every Streamlit rerun
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_templates():
    try:
        resp = requests.get("{}/api/templates".format(API_URL), timeout=5)
        return resp.json().get("templates", []) if resp.ok else []
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def _fetch_prompt_history(user_id):
    try:
        resp = requests.get(
            "{}/api/portal/prompt-history".format(API_URL),
            params={"user_id": user_id, "limit": 30}, timeout=5)
        return resp.json().get("prompts", []) if resp.ok else []
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def _fetch_leaderboard():
    try:
        resp = requests.get(
            "{}/api/portal/leaderboard".format(API_URL),
            params={"period": "all"}, timeout=5)
        return resp.json().get("leaderboard", []) if resp.ok else []
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def _fetch_achievements(user_id):
    try:
        resp = requests.get(
            "{}/api/portal/achievements/{}".format(API_URL, user_id),
            timeout=5)
        return resp.json().get("achievements", []) if resp.ok else []
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def _fetch_leaderboard_period(period):
    try:
        resp = requests.get(
            "{}/api/portal/leaderboard".format(API_URL),
            params={"period": period}, timeout=5)
        return resp.json().get("leaderboard", []) if resp.ok else []
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_arena_stats():
    try:
        return requests.get(
            "{}/api/arena/stats".format(API_URL), timeout=5).json()
    except Exception:
        return {"proposals": {}, "insights": {}, "categories": [],
                "total_agents": 0}


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_arena_leaderboard():
    try:
        return requests.get(
            "{}/api/arena/leaderboard".format(API_URL), timeout=5
        ).json().get("leaderboard", [])
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_arena_proposals():
    try:
        return requests.get(
            "{}/api/arena/proposals".format(API_URL),
            params={"limit": 50}, timeout=5
        ).json().get("proposals", [])
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_arena_insights():
    try:
        return requests.get(
            "{}/api/arena/insights".format(API_URL),
            params={"limit": 50}, timeout=5
        ).json().get("insights", [])
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_di_data():
    try:
        return requests.get(
            "{}/api/arena/data-intelligence".format(API_URL), timeout=5
        ).json()
    except Exception:
        return {
            "agents": [], "categories": [], "insights": [],
            "summary": {"total_agents": 0, "total_insights": 0,
                        "total_impact": 0, "avg_confidence": 0},
            "category_stats": {},
        }


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_intelligence_reports():
    try:
        return requests.get(
            "{}/api/intelligence/reports".format(API_URL),
            params={"limit": 50}, timeout=5
        ).json().get("reports", [])
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_intelligence_detail(report_id):
    try:
        return requests.get(
            "{}/api/intelligence/reports/{}".format(API_URL, report_id),
            timeout=5
        ).json()
    except Exception:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_watchdog_status():
    try:
        return requests.get(
            "{}/api/watchdog/status".format(API_URL), timeout=5).json()
    except Exception:
        return {
            "system": SYSTEM_STATUS,
            "metrics": {"total_proposals": 0, "pending_review": 0,
                        "approved": 0, "rejected": 0,
                        "blocked_by_watchdog": 0},
            "risk_distribution": {},
        }


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_watchdog_pending():
    try:
        return requests.get(
            "{}/api/watchdog/pending".format(API_URL), timeout=5
        ).json().get("pending", [])
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_watchdog_all():
    try:
        return requests.get(
            "{}/api/watchdog/proposals".format(API_URL), timeout=5
        ).json().get("proposals", [])
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_watchdog_audit():
    try:
        return requests.get(
            "{}/api/watchdog/audit".format(API_URL), timeout=5).json()
    except Exception:
        return {"audits": [], "decisions": []}


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_agent_tasks():
    try:
        return requests.get(
            "{}/api/agent-tasks".format(API_URL),
            params={"limit": 20}, timeout=5
        ).json().get("tasks", [])
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_si_status():
    try:
        return requests.get(
            "{}/api/self-improvement/status".format(API_URL), timeout=5
        ).json()
    except Exception:
        return {}


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_si_history():
    try:
        return requests.get(
            "{}/api/self-improvement/history".format(API_URL), timeout=5
        ).json()
    except Exception:
        return {"cycles": [], "score_trends": []}


@st.cache_data(ttl=15, show_spinner=False)
def _fetch_agent_proposals(status=None):
    try:
        params = {"limit": 50}
        if status:
            params["status"] = status
        return requests.get(
            "{}/api/admin/agent-proposals".format(API_URL),
            params=params, timeout=5,
        ).json().get("proposals", [])
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_agent_scores():
    try:
        return requests.get(
            "{}/api/admin/agent-scores".format(API_URL), timeout=5
        ).json()
    except Exception:
        return {"scores": [], "agent_averages": []}


@st.cache_data(ttl=10, show_spinner=False)
def _fetch_executor_status():
    try:
        return requests.get(
            "{}/api/admin/executor/status".format(API_URL), timeout=5
        ).json()
    except Exception:
        return {"queue": {}, "approved_waiting": 0}


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_ci_findings(status=None, category=None):
    try:
        params = {"limit": 50}
        if status:
            params["status"] = status
        if category:
            params["category"] = category
        return requests.get(
            "{}/api/continuous-improvement/findings".format(API_URL),
            params=params, timeout=5,
        ).json().get("findings", [])
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_ci_metrics():
    try:
        return requests.get(
            "{}/api/continuous-improvement/metrics".format(API_URL), timeout=5
        ).json()
    except Exception:
        return {}


@st.cache_data(ttl=15, show_spinner=False)
def _fetch_game_leaderboard():
    try:
        return requests.get(
            "{}/api/game/leaderboard".format(API_URL), timeout=5
        ).json().get("agents", [])
    except Exception:
        return []


@st.cache_data(ttl=15, show_spinner=False)
def _fetch_game_status():
    try:
        return requests.get(
            "{}/api/game/status".format(API_URL), timeout=5
        ).json()
    except Exception:
        return {}


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_game_achievements():
    try:
        return requests.get(
            "{}/api/game/achievements".format(API_URL), timeout=5
        ).json().get("achievements", [])
    except Exception:
        return []


user = st.session_state.get("auth_user")
render_header(
    "Hub Documentation Portal",
    "**Procedures, data catalog, AI showcase, prompt intelligence "
    "& gamified learning** | Your single source of truth",
)


# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "Documentation", "Data Catalog", "Showcase",
    "Prompt Library", "Scoreboard", "The Arena", "Agent Network",
    "Data Intelligence", "WATCHDOG Safety", "Self-Improvement",
    "Agent Control",
])


# ============================================================================
# TAB 1: DOCUMENTATION
# ============================================================================

with tab1:
    st.subheader("Documentation Browser")

    # Search bar
    search_q = st.text_input("Search all documentation",
                              placeholder="e.g. fiscal calendar, WATCHDOG, API...",
                              key="portal_search")
    if search_q and len(search_q.strip()) >= 2:
        results = search_all_docs(search_q)
        if results:
            st.markdown("**{} matches found**".format(len(results)))
            for r in results[:20]:
                with st.expander("{} / {} (line {})".format(
                        r["source"], r["name"], r["line_number"])):
                    st.code(r["context"], language="markdown")
        else:
            st.info("No matches found.")
        st.markdown("---")

    # Category selector
    DOC_CATEGORIES = {
        "Guides": [
            ("USER_GUIDE", "User Guide"),
            ("RUNBOOK", "Operations Runbook"),
        ],
        "Architecture": [
            ("ARCHITECTURE", "System Architecture"),
            ("DECISIONS", "Architecture Decisions (ADRs)"),
        ],
        "Data": [
            ("data_catalog", "Data Catalog"),
            ("fiscal_calendar_profile", "Fiscal Calendar Profile"),
        ],
        "Quality": [
            ("DESIGN_USABILITY_RUBRIC", "Design & Usability Rubric"),
            ("CHANGELOG", "Changelog"),
        ],
    }

    col_cat, col_doc = st.columns([1, 3])

    with col_cat:
        st.markdown("**Categories**")

        # Documents
        for cat_name, docs in DOC_CATEGORIES.items():
            st.markdown("**{}**".format(cat_name))
            for doc_key, doc_label in docs:
                if st.button(doc_label, key="doc_{}".format(doc_key),
                              use_container_width=True):
                    st.session_state["portal_active_doc"] = (
                        "doc", doc_key, doc_label)

        # Procedures
        st.markdown("**Procedures**")
        for p in get_procedure_index():
            label = p["name"].replace("_", " ").title()
            if st.button(label, key="proc_{}".format(p["name"]),
                          use_container_width=True):
                st.session_state["portal_active_doc"] = (
                    "procedure", p["name"], label)

        # Learnings
        st.markdown("**Learnings**")
        for l in get_learning_index():
            label = l["name"].replace("_", " ").title()
            if st.button(label, key="learn_{}".format(l["name"]),
                          use_container_width=True):
                st.session_state["portal_active_doc"] = (
                    "learning", l["filename"], label)

    with col_doc:
        active = st.session_state.get("portal_active_doc")
        if active:
            doc_type, doc_key, doc_label = active
            st.markdown("### {}".format(doc_label))

            if doc_type == "doc":
                content = load_doc(doc_key)
            elif doc_type == "procedure":
                content = load_procedure(doc_key)
            elif doc_type == "learning":
                content = load_learning(doc_key)
            else:
                content = None

            if content:
                st.markdown(content)
            else:
                st.warning("Document not found: {}".format(doc_key))
        else:
            # Default: show index
            st.markdown("### Welcome to the Hub Documentation Portal")
            st.markdown(
                "Select a document from the left panel to view it here.\n\n"
                "**Available content:**"
            )
            docs = get_doc_index()
            procs = get_procedure_index()
            learns = get_learning_index()
            d1, d2, d3 = st.columns(3)
            d1.metric("Documents", len(docs))
            d2.metric("Procedures", len(procs))
            d3.metric("Learnings", len(learns))

            st.markdown("**Documents:**")
            for d in docs:
                st.caption("{} ({} KB, modified {})".format(
                    d["filename"], d["size_kb"], d["modified"]))


# ============================================================================
# TAB 2: DATA CATALOG
# ============================================================================

with tab2:
    st.subheader("Data Catalog")

    sources = get_data_sources()

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Data Sources", len(sources))
    k2.metric("Total Rows", "383M+")
    k3.metric("Total Size", "7+ GB")
    k4.metric("Products", "72,911")

    st.markdown("---")

    # Data source cards
    for src in sources:
        with st.expander("{} ({})".format(src["name"], src["type"])):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown("**Source:** {}".format(src["source"]))
                st.markdown("**Grain:** {}".format(src["grain"]))
                st.markdown("**Period:** {}".format(src["period"]))
                st.markdown("**Size:** {} ({} rows)".format(
                    src["size"], src["rows"]))
                if src["stores"]:
                    st.markdown("**Stores:** {}".format(src["stores"]))
                st.markdown("**Join Key:** `{}`".format(src["join_key"]))

            with c2:
                st.markdown("**Used by:**")
                for dash in src["used_by"]:
                    st.markdown("- {}".format(dash))

            # Schema table
            st.markdown("**Schema:**")
            schema_df = pd.DataFrame(
                src["columns"],
                columns=["Column", "Type", "Description"],
            )
            st.dataframe(schema_df, hide_index=True)

    # Data relationships
    st.markdown("---")
    st.markdown("### Data Relationships & Join Keys")
    st.markdown("""
| Source | Join Key | Target | Match Rate |
|--------|----------|--------|------------|
| Transactions | `PLUItem_ID` | Product Hierarchy `ProductNumber` | 98.3% by PLU |
| Transactions | `CAST(SaleDate AS DATE)` | Fiscal Calendar `TheDate` | 100% (959/959 dates) |
| Weekly Aggregated | `Store + Department` | Store Master | 100% |
| Hub Metadata | Internal keys | Learning modules, roles | N/A |
""")


# ============================================================================
# TAB 3: SHOWCASE
# ============================================================================

with tab3:
    st.subheader("AI Centre of Excellence")

    # Audit metrics
    metrics = parse_audit_metrics()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tasks Completed", metrics["task_count"])
    avg = metrics["avg_scores"]
    m2.metric("Avg Score", "{}/10".format(avg.get("avg", "N/A")))
    m3.metric("Dashboards", "16")
    m4.metric("Tests", "657+")

    # WATCHDOG Governance
    st.markdown("---")
    st.markdown("### WATCHDOG Governance System")

    w1, w2 = st.columns([2, 1])
    with w1:
        st.markdown("""
**7 Immutable Laws:**
1. Honest code - behaviour matches names
2. Full audit trail - no gaps
3. Test before ship - min 1 success + 1 failure per function
4. Zero secrets in code - .env only
5. Operator authority - Gus Harris only
6. Data correctness - every output traceable to source
7. Document everything - no undocumented features
""")

    with w2:
        # Score radar chart
        if avg:
            criteria = ["H", "R", "S", "C", "D", "U", "X"]
            labels = ["Honest", "Reliable", "Safe", "Clean",
                       "Data Correct", "Usable", "Documented"]
            values = [avg.get(c, 0) for c in criteria]
            values.append(values[0])  # close the polygon
            labels.append(labels[0])

            fig_radar = go.Figure(data=go.Scatterpolar(
                r=values, theta=labels, fill="toself",
                line_color="#0d9488",
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                height=300, margin=dict(l=40, r=40, t=20, b=20),
            )
            st.plotly_chart(fig_radar,
                            key="watchdog_radar")

    # Rubric scores detail
    if avg:
        score_cols = st.columns(7)
        criteria_full = ["Honest", "Reliable", "Safe", "Clean",
                          "DataCorrect", "Usable", "Documented"]
        for i, (key, name) in enumerate(zip(
                ["H", "R", "S", "C", "D", "U", "X"], criteria_full)):
            score_cols[i].metric(name, "{}/10".format(avg.get(key, "?")))

    # Key implementations
    st.markdown("---")
    st.markdown("### Key Implementations")

    # 2 columns of cards
    for i in range(0, len(SHOWCASE_IMPLEMENTATIONS), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(SHOWCASE_IMPLEMENTATIONS):
                impl = SHOWCASE_IMPLEMENTATIONS[idx]
                with col:
                    st.markdown("**{}**".format(impl["name"]))
                    st.caption(impl["stats"])
                    st.markdown(impl["desc"])
                    st.caption("Dashboard: {}".format(impl["dashboard"]))

    # Score trend
    if metrics["score_entries"]:
        st.markdown("---")
        st.markdown("### Score Trend Over Time")
        df_scores = pd.DataFrame(metrics["score_entries"])
        df_scores["task_num"] = range(1, len(df_scores) + 1)
        fig_trend = px.line(
            df_scores, x="task_num", y="avg",
            labels={"task_num": "Task #", "avg": "Average Score"},
            markers=True,
        )
        fig_trend.update_layout(height=300)
        fig_trend.add_hline(y=7, line_dash="dash", line_color="red",
                             annotation_text="Pass threshold (7.0)")
        st.plotly_chart(fig_trend,
                        key="score_trend")


# ============================================================================
# TAB 4: PROMPT LIBRARY
# ============================================================================

with tab4:
    st.subheader("Prompt Library & Intelligence")

    lib_tab1, lib_tab2, lib_tab3 = st.tabs([
        "Browse Library", "My History", "Submit Prompt",
    ])

    with lib_tab1:
        st.markdown("**Saved Prompt Templates**")
        templates = _fetch_templates()
        if templates:
            for t in templates[:20]:
                with st.expander("{} ({})".format(
                        t.get("title", "Untitled"),
                        t.get("category", "General"))):
                    st.markdown(t.get("description", ""))
                    st.code(t.get("template", ""), language="text")
                    c1, c2, c3 = st.columns(3)
                    c1.caption("Uses: {}".format(t.get("uses", 0)))
                    c2.caption("Rating: {}".format(
                        t.get("avg_rating", "N/A")))
                    c3.caption("Difficulty: {}".format(
                        t.get("difficulty", "?")))
        else:
            st.info("No prompt templates saved yet. "
                    "Use the Prompt Builder (port 8504) to create some.")

    with lib_tab2:
        st.markdown("**My Prompt History**")
        user_id = (user or {}).get("email", "anonymous")
        prompts = _fetch_prompt_history(user_id)
        if prompts:
            for p in prompts:
                with st.expander("{} - {}".format(
                        p.get("created_at", ""),
                        p["prompt_text"][:80])):
                    st.markdown("**Prompt:**")
                    st.text(p["prompt_text"])
                    if p.get("outcome"):
                        st.markdown("**Outcome:** {}".format(
                            p["outcome"]))
                    if p.get("ai_review"):
                        st.markdown("**AI Review:** {}".format(
                            p["ai_review"]))
                    if p.get("rating"):
                        st.markdown("**Rating:** {}/5".format(
                            p["rating"]))
        else:
            st.info("No prompt history yet. Submit prompts "
                    "in the 'Submit Prompt' tab.")

    with lib_tab3:
        st.markdown("**Submit & Review a Prompt**")
        prompt_text = st.text_area(
            "Your prompt", height=150,
            placeholder="Paste a prompt you used or want to improve...",
            key="portal_submit_prompt",
        )
        prompt_context = st.text_input(
            "Context (optional)",
            placeholder="What was this prompt for?",
            key="portal_prompt_context",
        )
        prompt_outcome = st.text_input(
            "Outcome (optional)",
            placeholder="What was the result?",
            key="portal_prompt_outcome",
        )
        prompt_rating = st.slider("Rate this prompt", 1, 5, 3,
                                   key="portal_prompt_rating")

        if st.button("Save to History", key="portal_save_prompt"):
            if prompt_text.strip():
                user_id = (user or {}).get("email", "anonymous")
                try:
                    resp = requests.post(
                        "{}/api/portal/prompt-history".format(API_URL),
                        json={
                            "user_id": user_id,
                            "prompt_text": prompt_text,
                            "context": prompt_context,
                            "outcome": prompt_outcome,
                            "rating": prompt_rating,
                        },
                        timeout=5,
                    )
                    if resp.ok:
                        st.success("Prompt saved to history.")
                    else:
                        st.error("Failed to save prompt.")
                except Exception:
                    st.warning("Backend not available.")
            else:
                st.warning("Please enter a prompt.")


# ============================================================================
# TAB 5: SCOREBOARD
# ============================================================================

with tab5:
    st.subheader("Gamified Scoreboard")

    user_id = (user or {}).get("email", "anonymous")

    # Load scores (cached)
    leaderboard = _fetch_leaderboard()

    # Calculate user total
    user_total = sum(
        e["total_points"] for e in leaderboard
        if e["user_id"] == user_id
    )

    # Determine level
    current_level = "Starter"
    current_icon = "\U0001f331"
    next_milestone = MILESTONES[0]["points"]
    for m in MILESTONES:
        if user_total >= m["points"]:
            current_level = m["label"]
            current_icon = m["icon"]
        else:
            next_milestone = m["points"]
            break

    # KPI row
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Points", "{:,}".format(user_total))
    s2.metric("Level", "{} {}".format(current_icon, current_level))
    s3.metric("Next Milestone", "{:,} pts".format(next_milestone))

    # Achievements count (cached)
    achievements = _fetch_achievements(user_id)
    s4.metric("Achievements", len(achievements))

    # Milestone badges
    st.markdown("---")
    st.markdown("### Milestones")
    badge_cols = st.columns(len(MILESTONES))
    earned_codes = {a["achievement_code"] for a in achievements}
    for i, m in enumerate(MILESTONES):
        with badge_cols[i]:
            earned = (m["code"] in earned_codes
                       or user_total >= m["points"])
            status = "Earned" if earned else "Locked"
            st.markdown(
                "**{icon} {name}**\n\n"
                "{pts:,} points\n\n"
                "*{label}*\n\n"
                "{status}".format(
                    icon=m["icon"], name=m["name"],
                    pts=m["points"], label=m["label"],
                    status=status,
                )
            )

    # Leaderboard
    st.markdown("---")
    st.markdown("### Leaderboard")

    period = st.radio("Period", ["All Time", "This Month", "This Week"],
                       horizontal=True, key="portal_lb_period")
    period_map = {"All Time": "all", "This Month": "month",
                   "This Week": "week"}
    lb_data = _fetch_leaderboard_period(period_map[period])

    if lb_data:
        df_lb = pd.DataFrame(lb_data)
        st.dataframe(
            df_lb[["user_id", "category", "total_points", "actions"]], hide_index=True,
        )
    else:
        st.info("No scores yet. Start earning points!")

    # How to earn points
    st.markdown("---")
    st.markdown("### How to Earn Points")

    hp_col, ap_col = st.columns(2)
    with hp_col:
        st.markdown("**Human Points**")
        for a in POINT_ACTIONS_HUMAN:
            st.markdown("- **+{pts}** {label}".format(
                pts=a["points"], label=a["label"]))

    with ap_col:
        st.markdown("**AI Points**")
        for a in POINT_ACTIONS_AI:
            st.markdown("- **+{pts}** {label}".format(
                pts=a["points"], label=a["label"]))

    # Quick award button (for demo/testing)
    st.markdown("---")
    with st.expander("Award Points (Admin)"):
        award_user = st.text_input("User ID", value=user_id,
                                    key="portal_award_user")
        award_pts = st.number_input("Points", min_value=1, max_value=100,
                                     value=5, key="portal_award_pts")
        award_cat = st.selectbox("Category", ["human", "ai"],
                                  key="portal_award_cat")
        award_reason = st.text_input("Reason", key="portal_award_reason")
        if st.button("Award", key="portal_award_btn"):
            try:
                resp = requests.post(
                    "{}/api/portal/score".format(API_URL),
                    json={
                        "user_id": award_user,
                        "points": award_pts,
                        "category": award_cat,
                        "reason": award_reason,
                    },
                    timeout=5,
                )
                if resp.ok:
                    total = resp.json().get("total_points", 0)
                    st.success("Awarded {} points. Total: {:,}".format(
                        award_pts, total))
                    _fetch_leaderboard.clear()
                    _fetch_achievements.clear()
                    st.rerun()
            except Exception:
                st.warning("Backend not available.")

    # --- AI Agent Competition ---
    st.markdown("---")
    st.markdown("### AI Agent Competition")
    st.caption("6 AI agents competing to deliver business value through analysis, reports, and revenue discovery.")

    game_agents = _fetch_game_leaderboard()
    game_stats = _fetch_game_status()

    if not game_agents:
        st.info("No game agents seeded yet.")
        if st.button("Initialize 6 Competing Agents", key="portal_seed_game"):
            try:
                resp = requests.post(
                    "{}/api/game/seed".format(API_URL), timeout=10)
                if resp.ok:
                    data = resp.json()
                    st.success("Seeded {} agents and {} tasks.".format(
                        data.get("agents_inserted", 0),
                        data.get("tasks_inserted", 0)))
                    _fetch_game_leaderboard.clear()
                    _fetch_game_status.clear()
                    st.rerun()
            except Exception:
                st.warning("Backend not available.")
    else:
        # KPI row
        gk1, gk2, gk3, gk4 = st.columns(4)
        gk1.metric("Total Agent Points",
                    "{:,}".format(game_stats.get("total_points", 0)))
        gk2.metric("Revenue Found",
                    "${:,.0f}".format(game_stats.get("total_revenue", 0)))
        gk3.metric("Reports Completed",
                    str(game_stats.get("total_reports", 0)))
        gk4.metric("Avg Rubric Score",
                    "{:.1f}/10".format(game_stats.get("avg_rubric_score", 0)))

        # Leaderboard table
        rank_icons = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}
        lb_rows = []
        for agent in game_agents:
            rank = agent["rank"]
            icon = rank_icons.get(rank, "")
            lb_rows.append({
                "Rank": "{} #{}".format(icon, rank).strip(),
                "Agent": agent["name"],
                "Points": "{:,}".format(agent["total_points"]),
                "Reports": agent["reports_completed"],
                "Revenue": "${:,.0f}".format(agent["revenue_found"]),
                "Avg Score": "{:.1f}".format(agent["avg_rubric_score"]),
                "Category": agent["category"],
            })

        if lb_rows:
            df_game = pd.DataFrame(lb_rows)
            st.dataframe(df_game, hide_index=True, use_container_width=True)

        # Achievements
        game_achs = _fetch_game_achievements()
        if game_achs:
            with st.expander("Achievements Earned ({})".format(len(game_achs))):
                for ach in game_achs[:20]:
                    st.markdown("- **{}**: {} (+{} pts) — {}".format(
                        ach["agent_name"], ach["achievement_name"],
                        ach["points_awarded"], ach.get("earned_at", "")[:10]))

        # Execute button
        exec_status = _fetch_executor_status()
        approved = exec_status.get("approved_waiting", 0)
        if approved > 0:
            st.info("{} approved tasks waiting for execution.".format(approved))
            if st.button("Execute All Approved Tasks", key="portal_exec_game"):
                try:
                    resp = requests.post(
                        "{}/api/admin/executor/run".format(API_URL), timeout=30)
                    if resp.ok:
                        data = resp.json()
                        st.success("Executed {} tasks.".format(
                            data.get("executed", 0)))
                        _fetch_game_leaderboard.clear()
                        _fetch_game_status.clear()
                        _fetch_game_achievements.clear()
                        st.rerun()
                except Exception:
                    st.warning("Execution timed out or backend unavailable.")


# ============================================================================
# TAB 6: THE ARENA — Agent Competition Dashboard
# ============================================================================

with tab6:
    st.subheader("The Arena")
    st.caption(
        "5 autonomous agent teams competing to deliver the most impactful "
        "AI-driven proposals for Harris Farm Markets"
    )

    # Fetch arena data (cached)
    arena_stats = _fetch_arena_stats()
    arena_leaderboard = _fetch_arena_leaderboard()
    arena_proposals_data = _fetch_arena_proposals()

    p_stats = arena_stats.get("proposals", {})
    i_stats = arena_stats.get("insights", {})

    # KPI Row
    ak1, ak2, ak3, ak4 = st.columns(4)
    ak1.metric("Total Proposals", p_stats.get("total", 0))
    avg_score = p_stats.get("avg_score", 0)
    ak2.metric("Avg Score", "{:.1f} / {}".format(
        avg_score, EVALUATION_MAX_SCORE))
    total_impact = p_stats.get("total_impact", 0)
    ak3.metric("Total Impact", "${:,.0f}".format(total_impact))
    ak4.metric("Active Agents", arena_stats.get("total_agents", 0))

    st.markdown("---")

    # Team Standings — horizontal bar chart
    st.markdown("### Team Standings")
    if arena_leaderboard:
        team_names = []
        team_scores = []
        team_colors = []
        for entry in arena_leaderboard:
            team = get_team(entry["team_id"])
            if team:
                team_names.append("{} ({})".format(
                    team["name"], team["firm"]))
                team_scores.append(entry.get("avg_score", 0))
                team_colors.append(team["color"])

        fig_standings = go.Figure(data=[go.Bar(
            y=team_names[::-1],
            x=team_scores[::-1],
            orientation="h",
            marker_color=team_colors[::-1],
            text=["{:.1f}".format(s) for s in team_scores[::-1]],
            textposition="outside",
        )])
        fig_standings.update_layout(
            xaxis_title="Average Score (out of {})".format(
                EVALUATION_MAX_SCORE),
            height=280,
            margin=dict(l=10, r=10, t=10, b=40),
        )
        st.plotly_chart(fig_standings,
                        key="arena_standings")

    # Two-column layout: Proposals + Team Radar
    arena_left, arena_right = st.columns([3, 2])

    with arena_left:
        st.markdown("### Top Proposals")
        scored_proposals = [p for p in arena_proposals_data
                           if p.get("total_score", 0) > 0]
        for p in scored_proposals[:8]:
            team = get_team(p["team_id"]) or {}
            badge_color = team.get("color", "#666")
            score = p.get("total_score", 0)
            threshold_met = score >= IMPLEMENTATION_THRESHOLD

            with st.expander(
                "{icon} {title} — {score}/{max} {flag}".format(
                    icon=team.get("icon", ""),
                    title=p["title"],
                    score=score,
                    max=EVALUATION_MAX_SCORE,
                    flag="IMPLEMENT" if threshold_met else "",
                )
            ):
                st.markdown(
                    "**Team:** {name} ({firm}) | **Category:** {cat} | "
                    "**Department:** {dept}".format(
                        name=team.get("name", "?"),
                        firm=team.get("firm", "?"),
                        cat=p.get("category", ""),
                        dept=p.get("department", ""),
                    )
                )
                st.markdown(p.get("description", ""))

                # Tier breakdown
                try:
                    tier_scores = json.loads(
                        p.get("tier_scores", "{}"))
                except Exception:
                    tier_scores = {}

                if tier_scores:
                    tier_cols = st.columns(5)
                    for i, tier in enumerate(EVALUATION_TIERS):
                        val = tier_scores.get(tier["id"], 0)
                        tier_cols[i].metric(
                            tier["name"][:12],
                            "{}/{}".format(val, tier["max_points"]),
                        )

                st.caption(
                    "Impact: ${:,.0f} | Effort: {} weeks | "
                    "Complexity: {} | Status: {}".format(
                        p.get("estimated_impact_aud", 0),
                        p.get("estimated_effort_weeks", 0),
                        p.get("complexity", "?"),
                        p.get("status", "?"),
                    )
                )

    with arena_right:
        st.markdown("### Team Deep Dive")
        team_options = {
            "{} {} ({})".format(t["icon"], t["name"], t["firm"]): t["id"]
            for t in AGENT_TEAMS
        }
        team_keys = list(team_options.keys())
        selected_team_label = st.selectbox(
            "Select team", team_keys,
            key="arena_team_select",
        )
        if selected_team_label not in team_options:
            selected_team_label = team_keys[0] if team_keys else None
        selected_team_id = team_options.get(
            selected_team_label, AGENT_TEAMS[0]["id"])
        selected_team = get_team(selected_team_id)

        if selected_team:
            st.markdown("**Philosophy:** {}".format(
                selected_team["philosophy"]))
            st.markdown("**Motto:** *\"{}\"*".format(
                selected_team["motto"]))
            st.markdown("**Strengths:** {}".format(
                ", ".join(selected_team["strengths"])))

            # Team radar across 5 tiers
            team_proposals = [p for p in arena_proposals_data
                             if p["team_id"] == selected_team_id
                             and p.get("total_score", 0) > 0]
            if team_proposals:
                tier_avgs = []
                tier_labels = []
                for tier in EVALUATION_TIERS:
                    vals = []
                    for p in team_proposals:
                        try:
                            ts = json.loads(
                                p.get("tier_scores", "{}"))
                            if tier["id"] in ts:
                                vals.append(ts[tier["id"]])
                        except Exception:
                            pass
                    tier_avgs.append(
                        sum(vals) / len(vals) if vals else 0)
                    tier_labels.append(tier["name"][:15])

                # Close polygon
                tier_avgs.append(tier_avgs[0])
                tier_labels.append(tier_labels[0])

                fig_radar = go.Figure(data=go.Scatterpolar(
                    r=tier_avgs,
                    theta=tier_labels,
                    fill="toself",
                    line_color=selected_team["color"],
                    fillcolor=selected_team["color"],
                    opacity=0.3,
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(
                        visible=True, range=[0, 30])),
                    height=300,
                    margin=dict(l=40, r=40, t=20, b=20),
                )
                st.plotly_chart(fig_radar,
                                key="arena_team_radar")
            else:
                st.info("No scored proposals for this team yet.")

    # Evaluation Pipeline
    st.markdown("---")
    st.markdown("### Evaluation Pipeline")
    st.caption(
        "Score proposals through the 5-tier evaluation rubric "
        "({} points max). Threshold to implement: {}+".format(
            EVALUATION_MAX_SCORE, IMPLEMENTATION_THRESHOLD)
    )

    evaluable = [p for p in arena_proposals_data
                 if p.get("status") in ("submitted", "evaluating", "scored")]
    if evaluable:
        eval_options = {
            "#{} — {} ({})".format(
                p["id"], p["title"][:50], p.get("status", "")
            ): p["id"]
            for p in evaluable
        }
        eval_keys = list(eval_options.keys())
        selected_proposal_label = st.selectbox(
            "Select proposal to evaluate",
            eval_keys,
            key="arena_eval_select",
        )
        if selected_proposal_label not in eval_options:
            selected_proposal_label = eval_keys[0] if eval_keys else None
        selected_proposal_id = eval_options.get(
            selected_proposal_label, evaluable[0]["id"] if evaluable else 0)

        eval_submissions = []
        for t_idx, tier in enumerate(EVALUATION_TIERS, 1):
            with st.expander(
                "Tier {}: {} (max {} pts)".format(
                    t_idx, tier["name"], tier["max_points"])
            ):
                st.caption(tier["description"])
                for crit in tier["criteria"]:
                    crit_name = crit["name"] if isinstance(crit, dict) else crit
                    score = st.slider(
                        crit_name,
                        min_value=1, max_value=5, value=3,
                        key="eval_{}_{}".format(
                            tier["id"],
                            crit_name.lower().replace(" ", "_")[:20]),
                    )
                    eval_submissions.append({
                        "tier": tier["id"],
                        "criterion": crit_name,
                        "score": score,
                    })

        if st.button("Submit Evaluation", key="arena_submit_eval"):
            try:
                user_id = (user or {}).get("email", "anonymous")
                resp = requests.post(
                    "{}/api/arena/evaluate".format(API_URL),
                    json={
                        "proposal_id": selected_proposal_id,
                        "evaluations": eval_submissions,
                        "evaluator": user_id,
                    },
                    timeout=10,
                )
                if resp.ok:
                    result = resp.json()
                    score = result.get("score", {})
                    st.success(
                        "Evaluation submitted! Total score: {}/{}".format(
                            score.get("total", 0), EVALUATION_MAX_SCORE))
                    # Award portal points for evaluating
                    requests.post(
                        "{}/api/portal/score".format(API_URL),
                        json={
                            "user_id": user_id,
                            "points": 15,
                            "category": "human",
                            "reason": "Arena evaluation submitted",
                        },
                        timeout=5,
                    )
                    _fetch_arena_proposals.clear()
                    _fetch_arena_stats.clear()
                    _fetch_leaderboard.clear()
                    st.rerun()
                else:
                    st.error("Evaluation failed.")
            except Exception:
                st.warning("Backend not available.")
    else:
        st.info("No proposals available for evaluation.")

    # Impact by Category
    st.markdown("---")
    st.markdown("### Impact by Category")
    categories = arena_stats.get("categories", [])
    if categories:
        fig_impact = go.Figure(data=[go.Bar(
            x=[c["category"].title() for c in categories],
            y=[c["impact"] for c in categories],
            marker_color=["#0d9488", "#f59e0b", "#6366f1",
                          "#ec4899", "#84cc16"][:len(categories)],
            text=["${:,.0f}".format(c["impact"]) for c in categories],
            textposition="outside",
        )])
        fig_impact.update_layout(
            yaxis_title="Estimated Impact ($AUD)",
            height=300,
            margin=dict(l=10, r=10, t=10, b=40),
        )
        st.plotly_chart(fig_impact,
                        key="arena_impact_chart")

    # Implemented proposals
    implemented = [p for p in arena_proposals_data
                   if p.get("status") == "implemented"]
    if implemented:
        st.markdown("### Implemented Proposals")
        for p in implemented:
            team = get_team(p["team_id"]) or {}
            st.markdown(
                "- **{}** ({}) — Score: {}/{}, Impact: ${:,.0f}".format(
                    p["title"], team.get("name", "?"),
                    p.get("total_score", 0), EVALUATION_MAX_SCORE,
                    p.get("estimated_impact_aud", 0),
                )
            )


# ============================================================================
# TAB 7: AGENT NETWORK — Department Analyst Registry
# ============================================================================

with tab7:
    st.subheader("Agent Network")
    st.caption(
        "41 department analyst agents across 8 business units, "
        "generating insights and proposals for Harris Farm Markets"
    )

    # Fetch insights (cached)
    insights_data = _fetch_arena_insights()

    # KPI Row
    nk1, nk2, nk3, nk4 = st.columns(4)
    nk1.metric("Total Agents", len(DEPARTMENT_AGENTS))
    nk2.metric("Business Units", len(BUSINESS_UNITS))
    dept_count = len(set(a["department"] for a in DEPARTMENT_AGENTS))
    nk3.metric("Departments Mapped", dept_count)
    nk4.metric("Active Insights", len(insights_data))

    st.markdown("---")

    # Agent Registry by Business Unit
    st.markdown("### Agent Registry")
    bu_options = ["All"] + [
        "{} {}".format(bu["icon"], bu["name"]) for bu in BUSINESS_UNITS
    ]
    selected_bu = st.selectbox("Filter by Business Unit", bu_options,
                                key="agent_bu_filter")

    if selected_bu == "All":
        filtered_agents = DEPARTMENT_AGENTS
    else:
        bu_name = selected_bu.split(" ", 1)[1] if " " in selected_bu else selected_bu
        filtered_agents = [a for a in DEPARTMENT_AGENTS
                          if any(bu["name"] == bu_name
                                for bu in BUSINESS_UNITS
                                if bu["id"] == a["business_unit"])]
        if not filtered_agents:
            # Fallback: match by business unit display name
            for bu in BUSINESS_UNITS:
                if bu["name"] == bu_name:
                    filtered_agents = get_agents_by_unit(bu["id"])
                    break

    # Agent cards in 3-column grid
    for i in range(0, len(filtered_agents), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(filtered_agents):
                agent = filtered_agents[idx]
                team = get_team(agent["team_id"]) or {}
                with col:
                    st.markdown(
                        "**{icon} {name}**".format(
                            icon=team.get("icon", ""),
                            name=agent["name"],
                        )
                    )
                    st.caption(
                        "{dept} | {team}".format(
                            dept=agent["department"],
                            team=team.get("name", "?"),
                        )
                    )
                    st.markdown("*{}*".format(agent["role"]))
                    caps = agent.get("capabilities", [])[:3]
                    for cap in caps:
                        st.markdown("- {}".format(cap))
                    sources = agent.get("data_sources", [])
                    if sources:
                        st.caption("Data: {}".format(
                            ", ".join(sources)))
                    st.markdown("---")

    # Department Coverage Chart
    st.markdown("### Department Coverage by Team")
    coverage_data = []
    for bu in BUSINESS_UNITS:
        agents = get_agents_by_unit(bu["id"])
        for agent in agents:
            team = get_team(agent["team_id"]) or {}
            coverage_data.append({
                "Business Unit": bu["name"],
                "Team": team.get("name", "?"),
                "Color": team.get("color", "#666"),
                "Count": 1,
            })

    if coverage_data:
        df_coverage = pd.DataFrame(coverage_data)
        fig_coverage = px.bar(
            df_coverage,
            x="Business Unit",
            color="Team",
            color_discrete_map={
                t["name"]: t["color"] for t in AGENT_TEAMS
            },
            title="",
            height=350,
        )
        fig_coverage.update_layout(
            margin=dict(l=10, r=10, t=10, b=60),
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig_coverage,
                        key="agent_coverage_chart")

    # Active Insights Feed
    st.markdown("---")
    st.markdown("### Active Insights")

    insight_filter = st.radio(
        "Type", ["All", "Opportunity", "Risk", "Trend", "Anomaly"],
        horizontal=True, key="insight_type_filter",
    )
    filtered_insights = insights_data
    if insight_filter != "All":
        filtered_insights = [
            ins for ins in insights_data
            if ins.get("insight_type") == insight_filter.lower()
        ]

    type_icons = {
        "opportunity": "💡",
        "risk": "⚠️",
        "trend": "📈",
        "anomaly": "🔍",
    }

    for ins in filtered_insights[:15]:
        itype = ins.get("insight_type", "")
        icon = type_icons.get(itype, "")
        confidence = ins.get("confidence", 0)
        conf_pct = "{:.0f}%".format(confidence * 100)

        with st.expander(
            "{} {} — {} ({}% confidence)".format(
                icon, ins["title"], ins.get("department", ""),
                int(confidence * 100),
            )
        ):
            st.markdown(ins.get("description", ""))
            ic1, ic2, ic3 = st.columns(3)
            ic1.metric("Confidence", conf_pct)
            ic2.metric("Impact", "${:,.0f}".format(
                ins.get("potential_impact_aud", 0)))
            ic3.metric("Data Source", ins.get("data_source", "N/A"))

            agent = get_agent(ins.get("agent_id", ""))
            team = get_team(ins.get("team_id", ""))
            if agent and team:
                st.caption(
                    "Agent: {} ({}) | Team: {} ({})".format(
                        agent["name"], agent["role"],
                        team["name"], team["firm"],
                    )
                )

    # Company Information Board
    st.markdown("---")
    st.markdown("### Company Information Board")

    cib1, cib2 = st.columns(2)
    with cib1:
        st.markdown("**Top Opportunities by Impact**")
        opps = sorted(
            [i for i in insights_data
             if i.get("insight_type") == "opportunity"],
            key=lambda x: x.get("potential_impact_aud", 0),
            reverse=True,
        )[:5]
        for opp in opps:
            st.markdown("- **{}** — ${:,.0f} ({})".format(
                opp["title"],
                opp.get("potential_impact_aud", 0),
                opp.get("department", ""),
            ))

    with cib2:
        st.markdown("**Active Risks to Monitor**")
        risks = [i for i in insights_data
                 if i.get("insight_type") == "risk"]
        for risk in risks:
            st.markdown("- **{}** — ${:,.0f} ({})".format(
                risk["title"],
                risk.get("potential_impact_aud", 0),
                risk.get("department", ""),
            ))

    st.markdown("---")
    cib3, cib4 = st.columns(2)
    with cib3:
        st.markdown("**Emerging Trends**")
        trends = [i for i in insights_data
                  if i.get("insight_type") == "trend"]
        for trend in trends:
            st.markdown("- **{}** — {} ({}%)".format(
                trend["title"],
                trend.get("department", ""),
                int(trend.get("confidence", 0) * 100),
            ))

    with cib4:
        st.markdown("**Coverage Summary**")
        st.markdown("- **{} agents** across **{} business units**".format(
            len(DEPARTMENT_AGENTS), len(BUSINESS_UNITS)))
        st.markdown("- **{} insights** generated".format(
            len(insights_data)))
        total_insight_impact = sum(
            i.get("potential_impact_aud", 0) for i in insights_data)
        st.markdown("- **${:,.0f}** total insight impact".format(
            total_insight_impact))
        avg_conf = (sum(i.get("confidence", 0) for i in insights_data)
                    / len(insights_data)) if insights_data else 0
        st.markdown("- **{:.0f}%** average confidence".format(
            avg_conf * 100))


# ============================================================================
# TAB 8: DATA INTELLIGENCE — Sales Maximization Command Center
# ============================================================================

with tab8:
    st.subheader("Data Intelligence Command Center")
    st.caption(
        "Real-time analysis of 383M+ POS transactions. "
        "Run analyses, review reports, and export evidence-based insights."
    )

    di_sub1, di_sub2, di_sub3, di_sub4 = st.tabs([
        "Run Analysis", "Generated Reports", "Agent Tasks", "Demo Insights",
    ])

    # ------------------------------------------------------------------
    # SUB-TAB 1: RUN ANALYSIS
    # ------------------------------------------------------------------
    with di_sub1:
        ANALYSIS_OPTIONS = {
            "basket_analysis": "Cross-sell / Basket Analysis",
            "stockout_detection": "Lost Sales / Stockout Detection",
            "price_dispersion": "Price Dispersion Analysis",
            "demand_pattern": "Demand Pattern Analysis",
            "slow_movers": "Slow Movers / Range Review",
        }
        ANALYSIS_DESCRIPTIONS = {
            "basket_analysis": "Find products frequently purchased together using self-join on receipt IDs",
            "stockout_detection": "Identify likely stockouts from zero-sale days for high-velocity items",
            "price_dispersion": "Find products with the highest price variation across stores (network-wide)",
            "demand_pattern": "Identify peak and trough demand by day-of-week and hour",
            "slow_movers": "Find underperforming products consuming shelf space",
        }

        STORE_OPTIONS = {
            "28": "Mosman", "10": "Pennant Hills", "24": "St Ives",
            "32": "Willoughby", "37": "Broadway", "40": "Erina",
            "44": "Orange", "48": "Manly", "49": "Mona Vale",
            "51": "Bowral", "52": "Cammeray", "54": "Potts Point",
            "56": "Boronia Park", "57": "Bondi Beach", "58": "Drummoyne",
            "59": "Bathurst", "63": "Randwick", "64": "Leichhardt",
            "65": "Bondi Westfield", "66": "Newcastle", "67": "Lindfield",
            "68": "Albury", "69": "Rose Bay", "70": "West End QLD",
            "74": "Isle of Capri QLD", "75": "Clayfield QLD",
            "76": "Lane Cove", "77": "Dural", "80": "Majura Park ACT",
            "84": "Redfern", "85": "Marrickville", "86": "Miranda",
            "87": "Maroubra",
        }

        rc1, rc2 = st.columns([2, 1])
        with rc1:
            analysis_type = st.selectbox(
                "Analysis Type",
                list(ANALYSIS_OPTIONS.keys()),
                format_func=lambda k: ANALYSIS_OPTIONS[k],
                key="di_analysis_type",
            )
            st.caption(ANALYSIS_DESCRIPTIONS.get(analysis_type, ""))

        with rc2:
            needs_store = analysis_type != "price_dispersion"
            if needs_store:
                store_id = st.selectbox(
                    "Store",
                    list(STORE_OPTIONS.keys()),
                    format_func=lambda k: "{} ({})".format(
                        STORE_OPTIONS[k], k),
                    key="di_store_id",
                )
            else:
                store_id = None
                st.info("Network-wide analysis (all stores)")

            days = st.slider("Lookback (days)", 14, 90, 30,
                             key="di_days_slider")

        if st.button("Run Analysis", type="primary", key="di_run_btn"):
            with st.spinner("Querying 383M+ transactions..."):
                try:
                    payload = {"days": days}
                    if store_id:
                        payload["store_id"] = store_id
                    resp = requests.post(
                        "{}/api/intelligence/run/{}".format(
                            API_URL, analysis_type),
                        json=payload, timeout=120,
                    )
                    if resp.status_code != 200:
                        st.error("Analysis failed: {}".format(
                            resp.json().get("detail", resp.text)[:200]))
                    else:
                        result = resp.json()
                        st.session_state["di_last_result"] = result
                        _fetch_intelligence_reports.clear()

                        # Rubric grade badge
                        rubric = result.get("rubric", {})
                        grade = rubric.get("grade", "Draft")
                        avg = rubric.get("average", 0)
                        grade_colors = {
                            "Board-ready": "#2e7d32",
                            "Reviewed": "#f57c00",
                            "Draft": "#666",
                        }
                        st.markdown(
                            '<span style="background:{}; color:white; '
                            'padding:4px 12px; border-radius:12px; '
                            'font-weight:bold">{} ({:.1f}/10)</span>'
                            '&nbsp;&nbsp; Report #{}'.format(
                                grade_colors.get(grade, "#666"),
                                grade, avg, result.get("id", "?"),
                            ),
                            unsafe_allow_html=True,
                        )

                        # Executive summary
                        st.markdown("### Executive Summary")
                        st.info(result.get("executive_summary", ""))

                        # Evidence tables
                        for table in result.get("evidence_tables", []):
                            st.markdown("### {}".format(
                                table.get("name", "Evidence")))
                            cols = table.get("columns", [])
                            rows = table.get("rows", [])
                            if cols and rows:
                                df = pd.DataFrame(rows, columns=cols)
                                st.dataframe(df)

                        # Financial impact
                        impact = result.get("financial_impact", {})
                        if impact:
                            st.markdown("### Financial Impact")
                            ic1, ic2, ic3 = st.columns(3)
                            ic1.metric(
                                "Est. Annual Value",
                                "${:,.0f}".format(
                                    impact.get("estimated_annual_value", 0)),
                            )
                            ic2.metric("Confidence",
                                       impact.get("confidence", "?").title())
                            ic3.metric("Basis",
                                       impact.get("basis", "")[:50])

                        # Recommendations
                        recs = result.get("recommendations", [])
                        if recs:
                            st.markdown("### Recommendations")
                            rec_df = pd.DataFrame(recs)
                            st.dataframe(rec_df)

                        # Rubric dimensions
                        st.markdown("### Presentation Rubric")
                        dims = rubric.get("dimensions", {})
                        dim_cols = st.columns(4)
                        for i, (key, dim) in enumerate(dims.items()):
                            col = dim_cols[i % 4]
                            score = dim.get("score", 0)
                            color = "#2e7d32" if score >= 8 else (
                                "#f57c00" if score >= 6 else "#e74c3c")
                            col.markdown(
                                '<div style="text-align:center">'
                                '<span style="font-size:1.5em; '
                                'color:{}">{}/10</span><br/>'
                                '<strong>{}</strong></div>'.format(
                                    color, score, dim.get("label", key)),
                                unsafe_allow_html=True,
                            )

                except requests.exceptions.Timeout:
                    st.error("Analysis timed out. Try a shorter lookback "
                             "period or a different store.")
                except Exception as e:
                    st.error("Error: {}".format(str(e)[:200]))

    # ------------------------------------------------------------------
    # SUB-TAB 2: GENERATED REPORTS
    # ------------------------------------------------------------------
    with di_sub2:
        reports_list = _fetch_intelligence_reports()

        if not reports_list:
            st.info("No reports generated yet. Use the 'Run Analysis' tab "
                    "to create your first analysis.")
        else:
            st.markdown("**{} reports generated**".format(len(reports_list)))

            for rpt in reports_list:
                grade = rpt.get("rubric_grade", "Draft")
                avg = rpt.get("rubric_average", 0)
                grade_colors = {
                    "Board-ready": "#2e7d32",
                    "Reviewed": "#f57c00",
                    "Draft": "#666",
                }

                with st.expander(
                    "{} — {} ({:.1f}/10) | {}".format(
                        rpt.get("title", "?")[:60],
                        grade, avg,
                        rpt.get("created_at", "")[:16],
                    )
                ):
                    rpt_id = rpt.get("id")

                    # Fetch full report (cached)
                    detail = _fetch_intelligence_detail(rpt_id)
                    if detail:
                        full_report = detail.get("report", {})
                        st.markdown("**Executive Summary**")
                        st.info(full_report.get("executive_summary", ""))

                        # Evidence tables
                        for ti, table in enumerate(
                                full_report.get("evidence_tables", [])):
                            cols = table.get("columns", [])
                            rows = table.get("rows", [])
                            if cols and rows:
                                df = pd.DataFrame(rows, columns=cols)
                                st.dataframe(
                                    df,
                                    key="rpt_{}_tbl_{}".format(rpt_id, ti))
                    else:
                        st.warning("Could not load report details.")

                    # Download buttons
                    dl1, dl2, dl3, dl4 = st.columns(4)
                    for fmt, label, col, mime in [
                        ("html", "HTML", dl1, "text/html"),
                        ("csv", "CSV", dl2, "text/csv"),
                        ("json", "JSON", dl3, "application/json"),
                        ("markdown", "Markdown", dl4, "text/markdown"),
                    ]:
                        try:
                            export_resp = requests.get(
                                "{}/api/intelligence/export/{}/{}".format(
                                    API_URL, rpt_id, fmt),
                                timeout=5,
                            )
                            if export_resp.status_code == 200:
                                ext = {"markdown": "md"}.get(fmt, fmt)
                                col.download_button(
                                    label,
                                    data=export_resp.text,
                                    file_name="report_{}.{}".format(
                                        rpt_id, ext),
                                    mime=mime,
                                    key="dl_{}_{}".format(rpt_id, fmt),
                                )
                        except Exception:
                            col.caption("{} unavailable".format(label))

    # ------------------------------------------------------------------
    # SUB-TAB 3: AGENT TASKS (NL-driven on-demand execution)
    # ------------------------------------------------------------------
    with di_sub3:
        st.markdown("### On-Demand Agent Tasks")
        st.caption(
            "Describe what you want to analyse in plain English. "
            "The system routes your request to the right analysis, "
            "executes it against real transaction data, scores the "
            "report, and runs a WATCHDOG safety review."
        )

        STORE_OPTIONS_AT = {
            "28": "Mosman", "10": "Pennant Hills", "24": "St Ives",
            "32": "Willoughby", "37": "Broadway", "40": "Erina",
            "44": "Orange", "48": "Manly", "49": "Mona Vale",
            "51": "Bowral", "52": "Cammeray", "54": "Potts Point",
            "56": "Boronia Park", "57": "Bondi Beach", "58": "Drummoyne",
            "59": "Bathurst", "63": "Randwick", "64": "Leichhardt",
            "65": "Bondi Westfield", "66": "Newcastle", "67": "Lindfield",
            "68": "Albury", "69": "Rose Bay", "70": "West End QLD",
            "74": "Isle of Capri QLD", "75": "Clayfield QLD",
            "76": "Lane Cove", "77": "Dural", "80": "Majura Park ACT",
            "84": "Redfern", "85": "Marrickville", "86": "Miranda",
            "87": "Maroubra",
        }

        at_query = st.text_area(
            "What do you want to analyse?",
            height=100,
            placeholder=(
                "e.g. 'Find products that run out during the day abnormally "
                "- items that deviate from their normal hourly basket "
                "penetration'"
            ),
            key="at_query_input",
        )

        at_col1, at_col2 = st.columns([2, 1])
        with at_col1:
            at_store_keys = ["Auto"] + list(STORE_OPTIONS_AT.keys())
            at_store = st.selectbox(
                "Store (optional)",
                at_store_keys,
                format_func=lambda k: "Auto-detect" if k == "Auto"
                    else "{} ({})".format(STORE_OPTIONS_AT.get(k, k), k),
                key="at_store_select",
            )
        with at_col2:
            at_days = st.slider("Lookback (days)", 7, 90, 30,
                                key="at_days_slider")

        if st.button("Submit Task", type="primary", key="at_submit_btn"):
            if not at_query or len(at_query.strip()) < 3:
                st.error("Please describe what you want to analyse.")
            else:
                with st.spinner("Routing query and executing analyses..."):
                    try:
                        payload = {
                            "query": at_query.strip(),
                            "days": at_days,
                        }
                        if at_store != "Auto":
                            payload["store_id"] = at_store

                        resp = requests.post(
                            "{}/api/agent-tasks".format(API_URL),
                            json=payload, timeout=180,
                        )
                        if resp.status_code != 200:
                            st.error("Task failed: {}".format(
                                resp.json().get("detail", resp.text)[:200]))
                        else:
                            at_result = resp.json()
                            st.session_state["at_last_result"] = at_result
                            _fetch_agent_tasks.clear()
                            _fetch_intelligence_reports.clear()

                            # Routing info
                            routing = at_result.get("routing", {})
                            st.markdown(
                                "**Routing:** {} (confidence: {:.0%})".format(
                                    routing.get("reasoning", ""),
                                    routing.get("confidence", 0),
                                ))

                            # WATCHDOG badge
                            wd = at_result.get("watchdog", {})
                            wd_level = wd.get("risk_level", "SAFE")
                            wd_icon = wd.get("risk_icon", "")
                            wd_colors = {
                                "SAFE": "#22c55e", "LOW": "#eab308",
                                "MEDIUM": "#f97316", "HIGH": "#ef4444",
                                "BLOCKED": "#1f2937",
                            }
                            wd_color = wd_colors.get(wd_level, "#666")
                            st.markdown(
                                '<span style="background:{}; color:white; '
                                'padding:4px 12px; border-radius:12px; '
                                'font-weight:bold">{} WATCHDOG: {}</span>'
                                '&nbsp;&nbsp; {} finding(s)'.format(
                                    wd_color, wd_icon, wd_level,
                                    wd.get("finding_count", 0),
                                ),
                                unsafe_allow_html=True,
                            )

                            # Errors
                            if at_result.get("errors"):
                                for err in at_result["errors"]:
                                    st.warning("Error: {}".format(err))

                            # Report cards
                            for rpt in at_result.get("reports", []):
                                rubric = rpt.get("rubric", {})
                                grade = rubric.get("grade", "Draft")
                                avg = rubric.get("average", 0)
                                grade_colors = {
                                    "Board-ready": "#2e7d32",
                                    "Reviewed": "#f57c00",
                                    "Draft": "#666",
                                }

                                with st.expander(
                                    "{} -- {} ({:.1f}/10) | Report #{}".format(
                                        rpt.get("title", "?")[:60],
                                        grade, avg, rpt.get("id", "?"),
                                    ),
                                ):
                                    st.markdown(
                                        '<span style="background:{}; '
                                        'color:white; padding:3px 10px; '
                                        'border-radius:10px; '
                                        'font-size:0.9em">'
                                        '{} {:.1f}/10</span>'.format(
                                            grade_colors.get(grade, "#666"),
                                            grade, avg,
                                        ),
                                        unsafe_allow_html=True,
                                    )

                                    st.info(rpt.get(
                                        "executive_summary", ""))

                                    # Evidence tables
                                    for ti, table in enumerate(
                                            rpt.get(
                                                "evidence_tables", [])):
                                        cols = table.get("columns", [])
                                        tbl_rows = table.get("rows", [])
                                        if cols and tbl_rows:
                                            df = pd.DataFrame(
                                                tbl_rows, columns=cols)
                                            st.dataframe(
                                                df,
                                                key="at_rpt_{}_tbl_{}".format(
                                                    rpt.get("id", 0), ti),
                                            )

                                    # Financial impact
                                    impact = rpt.get(
                                        "financial_impact", {})
                                    if impact.get(
                                            "estimated_annual_value"):
                                        fic1, fic2 = st.columns(2)
                                        fic1.metric(
                                            "Est. Annual Value",
                                            "${:,.0f}".format(
                                                impact[
                                                    "estimated_annual_value"
                                                ]),
                                        )
                                        fic2.metric(
                                            "Confidence",
                                            impact.get(
                                                "confidence",
                                                "?").title(),
                                        )

                                    # Recommendations
                                    recs = rpt.get(
                                        "recommendations", [])
                                    if recs:
                                        st.markdown(
                                            "**Recommendations:**")
                                        rec_df = pd.DataFrame(recs)
                                        st.dataframe(
                                            rec_df,
                                            key="at_rpt_{}_recs".format(
                                                rpt.get("id", 0)),
                                        )

                                    # Rubric dimensions
                                    dims = rubric.get("dimensions", {})
                                    if dims:
                                        dim_cols = st.columns(4)
                                        for di, (key, dim) in enumerate(
                                                dims.items()):
                                            col = dim_cols[di % 4]
                                            score = dim.get("score", 0)
                                            color = (
                                                "#2e7d32"
                                                if score >= 8
                                                else "#f57c00"
                                                if score >= 6
                                                else "#e74c3c"
                                            )
                                            col.markdown(
                                                '<div style='
                                                '"text-align:center">'
                                                '<span style='
                                                '"font-size:1.3em; '
                                                'color:{}">'
                                                '{}/10</span><br/>'
                                                '<strong>{}</strong>'
                                                '</div>'.format(
                                                    color, score,
                                                    dim.get(
                                                        "label", key)),
                                                unsafe_allow_html=True,
                                            )

                                    # Download buttons
                                    dl_cols = st.columns(4)
                                    for fmt, label, dl_col, mime in [
                                        ("html", "HTML",
                                         dl_cols[0], "text/html"),
                                        ("csv", "CSV",
                                         dl_cols[1], "text/csv"),
                                        ("json", "JSON",
                                         dl_cols[2],
                                         "application/json"),
                                        ("markdown", "Markdown",
                                         dl_cols[3], "text/markdown"),
                                    ]:
                                        try:
                                            exp_resp = requests.get(
                                                "{}/api/intelligence"
                                                "/export/{}/{}".format(
                                                    API_URL,
                                                    rpt.get("id", 0),
                                                    fmt),
                                                timeout=5,
                                            )
                                            if exp_resp.ok:
                                                ext = {"markdown": "md"
                                                       }.get(fmt, fmt)
                                                dl_col.download_button(
                                                    label,
                                                    data=exp_resp.text,
                                                    file_name=(
                                                        "report_{}.{}"
                                                        .format(
                                                            rpt.get(
                                                                "id", 0),
                                                            ext)),
                                                    mime=mime,
                                                    key="at_dl_{}_{}".format(
                                                        rpt.get("id", 0),
                                                        fmt),
                                                )
                                        except Exception:
                                            dl_col.caption(
                                                "{} unavailable".format(
                                                    label))

                    except requests.exceptions.Timeout:
                        st.error(
                            "Task timed out. Try fewer analysis types "
                            "or a shorter lookback period.")
                    except Exception as e:
                        st.error("Error: {}".format(str(e)[:200]))

        # Task History
        st.markdown("---")
        st.markdown("### Task History")
        tasks = _fetch_agent_tasks()
        if tasks:
            for task in tasks:
                status = task.get("status", "?")
                status_icons = {
                    "pending": "...",
                    "running": "...",
                    "completed": "Done",
                    "failed": "FAIL",
                }
                wd_status = task.get("watchdog_status", "")
                st.markdown(
                    "**#{}** | {} | {} | WATCHDOG: {} | {}".format(
                        task.get("id", "?"),
                        status_icons.get(status, status),
                        task.get("user_query", "")[:80],
                        wd_status or "-",
                        task.get("created_at", "")[:16],
                    )
                )
        else:
            st.info(
                "No tasks submitted yet. Enter a query above to "
                "get started.")

    # ------------------------------------------------------------------
    # SUB-TAB 4: DEMO INSIGHTS (existing seeded data)
    # ------------------------------------------------------------------
    with di_sub4:
        st.caption(
            "Demonstration data from seeded insights. "
            "Use 'Run Analysis' for real data-driven intelligence."
        )

        di_data = _fetch_di_data()

        di_summary = di_data.get("summary", {})
        di_insights = di_data.get("insights", [])
        di_cat_stats = di_data.get("category_stats", {})

        dk1, dk2, dk3, dk4 = st.columns(4)
        dk1.metric("Active Agents", di_summary.get("total_agents", 0))
        dk2.metric("Insights Generated",
                   di_summary.get("total_insights", 0))
        dk3.metric("Total Impact Identified",
                   "${:,.0f}".format(di_summary.get("total_impact", 0)))
        dk4.metric("Avg Confidence",
                   "{:.0f}%".format(
                       di_summary.get("avg_confidence", 0) * 100))

        st.markdown("---")
        st.markdown("### Intelligence Feed")

        type_icons = {
            "opportunity": "💡", "risk": "⚠️",
            "trend": "📈", "anomaly": "🔍",
        }
        for ins in di_insights[:12]:
            itype = ins.get("insight_type", "")
            icon = type_icons.get(itype, "")
            confidence = ins.get("confidence", 0)

            with st.expander(
                "{} {} — ${:,.0f} impact ({}% confidence)".format(
                    icon, ins.get("title", "?"),
                    ins.get("potential_impact_aud", 0),
                    int(confidence * 100),
                )
            ):
                st.markdown(ins.get("description", ""))
                dc1, dc2, dc3, dc4 = st.columns(4)
                dc1.metric("Type", itype.title())
                dc2.metric("Confidence",
                           "{:.0f}%".format(confidence * 100))
                dc3.metric("Impact", "${:,.0f}".format(
                    ins.get("potential_impact_aud", 0)))
                dc4.metric("Department",
                           ins.get("department", "N/A"))


# ============================================================================
# TAB 9: WATCHDOG SAFETY — Human-in-the-Loop Safety Dashboard
# ============================================================================

with tab9:
    st.subheader("WATCHDOG Safety Dashboard")
    st.caption(
        "Every agent proposal must pass through WATCHDOG before any action. "
        "No exceptions. No bypasses. Human approval required."
    )

    # Fetch WATCHDOG status and proposals (cached)
    wd_status = _fetch_watchdog_status()
    wd_pending = _fetch_watchdog_pending()
    wd_all = _fetch_watchdog_all()
    wd_audit_data = _fetch_watchdog_audit()

    wd_system = wd_status.get("system", {})
    wd_metrics = wd_status.get("metrics", {})
    wd_risk_dist = wd_status.get("risk_distribution", {})

    # -- System Status Banner --
    status_active = wd_system.get("watchdog_active", False)
    status_color = "#22c55e" if status_active else "#ef4444"
    st.markdown(
        '<div style="background:{}; color:white; padding:12px 20px; '
        'border-radius:8px; font-weight:600; text-align:center; '
        'margin-bottom:16px;">'
        '{} WATCHDOG is {} | Human-in-Loop: {} | Auto-Implementation: {} '
        '| Audit Logging: {}'
        '</div>'.format(
            status_color,
            "🛡️" if status_active else "⚠️",
            "ACTIVE" if status_active else "OFFLINE",
            "REQUIRED" if wd_system.get("human_in_loop_required") else "OFF",
            "DISABLED" if wd_system.get("auto_implementation_disabled")
            else "ENABLED",
            "ON" if wd_system.get("audit_logging_active") else "OFF",
        ),
        unsafe_allow_html=True,
    )

    # -- KPI Row --
    wk1, wk2, wk3, wk4, wk5 = st.columns(5)
    wk1.metric("Total Analyzed", wd_metrics.get("total_proposals", 0))
    wk2.metric("Pending Review", wd_metrics.get("pending_review", 0))
    wk3.metric("Approved", wd_metrics.get("approved", 0))
    wk4.metric("Rejected", wd_metrics.get("rejected", 0))
    wk5.metric("Blocked", wd_metrics.get("blocked_by_watchdog", 0))

    # -- Risk Distribution Chart --
    if wd_risk_dist:
        st.markdown("---")
        st.markdown("### Risk Distribution")
        risk_names = []
        risk_counts = []
        risk_colors = []
        for level in RISK_LEVELS:
            count = wd_risk_dist.get(level, 0)
            if count > 0:
                risk_names.append("{} {}".format(
                    RISK_ICONS.get(level, ""), level))
                risk_counts.append(count)
                risk_colors.append(RISK_COLORS.get(level, "#666"))

        if risk_names:
            fig_risk = go.Figure(data=[go.Bar(
                x=risk_names, y=risk_counts,
                marker_color=risk_colors,
                text=risk_counts, textposition="outside",
            )])
            fig_risk.update_layout(
                yaxis_title="Proposals",
                height=280,
                margin=dict(l=10, r=10, t=10, b=40),
            )
            st.plotly_chart(fig_risk,
                            key="wd_risk_chart")

    # -- Pending Approval Queue --
    st.markdown("---")
    st.markdown("### Pending Approval Queue")
    if wd_pending:
        st.warning("{} proposal(s) awaiting human review".format(
            len(wd_pending)))
        for prop in wd_pending:
            risk = prop.get("risk_level", "SAFE")
            risk_icon = RISK_ICONS.get(risk, "")
            tracking = prop.get("tracking_id", "")

            with st.expander(
                "{} {} — {} [{}]".format(
                    risk_icon, prop.get("title", "Untitled"),
                    risk, tracking[:16],
                )
            ):
                st.markdown("**Agent:** {} | **Risk:** {} {}".format(
                    prop.get("agent_id", "?"), risk_icon, risk))
                st.markdown("**Description:** {}".format(
                    prop.get("description", "N/A")))
                st.markdown("**Findings:** {} issue(s)".format(
                    prop.get("finding_count", 0)))
                st.caption("Submitted: {}".format(
                    prop.get("created_at", "?")))

                # Parse recommendation
                try:
                    rec = json.loads(prop.get("recommendation", "{}"))
                except Exception:
                    rec = {}
                if rec:
                    st.markdown("**WATCHDOG Recommendation:** {}".format(
                        rec.get("decision", "?")))
                    if rec.get("modifications"):
                        st.markdown("**Required Modifications:**")
                        for mod in rec["modifications"]:
                            st.markdown("- {}".format(mod))

                # Approve / Reject buttons
                wd_col1, wd_col2 = st.columns(2)
                with wd_col1:
                    approve_comment = st.text_input(
                        "Approval comments",
                        key="wd_approve_comment_{}".format(tracking),
                        placeholder="Optional comments...",
                    )
                    if st.button(
                        "Approve", key="wd_approve_{}".format(tracking),
                        type="primary",
                    ):
                        user_name = (user or {}).get("name", "Operator")
                        try:
                            resp = requests.post(
                                "{}/api/watchdog/approve".format(API_URL),
                                json={
                                    "tracking_id": tracking,
                                    "approver": user_name,
                                    "comments": approve_comment,
                                },
                                timeout=5,
                            )
                            if resp.ok:
                                st.success("Approved: {}".format(tracking))
                                _fetch_watchdog_status.clear()
                                _fetch_watchdog_pending.clear()
                                _fetch_watchdog_all.clear()
                                _fetch_watchdog_audit.clear()
                                st.rerun()
                            else:
                                st.error(resp.json().get(
                                    "detail", "Approval failed"))
                        except Exception:
                            st.warning("Backend not available.")

                with wd_col2:
                    reject_comment = st.text_input(
                        "Rejection reason",
                        key="wd_reject_comment_{}".format(tracking),
                        placeholder="Required: reason for rejection...",
                    )
                    if st.button(
                        "Reject", key="wd_reject_{}".format(tracking),
                    ):
                        if not reject_comment.strip():
                            st.error("Rejection reason is required.")
                        else:
                            user_name = (user or {}).get("name", "Operator")
                            try:
                                resp = requests.post(
                                    "{}/api/watchdog/reject".format(API_URL),
                                    json={
                                        "tracking_id": tracking,
                                        "approver": user_name,
                                        "comments": reject_comment,
                                    },
                                    timeout=5,
                                )
                                if resp.ok:
                                    st.success(
                                        "Rejected: {}".format(tracking))
                                    _fetch_watchdog_status.clear()
                                    _fetch_watchdog_pending.clear()
                                    _fetch_watchdog_all.clear()
                                    _fetch_watchdog_audit.clear()
                                    st.rerun()
                                else:
                                    st.error("Rejection failed.")
                            except Exception:
                                st.warning("Backend not available.")
    else:
        st.success("No proposals pending review. All clear.")

    # -- All Proposals Table --
    st.markdown("---")
    st.markdown("### All WATCHDOG Proposals")
    wd_filter = st.radio(
        "Filter", ["All", "Pending", "Approved", "Rejected", "Blocked"],
        horizontal=True, key="wd_proposal_filter",
    )
    status_map = {
        "All": None, "Pending": "pending_review",
        "Approved": "approved", "Rejected": "rejected",
        "Blocked": "blocked",
    }
    filter_status = status_map.get(wd_filter)

    filtered_wd = wd_all
    if filter_status:
        filtered_wd = [p for p in wd_all
                       if p.get("status") == filter_status]

    if filtered_wd:
        table_rows = []
        for p in filtered_wd[:30]:
            risk = p.get("risk_level", "?")
            table_rows.append({
                "Tracking ID": p.get("tracking_id", "")[:16],
                "Title": p.get("title", "")[:40],
                "Agent": p.get("agent_id", ""),
                "Risk": "{} {}".format(RISK_ICONS.get(risk, ""), risk),
                "Findings": p.get("finding_count", 0),
                "Status": p.get("status", "?"),
                "Reviewed By": p.get("reviewed_by", "—"),
                "Created": p.get("created_at", "")[:16],
            })
        df_wd = pd.DataFrame(table_rows)
        st.dataframe(df_wd, hide_index=True)
    else:
        st.info("No proposals match the selected filter.")

    # -- Audit Trail --
    st.markdown("---")
    st.markdown("### Audit Trail")
    audits = wd_audit_data.get("audits", [])
    decisions = wd_audit_data.get("decisions", [])

    wd_audit_tab1, wd_audit_tab2 = st.tabs([
        "Analysis Log", "Decision Log",
    ])

    with wd_audit_tab1:
        if audits:
            for a in audits[:20]:
                risk = a.get("risk_level", "?")
                risk_icon = RISK_ICONS.get(risk, "")
                st.markdown(
                    "**{}** {} {} — {} ({} findings) — {}".format(
                        a.get("tracking_id", "")[:16],
                        risk_icon, risk,
                        a.get("title", "?"),
                        a.get("finding_count", 0),
                        a.get("analyzed_at", "")[:19],
                    )
                )
        else:
            st.info("No analysis records yet.")

    with wd_audit_tab2:
        if decisions:
            for d in decisions[:20]:
                decision_icon = (
                    "✅" if d.get("decision") == "approved" else "❌")
                st.markdown(
                    "**{}** {} {} — by **{}** — {}".format(
                        d.get("tracking_id", "")[:16],
                        decision_icon,
                        d.get("decision", "?"),
                        d.get("approver", "?"),
                        d.get("decided_at", "")[:19],
                    )
                )
                if d.get("comments"):
                    st.caption("Comments: {}".format(d["comments"]))
        else:
            st.info("No decisions recorded yet.")

    # -- Safety Policy Reference --
    st.markdown("---")
    with st.expander("WATCHDOG Safety Policy Reference"):
        st.markdown("**Risk Levels:**")
        for level in RISK_LEVELS:
            st.markdown("- {} **{}** — {}".format(
                RISK_ICONS.get(level, ""),
                level,
                {
                    "SAFE": "No issues, low impact, easily reversible",
                    "LOW": "Minor concerns, requires human review",
                    "MEDIUM": "Significant concerns, careful review needed",
                    "HIGH": "Critical concerns, senior approval required",
                    "BLOCKED": "Unsafe, violates policy, must not proceed",
                }.get(level, ""),
            ))

        st.markdown("")
        st.markdown("**Blocked Actions** (always rejected):")
        blocked_list = [
            "delete_database", "drop_table", "modify_watchdog",
            "disable_safety", "bypass_approval", "modify_audit_log",
            "access_credentials", "external_data_export",
            "modify_pricing_live", "bulk_delete_products",
        ]
        for action in blocked_list:
            st.markdown("- {}".format(action.replace("_", " ").title()))

        st.markdown("")
        st.markdown("**Senior Approval Required:**")
        senior_list = [
            "pricing_change", "product_delist", "supplier_change",
            "financial_adjustment", "data_schema_change",
            "production_deployment", "customer_data_access",
        ]
        for action in senior_list:
            st.markdown("- {}".format(action.replace("_", " ").title()))

        st.markdown("")
        st.markdown("**Safety Scans Performed:**")
        st.markdown("1. Security — SQL injection, unsafe file ops, "
                     "credentials, external calls")
        st.markdown("2. Code Safety — resource exhaustion, "
                     "blocked actions, infrastructure changes")
        st.markdown("3. Privacy — PII detection, customer data access")
        st.markdown("4. Business — financial impact, complexity validation, "
                     "senior approval triggers")
        st.markdown("5. Compliance — food safety, financial reporting")


# ============================================================================
# TAB 10: SELF-IMPROVEMENT ENGINE
# ============================================================================

with tab10:
    st.subheader("Self-Improvement Engine")
    st.caption(
        "Automated loop: parse audit scores, identify weakest criteria, "
        "propose improvements, track attempts (MAX 3 per criterion per cycle)."
    )

    si_sub1, si_sub2, si_sub3 = st.tabs([
        "Score Tracking", "Continuous Improvement", "Cycle History",
    ])

    si_status = _fetch_si_status()
    si_history = _fetch_si_history()

    # ---- Sub-tab 1: Score Tracking ----
    with si_sub1:
        if not si_status or not si_status.get("averages"):
            st.warning(
                "No scoring data found. Ensure the backend is running and "
                "audit.log contains SCORES entries."
            )
        else:
            avgs = si_status.get("averages", {})
            weakest = si_status.get("weakest", {})
            attempts = si_status.get("attempts", {})
            recommendation = si_status.get("recommendation", "")

            # KPI metrics row
            si_cols = st.columns(7)
            criteria_list = ["H", "R", "S", "C", "D", "U", "X"]
            labels = {
                "H": "Honest", "R": "Reliable", "S": "Safe", "C": "Clean",
                "D": "DataCorrect", "U": "Usable", "X": "Documented",
            }
            for i, c in enumerate(criteria_list):
                score = avgs.get(c, 0)
                with si_cols[i]:
                    color = "red" if score < 7 else "orange" if score < 8 else "green"
                    st.markdown(
                        "<div style='text-align:center'>"
                        "<span style='font-size:2em;color:{}'>{}</span><br>"
                        "<b>{}</b></div>".format(color, score, labels[c]),
                        unsafe_allow_html=True,
                    )

            st.markdown("**Overall Average: {}** from {} scored tasks".format(
                avgs.get("avg", 0), avgs.get("count", 0)
            ))

            if recommendation:
                if "ESCALATE" in recommendation:
                    st.error(recommendation)
                elif "IMPROVE" in recommendation:
                    st.warning(recommendation)
                else:
                    st.success(recommendation)

            st.markdown("---")

            # Attempt Counters
            st.markdown("### Improvement Attempts (this cycle)")
            att_cols = st.columns(7)
            for i, c in enumerate(criteria_list):
                att = attempts.get(c, 0)
                with att_cols[i]:
                    bar = "{}/{}".format(att, 3)
                    color = "red" if att >= 3 else "orange" if att >= 2 else "green"
                    st.markdown(
                        "<div style='text-align:center'>"
                        "<span style='color:{}'>{}</span><br>"
                        "{}</div>".format(color, bar, c),
                        unsafe_allow_html=True,
                    )

            # Recent Scores
            st.markdown("---")
            st.markdown("### Recent Task Scores")
            recent = si_status.get("recent_scores", [])
            if recent:
                import pandas as pd
                df_scores = pd.DataFrame(recent)
                display_cols = ["timestamp", "task", "H", "R", "S", "C", "D",
                                "U", "X", "avg"]
                available = [c for c in display_cols if c in df_scores.columns]
                st.dataframe(df_scores[available], hide_index=True)
            else:
                st.info("No scored tasks yet.")

            # Score Trends
            trends = si_history.get("score_trends", [])
            if trends:
                st.markdown("### Score Trends (Stored)")
                import pandas as pd
                df_trends = pd.DataFrame(trends)
                if "recorded_at" in df_trends.columns and "avg_score" in df_trends.columns:
                    st.line_chart(
                        df_trends.set_index("recorded_at")["avg_score"],
                    )

    # ---- Sub-tab 2: Continuous Improvement ----
    with si_sub2:
        st.markdown("### Automated Codebase Audit")
        st.caption(
            "Scans backend and dashboards for safety issues, documentation gaps, "
            "and performance anti-patterns. Findings are tracked and can be "
            "promoted to agent proposals."
        )

        # Run Audit button
        if st.button("Run Full Audit", type="primary", key="ci_run_audit"):
            with st.spinner("Scanning codebase..."):
                try:
                    resp = requests.post(
                        "{}/api/continuous-improvement/audit".format(API_URL),
                        timeout=60,
                    )
                    if resp.status_code == 200:
                        audit_data = resp.json()
                        st.success(
                            "Audit complete: {} findings ({} new)".format(
                                audit_data.get("findings_count", 0),
                                audit_data.get("new_findings", 0),
                            )
                        )
                        # Show category breakdown
                        by_cat = audit_data.get("by_category", {})
                        if by_cat:
                            cat_cols = st.columns(len(by_cat))
                            for idx, (cat, count) in enumerate(by_cat.items()):
                                with cat_cols[idx]:
                                    st.metric(cat.title(), count)
                        st.cache_data.clear()
                    else:
                        st.error("Audit failed: {}".format(resp.status_code))
                except Exception as e:
                    st.error("Error: {}".format(e))

        st.markdown("---")

        # Health Metrics
        ci_metrics = _fetch_ci_metrics()
        if ci_metrics:
            st.markdown("### System Health Metrics")
            hm_cols = st.columns(6)
            fc = ci_metrics.get("file_counts", {})
            with hm_cols[0]:
                st.metric("Backend Files", fc.get("backend", 0))
            with hm_cols[1]:
                st.metric("Dashboard Files", fc.get("dashboards", 0))
            with hm_cols[2]:
                st.metric("Test Files", fc.get("tests", 0))
            with hm_cols[3]:
                st.metric("Test Functions", ci_metrics.get("test_count", 0))
            with hm_cols[4]:
                st.metric("DB Tables", ci_metrics.get("table_count", 0))
            with hm_cols[5]:
                st.metric("API Endpoints", ci_metrics.get("endpoint_count", 0))

            total_lines = ci_metrics.get("total_lines", 0)
            last_audit = ci_metrics.get("last_audit", "Never")
            st.caption("Total lines: {:,} | Last audit entry: {}".format(
                total_lines, last_audit or "N/A"))

        st.markdown("---")

        # Findings table
        st.markdown("### Open Findings")
        ci_findings = _fetch_ci_findings(status="open")
        if ci_findings:
            import pandas as pd
            df_f = pd.DataFrame(ci_findings)
            display = ["id", "category", "severity", "file_path",
                        "title", "status", "created_at"]
            available = [c for c in display if c in df_f.columns]
            st.dataframe(df_f[available], hide_index=True)
        else:
            st.info("No open findings. Run an audit to scan for issues.")

    # ---- Sub-tab 3: Cycle History ----
    with si_sub3:
        cycles = si_history.get("cycles", [])
        if cycles:
            st.markdown("### Improvement Cycle History")
            import pandas as pd
            df_cycles = pd.DataFrame(cycles)
            st.dataframe(df_cycles, hide_index=True)
        else:
            st.info("No improvement cycles recorded yet.")

        st.markdown("---")
        st.markdown("### Admin Actions")
        if st.button("Backfill scores from audit.log", key="si_backfill"):
            try:
                resp = requests.post(
                    "{}/api/self-improvement/backfill".format(API_URL),
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.success("Backfilled {} score records from audit.log".format(
                        data.get("rows_inserted", 0)
                    ))
                    st.cache_data.clear()
                else:
                    st.error("Failed: {}".format(resp.status_code))
            except Exception as e:
                st.error("Error: {}".format(e))


# ============================================================================
# TAB 11: AGENT CONTROL PANEL
# ============================================================================

with tab11:
    st.subheader("AI Agent Control Panel")
    st.caption(
        "Approve or reject agent proposals. Monitor agent performance. "
        "Trigger new analysis cycles."
    )

    # Executor status banner
    exec_status = _fetch_executor_status()
    queue = exec_status.get("queue", {})
    q_approved = exec_status.get("approved_waiting", 0)
    q_completed = exec_status.get("completed_total", 0)
    q_pending = exec_status.get("pending_total", 0)

    es_cols = st.columns(4)
    with es_cols[0]:
        st.metric("Pending", q_pending)
    with es_cols[1]:
        st.metric("Awaiting Execution", q_approved,
                   help="Approved but not yet executed")
    with es_cols[2]:
        st.metric("Completed", q_completed)
    with es_cols[3]:
        if st.button("Execute Approved Now", type="primary",
                     key="acp_execute_now"):
            try:
                resp = requests.post(
                    "{}/api/admin/executor/run".format(API_URL), timeout=120,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.success("{} proposal(s) executed with real data".format(
                        data.get("executed", 0)))
                    st.cache_data.clear()
                else:
                    st.error("Failed: {}".format(resp.status_code))
            except Exception as e:
                st.error("Error: {}".format(e))

    acp_sub1, acp_sub2, acp_sub3 = st.tabs([
        "Pending Approval", "Agent Performance", "Task History",
    ])

    # ---- Sub-tab 1: Pending Approval ----
    with acp_sub1:
        col_trigger, col_spacer = st.columns([1, 3])
        with col_trigger:
            if st.button("Rerun Analysis", type="primary",
                         key="acp_trigger"):
                try:
                    resp = requests.post(
                        "{}/api/admin/trigger-analysis".format(API_URL),
                        json={"type": "all"}, timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.success(data.get("message", "Tasks created"))
                        st.cache_data.clear()
                    else:
                        st.error("Failed: {}".format(resp.status_code))
                except Exception as e:
                    st.error("Error: {}".format(e))

        pending = _fetch_agent_proposals(status="PENDING")
        if not pending:
            st.success(
                "No pending tasks. All agents are idle or approved."
            )
        else:
            st.markdown("**{} proposals awaiting review:**".format(len(pending)))
            for prop in pending:
                pid = prop.get("id", 0)
                risk = prop.get("risk_level", "MEDIUM")
                risk_color = {"HIGH": "red", "MEDIUM": "orange", "LOW": "green"
                              }.get(risk, "gray")

                with st.container():
                    st.markdown(
                        "<div style='border-left:4px solid {};padding:8px 16px;"
                        "margin:8px 0;background:#f8f9fa;border-radius:4px'>"
                        "<b>{}</b> &mdash; {} "
                        "<span style='background:{};color:white;padding:2px 8px;"
                        "border-radius:4px;font-size:0.8em'>{} RISK</span>"
                        "<br><span style='color:#6b7280;font-size:0.85em'>"
                        "{}</span><br>"
                        "<span style='color:#059669;font-size:0.85em'>"
                        "Impact: {}</span>"
                        "</div>".format(
                            risk_color,
                            prop.get("agent_name", ""),
                            prop.get("task_type", ""),
                            risk_color, risk,
                            prop.get("description", ""),
                            prop.get("estimated_impact", "N/A"),
                        ),
                        unsafe_allow_html=True,
                    )
                    col_notes, col_approve, col_reject = st.columns([3, 1, 1])
                    with col_notes:
                        notes = st.text_input(
                            "Notes", key="acp_notes_{}".format(pid),
                            placeholder="Optional reviewer notes...",
                            label_visibility="collapsed",
                        )
                    with col_approve:
                        if st.button("Approve", key="acp_approve_{}".format(pid),
                                     type="primary"):
                            try:
                                resp = requests.post(
                                    "{}/api/admin/agent-proposals/{}/approve".format(
                                        API_URL, pid),
                                    json={"notes": notes}, timeout=5,
                                )
                                if resp.status_code == 200:
                                    st.success("Approved")
                                    st.cache_data.clear()
                                else:
                                    st.error(resp.json().get("detail", "Failed"))
                            except Exception as e:
                                st.error("Error: {}".format(e))
                    with col_reject:
                        if st.button("Reject", key="acp_reject_{}".format(pid)):
                            if not notes:
                                st.warning("Rejection requires notes")
                            else:
                                try:
                                    resp = requests.post(
                                        "{}/api/admin/agent-proposals/{}/reject".format(
                                            API_URL, pid),
                                        json={"notes": notes}, timeout=5,
                                    )
                                    if resp.status_code == 200:
                                        st.success("Rejected")
                                        st.cache_data.clear()
                                    else:
                                        st.error(resp.json().get("detail", "Failed"))
                                except Exception as e:
                                    st.error("Error: {}".format(e))

    # ---- Sub-tab 2: Agent Performance ----
    with acp_sub2:
        score_data = _fetch_agent_scores()
        agent_avgs = score_data.get("agent_averages", [])

        if not agent_avgs:
            st.info("No agent performance data yet. Run an analysis to generate scores.")
        else:
            st.markdown("### Agent Performance (Last 30 Days)")
            perf_cols = st.columns(min(len(agent_avgs), 4))
            for i, agent in enumerate(agent_avgs):
                with perf_cols[i % len(perf_cols)]:
                    avg = agent.get("avg_score", 0)
                    color = "green" if avg >= 8 else "orange" if avg >= 6 else "red"
                    st.markdown(
                        "<div style='text-align:center;border:1px solid #e5e7eb;"
                        "border-radius:8px;padding:16px;margin:4px'>"
                        "<b>{}</b><br>"
                        "<span style='font-size:2em;color:{}'>{:.1f}</span>"
                        "<span style='color:#9ca3af'> / 10</span><br>"
                        "<span style='color:#6b7280;font-size:0.85em'>"
                        "{} measurements</span></div>".format(
                            agent.get("agent_name", ""),
                            color, avg,
                            agent.get("measurements", 0),
                        ),
                        unsafe_allow_html=True,
                    )

        # Recent scores table
        recent_scores = score_data.get("scores", [])
        if recent_scores:
            st.markdown("### Recent Score Updates")
            import pandas as pd
            df_as = pd.DataFrame(recent_scores)
            display_cols = ["agent_name", "metric", "score", "baseline",
                            "evidence", "timestamp"]
            available = [c for c in display_cols if c in df_as.columns]
            st.dataframe(df_as[available], hide_index=True)

    # ---- Sub-tab 3: Task History ----
    with acp_sub3:
        all_proposals = _fetch_agent_proposals()
        if not all_proposals:
            st.info("No agent proposals yet.")
        else:
            import pandas as pd
            df_hist = pd.DataFrame(all_proposals)
            display_cols = ["id", "agent_name", "task_type", "description",
                            "risk_level", "status", "reviewer",
                            "execution_result", "created_at", "reviewed_at"]
            available = [c for c in display_cols if c in df_hist.columns]
            st.dataframe(df_hist[available], hide_index=True)

            # Completed tasks detail
            completed = [p for p in all_proposals
                         if p.get("status") == "COMPLETED"
                         and p.get("execution_result")]
            if completed:
                st.markdown("### Execution Results")
                for prop in completed[:10]:
                    with st.expander("{} #{} — {}".format(
                        prop.get("agent_name", ""), prop.get("id", ""),
                        prop.get("task_type", ""),
                    )):
                        st.text(prop.get("execution_result", "No result"))


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(
    "Hub Documentation Portal | "
    "Content sourced from docs/, watchdog/, and hub_data.db | "
    "16 dashboards across 5 hubs | "
    "5 agent teams, 47 analysts, 130-point rubric | "
    "WATCHDOG Safety Active | Self-Improvement Engine Active | "
    "Agent Control Panel Active"
)
render_footer("Hub Portal", user=user)
