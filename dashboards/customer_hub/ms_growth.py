"""
Customer Hub — Market Share > Growth Frontiers
Opportunity quadrant, issue radar, YoY trends, sudden shifts.
Includes the critical "low share ≠ opportunity" warning.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from customer_hub.components import (
    PALETTE, OPP_COLOURS, section_header, insight_callout, one_thing_box,
    fmt_period, filter_by_state, safe_int, STATE_RANGES,
)
from market_share_layer import (
    get_latest_period, get_periods,
    opportunity_analysis, flag_issues, detect_shifts,
    yoy_comparison, postcode_trend, nearest_store,
    STORE_LOCATIONS,
)


def render():
    latest = st.session_state.get("ms_latest") or get_latest_period()
    channel = st.session_state.get("ms_channel", "Total")
    state_filter = st.session_state.get("ms_state", "All")

    section_header(
        "Growth Frontiers",
        "Where the real opportunities (and real risks) live — backed by data, "
        "not assumptions.",
    )

    # ── Critical warning ──
    insight_callout(
        "<b>Low share does NOT automatically equal opportunity.</b> "
        "It could mean demographic mismatch, excessive distance, or "
        "customers who are travel-loyal to another brand. "
        "Always verify with penetration data and distance analysis "
        "before recommending investment. All opportunity flags below "
        "are <b>directional only</b>.",
        style="warning",
    )

    # ── Opportunity Quadrant ──
    st.subheader("Opportunity Quadrant")
    st.caption("Penetration vs Share identifies strategic opportunity types.")

    opps = opportunity_analysis(latest, channel)
    if not opps:
        st.info("No opportunity data.")
    else:
        odf = pd.DataFrame(opps)
        odf = filter_by_state(odf, state_filter)

        if odf.empty:
            st.info("No opportunity data for the selected state filter.")
        else:
            odf["market_size"] = pd.to_numeric(
                odf["market_size"], errors="coerce").fillna(0).clip(lower=0)

            fig_quad = px.scatter(
                odf, x="penetration_pct", y="market_share_pct",
                color="opportunity_type", size="market_size",
                hover_name="region_name",
                custom_data=["postcode", "spend_per_customer",
                             "nearest_store", "distance_km",
                             "distance_tier", "opportunity_type"],
                labels={
                    "penetration_pct": "Customer Penetration %",
                    "market_share_pct": "Market Share %",
                    "opportunity_type": "Type",
                },
                color_discrete_map=OPP_COLOURS,
                size_max=30,
            )
            fig_quad.update_traces(
                hovertemplate=(
                    "<b>%{hovertext}</b> (%{customdata[0]})<br>"
                    "Share: %{y:.1f}% | Penetration: %{x:.1f}%<br>"
                    "Spend: $%{customdata[1]:.0f}<br>"
                    "Store: %{customdata[2]} (%{customdata[3]:.0f}km, "
                    "%{customdata[4]})<br>Type: %{customdata[5]}"
                    "<extra></extra>"
                )
            )
            fig_quad.add_hline(y=5, line_dash="dash", line_color="#d1d5db",
                               annotation_text="5% share")
            fig_quad.add_vline(x=15, line_dash="dash", line_color="#d1d5db",
                               annotation_text="15% penetration")
            fig_quad.update_layout(height=600,
                                   legend=dict(orientation="h", y=-0.12))
            st.plotly_chart(fig_quad, use_container_width=True,
                            key="ms_opp_scatter")

            # Summary counts
            type_counts = odf["opportunity_type"].value_counts()
            cols = st.columns(min(5, len(type_counts)))
            for i, (opp_type, count) in enumerate(type_counts.items()):
                if i < len(cols):
                    cols[i].metric(opp_type, count)

            # Detail by type
            for opp_type in ["Stronghold", "Growth Opportunity",
                             "Basket Opportunity", "Retention Risk"]:
                subset = odf[odf["opportunity_type"] == opp_type]
                if not subset.empty:
                    with st.expander("{} — {} postcodes".format(
                            opp_type, len(subset))):
                        display = subset[["region_name", "postcode",
                                          "market_share_pct", "penetration_pct",
                                          "spend_per_customer", "nearest_store",
                                          "distance_km", "distance_tier"]].copy()
                        display.columns = [
                            "Region", "Postcode", "Share %", "Penetration %",
                            "Spend $", "Nearest Store", "Distance km", "Tier",
                        ]
                        st.dataframe(
                            display.sort_values("Share %", ascending=False),
                            use_container_width=True, hide_index=True,
                            key="ms_opp_{}".format(opp_type.replace(" ", "_")),
                        )

    # ── Issue Radar ──
    st.markdown("---")
    st.subheader("Issue Radar")
    st.caption("Postcodes with concerning trends — Core and Primary trade "
               "areas prioritised.")

    issues = flag_issues(latest, channel)
    if not issues:
        st.success("No significant issues detected for the current period.")
    else:
        if state_filter != "All":
            fn = STATE_RANGES.get(state_filter)
            if fn:
                issues = [i for i in issues if fn(i["postcode"])]

        urgent = [i for i in issues if i["severity"] == "Urgent"]
        warnings = [i for i in issues if i["severity"] == "Warning"]

        ik1, ik2, ik3 = st.columns(3)
        ik1.metric("Total Issues", len(issues))
        ik2.metric("Urgent", len(urgent),
                    delta="{} need attention".format(len(urgent)),
                    delta_color="inverse")
        ik3.metric("Warnings", len(warnings))

        if urgent:
            st.markdown("### Urgent Issues")
            st.caption("Core and Primary trade area postcodes losing share "
                       "— requires immediate investigation.")
            for issue in urgent:
                flags_str = " | ".join(issue["flags"])
                st.markdown(
                    "**{}** ({}) — Share: {:.1f}% ({:+.1f}pp YoY) — "
                    "*{}* ({:.0f}km, {})\n\n> {}".format(
                        issue["region_name"], issue["postcode"],
                        issue["current_share"], issue["share_change"],
                        issue["nearest_store"], issue["distance_km"],
                        issue["distance_tier"], flags_str,
                    )
                )

        if warnings:
            with st.expander("Warnings — {} postcodes".format(len(warnings))):
                wdf = pd.DataFrame(warnings)
                wdf["flags_str"] = wdf["flags"].apply(
                    lambda x: " | ".join(x))
                display = wdf[["region_name", "postcode", "current_share",
                               "share_change", "nearest_store",
                               "distance_tier", "flags_str"]].copy()
                display.columns = ["Region", "Postcode", "Share %",
                                   "Change pp", "Nearest Store", "Tier",
                                   "Flags"]
                st.dataframe(display, use_container_width=True,
                             hide_index=True, key="ms_issue_warn_tbl")

    # ── Sudden Shifts ──
    st.markdown("---")
    st.subheader("Sudden Shifts (Month-on-Month)")
    st.caption("Postcodes with >2pp month-on-month share change — "
               "may indicate data anomaly or real market event.")

    shift_threshold = st.slider("Shift Threshold (pp)", 1.0, 5.0, 2.0, 0.5,
                                key="ms_shift_threshold")
    shifts = detect_shifts(channel, shift_threshold)
    if shifts:
        sdf = pd.DataFrame(shifts[:100])
        sdf["period_label"] = sdf["current_period"].apply(fmt_period)
        st.dataframe(
            sdf[["period_label", "region_name", "region_code",
                 "prior_share", "current_share", "shift"]].rename(columns={
                "period_label": "Period", "region_name": "Region",
                "region_code": "Postcode", "prior_share": "Prior %",
                "current_share": "Current %", "shift": "Shift (pp)",
            }),
            use_container_width=True, hide_index=True, height=400,
            key="ms_shifts_tbl",
        )
    else:
        st.info("No shifts above {}pp threshold found.".format(
            shift_threshold))

    # ── Postcode Deep-Dive ──
    st.markdown("---")
    st.subheader("Postcode Deep-Dive")
    pc_input = st.text_input(
        "Enter postcode for trend analysis", placeholder="e.g. 2070",
        key="ms_pc_input",
    )
    if pc_input:
        trend_data = postcode_trend(pc_input, channel)
        if not trend_data:
            st.info("No data for postcode {}.".format(pc_input))
        else:
            pcdf = pd.DataFrame(trend_data)
            pcdf["period_date"] = pd.to_datetime(
                pcdf["period"].astype(str), format="%Y%m")

            store_name, dist_km, tier = nearest_store(pc_input)
            if store_name:
                st.caption("Nearest store: **{}** ({:.1f}km, {})".format(
                    store_name, dist_km, tier))

            c1, c2 = st.columns(2)
            with c1:
                fig_pc = px.line(
                    pcdf, x="period_date", y="market_share_pct",
                    labels={"period_date": "",
                            "market_share_pct": "Market Share %"},
                    color_discrete_sequence=["#2ECC71"],
                    title="Market Share Trend",
                )
                fig_pc.update_layout(height=300)
                st.plotly_chart(fig_pc, use_container_width=True,
                                key="ms_pc_share")
            with c2:
                fig_pen = px.line(
                    pcdf, x="period_date", y="customer_penetration_pct",
                    labels={"period_date": "",
                            "customer_penetration_pct": "Penetration %"},
                    color_discrete_sequence=["#7c3aed"],
                    title="Customer Penetration Trend",
                )
                fig_pen.update_layout(height=300)
                st.plotly_chart(fig_pen, use_container_width=True,
                                key="ms_pc_pen")

            c3, c4 = st.columns(2)
            with c3:
                fig_sp = px.line(
                    pcdf, x="period_date", y="spend_per_customer",
                    labels={"period_date": "",
                            "spend_per_customer": "Spend ($)"},
                    color_discrete_sequence=["#d97706"],
                    title="Spend per Customer Trend",
                )
                fig_sp.update_layout(height=300)
                st.plotly_chart(fig_sp, use_container_width=True,
                                key="ms_pc_spend")
            with c4:
                fig_mk = px.line(
                    pcdf, x="period_date", y="market_size_dollars",
                    labels={"period_date": "",
                            "market_size_dollars": "Market Size ($)"},
                    color_discrete_sequence=["#6366f1"],
                    title="Market Size Trend (directional only)",
                )
                fig_mk.update_layout(height=300)
                st.plotly_chart(fig_mk, use_container_width=True,
                                key="ms_pc_mkt")

    one_thing_box(
        "Growth Frontiers are <b>directional signals</b>, not investment cases. "
        "Before acting on any opportunity flag, validate with: (1) distance analysis, "
        "(2) demographic fit, (3) cannibalisation risk, and (4) existing store capacity."
    )
