"""
Customer Hub — Customer Insights > Known Customers
RFM segmentation, LTV tiers, frequency distribution, and department mix
from DuckDB transaction-level data.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from customer_hub.components import (
    PALETTE, SEGMENT_COLORS, section_header, insight_callout, one_thing_box,
)
from transaction_layer import TransactionStore
from transaction_queries import run_query


@st.cache_resource
def _get_store():
    return TransactionStore()


@st.cache_data(ttl=300, show_spinner="Querying transactions...")
def _query(name, **kwargs):
    return run_query(_get_store(), name, **kwargs)


def render():
    txn_start = st.session_state.get("ch_txn_start")
    txn_end = st.session_state.get("ch_txn_end")
    if not txn_start or not txn_end:
        st.info("Select a period in the Overview tab first.")
        return

    section_header(
        "Known Customers",
        "Analysis of identified loyalty customers (~12% of transactions). "
        "Despite the small subset, these represent high-engagement shoppers "
        "with rich behavioural data.",
    )

    try:
        rfm_data = _query("customer_rfm_segments", start=txn_start, end=txn_end)
    except Exception as e:
        st.error("Could not load customer data: {}".format(e))
        rfm_data = []

    if not rfm_data:
        st.info("No loyalty customer data available for the selected period.")
        return

    df_rfm = pd.DataFrame(rfm_data)

    # ── KPIs ──
    total_identified = len(df_rfm)
    avg_ltv = df_rfm["monetary"].mean()
    avg_freq = df_rfm["frequency"].mean()
    multi_store = (df_rfm["stores_visited"] >= 2).sum()
    multi_store_pct = multi_store / total_identified * 100

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Identified Customers", "{:,}".format(total_identified))
    k2.metric("Avg Lifetime Value", "${:,.0f}".format(avg_ltv))
    k3.metric("Avg Visit Frequency", "{:.1f} visits".format(avg_freq))
    k4.metric("Multi-Store Shoppers", "{:.1f}%".format(multi_store_pct))

    # Known vs Unknown insight
    insight_callout(
        "Only <b>~12%</b> of transactions carry a loyalty code, but these "
        "customers disproportionately drive value. Champions alone average "
        "<b>${:,.0f}</b> in spend. The opportunity: convert more anonymous "
        "shoppers into known, targetable customers.".format(
            df_rfm[df_rfm["segment"] == "Champion"]["monetary"].mean()
            if "Champion" in df_rfm["segment"].values else avg_ltv
        ),
        style="info",
    )

    # ── RFM Segmentation ──
    st.markdown("---")
    st.subheader("Customer Segmentation (RFM)")

    seg_summary = df_rfm.groupby("segment").agg(
        customers=("customercode", "count"),
        avg_spend=("monetary", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_recency=("recency_days", "mean"),
        total_revenue=("monetary", "sum"),
    ).reset_index()

    seg_order = ["Champion", "High-Value", "Regular", "Occasional", "Lapsed"]
    order_map = {s: i for i, s in enumerate(seg_order)}
    seg_summary["_order"] = seg_summary["segment"].map(order_map).fillna(99)
    seg_summary = seg_summary.sort_values("_order").drop(columns=["_order"])

    fig_seg = px.bar(
        seg_summary, x="customers", y="segment", orientation="h",
        color="segment", color_discrete_map=SEGMENT_COLORS,
        labels={"customers": "Customer Count", "segment": ""},
        text="customers",
    )
    fig_seg.update_layout(height=300, showlegend=False)
    fig_seg.update_traces(textposition="outside")
    st.plotly_chart(fig_seg, use_container_width=True, key="ch_rfm_segments")

    # Segment stats table
    seg_display = seg_summary.copy()
    seg_display.columns = [
        "Segment", "Customers", "Avg Spend ($)",
        "Avg Frequency", "Avg Recency (days)", "Total Revenue ($)",
    ]
    seg_display["Avg Spend ($)"] = seg_display["Avg Spend ($)"].apply(
        lambda x: "${:,.0f}".format(x))
    seg_display["Total Revenue ($)"] = seg_display["Total Revenue ($)"].apply(
        lambda x: "${:,.0f}".format(x))
    seg_display["Avg Frequency"] = seg_display["Avg Frequency"].apply(
        lambda x: "{:.1f}".format(x))
    seg_display["Avg Recency (days)"] = seg_display["Avg Recency (days)"].apply(
        lambda x: "{:.0f}".format(x))
    st.dataframe(seg_display, hide_index=True, use_container_width=True,
                 key="ch_seg_stats")

    # ── Purchase Frequency ──
    st.markdown("---")
    st.subheader("Purchase Frequency Distribution")
    try:
        freq_data = _query("customer_frequency_distribution",
                           start=txn_start, end=txn_end)
        if freq_data:
            df_freq = pd.DataFrame(freq_data)
            fig_freq = px.bar(
                df_freq, x="frequency_bucket", y="customer_count",
                color_discrete_sequence=[PALETTE["green"]],
                labels={"frequency_bucket": "Visit Frequency",
                        "customer_count": "Customers"},
                text="customer_count",
            )
            fig_freq.update_layout(height=350)
            fig_freq.update_traces(textposition="outside")
            st.plotly_chart(fig_freq, use_container_width=True,
                            key="ch_freq_hist")
    except Exception:
        st.info("Frequency distribution data unavailable.")

    # ── LTV Tiers ──
    st.markdown("---")
    st.subheader("Lifetime Value Tiers")
    try:
        ltv_data = _query("customer_ltv_tiers", start=txn_start, end=txn_end)
        if ltv_data:
            df_ltv = pd.DataFrame(ltv_data)
            ltv_colors = ["#059669", "#0d9488", "#3b82f6", "#f59e0b", "#94a3b8"]
            fig_ltv = px.bar(
                df_ltv, x="customer_count", y="ltv_tier", orientation="h",
                color="ltv_tier", color_discrete_sequence=ltv_colors,
                labels={"customer_count": "Customers", "ltv_tier": ""},
                text="customer_count",
            )
            fig_ltv.update_layout(height=300, showlegend=False)
            fig_ltv.update_traces(textposition="outside")
            st.plotly_chart(fig_ltv, use_container_width=True, key="ch_ltv_tiers")

            ltv_display = df_ltv[["ltv_tier", "customer_count", "avg_spend",
                                  "avg_visits", "avg_tenure_months",
                                  "projected_annual"]].copy()
            ltv_display.columns = [
                "Tier", "Customers", "Avg Spend ($)", "Avg Visits",
                "Avg Tenure (months)", "Projected Annual ($)",
            ]
            ltv_display["Avg Spend ($)"] = ltv_display["Avg Spend ($)"].apply(
                lambda x: "${:,.0f}".format(x))
            ltv_display["Projected Annual ($)"] = ltv_display[
                "Projected Annual ($)"].apply(lambda x: "${:,.0f}".format(x))
            ltv_display["Avg Visits"] = ltv_display["Avg Visits"].apply(
                lambda x: "{:.1f}".format(x))
            ltv_display["Avg Tenure (months)"] = ltv_display[
                "Avg Tenure (months)"].apply(lambda x: "{:.1f}".format(x))
            st.dataframe(ltv_display, hide_index=True, use_container_width=True,
                         key="ch_ltv_stats")
    except Exception:
        st.info("Lifetime value data unavailable.")

    # ── Top 20 ──
    st.markdown("---")
    st.subheader("Top 20 Customers by Spend")
    top_20 = df_rfm.head(20)[
        ["customercode", "segment", "monetary", "frequency",
         "stores_visited", "first_purchase", "last_purchase"]
    ].copy()
    top_20.columns = [
        "Customer", "Segment", "Total Spend ($)", "Visits",
        "Stores", "First Purchase", "Last Purchase",
    ]
    top_20["Total Spend ($)"] = top_20["Total Spend ($)"].apply(
        lambda x: "${:,.0f}".format(x))
    st.dataframe(top_20, hide_index=True, use_container_width=True,
                 key="ch_top20")

    # ── Department Mix ──
    st.markdown("---")
    st.subheader("Department Mix — Loyalty vs All Customers")
    try:
        dept_data = _query("customer_top_departments",
                           start=txn_start, end=txn_end)
        if dept_data:
            df_dept = pd.DataFrame(dept_data)
            df_dept = df_dept[df_dept["Department"].notna()]
            df_dept["loyalty_pct"] = (
                df_dept["loyalty_revenue"]
                / df_dept["loyalty_revenue"].sum() * 100
            )
            df_dept["total_pct"] = (
                df_dept["total_revenue"]
                / df_dept["total_revenue"].sum() * 100
            )
            dept_plot = df_dept.melt(
                id_vars=["Department"],
                value_vars=["loyalty_pct", "total_pct"],
                var_name="Group", value_name="Share %",
            )
            dept_plot["Group"] = dept_plot["Group"].map({
                "loyalty_pct": "Loyalty Customers",
                "total_pct": "All Customers",
            })
            fig_dept = px.bar(
                dept_plot, x="Share %", y="Department", color="Group",
                orientation="h", barmode="group",
                color_discrete_map={
                    "Loyalty Customers": PALETTE["green"],
                    "All Customers": "#94a3b8",
                },
                labels={"Department": ""},
            )
            fig_dept.update_layout(
                height=max(350, len(df_dept) * 40),
                legend=dict(orientation="h", y=-0.15),
            )
            st.plotly_chart(fig_dept, use_container_width=True,
                            key="ch_dept_mix")
    except Exception:
        st.info("Department mix data unavailable.")

    # ── Export ──
    st.markdown("---")
    exp1, exp2 = st.columns(2)
    with exp1:
        csv_seg = seg_summary.to_csv(index=False)
        st.download_button(
            "Download Segment Summary (CSV)", data=csv_seg,
            file_name="customer_segments.csv", mime="text/csv",
            key="ch_dl_segments",
        )
    with exp2:
        csv_top = df_rfm.head(100).to_csv(index=False)
        st.download_button(
            "Download Top 100 Customers (CSV)", data=csv_top,
            file_name="top_customers.csv", mime="text/csv",
            key="ch_dl_top",
        )

    one_thing_box(
        "Champions make up a tiny fraction of identified customers but "
        "generate an outsized share of revenue. Protect them at all costs."
    )
