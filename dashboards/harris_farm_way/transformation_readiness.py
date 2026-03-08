"""
Transformation -- Transformation Readiness Interview
Where are we today -- and where are we going?
ADKAR-structured diagnostic. Native Streamlit -- no iframe.
"""

import json
import uuid
import logging
from typing import Optional

import requests
import streamlit as st
import streamlit.components.v1 as components
from shared.styles import render_header, render_footer
from config.workstreams import get_workstream_by_id, get_active_workstreams

_log = logging.getLogger(__name__)
user = st.session_state.get("auth_user")

# ---------------------------------------------------------------------------
# URL param pre-loading + test mode detection
# ---------------------------------------------------------------------------

_ws_param = st.query_params.get("workstream", "")
_test_mode = st.query_params.get("test", "") == "true"
_preloaded_ws = get_workstream_by_id(_ws_param) if _ws_param else None

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_SUBMIT_URL = (
    "https://australia-southeast1-oval-blend-488902-p2"
    ".cloudfunctions.net/hfm-scr-insert"
)
_API_KEY = "hfm-scr-2026"

from shared.survey_config import (
    SECTIONS as _SECTIONS,
    DEPARTMENTS as _DEPARTMENTS,
    ROLE_LEVELS as _ROLE_LEVELS,
    score_label as _score_label_fn,
)

_STEP_LABELS = (
    ["Welcome"]
    + [s["label"] for s in _SECTIONS]
    + ["Review & Submit"]
)
_N_STEPS = len(_STEP_LABELS)

# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

_SK = "_tr"  # session-state key prefix


def _k(field):
    """Session-state key for a form field."""
    return f"{_SK}_{field}"


def _val(field, default=""):
    return st.session_state.get(_k(field), default)


def _score_label(v):
    return _score_label_fn(v)


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

render_header(
    "Transformation Readiness",
    "Where are we today \u2014 and where are we going?",
    goals=["G3", "G5"],
    strategy_context="Transformation \u2014 ADKAR Readiness & Vision",
)

# ---------------------------------------------------------------------------
# Mobile-first CSS
# ---------------------------------------------------------------------------

