"""
Harris Farm Hub — HiPo (High Potential) Signal Detection Engine

Silently tracks 9 behavioral signals that indicate high-potential AI users.
All functions take db_path as first argument (no FastAPI dependency).
Scores are 0-10 scale. Composite score is weighted average of all signals.
Python 3.9 compatible.
"""

import json
import math
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# SIGNAL DEFINITIONS
# ---------------------------------------------------------------------------

SIGNAL_DEFINITIONS = {
    "velocity": {
        "name": "Learning Velocity",
        "description": "Speed of progression through levels and modules",
        "weight": 1.0,
    },
    "curiosity": {
        "name": "Curiosity",
        "description": "Explores optional content, tries different approaches, uses Practice Lab",
        "weight": 0.8,
    },
    "ambition": {
        "name": "Ambition",
        "description": "Attempts stretch/elite exercises, tackles L6 enterprise challenges",
        "weight": 1.2,
    },
    "iteration": {
        "name": "Iteration Drive",
        "description": "Re-submits assessments to improve scores, edits prompts multiple times",
        "weight": 1.0,
    },
    "cross_pollination": {
        "name": "Cross-Pollination",
        "description": "Applies L-Series techniques in D-Series and vice versa, diverse module engagement",
        "weight": 0.9,
    },
    "teaching": {
        "name": "Teaching Instinct",
        "description": "High assessment scores plus peer battle participation and wins",
        "weight": 1.1,
    },
    "process_thinking": {
        "name": "Process Thinking",
        "description": "Consistent quality across all rubric dimensions, no spiky scores",
        "weight": 0.7,
    },
    "proactive_usage": {
        "name": "Proactive Usage",
        "description": "Uses Hub tools (Prompt Engine, Analytics Engine, Hub Assistant) beyond required exercises",
        "weight": 0.8,
    },
    "verification_strength": {
        "name": "Verification Strength",
        "description": "Progress across all 4 Woven Verification dimensions (Foundation, Breadth, Depth, Application)",
        "weight": 1.2,
    },
}

QUADRANT_THRESHOLDS = {
    "skill_high": 4,   # level_index >= 4 (Cultivator+)
    "hipo_high": 6.0,  # composite score >= 6.0
}


# ---------------------------------------------------------------------------
# TABLE INIT
# ---------------------------------------------------------------------------

def init_hipo_tables(conn):
    """Create sa_hipo_signals table. Safe to call repeatedly."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sa_hipo_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            score REAL DEFAULT 0.0,
            evidence_json TEXT DEFAULT '{}',
            calculated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, signal_type)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_hipo_user
        ON sa_hipo_signals(user_id)
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# HELPER: safe query for tables that may not exist yet
# ---------------------------------------------------------------------------

def _safe_query(conn, sql, params=()):
    """Execute a query, returning empty list if the table doesn't exist."""
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return []


def _safe_fetchone(conn, sql, params=(), default=None):
    """Execute a query returning one row, or default if table missing."""
    try:
        row = conn.execute(sql, params).fetchone()
        return row if row is not None else default
    except sqlite3.OperationalError:
        return default


def _clamp(value, lo=0.0, hi=10.0):
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# INDIVIDUAL SIGNAL CALCULATORS
# ---------------------------------------------------------------------------

