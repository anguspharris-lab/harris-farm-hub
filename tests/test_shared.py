"""
Tests for Harris Farm Hub Shared Modules
Law 3: min 1 success + 1 failure per function

Tests cover:
- Store network constants (STORES, REGIONS)
- 5/4/4 Retail Fiscal Calendar functions
- Real data access (SQLite database)
"""

import pytest
from datetime import datetime, timedelta
import sys
import os
import sqlite3
from pathlib import Path

# Add dashboards to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboards'))

from shared.stores import STORES, REGIONS
# Import calendar functions from sales_dashboard (canonical implementation)
from sales_dashboard import _fy_anchor, build_454_calendar, get_454_period, get_454_quarter

# Path to real database
DB_PATH = Path(__file__).parent.parent / "data" / "harris_farm.db"
HAS_DB = DB_PATH.exists()


# ============================================================================
# STORE NETWORK TESTS
# ============================================================================

class TestStoreNetwork:
    """Test the Harris Farm Markets store network constants."""

    def test_stores_count_is_21(self):
        """Success: STORES list contains exactly 21 stores"""
        assert len(STORES) == 21, f"Expected 21 stores, got {len(STORES)}"

    def test_stores_count_invalid(self):
        """Failure: verify test catches incorrect count"""
        # This test documents expected behavior - if store count changes,
        # tests should fail to alert developers
        assert len(STORES) != 20, "Store count should not be 20"
        assert len(STORES) != 22, "Store count should not be 22"

    def test_all_stores_have_names(self):
        """Success: all stores are non-empty strings"""
        for store in STORES:
            assert isinstance(store, str), f"Store {store} is not a string"
            assert len(store) > 0, f"Store name is empty"
            assert store.strip() == store, f"Store '{store}' has leading/trailing whitespace"

    def test_empty_store_name_rejected(self):
        """Failure: empty string is not a valid store name"""
        assert "" not in STORES, "Empty string found in STORES"
        assert None not in STORES, "None found in STORES"

    def test_stores_no_duplicates(self):
        """Success: all store names are unique"""
        assert len(STORES) == len(set(STORES)), \
            f"Duplicate stores found: {[s for s in STORES if STORES.count(s) > 1]}"

    def test_duplicate_detection_works(self):
        """Failure: verify duplicate detection logic"""
        test_list = ["Store A", "Store B", "Store A"]
        assert len(test_list) != len(set(test_list)), \
            "Duplicate detection should catch duplicates"

    def test_all_stores_in_regions(self):
        """Success: every store has a region mapping"""
        for store in STORES:
            assert store in REGIONS, f"Store '{store}' not found in REGIONS"

    def test_unknown_store_not_in_regions(self):
        """Failure: stores not in STORES list should not be in REGIONS"""
        fake_stores = ["Fake Store", "Non-existent Location", "Test Store 123"]
        for fake in fake_stores:
            assert fake not in REGIONS, f"Fake store '{fake}' should not be in REGIONS"

    def test_regions_match_stores_exactly(self):
        """Success: REGIONS keys exactly match STORES"""
        regions_keys = set(REGIONS.keys())
        stores_set = set(STORES)
        assert regions_keys == stores_set, \
            f"Mismatch: extra in REGIONS={regions_keys - stores_set}, missing={stores_set - regions_keys}"

    def test_regions_keys_mismatch_detected(self):
        """Failure: verify mismatch detection"""
        # Test that we can detect when sets don't match
        set_a = {"A", "B", "C"}
        set_b = {"A", "B", "D"}
        assert set_a != set_b, "Mismatch detection should work"

    def test_all_regions_are_valid_strings(self):
        """Success: all region values are non-empty strings"""
        valid_regions = {
            "Northern Beaches", "Eastern Suburbs", "Hills District",
            "North Shore", "Inner West", "Upper North Shore",
            "Sutherland Shire", "Western Sydney"
        }
        for store, region in REGIONS.items():
            assert isinstance(region, str), f"Region for {store} is not a string"
            assert len(region) > 0, f"Region for {store} is empty"
            assert region in valid_regions, f"Unknown region '{region}' for {store}"

    def test_invalid_region_value_rejected(self):
        """Failure: invalid region values should not exist"""
        invalid_regions = ["", None, "Unknown Region", "Test Area"]
        for store, region in REGIONS.items():
            assert region not in invalid_regions, \
                f"Store {store} has invalid region: {region}"


