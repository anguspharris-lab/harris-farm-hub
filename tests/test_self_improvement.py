"""Tests for the self-improvement engine."""

import os
import sys
import sqlite3
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from self_improvement import (
    CRITERIA, CRITERIA_LABELS, MAX_ATTEMPTS, MIN_ACCEPTABLE,
    parse_audit_scores, calculate_averages, identify_weakest,
    get_attempt_count, get_improvement_status,
    store_task_scores, record_improvement_cycle,
    get_improvement_history, get_score_trends,
    backfill_scores_from_audit,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_audit_log(tmp_path, monkeypatch):
    """Create a temporary audit.log with score entries."""
    log = tmp_path / "audit.log"
    log.write_text(
        "[2026-02-16T10:00:00Z] TASK: Dashboard Fix | SCORES: H=9 R=8 S=9 C=7 D=9 U=8 X=8 avg=8.3\n"
        "[2026-02-16T11:00:00Z] TASK: API Build | SCORES: H=8 R=9 S=9 C=8 D=8 U=9 X=9 avg=8.6\n"
        "[2026-02-16T12:00:00Z] TASK: Data Pipeline | SCORES: H=9 R=9 S=9 C=9 D=6 U=9 X=9 avg=8.6\n"
    )
    monkeypatch.setattr("self_improvement.AUDIT_LOG", str(log))
    return log


@pytest.fixture
def tmp_improvement_log(tmp_path, monkeypatch):
    """Create a temporary improvement_attempts.log."""
    log = tmp_path / "improvement_attempts.log"
    log.write_text(
        "# Improvement attempts log\n"
        "\n"
        "[IMPROVE] 2026-02-16 10:00 | D | attempt 1/3 | 6->7 | FAILED | Added validation\n"
        "[IMPROVE] 2026-02-16 11:00 | D | attempt 2/3 | 6->6.5 | FAILED | Extra checks\n"
    )
    monkeypatch.setattr("self_improvement.IMPROVEMENT_LOG", str(log))
    return log


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Create a temporary hub_data.db with required tables."""
    db_path = str(tmp_path / "hub_data.db")
    monkeypatch.setattr("self_improvement.HUB_DB", db_path)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""CREATE TABLE task_scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  task_name TEXT NOT NULL,
                  h INTEGER NOT NULL DEFAULT 0,
                  r INTEGER NOT NULL DEFAULT 0,
                  s INTEGER NOT NULL DEFAULT 0,
                  c INTEGER NOT NULL DEFAULT 0,
                  d INTEGER NOT NULL DEFAULT 0,
                  u INTEGER NOT NULL DEFAULT 0,
                  x INTEGER NOT NULL DEFAULT 0,
                  avg_score REAL NOT NULL DEFAULT 0,
                  recorded_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE improvement_cycles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  criterion TEXT NOT NULL,
                  criterion_label TEXT,
                  before_score REAL NOT NULL,
                  after_score REAL,
                  action_taken TEXT NOT NULL,
                  attempt_number INTEGER NOT NULL DEFAULT 1,
                  status TEXT NOT NULL DEFAULT 'pending',
                  recorded_at TEXT DEFAULT (datetime('now')))""")
    conn.commit()
    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# Tests: Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_criteria_count(self):
        assert len(CRITERIA) == 7

    def test_criteria_labels_match(self):
        for c in CRITERIA:
            assert c in CRITERIA_LABELS

    def test_max_attempts(self):
        assert MAX_ATTEMPTS == 3

    def test_min_acceptable(self):
        assert MIN_ACCEPTABLE == 7


# ---------------------------------------------------------------------------
# Tests: parse_audit_scores
# ---------------------------------------------------------------------------

class TestParseAuditScores:
    def test_parses_entries(self, tmp_audit_log):
        entries = parse_audit_scores()
        assert len(entries) == 3

    def test_most_recent_first(self, tmp_audit_log):
        entries = parse_audit_scores()
        assert entries[0]["task"] == "Data Pipeline"
        assert entries[2]["task"] == "Dashboard Fix"

    def test_score_values(self, tmp_audit_log):
        entries = parse_audit_scores()
        # Data Pipeline entry
        e = entries[0]
        assert e["H"] == 9
        assert e["D"] == 6
        assert e["avg"] == 8.6

    def test_limit(self, tmp_audit_log):
        entries = parse_audit_scores(limit=2)
        assert len(entries) == 2

    def test_empty_log(self, tmp_path, monkeypatch):
        log = tmp_path / "empty.log"
        log.write_text("no scores here\n")
        monkeypatch.setattr("self_improvement.AUDIT_LOG", str(log))
        assert parse_audit_scores() == []

    def test_missing_log(self, tmp_path, monkeypatch):
        monkeypatch.setattr("self_improvement.AUDIT_LOG", str(tmp_path / "nope.log"))
        assert parse_audit_scores() == []


# ---------------------------------------------------------------------------
# Tests: calculate_averages
# ---------------------------------------------------------------------------

class TestCalculateAverages:
    def test_averages(self, tmp_audit_log):
        avgs = calculate_averages()
        assert avgs["count"] == 3
        # H: (9+8+9)/3 = 8.67
        assert avgs["H"] == pytest.approx(8.67, abs=0.01)
        # D: (9+8+6)/3 = 7.67
        assert avgs["D"] == pytest.approx(7.67, abs=0.01)

    def test_no_entries(self):
        avgs = calculate_averages([])
        assert avgs["count"] == 0
        assert avgs["H"] == 0.0


