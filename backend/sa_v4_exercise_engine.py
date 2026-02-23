"""
Skills Academy v4 — Adaptive Exercise Selection Engine
Handles exercise selection (standard/stretch/elite), curveball injection,
foundation checks for provisional users, tier advancement/demotion,
and skip-ahead eligibility.
"""

import json
import random
import sqlite3
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIERS = ("standard", "stretch", "elite")
TIER_UP = {"standard": "stretch", "stretch": "elite", "elite": "elite"}
TIER_DOWN = {"elite": "stretch", "stretch": "standard", "standard": "standard"}

# Tier advancement thresholds
ADVANCE_THRESHOLD = 0.8    # >= 80% to move up a tier
DEMOTE_THRESHOLD = 0.6     # < 60% to drop a tier
SKIP_AHEAD_COUNT = 3       # 3 consecutive elite passes to skip ahead

# Curveball injection settings
CURVEBALL_MIN_INTERVAL = 3    # Minimum exercises before curveball eligible
CURVEBALL_PROB_AT_MIN = 0.75  # 75% chance at exactly 3 exercises since last
FOUNDATION_PASS_RATE = 0.80   # 80% pass rate needed for foundation dimension


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _connect(db_path):
    # type: (str) -> sqlite3.Connection
    """Create a connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row):
    # type: (sqlite3.Row) -> dict
    """Convert sqlite3.Row to plain dict."""
    if row is None:
        return {}
    return dict(row)


def _get_module_id(conn, module_code):
    # type: (sqlite3.Connection, str) -> Optional[int]
    """Resolve module_code to module_id."""
    row = conn.execute(
        "SELECT module_id FROM sa_modules WHERE module_code = ?",
        (module_code,)
    ).fetchone()
    if row:
        return row["module_id"]
    return None


def _get_module_level(conn, module_code):
    # type: (sqlite3.Connection, str) -> Optional[int]
    """Get the level_number for a module_code."""
    row = conn.execute(
        "SELECT level_number FROM sa_modules WHERE module_code = ?",
        (module_code,)
    ).fetchone()
    if row:
        return row["level_number"]
    return None


def _get_user_placed_level(conn, user_id):
    # type: (sqlite3.Connection, str) -> Optional[int]
    """Get the user's placed level from placement results."""
    row = conn.execute(
        "SELECT placed_level FROM sa_placement_v4 WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    if row:
        return row["placed_level"]
    return None


def _ensure_exercise_state(conn, user_id, module_code):
    # type: (sqlite3.Connection, str, str) -> dict
    """Get or create exercise state for user+module. Returns state dict.
    The sa_exercise_state table uses module_code (text), and columns
    consecutive_elite and attempts (from v3 schema)."""
    row = conn.execute(
        "SELECT * FROM sa_exercise_state WHERE user_id = ? AND module_code = ?",
        (user_id, module_code)
    ).fetchone()
    if row:
        d = _row_to_dict(row)
        # Alias v3 column names to v4 expected names
        d["consecutive_high_scores"] = d.get("consecutive_elite", 0)
        d["exercises_since_curveball"] = d.get("attempts", 0)
        return d

    # Create initial state
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO sa_exercise_state "
        "(user_id, module_code, current_tier, consecutive_elite, "
        "attempts, updated_at) "
        "VALUES (?,?,?,?,?,?)",
        (user_id, module_code, "standard", 0, 0, now)
    )
    conn.commit()

    row = conn.execute(
        "SELECT * FROM sa_exercise_state WHERE user_id = ? AND module_code = ?",
        (user_id, module_code)
    ).fetchone()
    d = _row_to_dict(row)
    d["consecutive_high_scores"] = d.get("consecutive_elite", 0)
    d["exercises_since_curveball"] = d.get("attempts", 0)
    return d


def _get_completed_exercise_ids(conn, user_id, module_id=None):
    # type: (sqlite3.Connection, str, Optional[int]) -> list
    """Get exercise_ids the user has already completed, optionally for a module."""
    if module_id is not None:
        rows = conn.execute(
            "SELECT DISTINCT er.exercise_id "
            "FROM sa_exercise_results er "
            "JOIN sa_exercises e ON er.exercise_id = e.exercise_id "
            "WHERE er.user_id = ? AND e.module_id = ?",
            (user_id, module_id)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT DISTINCT exercise_id FROM sa_exercise_results WHERE user_id = ?",
            (user_id,)
        ).fetchall()
    return [r["exercise_id"] for r in rows]


def _format_exercise(row, exercise_type="normal"):
    # type: (dict, str) -> dict
    """Format an exercise row into the standard return dict."""
    return {
        "exercise_id": row["exercise_id"],
        "exercise_title": row["exercise_title"],
        "scenario_text": row["scenario_text"],
        "tier": row["tier"],
        "context_tag": row["context_tag"],
        "exercise_type": exercise_type,
        "rubric_code": row["rubric_code"],
        "pass_score": row["pass_score"],
        "xp_reward": row["xp_reward"],
        "curveball_type": row.get("curveball_type"),
        "expected_approach": row.get("expected_approach"),
    }


