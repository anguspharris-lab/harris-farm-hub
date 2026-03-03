# Operations Tab Audit Report

**Date:** 2026-02-26
**Scope:** All 10 Operations-area dashboard tabs — filter logic, time selection, comparison capability, data sources

---

## Summary

| Tab | Filter Mechanism | Data Source | Date Range | Stores | Comparison | Status |
|-----|-----------------|-------------|------------|--------|------------|--------|
| Sales | fiscal_selector | harris_farm.db (weekly) | FY2016-FY2024 | 30 | vs Prior Year/Period | MIGRATED |
| Profitability | fiscal_selector | harris_farm.db (weekly) | FY2016-FY2024 | 30 | vs Prior Year/Period | MIGRATED |
| Revenue Bridge | fiscal_selector | DuckDB transactions | FY2024-FY2026 | 33 | vs Prior Year/Period | OK (no change) |
| Store Ops | fiscal_selector | DuckDB transactions | FY2024-FY2026 | 33 | vs Prior Year/Period | OK (no change) |
| Buying Hub | fiscal_selector | DuckDB transactions | FY2024-FY2026 | 33 | vs Prior Year/Period | FIXED (comparison enabled) |
| Product Intel | fiscal_selector | DuckDB transactions | FY2024-FY2026 | 33 | None | OK (no change) |
| PLU Intel | FY dropdown + compare | harris_farm_plu.db | FY2024-FY2026 | 43 | vs FY (YoY) | EXPANDED |
| Transport | fiscal_selector | Mock (seed 42) | 90 days | 21 | vs Prior Year/Period | MIGRATED |
| Customer Hub | fiscal_selector | DuckDB transactions | FY2024-FY2026 | 33 | None | FIXED (FY2024 added) |
| Customers | fiscal_selector | DuckDB transactions | FY2024-FY2026 | 33 | None | FIXED (FY2024 added) |

---

## Issues Found & Fixed

### 1. Sales Dashboard (sales_dashboard.py)
**Before:** 8 hardcoded period presets (Last 4/13/26/52 Weeks, This Period 454, This Quarter 454, FY2024, FY2023). Inline 454 calendar functions (~90 lines) duplicated from fiscal_calendar.py. No formal comparison mode.
**After:** Uses `render_fiscal_selector(show_comparison=True)`. Removed ~90 lines of inline 454 code. Full comparison support (vs Prior Year, vs Prior Period). All existing store/department/major_group cascading filters preserved.

### 2. Profitability Dashboard (profitability_dashboard.py)
**Before:** Identical inline 454 calendar + hardcoded presets as Sales. Same issues.
**After:** Same migration as Sales. Uses `render_fiscal_selector(show_comparison=True)`. Removed ~90 lines of inline 454 code.

### 3. Revenue Bridge (revenue_bridge_dashboard.py)
**Status:** Already uses `fiscal_selector`. No changes needed.

### 4. Store Ops (store_ops_dashboard.py)
**Status:** Already uses `fiscal_selector`. No changes needed.

### 5. Buying Hub (buying_hub_dashboard.py)
**Before:** Used `fiscal_selector` but with `show_comparison=False` (disabled).
**After:** Enabled `show_comparison=True`. Added caveats display. Users can now compare periods directly.

### 6. Product Intel (product_intel_dashboard.py)
**Status:** Already uses `fiscal_selector`. No comparison mode but the tab's purpose (product hierarchy browsing) doesn't require it. No changes needed.

### 7. PLU Intel (plu_intel_dashboard.py)
**Before:** Only FY dropdown selector. No period drill-down. No comparison capability.
**After:** Added YoY comparison dropdown (vs FY selector). Department Summary KPIs now show deltas when comparison FY selected. Added data coverage caption. Full fiscal_selector migration deferred — would require refactoring plu_layer.py API from FY-based to date-range-based queries.

### 8. Transport (transport_dashboard.py)
**Before:** Mock data (np.random.seed(42)). Own inline 454 calendar (~65 lines). Dead "Supplier Type" filter that was never wired to any data filtering. No indication to users that data is simulated.
**After:** Removed inline 454 calendar. Uses `render_fiscal_selector(show_comparison=True)`. Removed dead Supplier Type filter. Added `st.info()` banner clearly labelling data as simulated. Added coverage indicators.

### 9. Customer Hub (customer_hub/customer_overview.py)
**Before:** `allowed_fys=[2025, 2026]` hardcoded, even though transaction data covers FY2024-FY2026.
**After:** `allowed_fys=[2024, 2025, 2026]` — users can now access FY2024 data.

### 10. Customers (customer_dashboard.py)
**Before:** Same `allowed_fys=[2025, 2026]` restriction.
**After:** `allowed_fys=[2024, 2025, 2026]`.

---

## Store Count Discrepancies (Noted, Not Fixed)

Different data sources report different store counts:
- `harris_farm.db` (Sales/Profitability): 30 stores
- `harris_farm_plu.db` (PLU Intel): 43 stores
- `store_master.csv`: 41 entries
- DuckDB transactions: 33 stores
- Cannibalisation engine: 32 stores
- CBAS network data: 31 stores

This is expected — different systems track different store sets (retail only, concessions, online, closed stores). A master store reconciliation is available in the Store Network > Reconciliation tab.

---

## Data Coverage Indicators

All tabs using `fiscal_selector` now display caveats when the selected period has known issues (e.g., 53-week year, partial data coverage). The selector returns `caveats: list[str]` which is rendered as `st.caption()` notes.
