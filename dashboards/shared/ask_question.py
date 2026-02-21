"""
Harris Farm Hub — Reusable Natural Language Q&A Component
Drop into any dashboard for contextual Ask a Question with voice support.

Usage:
    from shared.ask_question import render_ask_question
    render_ask_question("sales")   # at the bottom of the dashboard
"""

import os
import re
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

from shared.schema_context import SUGGESTED_QUESTIONS

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# MAIN PUBLIC FUNCTION
# ---------------------------------------------------------------------------


def render_ask_question(page_context: str):
    """Render the Ask a Question section with voice support.

    Args:
        page_context: One of 'sales', 'profitability', 'customers',
                      'market_share', 'trending', 'store_ops',
                      'product_intel', 'revenue_bridge', 'buying_hub',
                      'general'.
    """
    st.markdown("---")
    st.subheader("Ask a Question")
    st.caption(
        f"Ask anything about your {page_context.replace('_', ' ')} data "
        "— type or use your voice"
    )

    # Voice input component
    _render_voice_input(page_context)

    # Question input form (form allows Enter key to submit)
    with st.form(key=f"nl_form_{page_context}", clear_on_submit=False):
        question = st.text_input(
            "Your question",
            value="",
            placeholder="e.g. Which store had the highest sales this week?",
            label_visibility="collapsed",
            key=f"nl_query_{page_context}",
        )
        submitted = st.form_submit_button("Ask", type="primary",
                                          use_container_width=True)

    # Suggested questions
    _render_suggested_questions(page_context)

    # Auto-read toggle
    auto_read = st.sidebar.toggle("Auto-read answers", value=False,
                                  key=f"auto_read_{page_context}")

    # Handle question
    if submitted and question and question.strip():
        _handle_question(question.strip(), page_context, auto_read)

    # Show history
    _render_history(page_context)


# ---------------------------------------------------------------------------
# QUESTION HANDLER
# ---------------------------------------------------------------------------


def _handle_question(question: str, page_context: str, auto_read: bool):
    """Process the natural language question end-to-end via backend API."""

    with st.status("Analysing your question...", expanded=True) as status:
        st.write("Understanding your question...")

        st.write("Generating query...")

        try:
            resp = requests.post(
                f"{API_URL}/api/query",
                json={
                    "question": question,
                    "dataset": page_context,
                    "user_id": "hub_user",
                },
                timeout=60,
            )
        except requests.exceptions.ConnectionError:
            status.update(label="Connection failed", state="error")
            st.error(
                "Could not connect to the Hub backend. "
                "Please try again in a moment."
            )
            return
        except Exception as e:
            status.update(label="Request failed", state="error")
            st.error(f"Query failed: {e}")
            return

        if resp.status_code != 200:
            status.update(label="Query error", state="error")
            detail = resp.json().get("detail", resp.text) if resp.text else str(resp.status_code)
            st.error(f"API error: {detail}")
            return

        result = resp.json()
        sql = result.get("generated_sql", "")
        explanation = result.get("explanation", "No explanation available.")
        rows = result.get("results", [])

        st.write("Done!")
        status.update(label="Done!", state="complete")

    # Display results
    st.markdown(f"**Question:** {question}")
    st.success(f"**Answer:** {explanation}")

    # Voice output
    _render_voice_output(explanation, auto_read, page_context)

    if rows:
        with st.expander("View Data", expanded=True):
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("View Generated SQL", expanded=False):
        st.code(sql, language="sql")

    # Feedback
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("Helpful", key=f"fb_up_{page_context}"):
            st.toast("Thanks for the feedback!")
    with col2:
        if st.button("Wrong", key=f"fb_down_{page_context}"):
            st.toast("Noted — we'll improve this query type")

    # Save to history
    if "qa_history" not in st.session_state:
        st.session_state.qa_history = []
    st.session_state.qa_history.append({
        "question": question,
        "answer": explanation,
        "sql": sql,
        "timestamp": datetime.now(),
        "page": page_context,
    })


