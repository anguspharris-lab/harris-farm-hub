"""
Skills Academy v4 — XP, Badge & Leaderboard Engine
====================================================
Manages a separate XP/gamification system for Skills Academy v4,
independent from the existing academy_engine.py (Paddock/sidebar).

Tables (created in sa_v4_schema.py):
    sa_user_xp, sa_xp_log, sa_badges_v4, sa_user_badges_v4, sa_levels

Python 3.9 compatible.
"""

import sqlite3
import math
from datetime import datetime, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# XP award amounts by source type
# ---------------------------------------------------------------------------
XP_AWARDS = {
    "theory_lesson": 10,
    "exercise_standard": 15,
    "exercise_stretch": 20,
    "exercise_elite": 25,
    "assessment_pass": 25,
    "assessment_high": 50,
    "mindset_assessment": 50,
    "library_contribution": 25,
    "mentor_levelup": 50,
    "citizen_dev_tool": 200,
    "output_8plus": 20,
    "l6_challenge": 500,
    "level_confirmation": 50,
    "placement_complete": 25,
    "daily_challenge": 20,
    "peer_battle_submit": 10,
    "peer_battle_win": 30,
    "curveball_pass": 20,
    "foundation_check_pass": 10,
    "skip_ahead_pass": 50,
}

# ---------------------------------------------------------------------------
# Level thresholds (quick lookup — canonical source is sa_levels table)
# ---------------------------------------------------------------------------
LEVEL_THRESHOLDS = [
    {"level": 1, "name": "Seed",        "min_xp": 0,    "max_xp": 50,    "color": "#8BC34A"},
    {"level": 2, "name": "Sprout",      "min_xp": 50,   "max_xp": 150,   "color": "#4CAF50"},
    {"level": 3, "name": "Growing",     "min_xp": 150,  "max_xp": 400,   "color": "#388E3C"},
    {"level": 4, "name": "Harvest",     "min_xp": 400,  "max_xp": 800,   "color": "#2E7D32"},
    {"level": 5, "name": "Canopy",      "min_xp": 800,  "max_xp": 1500,  "color": "#1B5E20"},
    {"level": 6, "name": "Root System", "min_xp": 1500, "max_xp": 99999, "color": "#004D40"},
]

# ---------------------------------------------------------------------------
# Streak multiplier tiers
# ---------------------------------------------------------------------------
STREAK_MULTIPLIERS = [
    (7, 2.0),   # 7+ day streak -> 2.0x
    (3, 1.5),   # 3+ day streak -> 1.5x
    (0, 1.0),   # default       -> 1.0x
]


