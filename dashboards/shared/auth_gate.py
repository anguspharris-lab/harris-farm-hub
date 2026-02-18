"""
Harris Farm Hub — Authentication Gate
Shared login gate for all Streamlit dashboards.
Call require_login() at the top of each dashboard before rendering content.
"""

import os
from pathlib import Path

import requests
import streamlit as st

# Load .env from project root so AUTH_ENABLED is available
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Login page CSS
# ---------------------------------------------------------------------------

_LOGIN_CSS = """
<style>
    /* Hide Streamlit chrome on login page */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 0 !important; max-width: 100% !important;}

    .auth-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
        margin: -6rem -4rem;
        padding: 2rem;
    }
    .auth-card {
        background: white;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        padding: 48px 40px;
        width: 100%;
        max-width: 420px;
    }
    .auth-logo {
        text-align: center;
        margin-bottom: 8px;
    }
    .auth-logo span {
        font-size: 2.8em;
    }
    .auth-title {
        text-align: center;
        font-size: 1.6em;
        font-weight: 700;
        color: #1e3a8a;
        margin: 0 0 4px 0;
        letter-spacing: -0.5px;
    }
    .auth-subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 0.95em;
        margin: 0 0 32px 0;
    }
    .auth-divider {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 24px 0;
    }
    .auth-footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.8em;
        margin-top: 24px;
    }
    .auth-toggle {
        text-align: center;
        margin-top: 16px;
    }
    .auth-toggle a {
        color: #1e3a8a;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.9em;
    }

    /* Style Streamlit form elements inside auth card */
    .auth-card .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1.5px solid #d1d5db;
        padding: 10px 14px;
        font-size: 0.95em;
    }
    .auth-card .stTextInput > div > div > input:focus {
        border-color: #1e3a8a;
        box-shadow: 0 0 0 3px rgba(30,58,138,0.1);
    }
    .auth-card .stButton > button {
        background: linear-gradient(135deg, #1e3a8a, #2563eb);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 1em;
        font-weight: 600;
        letter-spacing: 0.3px;
        transition: all 0.2s;
    }
    .auth-card .stButton > button:hover {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        box-shadow: 0 4px 12px rgba(30,58,138,0.3);
        transform: translateY(-1px);
    }
</style>
"""


