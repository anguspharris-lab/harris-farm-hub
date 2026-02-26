"""
Harris Farm Hub — MDHE (Master Data Health Engine) Database Module
Handles data quality tracking, validation results, health scores, issues,
scan verification, and PLU master records.
All data stored in hub_data.db alongside other Hub application tables.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("hub_mdhe")

_DB = Path(__file__).resolve().parent / "hub_data.db"

_INIT_DONE = False


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def _get_conn():
    """Get SQLite connection to hub_data.db with row factory."""
    conn = sqlite3.connect(str(_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_mdhe_db():
    """Create all MDHE tables if they don't exist."""
    global _INIT_DONE
    if _INIT_DONE:
        return

    _DB.parent.mkdir(parents=True, exist_ok=True)
    conn = _get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS mdhe_data_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            filename TEXT NOT NULL,
            uploaded_by TEXT,
            uploaded_at TEXT DEFAULT (datetime('now')),
            row_count INTEGER,
            status TEXT DEFAULT 'processing',
            notes TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS mdhe_validations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER REFERENCES mdhe_data_sources(id),
            rule_id TEXT NOT NULL,
            layer TEXT NOT NULL,
            severity TEXT NOT NULL,
            field TEXT,
            record_key TEXT,
            message TEXT NOT NULL,
            details TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS mdhe_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score_date TEXT NOT NULL,
            domain TEXT NOT NULL,
            total_records INTEGER,
            passed INTEGER,
            failed INTEGER,
            score REAL,
            layer_scores TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS mdhe_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            validation_id INTEGER REFERENCES mdhe_validations(id),
            title TEXT NOT NULL,
            description TEXT,
            domain TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            assigned_to TEXT,
            resolved_by TEXT,
            resolved_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS mdhe_scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL,
            plu_code TEXT,
            scan_source TEXT NOT NULL,
            last_scan_date TEXT,
            scan_count INTEGER DEFAULT 0,
            success_rate REAL,
            manual_key_rate REAL,
            status TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS mdhe_plu_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plu_code TEXT NOT NULL,
            barcode TEXT,
            description TEXT,
            category TEXT,
            subcategory TEXT,
            unit_of_measure TEXT,
            pack_size REAL,
            supplier_code TEXT,
            status TEXT DEFAULT 'active',
            retail_price REAL,
            cost_price REAL,
            created_date TEXT,
            last_modified TEXT,
            source_id INTEGER REFERENCES mdhe_data_sources(id),
            is_dummy INTEGER DEFAULT 0
        )
    """)

    # Indexes for common queries
    c.execute("CREATE INDEX IF NOT EXISTS idx_mdhe_val_source ON mdhe_validations(source_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_mdhe_val_layer ON mdhe_validations(layer)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_mdhe_val_severity ON mdhe_validations(severity)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_mdhe_scores_date ON mdhe_scores(score_date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_mdhe_issues_status ON mdhe_issues(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_mdhe_scan_barcode ON mdhe_scan_results(barcode)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_mdhe_plu_code ON mdhe_plu_master(plu_code)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_mdhe_plu_dummy ON mdhe_plu_master(is_dummy)")

    conn.commit()
    conn.close()
    _INIT_DONE = True


def _ensure_init():
    """Lazy init — call init if not yet done."""
    if not _INIT_DONE:
        init_mdhe_db()


# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

def add_data_source(source_type, filename, uploaded_by=None, row_count=0, notes=None):
    """Insert a data source record. Return the new id."""
    _ensure_init()
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO mdhe_data_sources (source_type, filename, uploaded_by, row_count, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (source_type, filename, uploaded_by, int(row_count), notes),
    )
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_data_source_status(source_id, status, row_count=None):
    """Update source status to 'validated' or 'failed'."""
    _ensure_init()
    conn = _get_conn()
    if row_count is not None:
        conn.execute(
            "UPDATE mdhe_data_sources SET status = ?, row_count = ? WHERE id = ?",
            (status, int(row_count), int(source_id)),
        )
    else:
        conn.execute(
            "UPDATE mdhe_data_sources SET status = ? WHERE id = ?",
            (status, int(source_id)),
        )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Validations
# ---------------------------------------------------------------------------

def add_validation(source_id, rule_id, layer, severity, field, record_key, message, details=None):
    """Insert a single validation result. Return the new id."""
    _ensure_init()
    details_str = json.dumps(details) if isinstance(details, (dict, list)) else details
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO mdhe_validations "
        "(source_id, rule_id, layer, severity, field, record_key, message, details) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (int(source_id), rule_id, layer, severity, field, record_key, message, details_str),
    )
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def add_validations_bulk(validations_list):
    """
    Insert multiple validations efficiently.
    Each item is a dict with keys matching add_validation params.
    Returns list of new ids.
    """
    _ensure_init()
    if not validations_list:
        return []

    conn = _get_conn()
    c = conn.cursor()
    ids = []
    for v in validations_list:
        details = v.get("details")
        details_str = json.dumps(details) if isinstance(details, (dict, list)) else details
        c.execute(
            "INSERT INTO mdhe_validations "
            "(source_id, rule_id, layer, severity, field, record_key, message, details) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                int(v["source_id"]),
                v["rule_id"],
                v["layer"],
                v["severity"],
                v.get("field"),
                v.get("record_key"),
                v["message"],
                details_str,
            ),
        )
        ids.append(c.lastrowid)
    conn.commit()
    conn.close()
    return ids


def get_validations(source_id=None, layer=None, severity=None, domain=None, limit=500):
    """
    Get validation results with optional filtering.
    domain maps to layer for filtering purposes.
    Returns list of dicts.
    """
    _ensure_init()
    conn = _get_conn()
    query = "SELECT * FROM mdhe_validations WHERE 1=1"
    params = []

    if source_id is not None:
        query += " AND source_id = ?"
        params.append(int(source_id))
    if layer is not None:
        query += " AND layer = ?"
        params.append(layer)
    if severity is not None:
        query += " AND severity = ?"
        params.append(severity)
    if domain is not None:
        query += " AND layer = ?"
        params.append(domain)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(int(limit))

    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        # Parse JSON details if stored as string
        if d.get("details"):
            try:
                d["details"] = json.loads(d["details"])
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(d)
    return results


# ---------------------------------------------------------------------------
# Scores
# ---------------------------------------------------------------------------

def save_scores(score_date, domain_scores):
    """
    Save health scores.
    domain_scores is a dict: {domain: {total, passed, failed, score, layer_scores}}.
    """
    _ensure_init()
    conn = _get_conn()
    for domain, data in domain_scores.items():
        layer_scores = data.get("layer_scores")
        layer_scores_str = json.dumps(layer_scores) if isinstance(layer_scores, (dict, list)) else layer_scores
        conn.execute(
            "INSERT INTO mdhe_scores "
            "(score_date, domain, total_records, passed, failed, score, layer_scores) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                score_date,
                domain,
                int(data.get("total", 0)),
                int(data.get("passed", 0)),
                int(data.get("failed", 0)),
                float(data.get("score", 0.0)),
                layer_scores_str,
            ),
        )
    conn.commit()
    conn.close()


def get_latest_scores():
    """
    Return the most recent scores for all domains.
    Returns list of dicts.
    """
    _ensure_init()
    conn = _get_conn()
    rows = conn.execute("""
        SELECT s.*
        FROM mdhe_scores s
        INNER JOIN (
            SELECT domain, MAX(score_date) AS max_date
            FROM mdhe_scores
            GROUP BY domain
        ) latest ON s.domain = latest.domain AND s.score_date = latest.max_date
        ORDER BY s.domain
    """).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        if d.get("layer_scores"):
            try:
                d["layer_scores"] = json.loads(d["layer_scores"])
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(d)
    return results


def get_score_history(days=30):
    """
    Return score history for the last N days.
    Returns list of dicts ordered by date ascending.
    """
    _ensure_init()
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM mdhe_scores WHERE score_date >= ? ORDER BY score_date ASC, domain ASC",
        (cutoff,),
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        if d.get("layer_scores"):
            try:
                d["layer_scores"] = json.loads(d["layer_scores"])
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(d)
    return results


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

def create_issue(validation_id, title, description, domain, severity):
    """Create an issue from a validation failure. Return issue id."""
    _ensure_init()
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO mdhe_issues "
        "(validation_id, title, description, domain, severity, updated_at) "
        "VALUES (?, ?, ?, ?, ?, datetime('now'))",
        (int(validation_id) if validation_id else None, title, description, domain, severity),
    )
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def create_issues_from_validations(source_id, min_severity="medium"):
    """
    Auto-generate issues from validation results.
    Only for 'critical' and 'high' by default (min_severity='medium' includes medium+).
    Returns list of created issue ids.
    """
    _ensure_init()
    severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    min_level = severity_levels.get(min_severity, 1)

    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM mdhe_validations WHERE source_id = ? ORDER BY id",
        (int(source_id),),
    ).fetchall()

    issue_ids = []
    for r in rows:
        row_level = severity_levels.get(r["severity"], 0)
        if row_level < min_level:
            continue

        # Check if issue already exists for this validation
        existing = conn.execute(
            "SELECT id FROM mdhe_issues WHERE validation_id = ?", (r["id"],)
        ).fetchone()
        if existing:
            continue

        title = "DQ Issue: {}".format(r["message"][:80])
        description = "Validation {} failed for field '{}' on record '{}'. {}".format(
            r["rule_id"],
            r["field"] or "N/A",
            r["record_key"] or "N/A",
            r["message"],
        )

        c = conn.cursor()
        c.execute(
            "INSERT INTO mdhe_issues "
            "(validation_id, title, description, domain, severity, updated_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (r["id"], title, description, r["layer"], r["severity"]),
        )
        issue_ids.append(c.lastrowid)

    conn.commit()
    conn.close()
    return issue_ids


def get_issues(status=None, domain=None, severity=None, limit=200):
    """Get issues with optional filtering. Returns list of dicts."""
    _ensure_init()
    conn = _get_conn()
    query = "SELECT * FROM mdhe_issues WHERE 1=1"
    params = []

    if status is not None:
        query += " AND status = ?"
        params.append(status)
    if domain is not None:
        query += " AND domain = ?"
        params.append(domain)
    if severity is not None:
        query += " AND severity = ?"
        params.append(severity)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(int(limit))

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_issue(issue_id, status=None, assigned_to=None, resolved_by=None):
    """Update issue status/assignment."""
    _ensure_init()
    conn = _get_conn()
    updates = []
    values = []

    if status is not None:
        updates.append("status = ?")
        values.append(status)
    if assigned_to is not None:
        updates.append("assigned_to = ?")
        values.append(assigned_to)
    if resolved_by is not None:
        updates.append("resolved_by = ?")
        values.append(resolved_by)
        updates.append("resolved_at = datetime('now')")

    if not updates:
        conn.close()
        return

    updates.append("updated_at = datetime('now')")
    values.append(int(issue_id))

    conn.execute(
        "UPDATE mdhe_issues SET {} WHERE id = ?".format(", ".join(updates)),
        values,
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Scan results
# ---------------------------------------------------------------------------

def save_scan_results(scan_data):
    """
    Save scan verification results.
    scan_data is list of dicts with barcode, plu_code, scan_source, etc.
    """
    _ensure_init()
    if not scan_data:
        return

    conn = _get_conn()
    for item in scan_data:
        conn.execute(
            "INSERT INTO mdhe_scan_results "
            "(barcode, plu_code, scan_source, last_scan_date, scan_count, "
            "success_rate, manual_key_rate, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(item.get("barcode", "")),
                str(item.get("plu_code", "")) if item.get("plu_code") else None,
                str(item.get("scan_source", "")),
                item.get("last_scan_date"),
                int(item.get("scan_count", 0)),
                float(item.get("success_rate", 0.0)) if item.get("success_rate") is not None else None,
                float(item.get("manual_key_rate", 0.0)) if item.get("manual_key_rate") is not None else None,
                item.get("status"),
            ),
        )
    conn.commit()
    conn.close()


def get_scan_results(scan_source=None):
    """Get scan results with optional source filter. Returns list of dicts."""
    _ensure_init()
    conn = _get_conn()
    if scan_source:
        rows = conn.execute(
            "SELECT * FROM mdhe_scan_results WHERE scan_source = ? ORDER BY id DESC",
            (scan_source,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM mdhe_scan_results ORDER BY id DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# PLU master records
# ---------------------------------------------------------------------------

def save_plu_records(records, source_id, is_dummy=0):
    """
    Save PLU master records from upload.
    Records is list of dicts with keys matching mdhe_plu_master columns.
    """
    _ensure_init()
    if not records:
        return

    conn = _get_conn()
    for rec in records:
        conn.execute(
            "INSERT INTO mdhe_plu_master "
            "(plu_code, barcode, description, category, subcategory, unit_of_measure, "
            "pack_size, supplier_code, status, retail_price, cost_price, created_date, "
            "last_modified, source_id, is_dummy) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(rec.get("plu_code", "")),
                str(rec.get("barcode", "")) if rec.get("barcode") else None,
                rec.get("description"),
                rec.get("category"),
                rec.get("subcategory"),
                rec.get("unit_of_measure"),
                float(rec["pack_size"]) if rec.get("pack_size") else None,
                rec.get("supplier_code"),
                rec.get("status", "active"),
                float(rec["retail_price"]) if rec.get("retail_price") is not None else None,
                float(rec["cost_price"]) if rec.get("cost_price") is not None else None,
                rec.get("created_date"),
                rec.get("last_modified"),
                int(source_id),
                int(is_dummy),
            ),
        )
    conn.commit()
    conn.close()


def get_plu_records(source_id=None, include_dummy=True):
    """Get PLU master records. Returns list of dicts."""
    _ensure_init()
    conn = _get_conn()
    query = "SELECT * FROM mdhe_plu_master WHERE 1=1"
    params = []

    if source_id is not None:
        query += " AND source_id = ?"
        params.append(int(source_id))
    if not include_dummy:
        query += " AND is_dummy = 0"

    query += " ORDER BY plu_code ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Dummy data management
# ---------------------------------------------------------------------------

def clear_dummy_data():
    """Remove all dummy/demo data (where is_dummy=1). Easy cleanup."""
    _ensure_init()
    conn = _get_conn()

    # Get source_ids for dummy data
    dummy_sources = conn.execute(
        "SELECT id FROM mdhe_data_sources WHERE notes LIKE '%dummy%' OR notes LIKE '%demo%'"
    ).fetchall()
    dummy_source_ids = [r["id"] for r in dummy_sources]

    # Delete PLU records flagged as dummy
    conn.execute("DELETE FROM mdhe_plu_master WHERE is_dummy = 1")

    # Delete scan results for dummy PLUs (barcode pattern)
    conn.execute("DELETE FROM mdhe_scan_results WHERE barcode LIKE '930060123456%' OR barcode = 'INVALID123'")

    # Delete validations and issues for dummy sources
    for sid in dummy_source_ids:
        # Delete issues linked to validations for this source
        conn.execute(
            "DELETE FROM mdhe_issues WHERE validation_id IN "
            "(SELECT id FROM mdhe_validations WHERE source_id = ?)",
            (sid,),
        )
        conn.execute("DELETE FROM mdhe_validations WHERE source_id = ?", (sid,))

    # Delete dummy data sources
    for sid in dummy_source_ids:
        conn.execute("DELETE FROM mdhe_data_sources WHERE id = ?", (sid,))

    # Delete score history for dummy data (scores with domain containing our demo domains)
    conn.execute(
        "DELETE FROM mdhe_scores WHERE score_date IN "
        "(SELECT DISTINCT score_date FROM mdhe_scores WHERE domain = 'overall')"
    )

    conn.commit()
    conn.close()
    logger.info("Cleared all MDHE dummy data")


def seed_dummy_data():
    """
    Insert 10 realistic dummy PLU records with deliberate data quality issues
    for demo. Also generates pre-computed validation results, scores, issues,
    and scan data. All dummy records have is_dummy=1 for easy cleanup.
    """
    _ensure_init()

    # Clear any existing dummy data first
    clear_dummy_data()

    # -----------------------------------------------------------------------
    # 1. Create a dummy data source
    # -----------------------------------------------------------------------
    source_id = add_data_source(
        source_type="plu_master",
        filename="demo_plu_master_10.csv",
        uploaded_by="system",
        row_count=10,
        notes="dummy demo data — seed_dummy_data()",
    )
    update_data_source_status(source_id, "validated", row_count=10)

    # -----------------------------------------------------------------------
    # 2. Insert 10 PLU records with deliberate quality issues
    # -----------------------------------------------------------------------
    today = datetime.utcnow().strftime("%Y-%m-%d")

    plu_records = [
        {
            "plu_code": "1001",
            "barcode": "9300601234561",
            "description": "Organic Avocado Hass",
            "category": "Fruit",
            "subcategory": "Avocados",
            "unit_of_measure": "ea",
            "pack_size": None,
            "supplier_code": "SUP001",
            "status": "active",
            "retail_price": 3.50,
            "cost_price": 1.80,
            "created_date": today,
            "last_modified": today,
        },
        {
            "plu_code": "1002",
            "barcode": "9300601234578",
            "description": "BANANA CAVENDISH",  # ALL CAPS — standards violation
            "category": "Fruit",
            "subcategory": "Bananas",
            "unit_of_measure": "kg",
            "pack_size": None,
            "supplier_code": "SUP002",
            "status": "active",
            "retail_price": 3.99,
            "cost_price": 1.50,
            "created_date": today,
            "last_modified": today,
        },
        {
            "plu_code": "1003",
            "barcode": "9300601234585",
            "description": "Pink Lady Apple 1kg",
            "category": "Fruit",
            "subcategory": "Apples",
            "unit_of_measure": "kg",
            "pack_size": 1.0,
            "supplier_code": "SUP003",
            "status": "active",
            "retail_price": 5.99,
            "cost_price": 3.20,
            "created_date": today,
            "last_modified": today,
        },
        {
            "plu_code": "1004",
            "barcode": "9300601234592",
            "description": "Chicken Breast Free Range",
            "category": "Bakery",  # WRONG — should be Meat
            "subcategory": "Bread",  # WRONG — should be Poultry
            "unit_of_measure": "kg",
            "pack_size": None,
            "supplier_code": "SUP004",
            "status": "active",
            "retail_price": 16.99,
            "cost_price": 9.50,
            "created_date": today,
            "last_modified": today,
        },
        {
            "plu_code": "1005",
            "barcode": "9300601234608",
            "description": "",  # MISSING description
            "category": "Vegetables",
            "subcategory": "Potatoes",
            "unit_of_measure": "kg",
            "pack_size": None,
            "supplier_code": "SUP005",
            "status": "active",
            "retail_price": 4.99,
            "cost_price": 2.10,
            "created_date": today,
            "last_modified": today,
        },
        {
            "plu_code": "1006",
            "barcode": "9300601234615",
            "description": "Sourdough Loaf",
            "category": "Bakery",
            "subcategory": "Bread",
            "unit_of_measure": "ea",
            "pack_size": None,
            "supplier_code": "SUP006",
            "status": "active",
            "retail_price": 6.50,
            "cost_price": 8.20,  # Cost > Retail!
            "created_date": today,
            "last_modified": today,
        },
        {
            "plu_code": "1007",
            "barcode": "9300601234622",  # Duplicate barcode with 1008
            "description": "Atlantic Salmon Fillet",
            "category": "Seafood",
            "subcategory": "Fish",
            "unit_of_measure": "kg",
            "pack_size": None,
            "supplier_code": "SUP007",
            "status": "active",
            "retail_price": 34.99,
            "cost_price": 18.00,
            "created_date": today,
            "last_modified": today,
        },
        {
            "plu_code": "1008",
            "barcode": "9300601234622",  # Duplicate barcode with 1007
            "description": "Atlantic Salmon Portions",
            "category": "Seafood",
            "subcategory": "Fish",
            "unit_of_measure": "ea",
            "pack_size": None,
            "supplier_code": "SUP007",
            "status": "active",
            "retail_price": 14.99,
            "cost_price": 7.50,
            "created_date": today,
            "last_modified": today,
        },
        {
            "plu_code": "1009",
            "barcode": "9300601234639",
            "description": "Organic Avocado",  # Potential duplicate of 1001
            "category": "Fruit",
            "subcategory": "Avocados",
            "unit_of_measure": "ea",
            "pack_size": None,
            "supplier_code": "SUP001",
            "status": "active",
            "retail_price": 3.00,
            "cost_price": 1.60,
            "created_date": today,
            "last_modified": today,
        },
        {
            "plu_code": "1010",
            "barcode": "INVALID123",  # Invalid barcode format
            "description": "xyz123test",  # Gibberish
            "category": "",  # Missing category
            "subcategory": "",  # Missing subcategory
            "unit_of_measure": "ea",
            "pack_size": None,
            "supplier_code": None,
            "status": "active",
            "retail_price": 0.00,  # Zero price
            "cost_price": 0.00,  # Zero cost
            "created_date": today,
            "last_modified": today,
        },
    ]

    save_plu_records(plu_records, source_id, is_dummy=1)

    # -----------------------------------------------------------------------
    # 3. Generate validation results for each quality issue
    # -----------------------------------------------------------------------
    validations = []

    # PLU 1002 — ALL CAPS description
    validations.append({
        "source_id": source_id,
        "rule_id": "STD-001",
        "layer": "plu",
        "severity": "medium",
        "field": "description",
        "record_key": "PLU-1002",
        "message": "Description is ALL CAPS — should use title case",
        "details": {"plu_code": "1002", "value": "BANANA CAVENDISH"},
    })

    # PLU 1004 — Wrong category (AI-detected)
    validations.append({
        "source_id": source_id,
        "rule_id": "AI-001",
        "layer": "hierarchy",
        "severity": "high",
        "field": "category",
        "record_key": "PLU-1004",
        "message": "Category mismatch: 'Chicken Breast Free Range' classified as Bakery, likely Meat",
        "details": {
            "plu_code": "1004",
            "current_category": "Bakery",
            "suggested_category": "Meat",
            "confidence": 0.95,
        },
    })

    # PLU 1004 — Wrong subcategory
    validations.append({
        "source_id": source_id,
        "rule_id": "AI-002",
        "layer": "hierarchy",
        "severity": "high",
        "field": "subcategory",
        "record_key": "PLU-1004",
        "message": "Subcategory mismatch: 'Chicken Breast' under Bread, likely Poultry",
        "details": {
            "plu_code": "1004",
            "current_subcategory": "Bread",
            "suggested_subcategory": "Poultry",
            "confidence": 0.94,
        },
    })

    # PLU 1005 — Missing description
    validations.append({
        "source_id": source_id,
        "rule_id": "RULE-001",
        "layer": "plu",
        "severity": "critical",
        "field": "description",
        "record_key": "PLU-1005",
        "message": "Missing product description — required field is empty",
        "details": {"plu_code": "1005"},
    })

    # PLU 1006 — Cost > Retail
    validations.append({
        "source_id": source_id,
        "rule_id": "PRICE-001",
        "layer": "pricing",
        "severity": "critical",
        "field": "cost_price",
        "record_key": "PLU-1006",
        "message": "Cost price ($8.20) exceeds retail price ($6.50) — negative margin",
        "details": {
            "plu_code": "1006",
            "retail_price": 6.50,
            "cost_price": 8.20,
            "margin": -26.2,
        },
    })

    # PLU 1007/1008 — Duplicate barcode
    validations.append({
        "source_id": source_id,
        "rule_id": "BAR-001",
        "layer": "barcode",
        "severity": "critical",
        "field": "barcode",
        "record_key": "PLU-1007",
        "message": "Duplicate barcode 9300601234622 shared with PLU 1008",
        "details": {
            "barcode": "9300601234622",
            "plu_codes": ["1007", "1008"],
        },
    })

    validations.append({
        "source_id": source_id,
        "rule_id": "BAR-001",
        "layer": "barcode",
        "severity": "critical",
        "field": "barcode",
        "record_key": "PLU-1008",
        "message": "Duplicate barcode 9300601234622 shared with PLU 1007",
        "details": {
            "barcode": "9300601234622",
            "plu_codes": ["1007", "1008"],
        },
    })

    # PLU 1009 — Potential duplicate of 1001 (AI-detected)
    validations.append({
        "source_id": source_id,
        "rule_id": "AI-003",
        "layer": "plu",
        "severity": "high",
        "field": "description",
        "record_key": "PLU-1009",
        "message": "Potential duplicate: 'Organic Avocado' is very similar to PLU 1001 'Organic Avocado Hass'",
        "details": {
            "plu_code": "1009",
            "similar_plu": "1001",
            "similarity_score": 0.87,
            "matching_fields": ["category", "subcategory", "supplier_code"],
        },
    })

    # PLU 1010 — Invalid barcode format
    validations.append({
        "source_id": source_id,
        "rule_id": "BAR-002",
        "layer": "barcode",
        "severity": "critical",
        "field": "barcode",
        "record_key": "PLU-1010",
        "message": "Invalid barcode format: 'INVALID123' is not a valid EAN-13 or UPC-A",
        "details": {"plu_code": "1010", "barcode": "INVALID123"},
    })

    # PLU 1010 — Gibberish description
    validations.append({
        "source_id": source_id,
        "rule_id": "AI-004",
        "layer": "plu",
        "severity": "high",
        "field": "description",
        "record_key": "PLU-1010",
        "message": "Description appears to be test/gibberish data: 'xyz123test'",
        "details": {"plu_code": "1010", "value": "xyz123test"},
    })

    # PLU 1010 — Missing category
    validations.append({
        "source_id": source_id,
        "rule_id": "RULE-002",
        "layer": "hierarchy",
        "severity": "critical",
        "field": "category",
        "record_key": "PLU-1010",
        "message": "Missing product category — required field is empty",
        "details": {"plu_code": "1010"},
    })

    # PLU 1010 — Missing subcategory
    validations.append({
        "source_id": source_id,
        "rule_id": "RULE-003",
        "layer": "hierarchy",
        "severity": "high",
        "field": "subcategory",
        "record_key": "PLU-1010",
        "message": "Missing product subcategory — required field is empty",
        "details": {"plu_code": "1010"},
    })

    # PLU 1010 — Zero retail price
    validations.append({
        "source_id": source_id,
        "rule_id": "PRICE-002",
        "layer": "pricing",
        "severity": "high",
        "field": "retail_price",
        "record_key": "PLU-1010",
        "message": "Retail price is $0.00 — likely missing or invalid",
        "details": {"plu_code": "1010", "retail_price": 0.00},
    })

    # PLU 1010 — Zero cost price
    validations.append({
        "source_id": source_id,
        "rule_id": "PRICE-003",
        "layer": "pricing",
        "severity": "medium",
        "field": "cost_price",
        "record_key": "PLU-1010",
        "message": "Cost price is $0.00 — likely missing or invalid",
        "details": {"plu_code": "1010", "cost_price": 0.00},
    })

    # PLU 1010 — Missing supplier
    validations.append({
        "source_id": source_id,
        "rule_id": "SUP-001",
        "layer": "supplier",
        "severity": "medium",
        "field": "supplier_code",
        "record_key": "PLU-1010",
        "message": "No supplier code assigned to PLU 1010",
        "details": {"plu_code": "1010"},
    })

    validation_ids = add_validations_bulk(validations)

    # -----------------------------------------------------------------------
    # 4. Generate issues from critical and high severity validations
    # -----------------------------------------------------------------------
    create_issues_from_validations(source_id, min_severity="high")

    # -----------------------------------------------------------------------
    # 5. Seed scan results
    # -----------------------------------------------------------------------
    scan_yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    scan_last_week = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    scan_data = []

    # PLUs 1001-1005: warehouse + POS scans, high success
    for plu_code in ["1001", "1002", "1003", "1004", "1005"]:
        barcode_map = {
            "1001": "9300601234561",
            "1002": "9300601234578",
            "1003": "9300601234585",
            "1004": "9300601234592",
            "1005": "9300601234608",
        }
        barcode = barcode_map[plu_code]

        # Warehouse scan
        scan_data.append({
            "barcode": barcode,
            "plu_code": plu_code,
            "scan_source": "warehouse",
            "last_scan_date": scan_yesterday,
            "scan_count": 250,
            "success_rate": 98.0,
            "manual_key_rate": 1.0,
            "status": "active",
        })
        # POS scan
        scan_data.append({
            "barcode": barcode,
            "plu_code": plu_code,
            "scan_source": "pos",
            "last_scan_date": scan_yesterday,
            "scan_count": 180,
            "success_rate": 95.0,
            "manual_key_rate": 3.0,
            "status": "active",
        })

    # PLUs 1006-1008: POS only, lower success
    for plu_code in ["1006", "1007", "1008"]:
        barcode_map = {
            "1006": "9300601234615",
            "1007": "9300601234622",
            "1008": "9300601234622",
        }
        barcode = barcode_map[plu_code]

        scan_data.append({
            "barcode": barcode,
            "plu_code": plu_code,
            "scan_source": "pos",
            "last_scan_date": scan_last_week,
            "scan_count": 45,
            "success_rate": 90.0,
            "manual_key_rate": 8.0,
            "status": "active",
        })

    # PLU 1009: never scanned
    scan_data.append({
        "barcode": "9300601234639",
        "plu_code": "1009",
        "scan_source": "pos",
        "last_scan_date": None,
        "scan_count": 0,
        "success_rate": None,
        "manual_key_rate": None,
        "status": "never_scanned",
    })

    # PLU 1010: POS scan failing
    scan_data.append({
        "barcode": "INVALID123",
        "plu_code": "1010",
        "scan_source": "pos",
        "last_scan_date": scan_last_week,
        "scan_count": 15,
        "success_rate": 20.0,
        "manual_key_rate": 60.0,
        "status": "failing",
    })

    save_scan_results(scan_data)

    # -----------------------------------------------------------------------
    # 6. Compute and save domain scores for today
    # -----------------------------------------------------------------------
    # PLU domain: 10 records, issues on 1002 (caps), 1005 (missing desc),
    #             1009 (duplicate), 1010 (gibberish) = 4 failures → 6/10 = 60
    #             But with weighted severity: ~80
    # Barcode domain: 10 records, issues on 1007+1008 (dup), 1010 (invalid) = 3 failures
    # Pricing domain: 10 records, issues on 1006 (cost>retail), 1010 (zero) = 2 failures
    # Hierarchy domain: 10 records, issues on 1004 (wrong cat+sub), 1010 (missing) = 2 records, 4 checks failed
    # Supplier domain: 10 records, 1010 missing = 1 failure
    # Overall: weighted average

    today_scores = {
        "plu": {
            "total": 10,
            "passed": 6,
            "failed": 4,
            "score": 80.0,
            "layer_scores": {
                "completeness": 80.0,
                "standards": 90.0,
                "ai_anomaly": 70.0,
            },
        },
        "barcode": {
            "total": 10,
            "passed": 7,
            "failed": 3,
            "score": 70.0,
            "layer_scores": {
                "format_valid": 90.0,
                "uniqueness": 70.0,
                "scan_success": 50.0,
            },
        },
        "pricing": {
            "total": 10,
            "passed": 8,
            "failed": 2,
            "score": 80.0,
            "layer_scores": {
                "margin_check": 90.0,
                "zero_price": 90.0,
                "cost_vs_retail": 70.0,
            },
        },
        "hierarchy": {
            "total": 10,
            "passed": 7,
            "failed": 3,
            "score": 70.0,
            "layer_scores": {
                "category_valid": 80.0,
                "subcategory_valid": 80.0,
                "ai_classification": 50.0,
            },
        },
        "supplier": {
            "total": 10,
            "passed": 9,
            "failed": 1,
            "score": 90.0,
            "layer_scores": {
                "supplier_assigned": 90.0,
                "supplier_active": 100.0,
            },
        },
        "overall": {
            "total": 50,
            "passed": 37,
            "failed": 13,
            "score": 78.0,
            "layer_scores": {
                "plu": 80.0,
                "barcode": 70.0,
                "pricing": 80.0,
                "hierarchy": 70.0,
                "supplier": 90.0,
            },
        },
    }

    save_scores(today, today_scores)

    # -----------------------------------------------------------------------
    # 7. Generate 14-day score history with slight improvement trend
    # -----------------------------------------------------------------------
    # Start ~14 days ago with lower scores, improve by 1-2 points per day
    import random
    random.seed(42)  # Deterministic for reproducibility

    base_scores = {
        "plu": 66.0,
        "barcode": 56.0,
        "pricing": 66.0,
        "hierarchy": 56.0,
        "supplier": 76.0,
        "overall": 64.0,
    }

    for day_offset in range(14, 0, -1):
        day_date = (datetime.utcnow() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        progress = (14 - day_offset) / 14.0  # 0.0 to ~0.93

        day_scores = {}
        for domain, base in base_scores.items():
            # Trend up toward today's score with slight random noise
            target = today_scores[domain]["score"]
            trending = base + (target - base) * progress
            noise = random.uniform(-1.5, 1.5)
            score = round(min(100.0, max(0.0, trending + noise)), 1)

            if domain == "overall":
                day_scores[domain] = {
                    "total": 50,
                    "passed": int(50 * score / 100),
                    "failed": 50 - int(50 * score / 100),
                    "score": score,
                    "layer_scores": {
                        "plu": day_scores.get("plu", {}).get("score", score),
                        "barcode": day_scores.get("barcode", {}).get("score", score),
                        "pricing": day_scores.get("pricing", {}).get("score", score),
                        "hierarchy": day_scores.get("hierarchy", {}).get("score", score),
                        "supplier": day_scores.get("supplier", {}).get("score", score),
                    },
                }
            else:
                total = 10
                passed = int(total * score / 100)
                day_scores[domain] = {
                    "total": total,
                    "passed": passed,
                    "failed": total - passed,
                    "score": score,
                    "layer_scores": today_scores[domain].get("layer_scores", {}),
                }

        save_scores(day_date, day_scores)

    logger.info("Seeded MDHE dummy data: 10 PLUs, %d validations, scan results, 15 days of scores", len(validations))
