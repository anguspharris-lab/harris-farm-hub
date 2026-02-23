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
# Login page CSS — targets Streamlit's actual DOM elements directly
# (NOT wrapper divs, which don't work across st.markdown blocks)
# ---------------------------------------------------------------------------

_LOGIN_CSS = """
<style>
    /* Hide Streamlit chrome on login page */
    #MainMenu, footer, header, [data-testid="stSidebar"],
    [data-testid="stSidebarNav"], .stDeployButton {
        display: none !important;
        visibility: hidden !important;
    }

    /* Dark navy background */
    .main, [data-testid="stAppViewContainer"],
    [data-testid="stHeader"],
    [data-testid="stAppViewContainer"] > section > div {
        background-color: #0B1628 !important;
    }

    /* Center content and constrain width */
    .block-container {
        max-width: 440px !important;
        margin: 0 auto !important;
        padding-top: 4rem !important;
    }

    /* Text colors for dark bg */
    .main p, .main li, .main span, .main div,
    .main label, .stCaption, small { color: #B0BEC5 !important; }
    .main strong, .main b, .main h1, .main h2, .main h3 { color: #FFFFFF !important; }

    /* Input fields on dark */
    .stTextInput > div > div {
        background-color: #1A2D50 !important;
        border-color: rgba(255,255,255,0.12) !important;
    }
    .stTextInput input { color: #FFFFFF !important; }
    .stTextInput label { color: #B0BEC5 !important; }

    /* Green submit button */
    .stFormSubmitButton > button,
    [data-testid="stFormSubmitButton"] > button {
        background-color: #2ECC71 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
    }

    .stFormSubmitButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #27AE60 !important;
    }

    /* Toggle button (Create Account / Sign In) */
    .stButton > button {
        border-radius: 8px !important;
        color: #B0BEC5 !important;
    }

    /* Dividers */
    hr { border-color: rgba(255,255,255,0.08) !important; }

    /* Checkbox */
    [data-testid="stCheckbox"] label { color: #8899AA !important; }
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
        return {"id": 0, "email": "dev@local", "name": "Developer", "role": "admin", "hub_role": "admin"}

    # Fast path: already logged in this session — no API call needed
    if st.session_state.get("auth_token") and st.session_state.get("auth_user"):
        return st.session_state["auth_user"]

    # Check URL query params (cross-port navigation, legacy)
    token = st.query_params.get("token", None)
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
                    st.query_params.clear()
                    return data["user"]
        except requests.RequestException:
            pass

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

    # Logo and title
    st.markdown(
        '<div style="text-align:center;margin-bottom:2rem;">'
        '<div style="font-size:3rem;margin-bottom:0.5rem;">&#127822;</div>'
        '<div style="font-size:1.75rem;font-weight:700;color:#FFFFFF;'
        'font-family:Georgia,serif;letter-spacing:-0.5px;margin-bottom:0.25rem;">'
        'Harris Farm Hub</div>'
        '<div style="font-size:0.8rem;color:#8899AA;'
        'letter-spacing:2px;text-transform:uppercase;font-weight:400;'
        'font-family:Trebuchet MS,sans-serif;">'
        'AI Centre of Excellence</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if not api_ok:
        st.error("Cannot connect to the Hub API. The backend may still be starting — please refresh in 30 seconds.")
        return

    mode = st.session_state.get("auth_mode", "login")
    if mode == "login":
        _render_login(api_url, site_pw_required)
    elif mode == "reset":
        _render_reset_password(api_url, site_pw_required)
    else:
        _render_register(api_url, site_pw_required)

    # Footer
    st.markdown(
        '<div style="text-align:center;margin-top:2rem;color:#8899AA;'
        'font-size:0.75rem;font-family:Trebuchet MS,sans-serif;">'
        'Harris Farm Markets &middot; Powered by AI</div>',
        unsafe_allow_html=True,
    )


def _render_login(api_url, site_pw_required):
    """Render the login form."""
    # Reveal toggle (outside form so it updates instantly)
    show_pw = st.checkbox("Reveal passwords", key="login_show_pw", value=False)
    pw_type = "default" if show_pw else "password"

    with st.form("login_form", clear_on_submit=False):
        if site_pw_required:
            site_password = st.text_input("Site Access Code", type=pw_type,
                                          placeholder="Enter site access code")
        else:
            site_password = None

        email = st.text_input("Email", placeholder="you@harrisfarm.com.au")
        password = st.text_input("Password", type=pw_type, placeholder="Enter password")

        st.markdown("")  # spacing
        submitted = st.form_submit_button("Enter The Hub", use_container_width=True)

        if submitted:
            _handle_login(api_url, site_pw_required, site_password, email, password)

    # Forgot password link
    if st.button("Forgot Password?", key="switch_reset", type="tertiary"):
        st.session_state["auth_mode"] = "reset"
        st.rerun()

    # Toggle to register
    st.markdown("---")
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
        except requests.RequestException as e:
            st.error(f"Cannot connect to the Hub API at {api_url}: {e}")
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
            detail = resp.json().get("detail", "Unknown error")
            st.error(f"Login failed: {detail}")
    except requests.RequestException as e:
        st.error(f"Cannot connect to the Hub API at {api_url}: {e}")


def _render_reset_password(api_url, site_pw_required):
    """Render the password reset form."""
    show_pw = st.checkbox("Reveal passwords", key="reset_show_pw", value=False)
    pw_type = "default" if show_pw else "password"

    with st.form("reset_form", clear_on_submit=False):
        st.markdown("**Reset your password**")
        st.caption("Enter the site access code, your email, and a new password.")

        site_password = st.text_input("Site Access Code", type=pw_type,
                                       placeholder="Required to verify identity")
        email = st.text_input("Email", placeholder="you@harrisfarm.com.au")
        new_password = st.text_input("New Password", type=pw_type,
                                      placeholder="Minimum 8 characters")
        confirm = st.text_input("Confirm New Password", type=pw_type,
                                 placeholder="Re-enter your new password")

        st.markdown("")
        submitted = st.form_submit_button("Reset Password", use_container_width=True)

        if submitted:
            if not site_password or not email or not new_password or not confirm:
                st.error("Please fill in all fields.")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters.")
            elif new_password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    resp = requests.post(
                        f"{api_url}/api/auth/reset-password",
                        json={
                            "email": email,
                            "new_password": new_password,
                            "site_password": site_password,
                        },
                        timeout=5,
                    )
                    if resp.status_code == 200:
                        st.success("Password reset! You can now sign in.")
                    else:
                        detail = resp.json().get("detail", "Reset failed.")
                        st.error(detail)
                except requests.RequestException:
                    st.error("Cannot connect to the Hub API.")

    # Back to login
    st.markdown("---")
    if st.button("Back to Sign In", key="switch_back_login", use_container_width=True):
        st.session_state["auth_mode"] = "login"
        st.rerun()


def _render_register(api_url, site_pw_required):
    """Render the registration form."""
    # Reveal toggle (outside form so it updates instantly)
    show_pw = st.checkbox("Reveal passwords", key="register_show_pw", value=False)
    pw_type = "default" if show_pw else "password"

    with st.form("register_form", clear_on_submit=False):
        if site_pw_required:
            site_password = st.text_input("Site Access Code", type=pw_type,
                                          placeholder="Required to create an account")
        else:
            site_password = None

        name = st.text_input("Full Name", placeholder="Your full name")
        email = st.text_input("Email", placeholder="you@harrisfarm.com.au")
        password = st.text_input("Choose Password", type=pw_type,
                                 placeholder="Minimum 8 characters")
        confirm = st.text_input("Confirm Password", type=pw_type,
                                placeholder="Re-enter your password")

        st.markdown("")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

        if submitted:
            _handle_register(api_url, site_pw_required, site_password,
                             name, email, password, confirm)

    # Toggle to login
    st.markdown("---")
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
