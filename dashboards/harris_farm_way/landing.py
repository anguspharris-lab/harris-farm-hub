"""
Transformation -- Landing Page
The AI-First Meeting Operating System.
Same process, different focus. One system. Not six separate tools.
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
    "Same process, different focus \u2014 one system, not six separate tools."
)

st.divider()

# -- The universal 3-step process -------------------------------------------
st.markdown("### Every session follows the same three steps")

p1, p2, p3 = st.columns(3)
with p1:
    with st.container(border=True):
        st.markdown(
            "<div style='text-align:center;font-size:2em;margin-bottom:4px;'>"
            "\U0001f4cb</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Step 1: Prepare")
        st.markdown(
            "Before the meeting, each participant completes a short form. "
            "Their input is captured, structured, and ready for synthesis."
        )
        st.caption("5 minutes per person")

with p2:
    with st.container(border=True):
        st.markdown(
            "<div style='text-align:center;font-size:2em;margin-bottom:4px;'>"
            "\U0001f9e0</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Step 2: Synthesise")
        st.markdown(
            "AI reads every response and surfaces themes, gaps, and "
            "opportunities. The facilitator walks in with clarity, not chaos."
        )
        st.caption("Automatic, before the meeting starts")

with p3:
    with st.container(border=True):
        st.markdown(
            "<div style='text-align:center;font-size:2em;margin-bottom:4px;'>"
            "\U0001f680</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Step 3: Execute")
        st.markdown(
            "Decisions are made in the room. Actions are logged. "
            "Intelligence feeds back into the Hub for the next cycle."
        )
        st.caption("Decisions, not discussions")

# Arrow connectors between steps
st.markdown(
    "<div style='text-align:center;color:#718096;font-size:0.85em;"
    "margin:-8px 0 8px;letter-spacing:0.1em;'>"
    "PREPARE &nbsp;\u2192&nbsp; SYNTHESISE &nbsp;\u2192&nbsp; EXECUTE"
    "</div>",
    unsafe_allow_html=True,
)

st.divider()

# -- Session type selector --------------------------------------------------
st.markdown("### Choose your session type \u2014 same process, different focus:")

# -- AI Journey: Readiness → Vision (connected pair) -----------------------
st.markdown(
    "<div style='background:rgba(6,182,212,0.06);border:1px solid rgba(6,182,212,0.15);"
    "border-radius:10px;padding:12px 18px;margin-bottom:12px;'>"
    "<span style='font-weight:600;color:#06B6D4;font-size:0.9em;'>"
    "\U0001f9ed AI Journey</span>"
    "<span style='color:#718096;font-size:0.85em;margin-left:8px;'>"
    "Start with Readiness, then Vision \u2014 a two-step journey to AI clarity</span>"
    "</div>",
    unsafe_allow_html=True,
)

j1, j_arrow, j2 = st.columns([5, 1, 5])

with j1:
    with st.container(border=True):
        st.markdown("#### \U0001f9e0 Step 1 \u2014 AI Readiness")
        st.markdown(
            "Where are we today? Assess your team\u2019s AI capability "
            "across 8 dimensions \u2014 honest answers build better plans."
        )
        st.caption("Use before any AI planning session")
        if "arr-interview" in _pages:
            st.page_link(_pages["arr-interview"], label="Start AI Readiness", use_container_width=True)

with j_arrow:
    st.markdown(
        "<div style='display:flex;align-items:center;justify-content:center;"
        "height:100%;min-height:120px;'>"
        "<div style='text-align:center;'>"
        "<div style='font-size:1.5em;color:#06B6D4;'>\u2192</div>"
        "<div style='font-size:0.7em;color:#718096;line-height:1.3;'>"
        "Start<br>here<br>then</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with j2:
    with st.container(border=True):
        st.markdown("#### \U0001f680 Step 2 \u2014 AI Vision Session")
        st.markdown(
            "Where are we going? Imagine what\u2019s possible \u2014 "
            "lighthouse opportunities, blockers, and the path forward."
        )
        st.caption("Use after completing AI Readiness")
        if "hfw-ai-vision" in _pages:
            st.page_link(_pages["hfw-ai-vision"], label="Start AI Vision", use_container_width=True)

st.markdown("")  # spacer

# -- Supply Chain Review (standalone, prominent) ----------------------------
m1, m2 = st.columns(2)

with m1:
    with st.container(border=True):
        st.markdown("#### \U0001f69b Supply Chain Review")
        st.markdown(
            "Our supply chain transformation starts with listening. "
            "Fill this in before every SC session \u2014 your input shapes the strategy."
        )
        st.caption("Use before every supply chain meeting")
        if "sc-interview" in _pages:
            st.page_link(_pages["sc-interview"], label="Start SC Review", use_container_width=True)

with m2:
    with st.container(border=True):
        st.markdown("#### \u26A1 Strategy Sprint")
        st.markdown(
            "Rapid alignment on what matters most \u2014 RAG status, "
            "decisions needed, risks, and next actions."
        )
        st.caption("Use when you need a decision made fast")
        if "hfw-strategy-sprint" in _pages:
            st.page_link(_pages["hfw-strategy-sprint"], label="Start Sprint", use_container_width=True)

# -- Dept One-Pager + Board Prep -------------------------------------------
m3, m4 = st.columns(2)

with m3:
    with st.container(border=True):
        st.markdown("#### \U0001f4cb Department One-Pager")
        st.markdown(
            "Your department at a glance \u2014 results, priorities, "
            "blockers, and asks. One page, one voice."
        )
        st.caption("Use before leadership reviews or town halls")
        if "hfw-dept-one-pager" in _pages:
            st.page_link(_pages["hfw-dept-one-pager"], label="Start One-Pager", use_container_width=True)

with m4:
    with st.container(border=True):
        st.markdown("#### \U0001f3db\ufe0f Board Prep")
        st.markdown(
            "Synthesise up to board level \u2014 highlights, metrics, "
            "decisions required, and risk register in one session."
        )
        st.caption("Use before every board meeting")
        if "hfw-board-prep" in _pages:
            st.page_link(_pages["hfw-board-prep"], label="Start Board Prep", use_container_width=True)

st.divider()

# -- SC Analysis link -------------------------------------------------------
with st.container(border=True):
    a_l, a_r = st.columns([3, 1])
    with a_l:
        st.markdown("#### \U0001f4ca Supply Chain Analysis")
        st.markdown(
            "Review aggregated interview responses, ADKAR scores, "
            "capability gaps, and key themes across all SC Review submissions."
        )
        st.caption("Read-only dashboard \u2014 the output of the Prepare \u2192 Synthesise pipeline")
    with a_r:
        if "sc-analysis" in _pages:
            st.page_link(_pages["sc-analysis"], label="View Analysis", use_container_width=True)

st.divider()

# -- Footer -----------------------------------------------------------------
st.markdown(
    "> *\"The best meetings don't just consume time \u2014 they create intelligence.\"*"
)

render_footer("Transformation", "AI-First Meeting Operating System", user=user)
