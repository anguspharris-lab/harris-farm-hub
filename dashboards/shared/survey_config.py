"""
Harris Farm Hub — Shared Survey Configuration
Single source of truth for survey questions, departments, and roles.
Used by the web form AND the conversation engine so all channels stay in sync.
"""

# ---------------------------------------------------------------------------
# Demographics
# ---------------------------------------------------------------------------

DEPARTMENTS = [
    "Buying", "Operations", "Supply Chain", "IT / Digital",
    "Finance", "People & Culture", "Marketing", "Property",
    "Executive", "Other",
]

ROLE_LEVELS = [
    "Team Member", "Team Lead", "Manager",
    "Department Head", "Executive",
]

# ---------------------------------------------------------------------------
# ADKAR Sections — the questionnaire
# Each section has cards, each card has fields (slider or text).
# The conversation engine iterates this list to generate questions.
# ---------------------------------------------------------------------------

SECTIONS = [
    {
        "key": "awareness",
        "label": "Awareness",
        "icon": "\U0001f4a1",
        "color": "#C0392B",
        "question": "Do we understand why change is needed?",
        "cards": [
            {
                "title": "Why Transform?",
                "icon": "\U0001f525",
                "fields": [
                    {
                        "key": "awareness_score",
                        "type": "slider",
                        "label": "How aware is your team that change is needed?",
                        "help": "1 = no awareness, 10 = fully understand the urgency",
                    },
                    {
                        "key": "why_transform",
                        "type": "text",
                        "label": (
                            "What makes you believe Harris Farm needs to "
                            "transform how we use AI and data?"
                        ),
                        "help": (
                            "What happens if we don\u2019t? "
                            "What\u2019s the cost of standing still?"
                        ),
                        "rows": 4,
                    },
                ],
            },
        ],
    },
    {
        "key": "desire",
        "label": "Desire",
        "icon": "\U0001f525",
        "color": "#C0392B",
        "question": "Do you want to be part of it?",
        "cards": [
            {
                "title": "Personal Commitment",
                "icon": "\U0001f91d",
                "fields": [
                    {
                        "key": "desire_score",
                        "type": "slider",
                        "label": (
                            "How much do you personally want to be "
                            "part of this transformation?"
                        ),
                        "help": "1 = not at all, 10 = I\u2019m all in",
                    },
                    {
                        "key": "desire_driver",
                        "type": "text",
                        "label": "What\u2019s driving that score?",
                        "help": "What excites you? What holds you back?",
                        "rows": 3,
                    },
                ],
            },
        ],
    },
    {
        "key": "knowledge",
        "label": "Knowledge",
        "icon": "\U0001f4da",
        "color": "#C8971F",
        "question": "Do we know what good looks like?",
        "cards": [
            {
                "title": "The 12-Month Picture",
                "icon": "\U0001f52d",
                "fields": [
                    {
                        "key": "knowledge_score",
                        "type": "slider",
                        "label": (
                            "How clear is your understanding of what "
                            "AI First looks like?"
                        ),
                        "help": "1 = no idea, 10 = crystal clear picture",
                    },
                    {
                        "key": "twelve_month_picture",
                        "type": "text",
                        "label": (
                            "What does AI First look like in your "
                            "department in 12 months?"
                        ),
                        "help": (
                            "How would your day be different? What would "
                            "your team be doing that they can\u2019t do today?"
                        ),
                        "rows": 4,
                    },
                    {
                        "key": "lighthouse",
                        "type": "text",
                        "label": (
                            "What\u2019s your lighthouse on the hill? "
                            "The big exciting vision you\u2019d love to see."
                        ),
                        "help": (
                            "Dream big. What would make you proud to say "
                            "\u2018we built that\u2019?"
                        ),
                        "rows": 4,
                    },
                ],
            },
        ],
    },
    {
        "key": "ability",
        "label": "Ability",
        "icon": "\U0001f4aa",
        "color": "#1565C0",
        "question": "Can we actually do it?",
        "cards": [
            {
                "title": "Current Capability",
                "icon": "\U0001f3af",
                "fields": [
                    {
                        "key": "capability_score",
                        "type": "slider",
                        "label": "What is your current AI capability?",
                        "help": (
                            "1 = no exposure at all, "
                            "10 = using AI daily and confidently"
                        ),
                    },
                    {
                        "key": "biggest_gap",
                        "type": "text",
                        "label": (
                            "What\u2019s the single biggest skill or tool "
                            "gap stopping you right now?"
                        ),
                        "help": (
                            "Be specific \u2014 what would make the biggest "
                            "difference if it was fixed tomorrow?"
                        ),
                        "rows": 3,
                    },
                ],
            },
        ],
    },
    {
        "key": "reinforcement",
        "label": "Reinforcement",
        "icon": "\U0001f512",
        "color": "#7C3AED",
        "question": "Will the change stick?",
        "cards": [
            {
                "title": "Making It Last",
                "icon": "\U0001f331",
                "fields": [
                    {
                        "key": "reinforcement_score",
                        "type": "slider",
                        "label": "How confident are you this will stick?",
                        "help": (
                            "1 = it will fizzle out, "
                            "10 = this is permanent change"
                        ),
                    },
                    {
                        "key": "confidence_lasting",
                        "type": "text",
                        "label": (
                            "What would make you confident this "
                            "transformation will actually happen and last?"
                        ),
                        "help": (
                            "What needs to be true for this to stick "
                            "\u2014 not just launch, but sustain?"
                        ),
                        "rows": 4,
                    },
                    {
                        "key": "need_from_leadership",
                        "type": "text",
                        "label": (
                            "What do you need from leadership "
                            "to keep going?"
                        ),
                        "help": (
                            "Support, resources, clarity, permission, "
                            "protection \u2014 what matters most?"
                        ),
                        "rows": 3,
                    },
                ],
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# Payload mapping — how form field keys map to BigQuery columns
# Used by the conversation engine to build the submit payload.
# ---------------------------------------------------------------------------

FIELD_TO_BQ = {
    "awareness_score": "adkar_awareness",
    "why_transform": "adkar_awareness_text",
    "desire_score": "adkar_desire",
    "desire_driver": "adkar_desire_text",
    "knowledge_score": "adkar_knowledge",
    "twelve_month_picture": "adkar_knowledge_text",
    "lighthouse": "lighthouse_vision",
    "capability_score": "adkar_ability",
    "biggest_gap": "adkar_ability_text",
    "reinforcement_score": "adkar_reinforcement",
    "confidence_lasting": "adkar_reinforcement_text",
    "need_from_leadership": "unlock_value",
}

# Score interpretation thresholds
SCORE_THRESHOLDS = [
    (8, "Strong", "#2D6A2D"),
    (6, "Adequate", "#C8971F"),
    (4, "Gap", "#C0392B"),
    (0, "Critical", "#C0392B"),
]


def score_label(v):
    """Return (label, color) for a score value."""
    for threshold, label, color in SCORE_THRESHOLDS:
        if v >= threshold:
            return label, color
    return "Critical", "#C0392B"


def build_field_sequence():
    """Generate ordered list of (section_idx, field_idx, field_dict, section_dict)
    from SECTIONS. Used by the conversation engine."""
    seq = []
    for si, section in enumerate(SECTIONS):
        for card in section["cards"]:
            for field in card["fields"]:
                seq.append((si, len(seq), field, section))
    return seq
