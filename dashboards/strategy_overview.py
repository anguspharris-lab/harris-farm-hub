"""
Harris Farm Hub — Strategy Overview
Five pillars, initiative tracker, and the 5 goals — all in one view.
"""

import streamlit as st

from nav import HUBS, _PORT_TO_SLUG
from shared.styles import HFM_GREEN, HFM_DARK, render_footer
from shared.goals_config import (
    HUB_GOALS,
    fetch_all_goal_metrics,
)

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1 — Five Pillars Strategy
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    f"<div style='background:linear-gradient(135deg, #0F1D35 0%, #132240 50%, #1A2D50 100%);"
    f"border:1px solid rgba(46,204,113,0.2);border-top:3px solid #2ECC71;"
    f"color:white;padding:28px 32px;border-radius:14px;margin-bottom:20px;'>"
    f"<div style='font-size:1.8em;font-weight:700;margin-bottom:4px;"
    f"font-family:Georgia,serif;'>"
    f"Our Strategy: Fewer, Bigger, Better</div>"
    f"<div style='font-size:1.05em;color:#B0BEC5;max-width:700px;'>"
    f"Vision 2030 &mdash; Australia's most loved fresh food retailer, inside and out. "
    f"Everything The Hub does maps back to these five pillars.</div>"
    f"</div>",
    unsafe_allow_html=True,
)

PILLAR_CONTEXT = {
    "Pillar 1": {
        "tagline": "We'll do things right, from end-to-end",
        "status_items": [
            "100% renewable energy \u2014 ACHIEVED",
            "B Corp certification \u2014 board approval Feb/Mar",
        ],
    },
    "Pillar 2": {
        "tagline": "We'll take the 'you get me' feeling to a whole new level",
        "status_items": [
            "Loyalty program pilot \u2014 Apr 2026",
            "Voice of Customer \u2014 in progress",
        ],
    },
    "Pillar 3": {
        "tagline": "We will be famous for attracting, developing, and retaining exceptional people",
        "status_items": [
            "Growing Legends Academy \u2014 6 levels, LIVE",
            "Prosci ADKAR \u2014 change management active",
        ],
    },
    "Pillar 4": {
        "tagline": "We will tidy up the supply chain, from pay to purchase",
        "status_items": [
            "OOS reduction 20% \u2014 target Jun 2026",
            "Grant Enders engaged \u2014 supply chain transformation",
        ],
    },
    "Pillar 5": {
        "tagline": "We'll build a brilliant back-end with tools that talk, systems that serve, data we trust",
        "status_items": [
            "AI Centre of Excellence \u2014 LIVE, 19 dashboards",
            "Citizen Developer Program \u2014 in progress",
        ],
    },
}


def _port_to_page(port):
    """Convert a legacy port number to a page object for st.page_link()."""
    slug = _PORT_TO_SLUG.get(port)
    if slug and slug in _pages:
        return _pages[slug]
    return None


# Only show the 5 strategic pillars (skip Way of Working which has no pillar number)
_pillar_hubs = [h for h in HUBS if h.get("pillar")]
p_cols = st.columns(len(_pillar_hubs))
for i, hub in enumerate(_pillar_hubs):
    with p_cols[i]:
        color = hub["color"]
        pillar = hub.get("pillar", "")
        ctx = PILLAR_CONTEXT.get(pillar, {})
        tagline = ctx.get("tagline", "")
        status_items = ctx.get("status_items", [])

        status_html = ""
        for item in status_items:
            status_html += (
                f"<div style='font-size:0.78em;color:#8899AA;margin:2px 0;'>"
                f"&bull; {item}</div>"
            )

        st.markdown(
            f"<div style='border-left:3px solid {color};"
            f"background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);"
            f"border-left:3px solid {color};"
            f"border-radius:0 8px 8px 0;padding:14px;min-height:160px;'>"
            f"<div style='font-size:0.7em;color:{color};font-weight:700;"
            f"text-transform:uppercase;letter-spacing:0.5px;'>{pillar}</div>"
            f"<div style='font-size:0.9em;font-weight:700;color:white;"
            f"font-family:Georgia,serif;margin:3px 0;'>{hub['icon']} {hub['name']}</div>"
            f"<div style='font-size:0.75em;color:#8899AA;font-style:italic;"
            f"margin-bottom:8px;'>{tagline}</div>"
            f"{status_html}"
            f"</div>",
            unsafe_allow_html=True,
        )

        first_port = hub["dashboards"][0][1]
        page = _port_to_page(first_port)
        if page:
            st.page_link(
                page, label=f"View {hub['name']} \u2192", use_container_width=True
            )

