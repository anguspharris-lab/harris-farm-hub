"""
Harris Farm Hub — Transaction Data Layer
DuckDB-backed query engine for 383M+ POS transaction records (parquet).
Source: Microsoft Fabric retail fact_pos_sales → parquet export.
"""

import duckdb
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("hub_api")

# ---------------------------------------------------------------------------
# PARQUET FILE LOCATIONS
# ---------------------------------------------------------------------------

# Project-local transaction data (Replit / portable deployment)
LOCAL_PARQUET_DIR = Path(__file__).parent.parent / "data" / "transactions"

LOCAL_PARQUET_FILES = {
    "FY24": LOCAL_PARQUET_DIR / "FY24.parquet",
    "FY25": LOCAL_PARQUET_DIR / "FY25.parquet",
    "FY26": LOCAL_PARQUET_DIR / "FY26.parquet",
}

# External dataset (local dev machine)
EXTERNAL_PARQUET_DIR = (
    Path.home()
    / "Desktop"
    / "ProjectManagement"
    / "Data"
    / "customer-transactions"
    / "raw"
)

EXTERNAL_PARQUET_FILES = {
    "FY24": EXTERNAL_PARQUET_DIR / "sales_01072023_parquet" / "sales_01072023_parquet.parquet",
    "FY25": EXTERNAL_PARQUET_DIR / "sales_01072024_parquet" / "sales_01072024_parquet.parquet",
    "FY26": EXTERNAL_PARQUET_DIR / "sales_01072025_parquet" / "sales_01072025_parquet.parquet",
}

# ---------------------------------------------------------------------------
# STORE NAME REFERENCE (Store_ID → display name)
# ---------------------------------------------------------------------------

STORE_NAMES = {
    "10": "Pennant Hills",
    "11": "Meats Pennant Hills",
    "24": "St Ives",
    "28": "Mosman",
    "32": "Willoughby",
    "37": "Broadway",
    "40": "Erina",
    "44": "Orange",
    "48": "Manly",
    "49": "Mona Vale",
    "51": "Bowral",
    "52": "Cammeray",
    "54": "Potts Point",
    "56": "Boronia Park",
    "57": "Bondi Beach",
    "58": "Drummoyne",
    "59": "Bathurst",
    "63": "Randwick",
    "64": "Leichhardt",
    "65": "Bondi Westfield",
    "66": "Newcastle",
    "67": "Lindfield",
    "68": "Albury",
    "69": "Rose Bay",
    "70": "West End QLD",
    "74": "Isle of Capri QLD",
    "75": "Clayfield QLD",
    "76": "Lane Cove",
    "77": "Dural",
    "80": "Majura Park ACT",
    "84": "Redfern",
    "85": "Marrickville",
    "86": "Miranda",
    "87": "Maroubra",
}

# Blocked SQL keywords for freeform query validation
_BLOCKED_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL", "COPY", "ATTACH",
    "DETACH", "EXPORT", "IMPORT", "LOAD", "INSTALL", "PRAGMA",
}

# ---------------------------------------------------------------------------
# TRANSACTION STORE
# ---------------------------------------------------------------------------


