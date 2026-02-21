"""
The Paddock -- AI Skills Assessment for Harris Farm
Native Streamlit dashboard: welcome, register, 5 assessment modules, results, admin.
"""
import json
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from shared.styles import render_header, render_footer
from shared.paddock_questions import (
    STORE_NAMES, get_departments, suggest_role_tier, ROLE_TIER_LABELS,
    TECH_COMFORT_OPTIONS, AI_EXPERIENCE_OPTIONS,
    MODULE_IDS, MODULE_META, MATURITY_LEVELS,
    get_module_questions, score_question, get_maturity,
    calculate_overall, get_recommendations,
)
import paddock_layer

# ============================================================================
# INIT — detect returning user
# ============================================================================

user = st.session_state.get("auth_user")

if "paddock_step" not in st.session_state:
    hub_email = (user or {}).get("email")
    if hub_email:
        existing = paddock_layer.get_user_by_hub_id(hub_email)
        if existing:
            result = paddock_layer.get_results(existing["id"])
            if result:
                st.session_state.paddock_step = "results"
                st.session_state.paddock_user_id = existing["id"]
            else:
                # Resume incomplete assessment
                st.session_state.paddock_step = "assess"
                st.session_state.paddock_user_id = existing["id"]
                _u = existing
                # Find first incomplete module
                for idx, mod in enumerate(MODULE_IDS):
                    qs = get_module_questions(mod, _u["role_tier"])
                    answered = paddock_layer.count_answered(_u["id"], mod)
                    if answered < len(qs):
                        st.session_state.paddock_module_idx = idx
                        st.session_state.paddock_question_idx = answered
                        st.session_state.paddock_show_intro = (answered == 0)
                        break
                else:
                    st.session_state.paddock_module_idx = 0
                    st.session_state.paddock_question_idx = 0
                    st.session_state.paddock_show_intro = True
        else:
            st.session_state.paddock_step = "welcome"
    else:
        st.session_state.paddock_step = "welcome"


# ============================================================================
# WELCOME SCREEN
# ============================================================================

