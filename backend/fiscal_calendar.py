"""
Harris Farm Hub — Fiscal Calendar Module
Loads the 4,018-day fiscal calendar from parquet and provides period
lookups, date range resolution, and comparison utilities.

Source: Financial_Calendar_Exported_2025-05-29.xlsx → data/fiscal_calendar_daily.parquet
Calendar: 5-4-4 retail calendar, FY2016-FY2026 (11 years)
Pattern: 5-week first month of quarter, 4-week second and third.
Weeks: Monday through Sunday. FY starts Monday nearest July 1.
53-week years: FY2016 and FY2022.
"""

import logging
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

import pandas as pd

logger = logging.getLogger("hub_api")

FISCAL_PARQUET = Path(__file__).parent.parent / "data" / "fiscal_calendar_daily.parquet"

# Fiscal years with 53 weeks (371 days)
LONG_YEARS = {2016, 2022}


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_fiscal_calendar() -> pd.DataFrame:
    """Load fiscal calendar parquet into a cached DataFrame.

    Returns DataFrame with 4,018 rows x 45 columns.
    TheDate is timezone-naive datetime for clean DuckDB joins.
    Cached in memory (~1 MB) after first call.
    """
    if not FISCAL_PARQUET.exists():
        logger.warning("Fiscal calendar not found: %s", FISCAL_PARQUET)
        return pd.DataFrame()

    df = pd.read_parquet(FISCAL_PARQUET)
    df["TheDate"] = pd.to_datetime(df["TheDate"])
    return df


# ---------------------------------------------------------------------------
# FISCAL YEAR FUNCTIONS
# ---------------------------------------------------------------------------

def get_fiscal_years() -> list:
    """Return list of available fiscal years as integers.

    Example: [2016, 2017, ..., 2026]
    """
    df = load_fiscal_calendar()
    if df.empty:
        return []
    return sorted(df["FinYear"].unique().tolist())


def get_fy_date_range(fin_year: int) -> tuple:
    """Return (start_date_str, end_date_str) for a fiscal year.

    Dates are inclusive. End date is the last day of the FY.
    Returns YYYY-MM-DD strings for direct use in SQL queries.
    Returns (None, None) if FY not found.
    """
    df = load_fiscal_calendar()
    if df.empty:
        return (None, None)

    fy_data = df[df["FinYear"] == fin_year]
    if fy_data.empty:
        return (None, None)

    start = fy_data["TheDate"].min()
    end = fy_data["TheDate"].max()
    # Return end + 1 day for exclusive range (standard SQL pattern)
    end_exclusive = end + pd.Timedelta(days=1)
    return (start.strftime("%Y-%m-%d"), end_exclusive.strftime("%Y-%m-%d"))


def is_long_year(fin_year: int) -> bool:
    """Return True if the fiscal year has 53 weeks (371 days)."""
    return fin_year in LONG_YEARS


# ---------------------------------------------------------------------------
# PERIOD FUNCTIONS
# ---------------------------------------------------------------------------

def get_fiscal_months(fin_year: int) -> list:
    """Return fiscal months for a given FY.

    Returns list of dicts with: month_no, name, short_name,
    weeks, days, start, end (YYYY-MM-DD strings).
    """
    df = load_fiscal_calendar()
    if df.empty:
        return []

    fy_data = df[df["FinYear"] == fin_year]
    if fy_data.empty:
        return []

    result = []
    for month_no in sorted(fy_data["FinMonthOfYearNo"].unique()):
        month_data = fy_data[fy_data["FinMonthOfYearNo"] == month_no]
        name = month_data["FinMonthOfYearName"].iloc[0]
        short_name = month_data["FinMonthOfYearShortName"].iloc[0]
        start = month_data["TheDate"].min()
        end = month_data["TheDate"].max()
        weeks = len(month_data) // 7
        end_exclusive = end + pd.Timedelta(days=1)
        result.append({
            "month_no": int(month_no),
            "name": str(name),
            "short_name": str(short_name),
            "weeks": int(weeks),
            "days": int(len(month_data)),
            "start": start.strftime("%Y-%m-%d"),
            "end": end_exclusive.strftime("%Y-%m-%d"),
        })
    return result


