"""
Harris Farm Hub — Pillar 4: Today's Business, Done Better (Intro Page)
Strategic front door for operations, supply chain, and financial performance.
"""

import os
import sqlite3
from pathlib import Path

import streamlit as st

from shared.styles import render_footer, HFM_GREEN, HFM_DARK
from shared.pillar_data import get_pillar
from shared.monday_connector import is_configured, fetch_board_summary, BOARD_IDS
from shared.strategic_framing import (
    pillar_hero, coming_soon_card, one_thing_box,
    initiative_summary_card, sub_page_links,
)

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})
pillar = get_pillar("P4")

# ── Fetch live metrics ──
_SALES_DB = Path(__file__).resolve().parent.parent / "harris_farm.db"

latest_revenue = 0
latest_gp_pct = 0
store_count = 43  # Known constant from store_master.csv

try:
    if _SALES_DB.exists():
        conn = sqlite3.connect(str(_SALES_DB))
        row = conn.execute(
            "SELECT SUM(total_sales), SUM(gp) "
            "FROM weekly_sales "
            "WHERE week_ending = (SELECT MAX(week_ending) FROM weekly_sales)"
        ).fetchone()
        if row and row[0]:
            latest_revenue = row[0]
            latest_gp_pct = (row[1] / row[0] * 100) if row[0] > 0 else 0
        conn.close()
except Exception:
    pass

# ── Hero Banner ──
rev_display = "${:,.0f}".format(latest_revenue) if latest_revenue else "$\u2014"
gp_display = "{:.1f}%".format(latest_gp_pct) if latest_gp_pct else "\u2014"

hero_metrics = [
    {"label": "Latest Week Revenue", "value": rev_display},
    {"label": "Gross Profit %", "value": gp_display},
    {"label": "Stores", "value": str(store_count)},
    {"label": "Transaction Rows", "value": "383.6M"},
]
pillar_hero(pillar, metrics=hero_metrics)

# ── Key Indicators ──
st.subheader("Key Indicators")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest Week Revenue", rev_display)
c2.metric("Gross Profit %", gp_display)
c3.metric("Active Stores", store_count)
c4.metric("Transaction History", "383.6M rows")

# ── Monday.com Initiatives ──
st.markdown("---")

if is_configured():
    summary = fetch_board_summary(BOARD_IDS["P4"])
    initiative_summary_card(summary)
else:
    st.markdown(
        "<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);"
        "border-radius:8px;padding:12px 16px;"
        "color:#8899AA;font-size:0.9em;'>"
        "\U0001f4cb <strong style='color:#B0BEC5;'>Initiative Tracking:</strong> Connect Monday.com "
        "to see P4 strategic initiatives here. "
        "Add <code>MONDAY_API_KEY</code> to your <code>.env</code> file."
        "</div>",
        unsafe_allow_html=True,
    )

# ── Strategic Context ──
st.markdown("---")
st.markdown(
    "<div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);"
    "border-radius:10px;padding:20px;'>"
    "<h3 style='color:white;margin-top:0;font-family:Georgia,serif;'>Tidy Up the Supply Chain</h3>"
    "<p style='color:#B0BEC5;'>"
    "Grant Enders is transforming our supply chain from pay to purchase. "
    "The Hub tracks this transformation with 383.6 million transaction rows, "
    "store-level P&Ls, PLU wastage analysis, and demand forecasting.</p>"
    "<p style='color:#8899AA;font-size:0.9em;'>"
    "<strong style='color:#B0BEC5;'>Key targets:</strong> OOS reduction 20% by Jun 2026 | "
    "Category buying optimisation | Weather-adjusted demand planning</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Sub-page Navigation ──
st.markdown("---")
st.subheader("Explore Operations")
sub_page_links([
    "sales", "profitability", "revenue-bridge", "store-ops",
    "buying-hub", "product-intel", "plu-intel", "transport",
])

# ── One Thing ──
one_thing_box(
    "The supply chain wins happen in the data before they happen in the warehouse. "
    "Every out-of-stock, every margin leak, every inefficient route "
    "\u2014 the evidence is already here. The question is whether we're looking."
)

render_footer("Operations HQ", "Pillar 4 \u2014 Today's Business, Done Better", user)
