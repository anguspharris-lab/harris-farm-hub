"""
Harris Farm Hub - Prompt-to-Approval: Approvals Dashboard
Managers review, approve, or request changes on PtA submissions.
"""

import os
import json

import requests
import streamlit as st
from datetime import datetime

from shared.styles import render_header, render_footer
from shared.pta_rubric import render_rubric_scorecard, APPROVAL_ROUTING

API_URL = os.getenv("API_URL", "http://localhost:8000")

user = st.session_state.get("auth_user")

render_header(
    "Approvals",
    "**Prompt-to-Approval** | Review and approve team submissions",
    goals=["G2", "G3"],
    strategy_context="The human sign-off that ensures quality — every output reviewed before it ships.",
)

# ============================================================================
# SIDEBAR — Filter & Stats
# ============================================================================

with st.sidebar:
    st.header("Filters")
    status_filter = st.selectbox(
        "Status",
        ["pending_approval", "approved", "revision_requested", "all"],
        format_func=lambda s: {
            "pending_approval": "Pending Approval",
            "approved": "Approved",
            "revision_requested": "Changes Requested",
            "all": "All Submissions",
        }.get(s, s),
        key="appr_status_filter",
    )

    task_filter = st.selectbox(
        "Task Type",
        ["all", "weekly_store_performance", "waste_analysis", "monthly_variance",
         "board_paper", "trading_meeting_prep", "category_review", "custom"],
        format_func=lambda s: s.replace("_", " ").title() if s != "all" else "All Types",
        key="appr_task_filter",
    )

    st.markdown("---")
    st.header("Quick Stats")

    try:
        all_subs = requests.get(
            f"{API_URL}/api/pta/submissions", params={"limit": 200}, timeout=5
        ).json().get("submissions", [])

        pending = sum(1 for s in all_subs if s["status"] == "pending_approval")
        approved = sum(1 for s in all_subs if s["status"] == "approved")
        revisions = sum(1 for s in all_subs if s["status"] == "revision_requested")

        st.metric("Pending Review", pending)
        st.metric("Approved", approved)
        st.metric("Changes Requested", revisions)
    except Exception:
        st.caption("Could not load stats.")


# ============================================================================
# MAIN — Submissions List
# ============================================================================

# Fetch submissions
params = {"limit": 50}
if status_filter != "all":
    params["status"] = status_filter
if task_filter != "all":
    params["task_type"] = task_filter

try:
    resp = requests.get(f"{API_URL}/api/pta/submissions", params=params, timeout=10)
    submissions = resp.json().get("submissions", []) if resp.status_code == 200 else []
except Exception:
    submissions = []
    st.error("Could not connect to Hub backend.")

if not submissions:
    if status_filter == "pending_approval":
        st.info("No submissions waiting for approval. Your team is all caught up!")
    else:
        st.info("No submissions found for the selected filters.")