def require_login(api_url=None):
    """
    Gate function -- call at top of every dashboard.

    Returns user dict (id, email, name, role) if authenticated.
    If not authenticated, shows login form and calls st.stop().
    If AUTH_ENABLED=false, returns a default dev user dict.
    """
    if api_url is None:
        api_url = API_URL

    # Dev bypass
    if os.getenv("AUTH_ENABLED", "true").lower() in ("false", "0", "no"):
        return {"id": 0, "email": "dev@local", "name": "Developer", "role": "admin"}

    # Check session_state first (fast path for reruns on same port)
    token = st.session_state.get("auth_token")
    source = "session_state"

    # Fall back to URL query params (cross-port navigation)
    if not token:
        token_val = st.query_params.get("token", None)
        if token_val:
            token = token_val
            source = "query_params"

    # Validate token if found
    if token:
        try:
            resp = requests.get(
                f"{api_url}/api/auth/verify",
                params={"token": token},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("valid"):
                    st.session_state["auth_token"] = token
                    st.session_state["auth_user"] = data["user"]
                    if source == "query_params":
                        st.query_params.clear()
                    return data["user"]
        except requests.RequestException:
            pass

        # Token invalid -- clear state
        st.session_state.pop("auth_token", None)
        st.session_state.pop("auth_user", None)

    # No valid token -- show login/register page
    _render_auth_page(api_url)
    st.stop()


def _render_auth_page(api_url):
    """Render the full-page login/register UI."""
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    # Check API connectivity and site password requirement
    site_pw_required = False
    api_ok = True
    try:
        resp = requests.get(f"{api_url}/api/auth/site-password-required", timeout=5)
        if resp.status_code == 200:
            site_pw_required = resp.json().get("required", False)
    except requests.RequestException:
        api_ok = False

    # Determine which form to show
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "login"

    st.markdown('<div class="auth-wrapper"><div class="auth-card">', unsafe_allow_html=True)

    # Logo and title
    st.markdown(
        '<div class="auth-logo"><span>&#127822;</span></div>'
        '<div class="auth-title">Harris Farm Hub</div>'
        '<div class="auth-subtitle">AI Centre of Excellence</div>',
        unsafe_allow_html=True,
    )

    if not api_ok:
        st.error("Cannot connect to the Hub API. Please ensure the backend is running on port 8000.")
        st.markdown('</div></div>', unsafe_allow_html=True)
        return

    if st.session_state.get("auth_mode", "login") == "login":
        _render_login(api_url, site_pw_required)
    else:
        _render_register(api_url, site_pw_required)

    st.markdown(
        '<div class="auth-footer">Harris Farm Markets &bull; AI Centre of Excellence</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div></div>', unsafe_allow_html=True)


def _render_login(api_url, site_pw_required):
    """Render the login form."""
    with st.form("login_form", clear_on_submit=False):
        if site_pw_required:
            site_password = st.text_input("Site Access Code", type="password",
                                          placeholder="Enter site access code")
        else:
            site_password = None

        email = st.text_input("Email Address", placeholder="you@harrisfarm.com.au")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        st.markdown("")  # spacing
        submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            _handle_login(api_url, site_pw_required, site_password, email, password)

    # Toggle to register
    st.markdown('<hr class="auth-divider">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Don't have an account?")
    with col2:
        if st.button("Create Account", key="switch_register", use_container_width=True):
            st.session_state["auth_mode"] = "register"
            st.rerun()


def _handle_login(api_url, site_pw_required, site_password, email, password):
    """Process login form submission."""
    if not email or not password:
        st.error("Please enter your email and password.")
        return

    # Validate site password if required
    if site_pw_required:
        if not site_password:
            st.error("Site access code is required.")
            return
        try:
            resp = requests.post(
                f"{api_url}/api/auth/site-check",
                json={"password": site_password},
                timeout=5,
            )
            if resp.status_code != 200 or not resp.json().get("valid"):
                st.error("Invalid site access code.")
                return
        except requests.RequestException:
            st.error("Cannot connect to the Hub API.")
            return

    # Authenticate user
    try:
        resp = requests.post(
            f"{api_url}/api/auth/login",
            json={"email": email, "password": password},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            st.session_state["auth_token"] = data["token"]
            st.session_state["auth_user"] = data["user"]
            st.session_state.pop("auth_mode", None)
            st.rerun()
        else:
            st.error("Invalid email or password. Please check your credentials.")
    except requests.RequestException:
        st.error("Cannot connect to the Hub API.")


def _render_register(api_url, site_pw_required):
    """Render the registration form."""
    with st.form("register_form", clear_on_submit=False):
        if site_pw_required:
            site_password = st.text_input("Site Access Code", type="password",
                                          placeholder="Required to create an account")
        else:
            site_password = None

        name = st.text_input("Full Name", placeholder="Your full name")
        email = st.text_input("Email Address", placeholder="you@harrisfarm.com.au")
        password = st.text_input("Choose Password", type="password",
                                 placeholder="Minimum 8 characters")
        confirm = st.text_input("Confirm Password", type="password",
                                placeholder="Re-enter your password")

        st.markdown("")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

        if submitted:
            _handle_register(api_url, site_pw_required, site_password,
                             name, email, password, confirm)

    # Toggle to login
    st.markdown('<hr class="auth-divider">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Already have an account?")
    with col2:
        if st.button("Sign In", key="switch_login", use_container_width=True):
            st.session_state["auth_mode"] = "login"
            st.rerun()


def _handle_register(api_url, site_pw_required, site_password,
                     name, email, password, confirm):
    """Process registration form submission."""
    if not name or not email or not password or not confirm:
        st.error("Please fill in all fields.")
        return

    if len(password) < 8:
        st.error("Password must be at least 8 characters.")
        return

    if password != confirm:
        st.error("Passwords do not match.")
        return

    # Validate site password if required
    if site_pw_required:
        if not site_password:
            st.error("Site access code is required to create an account.")
            return
        try:
            resp = requests.post(
                f"{api_url}/api/auth/site-check",
                json={"password": site_password},
                timeout=5,
            )
            if resp.status_code != 200 or not resp.json().get("valid"):
                st.error("Invalid site access code.")
                return
        except requests.RequestException:
            st.error("Cannot connect to the Hub API.")
            return

    # Create user via API
    try:
        resp = requests.post(
            f"{api_url}/api/auth/register",
            json={"name": name, "email": email, "password": password},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            st.session_state["auth_token"] = data["token"]
            st.session_state["auth_user"] = data["user"]
            st.session_state.pop("auth_mode", None)
            st.rerun()
        elif resp.status_code == 409:
            st.error("An account with this email already exists.")
        else:
            detail = resp.json().get("detail", "Registration failed.")
            st.error(detail)
    except requests.RequestException:
        st.error("Cannot connect to the Hub API.")


def logout_user(api_url=None):
    """Revoke session and clear session_state."""
    if api_url is None:
        api_url = API_URL

    token = st.session_state.get("auth_token")
    if token:
        try:
            requests.post(
                f"{api_url}/api/auth/logout",
                json={"token": token},
                timeout=5,
            )
        except requests.RequestException:
            pass

    for key in ["auth_token", "auth_user", "site_pw_verified", "auth_mode"]:
        st.session_state.pop(key, None)
    st.rerun()


def get_current_user():
    """Get the currently authenticated user from session_state, or None."""
    return st.session_state.get("auth_user")
