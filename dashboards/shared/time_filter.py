"""
Harris Farm Hub — Shared Time Dimension Filter
Reusable sidebar component for time-based filtering:
Hour of Day, Season, Fiscal Quarter, Fiscal Month.
Used by all transaction dashboards (Store Ops, Product Intel, Revenue Bridge, Buying Hub).
"""

import sys
from pathlib import Path
from datetime import date, timedelta

import streamlit as st

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from fiscal_calendar import (
    get_current_fiscal_period,
    get_fy_date_range,
    get_fiscal_weeks,
    get_fiscal_months,
    get_fiscal_quarters,
)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

HOUR_PRESETS = {
    "All Hours": None,
    "Early Morning (6-9)": (6, 9),
    "Morning (9-12)": (9, 12),
    "Lunch (12-14)": (12, 14),
    "Afternoon (14-17)": (14, 17),
    "Evening (17-20)": (17, 20),
    "Late (20-22)": (20, 22),
}

ALL_SEASONS = ["Summer", "Autumn", "Winter", "Spring"]

MONTH_TO_QUARTER = {
    1: 1, 2: 1, 3: 1,
    4: 2, 5: 2, 6: 2,
    7: 3, 8: 3, 9: 3,
    10: 4, 11: 4, 12: 4,
}


# ---------------------------------------------------------------------------
# MAIN RENDER FUNCTION
# ---------------------------------------------------------------------------

def render_time_filter(key_prefix="tf", fin_year=None):
    """Render time-based dimension filters in the sidebar.

    Args:
        key_prefix: Unique prefix for widget keys.
        fin_year: Selected fiscal year (for quarter/month labels).

    Returns:
        dict with keys:
            day_of_week_names: always None (all days included)
            hour_start: int or None
            hour_end: int or None
            hour_preset: str label or None
            season_names: list of season names or None (None = all)
            quarter_nos: list of ints or None (None = all)
            month_nos: list of ints or None (None = all)
    """
    st.sidebar.markdown("### Time Filters")

    # ---- Hour of Day ----
    hour_start, hour_end, hour_preset = _render_hour_of_day(key_prefix)

    # ---- Season ----
    selected_seasons = _render_season(key_prefix)

    # ---- Fiscal Quarter ----
    selected_quarters = _render_quarter(key_prefix, fin_year)

    # ---- Fiscal Month ----
    selected_months = _render_month(key_prefix, fin_year, selected_quarters)

    st.sidebar.markdown("---")

    return {
        "day_of_week_names": None,
        "hour_start": hour_start,
        "hour_end": hour_end,
        "hour_preset": hour_preset,
        "season_names": selected_seasons,
        "quarter_nos": selected_quarters,
        "month_nos": selected_months,
    }


# ---------------------------------------------------------------------------
# HOUR OF DAY
# ---------------------------------------------------------------------------

def _render_hour_of_day(key_prefix):
    """Render Hour of Day radio preset selector."""
    hour_label = st.sidebar.radio(
        "Hour of Day",
        list(HOUR_PRESETS.keys()),
        index=0,
        key=f"{key_prefix}_hour",
        label_visibility="visible",
    )
    hour_range = HOUR_PRESETS[hour_label]
    if hour_range:
        return hour_range[0], hour_range[1], hour_label
    return None, None, None


# ---------------------------------------------------------------------------
# SEASON
# ---------------------------------------------------------------------------

def _render_season(key_prefix):
    """Render Season multi-select."""
    selected = st.sidebar.multiselect(
        "Season",
        options=ALL_SEASONS,
        default=ALL_SEASONS,
        key=f"{key_prefix}_season",
    )
    if len(selected) == 4 or len(selected) == 0:
        return None
    return selected


# ---------------------------------------------------------------------------
# FISCAL QUARTER
# ---------------------------------------------------------------------------

def _render_quarter(key_prefix, fin_year):
    """Render Fiscal Quarter multi-select."""
    if not fin_year:
        return None

    quarters = get_fiscal_quarters(fin_year)
    if not quarters:
        return None

    q_labels = {
        q["quarter_no"]: f"Q{q['quarter_no']} ({q['name']})"
        for q in quarters
    }
    all_q_nos = list(q_labels.keys())

    selected = st.sidebar.multiselect(
        "Fiscal Quarter",
        options=all_q_nos,
        default=all_q_nos,
        format_func=lambda x: q_labels.get(x, f"Q{x}"),
        key=f"{key_prefix}_quarter",
    )

    if len(selected) == 4 or len(selected) == 0:
        return None
    return selected


