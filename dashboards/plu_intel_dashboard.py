"""
Harris Farm Hub — PLU Intelligence Dashboard
Weekly PLU performance: wastage, shrinkage, sales, margins, store benchmarking.
27.3M rows · 3 fiscal years · 43 stores · 26K+ PLUs
"""

import pandas as pd
import streamlit as st

from plu_layer import (
    db_available, get_departments, get_stores, get_fiscal_years,
    department_summary, store_performance, top_plus_by_wastage,
    top_plus_by_stocktake, top_plus_by_revenue, plu_weekly_trend,
    plu_store_breakdown, search_plu, weekly_department_trend,
)
from shared.styles import HFM_GREEN

user = st.session_state.get("auth_user")

st.title("PLU Intelligence")
st.caption("Weekly product-level performance across 43 stores · Wastage · Shrinkage · Margins")

if not db_available():
    st.error("PLU database not found. Place `harris_farm_plu.db` in the `data/` directory.")
    st.stop()

# ── Filters ──────────────────────────────────────────────────────────────────
fiscal_years = get_fiscal_years()
departments = get_departments()

col_fy, col_dept, col_view = st.columns([1, 2, 2])
with col_fy:
    fy = st.selectbox("Fiscal Year", fiscal_years, index=len(fiscal_years) - 1)
with col_dept:
    dept_options = ["All Departments"] + departments
    dept_sel = st.selectbox("Department", dept_options)
    dept = None if dept_sel == "All Departments" else dept_sel
with col_view:
    view = st.selectbox("View", [
        "Department Summary",
        "Wastage Hotspots",
        "Stocktake Variance",
        "Top Revenue PLUs",
        "Store Benchmarking",
        "PLU Lookup",
    ])

st.markdown("---")

# ── Department Summary ────────────────────────────────────────────────────────
if view == "Department Summary":
    data = department_summary(fiscal_year=fy)
    if not data:
        st.info("No data for selected filters.")
        st.stop()

    df = pd.DataFrame(data)
    df = df[df["sales"] > 0]

    # KPIs
    total_sales = df["sales"].sum()
    total_gm = df["gm"].sum()
    total_waste = df["wastage"].sum()
    total_stock = df["stocktake"].sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Sales", f"${total_sales / 1e6:,.1f}M")
    k2.metric("Gross Margin", f"${total_gm / 1e6:,.1f}M", f"{total_gm / total_sales * 100:.1f}%")
    k3.metric("Wastage", f"${total_waste / 1e6:,.1f}M", f"{total_waste / total_sales * 100:.1f}%")
    k4.metric("Stocktake Adj", f"${total_stock / 1e6:,.1f}M")

    st.markdown("")
    st.subheader("By Department")
    display = df.rename(columns={
        "department": "Department", "sales": "Sales $", "gm": "GM $",
        "gm_pct": "GM %", "wastage": "Wastage $", "wastage_pct": "Waste %",
        "stocktake": "Stocktake $", "plu_count": "PLUs",
    })
    st.dataframe(
        display[["Department", "Sales $", "GM $", "GM %", "Wastage $", "Waste %", "Stocktake $", "PLUs"]],
        use_container_width=True, hide_index=True,
    )

    # Department trend chart
    if dept:
        st.subheader(f"{dept} — Weekly Trend")
        trend = weekly_department_trend(dept)
        if trend:
            tdf = pd.DataFrame(trend)
            tdf["period"] = tdf["fiscal_year"].astype(str) + "-W" + tdf["fiscal_week"].astype(str).str.zfill(2)
            chart_data = tdf.set_index("period")[["sales", "wastage"]].rename(
                columns={"sales": "Sales", "wastage": "Wastage"}
            )
            st.line_chart(chart_data)

# ── Wastage Hotspots ──────────────────────────────────────────────────────────
elif view == "Wastage Hotspots":
    st.subheader(f"Top 50 PLUs by Wastage — FY{fy}")
    data = top_plus_by_wastage(fiscal_year=fy, department=dept, limit=50)
    if not data:
        st.info("No wastage data for selected filters.")
        st.stop()

    df = pd.DataFrame(data)
    st.dataframe(
        df.rename(columns={
            "plu_code": "PLU", "description": "Description", "department": "Dept",
            "major_group": "Group", "total_wastage": "Wastage $",
            "total_sales": "Sales $", "wastage_pct": "Waste %", "store_count": "Stores",
        })[["PLU", "Description", "Dept", "Wastage $", "Sales $", "Waste %", "Stores"]],
        use_container_width=True, hide_index=True,
    )

    total_waste = df["total_wastage"].sum()
    st.metric("Total Wastage (top 50 PLUs)", f"${total_waste:,.0f}")

