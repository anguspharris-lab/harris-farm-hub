"""
Harris Farm Hub — Workflow Engine
The central nervous system: Prompt → Prove → Propose → Progress
Multi-project tracking, pipeline view, talent radar, velocity metrics.
"""

import os
import json
from datetime import datetime

import requests
import streamlit as st

from shared.styles import render_header, render_footer, HFM_GREEN, HFM_DARK

API_URL = os.getenv("API_URL", "http://localhost:8000")

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})

render_header(
    "Workflow Engine",
    "**Prompt \u2192 Prove \u2192 Propose \u2192 Progress** | The end-to-end AI workflow for every Harris Farmer",
    goals=["G1", "G2", "G3", "G5"],
    strategy_context="Every prompt flows through a pipeline. Generate, score, iterate, approve. The method in action. "
    "The operating system for a data-first business \u2014 every prompt tracked, every decision auditable, every talent surfaced.",
)
st.caption("Every prompt flows through a pipeline. Generate, score, iterate, approve.")

# ============================================================================
# TABS
# ============================================================================

tab_pipeline, tab_projects, tab_talent, tab_velocity, tab_report = st.tabs([
    "\U0001f4cb Pipeline", "\U0001f4c1 Projects", "\U0001f3af Talent Radar",
    "\u26a1 Velocity", "\U0001f4ca Reports",
])


# ============================================================================
# TAB 1 — Pipeline (Kanban-style view)
# ============================================================================

