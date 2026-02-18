"""Gamified Agent Ecosystem — 6 competing AI agents earning points for business value.

Each agent specialises in a domain (stockout recovery, basket optimisation, etc.)
and earns points through the presentation-rubric grading pipeline and revenue
identification.  Points, multipliers and achievements drive a real-time leaderboard
displayed in the Hub Portal Scoreboard tab.
"""

import logging
import sqlite3
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1A  GAME AGENTS REGISTRY
# ---------------------------------------------------------------------------

GAME_AGENTS = [
    {
        "name": "StockoutRevenueHunter",
        "specialty": "Stockout revenue recovery",
        "category": "REVENUE_OPTIMIZATION",
        "analysis_types": ["intraday_stockout", "stockout_detection"],
        "system_prompt": (
            "You are StockoutRevenueHunter, an AI agent specialising in "
            "identifying revenue lost to out-of-stock events across Harris Farm "
            "Markets' 34 stores.  Analyse intra-day transaction gaps, detect "
            "zero-sale windows for historically active SKUs, and quantify the "
            "dollar value of lost sales.  Prioritise high-margin perishables "
            "and produce.  Present actionable recommendations for replenishment "
            "timing, safety-stock adjustments, and supplier lead-time improvements."
        ),
    },
    {
        "name": "CrossSellRevenueEngine",
        "specialty": "Basket optimisation and cross-sell",
        "category": "REVENUE_OPTIMIZATION",
        "analysis_types": ["basket_analysis"],
        "system_prompt": (
            "You are CrossSellRevenueEngine, an AI agent focused on basket "
            "analysis and cross-sell opportunities.  Mine 383M+ POS transactions "
            "to uncover high-affinity product pairs, under-penetrated combos, "
            "and seasonal bundles.  Calculate incremental revenue from targeted "
            "promotions and in-store adjacency changes.  Deliver buyer-ready "
            "recommendations with clear financial projections."
        ),
    },
    {
        "name": "BuyerInsightDashboarder",
        "specialty": "Actionable buyer reports and dashboards",
        "category": "DATA_VISIBILITY",
        "analysis_types": ["demand_pattern"],
        "system_prompt": (
            "You are BuyerInsightDashboarder, an AI agent that transforms raw "
            "data into Board-ready reports and dashboards for Harris Farm "
            "buyers.  Focus on demand patterns, seasonal trends, and category "
            "performance.  Every output must include executive summary, key "
            "metrics, and specific next-step actions.  Aim for Board-ready "
            "rubric scores (>= 9.0/10) on every report."
        ),
    },
    {
        "name": "StoreManagerOptimizer",
        "specialty": "Operational efficiencies and slow-mover identification",
        "category": "OPERATIONAL_EFFICIENCY",
        "analysis_types": ["slow_movers"],
        "system_prompt": (
            "You are StoreManagerOptimizer, an AI agent helping store managers "
            "improve operational efficiency.  Identify slow-moving lines for "
            "range review, flag waste-prone items, and recommend markdown "
            "strategies.  Quantify cost savings from reduced waste and improved "
            "shelf utilisation.  Deliver store-level action plans with clear "
            "KPIs and timelines."
        ),
    },
    {
        "name": "FabricIntegrationStrategist",
        "specialty": "Fabric integration and strategic planning",
        "category": "STRATEGIC_PLANNING",
        "analysis_types": ["demand_pattern"],
        "system_prompt": (
            "You are FabricIntegrationStrategist, an AI agent focused on "
            "strategic data integration.  Design plans for connecting Harris "
            "Farm's transaction data with supplier systems, loyalty platforms, "
            "and external market data.  Evaluate technology options, estimate "
            "implementation effort, and project ROI.  Produce Board-ready "
            "strategic proposals with clear milestones."
        ),
    },
    {
        "name": "TransactionInsightMiner",
        "specialty": "Hidden pattern discovery in transaction data",
        "category": "INSIGHTS",
        "analysis_types": ["price_dispersion"],
        "system_prompt": (
            "You are TransactionInsightMiner, an AI agent specialising in "
            "discovering hidden patterns in 383M+ POS transactions.  Analyse "
            "price dispersion across stores, detect anomalous pricing, find "
            "time-of-day and day-of-week effects, and surface non-obvious "
            "correlations.  Quantify the financial impact of every insight "
            "and recommend concrete actions."
        ),
    },
]

