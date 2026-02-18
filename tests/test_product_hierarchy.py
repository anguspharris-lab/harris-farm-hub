"""
Tests for the Product Hierarchy Integration.
Covers: parquet file, hierarchy module, upgraded PLU lookup,
hierarchy-aware queries, API endpoints, and join coverage.
"""

import sys
from pathlib import Path

import pytest

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

HIERARCHY_PARQUET = Path(__file__).parent.parent / "data" / "product_hierarchy.parquet"


# ============================================================================
# HIERARCHY FILE TESTS
# ============================================================================

class TestHierarchyFile:
    """Verify the product_hierarchy.parquet file."""

    def test_parquet_exists(self):
        assert HIERARCHY_PARQUET.exists(), "product_hierarchy.parquet not found"

    def test_parquet_row_count(self):
        import pandas as pd
        df = pd.read_parquet(HIERARCHY_PARQUET)
        assert 70_000 < len(df) < 80_000, f"Expected ~72,911 rows, got {len(df)}"

    def test_parquet_columns(self):
        import pandas as pd
        df = pd.read_parquet(HIERARCHY_PARQUET)
        expected = {
            "ProductNumber", "ProductName", "DepartmentDesc",
            "MajorGroupDesc", "MinorGroupDesc", "HFMItemDesc",
            "BuyerId", "ProductLifecycleStateId",
            "DepartmentCode", "MajorGroupCode", "MinorGroupCode", "HFMItem",
        }
        assert expected.issubset(set(df.columns)), (
            f"Missing columns: {expected - set(df.columns)}"
        )

    def test_no_duplicate_product_numbers(self):
        import pandas as pd
        df = pd.read_parquet(HIERARCHY_PARQUET)
        dupes = df["ProductNumber"].duplicated().sum()
        assert dupes == 0, f"{dupes} duplicate ProductNumber values"

    def test_product_number_is_string(self):
        import pandas as pd
        df = pd.read_parquet(HIERARCHY_PARQUET)
        assert df["ProductNumber"].dtype == "object", (
            f"ProductNumber should be string, got {df['ProductNumber'].dtype}"
        )

    def test_department_codes_no_decimal(self):
        import pandas as pd
        df = pd.read_parquet(HIERARCHY_PARQUET)
        # Ensure no .0 suffixes (e.g., "10.0" should be "10")
        has_decimal = df["DepartmentCode"].str.contains(r"\.", na=False).any()
        assert not has_decimal, "DepartmentCode contains decimal points"


# ============================================================================
# HIERARCHY MODULE TESTS
# ============================================================================

class TestHierarchyModule:
    """Test backend/product_hierarchy.py functions."""

    def test_load_hierarchy_not_empty(self):
        from product_hierarchy import load_hierarchy
        load_hierarchy.cache_clear()
        df = load_hierarchy()
        assert len(df) > 70_000

    def test_get_departments_returns_nine(self):
        from product_hierarchy import get_departments
        depts = get_departments()
        assert len(depts) == 9, f"Expected 9 departments, got {len(depts)}"

    def test_get_departments_has_fv(self):
        from product_hierarchy import get_departments
        depts = get_departments()
        names = [d["name"] for d in depts]
        assert any("FRUIT" in n for n in names), "Missing FRUIT & VEGETABLES"

    def test_get_major_groups_for_fv(self):
        from product_hierarchy import get_major_groups
        groups = get_major_groups("10")
        assert len(groups) >= 2, "F&V should have multiple major groups"
        names = [g["name"] for g in groups]
        assert any("FRUIT" in n for n in names)

    def test_get_major_groups_invalid_dept(self):
        from product_hierarchy import get_major_groups
        groups = get_major_groups("99")
        assert groups == [], "Invalid dept code should return empty list"

    def test_get_minor_groups(self):
        from product_hierarchy import get_minor_groups
        groups = get_minor_groups("10", "2")  # F&V, Fruit
        assert len(groups) > 0, "F&V Fruit should have minor groups"

    def test_search_products_found(self):
        from product_hierarchy import search_products
        results = search_products("banana")
        assert len(results) > 0, "Should find banana products"
        assert all("product_name" in r for r in results)

    def test_search_products_not_found(self):
        from product_hierarchy import search_products
        results = search_products("zzzzzznonexistent")
        assert len(results) == 0

    def test_get_product_by_plu_known(self):
        from product_hierarchy import get_product_by_plu
        result = get_product_by_plu("4322")
        assert result is not None
        assert "STRAWBERRIES" in result["product_name"].upper()
        assert result["department_code"] == "10"

    def test_get_product_by_plu_unknown(self):
        from product_hierarchy import get_product_by_plu
        result = get_product_by_plu("0000000")
        assert result is None

    def test_hierarchy_stats(self):
        from product_hierarchy import hierarchy_stats
        stats = hierarchy_stats()
        assert stats["available"] is True
        assert stats["total_products"] > 70_000
        assert stats["departments"] == 9
        assert stats["major_groups"] == 30


