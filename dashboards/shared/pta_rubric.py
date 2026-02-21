"""
Harris Farm Hub — Prompt-to-Approval Rubric Engine
Scores AI outputs against 8 quality criteria.

Usage:
    from shared.pta_rubric import render_rubric_scorecard, STANDARD_RUBRIC, FIVE_TIER_RUBRIC
"""

import streamlit as st

# ---------------------------------------------------------------------------
# STANDARD RUBRIC — 8 criteria, used on every output
# ---------------------------------------------------------------------------

STANDARD_RUBRIC = {
    "audience_fit": {
        "name": "Audience Fit",
        "description": "Perfectly tailored to the reader's role, knowledge level, and decision needs",
        "scoring": {
            "9-10": "Perfectly tailored — reader immediately understands relevance and can act",
            "7-8": "Well targeted with minor misses in tone or detail level",
            "5-6": "Generally appropriate but misses some audience needs",
            "3-4": "Partially relevant but wrong level of detail or tone",
            "1-2": "Wrong audience entirely",
        },
    },
    "storytelling": {
        "name": "Storytelling",
        "description": "Clear narrative arc, compelling through-line, logical flow from problem to solution",
        "scoring": {
            "9-10": "Compelling narrative — reads like a story with clear beginning, middle, end",
            "7-8": "Good structure with logical flow, minor transitions could improve",
            "5-6": "Has structure but jumps around or loses the reader in places",
            "3-4": "Loosely connected sections without clear thread",
            "1-2": "Random collection of facts",
        },
    },
    "actionability": {
        "name": "Actionability",
        "description": "Specific next steps, clear owners, achievable timeline",
        "scoring": {
            "9-10": "Reader knows exactly what to do, who does it, and by when",
            "7-8": "Clear actions with most details, minor gaps in ownership or timing",
            "5-6": "Vague recommendations, unclear who does what",
            "3-4": "Suggestions without specifics",
            "1-2": "No actionable content",
        },
    },
    "visual_quality": {
        "name": "Visual Quality",
        "description": "Professional design, consistent formatting, effective data presentation",
        "scoring": {
            "9-10": "Publication-ready — clean, consistent, data tells the story",
            "7-8": "Professional with minor inconsistencies",
            "5-6": "Functional but visually inconsistent",
            "3-4": "Messy formatting, hard to scan",
            "1-2": "Unformatted text dump",
        },
    },
    "completeness": {
        "name": "Completeness",
        "description": "All necessary information present, obvious questions pre-answered",
        "scoring": {
            "9-10": "Everything needed — reader has no follow-up questions",
            "7-8": "Core content complete with minor gaps",
            "5-6": "Notable gaps that reader will ask about",
            "3-4": "Missing significant sections",
            "1-2": "Barely addresses the brief",
        },
    },
    "brevity": {
        "name": "Brevity",
        "description": "Respects reader's time — every sentence earns its place",
        "scoring": {
            "9-10": "Perfectly concise — nothing to add, nothing to remove",
            "7-8": "Mostly tight with minor padding",
            "5-6": "Could be 30% shorter without losing value",
            "3-4": "Significant repetition and filler",
            "1-2": "Bloated — buries the point",
        },
    },
    "data_integrity": {
        "name": "Data Integrity",
        "description": "All claims backed by verified, sourced data",
        "scoring": {
            "9-10": "Every number traceable to source, cross-verified, no unsubstantiated claims",
            "7-8": "Most data verified with clear sources",
            "5-6": "Some unverified claims or missing sources",
            "3-4": "Data present but questionable accuracy",
            "1-2": "Numbers appear fabricated or unverifiable",
        },
    },
    "honesty": {
        "name": "Honesty",
        "description": "Transparent about limitations, risks, and uncertainties",
        "scoring": {
            "9-10": "Risks, limitations, and caveats clearly stated — no surprises",
            "7-8": "Major risks acknowledged, minor ones implied",
            "5-6": "Some risks acknowledged but others conspicuously absent",
            "3-4": "Paints an overly optimistic picture",
            "1-2": "Deliberately misleading",
        },
    },
}

# ---------------------------------------------------------------------------
# 5-TIER ADVANCED RUBRIC — for board papers and major proposals
# ---------------------------------------------------------------------------

