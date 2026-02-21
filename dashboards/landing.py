"""
Harris Farm Hub — Mission Control
Front page for the AI Centre of Excellence.
Strategy pillars, 5 goals, quick launch, activity, WATCHDOG trust.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st

from nav import HUBS, _PORT_TO_SLUG
from shared.styles import render_footer, HFM_GREEN, HFM_DARK
from shared.goals_config import (
    HUB_GOALS,
    fetch_all_goal_metrics,
    goal_badge_html,
    fetch_recent_activity,
    fetch_watchdog_scores,
)

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1 — Mission Statement + Personalised Greeting
# ═══════════════════════════════════════════════════════════════════════════

# Time-based greeting
_hour = datetime.now().hour
if _hour < 12:
    _greeting = "Good morning"
elif _hour < 17:
    _greeting = "Good afternoon"
else:
    _greeting = "Good evening"

_user_name = ""
if user and user.get("name"):
    _user_name = f", {user['name'].split()[0]}"

st.markdown(
    f"<div style='background:linear-gradient(135deg, #16a34a 0%, #15803d 50%, #166534 100%);"
    f"color:white;padding:32px 36px;border-radius:14px;margin-bottom:20px;'>"
    f"<div style='font-size:1em;opacity:0.85;margin-bottom:4px;'>"
    f"{_greeting}{_user_name}</div>"
    f"<div style='font-size:2em;font-weight:700;margin-bottom:4px;'>"
    f"Harris Farm Hub</div>"
    f"<div style='font-size:1.2em;font-weight:500;opacity:0.95;margin-bottom:8px;'>"
    f"AI Centre of Excellence &mdash; For The Greater Goodness</div>"
    f"<div style='font-size:0.95em;opacity:0.9;max-width:700px;'>"
    f"Accelerating Harris Farm's strategy through AI that works alongside our "
    f"people &mdash; safely, transparently, and always improving.</div>"
    f"</div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2 — Five Pillars Strategy (moved up from bottom)
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    f"<h2 style='color:{HFM_DARK};margin-bottom:4px;'>Our Strategy: Fewer, Bigger, Better</h2>"
    "<p style='color:#6b7280;margin-top:0;'>"
    "Vision 2030 &mdash; Australia's most loved fresh food retailer, inside and out. "
    "Everything The Hub does maps back to these five pillars.</p>",
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


p_cols = st.columns(5)
for i, hub in enumerate(HUBS):
    with p_cols[i]:
        color = hub["color"]
        pillar = hub.get("pillar", "")
        ctx = PILLAR_CONTEXT.get(pillar, {})
        tagline = ctx.get("tagline", "")
        status_items = ctx.get("status_items", [])

        status_html = ""
        for item in status_items:
            status_html += (
                f"<div style='font-size:0.78em;color:#6b7280;margin:2px 0;'>"
                f"&bull; {item}</div>"
            )

        st.markdown(
            f"<div style='border-left:3px solid {color};background:white;"
            f"border-radius:0 8px 8px 0;padding:14px;min-height:160px;"
            f"box-shadow:0 1px 3px rgba(0,0,0,0.06);'>"
            f"<div style='font-size:0.7em;color:{color};font-weight:700;"
            f"text-transform:uppercase;letter-spacing:0.5px;'>{pillar}</div>"
            f"<div style='font-size:0.9em;font-weight:700;color:{HFM_DARK};"
            f"margin:3px 0;'>{hub['icon']} {hub['name']}</div>"
            f"<div style='font-size:0.75em;color:#9ca3af;font-style:italic;"
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
# SECTION 3 — The 5 Goals (Live Progress) — single DB call
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    f"<h2 style='color:{HFM_DARK};margin-bottom:4px;'>The 5 Goals</h2>"
    "<p style='color:#6b7280;margin-top:0;'>Why The Hub exists &mdash; "
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
        else:
            desc = desc

        # Metric lines
        metric_html = ""
        for label, val in metric_items.items():
            metric_html += (
                f"<div style='display:flex;justify-content:space-between;"
                f"font-size:0.8em;color:#374151;margin:3px 0;'>"
                f"<span>{label}</span>"
                f"<span style='font-weight:600;'>{val:,}</span></div>"
            )

        bar_color = goal["color"]

        st.markdown(
            f"<div style='border-left:4px solid {goal['color']};background:white;"
            f"border-radius:0 10px 10px 0;padding:16px;min-height:240px;"
            f"box-shadow:0 1px 4px rgba(0,0,0,0.08);'>"
            f"<div style='font-size:1.4em;'>{goal['icon']}</div>"
            f"<div style='font-size:0.95em;font-weight:700;color:{HFM_DARK};"
            f"margin:4px 0 2px;'>{goal['title']}</div>"
            f"<div style='font-size:0.78em;color:#6b7280;margin-bottom:8px;'>"
            f"{desc}</div>"
            f"<div style='font-size:0.75em;color:{goal['color']};font-style:italic;"
            f"margin-bottom:10px;'>{goal['key_question']}</div>"
            f"<div style='margin:8px 0;'>{metric_html}</div>"
            f"<div style='background:#e5e7eb;border-radius:6px;height:6px;margin-top:10px;'>"
            f"<div style='background:{bar_color};height:6px;border-radius:6px;"
            f"width:{progress}%;'></div></div>"
            f"<div style='font-size:0.7em;color:#9ca3af;text-align:right;margin-top:2px;'>"
            f"{progress}%</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4 — Quick Launch
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    f"<h2 style='color:{HFM_DARK};margin-bottom:4px;'>Quick Launch</h2>"
    "<p style='color:#6b7280;margin-top:0;'>Jump straight into what matters.</p>",
    unsafe_allow_html=True,
)

_QUICK_LAUNCH = [
    {"label": "When In Doubt, Ask AI", "icon": "\U0001f4a1", "slug": "learning-centre",
     "desc": "The one habit that changes everything \u2014 start here", "goal": "G3"},
    {"label": "Ask Our Data", "icon": "\U0001f50d", "slug": "prompt-builder",
     "desc": "Build analytical prompts and query 383M transactions", "goal": "G2"},
    {"label": "Learn AI", "icon": "\U0001f31f", "slug": "academy",
     "desc": "Growing Legends Academy \u2014 6 levels from Seed to Legend", "goal": "G3"},
    {"label": "Supply Chain", "icon": "\U0001f69a", "slug": "buying-hub",
     "desc": "Category buying, demand forecasting, weather analysis", "goal": "G4"},
    {"label": "Mission Control", "icon": "\U0001f3af", "slug": "mission-control",
     "desc": "Documentation, data catalog, AI showcase, and system governance", "goal": "G1"},
    {"label": "Hub Assistant", "icon": "\U0001f4ac", "slug": "hub-assistant",
     "desc": "Ask about policies, procedures, and golden rules", "goal": "G2"},
]

ql_row1 = st.columns(3)
ql_row2 = st.columns(3)
ql_cols = ql_row1 + ql_row2

for idx, ql in enumerate(_QUICK_LAUNCH):
    with ql_cols[idx]:
        badge = goal_badge_html(ql["goal"])
        st.markdown(
            f"<div style='background:white;border-radius:10px;padding:16px;"
            f"box-shadow:0 1px 4px rgba(0,0,0,0.08);min-height:110px;'>"
            f"<div style='font-size:1.5em;'>{ql['icon']}</div>"
            f"<div style='font-weight:700;color:{HFM_DARK};margin:4px 0 2px;'>"
            f"{ql['label']}</div>"
            f"<div style='font-size:0.8em;color:#6b7280;margin-bottom:6px;'>"
            f"{ql['desc']}</div>"
            f"{badge}"
            f"</div>",
            unsafe_allow_html=True,
        )
        page = _pages.get(ql["slug"])
        if page:
            st.page_link(page, label=f"Open {ql['label']} \u2192", use_container_width=True)

st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5 — What's Happening Now (Activity Feed)
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    f"<h2 style='color:{HFM_DARK};margin-bottom:4px;'>What's Happening Now</h2>"
    "<p style='color:#6b7280;margin-top:0;'>Recent reports, proposals, "
    "and improvements across The Hub.</p>",
    unsafe_allow_html=True,
)

activity = fetch_recent_activity(limit=10)

if activity:
    def _detail_color(detail: str, item_type: str) -> str:
        """Pick a display color based on the detail text and item type."""
        d = (detail or "").strip().upper()
        # Exact status matches (agent proposals)
        if d in ("COMPLETED", "APPROVED"):
            return "#22c55e"
        if d in ("PENDING",):
            return "#f59e0b"
        if d in ("FAILED", "REJECTED"):
            return "#ef4444"
        # Keyword-based for reports, improvements, watchdog
        if "GRADE:" in d:
            return "#3b82f6"  # blue for graded reports
        if "RISK: HIGH" in d or "RISK: CRITICAL" in d:
            return "#ef4444"
        if "RISK:" in d:
            return "#f59e0b"
        if item_type == "improvement":
            return "#a855f7"  # purple for improvement findings
        return "#6b7280"

    feed_html = "<div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;'>"
    for item in activity:
        goal_badges = " ".join(goal_badge_html(g) for g in item.get("goal_ids", []))
        detail = item.get("detail") or ""
        detail_color = _detail_color(detail, item.get("type", ""))
        ts = item.get("timestamp", "")[:16]

        feed_html += (
            f"<div style='background:white;border-radius:8px;padding:12px 14px;"
            f"box-shadow:0 1px 3px rgba(0,0,0,0.06);'>"
            f"<div style='display:flex;align-items:center;gap:8px;'>"
            f"<span style='font-size:1.2em;'>{item['icon']}</span>"
            f"<span style='font-size:0.85em;font-weight:600;color:{HFM_DARK};"
            f"flex:1;'>{item['title'][:60]}</span>"
            f"</div>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"margin-top:6px;'>"
            f"<span style='font-size:0.75em;color:{detail_color};font-weight:500;'>"
            f"{detail}</span>"
            f"<span style='font-size:0.7em;color:#9ca3af;'>{ts}</span>"
            f"</div>"
            f"<div style='margin-top:4px;'>{goal_badges}</div>"
            f"</div>"
        )
    feed_html += "</div>"
    st.markdown(feed_html, unsafe_allow_html=True)
else:
    st.info("No recent activity yet. Start by running an analysis or submitting a prompt.")

st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5B — CALL TO ARMS: The Search for AI Ninjas
# ═══════════════════════════════════════════════════════════════════════════

# Fetch ninja stats
try:
    import requests as _req
    _api = os.getenv("API_URL", "http://localhost:8000")
    _radar = _req.get(f"{_api}/api/workflow/talent-radar", timeout=3).json()
    _ninja_count = _radar.get("total_ninjas", 0)
    _active_users = _radar.get("total_active_users", 0)
except Exception:
    _ninja_count = 0
    _active_users = 0

# User level
try:
    _user_id = user or "unknown"
    _stats = _req.get(f"{_api}/api/pta/user-stats/{_user_id}", timeout=3).json()
    _user_level = _stats.get("level", "Prompt Apprentice")
    _user_points = _stats.get("total_points", 0)
    _level_badges = {"AI Ninja": "\U0001f977", "Prompt Master": "\U0001f525", "Prompt Specialist": "\u26a1", "Prompt Apprentice": "\U0001f331"}
    _next_levels = {"Prompt Apprentice": (101, "Prompt Specialist"), "Prompt Specialist": (501, "Prompt Master"), "Prompt Master": (2001, "AI Ninja"), "AI Ninja": (0, "")}
    _nxt = _next_levels.get(_user_level, (0, ""))
    _pts_to_next = max(_nxt[0] - _user_points, 0) if _nxt[0] > 0 else 0
except Exception:
    _user_level = "Prompt Apprentice"
    _user_points = 0
    _pts_to_next = 101

st.markdown(
    f"<div style='background:linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);"
    f"border-radius:14px;padding:32px 28px;text-align:center;margin:20px 0;'>"
    f"<div style='font-size:2em;margin-bottom:8px;'>\U0001f977 THE SEARCH IS ON \U0001f977</div>"
    f"<div style='color:#e0e0e0;font-size:1.05em;max-width:600px;margin:0 auto;line-height:1.6;'>"
    f"Harris Farm is looking for the <strong style='color:#E040FB;'>Ultimate Harris Farmers</strong> "
    f"\u2014 the AI Ninjas who will drive change in our business."
    f"<br><br>"
    f"They could be in any store. Any warehouse. Any office. They could be <strong style='color:#E040FB;'>YOU</strong>."
    f"<br><br>"
    f"<span style='color:#9ca3af;font-size:0.9em;'>"
    f"We don't care about your title or department. We care about your curiosity, "
    f"your drive, and your willingness to learn.</span>"
    f"</div>"
    f"<div style='margin-top:20px;display:flex;justify-content:center;gap:24px;'>"
    f"<div style='background:rgba(224,64,251,0.15);padding:12px 20px;border-radius:10px;'>"
    f"<div style='color:#E040FB;font-size:1.4em;font-weight:700;'>{_ninja_count}</div>"
    f"<div style='color:#9ca3af;font-size:0.8em;'>AI Ninjas</div></div>"
    f"<div style='background:rgba(255,255,255,0.08);padding:12px 20px;border-radius:10px;'>"
    f"<div style='color:white;font-size:1.4em;font-weight:700;'>{_active_users}</div>"
    f"<div style='color:#9ca3af;font-size:0.8em;'>Active Users</div></div>"
    f"<div style='background:rgba(255,255,255,0.08);padding:12px 20px;border-radius:10px;'>"
    f"<div style='color:white;font-size:1.4em;font-weight:700;'>{_user_level}</div>"
    f"<div style='color:#9ca3af;font-size:0.8em;'>Your Level ({_user_points} pts"
    f"{f' | {_pts_to_next} to next' if _pts_to_next > 0 else ''})</div></div>"
    f"</div></div>",
    unsafe_allow_html=True,
)

# CTA button — navigate to Prompt Engine
_prompt_page = _pages.get("prompt-builder")
if _prompt_page:
    _cta_cols = st.columns([1, 2, 1])
    with _cta_cols[1]:
        st.page_link(_prompt_page, label="\U0001f680 START YOUR FIRST PROMPT", use_container_width=True)

st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6 — WATCHDOG Trust & Safety
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    f"<h2 style='color:{HFM_DARK};margin-bottom:4px;'>"
    "\U0001f6e1\ufe0f WATCHDOG Trust & Safety</h2>"
    "<p style='color:#6b7280;margin-top:0;'>The Hub governs itself. "
    "Every action logged, every output scored.</p>",
    unsafe_allow_html=True,
)

wd_col1, wd_col2 = st.columns([2, 1])

with wd_col1:
    _LAWS = [
        ("Honest code", "behaviour matches names"),
        ("Full audit trail", "no gaps"),
        ("Test before ship", "min 1 success + 1 failure per function"),
        ("Zero secrets in code", ".env only"),
        ("Operator authority", "Gus Harris only"),
        ("Data correctness", "every output traceable to source"),
        ("Document everything", "no undocumented features"),
    ]
    laws_html = ""
    for i, (law, detail) in enumerate(_LAWS, 1):
        laws_html += (
            f"<div style='margin:4px 0;font-size:0.85em;'>"
            f"<span style='color:{HFM_GREEN};font-weight:700;'>{i}.</span> "
            f"<strong>{law}</strong> "
            f"<span style='color:#9ca3af;'>&mdash; {detail}</span></div>"
        )
    st.markdown(
        f"<div style='background:#f0fdf4;border:1px solid #bbf7d0;"
        f"border-radius:10px;padding:16px;'>"
        f"<div style='font-weight:600;color:{HFM_GREEN};margin-bottom:8px;'>"
        f"The 7 Laws of WATCHDOG Governance</div>"
        f"{laws_html}"
        f"</div>",
        unsafe_allow_html=True,
    )

with wd_col2:
    try:
        import plotly.graph_objects as go

        labels = ["Honest", "Reliable", "Safe", "Clean", "Data", "Usable", "Documented"]
        values = fetch_watchdog_scores()

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            fillcolor="rgba(75, 160, 33, 0.15)",
            line=dict(color=HFM_GREEN, width=2),
            name="Avg Score",
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=9)),
                angularaxis=dict(tickfont=dict(size=10)),
            ),
            showlegend=False,
            margin=dict(l=30, r=30, t=20, b=20),
            height=240,
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.caption("Install plotly for the WATCHDOG radar chart.")

    portal = _pages.get("mission-control")
    if portal:
        st.page_link(portal, label="Full WATCHDOG Dashboard \u2192", use_container_width=True)

# Scheduler status
try:
    _wd_conn = __import__("sqlite3").connect(
        str(Path(__file__).resolve().parent.parent / "backend" / "hub_data.db")
    )
    _wd_row = _wd_conn.execute(
        "SELECT run_at, findings_new, health_api, health_hub "
        "FROM watchdog_runs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    _wd_conn.close()
    if _wd_row:
        from datetime import datetime as _dt
        _ago = _dt.now() - _dt.fromisoformat(_wd_row[0])
        _mins = int(_ago.total_seconds() / 60)
        _ago_str = f"{_mins}m ago" if _mins < 120 else f"{_mins // 60}h ago"
        _health = f"api:{_wd_row[2]} hub:{_wd_row[3]}"
        st.caption(
            f"Automated WATCHDOG: last check {_ago_str} | "
            f"{_health} | {_wd_row[1]} new findings"
        )
    else:
        st.caption("Automated WATCHDOG: starting soon...")
except Exception:
    pass

st.markdown("")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7 — System Health (compact, developer-facing)
# ═══════════════════════════════════════════════════════════════════════════

with st.expander("System Health"):
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Dashboards", "19")
    h2.metric("API Endpoints", "112")
    h3.metric("Tests", "1,003")
    h4.metric("Transaction Rows", "383.6M")

# --- About (compact) ---
with st.expander("About Harris Farm Markets"):
    st.markdown(
        "**Founded in 1971** by David and Cathy Harris. 100% family-owned for over "
        "fifty years. 30+ stores across NSW, Queensland, and the ACT.\n\n"
        "**Our Purpose:** Living the Greater Goodness \u2014 good food does good things for people.\n\n"
        "**Our Strategy:** *Fewer, Bigger, Better* \u2014 Vision 2030: Australia's most loved "
        "fresh food retailer, inside and out.\n\n"
        "*Co-CEOs: Angus Harris & Luke Harris*"
    )

render_footer("Harris Farm Hub", "Mission Control \u2014 AI Centre of Excellence", user)