def _get_conn(db_path: str) -> sqlite3.Connection:
    """Open a connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _today_str() -> str:
    """Current UTC date as YYYY-MM-DD."""
    return datetime.utcnow().strftime("%Y-%m-%d")


def _now_iso() -> str:
    """Current UTC timestamp as ISO-8601."""
    return datetime.utcnow().isoformat()


def _streak_multiplier(streak_days: int) -> float:
    """Calculate streak multiplier from day count."""
    for threshold, mult in STREAK_MULTIPLIERS:
        if streak_days >= threshold:
            return mult
    return 1.0


# ===================================================================
#  LEVEL OPERATIONS
# ===================================================================

def get_level_for_xp(total_xp: int) -> dict:
    """Map an XP total to level info.

    Returns:
        {level, name, color, min_xp, max_xp, progress_pct, xp_to_next}
    """
    total_xp = max(0, int(total_xp))
    matched = LEVEL_THRESHOLDS[0]
    for lvl in LEVEL_THRESHOLDS:
        if total_xp >= lvl["min_xp"]:
            matched = lvl

    span = matched["max_xp"] - matched["min_xp"]
    progress_in_level = total_xp - matched["min_xp"]
    if span > 0:
        progress_pct = min(round(progress_in_level / span * 100, 1), 100.0)
    else:
        progress_pct = 100.0
    xp_to_next = max(0, matched["max_xp"] - total_xp)

    return {
        "level": matched["level"],
        "name": matched["name"],
        "color": matched["color"],
        "min_xp": matched["min_xp"],
        "max_xp": matched["max_xp"],
        "progress_pct": progress_pct,
        "xp_to_next": xp_to_next,
    }


def check_level_change(db_path: str, user_id: str) -> Optional[dict]:
    """Check if user's XP has crossed a level threshold.

    If so, updates sa_user_xp.current_level and returns change info.
    Returns None if no change.
    """
    conn = _get_conn(db_path)
    try:
        row = conn.execute(
            "SELECT total_xp, current_level FROM sa_user_xp WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None

        total_xp = row["total_xp"]
        old_level = row["current_level"]
        new_info = get_level_for_xp(total_xp)
        new_level = new_info["level"]

        if new_level != old_level:
            conn.execute(
                "UPDATE sa_user_xp SET current_level = ?, updated_at = ? WHERE user_id = ?",
                (new_level, _now_iso(), user_id),
            )
            conn.commit()
            return {
                "user_id": user_id,
                "old_level": old_level,
                "new_level": new_level,
                "new_level_name": new_info["name"],
                "new_level_color": new_info["color"],
                "total_xp": total_xp,
            }
        return None
    finally:
        conn.close()


# ===================================================================
#  STREAK OPERATIONS
# ===================================================================

def update_streak(db_path: str, user_id: str) -> dict:
    """Call on any activity. Updates streak_days and multiplier.

    - If last_active_date is today: no change.
    - If yesterday: increment streak.
    - If older or NULL: reset to 1.

    Returns:
        {streak_days, multiplier, is_new_day}
    """
    conn = _get_conn(db_path)
    try:
        today = _today_str()
        row = conn.execute(
            "SELECT streak_days, streak_multiplier, last_active_date "
            "FROM sa_user_xp WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if not row:
            # Create the user record first, then return defaults
            _ensure_user(conn, user_id)
            conn.commit()
            return {"streak_days": 1, "multiplier": 1.0, "is_new_day": True}

        last_active = row["last_active_date"]
        old_streak = row["streak_days"] or 0

        if last_active == today:
            # Already active today — no change
            return {
                "streak_days": old_streak,
                "multiplier": row["streak_multiplier"] or 1.0,
                "is_new_day": False,
            }

        # Determine new streak
        if last_active:
            try:
                last_dt = datetime.strptime(last_active, "%Y-%m-%d").date()
                today_dt = datetime.strptime(today, "%Y-%m-%d").date()
                delta = (today_dt - last_dt).days
            except ValueError:
                delta = 999
        else:
            delta = 999

        if delta == 1:
            new_streak = old_streak + 1
        else:
            new_streak = 1

        new_mult = _streak_multiplier(new_streak)

        conn.execute(
            "UPDATE sa_user_xp SET streak_days = ?, streak_multiplier = ?, "
            "last_active_date = ?, updated_at = ? WHERE user_id = ?",
            (new_streak, new_mult, today, _now_iso(), user_id),
        )
        conn.commit()

        return {"streak_days": new_streak, "multiplier": new_mult, "is_new_day": True}
    finally:
        conn.close()


# ===================================================================
#  XP OPERATIONS
# ===================================================================

def _ensure_user(conn: sqlite3.Connection, user_id: str) -> None:
    """Create sa_user_xp row for a user if it doesn't exist."""
    exists = conn.execute(
        "SELECT 1 FROM sa_user_xp WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not exists:
        now = _now_iso()
        today = _today_str()
        conn.execute(
            "INSERT INTO sa_user_xp "
            "(user_id, total_xp, current_level, weekly_xp, monthly_xp, "
            " streak_days, streak_multiplier, last_active_date, updated_at) "
            "VALUES (?, 0, 1, 0, 0, 1, 1.0, ?, ?)",
            (user_id, today, now),
        )


def get_xp(db_path: str, user_id: str) -> dict:
    """Get user's XP summary. Creates record if not exists.

    Returns:
        {user_id, total_xp, current_level, level_name, level_color,
         weekly_xp, monthly_xp, streak_days, streak_multiplier,
         xp_to_next_level, progress_pct, last_active_date}
    """
    conn = _get_conn(db_path)
    try:
        _ensure_user(conn, user_id)
        conn.commit()

        row = conn.execute(
            "SELECT * FROM sa_user_xp WHERE user_id = ?", (user_id,)
        ).fetchone()

        total_xp = row["total_xp"] or 0
        level_info = get_level_for_xp(total_xp)

        return {
            "user_id": user_id,
            "total_xp": total_xp,
            "current_level": level_info["level"],
            "level_name": level_info["name"],
            "level_color": level_info["color"],
            "weekly_xp": row["weekly_xp"] or 0,
            "monthly_xp": row["monthly_xp"] or 0,
            "streak_days": row["streak_days"] or 0,
            "streak_multiplier": row["streak_multiplier"] or 1.0,
            "xp_to_next_level": level_info["xp_to_next"],
            "progress_pct": level_info["progress_pct"],
            "last_active_date": row["last_active_date"],
        }
    finally:
        conn.close()


def award_xp(
    db_path: str,
    user_id: str,
    source_type: str,
    amount: Optional[int] = None,
    source_id: str = "",
    description: str = "",
) -> dict:
    """Award XP to user.

    Steps:
        1. Update streak
        2. Calculate multiplied amount
        3. Insert sa_xp_log
        4. Update sa_user_xp totals
        5. Check level change
        6. Check badge triggers

    If amount not specified, uses XP_AWARDS lookup for source_type.

    Returns:
        {xp_awarded, multiplier, new_total, level_changed, new_level,
         new_badges}
    """
    # Step 1: Update streak (separate connection)
    streak_info = update_streak(db_path, user_id)

    # Resolve base XP
    if amount is not None:
        base_xp = int(amount)
    else:
        base_xp = XP_AWARDS.get(source_type, 0)
        if base_xp == 0:
            return {
                "xp_awarded": 0,
                "multiplier": 1.0,
                "new_total": 0,
                "level_changed": False,
                "new_level": None,
                "new_badges": [],
            }

    # Step 2: Apply streak multiplier
    multiplier = streak_info["multiplier"]
    awarded = int(math.floor(base_xp * multiplier))

    conn = _get_conn(db_path)
    try:
        _ensure_user(conn, user_id)

        # Step 3: Insert XP log
        conn.execute(
            "INSERT INTO sa_xp_log (user_id, xp_amount, source_type, source_id, "
            "description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, awarded, source_type, source_id, description, _now_iso()),
        )

        # Step 4: Update totals
        conn.execute(
            "UPDATE sa_user_xp SET "
            "total_xp = total_xp + ?, "
            "weekly_xp = weekly_xp + ?, "
            "monthly_xp = monthly_xp + ?, "
            "updated_at = ? "
            "WHERE user_id = ?",
            (awarded, awarded, awarded, _now_iso(), user_id),
        )
        conn.commit()

        # Read new total
        row = conn.execute(
            "SELECT total_xp FROM sa_user_xp WHERE user_id = ?", (user_id,)
        ).fetchone()
        new_total = row["total_xp"] if row else awarded

    finally:
        conn.close()

    # Step 5: Check level change
    level_change = check_level_change(db_path, user_id)
    level_changed = level_change is not None
    new_level = level_change if level_changed else None

    # Step 6: Check badge triggers
    new_badges = check_triggers(db_path, user_id)

    return {
        "xp_awarded": awarded,
        "multiplier": multiplier,
        "new_total": new_total,
        "level_changed": level_changed,
        "new_level": new_level,
        "new_badges": new_badges,
    }


def get_xp_history(db_path: str, user_id: str, limit: int = 50) -> list:
    """Get recent XP log entries for a user.

    Returns list of dicts with:
        {log_id, xp_amount, source_type, source_id, description, created_at}
    """
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT log_id, xp_amount, source_type, source_id, description, created_at "
            "FROM sa_xp_log WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [
            {
                "log_id": r["log_id"],
                "xp_amount": r["xp_amount"],
                "source_type": r["source_type"],
                "source_id": r["source_id"],
                "description": r["description"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()


# ===================================================================
#  BADGE OPERATIONS
# ===================================================================

def get_badges(db_path: str, user_id: str) -> dict:
    """Get all badges for a user.

    Returns:
        {earned: [{badge_code, badge_name, icon, color, status, earned_at}],
         locked: [{badge_code, badge_name, icon, color, description}],
         total_earned, total_available}
    """
    conn = _get_conn(db_path)
    try:
        # All available badges
        all_badges = conn.execute(
            "SELECT badge_id, badge_code, badge_name, description, icon, color_hex "
            "FROM sa_badges_v4 ORDER BY badge_id"
        ).fetchall()

        # User's earned badges
        earned_rows = conn.execute(
            "SELECT ub.badge_id, ub.status, ub.earned_at, ub.confirmed_at, "
            "b.badge_code, b.badge_name, b.icon, b.color_hex "
            "FROM sa_user_badges_v4 ub "
            "JOIN sa_badges_v4 b ON ub.badge_id = b.badge_id "
            "WHERE ub.user_id = ? "
            "ORDER BY ub.earned_at DESC",
            (user_id,),
        ).fetchall()

        earned_ids = set()
        earned = []
        for r in earned_rows:
            earned_ids.add(r["badge_id"])
            earned.append({
                "badge_code": r["badge_code"],
                "badge_name": r["badge_name"],
                "icon": r["icon"],
                "color": r["color_hex"],
                "status": r["status"],
                "earned_at": r["earned_at"],
            })

        locked = []
        for b in all_badges:
            if b["badge_id"] not in earned_ids:
                locked.append({
                    "badge_code": b["badge_code"],
                    "badge_name": b["badge_name"],
                    "icon": b["icon"],
                    "color": b["color_hex"],
                    "description": b["description"],
                })

        return {
            "earned": earned,
            "locked": locked,
            "total_earned": len(earned),
            "total_available": len(all_badges),
        }
    finally:
        conn.close()


def check_triggers(db_path: str, user_id: str) -> list:
    """Check all badge trigger conditions and award newly earned badges.

    Trigger types:
        - level_confirmed: check sa_verification_status for confirmed levels
        - special: check various conditions

    Returns list of newly earned badge codes.
    """
    conn = _get_conn(db_path)
    newly_earned = []
    try:
        # Get all badges not yet earned by this user
        badges = conn.execute(
            "SELECT b.badge_id, b.badge_code, b.trigger_type, b.trigger_value "
            "FROM sa_badges_v4 b "
            "WHERE b.badge_id NOT IN ("
            "  SELECT badge_id FROM sa_user_badges_v4 WHERE user_id = ?"
            ")",
            (user_id,),
        ).fetchall()

        for badge in badges:
            trigger_type = badge["trigger_type"]
            trigger_value = badge["trigger_value"] or ""
            earned = False

            if trigger_type == "level_confirmed":
                earned = _check_level_confirmed_trigger(
                    db_path, user_id, trigger_value, conn
                )
            elif trigger_type == "special":
                # Parse trigger_value as simple key or JSON-like value
                earned = _check_special_trigger(
                    db_path, user_id, trigger_value, conn
                )

            if earned:
                conn.execute(
                    "INSERT INTO sa_user_badges_v4 (user_id, badge_id, status, earned_at) "
                    "VALUES (?, ?, 'provisional', ?)",
                    (user_id, badge["badge_id"], _now_iso()),
                )
                newly_earned.append(badge["badge_code"])

        if newly_earned:
            conn.commit()

        return newly_earned
    finally:
        conn.close()


def _check_level_confirmed_trigger(
    db_path: str, user_id: str, trigger_value: str, conn: sqlite3.Connection
) -> bool:
    """Check if user has a confirmed level at or above trigger_value.

    trigger_value is expected to be a level number string, e.g. '3'.
    """
    try:
        required_level = int(trigger_value)
    except (ValueError, TypeError):
        return False

    # Check sa_verification_status for confirmed levels
    try:
        row = conn.execute(
            "SELECT MAX(level_number) as max_confirmed "
            "FROM sa_verification_status "
            "WHERE user_id = ? AND status = 'confirmed'",
            (user_id,),
        ).fetchone()
        if row and row["max_confirmed"] is not None:
            return row["max_confirmed"] >= required_level
    except sqlite3.OperationalError:
        # Table may not exist yet
        pass

    return False


def _check_special_trigger(
    db_path: str,
    user_id: str,
    trigger_value: str,
    conn: sqlite3.Connection,
) -> bool:
    """Check a specific special trigger condition.

    Supported trigger_value actions:
        first_eval       - user has at least 1 assessment in xp log
        first_8plus      - user has earned output_8plus or assessment_high XP
        first_mentee     - user has earned mentor_levelup XP
        mindset_18       - user has 18+ mindset_assessment XP awards
        l6_challenge     - user has earned l6_challenge XP
        speed_l3         - reached level 3 with <= 50 XP log entries
        hipo_early       - reached level 4 with <= 80 XP log entries
        streak_7         - user has streak_days >= 7
        curveball_streak - user has >= 5 curveball_pass XP awards
    """
    trigger_value = (trigger_value or "").strip().lower()

    if trigger_value == "first_eval":
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_xp_log "
            "WHERE user_id = ? AND source_type IN ('assessment_pass', 'assessment_high')",
            (user_id,),
        ).fetchone()
        return (row["cnt"] or 0) >= 1

    elif trigger_value == "first_8plus":
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_xp_log "
            "WHERE user_id = ? AND source_type IN ('output_8plus', 'assessment_high')",
            (user_id,),
        ).fetchone()
        return (row["cnt"] or 0) >= 1

    elif trigger_value == "first_mentee":
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_xp_log "
            "WHERE user_id = ? AND source_type = 'mentor_levelup'",
            (user_id,),
        ).fetchone()
        return (row["cnt"] or 0) >= 1

    elif trigger_value == "mindset_18":
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_xp_log "
            "WHERE user_id = ? AND source_type = 'mindset_assessment'",
            (user_id,),
        ).fetchone()
        return (row["cnt"] or 0) >= 18

    elif trigger_value == "l6_challenge":
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_xp_log "
            "WHERE user_id = ? AND source_type = 'l6_challenge'",
            (user_id,),
        ).fetchone()
        return (row["cnt"] or 0) >= 1

    elif trigger_value == "speed_l3":
        # Reached level 3+ with 50 or fewer total XP log entries
        user_row = conn.execute(
            "SELECT current_level FROM sa_user_xp WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not user_row or (user_row["current_level"] or 1) < 3:
            return False
        count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_xp_log WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return (count_row["cnt"] or 0) <= 50

    elif trigger_value == "hipo_early":
        # Reached level 4+ with 80 or fewer total XP log entries
        user_row = conn.execute(
            "SELECT current_level FROM sa_user_xp WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not user_row or (user_row["current_level"] or 1) < 4:
            return False
        count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_xp_log WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return (count_row["cnt"] or 0) <= 80

    elif trigger_value == "streak_7":
        user_row = conn.execute(
            "SELECT streak_days FROM sa_user_xp WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return user_row is not None and (user_row["streak_days"] or 0) >= 7

    elif trigger_value == "curveball_streak":
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_xp_log "
            "WHERE user_id = ? AND source_type = 'curveball_pass'",
            (user_id,),
        ).fetchone()
        return (row["cnt"] or 0) >= 5

    # Unknown trigger — don't award
    return False


def upgrade_badge_status(db_path: str, user_id: str, badge_code: str) -> bool:
    """Upgrade a badge from provisional to confirmed.

    Sets confirmed_at timestamp.
    Returns True if upgraded, False if badge not found or already confirmed.
    """
    conn = _get_conn(db_path)
    try:
        # Find badge_id from code
        badge_row = conn.execute(
            "SELECT badge_id FROM sa_badges_v4 WHERE badge_code = ?",
            (badge_code,),
        ).fetchone()
        if not badge_row:
            return False

        badge_id = badge_row["badge_id"]

        # Check current status
        ub_row = conn.execute(
            "SELECT id, status FROM sa_user_badges_v4 "
            "WHERE user_id = ? AND badge_id = ?",
            (user_id, badge_id),
        ).fetchone()

        if not ub_row or ub_row["status"] == "confirmed":
            return False

        conn.execute(
            "UPDATE sa_user_badges_v4 SET status = 'confirmed', confirmed_at = ? "
            "WHERE id = ?",
            (_now_iso(), ub_row["id"]),
        )
        conn.commit()
        return True
    finally:
        conn.close()


# ===================================================================
#  LEADERBOARD OPERATIONS
# ===================================================================

def get_leaderboard(db_path: str, period: str = "all", limit: int = 50) -> list:
    """Get XP leaderboard.

    Args:
        period: 'all', 'weekly', or 'monthly'
        limit: max rows to return

    Returns:
        [{rank, user_id, xp, level_name, level_color, streak_days}]
    """
    column_map = {
        "all": "total_xp",
        "weekly": "weekly_xp",
        "monthly": "monthly_xp",
    }
    xp_col = column_map.get(period, "total_xp")

    conn = _get_conn(db_path)
    try:
        query = (
            "SELECT user_id, total_xp, weekly_xp, monthly_xp, "
            "current_level, streak_days "
            "FROM sa_user_xp "
            "WHERE {col} > 0 "
            "ORDER BY {col} DESC "
            "LIMIT ?"
        ).format(col=xp_col)

        rows = conn.execute(query, (limit,)).fetchall()

        results = []
        for rank, r in enumerate(rows, start=1):
            xp_value = r[xp_col]
            level_info = get_level_for_xp(r["total_xp"] or 0)
            results.append({
                "rank": rank,
                "user_id": r["user_id"],
                "xp": xp_value,
                "level_name": level_info["name"],
                "level_color": level_info["color"],
                "streak_days": r["streak_days"] or 0,
            })

        return results
    finally:
        conn.close()


def get_department_leaderboard(db_path: str) -> list:
    """Aggregate XP by department.

    Attempts to join sa_user_xp with a users/departments table.
    Falls back to individual leaderboard if no department data is available.

    Returns:
        [{rank, department, total_xp, member_count, avg_xp}]
    """
    conn = _get_conn(db_path)
    try:
        # Try to find department info — check if sa_user_profiles or similar exists
        try:
            dept_rows = conn.execute(
                "SELECT p.department, "
                "SUM(x.total_xp) as dept_xp, "
                "COUNT(DISTINCT x.user_id) as member_count, "
                "ROUND(AVG(x.total_xp), 1) as avg_xp "
                "FROM sa_user_xp x "
                "JOIN sa_user_profiles p ON x.user_id = p.user_id "
                "WHERE p.department IS NOT NULL AND p.department != '' "
                "GROUP BY p.department "
                "ORDER BY dept_xp DESC"
            ).fetchall()

            if dept_rows:
                results = []
                for rank, r in enumerate(dept_rows, start=1):
                    results.append({
                        "rank": rank,
                        "department": r["department"],
                        "total_xp": r["dept_xp"] or 0,
                        "member_count": r["member_count"] or 0,
                        "avg_xp": r["avg_xp"] or 0.0,
                    })
                return results
        except sqlite3.OperationalError:
            # sa_user_profiles table doesn't exist — fall back
            pass

        # Fallback: try auth_users table for department/role info
        try:
            dept_rows = conn.execute(
                "SELECT u.role as department, "
                "SUM(x.total_xp) as dept_xp, "
                "COUNT(DISTINCT x.user_id) as member_count, "
                "ROUND(AVG(x.total_xp), 1) as avg_xp "
                "FROM sa_user_xp x "
                "JOIN auth_users u ON x.user_id = u.email "
                "WHERE u.role IS NOT NULL AND u.role != '' "
                "GROUP BY u.role "
                "ORDER BY dept_xp DESC"
            ).fetchall()

            if dept_rows:
                results = []
                for rank, r in enumerate(dept_rows, start=1):
                    results.append({
                        "rank": rank,
                        "department": r["department"],
                        "total_xp": r["dept_xp"] or 0,
                        "member_count": r["member_count"] or 0,
                        "avg_xp": r["avg_xp"] or 0.0,
                    })
                return results
        except sqlite3.OperationalError:
            pass

        # Final fallback: return individual leaderboard
        return get_leaderboard(db_path, period="all", limit=50)

    finally:
        conn.close()


# ===================================================================
#  UTILITY: Weekly/Monthly XP Reset
# ===================================================================

def reset_weekly_xp(db_path: str) -> int:
    """Reset weekly_xp for all users. Call from a scheduled job.

    Returns number of rows updated.
    """
    conn = _get_conn(db_path)
    try:
        cursor = conn.execute(
            "UPDATE sa_user_xp SET weekly_xp = 0, updated_at = ?",
            (_now_iso(),),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def reset_monthly_xp(db_path: str) -> int:
    """Reset monthly_xp for all users. Call from a scheduled job.

    Returns number of rows updated.
    """
    conn = _get_conn(db_path)
    try:
        cursor = conn.execute(
            "UPDATE sa_user_xp SET monthly_xp = 0, updated_at = ?",
            (_now_iso(),),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()