st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2 — Strategic Initiative Pulse (Monday.com, if configured)
# ═══════════════════════════════════════════════════════════════════════════

try:
    from shared.monday_connector import is_configured as _monday_configured
    from shared.monday_connector import fetch_all_pillar_summaries
    from shared.pillar_data import get_all_pillars as _get_pillars

    if _monday_configured():
        _pillar_summaries = fetch_all_pillar_summaries()
        _all_pillars = _get_pillars()

        # Aggregate totals across all pillars
        _ip_total_all = sum(s.get("total", 0) for s in _pillar_summaries.values())
        _ip_done_all = sum(s.get("done", 0) for s in _pillar_summaries.values())
        _ip_prog_all = sum(s.get("in_progress", 0) for s in _pillar_summaries.values())
        _ip_stuck_all = sum(s.get("stuck", 0) for s in _pillar_summaries.values())
        _ip_pct_all = int((_ip_done_all / _ip_total_all) * 100) if _ip_total_all > 0 else 0

        # Section header with overall progress
        st.markdown(
            f"<div style='background:linear-gradient(135deg, #1e293b 0%, #334155 100%);"
            f"color:white;padding:24px 28px;border-radius:14px;margin-bottom:16px;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"flex-wrap:wrap;gap:12px;'>"
            f"<div>"
            f"<div style='font-size:1.4em;font-weight:700;margin-bottom:4px;'>"
            f"Strategy Tracker</div>"
            f"<div style='font-size:0.9em;opacity:0.8;'>"
            f"{_ip_total_all} strategic initiatives across 5 pillars "
            f"&mdash; tracked live from Monday.com</div>"
            f"</div>"
            f"<div style='display:flex;gap:20px;'>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:1.6em;font-weight:700;'>{_ip_pct_all}%</div>"
            f"<div style='font-size:0.75em;opacity:0.7;'>Complete</div></div>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:1.6em;font-weight:700;color:#4ade80;'>"
            f"{_ip_done_all}</div>"
            f"<div style='font-size:0.75em;opacity:0.7;'>Done</div></div>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:1.6em;font-weight:700;color:#60a5fa;'>"
            f"{_ip_prog_all}</div>"
            f"<div style='font-size:0.75em;opacity:0.7;'>In Progress</div></div>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:1.6em;font-weight:700;color:#f87171;'>"
            f"{_ip_stuck_all}</div>"
            f"<div style='font-size:0.75em;opacity:0.7;'>Stuck</div></div>"
            f"</div></div>"
            f"<div style='background:rgba(255,255,255,0.08);border-radius:6px;"
            f"height:8px;margin-top:16px;'>"
            f"<div style='background:#4ade80;height:8px;border-radius:6px;"
            f"width:{_ip_pct_all}%;transition:width 0.5s;'></div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Per-pillar breakdown cards
        _ip_cols = st.columns(5)
        for _ip_i, _ip_p in enumerate(_all_pillars):
            _ip_pid = _ip_p["id"]
            _ip_s = _pillar_summaries.get(_ip_pid, {})
            _ip_total = _ip_s.get("total", 0)
            _ip_done = _ip_s.get("done", 0)
            _ip_prog = _ip_s.get("in_progress", 0)
            _ip_stuck = _ip_s.get("stuck", 0)
            _ip_pct = int((_ip_done / _ip_total) * 100) if _ip_total > 0 else 0
            _ip_color = _ip_p["color"]
            with _ip_cols[_ip_i]:
                st.markdown(
                    "<div style='border-left:3px solid {color};background:rgba(255,255,255,0.05);"
                    "border:1px solid rgba(255,255,255,0.08);border-left:3px solid {color};"
                    "border-radius:0 8px 8px 0;padding:14px;"
                    "min-height:140px;'>"
                    "<div style='font-size:0.75em;color:{color};"
                    "font-weight:700;text-transform:uppercase;"
                    "letter-spacing:0.5px;'>{icon} {name}</div>"
                    "<div style='font-size:1.4em;font-weight:700;color:white;"
                    "margin:6px 0 4px;'>{done}<span style='font-size:0.6em;"
                    "color:#8899AA;font-weight:400;'>/{total}</span></div>"
                    "<div style='display:flex;gap:6px;font-size:0.72em;"
                    "margin-bottom:8px;'>"
                    "<span style='color:#2ECC71;'>&check; {done}</span>"
                    "<span style='color:#2563eb;'>&bull; {prog}</span>"
                    "<span style='color:#dc2626;'>&bull; {stuck}</span>"
                    "</div>"
                    "<div style='background:rgba(255,255,255,0.1);border-radius:4px;"
                    "height:6px;'>"
                    "<div style='background:{color};height:6px;"
                    "border-radius:4px;width:{pct}%;'></div></div>"
                    "<div style='font-size:0.68em;color:#8899AA;"
                    "text-align:right;margin-top:2px;'>{pct}%</div>"
                    "</div>".format(
                        color=_ip_color, icon=_ip_p["icon"],
                        name=_ip_p["short_name"], done=_ip_done,
                        total=_ip_total, prog=_ip_prog,
                        stuck=_ip_stuck, pct=_ip_pct, dark=HFM_DARK,
                    ),
                    unsafe_allow_html=True,
                )

        # CTA to full strategy tracker
        _wow_page = _pages.get("way-of-working")
        if _wow_page:
            _wow_c = st.columns([1, 2, 1])
            with _wow_c[1]:
                st.page_link(
                    _wow_page,
                    label="\U0001f4ca See How We're Tracking \u2192",
                    use_container_width=True,
                )

        st.markdown("")
except ImportError:
    pass

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3 — The 5 Goals (Live Progress) — single DB call
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    "<h2 style='color:white;margin-bottom:4px;font-family:Georgia,serif;'>The 5 Goals</h2>"
    "<p style='color:#8899AA;margin-top:0;'>Why The Hub exists &mdash; "
    "live progress across every goal.</p>",
    unsafe_allow_html=True,
)

