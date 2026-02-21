"""
Harris Farm Hub — Goals Framework (G1-G5)
The 5 Goals define WHY The Hub exists:
  G1: Bring Strategy to Life
  G2: Democratise Data
  G3: Train Our Superstars
  G4: Fast-Track Supply Chain
  G5: Always Improve
"""

import logging
import sqlite3
from pathlib import Path

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# The 5 Goals
# ---------------------------------------------------------------------------

HUB_GOALS = {
    "G1": {
        "id": "G1",
        "title": "Bring Strategy to Life",
        "short": "Strategy",
        "icon": "\U0001f4cd",
        "color": "#2d8659",
        "description": (
            "Make Harris Farm's 'Fewer, Bigger, Better' strategy visible, measurable, "
            "and actionable through live dashboards and intelligence reports."
        ),
        "key_question": "Can any Harris Farmer see how their work connects to the strategy?",
        "measures": [
            "Intelligence reports generated",
            "Strategic proposals implemented",
        ],
        "pillars_served": ["P1", "P2", "P4", "P5"],
        "status": "LIVE",
    },
    "G2": {
        "id": "G2",
        "title": "Democratise Data",
        "short": "Data",
        "icon": "\U0001f4ca",
        "color": "#3b82f6",
        "description": (
            "Put data into the hands of every Harris Farmer — from store managers checking "
            "weekend sales to buyers optimising orders with weather forecasts."
        ),
        "key_question": "Can a store manager answer their own data question without IT help?",
        "measures": [
            "Unique data users",
            "Queries generated",
        ],
        "pillars_served": ["P2", "P4", "P5"],
        "status": "LIVE",
    },
    "G3": {
        "id": "G3",
        "title": "Train Our Superstars",
        "short": "Superstars",
        "icon": "\U0001f31f",
        "color": "#a855f7",
        "description": (
            "Build AI capability across the business — from Seed to Legend. Every Harris "
            "Farmer should feel confident using AI as a job partner, not a replacement."
        ),
        "key_question": "Is every team member growing their AI skills at their own pace?",
        "measures": [
            "Learning paths started",
            "Prompts practised",
        ],
        "pillars_served": ["P3", "P5"],
        "status": "LIVE",
    },
    "G4": {
        "id": "G4",
        "title": "Fast-Track Supply Chain",
        "short": "Supply Chain",
        "icon": "\U0001f69a",
        "color": "#f59e0b",
        "description": (
            "Use AI to tidy up the supply chain from pay to purchase — reduce out-of-stocks, "
            "optimise buying, and get Grant Enders' vision into the data."
        ),
        "key_question": "Are we reducing waste and out-of-stocks measurably, week on week?",
        "measures": [
            "Operations agent proposals",
            "Supply chain analyses run",
        ],
        "pillars_served": ["P4"],
        "status": "LIVE",
    },
    "G5": {
        "id": "G5",
        "title": "Always Improve",
        "short": "Improve",
        "icon": "\U0001f504",
        "color": "#ef4444",
        "description": (
            "The Hub watches itself. WATCHDOG governance, self-improvement cycles, and "
            "continuous quality scoring ensure we get better every iteration."
        ),
        "key_question": "Is The Hub measurably better this week than last week?",
        "measures": [
            "Improvement findings actioned",
            "Average quality score",
        ],
        "pillars_served": ["P5"],
        "status": "LIVE",
    },
}

# ---------------------------------------------------------------------------
# Goal-to-Page mapping — which goals does each dashboard serve?
# ---------------------------------------------------------------------------

GOAL_PAGE_MAPPING = {
    "greater-goodness": ["G1"],
    "customers": ["G1", "G2"],
    "market-share": ["G1", "G2"],
    "learning-centre": ["G3"],
    "hub-assistant": ["G2", "G3"],
    "academy": ["G3"],
    "ai-adoption": ["G3", "G5"],
    "sales": ["G1", "G2", "G4"],
    "profitability": ["G1", "G2", "G4"],
    "transport": ["G4"],
    "store-ops": ["G2", "G4"],
    "buying-hub": ["G2", "G4"],
    "product-intel": ["G2", "G4"],
    "plu-intel": ["G2", "G4"],
    "prompt-builder": ["G2", "G3"],
    "the-rubric": ["G3", "G5"],
    "trending": ["G5"],
    "revenue-bridge": ["G1", "G2"],
    "mission-control": ["G1", "G5"],
    "agent-hub": ["G1", "G5"],
    "analytics-engine": ["G2", "G4"],
    "agent-ops": ["G1", "G5"],
}