def render_welcome():
    st.markdown(
        "<div style='background:linear-gradient(135deg, #4ba021 0%, #3d8a1b 100%);"
        "color:white;padding:60px 32px;border-radius:14px;text-align:center;"
        "margin:20px 0;'>"
        "<div style='font-size:4em;margin-bottom:16px;'>\U0001f331</div>"
        "<div style='font-size:2.4em;font-weight:800;margin-bottom:8px;'>"
        "The Paddock</div>"
        "<div style='font-size:1.1em;opacity:0.9;max-width:520px;margin:0 auto 24px;'>"
        "G'day! Welcome to The Paddock -- where Harris Farmers grow their AI skills."
        "</div>"
        "<div style='font-size:0.9em;opacity:0.7;'>"
        "5 quick modules | About 15-20 minutes | Fun, not a test</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("\U0001f331 Let's Get Started", use_container_width=True, type="primary"):
            st.session_state.paddock_step = "register"
            st.rerun()

    # Admin shortcut
    if (user or {}).get("role") == "admin":
        st.markdown("---")
        if st.button("\U0001f33f Admin: The Greenhouse", use_container_width=True):
            st.session_state.paddock_step = "admin"
            st.rerun()


# ============================================================================
# REGISTRATION SCREEN
# ============================================================================

def render_register():
    st.markdown("### \U0001f331 Tell us about yourself")
    st.caption("So we can tailor the assessment to your role.")

    with st.form("paddock_register", clear_on_submit=False):
        name = st.text_input("Full Name", placeholder="e.g. Jane Smith")
        employee_id = st.text_input("Employee ID (optional)", placeholder='e.g. HFM1234 or "Guest"')

        store = st.selectbox("Store / Location", [""] + STORE_NAMES)

        depts = get_departments(store) if store else []
        department = st.selectbox("Department", [""] + depts) if depts else ""

        suggested = suggest_role_tier(department) if department else 3
        role_tier = st.selectbox(
            "Your Role Level",
            options=list(ROLE_TIER_LABELS.keys()),
            format_func=lambda k: f"{k}. {ROLE_TIER_LABELS[k]}",
            index=suggested - 1,
        )

        st.markdown("**How comfortable are you with technology?**")
        tc_labels = {o["value"]: f"{o['emoji']} {o['label']}" for o in TECH_COMFORT_OPTIONS}
        tech_comfort = st.select_slider(
            "Tech comfort", options=[1, 2, 3, 4, 5],
            format_func=lambda v: tc_labels[v], value=3,
            label_visibility="collapsed",
        )

        st.markdown("**Have you used any AI tools before?**")
        ai_exp = st.radio(
            "AI experience",
            [o["value"] for o in AI_EXPERIENCE_OPTIONS],
            format_func=lambda v: next(o["label"] for o in AI_EXPERIENCE_OPTIONS if o["value"] == v),
            label_visibility="collapsed",
        )

        submitted = st.form_submit_button("\U0001f680 Start the Assessment", use_container_width=True)

        if submitted:
            if not name or not store or not department:
                st.error("Please fill in your name, store, and department.")
            else:
                hub_email = (user or {}).get("email")
                p_user = paddock_layer.register_user(
                    name=name, store=store, department=department,
                    role_tier=role_tier, hub_user_id=hub_email,
                    employee_id=employee_id or None,
                    tech_comfort=tech_comfort, ai_experience=ai_exp,
                )
                st.session_state.paddock_user_id = p_user["id"]
                st.session_state.paddock_step = "assess"
                st.session_state.paddock_module_idx = 0
                st.session_state.paddock_question_idx = 0
                st.session_state.paddock_show_intro = True
                st.session_state.paddock_start_time = time.time()
                st.rerun()


# ============================================================================
# ASSESSMENT SCREEN
# ============================================================================

def render_assessment():
    p_user = paddock_layer.get_user(st.session_state.paddock_user_id)
    if not p_user:
        st.error("User not found. Please start over.")
        return

    module_idx = st.session_state.get("paddock_module_idx", 0)
    question_idx = st.session_state.get("paddock_question_idx", 0)
    module_id = MODULE_IDS[module_idx]
    meta = MODULE_META[module_id]
    questions = get_module_questions(module_id, p_user["role_tier"])

    # Overall progress
    total_q = sum(len(get_module_questions(m, p_user["role_tier"])) for m in MODULE_IDS)
    done_q = sum(
        len(get_module_questions(MODULE_IDS[i], p_user["role_tier"]))
        for i in range(module_idx)
    ) + question_idx
    st.progress(done_q / total_q if total_q > 0 else 0,
                text=f"Module {module_idx + 1} of 5: {meta['title']}")

    # Module intro
    if st.session_state.get("paddock_show_intro", True):
        _render_module_intro(meta, module_idx, len(questions))
        return

    # Render question
    if question_idx < len(questions):
        _render_question(questions[question_idx], module_id, p_user, question_idx, len(questions))
    else:
        _advance_module(module_idx, p_user)


def _render_module_intro(meta, module_idx, q_count):
    st.markdown(
        f"<div style='text-align:center;padding:40px 20px;'>"
        f"<div style='font-size:4em;'>{meta['icon']}</div>"
        f"<div style='font-size:1.6em;font-weight:700;margin:12px 0 4px;'>"
        f"Module {module_idx + 1}: {meta['title']}</div>"
        f"<div style='color:#666;margin-bottom:8px;'>{meta['subtitle']}</div>"
        f"<div style='color:#999;font-size:0.9em;'>{q_count} questions</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Let's Go \U0001f331", use_container_width=True, type="primary"):
            st.session_state.paddock_show_intro = False
            st.session_state.paddock_start_time = time.time()
            st.rerun()


def _render_question(question, module_id, p_user, q_idx, q_total):
    qtype = question["type"]
    qid = question["id"]

    st.markdown(f"**Question {q_idx + 1} of {q_total}**")
    st.markdown(f"### {question['text']}")

    answer = None

    if qtype == "multiple_choice":
        options = question["options"]
        answer = st.radio(
            "Select one:", [o["value"] for o in options],
            format_func=lambda v: next(o["label"] for o in options if o["value"] == v),
            key=f"q_{qid}", label_visibility="collapsed",
        )

    elif qtype == "multiple_select":
        options = question["options"]
        max_sel = question.get("max_select")
        if max_sel:
            st.caption(f"Select up to {max_sel}")
        selected = []
        for o in options:
            if st.checkbox(o["label"], key=f"q_{qid}_{o['value']}"):
                selected.append(o["value"])
        if max_sel and len(selected) > max_sel:
            st.warning(f"Please select at most {max_sel} options.")
            return
        answer = selected if selected else None

    elif qtype == "prompt_comparison":
        options = question["options"]
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                f"<div style='background:#f0f7ed;padding:16px;border-radius:10px;"
                f"border:2px solid #ddd;min-height:120px;'>"
                f"<strong>{options[0]['label']}</strong><br><br>"
                f"<em>\"{options[0]['prompt']}\"</em></div>",
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                f"<div style='background:#f0f7ed;padding:16px;border-radius:10px;"
                f"border:2px solid #ddd;min-height:120px;'>"
                f"<strong>{options[1]['label']}</strong><br><br>"
                f"<em>\"{options[1]['prompt']}\"</em></div>",
                unsafe_allow_html=True,
            )
        answer = st.radio(
            "Which is better?",
            [o["value"] for o in options],
            format_func=lambda v: next(o["label"] for o in options if o["value"] == v),
            key=f"q_{qid}", horizontal=True,
        )

    elif qtype == "slider":
        answer = st.slider(
            "Your answer",
            min_value=question.get("min", 1),
            max_value=question.get("max", 10),
            value=5, key=f"q_{qid}",
            label_visibility="collapsed",
        )
        labels = question.get("labels", {})
        if labels:
            cols = st.columns(len(labels))
            for i, (val, label) in enumerate(sorted(labels.items())):
                with cols[i]:
                    st.caption(f"{val}: {label}")

    elif qtype == "free_text":
        answer = st.text_area(
            "Your answer",
            placeholder=question.get("placeholder", "Type your answer..."),
            key=f"q_{qid}", label_visibility="collapsed",
        )

    # Submit button
    st.markdown("")
    if st.button("Next \u2192", use_container_width=True, type="primary", key=f"next_{qid}"):
        if answer is None or answer == [] or answer == "":
            if qtype not in ("free_text",):
                st.warning("Please select an answer before continuing.")
                return

        # Score and save
        elapsed = int(time.time() - st.session_state.get("paddock_start_time", time.time()))
        score = score_question(question, answer)
        paddock_layer.save_response(
            st.session_state.paddock_user_id, module_id,
            qid, answer, score, elapsed,
        )

        # Advance
        module_idx = st.session_state.paddock_module_idx
        questions = get_module_questions(module_id, p_user["role_tier"])

        if q_idx + 1 < len(questions):
            st.session_state.paddock_question_idx = q_idx + 1
        else:
            _advance_module(module_idx, p_user)

        st.session_state.paddock_start_time = time.time()
        st.rerun()