# ---------------------------------------------------------------------------
# Core Selection
# ---------------------------------------------------------------------------

def get_next_exercise(db_path, user_id, module_code):
    # type: (str, str, str) -> dict
    """The main function. Returns the next exercise for this user in this module.

    Decision logic:
    1. Get user's verification status (provisional or confirmed)
    2. If provisional AND foundation checks needed for levels below:
       - Check sa_mastery_evidence for foundation dimension
       - If foundation_score < 80% for any level below current -> inject foundation check
    3. Get exercise state for this module (current tier, exercises_since_curveball)
    4. If exercises_since_curveball >= 3 (random 3-4): inject curveball at user's level
    5. Otherwise: return next exercise at current tier

    Returns dict with:
    - exercise_id, exercise_title, scenario_text, tier, context_tag
    - exercise_type: "normal" | "curveball" | "foundation_check"
    - rubric_code, pass_score, xp_reward
    - curveball_type (if curveball)
    """
    conn = _connect(db_path)
    try:
        module_id = _get_module_id(conn, module_code)
        if module_id is None:
            return {"error": "Module not found: {}".format(module_code)}

        level = _get_module_level(conn, module_code)
        placed_level = _get_user_placed_level(conn, user_id)

        # Step 1: Check verification status
        verification = conn.execute(
            "SELECT * FROM sa_verification_status "
            "WHERE user_id = ? ORDER BY level_number DESC LIMIT 1",
            (user_id,)
        ).fetchone()

        is_provisional = False
        if verification:
            is_provisional = verification["level_status"] == "provisional"

        # Step 2: Foundation check injection for provisional users
        if is_provisional and placed_level is not None:
            check_level = needs_foundation_check(db_path, user_id)
            if check_level is not None:
                foundation_ex = get_foundation_exercise(db_path, user_id, check_level)
                if foundation_ex is not None:
                    return foundation_ex

        # Step 3: Get exercise state
        state = _ensure_exercise_state(conn, user_id, module_code)
        current_tier = state["current_tier"]
        exercises_since = state["exercises_since_curveball"]

        # Step 4: Curveball injection
        if _should_inject_curveball(exercises_since):
            curveball = get_curveball_exercise(db_path, user_id, level)
            if curveball is not None:
                # Reset curveball counter
                conn.execute(
                    "UPDATE sa_exercise_state SET attempts = 0, "
                    "updated_at = ? WHERE user_id = ? AND module_code = ?",
                    (datetime.utcnow().isoformat(), user_id, module_code)
                )
                conn.commit()
                return curveball

        # Step 5: Normal exercise at current tier
        completed_ids = _get_completed_exercise_ids(conn, user_id, module_id)

        # Build exclusion clause
        if completed_ids:
            placeholders = ",".join("?" for _ in completed_ids)
            exclude_clause = " AND e.exercise_id NOT IN ({})".format(placeholders)
            params = [module_id, current_tier] + completed_ids
        else:
            exclude_clause = ""
            params = [module_id, current_tier]

        query = (
            "SELECT * FROM sa_exercises e "
            "WHERE e.module_id = ? AND e.tier = ? AND e.is_curveball = 0"
            "{} ORDER BY RANDOM() LIMIT 1".format(exclude_clause)
        )
        row = conn.execute(query, params).fetchone()

        if row:
            # Increment curveball counter
            conn.execute(
                "UPDATE sa_exercise_state SET attempts = ?, "
                "updated_at = ? WHERE user_id = ? AND module_code = ?",
                (exercises_since + 1, datetime.utcnow().isoformat(), user_id, module_code)
            )
            conn.commit()
            return _format_exercise(_row_to_dict(row), "normal")

        # Fallback: try adjacent tiers if no exercises at current tier
        for fallback_tier in TIERS:
            if fallback_tier == current_tier:
                continue
            if completed_ids:
                placeholders = ",".join("?" for _ in completed_ids)
                exclude_clause = " AND e.exercise_id NOT IN ({})".format(placeholders)
                params = [module_id, fallback_tier] + completed_ids
            else:
                exclude_clause = ""
                params = [module_id, fallback_tier]

            query = (
                "SELECT * FROM sa_exercises e "
                "WHERE e.module_id = ? AND e.tier = ? AND e.is_curveball = 0"
                "{} ORDER BY RANDOM() LIMIT 1".format(exclude_clause)
            )
            row = conn.execute(query, params).fetchone()
            if row:
                conn.execute(
                    "UPDATE sa_exercise_state SET attempts = ?, "
                    "updated_at = ? WHERE user_id = ? AND module_code = ?",
                    (exercises_since + 1, datetime.utcnow().isoformat(), user_id, module_code)
                )
                conn.commit()
                return _format_exercise(_row_to_dict(row), "normal")

        # All exercises completed for this module
        return {
            "exercise_id": None,
            "exercise_type": "complete",
            "message": "All exercises completed for module {}".format(module_code),
        }
    finally:
        conn.close()


