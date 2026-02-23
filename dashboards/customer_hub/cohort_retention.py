"""
Customer Hub — Customer Insights > Cohort & Retention
Cohort retention heatmap, retention curves, new customer acquisition.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from customer_hub.components import (
    PALETTE, section_header, insight_callout, one_thing_box,
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
        "Cohort Retention Analysis",
        "Track how cohorts of new loyalty customers retain over time. "
        "Each cohort is defined by the month of first purchase.",
    )

    try:
        cohort_data = _query("customer_cohort_retention",
                             start=txn_start, end=txn_end)
    except Exception as e:
        st.error("Could not load cohort data: {}".format(e))
        cohort_data = []

    if not cohort_data:
        st.info("No cohort data available for the selected period.")
        return

    df_cohort = pd.DataFrame(cohort_data)
    df_cohort["cohort_month"] = pd.to_datetime(df_cohort["cohort_month"])

    cohort_sizes = df_cohort[df_cohort["months_since"] == 0].set_index(
        "cohort_month"
    )["active_customers"].to_dict()

    df_cohort["cohort_size"] = df_cohort["cohort_month"].map(cohort_sizes)
    df_cohort["retention_pct"] = (
        df_cohort["active_customers"]
        / df_cohort["cohort_size"] * 100
    ).fillna(0)

    # ── KPIs ──
    m1_retention = df_cohort[
        df_cohort["months_since"] == 1]["retention_pct"].mean()
    m3_retention = df_cohort[
        df_cohort["months_since"] == 3]["retention_pct"].mean()
    m6_retention = df_cohort[
        df_cohort["months_since"] == 6]["retention_pct"].mean()

    avg_lifespan = df_cohort.groupby("cohort_month").apply(
        lambda g: g[g["retention_pct"] >= 10]["months_since"].max()
    ).mean()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Month-1 Retention",
              "{:.1f}%".format(m1_retention) if pd.notna(m1_retention)
              else "N/A")
    k2.metric("Month-3 Retention",
              "{:.1f}%".format(m3_retention) if pd.notna(m3_retention)
              else "N/A")
    k3.metric("Month-6 Retention",
              "{:.1f}%".format(m6_retention) if pd.notna(m6_retention)
              else "N/A")
    k4.metric("Avg Active Lifespan",
              "{:.0f} months".format(avg_lifespan)
              if pd.notna(avg_lifespan) else "N/A")

    # Revenue math callout
    if pd.notna(m1_retention) and pd.notna(m6_retention):
        drop = m1_retention - m6_retention
        insight_callout(
            "We lose <b>{:.0f}pp</b> of new customers between month 1 and "
            "month 6. If we improved month-6 retention by just 5pp, that's "
            "hundreds more repeat shoppers generating compounding revenue.".format(drop),
            style="warning",
        )

    # ── Heatmap ──
    st.markdown("---")
    st.subheader("Retention Heatmap")

    recent_cohorts = sorted(cohort_sizes.keys())[-12:]
    heatmap_data = df_cohort[
        (df_cohort["cohort_month"].isin(recent_cohorts))
        & (df_cohort["months_since"] <= 12)
    ]

    if not heatmap_data.empty:
        pivot = heatmap_data.pivot_table(
            index="cohort_month", columns="months_since",
            values="retention_pct", aggfunc="mean",
        )
        pivot.index = [d.strftime("%b %Y") for d in pivot.index]
        pivot.columns = ["M{}".format(int(c)) for c in pivot.columns]

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[
                [0, "#ef4444"], [0.3, "#fbbf24"],
                [0.6, "#86efac"], [1, "#059669"],
            ],
            text=[["{:.0f}%".format(v) if pd.notna(v) else ""
                   for v in row] for row in pivot.values],
            texttemplate="%{text}",
            textfont={"size": 11},
            hovertemplate=(
                "Cohort: %{y}<br>Month: %{x}<br>"
                "Retention: %{z:.1f}%<extra></extra>"
            ),
        ))
        fig_heatmap.update_layout(
            height=max(350, len(pivot) * 35),
            xaxis_title="Months Since First Purchase",
            yaxis_title="Cohort",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_heatmap, use_container_width=True,
                        key="ch_cohort_heatmap")

    # ── Retention Curves ──
    st.markdown("---")
    st.subheader("Retention Curves")

    last_6 = sorted(cohort_sizes.keys())[-6:]
    curve_data = df_cohort[
        (df_cohort["cohort_month"].isin(last_6))
        & (df_cohort["months_since"] <= 12)
    ].copy()

    if not curve_data.empty:
        curve_data["cohort_label"] = curve_data["cohort_month"].dt.strftime(
            "%b %Y")
        fig_curves = px.line(
            curve_data, x="months_since", y="retention_pct",
            color="cohort_label",
            labels={"months_since": "Months Since First Purchase",
                    "retention_pct": "Retention %",
                    "cohort_label": "Cohort"},
            markers=True,
        )
        fig_curves.update_layout(height=400,
                                 legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_curves, use_container_width=True,
                        key="ch_retention_curves")

    # ── New Customer Acquisition ──
    st.markdown("---")
    st.subheader("Monthly New Customer Acquisition")

    acq_data = pd.DataFrame([
        {"month": k, "new_customers": v}
        for k, v in sorted(cohort_sizes.items())
    ])

    if not acq_data.empty:
        acq_data["month_label"] = pd.to_datetime(
            acq_data["month"]).dt.strftime("%b %Y")

        fig_acq = go.Figure()
        fig_acq.add_trace(go.Bar(
            x=acq_data["month_label"], y=acq_data["new_customers"],
            marker_color=PALETTE["green"], name="New Customers",
        ))
        if len(acq_data) >= 3:
            z = np.polyfit(range(len(acq_data)),
                           acq_data["new_customers"], 1)
            p = np.poly1d(z)
            fig_acq.add_trace(go.Scatter(
                x=acq_data["month_label"], y=p(range(len(acq_data))),
                mode="lines",
                line=dict(color=PALETTE["amber"], dash="dash", width=2),
                name="Trend",
            ))
        fig_acq.update_layout(
            height=350, xaxis_tickangle=-45,
            legend=dict(orientation="h", y=-0.25),
        )
        st.plotly_chart(fig_acq, use_container_width=True,
                        key="ch_acquisition_chart")

    # ── Export ──
    st.markdown("---")
    csv_cohort = df_cohort.to_csv(index=False)
    st.download_button(
        "Download Cohort Data (CSV)", data=csv_cohort,
        file_name="cohort_retention.csv", mime="text/csv",
        key="ch_dl_cohort",
    )

    one_thing_box(
        "Retention is the compounding engine of grocery. A 5pp improvement "
        "in month-3 retention can be worth more than a 10% increase in "
        "new customer acquisition."
    )