else:
    st.markdown(f"**{len(submissions)} submission(s)**")

    for sub in submissions:
        sub_id = sub["id"]
        task_type = sub.get("task_type", "custom").replace("_", " ").title()
        user_id = sub.get("user_id", "unknown")
        user_role = sub.get("user_role", "")
        avg = sub.get("rubric_average") or 0
        verdict = sub.get("rubric_verdict", "")
        status = sub.get("status", "draft")
        created = sub.get("created_at", "")[:16]
        output_fmt = sub.get("output_format", "")

        # Status colour
        status_colours = {
            "pending_approval": "#d97706",
            "approved": "#16a34a",
            "revision_requested": "#dc2626",
            "draft": "#6b7280",
            "generated": "#3b82f6",
            "scored": "#8b5cf6",
        }
        colour = status_colours.get(status, "#6b7280")

        # Summary card
        with st.expander(
            f"**#{sub_id}** | {task_type} | {user_role} | "
            f"{avg}/10 ({verdict}) | "
            f"_{status.replace('_', ' ').title()}_"
        ):
            # Load full details
            try:
                full = requests.get(
                    f"{API_URL}/api/pta/submissions/{sub_id}", timeout=10
                ).json()
            except Exception:
                st.error("Could not load submission details.")
                continue

            # Overview
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Rubric Average", f"{avg}/10")
            with col2:
                st.metric("Verdict", verdict or "N/A")
            with col3:
                st.metric("Iterations", full.get("iteration_count", 1))
            with col4:
                st.metric("Format", output_fmt)

            st.caption(f"Submitted by: **{user_id}** ({user_role}) | {created}")

            # Original prompt
            with st.container():
                st.markdown("**Original Prompt:**")
                st.markdown(
                    f"<div style='background:#f9fafb; padding:12px; border-radius:6px; "
                    f"font-size:0.9em; border:1px solid #e5e7eb;'>"
                    f"{full.get('original_prompt', 'N/A')}</div>",
                    unsafe_allow_html=True,
                )

            # AI Output
            st.markdown("---")
            st.markdown("**AI Output:**")
            ai_output = full.get("ai_output", "")
            if ai_output:
                with st.container():
                    st.markdown(ai_output)
            else:
                st.caption("No output available.")

            # Human Annotations
            annotations = full.get("human_annotations", [])
            if annotations:
                st.markdown("---")
                st.markdown("**Human Annotations:**")
                for ann in annotations:
                    st.markdown(
                        f"<div style='background:#ecfdf5; padding:10px; border-radius:6px; "
                        f"border-left:3px solid #16a34a; margin-bottom:8px; font-size:0.9em;'>"
                        f"{ann}</div>",
                        unsafe_allow_html=True,
                    )

            # Rubric Scorecard
            rubric_scores = full.get("rubric_scores")
            if rubric_scores:
                st.markdown("---")
                st.markdown("**Rubric Scorecard:**")
                if isinstance(rubric_scores, str):
                    try:
                        rubric_scores = json.loads(rubric_scores)
                    except (json.JSONDecodeError, TypeError):
                        rubric_scores = None
                if rubric_scores:
                    render_rubric_scorecard(rubric_scores)

            # Approver notes (if any)
            if full.get("approver_notes"):
                st.markdown("---")
                st.markdown("**Approver Notes:**")
                st.info(full["approver_notes"])

            # Action buttons (only for pending submissions)
            if status == "pending_approval":
                st.markdown("---")
                st.markdown("**Your Decision:**")

                notes = st.text_area(
                    "Notes (optional)",
                    placeholder="Add feedback for the submitter...",
                    key=f"appr_notes_{sub_id}",
                )

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button(
                        "Approve",
                        type="primary",
                        use_container_width=True,
                        key=f"appr_approve_{sub_id}",
                    ):
                        try:
                            r = requests.post(
                                f"{API_URL}/api/pta/approve/{sub_id}",
                                params={"approver": "manager", "notes": notes},
                                timeout=10,
                            )
                            if r.status_code == 200:
                                st.success(f"Submission #{sub_id} approved! {r.json().get('points_awarded', 0)} points awarded.")
                                st.rerun()
                            else:
                                st.error(f"Failed: {r.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")

                with col_b:
                    if st.button(
                        "Request Changes",
                        use_container_width=True,
                        key=f"appr_revise_{sub_id}",
                    ):
                        if not notes.strip():
                            st.warning("Please add notes explaining what changes are needed.")
                        else:
                            try:
                                r = requests.post(
                                    f"{API_URL}/api/pta/request-changes/{sub_id}",
                                    params={"approver": "manager", "notes": notes},
                                    timeout=10,
                                )
                                if r.status_code == 200:
                                    st.info(f"Submission #{sub_id} sent back for changes.")
                                    st.rerun()
                                else:
                                    st.error(f"Failed: {r.text}")
                            except Exception as e:
                                st.error(f"Error: {e}")

                with col_c:
                    if st.button(
                        "Escalate",
                        use_container_width=True,
                        key=f"appr_escalate_{sub_id}",
                    ):
                        st.info("Escalation would forward to next approval level. (Coming soon)")


# ============================================================================
# FOOTER
# ============================================================================

render_footer("Approvals", user=user)
