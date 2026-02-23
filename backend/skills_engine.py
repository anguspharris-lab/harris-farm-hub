"""
Harris Farm Hub — Skills Academy Engine
Module management, prerequisite checking, and assessment scoring via Claude API.
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Assessment Rubric — 5 criteria, each /5, total /25
# ---------------------------------------------------------------------------

ASSESSMENT_RUBRIC = {
    "criteria": [
        {"key": "clarity", "name": "Request Clarity", "max": 5,
         "description": "Is the request unambiguous and specific?"},
        {"key": "context", "name": "Context Provision", "max": 5,
         "description": "Does it include relevant HFM business context?"},
        {"key": "data_spec", "name": "Data Specification", "max": 5,
         "description": "Does it specify what data to use or reference?"},
        {"key": "format", "name": "Output Format", "max": 5,
         "description": "Does it define the desired output structure?"},
        {"key": "actionability", "name": "Actionability", "max": 5,
         "description": "Will the output lead to a concrete business action?"},
    ],
    "pass_threshold": 18,
    "max_score": 25,
}

SCORING_SYSTEM_PROMPT = """You are an AI skills evaluator for Harris Farm Markets, an Australian fresh food retailer.

Score the submitted prompt against these 5 criteria (each 1-5):

1. **Request Clarity** (1-5): Is the request unambiguous and specific? Does the reader know exactly what is being asked?
2. **Context Provision** (1-5): Does it include relevant business context (store, department, time period, role)?
3. **Data Specification** (1-5): Does it specify what data sources, metrics, or information to use?
4. **Output Format** (1-5): Does it define the desired output structure (table, summary, bullet points, report)?
5. **Actionability** (1-5): Will the output lead to a concrete business decision or action?

Scoring guide:
- 1 = Missing entirely
- 2 = Vaguely present
- 3 = Adequate but could be stronger
- 4 = Good, clear, and useful
- 5 = Excellent, precise, and comprehensive

Be strict but fair. A score of 18+/25 represents genuinely good prompt craft.

