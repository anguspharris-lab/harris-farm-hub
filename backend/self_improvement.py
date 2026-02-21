"""
Harris Farm Hub — Self-Improvement Engine
Parses audit scores, tracks improvement cycles, identifies weakest criteria,
and manages the MAX 3 ATTEMPTS per criterion per cycle loop.
"""

import re
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

AUDIT_LOG = os.path.join(
    os.path.dirname(__file__), "..", "watchdog", "audit.log"
)
IMPROVEMENT_LOG = os.path.join(
    os.path.dirname(__file__), "..", "watchdog", "learnings",
    "improvement_attempts.log"
)
HUB_DB = os.path.join(os.path.dirname(__file__), "hub_data.db")

CRITERIA = ["H", "R", "S", "C", "D", "U", "X"]
CRITERIA_LABELS = {
    "H": "Honest",
    "R": "Reliable",
    "S": "Safe",
    "C": "Clean",
    "D": "DataCorrect",
    "U": "Usable",
    "X": "Documented",
}
MAX_ATTEMPTS = 3
MIN_ACCEPTABLE = 7


def parse_audit_scores(limit=50):
    """Extract H/R/S/C/D/U/X score lines from audit.log.

    Returns list of dicts: [{"timestamp": ..., "task": ..., "H": 9, ...}]
    most recent first.
    """
    if not os.path.exists(AUDIT_LOG):
        return []

    # Universal pattern — catches all 6 audit.log score formats:
    #   1. H:8 R:8 S:9 ...       (colon, no prefix)
    #   2. Score: H=9 ... D=N/A   (mixed case, N/A value)
    #   3. SCORE: H=9 R=9 ...     (uppercase prefix)
    #   4. SCORE: H8 R8 S8 ...    (no delimiter)
    #   5. SCORES: H=9 R=9 ...    (plural prefix)
    #   6. H=9 R=9 S=9 ...        (inline, no prefix)
    pattern = re.compile(
        r"(?:SCORES?:\s*)?"
        r"H[=:]?(\d+)\s+"
        r"R[=:]?(\d+)\s+"
        r"S[=:]?(\d+)\s+"
        r"C[=:]?(\d+)\s+"
        r"D[=:]?(\d+|N/?A)\s+"
        r"U[=:]?(\d+)\s+"
        r"X[=:]?(\d+)",
        re.IGNORECASE,
    )
    ts_pattern = re.compile(r"\[(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})")
    task_pattern = re.compile(r"TASK:\s*([^|]+)")

    entries = []
    with open(AUDIT_LOG, "r") as f:
        lines = f.readlines()

    for line in reversed(lines):
        m = pattern.search(line)
        if not m:
            continue
        scores = {}
        for i, c in enumerate(CRITERIA):
            raw = m.group(i + 1)
            if raw.upper().replace("/", "") == "NA":
                scores[c] = 0  # D=N/A → 0 (excluded from avg)
            else:
                scores[c] = int(raw)

        ts_match = ts_pattern.search(line)
        timestamp = ts_match.group(1) if ts_match else ""

        task_match = task_pattern.search(line)
        task = task_match.group(1).strip() if task_match else ""

        scores["timestamp"] = timestamp
        scores["task"] = task
        valid = [scores[c] for c in CRITERIA if scores[c] > 0]
        scores["avg"] = round(sum(valid) / len(valid), 1) if valid else 0
        entries.append(scores)

        if len(entries) >= limit:
            break

    return entries


def calculate_averages(entries=None):
    """Calculate average score per criterion from recent audit entries.

    Returns dict: {"H": 8.5, "R": 9.0, ..., "avg": 8.7, "count": 5}
    """
    if entries is None:
        entries = parse_audit_scores()

    if not entries:
        return {c: 0.0 for c in CRITERIA + ["avg", "count"]}

    avgs = {}
    for c in CRITERIA:
        vals = [e[c] for e in entries if e.get(c, 0) > 0]
        avgs[c] = round(sum(vals) / len(vals), 2) if vals else 0.0

    avgs["avg"] = round(sum(avgs[c] for c in CRITERIA) / 7, 2)
    avgs["count"] = len(entries)
    return avgs


def identify_weakest(averages=None):
    """Find the criterion with the lowest average score.

    Returns (criterion_code, score, label) or None if no data.
    """
    if averages is None:
        averages = calculate_averages()

    if averages.get("count", 0) == 0:
        return None

    weakest = min(CRITERIA, key=lambda c: averages.get(c, 10))
    return (weakest, averages[weakest], CRITERIA_LABELS[weakest])


def get_attempt_count(criterion):
    """Count current cycle attempts for a criterion from improvement_attempts.log."""
    if not os.path.exists(IMPROVEMENT_LOG):
        return 0

    with open(IMPROVEMENT_LOG, "r") as f:
        content = f.read()

    pattern = re.compile(
        r"\[IMPROVE\].*\b" + re.escape(criterion) + r"\b.*attempt\s+(\d+)/3",
        re.IGNORECASE,
    )
    matches = pattern.findall(content)
    return int(matches[-1]) if matches else 0


