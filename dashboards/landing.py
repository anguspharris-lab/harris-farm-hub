"""
Harris Farm Hub — Landing Page
Centre of Excellence — "For The Greater Goodness"
Aligned with Harris Farm's 5 Strategic Pillars.
Port 8500.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st

from nav import render_nav, HUBS, BASE_URL
from shared.styles import apply_styles, render_footer, HFM_GREEN, HFM_DARK

st.set_page_config(
    page_title="Harris Farm Hub — Centre of Excellence",
    page_icon="\U0001f34e",
    layout="wide",
)


def check_password():
    """Simple password protection."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("\U0001f512 Harris Farm Hub")
        pw = st.text_input("Password:", type="password")
        if st.button("Login"):
            if pw == "HFM2026!1":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        st.stop()


check_password()

apply_styles()
render_nav(8500)

# --- Hero ---
st.markdown(
    f"<h1 style='margin-bottom:0;color:{HFM_GREEN};'>Harris Farm Hub</h1>"
    "<p style='color:#6b7280;font-size:1.2em;margin-top:4px;'>"
    "<strong>AI Centre of Excellence</strong> &mdash; For The Greater Goodness</p>"
    "<p style='color:#9ca3af;font-size:0.95em;margin-top:2px;'>"
    "Family owned since '71. AI-powered since '26. "
    "Empowering every Harris Farmer with data-driven insights.</p>",
    unsafe_allow_html=True,
)

# --- Strategy Banner ---
st.markdown(
    "<div style='background:linear-gradient(135deg, #4ba021 0%, #3a8019 100%);"
    "color:white;padding:20px 28px;border-radius:10px;margin:12px 0 20px 0;'>"
    "<div style='font-size:1.3em;font-weight:700;margin-bottom:6px;'>"
    "Fewer, Bigger, Better</div>"
    "<div style='font-size:0.95em;opacity:0.95;'>"
    "Our strategy to become Australia's most loved fresh food retailer — inside and out. "
    "The Hub brings Pillars 4 &amp; 5 to life: smarter operations today, "
    "AI-powered innovation for tomorrow.</div>"
    "</div>",
    unsafe_allow_html=True,
)

# --- Quick KPIs ---
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "harris_farm.db"

if DB_PATH.exists():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        store_count = conn.execute(
            "SELECT COUNT(DISTINCT store) FROM sales"
        ).fetchone()[0]

        total_sales = conn.execute(
            "SELECT printf('%.1f', SUM(value)/1e6) FROM sales "
            "WHERE measure = 'Sales - Val'"
        ).fetchone()[0]

        latest_we = conn.execute(
            "SELECT MAX(week_ending) FROM sales"
        ).fetchone()[0]

        avg_share = conn.execute(
            "SELECT printf('%.1f', AVG(market_share_pct)) FROM market_share "
            "WHERE channel = 'Total'"
        ).fetchone()[0]

        customer_total = conn.execute(
            "SELECT printf('%.0f', SUM(value)/1000) FROM customers "
            "WHERE measure = 'Customer Count'"
        ).fetchone()[0]
    except Exception:
        store_count = total_sales = latest_we = avg_share = customer_total = "—"
    finally:
        conn.close()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Stores", store_count)
    k2.metric("Total Sales", f"${total_sales}M" if total_sales else "—")
    k3.metric("Avg Market Share", f"{avg_share}%" if avg_share else "—")
    k4.metric("Customer Visits (K)", f"{customer_total}K" if customer_total else "—")

    st.caption(f"Data through {latest_we}" if latest_we else "")

st.markdown("")

# --- Pillar Cards ---
# Map pillar numbers to additional context for the cards
PILLAR_CONTEXT = {
    "Pillar 1": {
        "tagline": "We'll do things right, from end-to-end",
        "status_items": [
            "100% renewable energy — ACHIEVED",
            "B Corp certification — board approval Feb/Mar",
        ],
    },
    "Pillar 2": {
        "tagline": "We'll take the 'you get me' feeling to a whole new level",
        "status_items": [
            "Loyalty program pilot — Apr 2026",
            "Voice of Customer — in progress",
        ],
    },
    "Pillar 3": {
        "tagline": "We will be famous for attracting, developing, and retaining exceptional people",
        "status_items": [
            "Prompt Academy — 5 levels, in progress",
            "Prosci ADKAR — change management active",
        ],
    },
    "Pillar 4": {
        "tagline": "We will tidy up the supply chain, from pay to purchase",
        "status_items": [
            "OOS reduction 20% — target Jun 2026",
            "Buying automation — in progress",
        ],
    },
    "Pillar 5": {
        "tagline": "We'll build a brilliant back-end with tools that talk, systems that serve, data we trust",
        "status_items": [
            "AI Centre of Excellence — CRITICAL, active",
            "Citizen Developer Program — in progress",
        ],
    },
}

_token_qs = ""

# Render hub cards — 3 top, 2 bottom (or adapt to count)
_n_hubs = len(HUBS)
if _n_hubs <= 3:
    all_cols = st.columns(_n_hubs)
elif _n_hubs <= 6:
    row1 = st.columns(3)
    row2 = st.columns(3) if _n_hubs > 3 else []
    all_cols = row1 + row2
else:
    all_cols = st.columns(_n_hubs)

