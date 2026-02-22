"""
Harris Farm Hub — Academy Gamification Engine

Core logic for XP system, level progression, streak tracking,
daily challenges, badge system, and leaderboards.
All functions take db_path as first argument (no FastAPI dependency).
"""

import sqlite3
import json
from datetime import date, datetime, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# XP CONFIGURATION
# ---------------------------------------------------------------------------

XP_ACTIONS = {
    "login": 5,
    "module_complete": 50,
    "module_start": 5,
    "arena_submit": 30,
    "arena_win": 100,
    "daily_challenge": 20,
    "prompt_score_high": 15,
    "prompt_score_medium": 10,
    "score_this_exercise": 10,
    "badge_earned": 10,
    "first_prompt": 10,
    "showcase_submit": 25,
    "quality_review": 10,
}

LEVEL_THRESHOLDS = [
    {"name": "Seed",       "icon": "\U0001f331", "min_xp": 0,    "max_xp": 99},
    {"name": "Sprout",     "icon": "\U0001f33f", "min_xp": 100,  "max_xp": 299},
    {"name": "Grower",     "icon": "\U0001f33b", "min_xp": 300,  "max_xp": 599},
    {"name": "Harvester",  "icon": "\U0001f9fa", "min_xp": 600,  "max_xp": 999},
    {"name": "Cultivator", "icon": "\U0001f333", "min_xp": 1000, "max_xp": 1499},
    {"name": "Legend",     "icon": "\U0001f3c6", "min_xp": 1500, "max_xp": None},
]

STREAK_CONFIG = {
    "base": 1.0,
    "increment_per_day": 0.1,
    "max_multiplier": 2.0,
}

# ---------------------------------------------------------------------------
# BADGE DEFINITIONS
# ---------------------------------------------------------------------------

BADGE_DEFINITIONS = [
    # Onboarding
    {"code": "first_prompt",     "name": "First Prompt",       "icon": "\u2728",       "desc": "Wrote your first AI prompt", "category": "achievement"},
    {"code": "first_module",     "name": "First Module",       "icon": "\U0001f4d6",   "desc": "Completed your first Learning Centre module", "category": "learning"},
    {"code": "first_arena",      "name": "Arena Debut",        "icon": "\U0001f3df\ufe0f", "desc": "Submitted your first Arena challenge", "category": "arena"},
    # Streaks
    {"code": "streak_3",         "name": "3-Day Streak",       "icon": "\U0001f525",   "desc": "3 consecutive days of engagement", "category": "streak"},
    {"code": "streak_7",         "name": "7-Day Streak",       "icon": "\U0001f525",   "desc": "One full week streak", "category": "streak"},
    {"code": "streak_14",        "name": "14-Day Streak",      "icon": "\U0001f4aa",   "desc": "Two-week commitment", "category": "streak"},
    {"code": "streak_30",        "name": "Monthly Legend",     "icon": "\U0001f451",   "desc": "30-day engagement streak", "category": "streak"},
    # Levels
    {"code": "level_sprout",     "name": "Sprouted!",          "icon": "\U0001f33f",   "desc": "Reached Sprout level", "category": "level"},
    {"code": "level_grower",     "name": "Growing Strong",     "icon": "\U0001f33b",   "desc": "Reached Grower level", "category": "level"},
    {"code": "level_harvester",  "name": "Reaping Results",    "icon": "\U0001f9fa",   "desc": "Reached Harvester level", "category": "level"},
    {"code": "level_cultivator", "name": "Shaping the Farm",   "icon": "\U0001f333",   "desc": "Reached Cultivator level", "category": "level"},
    {"code": "level_legend",     "name": "Growing Legend",     "icon": "\U0001f3c6",   "desc": "Achieved Legend status!", "category": "level"},
    # Learning
    {"code": "modules_3",        "name": "Keen Learner",       "icon": "\U0001f4da",   "desc": "Completed 3 Learning Centre modules", "category": "learning"},
    {"code": "modules_6",        "name": "Halfway There",      "icon": "\U0001f393",   "desc": "Completed 6 Learning Centre modules", "category": "learning"},
    {"code": "all_modules",      "name": "Full Curriculum",    "icon": "\U0001f3c5",   "desc": "Completed all 12 Learning Centre modules", "category": "learning"},
    # Arena
    {"code": "arena_3",          "name": "Arena Regular",      "icon": "\u2694\ufe0f",  "desc": "Submitted 3 Arena challenges", "category": "arena"},
    {"code": "arena_champion",   "name": "Arena Champion",     "icon": "\U0001f3c6",   "desc": "Won an Arena challenge", "category": "arena"},
    # Quality
    {"code": "score_20",         "name": "Prompt Master",      "icon": "\U0001f48e",   "desc": "Achieved a 20+ rubric score on a prompt", "category": "achievement"},
    {"code": "score_24",         "name": "Near Perfect",       "icon": "\u2b50",       "desc": "Achieved a 24+ rubric score", "category": "achievement"},
    # Daily challenges
    {"code": "daily_5",          "name": "5 Dailies",          "icon": "\U0001f4c5",   "desc": "Completed 5 daily challenges", "category": "achievement"},
    {"code": "daily_20",         "name": "Daily Devotee",      "icon": "\U0001f31f",   "desc": "Completed 20 daily challenges", "category": "achievement"},
]


