"""
Harris Farm Hub — Presentation Rubric Engine
Scores analysis reports against 8 quality dimensions.

Grades:
  Board-ready: avg >= 9.0
  Reviewed:    avg >= 7.0
  Draft:       avg < 7.0
"""


# ---------------------------------------------------------------------------
# DIMENSION SCORERS
# ---------------------------------------------------------------------------

def _score_audience(result):
    """Does the report have a clear, concise executive summary?"""
    summary = result.get("executive_summary", "")
    if not summary:
        return 0, "No executive summary"

    score = 2  # Base for having a summary
    length = len(summary)

    if length <= 500:
        score += 3  # Concise
    elif length <= 800:
        score += 2
    elif length <= 1200:
        score += 1
    # else too verbose, no bonus

    # Contains key numbers?
    if "$" in summary or "%" in summary:
        score += 2  # Quantified
    if any(w in summary.lower() for w in ["found", "identified", "analysed", "analyzed"]):
        score += 1  # Active voice
    if any(w in summary.lower() for w in ["recommend", "suggest", "should", "action"]):
        score += 1  # Actionable

    return min(score, 10), "Summary: {} chars".format(length)


def _score_story(result):
    """Does the report have narrative flow: situation -> findings -> impact -> action?"""
    score = 0
    parts = []

    if result.get("executive_summary"):
        score += 2
        parts.append("situation")
    if result.get("findings"):
        score += 2
        parts.append("findings")
    if result.get("evidence_tables"):
        score += 2
        parts.append("evidence")
    if result.get("financial_impact", {}).get("estimated_annual_value"):
        score += 2
        parts.append("impact")
    if result.get("recommendations"):
        score += 2
        parts.append("action")

    return min(score, 10), "Flow: {}".format(" -> ".join(parts))


def _score_action(result):
    """Do recommendations have owner, timeline, and priority?"""
    recs = result.get("recommendations", [])
    if not recs:
        return 0, "No recommendations"

    total_fields = 0
    max_fields = len(recs) * 3  # owner + timeline + priority per rec

    for r in recs:
        if r.get("owner"):
            total_fields += 1
        if r.get("timeline"):
            total_fields += 1
        if r.get("priority"):
            total_fields += 1

    if max_fields == 0:
        return 0, "No recommendation fields"

    pct = total_fields / max_fields
    count_bonus = min(len(recs), 3) / 3  # up to 1.0 bonus for 3+ recs
    score = round(pct * 8 + count_bonus * 2)

    return min(score, 10), "{}/{} fields across {} recs".format(
        total_fields, max_fields, len(recs))


def _score_visual(result):
    """Are evidence tables present with actual data rows?"""
    tables = result.get("evidence_tables", [])
    if not tables:
        return 0, "No evidence tables"

    total_rows = sum(len(t.get("rows", [])) for t in tables)
    has_columns = all(t.get("columns") for t in tables)

    score = 1  # Base for having tables
    if has_columns:
        score += 2
    if total_rows >= 5:
        score += 2
    elif total_rows >= 1:
        score += 1
    if total_rows >= 10:
        score += 1
    if len(tables) >= 2:
        score += 1  # Multiple evidence tables
    if total_rows >= 20:
        score += 1
    if has_columns and all(len(t.get("columns", [])) >= 3 for t in tables):
        score += 1  # Rich column structure

    return min(score, 10), "{} tables, {} rows".format(len(tables), total_rows)


def _score_complete(result):
    """Are all required sections present?"""
    score = 0
    present = []
    missing = []

    checks = [
        ("executive_summary", "Executive Summary"),
        ("findings", "Findings"),
        ("evidence_tables", "Evidence Tables"),
        ("financial_impact", "Financial Impact"),
        ("recommendations", "Recommendations"),
        ("methodology", "Methodology"),
    ]

    for key, label in checks:
        val = result.get(key)
        if val and (not isinstance(val, (list, dict)) or len(val) > 0):
            score += 1.5
            present.append(label)
        else:
            missing.append(label)

    # Bonus for methodology depth
    method = result.get("methodology", {})
    if method.get("data_source"):
        score += 0.5
    if method.get("sql_used"):
        score += 0.5

    score = round(min(score, 10))
    rationale = "Present: {}".format(", ".join(present))
    if missing:
        rationale += " | Missing: {}".format(", ".join(missing))

    return score, rationale


