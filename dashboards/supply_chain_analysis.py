"""
Harris Farm Hub -- Transformation Analysis Dashboard
What our people are telling us -- and what it means.
Reads from both legacy sc_review_responses and new meeting_os_responses tables.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from shared.styles import render_header, render_footer
from shared.bigquery_connector import (
    is_bigquery_available, bq_query, get_response_counts_by_focus,
)
from config.workstreams import get_active_workstreams

_log = logging.getLogger(__name__)
user = st.session_state.get("auth_user")

# Demo toggle in sidebar
_test_mode = st.sidebar.toggle(
    "Demo Mode", value=st.session_state.get("transformation_test_mode", False),
    key="_sca_demo_toggle",
    help="When on, reads from the test table instead of production",
)
st.session_state["transformation_test_mode"] = _test_mode
if _test_mode:
    st.sidebar.caption("Reading from test table")

render_header(
    "Transformation Analysis",
    "What our people are telling us \u2014 and what it means.",
    goals=["G3", "G5"],
    strategy_context="Transformation \u2014 Aggregated Readiness & Vision",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DS = "oval-blend-488902-p2.Surveys"
ADKAR_DIMS = ["Awareness", "Desire", "Knowledge", "Ability", "Reinforcement"]
ADKAR_COLORS = {
    "Awareness": "#C0392B", "Desire": "#C8971F", "Knowledge": "#C8971F",
    "Ability": "#1565C0", "Reinforcement": "#7C3AED",
}
CAP_DIMS = [
    "Visibility", "Disruption Response", "Data Quality", "Technology",
    "Suppliers", "Transport", "Demand Planning", "Sustainability",
]
_PLOT_BG = "#F5F7F5"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_float(val):
    """Parse to float, return None if outside 1-10 or unparseable."""
    if val is None:
        return None
    try:
        v = float(val)
        return v if 1 <= v <= 10 else None
    except (ValueError, TypeError):
        return None


def _clean_tt(raw):
    """Normalise transformation_type label."""
    if not raw:
        return "Other"
    s = str(raw)
    if "supply chain" in s.lower():
        return "Supply Chain"
    if "ai" in s.lower() or "digital" in s.lower():
        return "AI & Digital"
    return s.strip() or "Other"


def _std(vals):
    """Standard deviation (population)."""
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    return (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5


# ---------------------------------------------------------------------------
# Data loading — both BQ tables, normalised
# ---------------------------------------------------------------------------


@st.cache_data(ttl=120, show_spinner="Picking the freshest data for you\u2026")
def _load_all(test=False):
    # type: (bool) -> List[Dict[str, Any]]
    """Load and normalise responses from both BQ tables."""
    rows = []  # type: List[Dict[str, Any]]
    _tbl_suffix = "_test" if test else ""

    # 1) sc_review_responses — handles legacy SCR, ARR, and new ADKAR rows
    try:
        df = bq_query(
            f"SELECT * FROM `{DS}.sc_review_responses{_tbl_suffix}` ORDER BY submitted_at DESC"
        )
        for _, r in df.iterrows():
            d = r.to_dict()
            mt = str(d.get("meeting_type") or "SCR")

            if mt == "TRANSFORMATION_READINESS":
                # New ADKAR flat columns
                adkar = {
                    "Awareness": _safe_float(d.get("adkar_awareness")),
                    "Desire": _safe_float(d.get("adkar_desire")),
                    "Knowledge": _safe_float(d.get("adkar_knowledge")),
                    "Ability": _safe_float(d.get("adkar_ability")),
                    "Reinforcement": _safe_float(
                        d.get("adkar_reinforcement")
                    ),
                }
                text = {
                    "why_transform": d.get("adkar_awareness_text", "") or "",
                    "desire_driver": d.get("adkar_desire_text", "") or "",
                    "twelve_month_picture": d.get(
                        "adkar_knowledge_text", ""
                    ) or "",
                    "lighthouse": d.get("lighthouse_vision", "") or "",
                    "biggest_gap": d.get("adkar_ability_text", "") or "",
                    "confidence_lasting": d.get(
                        "adkar_reinforcement_text", ""
                    ) or "",
                    "need_from_leadership": d.get("unlock_value", "") or "",
                }
                initiative = d.get("initiative_name", "") or ""
                tt = _clean_tt(d.get("transformation_focus", ""))
                source = "adkar"
                caps = {}
            else:
                # Legacy SCR / ARR mapping
                adkar = {
                    "Awareness": _safe_float(d.get("urgency")),
                    "Desire": _safe_float(d.get("desire_score")),
                    "Knowledge": _safe_float(d.get("clarity_score")),
                    "Ability": _safe_float(d.get("readiness_score")),
                    "Reinforcement": _safe_float(d.get("sustain_score")),
                }
                text = {
                    "why_transform": d.get("external_pressures", "") or "",
                    "desire_driver": "",
                    "twelve_month_picture": d.get("ideal_5yr", "") or "",
                    "lighthouse": "",
                    "biggest_gap": d.get("one_big_thing", "") or "",
                    "confidence_lasting": "",
                    "need_from_leadership": "",
                    "protect_processes": d.get(
                        "protect_processes", ""
                    ) or "",
                    "worries": d.get("worries", "") or "",
                    "customer_impact": d.get("customer_impact", "") or "",
                    "additional": d.get("additional", "") or "",
                }
                initiative = d.get("initiative_name", "") or "Supply Chain Review"
                tt = "Supply Chain"
                source = "legacy"
                caps = {
                    "Visibility": _safe_float(d.get("rf_visibility")),
                    "Disruption Response": _safe_float(
                        d.get("rf_disruption")
                    ),
                    "Data Quality": _safe_float(d.get("rf_data")),
                    "Technology": _safe_float(d.get("rf_technology")),
                    "Suppliers": _safe_float(d.get("rf_suppliers")),
                    "Transport": _safe_float(d.get("rf_transport")),
                    "Demand Planning": _safe_float(d.get("rf_demand")),
                    "Sustainability": _safe_float(
                        d.get("rf_sustainability")
                    ),
                }

            rows.append({
                "name": d.get("name", "") or "",
                "department": d.get("department", "") or "",
                "role": d.get("role", "") or "",
                "transformation_type": tt,
                "initiative_name": initiative,
                "session_id": d.get("session_id", "") or "",
                "submitted_at": str(d.get("submitted_at", "")),
                "source": source,
                "channel": d.get("channel", "web") or "web",
                "adkar": adkar,
                "text": text,
                "capabilities": caps,
            })
    except Exception as e:
        _log.warning("SC responses: %s", e)

    # 2) meeting_os_responses (TRANSFORMATION_READINESS) — backward compat
    #    for any responses submitted before Cloud Function update
    try:
        df = bq_query(f"""
            SELECT * FROM `{DS}.meeting_os_responses`
            WHERE meeting_type = 'TRANSFORMATION_READINESS'
            ORDER BY submitted_at DESC
        """)
        for _, r in df.iterrows():
            d = r.to_dict()
            responses = json.loads(d.get("responses_json") or "{}")
            scores = json.loads(d.get("scores_json") or "{}")
            rows.append({
                "name": d.get("name", "") or "",
                "department": d.get("department", "") or "",
                "role": d.get("role", "") or "",
                "transformation_type": _clean_tt(
                    responses.get("transformation_type", "")
                ),
                "initiative_name": responses.get(
                    "initiative_name", ""
                ) or "",
                "session_id": "",
                "submitted_at": str(d.get("submitted_at", "")),
                "source": "new",
                "channel": "web",
                "adkar": {
                    "Awareness": _safe_float(
                        scores.get("awareness_score")
                    ),
                    "Desire": _safe_float(scores.get("desire_score")),
                    "Knowledge": _safe_float(
                        scores.get("knowledge_score")
                    ),
                    "Ability": _safe_float(
                        scores.get("capability_score")
                    ),
                    "Reinforcement": _safe_float(
                        scores.get("reinforcement_score")
                    ),
                },
                "text": {
                    "why_transform": responses.get("why_transform", ""),
                    "desire_driver": responses.get("desire_driver", ""),
                    "twelve_month_picture": responses.get(
                        "twelve_month_picture", ""
                    ),
                    "lighthouse": responses.get("lighthouse", ""),
                    "biggest_gap": responses.get("biggest_gap", ""),
                    "confidence_lasting": responses.get(
                        "confidence_lasting", ""
                    ),
                    "need_from_leadership": responses.get(
                        "need_from_leadership", ""
                    ),
                },
                "capabilities": {},
            })
    except Exception as e:
        _log.warning("New TR responses: %s", e)

    return rows


# ---------------------------------------------------------------------------
# BigQuery availability gate
# ---------------------------------------------------------------------------

if not is_bigquery_available():
    st.warning(
        "BigQuery is not available. Cannot load transformation responses."
    )
    render_footer("Transformation Analysis", "Transformation", user=user)
    st.stop()

all_responses = _load_all(test=_test_mode)

if not all_responses:
    st.info(
        "Nothing here yet \u2014 but something good is growing. "
        "Complete a Transformation Readiness interview to get started."
    )
    _tr_page = st.session_state.get("_pages", {}).get("hfw-transformation-readiness")
    if _tr_page:
        st.page_link(_tr_page, label="Start a Transformation Readiness Interview", use_container_width=True)
    render_footer("Transformation Analysis", "Transformation", user=user)
    st.stop()

# ---------------------------------------------------------------------------
# Filter bar
# ---------------------------------------------------------------------------

st.divider()

all_types = sorted(set(r["transformation_type"] for r in all_responses))
all_depts = sorted(
    set(r["department"] for r in all_responses if r["department"])
)
all_initiatives = sorted(
    set(r.get("initiative_name", "") for r in all_responses
        if r.get("initiative_name"))
)
# Workstream names from config
_ws_names = ["All"] + [ws["name"] for ws in get_active_workstreams()]

all_channels = sorted(
    set(r.get("channel", "web") for r in all_responses if r.get("channel"))
)

type_filter = "All"
dept_filter = "All"
time_filter = "All Time"
init_filter = "All"
ws_filter = "All"
channel_filter = "All"

with st.expander("Filters", expanded=False):
    f1, f2, f3, f4, f5, f6, f7 = st.columns([2, 2, 2, 2, 2, 1, 1])
    with f1:
        ws_filter = st.selectbox("Workstream", _ws_names)
    with f2:
        type_filter = st.selectbox("Transformation Type", ["All"] + all_types)
    with f3:
        init_filter = st.selectbox("Initiative", ["All"] + all_initiatives)
    with f4:
        dept_filter = st.selectbox("Department", ["All"] + all_depts)
    with f5:
        time_filter = st.selectbox(
            "Time Period", ["All Time", "Last 30 Days", "Last 90 Days"]
        )
    with f6:
        channel_filter = st.selectbox("Channel", ["All"] + all_channels)
    with f7:
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# Apply filters
filtered = all_responses
if ws_filter != "All":
    filtered = [r for r in filtered if r["transformation_type"] == ws_filter
                or r.get("initiative_name") == ws_filter]
if type_filter != "All":
    filtered = [r for r in filtered if r["transformation_type"] == type_filter]
if init_filter != "All":
    filtered = [r for r in filtered if r.get("initiative_name") == init_filter]
if dept_filter != "All":
    filtered = [r for r in filtered if r["department"] == dept_filter]
if channel_filter != "All":
    filtered = [r for r in filtered if r.get("channel", "web") == channel_filter]
if time_filter != "All Time":
    cutoff_days = 30 if "30" in time_filter else 90
    cutoff_str = (datetime.utcnow() - timedelta(days=cutoff_days)).isoformat()
    filtered = [r for r in filtered if r["submitted_at"] >= cutoff_str]

n = len(filtered)

if n == 0:
    st.info("No responses match the current filters.")
    render_footer("Transformation Analysis", "Transformation", user=user)
    st.stop()

# ---------------------------------------------------------------------------
# Hero metrics bar
# ---------------------------------------------------------------------------

# Compute ADKAR average across all dimensions and respondents
_all_adkar_vals = []
for r in filtered:
    for d in ADKAR_DIMS:
        v = r["adkar"].get(d)
        if v is not None:
            _all_adkar_vals.append(v)
_adkar_avg = sum(_all_adkar_vals) / len(_all_adkar_vals) if _all_adkar_vals else None

_dept_count = len(set(r["department"] for r in filtered if r["department"]))

latest = max((r["submitted_at"] for r in filtered), default="\u2014")
if latest != "\u2014":
    try:
        dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
        latest = dt.strftime("%d %b %Y")
    except Exception:
        latest = latest[:10]

k1, k2, k3, k4 = st.columns(4)

_metric_card_css = (
    "background:#FFFFFF;border-left:4px solid #2D6A2D;"
    "border-radius:8px;padding:20px 24px;"
    "box-shadow:0 1px 4px rgba(0,0,0,0.06);"
)

with k1:
    st.markdown(
        f"<div style='{_metric_card_css}'>"
        f"<div style='font-size:35px;font-weight:700;color:#1A1A1A;line-height:1;'>{n}</div>"
        f"<div style='font-size:12px;color:#717171;margin-top:6px;'>Responses</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
with k2:
    _adkar_display = f"{_adkar_avg:.1f}/10" if _adkar_avg is not None else "\u2014"
    st.markdown(
        f"<div style='{_metric_card_css}'>"
        f"<div style='font-size:35px;font-weight:700;color:#1A1A1A;line-height:1;'>{_adkar_display}</div>"
        f"<div style='font-size:12px;color:#717171;margin-top:6px;'>ADKAR Average</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f"<div style='{_metric_card_css}'>"
        f"<div style='font-size:35px;font-weight:700;color:#1A1A1A;line-height:1;'>{_dept_count}</div>"
        f"<div style='font-size:12px;color:#717171;margin-top:6px;'>Departments</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        f"<div style='{_metric_card_css}'>"
        f"<div style='font-size:35px;font-weight:700;color:#1A1A1A;line-height:1;'>{latest}</div>"
        f"<div style='font-size:12px;color:#717171;margin-top:6px;'>Latest</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Channel Breakdown
# ---------------------------------------------------------------------------

from collections import Counter
_channel_counts = Counter(r.get("channel", "web") for r in filtered)
if len(_channel_counts) > 1:
    st.markdown("")
    st.markdown("#### Responses by Channel")
    _ch_icons = {"web": "Globe", "whatsapp": "WhatsApp", "sms": "SMS", "simulator": "Simulator"}
    _ch_cols = st.columns(len(_channel_counts))
    for i, (ch, cnt) in enumerate(sorted(_channel_counts.items(), key=lambda x: -x[1])):
        with _ch_cols[i]:
            _ch_label = _ch_icons.get(ch, ch.title())
            st.metric(_ch_label, cnt)
    st.markdown("")

# ---------------------------------------------------------------------------
# Headline insight card
# ---------------------------------------------------------------------------

if _adkar_avg is not None:
    _insight_color = "#2D6A2D" if _adkar_avg >= 7 else "#C8971F" if _adkar_avg >= 5 else "#C0392B"
    _insight_label = (
        "Strong readiness" if _adkar_avg >= 7
        else "Moderate readiness \u2014 some gaps to close" if _adkar_avg >= 5
        else "Low readiness \u2014 significant work needed"
    )
    # Find lowest ADKAR dimension
    _dim_avgs = {}
    for d in ADKAR_DIMS:
        vals = [r["adkar"].get(d) for r in filtered if r["adkar"].get(d) is not None]
        if vals:
            _dim_avgs[d] = sum(vals) / len(vals)
    _lowest = min(_dim_avgs, key=_dim_avgs.get) if _dim_avgs else None
    _lowest_text = f" Biggest gap: **{_lowest}** ({_dim_avgs[_lowest]:.1f}/10)." if _lowest else ""

    st.markdown(
        f"<div style='background:{_insight_color};color:#FFFFFF;border-radius:10px;"
        f"padding:24px 28px;margin:16px 0 20px;width:100%;'>"
        f"<div style='font-weight:700;font-size:20px;margin-bottom:6px;color:#FFFFFF;'>"
        f"{_insight_label}</div>"
        f"<div style='font-size:16px;color:rgba(255,255,255,0.92);'>"
        f"{n} responses across {_dept_count} department{'s' if _dept_count != 1 else ''}. "
        f"Overall ADKAR average: {_adkar_avg:.1f}/10.{_lowest_text}"
        f"</div></div>",
        unsafe_allow_html=True,
    )

st.divider()

# ---------------------------------------------------------------------------
# Initiative Progress Cards
# ---------------------------------------------------------------------------

_initiatives = {}  # type: Dict[str, List[Dict]]
for r in filtered:
    iname = r.get("initiative_name") or "Unspecified"
    _initiatives.setdefault(iname, []).append(r)

if len(_initiatives) > 0:
    st.subheader("Initiative Progress")

    _init_names = sorted(_initiatives.keys())
    _cols = st.columns(min(len(_init_names), 3))

    for idx, iname in enumerate(_init_names):
        irows = _initiatives[iname]
        with _cols[idx % min(len(_init_names), 3)]:
            # Compute per-dimension averages
            _dim_scores = {d: [] for d in ADKAR_DIMS}
            for r in irows:
                for d in ADKAR_DIMS:
                    v = r["adkar"].get(d)
                    if v is not None:
                        _dim_scores[d].append(v)
            _dim_avgs_i = {
                d: (sum(vals) / len(vals) if vals else None)
                for d, vals in _dim_scores.items()
            }
            _valid_avgs = [v for v in _dim_avgs_i.values() if v is not None]
            _overall = (
                sum(_valid_avgs) / len(_valid_avgs) if _valid_avgs else None
            )

            # RAG status
            if _valid_avgs:
                _min_dim = min(_valid_avgs)
                if _min_dim >= 7:
                    _rag, _rag_color, _rag_bg = (
                        "GREEN", "#2D6A2D", "rgba(45,106,45,0.08)"
                    )
                elif _min_dim >= 5:
                    _rag, _rag_color, _rag_bg = (
                        "AMBER", "#C8971F", "rgba(146,113,10,0.08)"
                    )
                else:
                    _rag, _rag_color, _rag_bg = (
                        "RED", "#C0392B", "rgba(220,38,38,0.08)"
                    )
            else:
                _rag, _rag_color, _rag_bg = (
                    "\u2014", "#717171", "rgba(0,0,0,0.02)"
                )

            # Date range
            _dates = [
                r["submitted_at"][:10] for r in irows
                if r["submitted_at"]
            ]
            _date_range = ""
            if _dates:
                _d_min, _d_max = min(_dates), max(_dates)
                _date_range = (
                    _d_min if _d_min == _d_max else f"{_d_min} \u2014 {_d_max}"
                )

            with st.container(border=True):
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"align-items:center;margin-bottom:8px;'>"
                    f"<span style='font-weight:700;font-size:18px;"
                    f"color:#1A1A1A;'>\U0001f4ca {iname}</span>"
                    f"<span style='background:{_rag_bg};color:{_rag_color};"
                    f"font-weight:700;font-size:12px;padding:3px 10px;"
                    f"border-radius:12px;text-transform:uppercase;"
                    f"letter-spacing:0.05em;'>{_rag}</span></div>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"{len(irows)} response{'s' if len(irows) != 1 else ''}"
                    f" \u00b7 {_date_range}"
                )

                # Mini ADKAR bar chart
                if _valid_avgs:
                    _bar_dims = []
                    _bar_vals = []
                    _bar_colors = []
                    for d in ADKAR_DIMS:
                        v = _dim_avgs_i.get(d)
                        if v is not None:
                            _bar_dims.append(d[:3])
                            _bar_vals.append(round(v, 1))
                            _bar_colors.append(ADKAR_COLORS.get(d, "#717171"))

                    fig_bar = go.Figure(go.Bar(
                        x=_bar_vals,
                        y=_bar_dims,
                        orientation="h",
                        marker_color=_bar_colors,
                        text=[f"{v:.1f}" for v in _bar_vals],
                        textposition="outside",
                        textfont=dict(size=11, color="#1A1A1A"),
                    ))
                    fig_bar.update_layout(
                        height=140,
                        margin=dict(l=0, r=30, t=0, b=0),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(
                            range=[0, 10.5], showgrid=False,
                            showticklabels=False, zeroline=False,
                        ),
                        yaxis=dict(
                            tickfont=dict(size=11, color="#1A1A1A"),
                            autorange="reversed",
                        ),
                        bargap=0.3,
                    )
                    st.plotly_chart(
                        fig_bar, use_container_width=True,
                        config={"displayModeBar": False},
                    )
                else:
                    st.caption("No ADKAR scores yet.")

    st.divider()

# ---------------------------------------------------------------------------
# ADKAR Readiness Scores
# ---------------------------------------------------------------------------

st.subheader("How ready are we?")

# Collect scores per dimension
adkar_all = {d: [] for d in ADKAR_DIMS}  # type: Dict[str, List[float]]
for r in filtered:
    for d in ADKAR_DIMS:
        v = r["adkar"].get(d)
        if v is not None:
            adkar_all[d].append(v)

# Average score cards
a_cols = st.columns(5)
for col, dim in zip(a_cols, ADKAR_DIMS):
    vals = adkar_all[dim]
    avg = sum(vals) / len(vals) if vals else None
    _dim_color = ADKAR_COLORS.get(dim, "#717171")
    with col:
        st.markdown(
            f"<div style='border-top:3px solid {_dim_color};"
            f"border-radius:3px 3px 0 0;margin-bottom:-12px;'></div>",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.caption(dim.upper())
            if avg is not None:
                color = (
                    "#2D6A2D" if avg >= 8
                    else "#C8971F" if avg >= 6
                    else "#C0392B"
                )
                interp = (
                    "Strong" if avg >= 8
                    else "Adequate" if avg >= 6
                    else "Gap" if avg >= 4
                    else "Critical"
                )
                st.markdown(
                    f"<span style='font-size:32px;font-weight:700;"
                    f"color:{color};'>{avg:.1f}</span>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"{interp} \u00b7 {len(vals)} "
                    f"score{'s' if len(vals) != 1 else ''}"
                )
            else:
                st.markdown(
                    "<span style='font-size:32px;color:#4A4A4A;'>"
                    "\u2014</span>",
                    unsafe_allow_html=True,
                )
                st.caption("No numeric scores")

# ADKAR Heatmap — respondents x dimensions
heatmap_z = []
heatmap_names = []
for r in filtered:
    scores = [r["adkar"].get(d) for d in ADKAR_DIMS]
    if any(s is not None for s in scores):
        heatmap_z.append([s if s is not None else 0 for s in scores])
        heatmap_names.append(r["name"] or "Anonymous")

if heatmap_z:
    # Per-cell text color: dark on mid-range (gold), white on dark (red/green)
    _hm_text_colors = []
    for row in heatmap_z:
        row_colors = []
        for v in row:
            # Gold zone (4-7) needs dark text; red (<4) and green (>7) use white
            if 3.5 < v < 7.5:
                row_colors.append("#1A1A1A")
            else:
                row_colors.append("#FFFFFF")
        _hm_text_colors.append(row_colors)

    fig_hm = go.Figure(
        data=go.Heatmap(
            z=heatmap_z,
            x=ADKAR_DIMS,
            y=heatmap_names,
            colorscale=[
                [0, "#C0392B"], [0.4, "#C8971F"],
                [0.7, "#7CB342"], [1, "#2D6A2D"],
            ],
            zmin=1,
            zmax=10,
            showscale=True,
            hovertemplate=(
                "<b>%{y}</b><br>%{x}: %{z:.1f}<extra></extra>"
            ),
        )
    )
    # Per-cell annotations for dynamic text color
    _annotations = []
    for i, row in enumerate(heatmap_z):
        for j, v in enumerate(row):
            _annotations.append(dict(
                x=ADKAR_DIMS[j],
                y=heatmap_names[i],
                text=f"{v:.0f}" if v > 0 else "\u2014",
                font=dict(
                    size=14,
                    family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif",
                    color=_hm_text_colors[i][j],
                ),
                showarrow=False,
                xref="x",
                yref="y",
            ))
    fig_hm.update_layout(
        annotations=_annotations,
        title=dict(
            text="ADKAR Scores by Person & Dimension",
            font=dict(size=16, color="#2D6A2D", family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif"),
        ),
        height=max(300, len(heatmap_names) * 44 + 120),
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#1A1A1A", size=13, family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif"),
        xaxis=dict(
            side="top",
            tickfont=dict(size=13, color="#1A1A1A", family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif"),
            tickangle=0,
        ),
        yaxis=dict(
            tickfont=dict(size=13, color="#1A1A1A", family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif"),
            autorange="reversed",
        ),
    )
    st.plotly_chart(fig_hm, use_container_width=True)

# Gaps & Conflicts — only show if real disagreement exists (std dev >= 2)
variance_rows = []
for d in ADKAR_DIMS:
    vals = adkar_all[d]
    if len(vals) >= 2:
        sd = _std(vals)
        if sd >= 2.0:
            variance_rows.append({
                "Dimension": d,
                "Avg": round(sum(vals) / len(vals), 1),
                "Std Dev": round(sd, 1),
                "Min": min(vals),
                "Max": max(vals),
                "Range": max(vals) - min(vals),
                "n": len(vals),
            })

if variance_rows:
    st.markdown(
        "<div style='background:rgba(200,151,31,0.08);border-left:4px solid #C8971F;"
        "border-radius:0 8px 8px 0;padding:12px 16px;margin:8px 0;'>"
        "<strong style='color:#C8971F;'>Gaps & Conflicts</strong>"
        " <span style='color:#C8971F;font-size:13px;'>"
        "\u2014 these dimensions show significant disagreement across respondents"
        "</span></div>",
        unsafe_allow_html=True,
    )
    st.dataframe(
        pd.DataFrame(variance_rows), use_container_width=True, hide_index=True
    )

st.divider()

# ---------------------------------------------------------------------------
# Capability Gap Chart (legacy data with RF scores)
# ---------------------------------------------------------------------------

cap_scores = {d: [] for d in CAP_DIMS}  # type: Dict[str, List[float]]
for r in filtered:
    caps = r.get("capabilities") or {}
    for d in CAP_DIMS:
        v = caps.get(d)
        if v is not None:
            cap_scores[d].append(v)

has_caps = any(len(v) > 0 for v in cap_scores.values())

if has_caps:
    cap_avgs = []
    cap_labels = []
    cap_colors = []
    for d in CAP_DIMS:
        vals = cap_scores[d]
        if vals:
            avg = sum(vals) / len(vals)
            cap_avgs.append(round(avg, 1))
            cap_labels.append(d)
            cap_colors.append(
                "#2D6A2D" if avg >= 7
                else "#C8971F" if avg >= 5
                else "#C0392B"
            )

    if cap_avgs:
        fig_cap = go.Figure(
            data=go.Bar(
                x=cap_avgs,
                y=cap_labels,
                orientation="h",
                marker_color=cap_colors,
                text=[f"{v:.1f}" for v in cap_avgs],
                textposition="outside",
                textfont=dict(color="#1A1A1A", size=13, family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif"),
            )
        )
        fig_cap.update_layout(
            title=dict(
                text="Capability Gap Analysis",
                font=dict(size=16, color="#2D6A2D", family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif"),
            ),
            height=max(300, len(cap_labels) * 44 + 80),
            margin=dict(l=10, r=50, t=50, b=10),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(color="#1A1A1A", size=13, family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif"),
            xaxis=dict(
                range=[0, 10.5],
                gridcolor="rgba(0,0,0,0.10)",
                gridwidth=1,
                tickfont=dict(size=12, color="#4A4A4A"),
                dtick=2,
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(size=13, color="#1A1A1A", family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif"),
            ),
        )
        st.plotly_chart(fig_cap, use_container_width=True)

    st.divider()

# ---------------------------------------------------------------------------
# Department & Role Breakdowns (scale feature)
# ---------------------------------------------------------------------------

# Collect ADKAR scores by department
_dept_adkar = {}  # type: Dict[str, Dict[str, List[float]]]
_role_adkar = {}  # type: Dict[str, Dict[str, List[float]]]
for r in filtered:
    dept = r.get("department") or "Unknown"
    role = r.get("role") or "Unknown"
    for d in ADKAR_DIMS:
        v = r["adkar"].get(d)
        if v is not None:
            _dept_adkar.setdefault(dept, {}).setdefault(d, []).append(v)
            _role_adkar.setdefault(role, {}).setdefault(d, []).append(v)

if len(_dept_adkar) > 1:
    st.subheader("ADKAR by Department")

    # Department grouped bar chart
    _dept_names = sorted(_dept_adkar.keys())
    fig_dept = go.Figure()
    for d_idx, dim in enumerate(ADKAR_DIMS):
        avgs = []
        for dept in _dept_names:
            vals = _dept_adkar.get(dept, {}).get(dim, [])
            avgs.append(round(sum(vals) / len(vals), 1) if vals else 0)
        fig_dept.add_trace(go.Bar(
            name=dim,
            x=_dept_names,
            y=avgs,
            marker_color=ADKAR_COLORS.get(dim, "#717171"),
        ))
    fig_dept.update_layout(
        barmode="group",
        height=380,
        yaxis_range=[0, 10.5],
        yaxis_title="Score",
        margin=dict(t=20, b=40, l=40, r=20),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#1A1A1A"),
        legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig_dept, use_container_width=True)

    # Response count by department
    _dept_counts = {
        dept: sum(len(v) for v in dims.values()) // len(ADKAR_DIMS)
        for dept, dims in _dept_adkar.items()
    }
    fig_dept_ct = go.Figure(go.Bar(
        x=list(_dept_counts.values()),
        y=list(_dept_counts.keys()),
        orientation="h",
        marker_color="#2D6A2D",
        text=list(_dept_counts.values()),
        textposition="outside",
        textfont=dict(color="#1A1A1A", size=12),
    ))
    fig_dept_ct.update_layout(
        title="Responses by Department",
        height=max(200, len(_dept_counts) * 36 + 60),
        margin=dict(l=10, r=40, t=40, b=10),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#1A1A1A"),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig_dept_ct, use_container_width=True)

if len(_role_adkar) > 1:
    with st.expander("ADKAR by Role Level"):
        _role_names = sorted(_role_adkar.keys())
        fig_role = go.Figure()
        for dim in ADKAR_DIMS:
            avgs = []
            for role in _role_names:
                vals = _role_adkar.get(role, {}).get(dim, [])
                avgs.append(round(sum(vals) / len(vals), 1) if vals else 0)
            fig_role.add_trace(go.Bar(
                name=dim,
                x=_role_names,
                y=avgs,
                marker_color=ADKAR_COLORS.get(dim, "#717171"),
            ))
        fig_role.update_layout(
            barmode="group",
            height=340,
            yaxis_range=[0, 10.5],
            yaxis_title="Score",
            margin=dict(t=20, b=40, l=40, r=20),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(color="#1A1A1A"),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_role, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Top Themes by ADKAR Dimension
# ---------------------------------------------------------------------------

st.subheader("What our people are saying")
st.caption("Top voices per ADKAR dimension \u2014 real words from real people")

_ADKAR_TEXT_MAP = [
    ("Awareness", "#C0392B", [("Why Transform?", "why_transform")]),
    ("Desire", "#C8971F", [("What Drives It?", "desire_driver")]),
    ("Knowledge", "#C8971F", [
        ("12-Month Picture", "twelve_month_picture"),
        ("Lighthouse Vision", "lighthouse"),
    ]),
    ("Ability", "#1565C0", [("Biggest Gap", "biggest_gap")]),
    ("Reinforcement", "#7C3AED", [
        ("Making It Last", "confidence_lasting"),
        ("From Leadership", "need_from_leadership"),
    ]),
]

for dim_name, dim_color, fields in _ADKAR_TEXT_MAP:
    # Collect all entries across sub-fields for this dimension
    all_entries = []
    for field_label, field_key in fields:
        for r in filtered:
            val = r["text"].get(field_key, "").strip()
            if val:
                all_entries.append((r["name"] or "Anonymous", field_label, val))

    if not all_entries:
        continue

    with st.container(border=True):
        st.markdown(
            f"<span style='color:{dim_color};font-weight:700;'>"
            f"{dim_name.upper()}</span>"
            f" <span style='color:#4A4A4A;font-size:12px;'>"
            f"\u00b7 {len(all_entries)} response{'s' if len(all_entries) != 1 else ''}</span>",
            unsafe_allow_html=True,
        )
        for name, sub_label, quote in all_entries[:3]:
            st.markdown(
                f"**{name}** _{sub_label}_: {quote}"
            )
        if len(all_entries) > 3:
            with st.expander(f"Show all {len(all_entries)} responses"):
                for name, sub_label, quote in all_entries[3:]:
                    st.markdown(f"**{name}** _{sub_label}_: {quote}")

# Legacy-specific text (Worries, Protect, Impact)
_LEGACY_TEXT = [
    ("What's Working / Protect", "protect_processes"),
    ("Worries", "worries"),
    ("Customer Impact", "customer_impact"),
]
_legacy_entries_exist = False
for label, key in _LEGACY_TEXT:
    entries = [
        (r["name"] or "Anonymous", r["text"].get(key, ""))
        for r in filtered
        if r["text"].get(key, "").strip()
    ]
    if entries:
        if not _legacy_entries_exist:
            _legacy_entries_exist = True
        with st.expander(f"{label} ({len(entries)} responses)"):
            for name, quote in entries:
                st.markdown(f"**{name}:** {quote}")

st.divider()

# ---------------------------------------------------------------------------
# Individual Response Cards (scale-adaptive)
# ---------------------------------------------------------------------------

# <50: show all individual cards
# 50-200: summary only, hide individual cards by default
# 200+: aggregate only, no individual cards

if n >= 200:
    st.info(
        f"With {n} responses, individual cards are hidden to keep the page "
        f"fast. Use filters to narrow down to a specific department or "
        f"workstream to see individual responses."
    )
elif n >= 50:
    st.subheader("Every voice, in full")
    st.caption(
        f"{n} responses \u2014 showing summary view. "
        f"Filter to fewer than 50 to see individual cards."
    )
else:
    st.subheader("Every voice, in full")

_show_individual = n < 50
if n >= 50 and n < 200:
    _show_individual = st.checkbox(
        f"Show all {n} individual responses", value=False
    )

if _show_individual:
    pass  # fall through to the loop below

for r in (filtered if _show_individual else []):
    ts = r["submitted_at"][:10] if len(r["submitted_at"]) >= 10 else ""
    label_parts = [r["name"] or "Anonymous"]
    if r["transformation_type"]:
        label_parts.append(r["transformation_type"])
    if r["department"]:
        label_parts.append(r["department"])
    if ts:
        label_parts.append(ts)

    with st.expander(" \u00b7 ".join(label_parts)):
        # ADKAR scores
        score_parts = []
        for d in ADKAR_DIMS:
            v = r["adkar"].get(d)
            if v is not None:
                score_parts.append(f"{d}: **{v:.0f}**/10")
        if score_parts:
            st.markdown("**ADKAR:** " + " \u00b7 ".join(score_parts))

        # Capability scores (legacy)
        cap_parts = []
        for d in CAP_DIMS:
            v = (r.get("capabilities") or {}).get(d)
            if v is not None:
                cap_parts.append(f"{d}: {v:.0f}")
        if cap_parts:
            st.markdown(
                "**Capabilities:** " + " \u00b7 ".join(cap_parts)
            )

        # Text responses
        _ALL_TEXT_FIELDS = [
            ("Awareness \u2014 Why Transform?", "why_transform"),
            ("Desire \u2014 What Drives It?", "desire_driver"),
            ("Knowledge \u2014 12-Month Picture", "twelve_month_picture"),
            ("Knowledge \u2014 Lighthouse Vision", "lighthouse"),
            ("Ability \u2014 Biggest Gap", "biggest_gap"),
            ("Reinforcement \u2014 Making It Last", "confidence_lasting"),
            ("Reinforcement \u2014 From Leadership", "need_from_leadership"),
            ("What's Working / Protect", "protect_processes"),
            ("Worries", "worries"),
            ("Customer Impact", "customer_impact"),
        ]
        for label, key in _ALL_TEXT_FIELDS:
            val = r["text"].get(key, "")
            if val and val.strip():
                short_label = label.split(" \u2014 ")[1] if " \u2014 " in label else label
                st.markdown(f"**{short_label}:** {val}")

st.divider()

# ---------------------------------------------------------------------------
# Analyse with Claude
# ---------------------------------------------------------------------------

st.subheader("Let Claude connect the dots")

if "tr_analysis" not in st.session_state:
    st.session_state["tr_analysis"] = None


def _call_claude(responses):
    # type: (List[Dict[str, Any]]) -> Optional[Dict[str, Any]]
    """Send normalised responses to Claude for synthesis."""
    try:
        import anthropic
    except ImportError:
        st.error("anthropic package not installed")
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not set")
        return None

    # Build compact summary for Claude
    summary = []
    for r in responses:
        entry = {
            "name": r["name"],
            "department": r["department"],
            "role": r["role"],
            "transformation_type": r["transformation_type"],
            "adkar_scores": {
                k: v for k, v in r["adkar"].items() if v is not None
            },
            "text_responses": {
                k: v for k, v in r["text"].items() if v
            },
        }
        caps = {
            k: v
            for k, v in (r.get("capabilities") or {}).items()
            if v is not None
        }
        if caps:
            entry["capability_scores"] = caps
        summary.append(entry)

    prompt = (
        f"You are an organisational transformation analyst for Harris Farm "
        f"Markets. Analyse these {len(summary)} transformation readiness "
        f"interview responses.\n\n"
        f"Return ONLY valid JSON (no markdown, no code fences) with this "
        f"exact structure:\n"
        "{\n"
        '  "executive_summary": "3-4 sentence executive summary of '
        'transformation readiness findings",\n'
        '  "key_themes": [\n'
        '    {"theme": "theme title", "detail": "supporting evidence and '
        'quotes", "adkar_dimension": "which ADKAR dimension"}\n'
        "  ],\n"
        '  "biggest_gaps": [\n'
        '    {"gap": "description", "severity": "Critical|Significant|'
        'Moderate", "evidence": "what the data shows"}\n'
        "  ],\n"
        '  "recommended_actions": [\n'
        '    {"action": "specific action", "priority": "High|Medium|Low", '
        '"rationale": "why", "owner": "suggested owner/team"}\n'
        "  ],\n"
        '  "vision_statement": "One-line vision statement synthesised from '
        'all responses",\n'
        '  "execution_prompt": "A provocative one-line question to drive '
        'the next leadership conversation"\n'
        "}\n\n"
        "ADKAR scoring: 8-10 = Strong, 6-7 = Adequate, 4-5 = Gap, "
        "1-3 = Critical.\n"
        "Legacy ADKAR mapping: Awareness=urgency, Desire=desire, "
        "Knowledge=clarity, Ability=readiness, Reinforcement=sustain.\n\n"
        f"Interview Responses:\n{json.dumps(summary, indent=2)}"
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            # Remove opening fence (```json or ```)
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].strip()
        # Find the JSON object boundaries in case of preamble/postamble
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]
        return json.loads(text)
    except json.JSONDecodeError as e:
        _log.error("Claude JSON parse error: %s\nRaw text: %s", e, text[:500])
        st.error(f"Claude returned invalid JSON: {e}")
        return None
    except Exception as e:
        st.error(f"Claude API error: {e}")
        return None


if st.button(
    "Analyse with Claude",
    type="primary",
    use_container_width=True,
    disabled=n == 0,
):
    with st.spinner("Synthesising transformation data with Claude\u2026"):
        result = _call_claude(filtered)
        if result:
            st.session_state["tr_analysis"] = result
            st.success("Analysis complete")

# Display analysis results
analysis = st.session_state.get("tr_analysis")
if analysis:
    st.markdown("---")

    # Executive summary
    st.markdown("#### Executive Summary")
    st.info(analysis.get("executive_summary", ""))

    # Vision statement
    vision = analysis.get("vision_statement", "")
    if vision:
        st.markdown(f"> *\"{vision}\"*")

    # Key themes
    themes = analysis.get("key_themes", [])
    if themes:
        st.markdown("#### Key Themes")
        for t in themes:
            with st.container(border=True):
                dim = t.get("adkar_dimension", "")
                color = ADKAR_COLORS.get(dim, "#4A4A4A")
                st.markdown(
                    f"**{t.get('theme', '')}** "
                    f"<span style='color:{color};font-size:12px;'>"
                    f"\u00b7 {dim}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(t.get("detail", ""))

    # Biggest gaps
    gaps = analysis.get("biggest_gaps", [])
    if gaps:
        st.markdown("#### Biggest Gaps")
        for g in gaps:
            severity = g.get("severity", "")
            color = (
                "#C0392B" if severity == "Critical"
                else "#C8971F" if severity == "Significant"
                else "#1565C0"
            )
            st.markdown(
                f"- **{g.get('gap', '')}** "
                f"<span style='color:{color};'>({severity})</span> "
                f"\u2014 {g.get('evidence', '')}",
                unsafe_allow_html=True,
            )

    # Recommended actions
    actions = analysis.get("recommended_actions", [])
    if actions:
        st.markdown("#### Recommended Actions")
        for a in actions:
            priority = a.get("priority", "")
            icon = (
                "\U0001f534" if priority == "High"
                else "\U0001f7e1" if priority == "Medium"
                else "\U0001f7e2"
            )
            st.markdown(
                f"{icon} **{a.get('action', '')}** \u2014 "
                f"{a.get('rationale', '')} "
                f"_(Owner: {a.get('owner', 'TBD')})_"
            )

    # Execution prompt
    ep = analysis.get("execution_prompt", "")
    if ep:
        st.divider()
        st.markdown("#### Next Conversation Starter")
        st.warning(ep)

st.divider()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

render_footer("Transformation Analysis", "Transformation", user=user)