Return ONLY valid JSON (no markdown, no code fences):
{
    "clarity": <int 1-5>,
    "context": <int 1-5>,
    "data_spec": <int 1-5>,
    "format": <int 1-5>,
    "actionability": <int 1-5>,
    "total": <int sum>,
    "feedback": "<2-3 sentences of constructive feedback>",
    "improved_prompt": "<your improved version of the prompt>"
}"""


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_skills_tables(conn):
    """Create Skills Academy tables. Safe to call repeatedly."""
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS skills_modules (
        code TEXT PRIMARY KEY,
        series TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        prerequisites TEXT DEFAULT '[]',
        content_json TEXT DEFAULT '{}',
        sort_order INTEGER DEFAULT 0,
        duration_minutes INTEGER DEFAULT 45,
        difficulty TEXT DEFAULT 'beginner',
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS skills_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        module_code TEXT NOT NULL,
        prompt_text TEXT NOT NULL,
        scores_json TEXT,
        total_score INTEGER,
        feedback TEXT,
        improved_prompt TEXT,
        status TEXT DEFAULT 'submitted',
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sa_user ON skills_assessments(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sa_module ON skills_assessments(module_code)")

    # v3 — Adaptive difficulty tracking
    c.execute("""CREATE TABLE IF NOT EXISTS sa_exercise_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        module_code TEXT NOT NULL,
        current_tier TEXT DEFAULT 'standard',
        consecutive_elite INTEGER DEFAULT 0,
        last_score_pct REAL,
        attempts INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(user_id, module_code)
    )""")

    # v3 — Mindset assessments
    c.execute("""CREATE TABLE IF NOT EXISTS sa_mindset_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        level_number INTEGER NOT NULL,
        scores_json TEXT,
        composite_score REAL,
        scenario_used TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_mindset_user ON sa_mindset_assessments(user_id)")

    # v3 — Daily micro-challenges (90-second quick questions)
    c.execute("""CREATE TABLE IF NOT EXISTS sa_daily_micro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL,
        options_json TEXT,
        correct_answer TEXT NOT NULL,
        topic TEXT DEFAULT 'general',
        time_limit_seconds INTEGER DEFAULT 90,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS sa_daily_micro_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        challenge_id INTEGER NOT NULL,
        challenge_date TEXT NOT NULL,
        answer TEXT,
        is_correct INTEGER DEFAULT 0,
        time_seconds INTEGER,
        xp_awarded INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_micro_user ON sa_daily_micro_completions(user_id)")

    # v3 — Peer battles
    c.execute("""CREATE TABLE IF NOT EXISTS sa_peer_battles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        challenger_id TEXT NOT NULL,
        opponent_id TEXT,
        scenario_text TEXT NOT NULL,
        challenger_prompt TEXT,
        opponent_prompt TEXT,
        challenger_score_json TEXT,
        opponent_score_json TEXT,
        winner_id TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT DEFAULT (datetime('now')),
        completed_at TEXT
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_battles_status ON sa_peer_battles(status)")

    # v3 — Skip-ahead attempts
    c.execute("""CREATE TABLE IF NOT EXISTS sa_skip_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        from_module TEXT NOT NULL,
        to_module TEXT NOT NULL,
        challenge_text TEXT,
        response_text TEXT,
        score INTEGER,
        passed INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    conn.commit()


def seed_skills_modules(db_path, modules):
    """Seed module definitions into skills_modules table. Idempotent."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    count = c.execute("SELECT COUNT(*) FROM skills_modules").fetchone()[0]
    if count > 0:
        conn.close()
        return 0

    inserted = 0
    for m in modules:
        c.execute(
            """INSERT OR IGNORE INTO skills_modules
               (code, series, name, description, prerequisites, content_json,
                sort_order, duration_minutes, difficulty)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                m["code"], m["series"], m["name"], m["description"],
                json.dumps(m.get("prerequisites", [])),
                json.dumps({
                    "theory": m.get("theory", []),
                    "examples": m.get("examples", []),
                    "exercise": m.get("exercise", {}),
                    "assessment": m.get("assessment", {}),
                }),
                m.get("sort_order", 0),
                m.get("duration_minutes", 45),
                m.get("difficulty", "beginner"),
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


# ---------------------------------------------------------------------------
# Module queries
# ---------------------------------------------------------------------------

def get_all_modules(db_path):
    """Return all modules ordered by series then sort_order."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT code, series, name, description, prerequisites, "
        "sort_order, duration_minutes, difficulty FROM skills_modules "
        "ORDER BY series, sort_order"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_module(db_path, code):
    """Return a single module with full content."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM skills_modules WHERE code = ?", (code,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["prerequisites"] = json.loads(d.get("prerequisites") or "[]")
    d["content"] = json.loads(d.get("content_json") or "{}")
    return d


def check_prerequisites(db_path, user_id, module_code):
    """Check if user has passed all prerequisites for a module."""
    module = get_module(db_path, module_code)
    if not module:
        return False
    prereqs = module.get("prerequisites", [])
    if not prereqs:
        return True

    conn = sqlite3.connect(db_path)
    for prereq_code in prereqs:
        row = conn.execute(
            "SELECT MAX(total_score) as best FROM skills_assessments "
            "WHERE user_id = ? AND module_code = ? AND status = 'passed'",
            (user_id, prereq_code),
        ).fetchone()
        if not row or row[0] is None:
            conn.close()
            return False
    conn.close()
    return True


def get_user_skills_progress(db_path, user_id):
    """Get user's progress across all modules."""
    modules = get_all_modules(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    progress = []
    for m in modules:
        code = m["code"]
        # Best assessment for this module
        best = conn.execute(
            "SELECT MAX(total_score) as best_score, COUNT(*) as attempts "
            "FROM skills_assessments WHERE user_id = ? AND module_code = ?",
            (user_id, code),
        ).fetchone()

        best_score = best["best_score"] if best and best["best_score"] else 0
        attempts = best["attempts"] if best else 0
        passed = best_score >= ASSESSMENT_RUBRIC["pass_threshold"]

        # Check prereqs
        prereqs = json.loads(m.get("prerequisites") or "[]")
        prereqs_met = check_prerequisites(db_path, user_id, code)

        progress.append({
            "code": code,
            "series": m["series"],
            "name": m["name"],
            "difficulty": m["difficulty"],
            "best_score": best_score,
            "attempts": attempts,
            "passed": passed,
            "prerequisites": prereqs,
            "prereqs_met": prereqs_met,
            "locked": not prereqs_met and len(prereqs) > 0,
        })

    conn.close()
    return progress


# ---------------------------------------------------------------------------
# Assessment submission & scoring
# ---------------------------------------------------------------------------

def submit_assessment(db_path, user_id, module_code, prompt_text):
    """Store an assessment submission. Returns assessment ID."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """INSERT INTO skills_assessments
           (user_id, module_code, prompt_text, status)
           VALUES (?, ?, ?, 'submitted')""",
        (user_id, module_code, prompt_text),
    )
    assessment_id = c.lastrowid
    conn.commit()
    conn.close()
    return assessment_id


def score_assessment(db_path, assessment_id, anthropic_key):
    """Score an assessment using Claude API. Updates DB and returns scores."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM skills_assessments WHERE id = ?", (assessment_id,)
    ).fetchone()
    conn.close()

    if not row:
        return {"error": "Assessment not found"}

    prompt_text = row["prompt_text"]
    module_code = row["module_code"]

    # Call Claude API
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SCORING_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Module: {module_code}\n\nPrompt to evaluate:\n\n{prompt_text}",
            }],
        )
        response_text = message.content[0].text.strip()

        # Parse JSON response
        scores = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        import re
        match = re.search(r'\{[^{}]+\}', response_text, re.DOTALL)
        if match:
            scores = json.loads(match.group())
        else:
            return {"error": "Could not parse scoring response"}
    except Exception as e:
        return {"error": f"Claude API error: {str(e)}"}

    # Validate scores
    total = 0
    for crit in ASSESSMENT_RUBRIC["criteria"]:
        key = crit["key"]
        val = scores.get(key, 0)
        if not isinstance(val, int):
            val = int(val) if val else 0
        val = max(1, min(5, val))
        scores[key] = val
        total += val
    scores["total"] = total

    passed = total >= ASSESSMENT_RUBRIC["pass_threshold"]
    status = "passed" if passed else "needs_improvement"

    # Update DB
    conn = sqlite3.connect(db_path)
    conn.execute(
        """UPDATE skills_assessments
           SET scores_json = ?, total_score = ?, feedback = ?,
               improved_prompt = ?, status = ?
           WHERE id = ?""",
        (
            json.dumps(scores),
            total,
            scores.get("feedback", ""),
            scores.get("improved_prompt", ""),
            status,
            assessment_id,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "assessment_id": assessment_id,
        "scores": scores,
        "total": total,
        "passed": passed,
        "status": status,
        "feedback": scores.get("feedback", ""),
        "improved_prompt": scores.get("improved_prompt", ""),
    }


def get_assessment_results(db_path, user_id, module_code):
    """Get all assessment results for a user on a module."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, prompt_text, scores_json, total_score, feedback, "
        "improved_prompt, status, created_at "
        "FROM skills_assessments "
        "WHERE user_id = ? AND module_code = ? "
        "ORDER BY created_at DESC",
        (user_id, module_code),
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["scores"] = json.loads(d.get("scores_json") or "{}")
        del d["scores_json"]
        results.append(d)
    return results


# ---------------------------------------------------------------------------
# v3 — Adaptive Difficulty Engine
# ---------------------------------------------------------------------------

TIER_ORDER = ["standard", "stretch", "elite"]


def get_exercise_tier(db_path, user_id, module_code):
    """Get current exercise tier for a user on a module."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM sa_exercise_state WHERE user_id = ? AND module_code = ?",
        (user_id, module_code),
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "user_id": user_id,
        "module_code": module_code,
        "current_tier": "standard",
        "consecutive_elite": 0,
        "last_score_pct": None,
        "attempts": 0,
    }


