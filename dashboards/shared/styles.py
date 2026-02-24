"""Harris Farm Hub -- Dark Navy Design System
Common CSS, helpers, header, and footer for consistent dark UI.
Brand: Harris Farm Markets — "For The Greater Goodness"
Design: Dark navy with green accents, Georgia/Trebuchet typography
"""

import streamlit as st
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# Dark Navy Palette
# ═══════════════════════════════════════════════════════════════════════════

NAVY = "#0A0F0A"
NAVY_LIGHT = "#111A11"
NAVY_MID = "#1A2A1A"
NAVY_CARD = "#0D150D"

GREEN = "#2ECC71"
GREEN_DARK = "#27AE60"
GREEN_GLOW = "rgba(46,204,113,0.12)"

GOLD = "#F1C40F"
BLUE = "#3B82F6"
PURPLE = "#8B5CF6"
RED = "#EF4444"
ORANGE = "#F97316"
CYAN = "#06B6D4"
PINK = "#EC4899"

TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#B0BEC5"
TEXT_MUTED = "#8899AA"

GLASS = "rgba(255,255,255,0.05)"
GLASS_HOVER = "rgba(255,255,255,0.08)"
BORDER = "rgba(255,255,255,0.08)"
BORDER_LIGHT = "rgba(255,255,255,0.12)"

# Legacy aliases — imported by 41+ files, MUST keep these names
HFM_GREEN = GREEN
HFM_BLUE = BLUE
HFM_AMBER = ORANGE
HFM_RED = RED
HFM_DARK = TEXT_PRIMARY
HFM_BG = NAVY
HFM_LIGHT = NAVY_CARD

