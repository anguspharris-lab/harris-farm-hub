"""
Harris Farm Hub — Monday.com Connector
GraphQL client for fetching initiative data from Monday.com boards.
Graceful fallback when MONDAY_API_KEY is not configured.
"""

import os
import logging
from pathlib import Path
from typing import Optional

import streamlit as st

_log = logging.getLogger(__name__)

# Load .env so Streamlit process picks up MONDAY_API_KEY
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(str(_env_path))
except ImportError:
    pass

MONDAY_API_URL = "https://api.monday.com/v2"

# Monday.com board IDs for each pillar
BOARD_IDS = {
    "P1": 5001442659,
    "P2": 5001460085,
    "P3": 5001476308,
    "P4": 5001480788,
    "P5": 5001485134,
}

# Status label -> category mapping (covers all labels found in the 5 boards)
_STATUS_MAP = {
    "Done": "done",
    "Complete": "done",
    "Completed": "done",
    "Immediate requirements complete": "done",
    "Working on it": "in_progress",
    "In Progress": "in_progress",
    "Stuck": "stuck",
    "Blocked": "stuck",
    "Future steps": "not_started",
    "Not Started": "not_started",
    "": "not_started",
}


def is_configured():
    """Check if Monday.com API key is available."""
    key = os.getenv("MONDAY_API_KEY", "").strip()
    return bool(key)


def _get_headers():
    """Build authorization headers for Monday.com API."""
    key = os.getenv("MONDAY_API_KEY", "").strip()
    return {
        "Authorization": key,
        "Content-Type": "application/json",
    }


def _categorise_status(status_label):
    """Map a Monday.com status label to a category."""
    if not status_label:
        return "not_started"
    return _STATUS_MAP.get(status_label, "not_started")


@st.cache_data(ttl=300)
def fetch_board_items(board_id):
    """Fetch all items from a Monday.com board.

    Returns list of dicts: [{name, status, status_category, owner, group,
                             due_date, timeline, priority}, ...]
    Returns empty list if not configured or on error.
    """
    if not is_configured():
        return []

    import requests

    query = """
    query ($boardId: [ID!]) {
      boards(ids: $boardId) {
        name
        items_page(limit: 500) {
          items {
            name
            group { title }
            column_values {
              id
              text
              type
            }
          }
        }
      }
    }
    """

    try:
        resp = requests.post(
            MONDAY_API_URL,
            json={"query": query, "variables": {"boardId": [str(board_id)]}},
            headers=_get_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        # Check for API errors
        if "errors" in data:
            _log.warning("Monday.com API error: %s", data["errors"])
            return []

        boards = data.get("data", {}).get("boards", [])
        if not boards:
            return []

        items = boards[0].get("items_page", {}).get("items", [])
        results = []
        for item in items:
            # Extract columns by their known IDs
            status = ""
            owner = ""
            due_date = ""
            timeline = ""
            priority = ""

            for c in item.get("column_values", []):
                col_id = c.get("id", "")
                col_text = c.get("text") or ""

                if col_id == "project_status":
                    status = col_text
                elif col_id == "project_owner":
                    owner = col_text
                elif col_id == "project_task_completion_date":
                    due_date = col_text
                elif col_id == "project_timeline":
                    timeline = col_text
                elif col_id == "project_priority":
                    priority = col_text

            # Fallback: if no project_status found, try any status-type column
            if not status:
                for c in item.get("column_values", []):
                    if c.get("type") == "status" and c.get("text"):
                        status = c["text"]
                        break

            # Fallback: if no project_owner found, try any people-type column
            if not owner:
                for c in item.get("column_values", []):
                    if c.get("type") == "people" and c.get("text"):
                        owner = c["text"]
                        break

            results.append({
                "name": item["name"],
                "status": status,
                "status_category": _categorise_status(status),
                "owner": owner,
                "group": item.get("group", {}).get("title", ""),
                "due_date": due_date,
                "timeline": timeline,
                "priority": priority,
            })
        return results

    except Exception as exc:
        _log.warning("Monday.com fetch failed for board %s: %s", board_id, exc)
        return []


@st.cache_data(ttl=300)
def fetch_board_name(board_id):
    """Fetch the name of a Monday.com board."""
    if not is_configured():
        return ""

    import requests

    query = """
    query ($boardId: [ID!]) {
      boards(ids: $boardId) { name }
    }
    """
    try:
        resp = requests.post(
            MONDAY_API_URL,
            json={"query": query, "variables": {"boardId": [str(board_id)]}},
            headers=_get_headers(),
            timeout=10,
        )
        data = resp.json()
        boards = data.get("data", {}).get("boards", [])
        return boards[0]["name"] if boards else ""
    except Exception:
        return ""


def fetch_board_summary(board_id):
    """Fetch a summary of a Monday.com board.

    Returns dict: {total, done, in_progress, stuck, not_started, configured}
    """
    if not is_configured():
        return {
            "total": 0, "done": 0, "in_progress": 0,
            "stuck": 0, "not_started": 0, "configured": False,
        }

    items = fetch_board_items(board_id)
    summary = {
        "total": len(items),
        "done": 0,
        "in_progress": 0,
        "stuck": 0,
        "not_started": 0,
        "configured": True,
    }

    for item in items:
        cat = item.get("status_category", "not_started")
        if cat in summary:
            summary[cat] += 1

    return summary


def fetch_all_pillar_summaries():
    """Fetch summaries for all 5 pillar boards.

    Returns dict: {P1: {summary}, P2: {summary}, ...}
    """
    result = {}
    for pillar_id, board_id in BOARD_IDS.items():
        result[pillar_id] = fetch_board_summary(board_id)
    return result
