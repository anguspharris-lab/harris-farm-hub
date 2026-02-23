"""
Harris Farm Hub — Placement Challenge Content
5 escalating scenarios that assess AI prompt craft proficiency.
Used by placement_engine.py to determine starting level (L1-L5).

Each scenario targets a distinct skill:
    1. Recognition  — spotting issues in a weak prompt
    2. Construction — writing a prompt from scratch
    3. Iteration    — improving a prompt given feedback
    4. Scope        — decomposing a complex task into sequenced prompts
    5. Application  — designing a full multi-prompt AI workflow

Scoring: each scenario is worth 0-5 points (total 0-25).
The total maps to a starting level via LEVEL_BANDS.
"""

from typing import Optional, List, Dict

# ---------------------------------------------------------------------------
# Placement Scenarios
# ---------------------------------------------------------------------------

PLACEMENT_SCENARIOS: List[Dict] = [
    # ------------------------------------------------------------------
    # Scenario 1 — Recognition
    # ------------------------------------------------------------------
    {
        "id": 1,
        "name": "Recognition",
        "title": "Spot the Issues",
        "icon": "\U0001f50d",
        "time_limit_seconds": 180,
        "instruction": (
            "Read this AI prompt carefully. Identify ALL the issues that "
            "would prevent it from getting a useful response. List each "
            "issue and explain why it is a problem."
        ),
        "prompt_shown": "Tell me about sales at Crows Nest",
        "scoring_type": "ai",
        "max_score": 5,
        "scoring_guidance": (
            "Award 1 point for each distinct, valid issue identified "
            "(up to 5). Core issues include: no time period specified, "
            "no specific metrics requested (revenue, units, margin, etc.), "
            "no output format defined (table, chart, summary), no context "
            "about purpose or audience, no comparison basis (week-on-week, "
            "year-on-year), and excessively vague scope. Minor phrasing "
            "observations without substance do not count."
        ),
    },
    # ------------------------------------------------------------------
    # Scenario 2 — Construction
    # ------------------------------------------------------------------
    {
        "id": 2,
        "name": "Construction",
        "title": "Build a Prompt",
        "icon": "\U0001f528",
        "time_limit_seconds": 240,
        "instruction": (
            "Write a prompt to get AI to produce a weekly sales "
            "performance summary for the Crows Nest store, covering "
            "the last 4 weeks, that the store manager can use in their "
            "Monday team meeting."
        ),
        "scoring_type": "ai",
        "max_score": 5,
        "scoring_guidance": (
            "Score on 5 dimensions (1 point each): "
            "1) Clear role or context setting. "
            "2) Specific metrics requested (e.g. revenue, units, basket "
            "size, department breakdown). "
            "3) Defined time period and comparison basis. "
            "4) Specified output format suitable for a team meeting "
            "(e.g. summary table, bullet points, highlights). "
            "5) Audience awareness — language and depth appropriate for "
            "a store manager briefing their team."
        ),
    },
    # ------------------------------------------------------------------
    # Scenario 3 — Iteration
    # ------------------------------------------------------------------
    {
        "id": 3,
        "name": "Iteration",
        "title": "Improve with Feedback",
        "icon": "\U0001f504",
        "time_limit_seconds": 240,
        "instruction": (
            "Below is a prompt and the feedback it received. Rewrite "
            "the prompt addressing ALL the feedback points while "
            "keeping the original intent."
        ),
        "original_prompt": (
            "Analyse the top-selling products across all Harris Farm "
            "stores for the last quarter. Show trends and make "
            "recommendations."
        ),
        "feedback": [
            (
                "Which metric defines 'top-selling' — revenue, units, "
                "or margin?"
            ),
            (
                "Which quarter specifically? The prompt should name the "
                "date range."
            ),
            (
                "'All stores' is 21 locations — should results be "
                "grouped by store, by region, or aggregated?"
            ),
            (
                "'Show trends' is vague — compared to what baseline? "
                "Previous quarter? Same quarter last year?"
            ),
            (
                "Recommendations for whom? A buyer, a store manager, "
                "and a marketing lead would need different actions."
            ),
        ],
        "scoring_type": "ai",
        "max_score": 5,
        "scoring_guidance": (
            "Award 1 point for each feedback point clearly addressed "
            "in the rewritten prompt: "
            "1) Metric defined (revenue, units, or margin). "
            "2) Specific date range named. "
            "3) Grouping logic specified (store, region, or aggregate). "
            "4) Comparison baseline stated. "
            "5) Target audience and action orientation specified. "
            "Deduct nothing for reasonable creative additions."
        ),
    },
    # ------------------------------------------------------------------
    # Scenario 4 — Scope
    # ------------------------------------------------------------------
    {
        "id": 4,
        "name": "Scope",
        "title": "Break It Down",
        "icon": "\U0001f4cb",
        "time_limit_seconds": 300,
        "instruction": (
            "This task is too complex for a single prompt. Break it "
            "into 3 targeted prompts that build on each other, and "
            "explain the sequence."
        ),
        "task": (
            "The CEO wants a complete analysis of Harris Farm's "
            "competitive position in Sydney's Northern Beaches, "
            "including: current market share trends, customer "
            "demographics, competitor store locations and offerings, "
            "our store performance (Dee Why, Manly), potential for a "
            "third store, and a recommended 12-month strategy with "
            "budget estimates."
        ),
        "scoring_type": "ai",
        "max_score": 5,
        "scoring_guidance": (
            "Score across 5 dimensions (1 point each): "
            "1) Logical decomposition — 3 prompts that each tackle a "
            "coherent sub-task. "
            "2) Sequencing — clear rationale for the order; later "
            "prompts depend on earlier outputs. "
            "3) Coverage — all elements of the original task are "
            "addressed across the 3 prompts. "
            "4) Specificity — each prompt is detailed enough to "
            "produce a useful output on its own. "
            "5) Output chaining — explicit description of how the "
            "output of one prompt feeds into the next."
        ),
    },
    # ------------------------------------------------------------------
    # Scenario 5 — Application
    # ------------------------------------------------------------------
    {
        "id": 5,
        "name": "Application",
        "title": "Design a Workflow",
        "icon": "\U0001f680",
        "time_limit_seconds": 360,
        "instruction": (
            "Design a complete 3-prompt AI workflow to solve this "
            "business problem. For each prompt, specify: the "
            "role/persona, the specific request, and how output from "
            "one feeds into the next."
        ),
        "scenario": (
            "Harris Farm's Crows Nest store has seen a 3% decline in "
            "basket size over the past 8 weeks, despite foot traffic "
            "remaining stable. The store manager suspects the prepared "
            "foods section is underperforming but doesn't have time to "
            "analyse the data manually. The buying team needs to "
            "decide within 2 weeks whether to refresh the prepared "
            "foods range. Design an AI workflow to investigate the "
            "problem, identify the root cause, and produce a "
            "recommendation the buying team can act on."
        ),
        "scoring_type": "ai",
        "max_score": 5,
        "scoring_guidance": (
            "Score across 5 dimensions (1 point each): "
            "1) Role clarity — each prompt assigns a distinct, "
            "appropriate persona (e.g. data analyst, category manager, "
            "strategist). "
            "2) Request specificity — each prompt makes a concrete, "
            "actionable ask with measurable outputs. "
            "3) Data awareness — prompts reference realistic data "
            "sources (transaction data, category mix, basket metrics). "
            "4) Flow logic — clear handoff; output of prompt N is "
            "explicitly used as input to prompt N+1. "
            "5) Actionability — the final output is a recommendation "
            "the buying team can act on within the stated 2-week "
            "timeframe."
        ),
    },
]


