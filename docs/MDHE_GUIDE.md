# Master Data Health Engine (MDHE)
## Harris Farm Hub — Team Guide

**Date:** 26 February 2026
**Owner:** Angus Harris
**Status:** Live in Hub (Back of House section)

---

## What Is MDHE?

The Master Data Health Engine validates, scores, and surfaces data quality issues in our product master data (PLU records, barcodes, pricing, hierarchy). Bad master data = bad dashboards = bad decisions.

MDHE runs every uploaded dataset through **4 layers of validation**, scores each record, and generates actionable issues for the team to fix at the source.

**Where to find it:** Harris Farm Hub > Back of House > MDHE Dashboard / MDHE Upload / MDHE Issues

---

## The 4 Validation Layers

| Layer | Weight | What It Checks | Who Fixes |
|-------|--------|----------------|-----------|
| **Rules** | 35% | PLU format, barcode check digits (EAN-13), required fields, duplicates, price > 0, cost < retail | Data / IT |
| **Standards** | 30% | No ALL CAPS descriptions, valid category combos, UOM appropriate for category, price within range, margin within range | Buying team |
| **AI** | 20% | Description/category mismatches (e.g. "Chicken" in Bakery), fuzzy duplicate detection, gibberish descriptions | Buying team (review) |
| **Recon** | 15% | Warehouse scan verification, POS scan verification, manual key rate, scan success rate | IT / Warehouse |

---

## Data We Need From The Team

> "We're building a Master Data Health Engine in the Hub to score and validate our product master data. This will catch data quality issues (missing barcodes, wrong categories, orphan PLUs, price mismatches) before they hit dashboards and reports. To build this, I need the following data exports. CSV is preferred, Excel is fine. Don't worry about cleaning it -- the whole point is we validate it automatically."

**Format:** CSV preferred (UTF-8), Excel (.xlsx) fine. Headers in row 1. One file per data type. Include ALL records (active + inactive). Dates in YYYY-MM-DD. No password-protected files.

**Delivery:** Upload directly to the Hub via MDHE Upload page, or email to Gus/Phil for initial load.

| Priority | # | Document / Data | What to include | Owner | Expected Columns | Purpose |
|----------|---|----------------|-----------------|-------|------------------|---------|
| **Week 1** | 1 | **Full PLU Master File** | All active + inactive PLUs | Buying / IT | `plu_code, barcode, description, category, subcategory, commodity, unit_of_measure, pack_size, supplier_code, status (active/inactive), created_date, last_modified_date` | Core validation source |
| **Week 1** | 2 | **Product Hierarchy File** | Full category tree (Dept > Category > Subcategory > Commodity) with codes | Buying / IT | `dept_code, dept_name, category_code, category_name, subcategory_code, subcategory_name, commodity_code, commodity_name` | Hierarchy validation |
| **Week 1** | 3 | **Supplier Master File** | Supplier code, name, ABN, status, payment terms | Buying / Finance | `supplier_code, supplier_name, abn, status (active/inactive), payment_terms` | Cross-reference supplier codes |
| **Week 1** | 4 | **Price Book / Current Retail Prices** | PLU, store (or "all"), current retail price, cost price, margin %, effective date | Buying / Finance | `plu_code, store_code (or "ALL"), retail_price, cost_price, margin_pct, effective_date, currency (AUD)` | Price reasonableness checks |
| **Week 1** | 5 | **Barcode Register** | All barcodes mapped to PLU codes (including multi-barcode items) | IT / Buying | `barcode, plu_code, barcode_type (EAN13/UPC/internal), is_primary (Y/N), created_date` | Barcode integrity checks |
| **Week 2** | 6 | **Vision Scan Data** | Warehouse barcode scan logs | Warehouse / IT | `barcode, scan_timestamp, warehouse_location, scan_result (success/fail/unknown), operator_id (optional)` | Confirms barcodes work in the warehouse |
| **Week 2** | 7 | **POS Scan Report** | Checkout barcode scan logs | IT / POS vendor | `barcode, plu_resolved, store_code, scan_timestamp, scan_method (scan/manual_key), transaction_id (optional)` | Confirms barcodes scan at checkout |
| **Week 2** | 8 | **Store Master File** | Store code, name, address, postcode, state, format, status, open date | Ops / IT | `store_code, store_name, address, postcode, state, format, status, open_date` | Cross-reference store codes |
| **Week 2** | 9 | **Promotion History** | PLU, promo type, start/end date, promo price, store scope | Marketing / Buying | `plu_code, promo_type, start_date, end_date, promo_price, store_scope` | Validate price anomalies against promo periods |
| **Week 2** | 10 | **Discontinued / Delisted PLU List** | PLU codes removed from range with delist date and reason | Buying | `plu_code, description, delist_date, reason` | Flag transactions on dead PLUs |
| **Week 3+** | 11 | **Planogram Data** | PLU x store shelf allocation | Merch / Space Planning | `plu_code, store_code, shelf_location, facing_count` | Cross-ref active range vs allocated PLUs |
| **Week 3+** | 12 | **Supplier Product Catalogue** | Supplier's own product codes mapped to HFM PLU | Buying | `supplier_code, supplier_product_code, plu_code, supplier_description` | Supplier code validation |
| **Week 3+** | 13 | **Historical Price Changes** | PLU, old price, new price, change date | Finance / IT | `plu_code, old_price, new_price, change_date, changed_by` | Price change frequency analysis |

