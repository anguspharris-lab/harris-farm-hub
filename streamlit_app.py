"""
Harris Farm Hub — Standalone Streamlit App
Pure Streamlit. Zero FastAPI/uvicorn dependencies.
Reads directly from CSV data files in data/.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Harris Farm Hub",
    page_icon="\U0001f34e",
    layout="wide",
)

HFM_GREEN = "#4ba021"
HFM_DARK = "#171819"
DATA_DIR = Path(__file__).parent / "data"


# ---------------------------------------------------------------------------
# PASSWORD GATE
# ---------------------------------------------------------------------------

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("\U0001f512 Harris Farm Hub")
        pw = st.text_input("Password:", type="password")
        if st.button("Login"):
            if pw == "HFM2026!1":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        st.stop()


check_password()


# ---------------------------------------------------------------------------
# DATA LOADERS (cached, CSV only — no backend, no duckdb)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600)
def load_sales():
    """Load sales_by_major_group.csv and melt from wide to long format."""
    path = DATA_DIR / "sales_by_major_group.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    id_cols = [c for c in df.columns if not c.startswith("20")]
    date_cols = [c for c in df.columns if c.startswith("20")]
    long = df.melt(id_vars=id_cols, value_vars=date_cols,
                   var_name="week_ending", value_name="value")
    long["week_ending"] = pd.to_datetime(long["week_ending"])
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long


@st.cache_data(ttl=600)
def load_stores():
    path = DATA_DIR / "store_master.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


@st.cache_data(ttl=600)
def load_market_share():
    path = DATA_DIR / "market_share.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    for col in ["Market Size ($)", "Market Share (%)", "Customer Penetration (%)",
                 "Spend per Customer ($)", "Spend per Transaction ($)",
                 "Transactions per Customer (#)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(ttl=600)
def load_customers():
    path = DATA_DIR / "customers_by_store.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    id_cols = [c for c in df.columns if not c.startswith("20")]
    date_cols = [c for c in df.columns if c.startswith("20")]
    long = df.melt(id_vars=id_cols, value_vars=date_cols,
                   var_name="week_ending", value_name="value")
    long["week_ending"] = pd.to_datetime(long["week_ending"])
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long


# ---------------------------------------------------------------------------
# BRANDING
# ---------------------------------------------------------------------------

def render_header():
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:8px;'>"
        f"<span style='font-size:2.2em;'>\U0001f34e</span>"
        f"<div>"
        f"<span style='font-size:1.6em;font-weight:700;color:{HFM_GREEN};'>Harris Farm Hub</span>"
        f"<br><span style='font-size:0.85em;color:#6b7280;'>AI Centre of Excellence</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown("---")
    st.caption("Harris Farm Markets | Family owned since '71. AI-powered since '26.")


# ---------------------------------------------------------------------------
# PAGES
# ---------------------------------------------------------------------------

def page_home():
    render_header()

    st.markdown(
        f"<div style='background:linear-gradient(135deg,{HFM_GREEN} 0%,#3a8019 100%);"
        "color:white;padding:20px 28px;border-radius:10px;margin:12px 0 20px 0;'>"
        "<div style='font-size:1.3em;font-weight:700;margin-bottom:6px;'>"
        "Fewer, Bigger, Better</div>"
        "<div style='font-size:0.95em;opacity:0.95;'>"
        "Our strategy to become Australia's most loved fresh food retailer. "
        "The Hub brings data-driven insights to every Harris Farmer.</div></div>",
        unsafe_allow_html=True,
    )

    sales = load_sales()
    stores = load_stores()
    ms = load_market_share()

    if sales is not None:
        rev = sales[sales["Measure"] == "Sales - Val"]
        total_rev = rev["value"].sum()
        store_count = rev["Store"].nunique()
        latest_week = rev["week_ending"].max().strftime("%Y-%m-%d")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Stores", store_count)
        k2.metric("Total Revenue", f"${total_rev / 1e9:.2f}B")
        k3.metric("Data Through", latest_week)
        if ms is not None:
            avg_share = ms["Market Share (%)"].mean()
            k4.metric("Avg Market Share", f"{avg_share:.1f}%")
        else:
            k4.metric("Avg Market Share", "-")
    else:
        st.info("No sales data found. Place sales_by_major_group.csv in data/.")

    st.markdown("")
    st.markdown(
        "<div style='background:#f0fdf4;border-left:4px solid #4ba021;"
        "padding:16px 20px;border-radius:0 8px 8px 0;'>"
        "<strong>5 Strategic Pillars</strong><br>"
        "<span style='color:#6b7280;font-size:0.9em;'>"
        "1. For The Greater Goodness | "
        "2. Smashing It for the Customer | "
        "3. Growing Legendary Leadership | "
        "4. Today's Business, Done Better | "
        "5. Tomorrow's Business, Built Better"
        "</span></div>",
        unsafe_allow_html=True,
    )

    if sales is not None:
        st.markdown("### Weekly Revenue Trend (All Stores)")
        rev = sales[sales["Measure"] == "Sales - Val"]
        weekly = rev.groupby("week_ending")["value"].sum().reset_index()
        weekly = weekly.sort_values("week_ending").tail(52)
        fig = px.area(weekly, x="week_ending", y="value",
                      labels={"week_ending": "Week", "value": "Revenue ($)"},
                      color_discrete_sequence=[HFM_GREEN])
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=10, b=20))
        fig.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)

    render_footer()


def page_sales():
    render_header()
    st.title("Sales Dashboard")

    sales = load_sales()
    if sales is None:
        st.warning("Sales data not available. Place sales_by_major_group.csv in data/.")
        render_footer()
        return

    rev = sales[sales["Measure"] == "Sales - Val"].copy()

    # Filters
    c1, c2 = st.columns(2)
    all_stores = sorted(rev["Store"].dropna().unique())
    with c1:
        selected_stores = st.multiselect("Stores", all_stores, default=[])
    all_depts = sorted(rev["Dept"].dropna().unique())
    with c2:
        selected_depts = st.multiselect("Departments", all_depts, default=[])

    if selected_stores:
        rev = rev[rev["Store"].isin(selected_stores)]
    if selected_depts:
        rev = rev[rev["Dept"].isin(selected_depts)]

    # KPIs
    total = rev["value"].sum()
    latest_13 = rev[rev["week_ending"] >= rev["week_ending"].max() - pd.Timedelta(weeks=13)]
    rolling_13 = latest_13["value"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Revenue", f"${total / 1e6:,.1f}M")
    m2.metric("Rolling 13-Wk Revenue", f"${rolling_13 / 1e6:,.1f}M")
    m3.metric("Stores in View", rev["Store"].nunique())

    # Revenue by store
    st.subheader("Revenue by Store")
    by_store = (rev.groupby("Store")["value"].sum()
                .sort_values(ascending=True).tail(15).reset_index())
    fig = px.bar(by_store, x="value", y="Store", orientation="h",
                 color_discrete_sequence=[HFM_GREEN],
                 labels={"value": "Revenue ($)", "Store": ""})
    fig.update_layout(height=450, margin=dict(l=20, r=20, t=10, b=20))
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

    # Revenue by department
    st.subheader("Revenue by Department")
    by_dept = rev.groupby("Dept")["value"].sum().sort_values(ascending=False).reset_index()
    fig2 = px.pie(by_dept, values="value", names="Dept", hole=0.4,
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig2.update_layout(height=400, margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig2, use_container_width=True)

    # Weekly trend
    st.subheader("Weekly Sales Trend")
    weekly = rev.groupby("week_ending")["value"].sum().reset_index()
    weekly = weekly.sort_values("week_ending").tail(52)
    fig3 = px.line(weekly, x="week_ending", y="value",
                   labels={"week_ending": "Week", "value": "Revenue ($)"},
                   color_discrete_sequence=[HFM_GREEN])
    fig3.update_layout(height=350, margin=dict(l=20, r=20, t=10, b=20))
    fig3.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig3, use_container_width=True)

    render_footer()


def page_profitability():
    render_header()
    st.title("Profitability Dashboard")

    sales = load_sales()
    if sales is None:
        st.warning("Sales data not available.")
        render_footer()
        return

    rev = sales[sales["Measure"] == "Sales - Val"]
    gp = sales[sales["Measure"] == "Final Gross Prod - Val"]
    shrink = sales[sales["Measure"] == "Total Shrinkage - Val"]

    total_rev = rev["value"].sum()
    total_gp = gp["value"].sum()
    total_shrink = shrink["value"].sum()
    gp_pct = (total_gp / total_rev * 100) if total_rev else 0
    shrink_pct = (total_shrink / total_rev * 100) if total_rev else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue", f"${total_rev / 1e6:,.1f}M")
    m2.metric("Gross Profit", f"${total_gp / 1e6:,.1f}M")
    m3.metric("GP %", f"{gp_pct:.1f}%")
    m4.metric("Shrinkage %", f"{shrink_pct:.1f}%")

    # GP% by department
    st.subheader("Gross Profit % by Department")
    rev_dept = rev.groupby("Dept")["value"].sum()
    gp_dept = gp.groupby("Dept")["value"].sum()
    gp_pct_dept = (gp_dept / rev_dept * 100).dropna().sort_values(ascending=True).reset_index()
    gp_pct_dept.columns = ["Dept", "GP%"]

    fig = px.bar(gp_pct_dept, x="GP%", y="Dept", orientation="h",
                 color="GP%", color_continuous_scale=["#ef4444", "#eab308", HFM_GREEN],
                 labels={"GP%": "Gross Profit %", "Dept": ""})
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # GP% by store
    st.subheader("Gross Profit % by Store (Top 15)")
    rev_store = rev.groupby("Store")["value"].sum()
    gp_store = gp.groupby("Store")["value"].sum()
    gp_pct_store = (gp_store / rev_store * 100).dropna().sort_values(ascending=True)
    gp_pct_store = gp_pct_store.tail(15).reset_index()
    gp_pct_store.columns = ["Store", "GP%"]

    fig2 = px.bar(gp_pct_store, x="GP%", y="Store", orientation="h",
                  color_discrete_sequence=[HFM_GREEN],
                  labels={"GP%": "Gross Profit %", "Store": ""})
    fig2.update_layout(height=450, margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig2, use_container_width=True)

    # Weekly GP trend
    st.subheader("Weekly GP% Trend")
    rev_wk = rev.groupby("week_ending")["value"].sum()
    gp_wk = gp.groupby("week_ending")["value"].sum()
    gp_trend = (gp_wk / rev_wk * 100).dropna().reset_index()
    gp_trend.columns = ["week_ending", "GP%"]
    gp_trend = gp_trend.sort_values("week_ending").tail(52)
    fig3 = px.line(gp_trend, x="week_ending", y="GP%",
                   labels={"week_ending": "Week"},
                   color_discrete_sequence=[HFM_GREEN])
    fig3.update_layout(height=300, margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig3, use_container_width=True)

    render_footer()


def page_market_share():
    render_header()
    st.title("Market Share Dashboard")

    ms = load_market_share()
    if ms is None:
        st.warning("Market share data not available.")
        render_footer()
        return

    instore = ms[ms["Channel"] == "Instore"].copy()

    if instore.empty:
        st.info("No instore market share data found.")
        render_footer()
        return

    avg_share = instore["Market Share (%)"].mean()
    avg_penetration = instore["Customer Penetration (%)"].mean()
    avg_spend = instore["Spend per Customer ($)"].mean()

    m1, m2, m3 = st.columns(3)
    m1.metric("Avg Market Share", f"{avg_share:.2f}%")
    m2.metric("Avg Penetration", f"{avg_penetration:.1f}%")
    m3.metric("Avg Spend/Customer", f"${avg_spend:.2f}")

    # Share by region
    st.subheader("Market Share by Region")
    latest_period = instore["Period"].max()
    latest = instore[instore["Period"] == latest_period]
    by_region = (latest.groupby("Region Name")["Market Share (%)"]
                 .mean().sort_values(ascending=True).tail(20).reset_index())

    fig = px.bar(by_region, x="Market Share (%)", y="Region Name", orientation="h",
                 color_discrete_sequence=[HFM_GREEN],
                 labels={"Region Name": ""})
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # Trend over time
    st.subheader("Market Share Trend")
    trend = instore.groupby("Period")["Market Share (%)"].mean().reset_index()
    trend = trend.sort_values("Period")
    fig2 = px.line(trend, x="Period", y="Market Share (%)",
                   color_discrete_sequence=[HFM_GREEN])
    fig2.update_layout(height=300, margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig2, use_container_width=True)

    render_footer()


def page_customers():
    render_header()
    st.title("Customer Dashboard")

    cust = load_customers()
    if cust is None:
        st.warning("Customer data not available.")
        render_footer()
        return

    actual = cust[cust["Measure"] == "Customer Count"].copy()
    if actual.empty:
        st.info("No customer count data found.")
        render_footer()
        return

    total_visits = actual["value"].sum()
    store_count = actual["Store"].nunique()

    m1, m2 = st.columns(2)
    m1.metric("Total Customer Visits", f"{total_visits / 1e6:,.1f}M")
    m2.metric("Stores Tracked", store_count)

    # Weekly trend
    st.subheader("Weekly Customer Visits")
    weekly = actual.groupby("week_ending")["value"].sum().reset_index()
    weekly = weekly.sort_values("week_ending").tail(52)
    fig = px.area(weekly, x="week_ending", y="value",
                  labels={"week_ending": "Week", "value": "Customer Visits"},
                  color_discrete_sequence=[HFM_GREEN])
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=10, b=20))
    fig.update_yaxes(tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

    # By store
    st.subheader("Customer Visits by Store (Top 15)")
    by_store = (actual.groupby("Store")["value"].sum()
                .sort_values(ascending=True).tail(15).reset_index())
    fig2 = px.bar(by_store, x="value", y="Store", orientation="h",
                  color_discrete_sequence=[HFM_GREEN],
                  labels={"value": "Customer Visits", "Store": ""})
    fig2.update_layout(height=450, margin=dict(l=20, r=20, t=10, b=20))
    fig2.update_xaxes(tickformat=",.0f")
    st.plotly_chart(fig2, use_container_width=True)

    render_footer()


# ---------------------------------------------------------------------------
# NAVIGATION
# ---------------------------------------------------------------------------

PAGES = {
    "\U0001f3e0 Home": page_home,
    "\U0001f4ca Sales": page_sales,
    "\U0001f4b0 Profitability": page_profitability,
    "\U0001f5fa Market Share": page_market_share,
    "\U0001f465 Customers": page_customers,
}

with st.sidebar:
    st.markdown(
        f"<div style='text-align:center;margin-bottom:16px;'>"
        f"<span style='font-size:2.5em;'>\U0001f34e</span><br>"
        f"<span style='font-weight:700;color:{HFM_GREEN};font-size:1.2em;'>"
        f"Harris Farm Hub</span></div>",
        unsafe_allow_html=True,
    )
    page = st.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
    st.markdown("---")
    st.caption("Family owned since '71")
    st.caption("AI-powered since '26")

PAGES[page]()