# ---------------------------------------------------------------------------
# Level Band Mapping
# ---------------------------------------------------------------------------

LEVEL_BANDS: List[Dict] = [
    {
        "min_score": 0,
        "max_score": 5,
        "level": 1,
        "label": "Seed \u2014 Starting fresh",
    },
    {
        "min_score": 6,
        "max_score": 10,
        "level": 1,
        "label": "Seed \u2014 Some awareness",
    },
    {
        "min_score": 11,
        "max_score": 15,
        "level": 2,
        "label": "Sprout \u2014 Foundations in place",
    },
    {
        "min_score": 16,
        "max_score": 20,
        "level": 3,
        "label": "Growing \u2014 Solid skills",
    },
    {
        "min_score": 21,
        "max_score": 25,
        "level": 4,
        "label": "Harvest \u2014 Advanced proficiency",
    },
]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def get_scenario(scenario_id: int) -> Optional[Dict]:
    """Return a single scenario by ID, or None if not found."""
    for scenario in PLACEMENT_SCENARIOS:
        if scenario["id"] == scenario_id:
            return scenario
    return None


def get_all_scenarios() -> List[Dict]:
    """Return all 5 placement scenarios."""
    return list(PLACEMENT_SCENARIOS)


def score_to_level(total_score: int) -> int:
    """Map a total score (0-25) to a starting level (1-4).

    Returns the level integer from the matching band.
    Scores outside 0-25 are clamped.
    """
    clamped = max(0, min(25, total_score))
    for band in LEVEL_BANDS:
        if band["min_score"] <= clamped <= band["max_score"]:
            return band["level"]
    # Fallback — should never reach here with valid bands
    return 1


def get_level_label(total_score: int) -> str:
    """Return a human-readable label for the given total score.

    Example: 'Sprout -- Foundations in place'
    """
    clamped = max(0, min(25, total_score))
    for band in LEVEL_BANDS:
        if band["min_score"] <= clamped <= band["max_score"]:
            return band["label"]
    return "Unknown"
