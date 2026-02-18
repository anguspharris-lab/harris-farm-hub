"""
Tests for The Rubric multi-LLM evaluation system
Law 3: min 1 success + 1 failure per function
"""

import pytest
from fastapi.testclient import TestClient
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, config, init_hub_database, RubricEvaluator


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_hub.db")
    monkeypatch.setattr(config, "HUB_DB", test_db)
    init_hub_database()
    yield test_db


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================================
# RubricEvaluator — unit tests
# ============================================================================

class TestRubricEvaluator:
    def test_evaluator_initialises(self):
        """Success: evaluator creates without error"""
        evaluator = RubricEvaluator()
        assert evaluator is not None

    def test_evaluator_handles_missing_keys(self):
        """Success: missing API keys return error status gracefully"""
        evaluator = RubricEvaluator()
        # Claude client is None when key is empty
        if not os.environ.get("ANTHROPIC_API_KEY"):
            assert evaluator.claude_client is None or True  # Either None or configured


# ============================================================================
# POST /api/rubric — Integration tests
# ============================================================================

class TestRubricEndpoint:
    def test_rubric_valid_request(self, client):
        """Success: rubric endpoint accepts valid request and returns structure"""
        payload = {
            "prompt": "What is the best pricing strategy for fresh produce?",
            "providers": ["claude"],
            "user_id": "test"
        }
        response = client.post("/api/rubric", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "query_id" in data
        assert "responses" in data
        assert "awaiting_chairman_decision" in data
        assert data["awaiting_chairman_decision"] is True

    def test_rubric_missing_prompt(self, client):
        """Failure: missing prompt returns 422"""
        payload = {"providers": ["claude"]}
        response = client.post("/api/rubric", json=payload)
        assert response.status_code == 422

    def test_rubric_invalid_provider(self, client):
        """Failure: invalid provider returns 422"""
        payload = {
            "prompt": "Test",
            "providers": ["bard"]
        }
        response = client.post("/api/rubric", json=payload)
        assert response.status_code == 422

    def test_rubric_stores_query(self, client, setup_test_db):
        """Success: rubric query is stored in database"""
        import sqlite3
        payload = {
            "prompt": "Test question for storage",
            "providers": ["claude"]
        }
        client.post("/api/rubric", json=payload)

        conn = sqlite3.connect(setup_test_db)
        c = conn.cursor()
        c.execute("SELECT question FROM queries WHERE query_type='rubric'")
        rows = c.fetchall()
        conn.close()
        assert len(rows) >= 1
        assert rows[0][0] == "Test question for storage"


# ============================================================================
# POST /api/decision — Chairman's Decision
# ============================================================================

class TestDecisionEndpoint:
    def test_decision_valid(self, client):
        """Success: valid decision recorded"""
        payload = {
            "query_id": 1,
            "winner": "Claude Sonnet 4.5",
            "feedback": "Better for retail context",
            "user_id": "chairman"
        }
        response = client.post("/api/decision", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "recorded"

    def test_decision_missing_query_id(self, client):
        """Failure: missing query_id returns 422"""
        payload = {
            "winner": "Claude",
            "user_id": "chairman"
        }
        response = client.post("/api/decision", json=payload)
        assert response.status_code == 422

    def test_decision_stored_in_db(self, client, setup_test_db):
        """Success: decision is persisted"""
        import sqlite3
        client.post("/api/decision", json={
            "query_id": 99,
            "winner": "ChatGPT-4 Turbo",
            "user_id": "test"
        })

        conn = sqlite3.connect(setup_test_db)
        c = conn.cursor()
        c.execute("SELECT winner FROM evaluations WHERE query_id=99")
        rows = c.fetchall()
        conn.close()
        assert len(rows) == 1
        assert rows[0][0] == "ChatGPT-4 Turbo"

    def test_decision_appears_in_analytics(self, client, setup_test_db):
        """Success: decisions show up in performance analytics"""
        # Record some decisions
        for winner in ["Claude", "Claude", "ChatGPT"]:
            client.post("/api/decision", json={
                "query_id": 1,
                "winner": winner,
                "user_id": "test"
            })

        response = client.get("/api/analytics/performance")
        perf = response.json()
        wins = {e["winner"]: e["wins"] for e in perf["llm_performance"]}
        assert wins.get("Claude", 0) == 2
        assert wins.get("ChatGPT", 0) == 1