# ---------------------------------------------------------------------------
# 1B  POINTS CONFIGURATION
# ---------------------------------------------------------------------------

POINTS_CONFIG = {
    "task_completed": 100,
    "rubric_board_ready": 300,      # avg >= 9.0
    "rubric_reviewed": 150,         # avg >= 7.0
    "revenue_per_10k": 1000,        # per $10K identified
    "dashboard_design": 150,        # DASHBOARD_DESIGN task type
    "planning_task": 400,           # PLANNING task type
}

MULTIPLIERS = {
    "first_to_identify": 2.0,
    "implemented_fast": 2.0,        # < 24 hrs
    "board_cited": 3.0,
}

# ---------------------------------------------------------------------------
# 1D  ACHIEVEMENTS
# ---------------------------------------------------------------------------

ACHIEVEMENTS = [
    {
        "code": "first_analysis",
        "name": "First Analysis",
        "description": "Complete your first analysis task",
        "criteria_fn": "_check_first_analysis",
        "points": 10,
    },
    {
        "code": "consistent_5",
        "name": "Consistent Performer",
        "description": "5 tasks scored above 9.0",
        "criteria_fn": "_check_consistent_5",
        "points": 50,
    },
    {
        "code": "board_ready_10",
        "name": "Board-Ready Streak",
        "description": "10 Board-ready grades",
        "criteria_fn": "_check_board_ready_10",
        "points": 100,
    },
    {
        "code": "revenue_hunter",
        "name": "Revenue Hunter",
        "description": "$100K+ revenue identified",
        "criteria_fn": "_check_revenue_hunter",
        "points": 200,
    },
    {
        "code": "top_scorer",
        "name": "Top Scorer",
        "description": "Highest points on the leaderboard",
        "criteria_fn": "_check_top_scorer",
        "points": 150,
    },
]


# ---------------------------------------------------------------------------
# 1C  CORE FUNCTIONS
# ---------------------------------------------------------------------------

