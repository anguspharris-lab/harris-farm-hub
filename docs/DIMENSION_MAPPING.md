# Product Intel — Dimension Mapping Architecture

**Date:** 2026-02-26
**Scope:** All dimension lookups in DuckDB transaction dashboards

---

## Data Pipeline Overview

```
[Parquet Files]                    [Hierarchy Parquet]           [Fiscal Calendar Parquet]
FY24/25/26.parquet                product_hierarchy.parquet      fiscal_calendar_daily.parquet
383M POS transaction rows         72,911 products (9 depts)      4,018 daily rows
Columns: Store_ID, PLUItem_ID,    Columns: ProductNumber,        Columns: TheDate, FinYear,
  SaleDate, Quantity,               ProductName, DepartmentDesc,   FinWeekOfYearNo, etc.
  SalesIncGST, GST,                MajorGroupDesc, MinorGroupDesc,
  EstimatedCOGS, CustomerCode      HFMItemDesc, BuyerId, etc.
         │                                  │                              │
         ▼                                  ▼                              ▼
[TransactionStore._get_connection()]
  → DuckDB in-memory
  → CREATE VIEW transactions AS UNION ALL read_parquet(FY24, FY25, FY26)
  → CREATE TABLE product_hierarchy AS read_parquet(product_hierarchy.parquet)
  → CREATE TABLE fiscal_calendar AS read_parquet(fiscal_calendar_daily.parquet)
         │
         ▼
[TransactionStore.query(sql, params)]
  → Executes SQL → returns list[dict]
  → Column names: desc[0].lower() for all result columns
         │
         ▼
[transaction_queries.run_query(store, query_name, **kwargs)]
  → Resolves named query from QUERIES dict
  → Handles optional filters ({store_filter}, {dept_filter}, etc.)
  → Calls store.query(sql, params)
         │
         ▼
[Dashboard Layer]
  → Product Intel, Store Ops, Buying Hub, Revenue Bridge, Customer Hub
  → Each dashboard calls run_query() or ts.query() directly
  → Enriches results with plu_lookup.enrich_items() or product_hierarchy functions
```

---

## Dimension Mappings

### 1. Product Dimension (PLU → Product Name)

| Property | Value |
|----------|-------|
| **Source** | `data/product_hierarchy.parquet` (72,911 rows) |
| **Join Key** | `transactions.PLUItem_ID = product_hierarchy.ProductNumber` |
| **Match Rate** | 98.2% (19,075 of 19,428 unique PLUs matched) |
| **Resolution** | Two paths: SQL JOIN or Python enrichment |

**Path A — SQL JOIN (hierarchy-filtered queries):**
```sql
SELECT t.PLUItem_ID AS pluitem_id,
       p.ProductName AS product_name, ...
FROM transactions t
JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
```
Used by: `top_items_filtered`, `slow_movers_filtered`, `top_items_by_department`, hierarchy revenue queries.

**Path B — Python enrichment (unfiltered queries):**
```python
items = run_query(ts, "top_items_by_revenue", ...)  # returns pluitem_id
enriched = enrich_items(items, plu_key="pluitem_id")  # adds product_name
```
Used by: `query_top_items()` in Product Intel (default view, no hierarchy filter).

**Enrichment chain:** `plu_lookup.load_plu_names()` → reads `product_hierarchy.parquet` columns `[ProductNumber, ProductName]` → returns `dict[str, str]` mapping PLU → name. Fallback: `data/product_lines.csv` (491 F&V items).

**Unmatched PLUs** (~1.8%): Show as `"PLU {id}"`. These are typically check-digit suffixed barcodes or discontinued products. `product_hierarchy.get_product_by_plu()` attempts progressive truncation (strip 1-2 trailing digits) for weighed/priced items.

### 2. Store Dimension (Store_ID → Store Name)

| Property | Value |
|----------|-------|
| **Source** | `STORE_NAMES` dict in `backend/transaction_layer.py` (33 stores) |
| **Lookup** | `STORE_NAMES.get(str(store_id), f"Store {store_id}")` |
| **Coverage** | 33 stores in dict, matches transaction data exactly |

The store dimension is a static Python dict, not a database table. Store IDs are string-typed ("10", "28", "37", etc.).

### 3. Time/Fiscal Dimension