SHARED_CSS = f"""
<style>
    /* ── Typography ── */
    html, body, .main {{
        font-family: 'Trebuchet MS', 'Segoe UI', sans-serif !important;
        font-size: 18px !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: Georgia, 'Times New Roman', serif !important;
    }}

    /* ── Layout ── */
    .main .block-container {{ padding-top: 1.5rem; }}

    /* ── Dark backgrounds ── */
    .main, [data-testid="stAppViewContainer"],
    [data-testid="stHeader"],
    section[data-testid="stSidebar"] {{
        background-color: {NAVY} !important;
    }}
    [data-testid="stAppViewContainer"] > section > div {{
        background-color: {NAVY} !important;
    }}

    /* ── Headings ── */
    h1 {{ color: {GREEN} !important; font-size: 2.4rem !important; font-weight: 700 !important; }}
    h2 {{ font-size: 1.8rem !important; font-weight: 600 !important; color: {TEXT_PRIMARY} !important; }}
    h3 {{ font-size: 1.4rem !important; font-weight: 600 !important; color: {TEXT_PRIMARY} !important; }}

    /* ── Body text ── */
    .main p, .main li, .main span, .main div {{
        font-size: 1.05rem !important;
        color: {TEXT_SECONDARY};
    }}
    .main strong, .main b {{ font-size: 1.05rem !important; color: {TEXT_PRIMARY}; }}

    /* ── Metric cards — glass style ── */
    .stMetric {{
        background-color: {NAVY_CARD} !important;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid {BORDER} !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 1rem !important; font-weight: 500 !important;
        color: {TEXT_SECONDARY} !important;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 2rem !important; font-weight: 700 !important;
        color: {TEXT_PRIMARY} !important;
    }}
    [data-testid="stMetricDelta"] {{ font-size: 0.95rem !important; }}

    /* ── Tab labels ── */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {NAVY_LIGHT} !important;
        border-radius: 8px;
        padding: 4px;
        gap: 2px;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-size: 1.1rem !important;
        padding: 10px 20px !important;
        color: {TEXT_MUTED} !important;
        border-radius: 6px !important;
        background-color: transparent !important;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {GREEN} !important;
        background-color: {NAVY_MID} !important;
        font-weight: 600 !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: {GREEN} !important;
    }}
    .stTabs [data-baseweb="tab-border"] {{
        background-color: transparent !important;
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background-color: {NAVY_LIGHT} !important;
        border-right: 1px solid {BORDER} !important;
    }}
    [data-testid="stSidebar"] label {{
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: {TEXT_SECONDARY} !important;
    }}
    [data-testid="stSidebar"] h3 {{
        font-size: 1.25rem !important;
        color: {TEXT_PRIMARY} !important;
    }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
        font-size: 1rem !important;
        color: {TEXT_SECONDARY} !important;
    }}

    /* ── Selectbox / inputs on dark ── */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div {{
        background-color: {NAVY_MID} !important;
        border-color: {BORDER_LIGHT} !important;
        color: {TEXT_PRIMARY} !important;
    }}
    [data-baseweb="select"] span,
    [data-baseweb="input"] input {{
        color: {TEXT_PRIMARY} !important;
    }}

    /* ── Expander ── */
    .streamlit-expanderHeader {{
        font-size: 1.1rem !important;
        color: {TEXT_PRIMARY} !important;
        background-color: {NAVY_CARD} !important;
        border-radius: 8px !important;
    }}
    details[data-testid="stExpander"] {{
        background-color: {NAVY_CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 8px !important;
    }}
    details[data-testid="stExpander"] summary {{
        color: {TEXT_PRIMARY} !important;
    }}

    /* ── Data tables ── */
    .stDataFrame {{
        background-color: {NAVY_CARD} !important;
        border-radius: 8px;
    }}
    .stDataFrame th {{
        font-size: 1rem !important; font-weight: 600 !important;
        background-color: {NAVY_MID} !important;
        color: {TEXT_PRIMARY} !important;
    }}
    .stDataFrame td {{
        font-size: 1rem !important;
        color: {TEXT_SECONDARY} !important;
    }}

    /* ── Captions ── */
    .stCaption, small {{ font-size: 0.9rem !important; color: {TEXT_MUTED} !important; }}

    /* ── Buttons — green accent ── */
    .stButton > button {{
        font-size: 1rem !important;
        padding: 8px 20px !important;
        background-color: {GREEN} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }}
    .stButton > button:hover {{
        background-color: {GREEN_DARK} !important;
        color: white !important;
    }}

    /* ── Link buttons / page links ── */
    a, .stPageLink a {{
        color: {GREEN} !important;
    }}

    /* ── Dividers ── */
    hr {{ border-color: {BORDER} !important; }}

    /* ── Info/Warning/Error boxes ── */
    [data-testid="stAlert"] {{
        background-color: {NAVY_CARD} !important;
        border: 1px solid {BORDER} !important;
        color: {TEXT_SECONDARY} !important;
        border-radius: 8px !important;
    }}

    /* ── Markdown containers / custom HTML ── */
    [data-testid="stMarkdownContainer"] {{
        color: {TEXT_SECONDARY} !important;
    }}
    [data-testid="stMarkdownContainer"] h1 {{ color: {GREEN} !important; }}
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {{ color: {TEXT_PRIMARY} !important; }}

    /* ── Radio buttons / checkboxes ── */
    [data-testid="stRadio"] label,
    [data-testid="stCheckbox"] label {{
        color: {TEXT_SECONDARY} !important;
    }}

    /* ── Text input ── */
    .stTextInput > div > div {{
        background-color: {NAVY_MID} !important;
        border-color: {BORDER_LIGHT} !important;
    }}
    .stTextInput input {{
        color: {TEXT_PRIMARY} !important;
    }}
    .stTextInput label {{
        color: {TEXT_SECONDARY} !important;
    }}

    /* ── Text area ── */
    .stTextArea textarea {{
        background-color: {NAVY_MID} !important;
        border-color: {BORDER_LIGHT} !important;
        color: {TEXT_PRIMARY} !important;
    }}

    /* ── Multiselect ── */
    .stMultiSelect [data-baseweb="tag"] {{
        background-color: {GREEN} !important;
        color: white !important;
    }}

    /* ── Progress bar ── */
    .stProgress > div > div {{
        background-color: {NAVY_MID} !important;
    }}
    .stProgress > div > div > div {{
        background-color: {GREEN} !important;
    }}

    /* ── Hide deploy button ── */
    .stDeployButton {{ display: none !important; }}
    [data-testid="stToolbar"] .stDeployButton {{ display: none !important; }}

    /* ── Plotly chart containers ── */
    .stPlotlyChart {{
        background-color: transparent !important;
    }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 8px; }}
    ::-webkit-scrollbar-track {{ background: {NAVY}; }}
    ::-webkit-scrollbar-thumb {{ background: {NAVY_MID}; border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {TEXT_MUTED}; }}
</style>
"""