def seed_game_agents(db_path):
    """Insert or update the 6 game agents.  Idempotent."""
    conn = sqlite3.connect(db_path)
    inserted = 0
    for agent in GAME_AGENTS:
        try:
            conn.execute(
                "INSERT INTO game_agents (name, specialty, category, system_prompt) "
                "VALUES (?, ?, ?, ?)",
                (agent["name"], agent["specialty"],
                 agent["category"], agent["system_prompt"]),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            conn.execute(
                "UPDATE game_agents SET specialty = ?, category = ?, "
                "system_prompt = ?, updated_at = datetime('now') "
                "WHERE name = ?",
                (agent["specialty"], agent["category"],
                 agent["system_prompt"], agent["name"]),
            )
    conn.commit()
    conn.close()
    logger.info("Seeded game agents: %d new, %d updated",
                inserted, len(GAME_AGENTS) - inserted)
    return inserted


def seed_initial_tasks(db_path):
    """Seed 3 tasks per agent (18 total) as APPROVED proposals.  Idempotent."""
    TASKS = {
        "StockoutRevenueHunter": [
            ("ANALYSIS", "Detect intra-day stockouts at top 5 revenue stores for the last 14 days"),
            ("ANALYSIS", "Quantify lost revenue from zero-sale windows in produce and dairy"),
            ("ANALYSIS", "Identify replenishment timing gaps for high-margin perishables"),
        ],
        "CrossSellRevenueEngine": [
            ("ANALYSIS", "Find top 20 cross-sell product pairs across all stores"),
            ("ANALYSIS", "Identify under-penetrated basket combos in premium categories"),
            ("ANALYSIS", "Calculate incremental revenue from seasonal bundle promotions"),
        ],
        "BuyerInsightDashboarder": [
            ("ANALYSIS", "Generate Board-ready demand pattern report for produce category"),
            ("ANALYSIS", "Create buyer briefing on seasonal trend shifts across departments"),
            ("ANALYSIS", "Build weekly category performance summary with action items"),
        ],
        "StoreManagerOptimizer": [
            ("ANALYSIS", "Identify slow-moving lines for range review across all stores"),
            ("ANALYSIS", "Flag waste-prone items and recommend markdown strategies"),
            ("ANALYSIS", "Calculate cost savings from improved shelf utilisation"),
        ],
        "FabricIntegrationStrategist": [
            ("ANALYSIS", "Design data integration plan for supplier replenishment systems"),
            ("ANALYSIS", "Evaluate technology options for loyalty platform connection"),
            ("ANALYSIS", "Project ROI for external market data integration"),
        ],
        "TransactionInsightMiner": [
            ("ANALYSIS", "Analyse price dispersion across all 34 stores for top 100 SKUs"),
            ("ANALYSIS", "Detect time-of-day and day-of-week purchasing patterns"),
            ("ANALYSIS", "Surface anomalous pricing events and quantify financial impact"),
        ],
    }

    conn = sqlite3.connect(db_path)
    inserted = 0
    for agent_name, tasks in TASKS.items():
        for task_type, description in tasks:
            # Check for existing identical task
            existing = conn.execute(
                "SELECT id FROM agent_proposals "
                "WHERE agent_name = ? AND description = ?",
                (agent_name, description),
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO agent_proposals "
                    "(agent_name, task_type, description, status, risk_level) "
                    "VALUES (?, ?, ?, 'APPROVED', 'LOW')",
                    (agent_name, task_type, description),
                )
                inserted += 1
    conn.commit()
    conn.close()
    logger.info("Seeded game tasks: %d new (18 total defined)", inserted)
    return inserted


def calculate_points(task_type, rubric_grade, rubric_avg, revenue_impact=0):
    """Calculate total points earned for a completed task.

    Returns (base_points, bonus_points, breakdown_str).
    """
    base = POINTS_CONFIG["task_completed"]
    bonus = 0
    parts = ["base:{}".format(base)]

    # Rubric quality bonus
    if rubric_avg >= 9.0:
        bonus += POINTS_CONFIG["rubric_board_ready"]
        parts.append("board_ready:{}".format(POINTS_CONFIG["rubric_board_ready"]))
    elif rubric_avg >= 7.0:
        bonus += POINTS_CONFIG["rubric_reviewed"]
        parts.append("reviewed:{}".format(POINTS_CONFIG["rubric_reviewed"]))

    # Revenue bonus (per $10K)
    if revenue_impact > 0:
        rev_units = int(revenue_impact / 10000)
        if rev_units > 0:
            rev_bonus = rev_units * POINTS_CONFIG["revenue_per_10k"]
            bonus += rev_bonus
            parts.append("revenue:{}".format(rev_bonus))

    # Task type bonuses
    if task_type == "DASHBOARD_DESIGN":
        bonus += POINTS_CONFIG["dashboard_design"]
        parts.append("dashboard:{}".format(POINTS_CONFIG["dashboard_design"]))
    elif task_type == "PLANNING":
        bonus += POINTS_CONFIG["planning_task"]
        parts.append("planning:{}".format(POINTS_CONFIG["planning_task"]))

    total = base + bonus
    breakdown = ",".join(parts)
    return total, breakdown


def award_game_points(db_path, agent_name, proposal_id, points, breakdown,
                      multiplier=1.0):
    """Award points to a game agent.  Updates totals and logs the award."""
    final_points = int(points * multiplier)

    conn = sqlite3.connect(db_path)
    try:
        # Log the point award
        conn.execute(
            "INSERT INTO game_points_log "
            "(agent_name, proposal_id, points, breakdown, multiplier) "
            "VALUES (?, ?, ?, ?, ?)",
            (agent_name, proposal_id, final_points, breakdown, multiplier),
        )

        # Update agent totals
        conn.execute(
            "UPDATE game_agents SET "
            "total_points = total_points + ?, "
            "reports_completed = reports_completed + 1, "
            "updated_at = datetime('now') "
            "WHERE name = ?",
            (final_points, agent_name),
        )

        conn.commit()
    finally:
        conn.close()

    logger.info("Awarded %d points to %s (proposal #%d, x%.1f)",
                final_points, agent_name, proposal_id, multiplier)
    return final_points


def update_agent_rubric(db_path, agent_name, rubric_avg):
    """Update the running average rubric score for an agent."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT reports_completed, avg_rubric_score FROM game_agents "
            "WHERE name = ?", (agent_name,)
        ).fetchone()
        if row:
            n = row[0]
            old_avg = row[1] or 0.0
            # Running average: new_avg = (old_avg * (n-1) + new_score) / n
            if n > 0:
                new_avg = (old_avg * (n - 1) + rubric_avg) / n
            else:
                new_avg = rubric_avg
            conn.execute(
                "UPDATE game_agents SET avg_rubric_score = ?, "
                "updated_at = datetime('now') WHERE name = ?",
                (round(new_avg, 2), agent_name),
            )
            conn.commit()
    finally:
        conn.close()


def update_agent_revenue(db_path, agent_name, revenue_amount):
    """Add revenue found to an agent's running total."""
    if revenue_amount <= 0:
        return
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE game_agents SET "
            "revenue_found = revenue_found + ?, "
            "updated_at = datetime('now') "
            "WHERE name = ?",
            (revenue_amount, agent_name),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# ACHIEVEMENT CHECKING
# ---------------------------------------------------------------------------

def _check_first_analysis(conn, agent_name):
    """Has the agent completed at least 1 task?"""
    row = conn.execute(
        "SELECT reports_completed FROM game_agents WHERE name = ?",
        (agent_name,),
    ).fetchone()
    return row and row[0] >= 1


def _check_consistent_5(conn, agent_name):
    """Has the agent completed 5+ tasks with score > 9.0?"""
    row = conn.execute(
        "SELECT COUNT(*) FROM agent_scores "
        "WHERE agent_name = ? AND score >= 9.0",
        (agent_name,),
    ).fetchone()
    return row and row[0] >= 5


def _check_board_ready_10(conn, agent_name):
    """Has the agent earned 10+ Board-ready grades?"""
    row = conn.execute(
        "SELECT COUNT(*) FROM intelligence_reports "
        "WHERE analysis_type IN ("
        "  SELECT description FROM agent_proposals WHERE agent_name = ?"
        ") AND rubric_grade = 'Board-ready'",
        (agent_name,),
    ).fetchone()
    # Fallback: count from agent_scores with high scores
    if not row or row[0] < 10:
        row = conn.execute(
            "SELECT COUNT(*) FROM agent_scores "
            "WHERE agent_name = ? AND score >= 9.0",
            (agent_name,),
        ).fetchone()
    return row and row[0] >= 10


def _check_revenue_hunter(conn, agent_name):
    """Has the agent identified $100K+ in revenue?"""
    row = conn.execute(
        "SELECT revenue_found FROM game_agents WHERE name = ?",
        (agent_name,),
    ).fetchone()
    return row and row[0] >= 100000


def _check_top_scorer(conn, agent_name):
    """Is this agent currently the top scorer?"""
    row = conn.execute(
        "SELECT name FROM game_agents WHERE active = 1 "
        "ORDER BY total_points DESC LIMIT 1",
    ).fetchone()
    return row and row[0] == agent_name


_ACHIEVEMENT_CHECKS = {
    "first_analysis": _check_first_analysis,
    "consistent_5": _check_consistent_5,
    "board_ready_10": _check_board_ready_10,
    "revenue_hunter": _check_revenue_hunter,
    "top_scorer": _check_top_scorer,
}


def check_game_achievements(db_path, agent_name):
    """Check and award any newly earned achievements for an agent."""
    conn = sqlite3.connect(db_path)
    awarded = []
    try:
        # Get already-earned achievements
        earned = {
            r[0] for r in conn.execute(
                "SELECT achievement_code FROM game_achievements "
                "WHERE agent_name = ?", (agent_name,)
            ).fetchall()
        }

        for ach in ACHIEVEMENTS:
            code = ach["code"]
            if code in earned:
                continue

            check_fn = _ACHIEVEMENT_CHECKS.get(code)
            if check_fn and check_fn(conn, agent_name):
                try:
                    conn.execute(
                        "INSERT INTO game_achievements "
                        "(agent_name, achievement_code, achievement_name, points_awarded) "
                        "VALUES (?, ?, ?, ?)",
                        (agent_name, code, ach["name"], ach["points"]),
                    )
                    # Add achievement points to agent total
                    conn.execute(
                        "UPDATE game_agents SET total_points = total_points + ? "
                        "WHERE name = ?",
                        (ach["points"], agent_name),
                    )
                    awarded.append(code)
                    logger.info("Achievement unlocked: %s -> %s (+%d pts)",
                                agent_name, ach["name"], ach["points"])
                except sqlite3.IntegrityError:
                    pass  # Already earned (race condition)

        conn.commit()
    finally:
        conn.close()

    return awarded


# ---------------------------------------------------------------------------
# LEADERBOARD & DETAIL
# ---------------------------------------------------------------------------

def get_game_leaderboard(db_path):
    """Return ranked list of all game agents with stats."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT name, specialty, category, total_points, "
            "reports_completed, reports_implemented, avg_rubric_score, "
            "revenue_found, active "
            "FROM game_agents ORDER BY total_points DESC"
        ).fetchall()
        result = []
        for i, row in enumerate(rows):
            entry = dict(row)
            entry["rank"] = i + 1
            result.append(entry)
        return result
    finally:
        conn.close()


def get_agent_game_detail(db_path, agent_name):
    """Full stats for a single game agent."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Agent basics
        agent = conn.execute(
            "SELECT * FROM game_agents WHERE name = ?",
            (agent_name,),
        ).fetchone()
        if not agent:
            return None

        detail = dict(agent)

        # Achievements
        achs = conn.execute(
            "SELECT achievement_code, achievement_name, points_awarded, earned_at "
            "FROM game_achievements WHERE agent_name = ? ORDER BY earned_at",
            (agent_name,),
        ).fetchall()
        detail["achievements"] = [dict(a) for a in achs]

        # Recent points log
        points_log = conn.execute(
            "SELECT proposal_id, points, breakdown, multiplier, created_at "
            "FROM game_points_log WHERE agent_name = ? "
            "ORDER BY created_at DESC LIMIT 10",
            (agent_name,),
        ).fetchall()
        detail["recent_points"] = [dict(p) for p in points_log]

        # Recent proposals
        proposals = conn.execute(
            "SELECT id, task_type, description, status, created_at "
            "FROM agent_proposals WHERE agent_name = ? "
            "ORDER BY created_at DESC LIMIT 10",
            (agent_name,),
        ).fetchall()
        detail["recent_proposals"] = [dict(p) for p in proposals]

        return detail
    finally:
        conn.close()


def get_game_status(db_path):
    """Aggregate game statistics."""
    conn = sqlite3.connect(db_path)
    try:
        totals = conn.execute(
            "SELECT COUNT(*) as agent_count, "
            "COALESCE(SUM(total_points), 0) as total_points, "
            "COALESCE(SUM(reports_completed), 0) as total_reports, "
            "COALESCE(SUM(revenue_found), 0) as total_revenue, "
            "COALESCE(AVG(avg_rubric_score), 0) as avg_score "
            "FROM game_agents WHERE active = 1"
        ).fetchone()

        achievements_count = conn.execute(
            "SELECT COUNT(*) FROM game_achievements"
        ).fetchone()[0]

        approved_waiting = conn.execute(
            "SELECT COUNT(*) FROM agent_proposals WHERE status = 'APPROVED'"
        ).fetchone()[0]

        return {
            "agent_count": totals[0],
            "total_points": totals[1],
            "total_reports": totals[2],
            "total_revenue": round(totals[3], 2),
            "avg_rubric_score": round(totals[4], 2),
            "achievements_earned": achievements_count,
            "approved_waiting": approved_waiting,
        }
    finally:
        conn.close()


def get_all_achievements(db_path):
    """Return all earned achievements across all agents."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT agent_name, achievement_code, achievement_name, "
            "points_awarded, earned_at "
            "FROM game_achievements ORDER BY earned_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