# Analysis-type to goal mapping — used by activity feed for contextual tagging
_ANALYSIS_GOAL_MAP = {
    "basket": ["G2", "G4"],
    "stockout": ["G4"],
    "intraday_stockout": ["G4"],
    "price": ["G1", "G4"],
    "demand": ["G4"],
    "slow_movers": ["G4"],
    "halo_effect": ["G2", "G4"],
    "specials_uplift": ["G1", "G4"],
    "margin_analysis": ["G1", "G4"],
    "customer_analysis": ["G1", "G2"],
    "store_benchmark": ["G2", "G4"],
}

# Supply chain analysis types (for G4 metric filtering)
_SUPPLY_CHAIN_TYPES = (
    "basket", "stockout", "intraday_stockout", "demand",
    "slow_movers", "halo_effect", "specials_uplift", "margin_analysis",
)

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

_HUB_DATA_DB = Path(__file__).resolve().parent.parent.parent / "backend" / "hub_data.db"


def get_goal(goal_id: str) -> dict:
    """Return goal dict for G1-G5, or empty dict if not found."""
    return HUB_GOALS.get(goal_id, {})


def get_goals_for_page(slug: str) -> list:
    """Return list of goal dicts for a given page slug."""
    goal_ids = GOAL_PAGE_MAPPING.get(slug, [])
    return [HUB_GOALS[gid] for gid in goal_ids if gid in HUB_GOALS]


def goals_for_analysis_type(analysis_type: str) -> list:
    """Return goal IDs for a given analysis type."""
    return _ANALYSIS_GOAL_MAP.get(analysis_type, ["G2"])


def goal_badge_html(goal_id: str) -> str:
    """Return a small inline HTML badge for a goal (e.g. 'G1 Strategy')."""
    goal = HUB_GOALS.get(goal_id)
    if not goal:
        return ""
    return (
        f"<span style='display:inline-block;background:{goal['color']}20;"
        f"color:{goal['color']};border:1px solid {goal['color']}50;"
        f"border-radius:12px;padding:2px 10px;font-size:0.75em;"
        f"font-weight:600;margin:0 2px;'>"
        f"{goal['icon']} {goal_id}: {goal['short']}</span>"
    )


def _safe_count(conn, sql: str) -> int:
    """Execute a COUNT query safely, returning 0 on error."""
    try:
        result = conn.execute(sql).fetchone()
        return result[0] if result and result[0] else 0
    except Exception:
        return 0


def _get_conn():
    """Get a SQLite connection to hub_data.db, or None if not available."""
    if not _HUB_DATA_DB.exists():
        return None
    return sqlite3.connect(str(_HUB_DATA_DB))


def fetch_all_goal_metrics() -> dict:
    """Pull live metrics for ALL goals in a single DB connection.

    Returns dict of goal_id → {metrics: {...}, progress: int}.
    Much more efficient than calling fetch_goal_metrics() per goal.
    """
    empty = {gid: {"metrics": {}, "progress": 0} for gid in HUB_GOALS}

    conn = _get_conn()
    if not conn:
        return empty

    try:
        # G1: Strategy
        reports = _safe_count(conn, "SELECT COUNT(*) FROM intelligence_reports")
        implemented = _safe_count(
            conn, "SELECT COUNT(*) FROM arena_proposals WHERE status='IMPLEMENTED'"
        )
        g1_total = reports + implemented
        empty["G1"] = {
            "metrics": {"Intelligence Reports": reports, "Proposals Implemented": implemented},
            "progress": min(100, int((g1_total / 200) * 100)) if g1_total else 0,
        }

        # G2: Data
        users = _safe_count(
            conn, "SELECT COUNT(DISTINCT user_id) FROM queries WHERE user_id IS NOT NULL"
        )
        queries = _safe_count(conn, "SELECT COUNT(*) FROM generated_queries")
        g2_total = users + queries
        empty["G2"] = {
            "metrics": {"Data Users": users, "Queries Generated": queries},
            "progress": min(100, int((g2_total / 50) * 100)) if g2_total else 0,
        }

        # G3: Superstars
        prompts = _safe_count(conn, "SELECT COUNT(*) FROM prompt_templates")
        lessons = _safe_count(conn, "SELECT COUNT(*) FROM lessons")
        g3_total = prompts + lessons
        empty["G3"] = {
            "metrics": {"Prompt Templates": prompts, "Lessons Available": lessons},
            "progress": min(100, int((g3_total / 30) * 100)) if g3_total else 0,
        }

        # G4: Supply Chain (parameterized to avoid SQL interpolation)
        placeholders = ", ".join("?" for _ in _SUPPLY_CHAIN_TYPES)
        try:
            ops_proposals = conn.execute(
                f"SELECT COUNT(*) FROM agent_proposals WHERE task_type IN ({placeholders})",
                _SUPPLY_CHAIN_TYPES,
            ).fetchone()[0] or 0
        except Exception:
            ops_proposals = 0
        try:
            sc_reports = conn.execute(
                f"SELECT COUNT(*) FROM intelligence_reports WHERE analysis_type IN ({placeholders})",
                _SUPPLY_CHAIN_TYPES,
            ).fetchone()[0] or 0
        except Exception:
            sc_reports = 0
        g4_total = ops_proposals + sc_reports
        empty["G4"] = {
            "metrics": {"Supply Chain Proposals": ops_proposals, "Supply Chain Reports": sc_reports},
            "progress": min(100, int((g4_total / 100) * 100)) if g4_total else 0,
        }

        # G5: Improve
        findings = _safe_count(conn, "SELECT COUNT(*) FROM improvement_findings")
        scores = _safe_count(conn, "SELECT COUNT(*) FROM task_scores")
        g5_total = findings + scores
        empty["G5"] = {
            "metrics": {"Improvement Findings": findings, "Quality Scores Logged": scores},
            "progress": min(100, int((g5_total / 400) * 100)) if g5_total else 0,
        }

    except Exception as exc:
        _log.warning("fetch_all_goal_metrics failed: %s", exc)
    finally:
        conn.close()

    return empty