# ── Stocktake Variance ────────────────────────────────────────────────────────
elif view == "Stocktake Variance":
    st.subheader(f"Top 50 PLUs by Stocktake Variance — FY{fy}")
    data = top_plus_by_stocktake(fiscal_year=fy, department=dept, limit=50)
    if not data:
        st.info("No stocktake data for selected filters.")
        st.stop()

    df = pd.DataFrame(data)
    st.dataframe(
        df.rename(columns={
            "plu_code": "PLU", "description": "Description", "department": "Dept",
            "total_variance": "Variance $", "total_sales": "Sales $",
            "variance_pct": "Var %",
        })[["PLU", "Description", "Dept", "Variance $", "Sales $", "Var %"]],
        use_container_width=True, hide_index=True,
    )

# ── Top Revenue PLUs ──────────────────────────────────────────────────────────
elif view == "Top Revenue PLUs":
    st.subheader(f"Top 50 PLUs by Revenue — FY{fy}")
    data = top_plus_by_revenue(fiscal_year=fy, department=dept, limit=50)
    if not data:
        st.info("No data for selected filters.")
        st.stop()

    df = pd.DataFrame(data)
    st.dataframe(
        df.rename(columns={
            "plu_code": "PLU", "description": "Description", "department": "Dept",
            "major_group": "Group", "sales": "Sales $", "gm": "GM $",
            "gm_pct": "GM %", "store_count": "Stores",
        })[["PLU", "Description", "Dept", "Sales $", "GM $", "GM %", "Stores"]],
        use_container_width=True, hide_index=True,
    )

# ── Store Benchmarking ────────────────────────────────────────────────────────
elif view == "Store Benchmarking":
    st.subheader(f"Store Performance — FY{fy}")
    data = store_performance(fiscal_year=fy)
    if not data:
        st.info("No data.")
        st.stop()

    df = pd.DataFrame(data)

    # KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Stores", len(df))
    k2.metric("Avg GM%", f"{df['gm_pct'].mean():.1f}%")
    k3.metric("Avg Waste%", f"{df['wastage_pct'].mean():.1f}%")

    st.dataframe(
        df.rename(columns={
            "store_name": "Store", "sales": "Sales $", "gm": "GM $",
            "gm_pct": "GM %", "wastage": "Wastage $", "wastage_pct": "Waste %",
            "active_plus": "Active PLUs",
        })[["Store", "Sales $", "GM $", "GM %", "Wastage $", "Waste %", "Active PLUs"]],
        use_container_width=True, hide_index=True,
    )

    # Bar charts
    chart_df = df[df["sales"] > 0].sort_values("wastage_pct")
    st.subheader("Wastage Rate by Store")
    st.bar_chart(chart_df.set_index("store_name")["wastage_pct"])

# ── PLU Lookup ────────────────────────────────────────────────────────────────
elif view == "PLU Lookup":
    st.subheader("Search PLU")
    query = st.text_input("PLU code or description", placeholder="e.g. avocado, 4152, banana")

    if query:
        results = search_plu(query, limit=30)
        if not results:
            st.info("No PLUs found.")
            st.stop()

        df = pd.DataFrame(results)
        selected = st.selectbox(
            "Select PLU",
            df["plu_code"].tolist(),
            format_func=lambda x: f"{x} — {df[df['plu_code']==x]['description'].values[0]}"
        )

        if selected:
            st.markdown("---")
            st.subheader(f"PLU {selected}")
            item = df[df["plu_code"] == selected].iloc[0]
            st.markdown(f"**{item['description']}** · {item['department']} · {item['major_group']} · {item['minor_group']}")

            # Weekly trend
            trend = plu_weekly_trend(selected)
            if trend:
                tdf = pd.DataFrame(trend)
                tdf["period"] = tdf["fiscal_year"].astype(str) + "-W" + tdf["fiscal_week"].astype(str).str.zfill(2)

                t1, t2 = st.columns(2)
                with t1:
                    st.markdown("**Sales Trend**")
                    st.line_chart(tdf.set_index("period")["sales"])
                with t2:
                    st.markdown("**Wastage Trend**")
                    st.line_chart(tdf.set_index("period")["wastage"])

            # Store breakdown
            stores = plu_store_breakdown(selected, fiscal_year=fy)
            if stores:
                st.markdown(f"**Store Breakdown — FY{fy}**")
                sdf = pd.DataFrame(stores)
                st.dataframe(
                    sdf.rename(columns={
                        "store_name": "Store", "sales": "Sales $", "gm": "GM $",
                        "wastage": "Wastage $", "stocktake": "Stocktake $",
                    })[["Store", "Sales $", "GM $", "Wastage $", "Stocktake $"]],
                    use_container_width=True, hide_index=True,
                )
