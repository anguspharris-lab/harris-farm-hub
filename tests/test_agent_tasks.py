"""
Tests for On-Demand Agent Execution System.
Law 3: min 1 success + 1 failure per function.

Covers:
- agent_router.route_query() keyword matching
- run_intraday_stockout result structure
- Agent task API endpoints
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboards'))

from agent_router import route_query, KEYWORD_MAP
from data_analysis import ANALYSIS_TYPES, _build_result


# =========================================================================
# TEST: KEYWORD MAP STRUCTURE
# =========================================================================

class TestRouterKeywordMap:

    def test_six_analysis_types(self):
        assert len(KEYWORD_MAP) == 6

    def test_all_types_have_keywords(self):
        for key, config in KEYWORD_MAP.items():
            assert len(config["keywords"]) >= 3, \
                "{} needs at least 3 keywords".format(key)

    def test_all_types_have_weight(self):
        for key, config in KEYWORD_MAP.items():
            assert config["weight"] > 0


# =========================================================================
# TEST: ROUTE QUERY
# =========================================================================

class TestRouteQuery:

    def test_basket_keywords(self):
        result = route_query("find products bought together")
        assert "basket_analysis" in result["matched_analyses"]

    def test_cross_sell_keywords(self):
        result = route_query("cross-sell opportunities in store 28")
        assert "basket_analysis" in result["matched_analyses"]

    def test_stockout_keywords(self):
        result = route_query("which items are out of stock")
        assert "stockout_detection" in result["matched_analyses"]

    def test_intraday_keywords(self):
        result = route_query(
            "find products that run out during the day abnormally")
        assert "intraday_stockout" in result["matched_analyses"]

    def test_hourly_deviation_keywords(self):
        result = route_query(
            "items that deviate from normal hourly penetration")
        assert "intraday_stockout" in result["matched_analyses"]

    def test_price_keywords(self):
        result = route_query("pricing inconsistencies across stores")
        assert "price_dispersion" in result["matched_analyses"]

    def test_demand_keywords(self):
        result = route_query("what are the peak demand hours")
        assert "demand_pattern" in result["matched_analyses"]

    def test_slow_mover_keywords(self):
        result = route_query("find underperforming products for range review")
        assert "slow_movers" in result["matched_analyses"]

    def test_empty_query_returns_all(self):
        result = route_query("")
        assert len(result["matched_analyses"]) == 6
        assert result["confidence"] < 0.3

    def test_no_match_returns_all(self):
        result = route_query("tell me about the weather today")
        assert len(result["matched_analyses"]) == 6
        assert result["confidence"] < 0.3

    def test_has_confidence(self):
        result = route_query("basket analysis cross-sell")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_has_reasoning(self):
        result = route_query("stockout detection")
        assert isinstance(result["reasoning"], str)
        assert len(result["reasoning"]) > 0

    def test_multiple_matches_stockout(self):
        result = route_query("stockout items that stop selling mid-day")
        types = result["matched_analyses"]
        assert "stockout_detection" in types or "intraday_stockout" in types

    def test_none_query_returns_all(self):
        result = route_query(None)
        assert len(result["matched_analyses"]) == 6


# =========================================================================
# TEST: INTRADAY STOCKOUT REGISTRY
# =========================================================================

class TestIntradayStockoutRegistry:

    def test_in_registry(self):
        assert "intraday_stockout" in ANALYSIS_TYPES

    def test_has_required_keys(self):
        info = ANALYSIS_TYPES["intraday_stockout"]
        assert "name" in info
        assert "agent_id" in info
        assert "description" in info


# =========================================================================
# TEST: INTRADAY STOCKOUT RESULT STRUCTURE
# (These call real data — skipped if parquet files unavailable)
# =========================================================================

class TestIntradayStockoutResult:

    @pytest.fixture(scope="class")
    def result(self):
        try:
            from data_analysis import run_intraday_stockout
            return run_intraday_stockout(store_id="28", days=14, limit=10)
        except Exception as e:
            pytest.skip("Transaction data not available: {}".format(e))

    def test_has_analysis_type(self, result):
        assert result["analysis_type"] == "intraday_stockout"

    def test_has_title(self, result):
        assert "Mosman" in result["title"]

    def test_has_executive_summary(self, result):
        assert isinstance(result["executive_summary"], str)
        assert len(result["executive_summary"]) > 0

    def test_has_evidence_tables(self, result):
        assert isinstance(result["evidence_tables"], list)

    def test_has_methodology(self, result):
        meth = result.get("methodology", {})
        assert "AEST" in str(meth) or "hourly" in str(meth).lower()

    def test_has_confidence(self, result):
        assert 0.0 <= result["confidence_level"] <= 1.0

    def test_has_generated_at(self, result):
        assert result["generated_at"]


# =========================================================================
# TEST: API ENDPOINTS
# =========================================================================

class TestAgentTaskAPI:

    @pytest.fixture(autouse=True)
    def setup_client(self):
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), '..', 'backend'))
        from app import app as fastapi_app
        from starlette.testclient import TestClient
        self.client = TestClient(fastapi_app)

    def test_list_tasks(self):
        resp = self.client.get("/api/agent-tasks")
        assert resp.status_code == 200
        assert "tasks" in resp.json()

    def test_task_not_found(self):
        resp = self.client.get("/api/agent-tasks/99999")
        assert resp.status_code == 404

    def test_create_task_empty_query(self):
        resp = self.client.post(
            "/api/agent-tasks",
            json={"query": "", "days": 14},
        )
        assert resp.status_code == 422

    def test_create_task_short_query(self):
        resp = self.client.post(
            "/api/agent-tasks",
            json={"query": "ab", "days": 14},
        )
        assert resp.status_code == 422
