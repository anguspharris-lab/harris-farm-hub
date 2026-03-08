"""
Harris Farm Way -- Department One-Pager
Your department at a glance — results, priorities, blockers, asks.
Native Streamlit — no iframe.
"""

import json
import logging

import requests
import streamlit as st
from shared.styles import render_header, render_footer

_log = logging.getLogger(__name__)
user = st.session_state.get("auth_user")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_SUBMIT_URL = (
    "https://australia-southeast1-oval-blend-488902-p2"
    ".cloudfunctions.net/hfm-meeting-os-insert"
)
_API_KEY = "hfm-mos-2026"

_SECTIONS = [
    {
        "key": "results",
        "label": "Results & Highlights",
        "icon": "\U0001f3c6",
        "color": "#0891B2",
        "question": "How did we go this period?",
        "cards": [
            {
                "title": "Performance",
                "icon": "\U0001f4ca",
                "fields": [
                    {
                        "key": "performance_rating",
                        "type": "slider",
                        "label": "Overall Performance (1=Poor, 10=Excellent)",
                        "help": "How would you rate your department\u2019s performance?",
                    },
                    {
                        "key": "top_highlight",
                        "type": "text",
                        "label": "Top Highlight",
                        "help": "The one thing you\u2019re most proud of this period.",
                        "rows": 3,
                    },
                    {
                        "key": "key_metrics",
                        "type": "text",
                        "label": "Key Metrics",
                        "help": "2\u20133 numbers that tell the story of your department.",
                        "rows": 3,
                    },
                ],
            },
        ],
    },
    {
        "key": "priorities",
        "label": "Priorities & Blockers",
        "icon": "\U0001f3af",
        "color": "#2D6A2D",
        "question": "What\u2019s next and what\u2019s in the way?",
        "cards": [
            {
                "title": "Looking Ahead",
                "icon": "\U0001f680",
                "fields": [
                    {
                        "key": "top_3_priorities",
                        "type": "text",
                        "label": "Top 3 Priorities",
                        "help": "The three most important things for the next period.",
                        "rows": 4,
                    },
                    {
                        "key": "blockers",
                        "type": "text",
                        "label": "Blockers & Asks",
                        "help": "What do you need from other departments or leadership to succeed?",
                        "rows": 3,
                    },
                ],
            },
        ],
    },
]

_STEP_LABELS = (
    ["Welcome"]
    + [s["label"] for s in _SECTIONS]
    + ["Review & Submit"]
)
_N_STEPS = len(_STEP_LABELS)

# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

_SK = "_dop"  # session-state key prefix


def _k(field):
    return f"{_SK}_{field}"


def _val(field, default=""):
    return st.session_state.get(_k(field), default)


def _score_label(v):
    if v >= 8:
        return "Excellent", "#2D6A2D"
    if v >= 6:
        return "Good", "#0891B2"
    if v >= 4:
        return "Fair", "#C8971F"
    return "Needs Work", "#C0392B"


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

render_header(
    "Department One-Pager",
    "Your department at a glance \u2014 what matters, what\u2019s working, what needs help",
    goals=["G1"],
    strategy_context="The Harris Farm Way \u2014 Department One-Pager",
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
            f"<span style='display:inline-block;background:#0891B2;"
            f"color:#FFFFFF;font-weight:700;padding:7px 16px;"
            f"border-radius:20px;font-size:13px;margin:3px 2px;"
            f"box-shadow:0 2px 6px rgba(8,145,178,0.25);'>"
            f"{i + 1}. {label}</span>"
        )
    elif i < step:
        _pills.append(
            f"<span style='display:inline-block;"
            f"background:rgba(8,145,178,0.08);color:#0891B2;"
            f"font-weight:600;padding:6px 14px;border-radius:20px;"
            f"font-size:12px;margin:3px 2px;"
            f"border:1px solid rgba(8,145,178,0.15);'>"
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
    "<div style='text-align:center;margin:4px 0 8px;'>"
    + "".join(_pills) + "</div>",
    unsafe_allow_html=True,
)

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
            "\U0001f4cb</div>"
            "<div style='font-size:24px;font-weight:700;color:#0891B2;"
            "font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif;margin-bottom:8px;'>"
            f"Thank you{', ' + _val('name') if _val('name') else ''}."
            "</div>"
            "<div style='color:#1A1A1A;font-size:15px;'>"
            "Your department snapshot is captured.</div>"
            "</div>",
            unsafe_allow_html=True,
        )

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

    render_footer("Dept One-Pager", "The Harris Farm Way", user=user)
    st.stop()


