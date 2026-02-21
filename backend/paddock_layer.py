"""
Harris Farm Hub -- The Paddock Data Layer
SQLite CRUD for AI skills assessment: users, responses, results, feedback.
All data stored in hub_data.db alongside existing Hub tables.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = str(Path(__file__).resolve().parent / "hub_data.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _row_to_dict(row):
    # type: (Optional[sqlite3.Row]) -> Optional[dict]
    if row is None:
        return None
    return dict(row)


# ============================================================================
# USER REGISTRATION
# ============================================================================

def register_user(name, store, department, role_tier,
                  hub_user_id=None, employee_id=None,
                  tech_comfort=3, ai_experience=None):
    # type: (...) -> dict
    conn = _get_conn()
    c = conn.execute(
        """INSERT INTO paddock_users
           (hub_user_id, name, employee_id, store, department,
            role_tier, tech_comfort, ai_experience)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (hub_user_id, name, employee_id, store, department,
         int(role_tier), int(tech_comfort), ai_experience))
    conn.commit()
    user_id = c.lastrowid
    user = _row_to_dict(conn.execute(
        "SELECT * FROM paddock_users WHERE id = ?", (user_id,)).fetchone())
    conn.close()
    return user


def get_user(user_id):
    # type: (int) -> Optional[dict]
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM paddock_users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_user_by_hub_id(hub_user_id):
    # type: (str) -> Optional[dict]
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM paddock_users WHERE hub_user_id = ? ORDER BY id DESC LIMIT 1",
        (hub_user_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


# ============================================================================
# RESPONSE RECORDING
# ============================================================================

def save_response(user_id, module, question_id, answer, score, time_taken=None):
    # type: (int, str, str, object, int, Optional[int]) -> dict
    conn = _get_conn()
    answer_str = json.dumps(answer) if isinstance(answer, list) else str(answer or "")
    conn.execute(
        """INSERT INTO paddock_responses
           (user_id, module, question_id, answer, score, time_taken_seconds)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(user_id, module, question_id) DO UPDATE SET
               answer = excluded.answer,
               score = excluded.score,
               time_taken_seconds = excluded.time_taken_seconds""",
        (int(user_id), module, question_id, answer_str, int(score), time_taken))
    conn.commit()
    conn.close()
    return {"score": score, "question_id": question_id, "module": module}


def get_module_responses(user_id, module):
    # type: (int, str) -> list
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM paddock_responses WHERE user_id = ? AND module = ?",
        (int(user_id), module)).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_all_responses(user_id):
    # type: (int) -> list
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM paddock_responses WHERE user_id = ? ORDER BY module, question_id",
        (int(user_id),)).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def count_answered(user_id, module):
    # type: (int, str) -> int
    conn = _get_conn()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM paddock_responses WHERE user_id = ? AND module = ?",
        (int(user_id), module)).fetchone()
    conn.close()
    return row["cnt"] if row else 0


# ============================================================================
# RESULTS CALCULATION
# ============================================================================

