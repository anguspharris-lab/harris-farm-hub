"""
Harris Farm Hub — Analytics Engine
Page-view tracking and adoption metrics.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional


def init_analytics_tables(conn):
    """Create analytics tables. Call from init_hub_database()."""
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS page_views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        user_email TEXT NOT NULL DEFAULT '',
        page_slug TEXT NOT NULL,
        user_role TEXT NOT NULL DEFAULT 'user',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pv_user ON page_views(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pv_slug ON page_views(page_slug)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pv_date ON page_views(created_at)")

    conn.commit()


def log_page_view(db_path, user_id, user_email, page_slug, user_role="user"):
    """Log a single page view. Lightweight — called on every page load."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO page_views (user_id, user_email, page_slug, user_role) "
        "VALUES (?, ?, ?, ?)",
        (user_id, user_email, page_slug, user_role),
    )
    conn.commit()
    conn.close()


def get_analytics_summary(db_path, days=30):
    """
    Aggregate analytics for the last N days.
    Returns: unique_users, total_views, top_pages, views_by_day, avg_pages_per_user.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    # Unique users
    unique_users = conn.execute(
        "SELECT COUNT(DISTINCT user_id) FROM page_views WHERE created_at >= ?",
        (cutoff,),
    ).fetchone()[0]

    # Total views
    total_views = conn.execute(
        "SELECT COUNT(*) FROM page_views WHERE created_at >= ?",
        (cutoff,),
    ).fetchone()[0]

    # Top pages
    rows = conn.execute(
        "SELECT page_slug, COUNT(*) as views, COUNT(DISTINCT user_id) as users "
        "FROM page_views WHERE created_at >= ? "
        "GROUP BY page_slug ORDER BY views DESC LIMIT 15",
        (cutoff,),
    ).fetchall()
    top_pages = [{"slug": r["page_slug"], "views": r["views"], "users": r["users"]} for r in rows]

    # Views by day
    rows = conn.execute(
        "SELECT date(created_at) as day, COUNT(*) as views, "
        "COUNT(DISTINCT user_id) as users "
        "FROM page_views WHERE created_at >= ? "
        "GROUP BY date(created_at) ORDER BY day",
        (cutoff,),
    ).fetchall()
    views_by_day = [{"day": r["day"], "views": r["views"], "users": r["users"]} for r in rows]

    # Avg pages per user
    avg_pages = round(total_views / unique_users, 1) if unique_users > 0 else 0

    conn.close()
    return {
        "unique_users": unique_users,
        "total_views": total_views,
        "avg_pages_per_user": avg_pages,
        "top_pages": top_pages,
        "views_by_day": views_by_day,
        "days": days,
    }


def get_analytics_by_role(db_path, days=30):
    """Usage broken down by hub_role."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    rows = conn.execute(
        "SELECT user_role, COUNT(*) as views, COUNT(DISTINCT user_id) as users "
        "FROM page_views WHERE created_at >= ? "
        "GROUP BY user_role ORDER BY views DESC",
        (cutoff,),
    ).fetchall()
    conn.close()
    return [{"role": r["user_role"], "views": r["views"], "users": r["users"]} for r in rows]


def get_user_activity(db_path, days=30):
    """Per-user page counts and last active timestamp."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    rows = conn.execute(
        "SELECT user_id, user_email, user_role, "
        "COUNT(*) as page_views, "
        "COUNT(DISTINCT page_slug) as unique_pages, "
        "MAX(created_at) as last_active "
        "FROM page_views WHERE created_at >= ? "
        "GROUP BY user_id ORDER BY page_views DESC",
        (cutoff,),
    ).fetchall()
    conn.close()
    return [
        {
            "user_id": r["user_id"],
            "email": r["user_email"],
            "role": r["user_role"],
            "page_views": r["page_views"],
            "unique_pages": r["unique_pages"],
            "last_active": r["last_active"],
        }
        for r in rows
    ]
