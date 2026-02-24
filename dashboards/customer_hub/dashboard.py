"""
Harris Farm Hub — Customer Hub
Combined Customer Insights (POS) + Market Share (CBAS) experience.

'Fewer, Bigger, Better' — understand who shops with us and where we're
winning (or losing) market position, all in one place.
"""

import streamlit as st

from shared.styles import render_header, render_footer
from shared.ask_question import render_ask_question
from shared.voice_realtime import render_voice_data_box

user = st.session_state.get("auth_user")

render_header(
    "Customer Hub",
    "**Harris Farm Markets** | Customer intelligence & competitive position",
    goals=["G1", "G2"],
    strategy_context=(
        "Understanding who shops with us and where we stand competitively "
        "powers 'Fewer, Bigger, Better' — focus on customers who love us "
        "most in the places that matter."
    ),
)
st.caption("💡 Step 5: Review this data. Add your judgment. Your experience makes this useful.")

# ── Section selector ─────────────────────────────────────────────────────────

section = st.radio(
    "Choose a lens",
    ["Customer Insights", "Market Share"],
    horizontal=True,
    key="ch_section",
    help="Customer Insights = POS/loyalty data (Layer 1) | Market Share = CBAS competitive data (Layer 2)",
)

# ── Tab routing ──────────────────────────────────────────────────────────────

if section == "Customer Insights":
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

else:
    tab_names = ["Overview", "Store Performance", "Catchment Tiers",
                 "Growth Frontiers", "Map"]
    tabs = st.tabs(tab_names)

    from customer_hub.ms_overview import render as render_ms_overview
    from customer_hub.ms_store_perf import render as render_ms_store
    from customer_hub.ms_catchment import render as render_ms_catch
    from customer_hub.ms_growth import render as render_ms_growth
    from customer_hub.ms_map import render as render_ms_map

    with tabs[0]:
        render_ms_overview()
    with tabs[1]:
        render_ms_store()
    with tabs[2]:
        render_ms_catch()
    with tabs[3]:
        render_ms_growth()
    with tabs[4]:
        render_ms_map()

# ── Cross-dashboard links ────────────────────────────────────────────────────

st.markdown("---")
st.markdown("**Dig Deeper**")
_pages = st.session_state.get("_pages", {})
c1, c2, c3 = st.columns(3)
if "sales" in _pages:
    c1.page_link(_pages["sales"], label="Sales by Store", icon="📈")
if "plu-intel" in _pages:
    c2.page_link(_pages["plu-intel"], label="PLU Intelligence", icon="📊")
if "store-ops" in _pages:
    c3.page_link(_pages["store-ops"], label="Store Operations", icon="🏪")

# ── Footer ───────────────────────────────────────────────────────────────────

render_voice_data_box("customer_hub")
render_ask_question("customer_hub")
render_footer("Customer Hub", "Layer 1 (POS) + Layer 2 (CBAS)", user=user)