def _advance_module(module_idx, p_user):
    if module_idx + 1 < len(MODULE_IDS):
        st.session_state.paddock_module_idx = module_idx + 1
        st.session_state.paddock_question_idx = 0
        st.session_state.paddock_show_intro = True
    else:
        # All done — calculate results
        result = paddock_layer.calculate_results(st.session_state.paddock_user_id)
        # Learning Centre integration
        hub_email = (user or {}).get("email")
        paddock_layer.update_learning_progress(hub_email, result["maturity"]["level"])
        st.session_state.paddock_step = "results"
    st.rerun()


# ============================================================================
# RESULTS SCREEN
# ============================================================================

def render_results():
    p_user = paddock_layer.get_user(st.session_state.paddock_user_id)
    result = paddock_layer.get_results(st.session_state.paddock_user_id)
    if not p_user or not result:
        st.error("Results not found.")
        return

    maturity = get_maturity(result["overall_score"])

    # Hero badge
    st.markdown(
        f"<div style='text-align:center;padding:30px 20px;background:linear-gradient(135deg, #4ba021 0%, #3d8a1b 100%);"
        f"color:white;border-radius:14px;margin-bottom:20px;'>"
        f"<div style='font-size:3.5em;'>{maturity['icon']}</div>"
        f"<div style='font-size:1.8em;font-weight:800;margin:8px 0;'>"
        f"You're a {maturity['name']}!</div>"
        f"<div style='font-size:1.0em;opacity:0.9;max-width:500px;margin:0 auto;'>"
        f"{maturity['message']}</div>"
        f"<div style='font-size:2.5em;font-weight:900;margin-top:16px;'>"
        f"{result['overall_score']}<span style='font-size:0.4em;opacity:0.7;'>/100</span></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Radar chart
    col_radar, col_breakdown = st.columns([1, 1])

    with col_radar:
        st.markdown("#### Your AI Skills Profile")
        categories = ["Awareness", "Usage", "Critical Thinking", "Applied Skills", "Confidence"]
        values = [
            result["awareness_score"], result["usage_score"],
            result["critical_score"], result["applied_score"],
            result["confidence_score"],
        ]
        fig = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(75, 160, 33, 0.2)",
            line=dict(color="#4ba021", width=2),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False, height=350, margin=dict(l=60, r=60, t=30, b=30),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_breakdown:
        st.markdown("#### Module Breakdown")
        module_names = {
            "awareness": "\U0001f41d Awareness",
            "usage": "\U0001f331 Usage",
            "critical": "\U0001f50d Critical Thinking",
            "applied": "\U0001f33e Applied Skills",
            "confidence": "\U0001f33b Confidence",
        }
        for mod in MODULE_IDS:
            score_val = result.get(f"{mod}_score", 0)
            st.markdown(f"**{module_names[mod]}** — {score_val}/100")
            st.progress(score_val / 100)

    # Learning path recommendations
    st.markdown("---")
    st.markdown("### \U0001f4da Your Learning Path")
    st.caption(f"Personalised for a {ROLE_TIER_LABELS.get(p_user['role_tier'], 'team member')} at {maturity['name']} level")

    recs = get_recommendations(maturity["level"], p_user["role_tier"])
    if recs:
        cols = st.columns(min(len(recs), 3))
        type_icons = {"video": "\U0001f3ac", "hands-on": "\U0001f9ea", "article": "\U0001f4d6", "workshop": "\U0001f3af"}
        for i, rec in enumerate(recs):
            with cols[i % len(cols)]:
                icon = type_icons.get(rec["type"], "\U0001f4d6")
                st.markdown(
                    f"<div style='background:#f0f7ed;padding:16px;border-radius:10px;"
                    f"border-left:4px solid #4ba021;margin-bottom:12px;'>"
                    f"<div style='font-size:0.8em;color:#4ba021;font-weight:600;'>"
                    f"{icon} {rec['type'].upper()} | {rec['duration']}</div>"
                    f"<div style='font-weight:700;margin:6px 0 4px;'>{rec['title']}</div>"
                    f"<div style='font-size:0.85em;color:#666;'>{rec['description']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # Feedback form
    st.markdown("---")
    st.markdown("### \U0001f4ac How was the experience?")

    existing_fb = paddock_layer.get_feedback(st.session_state.paddock_user_id)
    if existing_fb:
        st.success("Thanks for your feedback!")
    else:
        with st.form("paddock_feedback"):
            rating = st.slider("Rate your experience", 1, 5, 4,
                               format="%d stars", help="1 = poor, 5 = excellent")
            confusion = st.text_area("Was anything confusing?", placeholder="Optional...", key="fb_conf")
            improvement = st.text_area("What would make this better?", placeholder="Optional...", key="fb_imp")
            if st.form_submit_button("Submit Feedback", use_container_width=True):
                paddock_layer.save_feedback(
                    st.session_state.paddock_user_id,
                    experience_rating=rating,
                    confusion_notes=confusion or None,
                    improvement_suggestions=improvement or None,
                )
                st.success("Thanks for the feedback!")
                st.rerun()

    # Start over
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("\U0001f504 Start Over (New Assessment)", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith("paddock_") or key.startswith("q_") or key.startswith("next_"):
                    del st.session_state[key]
            st.session_state.paddock_step = "welcome"
            st.rerun()


# ============================================================================
# ADMIN / GREENHOUSE SCREEN
# ============================================================================

def render_admin():
    if (user or {}).get("role") != "admin":
        st.warning("Admin access required.")
        if st.button("\u2190 Back to Welcome"):
            st.session_state.paddock_step = "welcome"
            st.rerun()
        return

    st.markdown("## \U0001f33f The Greenhouse — Admin Dashboard")

    overview = paddock_layer.admin_overview()

    if overview["total_users"] == 0:
        st.info("No assessments completed yet. Share The Paddock with your team to get started!")
        if st.button("\u2190 Back"):
            st.session_state.paddock_step = "welcome"
            st.rerun()
        return

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "\U0001f4ca Overview", "\U0001f5fa Heatmap", "\U0001f50d Gap Analysis",
        "\U0001f9e0 Dunning-Kruger", "\U0001f4ac Feedback", "\U0001f4e5 Export",
    ])

    with tab1:
        _admin_overview(overview)

    with tab2:
        _admin_heatmap()

    with tab3:
        _admin_gaps()

    with tab4:
        _admin_dk()

    with tab5:
        _admin_feedback()

    with tab6:
        _admin_export()

    st.markdown("---")
    if st.button("\u2190 Back to Welcome"):
        st.session_state.paddock_step = "welcome"
        st.rerun()


def _admin_overview(overview):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Users", overview["total_users"])
    c2.metric("Completed", overview["completed"])
    c3.metric("Completion Rate", f"{overview['completion_rate']}%")
    c4.metric("Avg Score", f"{overview['avg_score']}/100")

    # Maturity distribution
    mat_names = {m["level"]: f"{m['icon']} {m['name']}" for m in MATURITY_LEVELS}
    dist = overview["maturity_distribution"]
    if dist:
        st.markdown("#### Maturity Distribution")
        df = pd.DataFrame([
            {"Level": mat_names.get(k, str(k)), "Count": v}
            for k, v in sorted(dist.items())
        ])
        st.bar_chart(df.set_index("Level"))

    # Module completion
    mod_comp = overview["module_completion"]
    if mod_comp:
        st.markdown("#### Module Completion")
        for mod in MODULE_IDS:
            cnt = mod_comp.get(mod, 0)
            pct = cnt / overview["total_users"] * 100 if overview["total_users"] > 0 else 0
            st.markdown(f"**{MODULE_META[mod]['title']}** — {cnt} users ({pct:.0f}%)")
            st.progress(pct / 100)


def _admin_heatmap():
    heatmap = paddock_layer.admin_heatmap()
    if not heatmap:
        st.info("No data yet.")
        return

    st.markdown("#### Store x Maturity Heatmap")
    mat_names = {m["level"]: m["name"] for m in MATURITY_LEVELS}
    rows = []
    for store, levels in sorted(heatmap.items()):
        row = {"Store": store}
        for level in range(1, 6):
            row[mat_names.get(level, str(level))] = levels.get(level, 0)
        rows.append(row)
    df = pd.DataFrame(rows).set_index("Store")
    st.dataframe(df, use_container_width=True)


def _admin_gaps():
    gaps = paddock_layer.admin_gaps()

    st.markdown("#### By Department")
    if gaps["by_department"]:
        df = pd.DataFrame(gaps["by_department"])
        st.dataframe(df, use_container_width=True)

    st.markdown("#### By Role Tier")
    if gaps["by_tier"]:
        df = pd.DataFrame(gaps["by_tier"])
        df["role_tier"] = df["role_tier"].map(ROLE_TIER_LABELS)
        st.dataframe(df, use_container_width=True)


def _admin_dk():
    gaps = paddock_layer.admin_gaps()
    dk = gaps.get("dunning_kruger", [])
    if not dk:
        st.info("Not enough data yet.")
        return

    st.markdown("#### Confidence vs Ability")
    st.caption("Points above the diagonal = overconfident, below = underconfident")

    df = pd.DataFrame(dk)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["overall_score"], y=df["confidence_score"],
        mode="markers+text", text=df["name"],
        textposition="top center", textfont=dict(size=9),
        marker=dict(
            size=10,
            color=df["gap"].apply(lambda g: "#ef4444" if g > 15 else ("#3b82f6" if g < -15 else "#94a3b8")),
        ),
    ))
    fig.add_trace(go.Scatter(
        x=[0, 100], y=[0, 100], mode="lines",
        line=dict(color="#ccc", dash="dash"), showlegend=False,
    ))
    fig.update_layout(
        xaxis_title="Overall Score", yaxis_title="Confidence Score",
        xaxis=dict(range=[0, 100]), yaxis=dict(range=[0, 100]),
        height=450, showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _admin_feedback():
    fb = paddock_layer.admin_feedback_summary()
    c1, c2 = st.columns(2)
    c1.metric("Avg Rating", f"{fb['avg_rating']}/5")
    c2.metric("Total Feedback", fb["total_feedback"])

    if fb["verbatims"]:
        st.markdown("#### Recent Feedback")
        df = pd.DataFrame(fb["verbatims"])
        st.dataframe(df, use_container_width=True)

    if fb["free_text"]:
        st.markdown("#### Free-Text Responses")
        df = pd.DataFrame(fb["free_text"])
        st.dataframe(df, use_container_width=True)


def _admin_export():
    data = paddock_layer.admin_export()
    if not data:
        st.info("No data to export.")
        return

    df = pd.DataFrame(data)
    csv = df.to_csv(index=False)
    st.download_button(
        "\U0001f4e5 Download CSV",
        csv, "paddock_export.csv", "text/csv",
        use_container_width=True,
    )
    st.markdown(f"**{len(data)} records**")
    st.dataframe(df, use_container_width=True)


# ============================================================================
# MAIN ROUTER
# ============================================================================

render_header(
    "The Paddock",
    "**AI Skills Assessment** | Grow your AI confidence",
    goals=["G3"],
    strategy_context="Building AI literacy across all roles (Pillar 3 & 5)",
)

step = st.session_state.get("paddock_step", "welcome")

if step == "welcome":
    render_welcome()
elif step == "register":
    render_register()
elif step == "assess":
    render_assessment()
elif step == "results":
    render_results()
elif step == "admin":
    render_admin()
else:
    render_welcome()

render_footer("The Paddock", user=user)
