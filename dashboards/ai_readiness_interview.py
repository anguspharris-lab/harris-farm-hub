"""
Harris Farm Hub — AI Readiness Review Interview Tool
Uses the universal Meeting OS artifact (hfm-meeting-os.jsx) with ARR-specific config.
5-section stakeholder interview for AI readiness diagnostic.
Submits to legacy hfm-scr-insert Cloud Function via mapped format (meeting_type=ARR).
"""

import json
import streamlit as st
import streamlit.components.v1 as components

from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")

render_header(
    "AI Readiness \u2014 How Ready Are We?",
    "Capability assessment across 8 dimensions \u2014 honest answers build better plans",
    goals=["G3", "G5"],
    strategy_context="The Harris Farm Way \u2014 AI Readiness Review",
)

st.markdown(
    "<div style='background:rgba(6,182,212,0.08);border:1px solid rgba(6,182,212,0.2);"
    "border-radius:10px;padding:14px 18px;margin-bottom:20px;'>"
    "<div style='font-weight:600;color:#06B6D4;font-size:0.95em;'>How to use</div>"
    "<div style='color:#4A5568;font-size:0.88em;line-height:1.5;'>"
    "Complete each section using the Next button. Your progress auto-saves. "
    "On the final section, hit Submit \u2014 your response is saved to the database "
    "and a backup JSON file is downloaded automatically.</div>"
    "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Meeting config — maps all ARR questions into the universal artifact
# ---------------------------------------------------------------------------

MEETING_CONFIG = {
    "meetingType": "ARR",
    "title": "AI Readiness Review",
    "subtitle": "Harris Farm Markets \u2014 Stakeholder Interview",
    "headerEmoji": "\uD83E\uDD16",
    "accent": "#06B6D4",
    "storageKey": "hfm_arr_interview_v2",
    "emailRequired": False,
    "submitUrl": "https://australia-southeast1-oval-blend-488902-p2.cloudfunctions.net/hfm-scr-insert",
    "apiKey": "hfm-scr-2026",
    "submitFormat": "mapped",
    "submitMap": {
        "name": "name",
        "role": "role",
        "sc_touch": "ai_touchpoint",
        "meeting_type": "_LITERAL:ARR",
        "five_year_confidence": "confidence",
        "leverage_strengths": "leverage",
        "urgency": "urgency",
        "desire_score": "desire",
        "clarity_score": "clarity",
        "readiness_score": "readiness",
        "sustain_score": "sustain",
        "ai_data_literacy": "data_literacy",
        "ai_tool_exposure": "tool_exposure",
        "ai_process_readiness": "process_readiness",
        "ai_data_quality": "data_quality",
        "ai_digital_skills": "digital_skills",
        "ai_change_appetite": "change_appetite",
        "ai_governance": "governance",
        "ai_use_case_clarity": "use_case_clarity",
        "ai_current_tools": "current_tools",
        "ai_pain_points": "ai_pain_points",
        "ai_opportunities": "opportunities",
        "ai_concerns": "concerns",
        "ai_training_needs": "training_needs",
        "external_pressures": "external_pressures",
        "worries": "concerns",
        "ideal_5yr": "ideal_5yr",
        "one_big_thing": "one_big_thing",
        "customer_impact": "impact_if_successful",
        "additional": "additional_comments",
    },
    "welcomeTitle": "About You",
    "welcomeDescription": "This interview takes 10\u201315 minutes. Your responses will help us understand where Harris Farm is today with AI and technology, and where we should focus next. All answers are confidential.",
    "welcomeFields": [
        {"key": "name", "label": "Your Name", "placeholder": "Full name", "required": True},
        {"key": "role", "label": "Your Role", "placeholder": "e.g. Buyer, Store Manager, Head of Operations", "required": True},
        {"key": "department", "label": "Department", "placeholder": "e.g. Buying, Operations, IT, Supply Chain"},
        {"key": "ai_touchpoint", "label": "How does AI or technology touch your day-to-day work?", "type": "textarea", "help": "Think broadly \u2014 spreadsheets, reporting tools, automation, AI chatbots, anything digital", "rows": 3},
        {"key": "confidence", "label": "5-Year Confidence", "type": "slider", "help": "How confident are you that HFM\u2019s current technology and tools can support our growth over the next 5 years?", "color": "#06B6D4"},
    ],
    "sections": [
        {
            "key": "current",
            "label": "Current State",
            "icon": "\uD83D\uDDA5\uFE0F",
            "description": "Where we are today with AI and technology.",
            "cards": [
                {
                    "title": "What AI/Tech Do You Use Today?",
                    "color": "#06B6D4",
                    "icon": "\uD83D\uDEE0\uFE0F",
                    "questions": [
                        {"key": "current_tools", "type": "text", "label": "What tools and technology do you currently use?", "help": "List everything \u2014 Excel, ChatGPT, Power BI, D365, email, Slack, any apps or AI tools", "rows": 4},
                    ],
                },
                {
                    "title": "Pain Points & Time Wasters",
                    "color": "#F97316",
                    "icon": "\u23F0",
                    "questions": [
                        {"key": "ai_pain_points", "type": "text", "label": "What tasks waste the most time or cause the most frustration?", "help": "Repetitive reporting, manual data entry, chasing information, slow approvals...", "rows": 4},
                        {"key": "external_pressures", "type": "text", "label": "What external pressures are driving the need for AI/technology?", "help": "Competitor moves, customer expectations, cost pressures, speed-to-market...", "rows": 3},
                    ],
                },
                {
                    "title": "Scores",
                    "color": "#E8B84B",
                    "questions": [
                        {"key": "leverage", "type": "slider", "label": "Leverage", "help": "How well do we leverage the technology and data we already have?", "color": "#E8B84B"},
                        {"key": "urgency", "type": "slider", "label": "Urgency", "help": "How urgent is AI adoption for HFM right now?", "color": "#F97316"},
                    ],
                },
            ],
        },
        {
            "key": "adkar",
            "label": "Change Readiness",
            "icon": "\uD83E\uDDE0",
            "description": "ADKAR measures five dimensions of change readiness for AI adoption.",
            "cards": [
                {
                    "title": "Change Readiness (ADKAR)",
                    "color": "#8B5CF6",
                    "icon": "\uD83D\uDCA1",
                    "description": "Rate each on a 1\u201310 scale for AI adoption at Harris Farm.",
                    "questions": [
                        {"key": "opportunities", "type": "text", "label": "Where do you see the biggest opportunities for AI at HFM?", "rows": 3},
                        {"key": "concerns", "type": "text", "label": "What concerns you most about AI adoption?", "rows": 3},
                    ],
                },
                {
                    "title": "ADKAR Dimensions",
                    "color": "#8B5CF6",
                    "questions": [
                        {"key": "urgency", "type": "slider", "label": "Awareness", "help": "Does the team understand WHY AI adoption is important for HFM?", "color": "#EF4444"},
                        {"key": "desire", "type": "slider", "label": "Desire", "help": "Does the team WANT to adopt AI tools and new ways of working?", "color": "#F97316"},
                        {"key": "clarity", "type": "slider", "label": "Knowledge", "help": "Does the team know WHAT AI can do and HOW to use it effectively?", "color": "#E8B84B"},
                        {"key": "readiness", "type": "slider", "label": "Ability", "help": "Can the organisation EXECUTE an AI rollout right now?", "color": "#3B82F6"},
                        {"key": "sustain", "type": "slider", "label": "Reinforcement", "help": "Will AI adoption STICK? Can we sustain new tools and habits?", "color": "#8B5CF6"},
                    ],
                },
            ],
        },
        {
            "key": "vision",
            "label": "The Vision",
            "icon": "\uD83D\uDD2D",
            "description": "Paint the picture of what AI-enabled Harris Farm looks like.",
            "cards": [
                {
                    "title": "The AI Vision",
                    "color": "#06B6D4",
                    "icon": "\uD83C\uDF1F",
                    "questions": [
                        {"key": "ideal_5yr", "type": "text", "label": "What does AI-enabled Harris Farm look like in 5 years?", "help": "Paint the picture. How would your day-to-day be different? What would customers notice?", "rows": 5},
                        {"key": "one_big_thing", "type": "text", "label": "If you could automate or AI-enable ONE thing, what would it be?", "help": "The single highest-impact use case for AI in your area", "rows": 3},
                        {"key": "impact_if_successful", "type": "text", "label": "If we get AI right, what\u2019s the impact on customers and the team?", "help": "What does success look like for the people who matter most?", "rows": 3},
                    ],
                },
            ],
        },
        {
            "key": "ratings",
            "label": "AI Capabilities",
            "icon": "\uD83D\uDCCA",
            "description": "Rate each AI readiness dimension from 1 (critical gap) to 10 (well-prepared).",
            "cards": [
                {
                    "title": "AI Capability Assessment",
                    "color": "#E8B84B",
                    "icon": "\uD83C\uDFAF",
                    "questions": [
                        {"key": "data_literacy", "type": "slider", "label": "Data Literacy", "help": "Team\u2019s ability to understand, interpret, and work with data day-to-day", "color": "#E8B84B"},
                        {"key": "tool_exposure", "type": "slider", "label": "AI Tool Familiarity", "help": "Current exposure to AI tools (ChatGPT, Copilot, Claude, automation)", "color": "#E8B84B"},
                        {"key": "process_readiness", "type": "slider", "label": "Process Readiness", "help": "How ready are current workflows for AI-assisted automation?", "color": "#E8B84B"},
                        {"key": "data_quality", "type": "slider", "label": "Data Quality for AI", "help": "Is our data clean, structured, and accessible enough for AI to use?", "color": "#E8B84B"},
                        {"key": "digital_skills", "type": "slider", "label": "Digital Skills", "help": "General digital competency across the team (Excel, systems, platforms)", "color": "#E8B84B"},
                        {"key": "change_appetite", "type": "slider", "label": "Change Appetite", "help": "Willingness to try new tools and adopt new ways of working", "color": "#E8B84B"},
                        {"key": "governance", "type": "slider", "label": "AI Governance & Trust", "help": "Understanding of AI risks, data privacy, ethics, and when NOT to use AI", "color": "#E8B84B"},
                        {"key": "use_case_clarity", "type": "slider", "label": "Use Case Clarity", "help": "How clear is it where AI can genuinely add value vs. where it can\u2019t?", "color": "#E8B84B"},
                    ],
                },
                {
                    "title": "Training & Support",
                    "color": "#8B5CF6",
                    "icon": "\uD83C\uDF93",
                    "questions": [
                        {"key": "training_needs", "type": "text", "label": "What training or support would help you most with AI?", "help": "Workshops, 1-on-1 coaching, online courses, hands-on practice, prompt writing...", "rows": 3},
                        {"key": "additional_comments", "type": "text", "label": "Anything else?", "help": "Any other thoughts about AI at Harris Farm", "rows": 3},
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

render_footer("AI Readiness", "AI Readiness Review Program", user=user)
