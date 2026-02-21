"""
Tests for Harris Farm Hub Backend API
Law 3: min 1 success + 1 failure per function
"""

import pytest
from fastapi.testclient import TestClient
import sqlite3
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, config, init_hub_database

# Use a separate test database
TEST_DB = "test_hub_data.db"


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Use a temporary database for each test"""
    test_db = str(tmp_path / "test_hub.db")
    monkeypatch.setattr(config, "HUB_DB", test_db)
    init_hub_database()
    yield test_db


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================================
# GET / — Health Check
# ============================================================================

class TestHealthCheck:
    def test_root_returns_200(self, client):
        """Success: root endpoint returns service info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Harris Farm Hub API"
        assert data["status"] == "operational"
        assert "endpoints" in data

    def test_root_lists_all_endpoints(self, client):
        """Success: all expected endpoints are listed"""
        response = client.get("/")
        endpoints = response.json()["endpoints"]
        expected = ["natural_language_query", "rubric_evaluation",
                    "chairman_decision", "user_feedback",
                    "prompt_templates", "analytics"]
        for ep in expected:
            assert ep in endpoints


# ============================================================================
# POST /api/templates — Create Template
# ============================================================================

class TestCreateTemplate:
    def test_create_template_success(self, client):
        """Success: valid template is created"""
        payload = {
            "title": "Weekly Wastage Report",
            "description": "Shows wastage by category",
            "template": "Show all products with wastage above {{threshold}}%",
            "category": "retail_ops",
            "difficulty": "beginner"
        }
        response = client.post("/api/templates", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert "template_id" in data

    def test_create_template_missing_title(self, client):
        """Failure: missing required field returns 422"""
        payload = {
            "description": "test",
            "template": "test",
            "category": "finance",
            "difficulty": "beginner"
        }
        response = client.post("/api/templates", json=payload)
        assert response.status_code == 422

    def test_create_template_invalid_category(self, client):
        """Failure: invalid category enum returns 422"""
        payload = {
            "title": "Test",
            "description": "test",
            "template": "test",
            "category": "invalid_category",
            "difficulty": "beginner"
        }
        response = client.post("/api/templates", json=payload)
        assert response.status_code == 422

    def test_create_template_invalid_difficulty(self, client):
        """Failure: invalid difficulty enum returns 422"""
        payload = {
            "title": "Test",
            "description": "test",
            "template": "test",
            "category": "finance",
            "difficulty": "expert"
        }
        response = client.post("/api/templates", json=payload)
        assert response.status_code == 422


# ============================================================================
# GET /api/templates — List Templates
# ============================================================================

class TestListTemplates:
    def test_list_templates_empty(self, client):
        """Success: returns empty list when no templates"""
        response = client.get("/api/templates")
        assert response.status_code == 200
        data = response.json()
        assert data["templates"] == []
        assert data["count"] == 0

    def test_list_templates_with_data(self, client):
        """Success: returns templates after creation"""
        client.post("/api/templates", json={
            "title": "Test", "description": "d",
            "template": "t", "category": "finance",
            "difficulty": "beginner"
        })
        response = client.get("/api/templates")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_list_templates_filter_category(self, client):
        """Success: category filter works"""
        client.post("/api/templates", json={
            "title": "Finance", "description": "d",
            "template": "t", "category": "finance",
            "difficulty": "beginner"
        })
        client.post("/api/templates", json={
            "title": "Buying", "description": "d",
            "template": "t", "category": "buying",
            "difficulty": "beginner"
        })
        response = client.get("/api/templates?category=finance")
        assert response.json()["count"] == 1
        assert response.json()["templates"][0]["title"] == "Finance"

    def test_list_templates_filter_nonexistent(self, client):
        """Success: non-matching filter returns empty"""
        response = client.get("/api/templates?category=nonexistent")
        # Returns 200 with empty list (not 404)
        assert response.status_code == 200
        assert response.json()["count"] == 0


# ============================================================================
# POST /api/feedback — Submit Feedback
# ============================================================================

class TestFeedback:
    def test_submit_feedback_success(self, client):
        """Success: valid feedback is recorded"""
        payload = {
            "query_id": 1,
            "rating": 4,
            "comment": "Good answer",
            "user_id": "finance_team"
        }
        response = client.post("/api/feedback", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recorded"
        assert data["rating"] == 4

    def test_submit_feedback_rating_too_high(self, client):
        """Failure: rating above 5 returns 422"""
        payload = {
            "query_id": 1,
            "rating": 6,
            "user_id": "test"
        }
        response = client.post("/api/feedback", json=payload)
        assert response.status_code == 422

    def test_submit_feedback_rating_too_low(self, client):
        """Failure: rating below 1 returns 422"""
        payload = {
            "query_id": 1,
            "rating": 0,
            "user_id": "test"
        }
        response = client.post("/api/feedback", json=payload)
        assert response.status_code == 422

    def test_submit_feedback_missing_user_id(self, client):
        """Failure: missing user_id returns 422"""
        payload = {
            "query_id": 1,
            "rating": 3
        }
        response = client.post("/api/feedback", json=payload)
        assert response.status_code == 422


# ============================================================================
# POST /api/decision — Chairman's Decision
# ============================================================================

class TestChairmanDecision:
    def test_record_decision_success(self, client):
        """Success: valid decision is recorded"""
        payload = {
            "query_id": 1,
            "winner": "Claude Sonnet 4.5",
            "feedback": "More specific to Harris Farm",
            "user_id": "chairman"
        }
        response = client.post("/api/decision", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recorded"
        assert data["winner"] == "Claude Sonnet 4.5"

    def test_record_decision_missing_winner(self, client):
        """Failure: missing winner returns 422"""
        payload = {
            "query_id": 1,
            "user_id": "chairman"
        }
        response = client.post("/api/decision", json=payload)
        assert response.status_code == 422


# ============================================================================
# GET /api/analytics — Analytics Endpoints
# ============================================================================

class TestAnalytics:
    def test_performance_analytics_empty(self, client):
        """Success: performance analytics returns structure when empty"""
        response = client.get("/api/analytics/performance")
        assert response.status_code == 200
        data = response.json()
        assert "top_queries" in data
        assert "llm_performance" in data
        assert "popular_templates" in data

    def test_weekly_report_empty(self, client):
        """Success: weekly report returns zeros when no data"""
        response = client.get("/api/analytics/weekly-report")
        assert response.status_code == 200
        data = response.json()
        assert data["total_queries"] == 0
        assert data["average_rating"] == 0
        assert data["sql_success_rate"] == 0

    def test_weekly_report_has_insights(self, client):
        """Success: weekly report includes insights array"""
        response = client.get("/api/analytics/weekly-report")
        data = response.json()
        assert "insights" in data
        assert len(data["insights"]) == 3


# ============================================================================
# POST /api/query — Natural Language Query
# ============================================================================

class TestNaturalLanguageQuery:
    def test_query_missing_question(self, client):
        """Failure: missing question field returns 422"""
        payload = {"dataset": "sales"}
        response = client.post("/api/query", json=payload)
        assert response.status_code == 422

    def test_query_invalid_dataset(self, client):
        """Invalid dataset falls back to default — still returns 200."""
        payload = {
            "question": "What is total revenue?",
            "dataset": "invalid_dataset"
        }
        response = client.post("/api/query", json=payload)
        # dataset is a free-form str hint; unrecognised values fall
        # through to the default query generator, which succeeds.
        assert response.status_code == 200


# ============================================================================
# POST /api/rubric — Rubric Evaluation
# ============================================================================

class TestRubricEvaluation:
    def test_rubric_missing_prompt(self, client):
        """Failure: missing prompt returns 422"""
        payload = {"providers": ["claude"]}
        response = client.post("/api/rubric", json=payload)
        assert response.status_code == 422

    def test_rubric_invalid_provider(self, client):
        """Failure: invalid provider returns 422"""
        payload = {
            "prompt": "Test question",
            "providers": ["invalid_llm"]
        }
        response = client.post("/api/rubric", json=payload)
        assert response.status_code == 422


# ============================================================================
# Database Initialization
# ============================================================================

class TestDatabase:
    def test_init_creates_all_tables(self, setup_test_db):
        """Success: all required tables are created"""
        conn = sqlite3.connect(setup_test_db)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in c.fetchall()}
        conn.close()

        expected_tables = {
            "queries", "llm_responses", "evaluations",
            "feedback", "prompt_templates", "generated_queries"
        }
        for table in expected_tables:
            assert table in tables, f"Missing table: {table}"

    def test_init_idempotent(self, setup_test_db):
        """Success: calling init twice doesn't error"""
        # init already called once in fixture; call again
        init_hub_database()
        conn = sqlite3.connect(setup_test_db)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in c.fetchall()}
        conn.close()
        assert len(tables) >= 6
