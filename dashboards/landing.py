"""
Harris Farm Hub — Landing Page
Centre of Excellence — "For The Greater Goodness"
Aligned with Harris Farm's 5 Strategic Pillars.
"""

import sqlite3
from pathlib import Path

import streamlit as st

from nav import HUBS, _PORT_TO_SLUG
from shared.styles import render_footer, HFM_GREEN, HFM_DARK

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})

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

# --- Pillar Context ---
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


def _port_to_page(port):
    """Convert a legacy port number to a page object for st.page_link()."""
    slug = _PORT_TO_SLUG.get(port)
    if slug and slug in _pages:
        return _pages[slug]
    return None


# --- Pillar Cards ---
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
    if i == 3 and _n_hubs > 3:
        row2 = st.columns(min(3, _n_hubs - 3))
        all_cols = all_cols[:3] + row2
    col_idx = i if i < 3 else i
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

        # Status badges HTML
        status_html = ""
        for item in status_items:
            status_html += (
                f"<div style='font-size:0.8em;color:#6b7280;margin:2px 0;'>"
                f"&bull; {item}</div>"
            )

        # Card header (HTML for styling, no links)
        st.markdown(
            f"<div style='border:2px solid {color};border-radius:12px;padding:20px;"
            f"min-height:200px;background:white;'>"
            f"<div style='font-size:0.75em;color:{color};font-weight:600;"
            f"text-transform:uppercase;letter-spacing:1px;'>{pillar}</div>"
            f"<div style='font-size:1.3em;font-weight:bold;color:{HFM_DARK};"
            f"margin:4px 0;'>{icon} {pillar_title}</div>"
            f"<div style='font-size:0.85em;color:#6b7280;font-style:italic;"
            f"margin-bottom:10px;'>{tagline}</div>"
            f"<hr style='margin:10px 0;border-color:#e5e7eb;'>"
            f"<div style='margin-top:10px;'>{status_html}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Dashboard links — using st.page_link (session-safe, no reload)
        for label, port, d_icon, desc in hub["dashboards"]:
            page = _port_to_page(port)
            if page:
                st.page_link(page, label=f"{d_icon} {label}", use_container_width=True)

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
    "serving customers, building relationships, and doing your best work.</div>"
    "</div>",
    unsafe_allow_html=True,
)
st.page_link(_pages.get("learning-centre", "/"), label="Start with the Learning Centre", use_container_width=False)

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
    "and being built through our autonomous development pipeline.</div>"
    "</div>",
    unsafe_allow_html=True,
)
st.page_link(_pages.get("hub-portal", "/"), label="View full feature status in Hub Portal", use_container_width=False)

st.markdown("")

render_footer("Harris Farm Hub", "AI Centre of Excellence")