# ---------------------------------------------------------------------------
# XP SYSTEM
# ---------------------------------------------------------------------------

def get_level_for_xp(total_xp):
    """Return level info for a given XP total."""
    for i, lv in enumerate(LEVEL_THRESHOLDS):
        max_xp = lv["max_xp"]
        if max_xp is None or total_xp <= max_xp:
            xp_in_level = total_xp - lv["min_xp"]
            level_range = (max_xp - lv["min_xp"] + 1) if max_xp else 500
            progress_pct = min(round(xp_in_level / level_range * 100, 1), 100.0)
            xp_to_next = (max_xp - total_xp + 1) if max_xp else 0
            return {
                "level_index": i,
                "name": lv["name"],
                "icon": lv["icon"],
                "min_xp": lv["min_xp"],
                "max_xp": max_xp,
                "progress_pct": progress_pct,
                "xp_to_next": max(xp_to_next, 0),
            }
    return {"level_index": 5, "name": "Legend", "icon": "\U0001f3c6",
            "min_xp": 1500, "max_xp": None, "progress_pct": 100.0, "xp_to_next": 0}


def get_user_xp(db_path, user_id):
    """Get user's total XP and level info."""
    conn = sqlite3.connect(str(db_path))
    total = conn.execute(
        "SELECT COALESCE(SUM(xp_amount), 0) FROM academy_xp_log WHERE user_id = ?",
        (user_id,),
    ).fetchone()[0]
    conn.close()
    level = get_level_for_xp(total)
    return {"total_xp": total, **level}


def award_xp(db_path, user_id, action_type, base_xp=None, reference_id=None,
             reference_type=None, description=None):
    """Award XP to a user with streak multiplier applied."""
    if base_xp is None:
        base_xp = XP_ACTIONS.get(action_type, 0)
    if base_xp <= 0:
        return {"xp_awarded": 0}

    streak = get_streak(db_path, user_id)
    multiplier = streak.get("streak_multiplier", 1.0)
    xp_amount = int(base_xp * multiplier)

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO academy_xp_log "
        "(user_id, xp_amount, base_amount, multiplier, action_type, "
        "reference_id, reference_type, description) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, xp_amount, base_xp, multiplier, action_type,
         reference_id, reference_type, description),
    )
    conn.commit()
    conn.close()

    # Check for level-up badges
    check_and_award_badges(db_path, user_id)

    user_xp = get_user_xp(db_path, user_id)
    return {"xp_awarded": xp_amount, "multiplier": multiplier, **user_xp}


# ---------------------------------------------------------------------------
# STREAK ENGINE
# ---------------------------------------------------------------------------

