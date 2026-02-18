"""
Tests for Knowledge Base extraction, search, and API endpoints.
Law 3: min 1 success + 1 failure per function.
"""

import pytest
from fastapi.testclient import TestClient
import sqlite3
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

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
    """Insert sample knowledge base rows (triggers auto-populate FTS5)."""
    conn = sqlite3.connect(setup_test_db)
    rows = [
        ("Fruit and Veg/NUTS196.docx", "NUTS196 - Fruit and Veg Golden Rules.docx",
         "Fresh Produce", "docx",
         "Golden rule number one: always rotate stock. First in first out. "
         "Check for bruising daily. Display must be full, fresh, and vibrant by 7:30am.",
         "hash_fv1", 25, 0, 1, "2026-02-14T00:00:00Z"),
        ("Bakery/bread_procedures.docx", "bread_procedures.docx", "Perishables", "docx",
         "All bread must be baked by 6am. Wastage targets are under 5%. "
         "Sourdough requires 24h ferment. Temperature of oven must be checked.",
         "hash_bk1", 22, 0, 1, "2026-02-14T00:00:00Z"),
        ("Safety/food_safety.pdf", "POL033 - Food Safety.pdf", "Safety & Compliance", "pdf",
         "Temperature checks must be done every 2 hours. Cold chain must not exceed 5 degrees. "
         "Hot food must be above 60 degrees Celsius.",
         "hash_sf1", 24, 0, 1, "2026-02-14T00:00:00Z"),
        ("Fruit and Veg/wastage_report.pdf", "wastage_report.pdf", "Fresh Produce", "pdf",
         "Weekly wastage for F&V should be tracked per store. "
         "High wastage items include berries and leafy greens.",
         "hash_fv2", 18, 0, 1, "2026-02-14T00:00:00Z"),
        ("Service/NUTS084.docx", "NUTS084 - FRESH Customer Service Standards.docx",
         "Store Operations", "docx",
         "How to handle customer complaints: Listen, empathize, act. "
         "Follow the FRESH service standards. Escalate to duty manager if unresolved.",
         "hash_svc1", 20, 0, 1, "2026-02-14T00:00:00Z"),
        ("Dayforce/NUTS004.docx", "NUTS004 - Dayforce HCM Applying for Leave.docx",
         "Systems & Technology", "docx",
         "To process a leave request in Dayforce: Open the Dayforce app, "
         "tap Leave, select leave type, enter dates, submit for manager approval.",
         "hash_df1", 22, 0, 1, "2026-02-14T00:00:00Z"),
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
# Chunking logic (unit tests for extract_knowledge.py helpers)
# ============================================================================

class TestChunking:
    def test_short_text_no_chunking(self):
        from extract_knowledge import chunk_text
        text = "This is a short document with only a few words."
        chunks = chunk_text(text, "short.pdf")
        assert len(chunks) == 1
        assert chunks[0]["chunk_index"] == 0
        assert chunks[0]["chunk_total"] == 1

    def test_long_text_chunked(self):
        from extract_knowledge import chunk_text
        text = " ".join(["word"] * 3000)
        chunks = chunk_text(text, "long.pdf")
        assert len(chunks) > 1
        for c in chunks:
            assert c["chunk_total"] == len(chunks)
            assert c["word_count"] > 0

    def test_chunk_overlap(self):
        from extract_knowledge import chunk_text
        text = " ".join([f"w{i}" for i in range(3000)])
        chunks = chunk_text(text, "overlap.pdf")
        first_words = set(chunks[0]["content"].split())
        second_words = set(chunks[1]["content"].split())
        overlap = first_words & second_words
        assert len(overlap) > 0, "Chunks should overlap"


class TestContentHash:
    def test_same_input_same_hash(self):
        from extract_knowledge import content_hash
        assert content_hash("hello") == content_hash("hello")

    def test_different_input_different_hash(self):
        from extract_knowledge import content_hash
        assert content_hash("hello") != content_hash("world")


class TestCleanText:
    def test_removes_control_chars(self):
        from extract_knowledge import clean_text
        result = clean_text("hello\x00world\x01test")
        assert "\x00" not in result
        assert "\x01" not in result

    def test_collapses_newlines(self):
        from extract_knowledge import clean_text
        result = clean_text("a\n\n\n\n\nb")
        assert "\n\n\n" not in result


# ============================================================================
# Skip logic and category mapping (new extraction features)
# ============================================================================

class TestSkipPath:
    def test_skip_archived_folder(self):
        from extract_knowledge import should_skip_path
        base = Path("/data")
        assert should_skip_path(Path("/data/Archived/doc.pdf"), base) is True

    def test_skip_nested_archived(self):
        from extract_knowledge import should_skip_path
        base = Path("/data")
        assert should_skip_path(Path("/data/Dayforce/Archived Policies/old.pdf"), base) is True

    def test_skip_archieved_typo(self):
        from extract_knowledge import should_skip_path
        base = Path("/data")
        assert should_skip_path(Path("/data/Bakery/Archieved Policies/x.pdf"), base) is True

    def test_skip_outdated_folder(self):
        from extract_knowledge import should_skip_path
        base = Path("/data")
        assert should_skip_path(Path("/data/Outdated/doc.pdf"), base) is True

    def test_skip_250516_folder(self):
        from extract_knowledge import should_skip_path
        base = Path("/data")
        assert should_skip_path(Path("/data/250516 - Policies ready for review 2025/doc.pdf"), base) is True

    def test_active_folder_not_skipped(self):
        from extract_knowledge import should_skip_path
        base = Path("/data")
        assert should_skip_path(Path("/data/Safety/doc.pdf"), base) is False
        assert should_skip_path(Path("/data/Bakery/bread.docx"), base) is False

    def test_root_file_not_skipped(self):
        from extract_knowledge import should_skip_path
        base = Path("/data")
        assert should_skip_path(Path("/data/POL003.docx"), base) is False


class TestCategoryMapping:
    def test_fruit_veg_maps_to_fresh_produce(self):
        from extract_knowledge import get_category
        base = Path("/data")
        assert get_category(Path("/data/Fruit and Veg/doc.pdf"), base) == "Fresh Produce"

    def test_flowers_maps_to_fresh_produce(self):
        from extract_knowledge import get_category
        base = Path("/data")
        assert get_category(Path("/data/Flowers/roses.docx"), base) == "Fresh Produce"

    def test_bakery_maps_to_perishables(self):
        from extract_knowledge import get_category
        base = Path("/data")
        assert get_category(Path("/data/Bakery/bread.pdf"), base) == "Perishables"

    def test_dayforce_maps_to_systems(self):
        from extract_knowledge import get_category
        base = Path("/data")
        assert get_category(Path("/data/Dayforce/leave.pdf"), base) == "Systems & Technology"

    def test_safety_maps_to_compliance(self):
        from extract_knowledge import get_category
        base = Path("/data")
        assert get_category(Path("/data/Safety/whs.pdf"), base) == "Safety & Compliance"

    def test_golden_rules_category(self):
        from extract_knowledge import get_category
        base = Path("/data")
        assert get_category(Path("/data/2025 - Golden Rules/nuts.pdf"), base) == "Golden Rules"

    def test_policy_mode(self):
        from extract_knowledge import get_category
        base = Path("/data")
        assert get_category(Path("/data/POL033.docx"), base, category_mode="policy") == "Company Policy"

    def test_unmapped_folder_uses_raw_name(self):
        from extract_knowledge import get_category
        base = Path("/data")
        assert get_category(Path("/data/NewDepartment/doc.pdf"), base) == "NewDepartment"

    def test_root_file_uncategorised(self):
        from extract_knowledge import get_category
        base = Path("/data")
        assert get_category(Path("/data/readme.pdf"), base) == "Uncategorised"


# ============================================================================
# Knowledge Base search API (FTS5-backed)
# ============================================================================

class TestKnowledgeSearchAPI:
    def test_search_returns_results(self, client, seeded_kb):
        resp = client.get("/api/knowledge/search", params={"q": "wastage"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0
        filenames = [d["filename"] for d in data["results"]]
        assert any("wastage" in f.lower() for f in filenames)

    def test_search_empty_query_returns_empty(self, client, seeded_kb):
        resp = client.get("/api/knowledge/search", params={"q": ""})
        assert resp.status_code == 200
        assert resp.json()["results"] == []
        assert resp.json()["count"] == 0

    def test_search_no_match(self, client, seeded_kb):
        resp = client.get("/api/knowledge/search", params={"q": "xyznonexistent123"})
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_search_with_category_filter(self, client, seeded_kb):
        resp = client.get("/api/knowledge/search", params={"q": "golden rules", "category": "Fresh Produce"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0
        for d in data["results"]:
            assert d["category"] == "Fresh Produce"

    def test_search_category_filter_excludes(self, client, seeded_kb):
        resp = client.get("/api/knowledge/search", params={"q": "bread baked", "category": "Safety & Compliance"})
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_stop_words_do_not_pollute_results(self, client, seeded_kb):
        """Queries like 'What are the golden rules?' should strip stop words."""
        resp = client.get("/api/knowledge/search", params={"q": "What are the golden rules?"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0
        # Should NOT return all 6 docs — stop words like 'what', 'are', 'the' are stripped
        assert data["count"] <= 4

    def test_stemming_matches_variants(self, client, seeded_kb):
        """Porter stemming: 'baking' should match 'baked'."""
        resp = client.get("/api/knowledge/search", params={"q": "baking sourdough"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0


# ============================================================================
# Target query validation — the 5 required queries
# ============================================================================

class TestTargetQueries:
    def test_golden_rules_fruit_veg(self, client, seeded_kb):
        resp = client.get("/api/knowledge/search", params={"q": "golden rules Fruit & Veg"})
        data = resp.json()
        assert data["count"] > 0
        assert "Golden Rules" in data["results"][0]["filename"]

    def test_dayforce_leave_request(self, client, seeded_kb):
        resp = client.get("/api/knowledge/search", params={"q": "Dayforce leave request"})
        data = resp.json()
        assert data["count"] > 0
        assert "Dayforce" in data["results"][0]["filename"]

    def test_food_safety_temperature(self, client, seeded_kb):
        resp = client.get("/api/knowledge/search", params={"q": "food safety temperature rules"})
        data = resp.json()
        assert data["count"] > 0
        first = data["results"][0]
        assert "safety" in first["filename"].lower() or "temperature" in first.get("snippet", "").lower()

    def test_customer_complaints(self, client, seeded_kb):
        resp = client.get("/api/knowledge/search", params={"q": "handle customer complaints"})
        data = resp.json()
        assert data["count"] > 0
        assert "customer" in data["results"][0]["snippet"].lower()

    def test_new_store_opening_graceful(self, client, seeded_kb):
        """No docs about store opening -> may return empty or tangential, no error."""
        resp = client.get("/api/knowledge/search", params={"q": "procedure opening new store"})
        assert resp.status_code == 200


# ============================================================================
# Knowledge Base stats API
# ============================================================================

class TestKnowledgeStatsAPI:
    def test_stats_with_data(self, client, seeded_kb):
        resp = client.get("/api/knowledge/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_documents"] == 6
        assert data["total_words"] > 0
        assert len(data["categories"]) > 0

    def test_stats_empty_kb(self, client):
        resp = client.get("/api/knowledge/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_documents"] == 0
        assert data["total_words"] == 0


# ============================================================================
# Rubric with knowledge base flag
# ============================================================================

class TestRubricKBFlag:
    def test_rubric_request_accepts_kb_flag(self, client, seeded_kb):
        resp = client.post("/api/rubric", json={
            "prompt": "How should we handle wastage?",
            "providers": ["claude"],
            "use_knowledge_base": True,
            "user_id": "test"
        })
        assert resp.status_code != 422

    def test_rubric_request_kb_false(self, client, seeded_kb):
        resp = client.post("/api/rubric", json={
            "prompt": "Test question",
            "providers": ["claude"],
            "use_knowledge_base": False,
            "user_id": "test"
        })
        assert resp.status_code != 422