def get_adaptive_tier(db_path, user_id, module_code):
    # type: (str, str, str) -> dict
    """Get current adaptive tier for user on module.
    Returns: {current_tier, consecutive_high_scores, skip_ahead_eligible, exercises_completed}
    """
    conn = _connect(db_path)
    try:
        module_id = _get_module_id(conn, module_code)
        if module_id is None:
            return {
                "current_tier": "standard",
                "consecutive_high_scores": 0,
                "skip_ahead_eligible": False,
                "exercises_completed": 0,
            }

        state = _ensure_exercise_state(conn, user_id, module_code)

        # Count completed exercises
        completed = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_exercise_results er "
            "JOIN sa_exercises e ON er.exercise_id = e.exercise_id "
            "WHERE er.user_id = ? AND e.module_id = ?",
            (user_id, module_id)
        ).fetchone()
        exercises_completed = completed["cnt"] if completed else 0

        current_tier = state["current_tier"]
        consecutive = state["consecutive_high_scores"]
        skip_eligible = (current_tier == "elite" and consecutive >= SKIP_AHEAD_COUNT)

        return {
            "current_tier": current_tier,
            "consecutive_high_scores": consecutive,
            "skip_ahead_eligible": skip_eligible,
            "exercises_completed": exercises_completed,
        }
    finally:
        conn.close()