def get_streak(db_path, user_id):
    """Get streak data for a user."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM academy_streaks WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "user_id": user_id,
        "current_streak": 0,
        "longest_streak": 0,
        "last_active_date": None,
        "streak_multiplier": 1.0,
        "total_active_days": 0,
    }


def update_streak(db_path, user_id):
    """Record daily engagement. Returns streak info and whether XP was awarded."""
    today_str = date.today().isoformat()
    streak = get_streak(db_path, user_id)
    last_date = streak.get("last_active_date")

    if last_date == today_str:
        return {**streak, "is_new_day": False, "streak_bonus_xp": 0}

    current = streak["current_streak"]
    longest = streak["longest_streak"]
    total_days = streak["total_active_days"]

    if last_date:
        last = date.fromisoformat(last_date)
        diff = (date.today() - last).days
        if diff == 1:
            current += 1
        elif diff > 1:
            current = 1
    else:
        current = 1

    if current > longest:
        longest = current

    multiplier = min(
        STREAK_CONFIG["base"] + (current - 1) * STREAK_CONFIG["increment_per_day"],
        STREAK_CONFIG["max_multiplier"],
    )
    total_days += 1

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO academy_streaks (user_id, current_streak, longest_streak, "
        "last_active_date, streak_multiplier, total_active_days, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, datetime('now')) "
        "ON CONFLICT(user_id) DO UPDATE SET "
        "current_streak=excluded.current_streak, longest_streak=excluded.longest_streak, "
        "last_active_date=excluded.last_active_date, streak_multiplier=excluded.streak_multiplier, "
        "total_active_days=excluded.total_active_days, updated_at=datetime('now')",
        (user_id, current, longest, today_str, multiplier, total_days),
    )
    conn.commit()
    conn.close()

    # Award login XP
    login_xp = XP_ACTIONS.get("login", 5)
    xp_amount = int(login_xp * multiplier)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO academy_xp_log "
        "(user_id, xp_amount, base_amount, multiplier, action_type, description) "
        "VALUES (?, ?, ?, ?, 'login', 'Daily check-in')",
        (user_id, xp_amount, login_xp, multiplier),
    )
    conn.commit()
    conn.close()

    # Check streak badges
    check_and_award_badges(db_path, user_id)

    return {
        "user_id": user_id,
        "current_streak": current,
        "longest_streak": longest,
        "last_active_date": today_str,
        "streak_multiplier": round(multiplier, 1),
        "total_active_days": total_days,
        "is_new_day": True,
        "streak_bonus_xp": xp_amount,
    }


# ---------------------------------------------------------------------------
# DAILY CHALLENGES
# ---------------------------------------------------------------------------

def seed_daily_challenges(db_path):
    """Seed the challenge pool from DAILY_CHALLENGE_POOL. Idempotent."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(db_path).resolve().parent.parent / "dashboards"))
    from shared.academy_content import DAILY_CHALLENGE_POOL

    conn = sqlite3.connect(str(db_path))
    inserted = 0
    for ch in DAILY_CHALLENGE_POOL:
        try:
            conn.execute(
                "INSERT INTO academy_daily_challenges "
                "(challenge_code, title, description, challenge_type, difficulty, "
                "xp_reward, target_level, metadata_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ch["code"], ch["title"], ch["description"], ch["type"],
                 ch.get("difficulty", "beginner"), ch.get("xp_reward", 20),
                 ch.get("target_level"), json.dumps(ch.get("metadata", {}))),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    return inserted


def get_todays_challenge(db_path, user_id):
    """Get today's challenge (deterministic rotation) and completion status."""
    today_str = date.today().isoformat()
    day_number = (date.today() - date(2025, 1, 1)).days

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    challenges = conn.execute(
        "SELECT * FROM academy_daily_challenges WHERE active = 1 ORDER BY id"
    ).fetchall()

    if not challenges:
        conn.close()
        return None

    idx = day_number % len(challenges)
    challenge = dict(challenges[idx])

    completed = conn.execute(
        "SELECT id FROM academy_daily_completions "
        "WHERE user_id = ? AND challenge_id = ? AND challenge_date = ?",
        (user_id, challenge["id"], today_str),
    ).fetchone()
    conn.close()

    challenge["completed_today"] = completed is not None
    challenge["challenge_date"] = today_str
    return challenge


def complete_daily_challenge(db_path, user_id, challenge_id):
    """Mark a daily challenge as complete and award XP."""
    today_str = date.today().isoformat()
    conn = sqlite3.connect(str(db_path))

    # Check not already completed
    existing = conn.execute(
        "SELECT id FROM academy_daily_completions "
        "WHERE user_id = ? AND challenge_id = ? AND challenge_date = ?",
        (user_id, challenge_id, today_str),
    ).fetchone()
    if existing:
        conn.close()
        return {"already_completed": True, "xp_earned": 0}

    # Get challenge XP reward
    row = conn.execute(
        "SELECT xp_reward FROM academy_daily_challenges WHERE id = ?",
        (challenge_id,),
    ).fetchone()
    base_xp = row[0] if row else 20
    conn.close()

    # Award XP (uses streak multiplier internally)
    result = award_xp(db_path, user_id, "daily_challenge", base_xp=base_xp,
                      reference_id=str(challenge_id), reference_type="challenge",
                      description="Daily challenge completed")

    # Record completion
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT OR IGNORE INTO academy_daily_completions "
        "(user_id, challenge_id, challenge_date, xp_earned) VALUES (?, ?, ?, ?)",
        (user_id, challenge_id, today_str, result.get("xp_awarded", 0)),
    )
    conn.commit()
    conn.close()

    check_and_award_badges(db_path, user_id)
    return {"already_completed": False, "xp_earned": result.get("xp_awarded", 0), **result}