def calculate_velocity(db_path, user_id):
    """Calculate velocity signal (0-10) based on XP earn rate and module
    completion speed.  Score = XP per active day normalized to 0-10."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Total XP and date range from academy_xp_log
    row = _safe_fetchone(
        conn,
        "SELECT COALESCE(SUM(xp_amount), 0) AS total_xp, "
        "MIN(created_at) AS first_at, MAX(created_at) AS last_at "
        "FROM academy_xp_log WHERE user_id = ?",
        (user_id,),
    )

    total_xp = 0
    days_active = 1
    first_at = None
    if row and row["total_xp"]:
        total_xp = row["total_xp"]
        first_at = row["first_at"]
        if row["first_at"] and row["last_at"]:
            try:
                d1 = datetime.fromisoformat(row["first_at"][:10])
                d2 = datetime.fromisoformat(row["last_at"][:10])
                days_active = max((d2 - d1).days, 1)
            except (ValueError, TypeError):
                days_active = 1

    # Assessment pass count
    pass_row = _safe_fetchone(
        conn,
        "SELECT COUNT(*) AS cnt FROM skills_assessments "
        "WHERE user_id = ? AND passed = 1",
        (user_id,),
    )
    pass_count = pass_row["cnt"] if pass_row else 0

    conn.close()

    # XP per day — 50 XP/day = score 10
    xp_per_day = total_xp / days_active if days_active > 0 else 0
    xp_score = _clamp(xp_per_day / 5.0)  # 50 XP/day -> 10

    # Pass rate bonus: each pass adds 0.5, cap at 3.0
    pass_bonus = min(pass_count * 0.5, 3.0)

    score = _clamp((xp_score * 0.7) + (pass_bonus * 0.3))
    evidence = {
        "total_xp": total_xp,
        "days_active": days_active,
        "xp_per_day": round(xp_per_day, 1),
        "assessment_passes": pass_count,
    }
    return (round(score, 2), evidence)


def calculate_curiosity(db_path, user_id):
    """Calculate curiosity signal (0-10).  Measures module variety, practice
    lab usage, and topic diversity in Paddock attempts."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Distinct modules attempted in skills_assessments
    mod_rows = _safe_query(
        conn,
        "SELECT COUNT(DISTINCT module_code) AS cnt "
        "FROM skills_assessments WHERE user_id = ?",
        (user_id,),
    )
    distinct_modules = mod_rows[0]["cnt"] if mod_rows else 0

    # Practice Lab usage
    practice_rows = _safe_query(
        conn,
        "SELECT COUNT(*) AS cnt FROM skills_assessments "
        "WHERE user_id = ? AND module_code = 'practice'",
        (user_id,),
    )
    practice_count = practice_rows[0]["cnt"] if practice_rows else 0

    # Paddock topic variety
    paddock_rows = _safe_query(
        conn,
        "SELECT COUNT(DISTINCT topic) AS cnt FROM paddock_attempts "
        "WHERE user_id = ?",
        (user_id,),
    )
    paddock_topics = paddock_rows[0]["cnt"] if paddock_rows else 0

    conn.close()

    # 10 distinct modules = full score on that dimension
    module_score = _clamp(distinct_modules / 10.0 * 10.0)
    practice_score = _clamp(practice_count * 2.0)  # 5 practice sessions = 10
    paddock_score = _clamp(paddock_topics / 5.0 * 10.0)

    score = _clamp(module_score * 0.4 + practice_score * 0.3 + paddock_score * 0.3)
    evidence = {
        "distinct_modules": distinct_modules,
        "practice_lab_uses": practice_count,
        "paddock_topics": paddock_topics,
    }
    return (round(score, 2), evidence)


def calculate_ambition(db_path, user_id):
    """Calculate ambition signal (0-10).  Counts stretch-tier and elite-tier
    exercise completions plus L6 enterprise challenge attempts."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Stretch-tier exercises from sa_exercise_state
    stretch_rows = _safe_query(
        conn,
        "SELECT COUNT(*) AS cnt FROM sa_exercise_state "
        "WHERE user_id = ? AND tier = 'stretch' AND status = 'complete'",
        (user_id,),
    )
    stretch_count = stretch_rows[0]["cnt"] if stretch_rows else 0

    # Elite-tier exercises
    elite_rows = _safe_query(
        conn,
        "SELECT COUNT(*) AS cnt FROM sa_exercise_state "
        "WHERE user_id = ? AND tier = 'elite' AND status = 'complete'",
        (user_id,),
    )
    elite_count = elite_rows[0]["cnt"] if elite_rows else 0

    # L6 enterprise challenges (module_code starts with 'L6')
    l6_rows = _safe_query(
        conn,
        "SELECT COUNT(*) AS cnt FROM skills_assessments "
        "WHERE user_id = ? AND module_code LIKE 'L6%'",
        (user_id,),
    )
    l6_count = l6_rows[0]["cnt"] if l6_rows else 0

    conn.close()

    # 5 stretch = 5 pts, 3 elite = 3 pts, L6 attempt = 2 pts
    stretch_score = min(stretch_count, 5)
    elite_score = min(elite_count * 1.5, 4.0)
    l6_score = min(l6_count, 1) * 2.0  # binary: attempted or not, worth 2

    score = _clamp(stretch_score + elite_score + l6_score)
    evidence = {
        "stretch_exercises": stretch_count,
        "elite_exercises": elite_count,
        "l6_attempts": l6_count,
    }
    return (round(score, 2), evidence)


def calculate_iteration(db_path, user_id):
    """Calculate iteration signal (0-10).  Measures re-submissions per module
    and whether scores improved on re-submission."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Group submissions by module_code, ordered by submitted_at
    rows = _safe_query(
        conn,
        "SELECT module_code, score, submitted_at FROM skills_assessments "
        "WHERE user_id = ? ORDER BY module_code, submitted_at",
        (user_id,),
    )
    conn.close()

    if not rows:
        return (0.0, {"modules_resubmitted": 0, "improvements": 0, "total_submissions": 0})

    # Group by module
    modules = {}  # type: dict
    for r in rows:
        code = r["module_code"]
        if code not in modules:
            modules[code] = []
        modules[code].append(r["score"] if r["score"] is not None else 0)

    resubmitted = 0
    improvements = 0
    total_submissions = len(rows)

    for code, scores in modules.items():
        if len(scores) > 1:
            resubmitted += 1
            # Check if any later score improved over the first
            if max(scores[1:]) > scores[0]:
                improvements += 1

    # 3+ modules resubmitted with improvements = high score
    resub_score = _clamp(resubmitted * 2.0)  # 5 resubs = 10
    improve_score = _clamp(improvements * 3.0)  # 3-4 improvements = ~10

    score = _clamp(resub_score * 0.4 + improve_score * 0.6)
    evidence = {
        "modules_resubmitted": resubmitted,
        "improvements": improvements,
        "total_submissions": total_submissions,
    }
    return (round(score, 2), evidence)


