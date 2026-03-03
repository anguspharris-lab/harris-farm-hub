"""
Harris Farm Hub — Supply Chain Interview Tool
Embeds the React interview artifact (hfm-interview-v5) via st.components.html().
5-section stakeholder interview for supply chain transformation diagnostic.
"""

import streamlit as st
import streamlit.components.v1 as components

from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")

render_header(
    "Supply Chain Interview",
    "Stakeholder interview tool for supply chain transformation diagnostic",
    goals=["G5"],
    strategy_context="Pillar 5 — Tomorrow's Business: AI, innovation, growth",
)

st.markdown(
    "<div style='background:rgba(249,115,22,0.08);border:1px solid rgba(249,115,22,0.2);"
    "border-radius:10px;padding:14px 18px;margin-bottom:20px;'>"
    "<div style='font-weight:600;color:#F97316;font-size:0.95em;'>How to use</div>"
    "<div style='color:#B0BEC5;font-size:0.88em;line-height:1.5;'>"
    "Complete each section using the Next button. Your progress auto-saves. "
    "On the final section, hit Submit — your response is saved to the database "
    "and a backup JSON file is downloaded automatically.</div>"
    "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Embedded React Interview Artifact
# ---------------------------------------------------------------------------

_INTERVIEW_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0A0F0A; color: #F1F8E9; font-family: 'Trebuchet MS', 'Segoe UI', sans-serif; }
  input[type="range"] { -webkit-appearance: none; height: 6px; border-radius: 3px; background: rgba(255,255,255,0.12); outline: none; }
  input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; width: 20px; height: 20px; border-radius: 50%; cursor: pointer; }
  textarea:focus, input:focus { outline: none; border-color: rgba(46,204,113,0.5) !important; }
  ::selection { background: rgba(46,204,113,0.3); }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
</style>
</head>
<body>
<div id="root"></div>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>
<script type="text/babel">
""" + open(
    str(__import__("pathlib").Path(__file__).resolve().parent.parent / "artifacts" / "hfm-interview-v5.jsx")
).read() + """
</script>
</body>
</html>
"""

components.html(_INTERVIEW_HTML, height=1200, scrolling=True)

render_footer("SC Interview", "Supply Chain Transformation Program", user=user)
