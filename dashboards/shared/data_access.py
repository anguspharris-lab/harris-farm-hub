"""
Harris Farm Hub - Shared Data Access Module
Provides centralized database access functions for all dashboards
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any


# Cache the database path
_DB_PATH_CACHE: Optional[Path] = None


def get_db_path() -> Path:
    """
    Returns path to data/harris_farm.db relative to project root.
    Caches the path for subsequent calls.

    Returns:
        Path: Absolute path to harris_farm.db
    """
    global _DB_PATH_CACHE

    if _DB_PATH_CACHE is None:
        # Project root is 2 levels up from the shared/ directory
        shared_dir = Path(__file__).resolve().parent
        project_root = shared_dir.parent.parent
        _DB_PATH_CACHE = project_root / "data" / "harris_farm.db"

    return _DB_PATH_CACHE


def get_stores() -> List[str]:
    """
    Returns list of store names from stores table.
    Only includes retail stores, sorted by store_name.

    Returns:
        List[str]: Sorted list of store names (e.g., '10 - HFM Pennant Hills')
    """
    db_path = get_db_path()

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT store_name
            FROM stores
            WHERE store_type = 'Retail'
            ORDER BY store_name
        """)

        return [row['store_name'] for row in cursor.fetchall()]


def get_departments() -> List[Dict[str, Any]]:
    """
    Returns list of departments with their major groups.

    Returns:
        List[Dict]: List of dicts with keys:
            - department_code: int
            - department_name: str
            - major_group_code: int
            - major_group_name: str
    """
    db_path = get_db_path()

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                department_code,
                department_name,
                major_group_code,
                major_group_name
            FROM departments
            ORDER BY department_code, major_group_code
        """)

        return [dict(row) for row in cursor.fetchall()]


def get_sales_data(
    stores: Optional[List[str]] = None,
    departments: Optional[List[str]] = None,
    major_groups: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    measure: str = 'Sales - Val',
    channel: str = 'Retail',
    promo: str = 'N'
) -> List[Dict[str, Any]]:
    """
    Queries sales table with optional filters.

    Args:
        stores: List of store names to filter (e.g., ['10 - HFM Pennant Hills'])
        departments: List of department names to filter (e.g., ['10 - Fruit & Vegetables'])
        major_groups: List of major group names to filter
        date_from: Start date in YYYY-MM-DD format (inclusive)
        date_to: End date in YYYY-MM-DD format (inclusive)
        measure: Measure to filter (default: 'Sales - Val')
        channel: Channel to filter (default: 'Retail')
        promo: Promotion flag 'Y' or 'N' (default: 'N')

    Returns:
        List[Dict]: List of dicts with keys:
            - store: str
            - department: str
            - major_group: str
            - week_ending: str
            - value: float
    """
    db_path = get_db_path()

    # Build query with filters
    query = """
        SELECT
            store,
            department,
            major_group,
            week_ending,
            value
        FROM sales
        WHERE channel = ?
          AND measure = ?
          AND is_promotion = ?
    """

    params = [channel, measure, promo]

    if stores:
        placeholders = ','.join('?' * len(stores))
        query += f" AND store IN ({placeholders})"
        params.extend(stores)

    if departments:
        placeholders = ','.join('?' * len(departments))
        query += f" AND department IN ({placeholders})"
        params.extend(departments)

    if major_groups:
        placeholders = ','.join('?' * len(major_groups))
        query += f" AND major_group IN ({placeholders})"
        params.extend(major_groups)

    if date_from:
        query += " AND week_ending >= ?"
        params.append(date_from)

    if date_to:
        query += " AND week_ending <= ?"
        params.append(date_to)

    query += " ORDER BY week_ending, store, department"

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]


def get_customer_data(
    stores: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Queries customers table with optional filters.

    Args:
        stores: List of store names to filter
        date_from: Start date in YYYY-MM-DD format (inclusive)
        date_to: End date in YYYY-MM-DD format (inclusive)

    Returns:
        List[Dict]: List of dicts with keys:
            - store: str
            - channel: str
            - measure: str
            - week_ending: str
            - value: float
    """
    db_path = get_db_path()

    query = """
        SELECT
            store,
            channel,
            measure,
            week_ending,
            value
        FROM customers
        WHERE 1=1
    """

    params = []

    if stores:
        placeholders = ','.join('?' * len(stores))
        query += f" AND store IN ({placeholders})"
        params.extend(stores)

    if date_from:
        query += " AND week_ending >= ?"
        params.append(date_from)

    if date_to:
        query += " AND week_ending <= ?"
        params.append(date_to)

    query += " ORDER BY week_ending, store"

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]


def get_fiscal_calendar() -> List[Dict[str, Any]]:
    """
    Returns fiscal calendar table as list of dicts.

    Returns:
        List[Dict]: List of dicts with keys:
            - sequence: int
            - week_ending_date: str
            - month_end: str
            - prior_month_end: str
            - retail_weeks_in_month: int
            - financial_year: str
            - fin_week_of_month: int
            - fin_week_of_year: int
            - prior_year_week_ending: str
            - current_fy_start: str
            - prior_fy_start: str
    """
    db_path = get_db_path()

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                sequence,
                week_ending_date,
                month_end,
                prior_month_end,
                retail_weeks_in_month,
                financial_year,
                fin_week_of_month,
                fin_week_of_year,
                prior_year_week_ending,
                current_fy_start,
                prior_fy_start
            FROM fiscal_calendar
            ORDER BY sequence
        """)

        return [dict(row) for row in cursor.fetchall()]


def get_market_share(
    region_code: Optional[str] = None,
    channel: str = 'Total',
    period_from: Optional[int] = None,
    period_to: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Queries market_share table with optional filters.

    Args:
        region_code: Region code to filter (e.g., 'Sydney')
        channel: Channel to filter (default: 'Total')
        period_from: Start period (YYYYMM format, inclusive)
        period_to: End period (YYYYMM format, inclusive)

    Returns:
        List[Dict]: List of dicts with keys:
            - period: int
            - region_code: str
            - region_name: str
            - industry_name: str
            - channel: str
            - market_size_dollars: float
            - market_share_pct: float
            - customer_penetration_pct: float
            - spend_per_customer: float
            - spend_per_transaction: float
            - transactions_per_customer: float
    """
    db_path = get_db_path()

    query = """
        SELECT
            period,
            region_code,
            region_name,
            industry_name,
            channel,
            market_size_dollars,
            market_share_pct,
            customer_penetration_pct,
            spend_per_customer,
            spend_per_transaction,
            transactions_per_customer
        FROM market_share
        WHERE channel = ?
    """

    params = [channel]

    if region_code:
        query += " AND region_code = ?"
        params.append(region_code)

    if period_from:
        query += " AND period >= ?"
        params.append(period_from)

    if period_to:
        query += " AND period <= ?"
        params.append(period_to)

    query += " ORDER BY period, region_code"

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]