# ---------------------------------------------------------------------------
# SUGGESTED QUESTIONS
# ---------------------------------------------------------------------------


def _render_suggested_questions(page_context: str):
    """Show clickable suggested questions relevant to the current page."""
    suggestions = SUGGESTED_QUESTIONS.get(
        page_context, SUGGESTED_QUESTIONS.get("general", [])
    )
    if not suggestions:
        return

    with st.expander("Suggested questions", expanded=False):
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(suggestion,
                             key=f"suggest_{page_context}_{i}",
                             use_container_width=True):
                    st.session_state[f"nl_query_{page_context}"] = suggestion
                    st.rerun()


# ---------------------------------------------------------------------------
# SESSION HISTORY
# ---------------------------------------------------------------------------


def _render_history(page_context: str):
    """Show previous Q&A pairs from this session."""
    history = st.session_state.get("qa_history", [])
    if not history:
        return

    with st.expander(
        f"Previous Questions ({len(history)})", expanded=False
    ):
        for qa in reversed(history):
            st.markdown(f"**Q:** {qa['question']}")
            st.markdown(f"**A:** {qa['answer'][:300]}...")
            st.caption(
                f"{qa['timestamp'].strftime('%H:%M')} · "
                f"{qa['page'].replace('_', ' ')} dashboard"
            )
            st.markdown("---")


# ---------------------------------------------------------------------------
# VOICE INPUT  (Web Speech API — browser-native, no cost)
# ---------------------------------------------------------------------------


def _render_voice_input(page_context: str):
    """Render a microphone button that uses the browser's speech-to-text."""
    voice_html = """
    <div id="voice-container" style="display:flex;align-items:center;gap:10px;font-family:sans-serif;margin-bottom:6px;">
        <button id="mic-btn" onclick="toggleMic()" style="
            background:#f0f2f6;border:1px solid #ddd;border-radius:50%;
            width:42px;height:42px;cursor:pointer;font-size:18px;
            display:flex;align-items:center;justify-content:center;
            transition:all 0.2s ease;" title="Click to speak">&#127908;</button>
        <span id="mic-status" style="color:#666;font-size:13px;"></span>
    </div>

    <script>
    let recognition = null;
    let isListening = false;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SR();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-AU';

        recognition.onresult = (e) => {
            let transcript = '';
            for (let i = e.resultIndex; i < e.results.length; i++) {
                transcript += e.results[i][0].transcript;
            }
            document.getElementById('mic-status').textContent = transcript;

            if (e.results[e.results.length - 1].isFinal) {
                // Try to populate the Streamlit text input
                const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                const nlInput = Array.from(inputs).find(i =>
                    i.placeholder && i.placeholder.includes('e.g.')
                );
                if (nlInput) {
                    const setter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    setter.call(nlInput, transcript);
                    nlInput.dispatchEvent(new Event('input', {bubbles:true}));
                    nlInput.dispatchEvent(new Event('change', {bubbles:true}));
                }
            }
        };

        recognition.onend = () => {
            isListening = false;
            document.getElementById('mic-btn').style.background = '#f0f2f6';
            document.getElementById('mic-btn').style.boxShadow = 'none';
            if (!document.getElementById('mic-status').textContent.startsWith('Please'))
                document.getElementById('mic-status').textContent = '';
        };

        recognition.onerror = (e) => {
            isListening = false;
            document.getElementById('mic-btn').style.background = '#f0f2f6';
            if (e.error === 'not-allowed') {
                document.getElementById('mic-status').textContent = 'Please allow microphone access';
            }
        };
    } else {
        document.getElementById('mic-btn').style.display = 'none';
        document.getElementById('mic-status').textContent = 'Voice not supported in this browser';
    }

    function toggleMic() {
        if (!recognition) return;
        // Stop any speech output to avoid feedback loop
        if (window.parent.speechSynthesis) window.parent.speechSynthesis.cancel();

        if (isListening) {
            recognition.stop();
            isListening = false;
        } else {
            recognition.start();
            isListening = true;
            document.getElementById('mic-btn').style.background = '#ef4444';
            document.getElementById('mic-btn').style.boxShadow = '0 0 0 3px rgba(239,68,68,0.3)';
            document.getElementById('mic-status').textContent = 'Listening...';
        }
    }
    </script>
    """
    components.html(voice_html, height=50, scrolling=False)


