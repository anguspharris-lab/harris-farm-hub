"""
Skills Academy v4 — Woven Verification Engine
4 dimensions of mastery evidence: Foundation, Breadth, Depth, Application.
Promotion from Provisional to Confirmed. Gap detection. Dormancy handling.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# Dimension thresholds
# ---------------------------------------------------------------------------

FOUNDATION_TARGET = 0.80   # 80% of below-level checks passed
BREADTH_TARGET = 5          # 5+ distinct context tags at Stretch+
DEPTH_TARGET = 3            # 3+ curveballs passed at 3.5+
APPLICATION_TARGET = 1      # 1+ capstone completed
DORMANCY_DAYS = 30          # 30+ days without activity
CONFIRMATION_XP_BONUS = 50  # XP awarded on level confirmation

# Context tag universe
CONTEXT_TAGS = [
    "operations", "commercial", "customer", "supply_chain",
    "finance", "data", "reporting", "strategy",
]


# ---------------------------------------------------------------------------
# Dimension calculators
# ---------------------------------------------------------------------------

def calc_foundation_score(db_path: str, user_id: str, level: int) -> dict:
    """Calculate foundation dimension: % of below-level checks passed.
    For a user at Level N, checks levels 1 through N-1.
    Returns: {score: float 0-1, checks_passed: int, checks_total: int, levels_checked: dict}"""
    if level <= 1:
        # No foundation checks needed for L1
        return {"score": 1.0, "checks_passed": 0, "checks_total": 0, "levels_checked": {}}

    conn = sqlite3.connect(db_path)
    try:
        total = 0
        passed = 0
        levels_detail = {}

        for check_level in range(1, level):
            rows = conn.execute(
                "SELECT score, passed FROM sa_mastery_evidence "
                "WHERE user_id = ? AND target_level = ? AND dimension = 'foundation'",
                (user_id, check_level),
            ).fetchall()

            level_total = len(rows)
            level_passed = sum(1 for r in rows if r[1])
            total += max(level_total, 1)  # At least 1 expected per level
            passed += level_passed
            levels_detail[check_level] = {
                "total": level_total,
                "passed": level_passed,
                "complete": level_passed > 0,
            }

        score = passed / total if total > 0 else 0.0
        return {
            "score": round(score, 2),
            "checks_passed": passed,
            "checks_total": total,
            "levels_checked": levels_detail,
        }
    finally:
        conn.close()


def calc_breadth_count(db_path: str, user_id: str, level: int) -> dict:
    """Calculate breadth dimension: distinct context tags passed at Stretch+ tier.
    Returns: {count: int, tags: list, target: 5}"""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT context_tag FROM sa_mastery_evidence "
            "WHERE user_id = ? AND target_level = ? AND dimension = 'breadth' AND passed = 1",
            (user_id, level),
        ).fetchall()
        tags = [r[0] for r in rows if r[0]]
        return {
            "count": len(tags),
            "tags": tags,
            "missing": [t for t in CONTEXT_TAGS if t not in tags],
            "target": BREADTH_TARGET,
        }
    finally:
        conn.close()


def calc_depth_count(db_path: str, user_id: str, level: int) -> dict:
    """Calculate depth dimension: curveballs passed at 3.5+.
    Returns: {count: int, curveball_scores: list, target: 3}"""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT score, detail_json FROM sa_mastery_evidence "
            "WHERE user_id = ? AND target_level = ? AND dimension = 'depth' AND passed = 1",
            (user_id, level),
        ).fetchall()
        scores = [r[0] for r in rows if r[0] is not None]
        return {
            "count": len(scores),
            "curveball_scores": scores,
            "target": DEPTH_TARGET,
        }
    finally:
        conn.close()


def calc_application_status(db_path: str, user_id: str, level: int) -> dict:
    """Calculate application dimension: capstone/live problem completed.
    Returns: {passed: bool, count: int, target: 1}"""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT score, passed FROM sa_mastery_evidence "
            "WHERE user_id = ? AND target_level = ? AND dimension = 'application' AND passed = 1",
            (user_id, level),
        ).fetchall()
        return {
            "passed": len(rows) >= APPLICATION_TARGET,
            "count": len(rows),
            "target": APPLICATION_TARGET,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Evidence recording
# ---------------------------------------------------------------------------

def record_foundation_evidence(db_path: str, user_id: str, check_level: int,
                               score: float, passed: bool,
                               exercise_id: Optional[int] = None,
                               detail: Optional[dict] = None) -> int:
    """Record a foundation check result."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO sa_mastery_evidence "
            "(user_id, target_level, dimension, evidence_type, score, passed, "
            "source_exercise_id, detail_json, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                user_id, check_level, "foundation",
                "foundation_check_L{}".format(check_level),
                score, 1 if passed else 0,
                exercise_id,
                json.dumps(detail) if detail else None,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def record_breadth_evidence(db_path: str, user_id: str, level: int,
                            context_tag: str, score: float, passed: bool,
                            exercise_id: Optional[int] = None) -> int:
    """Record a breadth evidence point (exercise passed at Stretch+ with context tag)."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO sa_mastery_evidence "
            "(user_id, target_level, dimension, evidence_type, context_tag, "
            "score, passed, source_exercise_id, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                user_id, level, "breadth", "stretch_pass",
                context_tag, score, 1 if passed else 0,
                exercise_id, datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def record_depth_evidence(db_path: str, user_id: str, level: int,
                          curveball_score: float, passed: bool,
                          exercise_id: Optional[int] = None,
                          curveball_type: Optional[str] = None) -> int:
    """Record a curveball result as depth evidence."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO sa_mastery_evidence "
            "(user_id, target_level, dimension, evidence_type, score, passed, "
            "source_exercise_id, detail_json, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                user_id, level, "depth", "curveball_pass",
                curveball_score, 1 if passed else 0,
                exercise_id,
                json.dumps({"curveball_type": curveball_type}) if curveball_type else None,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def record_application_evidence(db_path: str, user_id: str, level: int,
                                score: float, passed: bool,
                                exercise_id: Optional[int] = None,
                                problem_id: Optional[int] = None) -> int:
    """Record a capstone/live problem completion as application evidence."""
    conn = sqlite3.connect(db_path)
    try:
        detail = {}
        if problem_id:
            detail["problem_id"] = problem_id
        cur = conn.execute(
            "INSERT INTO sa_mastery_evidence "
            "(user_id, target_level, dimension, evidence_type, score, passed, "
            "source_exercise_id, detail_json, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                user_id, level, "application", "capstone_pass",
                score, 1 if passed else 0,
                exercise_id,
                json.dumps(detail) if detail else None,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# After-exercise hook: update evidence + check promotion
# ---------------------------------------------------------------------------

def process_exercise_result(db_path: str, user_id: str, exercise_result: dict) -> dict:
    """Called after every exercise is scored. Updates mastery evidence and checks promotion.

    exercise_result should contain:
    - exercise_id, is_curveball, curveball_score, curveball_type
    - passed, total_score, context_tag, tier
    - module_code, level

    Returns: {evidence_recorded: list, promotion: Optional[dict], gap_info: Optional[dict]}
    """
    evidence_recorded = []
    level = exercise_result.get("level", 1)
    is_curveball = exercise_result.get("is_curveball", False)
    passed = exercise_result.get("passed", False)
    exercise_id = exercise_result.get("exercise_id")
    context_tag = exercise_result.get("context_tag", "")
    tier = exercise_result.get("tier", "standard")

    # Record depth evidence if curveball
    if is_curveball:
        curveball_score = exercise_result.get("curveball_score", 0)
        curveball_passed = curveball_score >= 3.5
        record_depth_evidence(
            db_path, user_id, level,
            curveball_score, curveball_passed,
            exercise_id,
            exercise_result.get("curveball_type"),
        )
        evidence_recorded.append("depth")

    # Record breadth evidence if passed at stretch or elite
    elif passed and tier in ("stretch", "elite") and context_tag:
        record_breadth_evidence(
            db_path, user_id, level,
            context_tag, exercise_result.get("total_score", 0),
            True, exercise_id,
        )
        evidence_recorded.append("breadth")

    # Check if this was a foundation check
    if exercise_result.get("is_foundation_check"):
        check_level = exercise_result.get("check_level", level)
        record_foundation_evidence(
            db_path, user_id, check_level,
            exercise_result.get("total_score", 0), passed,
            exercise_id,
        )
        evidence_recorded.append("foundation")

    # Update last_activity_at
    _update_last_activity(db_path, user_id, level)

    # Check promotion
    promotion = check_and_promote(db_path, user_id, level)

    return {
        "evidence_recorded": evidence_recorded,
        "promotion": promotion,
    }


def _update_last_activity(db_path: str, user_id: str, level: int) -> None:
    """Update last_activity_at in verification status."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE sa_verification_status SET last_activity_at = ? "
            "WHERE user_id = ? AND level_number = ?",
            (datetime.utcnow().isoformat(), user_id, level),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Promotion check
# ---------------------------------------------------------------------------

def check_all_dimensions(db_path: str, user_id: str, level: int) -> dict:
    """Calculate all 4 dimension scores for a user at a level.
    Returns: {foundation, breadth, depth, application, all_met: bool}"""
    foundation = calc_foundation_score(db_path, user_id, level)
    breadth = calc_breadth_count(db_path, user_id, level)
    depth = calc_depth_count(db_path, user_id, level)
    application = calc_application_status(db_path, user_id, level)

    all_met = (
        foundation["score"] >= FOUNDATION_TARGET
        and breadth["count"] >= BREADTH_TARGET
        and depth["count"] >= DEPTH_TARGET
        and application["passed"]
    )

    return {
        "foundation": foundation,
        "breadth": breadth,
        "depth": depth,
        "application": application,
        "all_met": all_met,
    }


def check_and_promote(db_path: str, user_id: str, level: int) -> Optional[dict]:
    """Check if all 4 dimensions meet threshold. If so, promote Provisional -> Confirmed.
    Returns promotion event dict or None."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Get current status
        row = conn.execute(
            "SELECT * FROM sa_verification_status "
            "WHERE user_id = ? AND level_number = ?",
            (user_id, level),
        ).fetchone()

        if not row:
            return None

        # Already confirmed — nothing to do
        if row["level_status"] == "confirmed":
            return None

        # Check all dimensions
        dims = check_all_dimensions(db_path, user_id, level)

        if not dims["all_met"]:
            # Update dimension scores in verification_status for ring display
            conn.execute(
                "UPDATE sa_verification_status "
                "SET foundation_score = ?, breadth_count = ?, depth_count = ?, "
                "application_passed = ? WHERE user_id = ? AND level_number = ?",
                (
                    dims["foundation"]["score"],
                    dims["breadth"]["count"],
                    dims["depth"]["count"],
                    1 if dims["application"]["passed"] else 0,
                    user_id, level,
                ),
            )
            conn.commit()
            return None

        # All dimensions met — PROMOTE!
        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE sa_verification_status "
            "SET level_status = 'confirmed', confirmed_at = ?, "
            "foundation_score = ?, breadth_count = ?, depth_count = ?, "
            "application_passed = 1 "
            "WHERE user_id = ? AND level_number = ?",
            (
                now,
                dims["foundation"]["score"],
                dims["breadth"]["count"],
                dims["depth"]["count"],
                user_id, level,
            ),
        )
        conn.commit()

        return {
            "user_id": user_id,
            "level": level,
            "status": "confirmed",
            "confirmed_at": now,
            "xp_bonus": CONFIRMATION_XP_BONUS,
            "dimensions": dims,
            "message": "Level {} Confirmed! You've proven it across {} scenarios.".format(
                level, dims["breadth"]["count"] + dims["depth"]["count"]
            ),
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Verification status + ring data
# ---------------------------------------------------------------------------

def get_verification_status(db_path: str, user_id: str,
                            level: Optional[int] = None) -> dict:
    """Get verification status for a user. If level specified, return single level.
    Otherwise return all levels."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if level is not None:
            row = conn.execute(
                "SELECT * FROM sa_verification_status "
                "WHERE user_id = ? AND level_number = ?",
                (user_id, level),
            ).fetchone()
            if not row:
                return {"level": level, "status": "none"}
            return _row_to_status(row)
        else:
            rows = conn.execute(
                "SELECT * FROM sa_verification_status "
                "WHERE user_id = ? ORDER BY level_number",
                (user_id,),
            ).fetchall()
            return {
                "user_id": user_id,
                "levels": [_row_to_status(r) for r in rows],
            }
    finally:
        conn.close()


def _row_to_status(row) -> dict:
    return {
        "level": row["level_number"],
        "status": row["level_status"],
        "foundation_score": row["foundation_score"],
        "breadth_count": row["breadth_count"],
        "depth_count": row["depth_count"],
        "application_passed": bool(row["application_passed"]),
        "confirmed_at": row["confirmed_at"],
        "last_activity_at": row["last_activity_at"],
    }


def get_ring_data(db_path: str, user_id: str, level: int) -> dict:
    """Get verification ring data for the frontend.
    Returns 4 rings with current value, target, percentage, and met flag."""
    dims = check_all_dimensions(db_path, user_id, level)

    foundation_pct = min(100, int(dims["foundation"]["score"] / FOUNDATION_TARGET * 100))
    breadth_pct = min(100, int(dims["breadth"]["count"] / BREADTH_TARGET * 100))
    depth_pct = min(100, int(dims["depth"]["count"] / DEPTH_TARGET * 100))
    app_pct = 100 if dims["application"]["passed"] else 0

    return {
        "level": level,
        "all_met": dims["all_met"],
        "rings": {
            "foundation": {
                "label": "Foundation",
                "icon": "\U0001f3db",
                "color": "#3b82f6",
                "current": dims["foundation"]["score"],
                "target": FOUNDATION_TARGET,
                "percentage": foundation_pct,
                "met": dims["foundation"]["score"] >= FOUNDATION_TARGET,
                "detail": dims["foundation"],
            },
            "breadth": {
                "label": "Breadth",
                "icon": "\U0001f310",
                "color": "#8b5cf6",
                "current": dims["breadth"]["count"],
                "target": BREADTH_TARGET,
                "percentage": breadth_pct,
                "met": dims["breadth"]["count"] >= BREADTH_TARGET,
                "detail": dims["breadth"],
            },
            "depth": {
                "label": "Depth",
                "icon": "\U0001f3af",
                "color": "#f59e0b",
                "current": dims["depth"]["count"],
                "target": DEPTH_TARGET,
                "percentage": depth_pct,
                "met": dims["depth"]["count"] >= DEPTH_TARGET,
                "detail": dims["depth"],
            },
            "application": {
                "label": "Application",
                "icon": "\u26a1",
                "color": "#22c55e",
                "current": 1 if dims["application"]["passed"] else 0,
                "target": APPLICATION_TARGET,
                "percentage": app_pct,
                "met": dims["application"]["passed"],
                "detail": dims["application"],
            },
        },
    }


# ---------------------------------------------------------------------------
# Gap detection & remediation
# ---------------------------------------------------------------------------

def detect_gaps(db_path: str, user_id: str, level: int) -> list:
    """Detect which verification dimensions have gaps.
    Returns list of gap dicts with suggestions."""
    dims = check_all_dimensions(db_path, user_id, level)
    gaps = []

    if dims["foundation"]["score"] < FOUNDATION_TARGET:
        gaps.append({
            "dimension": "foundation",
            "current": dims["foundation"]["score"],
            "target": FOUNDATION_TARGET,
            "label": "Stretch Challenge: Foundation",
            "message": "Your advanced skills are strong, but we noticed a gap in the basics. "
                       "Here's a quick refresher.",
            "suggestion": "Complete {} more foundation warm-up exercises.".format(
                max(1, 2 - dims["foundation"]["checks_passed"])
            ),
        })

    if dims["breadth"]["count"] < BREADTH_TARGET:
        missing = dims["breadth"].get("missing", [])
        gaps.append({
            "dimension": "breadth",
            "current": dims["breadth"]["count"],
            "target": BREADTH_TARGET,
            "label": "Stretch Challenge: Breadth",
            "message": "You've nailed {} contexts -- try these exercises in areas "
                       "you haven't explored yet.".format(dims["breadth"]["count"]),
            "suggestion": "Try exercises tagged: {}".format(
                ", ".join(missing[:3]) if missing else "any new context"
            ),
            "missing_tags": missing,
        })

    if dims["depth"]["count"] < DEPTH_TARGET:
        gaps.append({
            "dimension": "depth",
            "current": dims["depth"]["count"],
            "target": DEPTH_TARGET,
            "label": "Stretch Challenge: Depth",
            "message": "The tricky scenarios caught you out. Here's what to watch for.",
            "suggestion": "Complete {} more curveball exercises.".format(
                DEPTH_TARGET - dims["depth"]["count"]
            ),
        })

    if not dims["application"]["passed"]:
        gaps.append({
            "dimension": "application",
            "current": 0,
            "target": APPLICATION_TARGET,
            "label": "Stretch Challenge: Application",
            "message": "Complete a capstone problem to demonstrate your skills on a real "
                       "Harris Farm challenge.",
            "suggestion": "Head to the Live Problems tab and solve one at your level.",
        })

    return gaps


# ---------------------------------------------------------------------------
# Dormancy detection
# ---------------------------------------------------------------------------

def check_dormancy(db_path: str, user_id: str) -> Optional[dict]:
    """Check if user has been inactive for 30+ days.
    Returns welcome-back data if dormant, None otherwise."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM sa_verification_status "
            "WHERE user_id = ? ORDER BY level_number DESC LIMIT 1",
            (user_id,),
        ).fetchall()

        if not rows:
            return None

        row = rows[0]
        last_activity = row["last_activity_at"]
        if not last_activity:
            return None

        try:
            last_dt = datetime.fromisoformat(last_activity)
        except (ValueError, TypeError):
            return None

        days_inactive = (datetime.utcnow() - last_dt).days

        if days_inactive < DORMANCY_DAYS:
            return None

        # Mark as dormant
        conn.execute(
            "UPDATE sa_verification_status SET level_status = 'dormant' "
            "WHERE user_id = ? AND level_number = ? AND level_status != 'confirmed'",
            (user_id, row["level_number"]),
        )
        conn.commit()

        return {
            "user_id": user_id,
            "days_inactive": days_inactive,
            "level": row["level_number"],
            "status": row["level_status"],
            "message": "Welcome back! It's been {} days. Let's warm up.".format(days_inactive),
            "action": "warmup_challenge",
        }
    finally:
        conn.close()


