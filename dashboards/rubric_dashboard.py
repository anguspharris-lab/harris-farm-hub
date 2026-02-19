"""
Harris Farm Hub - The Rubric: AI Training & Prompt Skills
Learn to write effective prompts, practice with challenges, compare AI
responses, and evaluate them using a structured rubric.
"""

import streamlit as st
import requests
import json
import plotly.graph_objects as go
from datetime import datetime

API_URL = "http://localhost:8000"

from shared.styles import render_header, render_footer
from shared.training_content import (
    BUILDING_BLOCKS, PROMPT_EXAMPLES, CHALLENGES,
    RUBRIC_CRITERIA, BADGES, COACH_SYSTEM_PROMPT,
    check_prompt_quality,
)

st.markdown("<style>.winner-card { border: 3px solid #10b981; border-radius: 10px; padding: 10px; }</style>", unsafe_allow_html=True)
user = st.session_state.get("auth_user")

render_header("⚖️ The Rubric", "**AI Training & Prompt Skills** | Learn to write great prompts and evaluate AI responses")


@st.cache_data(ttl=300, show_spinner=False)
def _rubric_load_performance():
    try:
        resp = requests.get(f"{API_URL}/api/analytics/performance", timeout=5)
        return resp.json() if resp.status_code == 200 else {}
    except Exception:
        return {}

# ---------------------------------------------------------------------------
# SESSION STATE DEFAULTS
# ---------------------------------------------------------------------------

if "progress" not in st.session_state:
    st.session_state.progress = {
        "challenges_done": 0,
        "evaluations_done": 0,
        "providers_used": set(),
        "best_scores": {},
        "badges": set(),
    }

# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------

tabs = st.tabs(["📖 Learn", "✏️ Practice", "⚖️ Compare", "📋 Scorecard", "🏅 My Progress"])

# ============================================================================
# TAB 1: LEARN
# ============================================================================

with tabs[0]:
    st.subheader("What Makes a Good Prompt?")
    st.markdown(
        "A prompt is the question or instruction you give to an AI. "
        "The better your prompt, the better the answer. "
        "Here's an example of the difference:"
    )

    col_bad, col_good = st.columns(2)
    with col_bad:
        st.error("**Bad prompt:**\n\nTell me about fruit")
    with col_good:
        st.success(
            "**Good prompt:**\n\n"
            "You are a Harris Farm fresh produce specialist. "
            "What are the 3 most common causes of stone fruit wastage "
            "at our Bondi store over the last 4 weeks? "
            "Present as a numbered list with cost impact and one action for each."
        )

    st.markdown("---")

    # --- 5 Building Blocks ---
    st.subheader("The 5 Building Blocks")
    st.markdown("Every great prompt uses these 5 elements. Click each one to learn more.")

    for block in BUILDING_BLOCKS:
        with st.expander(f"**{block['icon']}. {block['name']}** — {block['short']}"):
            st.markdown(block["explanation"])
            st.info(f"**Example:** _{block['example']}_")
            st.caption(f"Tip: {block['tip']}")

    st.markdown("---")

    # --- Good vs Bad Examples ---
    st.subheader("Good vs Bad Prompts — Harris Farm Examples")

    for ex in PROMPT_EXAMPLES:
        with st.expander(f"**{ex['department']}**"):
            c1, c2 = st.columns(2)
            with c1:
                st.error(f"**Bad:** {ex['bad']}")
            with c2:
                st.success(f"**Good:** {ex['good']}")
            st.caption(f"Why it's better: {ex['why']}")

    st.markdown("---")

    # --- What is a Rubric? ---
    st.subheader("What is a Rubric?")
    st.markdown(
        "A **rubric** is a checklist for quality. Instead of just saying "
        "'this answer is good', a rubric gives you **specific criteria** to score against. "
        "This makes your evaluation fair, consistent, and useful for learning."
    )
    st.markdown("The Rubric uses **5 scoring criteria** (each scored 1-5):")

    for c in RUBRIC_CRITERIA:
        st.markdown(f"- **{c['name']}**: {c['description']}")

    st.info("Ready to try it? Head to the **Scorecard** tab to evaluate AI responses using these criteria.")


# ============================================================================
# TAB 2: PRACTICE
# ============================================================================

