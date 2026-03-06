"""
Harris Farm Way -- Strategy Sprint
Rapid alignment on what matters most — RAG status, decisions, risks, actions.
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")

render_header(
    "Strategy Sprint",
    "Rapid alignment on what matters most \u2014 decisions, not discussions",
    goals=["G1", "G5"],
    strategy_context="The Harris Farm Way \u2014 Strategy Sprint",
)

MEETING_CONFIG = {
    "meetingType": "STRATEGY_SPRINT",
    "title": "Strategy Sprint",
    "subtitle": "Decisions, not discussions \u2014 align fast, act faster",
    "headerEmoji": "\u26A1",
    "accent": "#7C3AED",
    "storageKey": "hfm_mos_strategy_sprint_v2",
    "emailRequired": True,
    "submitUrl": "https://australia-southeast1-oval-blend-488902-p2.cloudfunctions.net/hfm-meeting-os-insert",
    "apiKey": "hfm-mos-2026",
    "welcomeTitle": "About You",
    "welcomeDescription": "Quick strategic alignment \u2014 5 minutes to capture where we are, what needs deciding, and what happens next.",
    "welcomeFields": [
        {"key": "name", "label": "Full Name", "placeholder": "Your full name", "required": True},
        {"key": "role", "label": "Role / Title", "placeholder": "e.g. Head of Buying, Store Manager", "required": True},
        {"key": "department", "label": "Department", "placeholder": "e.g. Operations, Buying, Supply Chain"},
    ],
    "sections": [
        {
            "key": "status",
            "label": "Current Status",
            "icon": "\uD83D\uDEA6",
            "description": "Where do things stand right now?",
            "cards": [
                {
                    "title": "Status Check",
                    "color": "#7C3AED",
                    "icon": "\uD83D\uDCCA",
                    "questions": [
                        {"key": "overall_rag", "type": "slider", "label": "Overall RAG (1=Red, 5=Amber, 10=Green)", "help": "How would you rate overall progress?", "color": "#7C3AED"},
                        {"key": "biggest_win", "type": "text", "label": "Biggest Win This Period", "help": "What\u2019s the single best thing that happened?", "rows": 3},
                        {"key": "biggest_risk", "type": "text", "label": "Biggest Risk Right Now", "help": "What keeps you up at night?", "rows": 3},
                    ],
                },
            ],
        },
        {
            "key": "decisions",
            "label": "Decisions Needed",
            "icon": "\uD83C\uDFAF",
            "description": "What needs to be decided in this session?",
            "cards": [
                {
                    "title": "Decisions & Blockers",
                    "color": "#DC2626",
                    "icon": "\u2757",
                    "questions": [
                        {"key": "decision_1", "type": "text", "label": "Decision 1", "help": "State the decision clearly \u2014 what, by when, who owns it.", "rows": 3},
                        {"key": "decision_2", "type": "text", "label": "Decision 2 (if any)", "help": "Another decision that needs alignment.", "rows": 3},
                        {"key": "blockers", "type": "text", "label": "Blockers", "help": "What\u2019s preventing progress that this group can unblock?", "rows": 3},
                    ],
                },
            ],
        },
        {
            "key": "next",
            "label": "Next Actions",
            "icon": "\uD83D\uDE80",
            "description": "What happens after this meeting?",
            "cards": [
                {
                    "title": "Action Plan",
                    "color": "#2D6A2D",
                    "icon": "\u2705",
                    "questions": [
                        {"key": "top_3_actions", "type": "text", "label": "Top 3 Actions", "help": "The three most important things to do next.", "rows": 4},
                        {"key": "owner_accountability", "type": "text", "label": "Who Owns What", "help": "Name the person, name the action, name the date.", "rows": 3},
                        {"key": "success_look_like", "type": "text", "label": "What Does Success Look Like?", "help": "How will we know this sprint worked?", "rows": 3},
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

render_footer("Strategy Sprint", "The Harris Farm Way", user=user)
