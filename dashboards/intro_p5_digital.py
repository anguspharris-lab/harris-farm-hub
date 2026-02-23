"""
Harris Farm Hub — Pillar 5: Tomorrow's Business, Built Better (Intro Page)
Strategic front door for the digital platform, AI agents, and system governance.
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
pillar = get_pillar("P5")

# ── Fetch live metrics ──
_HUB_DB = Path(__file__).resolve().parent.parent / "backend" / "hub_data.db"

hub_pages = len(_pages) + 1  # +1 for home
kb_articles = 0
agent_count = 0
prompt_templates = 0

try:
    if _HUB_DB.exists():
        conn = sqlite3.connect(str(_HUB_DB))
        row = conn.execute("SELECT COUNT(*) FROM knowledge_base").fetchone()
        kb_articles = row[0] if row and row[0] else 0

        row = conn.execute("SELECT COUNT(*) FROM agent_registry").fetchone()
        agent_count = row[0] if row and row[0] else 0

        row = conn.execute("SELECT COUNT(*) FROM prompt_templates").fetchone()
        prompt_templates = row[0] if row and row[0] else 0

        conn.close()
except Exception:
    pass

# ── Hero Banner ──
hero_metrics = [
    {"label": "Hub Pages", "value": str(hub_pages)},
    {"label": "KB Articles", "value": str(kb_articles)},
    {"label": "AI Agents", "value": str(agent_count)},
    {"label": "Prompt Templates", "value": str(prompt_templates)},
]
pillar_hero(pillar, metrics=hero_metrics)

# ── Key Indicators ──
st.subheader("Platform Health")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Hub Pages", hub_pages)
c2.metric("Knowledge Base", "{} articles".format(kb_articles))
c3.metric("AI Agents", agent_count)
c4.metric("Prompt Templates", prompt_templates)

# ── Monday.com Initiatives ──
st.markdown("---")

if is_configured():
    summary = fetch_board_summary(BOARD_IDS["P5"])
    initiative_summary_card(summary)
else:
    st.markdown(
        "<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);"
        "border-radius:8px;padding:12px 16px;"
        "color:#8899AA;font-size:0.9em;'>"
        "\U0001f4cb <strong style='color:#B0BEC5;'>Initiative Tracking:</strong> Connect Monday.com "
        "to see P5 strategic initiatives here. "
        "Add <code>MONDAY_API_KEY</code> to your <code>.env</code> file."
        "</div>",
        unsafe_allow_html=True,
    )

# ── Strategic Context ──
st.markdown("---")
st.markdown(
    "<div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);"
    "border-radius:10px;padding:20px;'>"
    "<h3 style='color:white;margin-top:0;font-family:Georgia,serif;'>The Platform Is the Strategy</h3>"
    "<p style='color:#B0BEC5;'>"
    "The AI Centre of Excellence isn't a department \u2014 it's how Harris Farm "
    "operates. Every dashboard, every agent, every prompt template exists to make "
    "the strategy visible, measurable, and actionable.</p>"
    "<p style='color:#8899AA;font-size:0.9em;'>"
    "<strong style='color:#B0BEC5;'>Key initiatives:</strong> Citizen Developer Program | "
    "WATCHDOG governance | Agent marketplace | "
    "Analytics self-service</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Sub-page Navigation ──
st.markdown("---")
st.subheader("Explore Digital & AI")
sub_page_links([
    "workflow-engine", "analytics-engine", "agent-hub",
    "agent-ops", "ai-adoption", "trending", "mission-control",
])

# ── One Thing ──
one_thing_box(
    "The best platform is the one people actually use. "
    "Measure adoption, not features. A dashboard nobody opens "
    "is worse than no dashboard at all \u2014 it creates a false sense of progress."
)

render_footer("Digital & AI HQ", "Pillar 5 \u2014 Tomorrow's Business, Built Better", user)
