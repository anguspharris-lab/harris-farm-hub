"""
Harris Farm Hub -- Shared Knowledge Base Chat Component
Reusable RAG chat UI backed by /api/chat and /api/knowledge endpoints.

Usage:
    from shared.kb_chat import render_kb_chat, render_kb_stats_sidebar
    render_kb_chat("hub")        # full chat in Hub Assistant
    render_kb_chat("lc_kb")      # embedded chat in Learning Centre tab
"""

import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Knowledge Base stats (cached, self-healing)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300, show_spinner=False)
def load_kb_stats():
    """Fetch KB stats from the API. Cached 5 min. Returns empty dict on failure."""
    try:
        resp = requests.get(f"{API_URL}/api/knowledge/stats", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return {}
    except Exception:
        return {}


def get_kb_categories():
    """Return (category_list, stats_dict). Category list has 'All' prepended."""
    stats = load_kb_stats()
    cats = ["All"]
    cats += [c["category"] for c in stats.get("categories", [])]
    return cats, stats


def render_kb_stats_sidebar():
    """Render KB document count and word count in sidebar."""
    stats = load_kb_stats()
    total_docs = stats.get("total_documents", 0)
    total_words = stats.get("total_words", 0)
    st.markdown("### Knowledge Base")
    if total_docs > 0:
        st.caption(f"{total_docs} documents | {total_words:,} words")
    else:
        st.caption("Loading knowledge base...")
        # Clear cache so next render retries instead of showing 0 for 5 min
        load_kb_stats.clear()


# ---------------------------------------------------------------------------
# Main chat component
# ---------------------------------------------------------------------------

_DEFAULT_SUGGESTIONS = [
    "What are the golden rules for Fruit & Veg?",
    "How do I process a Dayforce leave request?",
    "What are the food safety temperature rules?",
    "How do I pick an online order?",
    "What is the bread baking schedule?",
]


def render_kb_chat(
    key_prefix,
    provider="claude",
    category=None,
    show_suggestions=True,
    suggestions=None,
    compact=False,
):
    """Render the KB chat interface.

    Args:
        key_prefix: Unique prefix for widget keys and session state.
                    E.g. "hub" for Hub Assistant, "lc_kb" for Learning Centre.
        provider: LLM provider ("claude", "chatgpt", "grok").
        category: Category filter (None = all).
        show_suggestions: Whether to show suggested questions.
        suggestions: Custom suggestion list. Defaults to standard set.
        compact: If True, use a more compact layout (no dividers).
    """
    history_key = f"{key_prefix}_chat_history"
    pending_key = f"{key_prefix}_pending_question"

    # Initialise chat history for this instance
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    # Display existing messages
    for msg in st.session_state[history_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("kb_docs"):
                with st.expander(f"Sources ({len(msg['kb_docs'])} documents)"):
                    for doc in msg["kb_docs"]:
                        st.markdown(
                            f"- **{doc['filename']}** — _{doc['category']}_"
                        )

    # Handle pending question from suggestion buttons
    user_input = None
    if pending_key in st.session_state:
        user_input = st.session_state.pop(pending_key)

    # Chat input
    if user_input is None:
        user_input = st.chat_input(
            "Ask about Harris Farm procedures...",
            key=f"{key_prefix}_chat_input",
        )

    if user_input:
        # Show user message
        st.session_state[history_key].append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.markdown(user_input)

        # Build conversation history for API
        api_history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state[history_key][:-1]
            if m["role"] in ("user", "assistant")
        ]

        # Call API
        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/api/chat",
                        json={
                            "message": user_input,
                            "history": api_history,
                            "category": category,
                            "provider": provider,
                            "user_id": "staff",
                        },
                        timeout=90,
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        answer = data["response"]
                        kb_docs = data.get("kb_docs_used", [])

                        st.markdown(answer)

                        if data.get("status") == "error":
                            st.warning(
                                "LLM returned an error. "
                                "Check API key configuration in .env"
                            )

                        if kb_docs:
                            with st.expander(
                                f"Sources ({len(kb_docs)} documents)"
                            ):
                                for doc in kb_docs:
                                    st.markdown(
                                        f"- **{doc['filename']}** "
                                        f"— _{doc['category']}_"
                                    )

                        st.session_state[history_key].append({
                            "role": "assistant",
                            "content": answer,
                            "kb_docs": kb_docs,
                            "provider": data.get("provider"),
                            "tokens": data.get("tokens"),
                            "latency_ms": data.get("latency_ms"),
                        })
                    else:
                        st.error(
                            f"API returned status {resp.status_code}. "
                            "Is the backend running?"
                        )
                except requests.exceptions.ConnectionError:
                    st.error(
                        "Could not connect to the Hub backend. "
                        "Please try again in a moment."
                    )
                except requests.exceptions.Timeout:
                    st.error(
                        "Request timed out. The LLM may be slow — try again."
                    )

    # Suggested questions (rendered below chat when empty)
    if show_suggestions and not st.session_state[history_key]:
        if suggestions is None:
            suggestions = _DEFAULT_SUGGESTIONS
        if not compact:
            st.markdown("---")
        st.markdown("**Try asking...**")
        for s in suggestions:
            if st.button(
                s,
                key=f"{key_prefix}_sug_{hash(s)}",
                use_container_width=True,
            ):
                st.session_state[pending_key] = s
                st.rerun()
