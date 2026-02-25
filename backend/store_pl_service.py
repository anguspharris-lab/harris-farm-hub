"""
Store P&L History Service
=========================
Parses the GL-level Store P&L CSV (wide pivot format) into a normalised
long-format SQLite table and provides query functions for dashboards.

Data source: data/hfm_uploads/store_pl_history.csv
Target table: store_pl_history in backend/hub_data.db

Schema (long format):
  store_id        INTEGER   — Store number (e.g. 10, 24, 28)
  store_name      TEXT      — Display name (e.g. "HFM Pennant Hills")
  channel         TEXT      — "Retail", "Online", or "Concession"
  area_group      TEXT      — AreaGroup1..10, ConcessionStores, NewStores
  gl_level1       TEXT      — P&L section (01-Sales, 02-Cost of sales, ...)
  gl_level2       TEXT      — Sub-section
  gl_level3       TEXT      — Detail level
  account_code    INTEGER   — GL account number
  account_name    TEXT      — GL account description
  year            INTEGER   — Calendar year
  month           INTEGER   — Calendar month (1-12)
  fy_year         INTEGER   — Fiscal year (starts July, so Jul 2024 = FY2025)
  fy_period       INTEGER   — Fiscal period 1-12 (Jul=1, Jun=12)
  value           REAL      — Dollar amount (AUD)
"""

import csv
import os
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
_PROJECT = _HERE.parent
_CSV_PATH = _PROJECT / "data" / "hfm_uploads" / "store_pl_history.csv"
_DB_PATH = _HERE / "hub_data.db"

# ---------------------------------------------------------------------------
# Fiscal calendar helpers
# ---------------------------------------------------------------------------

def _fy_from_cal(year: int, month: int) -> int:
    """Harris Farm FY starts July. Jul 2024 → FY2025."""
    return year + 1 if month >= 7 else year


def _fy_period(month: int) -> int:
    """Convert calendar month to fiscal period (Jul=1, Aug=2, ..., Jun=12)."""
    return month - 6 if month >= 7 else month + 6


# ---------------------------------------------------------------------------
# CSV parsing — wide to long
# ---------------------------------------------------------------------------

