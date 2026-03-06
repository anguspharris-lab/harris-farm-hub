"""
Harris Farm Way -- Landing Page
The AI-First Meeting Operating System.
The front door for ALL structured sessions at Harris Farm.
"""

import streamlit as st
from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})

render_header(
    "This is how Harris Farm transforms.",
    "AI First decisions. Supply chain reimagined. Every meeting moves the business forward.",
    goals=["G1", "G5"],
    strategy_context="Transformation \u2014 Chapter 1 of the Harris Farm AI First story",
)

# -- Hero text --------------------------------------------------------------
st.markdown(
    "Everything that changes how we work lives here. "
    "Six session types, one tool, one place \u2014 "
    "every meeting starts with a question, ends with a decision, "
    "and leaves a trail of intelligence the whole business can use."
)

st.divider()

# -- 3-step visual ----------------------------------------------------------
st.markdown("### How It Works")

p1, p2, p3 = st.columns(3)
with p1:
    with st.container(border=True):
        st.markdown("#### Step 1: Prepare")
        st.markdown(
            "Before the meeting, each participant completes a short form. "
            "Their input is captured, structured, and ready for synthesis."
        )
        st.caption("5 minutes per person")

with p2:
    with st.container(border=True):
        st.markdown("#### Step 2: Synthesise")
        st.markdown(
            "AI reads every response and surfaces themes, gaps, and "
            "opportunities. The facilitator walks in with clarity, not chaos."
        )
        st.caption("Automatic, before the meeting starts")

with p3:
    with st.container(border=True):
        st.markdown("#### Step 3: Execute")
        st.markdown(
            "Decisions are made in the room. Actions are logged. "
            "Intelligence feeds back into the Hub for the next cycle."
        )
        st.caption("Decisions, not discussions")

st.divider()

# -- Meeting Types ----------------------------------------------------------
st.markdown("### Choose Your Session")
st.markdown(
    "Each session type has its own question set, tailored to the decisions "
    "that need to be made. Pick the one that fits."
)

# Row 1: SC Review + AI Readiness
m1, m2 = st.columns(2)

with m1:
    with st.container(border=True):
        st.markdown("#### Supply Chain Review")
        st.markdown(
            "The original. Stakeholder interviews for supply chain "
            "transformation \u2014 from pay to purchase."
        )
        st.caption("5 sections \u00b7 ~15 minutes")
        if "sc-interview" in _pages:
            st.page_link(_pages["sc-interview"], label="Start SC Review", use_container_width=True)

with m2:
    with st.container(border=True):
        st.markdown("#### AI Readiness Review")
        st.markdown(
            "How ready is your team for AI? Capability assessment "
            "across 8 dimensions."
        )
        st.caption("5 sections \u00b7 ~12 minutes")
        if "arr-interview" in _pages:
            st.page_link(_pages["arr-interview"], label="Start AI Readiness", use_container_width=True)

# Row 2: AI Vision + Strategy Sprint
m3, m4 = st.columns(2)

with m3:
    with st.container(border=True):
        st.markdown("#### AI Vision Session")
        st.markdown(
            "Where we imagine what's possible. AI capability, blockers, "
            "and lighthouse opportunities."
        )
        st.caption("3 sections \u00b7 ~10 minutes")
        if "hfw-ai-vision" in _pages:
            st.page_link(_pages["hfw-ai-vision"], label="Start AI Vision", use_container_width=True)

with m4:
    with st.container(border=True):
        st.markdown("#### Strategy Sprint")
        st.markdown(
            "Rapid alignment on RAG status, decisions needed, "
            "risks, and next actions."
        )
        st.caption("3 sections \u00b7 ~10 minutes")
        if "hfw-strategy-sprint" in _pages:
            st.page_link(_pages["hfw-strategy-sprint"], label="Start Sprint", use_container_width=True)

# Row 3: Dept One-Pager + Board Prep
m5, m6 = st.columns(2)

with m5:
    with st.container(border=True):
        st.markdown("#### Department One-Pager")
        st.markdown(
            "Your department at a glance \u2014 results, priorities, "
            "blockers, and asks."
        )
        st.caption("2 sections \u00b7 ~8 minutes")
        if "hfw-dept-one-pager" in _pages:
            st.page_link(_pages["hfw-dept-one-pager"], label="Start One-Pager", use_container_width=True)

with m6:
    with st.container(border=True):
        st.markdown("#### Board Prep")
        st.markdown(
            "Board-ready in one session. Highlights, key metrics, "
            "decisions required, and risk register."
        )
        st.caption("3 sections \u00b7 ~10 minutes")
        if "hfw-board-prep" in _pages:
            st.page_link(_pages["hfw-board-prep"], label="Start Board Prep", use_container_width=True)

st.divider()

# -- SC Analysis link -------------------------------------------------------
with st.container(border=True):
    a_l, a_r = st.columns([3, 1])
    with a_l:
        st.markdown("#### Supply Chain Analysis")
        st.markdown(
            "Review aggregated interview responses, ADKAR scores, "
            "capability gaps, and key themes across all SC Review submissions."
        )
        st.caption("Read-only dashboard")
    with a_r:
        if "sc-analysis" in _pages:
            st.page_link(_pages["sc-analysis"], label="View Analysis", use_container_width=True)

st.divider()

# -- Footer -----------------------------------------------------------------
st.markdown(
    "> *\"The best meetings don't just consume time \u2014 they create intelligence.\"*"
)

render_footer("Transformation", "AI-First Meeting Operating System", user=user)