---

## How To Use MDHE

### Uploading Data

1. Navigate to **Back of House > MDHE Upload** in the Hub
2. Select the **Data Type** from the dropdown (e.g. "PLU Master File", "Barcode Register")
3. Click **Browse Files** or drag-and-drop a CSV/Excel file
4. The system previews the first 20 rows -- confirm the columns look correct
5. If column names don't match, use the **Column Mapping** dropdowns to map your columns to the required fields
6. Click **Upload & Validate** -- the file is saved and validation runs automatically
7. When complete, you'll see a summary: total rows, pass rate, issues found
8. Click through to the MDHE Dashboard or MDHE Issues to review

### Reading Health Scores

**Overall Score (0-100):** Weighted average across all 4 validation layers. Displayed as a large number with colour coding:

| Score | Colour | Meaning |
|-------|--------|---------|
| 95-100 | Green | Excellent -- master data is clean, minimal issues |
| 85-94 | Blue | Good -- some minor issues, nothing blocking |
| 70-84 | Amber | Needs Attention -- significant gaps that could affect reporting |
| Below 70 | Red | Critical -- major data quality problems, dashboards may show incorrect numbers |

**Domain Scores:** Each domain (PLU, Barcode, Pricing, Hierarchy, Supplier) is scored independently. A low domain score tells you exactly where the problem is:

- **Low PLU score** -- missing descriptions, duplicate codes, format issues
- **Low Barcode score** -- invalid check digits, multi-mapped barcodes, orphan barcodes
- **Low Pricing score** -- cost > retail, zero prices, extreme outliers
- **Low Hierarchy score** -- invalid category codes, orphan subcategories
- **Low Supplier score** -- unknown supplier codes, inactive suppliers on active PLUs

**Layer Breakdown:** Each domain shows its 4-layer scores so you can see WHERE the failures are:

- Rules layer failing = basic data format problems (easiest to fix)
- Standards layer failing = business logic violations (need buying team input)
- AI layer failing = anomalies that need human judgment to resolve
- Recon layer failing = data doesn't match across systems (need IT investigation)

### Using Scan Verification

The Scan Verification tab answers: "Does our barcode data actually work in the real world?"

**Warehouse Scan Match Rate:**
- What % of barcodes in the master file have been successfully scanned by the warehouse vision system
- High match rate (>95%) = barcodes are correct and scannable
- Low match rate = barcodes may be wrong, labels may be unreadable, or items not yet received

**POS Scan Match Rate:**
- What % of barcodes successfully scan at checkout
- **Manual Key Rate** is the critical metric -- if store staff have to manually type PLU codes instead of scanning, the barcode is broken
- Manual key rate >5% for a product = barcode needs investigation
- Manual key rate >10% for a store = possible scanner hardware issue

