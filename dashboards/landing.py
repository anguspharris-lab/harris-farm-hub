"""
Harris Farm Hub — Home Page
The AI-First Manifesto landing experience.
Built with native Streamlit components only.
"""

import streamlit as st


def render_home_page():
    """Render the Hub home page using native Streamlit components."""

    # Get user info from session state
    _auth = st.session_state.get("auth_user", {})
    user_name = _auth.get("name", "Harris Farmer") if isinstance(_auth, dict) else "Harris Farmer"
    first_name = user_name.split()[0] if user_name != "Harris Farmer" else "Gus"
    _pages = st.session_state.get("_pages", {})

    # ── Hero ──────────────────────────────────────────────────────────
    st.markdown("#### AI CENTRE OF EXCELLENCE — LIVE :green_circle:")
    st.title("Inspiring Harris Farmers to Scale with AI")
    st.markdown("### *You are the architect. AI is the builder. Together you are unstoppable.*")

    st.divider()

    # ── Philosophy — "Harris Farming It" ──────────────────────────────
    st.markdown(
        '> *"Don\'t think about the one next thing. Think about the **whole process**. '
        'End to end. Then your computer does it."*'
    )
    st.caption('— "Harris Farming It" — The mindset shift that changes everything')

    col_old, col_new = st.columns(2)
    with col_old:
        st.error(
            "**The Old Way**\n\n"
            "Think small → do one task → pass it on → wait → chase → redo → "
            "meet to discuss what happened"
        )
    with col_new:
        st.success(
            "**The New Way**\n\n"
            "Think end-to-end → write ONE prompt → AI builds it → "
            "you review & add context → ship it"
        )

    st.divider()

    # ── Stats ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("73%", "of retail AI leaders outperform peers")
    c2.metric("40%", "time saved on reporting & analysis")
    c3.metric("$2.4M", "annualised value from AI initiatives")
    c4.metric("30+", "stores powering the data engine")

    st.divider()

    # ── Four Doors ────────────────────────────────────────────────────
    d1, d2, d3, d4 = st.columns(4)

    with d1:
        st.markdown("### :triangular_ruler: Strategy")
        st.markdown("Fewer, Bigger, Better — our 5 pillars, live progress, board-ready reporting.")
        if "strategy-overview" in _pages:
            st.page_link(_pages["strategy-overview"], label="Explore pillars →", use_container_width=True)

    with d2:
        st.markdown("### :brain: Growing Legends")
        st.markdown("From Seed to Cultivator. Prove what you can ship.")
        if "skills-academy" in _pages:
            st.page_link(_pages["skills-academy"], label="Start your journey →", use_container_width=True)

    with d3:
        st.markdown("### :bar_chart: Operations")
        st.markdown("Ask in plain English, get answers in seconds.")
        if "sales" in _pages:
            st.page_link(_pages["sales"], label="Open dashboards →", use_container_width=True)

    with d4:
        st.markdown("### :microscope: Back of House")
        st.markdown("The Rubric. WATCHDOG. How it's all built.")
        if "the-rubric" in _pages:
            st.page_link(_pages["the-rubric"], label="See the engine →", use_container_width=True)

    st.divider()

    # ── The AI-First Method (6 steps) ─────────────────────────────────
    st.header("The AI-First Method")
    st.markdown("Six steps. One prompt. The whole process. This is how every Harris Farmer becomes 10x more effective.")

    # Row 1: Steps 1 & 2
    s1, s2 = st.columns(2)
    with s1:
        with st.container(border=True):
            st.markdown("**Step 01 — Define the Whole Outcome**")
            st.markdown(
                'Don\'t ask "what\'s my next task?" Ask "what is the entire end-to-end '
                'outcome I need?" The prompt IS the work.'
            )
            st.code(
                "Build a complete weekly performance review that compares\n"
                "to budget, flags problems, recommends actions, and is\n"
                "ready for my manager to approve.",
                language=None,
            )
    with s2:
        with st.container(border=True):
            st.markdown("**Step 02 — Flood It With Context**")
            st.markdown(
                "AI knows everything but it needs YOUR data. The more specific context "
                "you give — role, audience, format, constraints — the better the output."
            )
            st.code(
                "Include: who it's for, what decisions it drives,\n"
                "what data sources to use, what format the output\n"
                "needs to be in.",
                language=None,
            )

    # Row 2: Steps 3 & 4
    s3, s4 = st.columns(2)
    with s3:
        with st.container(border=True):
            st.markdown("**Step 03 — Run It Through The Rubric**")
            st.markdown(
                "Every output gets scored. Our 5-tier review system catches what humans miss. "
                "Nothing ships below an 8."
            )
            st.code(
                "CTO Panel → CLO Panel → Strategic Alignment →\n"
                "Implementation → Presentation Quality.\n"
                "Score ≥ 8.0 to ship.",
                language=None,
            )
    with s4:
        with st.container(border=True):
            st.markdown("**Step 04 — Ask AI What's Missing**")
            st.markdown(
                "After your first draft, ask: \"What additional context would help you "
                "improve this?\" AI will tell you exactly what it needs."
            )
            st.code(
                "What am I missing? What would make this board-ready?\n"
                "What data would strengthen the recommendations?",
                language=None,
            )

    # Row 3: Steps 5 & 6
    s5, s6 = st.columns(2)
    with s5:
        with st.container(border=True):
            st.markdown("**Step 05 — Review, Add Your Judgment**")
            st.markdown(
                "AI builds it. You add what only a human can — context, relationships, "
                "gut feel, the Harris Farm way. Your expertise matters most."
            )
            st.code(
                "Your 20 years of produce knowledge + AI's data\n"
                "analysis = decisions nobody else can make.",
                language=None,
            )
    with s6:
        with st.container(border=True):
            st.markdown("**Step 06 — Ship It & Share the Prompt**")
            st.markdown(
                "Built a great prompt? Save it. Share it. Your colleagues will thank you. "
                "This is how we all level up together."
            )
            st.code(
                "Save → Prompt Library → Tagged by role & use case →\n"
                "Anyone can reuse and improve it.",
                language=None,
            )

    st.divider()

    # ── CTA ────────────────────────────────────────────────────────────
    st.subheader("It's Not AI vs You. It's You Using AI.")
    st.markdown(
        "Everyone can be an expert with an LLM on their side. You could be in any store, "
        "any warehouse, anywhere. When you use AI as your workhorse, **you take the leap up the ladder.**"
    )
    cta1, cta2, _cta_spacer = st.columns([1, 1, 2])
    with cta1:
        if "hub-assistant" in _pages:
            st.page_link(_pages["hub-assistant"], label=":rocket: Ask The Hub a Question", use_container_width=True)
    with cta2:
        if "skills-academy" in _pages:
            st.page_link(_pages["skills-academy"], label=":books: Start Growing", use_container_width=True)

    st.divider()

    # ── Ninja Leaderboard ─────────────────────────────────────────────
    st.subheader(":ninja: AI Ninja Leaderboard — This Month")
    n1, n2, n3, n4, n5 = st.columns(5)
    _leaders = [
        (n1, "#1", first_name, _auth.get("hub_role", "Co-CEO").replace("_", " ").title() if isinstance(_auth, dict) else "Co-CEO", "Cultivator", "2,840 XP"),
        (n2, "#2", "Sarah M.", "Head of Buying", "Harvester", "1,920 XP"),
        (n3, "#3", "James T.", "Area Manager West", "Harvester", "1,680 XP"),
        (n4, "#4", "Kim L.", "Store Manager Bondi", "Grower", "1,340 XP"),
        (n5, "#5", "Dan P.", "Warehouse Ops", "Grower", "1,180 XP"),
    ]
    for col, rank, name, role, level, xp in _leaders:
        with col:
            with st.container(border=True):
                st.caption(f"{rank} · {level.upper()}")
                st.markdown(f"**{name}**")
                st.caption(role)
                st.markdown(f"**{xp}**")

    st.divider()

    # ── Closing Quote ─────────────────────────────────────────────────
    st.markdown(
        "> *\"The future of Harris Farm isn't AI replacing Harris Farmers. "
        "It's **Harris Farmers with AI** replacing Harris Farmers without it.\"*"
    )
    st.caption("— The Harris Farming It Manifesto")

    # ── Footer ────────────────────────────────────────────────────────
    st.caption("Built with :green_heart: by Harris Farmers, for Harris Farmers")


render_home_page()