def calculate_cross_pollination(db_path, user_id):
    """Calculate cross-pollination signal (0-10).  Checks engagement across
    both L-series and D-series modules."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    rows = _safe_query(
        conn,
        "SELECT DISTINCT module_code FROM skills_assessments WHERE user_id = ?",
        (user_id,),
    )
    conn.close()

    l_series = set()
    d_series = set()
    other = set()
    for r in rows:
        code = r["module_code"] or ""
        if code.upper().startswith("L"):
            l_series.add(code)
        elif code.upper().startswith("D"):
            d_series.add(code)
        else:
            other.add(code)

    has_both = 1 if (l_series and d_series) else 0
    total_distinct = len(l_series) + len(d_series) + len(other)

    # Cross-pollination: having both series = 4 pts base, diversity adds rest
    cross_score = has_both * 4.0
    diversity_score = _clamp(total_distinct / 10.0 * 6.0)  # 10 modules = 6 pts

    score = _clamp(cross_score + diversity_score)
    evidence = {
        "l_series_modules": len(l_series),
        "d_series_modules": len(d_series),
        "other_modules": len(other),
        "has_both_series": bool(has_both),
    }
    return (round(score, 2), evidence)


def calculate_teaching(db_path, user_id):
    """Calculate teaching signal (0-10).  High assessment scores + peer battle
    participation and win rate."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Average assessment score
    score_row = _safe_fetchone(
        conn,
        "SELECT AVG(score) AS avg_score, COUNT(*) AS cnt "
        "FROM skills_assessments WHERE user_id = ?",
        (user_id,),
    )
    avg_score = score_row["avg_score"] if score_row and score_row["avg_score"] else 0
    assessment_count = score_row["cnt"] if score_row else 0

    # Peer battle participation (table may not exist yet)
    battle_rows = _safe_query(
        conn,
        "SELECT COUNT(*) AS total, "
        "SUM(CASE WHEN winner_id = ? THEN 1 ELSE 0 END) AS wins "
        "FROM sa_peer_battles "
        "WHERE challenger_id = ? OR opponent_id = ?",
        (user_id, user_id, user_id),
    )
    battle_total = battle_rows[0]["total"] if battle_rows else 0
    battle_wins = battle_rows[0]["wins"] if battle_rows and battle_rows[0]["wins"] else 0

    conn.close()

    # High avg score (>20/25 = good, 25/25 = perfect)
    if assessment_count == 0:
        mastery_score = 0.0
    else:
        mastery_score = _clamp((avg_score - 15.0) / 10.0 * 10.0)

    # Battle participation: each battle = 1 pt, win rate bonus
    battle_score = _clamp(battle_total * 1.0)  # 10 battles = 10
    win_rate = (battle_wins / battle_total) if battle_total > 0 else 0
    win_bonus = win_rate * 3.0

    score = _clamp(mastery_score * 0.5 + battle_score * 0.25 + win_bonus * 0.25)
    evidence = {
        "avg_assessment_score": round(avg_score, 1),
        "assessment_count": assessment_count,
        "peer_battles": battle_total,
        "peer_wins": battle_wins,
        "win_rate": round(win_rate, 2),
    }
    return (round(score, 2), evidence)


