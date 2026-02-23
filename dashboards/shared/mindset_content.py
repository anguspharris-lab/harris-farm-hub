"""
Harris Farm Hub -- Mindset Assessment Content
==============================================
Measures 4 indicators of AI mindset at each level transition (L2+).
Used by skills_engine.py to track mindset growth over time.

Scenario-based assessments grounded in Harris Farm Markets operations.
Each level has one scenario with 4 questions (one per indicator).
Each question has 4 options scored 1-4 (worst to best).

Python 3.9 compatible.
"""

from typing import Optional

# ---------------------------------------------------------------------------
# THE 4 MINDSET INDICATORS
# ---------------------------------------------------------------------------

MINDSET_INDICATORS = [
    {
        "key": "first_instinct",
        "name": "First Instinct",
        "icon": "\u26a1",
        "description": (
            "When faced with a new task, does the user instinctively "
            "think about how AI could help?"
        ),
        "low_label": "Manual-first thinking",
        "high_label": "AI-first thinking",
    },
    {
        "key": "scope",
        "name": "Scope of Thinking",
        "icon": "\U0001f52d",
        "description": (
            "How broadly does the user consider the problem space "
            "and stakeholders?"
        ),
        "low_label": "Narrow, task-focused",
        "high_label": "System-wide thinking",
    },
    {
        "key": "ambition",
        "name": "Scale of Ambition",
        "icon": "\U0001f680",
        "description": (
            "How transformative and bold are the user's ideas "
            "for AI application?"
        ),
        "low_label": "Incremental improvements",
        "high_label": "Transformative vision",
    },
    {
        "key": "breadth",
        "name": "Creative Breadth",
        "icon": "\U0001f3a8",
        "description": (
            "How varied and creative are the user's approaches "
            "to using AI?"
        ),
        "low_label": "Single-approach thinking",
        "high_label": "Multi-modal creativity",
    },
]

# ---------------------------------------------------------------------------
# MINDSET SCENARIOS — ONE PER LEVEL (L2 - L6)
# ---------------------------------------------------------------------------