def get_fiscal_quarters(fin_year: int) -> list:
    """Return fiscal quarters for a given FY.

    Returns list of dicts with: quarter_no, name, days, start, end.
    """
    df = load_fiscal_calendar()
    if df.empty:
        return []

    fy_data = df[df["FinYear"] == fin_year]
    if fy_data.empty:
        return []

    result = []
    for q_no in sorted(fy_data["FinQuarterOfYearNo"].unique()):
        q_data = fy_data[fy_data["FinQuarterOfYearNo"] == q_no]
        name = q_data["FinQuarterOfYearName"].iloc[0]
        start = q_data["TheDate"].min()
        end = q_data["TheDate"].max()
        end_exclusive = end + pd.Timedelta(days=1)
        result.append({
            "quarter_no": int(q_no),
            "name": str(name),
            "days": int(len(q_data)),
            "start": start.strftime("%Y-%m-%d"),
            "end": end_exclusive.strftime("%Y-%m-%d"),
        })
    return result


def get_fiscal_weeks(fin_year: int) -> list:
    """Return fiscal weeks for a given FY.

    Returns list of dicts with: week_no, name, start, end.
    """
    df = load_fiscal_calendar()
    if df.empty:
        return []

    fy_data = df[df["FinYear"] == fin_year]
    if fy_data.empty:
        return []

    result = []
    for w_no in sorted(fy_data["FinWeekOfYearNo"].unique()):
        w_data = fy_data[fy_data["FinWeekOfYearNo"] == w_no]
        name = w_data["FinWeekOfYearName"].iloc[0]
        start = w_data["TheDate"].min()
        end = w_data["TheDate"].max()
        end_exclusive = end + pd.Timedelta(days=1)
        result.append({
            "week_no": int(w_no),
            "name": str(name),
            "start": start.strftime("%Y-%m-%d"),
            "end": end_exclusive.strftime("%Y-%m-%d"),
        })
    return result


# ---------------------------------------------------------------------------
# CURRENT PERIOD
# ---------------------------------------------------------------------------

def get_current_fiscal_period() -> dict:
    """Return the fiscal period context for today's date.

    Returns dict with: fin_year, quarter_no, quarter_name,
    month_no, month_name, week_no, week_name, day_of_week,
    business_day, season. Returns empty dict if calendar unavailable.
    """
    df = load_fiscal_calendar()
    if df.empty:
        return {}

    today = pd.Timestamp(date.today())
    row = df[df["TheDate"] == today]

    if row.empty:
        # Today is outside calendar range
        return {"error": f"Date {today.strftime('%Y-%m-%d')} not in fiscal calendar"}

    r = row.iloc[0]
    return {
        "date": today.strftime("%Y-%m-%d"),
        "fin_year": int(r["FinYear"]),
        "quarter_no": int(r["FinQuarterOfYearNo"]),
        "quarter_name": str(r["FinQuarterOfYearName"]),
        "month_no": int(r["FinMonthOfYearNo"]),
        "month_name": str(r["FinMonthOfYearName"]),
        "week_no": int(r["FinWeekOfYearNo"]),
        "week_name": str(r["FinWeekOfYearName"]),
        "day_of_week": str(r["DayOfWeekName"]),
        "business_day": str(r["BusinessDay"]),
        "season": str(r["SeasonName"]),
        "is_long_year": is_long_year(int(r["FinYear"])),
    }


# ---------------------------------------------------------------------------
# COMPARISON UTILITIES
# ---------------------------------------------------------------------------

