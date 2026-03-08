"""
Back of House — Landing Page
The engine room — how we build, govern, and maintain The Hub.
"""

import streamlit as st
from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})

render_header(
    "Back of House",
    "The engine room \u2014 how we build, govern, and maintain The Hub.",
    goals=[],
    strategy_context="Back of House",
)

st.markdown(
    "<div style='color:#1A1A1A;font-size:17px;'>"
    "Everything behind the curtain. Data quality, system configuration, "
    "build methodology, and team admin \u2014 the foundations that keep "
    "The Hub running.</div>",
    unsafe_allow_html=True,
)

st.divider()

# -- The Harris Farm Way (prominent, full-width) ------------------------------
with st.container(border=True):
    st.markdown(
        "<div style='font-size:32px;margin-bottom:4px;'>"
        "\U0001f9ed</div>",
        unsafe_allow_html=True,
    )
    st.markdown("#### The Harris Farm Way")
    st.markdown(
        "Our meeting operating system. Strategy Sprints, Department One-Pagers, "
        "and Board Prep \u2014 every session starts with preparation, every decision "
        "ends with an execution prompt, every voice is heard."
    )
    if "hfw-way-landing" in _pages:
        st.page_link(
            _pages["hfw-way-landing"],
            label="Open The Harris Farm Way",
            use_container_width=True,
        )

st.markdown("")

c1, c2 = st.columns(2)

with c1:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:32px;margin-bottom:4px;'>"
            "\U0001f4ca</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Master Data")
        st.markdown(
            "Where we validate, score and fix product data quality. "
            "PLUs, barcodes, pricing, hierarchy \u2014 the foundation "
            "everything else is built on."
        )
        if "mdhe-dashboard" in _pages:
            st.page_link(
                _pages["mdhe-dashboard"],
                label="Open Master Data",
                use_container_width=True,
            )

with c2:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:32px;margin-bottom:4px;'>"
            "\u2699\ufe0f</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### System & AI")
        st.markdown(
            "Connections, APIs, configuration and the infrastructure "
            "that keeps The Hub running."
        )
        if "workflow-engine" in _pages:
            st.page_link(
                _pages["workflow-engine"],
                label="Open System & AI",
                use_container_width=True,
            )

c3, c4 = st.columns(2)

with c3:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:32px;margin-bottom:4px;'>"
            "\u2705</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### How We Build")
        st.markdown(
            "The Rubric, WATCHDOG, approvals, and the methodology "
            "behind every decision we ship."
        )
        if "approvals" in _pages:
            st.page_link(
                _pages["approvals"],
                label="Open How We Build",
                use_container_width=True,
            )

with c4:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:32px;margin-bottom:4px;'>"
            "\U0001f465</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Admin")
        st.markdown(
            "User management, marketing assets, and operational tools "
            "for The Hub team."
        )
        if "user-management" in _pages:
            st.page_link(
                _pages["user-management"],
                label="Open Admin",
                use_container_width=True,
            )

# ---------------------------------------------------------------------------
# Transformation Test Mode toggle
# ---------------------------------------------------------------------------

st.divider()
with st.container(border=True):
    st.markdown("#### Transformation Test Mode")
    st.caption(
        "When enabled, transformation forms and analysis read/write "
        "to the test table instead of production."
    )
    _tm = st.toggle(
        "Enable Test Mode",
        value=st.session_state.get("transformation_test_mode", False),
        key="_boh_test_mode",
    )
    st.session_state["transformation_test_mode"] = _tm
    if _tm:
        st.info("Test mode is ON \u2014 transformation data goes to test table.")

render_footer("Back of House", "The Hub", user=user)
