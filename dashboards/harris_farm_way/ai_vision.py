"""
Harris Farm Way -- AI Vision Session
Where we imagine what's possible — AI capability, blockers, lighthouse opportunities.
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")

render_header(
    "AI Vision Session",
    "Where we imagine what\u2019s possible \u2014 your input shapes our AI future",
    goals=["G3", "G5"],
    strategy_context="The Harris Farm Way \u2014 AI Vision",
)

MEETING_CONFIG = {
    "meetingType": "AI_VISION",
    "title": "AI Vision Session",
    "subtitle": "Imagine what\u2019s possible \u2014 then let\u2019s build it together",
    "headerEmoji": "\uD83E\uDDE0",
    "accent": "#2D6A2D",
    "storageKey": "hfm_mos_ai_vision_v2",
    "emailRequired": True,
    "submitUrl": "https://australia-southeast1-oval-blend-488902-p2.cloudfunctions.net/hfm-meeting-os-insert",
    "apiKey": "hfm-mos-2026",
    "welcomeTitle": "About You",
    "welcomeDescription": "This session takes 10\u201315 minutes. Your honest perspective on AI helps us focus our efforts where they\u2019ll make the biggest difference.",
    "welcomeFields": [
        {"key": "name", "label": "Full Name", "placeholder": "Your full name", "required": True},
        {"key": "role", "label": "Role / Title", "placeholder": "e.g. Store Manager, Buyer, Head of Ops", "required": True},
        {"key": "department", "label": "Department", "placeholder": "e.g. Operations, Buying, IT"},
    ],
    "sections": [
        {
            "key": "capability",
            "label": "Current AI Capability",
            "icon": "\uD83D\uDCCA",
            "description": "How would you rate your team\u2019s current AI readiness?",
            "cards": [
                {
                    "title": "AI Readiness Scores",
                    "color": "#2D6A2D",
                    "icon": "\uD83C\uDFAF",
                    "description": "Rate each dimension from 1 (critical gap) to 10 (well-prepared).",
                    "questions": [
                        {"key": "ai_awareness", "type": "slider", "label": "AI Awareness", "help": "How well does your team understand what AI can do?"},
                        {"key": "ai_usage", "type": "slider", "label": "Current AI Usage", "help": "How much is AI being used in day-to-day work?"},
                        {"key": "data_readiness", "type": "slider", "label": "Data Readiness", "help": "Is your data clean and accessible enough for AI?"},
                    ],
                },
            ],
        },
        {
            "key": "blockers",
            "label": "Blockers & Concerns",
            "icon": "\uD83D\uDEA7",
            "description": "Understanding what\u2019s holding us back is the first step to moving forward.",
            "cards": [
                {
                    "title": "What\u2019s In the Way?",
                    "color": "#F97316",
                    "icon": "\u26A0\uFE0F",
                    "questions": [
                        {"key": "biggest_blocker", "type": "text", "label": "Biggest Blocker", "help": "What is the single biggest thing preventing AI adoption in your area?", "rows": 3},
                        {"key": "concerns", "type": "text", "label": "Concerns", "help": "What worries you about AI in the workplace?", "rows": 3},
                        {"key": "skills_gap", "type": "text", "label": "Skills Gap", "help": "What skills does your team need to develop?", "rows": 3},
                    ],
                },
            ],
        },
        {
            "key": "lighthouse",
            "label": "Lighthouse Opportunities",
            "icon": "\uD83D\uDCA1",
            "description": "If AI could solve one problem perfectly, what would it be?",
            "cards": [
                {
                    "title": "The Big Opportunity",
                    "color": "#06B6D4",
                    "icon": "\uD83C\uDF1F",
                    "questions": [
                        {"key": "lighthouse_opportunity", "type": "text", "label": "Lighthouse Opportunity", "help": "Describe the one process or problem where AI would make the biggest difference.", "rows": 4},
                        {"key": "impact_if_solved", "type": "text", "label": "Impact If Solved", "help": "What would change if this was solved well?", "rows": 3},
                        {"key": "quick_wins", "type": "text", "label": "Quick Wins", "help": "What are 2\u20133 small things AI could help with right now?", "rows": 3},
                    ],
                },
            ],
        },
    ],
}

_JSX_PATH = str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent / "artifacts" / "hfm-meeting-os.jsx")

_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #FAFAF7; color: #1A1A1A; font-family: 'Trebuchet MS', 'Segoe UI', sans-serif; }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 3px; }
</style>
</head>
<body>
<div id="root"></div>
<script>window.__MEETING_CONFIG__ = """ + json.dumps(MEETING_CONFIG) + """;</script>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>
<script type="text/babel">
""" + open(_JSX_PATH).read() + """
</script>
</body>
</html>
"""

components.html(_HTML, height=1400, scrolling=True)

render_footer("AI Vision", "The Harris Farm Way", user=user)