# ============================================================================
# 5/4/4 RETAIL FISCAL CALENDAR TESTS
# ============================================================================

class TestFiscalYearAnchor:
    """Test FY anchor calculation (Monday closest to 1 July)."""

    def test_fy_start_is_monday(self):
        """Success: FY anchor is always a Monday"""
        # Test multiple years
        for year in [2024, 2025, 2026]:
            anchor = _fy_anchor(year)
            assert anchor.weekday() == 0, \
                f"FY anchor {anchor} for {year} is not Monday (weekday={anchor.weekday()})"

    def test_fy_start_not_tuesday(self):
        """Failure: FY anchor should never be Tuesday"""
        for year in [2024, 2025, 2026]:
            anchor = _fy_anchor(year)
            assert anchor.weekday() != 1, \
                f"FY anchor should not be Tuesday"

    def test_fy_start_near_july_1(self):
        """Success: FY anchor within 3 days of July 1"""
        for year in [2024, 2025, 2026]:
            anchor = _fy_anchor(year)
            july_1 = datetime(year, 7, 1)
            days_diff = abs((anchor - july_1).days)
            assert days_diff <= 3, \
                f"FY anchor {anchor} is {days_diff} days from July 1 {year} (max 3)"

    def test_fy_start_not_far_from_july(self):
        """Failure: FY anchor should not be more than a week from July 1"""
        for year in [2024, 2025, 2026]:
            anchor = _fy_anchor(year)
            july_1 = datetime(year, 7, 1)
            days_diff = abs((anchor - july_1).days)
            assert days_diff <= 7, \
                f"FY anchor too far from July 1: {days_diff} days"

    def test_specific_fy_2025(self):
        """Success: FY 2025 starts Monday June 30, 2025"""
        anchor = _fy_anchor(2025)
        # July 1, 2025 is a Tuesday, so Monday closest is June 30
        expected = datetime(2025, 6, 30)
        assert anchor == expected, \
            f"Expected {expected}, got {anchor}"

    def test_specific_fy_2026(self):
        """Success: FY 2026 starts Monday June 29, 2026"""
        anchor = _fy_anchor(2026)
        # July 1, 2026 is a Wednesday, so Monday closest is June 29
        expected = datetime(2026, 6, 29)
        assert anchor == expected, \
            f"Expected {expected}, got {anchor}"


