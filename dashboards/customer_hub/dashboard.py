"""
Harris Farm Hub — Customer Hub
Customer Insights from POS/loyalty data (Layer 1).

'Fewer, Bigger, Better' — understand who shops with us, how often,
and what drives their loyalty.
"""

import streamlit as st

from shared.styles import render_header, render_footer
from shared.ask_question import render_ask_question
from shared.voice_realtime import render_voice_data_box

user = st.session_state.get("auth_user")

render_header(
    "Customer Hub",
    "**Harris Farm Markets** | Customer intelligence from POS & loyalty data",
    goals=["G1", "G2"],
    strategy_context=(
        "Understanding who shops with us and what drives their loyalty "
        "powers 'Fewer, Bigger, Better' — focus on customers who love us "
        "most in the places that matter."
    ),
)
st.caption("Step 5: Review this data. Add your judgment. Your experience makes this useful.")

# ── Tabs ─────────────────────────────────────────────────────────────────────

tab_names = ["Overview", "Known Customers", "Channel Analysis",
             "Cohort & Retention", "By Store"]
tabs = st.tabs(tab_names)

from customer_hub.customer_overview import render as render_overview
from customer_hub.known_customers import render as render_known
from customer_hub.channel_analysis import render as render_channel
from customer_hub.cohort_retention import render as render_cohort
from customer_hub.customer_by_store import render as render_by_store

with tabs[0]:
    render_overview()
with tabs[1]:
    render_known()
with tabs[2]:
    render_channel()
with tabs[3]:
    render_cohort()
with tabs[4]:
    render_by_store()

# ── Cross-dashboard links ────────────────────────────────────────────────────

st.markdown("---")
st.markdown("**Related**")
_pages = st.session_state.get("_pages", {})
c1, c2, c3, c4 = st.columns(4)
if "sales" in _pages:
    c1.page_link(_pages["sales"], label="Sales by Store", icon="\U0001f4c8")
if "plu-intel" in _pages:
    c2.page_link(_pages["plu-intel"], label="PLU Intelligence", icon="\U0001f4ca")
if "store-ops" in _pages:
    c3.page_link(_pages["store-ops"], label="Store Operations", icon="\U0001f3ea")
if "market-share" in _pages:
    c4.page_link(_pages["market-share"], label="Market Share", icon="\U0001f4ca")

# ── Footer ───────────────────────────────────────────────────────────────────

render_voice_data_box("customer_hub")
render_ask_question("customer_hub")
render_footer("Customer Hub", "Layer 1 — POS & loyalty data", user=user)
