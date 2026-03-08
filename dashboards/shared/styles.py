"""Harris Farm Hub -- Modern Light Design System
Common CSS, helpers, header, and footer for consistent UI.
Brand: Harris Farm Markets -- "Living the Greater Goodness"
Design: Clean white with green accents, system typography (Google/Claude-inspired)
"""

import streamlit as st
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# Modern Light Palette
# ═══════════════════════════════════════════════════════════════════════════

NAVY = "#F5F7F5"              # primary background (light green-grey)
NAVY_LIGHT = "#F0F4F0"        # sidebar / tab bar
NAVY_MID = "#EEF2EE"          # tertiary surfaces
NAVY_CARD = "#FFFFFF"          # card surfaces

GREEN = "#2D6A2D"              # primary brand — Harris Farm green
GREEN_DARK = "#235522"
GREEN_GLOW = "rgba(45,106,45,0.12)"

GOLD = "#C8971F"               # darker gold — readable on white
BLUE = "#1565C0"
PURPLE = "#7C3AED"
RED = "#C0392B"
ORANGE = "#C8971F"             # amber/warning
CYAN = "#0891B2"
PINK = "#DB2777"

TEXT_PRIMARY = "#1A1A1A"       # near black
TEXT_SECONDARY = "#4A4A4A"     # dark grey body
TEXT_MUTED = "#717171"         # helper text

GLASS = "rgba(0,0,0,0.02)"
GLASS_HOVER = "rgba(45,106,45,0.04)"
BORDER = "#E0E8E0"
BORDER_LIGHT = "#D0D9D0"

# Legacy aliases -- imported by 41+ files, MUST keep these names
HFM_GREEN = GREEN
HFM_BLUE = BLUE
HFM_AMBER = ORANGE
HFM_RED = RED
HFM_DARK = TEXT_PRIMARY
HFM_BG = NAVY
HFM_LIGHT = NAVY_CARD

