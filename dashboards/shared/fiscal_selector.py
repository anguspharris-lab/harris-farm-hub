"""
Harris Farm Hub — Shared Fiscal Period Selector
Reusable Streamlit component for fiscal period filtering across all dashboards.

Provides a consistent UI for selecting fiscal year, period type, and comparison mode.
Resolves all dates from the authoritative fiscal calendar parquet file.

Usage:
    from shared.fiscal_selector import render_fiscal_selector

    filters = render_fiscal_selector(
        key_prefix="main",
        show_comparison=True,
        show_store=True,
        store_names=STORE_NAMES,
        allowed_fys=[2024, 2025, 2026],
    )
    start_str = filters["start_date"]
    end_str = filters["end_date"]
    store_id = filters["store_id"]
"""

import sys
from datetime import date
from pathlib import Path

import streamlit as st

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from fiscal_calendar import (
    get_fiscal_years,
    get_fy_date_range,
    get_fiscal_months,
    get_fiscal_quarters,
    get_fiscal_weeks,
    get_current_fiscal_period,
    get_comparison_range,
    is_long_year,
)


def render_fiscal_selector(
    key_prefix="fiscal",
    show_comparison=False,
    show_store=False,
    store_names=None,
    allowed_fys=None,
    default_fy=None,
):
    """Render a fiscal period selector and return selected date range.

    Args:
        key_prefix: Unique prefix for Streamlit widget keys.
        show_comparison: Show comparison period selector.
        show_store: Show store filter selector.
        store_names: Dict of {store_id: store_name} for store filter.
        allowed_fys: List of allowed fiscal years (e.g., [2024, 2025, 2026]).
        default_fy: Default fiscal year. If None, uses current FY.

    Returns:
        dict with keys:
            start_date: str (YYYY-MM-DD)
            end_date: str (YYYY-MM-DD)
            fin_year: int
            period_type: str ("fy", "quarter", "month", "week", "custom")
            period_label: str (human-readable description)
            comparison: dict or None (start_date, end_date, label)
            store_id: str or None
            caveats: list of str
    """
    # Available fiscal years
    all_fys = get_fiscal_years()
    if allowed_fys:
        fys = [fy for fy in all_fys if fy in allowed_fys]
    else:
        fys = all_fys

    if not fys:
        st.error("No fiscal years available.")
        return _empty_result()

    # Default to current FY or last available
    if default_fy and default_fy in fys:
        default_idx = fys.index(default_fy)
    else:
        current = get_current_fiscal_period()
        current_fy = current.get("fin_year")
        if current_fy and current_fy in fys:
            default_idx = fys.index(current_fy)
        else:
            default_idx = len(fys) - 1

    # Period type options
    period_types = ["Full Year", "Year to Date", "Quarter", "Month", "Week", "Custom"]

    # --- Row 1: FY + Period Type ---
    col1, col2 = st.columns(2)

    with col1:
        selected_fy = st.selectbox(
            "Fiscal Year",
            fys,
            index=default_idx,
            format_func=lambda fy: f"FY{fy}",
            key=f"{key_prefix}_fy",
        )

    with col2:
        period_type = st.selectbox(
            "Period",
            period_types,
            index=1,  # Default: Year to Date
            key=f"{key_prefix}_period_type",
        )

    # --- Row 2: Period-specific selector ---
    caveats = []

    if period_type == "Full Year":
        start, end = get_fy_date_range(selected_fy)
        label = f"FY{selected_fy} (Full Year)"
        pt = "fy"

    elif period_type == "Year to Date":
        fy_start, fy_end = get_fy_date_range(selected_fy)
        today_str = date.today().strftime("%Y-%m-%d")
        # If today is past FY end, show full year
        if today_str >= fy_end:
            end = fy_end
        else:
            end = today_str
        start = fy_start
        current = get_current_fiscal_period()
        if current.get("fin_year") == selected_fy:
            label = f"FY{selected_fy} YTD ({current.get('month_name', '')} {current.get('week_name', '')})"
        else:
            label = f"FY{selected_fy} (Full Year)"
        pt = "fy"

    elif period_type == "Quarter":
        quarters = get_fiscal_quarters(selected_fy)
        if not quarters:
            st.warning(f"No quarter data for FY{selected_fy}")
            return _empty_result()

        q_options = {q["quarter_no"]: f"Q{q['quarter_no']} ({q['name']})" for q in quarters}
        selected_q = st.selectbox(
            "Quarter",
            list(q_options.keys()),
            format_func=lambda x: q_options[x],
            key=f"{key_prefix}_quarter",
        )
        q = next(q for q in quarters if q["quarter_no"] == selected_q)
        start, end = q["start"], q["end"]
        label = f"FY{selected_fy} Q{selected_q}"
        pt = "quarter"

    elif period_type == "Month":
        months = get_fiscal_months(selected_fy)
        if not months:
            st.warning(f"No month data for FY{selected_fy}")
            return _empty_result()

        m_options = {m["month_no"]: f"{m['name']} ({m['weeks']}w)" for m in months}
        selected_m = st.selectbox(
            "Month",
            list(m_options.keys()),
            format_func=lambda x: m_options[x],
            key=f"{key_prefix}_month",
        )
        m = next(m for m in months if m["month_no"] == selected_m)
        start, end = m["start"], m["end"]
        label = f"{m['name']} FY{selected_fy} ({m['weeks']}w)"
        pt = "month"

    elif period_type == "Week":
        weeks = get_fiscal_weeks(selected_fy)
        if not weeks:
            st.warning(f"No week data for FY{selected_fy}")
            return _empty_result()

        w_options = {w["week_no"]: f"{w['name']} ({w['start']})" for w in weeks}
        selected_w = st.selectbox(
            "Week",
            list(w_options.keys()),
            format_func=lambda x: w_options[x],
            key=f"{key_prefix}_week",
        )
        w = next(w for w in weeks if w["week_no"] == selected_w)
        start, end = w["start"], w["end"]
        label = f"{w['name']} FY{selected_fy}"
        pt = "week"

        if selected_w == 53:
            caveats.append("Week 53 only exists in 53-week years (FY2016, FY2022).")

    else:  # Custom
        fy_start, fy_end = get_fy_date_range(selected_fy)
        c1, c2 = st.columns(2)
        with c1:
            custom_start = st.date_input(
                "Start Date",
                value=date.fromisoformat(fy_start) if fy_start else date(2025, 7, 1),
                key=f"{key_prefix}_custom_start",
            )
        with c2:
            custom_end = st.date_input(
                "End Date",
                value=date.today(),
                key=f"{key_prefix}_custom_end",
            )
        if custom_start >= custom_end:
            st.error("Start date must be before end date.")
            return _empty_result()
        start = custom_start.strftime("%Y-%m-%d")
        end = custom_end.strftime("%Y-%m-%d")
        label = f"Custom: {start} to {end}"
        pt = "custom"

    # 53-week year caveat
    if is_long_year(selected_fy):
        caveats.append(f"FY{selected_fy} is a 53-week year (371 days).")

    # --- Row 3: Store filter (optional) ---
    store_id = None
    if show_store and store_names:
        store_opts = {"": "All Stores (Network)"}
        store_opts.update({
            sid: f"{name} ({sid})" for sid, name in sorted(
                store_names.items(), key=lambda x: x[1])
        })
        selected_store = st.selectbox(
            "Store",
            list(store_opts.keys()),
            format_func=lambda x: store_opts[x],
            key=f"{key_prefix}_store",
        )
        store_id = selected_store if selected_store else None

    # --- Row 4: Comparison (optional) ---
    comparison = None
    if show_comparison:
        compare_options = ["None", "vs Prior Year", "vs Prior Period"]
        compare_mode = st.selectbox(
            "Compare",
            compare_options,
            key=f"{key_prefix}_compare",
        )

        if compare_mode == "vs Prior Year" and pt != "custom":
            if pt == "fy":
                comp = get_comparison_range("fy", None, selected_fy)
            elif pt == "quarter":
                comp = get_comparison_range("quarter", selected_q, selected_fy)
            elif pt == "month":
                comp = get_comparison_range("month", selected_m, selected_fy)
            elif pt == "week":
                comp = get_comparison_range("week", selected_w, selected_fy)
            else:
                comp = {"current": None, "prior": None, "caveats": []}

            if comp.get("prior"):
                comparison = comp["prior"]
            caveats.extend(comp.get("caveats", []))

        elif compare_mode == "vs Prior Period":
            # Prior period = the period immediately before the current one
            if pt == "quarter" and selected_q > 1:
                prev_q = next((q for q in quarters if q["quarter_no"] == selected_q - 1), None)
                if prev_q:
                    comparison = {"start": prev_q["start"], "end": prev_q["end"],
                                  "label": f"Q{selected_q - 1} FY{selected_fy}"}
            elif pt == "month" and selected_m > 1:
                prev_m = next((m for m in months if m["month_no"] == selected_m - 1), None)
                if prev_m:
                    comparison = {"start": prev_m["start"], "end": prev_m["end"],
                                  "label": f"{prev_m['name']} FY{selected_fy}"}
            elif pt == "week" and selected_w > 1:
                prev_w = next((w for w in weeks if w["week_no"] == selected_w - 1), None)
                if prev_w:
                    comparison = {"start": prev_w["start"], "end": prev_w["end"],
                                  "label": f"{prev_w['name']} FY{selected_fy}"}

    # --- Summary line ---
    store_label = store_names.get(store_id, "All Network") if store_id and store_names else "All Network"
    st.markdown(f"**Showing:** {store_label} | {label} | {start} to {end}")

    if caveats:
        for caveat in caveats:
            st.caption(f"Note: {caveat}")

    return {
        "start_date": start,
        "end_date": end,
        "fin_year": selected_fy,
        "period_type": pt,
        "period_label": label,
        "comparison": comparison,
        "store_id": store_id,
        "caveats": caveats,
    }


def _empty_result():
    """Return an empty result dict when the selector can't resolve dates."""
    return {
        "start_date": None,
        "end_date": None,
        "fin_year": None,
        "period_type": None,
        "period_label": None,
        "comparison": None,
        "store_id": None,
        "caveats": ["Unable to resolve fiscal period."],
    }
