"""
Customer Hub — Shared Components
Metric cards, section headers, insight callouts, and CSS for the Customer Hub.
"""

import streamlit as st

# ── Brand palette ────────────────────────────────────────────────────────────

HFM_GREEN = "#2ECC71"

PALETTE = {
    "green": "#2d8659",
    "dark_blue": "#1e3a8a",
    "purple": "#7c3aed",
    "teal": "#0d9488",
    "amber": "#d97706",
    "red": "#dc2626",
    "grey": "#6b7280",
}

SEGMENT_COLORS = {
    "Champion": "#059669",
    "High-Value": "#0d9488",
    "Regular": "#3b82f6",
    "Occasional": "#f59e0b",
    "Lapsed": "#ef4444",
}

HEALTH_COLOURS = {
    "Accelerating": "#2ECC71",
    "Growing": "#65a30d",
    "Stable": "#d97706",
    "Softening": "#ea580c",
    "Declining": "#dc2626",
    "New": "#9ca3af",
}

HEALTH_ORDER = ["Accelerating", "Growing", "Stable", "Softening", "Declining", "New"]

GRADE_COLOURS = {
    "A": "#2ECC71",
    "B": "#65a30d",
    "C": "#d97706",
    "D": "#ea580c",
    "F": "#dc2626",
}

OPP_COLOURS = {
    "Stronghold": "#2ECC71",
    "Growth Opportunity": "#2563eb",
    "Basket Opportunity": "#d97706",
    "Retention Risk": "#dc2626",
    "Monitor": "#9ca3af",
}

STATE_COLOURS = {"NSW": "#2ECC71", "QLD": "#7c3aed", "ACT": "#d97706"}


# ── Reusable UI components ───────────────────────────────────────────────────

def section_header(title, subtitle="", icon=""):
    """Render a styled section header with optional subtitle."""
    if icon:
        title = "{} {}".format(icon, title)
    st.markdown(
        "<h2 style='margin-bottom:0;'>{}</h2>".format(title),
        unsafe_allow_html=True,
    )
    if subtitle:
        st.caption(subtitle)


def insight_callout(text, style="info"):
    """Render a storytelling insight box. style: info | success | warning."""
    colour_map = {
        "info": ("#eff6ff", "#1e40af", "#dbeafe"),
        "success": ("#f0fdf4", "#166534", "#dcfce7"),
        "warning": ("#fffbeb", "#92400e", "#fef3c7"),
    }
    bg, fg, border = colour_map.get(style, colour_map["info"])
    st.markdown(
        "<div style='background:{bg};color:{fg};border-left:4px solid {fg};"
        "padding:12px 16px;border-radius:6px;margin:8px 0 16px 0;"
        "font-size:0.95rem;'>{text}</div>".format(
            bg=bg, fg=fg, text=text
        ),
        unsafe_allow_html=True,
    )


def one_thing_box(text):
    """Render a 'One Thing to Remember' callout."""
    st.markdown(
        "<div style='background:linear-gradient(135deg,#f0fdf4,#dcfce7);"
        "border-left:4px solid #2ECC71;padding:14px 18px;border-radius:8px;"
        "margin:12px 0;'>"
        "<div style='font-weight:700;color:#166534;margin-bottom:4px;'>"
        "One Thing to Remember</div>"
        "<div style='color:#15803d;font-size:0.95rem;'>{}</div>"
        "</div>".format(text),
        unsafe_allow_html=True,
    )


def metric_row(metrics):
    """Render a row of metrics. metrics: list of (label, value, delta) tuples."""
    cols = st.columns(len(metrics))
    for i, m in enumerate(metrics):
        label = m[0]
        value = m[1]
        delta = m[2] if len(m) > 2 else None
        if delta is not None:
            cols[i].metric(label, value, delta)
        else:
            cols[i].metric(label, value)


def fmt_period(p):
    """Format period int 202507 → '2025-07'."""
    s = str(p)
    return "{}-{}".format(s[:4], s[4:])


def store_display_name(full_name):
    """'10 - HFM Pennant Hills' -> 'Pennant Hills'."""
    if " - HFM " in full_name:
        return full_name.split(" - HFM ", 1)[1]
    if " - " in full_name:
        return full_name.split(" - ", 1)[1]
    return full_name


def safe_int(pc, default=0):
    """Safely convert a postcode to int."""
    try:
        return int(pc)
    except (ValueError, TypeError):
        return default


STATE_RANGES = {
    "NSW": lambda pc: 2000 <= safe_int(pc) <= 2999,
    "QLD": lambda pc: 4000 <= safe_int(pc) <= 4999,
    "ACT": lambda pc: 2600 <= safe_int(pc) <= 2618 or safe_int(pc) in range(2900, 2915),
}


def filter_by_state(df, state, postcode_col="postcode"):
    """Filter DataFrame by state based on postcode ranges."""
    if state == "All":
        return df
    fn = STATE_RANGES.get(state)
    if fn and not df.empty:
        return df[df[postcode_col].apply(fn)]
    return df