def parse_csv(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Parse the wide-format P&L CSV into a long-format DataFrame.

    Returns DataFrame with columns:
        store_id, store_name, channel, area_group,
        gl_level1, gl_level2, gl_level3,
        account_code, account_name,
        year, month, fy_year, fy_period, value
    """
    path = Path(csv_path) if csv_path else _CSV_PATH
    if not path.exists():
        raise FileNotFoundError(f"Store P&L CSV not found: {path}")

    # ------ Read header rows for year/month mapping ------
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        row_years = next(reader)    # Row 0: Year
        row_months = next(reader)   # Row 1: Month
        row_headers = next(reader)  # Row 2: Column names

    # Build (year, month) mapping for value columns (index 13+)
    period_map = {}  # col_index → (year, month)
    for i in range(13, len(row_years)):
        try:
            y = int(float(row_years[i]))
            m = int(float(row_months[i]))
            period_map[i] = (y, m)
        except (ValueError, IndexError):
            continue

    # ------ Read data rows ------
    rows_out = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for _ in range(3):
            next(reader)  # Skip header rows

        for row in reader:
            if len(row) < 14:
                continue

            # Metadata columns
            channel_raw = row[1].strip()  # "1. Retail", "2. Online", "3. Concession"
            channel = channel_raw.split(". ", 1)[-1] if ". " in channel_raw else channel_raw
            area_group = row[2].strip()

            try:
                store_id = int(row[3])
            except (ValueError, TypeError):
                continue

            store_company = row[4].strip()
            # Extract clean name: "10 - HFM Pennant Hills" → "HFM Pennant Hills"
            store_name = store_company.split(" - ", 1)[-1] if " - " in store_company else store_company

            gl_level1 = row[7].strip()
            gl_level2 = row[8].strip()
            gl_level3 = row[9].strip()

            try:
                account_code = int(row[10])
            except (ValueError, TypeError):
                account_code = 0

            account_name = row[11].strip()

            # Parse value columns
            for col_idx, (year, month) in period_map.items():
                if col_idx >= len(row):
                    continue
                raw = row[col_idx].strip()
                if not raw or raw == "":
                    continue

                # Parse comma-formatted numbers: "1,054,885.18" or "-45,598.34"
                try:
                    val = float(raw.replace(",", "").replace('"', ""))
                except ValueError:
                    continue

                if val == 0.0:
                    continue  # Skip zero values to reduce storage

                rows_out.append({
                    "store_id": store_id,
                    "store_name": store_name,
                    "channel": channel,
                    "area_group": area_group,
                    "gl_level1": gl_level1,
                    "gl_level2": gl_level2,
                    "gl_level3": gl_level3,
                    "account_code": account_code,
                    "account_name": account_name,
                    "year": year,
                    "month": month,
                    "fy_year": _fy_from_cal(year, month),
                    "fy_period": _fy_period(month),
                    "value": val,
                })

    df = pd.DataFrame(rows_out)
    return df


# ---------------------------------------------------------------------------
# SQLite storage
# ---------------------------------------------------------------------------

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS store_pl_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id    INTEGER NOT NULL,
    store_name  TEXT NOT NULL,
    channel     TEXT NOT NULL,
    area_group  TEXT NOT NULL,
    gl_level1   TEXT NOT NULL,
    gl_level2   TEXT NOT NULL,
    gl_level3   TEXT NOT NULL,
    account_code INTEGER NOT NULL,
    account_name TEXT NOT NULL,
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    fy_year     INTEGER NOT NULL,
    fy_period   INTEGER NOT NULL,
    value       REAL NOT NULL
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_spl_store ON store_pl_history(store_id);",
    "CREATE INDEX IF NOT EXISTS idx_spl_fy ON store_pl_history(fy_year, fy_period);",
    "CREATE INDEX IF NOT EXISTS idx_spl_gl1 ON store_pl_history(gl_level1);",
    "CREATE INDEX IF NOT EXISTS idx_spl_account ON store_pl_history(account_name);",
    "CREATE INDEX IF NOT EXISTS idx_spl_ym ON store_pl_history(year, month);",
]

# Summary P&L view — pre-aggregated per store per month
_CREATE_SUMMARY = """
CREATE TABLE IF NOT EXISTS store_pl_summary (
    store_id      INTEGER NOT NULL,
    store_name    TEXT NOT NULL,
    channel       TEXT NOT NULL,
    year          INTEGER NOT NULL,
    month         INTEGER NOT NULL,
    fy_year       INTEGER NOT NULL,
    fy_period     INTEGER NOT NULL,
    revenue       REAL DEFAULT 0,
    cogs          REAL DEFAULT 0,
    gross_profit  REAL DEFAULT 0,
    employment    REAL DEFAULT 0,
    occupancy     REAL DEFAULT 0,
    buying_fees   REAL DEFAULT 0,
    other_opex    REAL DEFAULT 0,
    ebitda        REAL DEFAULT 0,
    depreciation  REAL DEFAULT 0,
    non_operating REAL DEFAULT 0,
    interest      REAL DEFAULT 0,
    tax           REAL DEFAULT 0,
    net_profit    REAL DEFAULT 0,
    PRIMARY KEY (store_id, year, month)
);
"""


def ingest_to_sqlite(df: Optional[pd.DataFrame] = None, db_path: Optional[str] = None):
    """Load parsed P&L data into SQLite. Drops and recreates tables."""
    if df is None:
        df = parse_csv()

    db = Path(db_path) if db_path else _DB_PATH
    conn = sqlite3.connect(str(db))
    cur = conn.cursor()

    # Recreate detail table
    cur.execute("DROP TABLE IF EXISTS store_pl_history")
    cur.execute(_CREATE_TABLE)
    for idx_sql in _CREATE_INDEXES:
        cur.execute(idx_sql)

    # Bulk insert
    cols = [
        "store_id", "store_name", "channel", "area_group",
        "gl_level1", "gl_level2", "gl_level3",
        "account_code", "account_name",
        "year", "month", "fy_year", "fy_period", "value",
    ]
    placeholders = ", ".join(["?"] * len(cols))
    insert_sql = f"INSERT INTO store_pl_history ({', '.join(cols)}) VALUES ({placeholders})"

    records = df[cols].values.tolist()
    cur.executemany(insert_sql, records)

    # Build summary table
    cur.execute("DROP TABLE IF EXISTS store_pl_summary")
    cur.execute(_CREATE_SUMMARY)

    # Map GL_Level1 to summary columns
    gl1_mapping = {
        "01-Sales": "revenue",
        "02-Cost of sales": "cogs",
        "03-Employment expenses": "employment",
        "04-Occupancy costs": "occupancy",
        "05-Buying Fees": "buying_fees",
        "06-Other operating expenses": "other_opex",
        "07-Non-operating inc and exp": "non_operating",
        "08-Depreciation & amortisation": "depreciation",
        "10-Interest & finance costs": "interest",
        "11-Tax expense": "tax",
    }

    # Aggregate by store/month/gl_level1
    agg = df.groupby(["store_id", "store_name", "channel", "year", "month", "fy_year", "fy_period", "gl_level1"])["value"].sum().reset_index()

    # Pivot to one row per store-month
    pivot = agg.pivot_table(
        index=["store_id", "store_name", "channel", "year", "month", "fy_year", "fy_period"],
        columns="gl_level1",
        values="value",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    # Flatten column names
    pivot.columns = [c if isinstance(c, str) and c else str(c) for c in pivot.columns]

    # Build summary rows
    summary_rows = []
    for _, r in pivot.iterrows():
        revenue = float(r.get("01-Sales", 0))
        cogs = float(r.get("02-Cost of sales", 0))
        employment = float(r.get("03-Employment expenses", 0))
        occupancy_val = float(r.get("04-Occupancy costs", 0))
        buying = float(r.get("05-Buying Fees", 0))
        other_opex = float(r.get("06-Other operating expenses", 0))
        non_op = float(r.get("07-Non-operating inc and exp", 0))
        depreciation = float(r.get("08-Depreciation & amortisation", 0))
        interest_val = float(r.get("10-Interest & finance costs", 0))
        tax_val = float(r.get("11-Tax expense", 0))

        gross_profit = revenue + cogs  # COGS is negative in GL
        ebitda = gross_profit + employment + occupancy_val + buying + other_opex
        net_profit = ebitda + depreciation + non_op + interest_val + tax_val

        summary_rows.append((
            int(r["store_id"]), str(r["store_name"]), str(r["channel"]),
            int(r["year"]), int(r["month"]), int(r["fy_year"]), int(r["fy_period"]),
            revenue, cogs, gross_profit, employment, occupancy_val, buying,
            other_opex, ebitda, depreciation, non_op, interest_val, tax_val, net_profit,
        ))

    cur.executemany(
        """INSERT OR REPLACE INTO store_pl_summary
           (store_id, store_name, channel, year, month, fy_year, fy_period,
            revenue, cogs, gross_profit, employment, occupancy, buying_fees,
            other_opex, ebitda, depreciation, non_operating, interest, tax, net_profit)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        summary_rows,
    )

    conn.commit()
    detail_count = cur.execute("SELECT COUNT(*) FROM store_pl_history").fetchone()[0]
    summary_count = cur.execute("SELECT COUNT(*) FROM store_pl_summary").fetchone()[0]
    conn.close()

    return {"detail_rows": detail_count, "summary_rows": summary_count}


