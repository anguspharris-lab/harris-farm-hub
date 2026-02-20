"""
Harris Farm Hub — PLU Data Layer
Query engine for PLU weekly results database (harris_farm_plu.db).
27.3M rows, 3 fiscal years, 43 stores, 26K+ active PLUs.
"""

import os
import sqlite3
from pathlib import Path

PLU_DB = str(Path(__file__).resolve().parent.parent / "data" / "harris_farm_plu.db")


def _get_conn():
    conn = sqlite3.connect(PLU_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def get_departments():
    """List all departments."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT DISTINCT department FROM dim_item WHERE department IS NOT NULL ORDER BY department"
    ).fetchall()
    conn.close()
    return [r["department"] for r in rows]


def get_stores():
    """List all stores with names."""
    conn = _get_conn()
    rows = conn.execute("SELECT store_id, store_name FROM dim_store ORDER BY store_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_fiscal_years():
    """Available fiscal years."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT DISTINCT fiscal_year FROM weekly_plu_results ORDER BY fiscal_year"
    ).fetchall()
    conn.close()
    return [r["fiscal_year"] for r in rows]


def department_summary(fiscal_year=None, channel="Retail"):
    """Department-level performance summary."""
    conn = _get_conn()
    fy_clause = f"AND f.fiscal_year = {int(fiscal_year)}" if fiscal_year else ""
    rows = conn.execute(f"""
        SELECT i.department,
               ROUND(SUM(f.sales_ex_gst), 0) as sales,
               ROUND(SUM(f.gross_margin), 0) as gm,
               ROUND(SUM(f.gross_margin) / NULLIF(SUM(f.sales_ex_gst), 0) * 100, 1) as gm_pct,
               ROUND(SUM(f.wastage), 0) as wastage,
               ROUND(SUM(f.wastage) / NULLIF(SUM(f.sales_ex_gst), 0) * 100, 1) as wastage_pct,
               ROUND(SUM(f.stocktake_cost), 0) as stocktake,
               COUNT(DISTINCT f.plu_code) as plu_count
        FROM weekly_plu_results f
        JOIN dim_item i ON f.plu_code = i.plu_code
        WHERE f.channel = ? {fy_clause}
        GROUP BY i.department
        ORDER BY sales DESC
    """, (channel,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def store_performance(fiscal_year=None, channel="Retail"):
    """Store-level performance ranking."""
    conn = _get_conn()
    fy_clause = f"AND f.fiscal_year = {int(fiscal_year)}" if fiscal_year else ""
    rows = conn.execute(f"""
        SELECT f.store_id, s.store_name,
               ROUND(SUM(f.sales_ex_gst), 0) as sales,
               ROUND(SUM(f.gross_margin), 0) as gm,
               ROUND(SUM(f.gross_margin) / NULLIF(SUM(f.sales_ex_gst), 0) * 100, 1) as gm_pct,
               ROUND(SUM(f.wastage), 0) as wastage,
               ROUND(SUM(f.wastage) / NULLIF(SUM(f.sales_ex_gst), 0) * 100, 1) as wastage_pct,
               COUNT(DISTINCT f.plu_code) as active_plus
        FROM weekly_plu_results f
        JOIN dim_store s ON f.store_id = s.store_id
        WHERE f.channel = ? {fy_clause}
        GROUP BY f.store_id
        HAVING sales > 0
        ORDER BY sales DESC
    """, (channel,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def top_plus_by_wastage(fiscal_year=None, department=None, limit=20, channel="Retail"):
    """Top PLUs by wastage (most negative = worst)."""
    conn = _get_conn()
    clauses = ["f.channel = ?"]
    params = [channel]
    if fiscal_year:
        clauses.append(f"f.fiscal_year = {int(fiscal_year)}")
    if department:
        clauses.append("i.department = ?")
        params.append(department)
    where = " AND ".join(clauses)
    rows = conn.execute(f"""
        SELECT f.plu_code, i.description, i.department, i.major_group,
               ROUND(SUM(f.wastage), 0) as total_wastage,
               ROUND(SUM(f.sales_ex_gst), 0) as total_sales,
               ROUND(SUM(f.wastage) / NULLIF(SUM(f.sales_ex_gst), 0) * 100, 1) as wastage_pct,
               COUNT(DISTINCT f.store_id) as store_count
        FROM weekly_plu_results f
        JOIN dim_item i ON f.plu_code = i.plu_code
        WHERE {where}
        GROUP BY f.plu_code
        HAVING total_wastage < -100
        ORDER BY total_wastage ASC
        LIMIT ?
    """, params + [limit]).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def top_plus_by_stocktake(fiscal_year=None, department=None, limit=20, channel="Retail"):
    """Top PLUs by stocktake variance."""
    conn = _get_conn()
    clauses = ["f.channel = ?"]
    params = [channel]
    if fiscal_year:
        clauses.append(f"f.fiscal_year = {int(fiscal_year)}")
    if department:
        clauses.append("i.department = ?")
        params.append(department)
    where = " AND ".join(clauses)
    rows = conn.execute(f"""
        SELECT f.plu_code, i.description, i.department,
               ROUND(SUM(f.stocktake_cost), 0) as total_variance,
               ROUND(SUM(f.sales_ex_gst), 0) as total_sales,
               ROUND(SUM(f.stocktake_cost) / NULLIF(SUM(f.sales_ex_gst), 0) * 100, 1) as variance_pct
        FROM weekly_plu_results f
        JOIN dim_item i ON f.plu_code = i.plu_code
        WHERE {where} AND f.stocktake_cost != 0
        GROUP BY f.plu_code
        ORDER BY total_variance ASC
        LIMIT ?
    """, params + [limit]).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def top_plus_by_revenue(fiscal_year=None, department=None, limit=20, channel="Retail"):
    """Top PLUs by revenue."""
    conn = _get_conn()
    clauses = ["f.channel = ?"]
    params = [channel]
    if fiscal_year:
        clauses.append(f"f.fiscal_year = {int(fiscal_year)}")
    if department:
        clauses.append("i.department = ?")
        params.append(department)
    where = " AND ".join(clauses)
    rows = conn.execute(f"""
        SELECT f.plu_code, i.description, i.department, i.major_group,
               ROUND(SUM(f.sales_ex_gst), 0) as sales,
               ROUND(SUM(f.gross_margin), 0) as gm,
               ROUND(SUM(f.gross_margin) / NULLIF(SUM(f.sales_ex_gst), 0) * 100, 1) as gm_pct,
               COUNT(DISTINCT f.store_id) as store_count
        FROM weekly_plu_results f
        JOIN dim_item i ON f.plu_code = i.plu_code
        WHERE {where}
        GROUP BY f.plu_code
        ORDER BY sales DESC
        LIMIT ?
    """, params + [limit]).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def plu_weekly_trend(plu_code, channel="Retail"):
    """Weekly time series for a specific PLU across all years."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT f.fiscal_year, f.fiscal_week,
               ROUND(SUM(f.sales_ex_gst), 2) as sales,
               ROUND(SUM(f.gross_margin), 2) as gm,
               ROUND(SUM(f.wastage), 2) as wastage,
               ROUND(SUM(f.stocktake_cost), 2) as stocktake,
               COUNT(DISTINCT f.store_id) as stores
        FROM weekly_plu_results f
        WHERE f.plu_code = ? AND f.channel = ?
        GROUP BY f.fiscal_year, f.fiscal_week
        ORDER BY f.fiscal_year, f.fiscal_week
    """, (str(plu_code), channel)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def plu_store_breakdown(plu_code, fiscal_year=None, channel="Retail"):
    """Store-level breakdown for a specific PLU."""
    conn = _get_conn()
    fy_clause = f"AND f.fiscal_year = {int(fiscal_year)}" if fiscal_year else ""
    rows = conn.execute(f"""
        SELECT f.store_id, s.store_name,
               ROUND(SUM(f.sales_ex_gst), 0) as sales,
               ROUND(SUM(f.gross_margin), 0) as gm,
               ROUND(SUM(f.wastage), 0) as wastage,
               ROUND(SUM(f.stocktake_cost), 0) as stocktake
        FROM weekly_plu_results f
        JOIN dim_store s ON f.store_id = s.store_id
        WHERE f.plu_code = ? AND f.channel = ? {fy_clause}
        GROUP BY f.store_id
        ORDER BY sales DESC
    """, (str(plu_code), channel)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_plu(query, limit=20):
    """Search PLU by code or description."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT plu_code, description, department, major_group, minor_group
        FROM dim_item
        WHERE plu_code LIKE ? OR description LIKE ? OR item_desc LIKE ?
        LIMIT ?
    """, (f"%{query}%", f"%{query.upper()}%", f"%{query.upper()}%", limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def weekly_department_trend(department, channel="Retail"):
    """Weekly sales/wastage trend for a department."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT f.fiscal_year, f.fiscal_week,
               ROUND(SUM(f.sales_ex_gst), 0) as sales,
               ROUND(SUM(f.gross_margin), 0) as gm,
               ROUND(SUM(f.wastage), 0) as wastage
        FROM weekly_plu_results f
        JOIN dim_item i ON f.plu_code = i.plu_code
        WHERE i.department = ? AND f.channel = ?
        GROUP BY f.fiscal_year, f.fiscal_week
        ORDER BY f.fiscal_year, f.fiscal_week
    """, (department, channel)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def db_available():
    """Check if PLU database exists."""
    return os.path.exists(PLU_DB)
