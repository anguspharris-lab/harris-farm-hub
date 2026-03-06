"""
Harris Farm Hub — Supply Chain Interview Tool
Uses the universal Meeting OS artifact (hfm-meeting-os.jsx) with SCR-specific config.
5-section stakeholder interview for supply chain transformation diagnostic.
Submits to legacy hfm-scr-insert Cloud Function via mapped format.
"""

import json
import streamlit as st
import streamlit.components.v1 as components

from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")

render_header(
    "Supply Chain Review",
    "This is how we listen before we lead \u2014 Chapter 1 of our transformation story",
    goals=["G4", "G5"],
    strategy_context="The Harris Farm Way \u2014 Supply Chain Transformation",
)

st.markdown(
    "<div style='background:rgba(45,106,45,0.06);border:1px solid rgba(45,106,45,0.15);"
    "border-radius:10px;padding:14px 18px;margin-bottom:20px;'>"
    "<div style='font-weight:600;color:#2D6A2D;font-size:0.95em;'>How to use</div>"
    "<div style='color:#4A5568;font-size:0.88em;line-height:1.5;'>"
    "Complete each section using the Next button. Your progress auto-saves. "
    "On the final section, hit Submit \u2014 your response is saved to the database "
    "and a backup JSON file is downloaded automatically.</div>"
    "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Meeting config — maps all SCR questions into the universal artifact
# ---------------------------------------------------------------------------

MEETING_CONFIG = {
    "meetingType": "SCR",
    "title": "Supply Chain Transformation",
    "subtitle": "Harris Farm Markets \u2014 Stakeholder Interview",
    "headerEmoji": "\uD83D\uDE9B",
    "accent": "#2D6A2D",
    "storageKey": "hfm_sc_interview_v6",
    "emailRequired": False,
    "submitUrl": "https://australia-southeast1-oval-blend-488902-p2.cloudfunctions.net/hfm-scr-insert",
    "apiKey": "hfm-scr-2026",
    "submitFormat": "mapped",
    "submitMap": {
        "name": "name",
        "role": "role",
        "sc_touch": "sc_touchpoint",
        "five_year_confidence": "confidence",
        "leverage_strengths": "leverage",
        "urgency": "urgency",
        "desire_score": "desire",
        "clarity_score": "clarity",
        "readiness_score": "readiness",
        "sustain_score": "sustain",
        "rf_visibility": "visibility",
        "rf_disruption": "disruption_response",
        "rf_data": "data_quality",
        "rf_technology": "technology",
        "rf_suppliers": "suppliers",
        "rf_transport": "transport",
        "rf_demand": "demand_planning",
        "rf_sustainability": "sustainability",
        "protect_processes": "protect",
        "external_pressures": "external_pressures",
        "worries": "worries",
        "ideal_5yr": "ideal_5yr",
        "one_big_thing": "one_big_thing",
        "customer_impact": "impact_if_successful",
        "additional": "additional_comments",
    },
    "welcomeTitle": "About You",
    "welcomeDescription": "This interview takes 10\u201315 minutes. Your responses will help shape our supply chain transformation program. All answers are confidential and used for diagnostic purposes only.",
    "welcomeFields": [
        {"key": "name", "label": "Your Name", "placeholder": "Full name", "required": True},
        {"key": "role", "label": "Your Role", "placeholder": "e.g. Head of Logistics, Store Manager", "required": True},
        {"key": "department", "label": "Department", "placeholder": "e.g. Supply Chain, Operations, Buying"},
        {"key": "sc_touchpoint", "label": "How does supply chain touch your day-to-day?", "type": "textarea", "help": "What parts of the supply chain do you interact with most?", "rows": 3},
        {"key": "confidence", "label": "5-Year Confidence", "type": "slider", "help": "How confident are you that our current supply chain can support HFM\u2019s growth over the next 5 years?", "color": "#2D6A2D"},
    ],
    "sections": [
        {
            "key": "working",
            "label": "What's Working",
            "icon": "\uD83D\uDEE1\uFE0F",
            "description": "Protecting what works while identifying what needs to change.",
            "cards": [
                {
                    "title": "What to Protect",
                    "color": "#2D6A2D",
                    "icon": "\uD83C\uDF31",
                    "questions": [
                        {"key": "protect", "type": "text", "label": "What\u2019s working well that we should protect?", "help": "What parts of our supply chain work well today? What would you NOT want to change?", "rows": 4},
                    ],
                },
                {
                    "title": "Pressures & Challenges",
                    "color": "#F97316",
                    "icon": "\u26A0\uFE0F",
                    "questions": [
                        {"key": "pain_points", "type": "text", "label": "What are the biggest pain points?", "help": "Where does the supply chain create friction, delays, or waste?", "rows": 4},
                        {"key": "external_pressures", "type": "text", "label": "What external pressures concern you?", "help": "Market changes, competitor moves, regulatory shifts, supplier risks...", "rows": 3},
                    ],
                },
                {
                    "title": "Scores",
                    "color": "#E8B84B",
                    "questions": [
                        {"key": "leverage", "type": "slider", "label": "Leverage", "help": "How well do we leverage our existing supply chain strengths?", "color": "#E8B84B"},
                        {"key": "urgency", "type": "slider", "label": "Urgency", "help": "How urgent is supply chain transformation for HFM right now?", "color": "#F97316"},
                    ],
                },
            ],
        },
        {
            "key": "adkar",
            "label": "Change Readiness",
            "icon": "\uD83E\uDDE0",
            "description": "ADKAR measures five dimensions of change readiness: Awareness, Desire, Knowledge, Ability, Reinforcement.",
            "cards": [
                {
                    "title": "Change Readiness (ADKAR)",
                    "color": "#8B5CF6",
                    "icon": "\uD83D\uDCAC",
                    "description": "Rate each on a 1\u201310 scale for our supply chain transformation.",
                    "questions": [
                        {"key": "excites", "type": "text", "label": "What excites you about transforming our supply chain?", "rows": 3},
                        {"key": "worries", "type": "text", "label": "What worries you about it?", "rows": 3},
                    ],
                },
                {
                    "title": "ADKAR Dimensions",
                    "color": "#8B5CF6",
                    "questions": [
                        {"key": "urgency", "type": "slider", "label": "Awareness", "help": "Does the team understand WHY supply chain change is needed?", "color": "#EF4444"},
                        {"key": "desire", "type": "slider", "label": "Desire", "help": "Does the team WANT this transformation to happen?", "color": "#F97316"},
                        {"key": "clarity", "type": "slider", "label": "Knowledge", "help": "Does the team know WHAT good looks like and HOW to get there?", "color": "#E8B84B"},
                        {"key": "readiness", "type": "slider", "label": "Ability", "help": "Can the organisation EXECUTE the transformation right now?", "color": "#3B82F6"},
                        {"key": "sustain", "type": "slider", "label": "Reinforcement", "help": "Will changes STICK? Can we sustain new ways of working?", "color": "#8B5CF6"},
                    ],
                },
            ],
        },
        {
            "key": "vision",
            "label": "The Vision",
            "icon": "\uD83D\uDD2D",
            "description": "Paint the picture of what world-class looks like for Harris Farm.",
            "cards": [
                {
                    "title": "The Vision",
                    "color": "#06B6D4",
                    "icon": "\uD83C\uDF1F",
                    "questions": [
                        {"key": "ideal_5yr", "type": "text", "label": "What does a world-class supply chain look like for HFM in 5 years?", "help": "Paint the picture. What would be different? What would it feel like?", "rows": 5},
                        {"key": "one_big_thing", "type": "text", "label": "If you could change ONE big thing, what would it be?", "help": "The single highest-impact change you\u2019d make", "rows": 3},
                        {"key": "impact_if_successful", "type": "text", "label": "If we get this right, what\u2019s the impact on customers and the team?", "help": "What does success look like for the people who matter most?", "rows": 3},
                    ],
                },
            ],
        },
        {
            "key": "ratings",
            "label": "Quick Ratings",
            "icon": "\uD83D\uDCCA",
            "description": "Rate each supply chain capability from 1 (critical gap) to 10 (world-class).",
            "cards": [
                {
                    "title": "Capability Assessment",
                    "color": "#E8B84B",
                    "icon": "\uD83C\uDFAF",
                    "questions": [
                        {"key": "visibility", "type": "slider", "label": "Supply Chain Visibility", "help": "End-to-end view of inventory, orders, and flow", "color": "#E8B84B"},
                        {"key": "disruption_response", "type": "slider", "label": "Disruption Response", "help": "Speed and effectiveness when things go wrong", "color": "#E8B84B"},
                        {"key": "data_quality", "type": "slider", "label": "Data & Insights", "help": "Quality and timeliness of supply chain data", "color": "#E8B84B"},
                        {"key": "technology", "type": "slider", "label": "Technology & Tools", "help": "Systems supporting supply chain operations", "color": "#E8B84B"},
                        {"key": "suppliers", "type": "slider", "label": "Supplier Relationships", "help": "Partnership quality, reliability, communication", "color": "#E8B84B"},
                        {"key": "transport", "type": "slider", "label": "Transport & Logistics", "help": "Delivery efficiency, route optimisation, costs", "color": "#E8B84B"},
                        {"key": "demand_planning", "type": "slider", "label": "Demand Planning", "help": "Forecasting accuracy, seasonal readiness", "color": "#E8B84B"},
                        {"key": "sustainability", "type": "slider", "label": "Sustainability & Waste", "help": "Waste reduction, packaging, environmental impact", "color": "#E8B84B"},
                    ],
                },
                {
                    "title": "Anything Else?",
                    "color": "#718096",
                    "questions": [
                        {"key": "additional_comments", "type": "text", "label": "Additional comments or thoughts", "help": "Anything we haven\u2019t covered that you think is important", "rows": 3},
                    ],
                },
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# Embedded React artifact
# ---------------------------------------------------------------------------

_JSX_PATH = str(__import__("pathlib").Path(__file__).resolve().parent.parent / "artifacts" / "hfm-meeting-os.jsx")

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

components.html(_HTML, height=1600, scrolling=True)

render_footer("SC Interview", "Supply Chain Transformation Program", user=user)