st.markdown(
    """<style>
    /* Mobile touch targets */
    div[data-testid="stFormSubmitButton"] button,
    div.stButton > button {
        min-height: 44px !important;
        font-size: 16px !important;
    }
    /* Prevent iOS zoom on input focus */
    input, textarea, select {
        font-size: 16px !important;
    }
    /* No horizontal scroll */
    .main .block-container {
        max-width: 100% !important;
        overflow-x: hidden !important;
    }
    /* Responsive stepper — vertical on narrow screens */
    @media (max-width: 768px) {
        .tr-stepper {
            flex-direction: column !important;
            align-items: stretch !important;
        }
        .tr-stepper span {
            display: block !important;
            text-align: center !important;
            margin: 2px 0 !important;
        }
    }
    </style>""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Test mode banner
# ---------------------------------------------------------------------------

if _test_mode:
    st.markdown(
        "<div style='background:#FEF3C7;border:2px solid #F59E0B;"
        "border-radius:8px;padding:10px 16px;margin-bottom:12px;"
        "text-align:center;font-weight:600;color:#92400E;'>"
        "TEST MODE \u2014 responses go to the test table, not production"
        "</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Workstream info header (when loaded via URL)
# ---------------------------------------------------------------------------

if _preloaded_ws:
    st.markdown(
        f"<div style='border:2px solid #2D6A2D;border-radius:12px;"
        f"padding:16px 20px;margin-bottom:16px;"
        f"background:rgba(45,106,45,0.04);'>"
        f"<div style='font-size:18px;font-weight:700;color:#2D6A2D;'>"
        f"{_preloaded_ws['name']}</div>"
        f"<div style='font-size:14px;color:#4A4A4A;margin-top:4px;'>"
        f"{_preloaded_ws['description']}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

# Init step
if _k("step") not in st.session_state:
    st.session_state[_k("step")] = 0
if _k("submitted") not in st.session_state:
    st.session_state[_k("submitted")] = False

step = st.session_state[_k("step")]

# ---------------------------------------------------------------------------
# Stepper bar
# ---------------------------------------------------------------------------

_pills = []
for i, label in enumerate(_STEP_LABELS):
    if i == step:
        _pills.append(
            f"<span style='display:inline-block;background:#2D6A2D;"
            f"color:#FFFFFF;font-weight:700;padding:7px 16px;"
            f"border-radius:20px;font-size:13px;margin:3px 2px;"
            f"box-shadow:0 2px 6px rgba(45,106,45,0.25);'>"
            f"{i + 1}. {label}</span>"
        )
    elif i < step:
        _pills.append(
            f"<span style='display:inline-block;"
            f"background:rgba(45,106,45,0.08);color:#2D6A2D;"
            f"font-weight:600;padding:6px 14px;border-radius:20px;"
            f"font-size:12px;margin:3px 2px;"
            f"border:1px solid rgba(45,106,45,0.15);'>"
            f"\u2713 {label}</span>"
        )
    else:
        _pills.append(
            f"<span style='display:inline-block;"
            f"background:rgba(0,0,0,0.02);color:#717171;"
            f"font-weight:400;padding:6px 14px;border-radius:20px;"
            f"font-size:12px;margin:3px 2px;"
            f"border:1px solid rgba(0,0,0,0.04);'>"
            f"{i + 1}. {label}</span>"
        )

st.markdown(
    "<div class='tr-stepper' style='text-align:center;margin:4px 0 8px;"
    "display:flex;flex-wrap:wrap;justify-content:center;gap:2px;'>"
    + "".join(_pills) + "</div>",
    unsafe_allow_html=True,
)

# Progress bar
progress_pct = int(((step + 1) / _N_STEPS) * 100)
st.progress((step + 1) / _N_STEPS)
st.caption(f"{progress_pct}% complete")

st.markdown("")

# ---------------------------------------------------------------------------
# Thank-you screen
# ---------------------------------------------------------------------------

if st.session_state[_k("submitted")]:
    st.balloons()
    with st.container(border=True):
        st.markdown(
            "<div style='text-align:center;padding:20px 0;'>"
            "<div style='font-size:48px;margin-bottom:8px;'>"
            "\U0001f34e</div>"
            "<div style='font-size:24px;font-weight:700;color:#2D6A2D;"
            "font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif;margin-bottom:8px;'>"
            f"Thank you{', ' + _val('name') if _val('name') else ''}."
            "</div>"
            "<div style='color:#1A1A1A;font-size:15px;'>"
            "Your voice is shaping our future.</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    # Summary
    st.markdown("")
    st.markdown("#### Your responses")
    for sec in _SECTIONS:
        for card in sec["cards"]:
            for f in card["fields"]:
                v = _val(f["key"])
                if not v:
                    continue
                if f["type"] == "slider":
                    label_txt, label_color = _score_label(int(v))
                    st.markdown(
                        f"**{f['label']}:** "
                        f"<span style='color:{label_color};"
                        f"font-weight:700;'>{v}/10 ({label_txt})</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(f"**{f['label']}**")
                    st.markdown(f"> {v}")

    st.divider()
    if st.button("Start a new response"):
        for key in list(st.session_state.keys()):
            if key.startswith(_SK):
                del st.session_state[key]
        st.rerun()

    render_footer("Transformation Readiness", "Transformation", user=user)
    st.stop()


# ---------------------------------------------------------------------------
# Step 0: Welcome
# ---------------------------------------------------------------------------

if step == 0:
    # Generate session_id for auto-save
    if _k("session_id") not in st.session_state:
        st.session_state[_k("session_id")] = str(uuid.uuid4())[:8]

    # Pre-load workstream into transformation_type if from URL
    if _preloaded_ws and not _val("transformation_type"):
        st.session_state[_k("transformation_type")] = _preloaded_ws["name"]
        st.session_state[_k("initiative_name")] = _preloaded_ws["name"]
        st.session_state[_k("workstream_id")] = _preloaded_ws["id"]

    with st.container(border=True):
        st.markdown(
            "<div style='border-top:3px solid #2D6A2D;"
            "border-radius:3px 3px 0 0;margin:-20px -20px 16px;"
            "padding:0;'></div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### \U0001f33f About You")
        st.markdown(
            "This takes **5\u201310 minutes**. Your honest answers "
            "shape Harris Farm\u2019s transformation. "
            "Every voice counts equally."
        )
        st.markdown("")

        st.text_input(
            "First name *",
            placeholder="Your first name",
            key=_k("name"),
        )
        st.text_input(
            "Your email (so we can share your personal results)",
            placeholder="you@example.com",
            key=_k("email"),
            help="We\u2019ll never spam you \u2014 this is just so we can "
                 "show you how your scores compare to the group.",
        )
        email_val = _val("email")
        if email_val and "@" not in email_val:
            st.warning("Please enter a valid email address.")

        st.selectbox(
            "Department *",
            options=[""] + _DEPARTMENTS,
            format_func=lambda x: "Select your department" if x == "" else x,
            key=_k("department"),
        )
        st.selectbox(
            "Role level *",
            options=[""] + _ROLE_LEVELS,
            format_func=lambda x: "Select your role level" if x == "" else x,
            key=_k("role_level"),
        )

        # Workstream / transformation type
        _ws_locked = _preloaded_ws is not None
        if _ws_locked:
            # Show locked workstream name
            st.text_input(
                "Workstream",
                value=_preloaded_ws["name"],
                disabled=True,
                key=_k("transformation_type_display"),
            )
        else:
            # Build options from active workstreams + Other
            _ws_options = [ws["name"] for ws in get_active_workstreams()]
            if "Other" not in _ws_options:
                _ws_options.append("Other")
            st.selectbox(
                "What transformation are you reflecting on today? *",
                options=[""] + _ws_options,
                format_func=lambda x: (
                    "Select transformation" if x == "" else x
                ),
                key=_k("transformation_type"),
            )
        if _val("transformation_type") == "Other":
            st.text_input(
                "Describe the transformation",
                placeholder="What transformation are you reflecting on?",
                key=_k("transformation_other"),
            )

        st.text_input(
            "What initiative are you reflecting on?",
            placeholder="e.g. Supply Chain of the Future, AI First Rollout",
            key=_k("initiative_name"),
            help="Optional \u2014 groups your response with others on the same initiative.",
        )


# ---------------------------------------------------------------------------
# Steps 1-5: ADKAR sections
# ---------------------------------------------------------------------------

elif 1 <= step <= len(_SECTIONS):
    sec = _SECTIONS[step - 1]

    # Section intro
    st.markdown(
        f"<div style='text-align:center;color:#1A1A1A;"
        f"font-style:italic;margin-bottom:16px;'>"
        f"{sec['question']}</div>",
        unsafe_allow_html=True,
    )

    for card in sec["cards"]:
        with st.container(border=True):
            # Colored accent bar
            st.markdown(
                f"<div style='border-top:3px solid {sec['color']};"
                f"border-radius:3px 3px 0 0;margin:-20px -20px 16px;"
                f"padding:0;'></div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"#### {card['icon']} {card['title']}")

            for f in card["fields"]:
                if f["type"] == "slider":
                    val = st.slider(
                        f["label"],
                        min_value=1,
                        max_value=10,
                        value=int(_val(f["key"], 5)),
                        key=_k(f["key"]),
                        help=f.get("help", ""),
                    )
                    label_txt, label_color = _score_label(val)
                    st.markdown(
                        f"<span style='font-size:24px;font-weight:700;"
                        f"color:{label_color};'>{val}/10</span>"
                        f" <span style='font-size:13px;color:{label_color};"
                        f"font-weight:600;'>{label_txt}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.text_area(
                        f["label"],
                        height=f.get("rows", 3) * 32,
                        placeholder="Share your thoughts\u2026",
                        key=_k(f["key"]),
                        help=f.get("help", ""),
                    )


# ---------------------------------------------------------------------------
# Step 6: Review & Submit
# ---------------------------------------------------------------------------

else:
    # Scores summary
    _slider_fields = []
    for sec in _SECTIONS:
        for card in sec["cards"]:
            for f in card["fields"]:
                if f["type"] == "slider":
                    v = int(_val(f["key"], 5))
                    _slider_fields.append((sec["label"], f["label"], v))

    if _slider_fields:
        avg = sum(v for _, _, v in _slider_fields) / len(_slider_fields)
        avg_label, avg_color = _score_label(avg)

        st.markdown(
            f"<div style='text-align:center;background:rgba(45,106,45,0.06);"
            f"border-radius:12px;padding:28px 20px;margin-bottom:20px;"
            f"border:1px solid rgba(45,106,45,0.12);'>"
            f"<div style='font-size:45px;font-weight:800;color:{avg_color};"
            f"font-family:-apple-system, BlinkMacSystemFont, sans-serif;'>{avg:.1f}</div>"
            f"<div style='font-size:12px;color:#717171;text-transform:uppercase;"
            f"letter-spacing:0.08em;margin-top:4px;'>Overall Average</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        cols = st.columns(len(_slider_fields))
        for col, (sec_name, q_label, val) in zip(cols, _slider_fields):
            lbl, clr = _score_label(val)
            with col:
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<div style='font-size:24px;font-weight:700;"
                    f"color:{clr};'>{val}</div>"
                    f"<div style='font-size:12px;color:#717171;'>"
                    f"{sec_name}</div></div>",
                    unsafe_allow_html=True,
                )

    st.divider()

    # Text responses
    st.markdown("#### Your responses")
    for sec in _SECTIONS:
        for card in sec["cards"]:
            for f in card["fields"]:
                if f["type"] == "text":
                    v = _val(f["key"])
                    if v:
                        st.markdown(f"**{f['label']}**")
                        st.markdown(f"> {v}")
                        st.markdown("")

    st.divider()

    # Submit
    with st.container(border=True):
        st.markdown(
            "<div style='border-top:3px solid #2D6A2D;"
            "border-radius:3px 3px 0 0;margin:-20px -20px 16px;"
            "padding:0;'></div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### \U0001f680 Ready to Submit")
        st.markdown(
            "Your response will be saved to our transformation "
            "database. Every voice shapes what comes next."
        )

        _welcome_valid = (
            _val("name").strip()
            and _val("email").strip()
            and "@" in _val("email")
            and _val("department")
            and _val("role_level")
        )

        if not _welcome_valid:
            st.warning(
                "Please complete all required fields in the Welcome "
                "section before submitting."
            )

        if st.button(
            "\U0001f33f Submit Response",
            type="primary",
            use_container_width=True,
            disabled=not _welcome_valid,
        ):
            # Build flat payload for hfm-scr-insert
            if _preloaded_ws:
                tt = _preloaded_ws["name"]
            else:
                tt = _val("transformation_type", "")
                if tt == "Other":
                    tt = _val("transformation_other", "Other")

            email_val = _val("email")
            if _test_mode and "+test" not in email_val:
                at_pos = email_val.find("@")
                if at_pos > 0:
                    email_val = (
                        email_val[:at_pos] + "+test" + email_val[at_pos:]
                    )

            payload = {
                "meeting_type": "TRANSFORMATION_READINESS",
                # Required by hfm-scr-insert validation
                "name": _val("name"),
                "role": _val("role_level"),
                # New ADKAR fields
                "first_name": _val("name"),
                "email": email_val,
                "department": _val("department"),
                "role_level": _val("role_level"),
                "initiative_name": _val("initiative_name") or "",
                "transformation_focus": tt,
                "session_id": _val("session_id", ""),
                # ADKAR integer scores
                "adkar_awareness": int(_val("awareness_score", 5)),
                "adkar_desire": int(_val("desire_score", 5)),
                "adkar_knowledge": int(_val("knowledge_score", 5)),
                "adkar_ability": int(_val("capability_score", 5)),
                "adkar_reinforcement": int(
                    _val("reinforcement_score", 5)
                ),
                # ADKAR text responses
                "adkar_awareness_text": _val("why_transform"),
                "adkar_desire_text": _val("desire_driver"),
                "adkar_knowledge_text": _val("twelve_month_picture"),
                "adkar_ability_text": _val("biggest_gap"),
                "adkar_reinforcement_text": _val(
                    "confidence_lasting"
                ),
                # Additional text
                "lighthouse_vision": _val("lighthouse"),
                "biggest_blocker": _val("biggest_gap"),
                "unlock_value": _val("need_from_leadership"),
            }

            try:
                sep = "?" if "?" not in _SUBMIT_URL else "&"
                url = f"{_SUBMIT_URL}{sep}api_key={_API_KEY}"
                if _test_mode:
                    url += "&test=true"
                resp = requests.post(
                    url,
                    json=payload,
                    timeout=15,
                )
                if resp.ok:
                    st.session_state[_k("submitted")] = True
                    st.rerun()
                else:
                    st.error(
                        f"Submission failed: {resp.status_code} "
                        f"\u2014 {resp.text[:200]}"
                    )
            except Exception as e:
                st.error(f"Submission error: {e}")
                _log.exception("TR submit failed")

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

st.markdown("")

if step == _N_STEPS - 1:
    # Summary page — only Back
    if st.button("\u2190 Back to edit", use_container_width=False):
        st.session_state[_k("step")] = step - 1
        st.rerun()
else:
    c1, c2 = st.columns(2)
    with c1:
        if step > 0:
            if st.button("\u2190 Back", use_container_width=True):
                st.session_state[_k("step")] = step - 1
                st.rerun()
    with c2:
        # Validate welcome before allowing Next
        if step == 0:
            _can_next = (
                _val("name").strip()
                and _val("email").strip()
                and "@" in _val("email")
                and _val("department")
                and _val("role_level")
            )
        else:
            _can_next = True

        if st.button(
            "Next \u2192",
            type="primary",
            use_container_width=True,
            disabled=not _can_next,
        ):
            st.session_state[_k("step")] = step + 1
            st.rerun()

# ---------------------------------------------------------------------------
# Auto-save progress via localStorage
# ---------------------------------------------------------------------------

_autosave_html = """
<script>
(function() {
    const KEY = 'hfm_tr_progress';
    // Restore is handled by Streamlit session state;
    // this just provides a backup indicator for the user.
    const saved = localStorage.getItem(KEY);
    if (saved) {
        try {
            const data = JSON.parse(saved);
            const mins = Math.round((Date.now() - data.ts) / 60000);
            if (mins < 120) {
                // Recent save exists — no action needed, session state handles it
            }
        } catch(e) {}
    }
    // Save current step on every render
    localStorage.setItem(KEY, JSON.stringify({ts: Date.now(), active: true}));
})();
</script>
"""
components.html(_autosave_html, height=0, scrolling=False)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
render_footer("Transformation Readiness", "Transformation", user=user)