def update_exercise_tier(db_path, user_id, module_code, score_pct):
    """Update adaptive tier based on exercise score.
    score_pct >= 80 → advance tier; score_pct < 60 → drop tier.
    Returns updated state dict.
    """
    state = get_exercise_tier(db_path, user_id, module_code)
    current = state["current_tier"]
    idx = TIER_ORDER.index(current) if current in TIER_ORDER else 0
    consecutive_elite = state["consecutive_elite"]

    if score_pct >= 80 and idx < len(TIER_ORDER) - 1:
        idx += 1
    elif score_pct < 60 and idx > 0:
        idx -= 1

    new_tier = TIER_ORDER[idx]

    # Track consecutive elite completions for skip-ahead
    if new_tier == "elite" and score_pct >= 80:
        consecutive_elite += 1
    else:
        consecutive_elite = 0

    attempts = state["attempts"] + 1

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO sa_exercise_state "
        "(user_id, module_code, current_tier, consecutive_elite, "
        "last_score_pct, attempts, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, datetime('now')) "
        "ON CONFLICT(user_id, module_code) DO UPDATE SET "
        "current_tier=excluded.current_tier, "
        "consecutive_elite=excluded.consecutive_elite, "
        "last_score_pct=excluded.last_score_pct, "
        "attempts=excluded.attempts, updated_at=datetime('now')",
        (user_id, module_code, new_tier, consecutive_elite, score_pct, attempts),
    )
    conn.commit()
    conn.close()

    return {
        "user_id": user_id,
        "module_code": module_code,
        "current_tier": new_tier,
        "previous_tier": current,
        "tier_changed": new_tier != current,
        "consecutive_elite": consecutive_elite,
        "skip_ahead_eligible": consecutive_elite >= 3,
        "last_score_pct": score_pct,
        "attempts": attempts,
    }


