"""
Harris Farm Hub — Fiscal Calendar Converter
One-time script to convert Financial Calendar Excel to Parquet for DuckDB.

Usage:
    python3 scripts/convert_fiscal_calendar.py

Source: Financial_Calendar_Exported_2025-05-29.xlsx (4,018 days, 45 columns)
Output: data/fiscal_calendar_daily.parquet
"""

import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

EXCEL_PATH = (
    Path.home() / "Desktop" / "Working files"
    / "Financial_Calendar_Exported_2025-05-29.xlsx"
)

OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_PATH = OUTPUT_DIR / "fiscal_calendar_daily.parquet"

SHEET_NAME = "in"

REQUIRED_COLUMNS = [
    "Time_ID", "TheDate", "PreviousDay",
    "DayOfWeekNo", "DayOfWeekName", "DayOfWeekShortName",
    "BusinessDay", "Weekend",
    "LastDayOfWeek", "LastDayOfCalMonth", "LastDayOfFinMonth",
    "LastDayOfCalQuarter", "LastDayOfFinQuarter",
    "LastDayOfCalYear", "LastDayOfFinYear",
    "SeasonName",
    "CalDayOfYearNo", "CalDayOfMonthNo", "CalDayOfQuarterNo",
    "CalWeekOfYearNo", "CalWeekOfYearName",
    "CalMonthOfYearNo", "CalMonthOfYearName", "CalMonthOfYearShortName",
    "CalMonthAndYearName",
    "CalQuarterOfYearNo", "CalQuarterOfYearName", "CalYear",
    "FinDayOfYearNo", "FinDayOfMonthNo", "FinDayOfQuarterNo",
    "FinWeekOfYearNo", "FinWeekOfYearName",
    "FinMonthOfYearNo", "FinMonthOfYearName", "FinMonthOfYearShortName",
    "FinMonthAndYearName",
    "FinQuarterOfYearNo", "FinQuarterOfYearName", "FinYear",
    "CalWeekStartDate", "CalWeekEndDate",
    "FinWeekStartDate", "FinWeekEndDate",
]


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def validate(df: pd.DataFrame) -> list:
    """Validate fiscal calendar DataFrame. Returns list of errors (empty = OK)."""
    errors = []

    # Column check
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        errors.append(f"Missing columns: {missing}")

    # Row count
    if len(df) < 3_500 or len(df) > 5_000:
        errors.append(f"Unexpected row count: {len(df):,} (expected ~4,018)")

    # Null check
    total_nulls = df[REQUIRED_COLUMNS].isnull().sum().sum()
    if total_nulls > 0:
        null_cols = df[REQUIRED_COLUMNS].isnull().sum()
        bad = null_cols[null_cols > 0]
        errors.append(f"Nulls found: {dict(bad)}")

    # Unique dates
    dupes = df["TheDate"].duplicated().sum()
    if dupes > 0:
        errors.append(f"{dupes} duplicate TheDate values")

    # FY range
    fin_years = sorted(df["FinYear"].unique())
    if fin_years[0] > 2017 or fin_years[-1] < 2026:
        errors.append(f"FY range unexpected: {fin_years[0]}-{fin_years[-1]}")

    # 5-4-4 pattern check (verify non-53-week years have 364 days)
    fy_days = df.groupby("FinYear")["TheDate"].count()
    for fy, days in fy_days.items():
        if days not in (364, 371):
            errors.append(f"FY{fy} has {days} days (expected 364 or 371)")

    # Week boundaries (should be Mon=1 through Sun=7)
    dow_range = df["DayOfWeekNo"].unique()
    if set(dow_range) != {1, 2, 3, 4, 5, 6, 7}:
        errors.append(f"DayOfWeekNo values unexpected: {sorted(dow_range)}")

    return errors


# ---------------------------------------------------------------------------
# CONVERSION
# ---------------------------------------------------------------------------

def convert():
    """Read Excel, validate, write Parquet."""
    print(f"Reading: {EXCEL_PATH}")
    if not EXCEL_PATH.exists():
        print(f"ERROR: File not found: {EXCEL_PATH}")
        sys.exit(1)

    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
    print(f"  Rows: {len(df):,}")
    print(f"  Columns: {len(df.columns)}")

    # Validate
    errors = validate(df)
    if errors:
        print("\nVALIDATION ERRORS:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("  Validation: PASSED")

    # Cast TheDate to timezone-naive datetime for clean DuckDB DATE joins
    df["TheDate"] = pd.to_datetime(df["TheDate"]).dt.tz_localize(None)

    # Cast date columns to timezone-naive
    for col in ["CalWeekStartDate", "CalWeekEndDate",
                "FinWeekStartDate", "FinWeekEndDate",
                "CalMonthAndYearName", "FinMonthAndYearName"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.tz_localize(None)

    # Ensure integer columns are int64
    for col in ["Time_ID", "PreviousDay", "DayOfWeekNo",
                "CalDayOfYearNo", "CalDayOfMonthNo", "CalDayOfQuarterNo",
                "CalWeekOfYearNo", "CalMonthOfYearNo", "CalQuarterOfYearNo", "CalYear",
                "FinDayOfYearNo", "FinDayOfMonthNo", "FinDayOfQuarterNo",
                "FinWeekOfYearNo", "FinMonthOfYearNo", "FinQuarterOfYearNo", "FinYear"]:
        if col in df.columns:
            df[col] = df[col].astype("int64")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write parquet
    df.to_parquet(OUTPUT_PATH, index=False, compression="snappy")
    print(f"\nWritten: {OUTPUT_PATH}")
    print(f"  Size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")

    # Summary stats
    print(f"\n--- Summary ---")
    print(f"Total days: {len(df):,}")
    print(f"Date range: {df['TheDate'].min().strftime('%Y-%m-%d')} to "
          f"{df['TheDate'].max().strftime('%Y-%m-%d')}")

    print(f"\nBy Fiscal Year:")
    fy_days = df.groupby("FinYear")["TheDate"].agg(["count", "min", "max"])
    for fy, row in fy_days.iterrows():
        weeks = row["count"] // 7
        marker = " (53-week)" if row["count"] == 371 else ""
        print(f"  FY{fy}: {row['count']} days ({weeks} weeks){marker}  "
              f"{row['min'].strftime('%Y-%m-%d')} to {row['max'].strftime('%Y-%m-%d')}")

    # 5-4-4 pattern verification
    print(f"\n5-4-4 Pattern (FY2026):")
    fy26 = df[df["FinYear"] == 2026]
    for m in range(1, 13):
        month_data = fy26[fy26["FinMonthOfYearNo"] == m]
        if len(month_data) > 0:
            name = month_data["FinMonthOfYearName"].iloc[0]
            weeks = len(month_data) // 7
            print(f"  Month {m:2d} ({name:>10s}): {weeks} weeks, {len(month_data)} days")

    # 53-week years
    long_years = [fy for fy, days in df.groupby("FinYear")["TheDate"].count().items()
                  if days == 371]
    print(f"\n53-week years: {long_years if long_years else 'none'}")

    null_counts = df.isnull().sum()
    non_zero = null_counts[null_counts > 0]
    if len(non_zero) > 0:
        print(f"\nNull values:")
        for col, count in non_zero.items():
            print(f"  {col}: {count}")
    else:
        print(f"\nNull values: none")

    print(f"\nDone. Fiscal calendar ready for DuckDB integration.")


if __name__ == "__main__":
    convert()
