"""
Harris Farm Hub — Workstream Registry
Single source of truth for all transformation workstreams.
"""

from typing import Optional

WORKSTREAMS = [
    {
        "id": "scr-2026",
        "name": "Supply Chain Review",
        "description": "Shape the future of our end-to-end supply chain",
        "type": "TRANSFORMATION_READINESS",
        "status": "active",
        "deadline": "2026-04-30",
        "expected_participants": None,
        "questionnaire": "adkar",
        "channel_code": "SCR2026",
        "share_message": (
            "Hey! Harris Farm is reshaping our supply chain and your "
            "perspective matters. Takes 5 mins: {url}"
        ),
    },
    {
        "id": "ai-vision-2026",
        "name": "AI Vision 2026",
        "description": "Help us understand how AI can support your daily work",
        "type": "TRANSFORMATION_READINESS",
        "status": "active",
        "deadline": "2026-06-30",
        "expected_participants": None,
        "questionnaire": "adkar",
        "channel_code": "AIVISION",
        "share_message": (
            "Harris Farm wants to hear how AI can help YOUR role. "
            "5 min survey: {url}"
        ),
    },
    {
        "id": "sc-future-2026",
        "name": "Supply Chain of the Future",
        "description": "Our next-gen supply chain — launching soon",
        "type": "TRANSFORMATION_READINESS",
        "status": "coming_soon",
        "deadline": None,
        "expected_participants": None,
        "questionnaire": "adkar",
        "channel_code": "SCFUTURE",
        "share_message": "",
    },
]


def get_all_workstreams():
    """Return all workstreams."""
    return WORKSTREAMS


def get_active_workstreams():
    """Return workstreams with status 'active'."""
    return [ws for ws in WORKSTREAMS if ws["status"] == "active"]


def get_workstream_by_id(ws_id: str) -> Optional[dict]:
    """Look up a workstream by its ID. Returns None if not found."""
    for ws in WORKSTREAMS:
        if ws["id"] == ws_id:
            return ws
    return None


def get_workstream_by_code(code: str) -> Optional[dict]:
    """Look up a workstream by its channel_code (e.g. 'SCR2026')."""
    code_upper = code.strip().upper()
    for ws in WORKSTREAMS:
        if ws.get("channel_code", "").upper() == code_upper:
            return ws
    return None
