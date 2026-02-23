"""
Skills Academy v4 — Placement Challenge Engine
5 scenarios -> provisional level assignment + verification status init.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Placement scenarios (5 escalating challenges)
# ---------------------------------------------------------------------------

PLACEMENT_SCENARIOS = [
    {
        "id": 1,
        "name": "Recognition",
        "time_seconds": 60,
        "max_score": 5,
        "type": "multiple_choice",
        "instruction": "A store manager asks you to find out why fresh produce sales dropped last week. Which is the best way to start with AI?",
        "options": [
            {"label": "A", "text": "Tell me about produce sales", "signal": "L1", "score": 1},
            {"label": "B", "text": "Analyse the weekly fresh produce sales decline at Bondi Beach for the week ending 16 Feb vs the prior 4-week average", "signal": "L2", "score": 3},
            {"label": "C", "text": "Compare fresh produce sales decline across all stores, cross-reference with delivery data, weather, and competitor promotions. Identify the 3 most likely causes and recommend actions.", "signal": "L3+", "score": 4},
            {"label": "D", "text": "I'd build a system that automatically detects sales anomalies daily, diagnoses probable causes, and alerts the relevant manager before they notice.", "signal": "L5", "score": 5},
        ],
    },
    {
        "id": 2,
        "name": "Construction",
        "time_seconds": 60,
        "max_score": 5,
        "type": "free_text",
        "instruction": "Write a prompt to help a Harris Farm buyer decide which dairy products to delist.",
        "scoring_criteria": "Score 1-5 based on: (1) Clear specific task verb, (2) Role/business context provided, (3) Data sources or metrics specified, (4) Output format defined, (5) Constraints/guardrails set. Award 1 point per element clearly present.",
    },
    {
        "id": 3,
        "name": "Iteration",
        "time_seconds": 60,
        "max_score": 5,
        "type": "free_text",
        "instruction": "This prompt scored 5/10. Make it score 8+.",
        "original_prompt": "Look at our top selling products and tell me which ones we should promote more.",
        "original_output": "Here are your top products by revenue: 1. Bananas 2. Avocados 3. Milk 4. Bread 5. Eggs. You could promote these more by putting them on special or advertising them.",
        "scoring_criteria": "Score 1-5: (1) Identifies specific weaknesses in original, (2) Adds measurable metrics and time period, (3) Specifies store/department scope, (4) Requests structured analysis not just a list, (5) Includes actionable format with decision criteria.",
    },
    {
        "id": 4,
        "name": "Scope",
        "time_seconds": 60,
        "max_score": 5,
        "type": "free_text",
        "instruction": "Harris Farm wants to reduce food waste by 30% across all stores. You have AI, all our data, and no constraints. What would you build?",
        "scoring_criteria": "Score on 4 mindset indicators (1.25 each): First Instinct (thinks AI-first?), Scope (whole system vs one step?), Ambition (incremental vs transformative?), Breadth (one technique vs multiple capabilities?). Total 0-5.",
    },
    {
        "id": 5,
        "name": "Application",
        "time_seconds": 60,
        "max_score": 5,
        "type": "free_text",
        "instruction": "Describe one process in your current role that AI could transform. Not just speed up -- fundamentally change.",
        "scoring_criteria": "Score 1-5: (1) Identifies a real process, (2) Explains current pain points, (3) Describes AI-powered alternative, (4) Shows transformation not just automation, (5) Considers implementation and scale.",
    },
]

# Level bands (score -> starting level)
LEVEL_BANDS = [
    (0, 8, 1),    # Score 0-8 -> Level 1 (Seed) Provisional
    (9, 14, 2),   # Score 9-14 -> Level 2 (Sprout) Provisional
    (15, 19, 3),  # Score 15-19 -> Level 3 (Growing) Provisional
    (20, 23, 4),  # Score 20-23 -> Level 4 (Harvest) Provisional
    (24, 25, 5),  # Score 24-25 -> Level 5 (Canopy) Provisional
]

LEVEL_LABELS = {
    1: "Seed",
    2: "Sprout",
    3: "Growing",
    4: "Harvest",
    5: "Canopy",
    6: "Root System",
}


def score_to_level(total_score: int) -> int:
    """Map total placement score (0-25) to starting level."""
    for low, high, level in LEVEL_BANDS:
        if low <= total_score <= high:
            return level
    return 1


# ---------------------------------------------------------------------------
# HiPo flag detection from placement
# ---------------------------------------------------------------------------

def detect_hipo_flags(responses: list) -> list:
    """Detect initial HiPo flags from placement responses.
    Returns list of flag strings visible to admin only."""
    flags = []
    total_time = sum(r.get("time_seconds", 60) for r in responses)

    for r in responses:
        sid = r.get("scenario_id", 0)
        score = r.get("score", 0)

        # Challenge 4 score >= 4/5 -> "Scale Thinker"
        if sid == 4 and score >= 4:
            flags.append("scale_thinker")

        # Challenge 5 describes process transformation -> "Process Reimaginer"
        if sid == 5 and score >= 4:
            flags.append("process_reimaginer")

    # All 5 completed in < 3 min with high scores -> "Accelerated Learner"
    total_score = sum(r.get("score", 0) for r in responses)
    if total_time < 180 and total_score >= 20:
        flags.append("accelerated_learner")

    return flags


# ---------------------------------------------------------------------------
# Scoring prompt for free-text challenges
# ---------------------------------------------------------------------------

def get_scoring_prompt(scenario: dict, user_response: str) -> str:
    """Build Claude prompt for scoring a free-text placement response."""
    parts = [
        "You are evaluating a placement challenge response for the Harris Farm AI Skills Academy.",
        "",
        "CHALLENGE: {}".format(scenario["name"]),
        "INSTRUCTION: {}".format(scenario["instruction"]),
    ]
    if scenario.get("original_prompt"):
        parts.append("ORIGINAL PROMPT SHOWN: {}".format(scenario["original_prompt"]))
    if scenario.get("original_output"):
        parts.append("ORIGINAL OUTPUT SHOWN: {}".format(scenario["original_output"]))
    parts.extend([
        "",
        "SCORING CRITERIA: {}".format(scenario["scoring_criteria"]),
        "",
        "USER'S RESPONSE:",
        user_response,
        "",
        'Respond ONLY with valid JSON: {{"score": <0-5>, "reasoning": "<brief explanation>"}}',
    ])
    return "\n".join(parts)


def score_free_text(scenario: dict, user_response: str,
                    anthropic_key: Optional[str] = None) -> dict:
    """Score a free-text placement response via Claude."""
    key = anthropic_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        # Fallback: basic heuristic scoring
        word_count = len(user_response.split())
        if word_count < 10:
            return {"score": 1, "reasoning": "Response too brief"}
        elif word_count < 30:
            return {"score": 2, "reasoning": "Basic response"}
        elif word_count < 60:
            return {"score": 3, "reasoning": "Moderate detail"}
        elif word_count < 100:
            return {"score": 4, "reasoning": "Good detail and structure"}
        else:
            return {"score": 4, "reasoning": "Detailed response"}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        prompt = get_scoring_prompt(scenario, user_response)
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
        score = max(0, min(5, int(result.get("score", 0))))
        return {"score": score, "reasoning": result.get("reasoning", "")}
    except Exception as e:
        # Fallback to heuristic
        word_count = len(user_response.split())
        score = min(4, max(1, word_count // 25))
        return {"score": score, "reasoning": "Scored by heuristic (API error: {})".format(str(e)[:50])}


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------

def get_scenarios() -> list:
    """Return the 5 placement scenario definitions (no answers/scoring info)."""
    safe = []
    for s in PLACEMENT_SCENARIOS:
        entry = {
            "id": s["id"],
            "name": s["name"],
            "time_seconds": s["time_seconds"],
            "max_score": s["max_score"],
            "type": s["type"],
            "instruction": s["instruction"],
        }
        if s["type"] == "multiple_choice":
            # Include options but not scores
            entry["options"] = [
                {"label": o["label"], "text": o["text"]}
                for o in s["options"]
            ]
        if s.get("original_prompt"):
            entry["original_prompt"] = s["original_prompt"]
        if s.get("original_output"):
            entry["original_output"] = s["original_output"]
        safe.append(entry)
    return safe


def get_result(db_path: str, user_id: str) -> Optional[dict]:
    """Get a user's placement result, or None if not placed."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM sa_placement_v4 WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row:
            return None
        return {
            "user_id": row["user_id"],
            "challenge_scores": json.loads(row["challenge_scores_json"]),
            "total_score": row["total_score"],
            "placed_level": row["placed_level"],
            "level_name": LEVEL_LABELS.get(row["placed_level"], "Unknown"),
            "hipo_flags": json.loads(row["hipo_flags_json"]) if row["hipo_flags_json"] else [],
            "completed_at": row["completed_at"],
        }
    finally:
        conn.close()


