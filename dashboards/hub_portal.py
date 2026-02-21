"""
Harris Farm Hub — Mission Control
Documentation browser, data catalog, AI showcase, and self-improvement engine.
Formerly "Hub Portal" with 11 tabs — agent, intelligence, and operations
tabs have been promoted to standalone pages (Agent Hub, Analytics Engine,
Agent Operations).
"""

import os

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

from shared.styles import render_header, render_footer
from shared.voice_realtime import render_voice_data_box
from shared.portal_content import (
    load_doc, load_procedure, load_learning,
    get_doc_index, get_procedure_index, get_learning_index,
    search_all_docs, parse_audit_metrics, get_data_sources,
    SHOWCASE_IMPLEMENTATIONS,
)

API_URL = os.getenv("API_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# CACHED API HELPERS
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------------------------

user = st.session_state.get("auth_user")
render_header(
    "Mission Control",
    "**Documentation, data catalog, AI showcase & self-improvement** | "
    "Your single source of truth",
    goals=["G1", "G5"],
    strategy_context="The Hub's control centre — strategy visibility, "
    "governance, and continuous improvement.",
)

# Navigation hints to promoted pages
_pages = st.session_state.get("_pages", {})
hint_cols = st.columns(3)
for slug, label, icon in [
    ("agent-hub", "Agent Hub", "\U0001f916"),
    ("analytics-engine", "Analytics Engine", "\U0001f52c"),
    ("agent-ops", "Agent Operations", "\U0001f6e1\ufe0f"),
]:
    page = _pages.get(slug)
    if page:
        with hint_cols[["agent-hub", "analytics-engine", "agent-ops"].index(slug)]:
            st.page_link(page, label="{} {}".format(icon, label),
                         use_container_width=True)

st.markdown("")


# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "Documentation", "Data Catalog", "Showcase", "Self-Improvement",
])


# ============================================================================
# TAB 1: DOCUMENTATION
# ============================================================================

with tab1:
    st.subheader("Documentation Browser")

    # Search bar
    search_q = st.text_input("Search all documentation",
                              placeholder="e.g. fiscal calendar, WATCHDOG, API...",
                              key="mc_portal_search")
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
                if st.button(doc_label, key="mc_doc_{}".format(doc_key),
                              use_container_width=True):
                    st.session_state["portal_active_doc"] = (
                        "doc", doc_key, doc_label)

        # Procedures
        st.markdown("**Procedures**")
        for p in get_procedure_index():
            label = p["name"].replace("_", " ").title()
            if st.button(label, key="mc_proc_{}".format(p["name"]),
                          use_container_width=True):
                st.session_state["portal_active_doc"] = (
                    "procedure", p["name"], label)

        # Learnings
        st.markdown("**Learnings**")
        for l in get_learning_index():
            label = l["name"].replace("_", " ").title()
            if st.button(label, key="mc_learn_{}".format(l["name"]),
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
            st.markdown("### Welcome to Mission Control")
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
                            key="mc_watchdog_radar")

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
        import plotly.express as px
        fig_trend = px.line(
            df_scores, x="task_num", y="avg",
            labels={"task_num": "Task #", "avg": "Average Score"},
            markers=True,
        )
        fig_trend.update_layout(height=300)
        fig_trend.add_hline(y=7, line_dash="dash", line_color="red",
                             annotation_text="Pass threshold (7.0)")
        st.plotly_chart(fig_trend,
                        key="mc_score_trend")


# ============================================================================
# TAB 4: SELF-IMPROVEMENT ENGINE
# ============================================================================

with tab4:
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
        if st.button("Run Full Audit", type="primary", key="mc_ci_run_audit"):
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
            df_cycles = pd.DataFrame(cycles)
            st.dataframe(df_cycles, hide_index=True)
        else:
            st.info("No improvement cycles recorded yet.")

        st.markdown("---")
        st.markdown("### Admin Actions")
        if st.button("Backfill scores from audit.log", key="mc_si_backfill"):
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
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(
    "Mission Control | "
    "Documentation, data catalog, AI showcase & self-improvement | "
    "Content sourced from docs/, watchdog/, and hub_data.db"
)
render_voice_data_box("general")

render_footer("Mission Control", user=user)
