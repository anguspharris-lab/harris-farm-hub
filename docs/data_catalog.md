# Harris Farm Hub — Transaction Data Catalog

## Overview

| Attribute | Value |
|-----------|-------|
| Source | Microsoft Fabric `retail fact_pos_sales` |
| Format | Apache Parquet |
| Location | `~/Desktop/ProjectManagement/Data/customer-transactions/raw/` |
| Total rows | 383,566,497 |
| Total size | 6.63 GB (3 files) |
| Date range | 1 Jul 2023 — 13 Feb 2026 (31 months) |
| Stores | 34 (30 in FY24, growing to 34 in FY26) |
| Query engine | DuckDB (in-memory, reads parquet directly) |

## Files

| File | Fiscal Year | Rows | Size | Date Range |
|------|------------|------|------|------------|
| `sales_01072023_parquet.parquet` | FY24 | 134,968,573 | 2.3 GB | 2023-07-01 — 2024-06-30 |
| `sales_01072024_parquet.parquet` | FY25 | 149,164,917 | 2.7 GB | 2024-07-01 — 2025-06-30 |
| `sales_01072025_parquet.parquet` | FY26 (YTD) | 99,433,007 | 1.7 GB | 2025-07-01 — 2026-02-13 |

## Schema

| Column | Type | Null% | Description | Example |
|--------|------|-------|-------------|---------|
| `Reference2` | string | 0% | Transaction reference ID (groups line items into baskets) | `SAL001009368` |
| `SaleDate` | timestamp (UTC) | 0% | Sale date/time in UTC. Add +11h for AEDT, +10h for AEST | `2025-11-15 01:23:45+00` |
| `Store_ID` | string | 0% | Store identifier (see Store Reference below) | `28` |
| `PLUItem_ID` | string | ~0% | Product/PLU item identifier | `4322` |
| `Quantity` | float64 | ~0% | Quantity sold (fractional for weighed items, negative = return) | `1.0`, `0.534` |
| `SalesIncGST` | float64 | 0% | Sale amount including GST (AUD). Negative = refund | `4.99` |
| `GST` | float64 | 0% | GST component (AUD). Zero for fresh food (~87-89% of rows) | `0.0`, `0.45` |
| `EstimatedCOGS` | float64 | 3-24% | Estimated cost of goods sold. Typically negative (cost). 24% null in FY24, ~3% in FY25+ | `-2.85` |
| `CustomerCode` | string | ~88% | Loyalty/customer identifier. Only ~12% of transactions have a code | `HFM-057372` |

## Data Quality Notes

1. **SaleDate is UTC** — Harris Farm stores operate in AEST/AEDT (UTC+10/+11). A sale at 10am Sydney time appears as midnight UTC. When analysing hourly patterns, convert first.

2. **CustomerCode is 88% null** — Low loyalty card capture rate. Only 12% of transactions have a customer identifier. Customer-level analysis is limited to this subset.

3. **EstimatedCOGS gaps** — 24.4% null in FY24 (improving to ~3% in FY25/26). COGS values are typically negative (representing cost to business). GP calculations should use `COALESCE`.

4. **Negative values** — ~0.1% of rows have negative Quantity or SalesIncGST. These are returns/refunds, not data errors.

5. **Apparent duplicates** — 8-10% of rows appear duplicated (same PLU, price, store, time). These are likely legitimate (multiple customers buying 1x of the same item at the same price). `Reference2` differentiates individual transactions.

6. **GST-free items** — 87-89% of rows have GST=0. This is correct: fresh food (fruit, vegetables, meat, bread) is GST-free in Australia. Non-zero GST indicates packaged/processed products.

## Store Reference