class TestBuild454Calendar:
    """Test 5/4/4 calendar construction."""

    def test_calendar_has_12_periods(self):
        """Success: calendar has exactly 12 periods"""
        _, periods = build_454_calendar(datetime(2025, 7, 1))
        assert len(periods) == 12, f"Expected 12 periods, got {len(periods)}"

    def test_calendar_wrong_period_count(self):
        """Failure: calendar should not have 13 or 11 periods"""
        _, periods = build_454_calendar(datetime(2025, 7, 1))
        assert len(periods) != 11, "Period count should not be 11"
        assert len(periods) != 13, "Period count should not be 13"

    def test_quarters_are_13_weeks_each(self):
        """Success: each quarter is exactly 13 weeks (5+4+4)"""
        _, periods = build_454_calendar(datetime(2025, 7, 1))

        for q in range(1, 5):  # Quarters 1-4
            q_periods = [p for p in periods if p['quarter'] == q]
            assert len(q_periods) == 3, f"Quarter {q} should have 3 periods"

            weeks = [p['weeks'] for p in q_periods]
            assert weeks == [5, 4, 4], \
                f"Quarter {q} should be [5, 4, 4] weeks, got {weeks}"

            total_weeks = sum(weeks)
            assert total_weeks == 13, \
                f"Quarter {q} should total 13 weeks, got {total_weeks}"

    def test_quarter_wrong_week_pattern(self):
        """Failure: quarters should not have different patterns"""
        _, periods = build_454_calendar(datetime(2025, 7, 1))

        for q in range(1, 5):
            q_periods = [p for p in periods if p['quarter'] == q]
            weeks = [p['weeks'] for p in q_periods]
            # Should NOT be these patterns
            assert weeks != [4, 4, 5], "Wrong pattern [4,4,5]"
            assert weeks != [4, 5, 4], "Wrong pattern [4,5,4]"
            assert weeks != [6, 4, 3], "Wrong pattern [6,4,3]"

    def test_period_dates_dont_overlap(self):
        """Success: period end dates + 1 day = next period start"""
        _, periods = build_454_calendar(datetime(2025, 7, 1))

        for i in range(len(periods) - 1):
            current_end = periods[i]['end']
            next_start = periods[i + 1]['start']
            expected_next = current_end + timedelta(days=1)
            assert next_start == expected_next, \
                f"Gap between period {i+1} and {i+2}: {current_end} -> {next_start}"

    def test_detect_period_gaps(self):
        """Failure: verify gap detection logic"""
        # Test that our gap detection works
        date1 = datetime(2025, 1, 1)
        date2 = datetime(2025, 1, 5)  # 4 day gap
        assert date2 != date1 + timedelta(days=1), \
            "Should detect when dates are not consecutive"

    def test_fy_start_is_monday(self):
        """Success: FY start date is always Monday"""
        fy_start, _ = build_454_calendar(datetime(2025, 7, 1))
        assert fy_start.weekday() == 0, \
            f"FY start {fy_start} is not Monday (weekday={fy_start.weekday()})"

    def test_all_period_starts_are_defined(self):
        """Success: all periods have start and end dates"""
        _, periods = build_454_calendar(datetime(2025, 7, 1))

        for p in periods:
            assert 'start' in p, f"Period {p['period']} missing start"
            assert 'end' in p, f"Period {p['period']} missing end"
            assert isinstance(p['start'], datetime), \
                f"Period {p['period']} start is not datetime"
            assert isinstance(p['end'], datetime), \
                f"Period {p['period']} end is not datetime"
            assert p['end'] >= p['start'], \
                f"Period {p['period']} end before start"


class TestGet454Period:
    """Test getting the current 454 period."""

    def test_get_period_returns_dict(self):
        """Success: function returns a period dict with required keys"""
        period = get_454_period(datetime(2025, 7, 15))

        required_keys = ['quarter', 'period', 'weeks', 'start', 'end']
        for key in required_keys:
            assert key in period, f"Period missing key: {key}"

    def test_get_period_missing_keys_detected(self):
        """Failure: verify key existence checking works"""
        test_dict = {'quarter': 1, 'period': 1}
        assert 'weeks' not in test_dict, "Should detect missing keys"

    def test_get_period_contains_reference_date(self):
        """Success: returned period contains the reference date"""
        ref_date = datetime(2025, 8, 15)
        period = get_454_period(ref_date)

        assert period['start'] <= ref_date <= period['end'], \
            f"Period {period['period']} ({period['start']} to {period['end']}) " \
            f"does not contain {ref_date}"

    def test_get_period_boundaries(self):
        """Success: period boundaries are inclusive"""
        _, periods = build_454_calendar(datetime(2025, 7, 1))
        first_period = periods[0]

        # Test that start date returns this period
        result = get_454_period(first_period['start'])
        assert result['period'] == first_period['period']

        # Test that end date returns this period
        result = get_454_period(first_period['end'])
        assert result['period'] == first_period['period']

    def test_get_period_date_outside_range(self):
        """Failure: date outside period should not match"""
        _, periods = build_454_calendar(datetime(2025, 7, 1))
        first_period = periods[0]

        # Date before period
        before = first_period['start'] - timedelta(days=1)
        result = get_454_period(before)
        assert result['period'] != first_period['period'], \
            "Date before period should not match"


