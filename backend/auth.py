"""
Harris Farm Hub — Authentication Module
Handles user authentication, session management, and auth auditing.
All passwords hashed with bcrypt. Sessions stored in SQLite.
"""

import os
import sqlite3
import secrets
import logging
from datetime import datetime, timedelta
from pathlib import Path

import bcrypt
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger("hub_auth")

AUTH_DB = os.path.join(os.path.dirname(__file__), "..", "data", "auth.db")


def _get_conn():
    """Get SQLite connection to auth database."""
    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def is_auth_enabled():
    """Check if authentication is enabled via AUTH_ENABLED env var."""
    return os.getenv("AUTH_ENABLED", "true").lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(password):
    """Hash a password using bcrypt with auto-generated salt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, hashed):
    """Verify a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_auth_db(db_path=None):
    """
    Create auth tables if they don't exist.
    Seed admin user and site password from env vars on first run.
    """
    if db_path:
        global AUTH_DB
        AUTH_DB = db_path

    Path(AUTH_DB).parent.mkdir(parents=True, exist_ok=True)
    conn = _get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS auth_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            ip_address TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")

    c.execute("""
        CREATE TABLE IF NOT EXISTS auth_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            action TEXT NOT NULL,
            email TEXT DEFAULT '',
            ip_address TEXT DEFAULT '',
            details TEXT DEFAULT ''
        )
    """)

    conn.commit()

    # Seed site password if not set
    site_pw = c.execute(
        "SELECT value FROM auth_config WHERE key = 'site_password_hash'"
    ).fetchone()
    if not site_pw:
        env_site_pw = os.getenv("AUTH_SITE_PASSWORD", "")
        if env_site_pw:
            c.execute(
                "INSERT INTO auth_config (key, value) VALUES (?, ?)",
                ("site_password_hash", hash_password(env_site_pw)),
            )
        c.execute(
            "INSERT OR IGNORE INTO auth_config (key, value) VALUES (?, ?)",
            ("require_site_password", "true" if env_site_pw else "false"),
        )

    # Seed session timeout
    timeout_row = c.execute(
        "SELECT value FROM auth_config WHERE key = 'session_timeout_hours'"
    ).fetchone()
    if not timeout_row:
        c.execute(
            "INSERT INTO auth_config (key, value) VALUES (?, ?)",
            ("session_timeout_hours", os.getenv("AUTH_SESSION_TIMEOUT", "24")),
        )

    # Seed admin user if no users exist
    user_count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count == 0:
        admin_email = os.getenv("AUTH_ADMIN_EMAIL", "")
        admin_pw = os.getenv("AUTH_ADMIN_PASSWORD", "")
        if admin_email and admin_pw:
            c.execute(
                "INSERT INTO users (email, name, password_hash, role) VALUES (?, ?, ?, ?)",
                (admin_email, "Admin", hash_password(admin_pw), "admin"),
            )
            log_auth_event("admin_seeded", admin_email, "", "Initial admin created from env", conn=conn)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Site password
# ---------------------------------------------------------------------------

def check_site_password(password):
    """Verify site-wide access password."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT value FROM auth_config WHERE key = 'site_password_hash'"
    ).fetchone()
    conn.close()
    if not row:
        return True  # No site password set = open access
    return verify_password(password, row["value"])


def is_site_password_required():
    """Check if site password is required."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT value FROM auth_config WHERE key = 'require_site_password'"
    ).fetchone()
    conn.close()
    if not row:
        return False
    return row["value"].lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def create_user(email, name, password, role="user"):
    """Create a new user. Returns user dict (without password_hash)."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO users (email, name, password_hash, role) VALUES (?, ?, ?, ?)",
            (email, name, hash_password(password), role),
        )
        conn.commit()
        user = conn.execute(
            "SELECT id, email, name, role, active, created_at FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        return dict(user) if user else None
    except sqlite3.IntegrityError:
        raise ValueError(f"User with email {email} already exists")
    finally:
        conn.close()


def authenticate_user(email, password):
    """Authenticate user by email and password. Returns user dict or None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, email, name, password_hash, role, active FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    conn.close()

    if not row:
        return None
    if not row["active"]:
        return None
    if not verify_password(password, row["password_hash"]):
        return None

    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
    }


