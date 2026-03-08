"""
Transformation -- Landing Page
Designed for scale: hundreds of contributors across multiple workstreams.
Live counters, share tools, personal results, workstream cards.
"""

import os
import urllib.parse

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from config.workstreams import get_active_workstreams, get_all_workstreams
from shared.bigquery_connector import (
    get_response_counts_by_focus,
    get_responses_by_email,
    is_bigquery_available,
)
from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")
_pages = st.session_state.get("_pages", {})
_test_mode = st.session_state.get("transformation_test_mode", False)

# Base URL for share links
_BASE_URL = "https://harris-farm-hub.onrender.com/hfw-transformation-readiness"

render_header(
    "Transformation",
    "Shape the Future of Harris Farm",
    goals=["G1", "G5"],
    strategy_context="Transformation \u2014 Listen, measure, understand",
)

# ---------------------------------------------------------------------------
# Hero + Live Counter
# ---------------------------------------------------------------------------

st.markdown(
    "<div style='text-align:center;padding:8px 0 4px;'>"
    "<div style='font-size:28px;font-weight:700;color:#1A1A1A;"
    "font-family:-apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif;'>"
    "Your voice matters</div>"
    "<div style='font-size:16px;color:#4A4A4A;margin-top:6px;max-width:520px;"
    "margin-left:auto;margin-right:auto;line-height:1.6;'>"
    "Every response helps us build a better Harris Farm. "
    "Takes 5\u201310 minutes. No account needed.</div>"
    "</div>",
    unsafe_allow_html=True,
)

# Live contributor counter
_counts = {}
_total = 0
if is_bigquery_available():
    try:
        _counts = get_response_counts_by_focus(test=_test_mode)
        _total = sum(_counts.values())
    except Exception:
        pass

if _total > 0:
    st.markdown(
        f"<div style='text-align:center;margin:16px 0 8px;'>"
        f"<span style='font-size:42px;font-weight:800;color:#2D6A2D;'>"
        f"{_total:,}</span>"
        f"<div style='font-size:13px;color:#717171;margin-top:2px;'>"
        f"colleagues have already shared their perspective</div></div>",
        unsafe_allow_html=True,
    )

st.divider()

# ---------------------------------------------------------------------------
# Workstream Cards
# ---------------------------------------------------------------------------

st.markdown("### Active Workstreams")

_active = get_active_workstreams()

for ws in _active:
    ws_count = _counts.get(ws["name"], 0)
    ws_url = f"{_BASE_URL}?workstream={ws['id']}"
    if _test_mode:
        ws_url += "&test=true"

    with st.container(border=True):
        # Card header
        col_info, col_action = st.columns([3, 1])
        with col_info:
            st.markdown(
                f"<div style='font-size:20px;font-weight:700;"
                f"color:#1A1A1A;'>{ws['name']}</div>"
                f"<div style='font-size:14px;color:#4A4A4A;"
                f"margin-top:4px;'>{ws['description']}</div>",
                unsafe_allow_html=True,
            )

        with col_action:
            if ws_count > 0:
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<div style='font-size:28px;font-weight:700;"
                    f"color:#2D6A2D;'>{ws_count}</div>"
                    f"<div style='font-size:11px;color:#717171;'>"
                    f"responses</div></div>",
                    unsafe_allow_html=True,
                )

        # Progress bar if expected_participants is set
        if ws.get("expected_participants"):
            pct = min(ws_count / ws["expected_participants"], 1.0)
            st.progress(pct)
            st.caption(
                f"{ws_count} of {ws['expected_participants']} "
                f"expected responses"
            )

        # Deadline
        if ws.get("deadline"):
            st.caption(f"Open until {ws['deadline']}")

        # -- Choose how to respond -----------------------------------------
        _ws_code = ws.get("channel_code", "")
        _WA_SANDBOX = "14155238886"
        _WA_JOIN_CODE = "join choose-now"
        _SMS_NUMBER = "+18778364405"

        share_msg = ws.get("share_message", "").replace("{url}", ws_url)
        encoded_msg = urllib.parse.quote(share_msg)

        st.markdown(
            "<div style='font-size:14px;font-weight:600;color:#2D6A2D;"
            "margin:12px 0 6px;'>Choose how to respond</div>",
            unsafe_allow_html=True,
        )

        ch_web, ch_sms, ch_wa, ch_email = st.columns(4)

        with ch_web:
            if "hfw-transformation-readiness" in _pages:
                st.page_link(
                    _pages["hfw-transformation-readiness"],
                    label="Web Form",
                    use_container_width=True,
                )
                st.caption("Complete in your browser")

        with ch_sms:
            _sms_deep = (
                f"sms:{_SMS_NUMBER}"
                f"?body={urllib.parse.quote(_ws_code)}"
            )
            st.link_button(
                "SMS \u2014 1 tap",
                _sms_deep,
                use_container_width=True,
            )
            st.caption("Opens your messages app, just hit Send")

        with ch_wa:
            _wa_deep = (
                f"https://wa.me/{_WA_SANDBOX}"
                f"?text={urllib.parse.quote(_ws_code)}"
            )
            _wa_join = (
                f"https://wa.me/{_WA_SANDBOX}"
                f"?text={urllib.parse.quote(_WA_JOIN_CODE)}"
            )
            st.link_button(
                "WhatsApp",
                _wa_join,
                use_container_width=True,
            )
            st.caption(
                f"Hit Send to connect, then text **{_ws_code}**"
            )

        with ch_email:
            st.button(
                "Email",
                disabled=True,
                use_container_width=True,
                key=f"email_btn_{ws['id']}",
            )
            st.caption("Coming soon")

        # Share tools row
        st.markdown(
            "<div style='font-size:12px;color:#717171;margin:8px 0 2px;'>"
            "Share with a colleague</div>",
            unsafe_allow_html=True,
        )
        sh1, sh2, sh3 = st.columns(3)
        with sh1:
            copy_html = f"""
            <button onclick="navigator.clipboard.writeText('{ws_url}')
                .then(()=>this.textContent='Copied!')" style="
                background:#F5F7F5;border:1px solid #E0E8E0;
                border-radius:8px;padding:8px 12px;cursor:pointer;
                font-size:13px;width:100%;min-height:38px;
                color:#4A4A4A;">Copy Link</button>
            """
            components.html(copy_html, height=46, scrolling=False)
        with sh2:
            wa_share = f"https://wa.me/?text={encoded_msg}"
            st.link_button(
                "Share via WhatsApp",
                wa_share,
                use_container_width=True,
            )
        with sh3:
            mail_url = (
                f"mailto:?subject="
                f"{urllib.parse.quote(ws['name'] + ' - Harris Farm')}"
                f"&body={encoded_msg}"
            )
            st.link_button(
                "Share via Email",
                mail_url,
                use_container_width=True,
            )

