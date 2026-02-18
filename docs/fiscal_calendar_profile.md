# Fiscal Calendar Structure Report

**Source:** `Financial_Calendar_Exported_2025-05-29.xlsx` (sheet: `in`)
**Generated:** 2026-02-15
**Status:** Profiling complete, ready for integration

---

## 1. Overview

| Attribute | Value |
|-----------|-------|
| **Rows** | 4,018 (daily granularity) |
| **Columns** | 45 |
| **Date range** | 2015-06-29 to 2026-06-28 |
| **Fiscal years** | FY2016 through FY2026 (11 years) |
| **Nulls** | Zero across all 4,018 rows and 45 columns |
| **File size** | 836 KB |

**vs Existing calendar:** The current `fiscal_calendar` table in harris_farm.db has 626 weekly rows with 11 columns (FY2015-FY2026). The new Excel file provides **day-level granularity** with **45 columns** of attributes — a significant upgrade.

---

## 2. Fiscal Year Structure

Harris Farm uses a **5-4-4 retail calendar** with fiscal years running approximately July 1 to June 30.

| Rule | Detail |
|------|--------|
| FY start | Monday nearest to July 1 |
| FY end | Sunday nearest to June 30 |
| Standard year | 364 days = 52 weeks |
| Leap years | 371 days = 53 weeks (FY2016, FY2022) |
| Week boundaries | Monday through Sunday |

### Fiscal Year Dates

| FY | Days | Weeks | Start | End |
|----|------|-------|-------|-----|
| FY2016 | 371 | 53 | 2015-06-29 | 2016-07-03 |
| FY2017 | 364 | 52 | 2016-07-04 | 2017-07-02 |
| FY2018 | 364 | 52 | 2017-07-03 | 2018-07-01 |
| FY2019 | 364 | 52 | 2018-07-02 | 2019-06-30 |
| FY2020 | 364 | 52 | 2019-07-01 | 2020-06-28 |
| FY2021 | 364 | 52 | 2020-06-29 | 2021-06-27 |
| FY2022 | 371 | 53 | 2021-06-28 | 2022-07-03 |
| FY2023 | 364 | 52 | 2022-07-04 | 2023-07-02 |
| FY2024 | 364 | 52 | 2023-07-03 | 2024-06-30 |
| FY2025 | 364 | 52 | 2024-07-01 | 2025-06-29 |
| FY2026 | 364 | 52 | 2025-06-30 | 2026-06-28 |

---

## 3. Month Pattern (5-4-4)

Each quarter has exactly **13 weeks / 91 days**, split as:

| Position | Weeks | Days |
|----------|-------|------|
| 1st month of quarter | 5 | 35 |
| 2nd month of quarter | 4 | 28 |
| 3rd month of quarter | 4 | 28 |

### FY2026 Financial Months

| Month # | Name | Weeks | Days | Start | End |
|---------|------|-------|------|-------|-----|
| 1 | July | 5 | 35 | 2025-06-30 | 2025-08-03 |
| 2 | August | 4 | 28 | 2025-08-04 | 2025-08-31 |
| 3 | September | 4 | 28 | 2025-09-01 | 2025-09-28 |
| 4 | October | 5 | 35 | 2025-09-29 | 2025-11-02 |
| 5 | November | 4 | 28 | 2025-11-03 | 2025-11-30 |
| 6 | December | 4 | 28 | 2025-12-01 | 2025-12-28 |
| 7 | January | 5 | 35 | 2025-12-29 | 2026-02-01 |
| 8 | February | 4 | 28 | 2026-02-02 | 2026-03-01 |
| 9 | March | 4 | 28 | 2026-03-02 | 2026-03-29 |
| 10 | April | 5 | 35 | 2026-03-30 | 2026-05-03 |
| 11 | May | 4 | 28 | 2026-05-04 | 2026-05-31 |
| 12 | June | 4 | 28 | 2026-06-01 | 2026-06-28 |

**Important:** Financial month names do NOT align with Gregorian months. "Financial July 2026" runs 2025-06-30 to 2025-08-03, not calendar July 1-31.

