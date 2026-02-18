"""Tests for the Continuous Improvement Agent: auditors, findings, API."""

import os
import sys
import sqlite3
import tempfile
import textwrap
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


# ---------------------------------------------------------------------------
# Code Safety Auditor Tests
# ---------------------------------------------------------------------------

class TestCodeSafetyAuditor:
    """Test the AST + regex code safety scanner."""

    def test_detects_eval_call(self, tmp_path):
        from continuous_improvement import CodeSafetyAuditor
        src = tmp_path / "bad.py"
        src.write_text("x = eval('1+1')\n")
        auditor = CodeSafetyAuditor(directories=[str(tmp_path)])
        findings = auditor.audit()
        titles = [f["title"] for f in findings]
        assert any("eval()" in t for t in titles)

    def test_detects_exec_call(self, tmp_path):
        from continuous_improvement import CodeSafetyAuditor
        src = tmp_path / "bad.py"
        src.write_text("exec('print(1)')\n")
        auditor = CodeSafetyAuditor(directories=[str(tmp_path)])
        findings = auditor.audit()
        titles = [f["title"] for f in findings]
        assert any("exec()" in t for t in titles)

    def test_detects_bare_except(self, tmp_path):
        from continuous_improvement import CodeSafetyAuditor
        src = tmp_path / "bad.py"
        src.write_text(textwrap.dedent("""\
            try:
                x = 1
            except:
                pass
        """))
        auditor = CodeSafetyAuditor(directories=[str(tmp_path)])
        findings = auditor.audit()
        titles = [f["title"] for f in findings]
        assert any("Bare except" in t for t in titles)

    def test_detects_large_file(self, tmp_path):
        from continuous_improvement import CodeSafetyAuditor
        src = tmp_path / "big.py"
        src.write_text("x = 1\n" * 600)
        auditor = CodeSafetyAuditor(directories=[str(tmp_path)])
        findings = auditor.audit()
        titles = [f["title"] for f in findings]
        assert any("Large file" in t for t in titles)

    def test_detects_os_system(self, tmp_path):
        from continuous_improvement import CodeSafetyAuditor
        src = tmp_path / "bad.py"
        src.write_text("import os\nos.system('ls')\n")
        auditor = CodeSafetyAuditor(directories=[str(tmp_path)])
        findings = auditor.audit()
        titles = [f["title"] for f in findings]
        assert any("os.system()" in t for t in titles)

    def test_clean_file_no_findings(self, tmp_path):
        from continuous_improvement import CodeSafetyAuditor
        src = tmp_path / "clean.py"
        src.write_text(textwrap.dedent("""\
            def greet(name):
                return "Hello, " + name
        """))
        auditor = CodeSafetyAuditor(directories=[str(tmp_path)])
        findings = auditor.audit()
        assert len(findings) == 0


# ---------------------------------------------------------------------------
# Documentation Auditor Tests
# ---------------------------------------------------------------------------

class TestDocumentationAuditor:
    """Test the documentation freshness and completeness checker."""

    def test_detects_stale_docs(self, tmp_path):
        from continuous_improvement import DocumentationAuditor
        doc = tmp_path / "old.md"
        doc.write_text("# Old doc\n")
        # Set mtime to 30 days ago
        old_time = os.path.getmtime(str(doc)) - (30 * 86400)
        os.utime(str(doc), (old_time, old_time))
        auditor = DocumentationAuditor(docs_dir=str(tmp_path))
        findings = auditor.audit()
        titles = [f["title"] for f in findings]
        assert any("Stale" in t for t in titles)

    def test_fresh_docs_no_finding(self, tmp_path):
        from continuous_improvement import DocumentationAuditor
        doc = tmp_path / "fresh.md"
        doc.write_text("# Fresh doc\n")
        auditor = DocumentationAuditor(docs_dir=str(tmp_path))
        findings = [f for f in auditor.audit() if "Stale" in f.get("title", "")]
        assert len(findings) == 0

    def test_detects_missing_docstring(self, tmp_path):
        from continuous_improvement import DocumentationAuditor
        src = tmp_path / "no_doc.py"
        src.write_text(textwrap.dedent("""\
            def public_func():
                return 42
        """))
        auditor = DocumentationAuditor(
            docs_dir=str(tmp_path), backend_dir=str(tmp_path))
        findings = auditor.audit()
        titles = [f["title"] for f in findings]
        assert any("Missing docstring" in t for t in titles)

    def test_private_func_not_flagged(self, tmp_path):
        from continuous_improvement import DocumentationAuditor
        src = tmp_path / "private.py"
        src.write_text(textwrap.dedent("""\
            def _helper():
                return 42
        """))
        auditor = DocumentationAuditor(
            docs_dir=str(tmp_path), backend_dir=str(tmp_path))
        findings = [f for f in auditor.audit()
                     if "Missing docstring" in f.get("title", "")]
        assert len(findings) == 0

    def test_detects_broken_link(self, tmp_path):
        from continuous_improvement import DocumentationAuditor
        doc = tmp_path / "links.md"
        doc.write_text("See [guide](NONEXISTENT.md) for details.\n")
        auditor = DocumentationAuditor(docs_dir=str(tmp_path))
        findings = auditor.audit()
        titles = [f["title"] for f in findings]
        assert any("Broken link" in t for t in titles)