def _score_brief(result):
    """Is the report appropriately concise (not over-verbose)?"""
    summary = result.get("executive_summary", "")
    findings = result.get("findings", [])
    recs = result.get("recommendations", [])

    # Must have content to score brevity
    if not summary and not findings:
        return 0, "No content to evaluate brevity"

    score = 0

    # Summary sweet spot: 100-500 chars
    if 100 <= len(summary) <= 500:
        score += 4  # Concise and substantive
    elif 50 <= len(summary) <= 800:
        score += 2  # Acceptable
    elif len(summary) > 800:
        score += 1  # Too verbose

    # Findings sweet spot: 3-15
    if 3 <= len(findings) <= 15:
        score += 3
    elif 1 <= len(findings) <= 50:
        score += 1

    # Recommendations sweet spot: 2-5
    if 2 <= len(recs) <= 5:
        score += 3
    elif 1 <= len(recs) <= 10:
        score += 1

    # Filler word penalty
    filler_words = ["however", "furthermore", "additionally", "moreover",
                    "it should be noted", "it is worth noting"]
    filler_count = sum(1 for f in filler_words if f in summary.lower())
    score = max(score - filler_count, 0)

    return min(score, 10), "Summary {} chars, {} findings, {} recs".format(
        len(summary), len(findings), len(recs))


def _score_data(result):
    """Are sources cited, SQL documented, limitations listed?"""
    method = result.get("methodology", {})
    if not method:
        return 0, "No methodology section"

    score = 0

    if method.get("data_source"):
        score += 3
    if method.get("query_window"):
        score += 2
    if method.get("sql_used"):
        score += 2
    if method.get("records_analyzed") is not None:
        score += 1

    limitations = method.get("limitations", [])
    if limitations:
        score += 1
        if len(limitations) >= 3:
            score += 1

    return min(score, 10), "Source: {}, SQL: {}, {} limitations".format(
        "yes" if method.get("data_source") else "no",
        "yes" if method.get("sql_used") else "no",
        len(limitations),
    )


def _score_honest(result):
    """Is confidence level set, are limitations acknowledged?"""
    score = 0

    confidence = result.get("confidence_level")
    if confidence is not None:
        score += 3
        # Appropriate confidence (not always 1.0)
        if 0 < confidence < 1.0:
            score += 2  # Not over-confident

    method = result.get("methodology", {})
    limitations = method.get("limitations", [])
    if limitations:
        score += 2
        if len(limitations) >= 2:
            score += 1

    # Financial impact has confidence qualifier
    impact = result.get("financial_impact", {})
    if impact.get("confidence"):
        score += 1
    if impact.get("basis"):
        score += 1

    return min(score, 10), "Confidence: {}, {} limitations, impact qualified: {}".format(
        confidence, len(limitations), bool(impact.get("confidence")),
    )


# ---------------------------------------------------------------------------
# MAIN EVALUATOR
# ---------------------------------------------------------------------------

DIMENSIONS = [
    ("audience", "Audience", _score_audience),
    ("story", "Story", _score_story),
    ("action", "Action", _score_action),
    ("visual", "Visual", _score_visual),
    ("complete", "Complete", _score_complete),
    ("brief", "Brief", _score_brief),
    ("data", "Data", _score_data),
    ("honest", "Honest", _score_honest),
]


def grade_label(avg):
    """Return grade label based on average score."""
    if avg >= 9.0:
        return "Board-ready"
    if avg >= 7.0:
        return "Reviewed"
    return "Draft"


def evaluate_report(result):
    """Evaluate an analysis result against the 8-dimension rubric.

    Returns:
        dict with keys: dimensions, total, average, grade, summary
    """
    dimensions = {}
    total = 0

    for key, label, scorer in DIMENSIONS:
        score, rationale = scorer(result)
        dimensions[key] = {
            "label": label,
            "score": score,
            "rationale": rationale,
        }
        total += score

    avg = round(total / len(DIMENSIONS), 1) if DIMENSIONS else 0
    grade = grade_label(avg)

    return {
        "dimensions": dimensions,
        "total": total,
        "average": avg,
        "grade": grade,
        "summary": "{} ({:.1f}/10 avg) — {} of 8 dimensions scored 8+".format(
            grade, avg,
            sum(1 for d in dimensions.values() if d["score"] >= 8),
        ),
    }