# ============================================================================
# UPGRADED PLU LOOKUP TESTS
# ============================================================================

class TestUpgradedPLULookup:
    """Test that plu_lookup.py now uses the full 72,911-product hierarchy."""

    def test_load_returns_large_dict(self):
        from plu_lookup import load_plu_names
        load_plu_names.cache_clear()
        names = load_plu_names()
        assert len(names) > 70_000, (
            f"Expected ~72,911 entries, got {len(names)}"
        )

    def test_resolve_known_plu(self):
        from plu_lookup import resolve_plu
        name = resolve_plu("4322")
        assert "PLU" not in name, "Known PLU should resolve to a real name"
        assert "STRAWBERRIES" in name.upper()

    def test_resolve_unknown_plu(self):
        from plu_lookup import resolve_plu
        name = resolve_plu("0000000")
        assert name.startswith("PLU ")

    def test_enrich_items_basic(self):
        from plu_lookup import enrich_items
        items = [{"plu_item_id": "4322"}]
        enriched = enrich_items(items)
        assert "product_name" in enriched[0]
        assert "STRAWBERRIES" in enriched[0]["product_name"].upper()

    def test_enrich_items_with_hierarchy(self):
        from plu_lookup import enrich_items, load_plu_details
        load_plu_details.cache_clear()
        items = [{"plu_item_id": "4322"}]
        enriched = enrich_items(items, include_hierarchy=True)
        assert "department" in enriched[0]
        assert "FRUIT" in enriched[0]["department"].upper()
        assert "major_group" in enriched[0]

    def test_coverage_stats_updated(self):
        from plu_lookup import plu_coverage_stats
        stats = plu_coverage_stats()
        assert stats["known_plus"] > 70_000
        assert "hierarchy" in stats["source"]

    def test_load_plu_details_populated(self):
        from plu_lookup import load_plu_details
        load_plu_details.cache_clear()
        details = load_plu_details()
        assert len(details) > 70_000
        d = details.get("4322", {})
        assert d.get("department") != ""
        assert d.get("lifecycle") != ""


# ============================================================================
# HIERARCHY-AWARE QUERY TESTS
# ============================================================================