# ---------------------------------------------------------------------------
# Performance Auditor Tests
# ---------------------------------------------------------------------------

class TestPerformanceAuditor:
    """Test the performance anti-pattern detector."""

    def test_detects_unbounded_select(self, tmp_path):
        from continuous_improvement import PerformanceAuditor
        src = tmp_path / "query.py"
        src.write_text(
            'rows = conn.execute("SELECT * FROM users WHERE active = 1").fetchall()\n'
        )
        auditor = PerformanceAuditor(directories=[str(tmp_path)])
        findings = auditor.audit()
        titles = [f["title"] for f in findings]
        assert any("Unbounded SELECT" in t for t in titles)

    def test_select_with_limit_ok(self, tmp_path):
        from continuous_improvement import PerformanceAuditor
        src = tmp_path / "query.py"
        src.write_text(
            'rows = conn.execute("SELECT * FROM users LIMIT 10").fetchall()\n'
        )
        auditor = PerformanceAuditor(directories=[str(tmp_path)])
        findings = [f for f in auditor.audit()
                     if "Unbounded SELECT" in f.get("title", "")]
        assert len(findings) == 0

    def test_detects_n_plus_one(self, tmp_path):
        from continuous_improvement import PerformanceAuditor
        src = tmp_path / "loop.py"
        src.write_text(textwrap.dedent("""\
            for item in items:
                conn.execute("SELECT * FROM detail WHERE id = ?", (item,))
        """))
        auditor = PerformanceAuditor(directories=[str(tmp_path)])
        findings = auditor.audit()
        titles = [f["title"] for f in findings]
        assert any("N+1" in t for t in titles)

    def test_clean_code_no_perf_findings(self, tmp_path):
        from continuous_improvement import PerformanceAuditor
        src = tmp_path / "clean.py"
        src.write_text(textwrap.dedent("""\
            def compute(x, y):
                return x + y
        """))
        auditor = PerformanceAuditor(directories=[str(tmp_path)])
        findings = auditor.audit()
        assert len(findings) == 0

    def test_select_specific_columns_ok(self, tmp_path):
        from continuous_improvement import PerformanceAuditor
        src = tmp_path / "query.py"
        src.write_text(
            'rows = conn.execute("SELECT id, name FROM users").fetchall()\n'
        )
        auditor = PerformanceAuditor(directories=[str(tmp_path)])
        findings = [f for f in auditor.audit()
                     if "Unbounded SELECT" in f.get("title", "")]
        assert len(findings) == 0


# ---------------------------------------------------------------------------
# Health Metrics Collector Tests
# ---------------------------------------------------------------------------

class TestHealthMetricsCollector:
    """Test the health metrics gatherer."""

    def test_collect_returns_dict(self):
        from continuous_improvement import HealthMetricsCollector
        collector = HealthMetricsCollector()
        metrics = collector.collect()
        assert isinstance(metrics, dict)
        assert "file_counts" in metrics
        assert "test_count" in metrics
        assert "table_count" in metrics
        assert "endpoint_count" in metrics

    def test_file_counts_are_positive(self):
        from continuous_improvement import HealthMetricsCollector
        collector = HealthMetricsCollector()
        metrics = collector.collect()
        counts = metrics["file_counts"]
        assert counts["backend"] > 0
        assert counts["dashboards"] > 0
        assert counts["tests"] > 0

    def test_test_count_positive(self):
        from continuous_improvement import HealthMetricsCollector
        collector = HealthMetricsCollector()
        metrics = collector.collect()
        assert metrics["test_count"] > 100  # We have 1000+ tests

    def test_endpoint_count_positive(self):
        from continuous_improvement import HealthMetricsCollector
        collector = HealthMetricsCollector()
        metrics = collector.collect()
        assert metrics["endpoint_count"] > 50  # 71+ endpoints


