"""
Way of Working — Overview Tab
Summary of all strategic initiatives across 5 pillars.
"""

import streamlit as st

from shared.styles import HFM_GREEN, HFM_DARK
from shared.monday_connector import fetch_all_pillar_summaries
from shared.pillar_data import get_all_pillars


def render():
    summaries = fetch_all_pillar_summaries()
    pillars = get_all_pillars()

    # Aggregate totals
    total = sum(s.get("total", 0) for s in summaries.values())
    done = sum(s.get("done", 0) for s in summaries.values())
    in_prog = sum(s.get("in_progress", 0) for s in summaries.values())
    stuck = sum(s.get("stuck", 0) for s in summaries.values())
    not_started = sum(s.get("not_started", 0) for s in summaries.values())
    pct = int((done / total) * 100) if total > 0 else 0

    # ── Top-level KPIs ──
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Initiatives", total)
    k2.metric("Done", done)
    k3.metric("In Progress", in_prog)
    k4.metric("Stuck", stuck, delta=None)
    k5.metric("Completion", "{}%".format(pct))

    # ── Overall progress bar ──
    st.markdown(
        "<div style='background:rgba(255,255,255,0.1);border-radius:8px;height:12px;"
        "margin:8px 0 24px;'>"
        "<div style='background:{};height:12px;border-radius:8px;"
        "width:{}%;transition:width 0.5s;'></div></div>".format(HFM_GREEN, pct),
        unsafe_allow_html=True,
    )

    # ── Per-pillar breakdown ──
    st.subheader("By Pillar")

    cols = st.columns(5)
    for i, pillar in enumerate(pillars):
        pid = pillar["id"]
        s = summaries.get(pid, {})
        p_total = s.get("total", 0)
        p_done = s.get("done", 0)
        p_ip = s.get("in_progress", 0)
        p_stuck = s.get("stuck", 0)
        p_pct = int((p_done / p_total) * 100) if p_total > 0 else 0
        color = pillar["color"]

        with cols[i]:
            st.markdown(
                "<div style='border-left:3px solid {color};background:rgba(255,255,255,0.05);"
                "border-radius:0 8px 8px 0;padding:14px;"
                "min-height:180px;'>"
                "<div style='font-size:1.2em;'>{icon}</div>"
                "<div style='font-weight:700;color:{dark};font-size:0.9em;"
                "margin:4px 0;'>{name}</div>"
                "<div style='font-size:0.8em;color:#8899AA;margin-bottom:8px;'>"
                "{done}/{total} done</div>"
                "<div style='display:flex;gap:4px;font-size:0.75em;'>"
                "<span style='color:#2ECC71;'>\u2713 {done}</span>"
                "<span style='color:#2563eb;'>\u25b6 {ip}</span>"
                "<span style='color:#dc2626;'>\u25cf {stuck}</span>"
                "</div>"
                "<div style='background:rgba(255,255,255,0.1);border-radius:4px;height:6px;"
                "margin-top:8px;'>"
                "<div style='background:{color};height:6px;border-radius:4px;"
                "width:{pct}%;'></div></div>"
                "<div style='font-size:0.7em;color:#8899AA;text-align:right;"
                "margin-top:2px;'>{pct}%</div>"
                "</div>".format(
                    color=color, icon=pillar["icon"], dark=HFM_DARK,
                    name=pillar["short_name"], done=p_done, total=p_total,
                    ip=p_ip, stuck=p_stuck, pct=p_pct,
                ),
                unsafe_allow_html=True,
            )

    # ── Status distribution ──
    if total > 0:
        st.markdown("---")
        st.subheader("Status Distribution")
        try:
            import plotly.graph_objects as go
            fig = go.Figure(data=[go.Pie(
                labels=["Done", "In Progress", "Stuck", "Not Started"],
                values=[done, in_prog, stuck, not_started],
                marker=dict(colors=["#2ECC71", "#2563eb", "#dc2626", "#d1d5db"]),
                hole=0.4,
                textinfo="label+value",
            )])
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15),
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Install plotly for the status distribution chart.")