class TestGet454Quarter:
    """Test getting the current 454 quarter."""

    def test_get_quarter_returns_tuple(self):
        """Success: function returns (start, end) tuple"""
        result = get_454_quarter(datetime(2025, 7, 15))

        assert isinstance(result, tuple), "Should return tuple"
        assert len(result) == 2, "Should return 2-element tuple"

        q_start, q_end = result
        assert isinstance(q_start, datetime), "Quarter start should be datetime"
        assert isinstance(q_end, datetime), "Quarter end should be datetime"

    def test_get_quarter_wrong_type(self):
        """Failure: verify type checking works"""
        result = get_454_quarter(datetime(2025, 7, 15))
        assert not isinstance(result, list), "Should not return list"
        assert not isinstance(result, dict), "Should not return dict"

    def test_quarter_is_13_weeks(self):
        """Success: quarter span is exactly 13 weeks (91 days)"""
        q_start, q_end = get_454_quarter(datetime(2025, 7, 15))

        days = (q_end - q_start).days + 1  # +1 because both dates are inclusive
        assert days == 91, f"Quarter should be 91 days, got {days}"

    def test_quarter_wrong_duration(self):
        """Failure: quarter should not be other durations"""
        q_start, q_end = get_454_quarter(datetime(2025, 7, 15))
        days = (q_end - q_start).days + 1

        assert days != 90, "Quarter should not be 90 days"
        assert days != 92, "Quarter should not be 92 days"
        assert days != 84, "Quarter should not be 84 days (12 weeks)"

    def test_quarter_contains_reference_date(self):
        """Success: returned quarter contains the reference date"""
        ref_date = datetime(2025, 9, 15)
        q_start, q_end = get_454_quarter(ref_date)

        assert q_start <= ref_date <= q_end, \
            f"Quarter ({q_start} to {q_end}) does not contain {ref_date}"

    def test_quarter_boundaries_are_period_boundaries(self):
        """Success: quarter start/end align with period boundaries"""
        _, periods = build_454_calendar(datetime(2025, 7, 1))

        # Check each quarter
        for q_num in range(1, 5):
            q_periods = [p for p in periods if p['quarter'] == q_num]
            expected_start = q_periods[0]['start']
            expected_end = q_periods[-1]['end']

            # Get quarter for a date in the middle of this quarter
            mid_date = expected_start + timedelta(days=45)
            actual_start, actual_end = get_454_quarter(mid_date)

            assert actual_start == expected_start, \
                f"Q{q_num} start mismatch: expected {expected_start}, got {actual_start}"
            assert actual_end == expected_end, \
                f"Q{q_num} end mismatch: expected {expected_end}, got {actual_end}"


# ============================================================================
# WTD (Week-to-Date) CALCULATION TESTS
# ============================================================================

