"""
Harris Farm Hub -- Store Network Dashboard (v2)
Integrates Phase 1 (CBAS), Phase 2 (ROC), and Phase 3 (Market Share) data
into a unified 8-tab strategic view of the Harris Farm store network.

Data sources:
  - CBAS Store Network Analysis (Feb 2026) via shared.whitespace_data
  - ROC analysis (estimated GPM, capital returns) via shared.property_intel
  - Market share catchments & quadrant matrix via shared.property_intel
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from typing import Optional

from shared.styles import render_header, render_footer, glass_card
from shared.property_intel import (
    get_roc_df,
    get_roc_summary,
    get_department_gp,
    get_format_analysis,
    get_fix_candidates,
    get_store_catchments,
    get_quadrant_matrix,
    get_cannibalisation,
    get_network_scorecard,
    get_enriched_scorecard,
    CLASSIFICATION_COLOURS,
    FORMAT_COLOURS,
    QUADRANT_COLOURS,
)
from shared.whitespace_data import (
    get_stores_df,
    get_ideal_profile,
    get_opportunities_df,
    get_meta,
    TIER_COLOURS,
)

# ── Common layout helpers ─────────────────────────────────────────────────────

_DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#FFFFFF", family="Trebuchet MS, sans-serif"),
)

_GRID = dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)")
_NO_GRID = dict(showgrid=False)


def _safe_pct(val, decimals: int = 1) -> str:
    """Format a value as percentage string, handling None/NaN."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    try:
        return f"{float(val):.{decimals}f}%"
    except (ValueError, TypeError):
        return "N/A"


def _safe_dollar(val, suffix: str = "") -> str:
    """Format a numeric value as dollar string."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    try:
        return f"${float(val):,.0f}{suffix}"
    except (ValueError, TypeError):
        return "N/A"


def _safe_float(val, fmt: str = ".2f") -> str:
    """Format a float with fallback."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    try:
        return f"{float(val):{fmt}}"
    except (ValueError, TypeError):
        return "N/A"


def _colour_for_roc(roc_val) -> str:
    """Return brand colour based on ROC value."""
    try:
        v = float(roc_val)
    except (ValueError, TypeError):
        return "#6B7280"
    if v >= 1.0:
        return "#2ECC71"
    elif v >= 0.7:
        return "#d97706"
    else:
        return "#dc2626"


def _placeholder(message: str = "Data not yet available."):
    """Show a styled placeholder when data is missing."""
    st.info(message + " This section will populate once the required data files are generated.")


# ── Auth & Header ─────────────────────────────────────────────────────────────

user = st.session_state.get("auth_user")

render_header(
    "Store Network",
    "Capital efficiency, market position, and strategic classification for every Harris Farm store",
    goals=["G1", "G3"],
    strategy_context=(
        "Understanding what makes our stores succeed -- revenue per sqm, GPM return on capital, "
        "catchment share -- drives the 'Fewer, Bigger, Better' strategy."
    ),
)
st.caption(
    "Sources: CBAS Network Analysis (Feb 2026) | Internal financials (ESTIMATED GPM) | "
    "CBAS Market Share (modelled). Capital assumptions clearly labelled."
)

# ── Load all data ─────────────────────────────────────────────────────────────

roc_df = get_roc_df()
roc_summary = get_roc_summary()
dept_gp = get_department_gp()
format_data = get_format_analysis()
fix_data = get_fix_candidates()
catchments_df = get_store_catchments()
quadrant_data = get_quadrant_matrix()
cannibalisation_data = get_cannibalisation()
scorecard_df = get_network_scorecard()
cbas_stores = get_stores_df()
cbas_meta = get_meta()

has_roc = not roc_df.empty
has_catchments = not catchments_df.empty
has_scorecard = not scorecard_df.empty

# ── Helper functions ──────────────────────────────────────────────────────────

