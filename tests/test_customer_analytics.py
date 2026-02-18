"""Tests for Customer Analytics — 8 new transaction queries and dashboard imports."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from transaction_layer import TransactionStore
from transaction_queries import run_query, QUERIES

# Use a wide date range that covers FY25+FY26 for meaningful loyalty data
START = "2024-07-01"
END = "2026-03-01"


@pytest.fixture(scope="module")
def ts():
    return TransactionStore()


# ---------------------------------------------------------------------------
# RFM SEGMENTATION
# ---------------------------------------------------------------------------

class TestRFMSegments:
    def test_returns_results(self, ts):
        rows = run_query(ts, "customer_rfm_segments", start=START, end=END)
        assert len(rows) > 0, "RFM query returned no rows"

    def test_has_required_columns(self, ts):
        rows = run_query(ts, "customer_rfm_segments", start=START, end=END)
        row = rows[0]
        for col in ("CustomerCode", "recency_days", "frequency",
                     "monetary", "stores_visited", "segment"):
            assert col in row, f"Missing column: {col}"

    def test_segments_are_valid(self, ts):
        rows = run_query(ts, "customer_rfm_segments", start=START, end=END)
        valid = {"Champion", "High-Value", "Regular", "Occasional", "Lapsed"}
        segments = {r["segment"] for r in rows}
        assert segments.issubset(valid), f"Unexpected segments: {segments - valid}"

    def test_monetary_positive(self, ts):
        rows = run_query(ts, "customer_rfm_segments", start=START, end=END)
        # Top row (ordered by monetary DESC) should be positive
        assert rows[0]["monetary"] > 0


# ---------------------------------------------------------------------------
# COHORT RETENTION
# ---------------------------------------------------------------------------

class TestCohortRetention:
    def test_returns_results(self, ts):
        rows = run_query(ts, "customer_cohort_retention",
                         start=START, end=END)
        assert len(rows) > 0, "Cohort query returned no rows"

    def test_has_required_columns(self, ts):
        rows = run_query(ts, "customer_cohort_retention",
                         start=START, end=END)
        row = rows[0]
        for col in ("cohort_month", "months_since", "active_customers"):
            assert col in row, f"Missing column: {col}"

    def test_months_since_non_negative(self, ts):
        rows = run_query(ts, "customer_cohort_retention",
                         start=START, end=END)
        for r in rows:
            assert r["months_since"] >= 0, f"Negative months_since: {r}"


# ---------------------------------------------------------------------------
# SEGMENT BASKETS
# ---------------------------------------------------------------------------

class TestSegmentBaskets:
    def test_returns_results(self, ts):
        rows = run_query(ts, "customer_segment_baskets", start=START, end=END)
        assert len(rows) > 0

    def test_has_avg_basket_value(self, ts):
        rows = run_query(ts, "customer_segment_baskets", start=START, end=END)
        for r in rows:
            assert "avg_basket_value" in r
            assert r["avg_basket_value"] > 0


# ---------------------------------------------------------------------------
# CHANNEL SUMMARY (store-level)
# ---------------------------------------------------------------------------

class TestChannelSummary:
    def test_returns_results(self, ts):
        rows = run_query(ts, "customer_channel_summary", start=START, end=END)
        assert len(rows) > 0

    def test_has_store_and_revenue(self, ts):
        rows = run_query(ts, "customer_channel_summary", start=START, end=END)
        row = rows[0]
        assert "Store_ID" in row
        assert "revenue" in row
        assert row["revenue"] > 0

    def test_multiple_stores(self, ts):
        rows = run_query(ts, "customer_channel_summary", start=START, end=END)
        assert len(rows) >= 30, "Expected at least 30 stores"


# ---------------------------------------------------------------------------
# CHANNEL CROSSOVER (store loyalty)
# ---------------------------------------------------------------------------

class TestChannelCrossover:
    def test_returns_results(self, ts):
        rows = run_query(ts, "customer_channel_crossover", start=START, end=END)
        assert len(rows) > 0

    def test_valid_store_loyalty_values(self, ts):
        rows = run_query(ts, "customer_channel_crossover", start=START, end=END)
        valid = {"Single Store", "2-3 Stores", "4+ Stores"}
        values = {r["store_loyalty"] for r in rows}
        assert values.issubset(valid), f"Unexpected values: {values - valid}"

    def test_spend_positive(self, ts):
        rows = run_query(ts, "customer_channel_crossover", start=START, end=END)
        for r in rows:
            assert r["total_spend"] > 0


# ---------------------------------------------------------------------------
# FREQUENCY DISTRIBUTION
# ---------------------------------------------------------------------------

class TestFrequencyDistribution:
    def test_returns_buckets(self, ts):
        rows = run_query(ts, "customer_frequency_distribution",
                         start=START, end=END)
        assert len(rows) > 0

    def test_valid_bucket_names(self, ts):
        rows = run_query(ts, "customer_frequency_distribution",
                         start=START, end=END)
        valid = {"1 visit", "2-3 visits", "4-6 visits",
                 "7-12 visits", "13-24 visits", "25+ visits"}
        buckets = {r["frequency_bucket"] for r in rows}
        assert buckets.issubset(valid), f"Unexpected buckets: {buckets - valid}"

    def test_customer_counts_positive(self, ts):
        rows = run_query(ts, "customer_frequency_distribution",
                         start=START, end=END)
        for r in rows:
            assert r["customer_count"] > 0


# ---------------------------------------------------------------------------
# LTV TIERS
# ---------------------------------------------------------------------------

class TestLTVTiers:
    def test_returns_results(self, ts):
        rows = run_query(ts, "customer_ltv_tiers", start=START, end=END)
        assert len(rows) > 0

    def test_valid_tier_names(self, ts):
        rows = run_query(ts, "customer_ltv_tiers", start=START, end=END)
        valid = {"Premium ($10K+)", "High ($5K-$10K)", "Medium ($2K-$5K)",
                 "Low ($500-$2K)", "Minimal (<$500)"}
        tiers = {r["ltv_tier"] for r in rows}
        assert tiers.issubset(valid), f"Unexpected tiers: {tiers - valid}"

    def test_projected_annual_positive(self, ts):
        rows = run_query(ts, "customer_ltv_tiers", start=START, end=END)
        for r in rows:
            assert r["projected_annual"] > 0


# ---------------------------------------------------------------------------
# TOP DEPARTMENTS
# ---------------------------------------------------------------------------

class TestTopDepartments:
    def test_returns_departments(self, ts):
        rows = run_query(ts, "customer_top_departments", start=START, end=END)
        assert len(rows) > 0

    def test_has_department_column(self, ts):
        rows = run_query(ts, "customer_top_departments", start=START, end=END)
        assert "Department" in rows[0]

    def test_revenue_positive(self, ts):
        rows = run_query(ts, "customer_top_departments", start=START, end=END)
        for r in rows:
            assert r["total_revenue"] > 0


# ---------------------------------------------------------------------------
# PRODUCT HIERARCHY BREAKDOWN (loyalty)
# ---------------------------------------------------------------------------

class TestCustomerByDepartment:
    def test_returns_departments(self, ts):
        rows = run_query(ts, "customer_by_department", start=START, end=END)
        assert len(rows) > 0

    def test_has_required_columns(self, ts):
        rows = run_query(ts, "customer_by_department", start=START, end=END)
        for col in ("Department", "customers", "revenue", "transactions"):
            assert col in rows[0], "Missing column: {}".format(col)

    def test_revenue_positive(self, ts):
        rows = run_query(ts, "customer_by_department", start=START, end=END)
        assert all(r["revenue"] > 0 for r in rows)


class TestCustomerByMajorGroup:
    def test_returns_categories(self, ts):
        # Get first department code
        depts = run_query(ts, "customer_by_department", start=START, end=END)
        assert len(depts) > 0
        # Need the dept code — query customer_top_departments for codes
        dept_data = run_query(ts, "department_revenue", start=START, end=END)
        dept_code = dept_data[0]["DepartmentCode"]
        rows = run_query(ts, "customer_by_major_group",
                         dept_code=dept_code, start=START, end=END)
        assert len(rows) > 0
        assert "Category" in rows[0]


class TestCustomerByMinorGroup:
    def test_returns_subcategories(self, ts):
        dept_data = run_query(ts, "department_revenue", start=START, end=END)
        dept_code = dept_data[0]["DepartmentCode"]
        major_data = run_query(ts, "major_group_revenue",
                               dept_code=dept_code, start=START, end=END)
        major_code = major_data[0]["MajorGroupCode"]
        rows = run_query(ts, "customer_by_minor_group",
                         dept_code=dept_code, major_code=major_code,
                         start=START, end=END)
        assert len(rows) > 0
        assert "Subcategory" in rows[0]


class TestChannelByDepartment:
    def test_returns_results(self, ts):
        rows = run_query(ts, "channel_by_department", start=START, end=END)
        assert len(rows) > 0

    def test_has_loyalty_columns(self, ts):
        rows = run_query(ts, "channel_by_department", start=START, end=END)
        for col in ("Department", "revenue", "loyalty_customers",
                     "loyalty_revenue"):
            assert col in rows[0], "Missing column: {}".format(col)


# ---------------------------------------------------------------------------
# EXISTING CUSTOMER QUERIES (regression)
# ---------------------------------------------------------------------------

class TestExistingCustomerQueries:
    def test_top_customers_by_spend(self, ts):
        rows = run_query(ts, "top_customers_by_spend",
                         start=START, end=END, limit=10)
        assert len(rows) == 10
        assert rows[0]["total_spend"] > rows[-1]["total_spend"]

    def test_basket_size_distribution(self, ts):
        rows = run_query(ts, "basket_size_distribution",
                         store_id="28", start=START, end=END)
        assert len(rows) > 0
        assert "basket_size" in rows[0]

    def test_avg_basket_by_store(self, ts):
        rows = run_query(ts, "avg_basket_by_store",
                         start=START, end=END)
        assert len(rows) >= 30


# ---------------------------------------------------------------------------
# QUERY CATALOG REGISTRATION
# ---------------------------------------------------------------------------

class TestQueryCatalog:
    """Verify all customer queries are properly registered."""

    @pytest.mark.parametrize("name", [
        "customer_rfm_segments",
        "customer_cohort_retention",
        "customer_segment_baskets",
        "customer_channel_summary",
        "customer_channel_crossover",
        "customer_frequency_distribution",
        "customer_ltv_tiers",
        "customer_top_departments",
        "customer_by_department",
        "customer_by_major_group",
        "customer_by_minor_group",
        "channel_by_department",
        "channel_by_major_group",
        "channel_by_minor_group",
    ])
    def test_query_registered(self, name):
        assert name in QUERIES, f"Query '{name}' not in QUERIES dict"

    @pytest.mark.parametrize("name", [
        "customer_rfm_segments",
        "customer_cohort_retention",
        "customer_segment_baskets",
        "customer_channel_summary",
        "customer_channel_crossover",
        "customer_frequency_distribution",
        "customer_ltv_tiers",
        "customer_top_departments",
        "customer_by_department",
        "customer_by_major_group",
        "customer_by_minor_group",
        "channel_by_department",
        "channel_by_major_group",
        "channel_by_minor_group",
    ])
    def test_query_has_description(self, name):
        assert "description" in QUERIES[name]
        assert len(QUERIES[name]["description"]) > 10
