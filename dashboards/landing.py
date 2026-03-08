"""
Harris Farm Hub -- Home Page
"We grow more than food." — The three-chapter AI story.
Built with native Streamlit components only.
"""

import streamlit as st


def render_home_page():
    """Render the Hub home page — three chapters + Harris Farm Way."""

    _auth = st.session_state.get("auth_user", {})
    user_name = _auth.get("name", "Harris Farmer") if isinstance(_auth, dict) else "Harris Farmer"
    first_name = user_name.split()[0] if user_name != "Harris Farmer" else "Gus"
    _pages = st.session_state.get("_pages", {})

    # -- Hero ---------------------------------------------------------------
    st.title("We grow more than food.")
    st.markdown(
        "### *We're transforming how we work — one process, one team, one decision at a time.*"
    )
    st.caption("Harris Farm Markets — Living the Greater Goodness")

    st.divider()

    # -- Key Stats ----------------------------------------------------------
    _stats = [
        ("30+", "Stores powering the data engine"),
        ("73%", "of retail AI leaders outperform peers"),
        ("40%", "time saved on reporting & analysis"),
        ("$2.4M", "annualised value from AI initiatives"),
    ]
    for col, (num, desc) in zip(st.columns(4), _stats):
        with col:
            with st.container(border=True):
                st.subheader(num)
                st.caption(desc)

    st.divider()

    # -- Three Chapters -----------------------------------------------------
    st.header("The Three Chapters")
    st.markdown(
        "Every transformation has a story. Ours has three chapters — "
        "each one building on the last."
    )

    ch1, ch2, ch3 = st.columns(3)

    with ch1:
        with st.container(border=True):
            st.markdown("#### Chapter 1: The Transformation")
            st.markdown(
                "Supply chain reimagined — from pay to purchase. "
                "We're using AI to reduce out-of-stocks, optimise buying, "
                "and turn 383 million transactions into actionable intelligence."
            )
            st.caption("Where the biggest operational wins live")
            if "hfw-transformation-readiness" in _pages:
                st.page_link(
                    _pages["hfw-transformation-readiness"],
                    label="Transformation Readiness",
                    use_container_width=True,
                )

    with ch2:
        with st.container(border=True):
            st.markdown("#### Chapter 2: The People")
            st.markdown(
                "Growing Legends, not just skills. Every Harris Farmer "
                "building AI capability at their own pace — from Seed to Legend. "
                "Because the best tech means nothing without great people."
            )
            st.caption("Where our superstars level up")
            if "skills-academy" in _pages:
                st.page_link(
                    _pages["skills-academy"],
                    label="Start Growing",
                    use_container_width=True,
                )

    with ch3:
        with st.container(border=True):
            st.markdown("#### Chapter 3: The Purpose")
            st.markdown(
                "The Greater Goodness, scaled by AI. Every decision we make "
                "with better data means less waste, happier communities, "
                "and a business that lasts another 50 years."
            )
            st.caption("Where strategy meets soul")
            if "strategy-overview" in _pages:
                st.page_link(
                    _pages["strategy-overview"],
                    label="Our Strategy",
                    use_container_width=True,
                )

    st.divider()

    # -- The Harris Farm Way ------------------------------------------------
    with st.container(border=True):
        hfw_l, hfw_r = st.columns([3, 1])
        with hfw_l:
            st.markdown("#### The Harris Farm Way")
            st.markdown(
                "Our AI-First Meeting Operating System. "
                "Every meeting starts with a question, ends with a decision, "
                "and leaves a trail of intelligence the whole business can use."
            )
            st.caption(
                "Supply Chain Reviews \u00b7 AI Vision Sessions \u00b7 "
                "Strategy Sprints \u00b7 Department One-Pagers \u00b7 Board Prep"
            )
        with hfw_r:
            if "hfw-landing" in _pages:
                st.page_link(
                    _pages["hfw-landing"],
                    label="Open the Playbook",
                    use_container_width=True,
                )

    st.divider()

    # -- Quick Access -------------------------------------------------------
    st.header("Jump In")
    d1, d2, d3, d4 = st.columns(4)

    with d1:
        st.markdown("**Strategy**")
        st.caption("Fewer, Bigger, Better — our 5 pillars, live progress.")
        if "strategy-overview" in _pages:
            st.page_link(_pages["strategy-overview"], label="Explore pillars", use_container_width=True)

    with d2:
        st.markdown("**Growing Legends**")
        st.caption("From Seed to Cultivator. Prove what you can ship.")
        if "skills-academy" in _pages:
            st.page_link(_pages["skills-academy"], label="Start your journey", use_container_width=True)

    with d3:
        st.markdown("**Operations**")
        st.caption("Ask in plain English, get answers in seconds.")
        if "sales" in _pages:
            st.page_link(_pages["sales"], label="Open dashboards", use_container_width=True)

    with d4:
        st.markdown("**Back of House**")
        st.caption("The Rubric. WATCHDOG. How it's all built.")
        if "the-rubric" in _pages:
            st.page_link(_pages["the-rubric"], label="See the engine", use_container_width=True)

    st.divider()

    # -- Ninja Leaderboard --------------------------------------------------
    st.subheader("AI Ninja Leaderboard — This Month")
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
                st.caption(f"{rank} \u00b7 {level.upper()}")
                st.markdown(f"**{name}**")
                st.caption(role)
                st.markdown(f"**{xp}**")

    st.divider()

    # -- Closing ------------------------------------------------------------
    st.markdown(
        "> *\"The future of Harris Farm isn't AI replacing Harris Farmers. "
        "It's **Harris Farmers with AI** replacing Harris Farmers without it.\"*"
    )
    st.caption("Built by our people, powered by AI, grown with purpose.")


render_home_page()