# ---------------------------------------------------------------------------
# VOICE OUTPUT  (SpeechSynthesis API — browser-native, no cost)
# ---------------------------------------------------------------------------


def _render_voice_output(text: str, auto_read: bool, page_context: str):
    """Render a Read Aloud button that speaks the answer."""
    # Clean text for speech
    clean = re.sub(r"[*#_~`]", "", text)
    clean = re.sub(r":[a-z_]+:", "", clean)
    clean = clean.replace("\n", ". ").replace("\r", "")
    clean = clean.replace("'", "\\'").replace('"', '\\"')

    auto_flag = "true" if auto_read else "false"

    speech_html = f"""
    <div style="margin:8px 0;">
        <button id="speak-btn" onclick="toggleSpeak()" style="
            background:#f0f2f6;border:1px solid #ddd;border-radius:20px;
            padding:6px 16px;cursor:pointer;font-size:13px;
            display:inline-flex;align-items:center;gap:6px;
            transition:all 0.2s ease;color:#333;">
            <span id="speak-icon">&#128264;</span>
            <span id="speak-label">Read Answer Aloud</span>
        </button>
    </div>

    <script>
    let isSpeaking = false;
    const autoRead = {auto_flag};

    function speakText() {{
        const synth = window.parent.speechSynthesis || window.speechSynthesis;
        if (!synth) return;

        const text = '{clean}';
        const utt = new SpeechSynthesisUtterance(text);

        // Prefer Australian English voices
        const voices = synth.getVoices();
        const tests = [
            v => v.name === 'Karen',
            v => v.name === 'Samantha',
            v => v.name.includes('Enhanced'),
            v => v.name.includes('Premium'),
            v => v.lang === 'en-AU',
            v => v.lang.startsWith('en')
        ];
        let voice = null;
        for (const t of tests) {{ voice = voices.find(t); if (voice) break; }}
        if (voice) utt.voice = voice;

        utt.rate = 0.95;
        utt.pitch = 1.05;
        utt.lang = 'en-AU';

        utt.onstart = () => {{
            isSpeaking = true;
            document.getElementById('speak-label').textContent = 'Stop Reading';
            document.getElementById('speak-icon').innerHTML = '&#9209;&#65039;';
            document.getElementById('speak-btn').style.background = '#e8f5e9';
        }};
        utt.onend = () => {{
            isSpeaking = false;
            document.getElementById('speak-label').textContent = 'Read Answer Aloud';
            document.getElementById('speak-icon').innerHTML = '&#128264;';
            document.getElementById('speak-btn').style.background = '#f0f2f6';
        }};

        synth.speak(utt);
    }}

    function toggleSpeak() {{
        const synth = window.parent.speechSynthesis || window.speechSynthesis;
        if (isSpeaking) {{
            synth.cancel();
            isSpeaking = false;
            document.getElementById('speak-label').textContent = 'Read Answer Aloud';
            document.getElementById('speak-icon').innerHTML = '&#128264;';
            document.getElementById('speak-btn').style.background = '#f0f2f6';
            return;
        }}
        speakText();
    }}

    // Load voices (needed for Chrome)
    if (window.parent.speechSynthesis) {{
        window.parent.speechSynthesis.onvoiceschanged = () => {{}};
    }}

    // Auto-read if enabled
    if (autoRead) {{
        setTimeout(speakText, 500);
    }}
    </script>
    """
    components.html(speech_html, height=50, scrolling=False)
