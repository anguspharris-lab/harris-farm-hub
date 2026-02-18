"""Tests for employee roles import and API endpoints."""

import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from import_roles import (
    read_xlsx,
    validate_and_clean,
    deduplicate,
    insert_roles,
    build_metadata,
    build_report,
    run_import,
)


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_rows():
    """Clean row dicts as returned by validate_and_clean."""
    return [
        {"function": "Retail", "department": "Service", "job": "Supervisor"},
        {"function": "Retail", "department": "Perishable", "job": "Section Lead"},
        {"function": "Support Office", "department": "Finance", "job": "Analyst"},
        {"function": "Support Office", "department": "IT", "job": "Data Engineer"},
        {"function": "Wholesale-Sydney", "department": "Wholesale Business", "job": "Sales"},
    ]


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary SQLite database."""
    db_path = str(tmp_path / "test_hub.db")
    return db_path


# ---------------------------------------------------------------------------
# READ XLSX
# ---------------------------------------------------------------------------

class TestReadXlsx:
    def test_reads_real_file(self):
        xlsx = Path(os.path.expanduser(
            "~/Desktop/Working files/HFM Job Roles.xlsx"
        ))
        if not xlsx.exists():
            pytest.skip("HFM Job Roles.xlsx not found")
        rows = read_xlsx(xlsx)
        assert len(rows) == 211
        assert "Function" in rows[0]
        assert "Department" in rows[0]
        assert "Job" in rows[0]

    def test_first_row_is_retail(self):
        xlsx = Path(os.path.expanduser(
            "~/Desktop/Working files/HFM Job Roles.xlsx"
        ))
        if not xlsx.exists():
            pytest.skip("HFM Job Roles.xlsx not found")
        rows = read_xlsx(xlsx)
        assert rows[0]["Function"] == "Retail"


# ---------------------------------------------------------------------------
# VALIDATE AND CLEAN
# ---------------------------------------------------------------------------

class TestValidateAndClean:
    def test_valid_rows_pass(self):
        raw = [
            {"Function": "Retail", "Department": "Service", "Job": "Supervisor"},
            {"Function": "Support Office", "Department": "IT", "Job": "Analyst"},
        ]
        clean, warnings = validate_and_clean(raw, [])
        assert len(clean) == 2
        assert len(warnings) == 0

    def test_missing_function_rejected(self):
        raw = [{"Function": None, "Department": "IT", "Job": "Analyst"}]
        clean, warnings = validate_and_clean(raw, [])
        assert len(clean) == 0
        assert len(warnings) == 1

    def test_missing_job_rejected(self):
        raw = [{"Function": "Retail", "Department": "Service", "Job": ""}]
        clean, warnings = validate_and_clean(raw, [])
        assert len(clean) == 0
        assert len(warnings) == 1

    def test_whitespace_trimmed(self):
        raw = [{"Function": "  Retail  ", "Department": " IT ", "Job": " Analyst "}]
        clean, _ = validate_and_clean(raw, [])
        assert clean[0]["function"] == "Retail"
        assert clean[0]["department"] == "IT"
        assert clean[0]["job"] == "Analyst"


# ---------------------------------------------------------------------------
# DEDUPLICATE
# ---------------------------------------------------------------------------

class TestDeduplicate:
    def test_no_dupes(self, sample_rows):
        unique, dupes = deduplicate(sample_rows, [])
        assert len(unique) == 5
        assert len(dupes) == 0

    def test_removes_dupes(self, sample_rows):
        rows_with_dupe = sample_rows + [sample_rows[0].copy()]
        unique, dupes = deduplicate(rows_with_dupe, [])
        assert len(unique) == 5
        assert len(dupes) == 1

    def test_keeps_first_occurrence(self, sample_rows):
        rows_with_dupe = sample_rows + [sample_rows[0].copy()]
        unique, _ = deduplicate(rows_with_dupe, [])
        assert unique[0] == sample_rows[0]


# ---------------------------------------------------------------------------
# INSERT ROLES
# ---------------------------------------------------------------------------

class TestInsertRoles:
    def test_insert_replace_mode(self, sample_rows, temp_db):
        count = insert_roles(temp_db, sample_rows, "replace", [])
        assert count == 5

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM employee_roles")
        assert c.fetchone()[0] == 5
        conn.close()

    def test_insert_append_mode(self, sample_rows, temp_db):
        insert_roles(temp_db, sample_rows[:3], "replace", [])
        count = insert_roles(temp_db, sample_rows, "append", [])
        assert count == 2  # only 2 new rows

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM employee_roles")
        assert c.fetchone()[0] == 5
        conn.close()

    def test_replace_clears_existing(self, sample_rows, temp_db):
        insert_roles(temp_db, sample_rows, "replace", [])
        insert_roles(temp_db, sample_rows[:2], "replace", [])

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM employee_roles")
        assert c.fetchone()[0] == 2
        conn.close()

    def test_idempotent_import(self, sample_rows, temp_db):
        insert_roles(temp_db, sample_rows, "replace", [])
        insert_roles(temp_db, sample_rows, "replace", [])

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM employee_roles")
        assert c.fetchone()[0] == 5
        conn.close()

    def test_timestamps_set(self, sample_rows, temp_db):
        insert_roles(temp_db, sample_rows[:1], "replace", [])

        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT created_at, updated_at FROM employee_roles")
        row = c.fetchone()
        assert row["created_at"] is not None
        assert row["updated_at"] is not None
        conn.close()


# ---------------------------------------------------------------------------
# BUILD METADATA
# ---------------------------------------------------------------------------

class TestBuildMetadata:
    def test_correct_counts(self, sample_rows):
        meta = build_metadata(sample_rows, "test.xlsx")
        assert meta["total_roles"] == 5
        assert meta["unique_functions"] == 3
        assert meta["unique_departments"] == 5
        assert meta["unique_jobs"] == 5
        assert meta["source_file"] == "test.xlsx"

    def test_lists_sorted(self, sample_rows):
        meta = build_metadata(sample_rows, "test.xlsx")
        assert meta["functions"] == sorted(meta["functions"])
        assert meta["departments"] == sorted(meta["departments"])
        assert meta["jobs"] == sorted(meta["jobs"])


# ---------------------------------------------------------------------------
# BUILD REPORT
# ---------------------------------------------------------------------------

class TestBuildReport:
    def test_report_contains_summary(self, sample_rows):
        report = build_report(sample_rows, [], [], 5)
        assert "Successful imports: 5" in report
        assert "Duplicates found:   0" in report

    def test_report_contains_sample(self, sample_rows):
        report = build_report(sample_rows, [], [], 5)
        assert "Supervisor" in report

    def test_report_contains_warnings(self, sample_rows):
        report = build_report(sample_rows, [], ["Row 5: missing Function"], 5)
        assert "Row 5: missing Function" in report


# ---------------------------------------------------------------------------
# RUN IMPORT (end-to-end)
# ---------------------------------------------------------------------------

class TestRunImport:
    def test_full_import(self, tmp_path):
        xlsx = Path(os.path.expanduser(
            "~/Desktop/Working files/HFM Job Roles.xlsx"
        ))
        if not xlsx.exists():
            pytest.skip("HFM Job Roles.xlsx not found")

        db_path = str(tmp_path / "test.db")
        out_dir = str(tmp_path / "roles")

        result = run_import(
            xlsx_path=str(xlsx),
            db_path=db_path,
            mode="replace",
            output_dir=out_dir,
        )

        assert result["status"] == "success"
        assert result["rows_imported"] == 211
        assert result["duplicates"] == 0
        assert result["warnings"] == 0

    def test_output_files_created(self, tmp_path):
        xlsx = Path(os.path.expanduser(
            "~/Desktop/Working files/HFM Job Roles.xlsx"
        ))
        if not xlsx.exists():
            pytest.skip("HFM Job Roles.xlsx not found")

        db_path = str(tmp_path / "test.db")
        out_dir = tmp_path / "roles"

        run_import(xlsx_path=str(xlsx), db_path=db_path, output_dir=str(out_dir))

        assert (out_dir / "role_metadata.json").exists()
        assert (out_dir / "import_report.txt").exists()
        assert (out_dir / "import_log.txt").exists()

    def test_metadata_json_valid(self, tmp_path):
        xlsx = Path(os.path.expanduser(
            "~/Desktop/Working files/HFM Job Roles.xlsx"
        ))
        if not xlsx.exists():
            pytest.skip("HFM Job Roles.xlsx not found")

        db_path = str(tmp_path / "test.db")
        out_dir = tmp_path / "roles"

        run_import(xlsx_path=str(xlsx), db_path=db_path, output_dir=str(out_dir))

        with open(out_dir / "role_metadata.json") as f:
            meta = json.load(f)

        assert meta["total_roles"] == 211
        assert meta["unique_functions"] == 3
        assert "Retail" in meta["functions"]

    def test_missing_file_returns_error(self, tmp_path):
        result = run_import(
            xlsx_path=str(tmp_path / "nonexistent.xlsx"),
            db_path=str(tmp_path / "test.db"),
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# API ENDPOINTS (via test client)
# ---------------------------------------------------------------------------

class TestRolesAPI:
    @pytest.fixture
    def client(self, tmp_path):
        """FastAPI test client with a fresh database."""
        from app import app, config, init_hub_database

        db_path = str(tmp_path / "api_test.db")
        config.HUB_DB = db_path
        init_hub_database()

        # Insert test data
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        now = datetime.now().isoformat()
        test_roles = [
            ("Retail", "Service", "Supervisor", now, now),
            ("Retail", "Perishable", "Section Lead", now, now),
            ("Support Office", "Finance", "Analyst", now, now),
        ]
        c.executemany(
            "INSERT INTO employee_roles (function, department, job, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            test_roles,
        )
        conn.commit()
        conn.close()

        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_get_roles_all(self, client):
        resp = client.get("/api/roles")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3

    def test_get_roles_filter_function(self, client):
        resp = client.get("/api/roles?function=Retail")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2

    def test_get_roles_filter_department(self, client):
        resp = client.get("/api/roles?department=Finance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1

    def test_get_roles_filter_no_match(self, client):
        resp = client.get("/api/roles?function=Nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0

    def test_get_metadata(self, client):
        resp = client.get("/api/roles/metadata")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_roles"] == 3
        assert data["unique_functions"] == 2
        assert "Retail" in data["functions"]
        assert data["source_file"] == "HFM Job Roles.xlsx"

    def test_get_metadata_empty_db(self, tmp_path):
        from app import app, config, init_hub_database

        db_path = str(tmp_path / "empty.db")
        config.HUB_DB = db_path
        init_hub_database()

        from fastapi.testclient import TestClient
        client = TestClient(app)

        resp = client.get("/api/roles/metadata")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_roles"] == 0
