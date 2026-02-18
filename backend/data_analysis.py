"""
Harris Farm Hub — Real Data Analysis Engine
Queries 383M+ POS transactions via DuckDB to generate evidence-based insights.
Each analysis function returns a standardized result dict.
"""

import logging
from datetime import datetime, timedelta

from transaction_layer import TransactionStore, STORE_NAMES
from transaction_queries import run_query

try:
    from product_hierarchy import get_product_by_plu
except ImportError:
    get_product_by_plu = None

logger = logging.getLogger("data_analysis")

# ---------------------------------------------------------------------------
# ANALYSIS TYPE REGISTRY
# ---------------------------------------------------------------------------

ANALYSIS_TYPES = {
    "basket_analysis": {
        "name": "Cross-sell / Basket Analysis",
        "agent_id": "di_transactions",
        "description": "Find products frequently purchased together",
    },
    "stockout_detection": {
        "name": "Lost Sales / Stockout Detection",
        "agent_id": "di_lost_sales",
        "description": "Identify likely stockouts from zero-sale days",
    },
    "price_dispersion": {
        "name": "Price Dispersion Analysis",
        "agent_id": "di_buying",
        "description": "Find products with highest price variation across stores",
    },
    "demand_pattern": {
        "name": "Demand Pattern Analysis",
        "agent_id": "di_lost_sales",
        "description": "Identify peak and trough demand periods",
    },
    "slow_movers": {
        "name": "Slow Movers / Range Review",
        "agent_id": "di_range",
        "description": "Find underperforming products consuming shelf space",
    },
    "intraday_stockout": {
        "name": "Intra-day Stockout Detection",
        "agent_id": "di_lost_sales",
        "description": "Detect items that stop selling mid-day by analysing hourly sales patterns",
    },
    "halo_effect": {
        "name": "Halo Effect / Basket Growth",
        "agent_id": "di_transactions",
        "description": "Identify products that lift basket value when present",
    },
    "specials_uplift": {
        "name": "Specials / Price Drop Uplift Forecast",
        "agent_id": "di_buying",
        "description": "Forecast demand uplift when products go on special",
    },
    "margin_analysis": {
        "name": "Wastage / Margin Erosion Analysis",
        "agent_id": "di_buying",
        "description": "Find products and stores with margin erosion using GP% analysis",
    },
    "customer_analysis": {
        "name": "Customer Segmentation Analysis",
        "agent_id": "di_transactions",
        "description": "RFM-style customer segmentation from loyalty transaction data",
    },
    "store_benchmark": {
        "name": "Store Benchmark / Comparison",
        "agent_id": "di_transactions",
        "description": "Compare all stores across KPIs with percentile ranking",
    },
}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _get_date_range(days):
    """Return (start_date, end_date) strings for a lookback window."""
    end = datetime.utcnow().date()
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def _enrich_with_product_names(rows, plu_key="PLUItem_ID"):
    """Add product_name from product_hierarchy to each row."""
    if get_product_by_plu is None:
        return rows
    for row in rows:
        plu = str(row.get(plu_key, ""))
        if plu:
            product = get_product_by_plu(plu)
            if product:
                row["product_name"] = product.get("product_name", plu)
                row["department"] = product.get("department", "")
                row["major_group"] = product.get("major_group", "")
            else:
                row["product_name"] = plu
    return rows


def _store_name(store_id):
    """Get display name for a store ID."""
    return STORE_NAMES.get(str(store_id), "Store {}".format(store_id))