with tab_pipeline:
    st.markdown("### Workflow Pipeline")
    st.caption("All active submissions by stage. Drag-and-drop coming soon \u2014 use the Prompt Engine to advance items.")

    # Filters
    pc1, pc2 = st.columns(2)
    with pc1:
        pipe_project = st.selectbox("Filter by Project", ["All Projects"], key="wf_pipe_proj")
    with pc2:
        pipe_user = st.text_input("Filter by User ID", key="wf_pipe_user", placeholder="Leave blank for all")

    try:
        params = {}
        if pipe_user:
            params["user_id"] = pipe_user
        resp = requests.get(f"{API_URL}/api/workflow/pipeline", params=params, timeout=10)
        pipeline = resp.json().get("pipeline", {}) if resp.status_code == 200 else {}
    except Exception:
        pipeline = {}
        st.error("Could not connect to Workflow API.")

    # 4P stage columns
    STAGES_DISPLAY = [
        ("prompting", "\u270d\ufe0f Prompt", "#579BFC"),
        ("proving", "\U0001f4ca Prove", "#00C875"),
        ("proposing", "\U0001f4e4 Propose", "#FDAB3D"),
        ("progressing", "\U0001f680 Progress", "#E040FB"),
    ]

    stage_cols = st.columns(len(STAGES_DISPLAY))

    for idx, (stage_key, stage_label, colour) in enumerate(STAGES_DISPLAY):
        items = pipeline.get(stage_key, [])
        with stage_cols[idx]:
            st.markdown(
                f"<div style='text-align:center;padding:8px;background:{colour}20;"
                f"border-radius:8px;border-top:3px solid {colour};margin-bottom:8px;'>"
                f"<strong style='color:{colour};'>{stage_label}</strong>"
                f"<br><span style='font-size:0.8em;color:#8899AA;'>{len(items)} items</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if not items:
                st.caption("No items")
            for item in items[:10]:
                task_type = (item.get("task_type") or "custom").replace("_", " ").title()
                avg = item.get("rubric_average") or 0
                score_color = "#2ECC71" if avg >= 8 else "#d97706" if avg >= 5 else "#dc2626" if avg > 0 else "#8899AA"
                user_id = item.get("user_id", "?")
                st.markdown(
                    f"<div style='background:rgba(255,255,255,0.05);padding:10px;border-radius:8px;"
                    f"border-left:3px solid {colour};margin-bottom:6px;"
                    f"border:1px solid rgba(255,255,255,0.08);font-size:0.85em;'>"
                    f"<strong>#{item['id']}</strong> {task_type}"
                    f"<br><span style='color:#8899AA;'>{user_id}</span>"
                    f"<br><span style='color:{score_color};font-weight:600;'>"
                    f"{avg}/10</span> {item.get('rubric_verdict', '')}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # Also show completed/blocked/archived counts
    st.markdown("---")
    done_cols = st.columns(4)
    for idx, (key, label) in enumerate([
        ("approved", "Approved"), ("completed", "Completed"),
        ("blocked", "Blocked"), ("archived", "Archived"),
    ]):
        items = pipeline.get(key, [])
        with done_cols[idx]:
            st.metric(label, len(items))


# ============================================================================
# TAB 2 — Projects
# ============================================================================

with tab_projects:
    st.markdown("### Project Portfolio")
    st.caption("Track multi-project initiatives across the business.")

    # Create project form
    with st.expander("Create New Project"):
        with st.form("wf_new_project"):
            pname = st.text_input("Project Name", placeholder="e.g. Supply Chain Transformation")
            pdesc = st.text_area("Description", placeholder="What is this project trying to achieve end-to-end?")
            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                ppriority = st.selectbox("Priority", ["P1 (Board)", "P2 (Executive)", "P3 (Department)", "P4 (Team)"])
            with pc2:
                ppillar = st.selectbox("Strategic Pillar", [
                    "Greater Goodness", "Customer", "People", "Operations", "Digital & AI",
                ])
            with pc3:
                pdept = st.text_input("Department", placeholder="e.g. Buying")
            ptarget = st.date_input("Target Date")
            submitted = st.form_submit_button("Create Project", type="primary")
            if submitted and pname:
                try:
                    r = requests.post(f"{API_URL}/api/workflow/projects", json={
                        "name": pname,
                        "description": pdesc,
                        "priority": ppriority.split(" ")[0],
                        "strategic_pillar": ppillar,
                        "department": pdept,
                        "target_date": str(ptarget),
                        "owner_id": user or "unknown",
                    }, timeout=10)
                    if r.status_code == 200:
                        st.success(f"Project created: {pname}")
                        st.rerun()
                    else:
                        st.error(f"Failed: {r.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

    # List projects
    try:
        resp = requests.get(f"{API_URL}/api/workflow/projects", params={"status": "all"}, timeout=10)
        projects = resp.json().get("projects", []) if resp.status_code == 200 else []
    except Exception:
        projects = []
        st.error("Could not load projects.")

    if not projects:
        st.info("No projects yet. Create one above to start tracking work.")
    else:
        for p in projects:
            health_colour = {"green": "#2ECC71", "amber": "#d97706", "red": "#dc2626"}.get(
                p.get("health", "green"), "#8899AA"
            )
            priority = p.get("priority", "P3")
            total = p.get("items_total", 0)
            completed = p.get("items_completed", 0)
            progress = round(completed / max(total, 1) * 100)

            with st.expander(
                f"**{p['name']}** | {priority} | "
                f"{completed}/{total} items | "
                f"Health: {p.get('health', 'green').title()}"
            ):
                mc1, mc2, mc3, mc4 = st.columns(4)
                with mc1:
                    st.metric("Items", total)
                with mc2:
                    st.metric("Completed", completed)
                with mc3:
                    st.metric("Blocked", p.get("items_blocked", 0))
                with mc4:
                    st.metric("Avg Quality", f"{p.get('avg_quality', 0)}/10")

                # Progress bar
                st.progress(progress / 100)
                st.caption(f"{progress}% complete | Target: {p.get('target_date', 'Not set')}")

                if p.get("description"):
                    st.markdown(f"_{p['description']}_")


# ============================================================================
# TAB 3 — Talent Radar
# ============================================================================

with tab_talent:
    st.markdown("### Talent Radar \u2014 Finding the AI Ninjas")
    st.caption(
        "The AI Ninjas could be anywhere \u2014 stores, warehouse, office. "
        "This radar surfaces the people driving change."
    )

    try:
        resp = requests.get(f"{API_URL}/api/workflow/talent-radar", timeout=10)
        radar = resp.json() if resp.status_code == 200 else {}
    except Exception:
        radar = {}
        st.error("Could not load Talent Radar data.")

    # Summary metrics
    tr1, tr2, tr3, tr4 = st.columns(4)
    with tr1:
        st.metric("Active Users", radar.get("total_active_users", 0))
    with tr2:
        st.metric("AI Ninjas", radar.get("total_ninjas", 0))
    with tr3:
        st.metric("Prompt Masters", radar.get("total_masters", 0))
    with tr4:
        dept_count = len(radar.get("department_adoption", []))
        st.metric("Departments Active", dept_count)

    st.markdown("---")

    # Top performers
    st.markdown("#### Top Performers")
    top = radar.get("top_performers", [])
    if top:
        for t in top[:10]:
            level_badge = {
                "AI Ninja": "\U0001f977",
                "Prompt Master": "\U0001f525",
                "Prompt Specialist": "\u26a1",
                "Prompt Apprentice": "\U0001f331",
            }.get(t.get("level", ""), "\U0001f331")

            st.markdown(
                f"<div style='background:rgba(255,255,255,0.05);padding:10px 14px;border-radius:8px;"
                f"border-left:3px solid {HFM_GREEN};margin-bottom:6px;"
                f"border:1px solid rgba(255,255,255,0.08);display:flex;"
                f"justify-content:space-between;align-items:center;'>"
                f"<div>"
                f"<strong>{level_badge} {t['user_id']}</strong>"
                f" <span style='color:#8899AA;font-size:0.85em;'>({t.get('user_role', '')})</span>"
                f"<br><span style='font-size:0.8em;color:#8899AA;'>"
                f"{t.get('submissions', 0)} submissions | "
                f"{t.get('avg_quality', 0)}/10 avg quality | "
                f"{int(t.get('first_time_approval_rate', 0) * 100)}% first-time approval</span>"
                f"</div>"
                f"<div style='text-align:right;'>"
                f"<strong style='color:{HFM_GREEN};font-size:1.1em;'>{t.get('total_points', 0)} pts</strong>"
                f"<br><span style='font-size:0.8em;color:#8899AA;'>{t.get('level', '')}</span>"
                f"</div></div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No submissions yet. Be the first AI Ninja!")

    # Rising stars
    st.markdown("---")
    st.markdown("#### Rising Stars")
    rising = radar.get("rising_stars", [])
    if rising:
        for r in rising[:5]:
            imp = r.get("quality_improvement", 0)
            st.markdown(
                f"\u2b06\ufe0f **{r['user_id']}** ({r.get('user_role', '')}) \u2014 "
                f"+{imp} quality improvement | {r.get('submissions', 0)} submissions"
            )
    else:
        st.caption("Rising stars will appear as users improve their rubric scores over time.")

    # Department adoption
    st.markdown("---")
    st.markdown("#### Department Adoption")
    dept = radar.get("department_adoption", [])
    if dept:
        for d in dept:
            st.markdown(
                f"**{d.get('department', '?')}** \u2014 "
                f"{d.get('active_users', 0)} users | "
                f"{d.get('total_submissions', 0)} submissions | "
                f"Avg quality: {round(d.get('avg_quality') or 0, 1)}/10"
            )
    else:
        st.caption("Department data will populate as more teams use the Hub.")


# ============================================================================
# TAB 4 — Velocity
# ============================================================================

with tab_velocity:
    st.markdown("### Workflow Velocity")
    st.caption("How fast is work moving through the pipeline? Where are the bottlenecks?")

    try:
        resp = requests.get(f"{API_URL}/api/workflow/velocity", timeout=10)
        vel = resp.json() if resp.status_code == 200 else {}
    except Exception:
        vel = {}
        st.error("Could not load velocity data.")

    vc1, vc2, vc3 = st.columns(3)
    with vc1:
        st.metric("Submitted (30d)", vel.get("submitted_last_n_days", 0))
    with vc2:
        st.metric("Completed (30d)", vel.get("completed_last_n_days", 0))
    with vc3:
        st.metric("Throughput", f"{vel.get('throughput_pct', 0)}%")

    # Bottlenecks
    bottlenecks = vel.get("bottlenecks", [])
    if bottlenecks:
        st.markdown("---")
        st.markdown("#### Bottlenecks")
        st.caption("Items stuck in a stage for more than 48 hours.")
        for b in bottlenecks:
            stage = b.get("workflow_stage", "?")
            colour = {
                "proposing": "#FDAB3D",
                "proving": "#00C875",
                "blocked": "#dc2626",
            }.get(stage, "#8899AA")
            st.markdown(
                f"<div style='background:{colour}10;padding:10px;border-radius:8px;"
                f"border-left:3px solid {colour};margin-bottom:6px;'>"
                f"<strong style='color:{colour};'>{stage.title()}</strong>: "
                f"{b.get('count', 0)} items stuck"
                f"<br><span style='font-size:0.8em;color:#8899AA;'>Oldest: {(b.get('oldest') or '')[:16]}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.success("No bottlenecks \u2014 all items are flowing smoothly.")


# ============================================================================
# TAB 5 — Reports
# ============================================================================

with tab_report:
    st.markdown("### Hub Reports")

    report_type = st.radio(
        "Report Type", ["Weekly Hub Report", "Monthly Board Summary"],
        horizontal=True, key="wf_report_type",
    )

    if report_type == "Weekly Hub Report":
        try:
            resp = requests.get(f"{API_URL}/api/workflow/report/weekly", timeout=10)
            rpt = resp.json() if resp.status_code == 200 else {}
        except Exception:
            rpt = {}
            st.error("Could not generate weekly report.")

        if rpt:
            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                change = rpt.get("change_pct", 0)
                delta_str = f"{change:+.0f}%" if change != 0 else "0%"
                st.metric("Submissions This Week", rpt.get("submissions_this_week", 0), delta=delta_str)
            with rc2:
                st.metric("Approved", rpt.get("approved_this_week", 0))
            with rc3:
                st.metric("Avg Quality", f"{rpt.get('avg_quality', 0)}/10")
            with rc4:
                st.metric("Adoption Gaps", len(rpt.get("adoption_gaps", [])))

            # Top performers
            top = rpt.get("top_performers", [])
            if top:
                st.markdown("#### Top Performers This Week")
                for i, t in enumerate(top, 1):
                    medal = ["\U0001f947", "\U0001f948", "\U0001f949", "4\ufe0f\u20e3", "5\ufe0f\u20e3"][min(i - 1, 4)]
                    st.markdown(f"{medal} **{t['user_id']}** \u2014 {t['points']} points")

            # Gaps
            gaps = rpt.get("adoption_gaps", [])
            if gaps:
                st.markdown("#### The Gap \u2014 Roles Not Yet Active This Week")
                st.caption("These roles haven't submitted any prompts. They need champions.")
                for g in gaps:
                    st.markdown(f"\u26a0\ufe0f {g}")

    else:  # Monthly
        try:
            resp = requests.get(f"{API_URL}/api/workflow/report/monthly", timeout=10)
            rpt = resp.json() if resp.status_code == 200 else {}
        except Exception:
            rpt = {}
            st.error("Could not generate monthly report.")

        if rpt:
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                st.metric("Active Users", rpt.get("active_users", 0))
            with mc2:
                st.metric("Submissions", rpt.get("total_submissions", 0))
            with mc3:
                st.metric("Approved", rpt.get("total_approved", 0))
            with mc4:
                st.metric("Avg Quality", f"{rpt.get('avg_quality', 0)}/10")

            st.markdown("---")
            st.markdown("#### Impact Estimates")
            ic1, ic2 = st.columns(2)
            with ic1:
                st.metric("Est. Hours Saved", f"{rpt.get('est_hours_saved', 0)}h")
            with ic2:
                st.metric("Est. Cost Saving", f"${rpt.get('est_cost_saving_aud', 0):,}")

            st.markdown("---")
            st.markdown("#### AI Ninja Level Distribution")
            levels = rpt.get("level_distribution", {})
            for level, count in levels.items():
                badge = {
                    "AI Ninja": "\U0001f977", "Prompt Master": "\U0001f525",
                    "Prompt Specialist": "\u26a1", "Prompt Apprentice": "\U0001f331",
                }.get(level, "")
                st.markdown(f"{badge} **{level}**: {count}")


# ============================================================================
# FOOTER
# ============================================================================

render_footer("Workflow Engine", user=user)