MINDSET_SCENARIOS = {
    2: {
        "title": "The Monday Report",
        "scenario": (
            "Your store manager asks you to prepare a summary of last "
            "week's sales performance for the Monday team meeting. You "
            "have access to the Hub's sales dashboard and AI tools."
        ),
        "questions": [
            {
                "indicator": "first_instinct",
                "question": "What's your first step?",
                "options": [
                    "Open a spreadsheet and start copying numbers manually",
                    "Ask a colleague how they usually do it",
                    "Check what data is available, then write a prompt to summarise it",
                    "Design a reusable AI workflow that auto-generates Monday reports every week",
                ],
            },
            {
                "indicator": "scope",
                "question": "Who else might benefit from this report?",
                "options": [
                    "Just the store manager who asked",
                    "The store team at the Monday meeting",
                    "The store team plus the area manager for regional comparison",
                    "The store team, area manager, and buying team — each getting a tailored version",
                ],
            },
            {
                "indicator": "ambition",
                "question": "If you could improve this process, what would you aim for?",
                "options": [
                    "Get the report done faster this week",
                    "Create a template that saves time every week",
                    "Build an automated workflow that generates the report every Monday morning",
                    (
                        "Design a system where every store automatically gets a "
                        "customised performance brief with AI-generated insights "
                        "and recommended actions"
                    ),
                ],
            },
            {
                "indicator": "breadth",
                "question": "What AI approach would you take?",
                "options": [
                    "One prompt to summarise the numbers",
                    "A prompt for the summary plus a separate prompt for visualisation suggestions",
                    "A chain of prompts: data summary, trend analysis, then talking points for the meeting",
                    (
                        "Multiple AI passes: data summary, competitor context from "
                        "market share data, customer feedback themes, and a draft "
                        "presentation script"
                    ),
                ],
            },
        ],
    },
    3: {
        "title": "Product Range Review",
        "scenario": (
            "A new competitor has opened near your Mosman store. The "
            "buying team wants to understand how to respond. You've been "
            "asked to help analyse the situation using AI."
        ),
        "questions": [
            {
                "indicator": "first_instinct",
                "question": "How do you begin the competitor analysis?",
                "options": [
                    "Walk through the competitor store and take notes by hand",
                    "Search online for the competitor's product range and pricing",
                    (
                        "Prompt AI to build a competitor analysis framework, then "
                        "feed in your observations and Hub data"
                    ),
                    (
                        "Design an AI-assisted research pipeline: scrape public info, "
                        "cross-reference with Mosman sales trends, and generate a "
                        "gap analysis against your own range"
                    ),
                ],
            },
            {
                "indicator": "scope",
                "question": "What data would you pull into the analysis?",
                "options": [
                    "Mosman store sales from the past month",
                    "Mosman sales plus the competitor's visible product range",
                    (
                        "Mosman sales, competitor range, market share trends for "
                        "surrounding postcodes, and customer demographics"
                    ),
                    (
                        "All of the above plus online order patterns, customer "
                        "feedback themes, supplier pricing data, and foot traffic "
                        "estimates from nearby stores for cannibalisation risk"
                    ),
                ],
            },
            {
                "indicator": "ambition",
                "question": "What outcome would you push for?",
                "options": [
                    "A list of products to add or promote at Mosman",
                    "A Mosman-specific range adjustment plan with expected margin impact",
                    (
                        "An ongoing AI-monitored competitive tracker that flags "
                        "when Mosman is losing share in key categories"
                    ),
                    (
                        "A network-wide competitive response system that automatically "
                        "identifies local threats for any store, recommends range "
                        "changes, and simulates margin outcomes before execution"
                    ),
                ],
            },
            {
                "indicator": "breadth",
                "question": "Which AI techniques would you combine?",
                "options": [
                    "A single prompt asking for competitive strategy advice",
                    "Separate prompts for data analysis and strategy recommendations",
                    (
                        "Data analysis prompts, a structured SWOT framework, and "
                        "AI-generated customer survey questions to validate assumptions"
                    ),
                    (
                        "Data analysis, sentiment mining of online reviews, AI-generated "
                        "range simulations, scenario modelling for three response "
                        "strategies, and a stakeholder-ready slide deck outline"
                    ),
                ],
            },
        ],
    },
    4: {
        "title": "Customer Retention Strategy",
        "scenario": (
            "Harris Farm's online channel has seen a 15% drop in repeat "
            "orders over the past quarter. The marketing team needs a "
            "data-driven retention strategy within 3 weeks."
        ),
        "questions": [
            {
                "indicator": "first_instinct",
                "question": "You receive the brief on Monday morning. What do you do first?",
                "options": [
                    "Pull up the online sales dashboard and start looking for patterns",
                    "Set up a meeting with the marketing team to discuss hypotheses",
                    (
                        "Prompt AI to define a retention analysis methodology, then "
                        "identify the data sources you need from the Hub"
                    ),
                    (
                        "Design an end-to-end AI project plan: automated data "
                        "extraction, cohort analysis, churn prediction model, and "
                        "a feedback loop to measure intervention effectiveness"
                    ),
                ],
            },
            {
                "indicator": "scope",
                "question": "Which teams should be involved in the solution?",
                "options": [
                    "Marketing — they own the brief",
                    "Marketing and the online operations team",
                    (
                        "Marketing, online ops, customer service, and the buying "
                        "team to check if range gaps are a factor"
                    ),
                    (
                        "Marketing, online ops, customer service, buying, store "
                        "managers for click-and-collect insights, and finance to "
                        "model the lifetime value impact of each retention tactic"
                    ),
                ],
            },
            {
                "indicator": "ambition",
                "question": "What does success look like to you?",
                "options": [
                    "A report explaining why repeat orders dropped",
                    "A report plus a recommended campaign to win back lapsed customers",
                    (
                        "An automated early-warning system that identifies at-risk "
                        "customers before they churn, with triggered re-engagement "
                        "offers"
                    ),
                    (
                        "A real-time personalisation engine that adapts product "
                        "recommendations, delivery slots, and promotional offers "
                        "per customer — turning retention into a self-improving system"
                    ),
                ],
            },
            {
                "indicator": "breadth",
                "question": "How would you use AI across the 3-week project?",
                "options": [
                    "Generate a summary of the sales decline with charts",
                    "Cohort analysis prompts plus AI-drafted email copy for a win-back campaign",
                    (
                        "Cohort analysis, customer segmentation, AI-generated "
                        "hypotheses for churn drivers, A/B test design for "
                        "retention offers, and a measurement dashboard spec"
                    ),
                    (
                        "All of the above, plus sentiment analysis on customer "
                        "service tickets, predictive churn scoring, AI-optimised "
                        "offer personalisation, competitor delivery benchmarking, "
                        "and an executive presentation with scenario modelling"
                    ),
                ],
            },
        ],
    },
    5: {
        "title": "Cross-Department Innovation",
        "scenario": (
            "The Co-CEOs have asked each department to propose one AI "
            "initiative that could save $500K annually or generate $1M "
            "in new value. Your department head has delegated this to you."
        ),
        "questions": [
            {
                "indicator": "first_instinct",
                "question": "How do you approach building the proposal?",
                "options": [
                    "Research what other retailers have done with AI and adapt an idea",
                    "Interview colleagues about their biggest time-wasters and pain points",
                    (
                        "Use AI to map every process in your department, estimate "
                        "automation potential, and rank initiatives by ROI"
                    ),
                    (
                        "Build an AI-powered discovery process: map workflows across "
                        "departments, identify cross-functional value chains, model "
                        "second-order effects, and generate a portfolio of options "
                        "with confidence-weighted ROI estimates"
                    ),
                ],
            },
            {
                "indicator": "scope",
                "question": "How wide do you cast the net for your proposal?",
                "options": [
                    "Focus on your own team's daily operations",
                    "Look across your department for the single highest-impact process",
                    (
                        "Examine touchpoints between your department and two or "
                        "three adjacent teams where AI could unlock shared value"
                    ),
                    (
                        "Map the full value chain from supplier to customer, identify "
                        "where AI at one link creates compounding benefits downstream, "
                        "and propose an initiative that lifts multiple departments"
                    ),
                ],
            },
            {
                "indicator": "ambition",
                "question": "What scale of change does your proposal target?",
                "options": [
                    "Automate a manual report to save 10 hours per week",
                    "Streamline an end-to-end workflow to halve processing time",
                    (
                        "Redesign a core business process around AI — changing how "
                        "decisions are made, not just how data is handled"
                    ),
                    (
                        "Propose a new AI-native capability that doesn't exist today — "
                        "one that could become a competitive moat and reshape how "
                        "Harris Farm operates in its category"
                    ),
                ],
            },
            {
                "indicator": "breadth",
                "question": "What AI capabilities does your proposal leverage?",
                "options": [
                    "Text generation for automating written outputs",
                    "Text generation plus data analysis for insight automation",
                    (
                        "Text generation, data analysis, workflow orchestration, "
                        "and a feedback loop that improves over time"
                    ),
                    (
                        "Multi-modal AI: language, vision, structured data, agent "
                        "orchestration, real-time decision support, and integration "
                        "with existing systems via APIs"
                    ),
                ],
            },
        ],
    },
    6: {
        "title": "Enterprise AI Governance",
        "scenario": (
            "Harris Farm is scaling AI use across all 21 stores. The "
            "board wants a governance framework that ensures quality, "
            "manages risk, and accelerates adoption. You've been asked "
            "to lead the project."
        ),
        "questions": [
            {
                "indicator": "first_instinct",
                "question": "What is your first move as project lead?",
                "options": [
                    "Draft a policy document based on AI governance templates you find online",
                    "Survey current AI usage across stores to understand the baseline",
                    (
                        "Use AI to audit existing usage patterns, classify risk levels, "
                        "and draft a governance framework tailored to HFM's context"
                    ),
                    (
                        "Design an AI-assisted governance system: automated usage "
                        "monitoring, risk scoring, quality benchmarking against the "
                        "WATCHDOG principles, and a living framework that evolves "
                        "as adoption matures"
                    ),
                ],
            },
            {
                "indicator": "scope",
                "question": "Who do you involve in designing the framework?",
                "options": [
                    "The IT team and a few power users",
                    "IT, department heads, and store managers",
                    (
                        "IT, department heads, store managers, frontline staff, "
                        "and the legal/compliance team"
                    ),
                    (
                        "All internal stakeholders plus external perspectives: "
                        "customers (via feedback data), suppliers (data sharing "
                        "protocols), industry bodies, and an AI ethics advisor"
                    ),
                ],
            },
            {
                "indicator": "ambition",
                "question": "What does your ideal governance framework achieve?",
                "options": [
                    "A clear set of rules about what AI can and cannot be used for",
                    "Rules plus a training program so everyone understands them",
                    (
                        "A dynamic framework with automated compliance checks, "
                        "tiered approval workflows, and continuous training "
                        "integrated into the Academy"
                    ),
                    (
                        "A self-improving governance ecosystem: AI monitors its own "
                        "usage quality, flags emerging risks before they materialise, "
                        "recommends policy updates, and creates a culture where "
                        "governance accelerates innovation rather than slowing it down"
                    ),
                ],
            },
            {
                "indicator": "breadth",
                "question": "What tools and methods does your governance plan include?",
                "options": [
                    "A written policy document and quarterly review meetings",
                    "Policy document, usage dashboards, and an approval workflow",
                    (
                        "Automated usage analytics, risk classification engine, "
                        "approval workflows, a quality rubric for AI outputs, "
                        "and a feedback mechanism for continuous improvement"
                    ),
                    (
                        "All of the above plus AI-powered anomaly detection on "
                        "outputs, sentiment tracking on staff adoption, benchmark "
                        "scoring against industry frameworks, board-ready reporting "
                        "automation, and an open innovation pipeline where any team "
                        "member can propose governed AI experiments"
                    ),
                ],
            },
        ],
    },
}

