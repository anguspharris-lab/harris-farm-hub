"""
Harris Farm Hub — Skills Academy Placement Engine
5-scenario placement challenge that determines a user's starting level (L1-L5).
Each scenario is scored 0-5 by Claude API. Total score (0-25) maps to a level.
Also detects initial HiPo (High Potential) flags from placement performance.
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Level mapping — total score (0-25) → starting level (1-5)
# ---------------------------------------------------------------------------

LEVEL_LABELS = {
    1: "L1 — Foundation",
    2: "L2 — Practitioner",
    3: "L3 — Advanced",
    4: "L4 — Expert",
    5: "L5 — Master",
}


def placement_to_level(total_score):
    """Map total score (0-25) to starting level (1-5).

    Scoring bands:
        0-5   → Level 1  (L1)
        6-10  → Level 1  (L1 with recognition)
        11-15 → Level 2  (L2)
        16-20 → Level 3  (L3)
        21-25 → Level 4  (L4)

    Note: Level 5 is never assigned from placement — it must be earned.
    """
    # type: (int) -> int
    score = max(0, min(25, int(total_score)))
    if score <= 10:
        return 1
    elif score <= 15:
        return 2
    elif score <= 20:
        return 3
    else:
        return 4


# ---------------------------------------------------------------------------
# HiPo flag detection
# ---------------------------------------------------------------------------

# Velocity threshold in seconds (3 minutes)
VELOCITY_THRESHOLD_SECONDS = 180


def detect_hipo_flags(responses):
    """Detect initial HiPo (High Potential) flags from placement responses.

    Flags detected:
        - "ambition"          : scenario 5 (application) scored 4 or 5
        - "velocity"          : total time under 3 minutes
        - "iteration"         : scenario 3 (iteration) scored 5
        - "process_thinking"  : scenario 4 (scope) scored 4 or 5

    Args:
        responses: list of dicts with keys:
            scenario_id (int), response (str), score (int), time_seconds (int)

    Returns:
        list of signal type strings (may be empty)
    """
    # type: (list) -> list
    if not responses:
        return []

    flags = []

    # Build a lookup by scenario_id for easy access
    by_scenario = {}
    for r in responses:
        sid = int(r.get("scenario_id", 0))
        by_scenario[sid] = r

    # Check scenario 5 — Application → "ambition"
    s5 = by_scenario.get(5)
    if s5 and int(s5.get("score", 0)) >= 4:
        flags.append("ambition")

    # Check total time → "velocity"
    total_time = sum(int(r.get("time_seconds", 0)) for r in responses)
    if total_time > 0 and total_time < VELOCITY_THRESHOLD_SECONDS:
        flags.append("velocity")

    # Check scenario 3 — Iteration → "iteration"
    s3 = by_scenario.get(3)
    if s3 and int(s3.get("score", 0)) == 5:
        flags.append("iteration")

    # Check scenario 4 — Scope → "process_thinking"
    s4 = by_scenario.get(4)
    if s4 and int(s4.get("score", 0)) >= 4:
        flags.append("process_thinking")

    return flags


# ---------------------------------------------------------------------------
# Claude API scoring prompt & scenario instructions
# ---------------------------------------------------------------------------

PLACEMENT_SCORING_PROMPT = (
    "You are evaluating a Skills Academy placement challenge response "
    "for Harris Farm Markets.\n\n"
    "Score this response from 0-5 based on the scenario type:\n\n"
    "{scenario_type_instructions}\n\n"
    "The user's response:\n{response}\n\n"
    "Return ONLY valid JSON:\n"
    '{{\"score\": <int 0-5>, \"feedback\": \"<one sentence>\"}}'
)

# Scenario-specific scoring instructions keyed by scenario type name
SCENARIO_SCORING = {
    "recognition": (
        "Score based on how many issues were correctly identified in the "
        "weak prompt. 0=none, 1=1 issue, 2=2 issues, 3=3 issues vaguely, "
        "4=3+ issues clearly, 5=all issues with specific fixes."
    ),
    "construction": (
        "Score the prompt quality: 0=gibberish, 1=bare question, "
        "2=has some structure, 3=decent with gaps, 4=good prompt missing "
        "1 element, 5=excellent with clarity+context+data+format+action."
    ),
    "iteration": (
        "Score improvement quality: 0=no change, 1=trivial change, "
        "2=addresses 1 feedback point, 3=addresses most feedback, "
        "4=good rewrite addressing all feedback, 5=excellent rewrite "
        "that exceeds the feedback."
    ),
    "scope": (
        "Score task decomposition: 0=no breakdown, 1=restates task, "
        "2=vague split, 3=reasonable split missing detail, 4=good "
        "decomposition with clear handoffs, 5=expert decomposition "
        "with sequencing and dependencies."
    ),
    "application": (
        "Score workflow design: 0=no workflow, 1=single generic prompt, "
        "2=basic sequence, 3=reasonable workflow missing context, 4=good "
        "workflow with role-specific detail, 5=expert workflow with "
        "iteration loops and quality checks."
    ),
}

# Ordered list mapping scenario_id (1-5) to scenario type
SCENARIO_ORDER = [
    "recognition",    # Scenario 1
    "construction",   # Scenario 2
    "iteration",      # Scenario 3
    "scope",          # Scenario 4
    "application",    # Scenario 5
]


def get_scoring_prompt(scenario_id, response_text):
    """Build the full scoring prompt for a given scenario and response.

    Args:
        scenario_id: int 1-5 identifying the scenario
        response_text: the user's response string

    Returns:
        Formatted prompt string ready to send to Claude API.
    """
    # type: (int, str) -> str
    idx = max(0, min(4, int(scenario_id) - 1))
    scenario_type = SCENARIO_ORDER[idx]
    instructions = SCENARIO_SCORING.get(scenario_type, "Score from 0-5.")

    return PLACEMENT_SCORING_PROMPT.format(
        scenario_type_instructions=instructions,
        response=response_text,
    )


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_placement_tables(conn):
    """Create sa_placement table. Safe to call repeatedly.

    The table stores one row per user with their placement results,
    including the full scored responses as JSON and any HiPo flags.
    """
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS sa_placement (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL UNIQUE,
        responses_json TEXT,
        total_score INTEGER DEFAULT 0,
        assigned_level INTEGER DEFAULT 1,
        hipo_flags_json TEXT DEFAULT '[]',
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_sap_user "
        "ON sa_placement(user_id)"
    )

    conn.commit()


# ---------------------------------------------------------------------------
# Placement queries
# ---------------------------------------------------------------------------

def get_user_placement(db_path, user_id):
    """Return placement result for a user, or None if not yet placed.

    Args:
        db_path: path to the SQLite database file
        user_id: unique user identifier (email)

    Returns:
        dict with placement details, or None
    """
    # type: (str, str) -> Optional[dict]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM sa_placement WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    d = dict(row)
    d["responses"] = json.loads(d.get("responses_json") or "[]")
    d["hipo_flags"] = json.loads(d.get("hipo_flags_json") or "[]")
    d["level_label"] = LEVEL_LABELS.get(d.get("assigned_level", 1), "L1 — Foundation")
    # Remove raw JSON columns from the returned dict
    d.pop("responses_json", None)
    d.pop("hipo_flags_json", None)
    return d


def has_completed_placement(db_path, user_id):
    """Quick check: has this user already completed placement?

    Args:
        db_path: path to the SQLite database file
        user_id: unique user identifier (email)

    Returns:
        True if placement record exists, False otherwise
    """
    # type: (str, str) -> bool
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT 1 FROM sa_placement WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return row is not None


# ---------------------------------------------------------------------------
# Placement submission
# ---------------------------------------------------------------------------

def submit_placement(db_path, user_id, scored_responses):
    """Store placement results and return summary.

    This function expects responses that have ALREADY been scored by the
    API layer (which calls Claude). It calculates the total score, maps
    to a starting level, detects HiPo flags, and persists everything.

    Args:
        db_path: path to the SQLite database file
        user_id: unique user identifier (email)
        scored_responses: list of dicts, each with keys:
            scenario_id (int), response (str), score (int), time_seconds (int)
            Optionally also: feedback (str)

    Returns:
        dict with: user_id, total_score, assigned_level, level_label,
                   hipo_flags, responses, created_at
    """
    # type: (str, str, list) -> dict

    # Calculate total score from individual scenario scores
    total_score = 0
    for r in scored_responses:
        score = int(r.get("score", 0))
        score = max(0, min(5, score))
        total_score += score

    # Map to starting level
    assigned_level = placement_to_level(total_score)

    # Detect HiPo flags
    hipo_flags = detect_hipo_flags(scored_responses)

    # Serialise for storage
    responses_json = json.dumps(scored_responses)
    hipo_flags_json = json.dumps(hipo_flags)
    now = datetime.utcnow().isoformat()

    # Persist — UNIQUE on user_id, so use INSERT OR REPLACE
    conn = sqlite3.connect(db_path)
    conn.execute(
        """INSERT OR REPLACE INTO sa_placement
           (user_id, responses_json, total_score, assigned_level,
            hipo_flags_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, responses_json, total_score, assigned_level,
         hipo_flags_json, now),
    )
    conn.commit()
    conn.close()

    return {
        "user_id": user_id,
        "total_score": total_score,
        "assigned_level": assigned_level,
        "level_label": LEVEL_LABELS.get(assigned_level, "L1 — Foundation"),
        "hipo_flags": hipo_flags,
        "responses": scored_responses,
        "created_at": now,
    }


