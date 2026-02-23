"""
Harris Farm Hub — Paddock Assessment Engine
Progressive difficulty assessment: questions get harder, stop at first wrong answer.
"""

import json
import random
import sqlite3
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Tier mapping — difficulty level → tier name
# ---------------------------------------------------------------------------

TIER_MAP = {
    0: "Unranked",
    1: "Seed", 2: "Seed",
    3: "Sprout", 4: "Sprout",
    5: "Grower", 6: "Grower",
    7: "Harvester", 8: "Harvester",
    9: "Cultivator",
    10: "Legend",
}

TIER_ICONS = {
    "Unranked": "\u2753",
    "Seed": "\U0001f331",
    "Sprout": "\U0001f33f",
    "Grower": "\U0001f33b",
    "Harvester": "\U0001f9d1\u200d\U0001f33e",
    "Cultivator": "\U0001f30d",
    "Legend": "\U0001f3c6",
}

TIER_ORDER = ["Unranked", "Seed", "Sprout", "Grower", "Harvester", "Cultivator", "Legend"]


def tier_rank(tier_name):
    """Numeric rank for sorting (higher = better)."""
    try:
        return TIER_ORDER.index(tier_name)
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_paddock_tables(conn):
    """Create Paddock assessment tables. Safe to call repeatedly."""
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS paddock_question_pool (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        difficulty_level INTEGER NOT NULL,
        question_type TEXT NOT NULL,
        question_text TEXT NOT NULL,
        options_json TEXT,
        correct_answer TEXT,
        explanation TEXT,
        topic TEXT,
        flag_count INTEGER DEFAULT 0,
        suspended INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pqp_level ON paddock_question_pool(difficulty_level)")

    c.execute("""CREATE TABLE IF NOT EXISTS paddock_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        max_level_reached INTEGER DEFAULT 0,
        tier_name TEXT DEFAULT 'Unranked',
        total_correct INTEGER DEFAULT 0,
        total_questions INTEGER DEFAULT 0,
        time_seconds INTEGER,
        status TEXT DEFAULT 'in_progress',
        created_at TEXT DEFAULT (datetime('now')),
        completed_at TEXT
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pa_user ON paddock_attempts(user_id)")

    c.execute("""CREATE TABLE IF NOT EXISTS paddock_attempt_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        difficulty_level INTEGER NOT NULL,
        answer TEXT,
        is_correct INTEGER DEFAULT 0,
        time_seconds INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (attempt_id) REFERENCES paddock_attempts(id)
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_par_attempt ON paddock_attempt_responses(attempt_id)")

    conn.commit()


def seed_question_pool(db_path, questions):
    """Bulk-insert seed questions into the pool. Idempotent."""
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM paddock_question_pool").fetchone()[0]
    if count > 0:
        conn.close()
        return 0

    inserted = 0
    for q in questions:
        conn.execute(
            """INSERT INTO paddock_question_pool
               (difficulty_level, question_type, question_text, options_json,
                correct_answer, explanation, topic)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                q["difficulty_level"],
                q["question_type"],
                q["question_text"],
                q.get("options_json", "[]"),
                q.get("correct_answer", ""),
                q.get("explanation", ""),
                q.get("topic", "general"),
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


# ---------------------------------------------------------------------------
# Question retrieval
# ---------------------------------------------------------------------------

def get_question_at_level(db_path, difficulty, exclude_ids=None):
    """Get a random unsuspended question at the given difficulty level."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    exclude = exclude_ids or []
    placeholders = ",".join("?" for _ in exclude) if exclude else ""

    if exclude:
        query = (
            "SELECT id, difficulty_level, question_type, question_text, "
            "options_json, topic FROM paddock_question_pool "
            "WHERE difficulty_level = ? AND suspended = 0 AND id NOT IN ({}) "
            "ORDER BY RANDOM() LIMIT 1"
        ).format(placeholders)
        params = [difficulty] + list(exclude)
    else:
        query = (
            "SELECT id, difficulty_level, question_type, question_text, "
            "options_json, topic FROM paddock_question_pool "
            "WHERE difficulty_level = ? AND suspended = 0 "
            "ORDER BY RANDOM() LIMIT 1"
        )
        params = [difficulty]

    row = conn.execute(query, params).fetchone()
    conn.close()

    if not row:
        return None

    d = dict(row)
    d["options"] = json.loads(d.get("options_json") or "[]")
    # Strip correct flag from options sent to client
    safe_options = []
    for opt in d["options"]:
        safe_options.append({"value": opt["value"], "label": opt["label"]})
    d["options"] = safe_options
    del d["options_json"]
    return d


# ---------------------------------------------------------------------------
# Assessment flow
# ---------------------------------------------------------------------------

def start_attempt(db_path, user_id):
    """Start a new Paddock assessment attempt. Returns attempt + first question."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO paddock_attempts (user_id) VALUES (?)",
        (user_id,),
    )
    attempt_id = c.lastrowid
    conn.commit()
    conn.close()

    question = get_question_at_level(db_path, 1)
    return {
        "attempt_id": attempt_id,
        "current_level": 1,
        "question": question,
        "status": "in_progress",
    }


def submit_answer(db_path, attempt_id, question_id, answer):
    """Submit an answer. Returns next question or assessment end."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get the attempt
    attempt = conn.execute(
        "SELECT * FROM paddock_attempts WHERE id = ? AND status = 'in_progress'",
        (attempt_id,),
    ).fetchone()
    if not attempt:
        conn.close()
        return {"error": "Attempt not found or already completed"}

    # Get the question with correct answer
    question = conn.execute(
        "SELECT * FROM paddock_question_pool WHERE id = ?",
        (question_id,),
    ).fetchone()
    if not question:
        conn.close()
        return {"error": "Question not found"}

    # Check answer
    correct_answer = question["correct_answer"]
    is_correct = str(answer).strip().lower() == str(correct_answer).strip().lower()
    difficulty = question["difficulty_level"]

    # Get previously answered question IDs for this attempt
    prev_ids = [
        r[0] for r in conn.execute(
            "SELECT question_id FROM paddock_attempt_responses WHERE attempt_id = ?",
            (attempt_id,),
        ).fetchall()
    ]

    # Record response
    conn.execute(
        """INSERT INTO paddock_attempt_responses
           (attempt_id, question_id, difficulty_level, answer, is_correct)
           VALUES (?, ?, ?, ?, ?)""",
        (attempt_id, question_id, difficulty, answer, 1 if is_correct else 0),
    )

    total_correct = conn.execute(
        "SELECT COUNT(*) FROM paddock_attempt_responses "
        "WHERE attempt_id = ? AND is_correct = 1",
        (attempt_id,),
    ).fetchone()[0]
    total_questions = conn.execute(
        "SELECT COUNT(*) FROM paddock_attempt_responses WHERE attempt_id = ?",
        (attempt_id,),
    ).fetchone()[0]

    # Update attempt counters
    conn.execute(
        "UPDATE paddock_attempts SET total_correct = ?, total_questions = ? WHERE id = ?",
        (total_correct, total_questions, attempt_id),
    )
    conn.commit()
    conn.close()

    explanation = question["explanation"] or ""

    if not is_correct:
        # Wrong answer — assessment ends
        result = finalize_attempt(db_path, attempt_id)
        return {
            "correct": False,
            "explanation": explanation,
            "correct_answer": correct_answer,
            "assessment_complete": True,
            "result": result,
        }

    # Correct — advance to next level
    next_level = difficulty + 1
    if next_level > 10:
        # Answered Level 10 correctly — Legend!
        result = finalize_attempt(db_path, attempt_id)
        return {
            "correct": True,
            "explanation": explanation,
            "assessment_complete": True,
            "result": result,
        }

    # Get next question (exclude already-seen questions)
    exclude = prev_ids + [question_id]
    next_question = get_question_at_level(db_path, next_level, exclude)

    if not next_question:
        # No more questions at this level — end with current level
        result = finalize_attempt(db_path, attempt_id)
        return {
            "correct": True,
            "explanation": explanation,
            "assessment_complete": True,
            "result": result,
            "note": "No more questions available at next level",
        }

    return {
        "correct": True,
        "explanation": explanation,
        "assessment_complete": False,
        "current_level": next_level,
        "question": next_question,
    }


def finalize_attempt(db_path, attempt_id):
    """Calculate final tier and update attempt record."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    attempt = conn.execute(
        "SELECT * FROM paddock_attempts WHERE id = ?",
        (attempt_id,),
    ).fetchone()
    if not attempt:
        conn.close()
        return {"error": "Attempt not found"}

    # Find max level where user answered correctly
    row = conn.execute(
        "SELECT MAX(difficulty_level) as max_level FROM paddock_attempt_responses "
        "WHERE attempt_id = ? AND is_correct = 1",
        (attempt_id,),
    ).fetchone()
    max_level = row["max_level"] if row and row["max_level"] else 0

    tier_name = TIER_MAP.get(max_level, "Unranked")

    # Calculate time from first to last response
    times = conn.execute(
        "SELECT MIN(created_at) as first_t, MAX(created_at) as last_t "
        "FROM paddock_attempt_responses WHERE attempt_id = ?",
        (attempt_id,),
    ).fetchone()

    time_seconds = 0
    if times and times["first_t"] and times["last_t"]:
        try:
            t1 = datetime.fromisoformat(times["first_t"])
            t2 = datetime.fromisoformat(times["last_t"])
            time_seconds = int((t2 - t1).total_seconds())
        except (ValueError, TypeError):
            pass

    now = datetime.utcnow().isoformat()
    conn.execute(
        """UPDATE paddock_attempts
           SET max_level_reached = ?, tier_name = ?, time_seconds = ?,
               status = 'completed', completed_at = ?
           WHERE id = ?""",
        (max_level, tier_name, time_seconds, now, attempt_id),
    )
    conn.commit()
    conn.close()

    return {
        "attempt_id": attempt_id,
        "max_level_reached": max_level,
        "tier_name": tier_name,
        "tier_icon": TIER_ICONS.get(tier_name, ""),
        "total_correct": int(attempt["total_correct"]),
        "total_questions": int(attempt["total_questions"]),
        "time_seconds": time_seconds,
    }


# ---------------------------------------------------------------------------
# User history & leaderboard
# ---------------------------------------------------------------------------

def get_user_best(db_path, user_id):
    """Get user's best Paddock attempt (highest level reached)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM paddock_attempts "
        "WHERE user_id = ? AND status = 'completed' "
        "ORDER BY max_level_reached DESC, total_correct DESC, time_seconds ASC "
        "LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    d = dict(row)
    d["tier_icon"] = TIER_ICONS.get(d.get("tier_name", ""), "")
    return d


def get_attempt_history(db_path, user_id, limit=20):
    """Get all attempts for a user, most recent first."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, max_level_reached, tier_name, total_correct, "
        "total_questions, time_seconds, status, created_at "
        "FROM paddock_attempts WHERE user_id = ? "
        "ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["tier_icon"] = TIER_ICONS.get(d.get("tier_name", ""), "")
        results.append(d)
    return results


def get_attempt_detail(db_path, attempt_id):
    """Get full attempt detail including all responses."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    attempt = conn.execute(
        "SELECT * FROM paddock_attempts WHERE id = ?",
        (attempt_id,),
    ).fetchone()
    if not attempt:
        conn.close()
        return None

    responses = conn.execute(
        "SELECT r.difficulty_level, r.answer, r.is_correct, r.time_seconds, "
        "q.question_text, q.correct_answer, q.explanation "
        "FROM paddock_attempt_responses r "
        "JOIN paddock_question_pool q ON r.question_id = q.id "
        "WHERE r.attempt_id = ? ORDER BY r.difficulty_level",
        (attempt_id,),
    ).fetchall()
    conn.close()

    d = dict(attempt)
    d["tier_icon"] = TIER_ICONS.get(d.get("tier_name", ""), "")
    d["responses"] = [dict(r) for r in responses]
    return d


def get_leaderboard(db_path, limit=100):
    """Get the Paddock leaderboard — ranked by tier (best), then level, then speed."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get each user's best attempt
    rows = conn.execute("""
        SELECT
            a.user_id,
            MAX(a.max_level_reached) as best_level,
            COUNT(DISTINCT a.id) as total_attempts
        FROM paddock_attempts a
        WHERE a.status = 'completed'
        GROUP BY a.user_id
        ORDER BY best_level DESC
        LIMIT ?
    """, (limit,)).fetchall()

    leaderboard = []
    for i, r in enumerate(rows):
        user_id = r["user_id"]
        best_level = r["best_level"]
        tier_name = TIER_MAP.get(best_level, "Unranked")

        # Get best attempt details for this user at this level
        best = conn.execute(
            "SELECT total_correct, time_seconds, created_at "
            "FROM paddock_attempts "
            "WHERE user_id = ? AND max_level_reached = ? AND status = 'completed' "
            "ORDER BY total_correct DESC, time_seconds ASC LIMIT 1",
            (user_id, best_level),
        ).fetchone()

        # Try to get display name from paddock_users table
        user_row = conn.execute(
            "SELECT name FROM paddock_users WHERE hub_user_id = ?",
            (user_id,),
        ).fetchone()
        display_name = user_row["name"] if user_row else user_id.split("@")[0]

        leaderboard.append({
            "rank": i + 1,
            "user_id": user_id,
            "display_name": display_name,
            "best_level": best_level,
            "tier_name": tier_name,
            "tier_icon": TIER_ICONS.get(tier_name, ""),
            "total_correct": best["total_correct"] if best else 0,
            "time_seconds": best["time_seconds"] if best else 0,
            "total_attempts": r["total_attempts"],
            "achieved_at": best["created_at"] if best else "",
        })

    conn.close()
    return leaderboard