**Never Scanned List:**
- Products in the master file that have NEVER been scanned (warehouse or POS)
- Could be: new items not yet received, discontinued items, data entry errors, incorrect barcodes
- Action: Review with buying team -- are these real products?

### Managing Issues

1. Navigate to **Back of House > MDHE Issues**
2. Issues are auto-generated from validation failures
3. **Open** issues need someone to investigate and fix
4. Click an issue to see: which rule failed, which record, what the expected vs actual value was
5. **Assign** issues to the right team (Buying, IT, Finance) using the dropdown
6. Once fixed at the source, re-upload the corrected data file
7. Mark the issue as **Resolved** with a note about what was fixed
8. **Won't Fix** is for known exceptions (e.g. a PLU intentionally priced at $0 for sampling)

### AI Insights Tab

The AI Insights tab flags patterns humans might miss:

- **Duplicate Candidates:** Products with similar names that might be the same item entered twice (e.g. "Organic Avocado" vs "Avocado Organic Hass")
- **Description Anomalies:** Items where the description doesn't match the category (e.g. "Chicken Breast" in the "Bakery" category)
- **Price Anomalies:** Items priced unusually high or low compared to similar products
- **Category Suggestions:** Items with missing or incorrect categories, with suggested corrections

AI insights are flagged for human review -- they're suggestions, not automatic fixes.

---

## Recommended Weekly Cadence

| Day | Action | Who |
|-----|--------|-----|
| **Monday AM** | Export fresh PLU master + price book from ERP/POS system | IT / Buying |
| **Monday AM** | Upload to MDHE via the Upload page | IT / Buying |
| **Monday** | Validation runs automatically -- review health scores | Gus / Phil |
| **Monday-Tuesday** | Assign critical/high issues to responsible teams | Gus / Phil |
| **Wednesday** | Teams fix issues at source (ERP, POS config, supplier comms) | Buying / IT |
| **Thursday** | Re-upload corrected data to confirm fixes | IT / Buying |
| **Friday** | Review improvement trend -- are scores going up week over week? | Gus / Phil |

---

## Demo Data

The MDHE currently has **10 demo PLU records** pre-loaded to show how validation works. These include deliberate quality issues:

| PLU | Description | Issue |
|-----|-------------|-------|
| 1001 | Organic Avocado Hass | Clean -- no issues |
| 1002 | BANANA CAVENDISH | ALL CAPS description (standards violation) |
| 1003 | Pink Lady Apple 1kg | Clean -- no issues |
| 1004 | Chicken Breast Free Range | Classified under Bakery instead of Meat (AI catch) |
| 1005 | *(empty)* | Missing description (rules violation) |
| 1006 | Sourdough Loaf | Cost $8.20 > Retail $6.50 (negative margin) |
| 1007 | Atlantic Salmon Fillet | Duplicate barcode (shared with 1008) |
| 1008 | Atlantic Salmon Portions | Duplicate barcode (shared with 1007) |
| 1009 | Organic Avocado | Near-duplicate of PLU 1001 (AI similarity) |
| 1010 | xyz123test | Everything wrong -- gibberish, invalid barcode, no category, zero prices |

**To clear demo data:** Click "Clear Demo Data" on the MDHE Upload page.

---

## Access & Roles

MDHE pages are visible to these Hub roles:

| Role | MDHE Dashboard | MDHE Upload | MDHE Issues |
|------|:-:|:-:|:-:|
| **Admin** | Yes | Yes | Yes |
| **General (user)** | Yes | Yes | Yes |
| **Data / IT** | Yes | Yes | Yes |
| **Buyer / Procurement** | Yes | No | Yes |
| **Finance / Analyst** | Yes | No | No |
| **Other roles** | No | No | No |

Admins can change roles via **Back of House > User Management**.

---

## Questions?

Contact Gus Harris or Phil Cribb. Or ask the Hub Assistant -- it knows about MDHE.