def handle_return(db_path: str, user_id: str, warmup_passed: bool) -> dict:
    """Handle a returning user's warmup result.
    If passed: restore status, carry on.
    If struggled: offer refresher exercises (not re-verification)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM sa_verification_status "
            "WHERE user_id = ? AND level_status = 'dormant' "
            "ORDER BY level_number DESC LIMIT 1",
            (user_id,),
        ).fetchone()

        if not row:
            return {"status": "no_dormant_status"}

        level = row["level_number"]

        if warmup_passed:
            # Restore to provisional (they keep their level)
            conn.execute(
                "UPDATE sa_verification_status SET level_status = 'provisional', "
                "last_activity_at = ? WHERE user_id = ? AND level_number = ?",
                (datetime.utcnow().isoformat(), user_id, level),
            )
            conn.commit()
            return {
                "status": "restored",
                "level": level,
                "message": "Welcome back! You're right where you left off.",
            }
        else:
            # Offer refresher exercises
            conn.execute(
                "UPDATE sa_verification_status SET level_status = 'provisional', "
                "last_activity_at = ? WHERE user_id = ? AND level_number = ?",
                (datetime.utcnow().isoformat(), user_id, level),
            )
            conn.commit()
            return {
                "status": "refresher_offered",
                "level": level,
                "message": "No worries! Here are some quick exercises to get back up to speed.",
                "suggested_exercises": "foundation_checks",
            }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Evidence log
# ---------------------------------------------------------------------------

def get_evidence_log(db_path: str, user_id: str, level: Optional[int] = None,
                     limit: int = 50) -> list:
    """Get detailed evidence log for a user."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if level:
            rows = conn.execute(
                "SELECT * FROM sa_mastery_evidence "
                "WHERE user_id = ? AND target_level = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (user_id, level, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sa_mastery_evidence "
                "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()

        return [
            {
                "id": r["id"],
                "dimension": r["dimension"],
                "evidence_type": r["evidence_type"],
                "context_tag": r["context_tag"],
                "score": r["score"],
                "passed": bool(r["passed"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()