SHARED_CSS = f"""
<style>
    /* -- Typography -- system fonts, fast, clean -- */
    html, body, .main {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                     Roboto, Oxygen, sans-serif !important;
        font-size: 14px !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                     Roboto, Oxygen, sans-serif !important;
    }}

    /* -- Layout -- */
    .main .block-container {{ padding-top: 1.5rem; max-width: 1200px; }}

    /* -- Backgrounds -- */
    .main, [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > section > div {{
        background-color: {NAVY} !important;
    }}
    [data-testid="stHeader"] {{
        background-color: {NAVY_CARD} !important;
        border-bottom: 1px solid {BORDER} !important;
    }}

    /* -- Headings -- */
    h1 {{
        color: {GREEN} !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
    }}
    h2 {{
        font-size: 22px !important;
        font-weight: 600 !important;
        color: {TEXT_PRIMARY} !important;
    }}
    h3 {{
        font-size: 18px !important;
        font-weight: 600 !important;
        color: {TEXT_PRIMARY} !important;
    }}
    h4 {{
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #2d2d2d !important;
    }}

    /* -- Body text -- */
    .main p, .main li, .main span, .main div {{
        font-size: 14px !important;
        color: #2d2d2d;
    }}
    .main strong, .main b {{
        font-size: 14px !important;
        color: {TEXT_PRIMARY};
    }}

    /* -- Metric cards -- */
    .stMetric {{
        background-color: {NAVY_CARD} !important;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid {BORDER} !important;
        border-left: 4px solid {GREEN} !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 13px !important;
        font-weight: 500 !important;
        color: {TEXT_MUTED} !important;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 28px !important;
        font-weight: 700 !important;
        color: {GREEN} !important;
    }}
    [data-testid="stMetricDelta"] {{
        font-size: 13px !important;
    }}

    /* -- Tab labels -- */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {NAVY_CARD} !important;
        border-radius: 0;
        padding: 0;
        gap: 0;
        border-bottom: 1px solid {BORDER} !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-size: 14px !important;
        padding: 10px 20px !important;
        color: {TEXT_SECONDARY} !important;
        border-radius: 0 !important;
        background-color: transparent !important;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {GREEN} !important;
        background-color: transparent !important;
        font-weight: 600 !important;
        box-shadow: none;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: {GREEN} !important;
        height: 2px !important;
    }}
    .stTabs [data-baseweb="tab-border"] {{
        background-color: transparent !important;
    }}

    /* -- Sidebar -- */
    section[data-testid="stSidebar"] {{
        background-color: {NAVY_LIGHT} !important;
        border-right: 1px solid {BORDER} !important;
    }}
    [data-testid="stSidebar"] label {{
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #2d2d2d !important;
    }}
    [data-testid="stSidebar"] h3 {{
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: {TEXT_MUTED} !important;
    }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
        font-size: 14px !important;
        color: #2d2d2d !important;
    }}

    /* -- Selectbox / inputs -- */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div {{
        background-color: {NAVY_CARD} !important;
        border: 1.5px solid {BORDER_LIGHT} !important;
        border-radius: 8px !important;
        color: {TEXT_PRIMARY} !important;
    }}
    [data-baseweb="select"] > div:focus-within,
    [data-baseweb="input"] > div:focus-within {{
        border-color: {GREEN} !important;
        box-shadow: 0 0 0 3px rgba(45,106,45,0.15) !important;
    }}
    [data-baseweb="select"] span,
    [data-baseweb="input"] input {{
        color: {TEXT_PRIMARY} !important;
    }}

    /* -- Expander -- */
    .streamlit-expanderHeader {{
        font-size: 14px !important;
        font-weight: 600 !important;
        color: {TEXT_PRIMARY} !important;
        background-color: {NAVY_CARD} !important;
        border-radius: 10px !important;
    }}
    details[data-testid="stExpander"] {{
        background-color: {NAVY_CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 10px !important;
    }}
    details[data-testid="stExpander"] summary {{
        color: {TEXT_PRIMARY} !important;
    }}

    /* -- Data tables -- */
    .stDataFrame {{
        background-color: {NAVY_CARD} !important;
        border-radius: 10px;
    }}
    .stDataFrame th {{
        font-size: 13px !important;
        font-weight: 600 !important;
        background-color: {NAVY_LIGHT} !important;
        color: {TEXT_PRIMARY} !important;
    }}
    .stDataFrame td {{
        font-size: 13px !important;
        color: {TEXT_SECONDARY} !important;
    }}

    /* -- Captions -- */
    .stCaption, small {{
        font-size: 12px !important;
        color: {TEXT_SECONDARY} !important;
    }}

    /* -- Buttons -- primary green -- */
    .stButton > button {{
        font-size: 14px !important;
        padding: 10px 20px !important;
        background-color: {GREEN} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: background-color 0.15s ease;
    }}
    .stButton > button:hover {{
        background-color: {GREEN_DARK} !important;
        color: white !important;
    }}

    /* -- Link buttons / page links -- */
    a, .stPageLink a {{
        color: {GREEN} !important;
    }}

    /* -- Dividers -- */
    hr {{
        border-color: {BORDER} !important;
    }}

    /* -- Info/Warning/Error boxes -- */
    [data-testid="stAlert"] {{
        background-color: {NAVY_CARD} !important;
        border: 1px solid {BORDER} !important;
        color: {TEXT_SECONDARY} !important;
        border-radius: 10px !important;
    }}

    /* -- Markdown containers / custom HTML -- */
    [data-testid="stMarkdownContainer"] {{
        color: #2d2d2d !important;
    }}
    [data-testid="stMarkdownContainer"] h1 {{
        color: {GREEN} !important;
    }}
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {{
        color: {TEXT_PRIMARY} !important;
    }}

    /* -- Radio buttons / checkboxes -- */
    [data-testid="stRadio"] label,
    [data-testid="stCheckbox"] label {{
        color: #2d2d2d !important;
    }}

    /* -- Text input -- */
    .stTextInput > div > div {{
        background-color: {NAVY_CARD} !important;
        border: 1.5px solid {BORDER_LIGHT} !important;
        border-radius: 8px !important;
    }}
    .stTextInput > div > div:focus-within {{
        border-color: {GREEN} !important;
        box-shadow: 0 0 0 3px rgba(45,106,45,0.15) !important;
    }}
    .stTextInput input {{
        color: {TEXT_PRIMARY} !important;
    }}
    .stTextInput input::placeholder {{
        color: #9a9a9a !important;
    }}
    .stTextInput label {{
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #2d2d2d !important;
    }}

    /* -- Text area -- */
    .stTextArea textarea {{
        background-color: {NAVY_CARD} !important;
        border: 1.5px solid {BORDER_LIGHT} !important;
        border-radius: 8px !important;
        color: {TEXT_PRIMARY} !important;
    }}
    .stTextArea textarea:focus {{
        border-color: {GREEN} !important;
        box-shadow: 0 0 0 3px rgba(45,106,45,0.15) !important;
    }}
    .stTextArea textarea::placeholder {{
        color: #9a9a9a !important;
    }}
    .stTextArea label {{
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #2d2d2d !important;
    }}

    /* -- Slider -- */
    .stSlider label {{
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #2d2d2d !important;
    }}

    /* -- Multiselect -- */
    .stMultiSelect [data-baseweb="tag"] {{
        background-color: {GREEN} !important;
        color: white !important;
    }}

    /* -- Progress bar -- */
    .stProgress > div > div {{
        background-color: {BORDER} !important;
    }}
    .stProgress > div > div > div {{
        background-color: {GREEN} !important;
    }}

    /* -- Containers with border -- */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        border-color: {BORDER} !important;
        border-radius: 10px !important;
        background-color: {NAVY_CARD} !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}

    /* -- Hide deploy button -- */
    .stDeployButton {{ display: none !important; }}
    [data-testid="stToolbar"] .stDeployButton {{ display: none !important; }}

    /* -- Plotly chart containers -- */
    .stPlotlyChart {{
        background-color: transparent !important;
    }}

    /* -- Scrollbar -- */
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: {NAVY}; }}
    ::-webkit-scrollbar-thumb {{ background: #B0C8B0; border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #8AAD8A; }}
</style>
"""


