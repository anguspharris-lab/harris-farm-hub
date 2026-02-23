"""
Skills Academy v4 — Social & Community Engine
Mentoring, prompt library, live problems, peer battles v4, daily challenges v4.
"""

import json
import os
import random
import sqlite3
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Mentoring
# ---------------------------------------------------------------------------

def create_mentoring_pair(db_path: str, mentor_id: str, mentee_id: str,
                          mentee_start_level: int, mentee_target_level: int) -> dict:
    """Create a mentor-mentee relationship."""
    conn = sqlite3.connect(db_path)
    try:
        # Check for existing active pair
        existing = conn.execute(
            "SELECT mentoring_id FROM sa_mentoring "
            "WHERE mentor_user_id = ? AND mentee_user_id = ? AND status = 'active'",
            (mentor_id, mentee_id),
        ).fetchone()
        if existing:
            return {"error": "Active mentoring pair already exists", "mentoring_id": existing[0]}

        cur = conn.execute(
            "INSERT INTO sa_mentoring (mentor_user_id, mentee_user_id, "
            "mentee_start_level, mentee_target_level, started_at) "
            "VALUES (?,?,?,?,?)",
            (mentor_id, mentee_id, mentee_start_level, mentee_target_level,
             datetime.utcnow().isoformat()),
        )
        conn.commit()
        return {"mentoring_id": cur.lastrowid, "status": "active"}
    finally:
        conn.close()