class TestHierarchyQueries:
    """Test the 7 new hierarchy-aware queries."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from transaction_layer import TransactionStore
        self.ts = TransactionStore()
        self.start = "2025-12-01"
        self.end = "2026-01-01"

    def test_department_revenue_returns_departments(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "department_revenue",
                      start=self.start, end=self.end)
        assert len(r) <= 9, "Should have at most 9 departments"
        assert len(r) > 0
        assert all("DepartmentDesc" in row for row in r)

    def test_department_revenue_sorted_by_revenue(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "department_revenue",
                      start=self.start, end=self.end)
        revenues = [row["revenue"] for row in r]
        assert revenues == sorted(revenues, reverse=True)

    def test_major_group_revenue(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "major_group_revenue",
                      dept_code="10", start=self.start, end=self.end)
        assert len(r) > 0
        assert all("MajorGroupDesc" in row for row in r)

    def test_minor_group_revenue(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "minor_group_revenue",
                      dept_code="10", major_code="2",
                      start=self.start, end=self.end)
        assert len(r) > 0
        assert all("MinorGroupDesc" in row for row in r)

    def test_department_monthly_trend(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "department_monthly_trend",
                      start=self.start, end=self.end)
        assert len(r) > 0
        assert all("period" in row and "DepartmentDesc" in row for row in r)

    def test_buyer_performance(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "buyer_performance",
                      start=self.start, end=self.end)
        assert len(r) > 0
        assert all("BuyerId" in row and "revenue" in row for row in r)

    def test_top_items_by_department(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "top_items_by_department",
                      dept_code="10", start=self.start, end=self.end,
                      limit=5)
        assert len(r) <= 5
        assert len(r) > 0
        assert all("ProductName" in row for row in r)

    def test_department_store_heatmap(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "department_store_heatmap",
                      start=self.start, end=self.end)
        assert len(r) > 0
        assert all("Store_ID" in row and "DepartmentDesc" in row for row in r)


# ============================================================================
# HIERARCHY API TESTS
# ============================================================================

class TestHierarchyAPI:
    """Test the 5 hierarchy API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
        from app import app
        from fastapi.testclient import TestClient
        self.client = TestClient(app)

    def test_departments_endpoint(self):
        r = self.client.get("/api/hierarchy/departments")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 9

    def test_browse_dept_endpoint(self):
        r = self.client.get("/api/hierarchy/browse/10")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 2

    def test_browse_invalid_dept(self):
        r = self.client.get("/api/hierarchy/browse/99")
        assert r.status_code == 404

    def test_browse_major_endpoint(self):
        r = self.client.get("/api/hierarchy/browse/10/2")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0

    def test_search_endpoint(self):
        r = self.client.get("/api/hierarchy/search?q=strawberry")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0

    def test_search_too_short(self):
        r = self.client.get("/api/hierarchy/search?q=x")
        assert r.status_code == 400

    def test_stats_endpoint(self):
        r = self.client.get("/api/hierarchy/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["available"] is True
        assert data["total_products"] > 70_000


# ============================================================================
# JOIN COVERAGE TESTS
# ============================================================================

# ============================================================================
# SEARCH HIERARCHY TESTS
# ============================================================================

class TestSearchHierarchy:
    """Test the search_hierarchy() function for the searchable product filter."""

    def test_search_by_product_name(self):
        from product_hierarchy import search_hierarchy
        results = search_hierarchy("banana")
        assert len(results) > 0, "Should find banana products"
        assert any("banana" in r["product_name"].lower() for r in results)

    def test_search_by_exact_plu(self):
        from product_hierarchy import search_hierarchy
        results = search_hierarchy("4322")
        assert len(results) > 0, "Should find PLU 4322"
        assert results[0]["product_number"] == "4322", (
            "Exact PLU match should be first result"
        )

    def test_search_by_department_name(self):
        from product_hierarchy import search_hierarchy
        results = search_hierarchy("FRUIT")
        assert len(results) > 0, "Should find products in Fruit dept"
        assert any("FRUIT" in r["dept_name"].upper() for r in results)

    def test_search_by_minor_group_name(self):
        from product_hierarchy import search_hierarchy
        results = search_hierarchy("Citrus")
        assert len(results) > 0, "Should find products in Citrus group"

    def test_search_respects_limit(self):
        from product_hierarchy import search_hierarchy
        results = search_hierarchy("ba", limit=5)
        assert len(results) <= 5

    def test_search_short_query_returns_empty(self):
        from product_hierarchy import search_hierarchy
        results = search_hierarchy("a")
        assert results == [], "Single character should return empty"

    def test_search_empty_query_returns_empty(self):
        from product_hierarchy import search_hierarchy
        results = search_hierarchy("")
        assert results == []

    def test_search_all_hierarchy_codes_present(self):
        from product_hierarchy import search_hierarchy
        results = search_hierarchy("banana")
        assert len(results) > 0
        required_keys = [
            "product_number", "product_name",
            "dept_code", "dept_name",
            "major_code", "major_name",
            "minor_code", "minor_name",
            "hfm_item_code", "hfm_item_name",
            "lifecycle",
        ]
        for r in results:
            for key in required_keys:
                assert key in r, f"Missing key: {key}"
                assert r[key] is not None, f"Key {key} is None"

    def test_search_plu_priority_ordering(self):
        from product_hierarchy import search_hierarchy
        # Search for a known PLU — it should appear first
        results = search_hierarchy("4322")
        assert len(results) > 0
        assert results[0]["product_number"] == "4322"

    def test_search_no_results(self):
        from product_hierarchy import search_hierarchy
        results = search_hierarchy("zzzzzznonexistent99")
        assert results == []

    def test_search_default_limit_is_50(self):
        from product_hierarchy import search_hierarchy
        # "a" would be too short, use a broad query
        results = search_hierarchy("an")
        assert len(results) <= 50


# ============================================================================
# JOIN COVERAGE TESTS
# ============================================================================

class TestActiveOnlyFiltering:
    """Test that hierarchy browsing functions return only active products."""

    def test_departments_only_active(self):
        """Success: all department product counts reflect active only."""
        from product_hierarchy import get_departments
        depts = get_departments()
        for d in depts:
            assert d["active_products"] == d["total_products"], (
                "Department '{}' total should equal active count".format(d["name"])
            )
            assert d["deleted_products"] == 0

    def test_major_groups_only_active(self):
        """Success: major group active_products equals total_products."""
        from product_hierarchy import get_major_groups
        groups = get_major_groups("10")  # F&V
        assert len(groups) > 0
        for g in groups:
            assert g["active_products"] == g["total_products"]

    def test_products_in_hfm_item_all_active(self):
        """Success: get_products_in_hfm_item returns only Active lifecycle."""
        from product_hierarchy import (
            get_departments, get_major_groups, get_minor_groups,
            get_hfm_items, get_products_in_hfm_item,
        )
        depts = get_departments()
        if not depts:
            pytest.skip("No departments")
        dept = depts[0]
        majors = get_major_groups(dept["code"])
        if not majors:
            pytest.skip("No major groups")
        major = majors[0]
        minors = get_minor_groups(dept["code"], major["code"])
        if not minors:
            pytest.skip("No minor groups")
        minor = minors[0]
        hfm_items = get_hfm_items(dept["code"], major["code"], minor["code"])
        if not hfm_items:
            pytest.skip("No HFM items")
        hfm = hfm_items[0]
        products = get_products_in_hfm_item(
            dept["code"], major["code"], minor["code"], hfm["code"])
        for p in products:
            assert p["lifecycle"] == "Active", (
                "Product {} has lifecycle '{}', expected 'Active'".format(
                    p["product_number"], p["lifecycle"])
            )

    def test_search_hierarchy_returns_only_active(self):
        """Success: search_hierarchy only returns active products."""
        from product_hierarchy import search_hierarchy
        results = search_hierarchy("banana")
        assert len(results) > 0
        for r in results:
            assert r["lifecycle"] == "Active", (
                "Search result {} has lifecycle '{}', expected 'Active'".format(
                    r["product_number"], r["lifecycle"])
            )

    def test_no_deleted_products_in_departments(self):
        """Failure: deleted-only hierarchy branches should not appear."""
        from product_hierarchy import load_hierarchy, get_departments
        # Get departments that have ONLY deleted products
        df = load_hierarchy()
        depts = get_departments()
        dept_codes = {d["code"] for d in depts}
        # Every returned department must have at least one active product
        for code in dept_codes:
            active_count = len(df[
                (df["DepartmentCode"] == code)
                & (df["ProductLifecycleStateId"] == "Active")
            ])
            assert active_count > 0, (
                "Dept {} appeared but has no active products".format(code))

    def test_no_deleted_products_in_minor_groups(self):
        """Failure: minor groups with no active products should be hidden."""
        from product_hierarchy import (
            get_departments, get_major_groups, get_minor_groups,
            load_hierarchy,
        )
        df = load_hierarchy()
        depts = get_departments()
        if not depts:
            pytest.skip("No departments")
        dept = depts[0]
        majors = get_major_groups(dept["code"])
        if not majors:
            pytest.skip("No major groups")
        major = majors[0]
        minors = get_minor_groups(dept["code"], major["code"])
        for m in minors:
            active_count = len(df[
                (df["DepartmentCode"] == dept["code"])
                & (df["MajorGroupCode"] == major["code"])
                & (df["MinorGroupCode"] == m["code"])
                & (df["ProductLifecycleStateId"] == "Active")
            ])
            assert active_count > 0, (
                "Minor group {} appeared but has no active products".format(
                    m["code"]))


class TestJoinCoverage:
    """Verify the PLU match rate between transactions and hierarchy."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from transaction_layer import TransactionStore
        self.ts = TransactionStore()

    def test_fy26_plu_match_rate(self):
        """Verify 97%+ PLU match rate by count."""
        result = self.ts.query("""
            SELECT
                COUNT(DISTINCT t.PLUItem_ID) AS total_plus,
                COUNT(DISTINCT CASE WHEN p.ProductNumber IS NOT NULL
                      THEN t.PLUItem_ID END) AS matched_plus
            FROM transactions t
            LEFT JOIN product_hierarchy p
                ON t.PLUItem_ID = p.ProductNumber
            WHERE t.fiscal_year = 'FY26'
        """)
        r = result[0]
        match_pct = r["matched_plus"] / r["total_plus"] * 100
        assert match_pct > 97, f"PLU match only {match_pct:.1f}% (expected >97%)"

    def test_fy26_revenue_match_rate(self):
        """Verify 97%+ revenue match rate."""
        result = self.ts.query("""
            SELECT
                SUM(t.SalesIncGST) AS total_revenue,
                SUM(CASE WHEN p.ProductNumber IS NOT NULL
                    THEN t.SalesIncGST ELSE 0 END) AS matched_revenue
            FROM transactions t
            LEFT JOIN product_hierarchy p
                ON t.PLUItem_ID = p.ProductNumber
            WHERE t.fiscal_year = 'FY26'
        """)
        r = result[0]
        match_pct = r["matched_revenue"] / r["total_revenue"] * 100
        assert match_pct > 97, f"Revenue match only {match_pct:.1f}% (expected >97%)"

    def test_query_catalog_count(self):
        """Verify the query catalog includes hierarchy queries."""
        from transaction_queries import get_query_catalog
        catalog = get_query_catalog()
        assert len(catalog) >= 31, f"Expected 31+ queries, got {len(catalog)}"
        names = [q["name"] for q in catalog]
        assert "department_revenue" in names
        assert "buyer_performance" in names
