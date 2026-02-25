"""
Harris Farm Hub — Demographics Dashboard
ABS Census 2021 data at postcode level, integrated with store performance.
Demographic Blueprint, correlation analysis, and opportunity scoring.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared.styles import render_header, render_footer, glass_card
from shared.demographic_intel import (
    get_store_profiles,
    get_correlations,
    get_top_predictors,
    get_blueprint,
    get_ideal_ranges,
    get_top_quartile_stores,
    get_postcode_scores,
    get_ranked_opportunities,
    get_cbas_whitespace_enriched,
    get_opportunity_summary,
    get_store_scorecard_with_demographics,
    DEMO_SCORE_COLOURS,
    score_to_tier,
)

# ── Layout helpers ───────────────────────────────────────────────────────────

_DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#FFFFFF", family="Trebuchet MS, sans-serif"),
)
_GRID = dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)")

_METRIC_LABELS = {
    "pct_professional_catchment": "Professional/Managerial %",
    "pct_degree_catchment": "Degree Holders %",
    "median_hh_income_weekly_catchment": "Median HH Income ($/wk)",
    "pct_wfh_catchment": "Work From Home %",
    "pct_high_income_hh_catchment": "High Income Households %",
    "seifa_irsad_score_catchment": "SEIFA IRSAD Score",
    "seifa_irsad_decile_catchment": "SEIFA Decile",
    "median_age_catchment": "Median Age",
    "median_rent_weekly_catchment": "Median Rent ($/wk)",
    "median_mortgage_monthly_catchment": "Median Mortgage ($/mth)",
    "avg_household_size_catchment": "Avg Household Size",
    "labour_force_participation_pct_catchment": "Labour Force Part. %",
    "unemployment_pct_catchment": "Unemployment %",
    "pct_professional": "Professional/Managerial %",
    "pct_degree": "Degree Holders %",
    "median_hh_income_weekly": "Median HH Income ($/wk)",
    "pct_wfh": "Work From Home %",
    "pct_high_income_hh": "High Income HH %",
    "seifa_irsad_decile": "SEIFA Decile",
}


def _label(col):
    return _METRIC_LABELS.get(col, col.replace("_", " ").title())


def _placeholder(msg="Data not yet available."):
    st.info(msg + " Run the demographic scoring pipeline to populate this section.")


# ── Auth & Header ────────────────────────────────────────────────────────────

user = st.session_state.get("auth_user")

render_header(
    "Demographics",
    "ABS Census 2021 profiles, demographic scoring, and opportunity validation",
    goals=["G2", "G3"],
    strategy_context=(
        "Demographics tell us which suburbs align with our shopper profile — "
        "affluent, professional, food-curious households."
    ),
)
st.caption(
    "Source: ABS Census 2021 (SA1 level, aggregated to postcode) | "
    "SEIFA IRSAD 2021 | 1,075 postcodes across NSW, QLD, ACT."
)

# ── Load data ────────────────────────────────────────────────────────────────

profiles = get_store_profiles()
blueprint = get_blueprint()
correlations = get_correlations()
scores_df = get_postcode_scores()
opp_summary = get_opportunity_summary()

has_profiles = not profiles.empty
has_blueprint = bool(blueprint)
has_scores = not scores_df.empty

# ── Tabs ─────────────────────────────────────────────────────────────────────

tab_exec, tab_profiles, tab_blueprint, tab_corr, tab_scores, tab_opps = st.tabs([
    "Overview",
    "Store Profiles",
    "Demographic Blueprint",
    "Correlations",
    "Postcode Scores",
    "Validated Opportunities",
])


# =============================================================================
# TAB 1: OVERVIEW
# =============================================================================

with tab_exec:
    if not has_profiles:
        _placeholder()
    else:
        # KPI row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Postcodes Scored", f"{len(scores_df):,}" if has_scores else "—")
        c2.metric("Stores Profiled", len(profiles))

        if has_blueprint:
            tq_stores = blueprint.get("top_quartile_stores", [])
            c3.metric("Top Quartile Stores", len(tq_stores))
        else:
            c3.metric("Top Quartile Stores", "—")

        if opp_summary:
            c4.metric("Validated Opportunities", opp_summary.get("low_share_opportunities", 0))
        else:
            c4.metric("Validated Opportunities", "—")

        st.markdown("---")

        # Key findings
        st.subheader("Key Findings")

        predictors = get_top_predictors(5)
        if predictors:
            st.markdown("**Top demographic predictors of store performance:**")
            for i, p in enumerate(predictors, 1):
                metric = p.get("demographic", "")
                corr_val = p.get("avg_abs_correlation", 0)
                st.markdown(
                    f"{i}. **{_label(metric)}** — avg |r| = {corr_val:.3f}"
                )

        if has_blueprint:
            st.markdown("---")
            diffs = blueprint.get("key_differentiators", [])[:5]
            if diffs:
                st.markdown("**What separates top-quartile stores from the rest:**")
                for d in diffs:
                    metric = d.get("metric", "")
                    diff_pct = d.get("difference_pct", 0)
                    top_val = d.get("top_quartile_avg", 0)
                    direction = "higher" if diff_pct > 0 else "lower"
                    st.markdown(
                        f"- **{_label(metric)}**: Top quartile is **{abs(diff_pct):.1f}% {direction}** "
                        f"({top_val:.1f})"
                    )

        # Store demographic summary scatter
        if has_profiles and "pct_professional_catchment" in profiles.columns:
            st.markdown("---")
            st.subheader("Store Demographics vs Performance")
            scorecard = get_store_scorecard_with_demographics()
            if not scorecard.empty and "gpm_roc_primary_4k" in scorecard.columns:
                fig = px.scatter(
                    scorecard.dropna(subset=["gpm_roc_primary_4k", "pct_professional_catchment"]),
                    x="pct_professional_catchment",
                    y="gpm_roc_primary_4k",
                    text="store",
                    color="format_segment" if "format_segment" in scorecard.columns else None,
                    color_discrete_map={"Express": "#2ECC71", "Standard": "#3B82F6", "Large": "#d97706"},
                    labels={
                        "pct_professional_catchment": "Professional/Managerial % (Catchment)",
                        "gpm_roc_primary_4k": "GPM ROC (est. @ $4K/sqm)",
                    },
                    title="Professional Workforce % vs GPM Return on Capital",
                )
                fig.update_traces(textposition="top center", textfont_size=10)
                fig.update_layout(**_DARK_LAYOUT, height=500)
                fig.update_xaxes(**_GRID)
                fig.update_yaxes(**_GRID)
                fig.add_hline(y=1.0, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                              annotation_text="1.0x breakeven")
                st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Interpretation: Higher professional workforce % in a store's catchment correlates "
            "with higher GPM return on capital. This is one of many demographic signals."
        )


# =============================================================================
# TAB 2: STORE PROFILES
# =============================================================================

with tab_profiles:
    if not has_profiles:
        _placeholder("Store demographic profiles not available.")
    else:
        st.subheader("Catchment Demographics by Store")
        st.caption("Population-weighted average demographics within each store's 10km catchment.")

        # Sortable table
        display_cols = [
            "store", "catchment_pop",
            "pct_professional_catchment", "pct_degree_catchment",
            "median_hh_income_weekly_catchment", "pct_wfh_catchment",
            "pct_high_income_hh_catchment", "seifa_irsad_decile_catchment",
            "unemployment_pct_catchment",
        ]
        available = [c for c in display_cols if c in profiles.columns]
        disp = profiles[available].copy()
        disp.columns = [_label(c) if c != "store" else "Store" for c in available]

        st.dataframe(
            disp.sort_values("Professional/Managerial %", ascending=False)
            if "Professional/Managerial %" in disp.columns
            else disp,
            use_container_width=True,
            hide_index=True,
        )

        # Radar chart for selected store vs network average
        st.markdown("---")
        st.subheader("Store Profile vs Network Average")

        store_names = profiles["store"].sort_values().tolist()
        selected = st.selectbox("Select store", store_names, index=0)

        radar_metrics = [
            "pct_professional_catchment", "pct_degree_catchment",
            "pct_high_income_hh_catchment", "pct_wfh_catchment",
            "seifa_irsad_decile_catchment",
        ]
        radar_available = [m for m in radar_metrics if m in profiles.columns]

        if radar_available and selected:
            store_row = profiles[profiles["store"] == selected].iloc[0]
            net_avg = profiles[radar_available].mean()

            # Normalize to 0-100 scale for radar
            mins = profiles[radar_available].min()
            maxs = profiles[radar_available].max()
            ranges = maxs - mins
            ranges = ranges.replace(0, 1)

            store_norm = ((store_row[radar_available] - mins) / ranges * 100).tolist()
            avg_norm = ((net_avg - mins) / ranges * 100).tolist()
            labels = [_label(m) for m in radar_available]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=store_norm + [store_norm[0]],
                theta=labels + [labels[0]],
                fill="toself",
                name=selected,
                line_color="#2ECC71",
                fillcolor="rgba(46,204,113,0.15)",
            ))
            fig.add_trace(go.Scatterpolar(
                r=avg_norm + [avg_norm[0]],
                theta=labels + [labels[0]],
                fill="toself",
                name="Network Average",
                line_color="#6B7280",
                fillcolor="rgba(107,114,128,0.1)",
            ))
            fig.update_layout(
                **_DARK_LAYOUT,
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.1)"),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                ),
                height=450,
                showlegend=True,
                legend=dict(x=0.5, y=-0.1, xanchor="center", orientation="h"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Raw values
            with st.expander("Raw demographic values"):
                raw = pd.DataFrame({
                    "Metric": [_label(m) for m in radar_available],
                    selected: [round(store_row[m], 1) for m in radar_available],
                    "Network Avg": [round(net_avg[m], 1) for m in radar_available],
                })
                st.dataframe(raw, use_container_width=True, hide_index=True)


# =============================================================================
# TAB 3: DEMOGRAPHIC BLUEPRINT
# =============================================================================

with tab_blueprint:
    if not has_blueprint:
        _placeholder("Demographic blueprint not available.")
    else:
        st.subheader("HFM Ideal Demographic Blueprint")
        st.caption(
            f"Derived from top-quartile stores by GPM ROC "
            f"(threshold: {blueprint.get('top_quartile_threshold', 'N/A')}x). "
            f"Method: {blueprint.get('method', 'N/A')}."
        )

        # Top vs Bottom quartile comparison
        tq = blueprint.get("top_quartile_profile", {})
        bq = blueprint.get("bottom_quartile_profile", {})
        ideal = blueprint.get("ideal_ranges", {})

        if tq and bq:
            st.markdown("#### Top Quartile vs Bottom Quartile")

            tq_stores = ", ".join(blueprint.get("top_quartile_stores", []))
            bq_stores = ", ".join(blueprint.get("bottom_quartile_stores", []))
            st.markdown(f"**Top quartile:** {tq_stores}")
            st.markdown(f"**Bottom quartile:** {bq_stores}")

            compare_metrics = [
                "pct_professional_catchment", "pct_degree_catchment",
                "median_hh_income_weekly_catchment", "pct_wfh_catchment",
                "pct_high_income_hh_catchment", "seifa_irsad_decile_catchment",
                "unemployment_pct_catchment",
            ]
            rows = []
            for m in compare_metrics:
                if m in tq and m in bq:
                    tq_val = tq[m]
                    bq_val = bq[m]
                    diff = ((tq_val - bq_val) / bq_val * 100) if bq_val != 0 else 0
                    rows.append({
                        "Metric": _label(m),
                        "Top Quartile": round(tq_val, 1),
                        "Bottom Quartile": round(bq_val, 1),
                        "Difference %": round(diff, 1),
                    })

            if rows:
                comp_df = pd.DataFrame(rows)
                st.dataframe(comp_df, use_container_width=True, hide_index=True)

            # Bar chart of key differentiators
            diffs = blueprint.get("key_differentiators", [])
            if diffs:
                st.markdown("---")
                st.markdown("#### Key Differentiators (Top vs Bottom Quartile)")
                diff_df = pd.DataFrame(diffs[:8])
                diff_df["metric_label"] = diff_df["metric"].map(_label)
                diff_df["abs_diff"] = diff_df["difference_pct"].abs()
                diff_df = diff_df.sort_values("abs_diff", ascending=True)

                fig = px.bar(
                    diff_df,
                    x="difference_pct",
                    y="metric_label",
                    orientation="h",
                    color="difference_pct",
                    color_continuous_scale=["#dc2626", "#6B7280", "#2ECC71"],
                    labels={"difference_pct": "Difference %", "metric_label": ""},
                    title="How Top Quartile Stores Differ Demographically",
                )
                fig.update_layout(**_DARK_LAYOUT, height=400, coloraxis_showscale=False)
                fig.update_xaxes(**_GRID)
                st.plotly_chart(fig, use_container_width=True)

        # Ideal ranges table
        if ideal:
            st.markdown("---")
            st.markdown("#### Ideal Demographic Ranges")
            ideal_rows = []
            for m, vals in ideal.items():
                if isinstance(vals, dict):
                    ideal_rows.append({
                        "Metric": _label(m),
                        "Min": round(vals.get("min", 0), 1),
                        "Ideal (Top Q Avg)": round(vals.get("top_q_avg", 0), 1),
                        "Max": round(vals.get("max", 0), 1),
                    })
            if ideal_rows:
                st.dataframe(pd.DataFrame(ideal_rows), use_container_width=True, hide_index=True)


# =============================================================================
# TAB 4: CORRELATIONS
# =============================================================================

with tab_corr:
    corr_matrix = correlations.get("correlation_matrix", {})
    if not corr_matrix:
        _placeholder("Correlation data not available.")
    else:
        st.subheader("Demographic-Performance Correlations")
        st.caption(
            "Pearson correlation between store catchment demographics and performance metrics. "
            "Values closer to +1 or -1 indicate stronger relationships."
        )

        # Build heatmap
        perf_metrics = list(corr_matrix.keys())
        demo_metrics = list(next(iter(corr_matrix.values())).keys()) if perf_metrics else []

        if perf_metrics and demo_metrics:
            z_data = []
            for pm in perf_metrics:
                row = [corr_matrix[pm].get(dm, 0) for dm in demo_metrics]
                z_data.append(row)

            fig = go.Figure(data=go.Heatmap(
                z=z_data,
                x=[_label(dm) for dm in demo_metrics],
                y=[_label(pm) for pm in perf_metrics],
                colorscale="RdBu",
                zmid=0,
                zmin=-1,
                zmax=1,
                text=[[f"{v:.2f}" for v in row] for row in z_data],
                texttemplate="%{text}",
                textfont={"size": 10},
            ))
            fig.update_layout(
                **_DARK_LAYOUT,
                height=350,
                xaxis=dict(tickangle=-45),
                title="Correlation Matrix: Demographics vs Performance",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Top predictors
        predictors = get_top_predictors(10)
        if predictors:
            st.markdown("---")
            st.subheader("Top Predictors (by average absolute correlation)")
            pred_df = pd.DataFrame(predictors)
            if "demographic" in pred_df.columns:
                pred_df["Metric"] = pred_df["demographic"].map(_label)
                pred_df = pred_df.rename(columns={"avg_abs_correlation": "Avg |r|"})
                st.dataframe(
                    pred_df[["Metric", "Avg |r|"]],
                    use_container_width=True,
                    hide_index=True,
                )

        st.caption(
            "Note: Correlations based on 26 stores — directional, not statistically rigorous. "
            "Use to inform hypothesis, not to draw conclusions."
        )


# =============================================================================
# TAB 5: POSTCODE SCORES
# =============================================================================

with tab_scores:
    if not has_scores:
        _placeholder("Postcode scores not available.")
    else:
        st.subheader("Demographic Fit Scores")
        st.caption(
            "Every postcode scored 0-100 on demographic alignment with the HFM ideal profile. "
            "Higher = better fit."
        )

        # Filters
        c1, c2, c3 = st.columns(3)
        states = sorted(scores_df["state"].dropna().unique().tolist())
        sel_state = c1.selectbox("State", ["All"] + states)
        min_pop = c2.number_input("Min population", value=1000, step=500)
        min_score = c3.slider("Min demographic score", 0, 100, 50)

        filtered = scores_df.copy()
        if sel_state != "All":
            filtered = filtered[filtered["state"] == sel_state]
        filtered = filtered[filtered["total_population"] >= min_pop]
        filtered = filtered[filtered["demographic_score"] >= min_score]

        st.markdown(f"**{len(filtered):,}** postcodes match filters")

        # Score distribution
        fig = px.histogram(
            filtered, x="demographic_score", nbins=30,
            color_discrete_sequence=["#2ECC71"],
            labels={"demographic_score": "Demographic Score"},
            title="Score Distribution",
        )
        fig.update_layout(**_DARK_LAYOUT, height=300)
        fig.update_xaxes(**_GRID)
        fig.update_yaxes(**_GRID)
        st.plotly_chart(fig, use_container_width=True)

        # Table
        display_cols = ["postcode", "state", "demographic_score", "total_population"]
        score_cols = [c for c in ["pct_professional", "pct_degree",
                                   "median_hh_income_weekly", "pct_wfh",
                                   "pct_high_income_hh", "seifa_irsad_decile"]
                      if c in filtered.columns]
        display_cols.extend(score_cols)

        disp = filtered[display_cols].copy()
        disp = disp.sort_values("demographic_score", ascending=False).head(100)
        rename_map = {c: _label(c) for c in score_cols}
        rename_map["postcode"] = "Postcode"
        rename_map["state"] = "State"
        rename_map["demographic_score"] = "Score"
        rename_map["total_population"] = "Population"
        disp = disp.rename(columns=rename_map)

        st.dataframe(disp, use_container_width=True, hide_index=True)

        # Search
        st.markdown("---")
        st.subheader("Look Up a Postcode")
        lookup = st.text_input("Enter postcode", placeholder="e.g. 2088")
        if lookup:
            match = scores_df[scores_df["postcode"].astype(str) == str(lookup.strip())]
            if match.empty:
                st.warning(f"Postcode {lookup} not found in dataset.")
            else:
                row = match.iloc[0]
                score = row.get("demographic_score", 0)
                tier = score_to_tier(score)
                st.metric("Demographic Score", f"{score:.1f} / 100", delta=tier)
                cols_show = [c for c in score_cols if c in match.columns]
                if cols_show:
                    vals = {_label(c): round(row[c], 1) for c in cols_show if pd.notna(row[c])}
                    st.json(vals)


# =============================================================================
# TAB 6: VALIDATED OPPORTUNITIES
# =============================================================================

with tab_opps:
    opps_ranked = get_ranked_opportunities(50)
    cbas_enriched = get_cbas_whitespace_enriched()

    if not opps_ranked and not cbas_enriched:
        _placeholder("Validated opportunities not available.")
    else:
        # Summary
        if opp_summary:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Low-Share Opportunities", opp_summary.get("low_share_opportunities", 0))
            c2.metric("High Cannib. Risk", opp_summary.get("high_cannibalisation_risk", 0))
            c3.metric("CBAS Whitespace Targets", opp_summary.get("cbas_whitespace_targets", 0))
            c4.metric("Postcodes Scored", opp_summary.get("total_postcodes_scored", 0))

        # CBAS whitespace targets enriched
        if cbas_enriched:
            st.markdown("---")
            st.subheader("CBAS Whitespace Targets — Demographic Validation")
            st.caption("The 16 whitespace targets from CBAS analysis, now enriched with ABS Census demographic scores.")

            cbas_df = pd.DataFrame(cbas_enriched)
            show_cols = []
            for c in ["suburb", "postcode", "state", "demographic_score", "hfm_share_pct",
                       "nearest_store", "distance_km", "cannibalisation_risk",
                       "overall_opportunity_score", "phase"]:
                if c in cbas_df.columns:
                    show_cols.append(c)

            if show_cols:
                sort_col = "overall_opportunity_score" if "overall_opportunity_score" in cbas_df.columns else "demographic_score"
                st.dataframe(
                    cbas_df[show_cols].sort_values(sort_col, ascending=False),
                    use_container_width=True,
                    hide_index=True,
                )

        # Ranked opportunities
        if opps_ranked:
            st.markdown("---")
            st.subheader("Top Growth Opportunities")
            st.caption(
                "Postcodes with high demographic fit (>70) and low HFM share (<5%). "
                "Ranked by demographic_score * (1 - share/20)."
            )

            opps_df = pd.DataFrame(opps_ranked)
            show_cols = []
            for c in ["postcode", "suburb", "state", "demographic_score",
                       "hfm_share_pct", "nearest_store", "distance_km",
                       "cannibalisation_risk", "overall_opportunity_score"]:
                if c in opps_df.columns:
                    show_cols.append(c)

            if show_cols:
                sort_col = "overall_opportunity_score" if "overall_opportunity_score" in opps_df.columns else "demographic_score"
                st.dataframe(
                    opps_df[show_cols].sort_values(sort_col, ascending=False).head(25),
                    use_container_width=True,
                    hide_index=True,
                )

        st.caption(
            "All opportunities are DIRECTIONAL ONLY. Low share does not equal opportunity. "
            "Always validate with site visits, competitor analysis, and lease availability."
        )


# ── Cross-links ──────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("**Related**")
_pages = st.session_state.get("_pages", {})
c1, c2, c3 = st.columns(3)
if "store-network" in _pages:
    c1.page_link(_pages["store-network"], label="Store Network", icon="\U0001f3ec")
if "market-share" in _pages:
    c2.page_link(_pages["market-share"], label="Market Share", icon="\U0001f4ca")
if "whitespace" in _pages:
    c3.page_link(_pages["whitespace"], label="Whitespace Analysis", icon="\U0001f5fa\ufe0f")

render_footer("Demographics", "ABS Census 2021 | SEIFA IRSAD 2021 | Phase 4 Integration", user=user)
