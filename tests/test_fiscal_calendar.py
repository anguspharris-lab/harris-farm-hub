"""
Tests for Fiscal Calendar Integration.
Covers: parquet file, backend module, DuckDB integration,
fiscal-aware queries, and API endpoints.
"""

import sys
from pathlib import Path

import pytest

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

FISCAL_PARQUET = Path(__file__).parent.parent / "data" / "fiscal_calendar_daily.parquet"


# ============================================================================
# PARQUET FILE TESTS
# ============================================================================

class TestFiscalParquet:
    """Verify the fiscal_calendar_daily.parquet file."""

    def test_parquet_exists(self):
        assert FISCAL_PARQUET.exists(), "fiscal_calendar_daily.parquet not found"

    def test_row_count(self):
        import pandas as pd
        df = pd.read_parquet(FISCAL_PARQUET)
        assert len(df) == 4018, f"Expected 4,018 rows, got {len(df)}"

    def test_column_count(self):
        import pandas as pd
        df = pd.read_parquet(FISCAL_PARQUET)
        assert len(df.columns) == 45, f"Expected 45 columns, got {len(df.columns)}"

    def test_no_nulls(self):
        import pandas as pd
        df = pd.read_parquet(FISCAL_PARQUET)
        total_nulls = df.isnull().sum().sum()
        assert total_nulls == 0, f"Found {total_nulls} null values"

    def test_date_range(self):
        import pandas as pd
        df = pd.read_parquet(FISCAL_PARQUET)
        min_date = df["TheDate"].min()
        max_date = df["TheDate"].max()
        assert min_date.year == 2015 and min_date.month == 6
        assert max_date.year == 2026 and max_date.month == 6

    def test_unique_dates(self):
        import pandas as pd
        df = pd.read_parquet(FISCAL_PARQUET)
        dupes = df["TheDate"].duplicated().sum()
        assert dupes == 0, f"{dupes} duplicate dates"


# ============================================================================
# FISCAL CALENDAR MODULE TESTS
# ============================================================================

class TestFiscalModule:
    """Test backend/fiscal_calendar.py functions."""

    def test_load_fiscal_calendar_not_empty(self):
        from fiscal_calendar import load_fiscal_calendar
        load_fiscal_calendar.cache_clear()
        df = load_fiscal_calendar()
        assert len(df) == 4018

    def test_get_fiscal_years_returns_11(self):
        from fiscal_calendar import get_fiscal_years
        years = get_fiscal_years()
        assert len(years) == 11
        assert 2016 in years
        assert 2026 in years

    def test_get_fy_date_range_valid(self):
        from fiscal_calendar import get_fy_date_range
        start, end = get_fy_date_range(2026)
        assert start is not None
        assert start.startswith("2025-06")
        assert end.startswith("2026-06")

    def test_get_fy_date_range_invalid(self):
        from fiscal_calendar import get_fy_date_range
        start, end = get_fy_date_range(9999)
        assert start is None
        assert end is None

    def test_get_fiscal_months_returns_12(self):
        from fiscal_calendar import get_fiscal_months
        months = get_fiscal_months(2026)
        assert len(months) == 12

    def test_fiscal_months_544_pattern(self):
        """Verify 5-4-4 pattern: months 1,4,7,10 have 5 weeks; rest have 4."""
        from fiscal_calendar import get_fiscal_months
        months = get_fiscal_months(2026)
        for m in months:
            if m["month_no"] in (1, 4, 7, 10):
                assert m["weeks"] == 5, f"Month {m['month_no']} should be 5 weeks"
            else:
                assert m["weeks"] == 4, f"Month {m['month_no']} should be 4 weeks"

    def test_get_fiscal_quarters_returns_4(self):
        from fiscal_calendar import get_fiscal_quarters
        quarters = get_fiscal_quarters(2026)
        assert len(quarters) == 4

    def test_quarter_is_91_days(self):
        from fiscal_calendar import get_fiscal_quarters
        quarters = get_fiscal_quarters(2026)
        for q in quarters:
            assert q["days"] == 91, f"Q{q['quarter_no']} has {q['days']} days, expected 91"

    def test_get_fiscal_weeks_count(self):
        from fiscal_calendar import get_fiscal_weeks
        weeks_52 = get_fiscal_weeks(2026)
        assert len(weeks_52) == 52
        weeks_53 = get_fiscal_weeks(2022)
        assert len(weeks_53) == 53

    def test_is_long_year(self):
        from fiscal_calendar import is_long_year
        assert is_long_year(2016) is True
        assert is_long_year(2022) is True
        assert is_long_year(2026) is False

    def test_get_current_fiscal_period(self):
        from fiscal_calendar import get_current_fiscal_period
        current = get_current_fiscal_period()
        assert "fin_year" in current
        assert current["fin_year"] >= 2024

    def test_comparison_range_normal(self):
        from fiscal_calendar import get_comparison_range
        comp = get_comparison_range("month", 7, 2026)
        assert comp["current"] is not None
        assert comp["prior"] is not None
        assert comp["current"]["label"] == "January FY2026"
        assert comp["prior"]["label"] == "January FY2025"

    def test_comparison_range_week53_caveat(self):
        from fiscal_calendar import get_comparison_range
        comp = get_comparison_range("week", 53, 2022)
        assert comp["prior"] is None
        assert len(comp["caveats"]) > 0
        assert "53" in comp["caveats"][0]

    def test_fiscal_calendar_stats(self):
        from fiscal_calendar import fiscal_calendar_stats
        stats = fiscal_calendar_stats()
        assert stats["available"] is True
        assert stats["total_days"] == 4018
        assert stats["calendar_pattern"] == "5-4-4"