# ---------------------------------------------------------------------------
# COMPOSITE FEEDBACK THRESHOLDS
# ---------------------------------------------------------------------------

_FEEDBACK_BANDS = [
    (1.0, 1.5, "Your instincts lean toward traditional approaches. The Academy modules ahead will help you build AI-first habits."),
    (1.5, 2.5, "You're starting to see where AI fits in. Focus on expanding the range of problems you apply it to."),
    (2.5, 3.5, "Strong AI mindset emerging. You think broadly and ambitiously — now push toward system-level thinking."),
    (3.5, 4.1, "Exceptional. You naturally think in AI-native workflows, cross-functional value, and scalable systems."),
]

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_mindset_scenario(level_number):
    # type: (int) -> Optional[dict]
    """Return the mindset scenario for a specific level, or None."""
    return MINDSET_SCENARIOS.get(level_number)


def get_all_scenarios():
    # type: () -> dict
    """Return all mindset scenarios keyed by level number."""
    return dict(MINDSET_SCENARIOS)


def score_mindset_responses(level_number, responses):
    # type: (int, dict) -> dict
    """Score a set of mindset responses.

    Parameters
    ----------
    level_number : int
        The level being assessed (2-6).
    responses : dict
        Mapping of indicator key to selected option index (0-3).
        Example: {"first_instinct": 2, "scope": 3, "ambition": 1, "breadth": 2}

    Returns
    -------
    dict with keys:
        scores  — dict of {indicator_key: int} (1-4)
        composite — float average (1.0-4.0)
        feedback — str summary feedback
    """
    scenario = MINDSET_SCENARIOS.get(level_number)
    if scenario is None:
        return {"scores": {}, "composite": 0.0, "feedback": "No scenario found for this level."}

    scores = {}
    for q in scenario["questions"]:
        key = q["indicator"]
        idx = responses.get(key, 0)
        # Clamp to valid range
        idx = max(0, min(3, idx))
        scores[key] = idx + 1  # Convert 0-3 index to 1-4 score

    total = sum(scores.values())
    count = len(scores) if scores else 1
    composite = round(total / count, 2)

    feedback = _FEEDBACK_BANDS[-1][2]  # default to highest
    for low, high, msg in _FEEDBACK_BANDS:
        if low <= composite < high:
            feedback = msg
            break

    return {
        "scores": scores,
        "composite": composite,
        "feedback": feedback,
    }