def check_skip_ahead(db_path, user_id, module_code):
    """Check if user is eligible to skip ahead (3+ consecutive elite scores)."""
    state = get_exercise_tier(db_path, user_id, module_code)
    return state.get("consecutive_elite", 0) >= 3


def get_rubric_type_for_module(module_code):
    """Determine which rubric to use based on module level.
    L1, L2, D1, D2 → 'foundational' (5 criteria × 5)
    L3, L4, D3, D4 → 'advanced' (8 criteria × 10)
    L5, L6, D5     → 'panel' (5 tiers × 10)
    """
    code_upper = module_code.upper()
    if code_upper in ("L1", "L2", "D1", "D2"):
        return "foundational"
    elif code_upper in ("L3", "L4", "D3", "D4"):
        return "advanced"
    else:
        return "panel"


# ---------------------------------------------------------------------------
# v3 — Mindset Assessment
# ---------------------------------------------------------------------------

def submit_mindset_assessment(db_path, user_id, level_number, responses):
    """Store mindset assessment results.
    responses: dict of {indicator_key: score (1-4)}
    Returns assessment summary.
    """
    scores = {}
    total = 0
    for key in ("first_instinct", "scope", "ambition", "breadth"):
        val = responses.get(key, 1)
        val = max(1, min(4, int(val)))
        scores[key] = val
        total += val
    composite = round(total / 4.0, 2)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO sa_mindset_assessments "
        "(user_id, level_number, scores_json, composite_score, scenario_used) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, level_number, json.dumps(scores), composite,
         "level_{}".format(level_number)),
    )
    assessment_id = c.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": assessment_id,
        "user_id": user_id,
        "level_number": level_number,
        "scores": scores,
        "composite_score": composite,
    }


