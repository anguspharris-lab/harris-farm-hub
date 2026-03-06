"""
Harris Farm Way -- Department One-Pager
Your department at a glance — results, priorities, blockers, asks.
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")

render_header(
    "Department One-Pager",
    "Your department at a glance \u2014 what matters, what\u2019s working, what needs help",
    goals=["G1"],
    strategy_context="The Harris Farm Way \u2014 Department One-Pager",
)

MEETING_CONFIG = {
    "meetingType": "DEPT_ONE_PAGER",
    "title": "Department One-Pager",
    "subtitle": "Your department at a glance \u2014 results, priorities, and what you need",
    "headerEmoji": "\uD83D\uDCCB",
    "accent": "#0891B2",
    "storageKey": "hfm_mos_dept_one_pager_v2",
    "emailRequired": True,
    "submitUrl": "https://australia-southeast1-oval-blend-488902-p2.cloudfunctions.net/hfm-meeting-os-insert",
    "apiKey": "hfm-mos-2026",
    "welcomeTitle": "About You",
    "welcomeDescription": "Quick and focused \u2014 capture the state of your department in 5 minutes.",
    "welcomeFields": [
        {"key": "name", "label": "Full Name", "placeholder": "Your full name", "required": True},
        {"key": "role", "label": "Role / Title", "placeholder": "e.g. Department Head, Team Lead", "required": True},
        {"key": "department", "label": "Department", "placeholder": "e.g. Buying, Operations, Supply Chain", "required": True},
    ],
    "sections": [
        {
            "key": "results",
            "label": "Results & Highlights",
            "icon": "\uD83C\uDFC6",
            "description": "How did we go this period?",
            "cards": [
                {
                    "title": "Performance",
                    "color": "#0891B2",
                    "icon": "\uD83D\uDCCA",
                    "questions": [
                        {"key": "performance_rating", "type": "slider", "label": "Overall Performance (1=Poor, 10=Excellent)", "help": "How would you rate your department\u2019s performance?", "color": "#0891B2"},
                        {"key": "top_highlight", "type": "text", "label": "Top Highlight", "help": "The one thing you\u2019re most proud of this period.", "rows": 3},
                        {"key": "key_metrics", "type": "text", "label": "Key Metrics", "help": "2\u20133 numbers that tell the story of your department.", "rows": 3},
                    ],
                },
            ],
        },
        {
            "key": "priorities",
            "label": "Priorities & Blockers",
            "icon": "\uD83C\uDFAF",
            "description": "What\u2019s next and what\u2019s in the way?",
            "cards": [
                {
                    "title": "Looking Ahead",
                    "color": "#2D6A2D",
                    "icon": "\uD83D\uDE80",
                    "questions": [
                        {"key": "top_3_priorities", "type": "text", "label": "Top 3 Priorities", "help": "The three most important things for the next period.", "rows": 4},
                        {"key": "blockers", "type": "text", "label": "Blockers & Asks", "help": "What do you need from other departments or leadership to succeed?", "rows": 3},
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

components.html(_HTML, height=1200, scrolling=True)

render_footer("Dept One-Pager", "The Harris Farm Way", user=user)