all_metrics = fetch_all_goal_metrics()

goal_cols = st.columns(5)
for i, (gid, goal) in enumerate(HUB_GOALS.items()):
    with goal_cols[i]:
        metrics = all_metrics.get(gid, {"metrics": {}, "progress": 0})
        progress = metrics.get("progress", 0)
        metric_items = metrics.get("metrics", {})

        # Word-boundary truncation for description
        desc = goal["description"]
        if len(desc) > 90:
            desc = desc[:90].rsplit(" ", 1)[0] + "..."

        # Metric lines
        metric_html = ""
        for label, val in metric_items.items():
            metric_html += (
                f"<div style='display:flex;justify-content:space-between;"
                f"font-size:0.8em;color:#B0BEC5;margin:3px 0;'>"
                f"<span>{label}</span>"
                f"<span style='font-weight:600;color:white;'>{val:,}</span></div>"
            )

        bar_color = goal["color"]

        st.markdown(
            f"<div style='border-left:4px solid {goal['color']};"
            f"background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);"
            f"border-left:4px solid {goal['color']};"
            f"border-radius:0 10px 10px 0;padding:16px;min-height:240px;'>"
            f"<div style='font-size:1.4em;'>{goal['icon']}</div>"
            f"<div style='font-size:0.95em;font-weight:700;color:white;"
            f"font-family:Georgia,serif;margin:4px 0 2px;'>{goal['title']}</div>"
            f"<div style='font-size:0.78em;color:#8899AA;margin-bottom:8px;'>"
            f"{desc}</div>"
            f"<div style='font-size:0.75em;color:{goal['color']};font-style:italic;"
            f"margin-bottom:10px;'>{goal['key_question']}</div>"
            f"<div style='margin:8px 0;'>{metric_html}</div>"
            f"<div style='background:rgba(255,255,255,0.1);border-radius:6px;height:6px;margin-top:10px;'>"
            f"<div style='background:{bar_color};height:6px;border-radius:6px;"
            f"width:{progress}%;'></div></div>"
            f"<div style='font-size:0.7em;color:#8899AA;text-align:right;margin-top:2px;'>"
            f"{progress}%</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown("")

render_footer("Strategy Overview", user=user)