def fetch_goal_metrics(goal_id: str) -> dict:
    """Pull live metrics for a single goal. Delegates to fetch_all_goal_metrics."""
    return fetch_all_goal_metrics().get(goal_id, {"metrics": {}, "progress": 0})


def fetch_watchdog_scores() -> list:
    """Pull average WATCHDOG H/R/S/C/D/U/X scores from task_scores.

    Returns list of 7 floats (one per criterion), defaulting to 7.0.
    """
    values = [7.0] * 7
    conn = _get_conn()
    if not conn:
        return values
    try:
        for i, c in enumerate(["h", "r", "s", "c", "d", "u", "x"]):
            row = conn.execute(
                f"SELECT AVG({c}) FROM task_scores WHERE {c} > 0"
            ).fetchone()
            if row and row[0]:
                values[i] = round(row[0], 1)
    except Exception:
        pass
    finally:
        conn.close()
    return values


def fetch_recent_activity(limit: int = 12) -> list:
    """Pull recent activity from hub_data.db for the front page feed.

    Returns list of dicts with type, title, detail, timestamp, goal_ids.
    Goal tagging is contextual based on analysis_type/task_type.
    """
    conn = _get_conn()
    if not conn:
        return []

    items = []
    try:
        # Intelligence reports — tag based on analysis_type
        for row in conn.execute(
            "SELECT title, analysis_type, rubric_grade, created_at "
            "FROM intelligence_reports ORDER BY created_at DESC LIMIT 5"
        ).fetchall():
            analysis_type = row[1] or ""
            items.append({
                "type": "report",
                "icon": "\U0001f4dd",
                "title": row[0] or f"{analysis_type} analysis",
                "detail": f"Grade: {row[2]}" if row[2] else analysis_type,
                "timestamp": row[3] or "",
                "goal_ids": goals_for_analysis_type(analysis_type),
            })

        # Agent proposals — tag based on task_type
        for row in conn.execute(
            "SELECT description, status, task_type, created_at "
            "FROM agent_proposals ORDER BY created_at DESC LIMIT 3"
        ).fetchall():
            task_type = row[2] or ""
            items.append({
                "type": "agent",
                "icon": "\U0001f916",
                "title": (row[0] or "Agent task")[:80],
                "detail": row[1] or "",
                "timestamp": row[3] or "",
                "goal_ids": goals_for_analysis_type(task_type),
            })

        # Improvement findings — always G5
        for row in conn.execute(
            "SELECT title, severity, category, created_at "
            "FROM improvement_findings ORDER BY created_at DESC LIMIT 3"
        ).fetchall():
            items.append({
                "type": "improvement",
                "icon": "\U0001f527",
                "title": row[0] or "Improvement finding",
                "detail": f"{row[1]} — {row[2]}" if row[1] and row[2] else (row[1] or row[2] or ""),
                "timestamp": row[3] or "",
                "goal_ids": ["G5"],
            })

        # WATCHDOG audits — always G5
        for row in conn.execute(
            "SELECT title, risk_level, finding_count, analyzed_at "
            "FROM watchdog_audit ORDER BY analyzed_at DESC LIMIT 2"
        ).fetchall():
            items.append({
                "type": "watchdog",
                "icon": "\U0001f6e1\ufe0f",
                "title": row[0] or "WATCHDOG audit",
                "detail": f"Risk: {row[1]}, Findings: {row[2]}",
                "timestamp": row[3] or "",
                "goal_ids": ["G5"],
            })

    except Exception:
        pass
    finally:
        conn.close()

    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return items[:limit]