def apply_styles(extra_css: str = ""):
    """Inject shared CSS into the page. Call before render_nav()."""
    if extra_css:
        css = SHARED_CSS.replace("</style>", f"    {extra_css}\n</style>")
    else:
        css = SHARED_CSS
    st.markdown(css, unsafe_allow_html=True)

    # Set Plotly default template globally -- all charts inherit light theme
    try:
        import plotly.io as pio
        import plotly.graph_objects as go
        if "hfm" not in pio.templates:
            pio.templates["hfm"] = go.layout.Template(
                layout=go.Layout(**plotly_light_template())
            )
        pio.templates.default = "hfm"
    except ImportError:
        pass


def glass_card(content_html: str, border_color: str = "", min_height: str = ""):
    """Return HTML for a clean card."""
    border = f"border-top: 3px solid {border_color};" if border_color else ""
    height = f"min-height: {min_height};" if min_height else ""
    return (
        f"<div style='background:{NAVY_CARD};"
        f"border:1px solid {BORDER};border-radius:10px;padding:20px 24px;"
        f"{border}{height}box-shadow:0 1px 3px rgba(0,0,0,0.08);'>"
        f"{content_html}</div>"
    )


def plotly_light_template():
    """Return a dict of Plotly layout overrides for the modern light theme.

    Usage: fig.update_layout(**plotly_light_template())
    """
    return dict(
        paper_bgcolor=NAVY_CARD,
        plot_bgcolor=NAVY_CARD,
        font=dict(
            family="-apple-system, BlinkMacSystemFont, 'Segoe UI', "
                   "Roboto, Oxygen, sans-serif",
            color=TEXT_PRIMARY,
            size=13,
        ),
        title_font=dict(
            family="-apple-system, BlinkMacSystemFont, 'Segoe UI', "
                   "Roboto, Oxygen, sans-serif",
            color=TEXT_PRIMARY,
            size=16,
        ),
        xaxis=dict(
            gridcolor="#F0F0F0",
            linecolor=BORDER,
            zerolinecolor="#E0E0E0",
            tickfont=dict(color=TEXT_SECONDARY, size=13),
        ),
        yaxis=dict(
            gridcolor="#F0F0F0",
            linecolor=BORDER,
            zerolinecolor="#E0E0E0",
            tickfont=dict(color=TEXT_SECONDARY, size=13),
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0)",
            font=dict(color=TEXT_PRIMARY, size=12),
        ),
        colorway=[
            GREEN, BLUE, GOLD, PURPLE, ORANGE,
            CYAN, PINK, RED, "#65A30D", "#6366F1",
        ],
        margin=dict(t=40, r=20, b=40, l=60),
        hoverlabel=dict(
            bgcolor=NAVY_CARD,
            font_color=TEXT_PRIMARY,
            bordercolor=BORDER,
        ),
    )


# Keep old name as alias for any direct callers
plotly_dark_template = plotly_light_template


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
                    f"<div style='font-size:12px;color:{TEXT_MUTED};"
                    f"margin-top:6px;font-style:italic;'>"
                    f"{strategy_context}</div>"
                )
            st.markdown(
                f"<div style='margin:8px 0 4px;'>{badges}{ctx_html}</div>",
                unsafe_allow_html=True,
            )
        except ImportError:
            pass

    st.caption("Living the Greater Goodness \u2014 Harris Farm Markets")
    st.markdown("---")


def render_footer(name: str, extra: str = "", user=None):
    """Render standard dashboard footer: divider + flag button + caption + logout."""
    parts = [name, "Harris Farm Markets \u2014 Living the Greater Goodness"]
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
    st.caption("The Hub \u00b7 Harris Farm Markets \u00b7 Built by our people, powered by AI, grown with purpose.")
