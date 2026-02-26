"""
Harris Farm Hub -- MDHE Issue Tracker
Track and resolve master data quality issues generated from MDHE validations.
Filterable by status, domain, severity. Supports bulk actions and inline updates.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict

import pandas as pd
import streamlit as st

# Backend imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from mdhe_db import init_mdhe_db, get_issues, update_issue
from shared.styles import (
    render_header, render_footer,
    GREEN, BLUE, GOLD, RED, ORANGE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    NAVY_CARD, NAVY_MID, BORDER,
)

# Ensure MDHE tables exist
init_mdhe_db()

# ============================================================================
# Constants
# ============================================================================

STATUS_OPTIONS = ["All", "open", "in_progress", "resolved", "wont_fix"]
STATUS_LABELS = {
    "All": "All",
    "open": "Open",
    "in_progress": "In Progress",
    "resolved": "Resolved",
    "wont_fix": "Won't Fix",
}
STATUS_COLORS = {
    "open": RED,
    "in_progress": ORANGE,
    "resolved": GREEN,
    "wont_fix": TEXT_MUTED,
}

SEVERITY_OPTIONS = ["All", "critical", "high", "medium", "low"]
SEVERITY_LABELS = {
    "All": "All",
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}
SEVERITY_COLORS = {
    "critical": RED,
    "high": ORANGE,
    "medium": GOLD,
    "low": TEXT_MUTED,
}

UPDATE_STATUS_OPTIONS = ["open", "in_progress", "resolved", "wont_fix"]


# ============================================================================
# Helpers
# ============================================================================

def _count_by_status(issues, status):
    # type: (List[Dict], str) -> int
    return sum(1 for i in issues if i.get("status") == status)


def _severity_label(severity):
    # type: (str) -> str
    return SEVERITY_LABELS.get(severity, severity)


def _status_label(status):
    # type: (str) -> str
    return STATUS_LABELS.get(status, status)


def _get_unique_domains(issues):
    # type: (List[Dict]) -> List[str]
    """Extract unique domain values from issues list."""
    domains = sorted(set(i.get("domain", "") for i in issues if i.get("domain")))
    return domains


# ============================================================================
# Main render function
# ============================================================================

def render_mdhe_issues():
    user = st.session_state.get("auth_user", {})

    render_header(
        "MDHE -- Issue Tracker",
        "Track and resolve master data quality issues",
    )

    # ------------------------------------------------------------------
    # Load all issues (unfiltered) for summary metrics
    # ------------------------------------------------------------------

    all_issues = get_issues(limit=1000)

    # ------------------------------------------------------------------
    # Section 1: Summary Metrics
    # ------------------------------------------------------------------

    st.subheader("Issue Summary")

    m1, m2, m3, m4 = st.columns(4)
    open_count = _count_by_status(all_issues, "open")
    in_progress_count = _count_by_status(all_issues, "in_progress")
    resolved_count = _count_by_status(all_issues, "resolved")
    wont_fix_count = _count_by_status(all_issues, "wont_fix")

    with m1:
        st.metric("Open Issues", open_count)
    with m2:
        st.metric("In Progress", in_progress_count)
    with m3:
        st.metric("Resolved", resolved_count)
    with m4:
        st.metric("Won't Fix", wont_fix_count)

    if not all_issues:
        st.info(
            "No issues found. Upload data in the MDHE Upload page or seed demo data to get started."
        )
        _pages = st.session_state.get("_pages", {})
        if "mdhe-upload" in _pages:
            st.page_link(_pages["mdhe-upload"], label="Go to MDHE Upload")
        render_footer("MDHE Issues", user=user)
        return

    # ------------------------------------------------------------------
    # Section 2: Filters
    # ------------------------------------------------------------------

    st.markdown("---")

    all_domains = _get_unique_domains(all_issues)
    domain_options = ["All"] + all_domains

    f1, f2, f3 = st.columns(3)
    with f1:
        filter_status = st.selectbox(
            "Status",
            STATUS_OPTIONS,
            format_func=lambda s: STATUS_LABELS.get(s, s),
            key="mdhe_issue_status_filter",
        )
    with f2:
        filter_domain = st.selectbox(
            "Domain",
            domain_options,
            key="mdhe_issue_domain_filter",
        )
    with f3:
        filter_severity = st.selectbox(
            "Severity",
            SEVERITY_OPTIONS,
            format_func=lambda s: SEVERITY_LABELS.get(s, s),
            key="mdhe_issue_severity_filter",
        )

    # Fetch filtered issues
    query_status = filter_status if filter_status != "All" else None
    query_domain = filter_domain if filter_domain != "All" else None
    query_severity = filter_severity if filter_severity != "All" else None

    filtered_issues = get_issues(
        status=query_status,
        domain=query_domain,
        severity=query_severity,
        limit=500,
    )

    st.caption("%d issue(s) matching filters" % len(filtered_issues))

    # ------------------------------------------------------------------
    # Section 3: Issues List
    # ------------------------------------------------------------------

    st.markdown("---")
    st.subheader("Issues")

    if not filtered_issues:
        st.info("No issues match the current filters.")
    else:
        for issue in filtered_issues:
            issue_id = issue.get("id", 0)
            title = issue.get("title", "Untitled Issue")
            description = issue.get("description", "")
            domain = issue.get("domain", "unknown")
            severity = issue.get("severity", "medium")
            status = issue.get("status", "open")
            assigned_to = issue.get("assigned_to", "")
            created_at = issue.get("created_at", "")
            validation_id = issue.get("validation_id")

            # Severity and status display colors
            sev_color = SEVERITY_COLORS.get(severity, TEXT_MUTED)
            stat_color = STATUS_COLORS.get(status, TEXT_MUTED)

            with st.container(border=True):
                # Title row with badges
                title_col, badge_col = st.columns([3, 1])
                with title_col:
                    st.markdown("**#%d** %s" % (issue_id, title))
                with badge_col:
                    st.markdown(
                        "**%s** | **%s**"
                        % (_severity_label(severity), _status_label(status))
                    )

                # Description
                if description:
                    st.caption(description[:200])

                # Detail expander
                with st.expander("Details & Actions"):
                    # Full description
                    if description and len(description) > 200:
                        st.markdown("**Full Description**")
                        st.markdown(description)

                    # Metadata
                    detail_c1, detail_c2, detail_c3 = st.columns(3)
                    with detail_c1:
                        st.markdown("**Domain:** %s" % domain)
                        st.markdown("**Created:** %s" % (created_at[:16] if created_at else "N/A"))
                    with detail_c2:
                        st.markdown("**Severity:** %s" % _severity_label(severity))
                        if validation_id:
                            st.markdown("**Validation ID:** %s" % str(validation_id))
                    with detail_c3:
                        st.markdown("**Status:** %s" % _status_label(status))
                        st.markdown("**Assigned To:** %s" % (assigned_to or "Unassigned"))

                    # Update controls
                    st.markdown("---")
                    st.markdown("**Update Issue**")

                    update_c1, update_c2, update_c3 = st.columns([2, 2, 1])

                    with update_c1:
                        current_status_idx = 0
                        if status in UPDATE_STATUS_OPTIONS:
                            current_status_idx = UPDATE_STATUS_OPTIONS.index(status)
                        new_status = st.selectbox(
                            "New Status",
                            UPDATE_STATUS_OPTIONS,
                            index=current_status_idx,
                            format_func=lambda s: STATUS_LABELS.get(s, s),
                            key="mdhe_issue_status_%d" % issue_id,
                        )

                    with update_c2:
                        new_assigned = st.text_input(
                            "Assigned To",
                            value=assigned_to or "",
                            key="mdhe_issue_assigned_%d" % issue_id,
                            placeholder="Enter name or email",
                        )

                    with update_c3:
                        st.markdown("")  # spacer for alignment
                        st.markdown("")
                        if st.button(
                            "Update",
                            key="mdhe_issue_update_%d" % issue_id,
                            use_container_width=True,
                        ):
                            try:
                                resolved_by = None
                                if new_status == "resolved":
                                    user_email = ""
                                    if isinstance(user, dict):
                                        user_email = user.get("email", "")
                                    resolved_by = user_email or new_assigned or "system"

                                update_issue(
                                    issue_id,
                                    status=new_status,
                                    assigned_to=new_assigned if new_assigned else None,
                                    resolved_by=resolved_by,
                                )
                                st.success("Issue #%d updated." % issue_id)
                                st.rerun()
                            except Exception as e:
                                st.error("Update failed: %s" % str(e))

    # ------------------------------------------------------------------
    # Section 4: Bulk Actions
    # ------------------------------------------------------------------

    st.markdown("---")
    st.subheader("Bulk Actions")

    bulk_c1, bulk_c2 = st.columns(2)

    with bulk_c1:
        st.markdown("**Assign all open issues in a domain**")
        bulk_domain_options = ["All"] + all_domains
        bulk_domain = st.selectbox(
            "Domain",
            bulk_domain_options,
            key="mdhe_bulk_domain",
        )
        bulk_assignee = st.text_input(
            "Assign to",
            key="mdhe_bulk_assignee",
            placeholder="Enter name or email",
        )
        if st.button("Assign", key="mdhe_bulk_assign_btn"):
            if not bulk_assignee.strip():
                st.warning("Please enter an assignee name or email.")
            else:
                try:
                    target_domain = bulk_domain if bulk_domain != "All" else None
                    open_issues = get_issues(status="open", domain=target_domain, limit=1000)
                    count = 0
                    for issue in open_issues:
                        update_issue(
                            issue["id"],
                            assigned_to=bulk_assignee.strip(),
                        )
                        count += 1
                    if count > 0:
                        domain_label = bulk_domain if bulk_domain != "All" else "all domains"
                        st.success(
                            "Assigned %d open issue(s) in %s to %s."
                            % (count, domain_label, bulk_assignee.strip())
                        )
                        st.rerun()
                    else:
                        st.info("No open issues found for the selected domain.")
                except Exception as e:
                    st.error("Bulk assign failed: %s" % str(e))

    with bulk_c2:
        st.markdown("**Close old resolved issues**")
        st.caption("Close all issues that were resolved more than 7 days ago.")
        if st.button("Close Resolved (>7 days)", key="mdhe_bulk_close_btn"):
            try:
                resolved_issues = get_issues(status="resolved", limit=1000)
                cutoff = datetime.utcnow() - timedelta(days=7)
                count = 0
                for issue in resolved_issues:
                    resolved_at = issue.get("resolved_at", "")
                    if resolved_at:
                        try:
                            resolved_dt = datetime.strptime(resolved_at[:19], "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            try:
                                resolved_dt = datetime.strptime(resolved_at[:10], "%Y-%m-%d")
                            except ValueError:
                                continue
                        if resolved_dt < cutoff:
                            update_issue(issue["id"], status="wont_fix")
                            count += 1
                if count > 0:
                    st.success("Closed %d resolved issue(s) older than 7 days." % count)
                    st.rerun()
                else:
                    st.info("No resolved issues older than 7 days found.")
            except Exception as e:
                st.error("Bulk close failed: %s" % str(e))

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------

    render_footer("MDHE Issues", user=user)


# ============================================================================
# Run
# ============================================================================

render_mdhe_issues()
