"""Tests for Transaction Data Layer — DuckDB parquet query engine and API endpoints."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from transaction_layer import (
    TransactionStore, LOCAL_PARQUET_FILES, EXTERNAL_PARQUET_FILES, STORE_NAMES,
)


# ---------------------------------------------------------------------------
# PARQUET FILE EXISTENCE
# ---------------------------------------------------------------------------

class TestParquetFiles:
    """Check that parquet files exist in either local or external location."""

    def _resolve(self, fy):
        """Return the first existing path for a fiscal year."""
        local = LOCAL_PARQUET_FILES.get(fy)
        if local and local.exists():
            return local
        external = EXTERNAL_PARQUET_FILES.get(fy)
        if external and external.exists():
            return external
        return None

    def test_fy24_exists(self):
        assert self._resolve("FY24") is not None, "FY24 parquet missing"

    def test_fy25_exists(self):
        assert self._resolve("FY25") is not None, "FY25 parquet missing"

    def test_fy26_exists(self):
        assert self._resolve("FY26") is not None, "FY26 parquet missing"

    def test_files_are_large(self):
        for fy in ["FY24", "FY25", "FY26"]:
            path = self._resolve(fy)
            assert path is not None, f"{fy} parquet missing"
            size_mb = path.stat().st_size / (1024 * 1024)
            assert size_mb > 100, f"{fy} parquet is only {size_mb:.0f}MB"


# ---------------------------------------------------------------------------
# STORE NAMES REFERENCE
# ---------------------------------------------------------------------------

class TestStoreNames:
    def test_store_count(self):
        assert len(STORE_NAMES) >= 30

    def test_known_stores(self):
        assert STORE_NAMES["28"] == "Mosman"
        assert STORE_NAMES["66"] == "Newcastle"
        assert STORE_NAMES["70"] == "West End QLD"

    def test_all_values_are_strings(self):
        for k, v in STORE_NAMES.items():
            assert isinstance(k, str)
            assert isinstance(v, str)


# ---------------------------------------------------------------------------
# TRANSACTION STORE INIT
# ---------------------------------------------------------------------------

class TestTransactionStoreInit:
    def test_creates_instance(self):
        ts = TransactionStore()
        assert ts is not None

    def test_has_three_fys(self):
        ts = TransactionStore()
        assert len(ts.available_fys) == 3
        assert set(ts.available_fys.keys()) == {"FY24", "FY25", "FY26"}


# ---------------------------------------------------------------------------
# SUMMARY QUERY
# ---------------------------------------------------------------------------

class TestSummary:
    @pytest.fixture(scope="class")
    def summary(self):
        ts = TransactionStore()
        return ts.summary()

    def test_returns_three_fiscal_years(self, summary):
        assert summary["total_fiscal_years"] == 3

    def test_total_rows_reasonable(self, summary):
        # Should be 383M ± 1M
        assert summary["total_rows"] > 380_000_000
        assert summary["total_rows"] < 390_000_000

    def test_fy24_row_count(self, summary):
        fy24 = next(f for f in summary["fiscal_years"] if f["fiscal_year"] == "FY24")
        assert fy24["row_count"] > 130_000_000

    def test_fy25_row_count(self, summary):
        fy25 = next(f for f in summary["fiscal_years"] if f["fiscal_year"] == "FY25")
        assert fy25["row_count"] > 145_000_000

    def test_fy26_row_count(self, summary):
        fy26 = next(f for f in summary["fiscal_years"] if f["fiscal_year"] == "FY26")
        assert fy26["row_count"] > 90_000_000

    def test_revenue_is_positive(self, summary):
        for fy in summary["fiscal_years"]:
            assert fy["total_revenue"] > 0

    def test_store_counts(self, summary):
        fy24 = next(f for f in summary["fiscal_years"] if f["fiscal_year"] == "FY24")
        assert fy24["store_count"] >= 30
        fy26 = next(f for f in summary["fiscal_years"] if f["fiscal_year"] == "FY26")
        assert fy26["store_count"] >= 34


# ---------------------------------------------------------------------------
# TOP ITEMS
# ---------------------------------------------------------------------------

class TestTopItems:
    @pytest.fixture(scope="class")
    def ts(self):
        return TransactionStore()

    def test_returns_correct_limit(self, ts):
        items = ts.top_items("2025-07-01", "2026-03-01", limit=5)
        assert len(items) == 5

    def test_items_sorted_by_revenue(self, ts):
        items = ts.top_items("2025-07-01", "2026-03-01", limit=10)
        revenues = [i["total_revenue"] for i in items]
        assert revenues == sorted(revenues, reverse=True)

    def test_store_filter(self, ts):
        items = ts.top_items("2025-07-01", "2026-03-01",
                             store_id="28", limit=5)
        assert len(items) == 5
        # Mosman revenue should be less than network total
        mosman_top = items[0]["total_revenue"]
        network = ts.top_items("2025-07-01", "2026-03-01", limit=1)
        assert mosman_top < network[0]["total_revenue"]

    def test_items_have_expected_fields(self, ts):
        items = ts.top_items("2025-07-01", "2026-03-01", limit=1)
        item = items[0]
        assert "plu_item_id" in item
        assert "transaction_count" in item
        assert "total_revenue" in item
        assert "total_qty" in item


# ---------------------------------------------------------------------------
# STORE TREND
# ---------------------------------------------------------------------------

class TestStoreTrend:
    @pytest.fixture(scope="class")
    def ts(self):
        return TransactionStore()

    def test_daily_grain(self, ts):
        trend = ts.store_trend("28", "2026-01-01", "2026-01-08", grain="daily")
        assert len(trend) == 7  # 7 days

    def test_monthly_grain(self, ts):
        trend = ts.store_trend("28", "2025-07-01", "2026-01-01", grain="monthly")
        assert len(trend) == 6  # Jul-Dec

    def test_revenue_positive(self, ts):
        trend = ts.store_trend("28", "2026-01-01", "2026-02-01", grain="daily")
        for day in trend:
            assert day["revenue"] > 0

    def test_has_expected_fields(self, ts):
        trend = ts.store_trend("28", "2026-01-01", "2026-01-02", grain="daily")
        assert len(trend) >= 1
        day = trend[0]
        for field in ("period", "line_items", "transactions", "revenue"):
            assert field in day


# ---------------------------------------------------------------------------
# PLU PERFORMANCE
# ---------------------------------------------------------------------------

class TestPLUPerformance:
    def test_known_plu(self):
        ts = TransactionStore()
        result = ts.plu_performance("4322", start="2025-07-01", end="2026-03-01")
        assert result["plu_item_id"] == "4322"
        assert result["total_revenue"] > 0
        assert result["stores_sold"] > 0
        assert len(result["by_store"]) > 0

    def test_by_store_has_names(self):
        ts = TransactionStore()
        result = ts.plu_performance("4322", start="2025-07-01", end="2026-03-01")
        for store in result["by_store"]:
            assert "store_name" in store
            assert "revenue" in store


# ---------------------------------------------------------------------------
# FREEFORM SQL VALIDATION
# ---------------------------------------------------------------------------

class TestSQLValidation:
    def test_valid_select(self):
        assert TransactionStore.validate_freeform_sql(
            "SELECT COUNT(*) FROM transactions") is None

    def test_rejects_insert(self):
        result = TransactionStore.validate_freeform_sql(
            "INSERT INTO transactions VALUES (1)")
        assert result is not None

    def test_rejects_drop(self):
        result = TransactionStore.validate_freeform_sql(
            "DROP TABLE transactions")
        assert result is not None

    def test_rejects_delete(self):
        result = TransactionStore.validate_freeform_sql(
            "DELETE FROM transactions")
        assert result is not None

    def test_rejects_non_select(self):
        result = TransactionStore.validate_freeform_sql(
            "UPDATE transactions SET x=1")
        assert result is not None

    def test_rejects_create(self):
        result = TransactionStore.validate_freeform_sql(
            "CREATE TABLE foo (id INT)")
        assert result is not None


# ---------------------------------------------------------------------------
# FREEFORM QUERY EXECUTION
# ---------------------------------------------------------------------------

class TestFreeformQuery:
    def test_simple_count(self):
        ts = TransactionStore()
        result = ts.query(
            "SELECT COUNT(*) AS n FROM transactions WHERE fiscal_year = 'FY26'")
        assert len(result) == 1
        assert result[0]["n"] > 90_000_000

    def test_max_rows_respected(self):
        ts = TransactionStore()
        result = ts.query(
            "SELECT * FROM transactions WHERE fiscal_year = 'FY26' LIMIT 100",
            max_rows=50)
        assert len(result) == 50


# ---------------------------------------------------------------------------
# QUERY LIBRARY
# ---------------------------------------------------------------------------

class TestQueryLibrary:
    def test_catalog_not_empty(self):
        from transaction_queries import get_query_catalog
        catalog = get_query_catalog()
        assert len(catalog) >= 15

    def test_run_gst_split(self):
        from transaction_queries import run_query
        ts = TransactionStore()
        result = run_query(ts, "gst_category_split",
                           start="2025-07-01", end="2026-03-01")
        assert len(result) == 2  # GST-Free and GST
        categories = {r["category"] for r in result}
        assert "GST-Free (Fresh)" in categories

    def test_run_hourly_pattern(self):
        from transaction_queries import run_query
        ts = TransactionStore()
        result = run_query(ts, "hourly_pattern",
                           store_id="28", start="2026-01-01", end="2026-02-01")
        assert len(result) >= 10  # Should have multiple hours

    def test_unknown_query_raises(self):
        from transaction_queries import run_query
        ts = TransactionStore()
        with pytest.raises(ValueError, match="Unknown query"):
            run_query(ts, "nonexistent_query")


# ---------------------------------------------------------------------------
# API ENDPOINTS (via test client)
# ---------------------------------------------------------------------------

class TestTransactionAPI:
    @pytest.fixture(scope="class")
    def client(self):
        from app import app
        # Initialize txn_store on app.state (normally done in lifespan)
        app.state.txn_store = TransactionStore()
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_summary_endpoint(self, client):
        resp = client.get("/api/transactions/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "fiscal_years" in data
        assert data["total_rows"] > 380_000_000

    def test_stores_endpoint(self, client):
        resp = client.get("/api/transactions/stores")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 30

    def test_top_items_endpoint(self, client):
        resp = client.get("/api/transactions/top-items",
                          params={"start": "2025-07-01", "end": "2026-03-01",
                                  "limit": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3

    def test_store_trend_endpoint(self, client):
        resp = client.get("/api/transactions/store-trend",
                          params={"store_id": "28", "start": "2026-01-01",
                                  "end": "2026-02-01", "grain": "daily"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["store_name"] == "Mosman"
        assert data["count"] > 0

    def test_plu_endpoint(self, client):
        resp = client.get("/api/transactions/plu/4322",
                          params={"start": "2025-07-01", "end": "2026-03-01"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["plu_item_id"] == "4322"
        assert data["total_revenue"] > 0

    def test_freeform_query_endpoint(self, client):
        resp = client.post("/api/transactions/query",
                           json={"sql": "SELECT COUNT(*) AS n FROM transactions WHERE fiscal_year = 'FY26'",
                                 "limit": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"][0]["n"] > 90_000_000

    def test_freeform_rejects_ddl(self, client):
        resp = client.post("/api/transactions/query",
                           json={"sql": "DROP TABLE transactions"})
        assert resp.status_code == 400

    def test_invalid_grain_rejected(self, client):
        resp = client.get("/api/transactions/store-trend",
                          params={"store_id": "28", "start": "2026-01-01",
                                  "end": "2026-02-01", "grain": "hourly"})
        assert resp.status_code == 400
