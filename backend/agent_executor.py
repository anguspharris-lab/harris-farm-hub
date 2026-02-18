"""
Harris Farm Hub — Agent Executor
Polls agent_proposals for APPROVED tasks, routes them to real analysis
functions, scores with the presentation rubric, stores results in
intelligence_reports, and marks the proposal COMPLETED.

Usage:
    python3 agent_executor.py              # foreground (Ctrl+C to stop)
    python3 agent_executor.py --once       # single pass, no loop
"""

import json
import os
import re
import sqlite3
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Ensure backend/ is on the path
_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here))

from app import config

logger = logging.getLogger("agent_executor")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

POLL_INTERVAL = int(os.getenv("EXECUTOR_POLL_INTERVAL", "30"))

# Map agent_name keywords → analysis_type(s)
AGENT_ANALYSIS_MAP = {
    "StockoutAnalyzer": ["intraday_stockout", "stockout_detection"],
    "BasketAnalyzer": ["basket_analysis"],
    "DemandAnalyzer": ["demand_pattern"],
    "PriceAnalyzer": ["price_dispersion"],
    "SlowMoverAnalyzer": ["slow_movers"],
    "ReportGenerator": ["demand_pattern"],
    "HaloAnalyzer": ["halo_effect"],
    "SpecialsAnalyzer": ["specials_uplift"],
    "MarginAnalyzer": ["margin_analysis"],
    "CustomerAnalyzer": ["customer_analysis"],
    "StoreBenchmarkAnalyzer": ["store_benchmark"],
}

# Default store for analyses that need one
DEFAULT_STORE = "28"  # Mosman


def _get_conn():
    conn = sqlite3.connect(config.HUB_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_approved_proposals():
    """Fetch all APPROVED proposals, oldest first."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, agent_name, task_type, description, proposed_changes, "
        "risk_level, estimated_impact "
        "FROM agent_proposals WHERE status = 'APPROVED' "
        "ORDER BY reviewed_at ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def route_proposal(proposal):
    """Determine which analysis function(s) to run for a proposal.

    Returns list of analysis_type strings, or empty list if not routable.
    """
    agent = proposal.get("agent_name", "")
    task_type = proposal.get("task_type", "")
    desc = (proposal.get("description", "") or "").lower()

    # Direct mapping from agent name
    if agent in AGENT_ANALYSIS_MAP:
        return AGENT_ANALYSIS_MAP[agent]

    # Keyword-based fallback from description
    if "margin" in desc or "wastage" in desc or "gp%" in desc or "erosion" in desc or "gross profit" in desc:
        return ["margin_analysis"]
    if "customer" in desc or "segment" in desc or "rfm" in desc or "loyalty" in desc or "retention" in desc:
        return ["customer_analysis"]
    if "benchmark" in desc or "store compar" in desc or "store rank" in desc or "kpi" in desc or "league table" in desc:
        return ["store_benchmark"]
    if "stockout" in desc or "intra-day" in desc or "lost sale" in desc:
        return ["intraday_stockout"]
    if "basket" in desc or "cross-sell" in desc or "cross sell" in desc:
        return ["basket_analysis"]
    if "halo" in desc or "basket grow" in desc or "basket lift" in desc:
        return ["halo_effect"]
    if "special" in desc or "price drop" in desc or "uplift" in desc or "promo" in desc:
        return ["specials_uplift"]
    if "demand" in desc or "peak" in desc or "pattern" in desc:
        return ["demand_pattern"]
    if "price" in desc or "dispersion" in desc:
        return ["price_dispersion"]
    if "slow" in desc or "range review" in desc or "underperform" in desc:
        return ["slow_movers"]

    # IMPROVEMENT / REPORT tasks — run self-improvement status check
    if task_type == "IMPROVEMENT":
        return ["_self_improvement"]
    if task_type == "REPORT":
        return ["demand_pattern"]  # default report is demand summary

    # Unknown — run demand_pattern as safe default
    return ["demand_pattern"]


def execute_analysis(analysis_type, store_id=None, days=14):
    """Run a real data analysis and return the result dict."""
    from data_analysis import (
        run_basket_analysis, run_stockout_detection, run_price_dispersion,
        run_demand_pattern, run_slow_movers, run_intraday_stockout,
        run_halo_effect, run_specials_uplift,
        run_margin_analysis, run_customer_analysis, run_store_benchmark,
    )

    runners = {
        "basket_analysis": run_basket_analysis,
        "stockout_detection": run_stockout_detection,
        "price_dispersion": run_price_dispersion,
        "demand_pattern": run_demand_pattern,
        "slow_movers": run_slow_movers,
        "intraday_stockout": run_intraday_stockout,
        "halo_effect": run_halo_effect,
        "specials_uplift": run_specials_uplift,
        "margin_analysis": run_margin_analysis,
        "customer_analysis": run_customer_analysis,
        "store_benchmark": run_store_benchmark,
    }

    runner = runners.get(analysis_type)
    if not runner:
        return None

    kwargs = {"days": days}
    if analysis_type not in ("price_dispersion", "store_benchmark") and store_id:
        kwargs["store_id"] = store_id

    return runner(**kwargs)


def execute_self_improvement():
    """Run self-improvement status check and return a result dict."""
    from self_improvement import get_improvement_status
    status = get_improvement_status()
    weakest = status.get("weakest", {})
    avgs = status.get("averages", {})
    return {
        "analysis_type": "self_improvement",
        "title": "Self-Improvement Status Report",
        "executive_summary": status.get("recommendation", "No recommendation"),
        "findings": [
            "Overall average: {}/10 from {} tasks".format(
                avgs.get("avg", 0), avgs.get("count", 0)
            ),
            "Weakest criterion: {} ({}) at {}".format(
                weakest.get("label", "N/A"),
                weakest.get("criterion", "N/A"),
                weakest.get("score", "N/A"),
            ),
        ],
        "evidence_tables": [],
        "financial_impact": {},
        "recommendations": [
            {"action": status.get("recommendation", ""), "priority": "HIGH"}
        ],
        "methodology": {"approach": "Audit log score parsing + trend analysis"},
        "confidence_level": 0.9,
        "generated_at": datetime.utcnow().isoformat(),
    }


def score_result(result):
    """Score a result dict with the presentation rubric."""
    try:
        from presentation_rubric import evaluate_report
        return evaluate_report(result)
    except Exception as e:
        logger.warning("Rubric scoring failed: %s", e)
        return {"grade": "Draft", "average": 0, "dimensions": {}}


def store_report(analysis_type, result, rubric, store_id, params):
    """Store result in intelligence_reports table."""
    conn = sqlite3.connect(config.HUB_DB)
    from data_analysis import ANALYSIS_TYPES
    agent_id = ANALYSIS_TYPES.get(analysis_type, {}).get("agent_id", "executor")

    conn.execute(
        "INSERT INTO intelligence_reports "
        "(analysis_type, agent_id, title, status, report_json, "
        "rubric_scores_json, rubric_grade, rubric_average, store_id, "
        "parameters_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            analysis_type, agent_id,
            result.get("title", ""),
            "completed",
            json.dumps(result, default=str),
            json.dumps(rubric, default=str),
            rubric.get("grade", "Draft"),
            rubric.get("average", 0),
            store_id,
            json.dumps(params, default=str),
        ),
    )
    report_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return report_id


def mark_completed(proposal_id, execution_result):
    """Mark proposal as COMPLETED with result summary."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.execute(
        "UPDATE agent_proposals SET status = 'COMPLETED', "
        "execution_result = ? WHERE id = ?",
        (execution_result[:2000] if execution_result else "", proposal_id),
    )
    conn.commit()
    conn.close()


