"""
Harris Farm Hub -- Master Data Health Engine (MDHE) Dashboard
Displays master data health scores, validation details, scan verification,
trends, and AI insights across 5 tabs.

Data source: mdhe_db module (SQLite backend for validation results, scores, scans).
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Backend import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from mdhe_db import (
    init_mdhe_db,
    get_latest_scores,
    get_score_history,
    get_validations,
    get_issues,
    get_scan_results,
    get_plu_records,
)

from shared.styles import (
    render_header,
    render_footer,
    plotly_dark_template,
    GREEN,
    BLUE,
    GOLD,
    PURPLE,
    RED,
    ORANGE,
    CYAN,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    NAVY,
    NAVY_CARD,
    NAVY_MID,
    BORDER,
    GLASS,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Initialise MDHE database tables
# ═══════════════════════════════════════════════════════════════════════════════

init_mdhe_db()


# ═══════════════════════════════════════════════════════════════════════════════
# Constants & helpers
# ═══════════════════════════════════════════════════════════════════════════════

DOMAINS = ["PLU", "Barcode", "Pricing", "Hierarchy", "Supplier"]
LAYERS = ["Rules", "Standards", "AI", "Recon"]
SEVERITIES = ["Critical", "High", "Medium", "Low"]

DOMAIN_COLORS = {
    "PLU": GREEN,
    "Barcode": BLUE,
    "Pricing": GOLD,
    "Hierarchy": PURPLE,
    "Supplier": ORANGE,
    "Overall": CYAN,
}

SEVERITY_COLORS = {
    "Critical": RED,
    "High": ORANGE,
    "Medium": GOLD,
    "Low": BLUE,
}

SEVERITY_ICONS = {
    "Critical": "!!",
    "High": "!",
    "Medium": "~",
    "Low": "-",
}


def score_color(score):
    """Return theme colour based on health score thresholds."""
    if score is None:
        return TEXT_MUTED
    if score >= 95:
        return GREEN
    if score >= 85:
        return BLUE
    if score >= 70:
        return GOLD
    return RED


def score_label(score):
    """Return human-readable label for a score band."""
    if score is None:
        return "No Data"
    if score >= 95:
        return "Excellent"
    if score >= 85:
        return "Good"
    if score >= 70:
        return "Fair"
    return "Poor"


def safe_json_loads(val, default=None):
    """Parse a JSON string safely, returning default on failure."""
    if val is None:
        return default or {}
    if isinstance(val, dict):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default or {}


# ═══════════════════════════════════════════════════════════════════════════════
# Cached data loaders
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_latest_scores():
    """Fetch the most recent domain health scores."""
    return get_latest_scores()


@st.cache_data(ttl=300)
def load_score_history(days=30):
    """Fetch score history for the last N days."""
    return get_score_history(days=days)


@st.cache_data(ttl=300)
def load_validations(domain=None, severity=None, layer=None):
    """Fetch validation results with optional filters."""
    return get_validations(domain=domain, severity=severity, layer=layer)


@st.cache_data(ttl=300)
def load_issues(status=None):
    """Fetch issues, optionally filtered by status."""
    return get_issues(status=status)


@st.cache_data(ttl=300)
def load_scan_results():
    """Fetch scan verification results."""
    return get_scan_results()


@st.cache_data(ttl=300)
def load_plu_records():
    """Fetch PLU master data records."""
    return get_plu_records()


# ═══════════════════════════════════════════════════════════════════════════════
# Main render function
# ═══════════════════════════════════════════════════════════════════════════════

def render_mdhe_dashboard():
    user = st.session_state.get("auth_user", {})

    render_header(
        "Master Data Health Engine",
        "Validate, score, and fix product master data quality issues",
    )

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Health Overview",
        "Validation Detail",
        "Scan Verification",
        "Trends & History",
        "AI Insights",
    ])

    # ==================================================================
    # TAB 1: Health Overview
    # ==================================================================
    with tab1:
        _render_health_overview()

    # ==================================================================
    # TAB 2: Validation Detail
    # ==================================================================
    with tab2:
        _render_validation_detail()

    # ==================================================================
    # TAB 3: Scan Verification
    # ==================================================================
    with tab3:
        _render_scan_verification()

    # ==================================================================
    # TAB 4: Trends & History
    # ==================================================================
    with tab4:
        _render_trends_history()

    # ==================================================================
    # TAB 5: AI Insights
    # ==================================================================
    with tab5:
        _render_ai_insights()

    # ── Footer ────────────────────────────────────────────────────────────
    render_footer("MDHE Dashboard", user=user)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Health Overview
# ═══════════════════════════════════════════════════════════════════════════════

def _render_health_overview():
    st.subheader("Data Health Overview")

    scores_raw = load_latest_scores()

    if not scores_raw:
        st.info(
            "No validation data yet. Upload master data files via the MDHE "
            "Upload page to get started."
        )
        return

    # Build a scores dict keyed by domain
    scores = {}
    for row in scores_raw:
        domain = row.get("domain", "Unknown")
        scores[domain] = {
            "score": row.get("score", 0),
            "layer_scores": safe_json_loads(row.get("layer_scores")),
            "record_count": row.get("record_count", 0),
            "validated_at": row.get("validated_at", ""),
        }

    # ── Overall score ─────────────────────────────────────────────────
    domain_scores = [s["score"] for s in scores.values() if s["score"] is not None]
    overall = sum(domain_scores) / len(domain_scores) if domain_scores else 0

    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            colour = score_color(overall)
            label = score_label(overall)
            st.markdown(
                f"<h1 style='text-align:center;color:{colour};font-size:4rem;"
                f"margin-bottom:0;'>{overall:.1f}</h1>"
                f"<p style='text-align:center;color:{TEXT_SECONDARY};"
                f"font-size:1.2rem;margin-top:0;'>"
                f"Overall Health Score  |  {label}</p>",
                unsafe_allow_html=True,
            )

    st.markdown("")

    # ── Domain score cards ────────────────────────────────────────────
    cols = st.columns(5)
    for idx, domain in enumerate(DOMAINS):
        with cols[idx]:
            data = scores.get(domain, {})
            sc = data.get("score")
            rc = data.get("record_count", 0)
            colour = score_color(sc)
            display_score = f"{sc:.1f}" if sc is not None else "--"
            display_records = f"{rc:,}" if rc else "0"

            with st.container(border=True):
                st.markdown(
                    f"<p style='color:{TEXT_MUTED};font-size:0.9rem;"
                    f"margin-bottom:4px;text-align:center;'>{domain}</p>"
                    f"<h2 style='text-align:center;color:{colour};"
                    f"margin:0;font-size:2.4rem;'>{display_score}</h2>"
                    f"<p style='text-align:center;color:{TEXT_MUTED};"
                    f"font-size:0.8rem;margin-top:4px;'>"
                    f"{display_records} records</p>",
                    unsafe_allow_html=True,
                )
                # Progress bar as visual indicator
                if sc is not None:
                    st.progress(min(sc / 100.0, 1.0))

    st.markdown("")

    # ── Layer breakdown chart ─────────────────────────────────────────
    st.subheader("Score by Validation Layer")

    layer_data = []
    for domain in DOMAINS:
        data = scores.get(domain, {})
        ls = data.get("layer_scores", {})
        for layer_name in LAYERS:
            layer_val = ls.get(layer_name.lower(), ls.get(layer_name, 0))
            layer_data.append({
                "Domain": domain,
                "Layer": layer_name,
                "Score": float(layer_val) if layer_val else 0,
            })

    if layer_data:
        df_layers = pd.DataFrame(layer_data)

        fig = px.bar(
            df_layers,
            y="Domain",
            x="Score",
            color="Layer",
            orientation="h",
            barmode="group",
            color_discrete_map={
                "Rules": GREEN,
                "Standards": BLUE,
                "AI": PURPLE,
                "Recon": ORANGE,
            },
        )
        fig.update_layout(**plotly_dark_template())
        fig.update_layout(
            height=350,
            xaxis_title="Score",
            yaxis_title="",
            xaxis_range=[0, 100],
        )
        st.plotly_chart(fig, use_container_width=True, key="mdhe_layer_breakdown")

    # ── Recent issues summary ─────────────────────────────────────────
    st.subheader("Open Issues by Severity")

    issues = load_issues(status="open")
    if issues:
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for issue in issues:
            sev = issue.get("severity", "Low")
            if sev in severity_counts:
                severity_counts[sev] += 1

        ic1, ic2, ic3, ic4 = st.columns(4)
        for col, (sev, count) in zip(
            [ic1, ic2, ic3, ic4], severity_counts.items()
        ):
            with col:
                col.metric(
                    label=sev,
                    value=count,
                    delta=None,
                )
    else:
        st.success("No open issues. Master data is looking clean.")

    # ── Last validation timestamp ─────────────────────────────────────
    latest_ts = None
    total_records = 0
    for data in scores.values():
        ts = data.get("validated_at", "")
        if ts and (latest_ts is None or ts > latest_ts):
            latest_ts = ts
        total_records += data.get("record_count", 0)

    if latest_ts:
        st.caption(
            f"Last validation: {latest_ts}  |  "
            f"Total records validated: {total_records:,}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Validation Detail
# ═══════════════════════════════════════════════════════════════════════════════

def _render_validation_detail():
    st.subheader("Validation Results")

    # ── Filters ───────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sel_domain = st.selectbox(
            "Domain",
            ["All"] + DOMAINS,
            key="mdhe_val_domain",
        )
    with fc2:
        sel_severity = st.selectbox(
            "Severity",
            ["All"] + SEVERITIES,
            key="mdhe_val_severity",
        )
    with fc3:
        sel_layer = st.selectbox(
            "Layer",
            ["All"] + LAYERS,
            key="mdhe_val_layer",
        )

    # Map "All" to None for the query
    q_domain = sel_domain if sel_domain != "All" else None
    q_severity = sel_severity if sel_severity != "All" else None
    q_layer = sel_layer if sel_layer != "All" else None

    validations = load_validations(
        domain=q_domain, severity=q_severity, layer=q_layer
    )

    if not validations:
        st.info("No validation results match the selected filters.")
        return

    df = pd.DataFrame(validations)

    # ── Summary metrics ───────────────────────────────────────────────
    sev_col_map = {s: 0 for s in SEVERITIES}
    for v in validations:
        sev = v.get("severity", "Low")
        if sev in sev_col_map:
            sev_col_map[sev] += 1

    mc1, mc2, mc3, mc4 = st.columns(4)
    for col, (sev, cnt) in zip(
        [mc1, mc2, mc3, mc4], sev_col_map.items()
    ):
        with col:
            col.metric(sev, cnt)

    st.markdown("")

    # ── Results table ─────────────────────────────────────────────────
    display_cols = [
        "rule_id", "layer", "severity", "domain", "field",
        "record_key", "message",
    ]
    available = [c for c in display_cols if c in df.columns]

    if available:
        # Rename for display
        rename_map = {
            "rule_id": "Rule ID",
            "layer": "Layer",
            "severity": "Severity",
            "domain": "Domain",
            "field": "Field",
            "record_key": "PLU Code",
            "message": "Message",
        }
        df_display = df[available].rename(columns=rename_map)

        st.dataframe(
            df_display,
            use_container_width=True,
            height=min(40 * len(df_display) + 40, 600),
            key="mdhe_validation_table",
        )

        # ── Export button ─────────────────────────────────────────────
        csv_data = df_display.to_csv(index=False)
        st.download_button(
            label="Export as CSV",
            data=csv_data,
            file_name=f"mdhe_validations_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="mdhe_export_csv",
        )
    else:
        st.warning("Validation data has unexpected column structure.")

    st.markdown("")

    # ── Severity distribution pie chart ───────────────────────────────
    st.subheader("Severity Distribution")

    sev_data = [
        {"Severity": sev, "Count": cnt}
        for sev, cnt in sev_col_map.items()
        if cnt > 0
    ]

    if sev_data:
        df_sev = pd.DataFrame(sev_data)
        fig = px.pie(
            df_sev,
            values="Count",
            names="Severity",
            color="Severity",
            color_discrete_map=SEVERITY_COLORS,
            hole=0.45,
        )
        fig.update_layout(**plotly_dark_template())
        fig.update_layout(height=380)
        fig.update_traces(
            textposition="inside",
            textinfo="label+percent",
            textfont_size=13,
        )
        st.plotly_chart(fig, use_container_width=True, key="mdhe_severity_pie")
    else:
        st.info("No issues to visualise.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Scan Verification
# ═══════════════════════════════════════════════════════════════════════════════

def _render_scan_verification():
    st.subheader("Barcode Scan Verification")

    scans = load_scan_results()

    if not scans:
        st.info(
            "No scan data uploaded yet. Upload vision scan or POS scan "
            "reports to see verification results."
        )
        return

    df_scans = pd.DataFrame(scans)

    # ── Summary metrics ───────────────────────────────────────────────
    total = len(df_scans)

    # Warehouse scan match rate
    wh_scanned = df_scans.get("warehouse_scanned")
    if wh_scanned is not None:
        wh_match = wh_scanned.sum() if hasattr(wh_scanned, "sum") else 0
        wh_rate = (wh_match / total * 100) if total > 0 else 0
    else:
        wh_rate = 0

    # POS scan match rate
    pos_scanned = df_scans.get("pos_scanned")
    if pos_scanned is not None:
        pos_match = pos_scanned.sum() if hasattr(pos_scanned, "sum") else 0
        pos_rate = (pos_match / total * 100) if total > 0 else 0
    else:
        pos_rate = 0

    # Average manual key rate
    mkr_col = df_scans.get("manual_key_rate")
    if mkr_col is not None:
        avg_mkr = mkr_col.mean() if hasattr(mkr_col, "mean") else 0
    else:
        avg_mkr = 0

    sm1, sm2, sm3 = st.columns(3)
    with sm1:
        st.metric("Warehouse Scan Match", f"{wh_rate:.1f}%")
    with sm2:
        st.metric("POS Scan Match", f"{pos_rate:.1f}%")
    with sm3:
        delta_color = "inverse" if avg_mkr > 5 else "normal"
        st.metric(
            "Avg Manual Key Rate",
            f"{avg_mkr:.1f}%",
            delta=f"{'Above' if avg_mkr > 5 else 'Below'} 5% threshold",
            delta_color=delta_color,
        )

    st.markdown("")

    # ── Scan status breakdown chart ───────────────────────────────────
    st.subheader("Scan Status Breakdown")

    status_col = df_scans.get("status")
    if status_col is not None:
        status_counts = status_col.value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        status_color_map = {
            "verified": GREEN,
            "failing": RED,
            "never_scanned": TEXT_MUTED,
        }

        fig = px.bar(
            status_counts,
            x="Status",
            y="Count",
            color="Status",
            color_discrete_map=status_color_map,
        )
        fig.update_layout(**plotly_dark_template())
        fig.update_layout(
            height=350,
            showlegend=False,
            xaxis_title="Scan Status",
            yaxis_title="Barcode Count",
        )
        st.plotly_chart(fig, use_container_width=True, key="mdhe_scan_status_bar")

    st.markdown("")

    # ── Never scanned list ────────────────────────────────────────────
    st.subheader("Never Scanned Barcodes")

    if status_col is not None:
        df_never = df_scans[status_col == "never_scanned"]
    else:
        df_never = pd.DataFrame()

    if len(df_never) > 0:
        never_cols = ["barcode", "plu_code", "product_name", "status"]
        available = [c for c in never_cols if c in df_never.columns]
        if available:
            st.dataframe(
                df_never[available].head(100),
                use_container_width=True,
                key="mdhe_never_scanned_table",
            )
            if len(df_never) > 100:
                st.caption(f"Showing 100 of {len(df_never)} never-scanned barcodes.")
        else:
            st.dataframe(df_never.head(100), key="mdhe_never_scanned_raw")
    else:
        st.success("All barcodes have been scanned at least once.")

    st.markdown("")

    # ── High manual key rate ──────────────────────────────────────────
    st.subheader("High Manual Key Rate (>10%)")

    if mkr_col is not None:
        df_high_mkr = df_scans[mkr_col > 10].sort_values(
            "manual_key_rate", ascending=False
        )
    else:
        df_high_mkr = pd.DataFrame()

    if len(df_high_mkr) > 0:
        mkr_cols = [
            "barcode", "plu_code", "product_name",
            "manual_key_rate", "status",
        ]
        available = [c for c in mkr_cols if c in df_high_mkr.columns]
        if available:
            st.dataframe(
                df_high_mkr[available].head(100),
                use_container_width=True,
                key="mdhe_high_mkr_table",
            )
            if len(df_high_mkr) > 100:
                st.caption(
                    f"Showing 100 of {len(df_high_mkr)} high manual-key barcodes."
                )
        else:
            st.dataframe(df_high_mkr.head(100), key="mdhe_high_mkr_raw")
    else:
        st.success("No barcodes exceed the 10% manual key rate threshold.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Trends & History
# ═══════════════════════════════════════════════════════════════════════════════

def _render_trends_history():
    st.subheader("Score Trends")

    history = load_score_history(days=30)

    if not history:
        st.info(
            "No historical score data yet. Scores are recorded each time "
            "a validation run completes."
        )
        return

    df_hist = pd.DataFrame(history)

    # ── Score trend chart ─────────────────────────────────────────────
    # Expect columns: domain, score, validated_at (or created_at / date)
    date_col = None
    for candidate in ["validated_at", "created_at", "date", "timestamp"]:
        if candidate in df_hist.columns:
            date_col = candidate
            break

    if date_col is None:
        st.warning("Score history data does not contain a date column.")
        return

    df_hist["date_parsed"] = pd.to_datetime(df_hist[date_col], errors="coerce")
    df_hist = df_hist.dropna(subset=["date_parsed"])

    if df_hist.empty:
        st.info("No parseable dates in score history.")
        return

    # Compute overall per date
    overall_rows = []
    for dt, grp in df_hist.groupby("date_parsed"):
        avg_score = grp["score"].mean()
        overall_rows.append({
            "domain": "Overall",
            "score": avg_score,
            "date_parsed": dt,
        })
    df_overall = pd.DataFrame(overall_rows)
    df_combined = pd.concat([df_hist, df_overall], ignore_index=True)

    fig = px.line(
        df_combined,
        x="date_parsed",
        y="score",
        color="domain",
        color_discrete_map=DOMAIN_COLORS,
        markers=True,
    )
    fig.update_layout(**plotly_dark_template())
    fig.update_layout(
        height=420,
        xaxis_title="Date",
        yaxis_title="Health Score",
        yaxis_range=[0, 105],
    )
    st.plotly_chart(fig, use_container_width=True, key="mdhe_score_trend_line")

    st.markdown("")

    # ── Issue resolution chart ────────────────────────────────────────
    st.subheader("Issue Resolution")

    all_issues = load_issues()
    if all_issues:
        df_issues = pd.DataFrame(all_issues)

        # Determine date column for issues
        issue_date_col = None
        for candidate in ["created_at", "validated_at", "date", "timestamp"]:
            if candidate in df_issues.columns:
                issue_date_col = candidate
                break

        if issue_date_col:
            df_issues["week"] = pd.to_datetime(
                df_issues[issue_date_col], errors="coerce"
            ).dt.to_period("W").astype(str)

            status_col = df_issues.get("status")
            if status_col is not None:
                weekly = (
                    df_issues.groupby(["week", "status"])
                    .size()
                    .reset_index(name="count")
                )

                status_colors = {"open": RED, "resolved": GREEN, "in_progress": BLUE}

                fig2 = px.bar(
                    weekly,
                    x="week",
                    y="count",
                    color="status",
                    barmode="group",
                    color_discrete_map=status_colors,
                )
                fig2.update_layout(**plotly_dark_template())
                fig2.update_layout(
                    height=350,
                    xaxis_title="Week",
                    yaxis_title="Issue Count",
                )
                st.plotly_chart(
                    fig2, use_container_width=True, key="mdhe_issue_resolution_bar"
                )
    else:
        st.info("No issue data available for resolution tracking.")

    st.markdown("")

    # ── Top recurring failures ────────────────────────────────────────
    st.subheader("Top Recurring Failures")

    all_validations = load_validations()
    if all_validations:
        df_val = pd.DataFrame(all_validations)
        if "rule_id" in df_val.columns:
            top_rules = (
                df_val.groupby("rule_id")
                .agg(
                    count=("rule_id", "size"),
                    severity=("severity", "first"),
                    message=("message", "first"),
                )
                .sort_values("count", ascending=False)
                .head(15)
                .reset_index()
            )

            rename_map = {
                "rule_id": "Rule ID",
                "count": "Occurrences",
                "severity": "Severity",
                "message": "Description",
            }
            st.dataframe(
                top_rules.rename(columns=rename_map),
                use_container_width=True,
                key="mdhe_recurring_failures_table",
            )
        else:
            st.info("No rule_id column found in validation data.")
    else:
        st.info("No validation data for failure analysis.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — AI Insights
# ═══════════════════════════════════════════════════════════════════════════════

def _render_ai_insights():
    st.subheader("AI-Powered Data Quality Insights")

    # Pull AI-layer validations
    ai_validations = load_validations(layer="AI")

    if not ai_validations:
        st.info(
            "No AI-layer insights available yet. AI analysis runs as part of "
            "each validation cycle and detects duplicates, category mismatches, "
            "and description anomalies."
        )
        return

    df_ai = pd.DataFrame(ai_validations)

    # ── Summary ───────────────────────────────────────────────────────
    total_ai = len(df_ai)
    sev_breakdown = df_ai["severity"].value_counts().to_dict() if "severity" in df_ai.columns else {}

    summary_parts = [f"**{total_ai}** AI-detected data quality issues found."]
    for sev in SEVERITIES:
        cnt = sev_breakdown.get(sev, 0)
        if cnt > 0:
            summary_parts.append(f"{cnt} {sev.lower()}")

    st.info(" | ".join(summary_parts))

    st.markdown("")

    # Categorise AI findings by rule_id prefix or message content
    rule_col = df_ai.get("rule_id") if "rule_id" in df_ai.columns else None

    # ── Duplicate candidates ──────────────────────────────────────────
    st.subheader("Duplicate Candidates")

    if rule_col is not None:
        df_dupes = df_ai[rule_col.str.contains("DUP", case=False, na=False)]
    else:
        df_dupes = df_ai[
            df_ai["message"].str.contains("duplicate", case=False, na=False)
        ] if "message" in df_ai.columns else pd.DataFrame()

    if len(df_dupes) > 0:
        dupe_cols = ["record_key", "field", "message", "severity"]
        available = [c for c in dupe_cols if c in df_dupes.columns]
        rename_map = {
            "record_key": "PLU Code",
            "field": "Field",
            "message": "Finding",
            "severity": "Severity",
        }
        df_dupe_display = df_dupes[available].rename(columns=rename_map)
        st.dataframe(
            df_dupe_display.head(50),
            use_container_width=True,
            key="mdhe_ai_duplicates_table",
        )
        if len(df_dupes) > 50:
            st.caption(f"Showing 50 of {len(df_dupes)} duplicate candidates.")
    else:
        st.success("No duplicate candidates detected by AI analysis.")

    st.markdown("")

    # ── Category mismatches ───────────────────────────────────────────
    st.subheader("Category Mismatches")

    if rule_col is not None:
        df_cat = df_ai[rule_col.str.contains("CAT", case=False, na=False)]
    else:
        df_cat = df_ai[
            df_ai["message"].str.contains("category|mismatch", case=False, na=False)
        ] if "message" in df_ai.columns else pd.DataFrame()

    if len(df_cat) > 0:
        cat_cols = ["record_key", "field", "message", "severity"]
        available = [c for c in cat_cols if c in df_cat.columns]
        rename_map = {
            "record_key": "PLU Code",
            "field": "Field",
            "message": "Finding",
            "severity": "Severity",
        }
        df_cat_display = df_cat[available].rename(columns=rename_map)
        st.dataframe(
            df_cat_display.head(50),
            use_container_width=True,
            key="mdhe_ai_category_table",
        )
        if len(df_cat) > 50:
            st.caption(f"Showing 50 of {len(df_cat)} category mismatches.")
    else:
        st.success("No category mismatches detected by AI analysis.")

    st.markdown("")

    # ── Description anomalies ─────────────────────────────────────────
    st.subheader("Description Anomalies")

    if rule_col is not None:
        df_desc = df_ai[rule_col.str.contains("DESC|ANOM", case=False, na=False)]
    else:
        df_desc = df_ai[
            df_ai["message"].str.contains(
                "description|gibberish|anomal", case=False, na=False
            )
        ] if "message" in df_ai.columns else pd.DataFrame()

    if len(df_desc) > 0:
        desc_cols = ["record_key", "field", "message", "severity"]
        available = [c for c in desc_cols if c in df_desc.columns]
        rename_map = {
            "record_key": "PLU Code",
            "field": "Field",
            "message": "Finding",
            "severity": "Severity",
        }
        df_desc_display = df_desc[available].rename(columns=rename_map)
        st.dataframe(
            df_desc_display.head(50),
            use_container_width=True,
            key="mdhe_ai_description_table",
        )
        if len(df_desc) > 50:
            st.caption(f"Showing 50 of {len(df_desc)} description anomalies.")
    else:
        st.success("No description anomalies detected by AI analysis.")

    # ── Uncategorised AI findings ─────────────────────────────────────
    # Show any AI results that did not fall into the above categories
    if rule_col is not None:
        categorised_idx = set()
        for df_cat_set in [df_dupes, df_cat, df_desc]:
            categorised_idx.update(df_cat_set.index.tolist())
        df_other = df_ai.loc[~df_ai.index.isin(categorised_idx)]
    else:
        df_other = pd.DataFrame()

    if len(df_other) > 0:
        st.markdown("")
        st.subheader("Other AI Findings")
        other_cols = ["rule_id", "record_key", "field", "message", "severity"]
        available = [c for c in other_cols if c in df_other.columns]
        rename_map = {
            "rule_id": "Rule ID",
            "record_key": "PLU Code",
            "field": "Field",
            "message": "Finding",
            "severity": "Severity",
        }
        st.dataframe(
            df_other[available].rename(columns=rename_map).head(50),
            use_container_width=True,
            key="mdhe_ai_other_table",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point — called when Streamlit loads this page
# ═══════════════════════════════════════════════════════════════════════════════

render_mdhe_dashboard()
