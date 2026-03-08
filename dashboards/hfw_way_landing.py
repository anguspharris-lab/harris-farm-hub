"""
The Harris Farm Way — Landing Page
The meeting operating system. A manifesto, not a menu item.
"""

import streamlit as st
from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})

render_header(
    "The Harris Farm Way",
    "This is the new way.",
    goals=["G1", "G5"],
    strategy_context="The Harris Farm Way \u2014 How we meet, decide, and move",
)

# -- Hero manifesto ----------------------------------------------------------
st.markdown(
    "<div style='font-size:18px;line-height:1.7;color:#1A1A1A;"
    "max-width:640px;margin-bottom:24px;'>"
    "We used to spend meetings debating the past.<br>"
    "Now we design the future.<br><br>"
    "Every session starts with preparation. Every decision "
    "ends with an execution prompt. Every voice is heard.<br><br>"
    "<strong style='color:#2D6A2D;'>This is how Harris Farm moves fast.</strong>"
    "</div>",
    unsafe_allow_html=True,
)

st.divider()

# -- Three session types ------------------------------------------------------
st.markdown("### Choose your session")

c1, c2, c3 = st.columns(3)

with c1:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:32px;margin-bottom:4px;'>"
            "\u26a1</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Strategy Sprint")
        st.markdown(
            "When you need a decision made fast. "
            "Time-boxed. Data-backed. Action out the other side."
        )
        if "hfw-strategy-sprint" in _pages:
            st.page_link(
                _pages["hfw-strategy-sprint"],
                label="Start Sprint",
                use_container_width=True,
            )

with c2:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:32px;margin-bottom:4px;'>"
            "\U0001f4cb</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Department One-Pager")
        st.markdown(
            "Your department\u2019s voice before every leadership review. "
            "Results, priorities, blockers, and asks."
        )
        if "hfw-dept-one-pager" in _pages:
            st.page_link(
                _pages["hfw-dept-one-pager"],
                label="Start One-Pager",
                use_container_width=True,
            )

with c3:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:32px;margin-bottom:4px;'>"
            "\U0001f3db\ufe0f</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Board Prep")
        st.markdown(
            "Everything the board needs in one session. "
            "Highlights, metrics, decisions, and risk register."
        )
        if "hfw-board-prep" in _pages:
            st.page_link(
                _pages["hfw-board-prep"],
                label="Start Board Prep",
                use_container_width=True,
            )

st.divider()

st.markdown(
    "<div style='background:rgba(45,106,45,0.08);border-radius:10px;"
    "padding:24px 28px;text-align:center;'>"
    "<div style='font-size:21px;font-weight:700;color:#2D6A2D;"
    "margin-bottom:6px;'>Come prepared or don\u2019t come.</div>"
    "<div style='font-size:15px;color:#1A1A1A;'>"
    "The best meetings don\u2019t just consume time "
    "\u2014 they create intelligence.</div>"
    "</div>",
    unsafe_allow_html=True,
)

render_footer("The Harris Farm Way", "Back of House", user=user)
