"""
Harris Farm Hub — Agent Hub
Scoreboard, The Arena (agent competition), and Agent Network in one page.
Extracted from hub_portal.py to improve usability and maintainability.
"""

import json
import os

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

from shared.styles import render_header, render_footer
from shared.voice_realtime import render_voice_data_box
from shared.portal_content import (
    MILESTONES, POINT_ACTIONS_AI, POINT_ACTIONS_HUMAN,
)
from shared.agent_teams import (
    AGENT_TEAMS, DEPARTMENT_AGENTS, EVALUATION_TIERS, BUSINESS_UNITS,
    EVALUATION_MAX_SCORE, IMPLEMENTATION_THRESHOLD,
    ARENA_ACHIEVEMENTS, TEAM_POINT_ACTIONS,
    get_team, get_agent, get_agents_by_unit, get_agents_by_team,
    calculate_proposal_score,
)

API_URL = os.getenv("API_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# CACHED API HELPERS
# ---------------------------------------------------------------------------

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


@st.cache_data(ttl=10, show_spinner=False)
def _fetch_executor_status():
    try:
        return requests.get(
            "{}/api/admin/executor/status".format(API_URL), timeout=5
        ).json()
    except Exception:
        return {"queue": {}, "approved_waiting": 0}


# ---------------------------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------------------------

user = st.session_state.get("auth_user")
render_header(
    "Agent Hub",
    "**Scoreboard, Arena competition & Agent Network** | "
    "AI agents competing to deliver business value",
    goals=["G1", "G5"],
    strategy_context="AI agents analysing, proposing, and competing "
    "to improve Harris Farm Markets.",
)


# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------

tab1, tab2, tab3 = st.tabs([
    "Scoreboard", "The Arena", "Agent Network",
])


# ============================================================================
# TAB 1: SCOREBOARD
# ============================================================================

with tab1:
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
                       horizontal=True, key="ah_lb_period")
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
                                    key="ah_award_user")
        award_pts = st.number_input("Points", min_value=1, max_value=100,
                                     value=5, key="ah_award_pts")
        award_cat = st.selectbox("Category", ["human", "ai"],
                                  key="ah_award_cat")
        award_reason = st.text_input("Reason", key="ah_award_reason")
        if st.button("Award", key="ah_award_btn"):
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
        if st.button("Initialize 6 Competing Agents", key="ah_seed_game"):
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
            if st.button("Execute All Approved Tasks", key="ah_exec_game"):
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
# TAB 2: THE ARENA — Agent Competition Dashboard
# ============================================================================

with tab2:
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
                        key="ah_arena_standings")

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
            key="ah_arena_team_select",
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
                                key="ah_arena_team_radar")
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
            key="ah_arena_eval_select",
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
                        key="ah_eval_{}_{}".format(
                            tier["id"],
                            crit_name.lower().replace(" ", "_")[:20]),
                    )
                    eval_submissions.append({
                        "tier": tier["id"],
                        "criterion": crit_name,
                        "score": score,
                    })

        if st.button("Submit Evaluation", key="ah_arena_submit_eval"):
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
                        key="ah_arena_impact_chart")

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
# TAB 3: AGENT NETWORK — Department Analyst Registry
# ============================================================================

with tab3:
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
                                key="ah_agent_bu_filter")

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
                        key="ah_agent_coverage_chart")

    # Active Insights Feed
    st.markdown("---")
    st.markdown("### Active Insights")

    insight_filter = st.radio(
        "Type", ["All", "Opportunity", "Risk", "Trend", "Anomaly"],
        horizontal=True, key="ah_insight_type_filter",
    )
    filtered_insights = insights_data
    if insight_filter != "All":
        filtered_insights = [
            ins for ins in insights_data
            if ins.get("insight_type") == insight_filter.lower()
        ]

    type_icons = {
        "opportunity": "\U0001f4a1",
        "risk": "\u26a0\ufe0f",
        "trend": "\U0001f4c8",
        "anomaly": "\U0001f50d",
    }

    for ins in filtered_insights[:15]:
        itype = ins.get("insight_type", "")
        icon = type_icons.get(itype, "")
        confidence = ins.get("confidence", 0)

        with st.expander(
            "{} {} — {} ({}% confidence)".format(
                icon, ins["title"], ins.get("department", ""),
                int(confidence * 100),
            )
        ):
            st.markdown(ins.get("description", ""))
            ic1, ic2, ic3 = st.columns(3)
            ic1.metric("Confidence", "{:.0f}%".format(confidence * 100))
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
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(
    "Agent Hub | "
    "5 agent teams, 41 analysts, 130-point evaluation rubric | "
    "Scoreboard + Arena + Agent Network"
)
render_voice_data_box("general")

render_footer("Agent Hub", user=user)