def mark_failed(proposal_id, error_msg):
    """Mark proposal as FAILED with error."""
    conn = sqlite3.connect(config.HUB_DB)
    conn.execute(
        "UPDATE agent_proposals SET status = 'FAILED', "
        "execution_result = ? WHERE id = ?",
        ("ERROR: {}".format(str(error_msg)[:500]), proposal_id),
    )
    conn.commit()
    conn.close()


def log_agent_score(agent_name, metric, score, evidence):
    """Record a performance score for an agent."""
    conn = sqlite3.connect(config.HUB_DB)
    prev = conn.execute(
        "SELECT score FROM agent_scores WHERE agent_name = ? AND metric = ? "
        "ORDER BY timestamp DESC LIMIT 1",
        (agent_name, metric),
    ).fetchone()
    baseline = prev[0] if prev else None

    conn.execute(
        "INSERT INTO agent_scores (agent_name, metric, score, baseline, evidence) "
        "VALUES (?,?,?,?,?)",
        (agent_name, metric, score, baseline, evidence),
    )
    conn.commit()
    conn.close()


def check_improvement_trigger(agent_name):
    """After every 5 completions for an agent, create a self-improvement proposal."""
    conn = _get_conn()
    count = conn.execute(
        "SELECT COUNT(*) FROM agent_proposals "
        "WHERE agent_name = ? AND status = 'COMPLETED'",
        (agent_name,),
    ).fetchone()[0]

    pending = conn.execute(
        "SELECT COUNT(*) FROM agent_proposals "
        "WHERE agent_name = 'SelfImprovementEngine' "
        "AND description LIKE ? AND status IN ('PENDING', 'APPROVED')",
        ("%{}%".format(agent_name),),
    ).fetchone()[0]
    conn.close()

    if count > 0 and count % 5 == 0 and pending == 0:
        conn = sqlite3.connect(config.HUB_DB)
        conn.execute(
            "INSERT INTO agent_proposals (agent_name, task_type, description, "
            "risk_level, estimated_impact) VALUES (?,?,?,?,?)",
            (
                "SelfImprovementEngine", "IMPROVEMENT",
                "Auto-triggered: Review performance of {} after {} completions".format(
                    agent_name, count
                ),
                "MEDIUM", "Score optimisation",
            ),
        )
        conn.commit()
        conn.close()
        logger.info("Self-improvement task created for %s (after %d completions)",
                     agent_name, count)