| Store_ID | Store Name | State |
|----------|-----------|-------|
| 10 | Pennant Hills | NSW |
| 11 | Meats Pennant Hills | NSW |
| 24 | St Ives | NSW |
| 28 | Mosman | NSW |
| 32 | Willoughby | NSW |
| 37 | Broadway | NSW |
| 40 | Erina | NSW |
| 44 | Orange | NSW |
| 48 | Manly | NSW |
| 49 | Mona Vale | NSW |
| 51 | Bowral | NSW |
| 52 | Cammeray | NSW |
| 54 | Potts Point | NSW |
| 56 | Boronia Park | NSW |
| 57 | Bondi Beach | NSW |
| 58 | Drummoyne | NSW |
| 59 | Bathurst | NSW |
| 63 | Randwick | NSW |
| 64 | Leichhardt | NSW |
| 65 | Bondi Westfield | NSW |
| 66 | Newcastle | NSW |
| 67 | Lindfield | NSW |
| 68 | Albury | NSW |
| 69 | Rose Bay | NSW |
| 70 | West End | QLD |
| 74 | Isle of Capri | QLD |
| 75 | Clayfield | QLD |
| 76 | Lane Cove | NSW |
| 77 | Dural | NSW |
| 80 | Majura Park | ACT |
| 84 | Redfern | NSW |
| 85 | Marrickville | NSW |
| 86 | Miranda | NSW |
| 87 | Maroubra | NSW |

## Fiscal Calendar

Harris Farm operates a **5-4-4 retail calendar**:
- Financial year runs July 1 — June 30
- Periods alternate 5-4-4 weeks (P01=5 weeks, P02=4 weeks, P03=4 weeks, etc.)
- FY24 = Jul 2023 — Jun 2024, FY25 = Jul 2024 — Jun 2025, FY26 = Jul 2025 — Jun 2026

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/transactions/summary` | GET | Row counts, date ranges, store counts per FY |
| `/api/transactions/stores` | GET | All stores with transaction counts and revenue |
| `/api/transactions/top-items` | GET | Top N items by revenue/qty/GP (params: start, end, store_id, limit, sort_by) |
| `/api/transactions/store-trend` | GET | Time-series for a store (params: store_id, start, end, grain) |
| `/api/transactions/plu/{plu_id}` | GET | Single PLU performance across all stores (params: start, end) |
| `/api/transactions/query` | POST | Freeform read-only SQL (body: sql, params, limit) |

## Query Examples

### Top 10 items by revenue (FY26 YTD)
```bash
curl "http://localhost:8000/api/transactions/top-items?start=2025-07-01&end=2026-03-01&limit=10"
```

### Mosman monthly trend
```bash
curl "http://localhost:8000/api/transactions/store-trend?store_id=28&start=2025-07-01&end=2026-03-01&grain=monthly"
```

### PLU 4322 performance
```bash
curl "http://localhost:8000/api/transactions/plu/4322?start=2025-07-01&end=2026-03-01"
```

### Freeform: GST split for Mosman FY26
```bash
curl -X POST http://localhost:8000/api/transactions/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT CASE WHEN GST=0 THEN '\''Fresh'\'' ELSE '\''Packaged'\'' END AS cat, SUM(SalesIncGST) AS rev FROM transactions WHERE Store_ID='\''28'\'' AND fiscal_year='\''FY26'\'' GROUP BY 1",
    "limit": 10
  }'
```

### Python: Using the query library
```python
from transaction_layer import TransactionStore
from transaction_queries import run_query

ts = TransactionStore()

# Top items
items = run_query(ts, "top_items_by_revenue",
                  start="2025-07-01", end="2026-03-01", limit=10)

# Basket analysis
baskets = run_query(ts, "basket_size_distribution",
                    store_id="28", start="2026-01-01", end="2026-02-01")

# Year-over-year
yoy = run_query(ts, "yoy_store_monthly", store_id="28")
```

## Data Lineage

```
Microsoft Fabric (POS System)
  → retail fact_pos_sales (40 columns)
    → Parquet export (9 columns selected, 13 Feb 2026)
      → ~/Desktop/ProjectManagement/Data/customer-transactions/raw/
        → DuckDB in-memory (read_parquet, zero-copy)
          → /api/transactions/* endpoints
```

## Known Limitations

1. **No product names** — Only PLU IDs are available. Product name lookup requires joining with a product master (not yet imported).
2. **No basket linking beyond Reference2** — Reference2 groups line items but there's no explicit basket/receipt table.
3. **UTC timestamps** — All analysis of time-of-day patterns must account for UTC→AEST/AEDT conversion.
4. **Low loyalty capture** — 88% of transactions have no CustomerCode, limiting customer-level analytics.
5. **COGS incomplete in FY24** — 24% null. Use FY25+ for reliable margin analysis.