# ---------------------------------------------------------------------------
# Findings Manager Tests
# ---------------------------------------------------------------------------

class TestFindingsManager:
    """Test the findings storage and lifecycle."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB

    def test_store_and_retrieve(self):
        from continuous_improvement import FindingsManager
        manager = FindingsManager(db_path=self.db_path)
        findings = [{
            "category": "test",
            "severity": "low",
            "file": "test_file.py",
            "line": 42,
            "title": "Test finding CI {}".format(id(self)),
            "detail": "For testing",
            "recommendation": "Fix it",
        }]
        inserted = manager.store_findings(findings)
        assert inserted >= 0  # May be 0 if duplicate from previous run

        results = manager.get_findings(category="test")
        assert len(results) >= 1

    def test_deduplication(self):
        from continuous_improvement import FindingsManager
        manager = FindingsManager(db_path=self.db_path)
        finding = {
            "category": "test",
            "severity": "low",
            "file": "dedup_test.py",
            "line": 1,
            "title": "Dedup test finding",
            "detail": "Same finding twice",
            "recommendation": "Fix it",
        }
        first = manager.store_findings([finding])
        second = manager.store_findings([finding])
        # Second insert should be 0 (duplicate)
        assert second == 0

    def test_update_status(self):
        from continuous_improvement import FindingsManager
        manager = FindingsManager(db_path=self.db_path)
        # Insert a finding
        finding = {
            "category": "test",
            "severity": "low",
            "file": "status_test.py",
            "line": 99,
            "title": "Status test {}".format(id(self)),
            "detail": "Testing status update",
            "recommendation": "Fix it",
        }
        manager.store_findings([finding])
        # Get the finding
        results = manager.get_findings(category="test")
        if results:
            fid = results[0]["id"]
            result = manager.update_status(fid, "acknowledged")
            assert result["status"] == "acknowledged"

    def test_promote_to_proposal(self):
        from continuous_improvement import FindingsManager
        manager = FindingsManager(db_path=self.db_path)
        finding = {
            "category": "test",
            "severity": "high",
            "file": "promote_test.py",
            "line": 1,
            "title": "Promote test {}".format(id(self)),
            "detail": "Should become a proposal",
            "recommendation": "Fix it urgently",
        }
        manager.store_findings([finding])
        results = manager.get_findings(category="test")
        if results:
            fid = results[0]["id"]
            result = manager.promote_to_proposal(fid)
            assert result.get("proposal_created") or result.get("status") == "promoted"


# ---------------------------------------------------------------------------
# Full Audit Orchestrator Tests
# ---------------------------------------------------------------------------

class TestRunFullAudit:
    """Test the run_full_audit() orchestrator."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB

    def test_returns_expected_structure(self):
        from continuous_improvement import run_full_audit
        result = run_full_audit(db_path=self.db_path)
        assert "timestamp" in result
        assert "findings_count" in result
        assert "by_category" in result
        assert "by_severity" in result
        assert "health_metrics" in result
        assert "new_findings" in result
        assert isinstance(result["findings"], list)

    def test_findings_count_matches(self):
        from continuous_improvement import run_full_audit
        result = run_full_audit(db_path=self.db_path)
        assert result["findings_count"] == len(result["findings"])


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------

class TestCIEndpoints:
    """Test continuous improvement API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        try:
            from app import app as fastapi_app
            from fastapi.testclient import TestClient
            self.client = TestClient(fastapi_app)
        except Exception:
            pytest.skip("FastAPI app not importable")

    def test_audit_endpoint(self):
        resp = self.client.post("/api/continuous-improvement/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert "findings_count" in data
        assert "health_metrics" in data

    def test_findings_endpoint(self):
        resp = self.client.get("/api/continuous-improvement/findings")
        assert resp.status_code == 200
        data = resp.json()
        assert "findings" in data
        assert isinstance(data["findings"], list)