def calculate_process_thinking(db_path, user_id):
    """Calculate process thinking signal (0-10).  Low std deviation across
    rubric criteria indicates consistent, balanced thinking."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Get rubric breakdowns from skills_assessments
    rows = _safe_query(
        conn,
        "SELECT rubric_scores_json FROM skills_assessments "
        "WHERE user_id = ? AND rubric_scores_json IS NOT NULL",
        (user_id,),
    )
    conn.close()

    if not rows:
        return (0.0, {"assessments_analysed": 0, "avg_std_dev": None})

    std_devs = []
    for r in rows:
        try:
            rubric = json.loads(r["rubric_scores_json"])
            if isinstance(rubric, dict) and rubric:
                values = [float(v) for v in rubric.values() if v is not None]
                if len(values) >= 2:
                    mean = sum(values) / len(values)
                    variance = sum((x - mean) ** 2 for x in values) / len(values)
                    std_devs.append(math.sqrt(variance))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

    if not std_devs:
        return (0.0, {"assessments_analysed": 0, "avg_std_dev": None})

    avg_std = sum(std_devs) / len(std_devs)

    # Low std dev = high process thinking.  std=0 -> 10, std>=3 -> 0
    score = _clamp((3.0 - avg_std) / 3.0 * 10.0)

    evidence = {
        "assessments_analysed": len(std_devs),
        "avg_std_dev": round(avg_std, 2),
    }
    return (round(score, 2), evidence)


def calculate_proactive_usage(db_path, user_id):
    """Calculate proactive usage signal (0-10).  Checks visits to Hub tools
    beyond Skills Academy (Prompt Engine, Analytics Engine, Hub Assistant)."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    target_pages = ["Prompt Engine", "Analytics Engine", "Hub Assistant"]

    # analytics_pageviews may not exist yet
    total_visits = 0
    distinct_tools = 0
    tool_visits = {}  # type: dict
    for page in target_pages:
        rows = _safe_query(
            conn,
            "SELECT COUNT(*) AS cnt FROM analytics_pageviews "
            "WHERE user_id = ? AND page_name = ?",
            (user_id, page),
        )
        cnt = rows[0]["cnt"] if rows else 0
        tool_visits[page] = cnt
        total_visits += cnt
        if cnt > 0:
            distinct_tools += 1

    conn.close()

    # 3 tools used = 4 pts, each 5 visits = 1 pt (up to 6 pts)
    breadth_score = distinct_tools * (4.0 / 3.0)  # 3 tools = 4
    depth_score = _clamp(total_visits / 5.0, 0.0, 6.0)

    score = _clamp(breadth_score + depth_score)
    evidence = {
        "tool_visits": tool_visits,
        "distinct_tools_used": distinct_tools,
        "total_visits": total_visits,
    }
    return (round(score, 2), evidence)