for i, hub in enumerate(HUBS):
    # Wrap to second row after 3 cards
    if i == 3 and _n_hubs > 3:
        row2 = st.columns(min(3, _n_hubs - 3))
        # Re-reference the second row columns
        all_cols = all_cols[:3] + row2
    col_idx = i if i < 3 else i  # index into all_cols
    with all_cols[col_idx]:
        color = hub["color"]
        icon = hub["icon"]
        name = hub["name"]
        pillar = hub.get("pillar", "")
        pillar_title = hub.get("pillar_title", "")
        first_port = hub["dashboards"][0][1]
        ctx = PILLAR_CONTEXT.get(pillar, {})
        tagline = ctx.get("tagline", "")
        status_items = ctx.get("status_items", [])

        # Dashboard links
        dash_list = ""
        for label, port, d_icon, desc in hub["dashboards"]:
            dash_list += (
                f"<div style='margin:5px 0;'>"
                f"<a href='{BASE_URL}:{port}{_token_qs}' target='_top' "
                f"style='color:{color};text-decoration:none;font-weight:600;'>"
                f"{d_icon} {label}</a>"
                f" <span style='color:#9ca3af;font-size:0.8em;'>— {desc}</span>"
                f"</div>"
            )

        # Status badges
        status_html = ""
        for item in status_items:
            status_html += (
                f"<div style='font-size:0.8em;color:#6b7280;margin:2px 0;'>"
                f"&bull; {item}</div>"
            )

        st.markdown(
            f"<div style='border:2px solid {color};border-radius:12px;padding:20px;"
            f"min-height:320px;background:white;'>"
            f"<div style='font-size:0.75em;color:{color};font-weight:600;"
            f"text-transform:uppercase;letter-spacing:1px;'>{pillar}</div>"
            f"<div style='font-size:1.3em;font-weight:bold;color:{HFM_DARK};"
            f"margin:4px 0;'>{icon} {pillar_title}</div>"
            f"<div style='font-size:0.85em;color:#6b7280;font-style:italic;"
            f"margin-bottom:10px;'>{tagline}</div>"
            f"<hr style='margin:10px 0;border-color:#e5e7eb;'>"
            f"{dash_list}"
            f"<div style='margin-top:10px;'>{status_html}</div>"
            f"<div style='margin-top:14px;'>"
            f"<a href='{BASE_URL}:{first_port}{_token_qs}' target='_top' "
            f"style='display:inline-block;padding:8px 20px;background:{color};"
            f"color:white;border-radius:6px;text-decoration:none;font-size:0.9em;'>"
            f"Open {name} &rarr;</a>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown("")

# --- AI Philosophy Banner ---
st.markdown(
    "<div style='background:#f0fdf4;border-left:4px solid #4ba021;"
    "padding:16px 20px;border-radius:0 8px 8px 0;margin:10px 0;'>"
    "<div style='font-weight:600;color:#171819;font-size:1.05em;'>"
    "AI as a Job Partner</div>"
    "<div style='color:#6b7280;font-size:0.9em;margin-top:4px;'>"
    "The Hub is about <strong>enablement, not replacement</strong>. "
    "AI takes care of the repetitive stuff so you can focus on what matters — "
    "serving customers, building relationships, and doing your best work. "
    "Start with the <a href='" + BASE_URL + ":8510' target='_top' "
    "style='color:#4ba021;font-weight:600;'>Learning Centre</a> "
    "to build your skills.</div>"
    "</div>",
    unsafe_allow_html=True,
)

# --- Harris Farm Story ---
with st.expander("About Harris Farm Markets"):
    st.markdown("""
**Founded in 1971** by David and Cathy Harris, Harris Farm Markets has been 100% family-owned
for over fifty years. What started as a single store in Villawood has grown into 30+ stores across
NSW, Queensland, and the ACT, united by a simple belief: **good food does good things for people.**

**Our Purpose:** Living the Greater Goodness — we believe in nature itself. Our pricing, produce,
and partnerships are guided by seasonal abundance and a commitment to Australian farmers,
sustainable sourcing, and community connection.

**Our Strategy:** *Fewer, Bigger, Better* — we're streamlining operations, scaling what works,
and elevating quality as we grow toward our Vision 2030: **Australia's most loved fresh food
retailer, inside and out.**

**The Hub** is our AI Centre of Excellence — Pillar 5 of our strategy brought to life.
It empowers every Harris Farmer with data-driven insights, from store managers checking
weekend sales to buyers optimising orders with weather forecasts.

*Co-CEOs: Angus Harris & Luke Harris*
    """)

# --- Feature Status Note ---
st.markdown(
    "<div style='background:#fffbeb;border-left:4px solid #d97706;"
    "padding:12px 16px;border-radius:0 8px 8px 0;margin:10px 0;'>"
    "<div style='font-size:0.85em;color:#92400e;'>"
    "<strong>Note:</strong> The Hub is actively evolving. "
    "Dashboards marked <strong>LIVE</strong> are fully functional. "
    "Features marked <strong>Future Development</strong> are planned "
    "and being built through our autonomous development pipeline. "
    "<a href='" + BASE_URL + ":8515' target='_top' "
    "style='color:#d97706;'>View full feature status in Hub Portal &rarr;</a>"
    "</div></div>",
    unsafe_allow_html=True,
)

st.markdown("")

render_footer("Harris Farm Hub", "AI Centre of Excellence")
