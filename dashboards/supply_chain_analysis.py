"""
Harris Farm Hub — Supply Chain Analysis Dashboard
Embeds the React analysis artifact (hfm-analysis-v5) via st.components.html().
Claude-powered analysis: upload interview JSONs, get ADKAR diagnostics automatically.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

from shared.styles import render_header, render_footer
from shared.bigquery_connector import is_bigquery_available, get_sc_responses

_log = logging.getLogger(__name__)

user = st.session_state.get("auth_user")

render_header(
    "Supply Chain Analysis",
    "AI-powered diagnostic from stakeholder interviews",
    goals=["G5"],
    strategy_context="Pillar 5 — Tomorrow's Business: AI, innovation, growth",
)

# ---------------------------------------------------------------------------
# Session state for responses and analysis
# ---------------------------------------------------------------------------

if "sc_responses" not in st.session_state:
    st.session_state["sc_responses"] = []
if "sc_analysis" not in st.session_state:
    st.session_state["sc_analysis"] = None
if "sc_bq_loaded" not in st.session_state:
    st.session_state["sc_bq_loaded"] = False

# ---------------------------------------------------------------------------
# Load from BigQuery (primary data source)
# ---------------------------------------------------------------------------

if not st.session_state["sc_bq_loaded"] and is_bigquery_available():
    try:
        bq_responses = get_sc_responses()
        if bq_responses:
            existing_names = {
                r.get("respondent", {}).get("name", "")
                for r in st.session_state["sc_responses"]
            }
            added = 0
            for resp in bq_responses:
                name = resp.get("respondent", {}).get("name", "")
                if name and name not in existing_names:
                    st.session_state["sc_responses"].append(resp)
                    existing_names.add(name)
                    added += 1
            if added:
                st.toast(f"Loaded {added} response(s) from BigQuery")
        st.session_state["sc_bq_loaded"] = True
    except Exception as e:
        _log.warning("Failed to load SC responses from BigQuery: %s", e)

# ---------------------------------------------------------------------------
# File uploader (supplementary — for offline JSON files)
# ---------------------------------------------------------------------------

with st.expander("Upload additional JSON files"):
    uploaded = st.file_uploader(
        "Upload interview JSON files",
        type=["json"],
        accept_multiple_files=True,
        help="Upload JSON files exported from the SC Interview tool (supplements BigQuery data)",
    )

    if uploaded:
        existing_names = {
            r.get("respondent", {}).get("name", "")
            for r in st.session_state["sc_responses"]
        }
        added = 0
        for f in uploaded:
            try:
                data = json.loads(f.read())
                name = data.get("respondent", {}).get("name", "")
                if name and name not in existing_names:
                    st.session_state["sc_responses"].append(data)
                    existing_names.add(name)
                    added += 1
            except (json.JSONDecodeError, KeyError):
                st.warning(f"Could not parse {f.name}")
        if added:
            st.success(f"Added {added} new response(s). Total: {len(st.session_state['sc_responses'])}")

# Response count
n = len(st.session_state["sc_responses"])
if n > 0:
    names = [r.get("respondent", {}).get("name", "?") for r in st.session_state["sc_responses"]]
    st.markdown(
        f"<div style='background:rgba(46,204,113,0.08);border:1px solid rgba(46,204,113,0.2);"
        f"border-radius:10px;padding:12px 16px;margin-bottom:16px;'>"
        f"<span style='font-weight:600;color:#2ECC71;'>{n} response(s)</span>"
        f"<span style='color:#B0BEC5;font-size:0.88em;margin-left:12px;'>"
        f"{', '.join(names)}</span></div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Claude analysis button
# ---------------------------------------------------------------------------

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    analyse_btn = st.button(
        "Analyse with Claude",
        disabled=n == 0,
        use_container_width=True,
        type="primary",
    )

with col2:
    if st.button("Refresh from BigQuery", use_container_width=True):
        st.session_state["sc_responses"] = []
        st.session_state["sc_analysis"] = None
        st.session_state["sc_bq_loaded"] = False
        st.rerun()

with col3:
    if st.button("Clear All", disabled=n == 0, use_container_width=True):
        st.session_state["sc_responses"] = []
        st.session_state["sc_analysis"] = None
        st.session_state["sc_bq_loaded"] = True  # Don't re-fetch on clear
        st.rerun()


def call_claude_analysis(responses):
    """Send all responses to Claude for ADKAR + capability analysis."""
    try:
        import anthropic
    except ImportError:
        st.error("anthropic package not installed")
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not set")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are an organisational change analyst. Analyse these {len(responses)} supply chain stakeholder interview responses for Harris Farm Markets.

Return ONLY valid JSON (no markdown, no code fences) with this exact structure:
{{
  "one_page_summary": "3-4 sentence executive summary of findings",
  "adkar_summary": {{
    "Awareness": {{"score": <avg>, "interpretation": "Strong|Adequate|Gap|Critical", "themes": "key themes from responses"}},
    "Desire": {{"score": <avg>, "interpretation": "...", "themes": "..."}},
    "Knowledge": {{"score": <avg>, "interpretation": "...", "themes": "..."}},
    "Ability": {{"score": <avg>, "interpretation": "...", "themes": "..."}},
    "Reinforcement": {{"score": <avg>, "interpretation": "...", "themes": "..."}}
  }},
  "capability_gaps": [
    {{"capability": "name", "avg_score": <n>, "interpretation": "...", "intervention": "recommended action"}}
  ],
  "themes": [
    {{"theme": "theme title", "detail": "supporting evidence and quotes from responses"}}
  ],
  "alignment": {{
    "agrees": ["areas of strong agreement"],
    "disagrees": ["areas of high variance / disagreement"]
  }},
  "recommendations": [
    {{"action": "description of recommended action", "priority": "High|Medium|Low", "rationale": "why"}}
  ]
}}

ADKAR scoring interpretation: 8-10 = Strong, 6-7 = Adequate, 4-5 = Gap, 1-3 = Critical.
The ADKAR scores map from the interview as: Awareness=urgency, Desire=desire, Knowledge=clarity, Ability=readiness, Reinforcement=sustain.

Interview Responses:
{json.dumps(responses, indent=2)}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text)
    except json.JSONDecodeError as e:
        st.error(f"Claude returned invalid JSON: {e}")
        st.code(text[:500])
        return None
    except Exception as e:
        st.error(f"Claude API error: {e}")
        return None


if analyse_btn and n > 0:
    with st.spinner("Analysing responses with Claude..."):
        result = call_claude_analysis(st.session_state["sc_responses"])
        if result:
            st.session_state["sc_analysis"] = result
            st.success("Analysis complete")

# ---------------------------------------------------------------------------
# Embedded React Analysis Artifact
# ---------------------------------------------------------------------------

_ARTIFACT_PATH = Path(__file__).resolve().parent.parent / "artifacts" / "hfm-analysis-v5.jsx"


def _build_analysis_html(responses, ai_analysis):
    """Build the full HTML page with React artifact and injected data."""
    jsx_code = ""
    if _ARTIFACT_PATH.exists():
        jsx_code = _ARTIFACT_PATH.read_text()
    else:
        jsx_code = "const root = ReactDOM.createRoot(document.getElementById('root')); root.render(React.createElement('div', {style:{color:'#EF4444'}}, 'Artifact file not found'));"

    # Inject data into the component via postMessage after render
    responses_json = json.dumps(responses)
    ai_json = json.dumps(ai_analysis) if ai_analysis else "null"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0A0F0A; color: #F1F8E9; font-family: 'Trebuchet MS', 'Segoe UI', sans-serif; }}
  textarea:focus, input:focus {{ outline: none; border-color: rgba(46,204,113,0.5) !important; }}
  ::selection {{ background: rgba(46,204,113,0.3); }}
  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-track {{ background: transparent; }}
  ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.15); border-radius: 3px; }}
</style>
</head>
<body>
<div id="root"></div>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>
<script type="text/babel">
{jsx_code}
</script>
<script>
// Inject data after React renders
setTimeout(function() {{
  var responses = {responses_json};
  var aiInsights = {ai_json};
  // Send AI insights to the React component
  if (aiInsights) {{
    window.postMessage({{ type: "ai_insights", payload: aiInsights }}, "*");
  }}
  // Pre-populate responses via localStorage (React reads on mount)
  try {{
    var stored = JSON.parse(localStorage.getItem("hfm_sc_analysis_v5") || "{{}}");
    stored.responses = responses;
    if (aiInsights) stored.aiInsights = aiInsights;
    localStorage.setItem("hfm_sc_analysis_v5", JSON.stringify(stored));
    // Trigger re-render by dispatching storage event
    window.dispatchEvent(new Event("storage"));
  }} catch(e) {{}}
}}, 500);
</script>
</body>
</html>"""


# Only render the artifact if there are responses
if n > 0:
    html = _build_analysis_html(
        st.session_state["sc_responses"],
        st.session_state.get("sc_analysis"),
    )
    components.html(html, height=1400, scrolling=True)
else:
    if is_bigquery_available():
        st.info("No interview responses found in the database yet. Complete an interview to get started.")
    else:
        st.info("BigQuery unavailable. Upload interview JSON files above to begin analysis.")

render_footer("SC Analysis", "Supply Chain Transformation Program", user=user)
