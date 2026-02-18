"""Tests for Out-of-Stock (zero-sales detection) queries."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from transaction_layer import TransactionStore
from transaction_queries import run_query, QUERIES

# FY26 Q2 window — baseline looks back 90 days into FY26 Q1
START = "2026-01-01"
END = "2026-01-15"
STORE_ID = "28"


@pytest.fixture(scope="module")
def ts():
    return TransactionStore()


# ---------------------------------------------------------------------------
# QUERY CATALOG REGISTRATION
# ---------------------------------------------------------------------------

class TestOOSCatalog:
    @pytest.mark.parametrize("name", [
        "oos_by_department",
        "oos_by_major_group",
        "oos_by_minor_group",
        "oos_summary",
        "oos_top_products",
    ])
    def test_query_registered(self, name):
        assert name in QUERIES, "Query '{}' not in QUERIES dict".format(name)

    @pytest.mark.parametrize("name", [
        "oos_by_department",
        "oos_by_major_group",
        "oos_by_minor_group",
        "oos_summary",
        "oos_top_products",
    ])
    def test_query_has_description(self, name):
        assert "description" in QUERIES[name]
        assert len(QUERIES[name]["description"]) > 10


# ---------------------------------------------------------------------------
# OOS BY DEPARTMENT
# ---------------------------------------------------------------------------

class TestOOSByDepartment:
    def test_returns_results(self, ts):
        rows = run_query(ts, "oos_by_department",
                         start=START, end=END, store_id=STORE_ID)
        assert len(rows) > 0, "oos_by_department returned no rows"

    def test_has_required_columns(self, ts):
        rows = run_query(ts, "oos_by_department",
                         start=START, end=END, store_id=STORE_ID)
        row = rows[0]
        for col in ("label", "code", "cal_date", "fiscal_week",
                     "fiscal_month", "month_name",
                     "missed_revenue", "oos_incidents",
                     "affected_products"):
            assert col in row, "Missing column: {}".format(col)

    def test_missed_revenue_positive(self, ts):
        rows = run_query(ts, "oos_by_department",
                         start=START, end=END, store_id=STORE_ID)
        total = sum(r["missed_revenue"] for r in rows)
        assert total > 0, "Total missed revenue should be positive"


# ---------------------------------------------------------------------------
# OOS BY MAJOR GROUP
# ---------------------------------------------------------------------------

class TestOOSByMajorGroup:
    def test_returns_results_with_dept(self, ts):
        # First get a valid department code
        dept_rows = run_query(ts, "oos_by_department",
                              start=START, end=END, store_id=STORE_ID)
        dept_code = dept_rows[0]["code"]
        rows = run_query(ts, "oos_by_major_group",
                         start=START, end=END, store_id=STORE_ID,
                         dept_code=dept_code)
        assert len(rows) > 0, "oos_by_major_group returned no rows"

    def test_has_label_and_revenue(self, ts):
        dept_rows = run_query(ts, "oos_by_department",
                              start=START, end=END, store_id=STORE_ID)
        dept_code = dept_rows[0]["code"]
        rows = run_query(ts, "oos_by_major_group",
                         start=START, end=END, store_id=STORE_ID,
                         dept_code=dept_code)
        assert "label" in rows[0]
        assert "missed_revenue" in rows[0]
        assert rows[0]["missed_revenue"] > 0


# ---------------------------------------------------------------------------
# OOS BY MINOR GROUP
# ---------------------------------------------------------------------------

class TestOOSByMinorGroup:
    def test_returns_results(self, ts):
        # Get a dept code
        dept_rows = run_query(ts, "oos_by_department",
                              start=START, end=END, store_id=STORE_ID)
        dept_code = dept_rows[0]["code"]
        # Get a major group code
        major_rows = run_query(ts, "oos_by_major_group",
                               start=START, end=END, store_id=STORE_ID,
                               dept_code=dept_code)
        major_code = major_rows[0]["code"]
        rows = run_query(ts, "oos_by_minor_group",
                         start=START, end=END, store_id=STORE_ID,
                         dept_code=dept_code, major_code=major_code)
        assert len(rows) > 0, "oos_by_minor_group returned no rows"

    def test_has_label_column(self, ts):
        dept_rows = run_query(ts, "oos_by_department",
                              start=START, end=END, store_id=STORE_ID)
        dept_code = dept_rows[0]["code"]
        major_rows = run_query(ts, "oos_by_major_group",
                               start=START, end=END, store_id=STORE_ID,
                               dept_code=dept_code)
        major_code = major_rows[0]["code"]
        rows = run_query(ts, "oos_by_minor_group",
                         start=START, end=END, store_id=STORE_ID,
                         dept_code=dept_code, major_code=major_code)
        assert "label" in rows[0]


# ---------------------------------------------------------------------------
# OOS SUMMARY
# ---------------------------------------------------------------------------

class TestOOSSummary:
    def test_returns_single_row(self, ts):
        rows = run_query(ts, "oos_summary",
                         start=START, end=END, store_id=STORE_ID)
        assert len(rows) == 1, "oos_summary should return exactly 1 row"

    def test_has_required_columns(self, ts):
        rows = run_query(ts, "oos_summary",
                         start=START, end=END, store_id=STORE_ID)
        row = rows[0]
        for col in ("oos_incidents", "affected_products",
                     "total_missed_revenue", "active_products",
                     "analysis_days"):
            assert col in row, "Missing column: {}".format(col)

    def test_values_non_negative(self, ts):
        rows = run_query(ts, "oos_summary",
                         start=START, end=END, store_id=STORE_ID)
        row = rows[0]
        assert row["total_missed_revenue"] >= 0
        assert row["active_products"] > 0
        assert row["analysis_days"] > 0


# ---------------------------------------------------------------------------
# OOS TOP PRODUCTS
# ---------------------------------------------------------------------------

class TestOOSTopProducts:
    def test_returns_results(self, ts):
        rows = run_query(ts, "oos_top_products",
                         start=START, end=END, store_id=STORE_ID,
                         limit=10)
        assert len(rows) > 0, "oos_top_products returned no rows"

    def test_respects_limit(self, ts):
        rows = run_query(ts, "oos_top_products",
                         start=START, end=END, store_id=STORE_ID,
                         limit=5)
        assert len(rows) <= 5, "Should respect limit=5"

    def test_has_required_columns(self, ts):
        rows = run_query(ts, "oos_top_products",
                         start=START, end=END, store_id=STORE_ID,
                         limit=5)
        row = rows[0]
        for col in ("PLUItem_ID", "product_name", "department",
                     "category", "oos_days", "total_days",
                     "missed_revenue", "peak_daily_missed"):
            assert col in row, "Missing column: {}".format(col)

    def test_oos_days_within_total(self, ts):
        rows = run_query(ts, "oos_top_products",
                         start=START, end=END, store_id=STORE_ID,
                         limit=10)
        for r in rows:
            assert r["oos_days"] <= r["total_days"], \
                "OOS days should not exceed total days"


# ---------------------------------------------------------------------------
# STORE FILTER
# ---------------------------------------------------------------------------

class TestOOSStoreFilter:
    def test_single_store_returns_results(self, ts):
        rows = run_query(ts, "oos_summary",
                         start=START, end=END, store_id=STORE_ID)
        assert rows[0]["oos_incidents"] > 0

    def test_single_store_less_than_all(self, ts):
        single = run_query(ts, "oos_summary",
                           start=START, end=END, store_id=STORE_ID)
        all_stores = run_query(ts, "oos_summary",
                               start=START, end=END)
        assert (single[0]["oos_incidents"]
                <= all_stores[0]["oos_incidents"]), \
            "Single store should have fewer incidents than all stores"
