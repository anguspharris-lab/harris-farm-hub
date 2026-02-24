"""
Harris Farm Hub - Hub Assistant: Knowledge Base Chatbot
Ask questions about Harris Farm procedures, golden rules, and operations.
Answers are grounded in the NUTS document knowledge base.
"""

import streamlit as st

from shared.styles import render_header, render_footer
from shared.kb_chat import (
    render_kb_chat,
    get_kb_categories,
    render_kb_stats_sidebar,
)

user = st.session_state.get("auth_user")

# ============================================================================
# HEADER
# ============================================================================

render_header(
    "Hub Assistant",
    "**Knowledge Base Chat** | Ask about procedures, golden rules & operations",
    goals=["G2", "G3"],
    strategy_context="This is Harris Farming It in action. Ask the question. Get the answer. Ship the insight. Steps 1-5 of the method happening in real time.",
)
st.caption("This is Harris Farming It in action. Ask the question. Get the answer.")

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("Settings")

    provider = st.selectbox(
        "AI Provider",
        ["claude", "chatgpt", "grok"],
        help="Select which LLM to use for answers",
    )

    categories, _stats = get_kb_categories()
    selected_category = st.selectbox(
        "Filter by Category",
        categories,
        help="Narrow answers to a specific department",
    )
    category = None if selected_category == "All" else selected_category

    st.markdown("---")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state["hub_chat_history"] = []
        st.rerun()

    render_kb_stats_sidebar()

# ============================================================================
# CHAT AREA
# ============================================================================

render_kb_chat(
    key_prefix="hub",
    provider=provider,
    category=category,
    show_suggestions=True,
)

# ============================================================================
# FOOTER
# ============================================================================

render_footer("Hub Assistant", user=user)