# ---------------------------------------------------------------------------
# BADGE SYSTEM
# ---------------------------------------------------------------------------

def get_user_badges(db_path, user_id):
    """Get earned badges and locked badge definitions."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    earned_rows = conn.execute(
        "SELECT * FROM academy_badges WHERE user_id = ? ORDER BY earned_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()

    earned_codes = {r["badge_code"] for r in earned_rows}
    earned = [dict(r) for r in earned_rows]
    locked = [
        {"code": b["code"], "name": b["name"], "icon": b["icon"],
         "desc": b["desc"], "category": b["category"]}
        for b in BADGE_DEFINITIONS if b["code"] not in earned_codes
    ]
    return {"earned": earned, "locked": locked, "total_earned": len(earned),
            "total_available": len(BADGE_DEFINITIONS)}


def check_and_award_badges(db_path, user_id):
    """Check eligibility and award any new badges. Returns list of newly awarded."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Get current state
    earned_codes = {
        r["badge_code"]
        for r in conn.execute(
            "SELECT badge_code FROM academy_badges WHERE user_id = ?", (user_id,)
        ).fetchall()
    }

    total_xp = conn.execute(
        "SELECT COALESCE(SUM(xp_amount), 0) FROM academy_xp_log WHERE user_id = ?",
        (user_id,),
    ).fetchone()[0]

    streak_row = conn.execute(
        "SELECT current_streak FROM academy_streaks WHERE user_id = ?", (user_id,)
    ).fetchone()
    current_streak = streak_row["current_streak"] if streak_row else 0

    modules_completed = conn.execute(
        "SELECT COUNT(*) FROM user_progress WHERE user_id = ? AND status = 'completed'",
        (user_id,),
    ).fetchone()[0]

    daily_count = conn.execute(
        "SELECT COUNT(*) FROM academy_daily_completions WHERE user_id = ?",
        (user_id,),
    ).fetchone()[0]

    xp_actions = conn.execute(
        "SELECT action_type, COUNT(*) as cnt FROM academy_xp_log "
        "WHERE user_id = ? GROUP BY action_type",
        (user_id,),
    ).fetchall()
    action_counts = {r["action_type"]: r["cnt"] for r in xp_actions}

    conn.close()

    level = get_level_for_xp(total_xp)

    # Eligibility rules
    eligible = []

    # Level badges
    level_badges = {
        "Sprout": "level_sprout", "Grower": "level_grower",
        "Harvester": "level_harvester", "Cultivator": "level_cultivator",
        "Legend": "level_legend",
    }
    for lv_name, badge_code in level_badges.items():
        lv_data = next((l for l in LEVEL_THRESHOLDS if l["name"] == lv_name), None)
        if lv_data and total_xp >= lv_data["min_xp"]:
            eligible.append(badge_code)

    # Streak badges
    if current_streak >= 3:
        eligible.append("streak_3")
    if current_streak >= 7:
        eligible.append("streak_7")
    if current_streak >= 14:
        eligible.append("streak_14")
    if current_streak >= 30:
        eligible.append("streak_30")

    # Module badges
    if modules_completed >= 1:
        eligible.append("first_module")
    if modules_completed >= 3:
        eligible.append("modules_3")
    if modules_completed >= 6:
        eligible.append("modules_6")
    if modules_completed >= 12:
        eligible.append("all_modules")

    # Daily challenge badges
    if daily_count >= 5:
        eligible.append("daily_5")
    if daily_count >= 20:
        eligible.append("daily_20")

    # Action-based badges
    if action_counts.get("arena_submit", 0) >= 1:
        eligible.append("first_arena")
    if action_counts.get("arena_submit", 0) >= 3:
        eligible.append("arena_3")

    # Award new badges
    newly_awarded = []
    badge_lookup = {b["code"]: b for b in BADGE_DEFINITIONS}

    conn = sqlite3.connect(str(db_path))
    for code in eligible:
        if code not in earned_codes and code in badge_lookup:
            b = badge_lookup[code]
            try:
                conn.execute(
                    "INSERT INTO academy_badges "
                    "(user_id, badge_code, badge_name, badge_icon, "
                    "badge_description, category, xp_awarded) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user_id, code, b["name"], b["icon"], b["desc"],
                     b["category"], XP_ACTIONS.get("badge_earned", 10)),
                )
                newly_awarded.append(b)
            except sqlite3.IntegrityError:
                pass
    conn.commit()
    conn.close()

    # Award badge XP (without triggering recursive badge check)
    if newly_awarded:
        badge_xp = XP_ACTIONS.get("badge_earned", 10) * len(newly_awarded)
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO academy_xp_log "
            "(user_id, xp_amount, base_amount, multiplier, action_type, description) "
            "VALUES (?, ?, ?, 1.0, 'badge_earned', ?)",
            (user_id, badge_xp, badge_xp,
             f"Earned {len(newly_awarded)} badge(s)"),
        )
        conn.commit()
        conn.close()

    return newly_awarded