---

## 4. Quarter Structure (FY2026)

| Quarter | Months | Days | Start | End |
|---------|--------|------|-------|-----|
| Q1 | Jul, Aug, Sep | 91 | 2025-06-30 | 2025-09-28 |
| Q2 | Oct, Nov, Dec | 91 | 2025-09-29 | 2025-12-28 |
| Q3 | Jan, Feb, Mar | 91 | 2025-12-29 | 2026-03-29 |
| Q4 | Apr, May, Jun | 91 | 2026-03-30 | 2026-06-28 |

---

## 5. Column Inventory (45 columns)

### Identity & Date Keys (3)
| Column | Type | Description |
|--------|------|-------------|
| `Time_ID` | int64 | YYYYMMDD integer key (unique per day) |
| `TheDate` | datetime | The actual date |
| `PreviousDay` | int64 | Previous day's Time_ID |

### Day-of-Week Attributes (4)
| Column | Type | Values |
|--------|------|--------|
| `DayOfWeekNo` | int64 | 1 (Mon) - 7 (Sun) |
| `DayOfWeekName` | string | Monday - Sunday |
| `DayOfWeekShortName` | string | Mon - Sun |
| `BusinessDay` | string | Y/N (Mon-Fri = Y) |
| `Weekend` | string | Y/N (Sat-Sun = Y) |

### Period Boundary Flags (7)
All Y/N flags indicating if this day is the last day of a given period:
- `LastDayOfWeek`, `LastDayOfCalMonth`, `LastDayOfFinMonth`
- `LastDayOfCalQuarter`, `LastDayOfFinQuarter`
- `LastDayOfCalYear`, `LastDayOfFinYear`

### Season (1)
| Column | Values |
|--------|--------|
| `SeasonName` | Autumn, Spring, Summer, Winter |

### Calendar Period Columns (13)
| Column | Description |
|--------|-------------|
| `CalDayOfYearNo` | 1-366 |
| `CalDayOfMonthNo` | 1-31 |
| `CalDayOfQuarterNo` | 1-92 |
| `CalWeekOfYearNo` | 1-53 |
| `CalWeekOfYearName` | "Week-01" to "Week-53" |
| `CalMonthOfYearNo` | 1-12 (Jan=1) |
| `CalMonthOfYearName` | January - December |
| `CalMonthOfYearShortName` | Jan - Dec |
| `CalMonthAndYearName` | Month+year datetime |
| `CalQuarterOfYearNo` | 1-4 |
| `CalQuarterOfYearName` | "Q1-2016" etc |
| `CalYear` | 2015-2026 |

### Financial Period Columns (13)
| Column | Description |
|--------|-------------|
| `FinDayOfYearNo` | 1-371 (>366 in 53-week years) |
| `FinDayOfMonthNo` | 1-35 (5-week months go to 35) |
| `FinDayOfQuarterNo` | 1-98 |
| `FinWeekOfYearNo` | 1-53 |
| `FinWeekOfYearName` | "Week-01" to "Week-53" |
| `FinMonthOfYearNo` | 1-12 (Month 1 = July) |
| `FinMonthOfYearName` | July - June |
| `FinMonthOfYearShortName` | Jul - Jun |
| `FinMonthAndYearName` | Month+year datetime |
| `FinQuarterOfYearNo` | 1-4 |
| `FinQuarterOfYearName` | "Q1-2016" etc |
| `FinYear` | 2016-2026 |

### Week Boundary Dates (4)
| Column | Description |
|--------|-------------|
| `CalWeekStartDate` | Calendar week start (Monday) |
| `CalWeekEndDate` | Calendar week end (Sunday) |
| `FinWeekStartDate` | Financial week start (Monday) |
| `FinWeekEndDate` | Financial week end (Sunday) |

---

## 6. Transaction Data Join Strategy

### Current Transaction Schema
- `SaleDate`: TIMESTAMP WITH TIME ZONE (AEST/AEDT)
- Transaction range: 2023-07-01 to 2026-02-13 (959 unique dates)
- Fiscal years: FY24, FY25, FY26

