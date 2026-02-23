"""
Harris Farm Hub — Pillar 3: Growing Legendary Leadership (Intro Page)
Strategic front door for people development, Academy, and AI adoption.
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
pillar = get_pillar("P3")

# ── Fetch live metrics ──
_API = os.getenv("API_URL", "http://localhost:8000")
_HUB_DB = Path(__file__).resolve().parent.parent / "backend" / "hub_data.db"

# Academy stats (from API)
academy_users = 0
total_xp = 0
try:
    import requests
    resp = requests.get("{}/api/academy/leaderboard".format(_API), timeout=3)
    if resp.status_code == 200:
        leaders = resp.json()
        academy_users = len(leaders)
        total_xp = sum(u.get("total_xp", 0) for u in leaders)
except Exception:
    pass

# PtA submissions (from hub_data.db)
pta_submissions = 0
try:
    if _HUB_DB.exists():
        conn = sqlite3.connect(str(_HUB_DB))
        row = conn.execute("SELECT COUNT(*) FROM pta_submissions").fetchone()
        pta_submissions = row[0] if row else 0
        conn.close()
except Exception:
    pass

# ── Hero Banner ──
hero_metrics = [
    {"label": "Academy Users", "value": str(academy_users)},
    {"label": "Total XP Earned", "value": "{:,}".format(total_xp)},
    {"label": "Prompt Submissions", "value": str(pta_submissions)},
]
pillar_hero(pillar, metrics=hero_metrics)

# ── Key Indicators ──
st.subheader("Key Indicators")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Academy Users", academy_users)

with c2:
    st.metric("Total XP Earned", "{:,}".format(total_xp))

with c3:
    coming_soon_card("eNPS Score", "Employee survey data not yet connected")

with c4:
    coming_soon_card("Turnover Rate", "HR data not yet connected")

# ── Monday.com Initiatives ──
st.markdown("---")

if is_configured():
    summary = fetch_board_summary(BOARD_IDS["P3"])
    initiative_summary_card(summary)
else:
    st.markdown(
        "<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);"
        "border-radius:8px;padding:12px 16px;"
        "color:#8899AA;font-size:0.9em;'>"
        "\U0001f4cb <strong style='color:#B0BEC5;'>Initiative Tracking:</strong> Connect Monday.com "
        "to see P3 strategic initiatives here. "
        "Add <code>MONDAY_API_KEY</code> to your <code>.env</code> file."
        "</div>",
        unsafe_allow_html=True,
    )

# ── Strategic Context ──
st.markdown("---")
st.markdown(
    "<div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);"
    "border-radius:10px;padding:20px;'>"
    "<h3 style='color:white;margin-top:0;font-family:Georgia,serif;'>Growing Legends, Not Just Skills</h3>"
    "<p style='color:#B0BEC5;'>AI adoption is a people strategy, not a tech project. "
    "The Academy, Prompt Engine, and Paddock exist because we believe every Harris Farmer "
    "can become exceptional \u2014 if we give them the right tools, the right training, "
    "and the right encouragement.</p>"
    "<p style='color:#8899AA;font-size:0.9em;'>"
    "<strong style='color:#B0BEC5;'>Prosci ADKAR</strong> change management is active across all P3 initiatives. "
    "We measure adoption, not just availability.</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Sub-page Navigation ──
st.markdown("---")
st.subheader("Explore People & Learning")
sub_page_links([
    "learning-centre", "the-paddock", "academy",
    "prompt-builder", "approvals", "the-rubric", "hub-assistant",
])

# ── One Thing ──
one_thing_box(
    "AI adoption is a people strategy, not a tech project. "
    "The gap between companies that succeed with AI and those that don't "
    "isn't technology \u2014 it's whether their people feel confident using it."
)

render_footer("Growing Legends", "Pillar 3 \u2014 Growing Legendary Leadership", user)