# ============================================================================
# DUCKDB INTEGRATION TESTS
# ============================================================================

class TestFiscalDuckDB:
    """Test fiscal_calendar table in DuckDB connections."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from transaction_layer import TransactionStore
        self.ts = TransactionStore()

    def test_fiscal_calendar_table_exists(self):
        result = self.ts.query("SELECT COUNT(*) AS cnt FROM fiscal_calendar")
        assert result[0]["cnt"] == 4018

    def test_join_transactions_to_calendar(self):
        result = self.ts.query("""
            SELECT COUNT(*) AS matched
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            WHERE fc.FinYear = 2026
        """)
        assert result[0]["matched"] > 0

    def test_all_transaction_dates_in_calendar(self):
        """Every transaction date should exist in the fiscal calendar."""
        result = self.ts.query("""
            SELECT COUNT(DISTINCT CAST(t.SaleDate AS DATE)) AS unmatched
            FROM transactions t
            LEFT JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            WHERE fc.TheDate IS NULL
        """)
        assert result[0]["unmatched"] == 0, (
            f"{result[0]['unmatched']} transaction dates not in fiscal calendar"
        )

    def test_finyear_boundary_alignment(self):
        """Fiscal calendar FinYear and parquet fiscal_year mostly agree.
        The 5-4-4 retail FY starts Monday nearest July 1, while parquet
        files use exact July 1. A few boundary days may differ."""
        result = self.ts.query("""
            SELECT fc.FinYear, t.fiscal_year,
                   COUNT(*) AS cnt
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            GROUP BY fc.FinYear, t.fiscal_year
            ORDER BY cnt DESC
        """)
        # The vast majority of rows should have matching labels
        total = sum(r["cnt"] for r in result)
        matched = 0
        for r in result:
            expected_label = f"FY{str(r['FinYear'])[2:]}"
            if r["fiscal_year"] == expected_label:
                matched += r["cnt"]
        match_pct = matched / total * 100
        assert match_pct > 99, f"Only {match_pct:.1f}% of rows have matching FY labels"


# ============================================================================
# FISCAL QUERY TESTS
# ============================================================================

class TestFiscalQueries:
    """Test the 10 fiscal-aware queries."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from transaction_layer import TransactionStore
        self.ts = TransactionStore()

    def test_fiscal_weekly_trend(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "fiscal_weekly_trend", fin_year=2026)
        assert len(r) > 0
        assert "week_no" in r[0]
        assert "revenue" in r[0]

    def test_fiscal_monthly_trend(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "fiscal_monthly_trend", fin_year=2026)
        assert len(r) > 0
        assert "month_name" in r[0]
        assert "weeks_in_month" in r[0]

    def test_fiscal_quarter_summary(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "fiscal_quarter_summary", fin_year=2026)
        assert len(r) >= 1
        assert "quarter_no" in r[0]
        assert "weeks" in r[0]

    def test_fiscal_yoy_weekly(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "fiscal_yoy_weekly",
                      fin_year=2026, fin_year_2=2025)
        assert len(r) > 0
        # Verify week 53 is excluded
        week_nos = [row["week_no"] for row in r]
        assert 53 not in week_nos

    def test_fiscal_yoy_monthly(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "fiscal_yoy_monthly",
                      fin_year=2026, fin_year_2=2025)
        assert len(r) > 0
        years = {row["FinYear"] for row in r}
        assert 2025 in years or 2026 in years

    def test_fiscal_day_of_week(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "fiscal_day_of_week",
                      start="2025-12-01", end="2026-01-01", store_id="28")
        assert len(r) == 7
        names = {row["DayOfWeekName"] for row in r}
        assert "Monday" in names
        assert "Sunday" in names

    def test_fiscal_season_comparison(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "fiscal_season_comparison",
                      fin_year=2026, fin_year_2=2025)
        assert len(r) > 0
        seasons = {row["SeasonName"] for row in r}
        assert len(seasons) >= 2

    def test_fiscal_hourly_by_day_type(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "fiscal_hourly_by_day_type",
                      start="2025-12-01", end="2026-01-01", store_id="28")
        assert len(r) > 0
        assert "day_type" in r[0]
        assert "hour_of_day" in r[0]

    def test_fiscal_hourly_heatmap(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "fiscal_hourly_heatmap",
                      start="2025-12-01", end="2026-01-01", store_id="28")
        assert len(r) > 0
        assert "DayOfWeekName" in r[0]
        assert "hour_of_day" in r[0]

    def test_fiscal_hourly_by_month(self):
        from transaction_queries import run_query
        r = run_query(self.ts, "fiscal_hourly_by_month",
                      fin_year=2026, store_id="28")
        assert len(r) > 0
        assert "month_name" in r[0]
        assert "hour_of_day" in r[0]


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