with tabs[1]:
    st.subheader("Practice Writing Prompts")
    st.markdown(
        "Choose a challenge, write a prompt, and get feedback from an AI coach. "
        "The coach will score your prompt against the 5 building blocks."
    )

    col_diff, col_challenge = st.columns([1, 3])

    with col_diff:
        difficulty = st.radio("Difficulty", list(CHALLENGES.keys()), index=0,
                              key="rubric_practice_difficulty")
        challenge_titles = [c["title"] for c in CHALLENGES[difficulty]]
        selected_title = st.radio("Challenge", challenge_titles, index=0,
                                  key="rubric_practice_challenge")

    challenge = next(c for c in CHALLENGES[difficulty] if c["title"] == selected_title)

    with col_challenge:
        st.markdown(f"### {challenge['title']}")
        st.info(f"**Scenario:** {challenge['scenario']}")

        with st.expander("Hints (click for help)"):
            for h in challenge["hints"]:
                st.markdown(f"- {h}")

        user_prompt = st.text_area(
            "Write your prompt here:",
            height=120,
            placeholder="Start writing your prompt...",
            key=f"practice_{challenge['id']}",
        )

        # Prompt quality preview
        if user_prompt:
            quality = check_prompt_quality(user_prompt)
            cols = st.columns(5)
            for i, block in enumerate(BUILDING_BLOCKS):
                check = quality["checks"][block["name"]]
                with cols[i]:
                    if check["present"]:
                        st.markdown(f"✅ **{block['name']}**")
                    else:
                        st.markdown(f"⬜ {block['name']}")
            st.caption(f"Prompt score: {quality['score']}/5 — {quality['level']}")

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            check_clicked = st.button(
                "🎯 Check My Prompt",
                type="primary",
                use_container_width=True,
                disabled=not user_prompt,
                key="rubric_check_prompt",
            )

        with col_btn2:
            try_real = st.button(
                "🚀 Try It For Real",
                use_container_width=True,
                disabled=not user_prompt,
                help="Send your prompt to an actual AI and see the response",
                key="rubric_try_real",
            )

        if check_clicked and user_prompt:
            with st.spinner("AI coach is reviewing your prompt..."):
                coach_msg = COACH_SYSTEM_PROMPT.format(
                    scenario=challenge["scenario"],
                    user_prompt=user_prompt,
                )
                try:
                    resp = requests.post(f"{API_URL}/api/chat", json={
                        "message": coach_msg,
                        "history": [],
                        "provider": "claude",
                        "user_id": "training",
                    }, timeout=90)

                    if resp.status_code == 200:
                        data = resp.json()
                        st.markdown("### Coach Feedback")
                        st.markdown(data["response"])

                        # Update progress
                        st.session_state.progress["challenges_done"] += 1
                        st.session_state.progress["badges"].add("first_prompt")
                        if difficulty == "Advanced":
                            st.session_state.progress["badges"].add("advanced_learner")

                        quality = check_prompt_quality(user_prompt)
                        if quality["score"] >= 4:
                            st.session_state.progress["badges"].add("prompt_pro")
                        st.session_state.progress["best_scores"][challenge["id"]] = quality["score"]
                    else:
                        st.error(f"API returned {resp.status_code}. Is the backend running?")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to Hub API. Is the backend running?")
                except Exception as e:
                    st.error(f"Error: {e}")

        if try_real and user_prompt:
            with st.spinner("Sending to AI..."):
                try:
                    resp = requests.post(f"{API_URL}/api/chat", json={
                        "message": user_prompt,
                        "history": [],
                        "provider": "claude",
                        "user_id": "training",
                    }, timeout=90)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.markdown("### AI Response")
                        st.markdown(data["response"])
                        kb_docs = data.get("kb_docs_used", [])
                        if kb_docs:
                            with st.expander(f"Sources ({len(kb_docs)} documents)"):
                                for doc in kb_docs:
                                    st.markdown(f"- **{doc['filename']}** — _{doc['category']}_")
                    else:
                        st.error(f"API returned {resp.status_code}.")
                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================================================
# TAB 3: COMPARE (existing Rubric functionality, preserved)
# ============================================================================

