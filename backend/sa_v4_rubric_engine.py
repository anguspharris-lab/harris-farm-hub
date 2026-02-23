"""
Skills Academy v4 — Rubric Evaluation Engine
3 rubrics (foundational / advanced_output / multi_tier_panel),
Claude API scoring, evaluation persistence.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Rubric helpers
# ---------------------------------------------------------------------------

def get_rubric(db_path: str, rubric_code: str) -> Optional[dict]:
    """Load a rubric definition from the DB."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM sa_rubrics WHERE rubric_code = ?", (rubric_code,)
        ).fetchone()
        if not row:
            return None
        return {
            "rubric_id": row["rubric_id"],
            "rubric_code": row["rubric_code"],
            "rubric_name": row["rubric_name"],
            "description": row["description"],
            "applicable_levels": json.loads(row["applicable_levels"]),
            "criteria": json.loads(row["criteria_json"]),
            "pass_threshold": row["pass_threshold"],
        }
    finally:
        conn.close()


def get_all_rubrics(db_path: str) -> list:
    """Return all rubric definitions."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM sa_rubrics ORDER BY rubric_id").fetchall()
        return [
            {
                "rubric_id": r["rubric_id"],
                "rubric_code": r["rubric_code"],
                "rubric_name": r["rubric_name"],
                "description": r["description"],
                "applicable_levels": json.loads(r["applicable_levels"]),
                "criteria": json.loads(r["criteria_json"]),
                "pass_threshold": r["pass_threshold"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_rubric_for_level(level: int) -> str:
    """Map a level number to the appropriate rubric code."""
    if level <= 2:
        return "foundational"
    elif level <= 4:
        return "advanced_output"
    else:
        return "multi_tier_panel"


def get_rubric_for_module(module_code: str) -> str:
    """Map module code to rubric code based on the level convention."""
    # L1/L2/D1 → foundational, L3/L4/D2/D3 → advanced, L5/D4 → panel
    code = module_code.upper()
    if code in ("L1", "L2", "D1"):
        return "foundational"
    elif code in ("L3", "L4", "D2", "D3"):
        return "advanced_output"
    else:
        return "multi_tier_panel"


# ---------------------------------------------------------------------------
# Claude scoring prompts
# ---------------------------------------------------------------------------

_FOUNDATIONAL_PROMPT = """You are an expert AI prompt evaluator for Harris Farm Markets.

Score this prompt on the Foundational Prompt Rubric (4 criteria, each 1-5):

1. **Task** (1-5): Is there a clear, specific verb phrase defining what AI should do?
   - 1: No task / "tell me about..."
   - 3: Has a verb but vague scope ("analyse sales")
   - 5: Precise verb + specific scope + measurable outcome

2. **Context** (1-5): Does the prompt provide relevant background?
   - 1: No context at all
   - 3: Some context but missing key info (role, audience, data available)
   - 5: Full context: role, audience, data sources, relevant constraints

3. **Format** (1-5): Is the desired output structure specified?
   - 1: No format guidance
   - 3: Basic format ("give me a table")
   - 5: Detailed structure (columns, grouping, summary sections, length)

4. **Constraints** (1-5): Are boundaries and guardrails set?
   - 1: No constraints
   - 3: Basic constraints (length or tone)
   - 5: Specific constraints: time range, exclusions, accuracy rules, scope limits

{exercise_context}

USER'S PROMPT:
{user_response}

Respond ONLY with valid JSON:
{{
  "scores": {{
    "Task": <1-5>,
    "Context": <1-5>,
    "Format": <1-5>,
    "Constraints": <1-5>
  }},
  "total_score": <sum of all scores>,
  "max_score": 20,
  "percentage": <total/20>,
  "feedback": "<2-3 sentences of specific, constructive feedback>",
  "improved_prompt": "<show what a 5/5 version would look like>"
}}"""


_ADVANCED_OUTPUT_PROMPT = """You are an expert output evaluator for Harris Farm Markets.

Score this output/prompt on the Advanced Output Rubric (8 criteria, each 1-10):

1. **Audience** (1-10): Is the output tailored to the specific audience?
2. **Storytelling** (1-10): Does it tell a clear narrative from data to insight?
3. **Actionability** (1-10): Does it lead to specific, concrete actions?
4. **Visual Quality** (1-10): Is the format/presentation clear and scannable?
5. **Completeness** (1-10): Does it address all aspects of the question?
6. **Brevity** (1-10): Is it concise without sacrificing clarity?
7. **Data Integrity** (1-10): Are numbers accurate, sourced, and contextualised?
8. **Honesty** (1-10): Does it flag limitations, uncertainties, and caveats?

The 8+ Rule: The weighted average must be 8.0+ to pass.

{exercise_context}

USER'S RESPONSE:
{user_response}