def get_mindset_history(db_path, user_id):
    """Get all mindset assessments for a user, ordered by level."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM sa_mindset_assessments WHERE user_id = ? "
        "ORDER BY level_number, created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["scores"] = json.loads(d.get("scores_json") or "{}")
        results.append(d)
    return results


# ---------------------------------------------------------------------------
# v3 — Daily Micro-Challenges
# ---------------------------------------------------------------------------

def seed_daily_micro(db_path, questions):
    """Seed micro-challenge question pool. Idempotent."""
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM sa_daily_micro").fetchone()[0]
    if count > 0:
        conn.close()
        return 0

    inserted = 0
    for q in questions:
        conn.execute(
            "INSERT INTO sa_daily_micro "
            "(question_text, options_json, correct_answer, topic, time_limit_seconds) "
            "VALUES (?, ?, ?, ?, ?)",
            (q["question"], json.dumps(q.get("options", [])),
             q["correct_answer"], q.get("topic", "general"),
             q.get("time_limit", 90)),
        )
        inserted += 1
    conn.commit()
    conn.close()
    return inserted


def get_daily_micro(db_path):
    """Get today's micro-challenge (deterministic daily rotation)."""
    from datetime import date as _date
    today_str = _date.today().isoformat()
    day_number = (_date.today() - _date(2025, 1, 1)).days

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    questions = conn.execute(
        "SELECT * FROM sa_daily_micro WHERE active = 1 ORDER BY id"
    ).fetchall()
    conn.close()

    if not questions:
        return None

    idx = day_number % len(questions)
    q = dict(questions[idx])
    q["options"] = json.loads(q.get("options_json") or "[]")
    q["challenge_date"] = today_str
    return q


def submit_daily_micro(db_path, user_id, challenge_id, answer, time_seconds):
    """Submit answer for daily micro-challenge. Returns result."""
    from datetime import date as _date
    today_str = _date.today().isoformat()

    # Check not already completed today
    conn = sqlite3.connect(db_path)
    existing = conn.execute(
        "SELECT id FROM sa_daily_micro_completions "
        "WHERE user_id = ? AND challenge_id = ? AND challenge_date = ?",
        (user_id, challenge_id, today_str),
    ).fetchone()
    if existing:
        conn.close()
        return {"already_completed": True, "xp_earned": 0}

    # Check answer
    conn.row_factory = sqlite3.Row
    q = conn.execute(
        "SELECT correct_answer FROM sa_daily_micro WHERE id = ?",
        (challenge_id,),
    ).fetchone()
    conn.close()

    is_correct = q["correct_answer"].strip().lower() == answer.strip().lower() if q else False

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO sa_daily_micro_completions "
        "(user_id, challenge_id, challenge_date, answer, is_correct, time_seconds) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, challenge_id, today_str, answer, 1 if is_correct else 0, time_seconds),
    )
    conn.commit()
    conn.close()

    return {
        "is_correct": is_correct,
        "correct_answer": q["correct_answer"] if q else "",
        "time_seconds": time_seconds,
    }


# ---------------------------------------------------------------------------
# v3 — Peer Battles
# ---------------------------------------------------------------------------

def create_peer_battle(db_path, challenger_id, scenario_text, challenger_prompt):
    """Create an open peer battle. Returns battle ID."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO sa_peer_battles "
        "(challenger_id, scenario_text, challenger_prompt, status) "
        "VALUES (?, ?, ?, 'open')",
        (challenger_id, scenario_text, challenger_prompt),
    )
    battle_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"id": battle_id, "status": "open"}


def join_peer_battle(db_path, battle_id, opponent_id, opponent_prompt):
    """Join an open peer battle with a prompt."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    battle = conn.execute(
        "SELECT * FROM sa_peer_battles WHERE id = ? AND status = 'open'",
        (battle_id,),
    ).fetchone()
    if not battle:
        conn.close()
        return {"error": "Battle not found or already matched"}
    if battle["challenger_id"] == opponent_id:
        conn.close()
        return {"error": "Cannot battle yourself"}

    conn.execute(
        "UPDATE sa_peer_battles SET opponent_id = ?, opponent_prompt = ?, "
        "status = 'matched' WHERE id = ?",
        (opponent_id, opponent_prompt, battle_id),
    )
    conn.commit()
    conn.close()
    return {"id": battle_id, "status": "matched"}