FIVE_TIER_RUBRIC = {
    "tier_1_cto_panel": {
        "name": "Tier 1: CTO Panel",
        "evaluators": ["Amazon CTO", "Uber CTO", "Anthropic CTO", "OpenAI CTO", "Canva CTO"],
        "criteria": ["Technical Architecture", "Scalability", "Reliability", "AI Integration", "Performance"],
        "pass_mark": 8.0,
    },
    "tier_2_clo_panel": {
        "name": "Tier 2: CLO Panel",
        "evaluators": ["McKinsey CLO", "Bain CLO", "Kearney CLO", "Google CLO", "Amazon CLO"],
        "criteria": ["Strategy Clarity", "Documentation Quality", "Change Management", "Training Plan", "Business Case"],
        "pass_mark": 8.0,
    },
    "tier_3_strategic": {
        "name": "Tier 3: Strategic Alignment",
        "criteria": ["Revenue Impact", "Customer Experience", "Operational Efficiency", "Competitive Advantage", "Brand Value"],
        "pass_mark": 8.0,
    },
    "tier_4_implementation": {
        "name": "Tier 4: Implementation Readiness",
        "criteria": ["Code Quality", "Testing Coverage", "Deployment Plan", "Rollback Strategy", "Support Model"],
        "pass_mark": 8.0,
    },
    "tier_5_presentation": {
        "name": "Tier 5: Presentation Quality",
        "criteria": list(STANDARD_RUBRIC.keys()),
        "pass_mark": 9.0,
    },
}

# ---------------------------------------------------------------------------
# APPROVAL ROUTING
# ---------------------------------------------------------------------------

APPROVAL_ROUTING = {
    "Store Manager": {"approver_role": "Area Manager", "level": "L1"},
    "Area Manager": {"approver_role": "Head of Operations", "level": "L2"},
    "Buyer": {"approver_role": "Head of Buying", "level": "L2"},
    "Finance Analyst": {"approver_role": "CFO", "level": "L2"},
    "Head of Buying": {"approver_role": "Co-CEO", "level": "L3"},
    "CFO": {"approver_role": "Co-CEO", "level": "L3"},
    "IT": {"approver_role": "CTO", "level": "L2"},
    "HR": {"approver_role": "Head of People", "level": "L2"},
    "Marketing": {"approver_role": "Head of Marketing", "level": "L2"},
    "Warehouse": {"approver_role": "Head of Logistics", "level": "L2"},
    "Executive": {"approver_role": "Board", "level": "L4"},
}

# ---------------------------------------------------------------------------
# ROLE-BASED DATA ACCESS
# ---------------------------------------------------------------------------

ROLE_DATA_ACCESS = {
    "Store Manager": {"stores": "own_store", "categories": "all", "financial": "own_store", "hr": "own_store"},
    "Area Manager": {"stores": "own_area", "categories": "all", "financial": "own_area", "hr": "own_area"},
    "Buyer": {"stores": "all", "categories": "own_categories", "financial": "own_categories", "supplier": "own_categories"},
    "Head of Buying": {"stores": "all", "categories": "all", "financial": "buying", "supplier": "all"},
    "Finance Analyst": {"stores": "all", "categories": "all", "financial": "all", "hr": "summary_only"},
    "CFO": {"stores": "all", "categories": "all", "financial": "all", "hr": "all"},
    "Executive": {"stores": "all", "categories": "all", "financial": "all", "hr": "all", "strategic": "all"},
    "IT": {"stores": "all", "infrastructure": "all", "financial": "it_budget"},
    "HR": {"hr": "all", "roster": "all", "stores": "all"},
    "Marketing": {"stores": "all", "categories": "all", "marketing": "all", "customer": "all"},
    "Warehouse": {"inventory": "all", "logistics": "all", "stores": "all"},
}

# ---------------------------------------------------------------------------
# POINTS SYSTEM
# ---------------------------------------------------------------------------

POINT_ACTIONS = {
    "complete_lesson": 20,
    "submit_prompt": 10,
    "approved_first_time": 25,
    "rubric_score_8_plus": 50,
    "rubric_score_9_plus": 100,
    "prompt_saved_to_library": 200,
    "template_used_by_others": 50,
    "five_tier_rubric_pass": 500,
    "board_paper_approved": 1000,
}

NINJA_LEVELS = {
    "Prompt Apprentice": {"min_points": 0, "max_points": 100, "badge": "Seedling", "colour": "#90CAF9"},
    "Prompt Specialist": {"min_points": 101, "max_points": 500, "badge": "Lightning", "colour": "#66BB6A"},
    "Prompt Master": {"min_points": 501, "max_points": 2000, "badge": "Fire", "colour": "#FFA726"},
    "AI Ninja": {"min_points": 2001, "max_points": None, "badge": "Ninja", "colour": "#E040FB"},
}


def get_ninja_level(points):
    """Return the ninja level name for a given point total."""
    for level_name, info in NINJA_LEVELS.items():
        max_pts = info["max_points"]
        if max_pts is None or points <= max_pts:
            return level_name
    return "AI Ninja"