Respond ONLY with valid JSON:
{{
  "scores": {{
    "Audience": <1-10>,
    "Storytelling": <1-10>,
    "Actionability": <1-10>,
    "Visual Quality": <1-10>,
    "Completeness": <1-10>,
    "Brevity": <1-10>,
    "Data Integrity": <1-10>,
    "Honesty": <1-10>
  }},
  "total_score": <weighted sum>,
  "max_score": 10.0,
  "percentage": <weighted average / 10>,
  "feedback": "<2-3 sentences of specific, constructive feedback>",
  "improved_version": "<show what an 8+ version would look like>"
}}"""


_PANEL_PROMPT = """You are a multi-tier expert panel evaluating a strategic deliverable for Harris Farm Markets.

Score on the Multi-Tier Panel Rubric (5 tiers, each 1-10):

1. **T1: CTO Panel** (1-10): Technical feasibility, architecture quality, scalability
2. **T2: CLO Panel** (1-10): Legal compliance, data governance, risk management
3. **T3: Strategic Alignment** (1-10): Alignment with Harris Farm strategy (Fewer Bigger Better, Vision 2030, For The Greater Goodness)
4. **T4: Implementation** (1-10): Practical deployment plan, timeline, resource needs
5. **T5: Presentation** (1-10): Communication quality, stakeholder clarity, persuasiveness

Pass: 8/10 per tier.

{exercise_context}

USER'S RESPONSE:
{user_response}

Respond ONLY with valid JSON:
{{
  "scores": {{
    "T1: CTO Panel": <1-10>,
    "T2: CLO Panel": <1-10>,
    "T3: Strategic Alignment": <1-10>,
    "T4: Implementation": <1-10>,
    "T5: Presentation": <1-10>
  }},
  "total_score": <average>,
  "max_score": 10.0,
  "percentage": <average / 10>,
  "feedback": "<2-3 sentences of specific feedback per tier that scored below 8>",
  "improvement_areas": ["<area1>", "<area2>"]
}}"""


_CURVEBALL_PROMPT = """You are evaluating a curveball response in the Harris Farm AI Skills Academy.

This was a CURVEBALL exercise — a tricky scenario with an unexpected twist.
Score the user's response on a 1-5 scale:

1 = Completely missed the twist / gave a naive or dangerous answer
2 = Partially recognised something was off but didn't address it
3 = Identified the issue but response was incomplete or superficial
4 = Good identification and handling of the twist with minor gaps
5 = Excellent — fully recognised and addressed the twist with nuance

The twist: {curveball_type}
Expected approach: {expected_approach}

SCENARIO:
{scenario_text}

USER'S RESPONSE:
{user_response}