with tabs[2]:
    st.subheader("Compare AI Responses")
    st.markdown(
        "Now that you know how to write good prompts, test them against "
        "multiple AI models. See how the same prompt gets different responses."
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        prompt = st.text_area(
            "Your question",
            placeholder="e.g., What pricing strategy should Harris Farm use for premium organic produce?",
            height=100,
            key="compare_prompt",
        )

        context = st.text_area(
            "Additional context (optional)",
            placeholder="e.g., Harris Farm Markets operates 30+ stores in NSW...",
            height=60,
            key="compare_context",
        )

    with col2:
        st.markdown("### Select LLMs")
        use_claude = st.checkbox("Claude", value=True, key="cmp_claude")
        use_chatgpt = st.checkbox("ChatGPT", value=True, key="cmp_chatgpt")
        use_grok = st.checkbox("Grok", value=False, key="cmp_grok")

        providers = []
        if use_claude:
            providers.append("claude")
        if use_chatgpt:
            providers.append("chatgpt")
        if use_grok:
            providers.append("grok")

        st.markdown("---")
        st.markdown("### Knowledge Base")
        use_kb = st.checkbox("Include KB context", value=True, key="cmp_kb")
        st.caption(f"{len(providers)} provider(s) selected")

    # Prompt quality checklist
    if prompt:
        quality = check_prompt_quality(prompt)
        st.markdown("**Prompt Quality Check:**")
        cols = st.columns(5)
        for i, block in enumerate(BUILDING_BLOCKS):
            check = quality["checks"][block["name"]]
            with cols[i]:
                icon = "✅" if check["present"] else "⬜"
                st.markdown(f"{icon} {block['name']}")
        if quality["score"] < 3:
            st.caption(f"Score: {quality['score']}/5 — Try adding more building blocks for better results!")
        else:
            st.caption(f"Score: {quality['score']}/5 — {quality['level']}")

    if st.button("⚖️ Run The Rubric", type="primary", use_container_width=True,
                 disabled=not prompt or len(providers) < 1, key="run_compare"):
        if prompt and len(providers) >= 1:
            with st.spinner("Querying LLMs... This may take 10-30 seconds."):
                try:
                    resp = requests.post(
                        f"{API_URL}/api/rubric",
                        json={
                            "prompt": prompt,
                            "context": context if context else None,
                            "providers": providers,
                            "user_id": "chairman",
                            "use_knowledge_base": use_kb,
                        },
                        timeout=90,
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        st.session_state["rubric_result"] = result
                        st.session_state["rubric_decided"] = False
                        st.session_state.progress["providers_used"].update(providers)
                        if len(st.session_state.progress["providers_used"]) >= 3:
                            st.session_state.progress["badges"].add("multi_model")
                    else:
                        st.error(f"API returned {resp.status_code}. Check the backend.")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to Hub API on port 8000.")
                except requests.exceptions.Timeout:
                    st.error("Request timed out — try again.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # Display results
    if "rubric_result" in st.session_state:
        result = st.session_state["rubric_result"]
        responses = result.get("responses", [])

        if responses:
            st.markdown("---")
            st.subheader("Responses")

            # Metrics row
            cols = st.columns(len(responses))
            for col, resp_item in zip(cols, responses):
                with col:
                    provider = resp_item.get("provider", "Unknown")
                    status = resp_item.get("status", "error")
                    if status == "success":
                        latency = resp_item.get("latency_ms", 0)
                        tokens = resp_item.get("tokens", 0)
                        st.metric(provider, f"{latency:.0f}ms", f"{tokens} tokens")
                    else:
                        st.metric(provider, "Error", "")

            st.markdown("---")

            # Response content
            cols = st.columns(len(responses))
            for col, resp_item in zip(cols, responses):
                with col:
                    provider = resp_item.get("provider", "Unknown")
                    status = resp_item.get("status", "error")
                    st.markdown(f"### {provider}")
                    if status == "success":
                        st.markdown(resp_item.get("response", "No response"))
                    else:
                        st.error(resp_item.get("response", "Error occurred"))

            # KB docs
            kb_docs = result.get("knowledge_base_docs", [])
            if kb_docs:
                with st.expander(f"Knowledge Base context ({len(kb_docs)} document(s) used)"):
                    for doc in kb_docs:
                        st.markdown(f"- **{doc.get('filename', 'Unknown')}** — _{doc.get('category', 'Uncategorised')}_")

            # Chairman's Decision
            st.markdown("---")
            st.subheader("Chairman's Decision")

            if st.session_state.get("rubric_decided"):
                st.success(f"Decision recorded: **{st.session_state.get('rubric_winner')}**")
            else:
                st.markdown(
                    "Which response was best? Consider: accuracy, practicality, "
                    "completeness, and alignment with Harris Farm strategy. "
                    "Or head to the **Scorecard** tab for a structured evaluation."
                )

                provider_names = [r.get("provider", "Unknown") for r in responses if r.get("status") == "success"]

                if provider_names:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        winner = st.radio("Select the winner", provider_names, horizontal=True, key="cmp_winner")
                        feedback = st.text_input("Why? (optional)", placeholder="e.g., More specific to Harris Farm context", key="cmp_feedback")
                    with col2:
                        if st.button("Record Decision", type="primary", use_container_width=True, key="cmp_decide"):
                            try:
                                decision_resp = requests.post(
                                    f"{API_URL}/api/decision",
                                    json={
                                        "query_id": result.get("query_id", 0),
                                        "winner": winner,
                                        "feedback": feedback if feedback else None,
                                        "user_id": "chairman",
                                    },
                                    timeout=10,
                                )
                                if decision_resp.status_code == 200:
                                    st.session_state["rubric_decided"] = True
                                    st.session_state["rubric_winner"] = winner
                                    st.success(f"Recorded: **{winner}** wins!")
                                    st.balloons()
                                else:
                                    st.error("Failed to record decision.")
                            except Exception as e:
                                st.error(f"Error: {e}")
                else:
                    st.warning("No successful responses. Check your API keys in .env")

    # History
    with st.expander("LLM Performance History"):
        perf = _rubric_load_performance()
        llm_wins = perf.get("llm_performance", [])
        if llm_wins:
            for entry in llm_wins:
                st.markdown(f"- **{entry['winner']}**: {entry['wins']} win(s)")
        else:
            st.info("No decisions recorded yet.")


# ============================================================================
# TAB 4: SCORECARD
# ============================================================================

with tabs[3]:
    st.subheader("Score AI Responses with a Rubric")
    st.markdown(
        "Instead of just picking a winner, evaluate each response using "
        "**5 specific criteria**. This teaches you to think critically about AI output."
    )

    # Check if we have results from Compare tab
    has_results = "rubric_result" in st.session_state
    responses_to_score = []

    if has_results:
        result = st.session_state["rubric_result"]
        responses_to_score = [r for r in result.get("responses", []) if r.get("status") == "success"]

    if not responses_to_score:
        st.info(
            "No responses to score yet. Go to the **Compare** tab first, "
            "run a query, then come back here to evaluate the responses."
        )
        st.markdown("---")
        st.markdown("### How the Scorecard Works")
        for c in RUBRIC_CRITERIA:
            with st.expander(f"**{c['name']}**: {c['description']}"):
                for score, desc in c["guide"].items():
                    st.markdown(f"- **{score}/5**: {desc}")
    else:
        # Scoring interface
        all_scores = {}

        for resp_item in responses_to_score:
            provider = resp_item.get("provider", "Unknown")
            st.markdown(f"---")
            st.markdown(f"### Score: {provider}")

            with st.expander(f"View {provider}'s response", expanded=False):
                st.markdown(resp_item.get("response", ""))

            scores = {}
            cols = st.columns(5)
            for i, criterion in enumerate(RUBRIC_CRITERIA):
                with cols[i]:
                    score_val = st.slider(
                        criterion["name"],
                        1, 5, 3,
                        key=f"score_{provider}_{criterion['name']}",
                        help=criterion["description"],
                    )
                    scores[criterion["name"]] = score_val

            avg = sum(scores.values()) / len(scores)
            st.caption(f"Average: **{avg:.1f}/5**")
            all_scores[provider] = scores

        # Radar chart comparison
        if len(all_scores) >= 2:
            st.markdown("---")
            st.subheader("Comparison")

            categories = [c["name"] for c in RUBRIC_CRITERIA]

            fig = go.Figure()
            colors = ["#1e3a8a", "#10b981", "#f59e0b"]
            for i, (provider, scores) in enumerate(all_scores.items()):
                values = [scores[cat] for cat in categories]
                values.append(values[0])  # close the polygon
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories + [categories[0]],
                    fill="toself",
                    name=provider,
                    line_color=colors[i % len(colors)],
                    opacity=0.6,
                ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                showlegend=True,
                height=400,
                title="Response Quality Comparison",
            )
            st.plotly_chart(fig, key="rubric_radar_chart")

            # Winner by rubric
            averages = {p: sum(s.values()) / len(s) for p, s in all_scores.items()}
            rubric_winner = max(averages, key=averages.get)
            st.success(f"**Winner by rubric:** {rubric_winner} (avg {averages[rubric_winner]:.1f}/5)")

            # Compare with Chairman's Decision
            if st.session_state.get("rubric_decided"):
                chairman_pick = st.session_state.get("rubric_winner")
                if chairman_pick == rubric_winner:
                    st.info(f"Your rubric agrees with the Chairman's Decision ({chairman_pick})!")
                else:
                    st.warning(
                        f"Interesting! The Chairman picked **{chairman_pick}** "
                        f"but your rubric says **{rubric_winner}**. "
                        "This is normal — rubrics help make evaluation more structured."
                    )

        # Save evaluation
        if st.button("Save My Evaluation", type="primary", key="save_scorecard"):
            st.session_state.progress["evaluations_done"] += 1
            st.session_state.progress["badges"].add("sharp_eye")
            if st.session_state.progress["evaluations_done"] >= 3:
                st.session_state.progress["badges"].add("rubric_master")
            st.success("Evaluation saved! Check the **My Progress** tab.")


# ============================================================================
# TAB 5: MY PROGRESS
# ============================================================================

with tabs[4]:
    st.subheader("My Learning Progress")
    st.markdown("Track your prompt writing and evaluation skills.")

    progress = st.session_state.progress

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Challenges Done", progress["challenges_done"])
    with col2:
        st.metric("Evaluations Done", progress["evaluations_done"])
    with col3:
        providers_count = len(progress["providers_used"])
        st.metric("Providers Tried", f"{providers_count}/3")
    with col4:
        badge_count = len(progress["badges"])
        st.metric("Badges Earned", f"{badge_count}/{len(BADGES)}")

    st.markdown("---")

    # Skills radar
    if progress["best_scores"]:
        st.subheader("Prompt Skills")

        # Calculate average score per building block from challenge results
        # For now show overall best scores
        avg_score = sum(progress["best_scores"].values()) / len(progress["best_scores"])
        st.markdown(f"**Average prompt quality score:** {avg_score:.1f}/5")

    # Badges
    st.subheader("Badges")

    cols = st.columns(3)
    for i, badge in enumerate(BADGES):
        with cols[i % 3]:
            earned = badge["id"] in progress["badges"]
            if earned:
                st.success(f"{badge['icon']} **{badge['name']}**\n\n{badge['description']}")
            else:
                st.markdown(f"🔒 ~~{badge['name']}~~\n\n_{badge['description']}_")

    st.markdown("---")

    # Next steps
    st.subheader("Next Steps")
    if progress["challenges_done"] == 0:
        st.info("Start by going to the **Practice** tab and completing your first challenge!")
    elif progress["evaluations_done"] == 0:
        st.info("Great prompting! Now try the **Scorecard** tab to evaluate AI responses.")
    elif "advanced_learner" not in progress["badges"]:
        st.info("You're doing well! Try an **Advanced** challenge in the Practice tab.")
    else:
        st.success(
            "You're an AI prompt expert! Keep practising and share your "
            "skills with the team. Try the **Prompt Builder** (port 8504) "
            "for more advanced analytical prompts."
        )

    if st.button("Reset Progress", key="reset_progress"):
        st.session_state.progress = {
            "challenges_done": 0,
            "evaluations_done": 0,
            "providers_used": set(),
            "best_scores": {},
            "badges": set(),
        }
        st.rerun()


# ============================================================================
# FOOTER
# ============================================================================

render_footer("The Rubric", user=user)
