"""
AI Adoption Tracker — SQLite Cache Layer
Stores normalised usage data from all AI platforms.
Serves from cache on page load; background refresh every N hours.
"""

import sqlite3
import datetime
from pathlib import Path
from typing import Optional

import yaml

_DIR = Path(__file__).resolve().parent
_CFG = yaml.safe_load((_DIR / "config.yaml").read_text())
_DB_PATH = str(Path(__file__).resolve().parent.parent.parent / _CFG["cache_db"])


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_cache_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ai_users (
            email TEXT NOT NULL,
            name TEXT,
            platform TEXT NOT NULL,
            role TEXT,
            last_synced TEXT NOT NULL,
            PRIMARY KEY (email, platform)
        );

        CREATE TABLE IF NOT EXISTS ai_usage (
            email TEXT NOT NULL,
            platform TEXT NOT NULL,
            date TEXT NOT NULL,
            message_count INTEGER DEFAULT 0,
            tokens INTEGER DEFAULT 0,
            model TEXT,
            last_synced TEXT NOT NULL,
            PRIMARY KEY (email, platform, date, model)
        );

        CREATE TABLE IF NOT EXISTS ai_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            sync_time TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            users_synced INTEGER DEFAULT 0,
            records_synced INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()


def last_sync_time(platform: str) -> Optional[str]:
    """Return ISO timestamp of last successful sync for a platform."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT sync_time FROM ai_sync_log WHERE platform = ? AND status = 'success' "
        "ORDER BY sync_time DESC LIMIT 1",
        (platform,),
    ).fetchone()
    conn.close()
    return row["sync_time"] if row else None


def needs_refresh(platform: str) -> bool:
    """True if platform hasn't been synced within the configured interval."""
    last = last_sync_time(platform)
    if not last:
        return True
    interval = _CFG.get("refresh_interval_hours", 6)
    last_dt = datetime.datetime.fromisoformat(last)
    return datetime.datetime.now() - last_dt > datetime.timedelta(hours=interval)


def log_sync(platform: str, status: str, message: str = "",
             users_synced: int = 0, records_synced: int = 0):
    """Record a sync attempt."""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO ai_sync_log (platform, sync_time, status, message, users_synced, records_synced) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (platform, datetime.datetime.now().isoformat(), status, message,
         users_synced, records_synced),
    )
    conn.commit()
    conn.close()


def upsert_users(platform: str, users: list[dict]):
    """Upsert user records. Each dict: {email, name, role?}."""
    conn = _get_conn()
    now = datetime.datetime.now().isoformat()
    for u in users:
        conn.execute(
            "INSERT INTO ai_users (email, name, platform, role, last_synced) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(email, platform) DO UPDATE SET name=?, role=?, last_synced=?",
            (u["email"], u.get("name", ""), platform, u.get("role", ""),
             now, u.get("name", ""), u.get("role", ""), now),
        )
    conn.commit()
    conn.close()


def upsert_usage(platform: str, records: list[dict]):
    """Upsert usage records. Each dict: {email, date, message_count, tokens, model}."""
    conn = _get_conn()
    now = datetime.datetime.now().isoformat()
    for r in records:
        conn.execute(
            "INSERT INTO ai_usage (email, platform, date, message_count, tokens, model, last_synced) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(email, platform, date, model) DO UPDATE SET "
            "message_count=?, tokens=?, last_synced=?",
            (r["email"], platform, r["date"], r.get("message_count", 0),
             r.get("tokens", 0), r.get("model", "unknown"), now,
             r.get("message_count", 0), r.get("tokens", 0), now),
        )
    conn.commit()
    conn.close()


# ── Read queries ─────────────────────────────────────────────────────────────

def get_active_users(days: int = 30) -> list[dict]:
    """Unique users with activity in the last N days, joined across platforms."""
    conn = _get_conn()
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    rows = conn.execute("""
        SELECT u.email, u.name,
               COALESCE(SUM(CASE WHEN a.platform = 'anthropic' THEN a.message_count END), 0) AS claude_messages,
               COALESCE(SUM(CASE WHEN a.platform = 'openai' THEN a.message_count END), 0) AS chatgpt_messages,
               COALESCE(SUM(a.message_count), 0) AS total_messages,
               MAX(a.date) AS last_active
        FROM ai_users u
        LEFT JOIN ai_usage a ON u.email = a.email AND a.date >= ?
        GROUP BY u.email, u.name
        HAVING total_messages > 0
        ORDER BY total_messages DESC
    """, (cutoff,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_total_messages(days: int = 30) -> int:
    conn = _get_conn()
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT COALESCE(SUM(message_count), 0) FROM ai_usage WHERE date >= ?",
        (cutoff,),
    ).fetchone()
    conn.close()
    return row[0]


def get_platform_split(days: int = 30) -> dict:
    """Return {platform_label: message_count} for last N days."""
    conn = _get_conn()
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT platform, SUM(message_count) AS total FROM ai_usage "
        "WHERE date >= ? GROUP BY platform",
        (cutoff,),
    ).fetchall()
    conn.close()
    labels = {p["env_var"].split("_")[0].lower(): p["label"]
              for _, p in _CFG.get("platforms", {}).items()}
    labels.update({"openai": "ChatGPT", "anthropic": "Claude"})
    return {labels.get(r["platform"], r["platform"]): r["total"] for r in rows}


def get_weekly_active_users(weeks: int = 12) -> list[dict]:
    """Weekly active user counts for sparkline."""
    conn = _get_conn()
    cutoff = (datetime.datetime.now() - datetime.timedelta(weeks=weeks)).strftime("%Y-%m-%d")
    rows = conn.execute("""
        SELECT strftime('%Y-W%W', date) AS week,
               COUNT(DISTINCT email) AS active_users
        FROM ai_usage
        WHERE date >= ? AND message_count > 0
        GROUP BY week
        ORDER BY week
    """, (cutoff,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_usage_csv() -> list[dict]:
    """All usage records for CSV export."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT u.email, u.name, a.platform, a.date, a.message_count, a.tokens, a.model
        FROM ai_usage a
        LEFT JOIN ai_users u ON a.email = u.email AND a.platform = u.platform
        ORDER BY a.date DESC, u.email
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