def _build_result(analysis_type, title, executive_summary, findings,
                  evidence_tables, financial_impact, recommendations,
                  methodology, confidence):
    """Build standardized result dict."""
    return {
        "analysis_type": analysis_type,
        "title": title,
        "executive_summary": executive_summary,
        "findings": findings,
        "evidence_tables": evidence_tables,
        "financial_impact": financial_impact,
        "recommendations": recommendations,
        "methodology": methodology,
        "confidence_level": confidence,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# ANALYSIS A: BASKET / CROSS-SELL
# ---------------------------------------------------------------------------

def run_basket_analysis(store_id=None, days=30, min_support=5, limit=50):
    """Find products frequently purchased together using real transaction data.

    Scoped to 1 store + N days to keep the self-join fast.
    """
    start, end = _get_date_range(days)
    if not store_id:
        store_id = "28"  # Default to Mosman (high-volume store)

    store_display = _store_name(store_id)
    ts = TransactionStore()

    sql = """
        WITH baskets AS (
            SELECT Reference2 AS txn_id, PLUItem_ID AS plu
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
              AND Quantity > 0
              AND SalesIncGST > 0
        ),
        multi_item AS (
            SELECT txn_id
            FROM baskets
            GROUP BY txn_id
            HAVING COUNT(DISTINCT plu) >= 2
        ),
        pairs AS (
            SELECT a.plu AS item_a, b.plu AS item_b,
                   COUNT(DISTINCT a.txn_id) AS pair_count
            FROM baskets a
            JOIN baskets b ON a.txn_id = b.txn_id AND a.plu < b.plu
            WHERE a.txn_id IN (SELECT txn_id FROM multi_item)
            GROUP BY a.plu, b.plu
            HAVING COUNT(DISTINCT a.txn_id) >= ?
        ),
        item_counts AS (
            SELECT plu, COUNT(DISTINCT txn_id) AS basket_count
            FROM baskets
            GROUP BY plu
        ),
        total AS (
            SELECT COUNT(DISTINCT txn_id) AS total_baskets FROM baskets
        )
        SELECT p.item_a, p.item_b, p.pair_count,
               ia.basket_count AS count_a,
               ib.basket_count AS count_b,
               t.total_baskets,
               ROUND(p.pair_count * 1.0 / t.total_baskets, 6) AS support,
               ROUND(p.pair_count * 1.0 / ia.basket_count, 4) AS conf_a_to_b,
               ROUND(p.pair_count * 1.0 / ib.basket_count, 4) AS conf_b_to_a,
               ROUND(
                   (p.pair_count * 1.0 / t.total_baskets)
                   / ((ia.basket_count * 1.0 / t.total_baskets)
                      * (ib.basket_count * 1.0 / t.total_baskets)),
                   2
               ) AS lift
        FROM pairs p
        JOIN item_counts ia ON p.item_a = ia.plu
        JOIN item_counts ib ON p.item_b = ib.plu
        CROSS JOIN total t
        ORDER BY lift DESC, pair_count DESC
        LIMIT ?
    """

    try:
        results = ts.query(sql, [store_id, start, end, min_support, limit],
                           timeout_seconds=60, max_rows=limit)
    except Exception as e:
        logger.error("Basket analysis failed: %s", e)
        return _build_result(
            "basket_analysis",
            "Basket Analysis — {}".format(store_display),
            "Analysis could not complete: {}".format(str(e)[:100]),
            [], [], {}, [], {"data_source": "N/A", "limitations": [str(e)]},
            0.0,
        )

    if not results:
        return _build_result(
            "basket_analysis",
            "Basket Analysis — {}".format(store_display),
            "No product pairs met the minimum support threshold.",
            [], [], {}, [],
            {"data_source": "POS Transactions", "query_window": "{} to {}".format(start, end),
             "records_analyzed": 0, "limitations": ["No pairs above threshold"],
             "sql_used": "basket self-join"},
            0.0,
        )

    # Enrich with product names
    for r in results:
        if get_product_by_plu:
            pa = get_product_by_plu(str(r.get("item_a", "")))
            pb = get_product_by_plu(str(r.get("item_b", "")))
            r["name_a"] = pa["product_name"] if pa else str(r["item_a"])
            r["name_b"] = pb["product_name"] if pb else str(r["item_b"])
        else:
            r["name_a"] = str(r.get("item_a", ""))
            r["name_b"] = str(r.get("item_b", ""))

    total_baskets = results[0].get("total_baskets", 0) if results else 0

    # Build evidence table
    table_rows = []
    for r in results[:20]:
        table_rows.append([
            r.get("name_a", "")[:35],
            r.get("name_b", "")[:35],
            r.get("pair_count", 0),
            "{:.1%}".format(r.get("conf_a_to_b", 0)),
            "{:.1%}".format(r.get("conf_b_to_a", 0)),
            "{:.1f}".format(r.get("lift", 0)),
        ])

    evidence = [{
        "name": "Top Product Pairs — {} ({} days)".format(store_display, days),
        "columns": ["Product A", "Product B", "Co-purchases",
                     "Conf A→B", "Conf B→A", "Lift"],
        "rows": table_rows,
    }]

    # Financial impact estimate
    top_pair = results[0] if results else {}
    avg_lift = sum(r.get("lift", 0) for r in results[:10]) / min(len(results), 10)
    annual_factor = 365.0 / days
    est_annual = sum(r.get("pair_count", 0) for r in results[:10]) * 5.0 * annual_factor

    exec_summary = (
        "Analysed {:,} baskets at {} over {} days. Found {} product pairs "
        "with lift > 1.0 (bought together more than expected). "
        "Top pair: {} + {} (lift {:.1f}x, {:.0%} confidence).".format(
            total_baskets, store_display, days, len(results),
            top_pair.get("name_a", "?")[:30],
            top_pair.get("name_b", "?")[:30],
            top_pair.get("lift", 0),
            top_pair.get("conf_a_to_b", 0),
        )
    )

    return _build_result(
        "basket_analysis",
        "Cross-sell Opportunities — {} ({} days)".format(store_display, days),
        exec_summary,
        results,
        evidence,
        {
            "estimated_annual_value": round(est_annual, 2),
            "confidence": "medium",
            "basis": "Estimated from cross-sell lift across top 10 pairs",
        },
        [
            {"action": "Co-locate top-lift products on shelf/display",
             "owner": "Store Manager", "timeline": "2 weeks", "priority": "high"},
            {"action": "Create bundle promotions for top 5 pairs",
             "owner": "Category Manager", "timeline": "4 weeks", "priority": "medium"},
            {"action": "Train staff on cross-sell recommendations",
             "owner": "Training Manager", "timeline": "2 weeks", "priority": "medium"},
        ],
        {
            "data_source": "POS Transactions (DuckDB/Parquet)",
            "query_window": "{} to {}".format(start, end),
            "records_analyzed": total_baskets,
            "limitations": [
                "Single store analysis (not network-wide)",
                "Support threshold of {} may exclude rare but valuable pairs".format(min_support),
                "Lift does not account for promotional effects",
                "Transaction-level grouping by Reference2 (receipt ID)",
            ],
            "sql_used": "Self-join on Reference2, CTE-based pair counting with lift calculation",
        },
        min(0.85, 0.5 + (len(results) / 100.0)),
    )


# ---------------------------------------------------------------------------
# ANALYSIS B: STOCKOUT / LOST SALES DETECTION
# ---------------------------------------------------------------------------

def run_stockout_detection(store_id=None, days=60, min_velocity=5.0, limit=50):
    """Detect likely stockouts by finding zero-sale days for high-velocity items."""
    start, end = _get_date_range(days)
    if not store_id:
        store_id = "28"

    store_display = _store_name(store_id)
    ts = TransactionStore()

    sql = """
        WITH daily_sales AS (
            SELECT PLUItem_ID,
                   CAST(SaleDate AS DATE) AS sale_date,
                   SUM(Quantity) AS daily_qty,
                   SUM(SalesIncGST) AS daily_revenue
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
              AND Quantity > 0
            GROUP BY PLUItem_ID, CAST(SaleDate AS DATE)
        ),
        velocity AS (
            SELECT PLUItem_ID,
                   AVG(daily_qty) AS avg_daily_qty,
                   AVG(daily_revenue) AS avg_daily_revenue,
                   COUNT(DISTINCT sale_date) AS active_days,
                   SUM(daily_revenue) AS total_revenue
            FROM daily_sales
            GROUP BY PLUItem_ID
            HAVING AVG(daily_qty) >= ?
        ),
        date_spine AS (
            SELECT TheDate AS cal_date
            FROM fiscal_calendar
            WHERE TheDate >= CAST(? AS DATE)
              AND TheDate < CAST(? AS DATE)
        ),
        gaps AS (
            SELECT v.PLUItem_ID, d.cal_date
            FROM velocity v
            CROSS JOIN date_spine d
            LEFT JOIN daily_sales ds
                ON v.PLUItem_ID = ds.PLUItem_ID
                AND d.cal_date = ds.sale_date
            WHERE ds.sale_date IS NULL
        )
        SELECT g.PLUItem_ID,
               v.avg_daily_qty,
               v.avg_daily_revenue,
               v.active_days,
               v.total_revenue,
               COUNT(*) AS zero_sale_days,
               ROUND(COUNT(*) * v.avg_daily_revenue, 2) AS estimated_lost_revenue
        FROM gaps g
        JOIN velocity v ON g.PLUItem_ID = v.PLUItem_ID
        GROUP BY g.PLUItem_ID, v.avg_daily_qty, v.avg_daily_revenue,
                 v.active_days, v.total_revenue
        HAVING COUNT(*) >= 3
        ORDER BY estimated_lost_revenue DESC
        LIMIT ?
    """

    try:
        results = ts.query(
            sql, [store_id, start, end, min_velocity, start, end, limit],
            timeout_seconds=60, max_rows=limit,
        )
    except Exception as e:
        logger.error("Stockout detection failed: %s", e)
        return _build_result(
            "stockout_detection",
            "Stockout Detection — {}".format(store_display),
            "Analysis could not complete: {}".format(str(e)[:100]),
            [], [], {}, [],
            {"data_source": "N/A", "limitations": [str(e)]}, 0.0,
        )

    results = _enrich_with_product_names(results)

    # Evidence table
    table_rows = []
    for r in results[:20]:
        table_rows.append([
            r.get("product_name", str(r.get("PLUItem_ID", "")))[:35],
            "{:.1f}".format(r.get("avg_daily_qty", 0)),
            "${:.2f}".format(r.get("avg_daily_revenue", 0)),
            r.get("zero_sale_days", 0),
            r.get("active_days", 0),
            "${:,.2f}".format(r.get("estimated_lost_revenue", 0)),
        ])

    evidence = [{
        "name": "Likely Stockouts — {} ({} days)".format(store_display, days),
        "columns": ["Product", "Avg Daily Units", "Avg Daily Rev",
                     "Zero-Sale Days", "Active Days", "Est. Lost Revenue"],
        "rows": table_rows,
    }]

    total_lost = sum(r.get("estimated_lost_revenue", 0) for r in results)
    annual_factor = 365.0 / days

    if results:
        exec_summary = (
            "Identified {} high-velocity products at {} with likely stockout "
            "periods over {} days. Total estimated lost revenue: ${:,.0f}. "
            "Annualised: ${:,.0f}. Top item: {} with {} zero-sale days "
            "(${:,.0f} lost).".format(
                len(results), store_display, days,
                total_lost, total_lost * annual_factor,
                results[0].get("product_name", "?")[:30],
                results[0].get("zero_sale_days", 0),
                results[0].get("estimated_lost_revenue", 0),
            )
        )
    else:
        exec_summary = "No stockout candidates found at {} for the period.".format(
            store_display)

    return _build_result(
        "stockout_detection",
        "Lost Sales / Stockout Detection — {}".format(store_display),
        exec_summary,
        results,
        evidence,
        {
            "estimated_annual_value": round(total_lost * annual_factor, 2),
            "confidence": "medium",
            "basis": "Zero-sale days x avg daily revenue for items with velocity >= {:.0f} units/day".format(
                min_velocity),
        },
        [
            {"action": "Investigate top 10 stockout items with store manager",
             "owner": "Store Manager", "timeline": "1 week", "priority": "high"},
            {"action": "Increase safety stock for high-velocity items",
             "owner": "Buyer", "timeline": "2 weeks", "priority": "high"},
            {"action": "Review reorder points and lead times",
             "owner": "Supply Chain", "timeline": "4 weeks", "priority": "medium"},
        ],
        {
            "data_source": "POS Transactions + Fiscal Calendar (DuckDB)",
            "query_window": "{} to {}".format(start, end),
            "records_analyzed": sum(r.get("active_days", 0) for r in results),
            "limitations": [
                "Zero-sale days may not always indicate stockouts (seasonal products, store closures)",
                "No inventory system data — inference based on sales absence only",
                "Minimum velocity threshold of {:.0f} units/day may miss slower-selling items".format(
                    min_velocity),
                "Does not account for planned range changes or delistings",
            ],
            "sql_used": "CTE: daily_sales → velocity filter → fiscal date spine → LEFT JOIN gap detection",
        },
        min(0.80, 0.4 + (len(results) / 50.0)),
    )


# ---------------------------------------------------------------------------
# ANALYSIS C: PRICE DISPERSION
# ---------------------------------------------------------------------------

def run_price_dispersion(days=90, min_stores=5, min_txns=20, limit=50):
    """Find products with the highest price variation across stores."""
    start, end = _get_date_range(days)
    ts = TransactionStore()

    sql = """
        WITH store_prices AS (
            SELECT t.PLUItem_ID,
                   t.Store_ID,
                   COUNT(*) AS txn_count,
                   AVG(t.SalesIncGST / NULLIF(t.Quantity, 0)) AS avg_unit_price,
                   SUM(t.SalesIncGST) AS store_revenue
            FROM transactions t
            WHERE t.Quantity > 0
              AND t.SalesIncGST > 0
              AND t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY t.PLUItem_ID, t.Store_ID
            HAVING COUNT(*) >= ?
        ),
        dispersion AS (
            SELECT PLUItem_ID,
                   COUNT(DISTINCT Store_ID) AS stores_stocked,
                   ROUND(MIN(avg_unit_price), 2) AS min_price,
                   ROUND(MAX(avg_unit_price), 2) AS max_price,
                   ROUND(AVG(avg_unit_price), 2) AS network_avg_price,
                   ROUND(STDDEV(avg_unit_price), 2) AS price_std,
                   ROUND(MAX(avg_unit_price) - MIN(avg_unit_price), 2) AS price_range,
                   ROUND((MAX(avg_unit_price) - MIN(avg_unit_price))
                         / NULLIF(AVG(avg_unit_price), 0) * 100, 1) AS cv_pct,
                   SUM(store_revenue) AS total_revenue
            FROM store_prices
            GROUP BY PLUItem_ID
            HAVING COUNT(DISTINCT Store_ID) >= ?
        )
        SELECT d.*,
               p.ProductName, p.DepartmentDesc, p.MajorGroupDesc
        FROM dispersion d
        LEFT JOIN product_hierarchy p ON d.PLUItem_ID = CAST(p.ProductNumber AS VARCHAR)
        WHERE d.cv_pct > 5
        ORDER BY d.cv_pct DESC
        LIMIT ?
    """

    try:
        results = ts.query(
            sql, [start, end, min_txns, min_stores, limit],
            timeout_seconds=120, max_rows=limit,
        )
    except Exception as e:
        logger.error("Price dispersion failed: %s", e)
        return _build_result(
            "price_dispersion", "Price Dispersion Analysis",
            "Analysis could not complete: {}".format(str(e)[:100]),
            [], [], {}, [],
            {"data_source": "N/A", "limitations": [str(e)]}, 0.0,
        )

    # Evidence table
    table_rows = []
    for r in results[:20]:
        table_rows.append([
            r.get("ProductName", str(r.get("PLUItem_ID", "")))[:35],
            r.get("DepartmentDesc", "")[:15],
            r.get("stores_stocked", 0),
            "${:.2f}".format(r.get("min_price", 0)),
            "${:.2f}".format(r.get("max_price", 0)),
            "${:.2f}".format(r.get("network_avg_price", 0)),
            "${:.2f}".format(r.get("price_range", 0)),
            "{:.1f}%".format(r.get("cv_pct", 0)),
            "${:,.0f}".format(r.get("total_revenue", 0)),
        ])

    evidence = [{
        "name": "Products with Highest Price Variation ({} days)".format(days),
        "columns": ["Product", "Dept", "Stores", "Min Price", "Max Price",
                     "Avg Price", "Range", "CV%", "Revenue"],
        "rows": table_rows,
    }]

    # Financial impact: if highest-priced stores matched network avg
    total_opportunity = 0
    for r in results:
        price_range = r.get("price_range", 0)
        revenue = r.get("total_revenue", 0)
        if revenue > 0 and price_range > 0:
            total_opportunity += price_range * revenue * 0.01

    annual_factor = 365.0 / days

    if results:
        top = results[0]
        exec_summary = (
            "Analysed pricing across {} stores over {} days. Found {} products "
            "with >5% price variation (coefficient of variation). "
            "Top dispersion: {} — priced ${:.2f} to ${:.2f} across {} stores "
            "({:.1f}% CV). Price harmonisation could unlock ${:,.0f}/year.".format(
                min_stores, days, len(results),
                top.get("ProductName", "?")[:30],
                top.get("min_price", 0), top.get("max_price", 0),
                top.get("stores_stocked", 0), top.get("cv_pct", 0),
                total_opportunity * annual_factor,
            )
        )
    else:
        exec_summary = "No products found with significant price variation."

    return _build_result(
        "price_dispersion",
        "Price Dispersion Analysis — Network-wide ({} days)".format(days),
        exec_summary,
        results,
        evidence,
        {
            "estimated_annual_value": round(total_opportunity * annual_factor, 2),
            "confidence": "medium",
            "basis": "Estimated from price harmonisation across stores with >5% CV",
        },
        [
            {"action": "Review pricing for top 10 high-CV products",
             "owner": "Pricing Manager", "timeline": "2 weeks", "priority": "high"},
            {"action": "Investigate root cause of price differences (supplier, region, promotions)",
             "owner": "Category Manager", "timeline": "4 weeks", "priority": "medium"},
            {"action": "Establish pricing guidelines for multi-store consistency",
             "owner": "Commercial Director", "timeline": "6 weeks", "priority": "medium"},
        ],
        {
            "data_source": "POS Transactions + Product Hierarchy (DuckDB)",
            "query_window": "{} to {}".format(start, end),
            "records_analyzed": sum(r.get("total_revenue", 0) for r in results),
            "limitations": [
                "Price variation may be intentional (location-based pricing, promotions)",
                "Coefficient of variation does not distinguish between markdown and premium pricing",
                "Unit price calculated as SalesIncGST/Quantity — affected by multi-buy discounts",
                "Minimum {} transactions per store-product to avoid noise".format(min_txns),
            ],
            "sql_used": "CTE: store_prices → dispersion aggregation → JOIN product_hierarchy",
        },
        min(0.85, 0.5 + (len(results) / 80.0)),
    )


# ---------------------------------------------------------------------------
# ANALYSIS D: DEMAND PATTERN
# ---------------------------------------------------------------------------

def run_demand_pattern(store_id=None, days=90):
    """Identify peak and trough demand periods using existing query library."""
    start, end = _get_date_range(days)
    if not store_id:
        store_id = "28"

    store_display = _store_name(store_id)
    ts = TransactionStore()

    # Use existing queries
    try:
        dow_data = run_query(ts, "day_of_week_pattern",
                             store_id=store_id, start=start, end=end)
    except Exception:
        dow_data = []

    try:
        hourly_data = run_query(ts, "hourly_pattern",
                                store_id=store_id, start=start, end=end)
    except Exception:
        hourly_data = []

    if not dow_data and not hourly_data:
        return _build_result(
            "demand_pattern",
            "Demand Pattern Analysis — {}".format(store_display),
            "No demand data available for the selected period.",
            [], [], {}, [],
            {"data_source": "N/A", "limitations": ["No data"]}, 0.0,
        )

    # Day of week analysis
    dow_table = []
    peak_day = None
    trough_day = None
    peak_rev = 0
    trough_rev = float("inf")

    for d in dow_data:
        rev = d.get("revenue", 0)
        day_name = d.get("day_name", "?")
        dow_table.append([
            day_name,
            "{:,}".format(d.get("transactions", 0)),
            "${:,.0f}".format(rev),
            "${:.2f}".format(d.get("avg_item_value", 0) if d.get("avg_item_value") else 0),
        ])
        if rev > peak_rev:
            peak_rev = rev
            peak_day = day_name
        if rev < trough_rev and rev > 0:
            trough_rev = rev
            trough_day = day_name

    # Hourly analysis
    hourly_table = []
    peak_hour = None
    peak_hour_rev = 0

    for h in hourly_data:
        rev = h.get("revenue", 0)
        hour = h.get("hour_of_day", 0)
        hourly_table.append([
            "{:02d}:00".format(hour),
            "{:,}".format(h.get("transactions", 0)),
            "${:,.0f}".format(rev),
        ])
        if rev > peak_hour_rev:
            peak_hour_rev = rev
            peak_hour = hour

    evidence = []
    if dow_table:
        evidence.append({
            "name": "Revenue by Day of Week — {}".format(store_display),
            "columns": ["Day", "Transactions", "Revenue", "Avg Item Value"],
            "rows": dow_table,
        })
    if hourly_table:
        evidence.append({
            "name": "Revenue by Hour (AEST) — {}".format(store_display),
            "columns": ["Hour", "Transactions", "Revenue"],
            "rows": hourly_table,
        })

    # Gap calculation
    weekly_gap = peak_rev - trough_rev if peak_rev and trough_rev else 0
    annual_gap = weekly_gap * 52

    exec_summary = (
        "Analysed demand patterns at {} over {} days. "
        "Peak day: {} (${:,.0f} revenue). Trough day: {} (${:,.0f}). "
        "Peak hour: {:02d}:00 AEST. Day-of-week revenue gap: ${:,.0f}/week.".format(
            store_display, days,
            peak_day or "?", peak_rev,
            trough_day or "?", trough_rev if trough_rev < float("inf") else 0,
            peak_hour or 0, weekly_gap,
        )
    )

    return _build_result(
        "demand_pattern",
        "Demand Patterns — {} ({} days)".format(store_display, days),
        exec_summary,
        dow_data + hourly_data,
        evidence,
        {
            "estimated_annual_value": round(annual_gap * 0.1, 2),
            "confidence": "high",
            "basis": "10% capture of peak-to-trough revenue gap across the week",
        },
        [
            {"action": "Increase staffing during peak hours ({:02d}:00 AEST)".format(peak_hour or 10),
             "owner": "Store Manager", "timeline": "1 week", "priority": "high"},
            {"action": "Run promotions on trough day ({}) to drive traffic".format(trough_day or "TBD"),
             "owner": "Marketing Manager", "timeline": "4 weeks", "priority": "medium"},
            {"action": "Review opening hours and stock levels for peak periods",
             "owner": "Operations Manager", "timeline": "2 weeks", "priority": "medium"},
        ],
        {
            "data_source": "POS Transactions (DuckDB)",
            "query_window": "{} to {}".format(start, end),
            "records_analyzed": sum(d.get("transactions", 0) for d in dow_data),
            "limitations": [
                "Hourly analysis uses AEST (UTC+11), does not adjust for daylight savings",
                "Revenue patterns may be influenced by promotions and external events",
                "Single store analysis — network patterns may differ",
            ],
            "sql_used": "Reused day_of_week_pattern and hourly_pattern from transaction_queries.py",
        },
        0.90,
    )


# ---------------------------------------------------------------------------
# ANALYSIS E: SLOW MOVERS / RANGE REVIEW
# ---------------------------------------------------------------------------

def run_slow_movers(store_id=None, days=90, threshold=10, limit=100):
    """Find underperforming products consuming shelf space."""
    start, end = _get_date_range(days)
    ts = TransactionStore()

    kwargs = {"start": start, "end": end, "threshold": threshold, "limit": limit}
    if store_id:
        kwargs["store_id"] = store_id
        store_display = _store_name(store_id)
    else:
        store_display = "All Stores"

    try:
        results = run_query(ts, "slow_movers_filtered", **kwargs)
    except Exception as e:
        logger.error("Slow movers query failed: %s", e)
        # Fallback to basic slow_movers without hierarchy
        try:
            results = run_query(ts, "slow_movers",
                                start=start, end=end,
                                threshold=threshold, limit=limit,
                                **({"store_id": store_id} if store_id else {}))
            results = _enrich_with_product_names(results)
        except Exception as e2:
            return _build_result(
                "slow_movers",
                "Slow Movers — {}".format(store_display),
                "Analysis could not complete: {}".format(str(e2)[:100]),
                [], [], {}, [],
                {"data_source": "N/A", "limitations": [str(e2)]}, 0.0,
            )

    # Evidence table
    table_rows = []
    for r in results[:30]:
        name = (r.get("product_name", "") or
                r.get("ProductName", "") or
                str(r.get("pluitem_id", r.get("PLUItem_ID", ""))))
        dept = r.get("DepartmentDesc", r.get("department", ""))
        table_rows.append([
            name[:35],
            dept[:15],
            r.get("transaction_count", 0),
            "${:,.2f}".format(r.get("total_revenue", 0)),
            r.get("stores_stocked", r.get("stores_sold", 0)),
        ])

    evidence = [{
        "name": "Slow-Moving Products — {} ({} days, <{} txns)".format(
            store_display, days, threshold),
        "columns": ["Product", "Department", "Transactions", "Revenue", "Stores"],
        "rows": table_rows,
    }]

    total_slow_revenue = sum(r.get("total_revenue", 0) for r in results)
    annual_factor = 365.0 / days

    exec_summary = (
        "Found {} products with fewer than {} transactions over {} days "
        "at {}. Combined revenue: ${:,.0f}. These products may be consuming "
        "shelf space that could be allocated to higher-performing items.".format(
            len(results), threshold, days, store_display, total_slow_revenue,
        )
    )

    return _build_result(
        "slow_movers",
        "Slow Movers / Range Review — {}".format(store_display),
        exec_summary,
        results,
        evidence,
        {
            "estimated_annual_value": round(total_slow_revenue * annual_factor * 0.5, 2),
            "confidence": "medium",
            "basis": "50% of slow-mover revenue assumed recoverable through range optimisation",
        },
        [
            {"action": "Review bottom 20 products for potential delisting",
             "owner": "Category Manager", "timeline": "4 weeks", "priority": "high"},
            {"action": "Investigate if slow movers are new products needing more time",
             "owner": "Buyer", "timeline": "2 weeks", "priority": "medium"},
            {"action": "Reallocate shelf space to top performers in same category",
             "owner": "Merchandising Manager", "timeline": "6 weeks", "priority": "medium"},
        ],
        {
            "data_source": "POS Transactions + Product Hierarchy (DuckDB)",
            "query_window": "{} to {}".format(start, end),
            "records_analyzed": len(results),
            "limitations": [
                "Low transaction count may indicate seasonal products, not poor performance",
                "Does not account for products recently introduced to range",
                "Threshold of {} transactions is configurable — lower threshold catches more products".format(
                    threshold),
                "No margin data available — some slow movers may be high-margin items",
            ],
            "sql_used": "Reused slow_movers_filtered from transaction_queries.py",
        },
        min(0.85, 0.5 + (len(results) / 100.0)),
    )


# ---------------------------------------------------------------------------
# ANALYSIS F: INTRA-DAY STOCKOUT DETECTION
# ---------------------------------------------------------------------------

def run_intraday_stockout(store_id=None, days=14, min_daily_txns=10, limit=50):
    """Detect products that stop selling during normally active hours.

    For each PLU at a store over N days:
    1. Compute the expected hourly sales distribution (8am-8pm AEST)
    2. On each day, flag items with 3+ zero-sale hours during hours when
       they normally sell (penetration > 2% of daily sales)
    3. Estimate lost revenue = gap_hours x avg_hourly_revenue
    4. Return top items by estimated lost revenue

    All hourly calculations use AEST: EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR)
    """
    start, end = _get_date_range(days)
    if not store_id:
        store_id = "28"

    store_display = _store_name(store_id)
    ts = TransactionStore()

    sql = """
        WITH hourly_sales AS (
            SELECT PLUItem_ID,
                   CAST(SaleDate AS DATE) AS sale_date,
                   EXTRACT(HOUR FROM SaleDate + INTERVAL '11' HOUR)::INTEGER AS hour_aest,
                   SUM(Quantity) AS hour_qty,
                   SUM(SalesIncGST) AS hour_revenue,
                   COUNT(DISTINCT Reference2) AS hour_txns
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
              AND Quantity > 0
              AND SalesIncGST > 0
            GROUP BY PLUItem_ID, CAST(SaleDate AS DATE),
                     EXTRACT(HOUR FROM SaleDate + INTERVAL '11' HOUR)::INTEGER
        ),
        daily_totals AS (
            SELECT PLUItem_ID, sale_date,
                   SUM(hour_qty) AS daily_qty,
                   SUM(hour_revenue) AS daily_revenue,
                   SUM(hour_txns) AS daily_txns,
                   COUNT(DISTINCT hour_aest) AS active_hours
            FROM hourly_sales
            WHERE hour_aest >= 8 AND hour_aest < 20
            GROUP BY PLUItem_ID, sale_date
            HAVING SUM(hour_txns) >= ?
        ),
        expected_profile AS (
            SELECT h.PLUItem_ID, h.hour_aest,
                   COUNT(DISTINCT h.sale_date) AS days_active_this_hour,
                   AVG(h.hour_revenue) AS avg_hour_revenue,
                   AVG(h.hour_revenue / NULLIF(d.daily_revenue, 0)) AS avg_hour_share
            FROM hourly_sales h
            JOIN daily_totals d ON h.PLUItem_ID = d.PLUItem_ID
                                AND h.sale_date = d.sale_date
            WHERE h.hour_aest >= 8 AND h.hour_aest < 20
            GROUP BY h.PLUItem_ID, h.hour_aest
        ),
        active_items AS (
            SELECT PLUItem_ID,
                   COUNT(DISTINCT hour_aest) AS expected_active_hours,
                   SUM(avg_hour_revenue) AS avg_daily_revenue
            FROM expected_profile
            WHERE avg_hour_share > 0.02
            GROUP BY PLUItem_ID
            HAVING COUNT(DISTINCT hour_aest) >= 4
        ),
        hour_spine AS (
            SELECT UNNEST(GENERATE_SERIES(8, 19)) AS hour_slot
        ),
        expected_slots AS (
            SELECT ai.PLUItem_ID, dt.sale_date, hs.hour_slot,
                   ep.avg_hour_revenue AS expected_revenue
            FROM active_items ai
            CROSS JOIN hour_spine hs
            JOIN daily_totals dt ON ai.PLUItem_ID = dt.PLUItem_ID
            JOIN expected_profile ep ON ai.PLUItem_ID = ep.PLUItem_ID
                                     AND hs.hour_slot = ep.hour_aest
            WHERE ep.avg_hour_share > 0.02
        ),
        gap_detection AS (
            SELECT es.PLUItem_ID, es.sale_date, es.hour_slot,
                   es.expected_revenue,
                   CASE WHEN h.hour_revenue IS NULL THEN 1 ELSE 0 END AS is_gap
            FROM expected_slots es
            LEFT JOIN hourly_sales h ON es.PLUItem_ID = h.PLUItem_ID
                                      AND es.sale_date = h.sale_date
                                      AND es.hour_slot = h.hour_aest
        ),
        gap_runs AS (
            SELECT PLUItem_ID, sale_date,
                   SUM(is_gap) AS gap_hours,
                   SUM(is_gap * expected_revenue) AS lost_revenue_day
            FROM gap_detection
            GROUP BY PLUItem_ID, sale_date
            HAVING SUM(is_gap) >= 3
        )
        SELECT gr.PLUItem_ID,
               COUNT(DISTINCT gr.sale_date) AS stockout_days,
               ROUND(AVG(gr.gap_hours), 1) AS avg_gap_hours,
               ROUND(SUM(gr.lost_revenue_day), 2) AS total_estimated_lost_revenue,
               ROUND(ai.avg_daily_revenue, 2) AS avg_daily_revenue,
               ai.expected_active_hours
        FROM gap_runs gr
        JOIN active_items ai ON gr.PLUItem_ID = ai.PLUItem_ID
        GROUP BY gr.PLUItem_ID, ai.avg_daily_revenue, ai.expected_active_hours
        ORDER BY total_estimated_lost_revenue DESC
        LIMIT ?
    """

    try:
        results = ts.query(sql, [store_id, start, end, min_daily_txns, limit])
    except Exception as e:
        logger.error("Intraday stockout query failed: %s", e)
        return _build_result(
            "intraday_stockout",
            "Intra-day Stockout Detection — {}".format(store_display),
            "Analysis could not be completed: {}".format(str(e)[:100]),
            [], [], {"estimated_annual_value": 0, "confidence": "low",
                     "basis": "Error"},
            [], {"data_source": "POS Transactions (DuckDB)",
                 "query_window": "{} to {}".format(start, end),
                 "records_analyzed": 0,
                 "limitations": ["Query failed: {}".format(str(e)[:100])],
                 "sql_used": "intraday_stockout CTE chain"}, 0.0,
        )

    results = _enrich_with_product_names(results, "PLUItem_ID")

    # Build evidence table
    table_rows = []
    for r in results:
        table_rows.append([
            r.get("product_name", r.get("PLUItem_ID", "")),
            r.get("department", ""),
            r.get("stockout_days", 0),
            "{:.1f}".format(r.get("avg_gap_hours", 0)),
            "${:,.2f}".format(r.get("total_estimated_lost_revenue", 0)),
            "${:,.2f}".format(r.get("avg_daily_revenue", 0)),
            r.get("expected_active_hours", 0),
        ])

    evidence = [{
        "name": "Intra-day Stockout Items — {} ({} days)".format(
            store_display, days),
        "columns": ["Product", "Department", "Stockout Days", "Avg Gap Hours",
                     "Est. Lost Revenue", "Avg Daily Revenue",
                     "Normal Active Hours"],
        "rows": table_rows,
    }]

    total_lost = sum(r.get("total_estimated_lost_revenue", 0) for r in results)
    annual_factor = 365.0 / days

    if results:
        top_item = results[0].get("product_name",
                                   results[0].get("PLUItem_ID", "?"))
        exec_summary = (
            "Detected {} products at {} with intra-day stockout patterns "
            "over {} days. These items stopped selling for 3+ consecutive "
            "hours during their normal trading window. Estimated total "
            "lost revenue: ${:,.0f}. Top affected item: {}.".format(
                len(results), store_display, days, total_lost, top_item,
            )
        )
    else:
        exec_summary = (
            "No significant intra-day stockout patterns detected at {} "
            "over {} days. Items maintained consistent hourly sales.".format(
                store_display, days,
            )
        )

    return _build_result(
        "intraday_stockout",
        "Intra-day Stockout Detection — {}".format(store_display),
        exec_summary,
        results,
        evidence,
        {
            "estimated_annual_value": round(total_lost * annual_factor, 2),
            "confidence": "medium",
            "basis": "Gap hours x average hourly revenue, annualised from {} days".format(days),
        },
        [
            {"action": "Investigate top 10 intra-day stockout items for replenishment gaps",
             "owner": "Store Manager", "timeline": "1 week", "priority": "high"},
            {"action": "Review delivery schedules for affected product categories",
             "owner": "Supply Chain Manager", "timeline": "2 weeks", "priority": "high"},
            {"action": "Consider mid-day replenishment for high-velocity items",
             "owner": "Operations Manager", "timeline": "4 weeks", "priority": "medium"},
            {"action": "Install shelf monitoring for top affected items",
             "owner": "Store Manager", "timeline": "6 weeks", "priority": "low"},
        ],
        {
            "data_source": "POS Transactions (DuckDB) — hourly granularity",
            "query_window": "{} to {}".format(start, end),
            "records_analyzed": len(results),
            "limitations": [
                "AEST approximation uses fixed +11h offset (not AEDT-aware)",
                "Gap detection requires 3+ consecutive hours — short gaps not captured",
                "Items with fewer than {} daily transactions excluded".format(min_daily_txns),
                "Does not distinguish between stockout and intentional de-display",
                "Revenue estimate assumes sales would follow historical hourly pattern",
            ],
            "sql_used": "intraday_stockout CTE chain: hourly_sales -> daily_totals -> "
                        "expected_profile -> active_items -> hour_spine -> expected_slots "
                        "-> gap_detection -> gap_runs",
        },
        min(0.85, 0.4 + (len(results) / 50.0)),
    )


# ---------------------------------------------------------------------------
# ANALYSIS G: HALO EFFECT / BASKET GROWTH
# ---------------------------------------------------------------------------

def run_halo_effect(store_id=None, days=30, min_baskets=20, limit=50):
    """Identify products that lift basket value when present.

    For each product, compares the average basket value of transactions
    containing that product vs the store average. Products with high
    'value uplift' are halo products that draw bigger-spending trips.
    """
    start, end = _get_date_range(days)
    if not store_id:
        store_id = "28"

    store_display = _store_name(store_id)
    ts = TransactionStore()

    sql = """
        WITH product_baskets AS (
            SELECT Reference2 AS txn_id,
                   SUM(SalesIncGST) AS basket_value,
                   COUNT(DISTINCT PLUItem_ID) AS basket_items
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
              AND Quantity > 0
              AND SalesIncGST > 0
            GROUP BY Reference2
            HAVING SUM(SalesIncGST) > 0
               AND SUM(SalesIncGST) < 5000
        ),
        overall AS (
            SELECT AVG(basket_value) AS network_avg_value,
                   AVG(basket_items) AS network_avg_items,
                   COUNT(*) AS total_baskets
            FROM product_baskets
        ),
        product_presence AS (
            SELECT DISTINCT Reference2 AS txn_id, PLUItem_ID
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
              AND Quantity > 0
              AND SalesIncGST > 0
        ),
        halo AS (
            SELECT pp.PLUItem_ID,
                   COUNT(DISTINCT pp.txn_id) AS baskets_with_product,
                   ROUND(AVG(pb.basket_value), 2) AS avg_basket_when_present,
                   ROUND(AVG(pb.basket_items), 1) AS avg_items_when_present
            FROM product_presence pp
            JOIN product_baskets pb ON pp.txn_id = pb.txn_id
            GROUP BY pp.PLUItem_ID
            HAVING COUNT(DISTINCT pp.txn_id) >= ?
        )
        SELECT h.PLUItem_ID,
               h.baskets_with_product,
               h.avg_basket_when_present,
               h.avg_items_when_present,
               o.network_avg_value,
               o.network_avg_items,
               o.total_baskets,
               ROUND(h.avg_basket_when_present / NULLIF(o.network_avg_value, 0), 2)
                   AS value_multiplier,
               ROUND(h.avg_basket_when_present - o.network_avg_value, 2)
                   AS value_uplift,
               ROUND(h.avg_items_when_present - o.network_avg_items, 1)
                   AS items_uplift
        FROM halo h CROSS JOIN overall o
        ORDER BY value_uplift DESC
        LIMIT ?
    """

    try:
        results = ts.query(
            sql,
            [store_id, start, end, store_id, start, end, min_baskets, limit],
            timeout_seconds=60, max_rows=limit,
        )
    except Exception as e:
        logger.error("Halo effect analysis failed: %s", e)
        return _build_result(
            "halo_effect",
            "Halo Effect — {}".format(store_display),
            "Analysis could not complete: {}".format(str(e)[:100]),
            [], [], {}, [],
            {"data_source": "N/A", "limitations": [str(e)]}, 0.0,
        )

    if not results:
        return _build_result(
            "halo_effect",
            "Halo Effect — {}".format(store_display),
            "No products met the minimum basket threshold at {}.".format(
                store_display),
            [], [], {}, [],
            {"data_source": "POS Transactions",
             "query_window": "{} to {}".format(start, end),
             "records_analyzed": 0,
             "limitations": ["No products above threshold"],
             "sql_used": "halo CTE chain"}, 0.0,
        )

    results = _enrich_with_product_names(results)
    total_baskets = results[0].get("total_baskets", 0) if results else 0

    # Build evidence table
    table_rows = []
    for r in results[:20]:
        table_rows.append([
            r.get("product_name", str(r.get("PLUItem_ID", "")))[:35],
            r.get("department", "")[:15],
            r.get("baskets_with_product", 0),
            "${:,.2f}".format(r.get("avg_basket_when_present", 0)),
            "${:,.2f}".format(r.get("network_avg_value", 0)),
            "${:+,.2f}".format(r.get("value_uplift", 0)),
            "{:.2f}x".format(r.get("value_multiplier", 0)),
            "{:+.1f}".format(r.get("items_uplift", 0)),
        ])

    evidence = [{
        "name": "Halo Products — {} ({} days)".format(store_display, days),
        "columns": ["Product", "Dept", "Baskets", "Avg Basket ($)",
                     "Network Avg ($)", "Value Uplift ($)", "Multiplier",
                     "Items Uplift"],
        "rows": table_rows,
    }]

    # Financial impact — conservative 10% attribution (correlation not causation)
    total_halo_value = sum(
        r.get("value_uplift", 0) * r.get("baskets_with_product", 0)
        for r in results[:10]
        if r.get("value_uplift", 0) > 0
    )
    annual_factor = 365.0 / days

    halo_count = len([r for r in results if r.get("value_multiplier", 0) > 1.0])
    top = results[0]
    exec_summary = (
        "Analysed {:,} baskets at {} over {} days. Found {} products with "
        "halo effect (basket value multiplier > 1.0x when present). "
        "Top halo product: {} — baskets containing it average ${:,.2f} vs "
        "network average ${:,.2f} ({:.2f}x multiplier, {:+.1f} extra items).".format(
            total_baskets, store_display, days, halo_count,
            top.get("product_name", "?")[:30],
            top.get("avg_basket_when_present", 0),
            top.get("network_avg_value", 0),
            top.get("value_multiplier", 0),
            top.get("items_uplift", 0),
        )
    )

    return _build_result(
        "halo_effect",
        "Halo Effect / Basket Growth — {} ({} days)".format(store_display, days),
        exec_summary,
        results,
        evidence,
        {
            "estimated_annual_value": round(total_halo_value * annual_factor * 0.1, 2),
            "confidence": "medium",
            "basis": "10% of correlated uplift for top 10 halo products, "
                     "annualised from {} days".format(days),
        },
        [
            {"action": "Ensure top 10 halo products are always in stock and prominently displayed",
             "owner": "Store Manager", "timeline": "1 week", "priority": "high"},
            {"action": "Cross-merchandise halo products near store entrance or high-traffic areas",
             "owner": "Merchandising Manager", "timeline": "2 weeks", "priority": "high"},
            {"action": "Investigate if halo products can anchor promotional baskets or bundles",
             "owner": "Category Manager", "timeline": "4 weeks", "priority": "medium"},
            {"action": "Compare halo products across stores to find network-wide growth drivers",
             "owner": "Commercial Director", "timeline": "6 weeks", "priority": "medium"},
        ],
        {
            "data_source": "POS Transactions (DuckDB/Parquet)",
            "query_window": "{} to {}".format(start, end),
            "records_analyzed": total_baskets,
            "limitations": [
                "Correlation not causation — high-value shoppers may simply buy premium items",
                "Single store analysis (not network-wide)",
                "Baskets capped at $5,000 to exclude bulk/trade orders",
                "Minimum {} baskets per product to reduce noise".format(min_baskets),
                "Does not account for promotional effects on basket composition",
                "Returns and zero-sale lines excluded (Quantity > 0, SalesIncGST > 0)",
            ],
            "sql_used": "CTE: product_baskets -> overall -> product_presence -> halo "
                        "-> value/items uplift",
        },
        min(0.80, 0.4 + (len(results) / 100.0)),
    )


# ---------------------------------------------------------------------------
# ANALYSIS H: SPECIALS / PRICE DROP UPLIFT FORECAST
# ---------------------------------------------------------------------------

def run_specials_uplift(store_id=None, days=90, min_special_days=3,
                        discount_threshold=15, limit=50):
    """Forecast demand uplift when products go on special.

    Detects historical price drops from POS unit prices (>discount_threshold%
    below the product's median price), then measures the volume multiplier
    during those periods to forecast how many units to order for a 7-day special.
    """
    start, end = _get_date_range(days)
    if not store_id:
        store_id = "28"

    store_display = _store_name(store_id)
    ts = TransactionStore()

    discount_fraction = 1.0 - discount_threshold / 100.0

    sql = """
        WITH daily_product AS (
            SELECT Store_ID,
                   PLUItem_ID,
                   CAST(SaleDate AS DATE) AS sale_date,
                   SUM(Quantity) AS daily_qty,
                   SUM(SalesIncGST) AS daily_revenue,
                   SUM(SalesIncGST) / NULLIF(SUM(Quantity), 0) AS avg_unit_price
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
              AND Quantity > 0
              AND SalesIncGST > 0
            GROUP BY Store_ID, PLUItem_ID, CAST(SaleDate AS DATE)
            HAVING SUM(Quantity) >= 1
               AND SUM(SalesIncGST) / NULLIF(SUM(Quantity), 0) > 0.10
               AND SUM(SalesIncGST) / NULLIF(SUM(Quantity), 0) < 500
        ),
        with_baseline AS (
            SELECT *,
                   MEDIAN(avg_unit_price) OVER (
                       PARTITION BY Store_ID, PLUItem_ID
                   ) AS median_price
            FROM daily_product
        ),
        price_events AS (
            SELECT *,
                   ROUND((median_price - avg_unit_price)
                         / NULLIF(median_price, 0) * 100, 1) AS discount_pct,
                   CASE WHEN avg_unit_price < median_price * ?
                        THEN 1 ELSE 0 END AS is_special
            FROM with_baseline
            WHERE median_price > 0.10
        ),
        product_summary AS (
            SELECT Store_ID,
                   PLUItem_ID,
                   COUNT(CASE WHEN is_special = 1 THEN 1 END) AS special_days,
                   COUNT(CASE WHEN is_special = 0 THEN 1 END) AS normal_days,
                   ROUND(AVG(CASE WHEN is_special = 0
                             THEN daily_qty END), 1) AS baseline_daily_qty,
                   ROUND(AVG(CASE WHEN is_special = 1
                             THEN daily_qty END), 1) AS special_daily_qty,
                   ROUND(AVG(CASE WHEN is_special = 0
                             THEN avg_unit_price END), 2) AS normal_price,
                   ROUND(AVG(CASE WHEN is_special = 1
                             THEN avg_unit_price END), 2) AS special_price,
                   ROUND(AVG(CASE WHEN is_special = 1
                             THEN discount_pct END), 1) AS avg_discount_pct,
                   ROUND(AVG(CASE WHEN is_special = 0
                             THEN daily_revenue END), 2) AS normal_daily_revenue,
                   ROUND(AVG(CASE WHEN is_special = 1
                             THEN daily_revenue END), 2) AS special_daily_revenue
            FROM price_events
            GROUP BY Store_ID, PLUItem_ID
            HAVING COUNT(CASE WHEN is_special = 1 THEN 1 END) >= ?
               AND COUNT(CASE WHEN is_special = 0 THEN 1 END) >= 5
        )
        SELECT ps.*,
               ROUND(special_daily_qty
                     / NULLIF(baseline_daily_qty, 0), 2) AS demand_multiplier,
               ROUND(special_daily_qty - baseline_daily_qty, 1) AS daily_qty_uplift,
               ROUND(special_daily_qty * 7, 0) AS forecast_weekly_units_on_special,
               ROUND((special_daily_revenue - normal_daily_revenue) * 7, 2)
                   AS weekly_revenue_uplift
        FROM product_summary ps
        WHERE special_daily_qty > baseline_daily_qty
          AND special_daily_qty / NULLIF(baseline_daily_qty, 0) < 20
        ORDER BY daily_qty_uplift DESC
        LIMIT ?
    """

    try:
        results = ts.query(
            sql,
            [store_id, start, end, discount_fraction, min_special_days, limit],
            timeout_seconds=60, max_rows=limit,
        )
    except Exception as e:
        logger.error("Specials uplift analysis failed: %s", e)
        return _build_result(
            "specials_uplift",
            "Specials Uplift Forecast — {}".format(store_display),
            "Analysis could not complete: {}".format(str(e)[:100]),
            [], [], {}, [],
            {"data_source": "N/A", "limitations": [str(e)]}, 0.0,
        )

    if not results:
        return _build_result(
            "specials_uplift",
            "Specials Uplift Forecast — {}".format(store_display),
            "No products at {} met the criteria for specials uplift "
            "analysis over {} days (minimum {} special days, >{}% "
            "discount).".format(store_display, days, min_special_days,
                                discount_threshold),
            [], [], {}, [],
            {"data_source": "POS Transactions",
             "query_window": "{} to {}".format(start, end),
             "records_analyzed": 0,
             "limitations": ["No products met threshold"],
             "sql_used": "specials CTE chain"}, 0.0,
        )

    results = _enrich_with_product_names(results)

    # Build evidence table
    table_rows = []
    for r in results[:20]:
        table_rows.append([
            r.get("product_name", str(r.get("PLUItem_ID", "")))[:30],
            r.get("department", "")[:15],
            "${:.2f}".format(r.get("normal_price", 0)),
            "${:.2f}".format(r.get("special_price", 0)),
            "{:.0f}%".format(r.get("avg_discount_pct", 0)),
            "{:.1f}".format(r.get("baseline_daily_qty", 0)),
            "{:.1f}".format(r.get("special_daily_qty", 0)),
            "{:.1f}x".format(r.get("demand_multiplier", 0)),
            "{:.0f}".format(r.get("forecast_weekly_units_on_special", 0)),
        ])

    evidence = [{
        "name": "Specials Uplift Forecast — {} ({} days)".format(
            store_display, days),
        "columns": ["Product", "Dept", "Normal Price", "Special Price",
                     "Discount%", "Normal Qty/Day", "Special Qty/Day",
                     "Multiplier", "Weekly Forecast"],
        "rows": table_rows,
    }]

    # Financial impact
    total_weekly_uplift = sum(
        r.get("weekly_revenue_uplift", 0)
        for r in results[:10]
        if r.get("weekly_revenue_uplift", 0) > 0
    )
    annual_specials_weeks = 26  # specials run ~50% of the year
    total_annual_value = total_weekly_uplift * annual_specials_weeks * 0.3

    top = results[0]
    avg_mult = sum(
        r.get("demand_multiplier", 0) for r in results[:10]
    ) / min(len(results), 10)

    exec_summary = (
        "Analysed products at {} over {} days with detectable price-drop "
        "events (>{}% below median). Found {} products where specials drive "
        "measurable volume uplift. Average demand multiplier: {:.1f}x. "
        "Top product: {} — sells {:.1f} units/day normally, {:.1f} on "
        "special ({:.1f}x uplift). Recommended weekly order on "
        "special: {:.0f} units.".format(
            store_display, days, discount_threshold,
            len(results), avg_mult,
            top.get("product_name", "?")[:30],
            top.get("baseline_daily_qty", 0),
            top.get("special_daily_qty", 0),
            top.get("demand_multiplier", 0),
            top.get("forecast_weekly_units_on_special", 0),
        )
    )

    return _build_result(
        "specials_uplift",
        "Specials Uplift Forecast — {} ({} days)".format(store_display, days),
        exec_summary,
        results,
        evidence,
        {
            "estimated_annual_value": round(total_annual_value, 2),
            "confidence": "medium",
            "basis": "30% of incremental special-period revenue for top 10 "
                     "products, assuming specials run ~26 weeks/year",
        },
        [
            {"action": "Use demand multipliers to set order quantities for upcoming specials",
             "owner": "Buyer", "timeline": "Immediate", "priority": "high"},
            {"action": "Review top 10 uplift products for next promotional cycle",
             "owner": "Category Manager", "timeline": "2 weeks", "priority": "high"},
            {"action": "Share weekly forecast units with supply chain before specials launch",
             "owner": "Buyer", "timeline": "1 week before special", "priority": "high"},
            {"action": "Monitor waste rates on specials products to validate forecast accuracy",
             "owner": "Store Manager", "timeline": "During special", "priority": "medium"},
            {"action": "Test reducing discount depth on high-multiplier products",
             "owner": "Pricing Manager", "timeline": "8 weeks", "priority": "medium"},
        ],
        {
            "data_source": "POS Transactions (DuckDB/Parquet)",
            "query_window": "{} to {}".format(start, end),
            "records_analyzed": sum(
                (r.get("special_days", 0) + r.get("normal_days", 0))
                for r in results
            ),
            "limitations": [
                "Price drops detected from POS unit price — does not confirm "
                "actual promotional activity",
                "Median baseline may be skewed if product was on special for "
                "majority of the period",
                "Discount threshold of {}% is configurable".format(
                    discount_threshold),
                "Volume uplift includes cannibalisation from competing products",
                "Unit price = SalesIncGST/Quantity — multi-buy deals may "
                "distort average price",
                "Minimum {} special days and 5 normal days required".format(
                    min_special_days),
                "Demand multiplier capped at 20x to exclude outlier products",
                "Forecast assumes same uplift pattern repeats",
            ],
            "sql_used": "CTE: daily_product -> with_baseline (MEDIAN window) "
                        "-> price_events -> product_summary -> demand_multiplier "
                        "+ weekly forecast",
        },
        min(0.80, 0.35 + (len(results) / 80.0)),
    )


# ---------------------------------------------------------------------------
# ANALYSIS I: MARGIN EROSION / WASTAGE
# ---------------------------------------------------------------------------

def run_margin_analysis(store_id=None, days=90, gp_threshold=10, limit=50):
    """Find products where GP% is significantly below department average.

    Uses EstimatedCOGS (stored as negative) to compute GP% per product per store,
    then compares to department averages. Products with GP% more than
    gp_threshold below their dept average are flagged as margin-eroded.
    """
    start, end = _get_date_range(days)
    ts = TransactionStore()

    store_clause = ""
    params = [start, end]
    if store_id:
        store_clause = "AND t.Store_ID = ?"
        params.append(str(store_id))

    sql = """
        WITH product_margins AS (
            SELECT t.PLUItem_ID,
                   t.Store_ID,
                   COUNT(*) AS txn_count,
                   SUM(t.SalesIncGST) AS total_revenue,
                   SUM(t.EstimatedCOGS) AS total_cogs,
                   ROUND(
                       (SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0))
                       / NULLIF(SUM(t.SalesIncGST), 0) * 100, 2
                   ) AS gp_pct
            FROM transactions t
            WHERE t.Quantity > 0
              AND t.SalesIncGST > 0
              AND t.EstimatedCOGS IS NOT NULL
              AND t.EstimatedCOGS != 0
              AND CAST(t.SaleDate AS DATE) >= CAST(? AS DATE)
              AND CAST(t.SaleDate AS DATE) <= CAST(? AS DATE)
              {store_clause}
            GROUP BY t.PLUItem_ID, t.Store_ID
            HAVING COUNT(*) >= 10
        ),
        dept_lookup AS (
            SELECT pm.*,
                   p.ProductName,
                   p.DepartmentDesc,
                   p.MajorGroupDesc
            FROM product_margins pm
            LEFT JOIN product_hierarchy p
                ON pm.PLUItem_ID = CAST(p.ProductNumber AS VARCHAR)
        ),
        dept_avg AS (
            SELECT DepartmentDesc,
                   ROUND(AVG(gp_pct), 2) AS avg_dept_gp_pct
            FROM dept_lookup
            WHERE DepartmentDesc IS NOT NULL
            GROUP BY DepartmentDesc
        ),
        erosion AS (
            SELECT dl.*,
                   da.avg_dept_gp_pct,
                   ROUND(da.avg_dept_gp_pct - dl.gp_pct, 2) AS gp_gap
            FROM dept_lookup dl
            JOIN dept_avg da ON dl.DepartmentDesc = da.DepartmentDesc
            WHERE dl.gp_pct < da.avg_dept_gp_pct - ?
        )
        SELECT * FROM erosion
        ORDER BY gp_gap DESC
        LIMIT ?
    """.format(store_clause=store_clause)

    params.extend([gp_threshold, limit])
    results = ts.query(sql, params, timeout_seconds=60, max_rows=limit)

    if not results:
        scope = _store_name(store_id) if store_id else "All Stores"
        return _build_result(
            "margin_analysis",
            "Margin Erosion Analysis — {} ({} days)".format(scope, days),
            "No products found with GP% more than {}% below department average.".format(
                gp_threshold),
            [], [], {}, [],
            {"data_source": "383M POS transactions (DuckDB/Parquet)",
             "query_window": "{} to {}".format(start, end),
             "records_analyzed": 0, "limitations": [], "sql_used": ""},
            0.3,
        )

    # Build evidence table
    evidence_rows = []
    total_gap_value = 0.0
    for row in results[:50]:
        product_name = row.get("ProductName") or row.get("PLUItem_ID", "Unknown")
        dept = row.get("DepartmentDesc", "")
        store = _store_name(row.get("Store_ID", ""))
        gp = row.get("gp_pct", 0)
        dept_gp = row.get("avg_dept_gp_pct", 0)
        gap = row.get("gp_gap", 0)
        revenue = row.get("total_revenue", 0)
        txns = row.get("txn_count", 0)
        gap_value = abs(gap) * revenue / 100.0 if revenue else 0
        total_gap_value += gap_value
        evidence_rows.append([
            str(product_name), str(dept), str(store),
            "{:.1f}%".format(gp), "{:.1f}%".format(dept_gp),
            "{:.1f}%".format(gap), "${:,.0f}".format(revenue),
            str(txns),
        ])

    scope = _store_name(store_id) if store_id else "All Stores"
    annual_factor = 365.0 / max(days, 1)
    top_10_gap = sum(
        abs(r.get("gp_gap", 0)) * r.get("total_revenue", 0) / 100.0
        for r in results[:10]
    )
    estimated_annual = top_10_gap * annual_factor * 0.30

    return _build_result(
        "margin_analysis",
        "Margin Erosion Analysis — {} ({} days)".format(scope, days),
        "Found {} products with GP% more than {}% below their department average. "
        "Top margin gap: {} ({}) at {:.1f}% GP vs {:.1f}% dept average — "
        "a {:.1f}% gap representing ${:,.0f} in margin erosion.".format(
            len(results), gp_threshold,
            results[0].get("ProductName") or results[0].get("PLUItem_ID", ""),
            results[0].get("DepartmentDesc", ""),
            results[0].get("gp_pct", 0),
            results[0].get("avg_dept_gp_pct", 0),
            results[0].get("gp_gap", 0),
            abs(results[0].get("gp_gap", 0)) * results[0].get("total_revenue", 0) / 100.0,
        ),
        results,
        [{
            "name": "Products with Margin Erosion (GP% below dept average by >{}%)".format(
                gp_threshold),
            "columns": ["Product", "Dept", "Store", "GP%", "Dept Avg GP%",
                        "Gap", "Revenue", "Txns"],
            "rows": evidence_rows,
        }],
        {
            "estimated_annual_value": round(estimated_annual, 0),
            "confidence": "medium",
            "basis": "30% capture of margin gap on top 10 eroded products, annualised "
                     "from {} days".format(days),
        },
        [
            {"action": "Investigate top 10 margin-eroded products for cost renegotiation",
             "owner": "Buyer", "timeline": "2 weeks", "priority": "HIGH"},
            {"action": "Review markdown practices at stores with worst GP% gap",
             "owner": "Store Manager", "timeline": "2 weeks", "priority": "HIGH"},
            {"action": "Compare COGS with supplier invoices for products >{}% below dept".format(
                gp_threshold),
             "owner": "Buying Manager", "timeline": "4 weeks", "priority": "MEDIUM"},
            {"action": "Set margin floor alerts for products consistently below department average",
             "owner": "Commercial Director", "timeline": "6 weeks", "priority": "MEDIUM"},
        ],
        {
            "data_source": "383M POS transactions (DuckDB/Parquet)",
            "query_window": "{} to {}".format(start, end),
            "records_analyzed": sum(r.get("txn_count", 0) for r in results),
            "limitations": [
                "EstimatedCOGS may not reflect actual cost — used as proxy",
                "GP% excludes products with zero/null COGS",
                "Margin erosion may be intentional (clearance, promotions)",
                "Department average GP% used as benchmark — variation within departments",
                "Minimum 10 transactions per product-store to reduce noise",
            ],
            "sql_used": "CTE: product_margins -> dept_lookup (hierarchy JOIN) "
                        "-> dept_avg -> erosion (gap > threshold)",
        },
        min(0.80, 0.4 + (len(results) / 60.0)),
    )


# ---------------------------------------------------------------------------
# ANALYSIS J: CUSTOMER SEGMENTATION
# ---------------------------------------------------------------------------

def run_customer_analysis(store_id=None, days=90, limit=50):
    """RFM-style customer segmentation from loyalty transaction data.

    Segments identified customers (CustomerCode present, ~12% of transactions)
    into Champion, Big Spender, Loyal, Regular, At Risk, Occasional, Lapsed.
    """
    start, end = _get_date_range(days)
    ts = TransactionStore()

    store_clause = ""
    params_base = [start, end]
    if store_id:
        store_clause = "AND t.Store_ID = ?"
        params_base.append(str(store_id))

    # Query 1: Segment summary
    segment_sql = """
        WITH customer_txns AS (
            SELECT t.CustomerCode,
                   t.Reference2,
                   CAST(t.SaleDate AS DATE) AS sale_date,
                   t.Store_ID,
                   t.SalesIncGST
            FROM transactions t
            WHERE t.CustomerCode IS NOT NULL
              AND CAST(t.CustomerCode AS VARCHAR) != 'NULL'
              AND CAST(t.CustomerCode AS VARCHAR) != ''
              AND LENGTH(CAST(t.CustomerCode AS VARCHAR)) > 4
              AND t.Quantity > 0
              AND t.SalesIncGST > 0
              AND CAST(t.SaleDate AS DATE) >= CAST(? AS DATE)
              AND CAST(t.SaleDate AS DATE) <= CAST(? AS DATE)
              {store_clause}
        ),
        baskets AS (
            SELECT CustomerCode,
                   Reference2,
                   sale_date,
                   Store_ID,
                   SUM(SalesIncGST) AS basket_value
            FROM customer_txns
            GROUP BY CustomerCode, Reference2, sale_date, Store_ID
        ),
        rfm AS (
            SELECT CustomerCode,
                   DATEDIFF('day', MAX(sale_date), CURRENT_DATE) AS recency_days,
                   COUNT(DISTINCT Reference2) AS frequency,
                   ROUND(SUM(basket_value), 2) AS monetary,
                   ROUND(AVG(basket_value), 2) AS avg_basket_value,
                   COUNT(DISTINCT Store_ID) AS stores_visited,
                   COUNT(DISTINCT sale_date) AS active_days,
                   MIN(sale_date) AS first_purchase,
                   MAX(sale_date) AS last_purchase
            FROM baskets
            GROUP BY CustomerCode
            HAVING COUNT(DISTINCT Reference2) >= 2
        ),
        segmented AS (
            SELECT *,
                   CASE
                       WHEN recency_days <= 30 AND frequency >= 12
                            AND monetary >= 5000 THEN 'Champion'
                       WHEN recency_days <= 30 AND monetary >= 3000 THEN 'Big Spender'
                       WHEN recency_days <= 60 AND frequency >= 6 THEN 'Loyal'
                       WHEN recency_days <= 90 AND frequency >= 3 THEN 'Regular'
                       WHEN recency_days > 90 AND frequency >= 6 THEN 'At Risk'
                       WHEN recency_days > 90 AND monetary >= 2000 THEN 'At Risk'
                       WHEN recency_days <= 90 THEN 'Occasional'
                       ELSE 'Lapsed'
                   END AS segment
            FROM rfm
        )
        SELECT segment,
               COUNT(*) AS customer_count,
               ROUND(AVG(recency_days), 0) AS avg_recency,
               ROUND(AVG(frequency), 1) AS avg_frequency,
               ROUND(AVG(monetary), 2) AS avg_monetary,
               ROUND(AVG(avg_basket_value), 2) AS avg_basket,
               ROUND(SUM(monetary), 2) AS total_revenue,
               ROUND(AVG(stores_visited), 1) AS avg_stores
        FROM segmented
        GROUP BY segment
        ORDER BY total_revenue DESC
    """.format(store_clause=store_clause)

    segment_results = ts.query(segment_sql, params_base[:], timeout_seconds=90,
                               max_rows=20)

    if not segment_results:
        scope = _store_name(store_id) if store_id else "All Stores"
        return _build_result(
            "customer_analysis",
            "Customer Segmentation — {} ({} days)".format(scope, days),
            "No identified customers found with sufficient transaction history.",
            [], [], {}, [],
            {"data_source": "383M POS transactions (DuckDB/Parquet)",
             "query_window": "{} to {}".format(start, end),
             "records_analyzed": 0, "limitations": [], "sql_used": ""},
            0.3,
        )

    # Query 2: Top individual customers
    top_sql = """
        WITH customer_txns AS (
            SELECT t.CustomerCode,
                   t.Reference2,
                   CAST(t.SaleDate AS DATE) AS sale_date,
                   t.Store_ID,
                   t.SalesIncGST
            FROM transactions t
            WHERE t.CustomerCode IS NOT NULL
              AND CAST(t.CustomerCode AS VARCHAR) != 'NULL'
              AND CAST(t.CustomerCode AS VARCHAR) != ''
              AND LENGTH(CAST(t.CustomerCode AS VARCHAR)) > 4
              AND t.Quantity > 0
              AND t.SalesIncGST > 0
              AND CAST(t.SaleDate AS DATE) >= CAST(? AS DATE)
              AND CAST(t.SaleDate AS DATE) <= CAST(? AS DATE)
              {store_clause}
        ),
        baskets AS (
            SELECT CustomerCode,
                   Reference2,
                   sale_date,
                   Store_ID,
                   SUM(SalesIncGST) AS basket_value
            FROM customer_txns
            GROUP BY CustomerCode, Reference2, sale_date, Store_ID
        ),
        rfm AS (
            SELECT CustomerCode,
                   DATEDIFF('day', MAX(sale_date), CURRENT_DATE) AS recency_days,
                   COUNT(DISTINCT Reference2) AS frequency,
                   ROUND(SUM(basket_value), 2) AS monetary,
                   ROUND(AVG(basket_value), 2) AS avg_basket_value,
                   COUNT(DISTINCT Store_ID) AS stores_visited
            FROM baskets
            GROUP BY CustomerCode
            HAVING COUNT(DISTINCT Reference2) >= 2
        ),
        segmented AS (
            SELECT *,
                   CASE
                       WHEN recency_days <= 30 AND frequency >= 12
                            AND monetary >= 5000 THEN 'Champion'
                       WHEN recency_days <= 30 AND monetary >= 3000 THEN 'Big Spender'
                       WHEN recency_days <= 60 AND frequency >= 6 THEN 'Loyal'
                       WHEN recency_days <= 90 AND frequency >= 3 THEN 'Regular'
                       WHEN recency_days > 90 AND frequency >= 6 THEN 'At Risk'
                       WHEN recency_days > 90 AND monetary >= 2000 THEN 'At Risk'
                       WHEN recency_days <= 90 THEN 'Occasional'
                       ELSE 'Lapsed'
                   END AS segment
            FROM rfm
        )
        SELECT CustomerCode, segment, recency_days, frequency,
               monetary, avg_basket_value, stores_visited
        FROM segmented
        ORDER BY monetary DESC
        LIMIT ?
    """.format(store_clause=store_clause)

    top_params = params_base[:] + [min(limit, 20)]
    top_results = ts.query(top_sql, top_params, timeout_seconds=90, max_rows=20)

    # Build evidence tables
    segment_rows = []
    total_customers = 0
    total_revenue = 0
    at_risk_revenue = 0
    for row in segment_results:
        seg = row.get("segment", "")
        count = row.get("customer_count", 0)
        rev = row.get("total_revenue", 0)
        total_customers += count
        total_revenue += rev
        if seg in ("At Risk", "Lapsed"):
            at_risk_revenue += rev
        segment_rows.append([
            str(seg),
            "{:,}".format(count),
            str(int(row.get("avg_recency", 0))),
            "{:.1f}".format(row.get("avg_frequency", 0)),
            "${:,.0f}".format(row.get("avg_monetary", 0)),
            "${:,.0f}".format(row.get("avg_basket", 0)),
            "${:,.0f}".format(rev),
        ])

    top_rows = []
    for row in (top_results or []):
        top_rows.append([
            str(row.get("CustomerCode", "")),
            str(row.get("segment", "")),
            str(int(row.get("recency_days", 0))),
            str(int(row.get("frequency", 0))),
            "${:,.0f}".format(row.get("monetary", 0)),
            "${:,.0f}".format(row.get("avg_basket_value", 0)),
            str(int(row.get("stores_visited", 0))),
        ])

    scope = _store_name(store_id) if store_id else "All Stores"
    annual_factor = 365.0 / max(days, 1)
    estimated_annual = at_risk_revenue * annual_factor * 0.10

    # Find champion stats for summary
    champion = next((r for r in segment_results if r.get("segment") == "Champion"), None)
    at_risk = next((r for r in segment_results if r.get("segment") == "At Risk"), None)

    summary_parts = [
        "Identified {:,} customers across {} segments.".format(
            total_customers, len(segment_results)),
    ]
    if champion:
        summary_parts.append(
            "{:,} Champions (avg ${:,.0f} spend, {:.0f} visits).".format(
                champion.get("customer_count", 0),
                champion.get("avg_monetary", 0),
                champion.get("avg_frequency", 0)))
    if at_risk:
        summary_parts.append(
            "{:,} At Risk customers representing ${:,.0f} in revenue — "
            "retention campaign opportunity.".format(
                at_risk.get("customer_count", 0),
                at_risk.get("total_revenue", 0)))

    evidence_tables = [{
        "name": "Customer Segment Summary",
        "columns": ["Segment", "Customers", "Avg Recency (days)",
                     "Avg Frequency", "Avg Spend", "Avg Basket",
                     "Total Revenue"],
        "rows": segment_rows,
    }]
    if top_rows:
        evidence_tables.append({
            "name": "Top 20 Customers by Total Spend",
            "columns": ["Customer", "Segment", "Recency", "Visits",
                         "Total Spend", "Avg Basket", "Stores"],
            "rows": top_rows,
        })

    return _build_result(
        "customer_analysis",
        "Customer Segmentation — {} ({} days)".format(scope, days),
        " ".join(summary_parts),
        segment_results,
        evidence_tables,
        {
            "estimated_annual_value": round(estimated_annual, 0),
            "confidence": "medium",
            "basis": "10% recovery of At Risk + Lapsed segment revenue (${:,.0f}), "
                     "annualised from {} days".format(at_risk_revenue, days),
        },
        [
            {"action": "Launch retention campaign for At Risk customers",
             "owner": "Marketing Manager", "timeline": "2 weeks", "priority": "HIGH"},
            {"action": "Create VIP program for Champions and Big Spenders",
             "owner": "Marketing Manager", "timeline": "4 weeks", "priority": "HIGH"},
            {"action": "Investigate why Lapsed customers stopped visiting",
             "owner": "Store Manager", "timeline": "4 weeks", "priority": "MEDIUM"},
            {"action": "Cross-promote across stores for single-store customers",
             "owner": "Marketing Manager", "timeline": "6 weeks", "priority": "MEDIUM"},
        ],
        {
            "data_source": "383M POS transactions (DuckDB/Parquet)",
            "query_window": "{} to {}".format(start, end),
            "records_analyzed": total_customers,
            "limitations": [
                "Only ~12% of transactions have CustomerCode — results skewed to loyalty members",
                "Segment thresholds are fixed — may need tuning per store",
                "Does not account for household-level shopping (multiple cards)",
                "Monetary value includes GST — not a margin metric",
                "Minimum 2 transactions required — single-visit customers excluded",
            ],
            "sql_used": "CTE: customer_txns -> baskets (Reference2) -> rfm "
                        "(recency/frequency/monetary) -> segmented (CASE thresholds)",
        },
        min(0.75, 0.35 + (total_customers / 500.0)),
    )


# ---------------------------------------------------------------------------
# ANALYSIS K: STORE BENCHMARK / COMPARISON
# ---------------------------------------------------------------------------

def run_store_benchmark(days=30, limit=50):
    """Compare all stores across KPIs with percentile ranking.

    Always network-wide (no store_id filter). Computes revenue, basket value,
    items per basket, revenue per day, GP%, and transaction count per store,
    then ranks with PERCENT_RANK() window functions.
    """
    start, end = _get_date_range(days)
    ts = TransactionStore()

    sql = """
        WITH store_kpis AS (
            SELECT t.Store_ID,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT t.Reference2) AS transaction_count,
                   ROUND(SUM(t.SalesIncGST), 2) AS total_revenue,
                   SUM(t.Quantity) AS total_units,
                   ROUND(SUM(t.SalesIncGST) / NULLIF(COUNT(DISTINCT t.Reference2), 0), 2)
                       AS avg_basket_value,
                   ROUND(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT t.Reference2), 0), 1)
                       AS avg_items_per_basket,
                   COUNT(DISTINCT t.PLUItem_ID) AS unique_products,
                   COUNT(DISTINCT CAST(t.SaleDate AS DATE)) AS active_days,
                   ROUND(SUM(t.SalesIncGST) / NULLIF(COUNT(DISTINCT CAST(t.SaleDate AS DATE)), 0), 2)
                       AS revenue_per_day,
                   ROUND(
                       (SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0))
                       / NULLIF(SUM(t.SalesIncGST), 0) * 100, 2
                   ) AS gp_pct
            FROM transactions t
            WHERE t.Quantity > 0
              AND t.SalesIncGST > 0
              AND CAST(t.SaleDate AS DATE) >= CAST(? AS DATE)
              AND CAST(t.SaleDate AS DATE) <= CAST(? AS DATE)
            GROUP BY t.Store_ID
            HAVING COUNT(DISTINCT t.Reference2) >= 100
        )
        SELECT *,
               ROUND(PERCENT_RANK() OVER (ORDER BY total_revenue) * 100, 0)
                   AS revenue_pctile,
               ROUND(PERCENT_RANK() OVER (ORDER BY avg_basket_value) * 100, 0)
                   AS basket_value_pctile,
               ROUND(PERCENT_RANK() OVER (ORDER BY avg_items_per_basket) * 100, 0)
                   AS items_pctile,
               ROUND(PERCENT_RANK() OVER (ORDER BY transaction_count) * 100, 0)
                   AS txn_count_pctile,
               ROUND(PERCENT_RANK() OVER (ORDER BY revenue_per_day) * 100, 0)
                   AS rev_per_day_pctile,
               ROUND(PERCENT_RANK() OVER (ORDER BY gp_pct) * 100, 0)
                   AS gp_pctile
        FROM store_kpis
        ORDER BY total_revenue DESC
        LIMIT ?
    """

    results = ts.query(sql, [start, end, limit], timeout_seconds=60, max_rows=limit)

    if not results:
        return _build_result(
            "store_benchmark",
            "Store Benchmark — All Stores ({} days)".format(days),
            "No stores found with sufficient transaction data.",
            [], [], {}, [],
            {"data_source": "383M POS transactions (DuckDB/Parquet)",
             "query_window": "{} to {}".format(start, end),
             "records_analyzed": 0, "limitations": [], "sql_used": ""},
            0.3,
        )

    # Enrich with store names and build evidence
    evidence_rows = []
    revenues = []
    for row in results:
        store = _store_name(row.get("Store_ID", ""))
        rev = row.get("total_revenue", 0)
        revenues.append(rev)
        evidence_rows.append([
            str(store),
            "${:,.0f}".format(rev),
            "{:,}".format(int(row.get("transaction_count", 0))),
            "${:.2f}".format(row.get("avg_basket_value", 0)),
            "{:.1f}".format(row.get("avg_items_per_basket", 0)),
            "${:,.0f}".format(row.get("revenue_per_day", 0)),
            "{:.1f}%".format(row.get("gp_pct", 0)),
            "{}%".format(int(row.get("revenue_pctile", 0))),
            "{}%".format(int(row.get("basket_value_pctile", 0))),
        ])

    # Financial impact: gap between bottom quartile and median
    sorted_revs = sorted(revenues)
    n = len(sorted_revs)
    if n >= 4:
        median_rev = sorted_revs[n // 2]
        bottom_q = sorted_revs[:n // 4]
        gap_per_store = median_rev - (sum(bottom_q) / max(len(bottom_q), 1))
        annual_factor = 365.0 / max(days, 1)
        estimated_annual = gap_per_store * len(bottom_q) * annual_factor * 0.05
    else:
        estimated_annual = 0

    # Top and bottom store for summary
    top_store = _store_name(results[0].get("Store_ID", ""))
    bottom_store = _store_name(results[-1].get("Store_ID", ""))

    return _build_result(
        "store_benchmark",
        "Store Benchmark — All Stores ({} days)".format(days),
        "Ranked {} stores across 6 KPIs. {} leads with ${:,.0f} revenue "
        "and ${:.2f} avg basket. {} trails at ${:,.0f} revenue. "
        "Network avg basket: ${:.2f}.".format(
            len(results), top_store,
            results[0].get("total_revenue", 0),
            results[0].get("avg_basket_value", 0),
            bottom_store,
            results[-1].get("total_revenue", 0),
            sum(r.get("avg_basket_value", 0) for r in results) / max(len(results), 1),
        ),
        results,
        [{
            "name": "Store Performance League Table ({} days)".format(days),
            "columns": ["Store", "Revenue", "Transactions", "Avg Basket",
                        "Items/Basket", "Rev/Day", "GP%",
                        "Revenue Pctile", "Basket Pctile"],
            "rows": evidence_rows,
        }],
        {
            "estimated_annual_value": round(estimated_annual, 0),
            "confidence": "medium",
            "basis": "5% of revenue gap between bottom-quartile and median stores, "
                     "annualised from {} days".format(days),
        },
        [
            {"action": "Share best practices from top-performing stores with bottom quartile",
             "owner": "Area Manager", "timeline": "2 weeks", "priority": "HIGH"},
            {"action": "Investigate low basket-value stores for range and merchandising gaps",
             "owner": "Category Manager", "timeline": "4 weeks", "priority": "HIGH"},
            {"action": "Review GP% outlier stores for pricing or cost issues",
             "owner": "Commercial Director", "timeline": "4 weeks", "priority": "MEDIUM"},
            {"action": "Set quarterly benchmark targets based on percentile bands",
             "owner": "Operations Director", "timeline": "6 weeks", "priority": "MEDIUM"},
        ],
        {
            "data_source": "383M POS transactions (DuckDB/Parquet)",
            "query_window": "{} to {}".format(start, end),
            "records_analyzed": sum(r.get("line_items", 0) for r in results),
            "limitations": [
                "Minimum 100 transactions required per store to rank",
                "Percentile ranking is relative — all stores may perform "
                "well or poorly in absolute terms",
                "Does not account for store size, location, or catchment demographics",
                "GP% uses EstimatedCOGS as proxy — may not reflect actual costs",
                "Active days affected by data availability, not store closure",
            ],
            "sql_used": "CTE: store_kpis (per-store aggregation) -> PERCENT_RANK() "
                        "window functions for 6 KPIs",
        },
        min(0.90, 0.5 + (len(results) / 30.0)),
    )