### Join Key
```sql
CAST(t.SaleDate AS DATE) = fc.TheDate
```

### Coverage
- All 959 transaction dates fall within the calendar range (FY2016-FY2026)
- The calendar extends back to FY2016, enabling up to 3 years of YoY comparisons for FY24+ data

### Hour-Level Analysis
`SaleDate` contains time components. For hourly analysis:
```sql
EXTRACT(HOUR FROM t.SaleDate AT TIME ZONE 'Australia/Sydney') AS hour_aest
```
No hour attribute in the fiscal calendar (day-level only), but hour extraction from transaction timestamps enables intra-day analysis when joined with fiscal calendar day attributes.

---

## 7. Comparison Period Fields

The fiscal calendar enables these comparison patterns:

| Comparison | Method |
|------------|--------|
| **Week-over-week** | Match `FinWeekOfYearNo` across `FinYear` values |
| **Month-over-month** | Match `FinMonthOfYearNo` across `FinYear` values |
| **Quarter-over-quarter** | Match `FinQuarterOfYearNo` across `FinYear` values |
| **Year-over-year** | Same `FinDayOfYearNo` or `FinWeekOfYearNo` in prior year |
| **Same day of week** | `DayOfWeekNo` within a financial period |
| **Season-over-season** | Match `SeasonName` across years |

**53-week year caveat:** FY2016 and FY2022 have week 53. When comparing to 52-week years, week 53 has no direct comparator. Recommended approach: exclude week 53 from WoW comparisons, or roll week 53 into week 52 for that year.

---

## 8. Data Quality Assessment

| Check | Result |
|-------|--------|
| Null values | Zero (all 4,018 x 45 cells populated) |
| Duplicate dates | None (4,018 unique TheDate values) |
| Date continuity | Complete (every day from 2015-06-29 to 2026-06-28) |
| Week consistency | All weeks are Mon-Sun |
| Month pattern | Consistent 5-4-4 across all FYs |
| Quarter balance | All quarters = 91 days (except 53-week year adjustments) |
| Business day logic | Mon-Fri = Y, Sat-Sun = N (no holidays marked) |
| Time_ID format | Valid YYYYMMDD for all rows |

**No holidays:** The `BusinessDay` flag is purely day-of-week based. No public holidays, Easter, Christmas etc. are marked. Holiday handling would need to be added separately if required.

---

## 9. Existing vs New Calendar Comparison

| Attribute | Existing (harris_farm.db) | New (Excel) |
|-----------|--------------------------|-------------|
| **Granularity** | Weekly (626 rows) | **Daily (4,018 rows)** |
| **Columns** | 11 | **45** |
| **FY range** | FY2015-FY2026 | FY2016-FY2026 |
| **Calendar periods** | Week only | **Day, week, month, quarter, year** |
| **Financial periods** | Week of year, week of month | **All levels + day counters** |
| **Day-of-week** | Not available | **Full (name, number, business flag)** |
| **Season** | Not available | **Available** |
| **Period boundaries** | Not available | **7 last-day flags** |
| **Calendar vs Financial** | Financial only | **Both calendar and financial** |
| **Prior period refs** | prior_year_week_ending | **Via FinWeekOfYearNo matching** |

**Recommendation:** Replace the existing weekly calendar with the new daily calendar. The new file is a strict superset — all information derivable from the old calendar is present in the new one, plus significantly more.

---

## 10. Key Design Decisions for Integration

1. **Store as parquet** in `data/fiscal_calendar.parquet` (same pattern as product_hierarchy)
2. **Load into DuckDB** as `fiscal_calendar` table alongside `transactions` and `product_hierarchy`
3. **JOIN on date**: `CAST(t.SaleDate AS DATE) = fc.TheDate`
4. **Use `FinYear`** (not the synthetic `fiscal_year` VARCHAR) for fiscal year grouping — they should agree but `FinYear` is the authoritative source
5. **Period selectors** should offer fiscal periods (FY, quarter, month, week) as primary options, with custom date range as fallback
6. **53-week years** (FY2016, FY2022): report honestly, exclude week 53 from WoW comparisons