def list_users():
    """List all users (without password hashes)."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, email, name, role, active, created_at, updated_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_user(user_id, **kwargs):
    """
    Update user fields. Supported: name, role, active, password.
    Password is hashed before storage.
    """
    conn = _get_conn()
    allowed = {"name", "role", "active"}

    updates = []
    values = []
    for key, val in kwargs.items():
        if key == "password":
            updates.append("password_hash = ?")
            values.append(hash_password(val))
        elif key in allowed:
            updates.append(f"{key} = ?")
            values.append(val)

    if not updates:
        conn.close()
        return

    updates.append("updated_at = datetime('now')")
    values.append(user_id)

    conn.execute(
        f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
        values,
    )
    conn.commit()
    conn.close()


def get_user_by_id(user_id):
    """Get user by ID (without password_hash)."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, email, name, role, active, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def _get_session_timeout():
    """Get session timeout in hours from auth_config."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT value FROM auth_config WHERE key = 'session_timeout_hours'"
    ).fetchone()
    conn.close()
    try:
        return int(row["value"]) if row else 24
    except (ValueError, TypeError):
        return 24


def create_session(user_id, ip_address=""):
    """Create a new session token for a user. Returns token string."""
    token = secrets.token_urlsafe(32)
    timeout = _get_session_timeout()
    expires = (datetime.utcnow() + timedelta(hours=timeout)).strftime("%Y-%m-%d %H:%M:%S")

    conn = _get_conn()
    conn.execute(
        "INSERT INTO sessions (token, user_id, expires_at, ip_address) VALUES (?, ?, ?, ?)",
        (token, user_id, expires, ip_address),
    )
    conn.commit()
    conn.close()
    return token


def verify_session(token):
    """
    Verify a session token. Returns user dict if valid, None if invalid/expired.
    """
    if not token:
        return None

    conn = _get_conn()
    row = conn.execute(
        """
        SELECT s.id, s.user_id, s.expires_at, u.email, u.name, u.role, u.active
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
        """,
        (token,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    # Check expiry
    expires = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
    if datetime.utcnow() > expires:
        revoke_session(token)
        return None

    # Check user active
    if not row["active"]:
        return None

    return {
        "id": row["user_id"],
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
    }


def revoke_session(token):
    """Revoke a specific session token."""
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def revoke_all_sessions(user_id):
    """Revoke all sessions for a user."""
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def list_active_sessions():
    """List all non-expired sessions with user info."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT s.id, s.token, s.user_id, s.created_at, s.expires_at,
               s.ip_address, u.email, u.name, u.role
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.expires_at > ?
        ORDER BY s.created_at DESC
        """,
        (now,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def cleanup_expired_sessions():
    """Delete all expired sessions."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_conn()
    result = conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
    count = result.rowcount
    conn.commit()
    conn.close()
    if count > 0:
        logger.info("Cleaned up %d expired sessions", count)
    return count


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def log_auth_event(action, email="", ip_address="", details="", conn=None):
    """Log an authentication event to the audit table."""
    close = False
    if conn is None:
        conn = _get_conn()
        close = True

    conn.execute(
        "INSERT INTO auth_audit (action, email, ip_address, details) VALUES (?, ?, ?, ?)",
        (action, email, ip_address, details),
    )
    conn.commit()

    if close:
        conn.close()


def get_auth_audit(limit=100):
    """Get recent auth audit entries."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, timestamp, action, email, ip_address, details "
        "FROM auth_audit ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Admin settings
# ---------------------------------------------------------------------------

def update_site_password(new_password):
    """Update the site-wide access password."""
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO auth_config (key, value) VALUES (?, ?)",
        ("site_password_hash", hash_password(new_password)),
    )
    conn.commit()
    conn.close()


def update_session_timeout(hours):
    """Update the session timeout (hours)."""
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO auth_config (key, value) VALUES (?, ?)",
        ("session_timeout_hours", str(int(hours))),
    )
    conn.commit()
    conn.close()


def update_require_site_password(required):
    """Enable or disable site password requirement."""
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO auth_config (key, value) VALUES (?, ?)",
        ("require_site_password", "true" if required else "false"),
    )
    conn.commit()
    conn.close()
