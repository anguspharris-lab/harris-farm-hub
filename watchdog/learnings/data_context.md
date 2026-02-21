# Data Context Rules — Harris Farm Hub

## Sales Table Grain (Critical)
The sales table has a composite key of (store, week_ending, department, **major_group**, measure, channel, is_promotion).
All 1,623,193 rows are unique at this grain. There are 28 major groups across 8 departments (e.g. Grocery has 8, F&V has 3).
**Do NOT omit major_group when checking for duplicates** — this was a false-alarm finding in the Feb 2026 Phase 1 audit.

## Core Principle
Every number displayed in a dashboard must trace back to aggregated transactional data.
No KPI should exist in isolation — it must be derivable from the underlying transaction records.

## Data Grain
- **Source**: POS register transactions (one row per basket item)
- **Dashboard grain**: Store × Category × Day (aggregated from transactions)
- **All KPIs** (revenue, margin, wastage, OOS, miss-picks) are columns on the same grain

## Sales Dashboard
- **Primary view**: Total revenue, gross profit, margin by store, by category, by day
- Revenue = sum of transaction totals
- Gross profit = revenue − COGS (aggregated)
- Margin % = gross profit / revenue × 100
- Transactions = count of unique baskets
- Avg basket = revenue / transactions

## Operational Metrics (same grain, same source)
- **Wastage cost** = COGS × wastage rate (spoilage/markdowns recorded at POS)
- **Wastage %** = wastage cost / COGS × 100
- **OOS hours** = shelf-empty time per store/category/day (from inventory system)
- **OOS lost sales** = OOS hours × (revenue / trading hours) — estimated impact
- **Miss-picks** = incorrectly picked items in online orders
- **Miss-pick rate** = miss-picks / online orders × 100

## What is NOT the Sales Dashboard
- **Market share by postcode** is a separate strategic/competitive view
- Postcode data comes from a different source (market research, not POS)
- Never mix postcode market share into transactional sales metrics

## Store Network
- 32 retail stores across NSW and QLD (plus concessions, meats, online)
- Store coordinates geocoded in `backend/market_share_layer.py` STORE_LOCATIONS dict
- Stores are physical locations, not postcodes or regions
- Each store has its own revenue, margin, wastage, OOS profile

## PLU Weekly Results Database (harris_farm_plu.db)
- **Source:** 3 years of PLU-level weekly results (FY2024-FY2026)
- **Rows:** 27.3M across weekly_plu_results fact table
- **Dimensions:** dim_item (75K PLUs), dim_store (43), dim_week (156)
- **Metrics:** sales_ex_gst, gst, cogs, wastage, stocktake_cost, other_cost, gross_margin
- **Channels:** Retail, Online Shopify, Ext Conc., Online Uber, Online Amazon
- **Critical:** numpy int32 from parquet must be converted to Python native types before SQLite insertion
- Wastage values are negative (cost outflows), stocktake_cost also negative
- Accessed via `backend/plu_layer.py`

## Market Share Data (Layer 2 — CBAS)
- **Table:** market_share in harris_farm.db (77K rows)
- **Grain:** postcode × channel × month (1,040 postcodes, 37 months, 3 channels)
- **Primary metric:** Market Share % (reliable, comparable)
- **Dollar values:** Directional estimates only — NEVER use as actual HFM revenue
- **NEVER mix** Layer 2 (market share) dollar values with Layer 1 (POS/ERP) revenue
- **Distance tiers:** Core (0-3km), Primary (3-5km), Secondary (5-10km), Extended (10-20km), No Presence (20km+)
- **Comparison:** Always same-month YoY, never sequential months
- **Postcode coords:** `data/postcode_coords.json` (1,040 postcodes, pgeocode/ABS)

## Mock Data Rules
- Seed: numpy RandomState(42) for deterministic output
- Date anchor: datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
  - Do NOT use .normalize() (pandas Timestamp method, not available on datetime)
- All mock values must be plausible for a premium grocery retailer
- Range checks: no negative revenue, margin 5%–55%, wastage 0%–25%

## 5/4/4 Retail Fiscal Calendar
- FY starts Monday closest to 1 July (Australian retail convention)
- Each quarter = 13 weeks in 5+4+4 week pattern (3 periods per quarter)
- 4 quarters × 13 weeks = 52 weeks per year
- Dashboard filter options:
  - WTD (Week-to-Date): Mon through today, compared to same days previous week
  - This Week: full Mon–Sun
  - This Period (454): current 4- or 5-week block
  - This Quarter (454): current 13-week quarter
  - Rolling windows: 7, 30, 90 days
- Never use calendar months for period analysis — always 454 periods

## Delta Comparisons
- Always compare current period vs previous equivalent period
- WTD compares to same number of days in prior week (not full week)
- Period compares to previous 454 period
- Quarter compares to previous 454 quarter
- Compute deltas from actual data, never hardcode delta values
- Wastage and OOS deltas use inverse colour (decrease = good)