def has_completed(db_path: str, user_id: str) -> bool:
    """Quick check if user has completed placement."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM sa_placement_v4 WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def submit_placement(db_path: str, user_id: str, responses: list,
                     anthropic_key: Optional[str] = None) -> dict:
    """Process all 5 placement responses, assign level, create verification status.

    responses: list of dicts with {scenario_id, response, time_seconds}
    For MC: response is the selected label (A/B/C/D)
    For free text: response is the text
    """
    scored_responses = []

    for resp in responses:
        sid = resp.get("scenario_id", 0)
        scenario = None
        for s in PLACEMENT_SCENARIOS:
            if s["id"] == sid:
                scenario = s
                break
        if not scenario:
            scored_responses.append({
                "scenario_id": sid, "score": 0,
                "reasoning": "Unknown scenario", "time_seconds": resp.get("time_seconds", 0),
            })
            continue

        if scenario["type"] == "multiple_choice":
            # Score MC by matching option label
            user_label = resp.get("response", "").strip().upper()
            score = 0
            for opt in scenario["options"]:
                if opt["label"] == user_label:
                    score = opt["score"]
                    break
            scored_responses.append({
                "scenario_id": sid, "score": score,
                "reasoning": "Selected option {}".format(user_label),
                "time_seconds": resp.get("time_seconds", 0),
            })
        else:
            # Score free text via Claude
            result = score_free_text(scenario, resp.get("response", ""), anthropic_key)
            scored_responses.append({
                "scenario_id": sid,
                "score": result["score"],
                "reasoning": result["reasoning"],
                "time_seconds": resp.get("time_seconds", 0),
                "response_text": resp.get("response", "")[:500],
            })

    total_score = sum(r["score"] for r in scored_responses)
    placed_level = score_to_level(total_score)
    hipo_flags = detect_hipo_flags(scored_responses)

    # Persist placement
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO sa_placement_v4 "
            "(user_id, challenge_scores_json, total_score, placed_level, "
            "hipo_flags_json, completed_at) VALUES (?,?,?,?,?,?)",
            (
                user_id,
                json.dumps(scored_responses),
                total_score,
                placed_level,
                json.dumps(hipo_flags),
                datetime.utcnow().isoformat(),
            ),
        )

        # Create initial verification status (Provisional)
        conn.execute(
            "INSERT OR IGNORE INTO sa_verification_status "
            "(user_id, level_number, level_status, foundation_score, breadth_count, "
            "depth_count, application_passed, last_activity_at, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                user_id, placed_level, "provisional",
                0.0, 0, 0, 0,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
            ),
        )

        # Create initial XP record
        conn.execute(
            "INSERT OR IGNORE INTO sa_user_xp "
            "(user_id, total_xp, current_level, weekly_xp, monthly_xp, "
            "streak_days, streak_multiplier, last_active_date, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                user_id, 0, placed_level, 0, 0,
                0, 1.0,
                datetime.utcnow().strftime("%Y-%m-%d"),
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()

        return {
            "user_id": user_id,
            "total_score": total_score,
            "placed_level": placed_level,
            "level_name": LEVEL_LABELS.get(placed_level, "Unknown"),
            "hipo_flags": hipo_flags,
            "responses": scored_responses,
            "status": "provisional",
        }
    finally:
        conn.close()


def reset_placement(db_path: str, user_id: str) -> bool:
    """Admin: delete a user's placement so they can retake it."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM sa_placement_v4 WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM sa_verification_status WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM sa_user_xp WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def get_summary(db_path: str) -> dict:
    """Admin: aggregate placement stats."""
    conn = sqlite3.connect(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM sa_placement_v4").fetchone()[0]
        avg = conn.execute("SELECT AVG(total_score) FROM sa_placement_v4").fetchone()[0]
        levels = {}
        for row in conn.execute(
            "SELECT placed_level, COUNT(*) as cnt FROM sa_placement_v4 GROUP BY placed_level"
        ).fetchall():
            levels[row[0]] = row[1]
        return {
            "total_placed": total,
            "avg_score": round(avg, 1) if avg else 0,
            "level_distribution": levels,
        }
    finally:
        conn.close()