class TransactionStore:
    """Query engine for Harris Farm POS transaction parquet files via DuckDB."""

    def __init__(self):
        self._verify_files()

    def _verify_files(self):
        """Check that parquet files exist. Checks project-local
        data/transactions/ first, then external Desktop path."""
        self.available_fys = {}

        # Try project-local files first (Replit / portable)
        for fy, path in LOCAL_PARQUET_FILES.items():
            if path.exists():
                self.available_fys[fy] = path

        if self.available_fys:
            logger.info("Using local transaction data: %s", LOCAL_PARQUET_DIR)
            return

        # Fall back to external path (local dev machine)
        for fy, path in EXTERNAL_PARQUET_FILES.items():
            if path.exists():
                self.available_fys[fy] = path
            else:
                logger.warning("Parquet file missing for %s: %s", fy, path)

        if self.available_fys:
            logger.info("Using external transaction data: %s",
                         EXTERNAL_PARQUET_DIR)
        else:
            logger.error("No parquet files found in %s or %s",
                         LOCAL_PARQUET_DIR, EXTERNAL_PARQUET_DIR)

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Return a DuckDB connection with `transactions` view and
        `product_hierarchy` table (if parquet available)."""
        conn = duckdb.connect(":memory:")

        unions = []
        for fy, path in sorted(self.available_fys.items()):
            # Paths are embedded as string literals (not params) because
            # DuckDB does not support prepared params in CREATE VIEW.
            escaped = str(path).replace("'", "''")
            unions.append(
                f"SELECT *, '{fy}' AS fiscal_year "
                f"FROM read_parquet('{escaped}')"
            )

        if not unions:
            raise RuntimeError("No parquet files available")

        sql = "CREATE VIEW transactions AS " + " UNION ALL ".join(unions)
        conn.execute(sql)

        # Load product hierarchy table (72,911 products) for JOIN queries
        hierarchy_path = (
            Path(__file__).parent.parent / "data" / "product_hierarchy.parquet"
        )
        if hierarchy_path.exists():
            escaped_h = str(hierarchy_path).replace("'", "''")
            conn.execute(
                f"CREATE TABLE product_hierarchy AS "
                f"SELECT * FROM read_parquet('{escaped_h}')"
            )

        # Load fiscal calendar (4,018 daily rows) for fiscal-aware queries
        fiscal_path = (
            Path(__file__).parent.parent / "data" / "fiscal_calendar_daily.parquet"
        )
        if fiscal_path.exists():
            escaped_fc = str(fiscal_path).replace("'", "''")
            conn.execute(
                f"CREATE TABLE fiscal_calendar AS "
                f"SELECT * FROM read_parquet('{escaped_fc}')"
            )

        return conn

    # ------------------------------------------------------------------
    # PUBLIC QUERY METHODS
    # ------------------------------------------------------------------

    def query(self, sql: str, params: Optional[list] = None,
              timeout_seconds: int = 30, max_rows: int = 10000) -> list[dict]:
        """
        Execute a read-only SQL query against the transactions view.
        Returns list of dicts (column-name → value).
        """
        conn = self._get_connection()
        try:
            result = conn.execute(sql, params or [])
            columns = [desc[0].lower() for desc in result.description]
            rows = result.fetchmany(max_rows)
            return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()

    def summary(self) -> dict:
        """Overview: row counts, date range, store counts per fiscal year."""
        conn = self._get_connection()
        try:
            rows = conn.execute("""
                SELECT fiscal_year,
                       COUNT(*) AS row_count,
                       COUNT(DISTINCT Store_ID) AS store_count,
                       COUNT(DISTINCT PLUItem_ID) AS plu_count,
                       MIN(SaleDate) AS min_date,
                       MAX(SaleDate) AS max_date,
                       SUM(SalesIncGST) AS total_revenue,
                       COUNT(DISTINCT Reference2) AS unique_transactions
                FROM transactions
                GROUP BY fiscal_year
                ORDER BY fiscal_year
            """).fetchall()
            columns = ["fiscal_year", "row_count", "store_count", "plu_count",
                        "min_date", "max_date", "total_revenue",
                        "unique_transactions"]
            fy_list = []
            total_rows = 0
            for row in rows:
                d = dict(zip(columns, row))
                d["min_date"] = str(d["min_date"])
                d["max_date"] = str(d["max_date"])
                d["total_revenue"] = round(d["total_revenue"], 2)
                total_rows += d["row_count"]
                fy_list.append(d)
            return {
                "fiscal_years": fy_list,
                "total_rows": total_rows,
                "total_fiscal_years": len(fy_list),
            }
        finally:
            conn.close()

    def get_stores(self) -> list[dict]:
        """Distinct stores with transaction counts and revenue."""
        conn = self._get_connection()
        try:
            rows = conn.execute("""
                SELECT Store_ID,
                       COUNT(*) AS transactions,
                       SUM(SalesIncGST) AS total_revenue,
                       MIN(SaleDate) AS first_sale,
                       MAX(SaleDate) AS last_sale
                FROM transactions
                GROUP BY Store_ID
                ORDER BY CAST(Store_ID AS INTEGER)
            """).fetchall()
            columns = ["store_id", "transactions", "total_revenue",
                        "first_sale", "last_sale"]
            result = []
            for row in rows:
                d = dict(zip(columns, row))
                d["store_name"] = STORE_NAMES.get(d["store_id"],
                                                   f"Store {d['store_id']}")
                d["total_revenue"] = round(d["total_revenue"], 2)
                d["first_sale"] = str(d["first_sale"])
                d["last_sale"] = str(d["last_sale"])
                result.append(d)
            return result
        finally:
            conn.close()

    def top_items(self, start: str, end: str,
                  store_id: Optional[str] = None,
                  limit: int = 20,
                  sort_by: str = "revenue") -> list[dict]:
        """Top N items by revenue, quantity, or gross profit."""
        sort_col = {
            "revenue": "total_revenue",
            "quantity": "total_qty",
            "gp": "est_gp",
            "transactions": "transaction_count",
        }.get(sort_by, "total_revenue")

        store_clause = "AND Store_ID = ?" if store_id else ""
        params = [start, end]
        if store_id:
            params.append(store_id)
        params.append(limit)

        conn = self._get_connection()
        try:
            rows = conn.execute(f"""
                SELECT PLUItem_ID,
                       COUNT(*) AS transaction_count,
                       SUM(Quantity) AS total_qty,
                       SUM(SalesIncGST) AS total_revenue,
                       SUM(EstimatedCOGS) AS total_cogs,
                       SUM(SalesIncGST) + COALESCE(SUM(EstimatedCOGS), 0)
                           AS est_gp
                FROM transactions
                WHERE SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
                  {store_clause}
                GROUP BY PLUItem_ID
                ORDER BY {sort_col} DESC
                LIMIT ?
            """, params).fetchall()
            columns = ["plu_item_id", "transaction_count", "total_qty",
                        "total_revenue", "total_cogs", "est_gp"]
            return [
                {k: (round(v, 2) if isinstance(v, float) else v)
                 for k, v in dict(zip(columns, row)).items()}
                for row in rows
            ]
        finally:
            conn.close()

    def store_trend(self, store_id: str, start: str, end: str,
                    grain: str = "daily") -> list[dict]:
        """Time-series revenue/transaction trend for a store."""
        trunc = {
            "daily": "day",
            "weekly": "week",
            "monthly": "month",
        }.get(grain, "day")

        conn = self._get_connection()
        try:
            rows = conn.execute(f"""
                SELECT DATE_TRUNC('{trunc}', SaleDate) AS period,
                       COUNT(*) AS line_items,
                       COUNT(DISTINCT Reference2) AS transactions,
                       SUM(SalesIncGST) AS revenue,
                       SUM(Quantity) AS quantity,
                       SUM(EstimatedCOGS) AS cogs
                FROM transactions
                WHERE Store_ID = ?
                  AND SaleDate >= CAST(? AS TIMESTAMP)
                  AND SaleDate < CAST(? AS TIMESTAMP)
                GROUP BY 1
                ORDER BY 1
            """, [store_id, start, end]).fetchall()
            columns = ["period", "line_items", "transactions", "revenue",
                        "quantity", "cogs"]
            return [
                {k: (str(v) if k == "period"
                      else round(v, 2) if isinstance(v, float) else v)
                 for k, v in dict(zip(columns, row)).items()}
                for row in rows
            ]
        finally:
            conn.close()

    def plu_performance(self, plu_id: str,
                        start: Optional[str] = None,
                        end: Optional[str] = None) -> dict:
        """Performance summary for a single PLU item across all stores."""
        date_clause = ""
        params = [plu_id]
        if start:
            date_clause += " AND SaleDate >= CAST(? AS TIMESTAMP)"
            params.append(start)
        if end:
            date_clause += " AND SaleDate < CAST(? AS TIMESTAMP)"
            params.append(end)

        conn = self._get_connection()
        try:
            # Overall summary
            overall = conn.execute(f"""
                SELECT COUNT(*) AS line_items,
                       COUNT(DISTINCT Reference2) AS transactions,
                       COUNT(DISTINCT Store_ID) AS stores_sold,
                       SUM(Quantity) AS total_qty,
                       SUM(SalesIncGST) AS total_revenue,
                       SUM(EstimatedCOGS) AS total_cogs,
                       MIN(SaleDate) AS first_sale,
                       MAX(SaleDate) AS last_sale
                FROM transactions
                WHERE PLUItem_ID = ? {date_clause}
            """, params).fetchone()
            overall_cols = ["line_items", "transactions", "stores_sold",
                            "total_qty", "total_revenue", "total_cogs",
                            "first_sale", "last_sale"]
            summary = dict(zip(overall_cols, overall))
            summary["plu_item_id"] = plu_id
            for k in ("total_revenue", "total_cogs", "total_qty"):
                if isinstance(summary[k], float):
                    summary[k] = round(summary[k], 2)
            for k in ("first_sale", "last_sale"):
                summary[k] = str(summary[k])

            # By store breakdown
            by_store = conn.execute(f"""
                SELECT Store_ID,
                       SUM(Quantity) AS qty,
                       SUM(SalesIncGST) AS revenue
                FROM transactions
                WHERE PLUItem_ID = ? {date_clause}
                GROUP BY Store_ID
                ORDER BY revenue DESC
            """, params).fetchall()
            summary["by_store"] = [
                {
                    "store_id": r[0],
                    "store_name": STORE_NAMES.get(r[0], f"Store {r[0]}"),
                    "quantity": round(r[1], 2) if r[1] else 0,
                    "revenue": round(r[2], 2) if r[2] else 0,
                }
                for r in by_store
            ]
            return summary
        finally:
            conn.close()

    @staticmethod
    def validate_freeform_sql(sql: str) -> Optional[str]:
        """
        Validate freeform SQL for safety.
        Returns None if valid, or an error message string.
        """
        stripped = sql.strip().rstrip(";").strip()
        if not stripped.upper().startswith("SELECT"):
            return "Query must start with SELECT"

        upper = stripped.upper()
        for keyword in _BLOCKED_KEYWORDS:
            # Check for keyword as a whole word
            if f" {keyword} " in f" {upper} ":
                return f"Blocked keyword: {keyword}"

        return None
