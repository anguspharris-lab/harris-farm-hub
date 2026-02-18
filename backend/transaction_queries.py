"""
Harris Farm Hub — Pre-built Transaction Query Library
Parameterised SQL queries for common analytics patterns against the
DuckDB-backed transaction parquet files.

Usage:
    from transaction_layer import TransactionStore
    from transaction_queries import run_query

    ts = TransactionStore()
    results = run_query(ts, "store_weekly_trend",
                        store_id="28", start="2025-07-01", end="2026-01-01")
"""

from typing import Optional

# ---------------------------------------------------------------------------
# QUERY DEFINITIONS
# ---------------------------------------------------------------------------

QUERIES = {
    # ------------------------------------------------------------------
    # REVENUE & ITEM RANKING
    # ------------------------------------------------------------------
    "top_items_by_revenue": {
        "description": "Top N items ranked by total revenue",
        "sql": """
            SELECT PLUItem_ID,
                   COUNT(*) AS transaction_count,
                   SUM(Quantity) AS total_qty,
                   SUM(SalesIncGST) AS total_revenue,
                   SUM(EstimatedCOGS) AS total_cogs,
                   SUM(SalesIncGST) + COALESCE(SUM(EstimatedCOGS), 0) AS est_gp,
                   AVG(SalesIncGST) AS avg_price
            FROM transactions
            WHERE SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
            GROUP BY PLUItem_ID
            ORDER BY total_revenue DESC
            LIMIT ?
        """,
        "params": ["start", "end", "limit"],
        "optional": ["store_id"],
    },

    "top_items_by_quantity": {
        "description": "Top N items ranked by quantity sold",
        "sql": """
            SELECT PLUItem_ID,
                   COUNT(*) AS transaction_count,
                   SUM(Quantity) AS total_qty,
                   SUM(SalesIncGST) AS total_revenue,
                   AVG(SalesIncGST / NULLIF(Quantity, 0)) AS avg_unit_price
            FROM transactions
            WHERE SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
            GROUP BY PLUItem_ID
            ORDER BY total_qty DESC
            LIMIT ?
        """,
        "params": ["start", "end", "limit"],
        "optional": ["store_id"],
    },

    # ------------------------------------------------------------------
    # TIME-SERIES TRENDS
    # ------------------------------------------------------------------
    "store_daily_trend": {
        "description": "Daily revenue and transaction trend for a store",
        "sql": """
            SELECT DATE_TRUNC('day', SaleDate) AS period,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT Reference2) AS transactions,
                   SUM(SalesIncGST) AS revenue,
                   SUM(Quantity) AS quantity,
                   SUM(EstimatedCOGS) AS cogs,
                   SUM(SalesIncGST) + COALESCE(SUM(EstimatedCOGS), 0) AS gp
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY 1
            ORDER BY 1
        """,
        "params": ["store_id", "start", "end"],
    },

    "store_weekly_trend": {
        "description": "Weekly revenue and transaction trend for a store",
        "sql": """
            SELECT DATE_TRUNC('week', SaleDate) AS period,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT Reference2) AS transactions,
                   SUM(SalesIncGST) AS revenue,
                   SUM(Quantity) AS quantity,
                   SUM(EstimatedCOGS) AS cogs,
                   SUM(SalesIncGST) + COALESCE(SUM(EstimatedCOGS), 0) AS gp
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY 1
            ORDER BY 1
        """,
        "params": ["store_id", "start", "end"],
    },

    "store_monthly_trend": {
        "description": "Monthly revenue and transaction trend for a store",
        "sql": """
            SELECT DATE_TRUNC('month', SaleDate) AS period,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT Reference2) AS transactions,
                   SUM(SalesIncGST) AS revenue,
                   SUM(Quantity) AS quantity,
                   SUM(EstimatedCOGS) AS cogs,
                   SUM(SalesIncGST) + COALESCE(SUM(EstimatedCOGS), 0) AS gp
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY 1
            ORDER BY 1
        """,
        "params": ["store_id", "start", "end"],
    },

    "network_monthly_trend": {
        "description": "Monthly revenue across entire network (all stores)",
        "sql": """
            SELECT DATE_TRUNC('month', SaleDate) AS period,
                   COUNT(DISTINCT Store_ID) AS active_stores,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT Reference2) AS transactions,
                   SUM(SalesIncGST) AS revenue,
                   SUM(EstimatedCOGS) AS cogs,
                   SUM(SalesIncGST) + COALESCE(SUM(EstimatedCOGS), 0) AS gp
            FROM transactions
            WHERE SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY 1
            ORDER BY 1
        """,
        "params": ["start", "end"],
    },

    # ------------------------------------------------------------------
    # CUSTOMER ANALYSIS
    # ------------------------------------------------------------------
    "customer_purchase_history": {
        "description": "Purchase history for a loyalty customer (12% of transactions have codes)",
        "sql": """
            SELECT DATE_TRUNC('month', SaleDate) AS period,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT Reference2) AS visits,
                   SUM(SalesIncGST) AS spend,
                   COUNT(DISTINCT Store_ID) AS stores_visited,
                   COUNT(DISTINCT PLUItem_ID) AS unique_items
            FROM transactions
            WHERE CustomerCode = ?
              AND CustomerCode IS NOT NULL
              AND CustomerCode != 'NULL'
            GROUP BY 1
            ORDER BY 1
        """,
        "params": ["customer_code"],
    },

    "top_customers_by_spend": {
        "description": "Top N customers by total spend (loyalty members only)",
        "sql": """
            SELECT CustomerCode,
                   COUNT(DISTINCT Reference2) AS visits,
                   SUM(SalesIncGST) AS total_spend,
                   AVG(SalesIncGST) AS avg_item_value,
                   COUNT(DISTINCT Store_ID) AS stores_visited,
                   MIN(SaleDate) AS first_purchase,
                   MAX(SaleDate) AS last_purchase
            FROM transactions
            WHERE CustomerCode IS NOT NULL
              AND CustomerCode != 'NULL'
              AND LENGTH(CustomerCode) > 4
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY CustomerCode
            ORDER BY total_spend DESC
            LIMIT ?
        """,
        "params": ["start", "end", "limit"],
    },

    "customer_rfm_segments": {
        "description": "RFM segmentation for all loyalty customers",
        "sql": """
            WITH rfm AS (
                SELECT CustomerCode,
                       DATEDIFF('day', MAX(SaleDate), CURRENT_TIMESTAMP) AS recency_days,
                       COUNT(DISTINCT Reference2) AS frequency,
                       SUM(SalesIncGST) AS monetary,
                       COUNT(DISTINCT Store_ID) AS stores_visited,
                       MIN(SaleDate) AS first_purchase,
                       MAX(SaleDate) AS last_purchase
                FROM transactions
                WHERE CustomerCode IS NOT NULL
                  AND CustomerCode != 'NULL'
                  AND LENGTH(CustomerCode) > 4
                  AND SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
                GROUP BY CustomerCode
            )
            SELECT CustomerCode, recency_days, frequency, monetary,
                   stores_visited, first_purchase, last_purchase,
                   CASE
                       WHEN recency_days <= 30 AND frequency >= 12 AND monetary >= 5000 THEN 'Champion'
                       WHEN recency_days <= 60 AND frequency >= 6 AND monetary >= 2000 THEN 'High-Value'
                       WHEN recency_days <= 90 AND frequency >= 3 THEN 'Regular'
                       WHEN recency_days <= 180 THEN 'Occasional'
                       ELSE 'Lapsed'
                   END AS segment
            FROM rfm
            ORDER BY monetary DESC
        """,
        "params": ["start", "end"],
    },

    "customer_cohort_retention": {
        "description": "Monthly cohort retention — first purchase month vs activity in following months",
        "sql": """
            WITH first_month AS (
                SELECT CustomerCode,
                       DATE_TRUNC('month', MIN(SaleDate)) AS cohort_month
                FROM transactions
                WHERE CustomerCode IS NOT NULL AND CustomerCode != 'NULL'
                  AND LENGTH(CustomerCode) > 4
                  AND SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
                GROUP BY CustomerCode
            ),
            activity AS (
                SELECT DISTINCT t.CustomerCode,
                       f.cohort_month,
                       DATE_TRUNC('month', t.SaleDate) AS activity_month
                FROM transactions t
                JOIN first_month f ON t.CustomerCode = f.CustomerCode
                WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
                  AND t.SaleDate < CAST(? AS TIMESTAMP)
            )
            SELECT cohort_month,
                   DATEDIFF('month', cohort_month, activity_month) AS months_since,
                   COUNT(DISTINCT CustomerCode) AS active_customers
            FROM activity
            GROUP BY cohort_month, months_since
            ORDER BY cohort_month, months_since
        """,
        "params": ["start", "end", "start", "end"],
    },

    "customer_segment_baskets": {
        "description": "Average basket size and value by RFM segment",
        "sql": """
            WITH rfm AS (
                SELECT CustomerCode,
                       DATEDIFF('day', MAX(SaleDate), CURRENT_TIMESTAMP) AS recency_days,
                       COUNT(DISTINCT Reference2) AS frequency,
                       SUM(SalesIncGST) AS monetary
                FROM transactions
                WHERE CustomerCode IS NOT NULL
                  AND CustomerCode != 'NULL'
                  AND LENGTH(CustomerCode) > 4
                  AND SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
                GROUP BY CustomerCode
            ),
            segments AS (
                SELECT CustomerCode,
                       CASE
                           WHEN recency_days <= 30 AND frequency >= 12 AND monetary >= 5000 THEN 'Champion'
                           WHEN recency_days <= 60 AND frequency >= 6 AND monetary >= 2000 THEN 'High-Value'
                           WHEN recency_days <= 90 AND frequency >= 3 THEN 'Regular'
                           WHEN recency_days <= 180 THEN 'Occasional'
                           ELSE 'Lapsed'
                       END AS segment
                FROM rfm
            ),
            baskets AS (
                SELECT t.CustomerCode,
                       t.Reference2,
                       COUNT(*) AS items,
                       SUM(t.SalesIncGST) AS basket_value
                FROM transactions t
                WHERE t.CustomerCode IS NOT NULL
                  AND t.CustomerCode != 'NULL'
                  AND LENGTH(t.CustomerCode) > 4
                  AND t.SaleDate >= CAST(? AS TIMESTAMP)
                  AND t.SaleDate < CAST(? AS TIMESTAMP)
                GROUP BY t.CustomerCode, t.Reference2
            )
            SELECT s.segment,
                   COUNT(DISTINCT b.CustomerCode) AS customers,
                   COUNT(*) AS total_baskets,
                   AVG(b.items) AS avg_items,
                   AVG(b.basket_value) AS avg_basket_value,
                   MEDIAN(b.basket_value) AS median_basket_value
            FROM baskets b
            JOIN segments s ON b.CustomerCode = s.CustomerCode
            GROUP BY s.segment
            ORDER BY avg_basket_value DESC
        """,
        "params": ["start", "end", "start", "end"],
    },

    "customer_channel_summary": {
        "description": "Store-level channel summary — transactions, revenue, baskets",
        "sql": """
            WITH baskets AS (
                SELECT Store_ID,
                       Reference2,
                       COUNT(*) AS items,
                       SUM(SalesIncGST) AS basket_value,
                       COUNT(DISTINCT CustomerCode) AS identified
                FROM transactions
                WHERE SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
                GROUP BY Store_ID, Reference2
            )
            SELECT Store_ID,
                   COUNT(*) AS total_baskets,
                   SUM(basket_value) AS revenue,
                   AVG(items) AS avg_items,
                   AVG(basket_value) AS avg_basket_value,
                   SUM(CASE WHEN identified > 0 THEN 1 ELSE 0 END) AS identified_baskets
            FROM baskets
            GROUP BY Store_ID
            ORDER BY revenue DESC
        """,
        "params": ["start", "end"],
    },

    "customer_channel_crossover": {
        "description": "Customers using multiple stores (proxy for channel/location loyalty)",
        "sql": """
            WITH cust_stores AS (
                SELECT CustomerCode,
                       COUNT(DISTINCT Store_ID) AS store_count,
                       COUNT(DISTINCT Reference2) AS visits,
                       SUM(SalesIncGST) AS spend
                FROM transactions
                WHERE CustomerCode IS NOT NULL
                  AND CustomerCode != 'NULL'
                  AND LENGTH(CustomerCode) > 4
                  AND SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
                GROUP BY CustomerCode
            )
            SELECT CASE
                     WHEN store_count = 1 THEN 'Single Store'
                     WHEN store_count <= 3 THEN '2-3 Stores'
                     ELSE '4+ Stores'
                   END AS store_loyalty,
                   COUNT(*) AS customer_count,
                   AVG(visits) AS avg_visits,
                   AVG(spend) AS avg_spend,
                   SUM(spend) AS total_spend
            FROM cust_stores
            GROUP BY store_loyalty
            ORDER BY avg_spend DESC
        """,
        "params": ["start", "end"],
    },

    "customer_frequency_distribution": {
        "description": "Visit frequency distribution for loyalty customers",
        "sql": """
            WITH visit_counts AS (
                SELECT CustomerCode,
                       COUNT(DISTINCT Reference2) AS visits
                FROM transactions
                WHERE CustomerCode IS NOT NULL
                  AND CustomerCode != 'NULL'
                  AND LENGTH(CustomerCode) > 4
                  AND SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
                GROUP BY CustomerCode
            )
            SELECT CASE
                     WHEN visits = 1 THEN '1 visit'
                     WHEN visits <= 3 THEN '2-3 visits'
                     WHEN visits <= 6 THEN '4-6 visits'
                     WHEN visits <= 12 THEN '7-12 visits'
                     WHEN visits <= 24 THEN '13-24 visits'
                     ELSE '25+ visits'
                   END AS frequency_bucket,
                   COUNT(*) AS customer_count,
                   AVG(visits) AS avg_visits,
                   MIN(visits) AS min_visits,
                   MAX(visits) AS max_visits
            FROM visit_counts
            GROUP BY frequency_bucket
            ORDER BY min_visits
        """,
        "params": ["start", "end"],
    },

    "customer_ltv_tiers": {
        "description": "Customer lifetime value tiers with tenure and projected annual spend",
        "sql": """
            WITH cust AS (
                SELECT CustomerCode,
                       SUM(SalesIncGST) AS total_spend,
                       COUNT(DISTINCT Reference2) AS visits,
                       COUNT(DISTINCT Store_ID) AS stores,
                       MIN(SaleDate) AS first_purchase,
                       MAX(SaleDate) AS last_purchase,
                       DATEDIFF('month', MIN(SaleDate), MAX(SaleDate)) + 1 AS tenure_months
                FROM transactions
                WHERE CustomerCode IS NOT NULL
                  AND CustomerCode != 'NULL'
                  AND LENGTH(CustomerCode) > 4
                  AND SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
                GROUP BY CustomerCode
            )
            SELECT CASE
                     WHEN total_spend >= 10000 THEN 'Premium ($10K+)'
                     WHEN total_spend >= 5000 THEN 'High ($5K-$10K)'
                     WHEN total_spend >= 2000 THEN 'Medium ($2K-$5K)'
                     WHEN total_spend >= 500 THEN 'Low ($500-$2K)'
                     ELSE 'Minimal (<$500)'
                   END AS ltv_tier,
                   COUNT(*) AS customer_count,
                   AVG(total_spend) AS avg_spend,
                   AVG(visits) AS avg_visits,
                   AVG(tenure_months) AS avg_tenure_months,
                   AVG(total_spend / GREATEST(tenure_months, 1)) AS avg_monthly_spend,
                   AVG(total_spend / GREATEST(tenure_months, 1) * 12) AS projected_annual
            FROM cust
            GROUP BY ltv_tier
            ORDER BY avg_spend DESC
        """,
        "params": ["start", "end"],
    },

    "customer_top_departments": {
        "description": "Department revenue mix for loyalty customers vs all customers",
        "sql": """
            SELECT ph.DepartmentDesc AS Department,
                   SUM(CASE WHEN t.CustomerCode IS NOT NULL
                            AND t.CustomerCode != 'NULL'
                            AND LENGTH(t.CustomerCode) > 4
                       THEN t.SalesIncGST ELSE 0 END) AS loyalty_revenue,
                   SUM(t.SalesIncGST) AS total_revenue,
                   COUNT(DISTINCT CASE WHEN t.CustomerCode IS NOT NULL
                                       AND t.CustomerCode != 'NULL'
                                       AND LENGTH(t.CustomerCode) > 4
                                  THEN t.CustomerCode END) AS loyalty_customers
            FROM transactions t
            LEFT JOIN product_hierarchy ph ON t.PLUItem_ID = ph.ProductNumber
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              AND ph.DepartmentDesc IS NOT NULL
            GROUP BY ph.DepartmentDesc
            ORDER BY total_revenue DESC
        """,
        "params": ["start", "end"],
    },

    # ------------------------------------------------------------------
    # CUSTOMER × PRODUCT HIERARCHY BREAKDOWN
    # ------------------------------------------------------------------
    "customer_by_department": {
        "description": "Loyalty customer metrics by department",
        "sql": """
            SELECT ph.DepartmentDesc AS Department,
                   COUNT(DISTINCT t.CustomerCode) AS customers,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   COUNT(*) AS line_items
            FROM transactions t
            JOIN product_hierarchy ph ON t.PLUItem_ID = ph.ProductNumber
            WHERE t.CustomerCode IS NOT NULL
              AND t.CustomerCode != 'NULL'
              AND LENGTH(t.CustomerCode) > 4
              AND t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              AND ph.DepartmentDesc IS NOT NULL
            GROUP BY ph.DepartmentDesc
            ORDER BY revenue DESC
        """,
        "params": ["start", "end"],
    },

    "customer_by_major_group": {
        "description": "Loyalty customer metrics by category within a department",
        "sql": """
            SELECT ph.MajorGroupDesc AS Category,
                   COUNT(DISTINCT t.CustomerCode) AS customers,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   COUNT(*) AS line_items
            FROM transactions t
            JOIN product_hierarchy ph ON t.PLUItem_ID = ph.ProductNumber
            WHERE t.CustomerCode IS NOT NULL
              AND t.CustomerCode != 'NULL'
              AND LENGTH(t.CustomerCode) > 4
              AND ph.DepartmentCode = ?
              AND t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              AND ph.MajorGroupDesc IS NOT NULL
            GROUP BY ph.MajorGroupDesc
            ORDER BY revenue DESC
        """,
        "params": ["dept_code", "start", "end"],
    },

    "customer_by_minor_group": {
        "description": "Loyalty customer metrics by subcategory within a category",
        "sql": """
            SELECT ph.MinorGroupDesc AS Subcategory,
                   COUNT(DISTINCT t.CustomerCode) AS customers,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   COUNT(*) AS line_items
            FROM transactions t
            JOIN product_hierarchy ph ON t.PLUItem_ID = ph.ProductNumber
            WHERE t.CustomerCode IS NOT NULL
              AND t.CustomerCode != 'NULL'
              AND LENGTH(t.CustomerCode) > 4
              AND ph.DepartmentCode = ?
              AND ph.MajorGroupCode = ?
              AND t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              AND ph.MinorGroupDesc IS NOT NULL
            GROUP BY ph.MinorGroupDesc
            ORDER BY revenue DESC
        """,
        "params": ["dept_code", "major_code", "start", "end"],
    },

    "channel_by_department": {
        "description": "All-customer revenue and loyalty rate by department",
        "sql": """
            SELECT ph.DepartmentDesc AS Department,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   COUNT(DISTINCT t.Store_ID) AS stores,
                   COUNT(DISTINCT CASE WHEN t.CustomerCode IS NOT NULL
                                       AND t.CustomerCode != 'NULL'
                                       AND LENGTH(t.CustomerCode) > 4
                                  THEN t.CustomerCode END) AS loyalty_customers,
                   SUM(CASE WHEN t.CustomerCode IS NOT NULL
                            AND t.CustomerCode != 'NULL'
                            AND LENGTH(t.CustomerCode) > 4
                       THEN t.SalesIncGST ELSE 0 END) AS loyalty_revenue
            FROM transactions t
            JOIN product_hierarchy ph ON t.PLUItem_ID = ph.ProductNumber
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              AND ph.DepartmentDesc IS NOT NULL
            GROUP BY ph.DepartmentDesc
            ORDER BY revenue DESC
        """,
        "params": ["start", "end"],
    },

    "channel_by_major_group": {
        "description": "All-customer revenue and loyalty rate by category within a dept",
        "sql": """
            SELECT ph.MajorGroupDesc AS Category,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   COUNT(DISTINCT CASE WHEN t.CustomerCode IS NOT NULL
                                       AND t.CustomerCode != 'NULL'
                                       AND LENGTH(t.CustomerCode) > 4
                                  THEN t.CustomerCode END) AS loyalty_customers,
                   SUM(CASE WHEN t.CustomerCode IS NOT NULL
                            AND t.CustomerCode != 'NULL'
                            AND LENGTH(t.CustomerCode) > 4
                       THEN t.SalesIncGST ELSE 0 END) AS loyalty_revenue
            FROM transactions t
            JOIN product_hierarchy ph ON t.PLUItem_ID = ph.ProductNumber
            WHERE ph.DepartmentCode = ?
              AND t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              AND ph.MajorGroupDesc IS NOT NULL
            GROUP BY ph.MajorGroupDesc
            ORDER BY revenue DESC
        """,
        "params": ["dept_code", "start", "end"],
    },

    "channel_by_minor_group": {
        "description": "All-customer revenue and loyalty rate by subcategory",
        "sql": """
            SELECT ph.MinorGroupDesc AS Subcategory,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   COUNT(DISTINCT CASE WHEN t.CustomerCode IS NOT NULL
                                       AND t.CustomerCode != 'NULL'
                                       AND LENGTH(t.CustomerCode) > 4
                                  THEN t.CustomerCode END) AS loyalty_customers,
                   SUM(CASE WHEN t.CustomerCode IS NOT NULL
                            AND t.CustomerCode != 'NULL'
                            AND LENGTH(t.CustomerCode) > 4
                       THEN t.SalesIncGST ELSE 0 END) AS loyalty_revenue
            FROM transactions t
            JOIN product_hierarchy ph ON t.PLUItem_ID = ph.ProductNumber
            WHERE ph.DepartmentCode = ?
              AND ph.MajorGroupCode = ?
              AND t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              AND ph.MinorGroupDesc IS NOT NULL
            GROUP BY ph.MinorGroupDesc
            ORDER BY revenue DESC
        """,
        "params": ["dept_code", "major_code", "start", "end"],
    },

    # ------------------------------------------------------------------
    # PRODUCT ANALYSIS
    # ------------------------------------------------------------------
    "plu_across_stores": {
        "description": "Single PLU performance broken down by store",
        "sql": """
            SELECT Store_ID,
                   COUNT(*) AS line_items,
                   SUM(Quantity) AS total_qty,
                   SUM(SalesIncGST) AS revenue,
                   SUM(EstimatedCOGS) AS cogs,
                   AVG(SalesIncGST) AS avg_price
            FROM transactions
            WHERE PLUItem_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY Store_ID
            ORDER BY revenue DESC
        """,
        "params": ["plu_id", "start", "end"],
    },

    "plu_monthly_trend": {
        "description": "Monthly trend for a single PLU item",
        "sql": """
            SELECT DATE_TRUNC('month', SaleDate) AS period,
                   COUNT(*) AS line_items,
                   SUM(Quantity) AS total_qty,
                   SUM(SalesIncGST) AS revenue,
                   AVG(SalesIncGST / NULLIF(Quantity, 0)) AS avg_unit_price
            FROM transactions
            WHERE PLUItem_ID = ?
            GROUP BY 1
            ORDER BY 1
        """,
        "params": ["plu_id"],
    },

    # ------------------------------------------------------------------
    # BASKET ANALYSIS
    # ------------------------------------------------------------------
    "basket_size_distribution": {
        "description": "Distribution of items per transaction (basket size)",
        "sql": """
            WITH baskets AS (
                SELECT Reference2,
                       COUNT(*) AS items,
                       SUM(SalesIncGST) AS basket_value
                FROM transactions
                WHERE Store_ID = ?
                  AND SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
                GROUP BY Reference2
            )
            SELECT items AS basket_size,
                   COUNT(*) AS frequency,
                   AVG(basket_value) AS avg_basket_value,
                   MIN(basket_value) AS min_basket_value,
                   MAX(basket_value) AS max_basket_value
            FROM baskets
            WHERE items <= 50
            GROUP BY items
            ORDER BY items
        """,
        "params": ["store_id", "start", "end"],
    },

    "avg_basket_by_store": {
        "description": "Average basket size and value by store",
        "sql": """
            WITH baskets AS (
                SELECT Store_ID,
                       Reference2,
                       COUNT(*) AS items,
                       SUM(SalesIncGST) AS basket_value
                FROM transactions
                WHERE SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
                GROUP BY Store_ID, Reference2
            )
            SELECT Store_ID,
                   COUNT(*) AS total_baskets,
                   AVG(items) AS avg_items,
                   AVG(basket_value) AS avg_basket_value,
                   MEDIAN(basket_value) AS median_basket_value
            FROM baskets
            GROUP BY Store_ID
            ORDER BY avg_basket_value DESC
        """,
        "params": ["start", "end"],
    },

    # ------------------------------------------------------------------
    # CATEGORY / GST SPLIT
    # ------------------------------------------------------------------
    "gst_category_split": {
        "description": "Revenue split between GST-free (fresh) and GST items",
        "sql": """
            SELECT CASE WHEN t.GST = 0 THEN 'GST-Free (Fresh)'
                        ELSE 'GST (Packaged/Processed)' END AS category,
                   COUNT(*) AS line_items,
                   SUM(t.SalesIncGST) AS revenue,
                   SUM(t.Quantity) AS quantity,
                   SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0) AS gp
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            {fiscal_join}
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {dept_filter}
              {major_filter}
              {minor_filter}
              {hfm_filter}
              {product_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
            GROUP BY 1
            ORDER BY revenue DESC
        """,
        "params": ["start", "end"],
        "optional": ["store_id", "dept_code", "major_code", "minor_code",
                     "hfm_item_code", "product_number"],
    },

    # ------------------------------------------------------------------
    # HOURLY PATTERNS
    # ------------------------------------------------------------------
    "hourly_pattern": {
        "description": "Hourly trading pattern (transactions and revenue by hour of day, AEST)",
        "sql": """
            SELECT EXTRACT(HOUR FROM SaleDate + INTERVAL '11' HOUR) AS hour_of_day,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT Reference2) AS transactions,
                   SUM(SalesIncGST) AS revenue
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY 1
            ORDER BY 1
        """,
        "params": ["store_id", "start", "end"],
    },

    # ------------------------------------------------------------------
    # YEAR-OVER-YEAR COMPARISON
    # ------------------------------------------------------------------
    "yoy_store_monthly": {
        "description": "Year-over-year monthly comparison for a store",
        "sql": """
            SELECT EXTRACT(YEAR FROM SaleDate) AS year,
                   EXTRACT(MONTH FROM SaleDate) AS month,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT Reference2) AS transactions,
                   SUM(SalesIncGST) AS revenue,
                   SUM(EstimatedCOGS) AS cogs
            FROM transactions
            WHERE Store_ID = ?
            GROUP BY 1, 2
            ORDER BY 2, 1
        """,
        "params": ["store_id"],
    },

    # ------------------------------------------------------------------
    # RETURNS / REFUNDS
    # ------------------------------------------------------------------
    "returns_summary": {
        "description": "Returns/refunds analysis (negative quantity or sales)",
        "sql": """
            SELECT Store_ID,
                   COUNT(*) AS return_lines,
                   SUM(SalesIncGST) AS return_value,
                   COUNT(DISTINCT Reference2) AS return_transactions
            FROM transactions
            WHERE (Quantity < 0 OR SalesIncGST < 0)
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY Store_ID
            ORDER BY return_value ASC
        """,
        "params": ["start", "end"],
    },

    # ------------------------------------------------------------------
    # DAY-OF-WEEK PATTERNS
    # ------------------------------------------------------------------
    "day_of_week_pattern": {
        "description": "Revenue and transactions by day of week for a store",
        "sql": """
            SELECT DAYOFWEEK(SaleDate) AS dow_num,
                   DAYNAME(SaleDate) AS day_name,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT Reference2) AS transactions,
                   SUM(SalesIncGST) AS revenue,
                   AVG(SalesIncGST) AS avg_item_value
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY 1, 2
            ORDER BY 1
        """,
        "params": ["store_id", "start", "end"],
    },

    # ------------------------------------------------------------------
    # HOURLY PATTERN (AEDT — UTC+11)
    # ------------------------------------------------------------------
    "hourly_pattern_aest": {
        "description": "Hourly trading pattern with AEDT offset (+11h from UTC)",
        "sql": """
            SELECT EXTRACT(HOUR FROM SaleDate + INTERVAL '11' HOUR) AS hour_aest,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT Reference2) AS transactions,
                   SUM(SalesIncGST) AS revenue
            FROM transactions
            WHERE Store_ID = ?
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY 1
            ORDER BY 1
        """,
        "params": ["store_id", "start", "end"],
    },

    # ------------------------------------------------------------------
    # STORE COMPARISON
    # ------------------------------------------------------------------
    "store_comparison_period": {
        "description": "Compare all stores side-by-side for a date range",
        "sql": """
            SELECT Store_ID,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT Reference2) AS transactions,
                   SUM(SalesIncGST) AS revenue,
                   SUM(Quantity) AS quantity,
                   SUM(EstimatedCOGS) AS cogs,
                   SUM(SalesIncGST) + COALESCE(SUM(EstimatedCOGS), 0) AS gp,
                   AVG(SalesIncGST) AS avg_item_value
            FROM transactions
            WHERE SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY Store_ID
            ORDER BY revenue DESC
        """,
        "params": ["start", "end"],
    },

    # ------------------------------------------------------------------
    # ANOMALY DETECTION
    # ------------------------------------------------------------------
    "anomaly_candidates": {
        "description": "Days with revenue > 2 std dev from store mean",
        "sql": """
            WITH daily AS (
                SELECT DATE_TRUNC('day', t.SaleDate) AS sale_date,
                       SUM(t.SalesIncGST) AS revenue
                FROM transactions t
                JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
                {fiscal_join}
                WHERE t.Store_ID = ?
                  AND t.SaleDate >= CAST(? AS TIMESTAMP)
                  AND t.SaleDate < CAST(? AS TIMESTAMP)
                  {dept_filter}
                  {major_filter}
                  {minor_filter}
                  {hfm_filter}
                  {product_filter}
                  {day_type_filter}
                  {hour_filter}
                  {season_filter}
                  {quarter_filter}
                  {month_filter}
                GROUP BY 1
            ),
            stats AS (
                SELECT AVG(revenue) AS mean_rev,
                       STDDEV(revenue) AS std_rev
                FROM daily
            )
            SELECT d.sale_date,
                   d.revenue,
                   s.mean_rev AS expected,
                   (d.revenue - s.mean_rev) / NULLIF(s.std_rev, 0) AS z_score
            FROM daily d, stats s
            WHERE ABS(d.revenue - s.mean_rev) > 2 * s.std_rev
            ORDER BY ABS(d.revenue - s.mean_rev) DESC
        """,
        "params": ["store_id", "start", "end"],
        "optional": ["dept_code", "major_code", "minor_code",
                     "hfm_item_code", "product_number"],
    },

    # ------------------------------------------------------------------
    # SLOW MOVERS
    # ------------------------------------------------------------------
    "slow_movers": {
        "description": "Items with low transaction count in period",
        "sql": """
            SELECT PLUItem_ID,
                   COUNT(*) AS transaction_count,
                   SUM(Quantity) AS total_qty,
                   SUM(SalesIncGST) AS total_revenue,
                   COUNT(DISTINCT Store_ID) AS stores_stocked
            FROM transactions
            WHERE SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
            GROUP BY PLUItem_ID
            HAVING COUNT(*) < ?
            ORDER BY transaction_count ASC
            LIMIT ?
        """,
        "params": ["start", "end", "threshold", "limit"],
        "optional": ["store_id"],
    },

    # ------------------------------------------------------------------
    # PRICE DISPERSION
    # ------------------------------------------------------------------
    "price_dispersion": {
        "description": "Price variation for a PLU across stores",
        "sql": """
            SELECT Store_ID,
                   COUNT(*) AS line_items,
                   AVG(SalesIncGST / NULLIF(Quantity, 0)) AS avg_unit_price,
                   MIN(SalesIncGST / NULLIF(Quantity, 0)) AS min_unit_price,
                   MAX(SalesIncGST / NULLIF(Quantity, 0)) AS max_unit_price,
                   STDDEV(SalesIncGST / NULLIF(Quantity, 0)) AS std_unit_price
            FROM transactions
            WHERE PLUItem_ID = ?
              AND Quantity > 0
              AND SalesIncGST > 0
              AND SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY Store_ID
            HAVING COUNT(*) >= 10
            ORDER BY avg_unit_price DESC
        """,
        "params": ["plu_id", "start", "end"],
    },

    # ------------------------------------------------------------------
    # REVENUE DECOMPOSITION
    # ------------------------------------------------------------------
    "revenue_decomposition_monthly": {
        "description": "Monthly revenue split: Fresh, Packaged, and Returns",
        "sql": """
            SELECT DATE_TRUNC('month', SaleDate) AS period,
                   SUM(CASE WHEN SalesIncGST >= 0 AND GST = 0
                            THEN SalesIncGST ELSE 0 END) AS fresh_revenue,
                   SUM(CASE WHEN SalesIncGST >= 0 AND GST > 0
                            THEN SalesIncGST ELSE 0 END) AS packaged_revenue,
                   SUM(CASE WHEN SalesIncGST < 0
                            THEN SalesIncGST ELSE 0 END) AS returns_value,
                   SUM(SalesIncGST) AS net_revenue,
                   COUNT(DISTINCT Reference2) AS transactions
            FROM transactions
            WHERE SaleDate >= CAST(? AS TIMESTAMP)
              AND SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
            GROUP BY 1
            ORDER BY 1
        """,
        "params": ["start", "end"],
        "optional": ["store_id"],
    },

    # ------------------------------------------------------------------
    # GST CATEGORY MONTHLY TREND
    # ------------------------------------------------------------------
    "gst_category_monthly_trend": {
        "description": "Monthly GST-free vs GST revenue trend",
        "sql": """
            SELECT DATE_TRUNC('month', t.SaleDate) AS period,
                   CASE WHEN t.GST = 0 THEN 'Fresh' ELSE 'Packaged' END AS category,
                   COUNT(*) AS line_items,
                   SUM(t.SalesIncGST) AS revenue,
                   SUM(t.Quantity) AS quantity
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            {fiscal_join}
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {dept_filter}
              {major_filter}
              {minor_filter}
              {hfm_filter}
              {product_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
            GROUP BY 1, 2
            ORDER BY 1, 2
        """,
        "params": ["start", "end"],
        "optional": ["store_id", "dept_code", "major_code", "minor_code",
                     "hfm_item_code", "product_number"],
    },

    # ------------------------------------------------------------------
    # PRODUCT HIERARCHY QUERIES (require product_hierarchy table)
    # ------------------------------------------------------------------
    "department_revenue": {
        "description": "Revenue/GP/transactions/unique SKUs by department",
        "sql": """
            SELECT p.DepartmentCode, p.DepartmentDesc,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) AS revenue,
                   SUM(t.EstimatedCOGS) AS cogs,
                   SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0) AS gp,
                   COUNT(DISTINCT t.PLUItem_ID) AS unique_skus
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            {fiscal_join}
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
            GROUP BY p.DepartmentCode, p.DepartmentDesc
            ORDER BY revenue DESC
        """,
        "params": ["start", "end"],
        "optional": ["store_id"],
    },

    "major_group_revenue": {
        "description": "Revenue by major group within a department",
        "sql": """
            SELECT p.MajorGroupCode, p.MajorGroupDesc,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) AS revenue,
                   SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0) AS gp,
                   COUNT(DISTINCT t.PLUItem_ID) AS unique_skus
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            {fiscal_join}
            WHERE p.DepartmentCode = ?
              AND t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
            GROUP BY p.MajorGroupCode, p.MajorGroupDesc
            ORDER BY revenue DESC
        """,
        "params": ["dept_code", "start", "end"],
        "optional": ["store_id"],
    },

    "minor_group_revenue": {
        "description": "Revenue by minor group within a major group",
        "sql": """
            SELECT p.MinorGroupCode, p.MinorGroupDesc,
                   COUNT(*) AS line_items,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.PLUItem_ID) AS unique_skus
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            {fiscal_join}
            WHERE p.DepartmentCode = ?
              AND p.MajorGroupCode = ?
              AND t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
            GROUP BY p.MinorGroupCode, p.MinorGroupDesc
            ORDER BY revenue DESC
        """,
        "params": ["dept_code", "major_code", "start", "end"],
        "optional": ["store_id"],
    },

    "department_monthly_trend": {
        "description": "Monthly revenue trend by department",
        "sql": """
            SELECT DATE_TRUNC('month', t.SaleDate) AS period,
                   p.DepartmentCode, p.DepartmentDesc,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.Reference2) AS transactions
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
            GROUP BY 1, p.DepartmentCode, p.DepartmentDesc
            ORDER BY 1, revenue DESC
        """,
        "params": ["start", "end"],
        "optional": ["store_id"],
    },

    "buyer_performance": {
        "description": "Revenue/GP by BuyerId",
        "sql": """
            SELECT p.BuyerId,
                   COUNT(DISTINCT p.DepartmentCode) AS departments,
                   COUNT(DISTINCT t.PLUItem_ID) AS unique_skus,
                   SUM(t.SalesIncGST) AS revenue,
                   SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0) AS gp,
                   COUNT(DISTINCT t.Reference2) AS transactions
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
            GROUP BY p.BuyerId
            ORDER BY revenue DESC
        """,
        "params": ["start", "end"],
        "optional": ["store_id"],
    },

    "top_items_by_department": {
        "description": "Top N items within a department by revenue",
        "sql": """
            SELECT t.PLUItem_ID, p.ProductName,
                   p.MajorGroupDesc, p.MinorGroupDesc,
                   SUM(t.SalesIncGST) AS revenue,
                   SUM(t.Quantity) AS total_qty,
                   COUNT(*) AS transaction_count
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            WHERE p.DepartmentCode = ?
              AND t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
            GROUP BY t.PLUItem_ID, p.ProductName,
                     p.MajorGroupDesc, p.MinorGroupDesc
            ORDER BY revenue DESC
            LIMIT ?
        """,
        "params": ["dept_code", "start", "end", "limit"],
        "optional": ["store_id"],
    },

    "department_store_heatmap": {
        "description": "Department revenue by store matrix",
        "sql": """
            SELECT t.Store_ID, p.DepartmentCode, p.DepartmentDesc,
                   SUM(t.SalesIncGST) AS revenue
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
            GROUP BY t.Store_ID, p.DepartmentCode, p.DepartmentDesc
            ORDER BY t.Store_ID, revenue DESC
        """,
        "params": ["start", "end"],
    },

    # ===================================================================
    # FISCAL CALENDAR QUERIES (10)
    # JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
    # ===================================================================

    "fiscal_weekly_trend": {
        "description": "Revenue/GP/transactions by fiscal week for a FY",
        "sql": """
            SELECT fc.FinYear, fc.FinWeekOfYearNo AS week_no,
                   fc.FinWeekOfYearName AS week_name,
                   MIN(CAST(fc.FinWeekStartDate AS DATE)) AS week_start,
                   MAX(CAST(fc.FinWeekEndDate AS DATE)) AS week_end,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) AS revenue,
                   SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0) AS gp
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            WHERE fc.FinYear = ?
              {store_filter}
            GROUP BY fc.FinYear, fc.FinWeekOfYearNo, fc.FinWeekOfYearName
            ORDER BY fc.FinWeekOfYearNo
        """,
        "params": ["fin_year"],
        "optional": ["store_id"],
    },

    "fiscal_monthly_trend": {
        "description": "Revenue by fiscal month (5-4-4 aligned)",
        "sql": """
            SELECT fc.FinYear, fc.FinMonthOfYearNo AS month_no,
                   fc.FinMonthOfYearName AS month_name,
                   MIN(CAST(fc.TheDate AS DATE)) AS month_start,
                   MAX(CAST(fc.TheDate AS DATE)) AS month_end,
                   COUNT(DISTINCT fc.FinWeekOfYearNo) AS weeks_in_month,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) AS revenue,
                   SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0) AS gp
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            WHERE fc.FinYear = ?
              {store_filter}
            GROUP BY fc.FinYear, fc.FinMonthOfYearNo, fc.FinMonthOfYearName
            ORDER BY fc.FinMonthOfYearNo
        """,
        "params": ["fin_year"],
        "optional": ["store_id"],
    },

    "fiscal_quarter_summary": {
        "description": "Quarter-level KPIs for a fiscal year",
        "sql": """
            SELECT fc.FinYear, fc.FinQuarterOfYearNo AS quarter_no,
                   fc.FinQuarterOfYearName AS quarter_name,
                   MIN(CAST(fc.TheDate AS DATE)) AS quarter_start,
                   MAX(CAST(fc.TheDate AS DATE)) AS quarter_end,
                   COUNT(DISTINCT fc.FinWeekOfYearNo) AS weeks,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0) AS gp,
                   COUNT(DISTINCT t.Store_ID) AS active_stores
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            WHERE fc.FinYear = ?
              {store_filter}
            GROUP BY fc.FinYear, fc.FinQuarterOfYearNo, fc.FinQuarterOfYearName
            ORDER BY fc.FinQuarterOfYearNo
        """,
        "params": ["fin_year"],
        "optional": ["store_id"],
    },

    "fiscal_yoy_weekly": {
        "description": "Week-over-week year-on-year comparison (excludes week 53)",
        "sql": """
            SELECT fc.FinWeekOfYearNo AS week_no,
                   fc.FinYear,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0) AS gp
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            WHERE fc.FinYear IN (?, ?)
              AND fc.FinWeekOfYearNo <= 52
              {store_filter}
            GROUP BY fc.FinWeekOfYearNo, fc.FinYear
            ORDER BY fc.FinWeekOfYearNo, fc.FinYear
        """,
        "params": ["fin_year", "fin_year_2"],
        "optional": ["store_id"],
    },

    "fiscal_yoy_monthly": {
        "description": "Month-over-month year-on-year comparison",
        "sql": """
            SELECT fc.FinMonthOfYearNo AS month_no,
                   fc.FinMonthOfYearName AS month_name,
                   fc.FinYear,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0) AS gp
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            WHERE fc.FinYear IN (?, ?)
              {store_filter}
            GROUP BY fc.FinMonthOfYearNo, fc.FinMonthOfYearName, fc.FinYear
            ORDER BY fc.FinMonthOfYearNo, fc.FinYear
        """,
        "params": ["fin_year", "fin_year_2"],
        "optional": ["store_id"],
    },

    "fiscal_day_of_week": {
        "description": "Day-of-week pattern with business day and weekend flags",
        "sql": """
            SELECT fc.DayOfWeekNo, fc.DayOfWeekName,
                   fc.BusinessDay, fc.Weekend,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) AS revenue
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {dept_filter}
              {major_filter}
              {minor_filter}
              {hfm_filter}
              {product_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
            GROUP BY fc.DayOfWeekNo, fc.DayOfWeekName, fc.BusinessDay, fc.Weekend
            ORDER BY fc.DayOfWeekNo
        """,
        "params": ["start", "end"],
        "optional": ["store_id", "dept_code", "major_code", "minor_code",
                     "hfm_item_code", "product_number"],
    },

    "fiscal_season_comparison": {
        "description": "Season-over-season revenue comparison",
        "sql": """
            SELECT fc.SeasonName, fc.FinYear,
                   SUM(t.SalesIncGST) AS revenue,
                   COUNT(DISTINCT t.Reference2) AS transactions
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            WHERE fc.FinYear IN (?, ?)
              {store_filter}
            GROUP BY fc.SeasonName, fc.FinYear
            ORDER BY fc.SeasonName, fc.FinYear
        """,
        "params": ["fin_year", "fin_year_2"],
        "optional": ["store_id"],
    },

    "fiscal_hourly_by_day_type": {
        "description": "Hourly revenue patterns split by business day vs weekend (AEST)",
        "sql": """
            SELECT fc.BusinessDay AS day_type,
                   EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR) AS hour_of_day,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) AS revenue
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {dept_filter}
              {major_filter}
              {minor_filter}
              {hfm_filter}
              {product_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
            GROUP BY fc.BusinessDay, EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR)
            ORDER BY fc.BusinessDay DESC, hour_of_day
        """,
        "params": ["start", "end"],
        "optional": ["store_id", "dept_code", "major_code", "minor_code",
                     "hfm_item_code", "product_number"],
    },

    "fiscal_hourly_heatmap": {
        "description": "Day-of-week x hour-of-day revenue heatmap (AEST)",
        "sql": """
            SELECT fc.DayOfWeekNo, fc.DayOfWeekName,
                   EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR) AS hour_of_day,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) AS revenue
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {dept_filter}
              {major_filter}
              {minor_filter}
              {hfm_filter}
              {product_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
            GROUP BY fc.DayOfWeekNo, fc.DayOfWeekName,
                     EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR)
            ORDER BY fc.DayOfWeekNo, hour_of_day
        """,
        "params": ["start", "end"],
        "optional": ["store_id", "dept_code", "major_code", "minor_code",
                     "hfm_item_code", "product_number"],
    },

    "fiscal_hourly_by_month": {
        "description": "Hourly patterns by fiscal month for a FY (AEST)",
        "sql": """
            SELECT fc.FinMonthOfYearNo AS month_no,
                   fc.FinMonthOfYearShortName AS month_name,
                   EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR) AS hour_of_day,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) AS revenue
            FROM transactions t
            JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
            WHERE fc.FinYear = ?
              AND t.Store_ID = ?
            GROUP BY fc.FinMonthOfYearNo, fc.FinMonthOfYearShortName,
                     EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR)
            ORDER BY fc.FinMonthOfYearNo, hour_of_day
        """,
        "params": ["fin_year", "store_id"],
    },

    # ------------------------------------------------------------------
    # FILTERED KPIs (hierarchy-aware)
    # ------------------------------------------------------------------
    "filtered_kpis": {
        "description": "KPI summary with optional product hierarchy and day-type filters",
        "sql": """
            SELECT COUNT(*) AS line_items,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) AS revenue,
                   SUM(t.Quantity) AS quantity,
                   SUM(t.EstimatedCOGS) AS cogs,
                   SUM(t.SalesIncGST) + COALESCE(SUM(t.EstimatedCOGS), 0) AS gp
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            {fiscal_join}
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {dept_filter}
              {major_filter}
              {minor_filter}
              {hfm_filter}
              {product_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
        """,
        "params": ["start", "end"],
        "optional": ["store_id", "dept_code", "major_code", "minor_code",
                     "hfm_item_code", "product_number"],
    },

    # ------------------------------------------------------------------
    # FILTERED DAILY TREND (hierarchy + time-aware)
    # ------------------------------------------------------------------
    "filtered_daily_trend": {
        "description": "Daily revenue/transaction trend with optional hierarchy and time filters",
        "sql": """
            SELECT DATE_TRUNC('day', t.SaleDate) AS period,
                   COUNT(*) AS line_items,
                   COUNT(DISTINCT t.Reference2) AS transactions,
                   SUM(t.SalesIncGST) AS revenue,
                   SUM(t.Quantity) AS quantity,
                   SUM(t.EstimatedCOGS) AS cogs
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            {fiscal_join}
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {dept_filter}
              {major_filter}
              {minor_filter}
              {hfm_filter}
              {product_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
            GROUP BY 1
            ORDER BY 1
        """,
        "params": ["start", "end"],
        "optional": ["store_id", "dept_code", "major_code", "minor_code",
                     "hfm_item_code", "product_number"],
    },

    # ------------------------------------------------------------------
    # TOP ITEMS — HIERARCHY-FILTERED
    # ------------------------------------------------------------------
    "top_items_filtered": {
        "description": "Top items by revenue with optional hierarchy and day-type filters",
        "sql": """
            SELECT t.PLUItem_ID AS pluitem_id,
                   p.ProductName AS product_name,
                   p.DepartmentDesc,
                   p.MajorGroupDesc,
                   p.MinorGroupDesc,
                   SUM(t.SalesIncGST) AS total_revenue,
                   SUM(t.Quantity) AS total_qty,
                   COUNT(*) AS transaction_count,
                   AVG(t.SalesIncGST / NULLIF(t.Quantity, 0)) AS avg_price
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            {fiscal_join}
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {dept_filter}
              {major_filter}
              {minor_filter}
              {hfm_filter}
              {product_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
            GROUP BY t.PLUItem_ID, p.ProductName, p.DepartmentDesc,
                     p.MajorGroupDesc, p.MinorGroupDesc
            ORDER BY total_revenue DESC
            LIMIT ?
        """,
        "params": ["start", "end", "limit"],
        "optional": ["store_id", "dept_code", "major_code", "minor_code",
                     "hfm_item_code", "product_number"],
    },

    # ------------------------------------------------------------------
    # SLOW MOVERS — HIERARCHY-FILTERED
    # ------------------------------------------------------------------
    "slow_movers_filtered": {
        "description": "Slow-moving items with optional hierarchy and day-type filters",
        "sql": """
            SELECT t.PLUItem_ID AS pluitem_id,
                   p.ProductName AS product_name,
                   p.DepartmentDesc,
                   p.MajorGroupDesc,
                   p.MinorGroupDesc,
                   COUNT(*) AS transaction_count,
                   SUM(t.Quantity) AS total_qty,
                   SUM(t.SalesIncGST) AS total_revenue,
                   COUNT(DISTINCT t.Store_ID) AS stores_stocked
            FROM transactions t
            JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
            {fiscal_join}
            WHERE t.SaleDate >= CAST(? AS TIMESTAMP)
              AND t.SaleDate < CAST(? AS TIMESTAMP)
              {store_filter}
              {dept_filter}
              {major_filter}
              {minor_filter}
              {hfm_filter}
              {product_filter}
              {day_type_filter}
              {hour_filter}
              {season_filter}
              {quarter_filter}
              {month_filter}
            GROUP BY t.PLUItem_ID, p.ProductName, p.DepartmentDesc,
                     p.MajorGroupDesc, p.MinorGroupDesc
            HAVING COUNT(*) < ?
            ORDER BY transaction_count ASC
            LIMIT ?
        """,
        "params": ["start", "end", "threshold", "limit"],
        "optional": ["store_id", "dept_code", "major_code", "minor_code",
                     "hfm_item_code", "product_number"],
    },

    # ------------------------------------------------------------------
    # LIKE-FOR-LIKE STORES
    # ------------------------------------------------------------------
    "like_for_like_stores": {
        "description": "Stores with transactions in both current and comparison periods",
        "sql": """
            WITH current_stores AS (
                SELECT DISTINCT Store_ID FROM transactions
                WHERE SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
            ),
            prior_stores AS (
                SELECT DISTINCT Store_ID FROM transactions
                WHERE SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
            )
            SELECT c.Store_ID
            FROM current_stores c
            JOIN prior_stores p ON c.Store_ID = p.Store_ID
            ORDER BY CAST(c.Store_ID AS INTEGER)
        """,
        "params": ["start", "end", "prior_start", "prior_end"],
    },

    # -----------------------------------------------------------------------
    # OUT-OF-STOCK (ZERO-SALES DETECTION)
    # -----------------------------------------------------------------------
    # Methodology: For each PLU x Store, build a 90-day baseline of average
    # daily revenue.  Products that sold on 30+ of those 90 days are "active".
    # For the analysis period, any day where an active product has zero sales
    # is flagged as a potential stock-out.  Missed revenue = baseline avg.

    "oos_by_department": {
        "description": "Estimated missed revenue by department x day (for heatmap rollup)",
        "sql": """
            WITH analysis_params AS (
                SELECT CAST(? AS DATE) AS start_date,
                       CAST(? AS DATE) AS end_date
            ),
            baseline AS (
                SELECT t.Store_ID, t.PLUItem_ID,
                       COUNT(DISTINCT CAST(t.SaleDate AS DATE)) AS selling_days,
                       SUM(t.SalesIncGST)
                           / NULLIF(COUNT(DISTINCT CAST(t.SaleDate AS DATE)), 0)
                           AS avg_daily_rev
                FROM transactions t
                JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
                WHERE t.SaleDate >= (SELECT start_date FROM analysis_params)
                                        - INTERVAL '90' DAY
                  AND t.SaleDate < (SELECT start_date FROM analysis_params)
                  {store_filter}
                GROUP BY t.Store_ID, t.PLUItem_ID
                HAVING selling_days >= 30
            ),
            analysis_sales AS (
                SELECT t.Store_ID, t.PLUItem_ID,
                       CAST(t.SaleDate AS DATE) AS sale_date,
                       SUM(t.SalesIncGST) AS daily_rev
                FROM transactions t
                WHERE t.SaleDate >= (SELECT start_date FROM analysis_params)
                  AND t.SaleDate < (SELECT end_date FROM analysis_params)
                GROUP BY t.Store_ID, t.PLUItem_ID,
                         CAST(t.SaleDate AS DATE)
            ),
            date_grid AS (
                SELECT CAST(gs AS DATE) AS cal_date
                FROM generate_series(
                    CAST((SELECT start_date FROM analysis_params)
                         AS TIMESTAMP),
                    CAST((SELECT end_date FROM analysis_params)
                         AS TIMESTAMP) - INTERVAL '1' DAY,
                    INTERVAL '1' DAY
                ) AS t(gs)
            ),
            expected AS (
                SELECT b.Store_ID, b.PLUItem_ID,
                       d.cal_date, b.avg_daily_rev
                FROM baseline b
                CROSS JOIN date_grid d
            ),
            gaps AS (
                SELECT e.Store_ID, e.PLUItem_ID,
                       e.cal_date, e.avg_daily_rev AS missed_revenue
                FROM expected e
                LEFT JOIN analysis_sales s
                    ON e.Store_ID = s.Store_ID
                    AND e.PLUItem_ID = s.PLUItem_ID
                    AND e.cal_date = s.sale_date
                WHERE s.daily_rev IS NULL OR s.daily_rev = 0
            )
            SELECT p.DepartmentDesc AS label,
                   p.DepartmentCode AS code,
                   g.cal_date,
                   fc.FinWeekOfYearNo AS fiscal_week,
                   fc.FinMonthOfYearNo AS fiscal_month,
                   fc.FinMonthOfYearShortName AS month_name,
                   SUM(g.missed_revenue) AS missed_revenue,
                   COUNT(*) AS oos_incidents,
                   COUNT(DISTINCT g.PLUItem_ID) AS affected_products
            FROM gaps g
            JOIN product_hierarchy p ON g.PLUItem_ID = p.ProductNumber
            JOIN fiscal_calendar fc ON g.cal_date = fc.TheDate
            GROUP BY p.DepartmentDesc, p.DepartmentCode, g.cal_date,
                     fc.FinWeekOfYearNo, fc.FinMonthOfYearNo, fc.FinMonthOfYearShortName
            ORDER BY p.DepartmentDesc, g.cal_date
        """,
        "params": ["start", "end"],
        "optional": ["store_id"],
    },

    "oos_by_major_group": {
        "description": "Estimated missed revenue by category x day (drill into department)",
        "sql": """
            WITH analysis_params AS (
                SELECT CAST(? AS DATE) AS start_date,
                       CAST(? AS DATE) AS end_date
            ),
            baseline AS (
                SELECT t.Store_ID, t.PLUItem_ID,
                       COUNT(DISTINCT CAST(t.SaleDate AS DATE)) AS selling_days,
                       SUM(t.SalesIncGST)
                           / NULLIF(COUNT(DISTINCT CAST(t.SaleDate AS DATE)), 0)
                           AS avg_daily_rev
                FROM transactions t
                JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
                WHERE t.SaleDate >= (SELECT start_date FROM analysis_params)
                                        - INTERVAL '90' DAY
                  AND t.SaleDate < (SELECT start_date FROM analysis_params)
                  {store_filter}
                  {dept_filter}
                GROUP BY t.Store_ID, t.PLUItem_ID
                HAVING selling_days >= 30
            ),
            analysis_sales AS (
                SELECT t.Store_ID, t.PLUItem_ID,
                       CAST(t.SaleDate AS DATE) AS sale_date,
                       SUM(t.SalesIncGST) AS daily_rev
                FROM transactions t
                WHERE t.SaleDate >= (SELECT start_date FROM analysis_params)
                  AND t.SaleDate < (SELECT end_date FROM analysis_params)
                GROUP BY t.Store_ID, t.PLUItem_ID,
                         CAST(t.SaleDate AS DATE)
            ),
            date_grid AS (
                SELECT CAST(gs AS DATE) AS cal_date
                FROM generate_series(
                    CAST((SELECT start_date FROM analysis_params)
                         AS TIMESTAMP),
                    CAST((SELECT end_date FROM analysis_params)
                         AS TIMESTAMP) - INTERVAL '1' DAY,
                    INTERVAL '1' DAY
                ) AS t(gs)
            ),
            expected AS (
                SELECT b.Store_ID, b.PLUItem_ID,
                       d.cal_date, b.avg_daily_rev
                FROM baseline b
                CROSS JOIN date_grid d
            ),
            gaps AS (
                SELECT e.Store_ID, e.PLUItem_ID,
                       e.cal_date, e.avg_daily_rev AS missed_revenue
                FROM expected e
                LEFT JOIN analysis_sales s
                    ON e.Store_ID = s.Store_ID
                    AND e.PLUItem_ID = s.PLUItem_ID
                    AND e.cal_date = s.sale_date
                WHERE s.daily_rev IS NULL OR s.daily_rev = 0
            )
            SELECT p.MajorGroupDesc AS label,
                   p.MajorGroupCode AS code,
                   g.cal_date,
                   fc.FinWeekOfYearNo AS fiscal_week,
                   fc.FinMonthOfYearNo AS fiscal_month,
                   fc.FinMonthOfYearShortName AS month_name,
                   SUM(g.missed_revenue) AS missed_revenue,
                   COUNT(*) AS oos_incidents,
                   COUNT(DISTINCT g.PLUItem_ID) AS affected_products
            FROM gaps g
            JOIN product_hierarchy p ON g.PLUItem_ID = p.ProductNumber
            JOIN fiscal_calendar fc ON g.cal_date = fc.TheDate
            GROUP BY p.MajorGroupDesc, p.MajorGroupCode, g.cal_date,
                     fc.FinWeekOfYearNo, fc.FinMonthOfYearNo, fc.FinMonthOfYearShortName
            ORDER BY p.MajorGroupDesc, g.cal_date
        """,
        "params": ["start", "end"],
        "optional": ["store_id", "dept_code"],
    },

    "oos_by_minor_group": {
        "description": "Estimated missed revenue by sub-category x day (drill into category)",
        "sql": """
            WITH analysis_params AS (
                SELECT CAST(? AS DATE) AS start_date,
                       CAST(? AS DATE) AS end_date
            ),
            baseline AS (
                SELECT t.Store_ID, t.PLUItem_ID,
                       COUNT(DISTINCT CAST(t.SaleDate AS DATE)) AS selling_days,
                       SUM(t.SalesIncGST)
                           / NULLIF(COUNT(DISTINCT CAST(t.SaleDate AS DATE)), 0)
                           AS avg_daily_rev
                FROM transactions t
                JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
                WHERE t.SaleDate >= (SELECT start_date FROM analysis_params)
                                        - INTERVAL '90' DAY
                  AND t.SaleDate < (SELECT start_date FROM analysis_params)
                  {store_filter}
                  {dept_filter}
                  {major_filter}
                GROUP BY t.Store_ID, t.PLUItem_ID
                HAVING selling_days >= 30
            ),
            analysis_sales AS (
                SELECT t.Store_ID, t.PLUItem_ID,
                       CAST(t.SaleDate AS DATE) AS sale_date,
                       SUM(t.SalesIncGST) AS daily_rev
                FROM transactions t
                WHERE t.SaleDate >= (SELECT start_date FROM analysis_params)
                  AND t.SaleDate < (SELECT end_date FROM analysis_params)
                GROUP BY t.Store_ID, t.PLUItem_ID,
                         CAST(t.SaleDate AS DATE)
            ),
            date_grid AS (
                SELECT CAST(gs AS DATE) AS cal_date
                FROM generate_series(
                    CAST((SELECT start_date FROM analysis_params)
                         AS TIMESTAMP),
                    CAST((SELECT end_date FROM analysis_params)
                         AS TIMESTAMP) - INTERVAL '1' DAY,
                    INTERVAL '1' DAY
                ) AS t(gs)
            ),
            expected AS (
                SELECT b.Store_ID, b.PLUItem_ID,
                       d.cal_date, b.avg_daily_rev
                FROM baseline b
                CROSS JOIN date_grid d
            ),
            gaps AS (
                SELECT e.Store_ID, e.PLUItem_ID,
                       e.cal_date, e.avg_daily_rev AS missed_revenue
                FROM expected e
                LEFT JOIN analysis_sales s
                    ON e.Store_ID = s.Store_ID
                    AND e.PLUItem_ID = s.PLUItem_ID
                    AND e.cal_date = s.sale_date
                WHERE s.daily_rev IS NULL OR s.daily_rev = 0
            )
            SELECT p.MinorGroupDesc AS label,
                   p.MinorGroupCode AS code,
                   g.cal_date,
                   fc.FinWeekOfYearNo AS fiscal_week,
                   fc.FinMonthOfYearNo AS fiscal_month,
                   fc.FinMonthOfYearShortName AS month_name,
                   SUM(g.missed_revenue) AS missed_revenue,
                   COUNT(*) AS oos_incidents,
                   COUNT(DISTINCT g.PLUItem_ID) AS affected_products
            FROM gaps g
            JOIN product_hierarchy p ON g.PLUItem_ID = p.ProductNumber
            JOIN fiscal_calendar fc ON g.cal_date = fc.TheDate
            GROUP BY p.MinorGroupDesc, p.MinorGroupCode, g.cal_date,
                     fc.FinWeekOfYearNo, fc.FinMonthOfYearNo, fc.FinMonthOfYearShortName
            ORDER BY p.MinorGroupDesc, g.cal_date
        """,
        "params": ["start", "end"],
        "optional": ["store_id", "dept_code", "major_code"],
    },

    "oos_summary": {
        "description": "Out-of-stock KPI summary (total missed revenue, incidents, products)",
        "sql": """
            WITH analysis_params AS (
                SELECT CAST(? AS DATE) AS start_date,
                       CAST(? AS DATE) AS end_date
            ),
            baseline AS (
                SELECT t.Store_ID, t.PLUItem_ID,
                       COUNT(DISTINCT CAST(t.SaleDate AS DATE)) AS selling_days,
                       SUM(t.SalesIncGST)
                           / NULLIF(COUNT(DISTINCT CAST(t.SaleDate AS DATE)), 0)
                           AS avg_daily_rev
                FROM transactions t
                JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
                WHERE t.SaleDate >= (SELECT start_date FROM analysis_params)
                                        - INTERVAL '90' DAY
                  AND t.SaleDate < (SELECT start_date FROM analysis_params)
                  {store_filter}
                  {dept_filter}
                  {major_filter}
                  {minor_filter}
                GROUP BY t.Store_ID, t.PLUItem_ID
                HAVING selling_days >= 30
            ),
            analysis_sales AS (
                SELECT t.Store_ID, t.PLUItem_ID,
                       CAST(t.SaleDate AS DATE) AS sale_date,
                       SUM(t.SalesIncGST) AS daily_rev
                FROM transactions t
                WHERE t.SaleDate >= (SELECT start_date FROM analysis_params)
                  AND t.SaleDate < (SELECT end_date FROM analysis_params)
                GROUP BY t.Store_ID, t.PLUItem_ID,
                         CAST(t.SaleDate AS DATE)
            ),
            date_grid AS (
                SELECT CAST(gs AS DATE) AS cal_date
                FROM generate_series(
                    CAST((SELECT start_date FROM analysis_params)
                         AS TIMESTAMP),
                    CAST((SELECT end_date FROM analysis_params)
                         AS TIMESTAMP) - INTERVAL '1' DAY,
                    INTERVAL '1' DAY
                ) AS t(gs)
            ),
            expected AS (
                SELECT b.Store_ID, b.PLUItem_ID,
                       d.cal_date, b.avg_daily_rev
                FROM baseline b
                CROSS JOIN date_grid d
            ),
            gaps AS (
                SELECT e.Store_ID, e.PLUItem_ID,
                       e.cal_date, e.avg_daily_rev AS missed_revenue
                FROM expected e
                LEFT JOIN analysis_sales s
                    ON e.Store_ID = s.Store_ID
                    AND e.PLUItem_ID = s.PLUItem_ID
                    AND e.cal_date = s.sale_date
                WHERE s.daily_rev IS NULL OR s.daily_rev = 0
            )
            SELECT COUNT(*) AS oos_incidents,
                   COUNT(DISTINCT g.PLUItem_ID) AS affected_products,
                   SUM(g.missed_revenue) AS total_missed_revenue,
                   (SELECT COUNT(*) FROM baseline) AS active_products,
                   (SELECT COUNT(*) FROM date_grid) AS analysis_days
            FROM gaps g
        """,
        "params": ["start", "end"],
        "optional": ["store_id", "dept_code", "major_code", "minor_code"],
    },

    "oos_top_products": {
        "description": "Top N products by estimated missed revenue (zero-sales days)",
        "sql": """
            WITH analysis_params AS (
                SELECT CAST(? AS DATE) AS start_date,
                       CAST(? AS DATE) AS end_date
            ),
            baseline AS (
                SELECT t.Store_ID, t.PLUItem_ID,
                       COUNT(DISTINCT CAST(t.SaleDate AS DATE)) AS selling_days,
                       SUM(t.SalesIncGST)
                           / NULLIF(COUNT(DISTINCT CAST(t.SaleDate AS DATE)), 0)
                           AS avg_daily_rev
                FROM transactions t
                JOIN product_hierarchy p ON t.PLUItem_ID = p.ProductNumber
                WHERE t.SaleDate >= (SELECT start_date FROM analysis_params)
                                        - INTERVAL '90' DAY
                  AND t.SaleDate < (SELECT start_date FROM analysis_params)
                  {store_filter}
                  {dept_filter}
                  {major_filter}
                  {minor_filter}
                GROUP BY t.Store_ID, t.PLUItem_ID
                HAVING selling_days >= 30
            ),
            analysis_sales AS (
                SELECT t.Store_ID, t.PLUItem_ID,
                       CAST(t.SaleDate AS DATE) AS sale_date,
                       SUM(t.SalesIncGST) AS daily_rev
                FROM transactions t
                WHERE t.SaleDate >= (SELECT start_date FROM analysis_params)
                  AND t.SaleDate < (SELECT end_date FROM analysis_params)
                GROUP BY t.Store_ID, t.PLUItem_ID,
                         CAST(t.SaleDate AS DATE)
            ),
            date_grid AS (
                SELECT CAST(gs AS DATE) AS cal_date
                FROM generate_series(
                    CAST((SELECT start_date FROM analysis_params)
                         AS TIMESTAMP),
                    CAST((SELECT end_date FROM analysis_params)
                         AS TIMESTAMP) - INTERVAL '1' DAY,
                    INTERVAL '1' DAY
                ) AS t(gs)
            ),
            expected AS (
                SELECT b.Store_ID, b.PLUItem_ID,
                       d.cal_date, b.avg_daily_rev
                FROM baseline b
                CROSS JOIN date_grid d
            ),
            gaps AS (
                SELECT e.Store_ID, e.PLUItem_ID,
                       e.cal_date, e.avg_daily_rev AS missed_revenue
                FROM expected e
                LEFT JOIN analysis_sales s
                    ON e.Store_ID = s.Store_ID
                    AND e.PLUItem_ID = s.PLUItem_ID
                    AND e.cal_date = s.sale_date
                WHERE s.daily_rev IS NULL OR s.daily_rev = 0
            )
            SELECT g.PLUItem_ID,
                   p.ProductName AS product_name,
                   p.DepartmentDesc AS department,
                   p.MajorGroupDesc AS category,
                   COUNT(*) AS oos_days,
                   (SELECT COUNT(*) FROM date_grid) AS total_days,
                   SUM(g.missed_revenue) AS missed_revenue,
                   MAX(g.missed_revenue) AS peak_daily_missed
            FROM gaps g
            JOIN product_hierarchy p ON g.PLUItem_ID = p.ProductNumber
            GROUP BY g.PLUItem_ID, p.ProductName,
                     p.DepartmentDesc, p.MajorGroupDesc
            ORDER BY missed_revenue DESC
            LIMIT ?
        """,
        "params": ["start", "end", "limit"],
        "optional": ["store_id", "dept_code", "major_code", "minor_code"],
    },
}


