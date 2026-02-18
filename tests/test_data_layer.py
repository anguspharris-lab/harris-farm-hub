"""
Harris Farm Hub — Data Layer Tests
Tests for data access abstraction layer.
Min 1 success + 1 failure per function (CLAUDE.md Law #3).
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import os

from backend.data_layer import (
    DataSource,
    MockDataSource,
    FabricDataSource,
    get_data_source,
)


# ============================================================================
# MOCK DATA SOURCE TESTS
# ============================================================================

class TestMockDataSource:
    """Tests for MockDataSource implementation."""

    def test_get_store_list_success(self):
        """Success: get_store_list returns 21 Harris Farm stores."""
        source = MockDataSource()
        stores = source.get_store_list()

        assert isinstance(stores, list)
        assert len(stores) == 21
        assert "Bondi Beach" in stores
        assert "Manly" in stores
        assert "Castle Hill" in stores

    def test_get_store_list_immutable(self):
        """Success: get_store_list returns a copy, not the original."""
        source = MockDataSource()
        stores1 = source.get_store_list()
        stores2 = source.get_store_list()

        # Modify one list
        stores1.append("Fake Store")

        # Other list should be unchanged
        assert len(stores2) == 21
        assert "Fake Store" not in stores2

    def test_get_sales_data_all_stores_all_categories(self):
        """Success: get_sales_data returns data for all stores and categories."""
        source = MockDataSource()
        df = source.get_sales_data()

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

        # Check expected columns
        expected_cols = [
            'date', 'store', 'category', 'revenue', 'cogs', 'gross_profit',
            'margin_pct', 'transactions', 'avg_basket', 'wastage_cost',
            'wastage_pct', 'oos_hours', 'oos_lost_sales', 'online_orders',
            'miss_picks'
        ]
        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"

        # Check data grain: 21 stores × 6 categories × 90 days
        unique_stores = df['store'].nunique()
        unique_categories = df['category'].nunique()
        unique_dates = df['date'].nunique()

        assert unique_stores == 21
        assert unique_categories == 6
        assert unique_dates == 90

    def test_get_sales_data_deterministic(self):
        """Success: Same seed produces identical data."""
        source1 = MockDataSource(seed=42)
        source2 = MockDataSource(seed=42)

        df1 = source1.get_sales_data()
        df2 = source2.get_sales_data()

        # DataFrames should be identical
        pd.testing.assert_frame_equal(df1, df2)

    def test_get_sales_data_different_seeds(self):
        """Failure: Different seeds produce different data."""
        source1 = MockDataSource(seed=42)
        source2 = MockDataSource(seed=99)

        df1 = source1.get_sales_data()
        df2 = source2.get_sales_data()

        # DataFrames should NOT be identical
        with pytest.raises(AssertionError):
            pd.testing.assert_frame_equal(df1, df2)

    def test_get_sales_data_filter_stores(self):
        """Success: Filter by specific stores."""
        source = MockDataSource()
        stores = ["Bondi Beach", "Manly"]
        df = source.get_sales_data(stores=stores)

        assert len(df) > 0
        assert set(df['store'].unique()) == set(stores)

    def test_get_sales_data_filter_categories(self):
        """Success: Filter by specific categories."""
        source = MockDataSource()
        categories = ["Fresh Produce", "Dairy"]
        df = source.get_sales_data(categories=categories)

        assert len(df) > 0
        assert set(df['category'].unique()) == set(categories)

    def test_get_sales_data_filter_dates(self):
        """Success: Filter by date range."""
        source = MockDataSource()
        date_to = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        date_from = date_to - timedelta(days=6)  # 7 days total

        df = source.get_sales_data(date_from=date_from, date_to=date_to)

        assert len(df) > 0
        assert df['date'].min() >= date_from
        assert df['date'].max() <= date_to
        assert df['date'].nunique() == 7

    def test_get_sales_data_filter_combined(self):
        """Success: Filter by stores, categories, and dates."""
        source = MockDataSource()
        stores = ["Bondi Beach"]
        categories = ["Fresh Produce"]
        date_to = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        date_from = date_to - timedelta(days=6)

        df = source.get_sales_data(
            stores=stores,
            categories=categories,
            date_from=date_from,
            date_to=date_to
        )

        assert len(df) > 0
        assert set(df['store'].unique()) == set(stores)
        assert set(df['category'].unique()) == set(categories)
        assert df['date'].nunique() == 7

        # Should have exactly 1 store × 1 category × 7 days = 7 rows
        assert len(df) == 7

    def test_get_sales_data_empty_filter(self):
        """Failure: Empty store/category filter returns empty DataFrame."""
        source = MockDataSource()

        # Empty store filter
        df = source.get_sales_data(stores=[])
        assert len(df) == 0

        # Empty category filter
        df = source.get_sales_data(categories=[])
        assert len(df) == 0

    def test_get_sales_data_nonexistent_store(self):
        """Failure: Filter by non-existent store returns empty DataFrame."""
        source = MockDataSource()
        df = source.get_sales_data(stores=["Fake Store"])

        assert len(df) == 0

    def test_get_sales_data_data_quality(self):
        """Success: Data quality checks pass."""
        source = MockDataSource()
        df = source.get_sales_data()

        # No negative revenue
        assert (df['revenue'] >= 0).all()

        # Margin between 5-55%
        assert (df['margin_pct'] >= 0.05).all()
        assert (df['margin_pct'] <= 0.55).all()

        # Wastage rate 0-25%
        assert (df['wastage_pct'] >= 0).all()
        assert (df['wastage_pct'] <= 25).all()

        # COGS + gross_profit = revenue (within ±0.01)
        calculated_revenue = df['cogs'] + df['gross_profit']
        assert ((df['revenue'] - calculated_revenue).abs() <= 0.01).all()

        # Transactions > 0
        assert (df['transactions'] > 0).all()

        # OOS hours 0-24
        assert (df['oos_hours'] >= 0).all()
        assert (df['oos_hours'] <= 24).all()

    def test_get_sales_data_kpi_traceability(self):
        """Success: All KPIs traceable to source data (±0.01)."""
        source = MockDataSource()
        df = source.get_sales_data()

        # Check one row in detail
        row = df.iloc[0]

        # Margin calculation
        expected_margin = row['gross_profit'] / row['revenue'] if row['revenue'] > 0 else 0
        assert abs(row['margin_pct'] - expected_margin) <= 0.0001

        # Avg basket calculation
        expected_basket = row['revenue'] / row['transactions'] if row['transactions'] > 0 else 0
        assert abs(row['avg_basket'] - expected_basket) <= 0.01

    def test_get_sales_data_caching(self):
        """Success: Data is cached and reused."""
        source = MockDataSource()

        # First call generates data
        df1 = source.get_sales_data()
        cache1_id = id(source._data_cache)

        # Second call reuses cache
        df2 = source.get_sales_data()
        cache2_id = id(source._data_cache)

        assert cache1_id == cache2_id
        pd.testing.assert_frame_equal(df1, df2)


# ============================================================================
# FABRIC DATA SOURCE TESTS
# ============================================================================

class TestFabricDataSource:
    """Tests for FabricDataSource stub."""

    def test_get_store_list_not_implemented(self):
        """Failure: get_store_list raises NotImplementedError."""
        source = FabricDataSource()

        with pytest.raises(NotImplementedError) as exc_info:
            source.get_store_list()

        assert "not yet implemented" in str(exc_info.value).lower()

    def test_get_sales_data_not_implemented(self):
        """Failure: get_sales_data raises NotImplementedError."""
        source = FabricDataSource()

        with pytest.raises(NotImplementedError) as exc_info:
            source.get_sales_data()

        assert "not yet implemented" in str(exc_info.value).lower()

    def test_initialization_with_config(self):
        """Success: FabricDataSource initializes with config."""
        config = {"workspace_id": "test123", "lakehouse_id": "lake456"}
        source = FabricDataSource(config=config)

        assert source.config == config

    def test_initialization_without_config(self):
        """Success: FabricDataSource initializes without config."""
        source = FabricDataSource()

        assert source.config == {}


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================

class TestGetDataSource:
    """Tests for get_data_source factory function."""

    def test_get_data_source_mock_default(self):
        """Success: get_data_source returns MockDataSource by default."""
        source = get_data_source()

        assert isinstance(source, MockDataSource)
        assert source.seed == 42

    def test_get_data_source_mock_explicit(self):
        """Success: get_data_source returns MockDataSource when db_type='mock'."""
        source = get_data_source(db_type="mock")

        assert isinstance(source, MockDataSource)
        assert source.seed == 42

    def test_get_data_source_fabric(self):
        """Success: get_data_source returns FabricDataSource when db_type='fabric'."""
        source = get_data_source(db_type="fabric")

        assert isinstance(source, FabricDataSource)

    def test_get_data_source_invalid_type(self):
        """Failure: get_data_source raises ValueError for invalid db_type."""
        with pytest.raises(ValueError) as exc_info:
            get_data_source(db_type="invalid")

        assert "unknown db_type" in str(exc_info.value).lower()
        assert "invalid" in str(exc_info.value).lower()

    def test_get_data_source_from_env_mock(self):
        """Success: get_data_source reads DB_TYPE from environment (mock)."""
        # Save original env var
        original = os.environ.get("DB_TYPE")

        try:
            os.environ["DB_TYPE"] = "mock"
            source = get_data_source()

            assert isinstance(source, MockDataSource)
        finally:
            # Restore original env var
            if original is not None:
                os.environ["DB_TYPE"] = original
            elif "DB_TYPE" in os.environ:
                del os.environ["DB_TYPE"]

    def test_get_data_source_from_env_fabric(self):
        """Success: get_data_source reads DB_TYPE from environment (fabric)."""
        original = os.environ.get("DB_TYPE")

        try:
            os.environ["DB_TYPE"] = "fabric"
            source = get_data_source()

            assert isinstance(source, FabricDataSource)
        finally:
            if original is not None:
                os.environ["DB_TYPE"] = original
            elif "DB_TYPE" in os.environ:
                del os.environ["DB_TYPE"]

    def test_get_data_source_case_insensitive(self):
        """Success: get_data_source is case-insensitive."""
        source1 = get_data_source(db_type="MOCK")
        source2 = get_data_source(db_type="Mock")
        source3 = get_data_source(db_type="FaBrIc")

        assert isinstance(source1, MockDataSource)
        assert isinstance(source2, MockDataSource)
        assert isinstance(source3, FabricDataSource)


# ============================================================================
# ABSTRACT BASE CLASS TESTS
# ============================================================================

class TestDataSourceABC:
    """Tests for DataSource abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Failure: Cannot instantiate DataSource directly."""
        with pytest.raises(TypeError):
            DataSource()

    def test_subclass_must_implement_methods(self):
        """Failure: Subclass must implement all abstract methods."""

        # Incomplete subclass missing get_store_list
        class IncompleteSource(DataSource):
            def get_sales_data(self, stores=None, categories=None,
                               date_from=None, date_to=None):
                return pd.DataFrame()

        with pytest.raises(TypeError):
            IncompleteSource()

    def test_subclass_implements_all_methods(self):
        """Success: Complete subclass can be instantiated."""

        class CompleteSource(DataSource):
            def get_sales_data(self, stores=None, categories=None,
                               date_from=None, date_to=None):
                return pd.DataFrame()

            def get_store_list(self):
                return []

        # Should not raise
        source = CompleteSource()
        assert isinstance(source, DataSource)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for data layer."""

    def test_end_to_end_mock_workflow(self):
        """Success: Complete workflow with MockDataSource."""
        # Get data source via factory
        source = get_data_source(db_type="mock")

        # Get store list
        stores = source.get_store_list()
        assert len(stores) == 21

        # Get sales data for specific stores
        df = source.get_sales_data(
            stores=["Bondi Beach", "Manly"],
            categories=["Fresh Produce"],
            date_from=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6),
            date_to=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )

        # Verify data quality
        assert len(df) == 14  # 2 stores × 1 category × 7 days
        assert (df['revenue'] >= 0).all()
        assert (df['margin_pct'] >= 0.05).all()
        assert (df['margin_pct'] <= 0.55).all()

    def test_data_consistency_across_calls(self):
        """Success: Multiple calls with same params return consistent data."""
        source = get_data_source(db_type="mock")

        df1 = source.get_sales_data(
            stores=["Bondi Beach"],
            categories=["Fresh Produce"],
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 1, 7)
        )

        df2 = source.get_sales_data(
            stores=["Bondi Beach"],
            categories=["Fresh Produce"],
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 1, 7)
        )

        pd.testing.assert_frame_equal(df1, df2)
