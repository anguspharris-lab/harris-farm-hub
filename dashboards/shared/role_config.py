"""
Harris Farm Hub — Role-Based Navigation Config
Defines which pages each role can see.
"""

# Role definitions: role_key -> {display_name, description, allowed_slugs}
# "admin" and "user" (default) see ALL pages — no filtering.
# Home page (_home) is always accessible — it's handled separately in app.py.

# Restricted pages — only admin and executive roles can see these.
# Sales, Profitability, and Property data is SLT + Grant Enders only.
_RESTRICTED_SLUGS = {
    "sales", "profitability", "revenue-bridge",
    "store-network", "market-share", "demographics",
    "whitespace", "competitor-map", "roce", "cannibalisation",
}

ROLE_DEFINITIONS = {
    "admin": {
        "display_name": "Administrator",
        "description": "Full access to all Hub pages including User Management",
        "allowed_slugs": "all",
    },
    "user": {
        "display_name": "General",
        "description": "General access — excludes financial and property data",
        "allowed_slugs": [
            "strategy-overview", "greater-goodness",
            "intro-people", "intro-operations", "intro-digital",
            "way-of-working",
            "skills-academy", "the-paddock", "prompt-builder", "hub-assistant",
            "customers", "store-ops", "buying-hub", "product-intel", "plu-intel",
            "transport", "analytics-engine",
            "the-rubric", "approvals", "trending",
            "mdhe-dashboard", "mdhe-upload", "mdhe-issues", "mdhe-guide",
        ],
    },
    "executive": {
        "display_name": "Executive / SLT",
        "description": "Full strategic access — sales, profitability, property, and all dashboards",
        "allowed_slugs": [
            "strategy-overview", "greater-goodness",
            "intro-people", "intro-operations", "intro-digital",
            "way-of-working",
            "skills-academy", "the-paddock", "prompt-builder", "hub-assistant",
            "customers", "sales", "profitability", "revenue-bridge",
            "store-ops", "buying-hub", "product-intel", "plu-intel",
            "transport", "analytics-engine",
            "store-network", "market-share", "demographics",
            "whitespace", "competitor-map", "roce", "cannibalisation",
            "ai-adoption", "mission-control", "adoption",
            "mdhe-dashboard", "mdhe-upload", "mdhe-issues", "mdhe-guide",
        ],
    },
    "store_manager": {
        "display_name": "Store Manager",
        "description": "Store operations, staff training, and AI tools",
        "allowed_slugs": [
            "store-ops", "plu-intel",
            "prompt-builder", "hub-assistant", "skills-academy", "the-paddock",
            "the-rubric",
        ],
    },
    "buyer": {
        "display_name": "Buyer / Procurement",
        "description": "Buying, PLU intelligence, product trends, supply chain, and data quality",
        "allowed_slugs": [
            "buying-hub", "plu-intel", "product-intel", "transport",
            "trending",
            "prompt-builder", "analytics-engine",
            "skills-academy", "the-paddock",
            "mdhe-dashboard", "mdhe-issues", "mdhe-guide",
        ],
    },
    "marketing": {
        "display_name": "Marketing",
        "description": "Customer insights, content tools, and assets",
        "allowed_slugs": [
            "customers", "marketing-assets",
            "prompt-builder", "trending", "analytics-engine",
            "hub-assistant", "skills-academy", "the-paddock",
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
        "description": "Customers, analytics, and data quality (financial data via SLT access only)",
        "allowed_slugs": [
            "customers", "analytics-engine",
            "prompt-builder", "hub-assistant",
            "mdhe-dashboard", "mdhe-guide",
        ],
    },
    "data_quality": {
        "display_name": "Data / IT",
        "description": "Master data health, product intel, PLU intel, and data quality",
        "allowed_slugs": [
            "mdhe-dashboard", "mdhe-upload", "mdhe-issues", "mdhe-guide",
            "product-intel", "plu-intel",
            "analytics-engine",
            "prompt-builder", "hub-assistant",
            "skills-academy", "the-paddock",
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