def _build_format_table_inline(df: pd.DataFrame):
    """Build format comparison from ROC dataframe when JSON is unavailable."""
    if "format_segment" not in df.columns:
        st.info("Format segmentation data not available.")
        return

    needed_cols = ["format_segment", "retail_sqm", "revenue", "gpm_roc_primary_4k"]
    available = [c for c in needed_cols if c in df.columns]
    if len(available) < 2:
        st.info("Insufficient data for format comparison.")
        return

    grouped = df.groupby("format_segment").agg(
        Stores=("short_name", "count"),
        Avg_SQM=("retail_sqm", "mean"),
        Avg_Revenue=("revenue", "mean"),
        Avg_GPM_ROC=("gpm_roc_primary_4k", "mean"),
    ).reset_index()
    grouped.columns = ["Format", "Stores", "Avg SQM", "Avg Revenue ($M)", "Avg GPM ROC (est.)"]
    grouped["Avg SQM"] = grouped["Avg SQM"].round(0)
    rev_col = "Avg Revenue ($M)"
    if rev_col in grouped.columns:
        grouped[rev_col] = (grouped[rev_col] / 1_000_000).round(1)
    grouped["Avg GPM ROC (est.)"] = grouped["Avg GPM ROC (est.)"].round(2)
    st.dataframe(grouped, use_container_width=True, hide_index=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_exec, tab_roc, tab_ms, tab_matrix, tab_cannibal, tab_score, tab_fix, tab_gaps = st.tabs([
    "Executive Summary",
    "ROC Analysis",
    "Market Share",
    "2x2 Matrix",
    "Cannibalisation",
    "Network Scorecard",
    "Fix Candidates",
    "Data Gaps",
])


# =============================================================================
# TAB 1: EXECUTIVE SUMMARY
# =============================================================================

with tab_exec:
    if not has_roc:
        _placeholder("ROC data not loaded.")
    else:
        # ── KPI row ──────────────────────────────────────────────────────
        totals = roc_summary.get("network_totals", {})
        store_count = len(roc_df)
        network_rev = totals.get("total_revenue_m", roc_df["revenue"].sum() / 1_000_000 if "revenue" in roc_df.columns else 0)
        avg_gpm_roc = totals.get("avg_gpm_roc_4k", roc_df["gpm_roc_primary_4k"].mean() if "gpm_roc_primary_4k" in roc_df.columns else 0)
        avg_gpm_pct = totals.get("avg_gpm_pct", roc_df["gpm_pct"].mean() if "gpm_pct" in roc_df.columns else 0)

        # Format split
        format_counts = roc_df["format_segment"].value_counts() if "format_segment" in roc_df.columns else pd.Series(dtype=int)
        format_str = " / ".join(
            f"{count} {fmt}" for fmt, count in format_counts.items()
        ) if not format_counts.empty else "N/A"

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Active Stores", store_count)
        c2.metric("Network Revenue", f"${network_rev:.0f}M" if isinstance(network_rev, (int, float)) else _safe_dollar(network_rev, "M"))
        c3.metric("Avg GPM ROC (est.)", f"{avg_gpm_roc:.2f}x" if isinstance(avg_gpm_roc, (int, float)) else "N/A")
        c4.metric("Network GPM%", _safe_pct(avg_gpm_pct))
        c5.metric("Format Split", format_str)

        st.markdown("---")

        # ── Top 3 / Bottom 3 by GPM ROC ─────────────────────────────────
        st.subheader("Top 3 & Bottom 3 Stores by GPM ROC (ESTIMATED)")

        roc_sorted = roc_df.dropna(subset=["gpm_roc_primary_4k"]).sort_values(
            "gpm_roc_primary_4k", ascending=False
        )

        top3 = roc_sorted.head(3)
        bot3 = roc_sorted.tail(3).sort_values("gpm_roc_primary_4k", ascending=True)

        col_top, col_bot = st.columns(2)

        with col_top:
            st.markdown("**Top Performers**")
            for _, row in top3.iterrows():
                colour = _colour_for_roc(row["gpm_roc_primary_4k"])
                name = row.get("short_name", "Unknown")
                roc_val = row["gpm_roc_primary_4k"]
                fmt = row.get("format_segment", "")
                sqm = row.get("retail_sqm", 0)
                st.markdown(
                    glass_card(
                        f"<span style='color:{colour};font-size:1.6em;font-weight:700;'>"
                        f"{roc_val:.2f}x</span>"
                        f"<span style='color:#FFFFFF;font-size:1.1em;margin-left:12px;'>"
                        f"{name}</span>"
                        f"<br><span style='color:#8899AA;font-size:0.85em;'>"
                        f"{fmt} | {sqm:,.0f} sqm</span>",
                        border_color=colour,
                    ),
                    unsafe_allow_html=True,
                )

        with col_bot:
            st.markdown("**Needs Attention**")
            for _, row in bot3.iterrows():
                colour = _colour_for_roc(row["gpm_roc_primary_4k"])
                name = row.get("short_name", "Unknown")
                roc_val = row["gpm_roc_primary_4k"]
                fmt = row.get("format_segment", "")
                sqm = row.get("retail_sqm", 0)
                st.markdown(
                    glass_card(
                        f"<span style='color:{colour};font-size:1.6em;font-weight:700;'>"
                        f"{roc_val:.2f}x</span>"
                        f"<span style='color:#FFFFFF;font-size:1.1em;margin-left:12px;'>"
                        f"{name}</span>"
                        f"<br><span style='color:#8899AA;font-size:0.85em;'>"
                        f"{fmt} | {sqm:,.0f} sqm</span>",
                        border_color=colour,
                    ),
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # ── Format comparison table ──────────────────────────────────────
        st.subheader("Format Comparison (ESTIMATED)")

        if format_data:
            fmt_rows = format_data.get("formats", [])
            if fmt_rows:
                fmt_df = pd.DataFrame(fmt_rows)
                st.dataframe(fmt_df, use_container_width=True, hide_index=True)
            else:
                # Build from ROC df
                _build_format_table_inline(roc_df)
        else:
            _build_format_table_inline(roc_df)

        # ── Key insight callout ──────────────────────────────────────────
        st.markdown(
            glass_card(
                "<span style='color:#2ECC71;font-weight:700;font-size:1.1em;'>"
                "Key Insight</span><br>"
                "<span style='color:#FFFFFF;'>"
                "Express format (&lt;1,200 sqm) averages ~1.17x GPM ROC -- "
                "1.8x more capital-efficient than Large format (0.66x). "
                "Smaller stores generate higher returns per dollar of invested capital."
                "</span>",
                border_color="#2ECC71",
            ),
            unsafe_allow_html=True,
        )

        st.caption(
            "GPM = Gross Product Margin (excludes transport & packaging). "
            "Capital estimated at $4K/sqm. All ROC figures are ESTIMATES."
        )


# =============================================================================
# TAB 2: ROC ANALYSIS
# =============================================================================

with tab_roc:
    if not has_roc:
        _placeholder("ROC data not loaded.")
    else:
        st.info(
            "All ROC values are ESTIMATED. GPM is Gross Product Margin (excludes transport "
            "& packaging). Capital is estimated using industry benchmarks ($4K/sqm primary assumption)."
        )

        # ── Horizontal bar: all stores by GPM ROC ────────────────────────
        st.subheader("GPM Return on Capital by Store (ESTIMATED)")

        bar_df = roc_df.dropna(subset=["gpm_roc_primary_4k"]).sort_values(
            "gpm_roc_primary_4k", ascending=True
        ).copy()

        if "format_segment" in bar_df.columns:
            fig_bar = px.bar(
                bar_df,
                x="gpm_roc_primary_4k",
                y="short_name",
                orientation="h",
                color="format_segment",
                color_discrete_map=FORMAT_COLOURS,
                labels={
                    "gpm_roc_primary_4k": "GPM ROC (est.) at $4K/sqm",
                    "short_name": "",
                    "format_segment": "Format",
                },
            )
        else:
            fig_bar = px.bar(
                bar_df,
                x="gpm_roc_primary_4k",
                y="short_name",
                orientation="h",
                color="gpm_roc_primary_4k",
                color_continuous_scale=["#dc2626", "#d97706", "#2ECC71"],
                labels={
                    "gpm_roc_primary_4k": "GPM ROC (est.) at $4K/sqm",
                    "short_name": "",
                },
            )

        # Add 1.0x reference line
        fig_bar.add_vline(
            x=1.0, line_dash="dash", line_color="#FFFFFF",
            annotation_text="1.0x breakeven",
            annotation_font_color="#FFFFFF",
        )
        fig_bar.update_layout(
            height=max(500, len(bar_df) * 24),
            margin=dict(l=0, r=20, t=30, b=40),
            **_DARK_LAYOUT,
            xaxis=dict(**_GRID, title="GPM ROC (est.)"),
            yaxis=dict(**_NO_GRID, title=""),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        # ── Sensitivity table ────────────────────────────────────────────
        st.subheader("Capital Sensitivity Analysis (ESTIMATED)")
        st.caption(
            "How GPM ROC changes under different capital-per-sqm assumptions. "
            "All three columns are estimates."
        )

        sens_cols = []
        for cost_label in ["3k", "4k", "5k"]:
            col_name = f"gpm_roc_primary_{cost_label}"
            if col_name in roc_df.columns:
                sens_cols.append(col_name)

        if sens_cols:
            sens_df = roc_df[["short_name", "format_segment", "retail_sqm"] + sens_cols].copy()
            rename_map = {"short_name": "Store", "format_segment": "Format", "retail_sqm": "SQM"}
            for c in sens_cols:
                cost = c.split("_")[-1].upper().replace("K", "K")
                rename_map[c] = f"ROC @ ${cost}/sqm"
            sens_df = sens_df.rename(columns=rename_map)
            sens_df = sens_df.sort_values(
                sens_df.columns[3] if len(sens_df.columns) > 3 else "Store",
                ascending=False,
            )
            # Round ROC columns
            for col in sens_df.columns:
                if col.startswith("ROC"):
                    sens_df[col] = sens_df[col].round(2)
            st.dataframe(sens_df, use_container_width=True, hide_index=True, height=500)
        else:
            st.info("Sensitivity columns not found. Only primary $4K/sqm assumption available.")

        st.markdown("---")

        # ── Scatter: Rev/sqm vs GPM ROC ─────────────────────────────────
        st.subheader("Revenue Density vs Capital Return (ESTIMATED)")

        if "retail_sqm" in roc_df.columns and "revenue" in roc_df.columns:
            scatter_df = roc_df.dropna(subset=["gpm_roc_primary_4k", "retail_sqm", "revenue"]).copy()
            scatter_df["rev_per_sqm"] = scatter_df["revenue"] / scatter_df["retail_sqm"]
            # Ensure size column is clean numeric
            scatter_df["retail_sqm_size"] = pd.to_numeric(
                scatter_df["retail_sqm"], errors="coerce"
            ).fillna(0).clip(lower=0)

            fig_scatter = px.scatter(
                scatter_df,
                x="rev_per_sqm",
                y="gpm_roc_primary_4k",
                size="retail_sqm_size",
                color="format_segment" if "format_segment" in scatter_df.columns else None,
                color_discrete_map=FORMAT_COLOURS,
                text="short_name",
                labels={
                    "rev_per_sqm": "Revenue per SQM ($)",
                    "gpm_roc_primary_4k": "GPM ROC (est.)",
                    "retail_sqm_size": "Retail SQM",
                    "format_segment": "Format",
                },
                size_max=40,
            )
            fig_scatter.update_traces(textposition="top center", textfont_size=10)
            fig_scatter.add_hline(
                y=1.0, line_dash="dash", line_color="rgba(255,255,255,0.4)",
                annotation_text="1.0x breakeven",
                annotation_font_color="#FFFFFF",
            )
            fig_scatter.update_layout(
                height=550,
                **_DARK_LAYOUT,
                xaxis=dict(**_GRID, title="Revenue per SQM ($)"),
                yaxis=dict(**_GRID, title="GPM ROC (est.)"),
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Revenue and/or sqm data not available for scatter plot.")

        st.markdown("---")

        # ── Department GP heatmap ────────────────────────────────────────
        st.subheader("Department GP Margin by Store (ESTIMATED)")

        if not dept_gp.empty:
            # Expect columns: store, department, gp_pct (or similar)
            dept_cols = dept_gp.columns.tolist()
            store_col = "store" if "store" in dept_cols else ("short_name" if "short_name" in dept_cols else None)
            dept_col = "department" if "department" in dept_cols else None
            gp_col = "gp_pct" if "gp_pct" in dept_cols else ("gpm_pct" if "gpm_pct" in dept_cols else None)

            if store_col and dept_col and gp_col:
                pivot = dept_gp.pivot_table(
                    index=store_col, columns=dept_col, values=gp_col, aggfunc="mean"
                )
                fig_heat = go.Figure(data=go.Heatmap(
                    z=pivot.values,
                    x=pivot.columns.tolist(),
                    y=pivot.index.tolist(),
                    colorscale=[[0, "#dc2626"], [0.5, "#d97706"], [1, "#2ECC71"]],
                    text=np.round(pivot.values, 1),
                    texttemplate="%{text}%",
                    hovertemplate="Store: %{y}<br>Dept: %{x}<br>GP: %{z:.1f}%<extra></extra>",
                ))
                fig_heat.update_layout(
                    height=max(500, len(pivot) * 22),
                    **_DARK_LAYOUT,
                    xaxis=dict(title="Department", tickangle=-45),
                    yaxis=dict(title=""),
                    margin=dict(l=0, r=20, t=30, b=80),
                )
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.dataframe(dept_gp, use_container_width=True, hide_index=True)
        else:
            _placeholder("Department GP data not yet available.")


# =============================================================================
# TAB 3: MARKET SHARE
# =============================================================================

with tab_ms:
    if not has_catchments:
        _placeholder(
            "Store catchment data not loaded. "
            "Generate market share catchment analysis to populate this tab."
        )
    else:
        st.subheader("Catchment Health by Store")
        st.caption(
            "Weighted average share % across each store's catchment postcodes. "
            "Share data from CBAS (modelled, not actual revenue)."
        )

        # ── Distance tier summary ────────────────────────────────────────
        st.markdown("#### Share by Distance Tier")

        tier_col_names = [
            "core_share_pct", "primary_share_pct", "secondary_share_pct",
            "extended_share_pct", "no_presence_share_pct",
        ]
        tier_labels = ["Core (0-3km)", "Primary (3-5km)", "Secondary (5-10km)",
                       "Extended (10-20km)", "No Presence (20km+)"]
        available_tiers = [c for c in tier_col_names if c in catchments_df.columns]

        if available_tiers:
            tier_avgs = []
            for col, label in zip(tier_col_names, tier_labels):
                if col in catchments_df.columns:
                    avg_val = catchments_df[col].mean()
                    tier_avgs.append({"Distance Tier": label, "Avg Share %": round(avg_val, 2)})
            if tier_avgs:
                st.dataframe(pd.DataFrame(tier_avgs), use_container_width=True, hide_index=True)
        else:
            # Show whatever columns are available
            st.caption("Distance tier breakdown not available. Showing overall catchment data.")

        st.markdown("---")

        # ── Catchment health ranking ─────────────────────────────────────
        st.markdown("#### Store Catchment Health Ranking")

        display_catch = catchments_df.copy()
        sort_col = "catchment_health_score" if "catchment_health_score" in display_catch.columns else "weighted_avg_share_pct"

        if sort_col in display_catch.columns:
            display_catch = display_catch.sort_values(sort_col, ascending=False)

        # Add trend arrows
        if "share_trend_pp" in display_catch.columns:
            trend_values = display_catch["share_trend_pp"]
            arrows = []
            for val in trend_values:
                if pd.isna(val):
                    arrows.append("--")
                elif val > 0.5:
                    arrows.append(f"+{val:.1f}pp")
                elif val < -0.5:
                    arrows.append(f"{val:.1f}pp")
                else:
                    arrows.append(f"{val:+.1f}pp")
            display_catch["Trend (YoY)"] = arrows

        catch_display_cols = []
        col_rename = {
            "store": "Store",
            "short_name": "Store",
            "weighted_avg_share_pct": "Wtd Avg Share %",
            "share_trend_pp": "Trend pp",
            "catchment_health_score": "Health Score",
            "Trend (YoY)": "Trend (YoY)",
        }
        for orig, renamed in col_rename.items():
            if orig in display_catch.columns:
                catch_display_cols.append(orig)

        if catch_display_cols:
            show_df = display_catch[catch_display_cols].rename(columns=col_rename)
            st.dataframe(show_df, use_container_width=True, hide_index=True, height=500)
        else:
            st.dataframe(display_catch, use_container_width=True, hide_index=True, height=500)

        st.markdown("---")

        # ── Top 5 growing / declining ────────────────────────────────────
        st.markdown("#### Share Trend: Top 5 Growing vs Top 5 Declining")

        if "share_trend_pp" in catchments_df.columns:
            trend_sorted = catchments_df.dropna(subset=["share_trend_pp"]).sort_values(
                "share_trend_pp", ascending=False
            )
            store_name_col = "store" if "store" in trend_sorted.columns else "short_name"

            col_grow, col_dec = st.columns(2)

            with col_grow:
                st.markdown("**Growing**")
                growing = trend_sorted.head(5)
                for _, row in growing.iterrows():
                    name = row.get(store_name_col, "Unknown")
                    trend_val = row["share_trend_pp"]
                    share_val = row.get("weighted_avg_share_pct", 0)
                    st.markdown(
                        glass_card(
                            f"<span style='color:#2ECC71;font-weight:700;'>"
                            f"+{trend_val:.1f}pp</span> "
                            f"<span style='color:#FFFFFF;'>{name}</span>"
                            f"<br><span style='color:#8899AA;font-size:0.85em;'>"
                            f"Current share: {share_val:.1f}%</span>",
                            border_color="#2ECC71",
                        ),
                        unsafe_allow_html=True,
                    )

            with col_dec:
                st.markdown("**Declining**")
                declining = trend_sorted.tail(5).sort_values("share_trend_pp", ascending=True)
                for _, row in declining.iterrows():
                    name = row.get(store_name_col, "Unknown")
                    trend_val = row["share_trend_pp"]
                    share_val = row.get("weighted_avg_share_pct", 0)
                    st.markdown(
                        glass_card(
                            f"<span style='color:#dc2626;font-weight:700;'>"
                            f"{trend_val:.1f}pp</span> "
                            f"<span style='color:#FFFFFF;'>{name}</span>"
                            f"<br><span style='color:#8899AA;font-size:0.85em;'>"
                            f"Current share: {share_val:.1f}%</span>",
                            border_color="#dc2626",
                        ),
                        unsafe_allow_html=True,
                    )
        else:
            st.info("Share trend data not available. YoY comparison requires two periods of data.")


# =============================================================================
# TAB 4: 2x2 MATRIX
# =============================================================================

with tab_matrix:
    st.subheader("Strategic Quadrant Matrix")
    st.caption(
        "X-axis = weighted catchment share (market position). "
        "Y-axis = GPM ROC at $4K/sqm (capital efficiency). "
        "Both axes use ESTIMATED data."
    )

    # We need both ROC and catchment data to build the matrix
    if not has_roc or not has_catchments:
        _placeholder(
            "Both ROC and catchment data are required for the 2x2 matrix. "
            "Missing: "
            + ("ROC " if not has_roc else "")
            + ("Catchments" if not has_catchments else "")
        )
    else:
        # Merge ROC with catchments
        store_col_catch = "store" if "store" in catchments_df.columns else "short_name"
        matrix_df = roc_df[["short_name", "gpm_roc_primary_4k", "revenue", "format_segment"]].copy()
        catch_merge = catchments_df[[store_col_catch, "weighted_avg_share_pct"]].copy()
        catch_merge = catch_merge.rename(columns={store_col_catch: "short_name"})
        matrix_df = matrix_df.merge(catch_merge, on="short_name", how="inner")
        matrix_df = matrix_df.dropna(subset=["gpm_roc_primary_4k", "weighted_avg_share_pct"])

        if matrix_df.empty:
            st.warning("No stores have both ROC and catchment share data.")
        else:
            # Calculate medians for quadrant dividers
            med_share = matrix_df["weighted_avg_share_pct"].median()
            med_roc = matrix_df["gpm_roc_primary_4k"].median()

            # Assign quadrants
            def assign_quadrant(row):
                high_share = row["weighted_avg_share_pct"] >= med_share
                high_roc = row["gpm_roc_primary_4k"] >= med_roc
                if high_share and high_roc:
                    return "Star"
                elif high_share and not high_roc:
                    return "Cash Cow"
                elif not high_share and high_roc:
                    return "Question Mark"
                else:
                    return "Fix or Exit"

            matrix_df["quadrant"] = matrix_df.apply(assign_quadrant, axis=1)

            # Ensure revenue size is clean
            matrix_df["rev_size"] = pd.to_numeric(
                matrix_df["revenue"], errors="coerce"
            ).fillna(0).clip(lower=0)

            # Build scatter
            fig_matrix = go.Figure()

            # Add quadrant background shapes
            x_min = matrix_df["weighted_avg_share_pct"].min() - 1
            x_max = matrix_df["weighted_avg_share_pct"].max() + 1
            y_min = matrix_df["gpm_roc_primary_4k"].min() - 0.1
            y_max = matrix_df["gpm_roc_primary_4k"].max() + 0.2

            # Quadrant shading
            shapes = [
                # Star (top-right) - green
                dict(type="rect", x0=med_share, x1=x_max, y0=med_roc, y1=y_max,
                     fillcolor="rgba(46,204,113,0.08)", line_width=0, layer="below"),
                # Cash Cow (bottom-right) - blue
                dict(type="rect", x0=med_share, x1=x_max, y0=y_min, y1=med_roc,
                     fillcolor="rgba(59,130,246,0.08)", line_width=0, layer="below"),
                # Question Mark (top-left) - amber
                dict(type="rect", x0=x_min, x1=med_share, y0=med_roc, y1=y_max,
                     fillcolor="rgba(217,119,6,0.08)", line_width=0, layer="below"),
                # Fix or Exit (bottom-left) - red
                dict(type="rect", x0=x_min, x1=med_share, y0=y_min, y1=med_roc,
                     fillcolor="rgba(220,38,38,0.08)", line_width=0, layer="below"),
            ]

            # Plot each quadrant as a separate trace for legend
            for quad_name, quad_colour in QUADRANT_COLOURS.items():
                q_data = matrix_df[matrix_df["quadrant"] == quad_name]
                if q_data.empty:
                    continue
                fig_matrix.add_trace(go.Scatter(
                    x=q_data["weighted_avg_share_pct"],
                    y=q_data["gpm_roc_primary_4k"],
                    mode="markers+text",
                    marker=dict(
                        size=q_data["rev_size"].apply(
                            lambda v: max(10, min(50, v / 1_000_000 * 3))
                        ),
                        color=quad_colour,
                        opacity=0.85,
                        line=dict(width=1, color="#FFFFFF"),
                    ),
                    text=q_data["short_name"],
                    textposition="top center",
                    textfont=dict(size=9, color="#FFFFFF"),
                    name=quad_name,
                    hovertemplate=(
                        "<b>%{text}</b><br>"
                        "Share: %{x:.1f}%<br>"
                        "GPM ROC: %{y:.2f}x<br>"
                        "<extra></extra>"
                    ),
                ))

            # Add median divider lines
            fig_matrix.add_hline(
                y=med_roc, line_dash="dot", line_color="rgba(255,255,255,0.3)",
                annotation_text=f"Median ROC: {med_roc:.2f}x",
                annotation_font_color="#8899AA",
                annotation_position="bottom right",
            )
            fig_matrix.add_vline(
                x=med_share, line_dash="dot", line_color="rgba(255,255,255,0.3)",
                annotation_text=f"Median Share: {med_share:.1f}%",
                annotation_font_color="#8899AA",
                annotation_position="top left",
            )

            # Quadrant labels
            fig_matrix.add_annotation(
                x=x_max - 0.5, y=y_max - 0.05, text="STAR", showarrow=False,
                font=dict(color="#2ECC71", size=14, family="Georgia"),
            )
            fig_matrix.add_annotation(
                x=x_max - 0.5, y=y_min + 0.05, text="CASH COW", showarrow=False,
                font=dict(color="#3B82F6", size=14, family="Georgia"),
            )
            fig_matrix.add_annotation(
                x=x_min + 0.5, y=y_max - 0.05, text="QUESTION MARK", showarrow=False,
                font=dict(color="#d97706", size=14, family="Georgia"),
            )
            fig_matrix.add_annotation(
                x=x_min + 0.5, y=y_min + 0.05, text="FIX OR EXIT", showarrow=False,
                font=dict(color="#dc2626", size=14, family="Georgia"),
            )

            fig_matrix.update_layout(
                shapes=shapes,
                height=620,
                **_DARK_LAYOUT,
                xaxis=dict(**_GRID, title="Weighted Catchment Share % (CBAS modelled)"),
                yaxis=dict(**_GRID, title="GPM ROC (est.) @ $4K/sqm"),
                legend=dict(
                    title="Quadrant",
                    bgcolor="rgba(0,0,0,0.4)",
                    font=dict(color="#FFFFFF"),
                ),
                margin=dict(l=60, r=20, t=30, b=60),
            )
            st.plotly_chart(fig_matrix, use_container_width=True)

            # Quadrant counts
            st.markdown("**Classification Counts**")
            quad_counts = matrix_df["quadrant"].value_counts()
            qcols = st.columns(4)
            for i, (qname, qcolour) in enumerate(QUADRANT_COLOURS.items()):
                count = quad_counts.get(qname, 0)
                qcols[i].markdown(
                    f"<div style='text-align:center;padding:10px;border-radius:8px;"
                    f"border:1px solid {qcolour};'>"
                    f"<span style='color:{qcolour};font-size:1.6em;font-weight:700;'>"
                    f"{count}</span><br>"
                    f"<span style='color:#B0BEC5;font-size:0.9em;'>{qname}</span></div>",
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown(
                "**Quadrant Definitions**\n\n"
                "- **Star** (high share + high ROC): Invest to grow. Best-performing stores.\n"
                "- **Cash Cow** (high share + low ROC): Optimise efficiency. Strong market position but capital-heavy.\n"
                "- **Question Mark** (low share + high ROC): Investigate growth. Efficient but under-penetrated.\n"
                "- **Fix or Exit** (low share + low ROC): Review for turnaround or closure."
            )


# =============================================================================
# TAB 5: CANNIBALISATION
# =============================================================================

with tab_cannibal:
    st.subheader("Cannibalisation Analysis")

    if not cannibalisation_data:
        _placeholder("Cannibalisation analysis not yet generated.")
    else:
        # ── Store pair cannibalisation ───────────────────────────────────
        store_pairs = cannibalisation_data.get("store_pairs", [])
        whitespace_cannibal = cannibalisation_data.get("whitespace_cannibalisation", [])

        if store_pairs:
            st.markdown("#### Flagged Store Pairs")
            st.caption("Existing store pairs with significant catchment overlap.")

            pairs_df = pd.DataFrame(store_pairs)

            # Filter control
            show_close = st.checkbox("Show only pairs within 3km", value=True, key="cannibal_3km")

            if show_close and "distance_km" in pairs_df.columns:
                pairs_df = pairs_df[pairs_df["distance_km"] <= 3.0]

            if pairs_df.empty:
                st.info("No store pairs within 3km. Uncheck the filter to see all pairs.")
            else:
                # Clean up column names for display
                display_pairs = pairs_df.copy()
                col_renames = {
                    "store_a": "Store A",
                    "store_b": "Store B",
                    "distance_km": "Distance (km)",
                    "overlap_pct": "Overlap %",
                    "cannibalisation_risk": "Risk Level",
                }
                available_renames = {k: v for k, v in col_renames.items() if k in display_pairs.columns}
                display_pairs = display_pairs.rename(columns=available_renames)
                st.dataframe(display_pairs, use_container_width=True, hide_index=True)
        else:
            st.info("No flagged store pairs in dataset.")

        st.markdown("---")

        # ── Whitespace cannibalisation ───────────────────────────────────
        if whitespace_cannibal:
            st.markdown("#### Whitespace Opportunity Cannibalisation Risk")
            st.caption(
                "Assessment of whether proposed new locations would steal from existing HFM "
                "stores or genuinely capture new market."
            )

            ws_df = pd.DataFrame(whitespace_cannibal)

            if not ws_df.empty:
                # Highlight high risk
                col_renames_ws = {
                    "opportunity": "Opportunity",
                    "location": "Location",
                    "nearest_store": "Nearest HFM Store",
                    "distance_km": "Distance (km)",
                    "cannibalisation_risk": "Risk",
                    "risk_level": "Risk",
                    "overlap_pct": "Est. Overlap %",
                    "notes": "Notes",
                }
                available_renames_ws = {k: v for k, v in col_renames_ws.items() if k in ws_df.columns}
                ws_display = ws_df.rename(columns=available_renames_ws)
                st.dataframe(ws_display, use_container_width=True, hide_index=True)

                # Insight callout
                risk_col = "Risk" if "Risk" in ws_display.columns else None
                if risk_col:
                    high_risk_count = len(ws_display[ws_display[risk_col].str.lower().str.contains("high", na=False)])
                    low_risk_count = len(ws_display[ws_display[risk_col].str.lower().str.contains("low", na=False)])
                    st.markdown(
                        glass_card(
                            f"<span style='color:#d97706;font-weight:700;'>Cannibalisation Summary</span><br>"
                            f"<span style='color:#dc2626;font-weight:600;'>{high_risk_count} High Risk</span> "
                            f"opportunities would primarily steal from existing stores.<br>"
                            f"<span style='color:#2ECC71;font-weight:600;'>{low_risk_count} Low Risk</span> "
                            f"opportunities represent genuinely new market entries.",
                            border_color="#d97706",
                        ),
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Whitespace cannibalisation data is empty.")
        else:
            st.info("Whitespace cannibalisation assessment not yet generated.")


# =============================================================================
# TAB 6: NETWORK SCORECARD
# =============================================================================

with tab_score:
    st.subheader("Unified Network Scorecard")
    st.caption(
        "All stores classified by strategic priority. "
        "Combines ROC (ESTIMATED), catchment share (CBAS modelled), CBAS performance data, "
        "and actual GL P&L where available."
    )

    if not has_scorecard:
        _placeholder("Network scorecard not available. Requires ROC + catchment data.")
    else:
        # Try to enrich with real GL P&L data
        enriched_sc = get_enriched_scorecard()
        working_sc = enriched_sc if not enriched_sc.empty else scorecard_df
        has_gl = "actual_revenue" in working_sc.columns

        if has_gl:
            st.success("GL P&L data linked — actual revenue, GP%, EBITDA%, and net profit columns available.")
        else:
            st.info("GL P&L data not available. Showing CBAS-estimated financials only.")

        # ── Filters ──────────────────────────────────────────────────────
        f1, f2, f3 = st.columns(3)

        classifications = sorted(working_sc["classification"].dropna().unique().tolist())
        cls_filter = f1.selectbox(
            "Classification", ["All"] + classifications, key="sc_cls"
        )

        formats = sorted(working_sc["format_segment"].dropna().unique().tolist()) if "format_segment" in working_sc.columns else []
        fmt_filter = f2.selectbox(
            "Format", ["All"] + formats, key="sc_fmt"
        )

        # State filter: try to infer from CBAS data
        if "state" in working_sc.columns:
            states = sorted(working_sc["state"].dropna().unique().tolist())
        else:
            states = []
        state_filter = f3.selectbox(
            "State", ["All"] + states, key="sc_state"
        )

        filtered_sc = working_sc.copy()
        if cls_filter != "All":
            filtered_sc = filtered_sc[filtered_sc["classification"] == cls_filter]
        if fmt_filter != "All" and "format_segment" in filtered_sc.columns:
            filtered_sc = filtered_sc[filtered_sc["format_segment"] == fmt_filter]
        if state_filter != "All" and "state" in filtered_sc.columns:
            filtered_sc = filtered_sc[filtered_sc["state"] == state_filter]

        # ── Display columns ──────────────────────────────────────────────
        desired_cols = [
            "short_name", "classification", "revenue", "gpm_roc_primary_4k",
            "gpm_pct", "weighted_avg_share_pct", "share_trend_pp",
            "retail_sqm", "format_segment", "centre_type",
            "performance_tier", "profitability_tier", "quadrant",
        ]
        # Add GL P&L columns if available
        if has_gl:
            desired_cols.extend([
                "actual_revenue", "actual_gp_pct", "actual_ebitda_pct", "actual_net_pct",
            ])

        available_display = [c for c in desired_cols if c in filtered_sc.columns]
        display_sc = filtered_sc[available_display].copy()

        col_labels = {
            "short_name": "Store",
            "classification": "Classification",
            "revenue": "CBAS Revenue ($M)",
            "gpm_roc_primary_4k": "GPM ROC (est.)",
            "gpm_pct": "GPM %",
            "weighted_avg_share_pct": "Catchment Share %",
            "share_trend_pp": "Share Trend (pp)",
            "retail_sqm": "SQM",
            "format_segment": "Format",
            "centre_type": "Centre Type",
            "performance_tier": "Perf. Tier",
            "profitability_tier": "Profit. Tier",
            "quadrant": "Quadrant",
            "actual_revenue": "GL Revenue ($M)",
            "actual_gp_pct": "GL GP %",
            "actual_ebitda_pct": "GL EBITDA %",
            "actual_net_pct": "GL Net %",
        }
        rename_available = {k: v for k, v in col_labels.items() if k in display_sc.columns}
        display_sc = display_sc.rename(columns=rename_available)

        # Format revenue columns as $M
        for rev_col in ["CBAS Revenue ($M)", "GL Revenue ($M)"]:
            if rev_col in display_sc.columns:
                display_sc[rev_col] = display_sc[rev_col].apply(
                    lambda x: round(x / 1_000_000, 1) if pd.notna(x) and isinstance(x, (int, float)) and x > 1000 else x
                )

        # Round numeric columns
        round_cols = ["GPM ROC (est.)", "GPM %", "Catchment Share %", "Share Trend (pp)",
                      "GL GP %", "GL EBITDA %", "GL Net %"]
        for col in round_cols:
            if col in display_sc.columns:
                display_sc[col] = pd.to_numeric(display_sc[col], errors="coerce").round(2)

        st.dataframe(display_sc, use_container_width=True, hide_index=True, height=600)

        # ── Classification summary ───────────────────────────────────────
        st.markdown("---")
        st.markdown("**Classification Summary**")
        cls_counts = scorecard_df["classification"].value_counts()
        cls_cols = st.columns(min(len(cls_counts), 6))
        for i, (cls_name, count) in enumerate(cls_counts.items()):
            colour = CLASSIFICATION_COLOURS.get(cls_name, "#6B7280")
            cls_cols[i % len(cls_cols)].markdown(
                f"<div style='text-align:center;padding:12px;border-radius:8px;"
                f"border:2px solid {colour};'>"
                f"<span style='color:{colour};font-size:1.8em;font-weight:700;'>"
                f"{count}</span><br>"
                f"<span style='color:#B0BEC5;font-size:0.85em;'>{cls_name}</span></div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown(
            "**Classification Logic**\n\n"
            "- **Invest**: Star quadrant stores. High share + high ROC. Priority for capex.\n"
            "- **Hold**: Cash Cow stores. High share, lower ROC. Maintain and optimise.\n"
            "- **Rationalise**: Question Mark stores. Low share, decent ROC. Needs investigation.\n"
            "- **Exit Review**: Fix or Exit quadrant. Low share + low ROC. Turnaround or close.\n"
            "- **Monitor (New)**: Opened in 2025. Insufficient history for classification."
        )


# =============================================================================
# TAB 7: FIX CANDIDATES
# =============================================================================

with tab_fix:
    st.subheader("Fix Candidates -- Drummoyne Pattern")
    st.caption(
        "Stores with strong customer metrics (high loyalty, good share) "
        "but weak capital efficiency (low GPM ROC). Typically the store format "
        "is too large for the catchment."
    )

    if not fix_data:
        _placeholder("Fix candidate analysis not yet generated.")
    else:
        candidates = fix_data.get("candidates", fix_data.get("stores", []))

        if not candidates:
            st.info("No fix candidates identified. All stores appear correctly sized for their catchments.")
        else:
            for i, candidate in enumerate(candidates):
                store_name = candidate.get("store", candidate.get("short_name", f"Store {i+1}"))
                diagnosis = candidate.get("diagnosis", "No diagnosis available.")
                actions = candidate.get("suggested_actions", candidate.get("actions", []))
                roc_val = candidate.get("gpm_roc", candidate.get("gpm_roc_primary_4k", None))
                share_val = candidate.get("market_share", candidate.get("weighted_avg_share_pct", None))
                sqm = candidate.get("retail_sqm", candidate.get("sqm", None))
                fmt = candidate.get("format_segment", candidate.get("format", ""))

                # Build card
                roc_str = f"{roc_val:.2f}x" if roc_val is not None else "N/A"
                share_str = f"{share_val:.1f}%" if share_val is not None else "N/A"
                sqm_str = f"{sqm:,.0f} sqm" if sqm is not None else "N/A"
                roc_colour = _colour_for_roc(roc_val) if roc_val is not None else "#6B7280"

                with st.expander(f"{store_name} -- GPM ROC: {roc_str} | Share: {share_str}", expanded=(i == 0)):
                    mc1, mc2, mc3, mc4 = st.columns(4)
                    mc1.metric("GPM ROC (est.)", roc_str)
                    mc2.metric("Catchment Share", share_str)
                    mc3.metric("Retail SQM", sqm_str)
                    mc4.metric("Format", fmt)

                    st.markdown("**Diagnosis**")
                    st.markdown(diagnosis)

                    if actions:
                        st.markdown("**Suggested Actions**")
                        if isinstance(actions, list):
                            for action in actions:
                                if isinstance(action, dict):
                                    action_text = action.get("action", action.get("description", str(action)))
                                    priority = action.get("priority", "")
                                    priority_str = f" ({priority})" if priority else ""
                                    st.markdown(f"- {action_text}{priority_str}")
                                else:
                                    st.markdown(f"- {action}")
                        else:
                            st.markdown(str(actions))

            st.markdown("---")
            st.markdown(
                glass_card(
                    "<span style='color:#d97706;font-weight:700;font-size:1.1em;'>"
                    "The Drummoyne Pattern</span><br>"
                    "<span style='color:#FFFFFF;'>"
                    "Some stores have loyal customers and decent market share, "
                    "but the physical store is too large for the revenue it generates. "
                    "The fix is typically format reduction (downsize SQM), "
                    "subletting excess space, or negotiating lower rent -- "
                    "not closing the store. These are valuable market positions "
                    "with a capital efficiency problem."
                    "</span>",
                    border_color="#d97706",
                ),
                unsafe_allow_html=True,
            )


# =============================================================================
# TAB 8: DATA GAPS
# =============================================================================

with tab_gaps:
    st.subheader("Data Availability & Gaps")
    st.caption("What we have, what we need, and what we are working on.")

    # ── Availability matrix ──────────────────────────────────────────────
    st.markdown("#### Data Availability Matrix")

    data_items = [
        {"Category": "Store Financials", "Item": "Annual Revenue", "Status": "ACTUAL", "Source": "Internal POS/ERP", "Available": True},
        {"Category": "Store Financials", "Item": "Gross Product Margin %", "Status": "ESTIMATED", "Source": "Industry benchmarks", "Available": True},
        {"Category": "Store Financials", "Item": "GL P&L (full accounting)", "Status": "ACTUAL", "Source": "GL Data Dump — Jul 2016 to Jan 2026", "Available": True},
        {"Category": "Store Financials", "Item": "Net Profit by Store", "Status": "ACTUAL", "Source": "GL P&L History", "Available": True},
        {"Category": "Store Financials", "Item": "Rent & Occupancy Costs", "Status": "ACTUAL", "Source": "GL P&L History", "Available": True},
        {"Category": "Store Financials", "Item": "Labour Cost by Store", "Status": "ACTUAL", "Source": "GL P&L History", "Available": True},
        {"Category": "Store Financials", "Item": "EBITDA by Store", "Status": "ACTUAL", "Source": "GL P&L History", "Available": True},
        {"Category": "Capital", "Item": "Capital per SQM", "Status": "ESTIMATED", "Source": "Industry benchmark ($4K/sqm)", "Available": True},
        {"Category": "Capital", "Item": "Actual Fitout Cost", "Status": "MISSING", "Source": "Property/Finance", "Available": False},
        {"Category": "Capital", "Item": "Lease Terms & Expiry", "Status": "MISSING", "Source": "Property team", "Available": False},
        {"Category": "Market Share", "Item": "CBAS Postcode Share", "Status": "ACTUAL (modelled)", "Source": "CBAS", "Available": True},
        {"Category": "Market Share", "Item": "Share Trend YoY", "Status": "ACTUAL (modelled)", "Source": "CBAS", "Available": True},
        {"Category": "Market Share", "Item": "Catchment Boundaries", "Status": "ESTIMATED", "Source": "Distance-based model", "Available": True},
        {"Category": "Customer", "Item": "Customer Count", "Status": "ACTUAL", "Source": "CBAS", "Available": True},
        {"Category": "Customer", "Item": "Share of Wallet", "Status": "ACTUAL (modelled)", "Source": "CBAS", "Available": True},
        {"Category": "Customer", "Item": "Basket Composition", "Status": "MISSING", "Source": "Transaction data", "Available": False},
        {"Category": "Operations", "Item": "Store Size (SQM)", "Status": "ACTUAL", "Source": "CBAS / Internal", "Available": True},
        {"Category": "Operations", "Item": "Department-level GP", "Status": "ESTIMATED", "Source": "Aggregate benchmarks", "Available": True},
        {"Category": "Operations", "Item": "Shrinkage by Store", "Status": "MISSING", "Source": "Operations", "Available": False},
        {"Category": "Demographics", "Item": "ABS Census by Postcode", "Status": "PLANNED", "Source": "ABS 2021 Census", "Available": False},
        {"Category": "Demographics", "Item": "Income & Occupation", "Status": "PLANNED", "Source": "ABS 2021 Census", "Available": False},
    ]

    gaps_df = pd.DataFrame(data_items)

    # Colour-code status
    def _status_colour(status: str) -> str:
        s = status.upper()
        if "ACTUAL" in s:
            return "#2ECC71"
        elif "ESTIMATED" in s:
            return "#d97706"
        elif "PLANNED" in s:
            return "#3B82F6"
        else:
            return "#dc2626"

    st.dataframe(
        gaps_df[["Category", "Item", "Status", "Source"]],
        use_container_width=True,
        hide_index=True,
    )

    # Visual summary
    actual_count = len([d for d in data_items if "ACTUAL" in d["Status"].upper()])
    estimated_count = len([d for d in data_items if "ESTIMATED" in d["Status"].upper()])
    missing_count = len([d for d in data_items if d["Status"].upper() == "MISSING"])
    planned_count = len([d for d in data_items if "PLANNED" in d["Status"].upper()])

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Actual", actual_count)
    g2.metric("Estimated", estimated_count)
    g3.metric("Missing", missing_count)
    g4.metric("Planned", planned_count)

    # Visual availability bar
    total = len(data_items)
    fig_avail = go.Figure()
    fig_avail.add_trace(go.Bar(
        x=[actual_count], y=["Data Coverage"], orientation="h",
        name="Actual", marker_color="#2ECC71",
        text=[f"{actual_count}"], textposition="inside",
    ))
    fig_avail.add_trace(go.Bar(
        x=[estimated_count], y=["Data Coverage"], orientation="h",
        name="Estimated", marker_color="#d97706",
        text=[f"{estimated_count}"], textposition="inside",
    ))
    fig_avail.add_trace(go.Bar(
        x=[planned_count], y=["Data Coverage"], orientation="h",
        name="Planned", marker_color="#3B82F6",
        text=[f"{planned_count}"], textposition="inside",
    ))
    fig_avail.add_trace(go.Bar(
        x=[missing_count], y=["Data Coverage"], orientation="h",
        name="Missing", marker_color="#dc2626",
        text=[f"{missing_count}"], textposition="inside",
    ))
    fig_avail.update_layout(
        barmode="stack",
        height=120,
        **_DARK_LAYOUT,
        margin=dict(l=0, r=20, t=10, b=10),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5,
            font=dict(color="#FFFFFF"),
        ),
    )
    st.plotly_chart(fig_avail, use_container_width=True)

    st.markdown("---")

    # ── Priority data requests ───────────────────────────────────────────
    st.markdown("#### Priority Data Requests")

    priorities = [
        {
            "Priority": "P1 -- DONE",
            "Data": "Store-level P&L (revenue, COGS, rent, labour, net profit)",
            "Owner": "Finance",
            "Impact": "GL P&L loaded — Jul 2016 to Jan 2026, 35 stores, 144 accounts",
        },
        {
            "Priority": "P1 -- Critical",
            "Data": "Actual fitout/capex cost per store",
            "Owner": "Property / Finance",
            "Impact": "Replaces $4K/sqm assumption with real capital figures",
        },
        {
            "Priority": "P2 -- High",
            "Data": "Lease terms, rent per sqm, lease expiry dates",
            "Owner": "Property",
            "Impact": "Enables true occupancy cost analysis and exit timing",
        },
        {
            "Priority": "P2 -- High",
            "Data": "ABS Census demographics by postcode",
            "Owner": "Data / Analytics",
            "Impact": "Links store success profiles to demographic predictors",
        },
        {
            "Priority": "P3 -- Medium",
            "Data": "Department-level actuals (revenue + GP by dept by store)",
            "Owner": "Buying / Finance",
            "Impact": "Identifies which departments drive profitability per format",
        },
        {
            "Priority": "P3 -- Medium",
            "Data": "Shrinkage and waste by store",
            "Owner": "Operations",
            "Impact": "Separates margin leakage from pricing/range issues",
        },
    ]

    st.dataframe(pd.DataFrame(priorities), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown(
        glass_card(
            "<span style='color:#3B82F6;font-weight:700;font-size:1.1em;'>"
            "Data Audit Reference</span><br>"
            "<span style='color:#FFFFFF;'>"
            "For the full data audit including methodology notes, assumptions log, "
            "and data request templates, see <code>hub-roc-data-audit.md</code> in the project docs. "
            "The finance team data request has been drafted and is ready for review."
            "</span>",
            border_color="#3B82F6",
        ),
        unsafe_allow_html=True,
    )


# ── Cross-links ──────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("**Related Dashboards**")
_pages = st.session_state.get("_pages", {})
c1, c2, c3 = st.columns(3)
if "whitespace" in _pages:
    c1.page_link(_pages["whitespace"], label="Whitespace Analysis", icon="\U0001f5fa\ufe0f")
if "market-share" in _pages:
    c2.page_link(_pages["market-share"], label="Market Share", icon="\U0001f4ca")
if "customers" in _pages:
    c3.page_link(_pages["customers"], label="Customer Hub", icon="\U0001f465")
c4, c5, c6 = st.columns(3)
if "profitability" in _pages:
    c4.page_link(_pages["profitability"], label="Profitability", icon="\U0001f4b0")
if "roce" in _pages:
    c5.page_link(_pages["roce"], label="ROCE Analysis", icon="\U0001f4b9")
if "cannibalisation" in _pages:
    c6.page_link(_pages["cannibalisation"], label="Cannibalisation", icon="\U0001f50d")

render_footer(
    "Store Network",
    "CBAS Network Analysis (Feb 2026) | ROC Analysis (ESTIMATED) | CBAS Market Share (modelled) | GL P&L History (Jul 2016 \u2013 Jan 2026)",
    user=user,
)
