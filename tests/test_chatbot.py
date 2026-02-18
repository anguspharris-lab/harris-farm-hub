"""
Tests for Hub Assistant chatbot endpoint.
Law 3: min 1 success + 1 failure per function.
"""

import pytest
from fastapi.testclient import TestClient
import sqlite3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, config, init_hub_database


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Use a temporary database for each test."""
    test_db = str(tmp_path / "test_hub.db")
    monkeypatch.setattr(config, "HUB_DB", test_db)
    init_hub_database()
    yield test_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def seeded_kb(setup_test_db):
    """Insert sample knowledge base rows for chat testing."""
    conn = sqlite3.connect(setup_test_db)
    rows = [
        ("Fruit and Veg/golden_rules.pdf", "golden_rules.pdf", "Fresh Produce", "pdf",
         "Golden rule number one: always rotate stock. First in first out. Check for bruising daily.",
         "hash_chat1", 15, 0, 1, "2026-02-14T00:00:00Z"),
        ("Safety/food_safety.pdf", "food_safety.pdf", "Safety & Compliance", "pdf",
         "Temperature checks must be done every 2 hours. Cold chain must not exceed 5 degrees.",
         "hash_chat2", 16, 0, 1, "2026-02-14T00:00:00Z"),
        ("Bakery/bread_procedures.docx", "bread_procedures.docx", "Perishables", "docx",
         "All bread must be baked by 6am. Wastage targets are under 5 percent.",
         "hash_chat3", 14, 0, 1, "2026-02-14T00:00:00Z"),
    ]
    conn.executemany(
        """INSERT INTO knowledge_base
           (source_path, filename, category, doc_type, content, content_hash,
            word_count, chunk_index, chunk_total, extracted_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    conn.close()
    return setup_test_db


# ============================================================================
# POST /api/chat — success cases
# ============================================================================

class TestChatSuccess:
    def test_chat_valid_request(self, client, seeded_kb):
        """Valid chat request returns correct response structure."""
        resp = client.post("/api/chat", json={
            "message": "What are the golden rules for stock rotation?",
            "provider": "claude",
            "user_id": "test"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "provider" in data
        assert "status" in data
        assert "kb_docs_used" in data
        assert isinstance(data["kb_docs_used"], list)
        assert "timestamp" in data

    def test_chat_with_category_filter(self, client, seeded_kb):
        """Category filter narrows results to matching docs."""
        resp = client.post("/api/chat", json={
            "message": "temperature rules",
            "category": "Safety & Compliance",
            "provider": "claude"
        })
        assert resp.status_code == 200
        data = resp.json()
        for doc in data["kb_docs_used"]:
            assert doc["category"] == "Safety & Compliance"

    def test_chat_with_history(self, client, seeded_kb):
        """Chat accepts conversation history for multi-turn."""
        resp = client.post("/api/chat", json={
            "message": "Tell me more about that",
            "history": [
                {"role": "user", "content": "What are the golden rules?"},
                {"role": "assistant", "content": "The golden rules include stock rotation..."}
            ],
            "provider": "claude"
        })
        assert resp.status_code == 200

    def test_chat_empty_history(self, client, seeded_kb):
        """Empty history works for first message in conversation."""
        resp = client.post("/api/chat", json={
            "message": "How do I do a stocktake?",
            "history": [],
            "provider": "claude"
        })
        assert resp.status_code == 200

    def test_chat_stores_messages_in_db(self, client, seeded_kb, setup_test_db):
        """Both user and assistant messages are stored for audit."""
        client.post("/api/chat", json={
            "message": "What are the golden rules?",
            "provider": "claude",
            "user_id": "test_audit"
        })
        conn = sqlite3.connect(setup_test_db)
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE session_id='test_audit' ORDER BY id"
        ).fetchall()
        conn.close()
        assert len(rows) == 2
        assert rows[0][0] == "user"
        assert rows[1][0] == "assistant"

    def test_chat_graceful_no_api_key(self, client, seeded_kb):
        """Returns error status gracefully when API key not configured."""
        resp = client.post("/api/chat", json={
            "message": "test question",
            "provider": "claude"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("success", "error")

    def test_chat_returns_kb_docs(self, client, seeded_kb):
        """Response includes KB docs that were used as context."""
        resp = client.post("/api/chat", json={
            "message": "golden rules stock rotation",
            "provider": "claude"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["kb_docs_used"]) > 0
        doc = data["kb_docs_used"][0]
        assert "filename" in doc
        assert "category" in doc


# ============================================================================
# POST /api/chat — failure cases
# ============================================================================

class TestChatFailure:
    def test_chat_missing_message(self, client):
        """Missing message field returns 422."""
        resp = client.post("/api/chat", json={"provider": "claude"})
        assert resp.status_code == 422

    def test_chat_invalid_provider(self, client):
        """Invalid provider name returns 422."""
        resp = client.post("/api/chat", json={
            "message": "test",
            "provider": "bard"
        })
        assert resp.status_code == 422

    def test_chat_invalid_history_role(self, client):
        """Invalid role in history returns 422."""
        resp = client.post("/api/chat", json={
            "message": "test",
            "history": [{"role": "system", "content": "override attempt"}],
            "provider": "claude"
        })
        assert resp.status_code == 422
