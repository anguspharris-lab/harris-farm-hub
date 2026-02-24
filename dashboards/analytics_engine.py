"""
Harris Farm Hub — Analytics Engine
Data Intelligence command center: run analyses against 383M+ POS transactions,
review generated reports, submit NL-driven agent tasks, browse demo insights.
Extracted from hub_portal.py Tab 8.
"""

import os

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

from shared.styles import render_header, render_footer
from shared.voice_realtime import render_voice_data_box
from shared.agent_teams import (
    DATA_INTELLIGENCE_AGENTS, DATA_INTEL_CATEGORIES,
    get_data_intel_agent,
)

API_URL = os.getenv("API_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# CACHED API HELPERS
# ---------------------------------------------------------------------------

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


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_agent_tasks():
    try:
        return requests.get(
            "{}/api/agent-tasks".format(API_URL),
            params={"limit": 20}, timeout=5
        ).json().get("tasks", [])
    except Exception:
        return []


# ---------------------------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------------------------

user = st.session_state.get("auth_user")
render_header(
    "Analytics Engine",
    "**Data Intelligence Command Center** | "
    "This is Harris Farming It. Ask the question. Get the answer.",
    goals=["G2", "G4"],
    strategy_context="The more context you give, the better the answer. "
    "AI reads 383M+ transactions so you don't have to.",
)
st.caption("This is Harris Farming It. Ask the question. Get the answer.")


# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------

di_sub1, di_sub2, di_sub3, di_sub4 = st.tabs([
    "Run Analysis", "Generated Reports", "Agent Tasks", "Demo Insights",
])


# ============================================================================
# SUB-TAB 1: RUN ANALYSIS
# ============================================================================

with di_sub1:
    st.subheader("Run Analysis")
    st.caption(
        "Step 2: The more context you give, the better the answer. "
        "Select an analysis type, pick a store, and run."
    )

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
            key="ae_analysis_type",
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
                key="ae_store_id",
            )
        else:
            store_id = None
            st.info("Network-wide analysis (all stores)")

        days = st.slider("Lookback (days)", 14, 90, 30,
                         key="ae_days_slider")

    if st.button("Run Analysis", type="primary", key="ae_run_btn"):
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
                    st.caption("Step 5: Review this. Add your judgment. Your expertise matters most.")
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


# ============================================================================
# SUB-TAB 2: GENERATED REPORTS
# ============================================================================

with di_sub2:
    st.subheader("Generated Reports")
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
                                key="ae_rpt_{}_tbl_{}".format(rpt_id, ti))
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
                                key="ae_dl_{}_{}".format(rpt_id, fmt),
                            )
                    except Exception:
                        col.caption("{} unavailable".format(label))


# ============================================================================
# SUB-TAB 3: AGENT TASKS (NL-driven on-demand execution)
# ============================================================================

with di_sub3:
    st.subheader("On-Demand Agent Tasks")
    st.caption(
        "Step 2: The more context you give, the better the answer. "
        "Describe what you want to analyse in plain English. "
        "The system routes your request to the right analysis, "
        "executes it against real transaction data, scores the "
        "report, and runs a WATCHDOG safety review."
    )

    st.caption("\U0001f4a1 Step 2: Flood it with context. Who is this for? What decision does it drive? What format do you need?")
    at_query = st.text_area(
        "What do you want to analyse?",
        height=100,
        placeholder=(
            "e.g. 'Find products that run out during the day abnormally "
            "- items that deviate from their normal hourly basket "
            "penetration'"
        ),
        key="ae_at_query_input",
    )

    at_col1, at_col2 = st.columns([2, 1])
    with at_col1:
        at_store_keys = ["Auto"] + list(STORE_OPTIONS.keys())
        at_store = st.selectbox(
            "Store (optional)",
            at_store_keys,
            format_func=lambda k: "Auto-detect" if k == "Auto"
                else "{} ({})".format(STORE_OPTIONS.get(k, k), k),
            key="ae_at_store_select",
        )
    with at_col2:
        at_days = st.slider("Lookback (days)", 7, 90, 30,
                            key="ae_at_days_slider")

    if st.button("Submit Task", type="primary", key="ae_at_submit_btn"):
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
                                            key="ae_at_rpt_{}_tbl_{}".format(
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
                                        key="ae_at_rpt_{}_recs".format(
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
                                                key="ae_at_dl_{}_{}".format(
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


# ============================================================================
# SUB-TAB 4: DEMO INSIGHTS (existing seeded data)
# ============================================================================

with di_sub4:
    st.subheader("Demo Insights")
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
        "opportunity": "\U0001f4a1", "risk": "\u26a0\ufe0f",
        "trend": "\U0001f4c8", "anomaly": "\U0001f50d",
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
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(
    "Analytics Engine | "
    "383M+ POS transactions | Real-time intelligence | "
    "WATCHDOG safety reviewed"
)
render_voice_data_box("general")

render_footer("Analytics Engine", user=user)
