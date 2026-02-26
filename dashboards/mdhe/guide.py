"""
Harris Farm Hub -- MDHE Guide
Displays the MDHE team documentation directly in the Hub.
Reads from docs/MDHE_GUIDE.md so the guide stays in sync with the repo.
"""

from pathlib import Path
import streamlit as st

from shared.styles import render_header, render_footer


def render_mdhe_guide():
    user = st.session_state.get("auth_user", {})

    render_header(
        "MDHE Guide",
        "Master Data Health Engine -- Team Documentation",
    )

    # Read the guide markdown from docs/
    guide_path = Path(__file__).resolve().parent.parent.parent / "docs" / "MDHE_GUIDE.md"

    if guide_path.exists():
        content = guide_path.read_text(encoding="utf-8")
        st.markdown(content)
    else:
        st.warning("MDHE Guide file not found at docs/MDHE_GUIDE.md")

    render_footer("MDHE Guide", user=user)


render_mdhe_guide()
