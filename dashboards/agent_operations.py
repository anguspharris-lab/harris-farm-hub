"""
Harris Farm Hub — Agent Operations
Unified agent governance: WATCHDOG safety review, approval queue,
execution & performance monitoring. Merges Hub Portal tabs 9 + 11
into a single 3-stage pipeline.
"""

import json
import os

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

from shared.styles import render_header, render_footer
from shared.voice_realtime import render_voice_data_box
from shared.watchdog_safety import (
    RISK_LEVELS, RISK_COLORS, RISK_ICONS, SYSTEM_STATUS,
)

API_URL = os.getenv("API_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# CACHED API HELPERS
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30, show_spinner=False)
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


# ---------------------------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------------------------

user = st.session_state.get("auth_user")
render_header(
    "Agent Operations",
    "**Safety review, approval queue & execution** | "
    "Every agent proposal passes through WATCHDOG before any action",
    goals=["G1", "G5"],
    strategy_context="Governance pipeline: safety analysis, human approval, "
    "monitored execution. No exceptions.",
)


# ---------------------------------------------------------------------------
# SYSTEM STATUS BANNER
# ---------------------------------------------------------------------------

wd_status = _fetch_watchdog_status()
wd_system = wd_status.get("system", {})
wd_metrics = wd_status.get("metrics", {})

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
        "\U0001f6e1\ufe0f" if status_active else "\u26a0\ufe0f",
        "ACTIVE" if status_active else "OFFLINE",
        "REQUIRED" if wd_system.get("human_in_loop_required") else "OFF",
        "DISABLED" if wd_system.get("auto_implementation_disabled")
        else "ENABLED",
        "ON" if wd_system.get("audit_logging_active") else "OFF",
    ),
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# EXECUTOR STATUS
# ---------------------------------------------------------------------------

exec_status = _fetch_executor_status()
q_approved = exec_status.get("approved_waiting", 0)
q_completed = exec_status.get("completed_total", 0)
q_pending = exec_status.get("pending_total", 0)

es_cols = st.columns(5)
with es_cols[0]:
    st.metric("Total Analyzed", wd_metrics.get("total_proposals", 0))
with es_cols[1]:
    st.metric("Pending Review", wd_metrics.get("pending_review", 0))
with es_cols[2]:
    st.metric("Approved", wd_metrics.get("approved", 0))
with es_cols[3]:
    st.metric("Rejected / Blocked",
              wd_metrics.get("rejected", 0) + wd_metrics.get("blocked_by_watchdog", 0))
with es_cols[4]:
    st.metric("Awaiting Execution", q_approved)


# ---------------------------------------------------------------------------
# TABS — 3-stage pipeline
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "Safety Review", "Approval Queue", "Execution & Performance", "Audit Trail",
])


# ============================================================================
# TAB 1: SAFETY REVIEW (WATCHDOG)
# ============================================================================