def get_comparison_range(period_type: str, period_value, fin_year: int) -> dict:
    """Return current and prior period date ranges for comparisons.

    Args:
        period_type: "fy", "quarter", "month", "week"
        period_value: quarter/month/week number (ignored for "fy")
        fin_year: the fiscal year

    Returns dict with:
        current: {start, end, label}
        prior: {start, end, label} or None
        caveats: list of str
    """
    caveats = []
    prior_year = fin_year - 1

    # Current period
    if period_type == "fy":
        start, end = get_fy_date_range(fin_year)
        label = f"FY{fin_year}"
        prior_start, prior_end = get_fy_date_range(prior_year)
        prior_label = f"FY{prior_year}"
    elif period_type == "quarter":
        quarters = get_fiscal_quarters(fin_year)
        q = next((q for q in quarters if q["quarter_no"] == period_value), None)
        if not q:
            return {"current": None, "prior": None, "caveats": [f"Q{period_value} not found in FY{fin_year}"]}
        start, end, label = q["start"], q["end"], q["name"]
        prior_quarters = get_fiscal_quarters(prior_year)
        pq = next((q for q in prior_quarters if q["quarter_no"] == period_value), None)
        prior_start = pq["start"] if pq else None
        prior_end = pq["end"] if pq else None
        prior_label = pq["name"] if pq else None
    elif period_type == "month":
        months = get_fiscal_months(fin_year)
        m = next((m for m in months if m["month_no"] == period_value), None)
        if not m:
            return {"current": None, "prior": None, "caveats": [f"Month {period_value} not found in FY{fin_year}"]}
        start, end, label = m["start"], m["end"], f"{m['name']} FY{fin_year}"
        prior_months = get_fiscal_months(prior_year)
        pm = next((m for m in prior_months if m["month_no"] == period_value), None)
        prior_start = pm["start"] if pm else None
        prior_end = pm["end"] if pm else None
        prior_label = f"{pm['name']} FY{prior_year}" if pm else None
    elif period_type == "week":
        weeks = get_fiscal_weeks(fin_year)
        w = next((w for w in weeks if w["week_no"] == period_value), None)
        if not w:
            return {"current": None, "prior": None, "caveats": [f"Week {period_value} not found in FY{fin_year}"]}
        start, end, label = w["start"], w["end"], f"{w['name']} FY{fin_year}"
        # Week 53 caveat
        if period_value == 53:
            caveats.append("Week 53 only exists in 53-week years (FY2016, FY2022). No prior year comparator available.")
            return {
                "current": {"start": start, "end": end, "label": label},
                "prior": None,
                "caveats": caveats,
            }
        prior_weeks = get_fiscal_weeks(prior_year)
        pw = next((w for w in prior_weeks if w["week_no"] == period_value), None)
        prior_start = pw["start"] if pw else None
        prior_end = pw["end"] if pw else None
        prior_label = f"{pw['name']} FY{prior_year}" if pw else None
    else:
        return {"current": None, "prior": None, "caveats": [f"Unknown period type: {period_type}"]}

    # 53-week year caveats
    if is_long_year(fin_year) and not is_long_year(prior_year):
        caveats.append(f"FY{fin_year} is a 53-week year; FY{prior_year} is 52 weeks. Week 53 excluded from comparisons.")
    elif not is_long_year(fin_year) and is_long_year(prior_year):
        caveats.append(f"FY{prior_year} was a 53-week year; FY{fin_year} is 52 weeks. Week 53 excluded from comparisons.")

    current = {"start": start, "end": end, "label": label} if start else None
    prior = {"start": prior_start, "end": prior_end, "label": prior_label} if prior_start else None

    return {
        "current": current,
        "prior": prior,
        "caveats": caveats,
    }


# ---------------------------------------------------------------------------
# STATISTICS
# ---------------------------------------------------------------------------

def fiscal_calendar_stats() -> dict:
    """Return fiscal calendar summary statistics."""
    df = load_fiscal_calendar()
    if df.empty:
        return {
            "available": False,
            "source": str(FISCAL_PARQUET),
            "message": "Fiscal calendar parquet not found",
        }

    return {
        "available": True,
        "source": str(FISCAL_PARQUET),
        "total_days": len(df),
        "fiscal_years": sorted(df["FinYear"].unique().tolist()),
        "date_range": {
            "start": df["TheDate"].min().strftime("%Y-%m-%d"),
            "end": df["TheDate"].max().strftime("%Y-%m-%d"),
        },
        "long_years": sorted(list(LONG_YEARS)),
        "calendar_pattern": "5-4-4",
        "week_boundaries": "Monday-Sunday",
    }
