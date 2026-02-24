"""
Harris Farm Hub — Pillar Data Registry
Central metadata for the 5 strategic pillars.
Used by intro pages, Way of Working, and strategic framing components.
"""

# Monday.com board IDs for initiative tracking
BOARD_IDS = {
    "P1": 5001442659,
    "P2": 5001460085,
    "P3": 5001476308,
    "P4": 5001480788,
    "P5": 5001485134,
}

PILLAR_REGISTRY = {
    "P1": {
        "id": "P1",
        "name": "For The Greater Goodness",
        "short_name": "Greater Goodness",
        "icon": "\U0001f331",
        "color": "#2ECC71",
        "tagline": "We'll do things right, from end-to-end",
        "strategic_question": (
            "Are we living the Greater Goodness \u2014 measurably, "
            "not just in marketing?"
        ),
        "board_id": 5001442659,
        "nav_slugs": ["intro-goodness", "greater-goodness"],
    },
    "P2": {
        "id": "P2",
        "name": "Smashing It for the Customer",
        "short_name": "Customer",
        "icon": "\U0001f465",
        "color": "#7c3aed",
        "tagline": "We'll take the 'you get me' feeling to a whole new level",
        "strategic_question": (
            "Do our customers feel known \u2014 and are we winning "
            "where it matters?"
        ),
        "board_id": 5001460085,
        "nav_slugs": ["customers"],
    },
    "P3": {
        "id": "P3",
        "name": "Growing Legendary Leadership",
        "short_name": "People",
        "icon": "\U0001f393",
        "color": "#2ECC71",
        "tagline": (
            "We will be famous for attracting, developing, "
            "and retaining exceptional people"
        ),
        "strategic_question": (
            "Are our people growing with AI as their brain partner "
            "\u2014 and do they feel it?"
        ),
        "board_id": 5001476308,
        "nav_slugs": [
            "intro-people", "learning-centre", "the-paddock", "academy",
            "prompt-builder", "approvals", "the-rubric", "hub-assistant",
        ],
    },
    "P4": {
        "id": "P4",
        "name": "Today's Business, Done Better",
        "short_name": "Operations",
        "icon": "\U0001f4ca",
        "color": "#d97706",
        "tagline": "We will tidy up the supply chain, from pay to purchase",
        "strategic_question": (
            "Are we running tighter, smarter, and faster \u2014 "
            "with AI reading the data before we ask?"
        ),
        "board_id": 5001480788,
        "nav_slugs": [
            "intro-operations", "sales", "profitability", "revenue-bridge",
            "store-ops", "buying-hub", "product-intel", "plu-intel", "transport",
        ],
    },
    "P5": {
        "id": "P5",
        "name": "Tomorrow's Business, Built Better",
        "short_name": "Digital & AI",
        "icon": "\U0001f680",
        "color": "#2ECC71",
        "tagline": (
            "We'll build a brilliant back-end with tools that talk, "
            "systems that serve, data we trust"
        ),
        "strategic_question": (
            "Is the platform accelerating the strategy through prompts, "
            "rubrics, and agents \u2014 or just existing?"
        ),
        "board_id": 5001485134,
        "nav_slugs": [
            "intro-digital", "workflow-engine", "analytics-engine",
            "agent-hub", "agent-ops", "ai-adoption", "trending",
            "mission-control",
        ],
    },
}


def get_pillar(pillar_id):
    """Return pillar dict for P1-P5, or empty dict if not found."""
    return PILLAR_REGISTRY.get(pillar_id, {})


def get_all_pillars():
    """Return list of all pillar dicts in order."""
    return [PILLAR_REGISTRY[pid] for pid in ["P1", "P2", "P3", "P4", "P5"]]


def get_board_id(pillar_id):
    """Return Monday.com board ID for a pillar."""
    return BOARD_IDS.get(pillar_id)