def calculate_verification_strength(db_path, user_id):
    """Calculate verification strength signal (0-10).  Measures progress
    across the 4 Woven Verification dimensions: Foundation, Breadth,
    Depth, Application.  Each dimension met = 2.5 pts."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Get the user's current verification status from v4 tables
    row = _safe_fetchone(
        conn,
        "SELECT level_number, level_status, foundation_score, "
        "breadth_count, depth_count, application_passed "
        "FROM sa_verification_status WHERE user_id = ? "
        "ORDER BY level_number DESC LIMIT 1",
        (user_id,),
    )

    if not row:
        conn.close()
        return (0.0, {"has_verification": False})

    foundation = row["foundation_score"] or 0.0
    breadth = row["breadth_count"] or 0
    depth = row["depth_count"] or 0
    application = row["application_passed"] or 0
    status = row["level_status"] or "provisional"

    conn.close()

    # Score each dimension (0-2.5 each, proportional to target)
    foundation_pts = min(foundation / 0.80, 1.0) * 2.5   # target 80%
    breadth_pts = min(breadth / 5.0, 1.0) * 2.5           # target 5 contexts
    depth_pts = min(depth / 3.0, 1.0) * 2.5               # target 3 curveballs
    application_pts = min(application / 1.0, 1.0) * 2.5    # target 1 capstone

    raw_score = foundation_pts + breadth_pts + depth_pts + application_pts

    # Confirmed status bonus: +1.0 (shows they've fully verified)
    if status == "confirmed":
        raw_score = min(raw_score + 1.0, 10.0)

    dimensions_met = sum([
        foundation >= 0.80,
        breadth >= 5,
        depth >= 3,
        application >= 1,
    ])

    score = _clamp(raw_score)
    evidence = {
        "foundation_score": round(foundation, 2),
        "breadth_count": breadth,
        "depth_count": depth,
        "application_passed": application,
        "dimensions_met": dimensions_met,
        "status": status,
    }
    return (round(score, 2), evidence)


# ---------------------------------------------------------------------------
# SIGNAL CALCULATION DISPATCHER
# ---------------------------------------------------------------------------

_CALCULATORS = {
    "velocity": calculate_velocity,
    "curiosity": calculate_curiosity,
    "ambition": calculate_ambition,
    "iteration": calculate_iteration,
    "cross_pollination": calculate_cross_pollination,
    "teaching": calculate_teaching,
    "process_thinking": calculate_process_thinking,
    "proactive_usage": calculate_proactive_usage,
    "verification_strength": calculate_verification_strength,
}


def calculate_all_signals(db_path, user_id):
    """Compute all 9 signals and upsert into sa_hipo_signals.
    Returns list of {signal_type, score, evidence}."""
    conn = sqlite3.connect(str(db_path))
    init_hipo_tables(conn)
    conn.close()

    results = []
    for signal_type, calc_fn in _CALCULATORS.items():
        score, evidence = calc_fn(db_path, user_id)
        results.append({
            "signal_type": signal_type,
            "score": score,
            "evidence": evidence,
        })
        # Upsert into sa_hipo_signals
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO sa_hipo_signals (user_id, signal_type, score, "
            "evidence_json, calculated_at) VALUES (?, ?, ?, ?, datetime('now')) "
            "ON CONFLICT(user_id, signal_type) DO UPDATE SET "
            "score=excluded.score, evidence_json=excluded.evidence_json, "
            "calculated_at=excluded.calculated_at",
            (user_id, signal_type, score, json.dumps(evidence)),
        )
        conn.commit()
        conn.close()

    return results


# ---------------------------------------------------------------------------
# COMPOSITE SCORE + QUADRANT
# ---------------------------------------------------------------------------

def _compute_composite(signals):
    """Weighted average of signal scores, normalized to 0-10."""
    total_weighted = 0.0
    total_weight = 0.0
    for s in signals:
        defn = SIGNAL_DEFINITIONS.get(s["signal_type"], {})
        w = defn.get("weight", 1.0)
        total_weighted += s["score"] * w
        total_weight += w
    if total_weight == 0:
        return 0.0
    return round(total_weighted / total_weight, 2)


def _get_quadrant(level_index, composite_score):
    """Determine quadrant from skill level and HiPo score."""
    high_skill = level_index >= QUADRANT_THRESHOLDS["skill_high"]
    high_hipo = composite_score >= QUADRANT_THRESHOLDS["hipo_high"]

    if high_skill and high_hipo:
        return "AI Leaders"
    elif not high_skill and high_hipo:
        return "Hidden Gems"
    elif high_skill and not high_hipo:
        return "Solid Practitioners"
    else:
        return "Early Stage"


def get_user_hipo(db_path, user_id):
    """Return all 9 signals + weighted composite score for a user.
    Returns: {signals: [...], composite_score: float, quadrant: str}"""
    conn = sqlite3.connect(str(db_path))
    init_hipo_tables(conn)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT signal_type, score, evidence_json, calculated_at "
        "FROM sa_hipo_signals WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()

    signals = []
    for r in rows:
        defn = SIGNAL_DEFINITIONS.get(r["signal_type"], {})
        signals.append({
            "signal_type": r["signal_type"],
            "name": defn.get("name", r["signal_type"]),
            "score": r["score"],
            "weight": defn.get("weight", 1.0),
            "evidence": json.loads(r["evidence_json"]) if r["evidence_json"] else {},
            "calculated_at": r["calculated_at"],
        })

    composite = _compute_composite(signals)

    # Get user level for quadrant placement
    try:
        from backend.academy_engine import get_user_xp
        xp_data = get_user_xp(db_path, user_id)
        level_index = xp_data.get("level_index", 0)
    except (ImportError, Exception):
        level_index = 0

    quadrant = _get_quadrant(level_index, composite)

    return {
        "user_id": user_id,
        "signals": signals,
        "composite_score": composite,
        "quadrant": quadrant,
    }


# ---------------------------------------------------------------------------
# ADMIN: LEADERBOARD + MATRIX
# ---------------------------------------------------------------------------

def get_hipo_leaderboard(db_path, limit=50):
    """Admin: Get users ranked by composite HiPo score.
    Returns list of {user_id, composite_score, top_signals}."""
    conn = sqlite3.connect(str(db_path))
    init_hipo_tables(conn)
    conn.row_factory = sqlite3.Row

    # Get all users who have signals
    user_rows = conn.execute(
        "SELECT DISTINCT user_id FROM sa_hipo_signals"
    ).fetchall()

    users = []
    for ur in user_rows:
        uid = ur["user_id"]
        signal_rows = conn.execute(
            "SELECT signal_type, score FROM sa_hipo_signals WHERE user_id = ?",
            (uid,),
        ).fetchall()

        signals = [{"signal_type": r["signal_type"], "score": r["score"]}
                   for r in signal_rows]
        composite = _compute_composite(signals)

        # Top 3 signals by score
        sorted_signals = sorted(signals, key=lambda s: s["score"], reverse=True)
        top_signals = sorted_signals[:3]

        # Get display name from auth users table
        name_row = _safe_fetchone(
            conn,
            "SELECT display_name FROM auth_users WHERE user_id = ?",
            (uid,),
        )
        display_name = name_row["display_name"] if name_row else uid

        users.append({
            "user_id": uid,
            "display_name": display_name,
            "composite_score": composite,
            "top_signals": top_signals,
        })

    conn.close()

    users.sort(key=lambda u: u["composite_score"], reverse=True)
    return users[:limit]


def get_hipo_matrix(db_path):
    """Admin: Get 2x2 matrix data (Skill Level x HiPo Score).
    Quadrants:
    - AI Leaders: high skill (level >= 4) + high HiPo (>= 6.0)
    - Hidden Gems: low skill (level < 4) + high HiPo (>= 6.0)
    - Solid Practitioners: high skill (level >= 4) + low HiPo (< 6.0)
    - Early Stage: low skill (level < 4) + low HiPo (< 6.0)
    Returns: {quadrants: {name: [users]}, summary: {counts}}"""
    try:
        from backend.academy_engine import get_user_xp
    except ImportError:
        # Fallback: cannot determine levels without academy_engine
        return {"quadrants": {}, "summary": {}}

    conn = sqlite3.connect(str(db_path))
    init_hipo_tables(conn)
    conn.row_factory = sqlite3.Row

    user_rows = conn.execute(
        "SELECT DISTINCT user_id FROM sa_hipo_signals"
    ).fetchall()

    quadrants = {
        "AI Leaders": [],
        "Hidden Gems": [],
        "Solid Practitioners": [],
        "Early Stage": [],
    }

    for ur in user_rows:
        uid = ur["user_id"]

        # Get composite score
        signal_rows = conn.execute(
            "SELECT signal_type, score FROM sa_hipo_signals WHERE user_id = ?",
            (uid,),
        ).fetchall()
        signals = [{"signal_type": r["signal_type"], "score": r["score"]}
                   for r in signal_rows]
        composite = _compute_composite(signals)

        # Get skill level
        try:
            xp_data = get_user_xp(db_path, uid)
            level_index = xp_data.get("level_index", 0)
            level_name = xp_data.get("name", "Seed")
            total_xp = xp_data.get("total_xp", 0)
        except Exception:
            level_index = 0
            level_name = "Seed"
            total_xp = 0

        # Display name
        name_row = _safe_fetchone(
            conn,
            "SELECT display_name FROM auth_users WHERE user_id = ?",
            (uid,),
        )
        display_name = name_row["display_name"] if name_row else uid

        quadrant = _get_quadrant(level_index, composite)
        user_data = {
            "user_id": uid,
            "display_name": display_name,
            "composite_score": composite,
            "level_index": level_index,
            "level_name": level_name,
            "total_xp": total_xp,
        }
        quadrants[quadrant].append(user_data)

    conn.close()

    summary = {q: len(users) for q, users in quadrants.items()}
    summary["total"] = sum(summary.values())
    return {"quadrants": quadrants, "summary": summary}