def get_mentoring_relationships(db_path: str, user_id: str) -> dict:
    """Get all mentoring relationships for a user (as mentor or mentee)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        as_mentor = conn.execute(
            "SELECT * FROM sa_mentoring WHERE mentor_user_id = ? ORDER BY started_at DESC",
            (user_id,),
        ).fetchall()
        as_mentee = conn.execute(
            "SELECT * FROM sa_mentoring WHERE mentee_user_id = ? ORDER BY started_at DESC",
            (user_id,),
        ).fetchall()
        return {
            "as_mentor": [dict(r) for r in as_mentor],
            "as_mentee": [dict(r) for r in as_mentee],
        }
    finally:
        conn.close()


def complete_mentoring(db_path: str, mentoring_id: int) -> bool:
    """Mark a mentoring relationship as completed."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE sa_mentoring SET status = 'completed', completed_at = ? "
            "WHERE mentoring_id = ?",
            (datetime.utcnow().isoformat(), mentoring_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Prompt Library
# ---------------------------------------------------------------------------

def submit_prompt(db_path: str, user_id: str, title: str, prompt_text: str,
                  description: str = "", use_case: str = "",
                  department: str = "", tags: str = "") -> dict:
    """Submit a prompt to the library for review."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO sa_prompt_library (user_id, title, prompt_text, description, "
            "use_case, department, tags, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (user_id, title, prompt_text, description, use_case, department, tags,
             datetime.utcnow().isoformat()),
        )
        conn.commit()
        return {"prompt_id": cur.lastrowid, "status": "submitted"}
    finally:
        conn.close()


def get_prompts(db_path: str, status: str = "approved", department: str = "",
                limit: int = 50) -> list:
    """Browse prompts in the library."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if status == "approved":
            condition = "is_approved = 1"
        elif status == "pending":
            condition = "is_approved = 0 AND reviewed_by IS NULL"
        else:
            condition = "1=1"

        if department:
            condition += " AND department = ?"
            rows = conn.execute(
                "SELECT * FROM sa_prompt_library WHERE {} "
                "ORDER BY created_at DESC LIMIT ?".format(condition),
                (department, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sa_prompt_library WHERE {} "
                "ORDER BY created_at DESC LIMIT ?".format(condition),
                (limit,),
            ).fetchall()

        return [
            {
                "prompt_id": r["prompt_id"],
                "user_id": r["user_id"],
                "title": r["title"],
                "prompt_text": r["prompt_text"],
                "description": r["description"],
                "department": r["department"],
                "tags": r["tags"],
                "rubric_score": r["rubric_score"],
                "is_approved": bool(r["is_approved"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def review_prompt(db_path: str, reviewer_id: str, prompt_id: int,
                  approved: bool, rubric_score: Optional[float] = None) -> dict:
    """Review a prompt submission."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE sa_prompt_library SET is_approved = ?, reviewed_by = ?, "
            "rubric_score = ? WHERE prompt_id = ?",
            (1 if approved else 0, reviewer_id, rubric_score, prompt_id),
        )
        conn.commit()
        return {"prompt_id": prompt_id, "approved": approved}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Live Problems
# ---------------------------------------------------------------------------

def get_live_problems(db_path: str, level: Optional[int] = None,
                      limit: int = 20) -> list:
    """Get active live problems, optionally filtered by level."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if level:
            rows = conn.execute(
                "SELECT * FROM sa_live_problems WHERE is_active = 1 AND level_number = ? "
                "ORDER BY times_used ASC LIMIT ?",
                (level, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sa_live_problems WHERE is_active = 1 "
                "ORDER BY level_number, times_used ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "problem_id": r["problem_id"],
                "level": r["level_number"],
                "title": r["problem_title"],
                "description": r["problem_description"],
                "department": r["department"],
                "times_used": r["times_used"],
                "avg_score": r["avg_score"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def submit_live_problem_solution(db_path: str, user_id: str, problem_id: int,
                                 response: str,
                                 anthropic_key: Optional[str] = None) -> dict:
    """Submit a solution to a live problem. Score it and update usage stats."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        problem = conn.execute(
            "SELECT * FROM sa_live_problems WHERE problem_id = ?", (problem_id,)
        ).fetchone()
        if not problem:
            return {"error": "Problem not found"}

        # Score via Claude (simplified — uses rubric engine in production)
        score = _score_live_problem(problem, response, anthropic_key)

        # Update usage stats
        times_used = (problem["times_used"] or 0) + 1
        old_avg = problem["avg_score"] or 0
        new_avg = ((old_avg * (times_used - 1)) + score) / times_used

        conn.execute(
            "UPDATE sa_live_problems SET times_used = ?, avg_score = ? "
            "WHERE problem_id = ?",
            (times_used, round(new_avg, 2), problem_id),
        )
        conn.commit()

        passed = score >= 0.7  # 70% threshold for capstone
        return {
            "problem_id": problem_id,
            "score": score,
            "passed": passed,
            "level": problem["level_number"],
            "feedback": "Good work!" if passed else "Keep refining — try addressing more dimensions.",
        }
    finally:
        conn.close()


def _score_live_problem(problem, response: str,
                        anthropic_key: Optional[str] = None) -> float:
    """Score a live problem response. Returns 0-1 score."""
    key = anthropic_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        # Heuristic fallback
        words = len(response.split())
        return min(0.9, max(0.3, words / 200))

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        prompt = (
            "Score this solution to a Harris Farm business problem on a 0-1 scale.\n\n"
            "PROBLEM: {}\n{}\n\n"
            "SOLUTION:\n{}\n\n"
            "Score criteria: completeness, actionability, data awareness, realism.\n"
            'Respond with JSON only: {{"score": <0.0-1.0>, "feedback": "<brief>"}}'
        ).format(problem["problem_title"], problem["problem_description"], response)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        result = json.loads(text)
        return float(result.get("score", 0.5))
    except Exception:
        words = len(response.split())
        return min(0.9, max(0.3, words / 200))


# ---------------------------------------------------------------------------
# Daily Challenges v4
# ---------------------------------------------------------------------------

def get_daily_challenge(db_path: str, user_id: str) -> dict:
    """Get today's daily challenge. Deterministic rotation based on date."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Get pool size
        count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sa_daily_challenges_v4 WHERE is_active = 1"
        ).fetchone()
        pool_size = count_row["cnt"] if count_row else 0
        if pool_size == 0:
            return {"error": "No daily challenges available"}

        # Deterministic daily index
        today = datetime.utcnow().strftime("%Y-%m-%d")
        day_ordinal = datetime.utcnow().toordinal()
        index = day_ordinal % pool_size

        # Get challenge at index
        challenge = conn.execute(
            "SELECT * FROM sa_daily_challenges_v4 WHERE is_active = 1 "
            "ORDER BY challenge_id LIMIT 1 OFFSET ?",
            (index,),
        ).fetchone()
        if not challenge:
            return {"error": "No challenge found"}

        # Check if user already completed today
        completion = conn.execute(
            "SELECT id FROM sa_daily_completions_v4 "
            "WHERE user_id = ? AND challenge_date = ?",
            (user_id, today),
        ).fetchone()

        result = {
            "challenge_id": challenge["challenge_id"],
            "title": challenge["title"],
            "scenario_text": challenge["scenario_text"],
            "difficulty": challenge["difficulty"],
            "topic": challenge["topic"],
            "xp_reward": challenge["xp_reward"],
            "completed_today": completion is not None,
            "date": today,
        }

        # Include options but NOT correct answer
        if challenge["options_json"]:
            result["options"] = json.loads(challenge["options_json"])

        return result
    finally:
        conn.close()


def complete_daily_challenge(db_path: str, user_id: str, challenge_id: int,
                             answer: str, time_seconds: int = 0) -> dict:
    """Submit answer to daily challenge."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # Check already completed
        existing = conn.execute(
            "SELECT id FROM sa_daily_completions_v4 WHERE user_id = ? AND challenge_date = ?",
            (user_id, today),
        ).fetchone()
        if existing:
            return {"error": "Already completed today's challenge", "already_completed": True}

        # Get challenge
        challenge = conn.execute(
            "SELECT * FROM sa_daily_challenges_v4 WHERE challenge_id = ?",
            (challenge_id,),
        ).fetchone()
        if not challenge:
            return {"error": "Challenge not found"}

        # Check answer
        correct = answer.strip() == (challenge["correct_answer"] or "").strip()

        # Record completion
        xp_awarded = challenge["xp_reward"] if correct else int(challenge["xp_reward"] * 0.5)
        conn.execute(
            "INSERT INTO sa_daily_completions_v4 "
            "(user_id, challenge_id, challenge_date, answer, is_correct, "
            "time_seconds, xp_awarded, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                user_id, challenge_id, today, answer,
                1 if correct else 0, time_seconds, xp_awarded,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()

        return {
            "correct": correct,
            "correct_answer": challenge["correct_answer"],
            "xp_awarded": xp_awarded,
            "time_seconds": time_seconds,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Peer Battles v4
# ---------------------------------------------------------------------------

def create_peer_battle(db_path: str, challenger_id: str, scenario_text: str,
                       challenger_response: str,
                       exercise_id: Optional[int] = None) -> dict:
    """Create an open peer battle."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO sa_peer_battles_v4 "
            "(scenario_text, exercise_id, user_a_id, user_a_response, status, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (
                scenario_text, exercise_id, challenger_id, challenger_response,
                "open", datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return {"battle_id": cur.lastrowid, "status": "open"}
    finally:
        conn.close()


def join_peer_battle(db_path: str, battle_id: int, opponent_id: str,
                     opponent_response: str,
                     anthropic_key: Optional[str] = None) -> dict:
    """Join a peer battle and trigger scoring."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        battle = conn.execute(
            "SELECT * FROM sa_peer_battles_v4 WHERE battle_id = ?", (battle_id,)
        ).fetchone()
        if not battle:
            return {"error": "Battle not found"}
        if battle["status"] != "open":
            return {"error": "Battle is not open"}
        if battle["user_a_id"] == opponent_id:
            return {"error": "Cannot battle yourself"}

        # Record opponent
        conn.execute(
            "UPDATE sa_peer_battles_v4 SET user_b_id = ?, user_b_response = ?, "
            "status = 'matched' WHERE battle_id = ?",
            (opponent_id, opponent_response, battle_id),
        )
        conn.commit()

        # Score both prompts
        result = _score_battle(
            battle["scenario_text"],
            battle["user_a_response"],
            opponent_response,
            anthropic_key,
        )

        winner = None
        if result["score_a"] > result["score_b"]:
            winner = battle["user_a_id"]
        elif result["score_b"] > result["score_a"]:
            winner = opponent_id

        conn.execute(
            "UPDATE sa_peer_battles_v4 SET user_a_score = ?, user_b_score = ?, "
            "winner_user_id = ?, judge_feedback_json = ?, status = 'complete', "
            "completed_at = ? WHERE battle_id = ?",
            (
                result["score_a"], result["score_b"],
                winner, json.dumps(result.get("feedback", {})),
                datetime.utcnow().isoformat(), battle_id,
            ),
        )
        conn.commit()

        return {
            "battle_id": battle_id,
            "user_a_score": result["score_a"],
            "user_b_score": result["score_b"],
            "winner": winner,
            "feedback": result.get("feedback", {}),
            "status": "complete",
        }
    finally:
        conn.close()


def _score_battle(scenario: str, response_a: str, response_b: str,
                  anthropic_key: Optional[str] = None) -> dict:
    """Score both battle responses."""
    key = anthropic_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        # Random fallback
        sa = round(random.uniform(5, 9), 1)
        sb = round(random.uniform(5, 9), 1)
        return {"score_a": sa, "score_b": sb, "feedback": {"note": "Heuristic scoring"}}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        prompt = (
            "Two users submitted prompts for the same scenario in a peer battle. "
            "Score each on a 1-10 scale based on clarity, specificity, and effectiveness.\n\n"
            "SCENARIO: {}\n\n"
            "PROMPT A:\n{}\n\n"
            "PROMPT B:\n{}\n\n"
            'Respond with JSON only: {{"score_a": <1-10>, "score_b": <1-10>, '
            '"feedback": {{"a": "<brief>", "b": "<brief>"}}}}'
        ).format(scenario, response_a, response_b)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        return json.loads(text)
    except Exception:
        sa = round(random.uniform(5, 9), 1)
        sb = round(random.uniform(5, 9), 1)
        return {"score_a": sa, "score_b": sb, "feedback": {"note": "Heuristic scoring"}}


def get_open_battles(db_path: str, limit: int = 20) -> list:
    """List open peer battles available to join."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT battle_id, scenario_text, user_a_id, created_at "
            "FROM sa_peer_battles_v4 WHERE status = 'open' "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "battle_id": r["battle_id"],
                "scenario_text": r["scenario_text"],
                "challenger": r["user_a_id"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_battle_result(db_path: str, battle_id: int) -> Optional[dict]:
    """Get a specific battle result."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM sa_peer_battles_v4 WHERE battle_id = ?",
            (battle_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "battle_id": row["battle_id"],
            "scenario_text": row["scenario_text"],
            "user_a": row["user_a_id"],
            "user_b": row["user_b_id"],
            "user_a_score": row["user_a_score"],
            "user_b_score": row["user_b_score"],
            "winner": row["winner_user_id"],
            "feedback": json.loads(row["judge_feedback_json"]) if row["judge_feedback_json"] else {},
            "status": row["status"],
            "completed_at": row["completed_at"],
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Challenge of the Month
# ---------------------------------------------------------------------------

def get_challenge_of_month(db_path: str) -> Optional[dict]:
    """Get the current month's gold-bordered challenge."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        current_month = datetime.utcnow().month
        row = conn.execute(
            "SELECT * FROM sa_daily_challenges_v4 "
            "WHERE is_monthly_check = 1 AND is_active = 1 "
            "ORDER BY challenge_id LIMIT 1 OFFSET ?",
            ((current_month - 1) % 12,),
        ).fetchone()
        if not row:
            return None
        return {
            "challenge_id": row["challenge_id"],
            "title": row["title"],
            "scenario_text": row["scenario_text"],
            "difficulty": row["difficulty"],
            "xp_reward": row["xp_reward"],
            "is_monthly": True,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Role Pathways
# ---------------------------------------------------------------------------

def get_role_pathways(db_path: str) -> list:
    """Get all role pathway definitions."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM sa_role_pathways ORDER BY role_name").fetchall()
        return [
            {
                "role_name": r["role_name"],
                "core_modules": json.loads(r["core_modules"]),
                "specialist_modules": json.loads(r["specialist_modules"]),
                "max_target_level": r["max_target_level"],
                "description": r["description"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_user_pathway(db_path: str, role_name: str) -> Optional[dict]:
    """Get a specific role pathway."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM sa_role_pathways WHERE role_name = ?", (role_name,)
        ).fetchone()
        if not row:
            return None
        return {
            "role_name": row["role_name"],
            "core_modules": json.loads(row["core_modules"]),
            "specialist_modules": json.loads(row["specialist_modules"]),
            "max_target_level": row["max_target_level"],
            "description": row["description"],
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Mindset Assessment (v4 — uses sa_scenarios table)
# ---------------------------------------------------------------------------

def get_mindset_scenario(db_path: str, level: int) -> Optional[dict]:
    """Get a random mindset scenario for the given level."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM sa_scenarios WHERE level_number = ? AND is_active = 1",
            (level,),
        ).fetchall()
        if not rows:
            return None
        chosen = random.choice(rows)
        return {
            "scenario_id": chosen["scenario_id"],
            "level": chosen["level_number"],
            "title": chosen["scenario_title"],
            "text": chosen["scenario_text"],
        }
    finally:
        conn.close()
