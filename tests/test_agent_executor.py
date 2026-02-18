"""Tests for the Agent Executor: routing, scoring, API endpoints."""

import os
import sys
import sqlite3
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


# ---------------------------------------------------------------------------
# Constants & Routing Tests
# ---------------------------------------------------------------------------

class TestExecutorConstants:
    """Verify executor constants and mapping."""

    def test_agent_analysis_map_has_entries(self):
        from agent_executor import AGENT_ANALYSIS_MAP
        assert len(AGENT_ANALYSIS_MAP) >= 6

    def test_all_map_values_are_lists(self):
        from agent_executor import AGENT_ANALYSIS_MAP
        for agent, types in AGENT_ANALYSIS_MAP.items():
            assert isinstance(types, list), "{} should map to list".format(agent)
            assert len(types) >= 1

    def test_default_store_is_string(self):
        from agent_executor import DEFAULT_STORE
        assert isinstance(DEFAULT_STORE, str)
        assert len(DEFAULT_STORE) > 0

    def test_poll_interval_is_positive(self):
        from agent_executor import POLL_INTERVAL
        assert isinstance(POLL_INTERVAL, int)
        assert POLL_INTERVAL > 0


class TestRouteProposal:
    """Test the route_proposal() function."""

    def test_route_stockout_analyzer(self):
        from agent_executor import route_proposal
        result = route_proposal({"agent_name": "StockoutAnalyzer"})
        assert "intraday_stockout" in result
        assert "stockout_detection" in result

    def test_route_basket_analyzer(self):
        from agent_executor import route_proposal
        result = route_proposal({"agent_name": "BasketAnalyzer"})
        assert result == ["basket_analysis"]

    def test_route_demand_analyzer(self):
        from agent_executor import route_proposal
        result = route_proposal({"agent_name": "DemandAnalyzer"})
        assert result == ["demand_pattern"]

    def test_route_price_analyzer(self):
        from agent_executor import route_proposal
        result = route_proposal({"agent_name": "PriceAnalyzer"})
        assert result == ["price_dispersion"]

    def test_route_slow_mover_analyzer(self):
        from agent_executor import route_proposal
        result = route_proposal({"agent_name": "SlowMoverAnalyzer"})
        assert result == ["slow_movers"]

    def test_route_report_generator(self):
        from agent_executor import route_proposal
        result = route_proposal({"agent_name": "ReportGenerator"})
        assert result == ["demand_pattern"]

    def test_route_by_description_stockout(self):
        from agent_executor import route_proposal
        result = route_proposal({
            "agent_name": "UnknownAgent",
            "description": "Detect intra-day stockouts at Mosman",
        })
        assert result == ["intraday_stockout"]

    def test_route_by_description_basket(self):
        from agent_executor import route_proposal
        result = route_proposal({
            "agent_name": "UnknownAgent",
            "description": "Cross-sell analysis for dairy products",
        })
        assert result == ["basket_analysis"]

    def test_route_by_description_demand(self):
        from agent_executor import route_proposal
        result = route_proposal({
            "agent_name": "UnknownAgent",
            "description": "Analyse demand patterns at peak hours",
        })
        assert result == ["demand_pattern"]

    def test_route_by_description_price(self):
        from agent_executor import route_proposal
        result = route_proposal({
            "agent_name": "UnknownAgent",
            "description": "Review price dispersion across stores",
        })
        assert result == ["price_dispersion"]

    def test_route_by_description_slow(self):
        from agent_executor import route_proposal
        result = route_proposal({
            "agent_name": "UnknownAgent",
            "description": "Find slow-moving lines for range review",
        })
        assert result == ["slow_movers"]

    def test_route_improvement_task(self):
        from agent_executor import route_proposal
        result = route_proposal({
            "agent_name": "UnknownAgent",
            "task_type": "IMPROVEMENT",
            "description": "Self-improvement cycle",
        })
        assert result == ["_self_improvement"]

    def test_route_report_task(self):
        from agent_executor import route_proposal
        result = route_proposal({
            "agent_name": "UnknownAgent",
            "task_type": "REPORT",
            "description": "Weekly summary",
        })
        assert result == ["demand_pattern"]

    def test_route_unknown_defaults(self):
        from agent_executor import route_proposal
        result = route_proposal({
            "agent_name": "CompletelyUnknown",
            "task_type": "CUSTOM",
            "description": "Something vague",
        })
        assert result == ["demand_pattern"]

    def test_route_empty_proposal(self):
        from agent_executor import route_proposal
        result = route_proposal({})
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_route_lost_sale_keyword(self):
        from agent_executor import route_proposal
        result = route_proposal({
            "agent_name": "X",
            "description": "Lost sale detection in produce",
        })
        assert result == ["intraday_stockout"]

    def test_route_description_none(self):
        from agent_executor import route_proposal
        result = route_proposal({
            "agent_name": "X",
            "description": None,
        })
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Database Helper Tests
# ---------------------------------------------------------------------------