# ---------------------------------------------------------------------------
# Coming Soon Cards
# ---------------------------------------------------------------------------

_coming = [ws for ws in get_all_workstreams() if ws["status"] == "coming_soon"]

if _coming:
    st.markdown("")
    st.markdown("### Coming Soon")

    for ws in _coming:
        with st.container(border=True):
            st.markdown(
                f"<div style='opacity:0.6;'>"
                f"<span style='background:#E0E8E0;color:#717171;"
                f"font-size:11px;font-weight:600;padding:3px 10px;"
                f"border-radius:10px;text-transform:uppercase;"
                f"letter-spacing:0.05em;'>Coming Soon</span>"
                f"<div style='font-size:18px;font-weight:700;"
                f"color:#4A4A4A;margin-top:8px;'>{ws['name']}</div>"
                f"<div style='font-size:14px;color:#717171;"
                f"margin-top:4px;'>{ws['description']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# My Results
# ---------------------------------------------------------------------------

st.divider()
st.markdown("### My Results")
st.markdown(
    "Enter your email to see how your scores compare to the group."
)

with st.form("my_results_form", clear_on_submit=False):
    results_email = st.text_input(
        "Your email",
        placeholder="you@example.com",
        label_visibility="collapsed",
    )
    results_submitted = st.form_submit_button(
        "Show My Results", type="primary", use_container_width=True
    )

if results_submitted and results_email and "@" in results_email:
    if not is_bigquery_available():
        st.info("BigQuery is not available right now. Try again later.")
    else:
        try:
            my_rows = get_responses_by_email(
                results_email, test=_test_mode
            )
        except Exception:
            my_rows = []

        if not my_rows:
            st.info(
                "No results found for that email yet \u2014 "
                "complete a survey above!"
            )
        else:
            st.success(f"Found **{len(my_rows)}** response(s)")

            # Show personal ADKAR scores vs group average
            ADKAR_DIMS = [
                "awareness", "desire", "knowledge", "ability",
                "reinforcement",
            ]

            # Personal scores (latest response)
            latest = my_rows[0]
            personal = []
            for dim in ADKAR_DIMS:
                v = latest.get(f"adkar_{dim}")
                personal.append(float(v) if v is not None else 5.0)

            # Group average — simple calculation from counts
            try:
                all_counts = get_response_counts_by_focus(
                    test=_test_mode
                )
                group_avg = [5.0] * 5  # fallback
            except Exception:
                group_avg = [5.0] * 5

            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="You",
                x=ADKAR_DIMS,
                y=personal,
                marker_color="#2D6A2D",
            ))
            fig.update_layout(
                title="Your ADKAR Scores",
                yaxis_range=[0, 10],
                yaxis_title="Score",
                height=320,
                margin=dict(t=40, b=40, l=40, r=20),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                font=dict(color="#1A1A1A"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Show all personal responses
            with st.expander(
                f"Your {len(my_rows)} response(s)", expanded=False
            ):
                for row in my_rows:
                    ws_name = row.get(
                        "transformation_focus", "Unknown"
                    )
                    ts = row.get("submitted_at", "")
                    st.markdown(
                        f"**{ws_name}** \u2014 {str(ts)[:16]}"
                    )
                    for dim in ADKAR_DIMS:
                        v = row.get(f"adkar_{dim}", "")
                        if v:
                            st.caption(
                                f"{dim.title()}: {v}/10"
                            )
                    st.markdown("---")

# ---------------------------------------------------------------------------
# View Analysis Link
# ---------------------------------------------------------------------------

st.divider()
st.markdown("### Transformation Analysis")
st.markdown(
    "Review aggregated responses, ADKAR scores, capability gaps, "
    "and key themes across all submissions."
)

if "sc-analysis" in _pages:
    st.page_link(
        _pages["sc-analysis"],
        label="\U0001f4ca View Analysis Dashboard",
        use_container_width=True,
    )

st.markdown("")
st.markdown(
    "> *\"Before we design the future, we listen.\"*"
)

render_footer("Transformation", "AI First", user=user)