Respond ONLY with valid JSON:
{{
  "curveball_score": <1-5>,
  "identified_twist": <true/false>,
  "feedback": "<2-3 sentences explaining what they did well and what they missed>",
  "coaching": "<1-2 sentences of supportive coaching if score < 3.5>"
}}"""


_RUBRIC_PROMPTS = {
    "foundational": _FOUNDATIONAL_PROMPT,
    "advanced_output": _ADVANCED_OUTPUT_PROMPT,
    "multi_tier_panel": _PANEL_PROMPT,
}


def build_scoring_prompt(rubric_code: str, exercise_context: str,
                         user_response: str) -> str:
    """Assemble the Claude API prompt for a given rubric."""
    template = _RUBRIC_PROMPTS.get(rubric_code, _FOUNDATIONAL_PROMPT)
    return template.format(
        exercise_context=exercise_context,
        user_response=user_response,
    )


def build_curveball_prompt(curveball_type: str, expected_approach: str,
                           scenario_text: str, user_response: str) -> str:
    """Assemble Claude prompt for curveball scoring."""
    return _CURVEBALL_PROMPT.format(
        curveball_type=curveball_type,
        expected_approach=expected_approach,
        scenario_text=scenario_text,
        user_response=user_response,
    )


# ---------------------------------------------------------------------------
# Claude API call
# ---------------------------------------------------------------------------

def _call_claude(prompt: str, anthropic_key: Optional[str] = None) -> dict:
    """Call Claude API for scoring. Returns parsed JSON dict."""
    key = anthropic_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        return {"error": "No ANTHROPIC_API_KEY configured"}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "Failed to parse Claude response", "raw": text}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Evaluate + persist
# ---------------------------------------------------------------------------

def evaluate_exercise(db_path: str, user_id: str, exercise_id: int,
                      user_response: str,
                      anthropic_key: Optional[str] = None) -> dict:
    """Score a user's exercise response via Claude and persist the evaluation.
    Returns the evaluation result dict."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Load exercise
        ex = conn.execute(
            "SELECT e.*, m.module_code FROM sa_exercises e "
            "JOIN sa_modules m ON e.module_id = m.module_id "
            "WHERE e.exercise_id = ?", (exercise_id,)
        ).fetchone()
        if not ex:
            return {"error": "Exercise not found"}

        rubric_code = ex["rubric_code"]
        is_curveball = bool(ex["is_curveball"])

        if is_curveball:
            prompt = build_curveball_prompt(
                curveball_type=ex["curveball_type"] or "unknown",
                expected_approach=ex["expected_approach"] or "",
                scenario_text=ex["scenario_text"],
                user_response=user_response,
            )
        else:
            exercise_context = "Exercise: {}\n\nScenario: {}".format(
                ex["exercise_title"], ex["scenario_text"]
            )
            if ex["expected_approach"]:
                exercise_context += "\n\nExpected approach: {}".format(ex["expected_approach"])
            prompt = build_scoring_prompt(rubric_code, exercise_context, user_response)

        # Call Claude
        result = _call_claude(prompt, anthropic_key)
        if "error" in result:
            return result

        # Calculate pass/fail
        if is_curveball:
            curveball_score = float(result.get("curveball_score", 0))
            passed = curveball_score >= ex["pass_score"]
            total_score = curveball_score
            scores_json = json.dumps({"curveball_score": curveball_score})
        else:
            scores = result.get("scores", {})
            percentage = float(result.get("percentage", 0))
            total_score = float(result.get("total_score", 0))
            passed = percentage >= ex["pass_score"]
            scores_json = json.dumps(scores)

        # Persist to sa_exercise_results
        conn.execute(
            "INSERT INTO sa_exercise_results "
            "(user_id, exercise_id, user_response, scores_json, total_score, passed, "
            "ai_feedback, is_curveball_result, curveball_score, context_tag, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                user_id, exercise_id, user_response, scores_json,
                total_score, 1 if passed else 0,
                result.get("feedback", result.get("coaching", "")),
                1 if is_curveball else 0,
                result.get("curveball_score") if is_curveball else None,
                ex["context_tag"],
                datetime.utcnow().isoformat(),
            ),
        )

        # Also persist to sa_rubric_evaluations if not a curveball
        evaluation_id = None
        if not is_curveball:
            rubric_row = conn.execute(
                "SELECT rubric_id FROM sa_rubrics WHERE rubric_code = ?",
                (rubric_code,)
            ).fetchone()
            if rubric_row:
                cur = conn.execute(
                    "INSERT INTO sa_rubric_evaluations "
                    "(user_id, rubric_id, module_id, exercise_id, prompt_text, "
                    "scores_json, total_score, passed, ai_feedback, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (
                        user_id, rubric_row["rubric_id"], ex["module_id"],
                        exercise_id, user_response, scores_json,
                        total_score, 1 if passed else 0,
                        result.get("feedback", ""),
                        datetime.utcnow().isoformat(),
                    ),
                )
                evaluation_id = cur.lastrowid

        conn.commit()

        return {
            "exercise_id": exercise_id,
            "rubric_code": rubric_code,
            "is_curveball": is_curveball,
            "scores": result.get("scores", {}),
            "total_score": total_score,
            "percentage": float(result.get("percentage", 0)),
            "passed": passed,
            "feedback": result.get("feedback", result.get("coaching", "")),
            "improved_prompt": result.get("improved_prompt", result.get("improved_version", "")),
            "curveball_score": result.get("curveball_score"),
            "identified_twist": result.get("identified_twist"),
            "evaluation_id": evaluation_id,
        }
    finally:
        conn.close()


def get_evaluation(db_path: str, evaluation_id: int) -> Optional[dict]:
    """Retrieve a specific rubric evaluation."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT e.*, r.rubric_code, r.rubric_name "
            "FROM sa_rubric_evaluations e "
            "JOIN sa_rubrics r ON e.rubric_id = r.rubric_id "
            "WHERE e.evaluation_id = ?", (evaluation_id,)
        ).fetchone()
        if not row:
            return None
        return {
            "evaluation_id": row["evaluation_id"],
            "user_id": row["user_id"],
            "rubric_code": row["rubric_code"],
            "rubric_name": row["rubric_name"],
            "scores": json.loads(row["scores_json"]),
            "total_score": row["total_score"],
            "passed": bool(row["passed"]),
            "feedback": row["ai_feedback"],
            "created_at": row["created_at"],
        }
    finally:
        conn.close()


def get_user_evaluations(db_path: str, user_id: str,
                         module_code: Optional[str] = None,
                         limit: int = 50) -> list:
    """Get evaluation history for a user, optionally filtered by module."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if module_code:
            rows = conn.execute(
                "SELECT e.*, r.rubric_code, r.rubric_name, m.module_code "
                "FROM sa_rubric_evaluations e "
                "JOIN sa_rubrics r ON e.rubric_id = r.rubric_id "
                "LEFT JOIN sa_modules m ON e.module_id = m.module_id "
                "WHERE e.user_id = ? AND m.module_code = ? "
                "ORDER BY e.created_at DESC LIMIT ?",
                (user_id, module_code, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT e.*, r.rubric_code, r.rubric_name, m.module_code "
                "FROM sa_rubric_evaluations e "
                "JOIN sa_rubrics r ON e.rubric_id = r.rubric_id "
                "LEFT JOIN sa_modules m ON e.module_id = m.module_id "
                "WHERE e.user_id = ? "
                "ORDER BY e.created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [
            {
                "evaluation_id": r["evaluation_id"],
                "rubric_code": r["rubric_code"],
                "rubric_name": r["rubric_name"],
                "module_code": r["module_code"],
                "scores": json.loads(r["scores_json"]),
                "total_score": r["total_score"],
                "passed": bool(r["passed"]),
                "feedback": r["ai_feedback"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()
