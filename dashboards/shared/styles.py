"""Harris Farm Hub -- Shared Dashboard Styles
Common CSS, header, and footer for consistent UI across all dashboards.
Brand: Harris Farm Markets — "For The Greater Goodness"
Colors: Primary green #4ba021, Secondary blue #a2d3f1, Text #171819
"""

import streamlit as st
from datetime import datetime

# Harris Farm brand palette
HFM_GREEN = "#4ba021"
HFM_BLUE = "#a2d3f1"
HFM_AMBER = "#d97706"
HFM_RED = "#ef4444"
HFM_DARK = "#171819"
HFM_BG = "#f5f5f5"
HFM_LIGHT = "#ffffff"

SHARED_CSS = """
<style>
    /* Base font size — everything scales from this */
    html, body, .main { font-size: 18px !important; }

    /* Layout */
    .main .block-container { padding-top: 1.5rem; }

    /* Headings — Harris Farm green */
    h1 { color: #4ba021; font-size: 2.4rem !important; font-weight: 700 !important; }
    h2 { font-size: 1.8rem !important; font-weight: 600 !important; color: #171819; }
    h3 { font-size: 1.4rem !important; font-weight: 600 !important; color: #171819; }

    /* Body text */
    .main p, .main li, .main span, .main div { font-size: 1.05rem !important; }
    .main strong, .main b { font-size: 1.05rem !important; }

    /* Metric cards */
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    [data-testid="stMetricLabel"] { font-size: 1rem !important; font-weight: 500 !important; }
    [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; }
    [data-testid="stMetricDelta"] { font-size: 0.95rem !important; }

    /* Tab labels */
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem !important;
        padding: 12px 24px !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] label {
        font-size: 1rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] h3 { font-size: 1.25rem !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        font-size: 1rem !important;
    }
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stMultiSelect,
    [data-testid="stSidebar"] .stRadio { font-size: 1rem !important; }

    /* Expander headers */
    .streamlit-expanderHeader { font-size: 1.1rem !important; }

    /* Data tables */
    .stDataFrame th { font-size: 1rem !important; font-weight: 600 !important; }
    .stDataFrame td { font-size: 1rem !important; }

    /* Captions */
    .stCaption, small { font-size: 0.9rem !important; }

    /* Buttons */
    .stButton > button { font-size: 1rem !important; padding: 8px 20px !important; }

    /* Hide Streamlit deploy button */
    .stDeployButton { display: none !important; }
    [data-testid="stToolbar"] .stDeployButton { display: none !important; }
</style>
"""


def apply_styles(extra_css: str = ""):
    """Inject shared CSS into the page. Call before render_nav()."""
    if extra_css:
        css = SHARED_CSS.replace("</style>", f"    {extra_css}\n</style>")
    else:
        css = SHARED_CSS
    st.markdown(css, unsafe_allow_html=True)


def render_header(title: str, subtitle: str):
    """Render standard dashboard header: title + bold subtitle + divider."""
    st.title(title)
    st.markdown(subtitle)
    st.caption("For The Greater Goodness — Harris Farm Markets")
    st.markdown("---")


def render_footer(name: str, extra: str = "", user=None):
    """Render standard dashboard footer: divider + caption with timestamp + user info."""
    parts = [name, "Harris Farm Hub — For The Greater Goodness"]
    if extra:
        parts.append(extra)
    if user and user.get("name"):
        parts.append(f"Logged in as {user['name']}")
    parts.append(datetime.now().strftime("%Y-%m-%d %H:%M"))
    st.markdown("---")
    if user:
        col1, col2 = st.columns([8, 1])
        with col1:
            st.caption(" | ".join(parts))
        with col2:
            from shared.auth_gate import logout_user
            if st.button("Logout", key="logout_btn"):
                logout_user()
    else:
        st.caption(" | ".join(parts))