# ---------------------------------------------------------------------------
# SCORING PROMPT — sent to Claude to evaluate AI output
# ---------------------------------------------------------------------------

SCORING_SYSTEM_PROMPT = """You are a senior business analyst scoring an AI-generated analysis for Harris Farm Markets.

Score the output against these 8 criteria, each rated 1-10:

1. **Audience Fit**: Is it tailored to the reader's role and decision needs?
2. **Storytelling**: Clear narrative arc from problem to solution?
3. **Actionability**: Specific next steps with owners and timelines?
4. **Visual Quality**: Professional formatting, effective data presentation?
5. **Completeness**: All necessary information present?
6. **Brevity**: Concise — every sentence earns its place?
7. **Data Integrity**: Claims backed by sourced data?
8. **Honesty**: Transparent about limitations and risks?

For each criterion, provide:
- A score from 1-10
- A one-sentence rationale

Then provide:
- The average score (to 1 decimal place)
- A verdict: "SHIP" if average >= 8.0, "REVISE" if 5.0-7.9, "REJECT" if < 5.0
- If average < 8.0, provide 2-3 specific improvement suggestions

Respond in this exact JSON format:
{
  "scores": {
    "audience_fit": {"score": 8, "rationale": "..."},
    "storytelling": {"score": 7, "rationale": "..."},
    "actionability": {"score": 9, "rationale": "..."},
    "visual_quality": {"score": 7, "rationale": "..."},
    "completeness": {"score": 8, "rationale": "..."},
    "brevity": {"score": 8, "rationale": "..."},
    "data_integrity": {"score": 6, "rationale": "..."},
    "honesty": {"score": 9, "rationale": "..."}
  },
  "average": 7.8,
  "verdict": "REVISE",
  "improvements": ["Be more specific about data sources", "Add timeline to recommendations"]
}"""


# ---------------------------------------------------------------------------
# STREAMLIT RENDERING — Visual scorecard
# ---------------------------------------------------------------------------

def _score_colour(score):
    """Return colour based on score: green 8+, amber 6-7, red <6."""
    if score >= 8:
        return "#16a34a"
    elif score >= 6:
        return "#d97706"
    return "#dc2626"


def _verdict_style(verdict):
    """Return (colour, icon) for verdict."""
    if verdict == "SHIP":
        return "#16a34a", "check-circle"
    elif verdict == "REVISE":
        return "#d97706", "alert-triangle"
    return "#dc2626", "x-circle"


def render_rubric_scorecard(scores_data):
    """Render a visual rubric scorecard in Streamlit.

    Args:
        scores_data: dict with keys: scores, average, verdict, improvements
            scores: dict of criterion -> {"score": int, "rationale": str}
    """
    if not scores_data or "scores" not in scores_data:
        st.warning("No rubric scores available.")
        return

    scores = scores_data["scores"]
    avg = scores_data.get("average", 0)
    verdict = scores_data.get("verdict", "REVISE")
    improvements = scores_data.get("improvements", [])

    v_colour, _ = _verdict_style(verdict)

    # Header with verdict
    st.markdown(
        f"""<div style="background:{v_colour}15; border-left:4px solid {v_colour};
        padding:12px 16px; border-radius:6px; margin-bottom:16px;">
        <span style="font-size:1.3em; font-weight:700; color:{v_colour};">
        {verdict}</span>
        <span style="color:#666; margin-left:12px;">Average: {avg}/10</span>
        </div>""",
        unsafe_allow_html=True,
    )

    # Score grid — 4 columns x 2 rows
    criteria_keys = list(STANDARD_RUBRIC.keys())
    for row_start in range(0, 8, 4):
        cols = st.columns(4)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx >= len(criteria_keys):
                break
            key = criteria_keys[idx]
            info = STANDARD_RUBRIC[key]
            score_data = scores.get(key, {})
            score_val = score_data.get("score", 0)
            rationale = score_data.get("rationale", "")
            colour = _score_colour(score_val)

            with col:
                st.markdown(
                    f"""<div style="text-align:center; padding:8px; border:1px solid #e5e7eb;
                    border-radius:8px; background:white;">
                    <div style="font-size:2em; font-weight:700; color:{colour};">{score_val}</div>
                    <div style="font-size:0.85em; font-weight:600; color:#374151;">{info['name']}</div>
                    <div style="font-size:0.7em; color:#9ca3af; margin-top:4px;">{rationale[:60]}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # Improvement suggestions
    if improvements and avg < 8.0:
        st.markdown("---")
        st.markdown("**Suggested Improvements:**")
        for imp in improvements:
            st.markdown(f"- {imp}")
