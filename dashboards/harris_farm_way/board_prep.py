"""
Harris Farm Way -- Board Prep
Board-ready in one session — highlights, metrics, decisions, risks.
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")

render_header(
    "Board Prep",
    "Board-ready in one session \u2014 structured input from every key voice",
    goals=["G1", "G5"],
    strategy_context="The Harris Farm Way \u2014 Board Prep",
)

MEETING_CONFIG = {
    "meetingType": "BOARD_PREP",
    "title": "Board Prep",
    "subtitle": "Board-ready in one session \u2014 the right information from the right people",
    "headerEmoji": "\uD83C\uDFDB\uFE0F",
    "accent": "#E8B84B",
    "storageKey": "hfm_mos_board_prep_v2",
    "emailRequired": True,
    "submitUrl": "https://australia-southeast1-oval-blend-488902-p2.cloudfunctions.net/hfm-meeting-os-insert",
    "apiKey": "hfm-mos-2026",
    "welcomeTitle": "About You",
    "welcomeDescription": "Your structured input helps build a clear, honest board pack. Takes 10 minutes.",
    "welcomeFields": [
        {"key": "name", "label": "Full Name", "placeholder": "Your full name", "required": True},
        {"key": "role", "label": "Role / Title", "placeholder": "e.g. Co-CEO, Head of Operations", "required": True},
        {"key": "department", "label": "Department", "placeholder": "e.g. Executive, Operations, Finance", "required": True},
    ],
    "sections": [
        {
            "key": "highlights",
            "label": "Highlights & Performance",
            "icon": "\uD83C\uDFC6",
            "description": "What should the board know first?",
            "cards": [
                {
                    "title": "Performance Snapshot",
                    "color": "#E8B84B",
                    "icon": "\uD83D\uDCCA",
                    "questions": [
                        {"key": "top_highlight", "type": "text", "label": "Top Highlight", "help": "The single most important thing to share with the board.", "rows": 3},
                        {"key": "performance_summary", "type": "text", "label": "Performance Summary", "help": "2\u20133 sentences on how we\u2019re tracking against plan.", "rows": 3},
                        {"key": "confidence_level", "type": "slider", "label": "Confidence in Hitting Targets", "help": "How confident are you that we\u2019ll hit this year\u2019s targets?", "color": "#E8B84B"},
                    ],
                },
            ],
        },
        {
            "key": "decisions",
            "label": "Decisions & Approvals",
            "icon": "\u2705",
            "description": "What does the board need to decide or approve?",
            "cards": [
                {
                    "title": "Board Decisions",
                    "color": "#DC2626",
                    "icon": "\u2757",
                    "questions": [
                        {"key": "decisions_required", "type": "text", "label": "Decisions Required", "help": "List each decision clearly \u2014 what, why, recommended action.", "rows": 4},
                        {"key": "investment_asks", "type": "text", "label": "Investment Asks", "help": "Any capital or operating expenditure that needs approval.", "rows": 3},
                    ],
                },
            ],
        },
        {
            "key": "risks",
            "label": "Risks & Outlook",
            "icon": "\uD83D\uDD2D",
            "description": "What should the board be watching?",
            "cards": [
                {
                    "title": "Risk & Outlook",
                    "color": "#7C3AED",
                    "icon": "\uD83C\uDF1F",
                    "questions": [
                        {"key": "top_risks", "type": "text", "label": "Top 3 Risks", "help": "The three biggest risks and what we\u2019re doing about each.", "rows": 4},
                        {"key": "outlook", "type": "text", "label": "6-Month Outlook", "help": "Where do you expect us to be in 6 months?", "rows": 3},
                        {"key": "board_message", "type": "text", "label": "One Thing the Board Should Know", "help": "If you could tell the board one thing, what would it be?", "rows": 3},
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

render_footer("Board Prep", "The Harris Farm Way", user=user)