def get_growth_summary(assessments):
    # type: (list) -> dict
    """Summarise mindset growth across multiple assessments over time.

    Parameters
    ----------
    assessments : list of dict
        Each dict must contain at minimum:
            level    — int (the level assessed)
            scores   — dict of {indicator_key: int}

    Returns
    -------
    dict with keys:
        per_indicator — dict of {key: {"trend": str, "first": int, "last": int}}
        overall_trend — str ("improving", "stable", or "declining")
        overall_first — float (first composite)
        overall_last  — float (last composite)
    """
    if not assessments:
        return {
            "per_indicator": {},
            "overall_trend": "no data",
            "overall_first": 0.0,
            "overall_last": 0.0,
        }

    # Sort by level to ensure chronological order
    sorted_a = sorted(assessments, key=lambda a: a.get("level", 0))

    indicator_keys = [ind["key"] for ind in MINDSET_INDICATORS]
    per_indicator = {}

    for key in indicator_keys:
        values = [a["scores"].get(key) for a in sorted_a if key in a.get("scores", {})]
        values = [v for v in values if v is not None]
        if len(values) < 2:
            trend = "insufficient data"
            first_val = values[0] if values else 0
            last_val = values[-1] if values else 0
        else:
            first_val = values[0]
            last_val = values[-1]
            diff = last_val - first_val
            if diff > 0:
                trend = "improving"
            elif diff < 0:
                trend = "declining"
            else:
                trend = "stable"
        per_indicator[key] = {
            "trend": trend,
            "first": first_val,
            "last": last_val,
        }

    # Overall composite trend
    composites = []
    for a in sorted_a:
        vals = [v for v in a.get("scores", {}).values() if v is not None]
        if vals:
            composites.append(sum(vals) / len(vals))

    overall_first = round(composites[0], 2) if composites else 0.0
    overall_last = round(composites[-1], 2) if composites else 0.0

    if len(composites) < 2:
        overall_trend = "insufficient data"
    elif overall_last > overall_first:
        overall_trend = "improving"
    elif overall_last < overall_first:
        overall_trend = "declining"
    else:
        overall_trend = "stable"

    return {
        "per_indicator": per_indicator,
        "overall_trend": overall_trend,
        "overall_first": overall_first,
        "overall_last": overall_last,
    }