def get_improvement_status():
    """Full status report of the self-improvement system.

    Returns dict with averages, weakest criterion, attempt counts,
    recent scores, and recommendations.
    """
    entries = parse_audit_scores(limit=20)
    averages = calculate_averages(entries)
    weakest = identify_weakest(averages)

    # Attempt counts per criterion
    attempts = {c: get_attempt_count(c) for c in CRITERIA}

    # Below-threshold criteria
    below_threshold = [
        (c, averages[c], CRITERIA_LABELS[c])
        for c in CRITERIA
        if averages[c] < MIN_ACCEPTABLE
    ]

    # Build recommendation
    recommendation = ""
    if weakest:
        code, score, label = weakest
        att = attempts[code]
        if att >= MAX_ATTEMPTS:
            recommendation = (
                "ESCALATE to operator: {} ({}) has failed {}/{} "
                "improvement attempts (avg score: {})".format(
                    label, code, att, MAX_ATTEMPTS, score
                )
            )
        elif score < MIN_ACCEPTABLE:
            recommendation = (
                "IMPROVE {label} ({code}): avg score {score} < {min}. "
                "Attempt {next}/{max} available.".format(
                    label=label, code=code, score=score,
                    min=MIN_ACCEPTABLE, next=att + 1, max=MAX_ATTEMPTS,
                )
            )
        else:
            recommendation = (
                "All criteria at or above threshold ({min}). "
                "Lowest: {label} ({code}) at {score}.".format(
                    min=MIN_ACCEPTABLE, label=label, code=code, score=score,
                )
            )

    return {
        "averages": averages,
        "weakest": {
            "criterion": weakest[0] if weakest else None,
            "score": weakest[1] if weakest else None,
            "label": weakest[2] if weakest else None,
        },
        "attempts": attempts,
        "below_threshold": below_threshold,
        "recommendation": recommendation,
        "recent_scores": entries[:10],
        "generated_at": datetime.now().isoformat(),
    }


def store_task_scores(task_name, scores_dict):
    """Store a scored task into the task_scores table.

    scores_dict: {"H": 9, "R": 8, ...}
    """
    conn = sqlite3.connect(HUB_DB)
    c = conn.cursor()
    valid = [scores_dict.get(cr, 0) or 0 for cr in CRITERIA]
    non_zero = [v for v in valid if v > 0]
    avg = round(sum(non_zero) / len(non_zero), 2) if non_zero else 0
    c.execute(
        """INSERT INTO task_scores
           (task_name, h, r, s, c, d, u, x, avg_score, recorded_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            task_name,
            scores_dict.get("H", 0), scores_dict.get("R", 0),
            scores_dict.get("S", 0), scores_dict.get("C", 0),
            scores_dict.get("D", 0), scores_dict.get("U", 0),
            scores_dict.get("X", 0), avg,
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return {"task": task_name, "avg": avg, "stored": True}


def record_improvement_cycle(criterion, before_score, after_score, action,
                             success):
    """Record an improvement attempt in both DB and log file.

    Returns dict with cycle details.
    """
    attempt_num = get_attempt_count(criterion) + 1
    status = "SUCCESS" if success else "FAILED"

    conn = sqlite3.connect(HUB_DB)
    c = conn.cursor()
    c.execute(
        """INSERT INTO improvement_cycles
           (criterion, criterion_label, before_score, after_score,
            action_taken, attempt_number, status, recorded_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            criterion, CRITERIA_LABELS.get(criterion, criterion),
            before_score, after_score, action, attempt_num, status,
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()

    # Also append to improvement_attempts.log
    log_line = (
        "\n[IMPROVE] {ts} | {crit} | attempt {att}/{max} | "
        "{before}->{after} | {status} | {action}".format(
            ts=datetime.now().strftime("%Y-%m-%d %H:%M"),
            crit=criterion, att=attempt_num, max=MAX_ATTEMPTS,
            before=before_score, after=after_score,
            status=status, action=action,
        )
    )

    log_path = Path(IMPROVEMENT_LOG)
    if log_path.exists():
        with open(log_path, "a") as f:
            f.write(log_line)

    return {
        "criterion": criterion,
        "attempt": attempt_num,
        "before": before_score,
        "after": after_score,
        "success": success,
        "escalate": attempt_num >= MAX_ATTEMPTS and not success,
    }


def get_improvement_history(limit=20):
    """Fetch recent improvement cycles from DB."""
    conn = sqlite3.connect(HUB_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute(
            """SELECT * FROM improvement_cycles
               ORDER BY id DESC LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in c.fetchall()]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def get_score_trends(limit=50):
    """Fetch scored tasks for trend analysis."""
    conn = sqlite3.connect(HUB_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute(
            """SELECT * FROM task_scores
               ORDER BY id DESC LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in c.fetchall()]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def backfill_scores_from_audit():
    """One-time backfill: parse all scores from audit.log into task_scores table.

    Returns count of inserted rows.
    """
    entries = parse_audit_scores(limit=500)
    if not entries:
        return 0

    conn = sqlite3.connect(HUB_DB)
    c = conn.cursor()
    inserted = 0

    for idx, entry in enumerate(reversed(entries)):
        task_name = entry.get("task", "") or "task_{}".format(idx + 1)
        ts = entry.get("timestamp", "")
        if not ts:
            ts = "audit_entry_{}".format(idx + 1)
        avg = entry.get("avg", 0)

        # Skip if already exists (by scores + task_name)
        c.execute(
            "SELECT COUNT(*) FROM task_scores WHERE task_name = ? AND h = ? AND r = ? AND avg_score = ?",
            (task_name, entry.get("H", 0), entry.get("R", 0), avg),
        )
        if c.fetchone()[0] > 0:
            continue

        c.execute(
            """INSERT INTO task_scores
               (task_name, h, r, s, c, d, u, x, avg_score, recorded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_name,
                entry.get("H", 0), entry.get("R", 0),
                entry.get("S", 0), entry.get("C", 0),
                entry.get("D", 0), entry.get("U", 0),
                entry.get("X", 0), avg, ts,
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    return inserted
