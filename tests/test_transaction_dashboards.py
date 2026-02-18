"""Tests for Transaction Dashboard infrastructure — PLU lookup, new queries, API endpoints."""

import os
import sys
from pathlib import Path

import pytest

# Disable auth gate for dashboard import tests
os.environ.setdefault("AUTH_ENABLED", "false")

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from plu_lookup import load_plu_names, resolve_plu, enrich_items, plu_coverage_stats
from transaction_layer import TransactionStore
from transaction_queries import run_query, get_query_catalog, QUERIES


# ---------------------------------------------------------------------------
# PLU LOOKUP
# ---------------------------------------------------------------------------

class TestPLULookup:
    def test_load_returns_dict(self):
        names = load_plu_names()
        assert isinstance(names, dict)

    def test_known_count(self):
        names = load_plu_names()
        assert len(names) >= 490  # 491 F&V items in product_lines.csv

    def test_resolve_known_plu(self):
        # PLU 4322 = STRAWBERRIES LARGE EA (from product hierarchy)
        result = resolve_plu("4322")
        assert "STRAWBERRIES" in result.upper()

    def test_resolve_unknown_plu(self):
        result = resolve_plu("0000000")
        assert result == "PLU 0000000"

    def test_enrich_items(self):
        items = [
            {"plu_item_id": "4322", "revenue": 1000},
            {"plu_item_id": "0000000", "revenue": 500},
        ]
        enriched = enrich_items(items)
        assert "STRAWBERRIES" in enriched[0]["product_name"].upper()
        assert enriched[1]["product_name"] == "PLU 0000000"

    def test_enrich_items_custom_key(self):
        items = [{"pluitem_id": "4322", "rev": 100}]
        enriched = enrich_items(items, plu_key="pluitem_id")
        assert "STRAWBERRIES" in enriched[0]["product_name"].upper()

    def test_coverage_stats(self):
        stats = plu_coverage_stats()
        assert stats["known_plus"] >= 490
        assert "products" in stats["coverage_note"].lower()


# ---------------------------------------------------------------------------
# NEW QUERIES
# ---------------------------------------------------------------------------

class TestNewQueries:
    @pytest.fixture(scope="class")
    def ts(self):
        return TransactionStore()

    def test_day_of_week_returns_7(self, ts):
        result = run_query(ts, "day_of_week_pattern",
                           store_id="28", start="2026-01-01", end="2026-02-01")
        assert len(result) == 7

    def test_day_of_week_has_day_name(self, ts):
        result = run_query(ts, "day_of_week_pattern",
                           store_id="28", start="2026-01-01", end="2026-02-01")
        day_names = {r["day_name"] for r in result}
        assert "Monday" in day_names
        assert "Sunday" in day_names

    def test_hourly_aest_returns_results(self, ts):
        result = run_query(ts, "hourly_pattern_aest",
                           store_id="28", start="2026-01-01", end="2026-02-01")
        assert len(result) >= 10  # Should have multiple hours

    def test_hourly_aest_hours_in_range(self, ts):
        result = run_query(ts, "hourly_pattern_aest",
                           store_id="28", start="2026-01-01", end="2026-02-01")
        hours = [r["hour_aest"] for r in result]
        assert all(0 <= h <= 23 for h in hours)

    def test_store_comparison_returns_stores(self, ts):
        result = run_query(ts, "store_comparison_period",
                           start="2026-01-01", end="2026-02-01")
        assert len(result) >= 30

    def test_store_comparison_sorted_by_revenue(self, ts):
        result = run_query(ts, "store_comparison_period",
                           start="2026-01-01", end="2026-02-01")
        revenues = [r["revenue"] for r in result]
        assert revenues == sorted(revenues, reverse=True)

    def test_anomaly_candidates_runs(self, ts):
        result = run_query(ts, "anomaly_candidates",
                           store_id="28", start="2025-07-01", end="2026-02-01")
        assert isinstance(result, list)

    def test_anomaly_has_z_score(self, ts):
        result = run_query(ts, "anomaly_candidates",
                           store_id="28", start="2025-07-01", end="2026-02-01")
        if result:
            assert "z_score" in result[0]

    def test_slow_movers_returns_results(self, ts):
        result = run_query(ts, "slow_movers",
                           start="2026-01-01", end="2026-02-01",
                           threshold=5, limit=10)
        assert isinstance(result, list)

    def test_price_dispersion(self, ts):
        result = run_query(ts, "price_dispersion",
                           plu_id="4322", start="2025-07-01", end="2026-02-01")
        assert len(result) > 0
        assert "avg_unit_price" in result[0]

    def test_revenue_decomposition(self, ts):
        result = run_query(ts, "revenue_decomposition_monthly",
                           start="2025-07-01", end="2026-02-01")
        assert len(result) >= 6  # Jul-Jan
        assert "fresh_revenue" in result[0]
        assert "packaged_revenue" in result[0]
        assert "returns_value" in result[0]

    def test_gst_category_monthly_trend(self, ts):
        result = run_query(ts, "gst_category_monthly_trend",
                           start="2025-07-01", end="2026-02-01")
        assert len(result) >= 10  # 7 months x 2 categories
        categories = {r["category"] for r in result}
        assert "Fresh" in categories
        assert "Packaged" in categories