# ---------------------------------------------------------------------------
# Query functions (used by dashboards and API)
# ---------------------------------------------------------------------------

def _get_conn():
    return sqlite3.connect(str(_DB_PATH))


def _clean_for_json(df: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN/inf with None so JSON serialisation works."""
    import numpy as np
    return df.replace([np.inf, -np.inf, np.nan], None)


def get_summary_df(
    store_ids: Optional[list] = None,
    fy_years: Optional[list] = None,
    channel: Optional[str] = None,
) -> pd.DataFrame:
    """Get the pre-aggregated P&L summary. Returns one row per store per month."""
    conn = _get_conn()
    query = "SELECT * FROM store_pl_summary WHERE 1=1"
    params = []
    if store_ids:
        placeholders = ",".join(["?"] * len(store_ids))
        query += f" AND store_id IN ({placeholders})"
        params.extend(store_ids)
    if fy_years:
        placeholders = ",".join(["?"] * len(fy_years))
        query += f" AND fy_year IN ({placeholders})"
        params.extend(fy_years)
    if channel:
        query += " AND channel = ?"
        params.append(channel)
    query += " ORDER BY store_id, year, month"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_detail_df(
    store_ids: Optional[list] = None,
    fy_years: Optional[list] = None,
    gl_level1: Optional[str] = None,
    account_name: Optional[str] = None,
) -> pd.DataFrame:
    """Get detailed GL-level P&L data."""
    conn = _get_conn()
    query = "SELECT * FROM store_pl_history WHERE 1=1"
    params = []
    if store_ids:
        placeholders = ",".join(["?"] * len(store_ids))
        query += f" AND store_id IN ({placeholders})"
        params.extend(store_ids)
    if fy_years:
        placeholders = ",".join(["?"] * len(fy_years))
        query += f" AND fy_year IN ({placeholders})"
        params.extend(fy_years)
    if gl_level1:
        query += " AND gl_level1 = ?"
        params.append(gl_level1)
    if account_name:
        query += " AND account_name = ?"
        params.append(account_name)
    query += " ORDER BY store_id, year, month"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_store_pl_annual(fy_year: Optional[int] = None, channel: str = "Retail") -> pd.DataFrame:
    """Annual P&L by store. If no FY given, uses the most recent complete FY."""
    conn = _get_conn()
    if fy_year is None:
        row = conn.execute(
            "SELECT MAX(fy_year) FROM store_pl_summary WHERE fy_period = 12"
        ).fetchone()
        fy_year = row[0] if row and row[0] else 2025

    query = """
        SELECT store_id, store_name,
               SUM(revenue) as revenue,
               SUM(cogs) as cogs,
               SUM(gross_profit) as gross_profit,
               SUM(employment) as employment,
               SUM(occupancy) as occupancy,
               SUM(buying_fees) as buying_fees,
               SUM(other_opex) as other_opex,
               SUM(ebitda) as ebitda,
               SUM(depreciation) as depreciation,
               SUM(non_operating) as non_operating,
               SUM(interest) as interest,
               SUM(tax) as tax,
               SUM(net_profit) as net_profit
        FROM store_pl_summary
        WHERE fy_year = ? AND channel = ?
        GROUP BY store_id, store_name
        ORDER BY revenue DESC
    """
    df = pd.read_sql_query(query, conn, params=[fy_year, channel])
    conn.close()

    if not df.empty:
        df["gp_pct"] = (df["gross_profit"] / df["revenue"].replace(0, float("nan")) * 100).round(2)
        df["ebitda_pct"] = (df["ebitda"] / df["revenue"].replace(0, float("nan")) * 100).round(2)
        df["net_pct"] = (df["net_profit"] / df["revenue"].replace(0, float("nan")) * 100).round(2)

    return _clean_for_json(df)


def get_network_monthly_trend(channel: str = "Retail") -> pd.DataFrame:
    """Monthly network-level P&L trend (all stores aggregated)."""
    conn = _get_conn()
    query = """
        SELECT year, month, fy_year, fy_period,
               SUM(revenue) as revenue,
               SUM(gross_profit) as gross_profit,
               SUM(ebitda) as ebitda,
               SUM(net_profit) as net_profit,
               COUNT(DISTINCT store_id) as store_count
        FROM store_pl_summary
        WHERE channel = ?
        GROUP BY year, month
        ORDER BY year, month
    """
    df = pd.read_sql_query(query, conn, params=[channel])
    conn.close()
    if not df.empty:
        df["gp_pct"] = (df["gross_profit"] / df["revenue"].replace(0, float("nan")) * 100).round(2)
        df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    return _clean_for_json(df)


def get_store_monthly_trend(store_id: int) -> pd.DataFrame:
    """Monthly P&L trend for a single store."""
    conn = _get_conn()
    query = """
        SELECT * FROM store_pl_summary
        WHERE store_id = ?
        ORDER BY year, month
    """
    df = pd.read_sql_query(query, conn, params=[store_id])
    conn.close()
    if not df.empty:
        df["gp_pct"] = (df["gross_profit"] / df["revenue"].replace(0, float("nan")) * 100).round(2)
        df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    return _clean_for_json(df)


def get_available_fy_years() -> list:
    """Return list of fiscal years that have data."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT DISTINCT fy_year FROM store_pl_summary ORDER BY fy_year"
        ).fetchall()
        return [r[0] for r in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def get_stores_list() -> list:
    """Return list of {store_id, store_name, channel} dicts."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT DISTINCT store_id, store_name, channel FROM store_pl_summary ORDER BY store_id"
        ).fetchall()
        return [{"store_id": r[0], "store_name": r[1], "channel": r[2]} for r in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def get_store_cost_breakdown(store_id: int, fy_year: Optional[int] = None) -> pd.DataFrame:
    """Detailed cost breakdown for a store in a fiscal year."""
    conn = _get_conn()
    if fy_year is None:
        row = conn.execute(
            "SELECT MAX(fy_year) FROM store_pl_history WHERE store_id = ? AND fy_period = 12",
            [store_id]
        ).fetchone()
        fy_year = row[0] if row and row[0] else 2025

    query = """
        SELECT gl_level1, gl_level2, account_name,
               SUM(value) as total
        FROM store_pl_history
        WHERE store_id = ? AND fy_year = ?
        GROUP BY gl_level1, gl_level2, account_name
        ORDER BY gl_level1, gl_level2, total DESC
    """
    df = pd.read_sql_query(query, conn, params=[store_id, fy_year])
    conn.close()
    return df


def get_lfl_comparison(fy_year: int, prior_fy: Optional[int] = None, channel: str = "Retail") -> pd.DataFrame:
    """Like-for-like comparison: stores present in both years."""
    if prior_fy is None:
        prior_fy = fy_year - 1

    current = get_store_pl_annual(fy_year, channel)
    prior = get_store_pl_annual(prior_fy, channel)

    if current.empty or prior.empty:
        return pd.DataFrame()

    # Only stores in both years
    common = set(current["store_id"]) & set(prior["store_id"])
    curr_lfl = current[current["store_id"].isin(common)].copy()
    prev_lfl = prior[prior["store_id"].isin(common)].copy()

    merged = curr_lfl.merge(
        prev_lfl[["store_id", "revenue", "gross_profit", "ebitda", "net_profit", "gp_pct"]],
        on="store_id", suffixes=("", "_prior"),
    )

    merged["revenue_growth_pct"] = (
        (merged["revenue"] - merged["revenue_prior"]) / merged["revenue_prior"].replace(0, float("nan")) * 100
    ).round(2)
    merged["gp_change_pp"] = (merged["gp_pct"] - merged["gp_pct_prior"]).round(2)

    return _clean_for_json(merged)


def get_ebit_by_store(fy_year: Optional[int] = None, channel: str = "Retail") -> pd.DataFrame:
    """EBIT by store — used for ROCE calculations.
    EBIT = EBITDA + Depreciation (depreciation is already negative in GL).
    """
    annual = get_store_pl_annual(fy_year, channel)
    if annual.empty:
        return annual
    annual["ebit"] = annual["ebitda"] + annual["depreciation"]
    annual["ebit_pct"] = (annual["ebit"] / annual["revenue"].replace(0, float("nan")) * 100).round(2)
    return _clean_for_json(annual)


def get_data_quality_report() -> dict:
    """Run data quality checks for WATCHDOG."""
    conn = _get_conn()
    checks = []

    try:
        # 1. Row counts
        detail = conn.execute("SELECT COUNT(*) FROM store_pl_history").fetchone()[0]
        summary = conn.execute("SELECT COUNT(*) FROM store_pl_summary").fetchone()[0]
        checks.append({"check": "Row counts", "status": "PASS", "detail": f"Detail: {detail:,}, Summary: {summary:,}"})

        # 2. Store count
        stores = conn.execute("SELECT COUNT(DISTINCT store_id) FROM store_pl_summary").fetchone()[0]
        checks.append({"check": "Store count", "status": "PASS", "detail": f"{stores} stores"})

        # 3. Date range
        min_date = conn.execute("SELECT MIN(year || '-' || printf('%02d', month)) FROM store_pl_summary").fetchone()[0]
        max_date = conn.execute("SELECT MAX(year || '-' || printf('%02d', month)) FROM store_pl_summary").fetchone()[0]
        checks.append({"check": "Date range", "status": "PASS", "detail": f"{min_date} to {max_date}"})

        # 4. Negative revenue check
        neg_rev = conn.execute(
            "SELECT COUNT(*) FROM store_pl_summary WHERE revenue < -1000"
        ).fetchone()[0]
        status = "WARN" if neg_rev > 0 else "PASS"
        checks.append({"check": "Negative revenue", "status": status, "detail": f"{neg_rev} months with revenue < -$1,000"})

        # 5. GP margin range
        weird_gp = conn.execute("""
            SELECT COUNT(*) FROM store_pl_summary
            WHERE revenue > 10000
              AND (gross_profit / revenue * 100 < 10 OR gross_profit / revenue * 100 > 60)
        """).fetchone()[0]
        status = "WARN" if weird_gp > 10 else "PASS"
        checks.append({"check": "GP margin range (10-60%)", "status": status, "detail": f"{weird_gp} months outside range"})

        # 6. Period completeness
        gaps = conn.execute("""
            SELECT store_id, store_name, COUNT(DISTINCT year || '-' || month) as periods
            FROM store_pl_summary
            WHERE channel = 'Retail'
            GROUP BY store_id
            ORDER BY periods
            LIMIT 5
        """).fetchall()
        min_periods = gaps[0][2] if gaps else 0
        checks.append({"check": "Period completeness", "status": "INFO",
                       "detail": f"Min periods per store: {min_periods}, Store: {gaps[0][1] if gaps else 'N/A'}"})

    except sqlite3.OperationalError as e:
        checks.append({"check": "Database", "status": "FAIL", "detail": str(e)})
    finally:
        conn.close()

    return {"checks": checks, "passed": sum(1 for c in checks if c["status"] == "PASS"), "total": len(checks)}


# ---------------------------------------------------------------------------
# CLI entry point — run `python3 -m backend.store_pl_service` to ingest
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Parsing Store P&L CSV...")
    df = parse_csv()
    print(f"  Parsed {len(df):,} rows from {df['store_id'].nunique()} stores")
    print(f"  FY range: {df['fy_year'].min()} to {df['fy_year'].max()}")
    print(f"  GL Level1 categories: {sorted(df['gl_level1'].unique())}")

    print("\nIngesting into SQLite...")
    result = ingest_to_sqlite(df)
    print(f"  Detail rows: {result['detail_rows']:,}")
    print(f"  Summary rows: {result['summary_rows']:,}")

    print("\nRunning data quality checks...")
    qc = get_data_quality_report()
    for c in qc["checks"]:
        icon = "✅" if c["status"] == "PASS" else "⚠️" if c["status"] == "WARN" else "ℹ️"
        print(f"  {icon} {c['check']}: {c['detail']}")

    print(f"\n{'✅' if qc['passed'] == qc['total'] else '⚠️'} {qc['passed']}/{qc['total']} checks passed")