def score_peer_battle(db_path, battle_id, anthropic_key):
    """Score a matched peer battle using Claude. Returns winner."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    battle = conn.execute(
        "SELECT * FROM sa_peer_battles WHERE id = ? AND status = 'matched'",
        (battle_id,),
    ).fetchone()
    if not battle:
        conn.close()
        return {"error": "Battle not ready for scoring"}

    scenario = battle["scenario_text"]
    prompt_a = battle["challenger_prompt"]
    prompt_b = battle["opponent_prompt"]

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system="You are judging a peer battle between two AI prompts. "
                   "Score each prompt 1-10 on clarity, context, format, and actionability. "
                   "Return JSON: {\"a_score\": <int>, \"b_score\": <int>, "
                   "\"a_feedback\": \"...\", \"b_feedback\": \"...\", "
                   "\"winner\": \"a\" or \"b\" or \"tie\"}",
            messages=[{
                "role": "user",
                "content": "Scenario: {}\n\nPrompt A:\n{}\n\nPrompt B:\n{}".format(
                    scenario, prompt_a, prompt_b
                ),
            }],
        )
        result = json.loads(message.content[0].text.strip())
    except Exception as e:
        conn.close()
        return {"error": "Scoring failed: {}".format(str(e))}

    winner_map = {
        "a": battle["challenger_id"],
        "b": battle["opponent_id"],
        "tie": None,
    }
    winner_id = winner_map.get(result.get("winner"), None)

    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE sa_peer_battles SET challenger_score_json = ?, "
        "opponent_score_json = ?, winner_id = ?, status = 'complete', "
        "completed_at = datetime('now') WHERE id = ?",
        (json.dumps({"score": result.get("a_score"), "feedback": result.get("a_feedback")}),
         json.dumps({"score": result.get("b_score"), "feedback": result.get("b_feedback")}),
         winner_id, battle_id),
    )
    conn.commit()
    conn.close()

    return {
        "id": battle_id,
        "winner_id": winner_id,
        "challenger_score": result.get("a_score"),
        "opponent_score": result.get("b_score"),
        "status": "complete",
    }


def get_open_battles(db_path, limit=20):
    """Get open peer battles available to join."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, challenger_id, scenario_text, created_at "
        "FROM sa_peer_battles WHERE status = 'open' "
        "ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# v3 — Skip-Ahead Challenges
# ---------------------------------------------------------------------------

def attempt_skip_ahead(db_path, user_id, from_module, to_module,
                       response_text, anthropic_key):
    """Attempt to skip ahead from one module to another.
    Requires scoring >= 20/25 on a harder challenge.
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=SCORING_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": "Skip-ahead challenge from {} to {}.\n\n"
                           "Prompt to evaluate:\n\n{}".format(
                               from_module, to_module, response_text),
            }],
        )
        scores = json.loads(message.content[0].text.strip())
        total = sum(
            max(1, min(5, int(scores.get(c["key"], 0))))
            for c in ASSESSMENT_RUBRIC["criteria"]
        )
    except Exception:
        total = 0
        scores = {}

    passed = total >= 20  # Higher bar for skip-ahead

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO sa_skip_attempts "
        "(user_id, from_module, to_module, response_text, score, passed) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, from_module, to_module, response_text, total, 1 if passed else 0),
    )
    conn.commit()
    conn.close()

    return {
        "user_id": user_id,
        "from_module": from_module,
        "to_module": to_module,
        "score": total,
        "passed": passed,
        "scores": scores,
    }
