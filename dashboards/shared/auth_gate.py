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
    [data-testid="stSidebarNav"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Dark gradient background — override EVERY Streamlit container */
    html, body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"],
    .main,
    .main > div,
    .block-container,
    [data-testid="stVerticalBlock"],
    section[data-testid="stSidebar"],
    .stApp > header {
        background: transparent !important;
        background-color: transparent !important;
    }

    .stApp {
        background: linear-gradient(135deg, #0a1628 0%, #1a2744 50%, #0d1f3c 100%) !important;
    }

    /* Center content vertically and constrain width */
    .stApp > .main > .block-container,
    .block-container {
        max-width: 440px !important;
        padding: 2rem 1.5rem !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        min-height: 100vh !important;
        margin: 0 auto !important;
    }

    /* ALL text on login page must be light */
    .stApp p, .stApp span, .stApp div, .stApp label,
    .stApp h1, .stApp h2, .stApp h3,
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div {
        color: rgba(255, 255, 255, 0.85) !important;
    }

    /* Style text input labels */
    .stTextInput > label,
    .stTextInput label,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        letter-spacing: 0.3px !important;
    }

    /* Pulsing glow animation for password fields */
    @keyframes pulse-glow {
        0%, 100% { text-shadow: 0 0 8px rgba(74, 222, 128, 0.8); opacity: 1; }
        50% { text-shadow: 0 0 16px rgba(74, 222, 128, 1); opacity: 0.7; }
    }

    /* Style ALL text input fields */
    .stTextInput input,
    .stTextInput > div > div > input,
    [data-testid="stTextInput"] input {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        padding: 14px 16px !important;
        font-size: 16px !important;
        caret-color: #4ade80 !important;
    }

    /* Password fields — bright green pulsing dots */
    .stTextInput input[type="password"] {
        color: #4ade80 !important;
        -webkit-text-fill-color: #4ade80 !important;
        font-size: 22px !important;
        letter-spacing: 6px !important;
        animation: pulse-glow 1.2s ease-in-out infinite !important;
    }

    .stTextInput input:focus,
    .stTextInput > div > div > input:focus {
        border-color: rgba(74, 222, 128, 0.5) !important;
        background: rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 0 0 3px rgba(74, 222, 128, 0.15) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    /* Focused password fields keep green glow */
    .stTextInput input[type="password"]:focus {
        color: #4ade80 !important;
        -webkit-text-fill-color: #4ade80 !important;
        box-shadow: 0 0 0 3px rgba(74, 222, 128, 0.2) !important;
    }

    .stTextInput input::placeholder,
    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.35) !important;
        -webkit-text-fill-color: rgba(255, 255, 255, 0.35) !important;
        animation: none !important;
        letter-spacing: normal !important;
        font-size: 15px !important;
    }

    /* Checkbox styling for reveal toggle */
    .stCheckbox label span,
    .stCheckbox label p {
        color: rgba(255, 255, 255, 0.6) !important;
        font-size: 13px !important;
    }

    /* Style the Sign In / Create Account button */
    .stFormSubmitButton > button,
    [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #2d7d3a, #3a9d4a) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px !important;
        transition: all 0.2s ease !important;
    }

    .stFormSubmitButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, #3a9d4a, #4aad5a) !important;
        box-shadow: 0 4px 15px rgba(45, 125, 58, 0.4) !important;
    }

    /* Toggle buttons (Create Account / Sign In) */
    .stButton > button {
        color: rgba(255, 255, 255, 0.7) !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.12) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        color: #fff !important;
    }

    /* Caption / helper text */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: rgba(255, 255, 255, 0.45) !important;
    }

    /* Error messages */
    .stAlert [data-testid="stNotificationContentError"] {
        background: rgba(220, 53, 69, 0.15) !important;
        border: 1px solid rgba(220, 53, 69, 0.3) !important;
        color: #ff6b7a !important;
    }

    /* Divider line */
    hr {
        border-color: rgba(255, 255, 255, 0.1) !important;
    }

    /* Mobile responsive */
    @media (max-width: 480px) {
        .stApp > .main > .block-container {
            padding: 1.5rem 1rem !important;
        }
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
                else:
                    # API explicitly said token is invalid — clear it
                    st.session_state.pop("auth_token", None)
                    st.session_state.pop("auth_user", None)
            else:
                # Non-200 response — clear token
                st.session_state.pop("auth_token", None)
                st.session_state.pop("auth_user", None)
        except requests.RequestException:
            # API unreachable — trust cached session if we have one
            cached_user = st.session_state.get("auth_user")
            if cached_user:
                return cached_user

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

    # Logo and title — self-contained HTML block (no wrapping divs)
    st.markdown(
        '<div style="text-align:center;padding-top:2rem;margin-bottom:2rem;">'
        '<div style="font-size:3rem;margin-bottom:0.5rem;">&#127822;</div>'
        '<div style="font-size:1.75rem;font-weight:700;color:#fff;'
        'letter-spacing:-0.5px;margin-bottom:0.25rem;">Harris Farm Hub</div>'
        '<div style="font-size:0.8rem;color:rgba(255,255,255,0.45);'
        'letter-spacing:2px;text-transform:uppercase;font-weight:400;">'
        'AI Centre of Excellence</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if not api_ok:
        st.error("Cannot connect to the Hub API. The backend may still be starting — please refresh in 30 seconds.")
        return

    if st.session_state.get("auth_mode", "login") == "login":
        _render_login(api_url, site_pw_required)
    else:
        _render_register(api_url, site_pw_required)

    # Footer
    st.markdown(
        '<div style="text-align:center;margin-top:2rem;color:rgba(255,255,255,0.25);'
        'font-size:0.75rem;">Harris Farm Markets &middot; Powered by AI</div>',
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
