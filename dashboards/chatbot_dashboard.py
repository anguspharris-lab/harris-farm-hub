"""
Harris Farm Hub - Hub Assistant: Knowledge Base Chatbot
Ask questions about Harris Farm procedures, golden rules, and operations.
Answers are grounded in the NUTS document knowledge base.
"""

import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="Hub Assistant | Harris Farm Hub",
    page_icon="💬",
    layout="wide"
)

API_URL = "http://localhost:8000"

from nav import render_nav
from shared.styles import apply_styles, render_header, render_footer
from shared.auth_gate import require_login

apply_styles()
user = require_login()
render_nav(8509, auth_token=st.session_state.get("auth_token"))

# ============================================================================
# HEADER
# ============================================================================

render_header("💬 Hub Assistant", "**Knowledge Base Chat** | Ask about procedures, golden rules & operations")

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("Settings")

    provider = st.selectbox("AI Provider", ["claude", "chatgpt", "grok"],
                            help="Select which LLM to use for answers")

    # Load categories from KB stats (cached)
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_kb_stats():
        try:
            resp = requests.get(f"{API_URL}/api/knowledge/stats", timeout=5)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            return {}

    kb_stats = _load_kb_stats()
    categories = ["All"]
    categories += [c["category"] for c in kb_stats.get("categories", [])]

    selected_category = st.selectbox("Filter by Category", categories,
                                     help="Narrow answers to a specific department")
    category = None if selected_category == "All" else selected_category

    st.markdown("---")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    # KB stats
    st.markdown("### Knowledge Base")
    total_docs = kb_stats.get("total_documents", 0)
    total_words = kb_stats.get("total_words", 0)
    st.caption(f"{total_docs} documents | {total_words:,} words")

    st.markdown("---")
    st.markdown("### Try asking...")
    suggestions = [
        "What are the golden rules for Fruit & Veg?",
        "How do I process a Dayforce leave request?",
        "What are the food safety temperature rules?",
        "How do I pick an online order?",
        "What is the bread baking schedule?",
    ]
    for s in suggestions:
        if st.button(s, key=f"sug_{hash(s)}", use_container_width=True):
            st.session_state.pending_question = s
            st.rerun()

# ============================================================================
# CHAT AREA
# ============================================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display existing messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("kb_docs"):
            with st.expander(f"Sources ({len(msg['kb_docs'])} documents)"):
                for doc in msg["kb_docs"]:
                    st.markdown(f"- **{doc['filename']}** — _{doc['category']}_")

# Handle suggested question
user_input = None
if "pending_question" in st.session_state:
    user_input = st.session_state.pop("pending_question")

# Chat input
if user_input is None:
    user_input = st.chat_input("Ask about Harris Farm procedures...")

if user_input:
    # Show user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build history for API
    api_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.chat_history[:-1]
        if m["role"] in ("user", "assistant")
    ]

    # Call API
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                resp = requests.post(f"{API_URL}/api/chat", json={
                    "message": user_input,
                    "history": api_history,
                    "category": category,
                    "provider": provider,
                    "user_id": "staff"
                }, timeout=90)

                if resp.status_code == 200:
                    data = resp.json()
                    answer = data["response"]
                    kb_docs = data.get("kb_docs_used", [])

                    st.markdown(answer)

                    if data.get("status") == "error":
                        st.warning("LLM returned an error. Check API key configuration in .env")

                    if kb_docs:
                        with st.expander(f"Sources ({len(kb_docs)} documents)"):
                            for doc in kb_docs:
                                st.markdown(f"- **{doc['filename']}** — _{doc['category']}_")

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "kb_docs": kb_docs,
                        "provider": data.get("provider"),
                        "tokens": data.get("tokens"),
                        "latency_ms": data.get("latency_ms")
                    })
                else:
                    st.error(f"API returned status {resp.status_code}. Is the backend running?")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to Hub API on port 8000. Is the backend running?")
            except requests.exceptions.Timeout:
                st.error("Request timed out. The LLM may be slow — try again.")

# ============================================================================
# FOOTER
# ============================================================================

render_footer("Hub Assistant", user=user)