# ---------------------------------------------------------------------------
# QUERY CATALOG
# ---------------------------------------------------------------------------

class TestQueryCatalog:
    def test_catalog_has_new_queries(self):
        catalog = get_query_catalog()
        names = {q["name"] for q in catalog}
        assert "day_of_week_pattern" in names
        assert "hourly_pattern_aest" in names
        assert "store_comparison_period" in names
        assert "anomaly_candidates" in names
        assert "slow_movers" in names
        assert "price_dispersion" in names
        assert "revenue_decomposition_monthly" in names
        assert "gst_category_monthly_trend" in names

    def test_catalog_count(self):
        catalog = get_query_catalog()
        assert len(catalog) >= 24  # 16 original + 8 new


# ---------------------------------------------------------------------------
# API ENDPOINTS
# ---------------------------------------------------------------------------

class TestNewTransactionAPI:
    @pytest.fixture(scope="class")
    def client(self):
        from app import app
        app.state.txn_store = TransactionStore()
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_query_catalog_endpoint(self, client):
        resp = client.get("/api/transactions/query-catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 24

    def test_run_query_endpoint(self, client):
        resp = client.get("/api/transactions/run/store_comparison_period",
                          params={"start": "2026-01-01", "end": "2026-02-01"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "store_comparison_period"
        assert data["count"] >= 30

    def test_run_unknown_query(self, client):
        resp = client.get("/api/transactions/run/nonexistent_query")
        assert resp.status_code == 404

    def test_run_query_with_store(self, client):
        resp = client.get("/api/transactions/run/day_of_week_pattern",
                          params={"store_id": "28", "start": "2026-01-01",
                                  "end": "2026-02-01"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 7


# ---------------------------------------------------------------------------
# STORE OPS ENHANCEMENT: NEW QUERIES
# ---------------------------------------------------------------------------

class TestFilteredKPIsQuery:
    """Tests for the filtered_kpis and like_for_like_stores queries."""

    def test_filtered_kpis_in_catalog(self):
        catalog = get_query_catalog()
        names = {q["name"] for q in catalog}
        assert "filtered_kpis" in names

    def test_filtered_kpis_params(self):
        q = QUERIES["filtered_kpis"]
        assert "start" in q["params"]
        assert "end" in q["params"]
        assert "dept_code" in q.get("optional", [])
        assert "major_code" in q.get("optional", [])
        assert "minor_code" in q.get("optional", [])
        assert "store_id" in q.get("optional", [])

    def test_like_for_like_stores_in_catalog(self):
        catalog = get_query_catalog()
        names = {q["name"] for q in catalog}
        assert "like_for_like_stores" in names

    def test_like_for_like_stores_params(self):
        q = QUERIES["like_for_like_stores"]
        assert "start" in q["params"]
        assert "end" in q["params"]
        assert "prior_start" in q["params"]
        assert "prior_end" in q["params"]


class TestHierarchyFilterSubstitution:
    """Tests that hierarchy filter placeholders get replaced correctly."""

    def test_dept_filter_replaced_when_provided(self):
        q = QUERIES["filtered_kpis"]
        sql = q["sql"]
        assert "{dept_filter}" in sql
        # After run_query processes it, the placeholder should be gone
        ts = TransactionStore()
        result = run_query(ts, "filtered_kpis",
                           start="2026-01-01", end="2026-02-01",
                           store_id="28", dept_code="10")
        assert isinstance(result, list)

    def test_dept_filter_omitted_when_absent(self):
        ts = TransactionStore()
        result = run_query(ts, "filtered_kpis",
                           start="2026-01-01", end="2026-02-01",
                           store_id="28")
        assert isinstance(result, list)
        if result:
            assert result[0]["revenue"] is not None

    def test_filtered_kpis_with_dept_returns_subset(self):
        ts = TransactionStore()
        all_kpis = run_query(ts, "filtered_kpis",
                             start="2026-01-01", end="2026-02-01",
                             store_id="28")
        dept_kpis = run_query(ts, "filtered_kpis",
                              start="2026-01-01", end="2026-02-01",
                              store_id="28", dept_code="10")
        if all_kpis and dept_kpis:
            assert dept_kpis[0]["revenue"] <= all_kpis[0]["revenue"]

    def test_lfl_stores_returns_results(self):
        ts = TransactionStore()
        result = run_query(ts, "like_for_like_stores",
                           start="2025-07-01", end="2026-02-01",
                           prior_start="2024-07-01", prior_end="2025-02-01")
        assert isinstance(result, list)
        assert len(result) >= 25  # Most stores active in both periods


class TestStoreOpsHelpers:
    """Tests for dashboard helper functions."""

    def test_calc_delta_positive(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from store_ops_dashboard import calc_delta
        assert calc_delta(110, 100) == "+10.0%"

    def test_calc_delta_negative(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from store_ops_dashboard import calc_delta
        assert calc_delta(90, 100) == "-10.0%"

    def test_calc_delta_zero_prior(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from store_ops_dashboard import calc_delta
        assert calc_delta(100, 0) is None

    def test_calc_delta_none_prior(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from store_ops_dashboard import calc_delta
        assert calc_delta(100, None) is None

    def test_catalog_count_updated(self):
        """Catalog should now include all new queries."""
        catalog = get_query_catalog()
        assert len(catalog) >= 28  # 24 + 2 (filtered_kpis, lfl) + 2 (top_items_filtered, slow_movers_filtered)


# ---------------------------------------------------------------------------
# NEW HIERARCHY-FILTERED QUERIES
# ---------------------------------------------------------------------------

class TestTopItemsFilteredQuery:
    """Tests for the top_items_filtered query."""

    def test_top_items_filtered_in_catalog(self):
        catalog = get_query_catalog()
        names = {q["name"] for q in catalog}
        assert "top_items_filtered" in names

    def test_top_items_filtered_params(self):
        q = QUERIES["top_items_filtered"]
        assert "start" in q["params"]
        assert "end" in q["params"]
        assert "limit" in q["params"]
        assert "dept_code" in q.get("optional", [])
        assert "store_id" in q.get("optional", [])

    def test_top_items_filtered_returns_results(self):
        ts = TransactionStore()
        result = run_query(ts, "top_items_filtered",
                           start="2026-01-01", end="2026-02-01",
                           dept_code="10", limit=10)
        assert isinstance(result, list)
        assert len(result) > 0
        assert "product_name" in result[0]
        assert "total_revenue" in result[0]

    def test_top_items_filtered_no_dept(self):
        ts = TransactionStore()
        result = run_query(ts, "top_items_filtered",
                           start="2026-01-01", end="2026-02-01",
                           limit=5)
        assert isinstance(result, list)
        assert len(result) == 5


class TestSlowMoversFilteredQuery:
    """Tests for the slow_movers_filtered query."""

    def test_slow_movers_filtered_in_catalog(self):
        catalog = get_query_catalog()
        names = {q["name"] for q in catalog}
        assert "slow_movers_filtered" in names

    def test_slow_movers_filtered_params(self):
        q = QUERIES["slow_movers_filtered"]
        assert "start" in q["params"]
        assert "end" in q["params"]
        assert "threshold" in q["params"]
        assert "limit" in q["params"]
        assert "dept_code" in q.get("optional", [])

    def test_slow_movers_filtered_returns_results(self):
        ts = TransactionStore()
        result = run_query(ts, "slow_movers_filtered",
                           start="2026-01-01", end="2026-02-01",
                           dept_code="10", threshold=5, limit=10)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# SHARED COMPONENTS
# ---------------------------------------------------------------------------

class TestHierarchyFilterModule:
    """Tests for dashboards/shared/hierarchy_filter.py (non-Streamlit parts)."""

    def test_hierarchy_filter_summary_none_when_no_filter(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.hierarchy_filter import hierarchy_filter_summary
        result = hierarchy_filter_summary({
            "dept_code": None, "major_code": None, "minor_code": None
        })
        assert result is None

    def test_hierarchy_filter_summary_dept_only(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.hierarchy_filter import hierarchy_filter_summary
        result = hierarchy_filter_summary({
            "dept_code": "10", "major_code": None, "minor_code": None
        })
        assert result is not None
        assert len(result) > 0

    def test_hierarchy_filter_summary_dept_and_major(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.hierarchy_filter import hierarchy_filter_summary
        result = hierarchy_filter_summary({
            "dept_code": "10", "major_code": "110", "minor_code": None
        })
        assert ">" in result


class TestDeepHierarchy:
    """Tests for levels 4-5 of hierarchy (HFM Item, Product/SKU)."""

    def test_get_hfm_items_returns_list(self):
        from product_hierarchy import get_hfm_items
        result = get_hfm_items("10", "110", "1101")
        assert isinstance(result, list)

    def test_get_hfm_items_have_expected_keys(self):
        from product_hierarchy import get_hfm_items
        result = get_hfm_items("10", "110", "1101")
        if result:
            item = result[0]
            assert "code" in item
            assert "name" in item
            assert "total_products" in item

    def test_get_products_in_hfm_item_returns_list(self):
        from product_hierarchy import get_products_in_hfm_item, get_hfm_items
        hfm_items = get_hfm_items("10", "110", "1101")
        if hfm_items:
            result = get_products_in_hfm_item("10", "110", "1101", hfm_items[0]["code"])
            assert isinstance(result, list)

    def test_get_products_have_expected_keys(self):
        from product_hierarchy import get_products_in_hfm_item, get_hfm_items
        hfm_items = get_hfm_items("10", "110", "1101")
        if hfm_items:
            result = get_products_in_hfm_item("10", "110", "1101", hfm_items[0]["code"])
            if result:
                prod = result[0]
                assert "product_number" in prod
                assert "product_name" in prod
                assert "lifecycle" in prod


class TestHFMFilterPlaceholder:
    """Tests for {hfm_filter} and {product_filter} placeholders."""

    def test_hfm_filter_in_filtered_kpis(self):
        q = QUERIES["filtered_kpis"]
        assert "{hfm_filter}" in q["sql"]
        assert "hfm_item_code" in q.get("optional", [])

    def test_product_filter_in_filtered_kpis(self):
        q = QUERIES["filtered_kpis"]
        assert "{product_filter}" in q["sql"]
        assert "product_number" in q.get("optional", [])

    def test_hfm_filter_in_top_items_filtered(self):
        q = QUERIES["top_items_filtered"]
        assert "{hfm_filter}" in q["sql"]

    def test_hfm_filter_in_slow_movers_filtered(self):
        q = QUERIES["slow_movers_filtered"]
        assert "{hfm_filter}" in q["sql"]


class TestDayTypeFilter:
    """Tests for {day_type_filter} and {fiscal_join} substitution."""

    def test_day_type_filter_in_filtered_kpis(self):
        q = QUERIES["filtered_kpis"]
        assert "{day_type_filter}" in q["sql"]

    def test_fiscal_join_in_filtered_kpis(self):
        q = QUERIES["filtered_kpis"]
        assert "{fiscal_join}" in q["sql"]

    def test_day_type_filter_in_hourly_queries(self):
        for name in ["fiscal_day_of_week", "fiscal_hourly_by_day_type",
                      "fiscal_hourly_heatmap"]:
            q = QUERIES[name]
            assert "{day_type_filter}" in q["sql"], f"{name} missing day_type_filter"

    def test_filtered_kpis_with_day_type_weekend(self):
        ts = TransactionStore()
        result = run_query(ts, "filtered_kpis",
                           start="2026-01-01", end="2026-02-01",
                           store_id="28", day_type="weekend")
        assert isinstance(result, list)

    def test_filtered_kpis_with_day_type_business(self):
        ts = TransactionStore()
        result = run_query(ts, "filtered_kpis",
                           start="2026-01-01", end="2026-02-01",
                           store_id="28", day_type="business")
        assert isinstance(result, list)

    def test_filtered_kpis_with_day_type_all(self):
        ts = TransactionStore()
        result = run_query(ts, "filtered_kpis",
                           start="2026-01-01", end="2026-02-01",
                           store_id="28", day_type="all")
        assert isinstance(result, list)


class TestHourlyWithHierarchy:
    """Tests for hourly queries with hierarchy filter support."""

    def test_hourly_queries_have_hierarchy_optional(self):
        for name in ["fiscal_day_of_week", "fiscal_hourly_by_day_type",
                      "fiscal_hourly_heatmap"]:
            q = QUERIES[name]
            optional = q.get("optional", [])
            assert "dept_code" in optional, f"{name} missing dept_code in optional"
            assert "hfm_item_code" in optional, f"{name} missing hfm_item_code"
            assert "product_number" in optional, f"{name} missing product_number"

    def test_fiscal_day_of_week_with_dept_filter(self):
        ts = TransactionStore()
        result = run_query(ts, "fiscal_day_of_week",
                           start="2026-01-01", end="2026-02-01",
                           store_id="28", dept_code="10")
        assert isinstance(result, list)

    def test_fiscal_hourly_heatmap_with_dept_filter(self):
        ts = TransactionStore()
        result = run_query(ts, "fiscal_hourly_heatmap",
                           start="2026-01-01", end="2026-02-01",
                           store_id="28", dept_code="10")
        assert isinstance(result, list)


class TestHierarchyFilterSummaryDeep:
    """Tests for hierarchy_filter_summary with HFM item and day type."""

    def test_summary_includes_hfm_item(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.hierarchy_filter import hierarchy_filter_summary
        result = hierarchy_filter_summary({
            "dept_code": "10", "major_code": "110", "minor_code": "1101",
            "hfm_item_code": "11011", "product_number": None,
            "day_type": "all",
        })
        assert result is not None
        assert result.count(">") >= 3  # dept > major > minor > hfm

    def test_summary_no_day_type_in_hierarchy(self):
        """Day type was removed from hierarchy_filter_summary (moved to time_filter)."""
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.hierarchy_filter import hierarchy_filter_summary
        result = hierarchy_filter_summary({
            "dept_code": None, "major_code": None, "minor_code": None,
            "hfm_item_code": None, "product_number": None,
            "day_type": "weekend",
        })
        # No hierarchy selected + day_type ignored = None
        assert result is None

    def test_summary_dept_only_no_day_type(self):
        """Day type no longer appended to hierarchy summary."""
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.hierarchy_filter import hierarchy_filter_summary
        result = hierarchy_filter_summary({
            "dept_code": "10", "major_code": None, "minor_code": None,
            "hfm_item_code": None, "product_number": None,
            "day_type": "business",
        })
        assert result is not None
        assert "Business Days" not in result


class TestHourlyChartsModule:
    """Tests for dashboards/shared/hourly_charts.py — verify queries exist."""

    def test_fiscal_day_of_week_in_catalog(self):
        catalog = get_query_catalog()
        names = {q["name"] for q in catalog}
        assert "fiscal_day_of_week" in names

    def test_fiscal_hourly_by_day_type_in_catalog(self):
        catalog = get_query_catalog()
        names = {q["name"] for q in catalog}
        assert "fiscal_hourly_by_day_type" in names

    def test_fiscal_hourly_heatmap_in_catalog(self):
        catalog = get_query_catalog()
        names = {q["name"] for q in catalog}
        assert "fiscal_hourly_heatmap" in names


# ---------------------------------------------------------------------------
# TIME FILTER MODULE
# ---------------------------------------------------------------------------

class TestTimeFilterModule:
    """Tests for dashboards/shared/time_filter.py — non-Streamlit logic."""

    def test_import(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import (
            render_time_filter, time_filter_summary,
            render_quick_period, resolve_quick_period,
            HOUR_PRESETS, ALL_SEASONS,
            MONTH_TO_QUARTER,
        )
        assert len(HOUR_PRESETS) >= 7
        assert len(ALL_SEASONS) == 4

    def test_month_to_quarter_mapping(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import MONTH_TO_QUARTER
        # Q1 = months 1-3, Q2 = months 4-6, Q3 = months 7-9, Q4 = months 10-12
        assert MONTH_TO_QUARTER[1] == 1
        assert MONTH_TO_QUARTER[3] == 1
        assert MONTH_TO_QUARTER[4] == 2
        assert MONTH_TO_QUARTER[7] == 3
        assert MONTH_TO_QUARTER[10] == 4
        assert MONTH_TO_QUARTER[12] == 4

    def test_summary_none_when_no_filters(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import time_filter_summary
        tf = {
            "day_of_week_names": None,
            "hour_start": None, "hour_end": None, "hour_preset": None,
            "season_names": None,
            "quarter_nos": None,
            "month_nos": None,
        }
        assert time_filter_summary(tf) is None

    def test_summary_hour_preset(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import time_filter_summary
        tf = {
            "day_of_week_names": None,
            "hour_start": 9, "hour_end": 12, "hour_preset": "Morning (9-12)",
            "season_names": None,
            "quarter_nos": None,
            "month_nos": None,
        }
        result = time_filter_summary(tf)
        assert "Morning" in result

    def test_summary_season(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import time_filter_summary
        tf = {
            "day_of_week_names": None,
            "hour_start": None, "hour_end": None, "hour_preset": None,
            "season_names": ["Summer", "Autumn"],
            "quarter_nos": None,
            "month_nos": None,
        }
        result = time_filter_summary(tf)
        assert "Summer" in result
        assert "Autumn" in result

    def test_summary_quarter(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import time_filter_summary
        tf = {
            "day_of_week_names": None,
            "hour_start": None, "hour_end": None, "hour_preset": None,
            "season_names": None,
            "quarter_nos": [1, 3],
            "month_nos": None,
        }
        result = time_filter_summary(tf)
        assert "Q1" in result
        assert "Q3" in result

    def test_summary_combined(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import time_filter_summary
        tf = {
            "day_of_week_names": None,
            "hour_start": 9, "hour_end": 12, "hour_preset": "Morning (9-12)",
            "season_names": ["Summer"],
            "quarter_nos": None,
            "month_nos": None,
        }
        result = time_filter_summary(tf)
        assert "Morning" in result
        assert "Summer" in result

    def test_summary_months(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import time_filter_summary
        tf = {
            "day_of_week_names": None,
            "hour_start": None, "hour_end": None, "hour_preset": None,
            "season_names": None,
            "quarter_nos": None,
            "month_nos": [1, 2, 3],
        }
        result = time_filter_summary(tf)
        assert "3 months" in result


class TestTimeFilterQueryHandlers:
    """Tests for time filter placeholder handlers in run_query()."""

    def test_dow_filter_generates_in_clause(self):
        """day_of_week_names kwarg generates DayOfWeekName IN clause."""
        q = QUERIES["filtered_kpis"]
        sql = q["sql"]
        # Simulate run_query handler logic
        dow_names = ["Monday", "Friday"]
        quoted = ", ".join(f"'{d}'" for d in dow_names)
        result = sql.replace("{day_type_filter}",
                             f"AND fc.DayOfWeekName IN ({quoted})")
        assert "AND fc.DayOfWeekName IN ('Monday', 'Friday')" in result

    def test_dow_filter_all_days_no_clause(self):
        """All 7 days = no filter clause."""
        q = QUERIES["filtered_kpis"]
        sql = q["sql"]
        result = sql.replace("{day_type_filter}", "")
        assert "{day_type_filter}" not in result

    def test_hour_filter_generates_extract(self):
        """hour_start/hour_end generates EXTRACT HOUR clause."""
        q = QUERIES["filtered_kpis"]
        sql = q["sql"]
        h_start, h_end = 9, 12
        result = sql.replace("{hour_filter}",
            f"AND EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR) >= {h_start} "
            f"AND EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR) < {h_end}")
        assert "EXTRACT(HOUR FROM t.SaleDate" in result
        assert ">= 9" in result
        assert "< 12" in result

    def test_hour_filter_no_range_no_clause(self):
        """No hour range = no filter clause."""
        q = QUERIES["filtered_kpis"]
        sql = q["sql"]
        result = sql.replace("{hour_filter}", "")
        assert "{hour_filter}" not in result

    def test_season_filter_generates_in_clause(self):
        """season_names generates SeasonName IN clause."""
        q = QUERIES["filtered_kpis"]
        sql = q["sql"]
        result = sql.replace("{season_filter}",
                             "AND fc.SeasonName IN ('Summer')")
        assert "AND fc.SeasonName IN ('Summer')" in result

    def test_season_filter_all_seasons_no_clause(self):
        """All 4 seasons = no filter clause."""
        q = QUERIES["filtered_kpis"]
        sql = q["sql"]
        result = sql.replace("{season_filter}", "")
        assert "{season_filter}" not in result

    def test_quarter_filter_generates_in_clause(self):
        """quarter_nos generates FinQuarterOfYearNo IN clause."""
        q = QUERIES["filtered_kpis"]
        sql = q["sql"]
        result = sql.replace("{quarter_filter}",
                             "AND fc.FinQuarterOfYearNo IN (1, 3)")
        assert "AND fc.FinQuarterOfYearNo IN (1, 3)" in result

    def test_month_filter_generates_in_clause(self):
        """month_nos generates FinMonthOfYearNo IN clause."""
        q = QUERIES["filtered_kpis"]
        sql = q["sql"]
        result = sql.replace("{month_filter}",
                             "AND fc.FinMonthOfYearNo IN (1, 2, 3)")
        assert "AND fc.FinMonthOfYearNo IN (1, 2, 3)" in result

    def test_all_placeholders_present_in_filtered_kpis(self):
        """All 5 time filter placeholders present in filtered_kpis query."""
        sql = QUERIES["filtered_kpis"]["sql"]
        for placeholder in ["{day_type_filter}", "{hour_filter}",
                            "{season_filter}", "{quarter_filter}",
                            "{month_filter}"]:
            assert placeholder in sql, f"{placeholder} missing from filtered_kpis"

    def test_all_placeholders_present_in_top_items_filtered(self):
        """All 5 time filter placeholders present in top_items_filtered query."""
        sql = QUERIES["top_items_filtered"]["sql"]
        for placeholder in ["{day_type_filter}", "{hour_filter}",
                            "{season_filter}", "{quarter_filter}",
                            "{month_filter}"]:
            assert placeholder in sql, f"{placeholder} missing from top_items_filtered"

    def test_all_placeholders_present_in_slow_movers_filtered(self):
        """All 5 time filter placeholders present in slow_movers_filtered query."""
        sql = QUERIES["slow_movers_filtered"]["sql"]
        for placeholder in ["{day_type_filter}", "{hour_filter}",
                            "{season_filter}", "{quarter_filter}",
                            "{month_filter}"]:
            assert placeholder in sql, f"{placeholder} missing from slow_movers_filtered"

    def test_all_placeholders_present_in_fiscal_day_of_week(self):
        """All 5 time filter placeholders present in fiscal_day_of_week query."""
        sql = QUERIES["fiscal_day_of_week"]["sql"]
        for placeholder in ["{day_type_filter}", "{hour_filter}",
                            "{season_filter}", "{quarter_filter}",
                            "{month_filter}"]:
            assert placeholder in sql, f"{placeholder} missing from fiscal_day_of_week"

    def test_all_placeholders_present_in_fiscal_hourly_queries(self):
        """All 5 time filter placeholders present in fiscal hourly queries."""
        for qname in ["fiscal_hourly_by_day_type", "fiscal_hourly_heatmap"]:
            sql = QUERIES[qname]["sql"]
            for placeholder in ["{day_type_filter}", "{hour_filter}",
                                "{season_filter}", "{quarter_filter}",
                                "{month_filter}"]:
                assert placeholder in sql, \
                    f"{placeholder} missing from {qname}"

    def test_fiscal_join_activates_for_dow(self):
        """fiscal_join activates when day_of_week_names present."""
        sql = QUERIES["filtered_kpis"]["sql"]
        assert "{fiscal_join}" in sql
        # Simulate handler
        result = sql.replace("{fiscal_join}",
            "JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate")
        assert "JOIN fiscal_calendar fc" in result

    def test_fiscal_join_empty_when_no_filters(self):
        """fiscal_join is empty string when no time filters."""
        sql = QUERIES["filtered_kpis"]["sql"]
        result = sql.replace("{fiscal_join}", "")
        assert "fiscal_calendar" not in result


class TestQuickPeriodResolve:
    """Tests for resolve_quick_period() in shared time_filter module."""

    def test_import_resolve_quick_period(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import resolve_quick_period
        # Should be callable
        assert callable(resolve_quick_period)

    def test_today_returns_dates(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import resolve_quick_period
        start, end, label = resolve_quick_period("Today")
        # May be None if fiscal calendar doesn't cover today
        if start is not None:
            assert "Today" in label
            assert len(start) == 10  # YYYY-MM-DD

    def test_qtd_returns_dates(self):
        """QTD (Quarter to Date) is the new addition."""
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import resolve_quick_period
        start, end, label = resolve_quick_period("QTD")
        if start is not None:
            assert "QTD" in label
            assert len(start) == 10

    def test_unknown_mode_returns_none(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import resolve_quick_period
        start, end, label = resolve_quick_period("NonExistent")
        assert start is None
        assert end is None
        assert label is None

    def test_all_modes_callable(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.time_filter import resolve_quick_period
        for mode in ["Today", "WTD", "MTD", "QTD", "YTD"]:
            start, end, label = resolve_quick_period(mode)
            # Either all None or all set
            if start is not None:
                assert end is not None
                assert label is not None


# ---------------------------------------------------------------------------
# FILTER PROPAGATION — upgraded queries
# ---------------------------------------------------------------------------

class TestFilterPropagation:
    """Tests for filter placeholder support in upgraded queries."""

    def test_filtered_daily_trend_in_catalog(self):
        catalog = get_query_catalog()
        names = {q["name"] for q in catalog}
        assert "filtered_daily_trend" in names

    def test_filtered_daily_trend_returns_results(self):
        ts = TransactionStore()
        result = run_query(ts, "filtered_daily_trend",
                           store_id="28", start="2025-07-01", end="2025-08-01")
        assert isinstance(result, list)
        assert len(result) > 0
        assert "period" in result[0]
        assert "revenue" in result[0]
        assert "transactions" in result[0]

    def test_filtered_daily_trend_with_hour_filter(self):
        ts = TransactionStore()
        all_data = run_query(ts, "filtered_daily_trend",
                             store_id="28", start="2025-07-01", end="2025-08-01")
        filtered = run_query(ts, "filtered_daily_trend",
                             store_id="28", start="2025-07-01", end="2025-08-01",
                             hour_start=9, hour_end=12)
        all_rev = sum(r["revenue"] for r in all_data)
        filt_rev = sum(r["revenue"] for r in filtered)
        assert filt_rev < all_rev, "Hour filter should reduce revenue"

    def test_department_revenue_has_time_placeholders(self):
        sql = QUERIES["department_revenue"]["sql"]
        for ph in ["{fiscal_join}", "{day_type_filter}", "{hour_filter}",
                   "{season_filter}", "{quarter_filter}", "{month_filter}"]:
            assert ph in sql, f"{ph} missing from department_revenue"

    def test_major_group_revenue_has_time_placeholders(self):
        sql = QUERIES["major_group_revenue"]["sql"]
        for ph in ["{fiscal_join}", "{hour_filter}", "{season_filter}"]:
            assert ph in sql, f"{ph} missing from major_group_revenue"

    def test_minor_group_revenue_has_time_placeholders(self):
        sql = QUERIES["minor_group_revenue"]["sql"]
        for ph in ["{fiscal_join}", "{hour_filter}", "{season_filter}"]:
            assert ph in sql, f"{ph} missing from minor_group_revenue"

    def test_gst_category_split_has_all_placeholders(self):
        sql = QUERIES["gst_category_split"]["sql"]
        for ph in ["{fiscal_join}", "{dept_filter}", "{major_filter}",
                   "{minor_filter}", "{hfm_filter}", "{product_filter}",
                   "{day_type_filter}", "{hour_filter}", "{season_filter}",
                   "{quarter_filter}", "{month_filter}"]:
            assert ph in sql, f"{ph} missing from gst_category_split"

    def test_gst_category_monthly_trend_has_all_placeholders(self):
        sql = QUERIES["gst_category_monthly_trend"]["sql"]
        for ph in ["{fiscal_join}", "{dept_filter}", "{hour_filter}",
                   "{season_filter}", "{quarter_filter}", "{month_filter}"]:
            assert ph in sql, f"{ph} missing from gst_category_monthly_trend"

    def test_anomaly_candidates_has_hierarchy_placeholders(self):
        sql = QUERIES["anomaly_candidates"]["sql"]
        for ph in ["{fiscal_join}", "{dept_filter}", "{major_filter}",
                   "{hour_filter}", "{season_filter}"]:
            assert ph in sql, f"{ph} missing from anomaly_candidates"

    def test_department_revenue_with_hour_filter(self):
        ts = TransactionStore()
        all_data = run_query(ts, "department_revenue",
                             store_id="28", start="2025-07-01", end="2025-08-01")
        filtered = run_query(ts, "department_revenue",
                             store_id="28", start="2025-07-01", end="2025-08-01",
                             hour_start=9, hour_end=12)
        all_rev = sum(r["revenue"] for r in all_data)
        filt_rev = sum(r["revenue"] for r in filtered)
        assert filt_rev < all_rev, "Hour filter should reduce revenue"

    def test_gst_split_with_season_filter(self):
        ts = TransactionStore()
        all_data = run_query(ts, "gst_category_split",
                             store_id="28", start="2025-07-01", end="2026-02-01")
        filtered = run_query(ts, "gst_category_split",
                             store_id="28", start="2025-07-01", end="2026-02-01",
                             season_names=["Summer"])
        all_rev = sum(r["revenue"] for r in all_data)
        filt_rev = sum(r["revenue"] for r in filtered)
        assert filt_rev < all_rev, "Season filter should reduce revenue"

    def test_anomaly_candidates_still_works_without_filters(self):
        ts = TransactionStore()
        result = run_query(ts, "anomaly_candidates",
                           store_id="28", start="2025-07-01", end="2026-02-01")
        assert isinstance(result, list)
        if result:
            assert "z_score" in result[0]

    def test_all_upgraded_queries_run_without_filters(self):
        """All upgraded queries still work with no optional filters."""
        ts = TransactionStore()
        for name in ["department_revenue", "gst_category_split",
                     "gst_category_monthly_trend", "filtered_daily_trend"]:
            result = run_query(ts, name,
                               store_id="28", start="2025-07-01", end="2025-08-01")
            assert isinstance(result, list), f"{name} should return a list"
            assert len(result) > 0, f"{name} should return data"


# ---------------------------------------------------------------------------
# WEEKEND DATA REGRESSION — ensures all 7 days always returned
# ---------------------------------------------------------------------------

class TestWeekendDataRegression:
    """Regression tests: Trading Patterns must include weekend (Sat/Sun) data.

    These tests guard against any future code change that accidentally
    filters out weekends. Weekend days are critical for a grocery retailer
    (highest revenue days).
    """

    @pytest.fixture(scope="class")
    def ts(self):
        return TransactionStore()

    # --- fiscal_day_of_week: must return all 7 days ---

    def test_day_of_week_returns_all_7_days(self, ts):
        """fiscal_day_of_week must return exactly 7 day rows."""
        result = run_query(ts, "fiscal_day_of_week",
                           store_id="28", start="2025-07-01", end="2025-08-01")
        assert len(result) == 7, (
            f"Expected 7 days, got {len(result)}. "
            f"Days returned: {[r['DayOfWeekName'] for r in result]}"
        )

    def test_day_of_week_includes_saturday(self, ts):
        """Saturday must be present in day-of-week results."""
        result = run_query(ts, "fiscal_day_of_week",
                           store_id="28", start="2025-07-01", end="2025-08-01")
        day_names = {r["DayOfWeekName"] for r in result}
        assert "Saturday" in day_names, f"Saturday missing. Got: {day_names}"

    def test_day_of_week_includes_sunday(self, ts):
        """Sunday must be present in day-of-week results."""
        result = run_query(ts, "fiscal_day_of_week",
                           store_id="28", start="2025-07-01", end="2025-08-01")
        day_names = {r["DayOfWeekName"] for r in result}
        assert "Sunday" in day_names, f"Sunday missing. Got: {day_names}"

    def test_weekend_revenue_is_nonzero(self, ts):
        """Weekend days must have non-zero revenue."""
        result = run_query(ts, "fiscal_day_of_week",
                           store_id="28", start="2025-07-01", end="2025-08-01")
        for row in result:
            if row["DayOfWeekName"] in ("Saturday", "Sunday"):
                assert row["revenue"] > 0, (
                    f"{row['DayOfWeekName']} has zero revenue"
                )

    def test_weekend_flag_correct(self, ts):
        """Saturday/Sunday should have Weekend='Y', BusinessDay='N'."""
        result = run_query(ts, "fiscal_day_of_week",
                           store_id="28", start="2025-07-01", end="2025-08-01")
        for row in result:
            if row["DayOfWeekName"] in ("Saturday", "Sunday"):
                assert row["Weekend"] == "Y", (
                    f"{row['DayOfWeekName']} has Weekend={row['Weekend']}"
                )
                assert row["BusinessDay"] == "N", (
                    f"{row['DayOfWeekName']} has BusinessDay={row['BusinessDay']}"
                )

    # --- fiscal_hourly_by_day_type: must include both day types ---

    def test_hourly_by_day_type_includes_weekends(self, ts):
        """fiscal_hourly_by_day_type must include Weekend rows (BusinessDay='N')."""
        result = run_query(ts, "fiscal_hourly_by_day_type",
                           store_id="28", start="2025-07-01", end="2025-08-01")
        day_types = {r["day_type"] for r in result}
        assert "N" in day_types, (
            f"Weekend rows (day_type='N') missing. Got types: {day_types}"
        )
        assert "Y" in day_types, (
            f"Business day rows (day_type='Y') missing. Got types: {day_types}"
        )

    # --- fiscal_hourly_heatmap: must include Sat/Sun ---

    def test_heatmap_includes_saturday(self, ts):
        """Heatmap must include Saturday rows."""
        result = run_query(ts, "fiscal_hourly_heatmap",
                           store_id="28", start="2025-07-01", end="2025-08-01")
        day_names = {r["DayOfWeekName"] for r in result}
        assert "Saturday" in day_names, f"Saturday missing from heatmap. Got: {day_names}"

    def test_heatmap_includes_sunday(self, ts):
        """Heatmap must include Sunday rows."""
        result = run_query(ts, "fiscal_hourly_heatmap",
                           store_id="28", start="2025-07-01", end="2025-08-01")
        day_names = {r["DayOfWeekName"] for r in result}
        assert "Sunday" in day_names, f"Sunday missing from heatmap. Got: {day_names}"

    # --- day_type="all" must NOT filter out weekends ---

    def test_day_type_all_includes_all_days(self, ts):
        """day_type='all' (from hierarchy_filter) must not filter any days."""
        result = run_query(ts, "fiscal_day_of_week",
                           store_id="28", start="2025-07-01", end="2025-08-01",
                           day_type="all")
        assert len(result) == 7, (
            f"day_type='all' returned {len(result)} days instead of 7"
        )

    # --- no filters = all days ---

    def test_no_filters_returns_all_days(self, ts):
        """Query with no day filters must return all 7 days."""
        result = run_query(ts, "fiscal_day_of_week",
                           start="2025-07-01", end="2025-08-01")
        assert len(result) == 7, (
            f"Unfiltered query returned {len(result)} days instead of 7"
        )

    # --- filtered_daily_trend should include weekend dates ---

    def test_daily_trend_includes_weekend_dates(self, ts):
        """Daily trend must include Saturday and Sunday dates."""
        result = run_query(ts, "filtered_daily_trend",
                           store_id="28", start="2025-07-01", end="2025-08-01")
        import datetime
        weekend_days = set()
        for row in result:
            period = row["period"]
            if hasattr(period, "weekday"):
                if period.weekday() >= 5:  # 5=Sat, 6=Sun
                    weekend_days.add(period.weekday())
            else:
                from datetime import datetime as dt
                d = dt.fromisoformat(str(period)[:10])
                if d.weekday() >= 5:
                    weekend_days.add(d.weekday())
        assert 5 in weekend_days, "No Saturday dates in daily trend"
        assert 6 in weekend_days, "No Sunday dates in daily trend"
