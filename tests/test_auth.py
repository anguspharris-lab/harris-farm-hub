"""
Tests for the authentication system.
Covers: auth module (password hashing, user management, sessions, audit),
        API endpoints, and auth gate.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


class TestPasswordHashing(unittest.TestCase):
    """Test bcrypt password hashing and verification."""

    def setUp(self):
        import auth
        self.auth = auth
        # Use temp DB for isolation
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test_auth.db")
        self.auth.AUTH_DB = self.db_path
        self.auth.init_auth_db(self.db_path)

    def test_hash_and_verify_password(self):
        """bcrypt hash round-trip succeeds."""
        h = self.auth.hash_password("mypassword123")
        self.assertTrue(self.auth.verify_password("mypassword123", h))

    def test_verify_wrong_password(self):
        """Wrong password returns False."""
        h = self.auth.hash_password("correct")
        self.assertFalse(self.auth.verify_password("wrong", h))

    def test_hash_is_bcrypt_format(self):
        """Hash starts with $2b$ (bcrypt marker)."""
        h = self.auth.hash_password("test")
        self.assertTrue(h.startswith("$2b$"))

    def test_different_hashes_for_same_password(self):
        """Each hash uses a unique salt."""
        h1 = self.auth.hash_password("same")
        h2 = self.auth.hash_password("same")
        self.assertNotEqual(h1, h2)
        # But both verify
        self.assertTrue(self.auth.verify_password("same", h1))
        self.assertTrue(self.auth.verify_password("same", h2))

    def test_verify_invalid_hash(self):
        """Invalid hash string returns False (no crash)."""
        self.assertFalse(self.auth.verify_password("test", "not-a-hash"))


class TestAuthDatabase(unittest.TestCase):
    """Test auth database initialization and configuration."""

    def setUp(self):
        import auth
        self.auth = auth
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test_auth.db")

    @patch.dict(os.environ, {
        "AUTH_ADMIN_EMAIL": "admin@test.com",
        "AUTH_ADMIN_PASSWORD": "AdminPass123",
        "AUTH_SITE_PASSWORD": "sitepass",
        "AUTH_SESSION_TIMEOUT": "12",
    })
    def test_init_creates_all_tables(self):
        """init_auth_db creates all 4 expected tables."""
        self.auth.init_auth_db(self.db_path)
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite%'"
        ).fetchall()]
        conn.close()
        for t in ["auth_config", "users", "sessions", "auth_audit"]:
            self.assertIn(t, tables)

    @patch.dict(os.environ, {
        "AUTH_ADMIN_EMAIL": "admin@test.com",
        "AUTH_ADMIN_PASSWORD": "AdminPass123",
        "AUTH_SITE_PASSWORD": "sitepass",
    })
    def test_init_creates_admin_user(self):
        """First init seeds admin user from env vars."""
        self.auth.init_auth_db(self.db_path)
        users = self.auth.list_users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["email"], "admin@test.com")
        self.assertEqual(users[0]["role"], "admin")

    @patch.dict(os.environ, {
        "AUTH_ADMIN_EMAIL": "admin@test.com",
        "AUTH_ADMIN_PASSWORD": "AdminPass123",
        "AUTH_SITE_PASSWORD": "sitepass",
    })
    def test_site_password_seeded(self):
        """Site password is hashed and stored in auth_config."""
        self.auth.init_auth_db(self.db_path)
        self.assertTrue(self.auth.check_site_password("sitepass"))
        self.assertFalse(self.auth.check_site_password("wrong"))

    @patch.dict(os.environ, {
        "AUTH_ADMIN_EMAIL": "admin@test.com",
        "AUTH_ADMIN_PASSWORD": "AdminPass123",
        "AUTH_SITE_PASSWORD": "",
    })
    def test_no_site_password_allows_access(self):
        """When no site password is set, check returns True."""
        self.auth.init_auth_db(self.db_path)
        self.assertTrue(self.auth.check_site_password("anything"))


class TestUserManagement(unittest.TestCase):
    """Test user CRUD operations."""

    def setUp(self):
        import auth
        self.auth = auth
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test_auth.db")
        with patch.dict(os.environ, {
            "AUTH_ADMIN_EMAIL": "",
            "AUTH_ADMIN_PASSWORD": "",
            "AUTH_SITE_PASSWORD": "",
        }):
            self.auth.init_auth_db(self.db_path)

    def test_create_user(self):
        """Create user returns dict with expected fields."""
        user = self.auth.create_user("test@test.com", "Test User", "pass123")
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "test@test.com")
        self.assertEqual(user["name"], "Test User")
        self.assertEqual(user["role"], "user")

    def test_create_duplicate_email(self):
        """Duplicate email raises ValueError."""
        self.auth.create_user("dup@test.com", "First", "pass1")
        with self.assertRaises(ValueError):
            self.auth.create_user("dup@test.com", "Second", "pass2")

    def test_authenticate_valid(self):
        """Valid credentials return user dict."""
        self.auth.create_user("auth@test.com", "Auth User", "correct")
        result = self.auth.authenticate_user("auth@test.com", "correct")
        self.assertIsNotNone(result)
        self.assertEqual(result["email"], "auth@test.com")

    def test_authenticate_wrong_password(self):
        """Wrong password returns None."""
        self.auth.create_user("auth2@test.com", "Auth2", "right")
        self.assertIsNone(self.auth.authenticate_user("auth2@test.com", "wrong"))

    def test_authenticate_nonexistent(self):
        """Non-existent email returns None."""
        self.assertIsNone(self.auth.authenticate_user("nobody@test.com", "pass"))

    def test_authenticate_inactive_user(self):
        """Inactive user returns None even with correct password."""
        user = self.auth.create_user("inactive@test.com", "Inactive", "pass")
        self.auth.update_user(user["id"], active=0)
        self.assertIsNone(self.auth.authenticate_user("inactive@test.com", "pass"))

    def test_list_users_no_password_hashes(self):
        """list_users() does not expose password_hash."""
        self.auth.create_user("safe@test.com", "Safe", "secret")
        users = self.auth.list_users()
        for u in users:
            self.assertNotIn("password_hash", u)

    def test_update_user_password(self):
        """Updating password re-hashes with bcrypt."""
        user = self.auth.create_user("upd@test.com", "Update", "oldpass")
        self.auth.update_user(user["id"], password="newpass")
        # Old password fails
        self.assertIsNone(self.auth.authenticate_user("upd@test.com", "oldpass"))
        # New password works
        self.assertIsNotNone(self.auth.authenticate_user("upd@test.com", "newpass"))

    def test_update_user_role(self):
        """Role can be changed."""
        user = self.auth.create_user("role@test.com", "Role", "pass")
        self.assertEqual(user["role"], "user")
        self.auth.update_user(user["id"], role="admin")
        updated = self.auth.get_user_by_id(user["id"])
        self.assertEqual(updated["role"], "admin")

    def test_create_admin_user(self):
        """Can create user with admin role."""
        user = self.auth.create_user("admin@test.com", "Admin", "pass", role="admin")
        self.assertEqual(user["role"], "admin")


class TestSessionManagement(unittest.TestCase):
    """Test session creation, validation, and revocation."""

    def setUp(self):
        import auth
        self.auth = auth
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test_auth.db")
        with patch.dict(os.environ, {
            "AUTH_ADMIN_EMAIL": "",
            "AUTH_ADMIN_PASSWORD": "",
            "AUTH_SITE_PASSWORD": "",
            "AUTH_SESSION_TIMEOUT": "24",
        }):
            self.auth.init_auth_db(self.db_path)
        self.user = self.auth.create_user("session@test.com", "Session User", "pass")

    def test_create_session(self):
        """create_session returns a non-empty token string."""
        token = self.auth.create_session(self.user["id"], "127.0.0.1")
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)

    def test_verify_valid_session(self):
        """Valid session token returns user dict."""
        token = self.auth.create_session(self.user["id"])
        result = self.auth.verify_session(token)
        self.assertIsNotNone(result)
        self.assertEqual(result["email"], "session@test.com")

    def test_verify_nonexistent_session(self):
        """Non-existent token returns None."""
        self.assertIsNone(self.auth.verify_session("bogus-token"))

    def test_verify_none_token(self):
        """None token returns None."""
        self.assertIsNone(self.auth.verify_session(None))

    def test_verify_empty_token(self):
        """Empty string token returns None."""
        self.assertIsNone(self.auth.verify_session(""))

    def test_verify_expired_session(self):
        """Expired session returns None."""
        token = self.auth.create_session(self.user["id"])
        # Manually expire the session
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        past = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("UPDATE sessions SET expires_at = ? WHERE token = ?", (past, token))
        conn.commit()
        conn.close()
        self.assertIsNone(self.auth.verify_session(token))

    def test_revoke_session(self):
        """Revoked token is no longer valid."""
        token = self.auth.create_session(self.user["id"])
        self.assertIsNotNone(self.auth.verify_session(token))
        self.auth.revoke_session(token)
        self.assertIsNone(self.auth.verify_session(token))

    def test_revoke_all_sessions(self):
        """revoke_all_sessions clears all tokens for a user."""
        t1 = self.auth.create_session(self.user["id"])
        t2 = self.auth.create_session(self.user["id"])
        self.assertIsNotNone(self.auth.verify_session(t1))
        self.assertIsNotNone(self.auth.verify_session(t2))
        self.auth.revoke_all_sessions(self.user["id"])
        self.assertIsNone(self.auth.verify_session(t1))
        self.assertIsNone(self.auth.verify_session(t2))

    def test_list_active_sessions(self):
        """list_active_sessions returns current sessions."""
        self.auth.create_session(self.user["id"], "10.0.0.1")
        sessions = self.auth.list_active_sessions()
        self.assertGreaterEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["email"], "session@test.com")

    def test_cleanup_expired_sessions(self):
        """cleanup removes expired sessions only."""
        active_token = self.auth.create_session(self.user["id"])
        expired_token = self.auth.create_session(self.user["id"])
        # Expire one
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        past = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("UPDATE sessions SET expires_at = ? WHERE token = ?", (past, expired_token))
        conn.commit()
        conn.close()
        count = self.auth.cleanup_expired_sessions()
        self.assertGreaterEqual(count, 1)
        # Active token still works
        self.assertIsNotNone(self.auth.verify_session(active_token))

    def test_session_inactive_user(self):
        """Session for deactivated user returns None."""
        token = self.auth.create_session(self.user["id"])
        self.assertIsNotNone(self.auth.verify_session(token))
        self.auth.update_user(self.user["id"], active=0)
        self.assertIsNone(self.auth.verify_session(token))


class TestAuditLogging(unittest.TestCase):
    """Test auth audit trail."""

    def setUp(self):
        import auth
        self.auth = auth
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test_auth.db")
        with patch.dict(os.environ, {
            "AUTH_ADMIN_EMAIL": "",
            "AUTH_ADMIN_PASSWORD": "",
            "AUTH_SITE_PASSWORD": "",
        }):
            self.auth.init_auth_db(self.db_path)

    def test_log_auth_event(self):
        """Events are logged to auth_audit table."""
        self.auth.log_auth_event("test_action", "user@test.com", "1.2.3.4", "Test details")
        entries = self.auth.get_auth_audit(10)
        self.assertTrue(any(e["action"] == "test_action" for e in entries))

    def test_get_auth_audit_limit(self):
        """get_auth_audit respects limit parameter."""
        for i in range(5):
            self.auth.log_auth_event(f"event_{i}", f"u{i}@test.com")
        entries = self.auth.get_auth_audit(3)
        self.assertEqual(len(entries), 3)

    def test_audit_ordered_newest_first(self):
        """Audit entries are returned newest first."""
        self.auth.log_auth_event("first", "a@test.com")
        self.auth.log_auth_event("second", "b@test.com")
        entries = self.auth.get_auth_audit(10)
        self.assertEqual(entries[0]["action"], "second")


class TestAuthEnabled(unittest.TestCase):
    """Test AUTH_ENABLED environment variable."""

    def test_default_is_enabled(self):
        """Without env var, auth is enabled."""
        import auth
        with patch.dict(os.environ, {}, clear=False):
            if "AUTH_ENABLED" in os.environ:
                del os.environ["AUTH_ENABLED"]
            # Default should be true (enabled)
            self.assertTrue(auth.is_auth_enabled())

    def test_disabled_by_env(self):
        """AUTH_ENABLED=false disables auth."""
        import auth
        with patch.dict(os.environ, {"AUTH_ENABLED": "false"}):
            self.assertFalse(auth.is_auth_enabled())

    def test_enabled_by_env(self):
        """AUTH_ENABLED=true enables auth."""
        import auth
        with patch.dict(os.environ, {"AUTH_ENABLED": "true"}):
            self.assertTrue(auth.is_auth_enabled())


class TestAdminSettings(unittest.TestCase):
    """Test admin settings updates."""

    def setUp(self):
        import auth
        self.auth = auth
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test_auth.db")
        with patch.dict(os.environ, {
            "AUTH_ADMIN_EMAIL": "",
            "AUTH_ADMIN_PASSWORD": "",
            "AUTH_SITE_PASSWORD": "original",
        }):
            self.auth.init_auth_db(self.db_path)

    def test_update_site_password(self):
        """Site password can be changed."""
        self.assertTrue(self.auth.check_site_password("original"))
        self.auth.update_site_password("new_password")
        self.assertFalse(self.auth.check_site_password("original"))
        self.assertTrue(self.auth.check_site_password("new_password"))

    def test_update_session_timeout(self):
        """Session timeout can be changed."""
        self.auth.update_session_timeout(48)
        # Verify new timeout is used
        self.assertEqual(self.auth._get_session_timeout(), 48)

    def test_update_require_site_password(self):
        """Site password requirement can be toggled."""
        self.auth.update_require_site_password(False)
        self.assertFalse(self.auth.is_site_password_required())
        self.auth.update_require_site_password(True)
        self.assertTrue(self.auth.is_site_password_required())


class TestAuthGateImports(unittest.TestCase):
    """Test that auth_gate module is importable."""

    def test_auth_gate_importable(self):
        """shared.auth_gate module exists and is importable."""
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
        from shared.auth_gate import require_login, logout_user, get_current_user
        self.assertTrue(callable(require_login))
        self.assertTrue(callable(logout_user))
        self.assertTrue(callable(get_current_user))


if __name__ == "__main__":
    unittest.main()