with tab1:
    st.subheader("WATCHDOG Safety Review")
    st.caption(
        "Every agent proposal is analysed for security, privacy, "
        "business impact, and compliance risks before human review."
    )

    wd_risk_dist = wd_status.get("risk_distribution", {})

    # Risk Distribution Chart
    if wd_risk_dist:
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
                            key="ao_wd_risk_chart")

    # Pending Safety Queue
    st.markdown("---")
    st.markdown("### Pending Safety Review")
    wd_pending = _fetch_watchdog_pending()

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
                        key="ao_wd_approve_comment_{}".format(tracking),
                        placeholder="Optional comments...",
                    )
                    if st.button(
                        "Approve", key="ao_wd_approve_{}".format(tracking),
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
                        key="ao_wd_reject_comment_{}".format(tracking),
                        placeholder="Required: reason for rejection...",
                    )
                    if st.button(
                        "Reject", key="ao_wd_reject_{}".format(tracking),
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

    # All WATCHDOG Proposals Table
    st.markdown("---")
    st.markdown("### All WATCHDOG Proposals")
    wd_all = _fetch_watchdog_all()
    wd_filter = st.radio(
        "Filter", ["All", "Pending", "Approved", "Rejected", "Blocked"],
        horizontal=True, key="ao_wd_proposal_filter",
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
                "Reviewed By": p.get("reviewed_by", "\u2014"),
                "Created": p.get("created_at", "")[:16],
            })
        df_wd = pd.DataFrame(table_rows)
        st.dataframe(df_wd, hide_index=True)
    else:
        st.info("No proposals match the selected filter.")

    # Safety Policy Reference
    st.markdown("---")
    with st.expander("WATCHDOG Safety Policy Reference"):
        st.markdown("**Risk Levels:**")
        for level in RISK_LEVELS:
            st.markdown("- {} **{}** \u2014 {}".format(
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
        st.markdown("1. Security \u2014 SQL injection, unsafe file ops, "
                     "credentials, external calls")
        st.markdown("2. Code Safety \u2014 resource exhaustion, "
                     "blocked actions, infrastructure changes")
        st.markdown("3. Privacy \u2014 PII detection, customer data access")
        st.markdown("4. Business \u2014 financial impact, complexity validation, "
                     "senior approval triggers")
        st.markdown("5. Compliance \u2014 food safety, financial reporting")


# ============================================================================
# TAB 2: APPROVAL QUEUE (Agent Control — Pending)
# ============================================================================

with tab2:
    st.subheader("Agent Proposal Approval")
    st.caption(
        "Approve or reject agent proposals. Trigger new analysis cycles."
    )

    col_trigger, col_exec, col_spacer = st.columns([1, 1, 2])
    with col_trigger:
        if st.button("Rerun Analysis", type="primary",
                     key="ao_acp_trigger"):
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

    with col_exec:
        if st.button("Execute Approved Now",
                     key="ao_acp_execute_now"):
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
                        "Notes", key="ao_acp_notes_{}".format(pid),
                        placeholder="Optional reviewer notes...",
                        label_visibility="collapsed",
                    )
                with col_approve:
                    if st.button("Approve", key="ao_acp_approve_{}".format(pid),
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
                    if st.button("Reject", key="ao_acp_reject_{}".format(pid)):
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


# ============================================================================
# TAB 3: EXECUTION & PERFORMANCE
# ============================================================================

with tab3:
    st.subheader("Execution & Performance")

    # Agent Performance
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
        df_as = pd.DataFrame(recent_scores)
        display_cols = ["agent_name", "metric", "score", "baseline",
                        "evidence", "timestamp"]
        available = [c for c in display_cols if c in df_as.columns]
        st.dataframe(df_as[available], hide_index=True)

    # Task History
    st.markdown("---")
    st.markdown("### Task History")
    all_proposals = _fetch_agent_proposals()
    if not all_proposals:
        st.info("No agent proposals yet.")
    else:
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
                with st.expander("{} #{} \u2014 {}".format(
                    prop.get("agent_name", ""), prop.get("id", ""),
                    prop.get("task_type", ""),
                )):
                    st.text(prop.get("execution_result", "No result"))


# ============================================================================
# TAB 4: AUDIT TRAIL
# ============================================================================

with tab4:
    st.subheader("Audit Trail")
    st.caption("Complete record of WATCHDOG analyses and human decisions.")

    wd_audit_data = _fetch_watchdog_audit()
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
                    "**{}** {} {} \u2014 {} ({} findings) \u2014 {}".format(
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
                    "\u2705" if d.get("decision") == "approved" else "\u274c")
                st.markdown(
                    "**{}** {} {} \u2014 by **{}** \u2014 {}".format(
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


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(
    "Agent Operations | "
    "WATCHDOG Safety Active | Human-in-Loop Required | "
    "Safety Review \u2192 Approval \u2192 Execution"
)
render_voice_data_box("general")

render_footer("Agent Operations", user=user)