# ---------------------------------------------------------------------------
# QUERY RUNNER
# ---------------------------------------------------------------------------

def get_query_catalog() -> list[dict]:
    """Return list of available queries with descriptions."""
    return [
        {"name": name, "description": q["description"],
         "params": q["params"],
         "optional": q.get("optional", [])}
        for name, q in QUERIES.items()
    ]


def run_query(store, query_name: str, **kwargs) -> list[dict]:
    """
    Execute a named query from the catalog.

    Args:
        store: TransactionStore instance
        query_name: Key from QUERIES dict
        **kwargs: Named parameters matching the query's params list
                  (start, end, store_id, limit, plu_id, customer_code,
                   dept_code, major_code, fin_year, fin_year_2)
    Returns:
        list of dicts
    """
    if query_name not in QUERIES:
        raise ValueError(f"Unknown query: {query_name}. "
                         f"Available: {list(QUERIES.keys())}")

    q = QUERIES[query_name]
    sql = q["sql"]

    # Handle optional store_id filter
    if "{store_filter}" in sql:
        if kwargs.get("store_id"):
            sql = sql.replace("{store_filter}", "AND t.Store_ID = ?"
                              if " t." in sql else "AND Store_ID = ?")
        else:
            sql = sql.replace("{store_filter}", "")

    # Handle optional hierarchy filters (incl. HFM item and product)
    hierarchy_filters = [
        ("{dept_filter}", "p.DepartmentCode", "dept_code"),
        ("{major_filter}", "p.MajorGroupCode", "major_code"),
        ("{minor_filter}", "p.MinorGroupCode", "minor_code"),
        ("{hfm_filter}", "p.HFMItem", "hfm_item_code"),
        ("{product_filter}", "p.ProductNumber", "product_number"),
    ]
    for filt, col, key in hierarchy_filters:
        if filt in sql:
            if kwargs.get(key):
                sql = sql.replace(filt, f"AND {col} = ?")
            else:
                sql = sql.replace(filt, "")

    # Handle conditional fiscal_calendar JOIN (for time dimension filters on non-fiscal queries)
    if "{fiscal_join}" in sql:
        needs_fc = (
            (kwargs.get("day_type") and kwargs["day_type"] != "all")
            or kwargs.get("day_of_week_names")
            or kwargs.get("hour_start") is not None
            or kwargs.get("season_names")
            or kwargs.get("quarter_nos")
            or kwargs.get("month_nos")
        )
        if needs_fc:
            sql = sql.replace("{fiscal_join}",
                "JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate")
        else:
            sql = sql.replace("{fiscal_join}", "")

    # Handle day-of-week / day-type filter (string substitution, not parameterized)
    # Values come from controlled checkbox selections — safe for string interpolation.
    if "{day_type_filter}" in sql:
        dow_names = kwargs.get("day_of_week_names")
        if dow_names and len(dow_names) < 7:
            quoted = ", ".join(f"'{d}'" for d in dow_names)
            sql = sql.replace("{day_type_filter}",
                              f"AND fc.DayOfWeekName IN ({quoted})")
        else:
            # Legacy day_type fallback
            day_type = kwargs.get("day_type", "all")
            if day_type == "business":
                sql = sql.replace("{day_type_filter}", "AND fc.BusinessDay = 'Y'")
            elif day_type == "weekend":
                sql = sql.replace("{day_type_filter}", "AND fc.Weekend = 'Y'")
            else:
                sql = sql.replace("{day_type_filter}", "")

    # Handle hour-of-day filter (string substitution — controlled int values)
    if "{hour_filter}" in sql:
        h_start = kwargs.get("hour_start")
        h_end = kwargs.get("hour_end")
        if h_start is not None and h_end is not None:
            sql = sql.replace("{hour_filter}",
                f"AND EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR) >= {int(h_start)} "
                f"AND EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR) < {int(h_end)}")
        else:
            sql = sql.replace("{hour_filter}", "")

    # Handle season filter (string substitution — controlled checkbox values)
    if "{season_filter}" in sql:
        seasons = kwargs.get("season_names")
        if seasons and len(seasons) < 4:
            quoted = ", ".join(f"'{s}'" for s in seasons)
            sql = sql.replace("{season_filter}",
                              f"AND fc.SeasonName IN ({quoted})")
        else:
            sql = sql.replace("{season_filter}", "")

    # Handle fiscal quarter filter (string substitution — controlled int values)
    if "{quarter_filter}" in sql:
        q_nos = kwargs.get("quarter_nos")
        if q_nos and len(q_nos) < 4:
            in_clause = ", ".join(str(int(q)) for q in q_nos)
            sql = sql.replace("{quarter_filter}",
                              f"AND fc.FinQuarterOfYearNo IN ({in_clause})")
        else:
            sql = sql.replace("{quarter_filter}", "")

    # Handle fiscal month filter (string substitution — controlled int values)
    if "{month_filter}" in sql:
        m_nos = kwargs.get("month_nos")
        if m_nos and len(m_nos) < 12:
            in_clause = ", ".join(str(int(m)) for m in m_nos)
            sql = sql.replace("{month_filter}",
                              f"AND fc.FinMonthOfYearNo IN ({in_clause})")
        else:
            sql = sql.replace("{month_filter}", "")

    # Build ordered params list.
    # Tail params (limit, threshold) are deferred because they appear
    # after optional WHERE-clause filters in the SQL but are listed in
    # q["params"] alongside the WHERE-clause params.
    params = []
    tail_params = []
    for p in q["params"]:
        key = p
        if key == "limit":
            tail_params.append(kwargs.get("limit", 20))
        elif key == "threshold":
            tail_params.append(kwargs.get("threshold", 10))
        elif key == "store_id":
            if kwargs.get("store_id"):
                params.append(kwargs["store_id"])
        elif key == "plu_id":
            params.append(kwargs["plu_id"])
        elif key == "customer_code":
            params.append(kwargs["customer_code"])
        elif key == "dept_code":
            params.append(kwargs["dept_code"])
        elif key == "major_code":
            params.append(kwargs["major_code"])
        elif key == "minor_code":
            params.append(kwargs["minor_code"])
        elif key == "prior_start":
            params.append(kwargs["prior_start"])
        elif key == "prior_end":
            params.append(kwargs["prior_end"])
        elif key == "fin_year":
            params.append(int(kwargs["fin_year"]))
        elif key == "fin_year_2":
            params.append(int(kwargs["fin_year_2"]))
        else:
            if key not in kwargs:
                raise ValueError(f"Missing required parameter: {key}")
            params.append(kwargs[key])

    # If store_id is optional and provided, append it
    if "store_id" in q.get("optional", []) and kwargs.get("store_id"):
        params.append(kwargs["store_id"])

    # Append optional hierarchy filter params in order
    for opt_key in ["dept_code", "major_code", "minor_code",
                    "hfm_item_code", "product_number"]:
        if opt_key in q.get("optional", []) and kwargs.get(opt_key):
            params.append(kwargs[opt_key])

    # Append tail params (LIMIT, HAVING threshold) after all WHERE-clause params
    params.extend(tail_params)

    return store.query(sql, params)