def update_adaptive_tier(db_path, user_id, module_code, score_pct):
    # type: (str, str, str, float) -> dict
    """After exercise scored, update tier:
    - score_pct >= 0.8 -> advance tier, increment consecutive_high_scores
    - score_pct < 0.6 -> drop tier, reset consecutive
    - Otherwise: stay same, reset consecutive
    - Increment exercises_since_curveball counter
    Returns: {new_tier, previous_tier, changed, consecutive_high_scores, skip_ahead_eligible}
    """
    conn = _connect(db_path)
    try:
        module_id = _get_module_id(conn, module_code)
        if module_id is None:
            return {"error": "Module not found: {}".format(module_code)}

        state = _ensure_exercise_state(conn, user_id, module_code)
        previous_tier = state["current_tier"]
        consecutive = state["consecutive_high_scores"]

        if score_pct >= ADVANCE_THRESHOLD:
            # Advance tier
            new_tier = TIER_UP[previous_tier]
            consecutive = consecutive + 1
        elif score_pct < DEMOTE_THRESHOLD:
            # Demote tier
            new_tier = TIER_DOWN[previous_tier]
            consecutive = 0
        else:
            # Stay same
            new_tier = previous_tier
            consecutive = 0

        changed = (new_tier != previous_tier)
        skip_eligible = (new_tier == "elite" and consecutive >= SKIP_AHEAD_COUNT)

        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE sa_exercise_state SET current_tier = ?, "
            "consecutive_elite = ?, updated_at = ? "
            "WHERE user_id = ? AND module_code = ?",
            (new_tier, consecutive, now, user_id, module_code)
        )
        conn.commit()

        return {
            "new_tier": new_tier,
            "previous_tier": previous_tier,
            "changed": changed,
            "consecutive_high_scores": consecutive,
            "skip_ahead_eligible": skip_eligible,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Curveball Logic
# ---------------------------------------------------------------------------

def _should_inject_curveball(exercises_since):
    # type: (int) -> bool
    """Internal: decide based on counter value whether to inject curveball.
    75% chance at exactly 3 exercises since last, 100% at 4+."""
    if exercises_since >= CURVEBALL_MIN_INTERVAL + 1:
        return True
    if exercises_since >= CURVEBALL_MIN_INTERVAL:
        return random.random() < CURVEBALL_PROB_AT_MIN
    return False


def should_inject_curveball(db_path, user_id, module_code):
    # type: (str, str, str) -> bool
    """True if exercises_since_curveball >= 3 and random check passes
    (75% chance at 3, 100% at 4+)."""
    conn = _connect(db_path)
    try:
        module_id = _get_module_id(conn, module_code)
        if module_id is None:
            return False

        state = _ensure_exercise_state(conn, user_id, module_code)
        exercises_since = state["exercises_since_curveball"]
        return _should_inject_curveball(exercises_since)
    finally:
        conn.close()


def get_curveball_exercise(db_path, user_id, level):
    # type: (str, str, int) -> Optional[dict]
    """Pick a curveball the user hasn't seen yet at their level.
    Query sa_exercises WHERE is_curveball=1 and module level matches.
    Exclude ones already in sa_exercise_results for this user."""
    conn = _connect(db_path)
    try:
        # Get all completed curveball exercise_ids for this user
        completed_ids = []
        rows = conn.execute(
            "SELECT DISTINCT exercise_id FROM sa_exercise_results "
            "WHERE user_id = ? AND is_curveball_result = 1",
            (user_id,)
        ).fetchall()
        completed_ids = [r["exercise_id"] for r in rows]

        # Find curveball exercises at the user's level (via module level_number)
        if completed_ids:
            placeholders = ",".join("?" for _ in completed_ids)
            exclude_clause = " AND e.exercise_id NOT IN ({})".format(placeholders)
            params = [level] + completed_ids
        else:
            exclude_clause = ""
            params = [level]

        query = (
            "SELECT e.* FROM sa_exercises e "
            "JOIN sa_modules m ON e.module_id = m.module_id "
            "WHERE e.is_curveball = 1 AND m.level_number = ?"
            "{} ORDER BY RANDOM() LIMIT 1".format(exclude_clause)
        )
        row = conn.execute(query, params).fetchone()
        if row:
            return _format_exercise(_row_to_dict(row), "curveball")
        return None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Foundation Check Logic
# ---------------------------------------------------------------------------

def needs_foundation_check(db_path, user_id):
    # type: (str, str) -> Optional[int]
    """Check if user needs a foundation check.
    Returns the level to check, or None.
    Logic: For each level below user's placed level, check sa_mastery_evidence
    for 'foundation' dimension. If < 80% pass rate (or no evidence), return that level.
    Only applies when verification_status.level_status == 'provisional'.
    """
    conn = _connect(db_path)
    try:
        # Get user's current verification status
        verification = conn.execute(
            "SELECT * FROM sa_verification_status "
            "WHERE user_id = ? AND level_status = 'provisional' "
            "ORDER BY level_number DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        if not verification:
            return None

        placed_level = verification["level_number"]

        # Check each level below the placed level
        for check_level in range(1, placed_level):
            # Count foundation evidence for this level
            total = conn.execute(
                "SELECT COUNT(*) as cnt FROM sa_mastery_evidence "
                "WHERE user_id = ? AND target_level = ? AND dimension = 'foundation'",
                (user_id, check_level)
            ).fetchone()
            total_count = total["cnt"] if total else 0

            if total_count == 0:
                # No foundation evidence at all for this level
                return check_level

            # Check pass rate
            passed = conn.execute(
                "SELECT COUNT(*) as cnt FROM sa_mastery_evidence "
                "WHERE user_id = ? AND target_level = ? AND dimension = 'foundation' "
                "AND passed = 1",
                (user_id, check_level)
            ).fetchone()
            passed_count = passed["cnt"] if passed else 0

            pass_rate = passed_count / total_count if total_count > 0 else 0.0
            if pass_rate < FOUNDATION_PASS_RATE:
                return check_level

        return None
    finally:
        conn.close()


def get_foundation_exercise(db_path, user_id, check_level):
    # type: (str, str, int) -> Optional[dict]
    """Pick a foundation check exercise for the given level.
    Look for exercises with title starting with '[Foundation Check]' at that level.
    Exclude already completed by this user."""
    conn = _connect(db_path)
    try:
        # Get completed exercise_ids for this user
        completed_rows = conn.execute(
            "SELECT DISTINCT exercise_id FROM sa_exercise_results WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        completed_ids = [r["exercise_id"] for r in completed_rows]

        if completed_ids:
            placeholders = ",".join("?" for _ in completed_ids)
            exclude_clause = " AND e.exercise_id NOT IN ({})".format(placeholders)
            params = [check_level] + completed_ids
        else:
            exclude_clause = ""
            params = [check_level]

        # Look for exercises titled with [Foundation Check] at the given level
        query = (
            "SELECT e.* FROM sa_exercises e "
            "JOIN sa_modules m ON e.module_id = m.module_id "
            "WHERE m.level_number = ? AND e.exercise_title LIKE '[Foundation Check]%%'"
            "{} ORDER BY RANDOM() LIMIT 1".format(exclude_clause)
        )
        row = conn.execute(query, params).fetchone()

        if row:
            return _format_exercise(_row_to_dict(row), "foundation_check")

        # Fallback: try any standard-tier exercise at that level
        if completed_ids:
            placeholders = ",".join("?" for _ in completed_ids)
            exclude_clause = " AND e.exercise_id NOT IN ({})".format(placeholders)
            params = [check_level, "standard"] + completed_ids
        else:
            exclude_clause = ""
            params = [check_level, "standard"]

        query = (
            "SELECT e.* FROM sa_exercises e "
            "JOIN sa_modules m ON e.module_id = m.module_id "
            "WHERE m.level_number = ? AND e.tier = ? AND e.is_curveball = 0"
            "{} ORDER BY RANDOM() LIMIT 1".format(exclude_clause)
        )
        row = conn.execute(query, params).fetchone()

        if row:
            return _format_exercise(_row_to_dict(row), "foundation_check")

        return None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Exercise History
# ---------------------------------------------------------------------------

def get_exercise_history(db_path, user_id, module_code, limit=20):
    # type: (str, str, str, int) -> list
    """Get scored exercise history for user on module."""
    conn = _connect(db_path)
    try:
        module_id = _get_module_id(conn, module_code)
        if module_id is None:
            return []

        rows = conn.execute(
            "SELECT er.*, e.exercise_title, e.tier, e.context_tag as ex_context_tag, "
            "e.is_curveball, e.curveball_type, e.rubric_code "
            "FROM sa_exercise_results er "
            "JOIN sa_exercises e ON er.exercise_id = e.exercise_id "
            "WHERE er.user_id = ? AND e.module_id = ? "
            "ORDER BY er.created_at DESC LIMIT ?",
            (user_id, module_id, limit)
        ).fetchall()

        results = []
        for r in rows:
            entry = {
                "id": r["id"],
                "exercise_id": r["exercise_id"],
                "exercise_title": r["exercise_title"],
                "tier": r["tier"],
                "context_tag": r["ex_context_tag"],
                "is_curveball": bool(r["is_curveball"]),
                "curveball_type": r["curveball_type"],
                "rubric_code": r["rubric_code"],
                "scores": json.loads(r["scores_json"]) if r["scores_json"] else {},
                "total_score": r["total_score"],
                "passed": bool(r["passed"]),
                "ai_feedback": r["ai_feedback"],
                "curveball_score": r["curveball_score"],
                "created_at": r["created_at"],
            }
            results.append(entry)
        return results
    finally:
        conn.close()


def get_context_tags_earned(db_path, user_id, level):
    # type: (str, str, int) -> list
    """Get distinct context tags where user passed at stretch or elite tier at this level.
    Used for breadth tracking."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT er.context_tag "
            "FROM sa_exercise_results er "
            "JOIN sa_exercises e ON er.exercise_id = e.exercise_id "
            "JOIN sa_modules m ON e.module_id = m.module_id "
            "WHERE er.user_id = ? AND m.level_number = ? "
            "AND e.tier IN ('stretch', 'elite') AND er.passed = 1 "
            "AND er.context_tag IS NOT NULL",
            (user_id, level)
        ).fetchall()
        return [r["context_tag"] for r in rows]
    finally:
        conn.close()


def get_module_progress(db_path, user_id, module_code):
    # type: (str, str, str) -> dict
    """Return: {total_exercises, completed, passed, current_tier, avg_score,
    exercises_since_curveball, consecutive_high_scores}"""
    conn = _connect(db_path)
    try:
        module_id = _get_module_id(conn, module_code)
        if module_id is None:
            return {
                "module_code": module_code,
                "total_exercises": 0,
                "completed": 0,
                "passed": 0,
                "current_tier": "standard",
                "avg_score": 0.0,
                "exercises_since_curveball": 0,
                "consecutive_high_scores": 0,
            }

        # Total available exercises (non-curveball) for this module
        total_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_exercises "
            "WHERE module_id = ? AND is_curveball = 0",
            (module_id,)
        ).fetchone()
        total_exercises = total_row["cnt"] if total_row else 0

        # Completed (distinct exercises attempted)
        completed_row = conn.execute(
            "SELECT COUNT(DISTINCT er.exercise_id) as cnt "
            "FROM sa_exercise_results er "
            "JOIN sa_exercises e ON er.exercise_id = e.exercise_id "
            "WHERE er.user_id = ? AND e.module_id = ?",
            (user_id, module_id)
        ).fetchone()
        completed = completed_row["cnt"] if completed_row else 0

        # Passed count
        passed_row = conn.execute(
            "SELECT COUNT(DISTINCT er.exercise_id) as cnt "
            "FROM sa_exercise_results er "
            "JOIN sa_exercises e ON er.exercise_id = e.exercise_id "
            "WHERE er.user_id = ? AND e.module_id = ? AND er.passed = 1",
            (user_id, module_id)
        ).fetchone()
        passed = passed_row["cnt"] if passed_row else 0

        # Average score
        avg_row = conn.execute(
            "SELECT AVG(er.total_score) as avg_score "
            "FROM sa_exercise_results er "
            "JOIN sa_exercises e ON er.exercise_id = e.exercise_id "
            "WHERE er.user_id = ? AND e.module_id = ?",
            (user_id, module_id)
        ).fetchone()
        avg_score = round(avg_row["avg_score"], 2) if avg_row and avg_row["avg_score"] else 0.0

        # Exercise state
        state = _ensure_exercise_state(conn, user_id, module_code)

        return {
            "module_code": module_code,
            "total_exercises": total_exercises,
            "completed": completed,
            "passed": passed,
            "current_tier": state["current_tier"],
            "avg_score": avg_score,
            "exercises_since_curveball": state["exercises_since_curveball"],
            "consecutive_high_scores": state["consecutive_high_scores"],
        }
    finally:
        conn.close()


def get_all_module_progress(db_path, user_id):
    # type: (str, str) -> list
    """Return progress for all active modules."""
    conn = _connect(db_path)
    try:
        modules = conn.execute(
            "SELECT module_code FROM sa_modules WHERE is_active = 1 "
            "ORDER BY level_number, display_order"
        ).fetchall()
        module_codes = [m["module_code"] for m in modules]
    finally:
        conn.close()

    # Call get_module_progress for each (opens/closes its own conn)
    results = []
    for code in module_codes:
        progress = get_module_progress(db_path, user_id, code)
        results.append(progress)
    return results


# ---------------------------------------------------------------------------
# Skip-Ahead
# ---------------------------------------------------------------------------

def check_skip_ahead(db_path, user_id, module_code):
    # type: (str, str, str) -> bool
    """True if consecutive_high_scores >= 3 at elite tier."""
    conn = _connect(db_path)
    try:
        module_id = _get_module_id(conn, module_code)
        if module_id is None:
            return False

        state = _ensure_exercise_state(conn, user_id, module_code)
        return (
            state["current_tier"] == "elite"
            and state["consecutive_high_scores"] >= SKIP_AHEAD_COUNT
        )
    finally:
        conn.close()


def get_available_modules(db_path, user_id):
    # type: (str, str) -> list
    """Return modules available to the user (prerequisites met, level unlocked).

    A module is available if:
    1. It is active
    2. The user's placed level >= module's level_number, OR the module's level <= placed_level
    3. If it has a prerequisite module, the user has completed at least 1 exercise in it and passed
    """
    conn = _connect(db_path)
    try:
        placed_level = _get_user_placed_level(conn, user_id)
        if placed_level is None:
            # Not placed yet -- only level 1 modules with no prereqs
            placed_level = 1

        # Get all active modules
        modules = conn.execute(
            "SELECT m.*, s.series_code, s.series_name "
            "FROM sa_modules m "
            "JOIN sa_series s ON m.series_id = s.series_id "
            "WHERE m.is_active = 1 "
            "ORDER BY m.level_number, m.display_order"
        ).fetchall()

        available = []
        for m in modules:
            mod = _row_to_dict(m)

            # Check level requirement
            if mod["level_number"] > placed_level:
                continue

            # Check prerequisite
            prereq_id = mod["prerequisite_module_id"]
            if prereq_id is not None:
                # User must have at least 1 passed exercise in the prerequisite module
                prereq_passed = conn.execute(
                    "SELECT COUNT(*) as cnt FROM sa_exercise_results er "
                    "JOIN sa_exercises e ON er.exercise_id = e.exercise_id "
                    "WHERE er.user_id = ? AND e.module_id = ? AND er.passed = 1",
                    (user_id, prereq_id)
                ).fetchone()
                if not prereq_passed or prereq_passed["cnt"] == 0:
                    # Check if they've at least completed an exercise (even if not passed)
                    # to give partial access -- but for strict gate, require a pass
                    continue

            available.append({
                "module_id": mod["module_id"],
                "module_code": mod["module_code"],
                "module_name": mod["module_name"],
                "description": mod["description"],
                "difficulty": mod["difficulty"],
                "estimated_minutes": mod["estimated_minutes"],
                "level_number": mod["level_number"],
                "series_code": mod["series_code"],
                "series_name": mod["series_name"],
                "has_prerequisite": prereq_id is not None,
            })

        return available
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Record exercise result + update mastery evidence
# ---------------------------------------------------------------------------

def record_exercise_result(db_path, user_id, exercise_id, score_pct, passed,
                           exercise_type="normal", context_tag=None):
    # type: (str, str, int, float, bool, str, Optional[str]) -> dict
    """After an exercise is scored (by the rubric engine), record the result
    and update mastery evidence + adaptive tier.

    This is the orchestration function called after evaluate_exercise()
    in sa_v4_rubric_engine.py returns a result.

    Returns dict with tier update info and mastery evidence update.
    """
    conn = _connect(db_path)
    try:
        # Look up the exercise to get module_code and level
        ex = conn.execute(
            "SELECT e.*, m.module_code, m.level_number "
            "FROM sa_exercises e "
            "JOIN sa_modules m ON e.module_id = m.module_id "
            "WHERE e.exercise_id = ?",
            (exercise_id,)
        ).fetchone()
        if not ex:
            return {"error": "Exercise not found"}

        module_code = ex["module_code"]
        level = ex["level_number"]
        tier = ex["tier"]
        is_curveball = bool(ex["is_curveball"])

        # Determine mastery dimension based on exercise type
        if exercise_type == "foundation_check":
            dimension = "foundation"
            target_level = level  # Foundation check targets the level it's checking
        elif exercise_type == "curveball":
            dimension = "depth"
            target_level = level
        elif tier in ("stretch", "elite") and passed:
            dimension = "breadth"
            target_level = level
        else:
            dimension = "foundation"
            target_level = level

        # Record mastery evidence
        now = datetime.utcnow().isoformat()
        detail = {
            "exercise_type": exercise_type,
            "tier": tier,
            "score_pct": score_pct,
        }
        conn.execute(
            "INSERT INTO sa_mastery_evidence "
            "(user_id, target_level, dimension, evidence_type, context_tag, "
            "score, passed, source_exercise_id, detail_json, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                user_id, target_level, dimension,
                "exercise_{}".format(exercise_type),
                context_tag or ex["context_tag"],
                score_pct, 1 if passed else 0,
                exercise_id, json.dumps(detail), now,
            )
        )

        # Update verification status last_activity_at
        conn.execute(
            "UPDATE sa_verification_status SET last_activity_at = ? "
            "WHERE user_id = ? AND level_number = (SELECT MAX(level_number) "
            "FROM sa_verification_status WHERE user_id = ?)",
            (now, user_id, user_id)
        )
        conn.commit()
    finally:
        conn.close()

    # Update adaptive tier (uses its own connection)
    tier_result = update_adaptive_tier(db_path, user_id, module_code, score_pct)

    return {
        "mastery_dimension": dimension,
        "target_level": target_level,
        "tier_update": tier_result,
    }


# ---------------------------------------------------------------------------
# Verification status helpers
# ---------------------------------------------------------------------------

def get_verification_status(db_path, user_id):
    # type: (str, str) -> list
    """Get all verification statuses for a user across levels."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM sa_verification_status "
            "WHERE user_id = ? ORDER BY level_number",
            (user_id,)
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def update_verification_scores(db_path, user_id, level_number):
    # type: (str, str, int) -> dict
    """Recalculate verification dimension scores for a user at a level.
    Returns updated verification status dict.

    Dimensions:
    - foundation: pass rate of foundation evidence
    - breadth: count of distinct context_tags passed at stretch/elite
    - depth: count of curveball passes
    - application: whether any application-type evidence passed
    """
    conn = _connect(db_path)
    try:
        # Foundation score: pass rate of foundation dimension evidence
        foundation_total = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_mastery_evidence "
            "WHERE user_id = ? AND target_level = ? AND dimension = 'foundation'",
            (user_id, level_number)
        ).fetchone()
        foundation_passed = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_mastery_evidence "
            "WHERE user_id = ? AND target_level = ? AND dimension = 'foundation' AND passed = 1",
            (user_id, level_number)
        ).fetchone()

        f_total = foundation_total["cnt"] if foundation_total else 0
        f_passed = foundation_passed["cnt"] if foundation_passed else 0
        foundation_score = round(f_passed / f_total, 2) if f_total > 0 else 0.0

        # Breadth: distinct context tags with passed stretch/elite exercises
        breadth_row = conn.execute(
            "SELECT COUNT(DISTINCT context_tag) as cnt FROM sa_mastery_evidence "
            "WHERE user_id = ? AND target_level = ? AND dimension = 'breadth' AND passed = 1",
            (user_id, level_number)
        ).fetchone()
        breadth_count = breadth_row["cnt"] if breadth_row else 0

        # Depth: count of passed curveball/depth evidence
        depth_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_mastery_evidence "
            "WHERE user_id = ? AND target_level = ? AND dimension = 'depth' AND passed = 1",
            (user_id, level_number)
        ).fetchone()
        depth_count = depth_row["cnt"] if depth_row else 0

        # Application: any application evidence passed
        app_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_mastery_evidence "
            "WHERE user_id = ? AND target_level = ? AND dimension = 'application' AND passed = 1",
            (user_id, level_number)
        ).fetchone()
        application_passed = 1 if (app_row and app_row["cnt"] > 0) else 0

        now = datetime.utcnow().isoformat()

        # Check if all dimensions meet confirmation thresholds
        # Foundation >= 80%, breadth >= 3 tags, depth >= 2 passes, application passed
        can_confirm = (
            foundation_score >= FOUNDATION_PASS_RATE
            and breadth_count >= 3
            and depth_count >= 2
            and application_passed == 1
        )

        new_status = "confirmed" if can_confirm else "provisional"
        confirmed_at = now if can_confirm else None

        # Upsert verification status
        conn.execute(
            "INSERT INTO sa_verification_status "
            "(user_id, level_number, level_status, foundation_score, "
            "breadth_count, depth_count, application_passed, "
            "confirmed_at, last_activity_at, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(user_id, level_number) DO UPDATE SET "
            "level_status = excluded.level_status, "
            "foundation_score = excluded.foundation_score, "
            "breadth_count = excluded.breadth_count, "
            "depth_count = excluded.depth_count, "
            "application_passed = excluded.application_passed, "
            "confirmed_at = COALESCE(excluded.confirmed_at, confirmed_at), "
            "last_activity_at = excluded.last_activity_at",
            (
                user_id, level_number, new_status,
                foundation_score, breadth_count, depth_count,
                application_passed, confirmed_at, now, now,
            )
        )
        conn.commit()

        return {
            "user_id": user_id,
            "level_number": level_number,
            "level_status": new_status,
            "foundation_score": foundation_score,
            "breadth_count": breadth_count,
            "depth_count": depth_count,
            "application_passed": application_passed,
            "can_confirm": can_confirm,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Admin / Stats
# ---------------------------------------------------------------------------

def get_exercise_stats(db_path, module_code=None):
    # type: (str, Optional[str]) -> dict
    """Get aggregate exercise statistics, optionally filtered by module.
    Returns: {total_attempts, total_passed, pass_rate, avg_score,
    tier_distribution, curveball_stats}"""
    conn = _connect(db_path)
    try:
        if module_code:
            module_id = _get_module_id(conn, module_code)
            if module_id is None:
                return {"error": "Module not found"}
            where = " AND e.module_id = ?"
            params_base = [module_id]  # type: list
        else:
            where = ""
            params_base = []

        # Total attempts and passes
        row = conn.execute(
            "SELECT COUNT(*) as total, SUM(er.passed) as passed, "
            "AVG(er.total_score) as avg_score "
            "FROM sa_exercise_results er "
            "JOIN sa_exercises e ON er.exercise_id = e.exercise_id "
            "WHERE 1=1" + where,
            params_base
        ).fetchone()

        total_attempts = row["total"] if row else 0
        total_passed = int(row["passed"]) if row and row["passed"] else 0
        avg_score = round(row["avg_score"], 2) if row and row["avg_score"] else 0.0
        pass_rate = round(total_passed / total_attempts, 2) if total_attempts > 0 else 0.0

        # Tier distribution of current exercise states
        tier_rows = conn.execute(
            "SELECT current_tier, COUNT(*) as cnt "
            "FROM sa_exercise_state "
            "GROUP BY current_tier"
        ).fetchall()
        tier_distribution = {}
        for tr in tier_rows:
            tier_distribution[tr["current_tier"]] = tr["cnt"]

        # Curveball stats
        cb_row = conn.execute(
            "SELECT COUNT(*) as total, SUM(er.passed) as passed, "
            "AVG(er.curveball_score) as avg_cb "
            "FROM sa_exercise_results er "
            "WHERE er.is_curveball_result = 1",
        ).fetchone()
        curveball_total = cb_row["total"] if cb_row else 0
        curveball_passed = int(cb_row["passed"]) if cb_row and cb_row["passed"] else 0
        curveball_avg = round(cb_row["avg_cb"], 2) if cb_row and cb_row["avg_cb"] else 0.0

        return {
            "total_attempts": total_attempts,
            "total_passed": total_passed,
            "pass_rate": pass_rate,
            "avg_score": avg_score,
            "tier_distribution": tier_distribution,
            "curveball_stats": {
                "total": curveball_total,
                "passed": curveball_passed,
                "avg_score": curveball_avg,
            },
        }
    finally:
        conn.close()


def get_user_exercise_summary(db_path, user_id):
    # type: (str, str) -> dict
    """Get a comprehensive exercise summary for a user across all modules.
    Returns: {total_completed, total_passed, total_curveballs, curveballs_passed,
    modules: [{module_code, completed, passed, current_tier, avg_score}],
    context_tags_by_level, skip_ahead_modules}"""
    conn = _connect(db_path)
    try:
        # Overall counts
        overall = conn.execute(
            "SELECT COUNT(*) as total, SUM(passed) as passed "
            "FROM sa_exercise_results WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        total_completed = overall["total"] if overall else 0
        total_passed = int(overall["passed"]) if overall and overall["passed"] else 0

        # Curveball counts
        cb = conn.execute(
            "SELECT COUNT(*) as total, SUM(passed) as passed "
            "FROM sa_exercise_results WHERE user_id = ? AND is_curveball_result = 1",
            (user_id,)
        ).fetchone()
        total_curveballs = cb["total"] if cb else 0
        curveballs_passed = int(cb["passed"]) if cb and cb["passed"] else 0
    finally:
        conn.close()

    # Per-module progress
    all_progress = get_all_module_progress(db_path, user_id)

    # Context tags by level
    placed_level = None
    conn2 = _connect(db_path)
    try:
        placed_level = _get_user_placed_level(conn2, user_id)
    finally:
        conn2.close()

    context_tags_by_level = {}
    if placed_level:
        for lv in range(1, placed_level + 1):
            tags = get_context_tags_earned(db_path, user_id, lv)
            if tags:
                context_tags_by_level[lv] = tags

    # Skip-ahead eligible modules
    skip_ahead_modules = []
    for prog in all_progress:
        if check_skip_ahead(db_path, user_id, prog["module_code"]):
            skip_ahead_modules.append(prog["module_code"])

    return {
        "user_id": user_id,
        "total_completed": total_completed,
        "total_passed": total_passed,
        "total_curveballs": total_curveballs,
        "curveballs_passed": curveballs_passed,
        "modules": all_progress,
        "context_tags_by_level": context_tags_by_level,
        "skip_ahead_modules": skip_ahead_modules,
    }
