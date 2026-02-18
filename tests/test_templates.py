"""
Tests for Prompt Academy template system
Law 3: min 1 success + 1 failure per function
"""

import pytest
from fastapi.testclient import TestClient
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, config, init_hub_database


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_hub.db")
    monkeypatch.setattr(config, "HUB_DB", test_db)
    init_hub_database()
    yield test_db


@pytest.fixture
def client():
    return TestClient(app)


def seed_templates(client):
    """Seed a set of templates for testing"""
    templates = [
        {"title": "Beginner Finance", "description": "d", "template": "t",
         "category": "finance", "difficulty": "beginner"},
        {"title": "Intermediate Buying", "description": "d", "template": "t",
         "category": "buying", "difficulty": "intermediate"},
        {"title": "Advanced Retail", "description": "d", "template": "t",
         "category": "retail_ops", "difficulty": "advanced"},
        {"title": "Beginner General", "description": "d", "template": "t",
         "category": "general", "difficulty": "beginner"},
    ]
    for t in templates:
        client.post("/api/templates", json=t)


class TestTemplateFiltering:
    def test_filter_by_category(self, client):
        """Success: category filter returns only matching templates"""
        seed_templates(client)
        resp = client.get("/api/templates?category=finance")
        assert resp.status_code == 200
        templates = resp.json()["templates"]
        assert len(templates) == 1
        assert templates[0]["title"] == "Beginner Finance"

    def test_filter_by_difficulty(self, client):
        """Success: difficulty filter returns only matching"""
        seed_templates(client)
        resp = client.get("/api/templates?difficulty=beginner")
        templates = resp.json()["templates"]
        assert len(templates) == 2

    def test_filter_combined(self, client):
        """Success: combined category + difficulty filter"""
        seed_templates(client)
        resp = client.get("/api/templates?category=general&difficulty=beginner")
        templates = resp.json()["templates"]
        assert len(templates) == 1
        assert templates[0]["title"] == "Beginner General"

    def test_filter_no_results(self, client):
        """Success: filter with no matches returns empty"""
        seed_templates(client)
        resp = client.get("/api/templates?category=merchandising")
        assert resp.json()["count"] == 0


class TestTemplateCategories:
    def test_all_valid_categories(self, client):
        """Success: all 5 valid categories accepted"""
        for cat in ["retail_ops", "buying", "merchandising", "finance", "general"]:
            resp = client.post("/api/templates", json={
                "title": f"Test {cat}", "description": "d",
                "template": "t", "category": cat, "difficulty": "beginner"
            })
            assert resp.status_code == 200

    def test_invalid_category_rejected(self, client):
        """Failure: invalid category returns 422"""
        resp = client.post("/api/templates", json={
            "title": "Bad", "description": "d",
            "template": "t", "category": "invalid", "difficulty": "beginner"
        })
        assert resp.status_code == 422


class TestTemplateDifficulty:
    def test_all_valid_difficulties(self, client):
        """Success: all 3 difficulties accepted"""
        for diff in ["beginner", "intermediate", "advanced"]:
            resp = client.post("/api/templates", json={
                "title": f"Test {diff}", "description": "d",
                "template": "t", "category": "general", "difficulty": diff
            })
            assert resp.status_code == 200

    def test_invalid_difficulty_rejected(self, client):
        """Failure: invalid difficulty returns 422"""
        resp = client.post("/api/templates", json={
            "title": "Bad", "description": "d",
            "template": "t", "category": "general", "difficulty": "expert"
        })
        assert resp.status_code == 422