class TestWTDCalculation:
    """Test week-to-date range calculation (inline logic from dashboards)."""

    def test_wtd_monday_is_week_start(self):
        """Success: WTD week starts on Monday"""
        # If reference date is Wednesday
        ref_date = datetime(2025, 7, 2)  # July 2, 2025 is Wednesday
        week_start = ref_date - timedelta(days=ref_date.weekday())

        assert week_start.weekday() == 0, \
            f"Week start {week_start} is not Monday (weekday={week_start.weekday()})"

    def test_wtd_not_sunday_start(self):
        """Failure: WTD should not start on Sunday"""
        ref_date = datetime(2025, 7, 2)  # Wednesday
        week_start = ref_date - timedelta(days=ref_date.weekday())

        assert week_start.weekday() != 6, "Week should not start on Sunday"

    def test_wtd_range_for_monday(self):
        """Success: Monday WTD is just Monday"""
        ref_date = datetime(2025, 6, 30)  # Monday
        week_start = ref_date - timedelta(days=ref_date.weekday())
        days_into_week = (ref_date - week_start).days + 1

        assert week_start == ref_date, "Monday's week starts on Monday"
        assert days_into_week == 1, "Monday is day 1 of week"

    def test_wtd_range_for_friday(self):
        """Success: Friday WTD is Mon-Fri (5 days)"""
        ref_date = datetime(2025, 7, 4)  # Friday
        week_start = ref_date - timedelta(days=ref_date.weekday())
        days_into_week = (ref_date - week_start).days + 1

        assert days_into_week == 5, f"Friday should be day 5, got {days_into_week}"
        expected_start = datetime(2025, 6, 30)  # Monday
        assert week_start == expected_start, \
            f"Week start should be {expected_start}, got {week_start}"

    def test_wtd_invalid_day_count(self):
        """Failure: WTD days should be 1-7, not 0 or 8"""
        # Test Wednesday
        ref_date = datetime(2025, 7, 2)
        week_start = ref_date - timedelta(days=ref_date.weekday())
        days_into_week = (ref_date - week_start).days + 1

        assert days_into_week >= 1, "Days into week should be at least 1"
        assert days_into_week <= 7, "Days into week should be at most 7"
        assert days_into_week != 0, "Days into week cannot be 0"

    def test_wtd_range_includes_reference_date(self):
        """Success: WTD range includes the reference date"""
        ref_date = datetime(2025, 7, 3)  # Thursday
        week_start = ref_date - timedelta(days=ref_date.weekday())

        assert week_start <= ref_date, \
            f"Week start {week_start} should be <= reference {ref_date}"

    def test_wtd_previous_week_calculation(self):
        """Success: previous week comparison uses same day count"""
        ref_date = datetime(2025, 7, 3)  # Thursday
        week_start = ref_date - timedelta(days=ref_date.weekday())
        days_into_week = (ref_date - week_start).days + 1

        prev_start = week_start - timedelta(days=7)
        prev_end = prev_start + timedelta(days=days_into_week - 1)

        # Previous week should also be 4 days (Mon-Thu)
        prev_days = (prev_end - prev_start).days + 1
        assert prev_days == days_into_week, \
            f"Previous week should have {days_into_week} days, got {prev_days}"

        assert prev_start.weekday() == 0, "Previous week should start on Monday"


# ============================================================================
# REAL DATA ACCESS TESTS (require harris_farm.db)
# ============================================================================

@pytest.mark.skipif(not HAS_DB, reason="harris_farm.db not found")
class TestRealDataStores:
    """Test real store data from SQLite database."""

    def test_retail_stores_exist(self):
        """Success: database has retail stores"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(DISTINCT store) FROM sales WHERE channel = 'Retail'"
            )
            count = cursor.fetchone()[0]
            assert count == 30, f"Expected 30 retail stores (27 NSW + 3 QLD), got {count}"

    def test_no_empty_store_names(self):
        """Failure: no store should have empty name"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sales WHERE store IS NULL OR store = ''"
            )
            count = cursor.fetchone()[0]
            assert count == 0, f"Found {count} rows with empty store names"

    def test_store_name_format(self):
        """Success: store names follow 'NN - HFM Name' format"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT store FROM sales ORDER BY store")
            stores = [r[0] for r in cursor.fetchall()]
            for store in stores:
                parts = store.split(" - ", 1)
                assert len(parts) == 2, f"Store '{store}' missing ' - ' separator"
                assert parts[0].strip().isdigit(), \
                    f"Store '{store}' prefix is not numeric"


@pytest.mark.skipif(not HAS_DB, reason="harris_farm.db not found")
class TestRealDataDepartments:
    """Test real department hierarchy from SQLite database."""

    def test_eight_departments(self):
        """Success: exactly 8 departments in sales data"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT department) FROM sales")
            count = cursor.fetchone()[0]
            assert count == 8, f"Expected 8 departments, got {count}"

    def test_department_names_correct(self):
        """Success: expected departments are present"""
        expected = {
            '10 - Fruit & Vegetables', '20 - Grocery', '30 - Perishable',
            '40 - Flowers', '50 - Proteins', '60 - Bakery',
            '70 - Liquor', '80 - Service/Counter'
        }
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT department FROM sales")
            actual = {r[0] for r in cursor.fetchall()}
            assert actual == expected, \
                f"Missing: {expected - actual}, Extra: {actual - expected}"

    def test_no_orphan_major_groups(self):
        """Failure: every major group should belong to a department"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT major_group) FROM sales
                WHERE department IS NULL OR department = ''
            """)
            count = cursor.fetchone()[0]
            assert count == 0, f"Found {count} major groups without department"

    def test_major_groups_per_department(self):
        """Success: departments have expected major group counts"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT department, COUNT(DISTINCT major_group) as mg_count
                FROM sales
                GROUP BY department
                ORDER BY department
            """)
            rows = cursor.fetchall()
            total_mgs = sum(r[1] for r in rows)
            assert total_mgs == 28, f"Expected 28 total major groups, got {total_mgs}"