| Property | Value |
|----------|-------|
| **Source** | `data/fiscal_calendar_daily.parquet` (4,018 rows) |
| **Join Key** | `CAST(t.SaleDate AS DATE) = fc.TheDate` |
| **Columns** | `FinYear`, `FinWeekOfYearNo`, `FinMonthOfYearNo`, `FinQuarterOfYearNo`, `DayOfWeekName`, `BusinessDay`, `SeasonName`, etc. |

Used by fiscal-aware queries: `fiscal_weekly_trend`, `fiscal_monthly_trend`, `fiscal_yoy_weekly`, and all queries with `{fiscal_join}` placeholder (conditionally joined when time dimension filters are active).

### 4. Customer Dimension

| Property | Value |
|----------|-------|
| **Source** | `transactions.CustomerCode` column (loyalty card codes) |
| **Coverage** | ~12% of transaction rows have non-null loyalty codes |
| **No master table** | No customer name/demographic table exists |

Customer analytics use RFM segmentation (Recency, Frequency, Monetary) computed from transaction data. No external customer dimension table.

### 5. Supplier/Buyer Dimension

| Property | Value |
|----------|-------|
| **Source** | `product_hierarchy.BuyerId` column |
| **Resolution** | Buyer IDs only (e.g., "TWHITE", "AW", "SYS") — no buyer name table |
| **Used by** | `buyer_performance` query in Buying Hub |

### 6. Cost Centre Dimension

**Not applicable.** No cost centre data exists in the transaction layer. Cost data comes from `EstimatedCOGS` column in transactions (estimated, not actual).

---

## Column Name Convention

**Rule:** All column names returned by `TransactionStore.query()` are **lowercase**.

DuckDB preserves CamelCase from parquet source files (e.g., `PLUItem_ID`, `Store_ID`). The `query()` method normalizes all column names to lowercase via `desc[0].lower()`.

| Parquet Column | DuckDB Returns | Python Key |
|---------------|----------------|------------|
| `PLUItem_ID` | `PLUItem_ID` | `pluitem_id` |
| `Store_ID` | `Store_ID` | `store_id` |
| `SaleDate` | `SaleDate` | `saledate` |
| `SalesIncGST` | `SalesIncGST` | `salesincgst` |
| `CustomerCode` | `CustomerCode` | `customercode` |
| SQL alias `AS total_revenue` | `total_revenue` | `total_revenue` |

**Consequence:** All dashboard code must use lowercase column names when accessing query results.

**Exception:** Code that loads parquet directly via pandas (`pd.read_parquet()` or `load_hierarchy()`) preserves original CamelCase. This applies to `product_hierarchy.py` functions like `get_departments()`, `search_products()`, etc.

---

## Root Cause of Dimension Name Bug (Fixed 2026-02-26)

**Symptom:** Product names displayed as "PLU 4322" instead of "Cavendish Bananas". Store names displayed as IDs instead of names.

**Root Cause:** `TransactionStore.query()` returned DuckDB column names preserving CamelCase from parquet files (`PLUItem_ID`), but Python consumer code expected lowercase keys (`pluitem_id`).

**Example failure path:**
1. `run_query(ts, "top_items_by_revenue", ...)` → SQL: `SELECT PLUItem_ID, ...`
2. DuckDB returns: `{"PLUItem_ID": "4322", ...}`
3. `enrich_items(items, plu_key="pluitem_id")` → `item.get("pluitem_id", "")` → `""` (key mismatch!)
4. `names.get("", f"PLU ")` → `"PLU "` for every item

**Fix:** Added `.lower()` to column name extraction in `TransactionStore.query()`, then updated all dashboard references to use lowercase keys.

---

## Files in the Dimension Pipeline

| File | Role |
|------|------|
| `backend/transaction_layer.py` | DuckDB query engine, `STORE_NAMES` dict, `TransactionStore.query()` |
| `backend/transaction_queries.py` | 40+ named SQL queries with parameterized filters |
| `backend/plu_lookup.py` | PLU → product name enrichment (`enrich_items`, `resolve_plu`) |
| `backend/product_hierarchy.py` | Product hierarchy browsing/search (pandas-based) |
| `dashboards/shared/hierarchy_filter.py` | Cascading sidebar filter: Dept → Category → Sub-Category → HFM Item → Product |
| `dashboards/shared/hourly_charts.py` | Shared time-pattern analysis component |
| `data/product_hierarchy.parquet` | 72,911 products × 12 columns (2.1MB) |
| `data/fiscal_calendar_daily.parquet` | 4,018 daily fiscal rows |
| `data/product_lines.csv` | 491 F&V items (fallback for PLU names) |