class TestMarkCompleted:
    """Test mark_completed and mark_failed helpers."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB

    def test_mark_completed(self):
        from agent_executor import mark_completed
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO agent_proposals (agent_name, task_type, description, "
            "status) VALUES (?, ?, ?, ?)",
            ("TestMarkAgent", "ANALYSIS", "For mark_completed test", "APPROVED"),
        )
        conn.commit()
        pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        mark_completed(pid, "Test result summary")

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT status, execution_result FROM agent_proposals WHERE id = ?",
            (pid,),
        ).fetchone()
        conn.close()
        assert row[0] == "COMPLETED"
        assert row[1] == "Test result summary"

    def test_mark_failed(self):
        from agent_executor import mark_failed
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO agent_proposals (agent_name, task_type, description, "
            "status) VALUES (?, ?, ?, ?)",
            ("TestFailAgent", "ANALYSIS", "For mark_failed test", "APPROVED"),
        )
        conn.commit()
        pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        mark_failed(pid, "Something went wrong")

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT status, execution_result FROM agent_proposals WHERE id = ?",
            (pid,),
        ).fetchone()
        conn.close()
        assert row[0] == "FAILED"
        assert "ERROR" in row[1]

    def test_mark_completed_truncates_long_result(self):
        from agent_executor import mark_completed
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO agent_proposals (agent_name, task_type, description, "
            "status) VALUES (?, ?, ?, ?)",
            ("TestTruncAgent", "ANALYSIS", "Truncation test", "APPROVED"),
        )
        conn.commit()
        pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        long_result = "x" * 5000
        mark_completed(pid, long_result)

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT execution_result FROM agent_proposals WHERE id = ?",
            (pid,),
        ).fetchone()
        conn.close()
        assert len(row[0]) <= 2000


class TestLogAgentScore:
    """Test log_agent_score helper."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB

    def test_log_new_score(self):
        from agent_executor import log_agent_score
        log_agent_score("TestScoreAgent", "INSIGHT_QUALITY", 8.5, "Test evidence")

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT score, evidence FROM agent_scores "
            "WHERE agent_name = 'TestScoreAgent' ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        conn.close()
        assert row[0] == 8.5
        assert row[1] == "Test evidence"

    def test_log_score_with_baseline(self):
        from agent_executor import log_agent_score
        # First score has no baseline
        log_agent_score("TestBaselineAgent", "ACCURACY", 7.0, "First")
        # Second score should have baseline = 7.0
        log_agent_score("TestBaselineAgent", "ACCURACY", 8.0, "Second")

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT score, baseline FROM agent_scores "
            "WHERE agent_name = 'TestBaselineAgent' AND evidence = 'Second'"
        ).fetchone()
        conn.close()
        assert row[0] == 8.0
        assert row[1] == 7.0


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------

class TestExecutorAPI:
    """Test executor API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        try:
            from app import app as fastapi_app
            from fastapi.testclient import TestClient
            self.client = TestClient(fastapi_app)
        except Exception:
            pytest.skip("FastAPI app not importable")

    def test_executor_status(self):
        resp = self.client.get("/api/admin/executor/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "queue" in data
        assert "approved_waiting" in data
        assert "completed_total" in data
        assert "pending_total" in data

    def test_executor_status_has_recent(self):
        resp = self.client.get("/api/admin/executor/status")
        data = resp.json()
        assert "recent_completions" in data
        assert isinstance(data["recent_completions"], list)

    def test_executor_run_endpoint(self):
        """POST /api/admin/executor/run returns success."""
        resp = self.client.post("/api/admin/executor/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "executed" in data

    def test_executor_run_returns_count(self):
        resp = self.client.post("/api/admin/executor/run")
        data = resp.json()
        assert isinstance(data["executed"], int)
        assert data["executed"] >= 0


# ---------------------------------------------------------------------------
# Self-Improvement Trigger Tests
# ---------------------------------------------------------------------------

class TestImprovementTrigger:
    """Test the check_improvement_trigger logic."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB

    def test_no_trigger_below_threshold(self):
        """Should not create improvement task for non-multiple-of-5 completions."""
        import time
        from agent_executor import check_improvement_trigger
        # Use unique agent name to avoid cross-run pollution
        agent = "TriggerNo_{}".format(int(time.time() * 1000) % 1000000)
        conn = sqlite3.connect(self.db_path)
        for i in range(3):
            conn.execute(
                "INSERT INTO agent_proposals (agent_name, task_type, description, "
                "status) VALUES (?, ?, ?, ?)",
                (agent, "ANALYSIS",
                 "Test {}".format(i), "COMPLETED"),
            )
        conn.commit()
        before = conn.execute(
            "SELECT COUNT(*) FROM agent_proposals "
            "WHERE agent_name = 'SelfImprovementEngine' "
            "AND description LIKE ?",
            ("%{}%".format(agent),),
        ).fetchone()[0]
        conn.close()

        check_improvement_trigger(agent)

        conn = sqlite3.connect(self.db_path)
        after = conn.execute(
            "SELECT COUNT(*) FROM agent_proposals "
            "WHERE agent_name = 'SelfImprovementEngine' "
            "AND description LIKE ?",
            ("%{}%".format(agent),),
        ).fetchone()[0]
        conn.close()
        assert after == before  # No new task created

    def test_trigger_at_five(self):
        """Should create improvement task at exactly 5 completions."""
        import time
        from agent_executor import check_improvement_trigger
        agent = "TriggerYes_{}".format(int(time.time() * 1000) % 1000000)
        conn = sqlite3.connect(self.db_path)
        for i in range(5):
            conn.execute(
                "INSERT INTO agent_proposals (agent_name, task_type, description, "
                "status) VALUES (?, ?, ?, ?)",
                (agent, "ANALYSIS",
                 "Test {}".format(i), "COMPLETED"),
            )
        conn.commit()
        conn.close()

        check_improvement_trigger(agent)

        conn = sqlite3.connect(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM agent_proposals "
            "WHERE agent_name = 'SelfImprovementEngine' "
            "AND description LIKE ?",
            ("%{}%".format(agent),),
        ).fetchone()[0]
        conn.close()
        assert count >= 1