def apply_styles(extra_css: str = ""):
    """Inject shared CSS into the page. Call before render_nav()."""
    if extra_css:
        css = SHARED_CSS.replace("</style>", f"    {extra_css}\n</style>")
    else:
        css = SHARED_CSS
    st.markdown(css, unsafe_allow_html=True)

    # Set Plotly default template globally — all charts inherit dark navy theme
    try:
        import plotly.io as pio
        import plotly.graph_objects as go
        if "navy" not in pio.templates:
            pio.templates["navy"] = go.layout.Template(
                layout=go.Layout(**plotly_dark_template())
            )
        pio.templates.default = "navy"
    except ImportError:
        pass


def glass_card(content_html: str, border_color: str = "", min_height: str = ""):
    """Return HTML for a frosted-glass card on navy background."""
    border = f"border-top: 3px solid {border_color};" if border_color else ""
    height = f"min-height: {min_height};" if min_height else ""
    return (
        f"<div style='background:{GLASS};backdrop-filter:blur(8px);"
        f"border:1px solid {BORDER};border-radius:12px;padding:20px;"
        f"{border}{height}box-shadow:0 4px 16px rgba(0,0,0,0.2);'>"
        f"{content_html}</div>"
    )


def plotly_dark_template():
    """Return a dict of Plotly layout overrides for the dark navy theme.

    Usage: fig.update_layout(**plotly_dark_template())
    """
    return dict(
        paper_bgcolor=NAVY_CARD,
        plot_bgcolor=NAVY_CARD,
        font=dict(family="Trebuchet MS, sans-serif", color=TEXT_SECONDARY),
        title_font=dict(family="Georgia, serif", color=TEXT_PRIMARY),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.06)",
            linecolor=BORDER,
            zerolinecolor="rgba(255,255,255,0.1)",
            tickfont=dict(color=TEXT_MUTED),
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.06)",
            linecolor=BORDER,
            zerolinecolor="rgba(255,255,255,0.1)",
            tickfont=dict(color=TEXT_MUTED),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_SECONDARY),
        ),
        colorway=[
            GREEN, BLUE, GOLD, PURPLE, ORANGE,
            CYAN, PINK, RED, "#A3E635", "#818CF8",
        ],
        margin=dict(t=40, r=20, b=40, l=60),
        hoverlabel=dict(
            bgcolor=NAVY_MID,
            font_color=TEXT_PRIMARY,
            bordercolor=BORDER,
        ),
    )


def render_header(title: str, subtitle: str, goals=None, strategy_context=None):
    """Render standard dashboard header with optional goal alignment."""
    st.title(title)
    st.markdown(subtitle)

    if goals:
        try:
            from shared.goals_config import HUB_GOALS, goal_badge_html
            badges = " ".join(goal_badge_html(g) for g in goals)
            ctx_html = ""
            if strategy_context:
                ctx_html = (
                    f"<div style='font-size:0.85em;color:{TEXT_MUTED};"
                    f"margin-top:6px;font-style:italic;'>"
                    f"{strategy_context}</div>"
                )
            st.markdown(
                f"<div style='margin:8px 0 4px;'>{badges}{ctx_html}</div>",
                unsafe_allow_html=True,
            )
        except ImportError:
            pass

    st.caption("For The Greater Goodness \u2014 Harris Farm Markets")
    st.markdown("---")


def render_footer(name: str, extra: str = "", user=None):
    """Render standard dashboard footer: divider + flag button + caption + logout."""
    parts = [name, "Harris Farm Hub \u2014 For The Greater Goodness"]
    if extra:
        parts.append(extra)
    if user and user.get("name"):
        parts.append(f"Logged in as {user['name']}")
    parts.append(datetime.now().strftime("%Y-%m-%d %H:%M"))
    st.markdown("---")

    # Universal flag button
    try:
        from shared.flag_widget import render_flag_button
        render_flag_button()
    except Exception:
        pass

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

    st.markdown("---")
    st.caption("The Hub \u00b7 Harris Farm Markets \u00b7 Built with \U0001f49a by Harris Farmers, for Harris Farmers")