# ---------------------------------------------------------------------------
# Placement analytics (for admin / Mission Control)
# ---------------------------------------------------------------------------

def get_placement_summary(db_path):
    """Return aggregate placement statistics.

    Useful for admin dashboards / Mission Control to see the distribution
    of placement outcomes across all users.

    Args:
        db_path: path to the SQLite database file

    Returns:
        dict with: total_placed, level_distribution, avg_score,
                   hipo_count, recent_placements
    """
    # type: (str) -> dict
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Total users who have completed placement
    total = conn.execute(
        "SELECT COUNT(*) as cnt FROM sa_placement"
    ).fetchone()["cnt"]

    # Level distribution
    level_rows = conn.execute(
        "SELECT assigned_level, COUNT(*) as cnt "
        "FROM sa_placement GROUP BY assigned_level "
        "ORDER BY assigned_level"
    ).fetchall()
    level_dist = {}
    for r in level_rows:
        level_key = "L{}".format(r["assigned_level"])
        level_dist[level_key] = r["cnt"]

    # Average score
    avg_row = conn.execute(
        "SELECT AVG(total_score) as avg_score FROM sa_placement"
    ).fetchone()
    avg_score = round(float(avg_row["avg_score"]), 1) if avg_row["avg_score"] else 0.0

    # Count users with any HiPo flags
    hipo_rows = conn.execute(
        "SELECT COUNT(*) as cnt FROM sa_placement "
        "WHERE hipo_flags_json != '[]'"
    ).fetchone()
    hipo_count = hipo_rows["cnt"] if hipo_rows else 0

    # Recent placements (last 10)
    recent = conn.execute(
        "SELECT user_id, total_score, assigned_level, "
        "hipo_flags_json, created_at "
        "FROM sa_placement ORDER BY created_at DESC LIMIT 10"
    ).fetchall()

    recent_list = []
    for r in recent:
        d = dict(r)
        d["hipo_flags"] = json.loads(d.get("hipo_flags_json") or "[]")
        d["level_label"] = LEVEL_LABELS.get(d["assigned_level"], "L1")
        d.pop("hipo_flags_json", None)
        recent_list.append(d)

    conn.close()

    return {
        "total_placed": total,
        "level_distribution": level_dist,
        "avg_score": avg_score,
        "hipo_count": hipo_count,
        "recent_placements": recent_list,
    }


def reset_user_placement(db_path, user_id):
    """Delete a user's placement record so they can retake it.

    This is an admin-only action. The API layer should enforce permissions.

    Args:
        db_path: path to the SQLite database file
        user_id: unique user identifier (email)

    Returns:
        True if a record was deleted, False if user had no placement
    """
    # type: (str, str) -> bool
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "DELETE FROM sa_placement WHERE user_id = ?",
        (user_id,),
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