class TestFiscalAPI:
    """Test the 3 fiscal calendar API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
        from app import app
        from transaction_layer import TransactionStore
        app.state.txn_store = TransactionStore()
        from fastapi.testclient import TestClient
        self.client = TestClient(app)

    def test_years_endpoint(self):
        r = self.client.get("/api/fiscal-calendar/years")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 11
        years = [y["fin_year"] for y in data["years"]]
        assert 2026 in years

    def test_periods_endpoint(self):
        r = self.client.get("/api/fiscal-calendar/periods/2026")
        assert r.status_code == 200
        data = r.json()
        assert data["fin_year"] == 2026
        assert len(data["months"]) == 12
        assert len(data["quarters"]) == 4

    def test_periods_invalid_fy(self):
        r = self.client.get("/api/fiscal-calendar/periods/9999")
        assert r.status_code == 404

    def test_current_endpoint(self):
        r = self.client.get("/api/fiscal-calendar/current")
        assert r.status_code == 200
        data = r.json()
        assert "fin_year" in data
        assert data["fin_year"] >= 2024

    def test_query_catalog_includes_fiscal(self):
        r = self.client.get("/api/transactions/query-catalog")
        assert r.status_code == 200
        data = r.json()
        names = {q["name"] for q in data["queries"]}
        assert "fiscal_weekly_trend" in names
        assert "fiscal_hourly_heatmap" in names
        assert data["count"] >= 41

    def test_run_fiscal_query_via_api(self):
        r = self.client.get("/api/transactions/run/fiscal_quarter_summary",
                            params={"fin_year": 2026})
        assert r.status_code == 200
        data = r.json()
        assert data["query"] == "fiscal_quarter_summary"
        assert data["count"] >= 1