def execute_proposal(proposal):
    """Execute a single approved proposal end-to-end."""
    pid = proposal["id"]
    agent_name = proposal["agent_name"]
    task_type = proposal["task_type"]
    description = proposal.get("description", "")

    logger.info("EXECUTING proposal #%d: %s [%s] — %s",
                pid, agent_name, task_type, description[:80])

    analysis_types = route_proposal(proposal)
    if not analysis_types:
        mark_failed(pid, "Could not route proposal to any analysis")
        return

    results_summary = []
    store_id = DEFAULT_STORE
    last_rubric = None
    last_result = None

    for atype in analysis_types:
        try:
            if atype == "_self_improvement":
                result = execute_self_improvement()
                rubric = {"grade": "Internal", "average": 9.0, "dimensions": {}}
            else:
                result = execute_analysis(atype, store_id=store_id, days=14)
                if not result:
                    results_summary.append("{}: no data".format(atype))
                    continue
                rubric = score_result(result)

            last_rubric = rubric
            last_result = result

            report_id = store_report(atype, result, rubric, store_id,
                                     {"store_id": store_id, "days": 14})

            grade = rubric.get("grade", "Draft")
            avg = rubric.get("average", 0)
            title = result.get("title", atype)
            summary = result.get("executive_summary", "")[:200]

            results_summary.append(
                "#{} {} — {} ({:.1f}/10): {}".format(
                    report_id, title, grade, avg, summary
                )
            )

            # Log agent performance score
            log_agent_score(
                agent_name, "INSIGHT_QUALITY", avg,
                "Report #{}: {} ({})".format(report_id, title, grade),
            )

            logger.info("  -> Report #%d: %s [%s %.1f/10]",
                         report_id, title, grade, avg)

        except Exception as e:
            logger.error("  -> %s failed: %s", atype, e)
            results_summary.append("{}: ERROR {}".format(atype, str(e)[:100]))

    # Mark proposal completed
    execution_result = "\n".join(results_summary)
    mark_completed(pid, execution_result)
    logger.info("Proposal #%d COMPLETED: %s", pid, execution_result[:120])

    # Award game points (non-critical)
    try:
        from agent_game import (calculate_points, award_game_points,
                                check_game_achievements, update_agent_rubric,
                                update_agent_revenue)
        rubric_grade = last_rubric.get("grade", "Draft") if last_rubric else "Draft"
        rubric_avg = last_rubric.get("average", 0) if last_rubric else 0
        revenue = 0
        if last_result:
            fi = last_result.get("financial_impact", {})
            if fi:
                revenue = fi.get("estimated_annual_value", 0) or 0
        points, breakdown = calculate_points(
            task_type, rubric_grade, rubric_avg, revenue)
        if points > 0:
            award_game_points(config.HUB_DB, agent_name, pid, points, breakdown)
            update_agent_rubric(config.HUB_DB, agent_name, rubric_avg)
            if revenue > 0:
                update_agent_revenue(config.HUB_DB, agent_name, revenue)
            check_game_achievements(config.HUB_DB, agent_name)
    except Exception as e:
        logger.debug("Game points skipped for proposal #%d: %s", pid, e)

    # Check if we should trigger self-improvement
    check_improvement_trigger(agent_name)


def run_once():
    """Single pass: execute all approved proposals."""
    proposals = get_approved_proposals()
    if not proposals:
        logger.info("No approved proposals to execute")
        return 0

    logger.info("Found %d approved proposal(s) to execute", len(proposals))
    for prop in proposals:
        execute_proposal(prop)
        time.sleep(0.5)  # Brief pause between proposals

    return len(proposals)


def run_loop():
    """Continuous polling loop."""
    logger.info("Agent Executor started (poll every %ds)", POLL_INTERVAL)
    while True:
        try:
            count = run_once()
            if count > 0:
                logger.info("Processed %d proposals this cycle", count)
        except KeyboardInterrupt:
            logger.info("Executor stopped by user")
            break
        except Exception as e:
            logger.error("Error in executor loop: %s", e)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        run_loop()