# ---------------------------------------------------------------------------
# FISCAL MONTH
# ---------------------------------------------------------------------------

def _render_month(key_prefix, fin_year, selected_quarters):
    """Render Fiscal Month multi-select, constrained by quarter selection."""
    if not fin_year:
        return None

    months = get_fiscal_months(fin_year)
    if not months:
        return None

    # Filter months by selected quarters
    if selected_quarters:
        available = [
            m for m in months
            if MONTH_TO_QUARTER.get(m["month_no"]) in selected_quarters
        ]
    else:
        available = months

    if not available:
        return None

    m_labels = {
        m["month_no"]: f"{m['short_name']} ({m['weeks']}w)"
        for m in available
    }
    all_m_nos = list(m_labels.keys())

    selected = st.sidebar.multiselect(
        "Fiscal Month",
        options=all_m_nos,
        default=all_m_nos,
        format_func=lambda x: m_labels.get(x, str(x)),
        key=f"{key_prefix}_month",
    )

    if len(selected) == len(all_m_nos) or len(selected) == 0:
        return None
    return selected


# ---------------------------------------------------------------------------
# QUICK PERIOD
# ---------------------------------------------------------------------------

def resolve_quick_period(mode):
    """Resolve a quick period shortcut to (start, end, label).

    Returns (None, None, None) if resolution fails.
    """
    current = get_current_fiscal_period()
    if not current or "error" in current:
        return None, None, None

    fy = current["fin_year"]
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    if mode == "Today":
        return today_str, tomorrow_str, f"Today ({today_str})"

    elif mode == "WTD":
        weeks = get_fiscal_weeks(fy)
        if weeks:
            w = next((w for w in weeks if w["week_no"] == current["week_no"]), None)
            if w:
                return w["start"], tomorrow_str, f"WTD - {current['week_name']}"
        return None, None, None

    elif mode == "MTD":
        months = get_fiscal_months(fy)
        if months:
            m = next((m for m in months if m["month_no"] == current["month_no"]), None)
            if m:
                return m["start"], tomorrow_str, f"MTD - {current['month_name']}"
        return None, None, None

    elif mode == "QTD":
        quarters = get_fiscal_quarters(fy)
        if quarters:
            q = next((q for q in quarters
                       if q["quarter_no"] == current["quarter_no"]), None)
            if q:
                return q["start"], tomorrow_str, \
                    f"QTD - Q{current['quarter_no']} FY{fy}"
        return None, None, None

    elif mode == "YTD":
        fy_start, _ = get_fy_date_range(fy)
        if fy_start:
            return fy_start, tomorrow_str, f"FY{fy} YTD"
        return None, None, None

    return None, None, None


def render_quick_period(key_prefix="qp"):
    """Render Quick Period radio in sidebar.

    Returns:
        tuple (start, end, label) or (None, None, None) if Fiscal Selector.
    """
    st.sidebar.markdown("### Quick Period")
    mode = st.sidebar.radio(
        "Select period",
        ["Fiscal Selector", "Today", "WTD", "MTD", "QTD", "YTD"],
        index=0,
        key=f"{key_prefix}_quick_period",
        label_visibility="collapsed",
    )

    if mode == "Fiscal Selector":
        return None, None, None

    return resolve_quick_period(mode)


# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------

def time_filter_summary(tf):
    """Build a human-readable label for active time filters.

    Args:
        tf: dict returned by render_time_filter().

    Returns:
        str label like "Morning (9-12)" or None if no filter active.
    """
    parts = []

    if tf.get("hour_preset"):
        parts.append(tf["hour_preset"])

    seasons = tf.get("season_names")
    if seasons:
        parts.append(", ".join(seasons))

    q_nos = tf.get("quarter_nos")
    if q_nos:
        parts.append("Q" + "+Q".join(str(q) for q in q_nos))

    m_nos = tf.get("month_nos")
    if m_nos:
        parts.append(f"{len(m_nos)} months")

    return " | ".join(parts) if parts else None