# ---------------------------------------------------------------------------
# LEADERBOARD
# ---------------------------------------------------------------------------

def get_leaderboard(db_path, period="all", limit=50):
    """Get individual leaderboard ranked by XP."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    if period == "week":
        date_filter = "AND created_at >= date('now', '-7 days')"
    elif period == "month":
        date_filter = "AND created_at >= date('now', '-30 days')"
    else:
        date_filter = ""

    rows = conn.execute(
        f"SELECT user_id, SUM(xp_amount) as total_xp, COUNT(*) as actions "
        f"FROM academy_xp_log WHERE 1=1 {date_filter} "
        f"GROUP BY user_id ORDER BY total_xp DESC LIMIT ?",
        (limit,),
    ).fetchall()

    result = []
    for rank, row in enumerate(rows, 1):
        level = get_level_for_xp(row["total_xp"])
        streak_row = conn.execute(
            "SELECT current_streak FROM academy_streaks WHERE user_id = ?",
            (row["user_id"],),
        ).fetchone()
        result.append({
            "rank": rank,
            "user_id": row["user_id"],
            "total_xp": row["total_xp"],
            "actions": row["actions"],
            "level_name": level["name"],
            "level_icon": level["icon"],
            "current_streak": streak_row["current_streak"] if streak_row else 0,
        })

    conn.close()
    return result


# ---------------------------------------------------------------------------
# FULL PROFILE
# ---------------------------------------------------------------------------

def get_full_profile(db_path, user_id):
    """Aggregated user profile: XP, level, streak, badges, recent activity."""
    xp_data = get_user_xp(db_path, user_id)
    streak_data = get_streak(db_path, user_id)
    badges_data = get_user_badges(db_path, user_id)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    recent = conn.execute(
        "SELECT action_type, xp_amount, description, created_at "
        "FROM academy_xp_log WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (user_id,),
    ).fetchall()

    modules_completed = conn.execute(
        "SELECT COUNT(*) FROM user_progress WHERE user_id = ? AND status = 'completed'",
        (user_id,),
    ).fetchone()[0]

    daily_count = conn.execute(
        "SELECT COUNT(*) FROM academy_daily_completions WHERE user_id = ?",
        (user_id,),
    ).fetchone()[0]
    conn.close()

    return {
        **xp_data,
        "streak": streak_data,
        "badges": badges_data,
        "recent_activity": [dict(r) for r in recent],
        "modules_completed": modules_completed,
        "dailies_completed": daily_count,
    }


# ---------------------------------------------------------------------------
# INTEGRATION HOOKS
# ---------------------------------------------------------------------------

def on_module_complete(db_path, user_id, module_code):
    """Called when a user completes a Learning Centre module."""
    return award_xp(db_path, user_id, "module_complete",
                    reference_id=module_code, reference_type="module",
                    description=f"Completed module {module_code}")


def on_prompt_scored(db_path, user_id, score, prompt_id=None):
    """Called when a user's prompt is scored (out of 25)."""
    if score >= 24:
        action = "prompt_score_high"
        desc = f"Excellent prompt score: {score}/25"
    elif score >= 20:
        action = "prompt_score_high"
        desc = f"High prompt score: {score}/25"
    elif score >= 14:
        action = "prompt_score_medium"
        desc = f"Good prompt score: {score}/25"
    else:
        return {"xp_awarded": 0}

    result = award_xp(db_path, user_id, action,
                      reference_id=str(prompt_id) if prompt_id else None,
                      reference_type="prompt", description=desc)

    # Check score-based badges
    if score >= 20:
        _try_award_badge(db_path, user_id, "score_20")
    if score >= 24:
        _try_award_badge(db_path, user_id, "score_24")

    return result


def _try_award_badge(db_path, user_id, badge_code):
    """Try to award a specific badge. Silent on duplicate."""
    badge_lookup = {b["code"]: b for b in BADGE_DEFINITIONS}
    b = badge_lookup.get(badge_code)
    if not b:
        return
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO academy_badges "
            "(user_id, badge_code, badge_name, badge_icon, "
            "badge_description, category, xp_awarded) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, badge_code, b["name"], b["icon"], b["desc"],
             b["category"], XP_ACTIONS.get("badge_earned", 10)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()
