"""
Harris Farm Hub — Role-Based Navigation Config
Defines which pages each role can see.
"""

# Role definitions: role_key -> {display_name, description, allowed_slugs}
# "admin" and "user" (default) see ALL pages — no filtering.
# Home page (_home) is always accessible — it's handled separately in app.py.

ROLE_DEFINITIONS = {
    "admin": {
        "display_name": "Administrator",
        "description": "Full access to all Hub pages",
        "allowed_slugs": "all",
    },
    "user": {
        "display_name": "General",
        "description": "Full access (default — set a role to personalise)",
        "allowed_slugs": "all",
    },
    "executive": {
        "display_name": "Executive",
        "description": "Strategy, initiatives, adoption, and high-level dashboards",
        "allowed_slugs": [
            "intro-goodness", "greater-goodness",
            "customers",
            "intro-people",
            "intro-operations", "sales", "profitability", "revenue-bridge",
            "intro-digital", "ai-adoption", "mission-control", "adoption",
            "way-of-working",
            "prompt-builder", "hub-assistant",
            "store-network", "market-share", "whitespace",
        ],
    },
    "store_manager": {
        "display_name": "Store Manager",
        "description": "Store sales, operations, staff training, and AI tools",
        "allowed_slugs": [
            "sales", "store-ops", "profitability", "plu-intel",
            "prompt-builder", "hub-assistant", "skills-academy", "the-paddock",
            "the-rubric",
        ],
    },
    "buyer": {
        "display_name": "Buyer / Procurement",
        "description": "Buying, PLU intelligence, product trends, and supply chain",
        "allowed_slugs": [
            "buying-hub", "plu-intel", "product-intel", "transport",
            "sales", "trending",
            "prompt-builder", "analytics-engine",
            "skills-academy", "the-paddock",
        ],
    },
    "marketing": {
        "display_name": "Marketing",
        "description": "Customer insights, market share, content tools, and assets",
        "allowed_slugs": [
            "customers", "marketing-assets",
            "prompt-builder", "trending", "analytics-engine",
            "hub-assistant", "skills-academy", "the-paddock",
            "market-share", "demographics",
        ],
    },
    "people_culture": {
        "display_name": "People & Culture",
        "description": "Learning, training, approvals, and people development",
        "allowed_slugs": [
            "intro-people", "skills-academy", "the-paddock",
            "prompt-builder", "approvals", "the-rubric",
            "hub-assistant",
        ],
    },
    "finance": {
        "display_name": "Finance / Analyst",
        "description": "Sales, profitability, revenue bridge, and data analysis",
        "allowed_slugs": [
            "sales", "profitability", "revenue-bridge",
            "customers", "analytics-engine",
            "prompt-builder",
            "store-network", "market-share", "whitespace",
        ],
    },
    "viewer": {
        "display_name": "Viewer",
        "description": "Read-only access to learning and basic tools",
        "allowed_slugs": [
            "skills-academy", "the-paddock", "hub-assistant",
            "prompt-builder", "the-rubric",
        ],
    },
}


def get_role_pages(role_key):
    """Return list of allowed page slugs for a role. Returns None for 'all'."""
    role = ROLE_DEFINITIONS.get(role_key)
    if not role:
        return None  # unknown role = all pages
    slugs = role["allowed_slugs"]
    if slugs == "all":
        return None
    return list(slugs)


def get_all_roles():
    """Return list of (role_key, display_name) for UI selector. Excludes admin."""
    return [
        (k, v["display_name"])
        for k, v in ROLE_DEFINITIONS.items()
        if k != "admin"
    ]


def get_role_display_name(role_key):
    """Return human-readable role name."""
    role = ROLE_DEFINITIONS.get(role_key, {})
    return role.get("display_name", role_key)
