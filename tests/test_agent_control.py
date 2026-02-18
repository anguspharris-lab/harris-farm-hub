"""Tests for the Agent Control Panel: tables, seeding, and API endpoints."""

import os
import sys
import sqlite3
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


# ---------------------------------------------------------------------------
# Table & Seed Tests
# ---------------------------------------------------------------------------

class TestAgentControlTables:
    """Verify agent_proposals and agent_scores tables exist and have schema."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB

    def test_agent_proposals_table_exists(self):
        conn = sqlite3.connect(self.db_path)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        conn.close()
        assert "agent_proposals" in tables

    def test_agent_scores_table_exists(self):
        conn = sqlite3.connect(self.db_path)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        conn.close()
        assert "agent_scores" in tables

    def test_agent_proposals_columns(self):
        conn = sqlite3.connect(self.db_path)
        cols = [r[1] for r in conn.execute(
            "PRAGMA table_info(agent_proposals)"
        ).fetchall()]
        conn.close()
        required = ["id", "agent_name", "task_type", "description",
                     "risk_level", "status", "reviewer", "reviewer_notes"]
        for col in required:
            assert col in cols

    def test_agent_scores_columns(self):
        conn = sqlite3.connect(self.db_path)
        cols = [r[1] for r in conn.execute(
            "PRAGMA table_info(agent_scores)"
        ).fetchall()]
        conn.close()
        required = ["id", "agent_name", "metric", "score", "baseline",
                     "evidence", "timestamp"]
        for col in required:
            assert col in cols


class TestAgentControlSeeding:
    """Verify sample data is seeded correctly."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB

    def test_proposals_seeded(self):
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM agent_proposals").fetchone()[0]
        conn.close()
        assert count >= 4  # 4 sample proposals

    def test_scores_seeded(self):
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM agent_scores").fetchone()[0]
        conn.close()
        assert count >= 7  # 7 sample scores

    def test_proposal_status_values(self):
        conn = sqlite3.connect(self.db_path)
        statuses = [r[0] for r in conn.execute(
            "SELECT DISTINCT status FROM agent_proposals"
        ).fetchall()]
        conn.close()
        for s in statuses:
            assert s in ("PENDING", "APPROVED", "REJECTED", "COMPLETED", "FAILED")

    def test_score_metric_values(self):
        conn = sqlite3.connect(self.db_path)
        metrics = [r[0] for r in conn.execute(
            "SELECT DISTINCT metric FROM agent_scores"
        ).fetchall()]
        conn.close()
        valid = {"ACCURACY", "SPEED", "INSIGHT_QUALITY", "USER_SATISFACTION"}
        for m in metrics:
            assert m in valid


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------

class TestAgentControlAPI:
    """Test the /api/admin/ endpoints."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        try:
            from app import app as fastapi_app
            from fastapi.testclient import TestClient
            self.client = TestClient(fastapi_app)
        except Exception:
            pytest.skip("FastAPI app not importable")

    def test_list_proposals(self):
        resp = self.client.get("/api/admin/agent-proposals")
        assert resp.status_code == 200
        data = resp.json()
        assert "proposals" in data
        assert len(data["proposals"]) >= 4

    def test_list_proposals_filtered(self):
        resp = self.client.get("/api/admin/agent-proposals",
                               params={"status": "PENDING"})
        assert resp.status_code == 200
        for prop in resp.json()["proposals"]:
            assert prop["status"] == "PENDING"

    def test_list_agent_scores(self):
        resp = self.client.get("/api/admin/agent-scores")
        assert resp.status_code == 200
        data = resp.json()
        assert "scores" in data
        assert "agent_averages" in data

    def test_record_agent_score(self):
        resp = self.client.post("/api/admin/agent-scores", json={
            "agent_name": "TestAgent",
            "metric": "ACCURACY",
            "score": 7.5,
            "evidence": "Test measurement",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_record_score_bad_metric(self):
        resp = self.client.post("/api/admin/agent-scores", json={
            "agent_name": "TestAgent",
            "metric": "INVALID",
            "score": 7.0,
        })
        assert resp.status_code == 422

    def test_record_score_out_of_range(self):
        resp = self.client.post("/api/admin/agent-scores", json={
            "agent_name": "TestAgent",
            "metric": "SPEED",
            "score": 15.0,
        })
        assert resp.status_code == 422

    def test_approve_nonexistent(self):
        resp = self.client.post("/api/admin/agent-proposals/99999/approve",
                                json={"notes": "test"})
        assert resp.status_code == 404

    def test_reject_without_notes(self):
        # First get a pending proposal ID
        proposals = self.client.get(
            "/api/admin/agent-proposals", params={"status": "PENDING"}
        ).json()["proposals"]
        if not proposals:
            pytest.skip("No pending proposals to test")
        pid = proposals[0]["id"]
        resp = self.client.post(
            "/api/admin/agent-proposals/{}/reject".format(pid),
            json={"notes": ""},
        )
        assert resp.status_code == 422

    def test_trigger_analysis(self):
        resp = self.client.post("/api/admin/trigger-analysis",
                                json={"type": "analysis"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["tasks"]) >= 2

    def test_approve_proposal(self):
        # Create a fresh proposal to approve
        from app import config
        conn = sqlite3.connect(config.HUB_DB)
        conn.execute(
            "INSERT INTO agent_proposals (agent_name, task_type, description, "
            "risk_level) VALUES (?, ?, ?, ?)",
            ("TestApproveAgent", "ANALYSIS", "Test proposal for approval", "LOW"),
        )
        conn.commit()
        pid = conn.execute(
            "SELECT id FROM agent_proposals WHERE agent_name = 'TestApproveAgent' "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        conn.close()

        resp = self.client.post(
            "/api/admin/agent-proposals/{}/approve".format(pid),
            json={"notes": "Approved in test"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify status changed
        conn = sqlite3.connect(config.HUB_DB)
        row = conn.execute(
            "SELECT status, reviewer FROM agent_proposals WHERE id = ?", (pid,)
        ).fetchone()
        conn.close()
        assert row[0] == "APPROVED"
        assert row[1] == "Gus Harris"

    def test_reject_proposal(self):
        from app import config
        conn = sqlite3.connect(config.HUB_DB)
        conn.execute(
            "INSERT INTO agent_proposals (agent_name, task_type, description, "
            "risk_level) VALUES (?, ?, ?, ?)",
            ("TestRejectAgent", "REPORT", "Test proposal for rejection", "LOW"),
        )
        conn.commit()
        pid = conn.execute(
            "SELECT id FROM agent_proposals WHERE agent_name = 'TestRejectAgent' "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        conn.close()

        resp = self.client.post(
            "/api/admin/agent-proposals/{}/reject".format(pid),
            json={"notes": "Not needed right now"},
        )
        assert resp.status_code == 200

        conn = sqlite3.connect(config.HUB_DB)
        row = conn.execute(
            "SELECT status FROM agent_proposals WHERE id = ?", (pid,)
        ).fetchone()
        conn.close()
        assert row[0] == "REJECTED"

    def test_cannot_approve_non_pending(self):
        """Cannot approve an already-approved proposal."""
        from app import config
        conn = sqlite3.connect(config.HUB_DB)
        conn.execute(
            "INSERT INTO agent_proposals (agent_name, task_type, description, "
            "status) VALUES (?, ?, ?, ?)",
            ("TestAgent", "ANALYSIS", "Already approved", "APPROVED"),
        )
        conn.commit()
        pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        resp = self.client.post(
            "/api/admin/agent-proposals/{}/approve".format(pid),
            json={"notes": "test"},
        )
        assert resp.status_code == 400