def calculate_results(user_id):
    # type: (int) -> dict
    try:
        from shared.paddock_questions import MODULE_IDS, WEIGHTS, get_maturity
    except ImportError:
        import sys
        _dash = str(Path(__file__).resolve().parent.parent / "dashboards")
        if _dash not in sys.path:
            sys.path.insert(0, _dash)
        from shared.paddock_questions import MODULE_IDS, WEIGHTS, get_maturity
    conn = _get_conn()

    module_scores = {}
    for mod in MODULE_IDS:
        rows = conn.execute(
            "SELECT score FROM paddock_responses WHERE user_id = ? AND module = ?",
            (int(user_id), mod)).fetchall()
        if rows:
            module_scores[mod] = round(sum(r["score"] for r in rows) / len(rows))
        else:
            module_scores[mod] = 0

    overall = round(sum(module_scores.get(m, 0) * WEIGHTS[m] for m in MODULE_IDS))
    maturity = get_maturity(overall)

    # Delete any previous result and insert new
    conn.execute("DELETE FROM paddock_results WHERE user_id = ?", (int(user_id),))
    conn.execute(
        """INSERT INTO paddock_results
           (user_id, maturity_level, awareness_score, usage_score,
            critical_score, applied_score, confidence_score, overall_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (int(user_id), maturity["level"],
         module_scores.get("awareness", 0),
         module_scores.get("usage", 0),
         module_scores.get("critical", 0),
         module_scores.get("applied", 0),
         module_scores.get("confidence", 0),
         overall))
    conn.commit()
    conn.close()

    return {
        "user_id": user_id,
        "maturity": maturity,
        "scores": {
            "awareness": module_scores.get("awareness", 0),
            "usage": module_scores.get("usage", 0),
            "critical": module_scores.get("critical", 0),
            "applied": module_scores.get("applied", 0),
            "confidence": module_scores.get("confidence", 0),
            "overall": overall,
        },
    }


def get_results(user_id):
    # type: (int) -> Optional[dict]
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM paddock_results WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (int(user_id),)).fetchone()
    conn.close()
    return _row_to_dict(row)


# ============================================================================
# FEEDBACK
# ============================================================================

def save_feedback(user_id, experience_rating=None,
                  confusion_notes=None, improvement_suggestions=None):
    # type: (int, Optional[int], Optional[str], Optional[str]) -> dict
    conn = _get_conn()
    conn.execute(
        """INSERT INTO paddock_feedback
           (user_id, experience_rating, confusion_notes, improvement_suggestions)
           VALUES (?, ?, ?, ?)""",
        (int(user_id), experience_rating, confusion_notes, improvement_suggestions))
    conn.commit()
    conn.close()
    return {"ok": True}


def get_feedback(user_id):
    # type: (int) -> Optional[dict]
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM paddock_feedback WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (int(user_id),)).fetchone()
    conn.close()
    return _row_to_dict(row)


# ============================================================================
# LEARNING CENTRE INTEGRATION
# ============================================================================

def update_learning_progress(hub_user_id, maturity_level):
    # type: (Optional[str], int) -> None
    if not hub_user_id:
        return
    conn = _get_conn()
    now = datetime.now().isoformat()
    # Map maturity level to recommended Learning Centre modules
    mapping = {
        1: ["L1", "K1"],
        2: ["L1", "L2", "K1"],
        3: ["L2", "L3", "D1"],
        4: ["L3", "L4", "D2"],
        5: ["L4", "D3", "D4"],
    }
    recommended = mapping.get(maturity_level, ["L1"])
    for module_code in recommended:
        conn.execute(
            """INSERT INTO user_progress (user_id, module_code, status, completion_pct, updated_at)
               VALUES (?, ?, 'not_started', 0, ?)
               ON CONFLICT(user_id, module_code) DO NOTHING""",
            (hub_user_id, module_code, now))
    conn.commit()
    conn.close()


# ============================================================================
# ADMIN QUERIES
# ============================================================================

def admin_overview():
    # type: () -> dict
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) as cnt FROM paddock_users").fetchone()["cnt"]
    completed = conn.execute("SELECT COUNT(*) as cnt FROM paddock_results").fetchone()["cnt"]
    avg_score = conn.execute(
        "SELECT COALESCE(AVG(overall_score), 0) as avg FROM paddock_results"
    ).fetchone()["avg"]

    # Maturity distribution
    dist = conn.execute(
        """SELECT maturity_level, COUNT(*) as cnt
           FROM paddock_results GROUP BY maturity_level ORDER BY maturity_level"""
    ).fetchall()

    # Module completion rates
    module_completion = conn.execute(
        """SELECT module, COUNT(DISTINCT user_id) as cnt
           FROM paddock_responses GROUP BY module"""
    ).fetchall()

    conn.close()
    return {
        "total_users": total,
        "completed": completed,
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
        "avg_score": round(avg_score, 1),
        "maturity_distribution": {r["maturity_level"]: r["cnt"] for r in dist},
        "module_completion": {r["module"]: r["cnt"] for r in module_completion},
    }


def admin_heatmap():
    # type: () -> dict
    conn = _get_conn()
    rows = conn.execute(
        """SELECT u.store, r.maturity_level, COUNT(*) as cnt
           FROM paddock_results r
           JOIN paddock_users u ON u.id = r.user_id
           GROUP BY u.store, r.maturity_level
           ORDER BY u.store"""
    ).fetchall()
    conn.close()
    heatmap = {}
    for r in rows:
        store = r["store"]
        if store not in heatmap:
            heatmap[store] = {}
        heatmap[store][r["maturity_level"]] = r["cnt"]
    return heatmap


def admin_gaps():
    # type: () -> dict
    conn = _get_conn()
    by_dept = conn.execute(
        """SELECT u.department, COUNT(*) as cnt, AVG(r.overall_score) as avg_score
           FROM paddock_results r
           JOIN paddock_users u ON u.id = r.user_id
           GROUP BY u.department ORDER BY avg_score"""
    ).fetchall()

    by_tier = conn.execute(
        """SELECT u.role_tier, COUNT(*) as cnt, AVG(r.overall_score) as avg_score
           FROM paddock_results r
           JOIN paddock_users u ON u.id = r.user_id
           GROUP BY u.role_tier ORDER BY u.role_tier"""
    ).fetchall()

    # Dunning-Kruger: confidence vs overall
    dk = conn.execute(
        """SELECT u.name, u.store, u.department, u.role_tier,
                  r.confidence_score, r.overall_score,
                  (r.confidence_score - r.overall_score) as gap
           FROM paddock_results r
           JOIN paddock_users u ON u.id = r.user_id
           ORDER BY ABS(gap) DESC LIMIT 20"""
    ).fetchall()

    conn.close()
    return {
        "by_department": [_row_to_dict(r) for r in by_dept],
        "by_tier": [_row_to_dict(r) for r in by_tier],
        "dunning_kruger": [_row_to_dict(r) for r in dk],
    }


def admin_insights():
    # type: () -> dict
    conn = _get_conn()
    ready_depts = conn.execute(
        """SELECT u.department, COUNT(*) as cnt, AVG(r.overall_score) as avg_score
           FROM paddock_results r
           JOIN paddock_users u ON u.id = r.user_id
           GROUP BY u.department ORDER BY avg_score DESC LIMIT 5"""
    ).fetchall()

    need_support = conn.execute(
        """SELECT u.store, COUNT(*) as cnt, AVG(r.overall_score) as avg_score
           FROM paddock_results r
           JOIN paddock_users u ON u.id = r.user_id
           GROUP BY u.store ORDER BY avg_score ASC LIMIT 5"""
    ).fetchall()

    hidden_champions = conn.execute(
        """SELECT u.name, u.store, u.department, u.role_tier, r.overall_score
           FROM paddock_results r
           JOIN paddock_users u ON u.id = r.user_id
           WHERE u.role_tier <= 2 AND r.overall_score >= 60
           ORDER BY r.overall_score DESC LIMIT 10"""
    ).fetchall()

    quick_wins = conn.execute(
        """SELECT u.department, COUNT(*) as cnt,
                  AVG(r.confidence_score) as avg_confidence,
                  AVG(r.overall_score) as avg_ability
           FROM paddock_results r
           JOIN paddock_users u ON u.id = r.user_id
           GROUP BY u.department
           HAVING avg_confidence > avg_ability
           ORDER BY (avg_confidence - avg_ability) DESC"""
    ).fetchall()

    conn.close()
    return {
        "ready_departments": [_row_to_dict(r) for r in ready_depts],
        "need_support": [_row_to_dict(r) for r in need_support],
        "hidden_champions": [_row_to_dict(r) for r in hidden_champions],
        "quick_wins": [_row_to_dict(r) for r in quick_wins],
    }


def admin_feedback_summary():
    # type: () -> dict
    conn = _get_conn()
    avg_rating = conn.execute(
        "SELECT COALESCE(AVG(experience_rating), 0) as avg, COUNT(*) as cnt FROM paddock_feedback"
    ).fetchone()

    verbatims = conn.execute(
        """SELECT f.experience_rating, f.confusion_notes, f.improvement_suggestions,
                  u.name, u.store, u.department, f.created_at
           FROM paddock_feedback f
           JOIN paddock_users u ON u.id = f.user_id
           ORDER BY f.created_at DESC LIMIT 50"""
    ).fetchall()

    # Free-text answers from modules (u8, ap_xx_5, h4, h5)
    free_text = conn.execute(
        """SELECT r.question_id, r.answer, u.name, u.store, u.role_tier
           FROM paddock_responses r
           JOIN paddock_users u ON u.id = r.user_id
           WHERE r.question_id IN ('u8', 'ap_34_5', 'ap_56_5', 'h4', 'h5')
           ORDER BY r.created_at DESC LIMIT 100"""
    ).fetchall()

    conn.close()
    return {
        "avg_rating": round(avg_rating["avg"], 1),
        "total_feedback": avg_rating["cnt"],
        "verbatims": [_row_to_dict(r) for r in verbatims],
        "free_text": [_row_to_dict(r) for r in free_text],
    }


def admin_export():
    # type: () -> list
    conn = _get_conn()
    rows = conn.execute(
        """SELECT u.id, u.name, u.employee_id, u.store, u.department,
                  u.role_tier, u.tech_comfort, u.ai_experience, u.created_at,
                  r.maturity_level, r.awareness_score, r.usage_score,
                  r.critical_score, r.applied_score, r.confidence_score,
                  r.overall_score
           FROM paddock_users u
           LEFT JOIN paddock_results r ON r.user_id = u.id
           ORDER BY u.created_at DESC"""
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def delete_user_data(user_id):
    # type: (int) -> None
    conn = _get_conn()
    conn.execute("DELETE FROM paddock_feedback WHERE user_id = ?", (int(user_id),))
    conn.execute("DELETE FROM paddock_results WHERE user_id = ?", (int(user_id),))
    conn.execute("DELETE FROM paddock_responses WHERE user_id = ?", (int(user_id),))
    conn.execute("DELETE FROM paddock_users WHERE id = ?", (int(user_id),))
    conn.commit()
    conn.close()
