"""
Harris Farm AI-First Manifesto — Challenge Bank

21 challenges mapped to the AI-First Method (6 steps), XP levels
(Seed → Sprout → Grower → Harvester → Cultivator), and role tiers.

Used by the Academy Gamification Engine to serve daily and on-demand
challenges that build real AI capability across the business.
"""

from typing import List, Optional

CHALLENGE_BANK: List[dict] = [
    # ── Seed Challenges (role_tiers=["all"]) ────────────────────────────
    {
        "id": 1,
        "title": "Your First Question",
        "description": (
            "Open Hub Assistant, ask something useful about your store or "
            "department. Screenshot the answer. Was it helpful? What would "
            "you ask differently?"
        ),
        "level": "seed",
        "role_tiers": ["all"],
        "method_steps": [1, 2],
        "xp_reward": 15,
        "estimated_minutes": 5,
        "success_criteria": (
            "Asked a specific question with context. Reflected on the "
            "quality of the answer."
        ),
    },
    {
        "id": 2,
        "title": "The Better Prompt",
        "description": (
            'Take this prompt: "tell me about sales" and rewrite it with '
            "context \u2014 who you are, what store, what time period, what "
            "you\u2019ll do with the answer. Compare both outputs."
        ),
        "level": "seed",
        "role_tiers": ["all"],
        "method_steps": [2],
        "xp_reward": 20,
        "estimated_minutes": 10,
        "success_criteria": (
            "Rewrote prompt with at least 3 context elements. Compared "
            "outputs and explained the difference."
        ),
    },
    {
        "id": 3,
        "title": "Spot the Error",
        "description": (
            "AI generated this product description: \u201cHarris Farm\u2019s "
            "organic Granny Smith apples are grown exclusively in "
            "Queensland\u2019s Granite Belt region and are available "
            "year-round at all 50+ stores nationwide.\u201d Find what\u2019s "
            "wrong. What would you ask AI to fix?"
        ),
        "level": "seed",
        "role_tiers": ["all"],
        "method_steps": [5],
        "xp_reward": 15,
        "estimated_minutes": 5,
        "success_criteria": (
            "Identified at least 2 factual errors. Wrote a correction prompt."
        ),
    },
    {
        "id": 4,
        "title": "The Explain It Test",
        "description": (
            "Ask AI to explain one of Harris Farm\u2019s five strategic "
            "pillars. Read the answer. Is it right? What\u2019s missing? "
            "Add your knowledge."
        ),
        "level": "seed",
        "role_tiers": ["all"],
        "method_steps": [5],
        "xp_reward": 20,
        "estimated_minutes": 10,
        "success_criteria": (
            "Evaluated AI output against actual strategy. Added at least "
            "one insight AI missed."
        ),
    },

    # ── Sprout Challenges — Store Managers ──────────────────────────────
    {
        "id": 5,
        "title": "Week in Review",
        "description": (
            "Write a prompt that compares your store\u2019s sales this week "
            "to last week AND to the two closest stores. Include who it\u2019s "
            "for and what format you want."
        ),
        "level": "sprout",
        "role_tiers": ["store_manager"],
        "method_steps": [1, 2],
        "xp_reward": 30,
        "estimated_minutes": 15,
        "success_criteria": (
            "Prompt specifies store, time period, comparison stores, "
            "audience, and output format."
        ),
    },
    {
        "id": 6,
        "title": "Roster Brain",
        "description": (
            "Write a prompt to analyse your store\u2019s hourly transaction "
            "patterns and suggest optimal staffing levels by day. Include "
            "your store name and current roster constraints."
        ),
        "level": "sprout",
        "role_tiers": ["store_manager"],
        "method_steps": [1, 2, 5],
        "xp_reward": 35,
        "estimated_minutes": 20,
        "success_criteria": (
            "Prompt includes store context, current constraints, and "
            "specific output format for roster planning."
        ),
    },
    {
        "id": 7,
        "title": "Customer Pulse",
        "description": (
            "Write a prompt to identify your store\u2019s top 10 selling "
            "products, bottom 10, and what that tells you about your "
            "customer base."
        ),
        "level": "sprout",
        "role_tiers": ["store_manager"],
        "method_steps": [1, 2, 4],
        "xp_reward": 30,
        "estimated_minutes": 15,
        "success_criteria": (
            "Prompt specifies store and time period. Interpretation includes "
            "customer insight, not just product listing."
        ),
    },

    # ── Sprout Challenges — Buyers ──────────────────────────────────────
    {
        "id": 8,
        "title": "Wastage Detective",
        "description": (
            "Write a prompt to analyse wastage trends in your top 5 "
            "categories over the last 4 weeks across all stores. What "
            "patterns does it find? What supplier conversations should "
            "you have?"
        ),
        "level": "sprout",
        "role_tiers": ["buyer"],
        "method_steps": [1, 2, 5],
        "xp_reward": 35,
        "estimated_minutes": 20,
        "success_criteria": (
            "Prompt specifies categories, time period, and asks for "
            "actionable supplier recommendations."
        ),
    },
    {
        "id": 9,
        "title": "Range Review",
        "description": (
            "Write a prompt to compare the performance of new products "
            "you\u2019ve ranged in the last 3 months vs established lines. "
            "Which are earning their shelf space?"
        ),
        "level": "sprout",
        "role_tiers": ["buyer"],
        "method_steps": [1, 2, 4, 5],
        "xp_reward": 40,
        "estimated_minutes": 25,
        "success_criteria": (
            "Prompt defines 'new' vs 'established', specifies metrics, and "
            "asks AI what data would strengthen the analysis."
        ),
    },
    {
        "id": 10,
        "title": "Price Position",
        "description": (
            "Write a prompt to analyse how your category\u2019s prices "
            "compare to market data. Where are we too high? Too low? "
            "What\u2019s the margin impact of adjusting?"
        ),
        "level": "sprout",
        "role_tiers": ["buyer"],
        "method_steps": [1, 2, 3, 5],
        "xp_reward": 40,
        "estimated_minutes": 25,
        "success_criteria": (
            "Prompt includes category, competitive context, and asks for "
            "margin impact analysis with rubric-quality output."
        ),
    },

    # ── Sprout Challenges — Warehouse/Logistics ─────────────────────────
    {
        "id": 11,
        "title": "Pick Perfect",
        "description": (
            "Write a prompt to identify the product categories with the "
            "highest pick error rates in the last month across the DC. "
            "What\u2019s causing the errors?"
        ),
        "level": "sprout",
        "role_tiers": ["warehouse"],
        "method_steps": [1, 2, 5],
        "xp_reward": 30,
        "estimated_minutes": 15,
        "success_criteria": (
            "Prompt specifies DC context, time period, and asks for root "
            "cause analysis not just numbers."
        ),
    },
    {
        "id": 12,
        "title": "Route Optimiser",
        "description": (
            "Write a prompt to compare delivery costs per store and "
            "identify which routes have the most room for improvement. "
            "Include current constraints."
        ),
        "level": "sprout",
        "role_tiers": ["warehouse"],
        "method_steps": [1, 2, 4],
        "xp_reward": 35,
        "estimated_minutes": 20,
        "success_criteria": (
            "Prompt includes fleet constraints, cost metrics, and asks AI "
            "what additional data would improve the analysis."
        ),
    },

    # ── Sprout Challenges — Finance/Support ─────────────────────────────
    {
        "id": 13,
        "title": "P&L Storyteller",
        "description": (
            "Write a prompt that takes this month\u2019s P&L and explains "
            "the 3 biggest variances to budget in language a store manager "
            "would understand."
        ),
        "level": "sprout",
        "role_tiers": ["finance"],
        "method_steps": [1, 2, 5],
        "xp_reward": 35,
        "estimated_minutes": 20,
        "success_criteria": (
            "Prompt specifies audience (store manager), requests plain "
            "language, and focuses on actionable variances."
        ),
    },
    {
        "id": 14,
        "title": "Board Ready",
        "description": (
            "Write a prompt to summarise a department update into a "
            "2-minute board presentation: key numbers, what\u2019s working, "
            "what\u2019s not, recommended actions."
        ),
        "level": "sprout",
        "role_tiers": ["finance"],
        "method_steps": [1, 2, 3],
        "xp_reward": 35,
        "estimated_minutes": 20,
        "success_criteria": (
            "Prompt defines board audience, time constraint, and includes "
            "rubric criteria for presentation quality."
        ),
    },

    # ── Grower Challenges (role_tiers=["all"]) ──────────────────────────
    {
        "id": 15,
        "title": "Template Builder",
        "description": (
            "Build a reusable prompt template for a recurring weekly task "
            "in your department. Document it so a colleague can use it "
            "without your help. Get one person to try it and give feedback."
        ),
        "level": "grower",
        "role_tiers": ["all"],
        "method_steps": [1, 2, 6],
        "xp_reward": 50,
        "estimated_minutes": 90,
        "success_criteria": (
            "Template is documented with instructions. At least one "
            "colleague has used it and provided feedback."
        ),
    },
    {
        "id": 16,
        "title": "The Improver",
        "description": (
            "Find a prompt in the Prompt Library. Use it. Score it with "
            "the Rubric. Then improve it \u2014 add more context, better "
            "format, clearer success criteria. Submit your improved version."
        ),
        "level": "grower",
        "role_tiers": ["all"],
        "method_steps": [2, 3, 4],
        "xp_reward": 40,
        "estimated_minutes": 30,
        "success_criteria": (
            "Original prompt scored. Improved version scores at least 1 "
            "point higher. Changes are documented."
        ),
    },
    {
        "id": 17,
        "title": "Cross-Department Intel",
        "description": (
            "Write a prompt that combines data from two different "
            "departments (e.g., buying + store ops, or finance + transport) "
            "to find an insight neither department would see alone."
        ),
        "level": "grower",
        "role_tiers": ["all"],
        "method_steps": [1, 2, 5],
        "xp_reward": 50,
        "estimated_minutes": 45,
        "success_criteria": (
            "Prompt references two data sources. Insight is genuinely "
            "cross-functional and actionable."
        ),
    },

    # ── Harvester Challenges (role_tiers=["all"]) ───────────────────────
    {
        "id": 18,
        "title": "Ship a Tool",
        "description": (
            "Build a dashboard, report template, or automated workflow "
            "that solves a real recurring problem for your team. Demo it "
            "to your manager. If it scores 8+ on the Rubric, it goes live."
        ),
        "level": "harvester",
        "role_tiers": ["all"],
        "method_steps": [1, 2, 3, 4, 5, 6],
        "xp_reward": 100,
        "estimated_minutes": 2400,
        "success_criteria": (
            "Working tool demonstrated. Rubric score 8+. Solves a real "
            "recurring problem. Approved by manager."
        ),
    },
    {
        "id": 19,
        "title": "The 2-Pager",
        "description": (
            "Write an Amazon-style 2-page document proposing an AI-powered "
            "improvement to a process in your department. Define the "
            "problem, the solution, the data needed, the expected ROI, "
            "and the prompt that builds it."
        ),
        "level": "harvester",
        "role_tiers": ["all"],
        "method_steps": [1, 2, 3, 5],
        "xp_reward": 75,
        "estimated_minutes": 600,
        "success_criteria": (
            "2-page document complete. Problem clearly defined. Solution "
            "includes working prompt. ROI estimated."
        ),
    },

    # ── Cultivator Challenges (role_tiers=["all"]) ──────────────────────
    {
        "id": 20,
        "title": "Grow a Legend",
        "description": (
            "Mentor someone from Seed to Sprout level. Document what you "
            "taught them, what worked, what didn\u2019t. Both mentor and "
            "mentee get XP."
        ),
        "level": "cultivator",
        "role_tiers": ["all"],
        "method_steps": [6],
        "xp_reward": 100,
        "estimated_minutes": 1200,
        "success_criteria": (
            "Mentee reached Sprout level. Mentoring log documented. Both "
            "participants reflect on the experience."
        ),
    },
    {
        "id": 21,
        "title": "Improve the System",
        "description": (
            "Identify something in The Hub that could be better. Write "
            "the Claude Code prompt that builds the fix. If it ships, "
            "you\u2019re a true Cultivator."
        ),
        "level": "cultivator",
        "role_tiers": ["all"],
        "method_steps": [1, 2, 3, 4, 5, 6],
        "xp_reward": 150,
        "estimated_minutes": 2400,
        "success_criteria": (
            "Improvement identified. Claude Code prompt written. If "
            "shipped: verified working, passes WATCHDOG."
        ),
    },
]


# ── Helper Functions ────────────────────────────────────────────────────


def get_challenges_for_level(level: str) -> List[dict]:
    """Return all challenges matching a given level (e.g., 'seed', 'sprout')."""
    return [c for c in CHALLENGE_BANK if c["level"] == level.lower()]


def get_challenge_for_user(level: str, role_tier: str) -> Optional[dict]:
    """Return the best-fit challenge for a user's level and role.

    Prefers role-specific challenges, falls back to 'all' role challenges.
    """
    level = level.lower()
    role_tier = role_tier.lower().replace(" ", "_") if role_tier else "all"
    # Try role-specific first
    matches = [
        c for c in CHALLENGE_BANK
        if c["level"] == level and role_tier in c["role_tiers"]
    ]
    if not matches:
        matches = [
            c for c in CHALLENGE_BANK
            if c["level"] == level and "all" in c["role_tiers"]
        ]
    return matches[0] if matches else None


def get_challenges_by_step(step_num: int) -> List[dict]:
    """Return all challenges that practice a given AI-First Method step (1-6)."""
    return [c for c in CHALLENGE_BANK if step_num in c["method_steps"]]
