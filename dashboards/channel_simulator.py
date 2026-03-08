"""
Harris Farm Hub — Channel Simulator
Phone-like chat UI for testing the conversational survey engine.
Uses the same ConversationEngine as WhatsApp/SMS — in-memory session.
Always writes to the TEST BigQuery table.
"""

import streamlit as st
from shared.conversation_engine import ConversationEngine, new_session

# ---------------------------------------------------------------------------
# Session setup
# ---------------------------------------------------------------------------

_SIM_KEY = "_sim_session"
_MSG_KEY = "_sim_messages"
_CHANNEL_KEY = "_sim_channel"

engine = ConversationEngine()


def _reset():
    """Reset the simulator conversation."""
    ch = st.session_state.get(_CHANNEL_KEY, "whatsapp")
    session = new_session(ch, "simulator@harrisfarm.local")
    session["test_mode"] = True
    st.session_state[_SIM_KEY] = session
    greeting = engine.get_greeting(ch)
    st.session_state[_MSG_KEY] = [{"role": "assistant", "text": greeting}]


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.title("Channel Simulator")
st.caption(
    "Test the conversational survey flow as it would appear on "
    "WhatsApp or SMS. All submissions go to the **test** table."
)

# Channel selector
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    channel = st.radio(
        "Channel",
        ["whatsapp", "sms"],
        horizontal=True,
        key="sim_channel_radio",
    )
with col3:
    if st.button("Reset Conversation", use_container_width=True):
        st.session_state[_CHANNEL_KEY] = channel
        _reset()
        st.rerun()

# Initialise on first load or channel switch
if _SIM_KEY not in st.session_state:
    st.session_state[_CHANNEL_KEY] = channel
    _reset()

if st.session_state.get(_CHANNEL_KEY) != channel:
    st.session_state[_CHANNEL_KEY] = channel
    _reset()
    st.rerun()

# ---------------------------------------------------------------------------
# Chat display
# ---------------------------------------------------------------------------

st.markdown(
    "<style>"
    ".sim-phone {"
    "  max-width: 480px;"
    "  margin: 0 auto;"
    "  border: 2px solid rgba(0,0,0,0.1);"
    "  border-radius: 20px;"
    "  padding: 16px;"
    "  min-height: 400px;"
    "  background: #FAFAFA;"
    "}"
    "</style>",
    unsafe_allow_html=True,
)

messages = st.session_state.get(_MSG_KEY, [])

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

user_input = st.chat_input("Type your response...")

if user_input:
    session = st.session_state[_SIM_KEY]
    reply = engine.process_message(session, user_input, channel)
    st.session_state[_SIM_KEY] = session

    messages.append({"role": "user", "text": user_input})
    messages.append({"role": "assistant", "text": reply})
    st.session_state[_MSG_KEY] = messages
    st.rerun()

# ---------------------------------------------------------------------------
# Debug panel (collapsed)
# ---------------------------------------------------------------------------

with st.expander("Session State (debug)"):
    session = st.session_state.get(_SIM_KEY, {})
    st.json({
        "current_state": session.get("current_state"),
        "current_field_idx": session.get("current_field_idx"),
        "waiting_for_text": session.get("waiting_for_text"),
        "answers": session.get("answers", {}),
        "completed": session.get("completed"),
    })