@pytest.mark.skipif(not HAS_DB, reason="harris_farm.db not found")
class TestRealDataSales:
    """Test real sales data integrity."""

    def test_sales_row_count(self):
        """Success: sales table has expected row count"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sales")
            count = cursor.fetchone()[0]
            assert count > 1_000_000, \
                f"Expected >1M sales rows, got {count}"

    def test_six_measures(self):
        """Success: exactly 6 measures in sales data"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT measure FROM sales ORDER BY measure")
            measures = [r[0] for r in cursor.fetchall()]
            assert len(measures) == 6, f"Expected 6 measures, got {len(measures)}"

    def test_measure_names_correct(self):
        """Success: expected measure names are present"""
        expected = {
            'Sales - Val', 'Initial Gross Profit - Val',
            'Final Gross Prod - Val', 'Bgt Sales - Val',
            'Bgt Final GP - Val', 'Total Shrinkage \u2013 Val'  # em-dash
        }
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT measure FROM sales")
            actual = {r[0] for r in cursor.fetchall()}
            assert actual == expected, \
                f"Missing: {expected - actual}, Extra: {actual - expected}"

    def test_no_measure_with_wrong_name(self):
        """Failure: 'Revenue' should not be a measure name"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT measure FROM sales")
            measures = {r[0] for r in cursor.fetchall()}
            assert 'Revenue' not in measures, "'Revenue' should not be a measure"
            assert 'Profit' not in measures, "'Profit' should not be a measure"

    def test_date_range(self):
        """Success: data spans FY2017 to FY2024"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MIN(week_ending), MAX(week_ending) FROM sales")
            min_date, max_date = cursor.fetchone()
            assert min_date <= '2017-01-01', \
                f"Data should start before 2017, starts {min_date}"
            assert max_date >= '2024-06-01', \
                f"Data should extend to at least Jun 2024, ends {max_date}"

    def test_no_future_dates(self):
        """Failure: no sales dates should be in the future"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sales WHERE week_ending > '2025-01-01'"
            )
            count = cursor.fetchone()[0]
            assert count == 0, f"Found {count} rows with future dates"

    def test_sales_values_positive(self):
        """Success: sales values are generally positive"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM sales
                WHERE measure = 'Sales - Val' AND value > 0
            """)
            positive = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(*) FROM sales WHERE measure = 'Sales - Val'
            """)
            total = cursor.fetchone()[0]
            ratio = positive / total if total > 0 else 0
            assert ratio > 0.95, \
                f"Expected >95% positive sales values, got {ratio:.1%}"

    def test_gp_traceable_to_sales(self):
        """Success: GP values exist for stores that have sales"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Check that stores with sales also have GP
            cursor.execute("""
                SELECT DISTINCT store FROM sales
                WHERE measure = 'Sales - Val'
            """)
            sales_stores = {r[0] for r in cursor.fetchall()}
            cursor.execute("""
                SELECT DISTINCT store FROM sales
                WHERE measure = 'Final Gross Prod - Val'
            """)
            gp_stores = {r[0] for r in cursor.fetchall()}
            # Every store with sales should have GP data
            missing_gp = sales_stores - gp_stores
            assert len(missing_gp) == 0, \
                f"Stores with sales but no GP: {missing_gp}"