# ---------------------------------------------------------------------------
# Step 0: Welcome
# ---------------------------------------------------------------------------

if step == 0:
    with st.container(border=True):
        st.markdown(
            "<div style='border-top:3px solid #0891B2;"
            "border-radius:3px 3px 0 0;margin:-20px -20px 16px;"
            "padding:0;'></div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### \U0001f4cb About You")
        st.markdown(
            "Quick and focused \u2014 capture the state of your "
            "department in **5 minutes**."
        )
        st.markdown("")

        st.text_input(
            "Full Name *",
            placeholder="Your full name",
            key=_k("name"),
        )
        st.text_input(
            "Email *",
            placeholder="you@harrisfarm.com.au",
            key=_k("email"),
        )
        email_val = _val("email")
        if (
            email_val
            and "@" in email_val
            and not email_val.endswith("@harrisfarm.com.au")
        ):
            st.error("Only @harrisfarm.com.au email addresses are accepted.")

        st.text_input(
            "Role / Title *",
            placeholder="e.g. Department Head, Team Lead",
            key=_k("role"),
        )
        st.text_input(
            "Department *",
            placeholder="e.g. Buying, Operations, Supply Chain",
            key=_k("department"),
        )


# ---------------------------------------------------------------------------
# Steps 1-2: Sections
# ---------------------------------------------------------------------------

elif 1 <= step <= len(_SECTIONS):
    sec = _SECTIONS[step - 1]

    st.markdown(
        f"<div style='text-align:center;color:#1A1A1A;"
        f"font-style:italic;margin-bottom:16px;'>"
        f"{sec['question']}</div>",
        unsafe_allow_html=True,
    )

    for card in sec["cards"]:
        with st.container(border=True):
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
# Final step: Review & Submit
# ---------------------------------------------------------------------------

else:
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
            f"<div style='text-align:center;background:rgba(8,145,178,0.06);"
            f"border-radius:12px;padding:28px 20px;margin-bottom:20px;"
            f"border:1px solid rgba(8,145,178,0.12);'>"
            f"<div style='font-size:45px;font-weight:800;color:{avg_color};"
            f"font-family:-apple-system, BlinkMacSystemFont, sans-serif;'>{avg:.1f}</div>"
            f"<div style='font-size:12px;color:#717171;text-transform:uppercase;"
            f"letter-spacing:0.08em;margin-top:4px;'>Overall Performance</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.divider()

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

    with st.container(border=True):
        st.markdown(
            "<div style='border-top:3px solid #0891B2;"
            "border-radius:3px 3px 0 0;margin:-20px -20px 16px;"
            "padding:0;'></div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### \U0001f680 Ready to Submit")
        st.markdown(
            "Your department one-pager will be saved. "
            "Clear, honest snapshots build a stronger business."
        )

        _welcome_valid = (
            _val("name").strip()
            and _val("email").endswith("@harrisfarm.com.au")
            and _val("role").strip()
            and _val("department").strip()
        )

        if not _welcome_valid:
            st.warning(
                "Please complete all required fields in the Welcome "
                "section before submitting."
            )

        if st.button(
            "\U0001f4cb Submit One-Pager",
            type="primary",
            use_container_width=True,
            disabled=not _welcome_valid,
        ):
            responses = {}
            scores = {}
            for sec in _SECTIONS:
                for card in sec["cards"]:
                    for f in card["fields"]:
                        v = _val(f["key"])
                        if f["type"] == "slider":
                            scores[f["key"]] = int(v) if v else 5
                        else:
                            responses[f["key"]] = v or ""

            payload = {
                "meeting_type": "DEPT_ONE_PAGER",
                "email": _val("email"),
                "name": _val("name"),
                "role": _val("role"),
                "department": _val("department"),
                "responses_json": json.dumps(responses),
                "scores_json": json.dumps(scores),
            }

            try:
                sep = "?" if "?" not in _SUBMIT_URL else "&"
                url = f"{_SUBMIT_URL}{sep}api_key={_API_KEY}"
                resp = requests.post(url, json=payload, timeout=15)
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
                _log.exception("DOP submit failed")

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

st.markdown("")

if step == _N_STEPS - 1:
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
        if step == 0:
            _can_next = (
                _val("name").strip()
                and _val("email").endswith("@harrisfarm.com.au")
                and _val("role").strip()
                and _val("department").strip()
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
# Footer
# ---------------------------------------------------------------------------

st.divider()
render_footer("Dept One-Pager", "The Harris Farm Way", user=user)
