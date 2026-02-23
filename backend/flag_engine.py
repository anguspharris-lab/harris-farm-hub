"""
Harris Farm Hub — Flag Engine
Universal human-in-the-loop feedback system.
Users flag issues on any Hub page; system triages and tracks resolution.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Flag categories and severity weights
# ---------------------------------------------------------------------------

FLAG_CATEGORIES = [
    {"key": "data_wrong", "label": "Data looks wrong", "severity": 5},
    {"key": "wrong_answer", "label": "Wrong answer", "severity": 4},
    {"key": "outdated", "label": "Outdated information", "severity": 3},
    {"key": "confusing", "label": "Confusing UX", "severity": 2},
    {"key": "other", "label": "Other", "severity": 1},
]

IMPACT_WEIGHTS = {
    "sales": 5, "profitability": 5, "revenue-bridge": 5,
    "store-ops": 4, "buying-hub": 4, "plu-intel": 4,
    "customers": 4, "product-intel": 4,
    "the-paddock": 3, "skills-academy": 2,
    "hub-assistant": 3, "prompt-builder": 3,
}
DEFAULT_IMPACT = 2


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_flag_tables(conn):
    """Create flag tables. Safe to call repeatedly."""
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS hub_flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        page_slug TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        element_id TEXT,
        priority_score REAL,
        status TEXT DEFAULT 'open',
        resolution_notes TEXT,
        resolved_by TEXT,
        resolved_at TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_hf_page ON hub_flags(page_slug)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_hf_status ON hub_flags(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_hf_user ON hub_flags(user_id)")

    conn.commit()


# ---------------------------------------------------------------------------
# Flag submission
# ---------------------------------------------------------------------------

def submit_flag(db_path, user_id, page_slug, category, description="",
                element_id=None):
    """Submit a new flag. Returns flag ID."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """INSERT INTO hub_flags
           (user_id, page_slug, category, description, element_id)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, page_slug, category, description or "", element_id),
    )
    flag_id = c.lastrowid
    conn.commit()

    # Calculate and store priority
    priority = calculate_priority(db_path, flag_id)
    conn.execute(
        "UPDATE hub_flags SET priority_score = ? WHERE id = ?",
        (priority, flag_id),
    )
    conn.commit()
    conn.close()

    return {"flag_id": flag_id, "priority": priority}


# ---------------------------------------------------------------------------
# Priority scoring
# ---------------------------------------------------------------------------

def calculate_priority(db_path, flag_id):
    """Calculate priority score = Volume x Severity x Recency x Impact."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    flag = conn.execute(
        "SELECT * FROM hub_flags WHERE id = ?", (flag_id,)
    ).fetchone()
    if not flag:
        conn.close()
        return 0.0

    page_slug = flag["page_slug"]
    category = flag["category"]
    element_id = flag["element_id"]

    # Volume: how many unique users flagged the same page+element
    if element_id:
        volume_count = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM hub_flags "
            "WHERE page_slug = ? AND element_id = ? AND status = 'open'",
            (page_slug, element_id),
        ).fetchone()[0]
    else:
        volume_count = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM hub_flags "
            "WHERE page_slug = ? AND category = ? AND status = 'open'",
            (page_slug, category),
        ).fetchone()[0]
    volume = max(1, volume_count)

    # Severity from category
    severity = 1
    for cat in FLAG_CATEGORIES:
        if cat["key"] == category:
            severity = cat["severity"]
            break

    # Recency
    created = flag["created_at"] or ""
    recency = 1
    try:
        created_dt = datetime.fromisoformat(created)
        age_days = (datetime.utcnow() - created_dt).days
        if age_days == 0:
            recency = 3
        elif age_days <= 7:
            recency = 2
        else:
            recency = 1
    except (ValueError, TypeError):
        pass

    # Impact from page type
    impact = IMPACT_WEIGHTS.get(page_slug, DEFAULT_IMPACT)

    conn.close()

    return round(volume * severity * recency * impact, 1)


# ---------------------------------------------------------------------------
# Admin queries
# ---------------------------------------------------------------------------

def get_flags(db_path, status=None, page_slug=None, limit=100):
    """Get flags, optionally filtered by status and page."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM hub_flags WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if page_slug:
        query += " AND page_slug = ?"
        params.append(page_slug)

    query += " ORDER BY priority_score DESC, created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_flag(db_path, flag_id, resolution_notes, resolved_by):
    """Resolve a flag."""
    conn = sqlite3.connect(db_path)
    now = datetime.utcnow().isoformat()
    conn.execute(
        """UPDATE hub_flags
           SET status = 'resolved', resolution_notes = ?,
               resolved_by = ?, resolved_at = ?
           WHERE id = ?""",
        (resolution_notes, resolved_by, now, flag_id),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "flag_id": flag_id}


def dismiss_flag(db_path, flag_id, resolved_by):
    """Dismiss a flag (not a real issue)."""
    conn = sqlite3.connect(db_path)
    now = datetime.utcnow().isoformat()
    conn.execute(
        """UPDATE hub_flags
           SET status = 'dismissed', resolved_by = ?, resolved_at = ?
           WHERE id = ?""",
        (resolved_by, now, flag_id),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "flag_id": flag_id}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def get_flag_metrics(db_path):
    """Get flag system metrics."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Counts by status
    status_counts = {}
    for row in conn.execute(
        "SELECT status, COUNT(*) as cnt FROM hub_flags GROUP BY status"
    ).fetchall():
        status_counts[row["status"]] = row["cnt"]

    # Top flagged pages
    top_pages = conn.execute(
        "SELECT page_slug, COUNT(*) as cnt FROM hub_flags "
        "WHERE status = 'open' GROUP BY page_slug "
        "ORDER BY cnt DESC LIMIT 10"
    ).fetchall()

    # Flags by category
    by_category = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM hub_flags "
        "GROUP BY category ORDER BY cnt DESC"
    ).fetchall()

    # Weekly trend (last 8 weeks)
    weekly_trend = conn.execute(
        "SELECT strftime('%Y-W%W', created_at) as week, COUNT(*) as cnt "
        "FROM hub_flags "
        "WHERE created_at >= datetime('now', '-56 days') "
        "GROUP BY week ORDER BY week"
    ).fetchall()

    # Resolution stats
    resolved = conn.execute(
        "SELECT COUNT(*) as total, "
        "AVG(JULIANDAY(resolved_at) - JULIANDAY(created_at)) as avg_days "
        "FROM hub_flags WHERE status IN ('resolved', 'dismissed') "
        "AND resolved_at IS NOT NULL"
    ).fetchone()

    conn.close()

    return {
        "status_counts": status_counts,
        "top_flagged_pages": [dict(r) for r in top_pages],
        "by_category": [dict(r) for r in by_category],
        "weekly_trend": [dict(r) for r in weekly_trend],
        "total_resolved": resolved["total"] if resolved else 0,
        "avg_resolution_days": round(resolved["avg_days"] or 0, 1) if resolved else 0,
    }
