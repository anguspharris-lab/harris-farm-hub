"""
Customer Hub — Shared Components
Metric cards, section headers, insight callouts, and CSS for the Customer Hub.
"""

import streamlit as st

# ── Brand palette ────────────────────────────────────────────────────────────

HFM_GREEN = "#2D6A2D"

PALETTE = {
    "green": "#2D6A2D",
    "dark_blue": "#1565C0",
    "purple": "#7c3aed",
    "teal": "#0891B2",
    "amber": "#C8971F",
    "red": "#C0392B",
    "grey": "#717171",
}

SEGMENT_COLORS = {
    "Champion": "#2D6A2D",
    "High-Value": "#0891B2",
    "Regular": "#1565C0",
    "Occasional": "#C8971F",
    "Lapsed": "#C0392B",
}

HEALTH_COLOURS = {
    "Accelerating": "#2D6A2D",
    "Growing": "#65a30d",
    "Stable": "#C8971F",
    "Softening": "#C8971F",
    "Declining": "#C0392B",
    "New": "#9ca3af",
}

HEALTH_ORDER = ["Accelerating", "Growing", "Stable", "Softening", "Declining", "New"]

GRADE_COLOURS = {
    "A": "#2D6A2D",
    "B": "#65a30d",
    "C": "#C8971F",
    "D": "#C8971F",
    "F": "#C0392B",
}

OPP_COLOURS = {
    "Stronghold": "#2D6A2D",
    "Growth Opportunity": "#1565C0",
    "Basket Opportunity": "#C8971F",
    "Retention Risk": "#C0392B",
    "Monitor": "#9ca3af",
}

STATE_COLOURS = {"NSW": "#2D6A2D", "QLD": "#7c3aed", "ACT": "#C8971F"}


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
        "info": ("rgba(21,101,192,0.04)", "#1565C0", "rgba(21,101,192,0.08)"),
        "success": ("rgba(45,106,45,0.04)", "#1B4D1B", "rgba(45,106,45,0.08)"),
        "warning": ("rgba(200,151,31,0.04)", "#C8971F", "rgba(200,151,31,0.08)"),
    }
    bg, fg, border = colour_map.get(style, colour_map["info"])
    st.markdown(
        "<div style='background:{bg};color:{fg};border-left:4px solid {fg};"
        "padding:12px 16px;border-radius:6px;margin:8px 0 16px 0;"
        "font-size:15px;'>{text}</div>".format(
            bg=bg, fg=fg, text=text
        ),
        unsafe_allow_html=True,
    )


def one_thing_box(text):
    """Render a 'One Thing to Remember' callout."""
    st.markdown(
        "<div style='background:linear-gradient(135deg,rgba(45,106,45,0.04),rgba(45,106,45,0.08));"
        "border-left:4px solid #2D6A2D;padding:14px 18px;border-radius:8px;"
        "margin:12px 0;'>"
        "<div style='font-weight:700;color:#1B4D1B;margin-bottom:4px;'>"
        "One Thing to Remember</div>"
        "<div style='color:#235522;font-size:15px;'>{}</div>"
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