# ---------------------------------------------------------------------------
# Tests: identify_weakest
# ---------------------------------------------------------------------------

class TestIdentifyWeakest:
    def test_finds_weakest(self, tmp_audit_log):
        result = identify_weakest()
        # C: (7+8+9)/3=8.0, D: (9+8+6)/3=7.67 — D is weakest
        assert result[0] == "D"
        assert result[2] == "DataCorrect"

    def test_no_data(self):
        result = identify_weakest({"count": 0})
        assert result is None


# ---------------------------------------------------------------------------
# Tests: get_attempt_count
# ---------------------------------------------------------------------------

class TestGetAttemptCount:
    def test_reads_attempts(self, tmp_improvement_log):
        assert get_attempt_count("D") == 2

    def test_no_attempts(self, tmp_improvement_log):
        assert get_attempt_count("H") == 0

    def test_missing_log(self, tmp_path, monkeypatch):
        monkeypatch.setattr("self_improvement.IMPROVEMENT_LOG",
                            str(tmp_path / "nope.log"))
        assert get_attempt_count("D") == 0


# ---------------------------------------------------------------------------
# Tests: get_improvement_status
# ---------------------------------------------------------------------------

class TestGetImprovementStatus:
    def test_status_structure(self, tmp_audit_log, tmp_improvement_log):
        status = get_improvement_status()
        assert "averages" in status
        assert "weakest" in status
        assert "attempts" in status
        assert "recommendation" in status
        assert "recent_scores" in status
        assert "generated_at" in status

    def test_recommendation_improve(self, tmp_audit_log, tmp_improvement_log):
        # D avg = 7.67, below threshold? no (7.67 >= 7)
        # But it's still the weakest. If we lower D:
        status = get_improvement_status()
        # D is at 7.67 — above 7, so recommendation should say "at or above"
        assert "threshold" in status["recommendation"].lower() or \
               "lowest" in status["recommendation"].lower()


# ---------------------------------------------------------------------------
# Tests: store_task_scores
# ---------------------------------------------------------------------------

class TestStoreTaskScores:
    def test_stores_scores(self, tmp_db):
        result = store_task_scores("Test Task", {
            "H": 9, "R": 8, "S": 9, "C": 8, "D": 9, "U": 8, "X": 9
        })
        assert result["stored"] is True
        assert result["avg"] == pytest.approx(8.57, abs=0.01)

    def test_retrieves_stored(self, tmp_db):
        store_task_scores("Task A", {
            "H": 10, "R": 10, "S": 10, "C": 10, "D": 10, "U": 10, "X": 10
        })
        trends = get_score_trends()
        assert len(trends) == 1
        assert trends[0]["task_name"] == "Task A"
        assert trends[0]["avg_score"] == 10.0


# ---------------------------------------------------------------------------
# Tests: record_improvement_cycle
# ---------------------------------------------------------------------------

class TestRecordImprovementCycle:
    def test_records_cycle(self, tmp_db, tmp_improvement_log):
        result = record_improvement_cycle("D", 6.5, 7.2, "Added validation", True)
        assert result["criterion"] == "D"
        assert result["success"] is True
        assert result["attempt"] == 3  # 2 existing + 1 new

    def test_escalate_on_failure(self, tmp_db, tmp_improvement_log):
        result = record_improvement_cycle("D", 6.5, 6.5, "Tried again", False)
        assert result["escalate"] is True  # attempt 3 and failed

    def test_history(self, tmp_db, tmp_improvement_log):
        record_improvement_cycle("H", 7.0, 8.0, "Improved naming", True)
        history = get_improvement_history()
        assert len(history) == 1
        assert history[0]["criterion"] == "H"


# ---------------------------------------------------------------------------
# Tests: backfill_scores_from_audit
# ---------------------------------------------------------------------------

class TestBackfillScores:
    def test_backfills(self, tmp_audit_log, tmp_db):
        inserted = backfill_scores_from_audit()
        assert inserted == 3

    def test_idempotent(self, tmp_audit_log, tmp_db):
        backfill_scores_from_audit()
        inserted = backfill_scores_from_audit()
        assert inserted == 0  # already backfilled


# ---------------------------------------------------------------------------
# Tests: API endpoints (via FastAPI TestClient)
# ---------------------------------------------------------------------------

class TestSelfImprovementAPI:
    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Import app and create test client."""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
            from app import app as fastapi_app
            from fastapi.testclient import TestClient
            self.client = TestClient(fastapi_app)
        except Exception:
            pytest.skip("FastAPI app not importable")

    def test_status_endpoint(self):
        resp = self.client.get("/api/self-improvement/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "averages" in data

    def test_history_endpoint(self):
        resp = self.client.get("/api/self-improvement/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "cycles" in data
        assert "score_trends" in data

    def test_record_scores_validation(self):
        resp = self.client.post("/api/self-improvement/record-scores",
                                json={"task_name": ""})
        assert resp.status_code == 422

    def test_record_scores_out_of_range(self):
        resp = self.client.post("/api/self-improvement/record-scores",
                                json={"task_name": "test", "H": 15})
        assert resp.status_code == 422

    def test_record_cycle_bad_criterion(self):
        resp = self.client.post("/api/self-improvement/record-cycle",
                                json={"criterion": "Z", "action": "test"})
        assert resp.status_code == 422

    def test_backfill_endpoint(self):
        resp = self.client.post("/api/self-improvement/backfill")
        assert resp.status_code == 200
        assert "rows_inserted" in resp.json()
