"""
Harris Farm Hub - Sales Performance Dashboard
All KPIs derived from real transactional data in data/harris_farm.db.
Sales, GP, Budget, Shrinkage: every number traces to source weekly aggregates.
Store network: 27 Harris Farm Markets retail stores (real).
Data: Weekly by store, department, major group (FY2017-FY2024).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

# ============================================================================
# STYLING
# ============================================================================

from shared.styles import render_header, render_footer
from shared.ask_question import render_ask_question
from shared.voice_realtime import render_voice_data_box
from shared.fiscal_selector import render_fiscal_selector

user = st.session_state.get("auth_user")


# ============================================================================
# DATABASE PATH
# ============================================================================

def _get_db_path() -> Path:
    """Return path to harris_farm.db relative to project root."""
    return Path(__file__).resolve().parent.parent / "data" / "harris_farm.db"


def store_display_name(full_name: str) -> str:
    """'10 - HFM Pennant Hills' -> 'Pennant Hills'"""
    parts = full_name.split(" - ", 1)
    if len(parts) == 2:
        name = parts[1]
        if name.startswith("HFM "):
            name = name[4:]
        if name.startswith("HFM Meats "):
            name = name[10:]
        return name
    return full_name


# ============================================================================
# DATA LOADING — Real SQLite queries with Streamlit caching
# ============================================================================

@st.cache_data(ttl=300)
def load_stores():
    """Get sorted list of retail store names from DB."""
    db = _get_db_path()
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT store FROM sales
            WHERE channel = 'Retail'
            ORDER BY store
        """)
        return [row[0] for row in cursor.fetchall()]


@st.cache_data(ttl=300)
def load_departments():
    """Get sorted list of department names from sales data."""
    db = _get_db_path()
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT department FROM sales ORDER BY department
        """)
        return [row[0] for row in cursor.fetchall()]


@st.cache_data(ttl=300)
def load_major_groups(department=None):
    """Get major groups, optionally filtered by department."""
    db = _get_db_path()
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        if department:
            cursor.execute("""
                SELECT DISTINCT major_group FROM sales
                WHERE department = ? ORDER BY major_group
            """, (department,))
        else:
            cursor.execute("""
                SELECT DISTINCT major_group FROM sales ORDER BY major_group
            """)
        return [row[0] for row in cursor.fetchall()]


@st.cache_data(ttl=300)
def load_sales_data(date_from, date_to, stores=None, departments=None,
                    major_groups=None, promo='N'):
    """
    Load weekly sales data for all measures, pivoted wide.
    Returns DataFrame with columns: store, department, major_group, week_ending,
    plus one column per measure (sales, gp, initial_gp, budget_sales, budget_gp, shrinkage).
    """
    db = _get_db_path()

    query = """
        SELECT
            store, department, major_group, week_ending, measure, value
        FROM sales
        WHERE channel = 'Retail'
          AND is_promotion = ?
          AND week_ending >= ?
          AND week_ending <= ?
    """
    params = [promo, date_from, date_to]

    if stores:
        placeholders = ','.join('?' * len(stores))
        query += f" AND store IN ({placeholders})"
        params.extend(stores)

    if departments:
        placeholders = ','.join('?' * len(departments))
        query += f" AND department IN ({placeholders})"
        params.extend(departments)

    if major_groups:
        placeholders = ','.join('?' * len(major_groups))
        query += f" AND major_group IN ({placeholders})"
        params.extend(major_groups)

    with sqlite3.connect(db) as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if df.empty:
        return pd.DataFrame()

    # Pivot measures into columns
    measure_map = {
        'Sales - Val': 'sales',
        'Final Gross Prod - Val': 'gp',
        'Initial Gross Profit - Val': 'initial_gp',
        'Bgt Sales - Val': 'budget_sales',
        'Bgt Final GP - Val': 'budget_gp',
        'Total Shrinkage \u2013 Val': 'shrinkage',  # em-dash
    }

    df['measure_col'] = df['measure'].map(measure_map)
    df = df.dropna(subset=['measure_col'])

    pivoted = df.pivot_table(
        index=['store', 'department', 'major_group', 'week_ending'],
        columns='measure_col',
        values='value',
        aggfunc='sum'
    ).reset_index()

    pivoted.columns.name = None

    # Ensure all measure columns exist
    for col in measure_map.values():
        if col not in pivoted.columns:
            pivoted[col] = 0.0

    pivoted['week_ending'] = pd.to_datetime(pivoted['week_ending'])
    return pivoted


@st.cache_data(ttl=300)
def get_date_range():
    """Get min/max week_ending from sales data."""
    db = _get_db_path()
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(week_ending), MAX(week_ending) FROM sales")
        row = cursor.fetchone()
        return row[0], row[1]


def compute_period_delta(current_val, previous_val):
    """Return percentage change string for metric deltas."""
    if previous_val == 0:
        return None
    pct = (current_val - previous_val) / abs(previous_val) * 100
    return f"{pct:+.1f}%"


# ============================================================================
# HEADER
# ============================================================================

render_header(
    "Sales Performance",
    "**Harris Farm Markets** | Weekly sales, GP, budget & shrinkage analytics",
    goals=["G1", "G2", "G4"],
    strategy_context="Revenue is the scoreboard. AI reads the pattern \u2014 where growth is real, where it\u2019s seasonal, where we need to act.",
)
st.caption("\U0001f4a1 Step 5: Review this data. Add your judgment. Your experience makes this useful.")

# ============================================================================
# FILTERS
# ============================================================================

stores_list = load_stores()
departments_list = load_departments()
data_min, data_max = get_date_range()

# --- Fiscal Period Selector ---
filters = render_fiscal_selector(
    key_prefix="sales",
    show_comparison=True,
    show_store=False,
    allowed_fys=[2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
)

if not filters["start_date"]:
    st.stop()

date_from = filters["start_date"]
date_to = filters["end_date"]

# Comparison period
if filters["comparison"]:
    prev_from = filters["comparison"]["start"]
    prev_to = filters["comparison"]["end"]
else:
    prev_from = None
    prev_to = None

# --- Store / Department / Major Group Filters ---
col2, col3, col4 = st.columns(3)

with col2:
    store_options = ["All Stores"] + [
        store_display_name(s) + f" [{s.split(' - ')[0]}]" for s in stores_list
    ]
    store_filter = st.multiselect("Stores", store_options,
                                  default=["All Stores"], key="sales_stores")

with col3:
    dept_filter = st.multiselect(
        "Department",
        ["All Departments"] + departments_list,
        default=["All Departments"],
        key="sales_depts",
    )

with col4:
    # Cascading: show major groups for selected departments
    if "All Departments" not in dept_filter and dept_filter:
        available_mgs = []
        for d in dept_filter:
            available_mgs.extend(load_major_groups(d))
        available_mgs = sorted(set(available_mgs))
    else:
        available_mgs = load_major_groups()

    # Reset major group selection when options change
    mg_key = "sales_major_groups"
    current_mg = st.session_state.get(mg_key, ["All Major Groups"])
    valid_mg = [v for v in current_mg if v in (["All Major Groups"] + available_mgs)]
    if not valid_mg:
        valid_mg = ["All Major Groups"]

    mg_filter = st.multiselect(
        "Major Group",
        ["All Major Groups"] + available_mgs,
        default=valid_mg,
        key=mg_key,
    )

# Resolve store filter to DB store names
selected_stores = None
if "All Stores" not in store_filter and store_filter:
    # Extract store codes from filter labels like "Pennant Hills [10]"
    selected_stores = []
    for sf in store_filter:
        code = sf.split("[")[-1].rstrip("]") if "[" in sf else ""
        for s in stores_list:
            if s.startswith(code + " - "):
                selected_stores.append(s)
                break

selected_depts = None
if "All Departments" not in dept_filter and dept_filter:
    selected_depts = dept_filter

selected_mgs = None
if "All Major Groups" not in mg_filter and mg_filter:
    selected_mgs = mg_filter

# Coverage indicator
if filters.get("caveats"):
    for c in filters["caveats"]:
        st.caption(f"Note: {c}")
st.caption(f"Data range: {data_min} to {data_max}")

# ============================================================================
# LOAD DATA
# ============================================================================

df = load_sales_data(date_from, date_to, selected_stores, selected_depts,
                     selected_mgs)
if prev_from and prev_to:
    prev_df = load_sales_data(prev_from, prev_to, selected_stores, selected_depts,
                              selected_mgs)
else:
    prev_df = pd.DataFrame()

if df.empty:
    st.warning("No data found for the selected filters. Try broadening your selection.")
    st.stop()

# ============================================================================
# KEY METRICS
# ============================================================================

st.subheader("Key Performance Indicators")

total_sales = df['sales'].sum()
total_gp = df['gp'].sum()
gp_pct = (total_gp / total_sales * 100) if total_sales > 0 else 0
total_budget = df['budget_sales'].sum()
budget_var = ((total_sales - total_budget) / total_budget * 100) if total_budget > 0 else 0
total_shrinkage = df['shrinkage'].sum()
budget_gp_total = df['budget_gp'].sum()
budget_gp_pct = (budget_gp_total / total_budget * 100) if total_budget > 0 else 0

# Previous period
prev_sales = prev_df['sales'].sum() if not prev_df.empty else 0
prev_gp = prev_df['gp'].sum() if not prev_df.empty else 0
prev_gp_pct = (prev_gp / prev_sales * 100) if prev_sales > 0 else 0
prev_budget = prev_df['budget_sales'].sum() if not prev_df.empty else 0
prev_budget_var = ((prev_sales - prev_budget) / prev_budget * 100) if prev_budget > 0 else 0
prev_shrinkage = prev_df['shrinkage'].sum() if not prev_df.empty else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Total Sales", f"${total_sales:,.0f}",
              delta=compute_period_delta(total_sales, prev_sales))

with col2:
    st.metric("Gross Profit", f"${total_gp:,.0f}",
              delta=compute_period_delta(total_gp, prev_gp))

with col3:
    st.metric("GP %", f"{gp_pct:.1f}%",
              delta=compute_period_delta(gp_pct, prev_gp_pct),
              delta_color="normal")

with col4:
    st.metric("Budget Variance", f"{budget_var:+.1f}%",
              delta=compute_period_delta(budget_var, prev_budget_var),
              delta_color="normal")

with col5:
    st.metric("Shrinkage", f"${total_shrinkage:,.0f}",
              delta=compute_period_delta(total_shrinkage, prev_shrinkage),
              delta_color="inverse")

with col6:
    st.metric("Budget GP %", f"{budget_gp_pct:.1f}%")

st.markdown("---")

# ============================================================================
# WEEKLY SALES & PROFIT TREND
# ============================================================================

st.subheader("Weekly Sales & Profit Trend")

weekly = df.groupby('week_ending').agg(
    sales=('sales', 'sum'),
    gp=('gp', 'sum'),
    budget_sales=('budget_sales', 'sum'),
    shrinkage=('shrinkage', 'sum'),
).reset_index().sort_values('week_ending')

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=weekly['week_ending'], y=weekly['sales'],
    name='Sales', line=dict(color='#1e3a8a', width=2), fill='tozeroy',
))
fig_trend.add_trace(go.Scatter(
    x=weekly['week_ending'], y=weekly['gp'],
    name='Gross Profit', line=dict(color='#10b981', width=2), fill='tozeroy',
))
fig_trend.add_trace(go.Scatter(
    x=weekly['week_ending'], y=weekly['budget_sales'],
    name='Budget', line=dict(color='#f59e0b', width=1, dash='dash'),
))
fig_trend.add_trace(go.Scatter(
    x=weekly['week_ending'], y=weekly['shrinkage'],
    name='Shrinkage', line=dict(color='#ef4444', width=1, dash='dot'),
))
fig_trend.update_layout(
    height=400, hovermode='x unified',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    yaxis_title="Amount ($)",
)
st.plotly_chart(fig_trend, key="sales_trend_chart")

# ============================================================================
# STORE PERFORMANCE + DEPARTMENT MIX
# ============================================================================

col1, col2 = st.columns(2)

with col1:
    st.subheader("Store Performance")

    store_perf = df.groupby('store').agg(
        sales=('sales', 'sum'),
        gp=('gp', 'sum'),
        budget_sales=('budget_sales', 'sum'),
        shrinkage=('shrinkage', 'sum'),
    ).reset_index()
    store_perf['gp_pct'] = (
        store_perf['gp'] / store_perf['sales'] * 100
    ).where(store_perf['sales'] > 0, 0)
    store_perf['display_name'] = store_perf['store'].apply(store_display_name)
    store_perf = store_perf.sort_values('sales', ascending=True)

    fig_stores = px.bar(
        store_perf, x='sales', y='display_name', orientation='h',
        color='gp_pct', color_continuous_scale='RdYlGn',
        labels={'sales': 'Sales ($)', 'gp_pct': 'GP %', 'display_name': 'Store'},
        title="Sales by Store (coloured by GP %)",
    )
    fig_stores.update_layout(height=max(400, len(store_perf) * 22))
    st.plotly_chart(fig_stores, key="sales_store_chart")

with col2:
    st.subheader("Department Mix")

    dept_perf = df.groupby('department').agg(
        sales=('sales', 'sum'),
        gp=('gp', 'sum'),
    ).reset_index()
    dept_perf['gp_pct'] = (
        dept_perf['gp'] / dept_perf['sales'] * 100
    ).where(dept_perf['sales'] > 0, 0)
    # Clean department names for display
    dept_perf['dept_name'] = dept_perf['department'].apply(
        lambda x: x.split(' - ', 1)[1] if ' - ' in x else x
    )

    fig_dept = px.pie(
        dept_perf, values='sales', names='dept_name',
        title="Sales Share by Department", hole=0.4,
    )
    fig_dept.update_layout(height=300)
    st.plotly_chart(fig_dept, key="sales_dept_chart")

    # Department table
    dept_table = dept_perf[['dept_name', 'sales', 'gp', 'gp_pct']].copy()
    dept_table = dept_table.sort_values('sales', ascending=False)
    dept_table['sales'] = dept_table['sales'].apply(lambda x: f"${x:,.0f}")
    dept_table['gp'] = dept_table['gp'].apply(lambda x: f"${x:,.0f}")
    dept_table['gp_pct'] = dept_table['gp_pct'].apply(lambda x: f"{x:.1f}%")
    dept_table.columns = ['Department', 'Sales', 'Gross Profit', 'GP %']
    st.dataframe(dept_table, hide_index=True)

st.markdown("---")

# ============================================================================
# DEPARTMENT -> MAJOR GROUP HIERARCHY
# ============================================================================

st.subheader("Department / Major Group Hierarchy")

hierarchy = df.groupby(['department', 'major_group']).agg(
    sales=('sales', 'sum'),
    gp=('gp', 'sum'),
    budget_sales=('budget_sales', 'sum'),
    shrinkage=('shrinkage', 'sum'),
).reset_index()

hierarchy['gp_pct'] = (
    hierarchy['gp'] / hierarchy['sales'] * 100
).where(hierarchy['sales'] > 0, 0)
hierarchy['budget_var'] = (
    (hierarchy['sales'] - hierarchy['budget_sales']) / hierarchy['budget_sales'] * 100
).where(hierarchy['budget_sales'] > 0, 0)

# Clean names for display
hierarchy['dept_name'] = hierarchy['department'].apply(
    lambda x: x.split(' - ', 1)[1] if ' - ' in x else x
)
hierarchy['mg_name'] = hierarchy['major_group'].apply(
    lambda x: x.split(' - ', 1)[1] if ' - ' in x else x
)

if not hierarchy.empty:
    fig_tree = px.treemap(
        hierarchy, path=['dept_name', 'mg_name'], values='sales',
        color='gp_pct', color_continuous_scale='RdYlGn',
        color_continuous_midpoint=hierarchy['gp_pct'].median(),
        title="Sales by Department / Major Group (coloured by GP %)",
    )
    fig_tree.update_layout(height=500)
    st.plotly_chart(fig_tree, key="sales_tree_chart")

    # Hierarchy detail table
    hier_table = hierarchy[['dept_name', 'mg_name', 'sales', 'gp', 'gp_pct',
                            'budget_var', 'shrinkage']].copy()
    hier_table = hier_table.sort_values(['dept_name', 'sales'], ascending=[True, False])
    hier_table['sales'] = hier_table['sales'].apply(lambda x: f"${x:,.0f}")
    hier_table['gp'] = hier_table['gp'].apply(lambda x: f"${x:,.0f}")
    hier_table['gp_pct'] = hier_table['gp_pct'].apply(lambda x: f"{x:.1f}%")
    hier_table['budget_var'] = hier_table['budget_var'].apply(lambda x: f"{x:+.1f}%")
    hier_table['shrinkage'] = hier_table['shrinkage'].apply(lambda x: f"${x:,.0f}")
    hier_table.columns = ['Department', 'Major Group', 'Sales', 'GP', 'GP %',
                           'Budget Var', 'Shrinkage']
    st.dataframe(hier_table, hide_index=True)

st.markdown("---")

# ============================================================================
# SHRINKAGE ANALYSIS
# ============================================================================

st.subheader("Shrinkage by Department")

col1, col2 = st.columns(2)

with col1:
    shrink_dept = df.groupby('department').agg(
        shrinkage=('shrinkage', 'sum'),
        sales=('sales', 'sum'),
    ).reset_index()
    shrink_dept['shrink_pct'] = (
        shrink_dept['shrinkage'] / shrink_dept['sales'] * 100
    ).where(shrink_dept['sales'] > 0, 0)
    shrink_dept['dept_name'] = shrink_dept['department'].apply(
        lambda x: x.split(' - ', 1)[1] if ' - ' in x else x
    )
    shrink_dept = shrink_dept.sort_values('shrinkage', ascending=False)

    fig_shrink = px.bar(
        shrink_dept, x='dept_name', y='shrinkage',
        color='shrink_pct', color_continuous_scale='Oranges',
        labels={'shrinkage': 'Shrinkage ($)', 'shrink_pct': 'Shrinkage % of Sales',
                'dept_name': 'Department'},
        title="Shrinkage Cost by Department",
    )
    fig_shrink.update_layout(height=350)
    st.plotly_chart(fig_shrink, key="sales_shrink_dept_chart")

with col2:
    shrink_store = df.groupby('store').agg(
        shrinkage=('shrinkage', 'sum'),
        sales=('sales', 'sum'),
    ).reset_index()
    shrink_store['shrink_pct'] = (
        shrink_store['shrinkage'] / shrink_store['sales'] * 100
    ).where(shrink_store['sales'] > 0, 0)
    shrink_store['display_name'] = shrink_store['store'].apply(store_display_name)
    shrink_store = shrink_store.sort_values('shrinkage', ascending=False).head(10)

    fig_shrink_store = px.bar(
        shrink_store, x='display_name', y='shrinkage',
        color='shrink_pct', color_continuous_scale='Reds',
        labels={'shrinkage': 'Shrinkage ($)', 'shrink_pct': 'Shrinkage %',
                'display_name': 'Store'},
        title="Top 10 Stores by Shrinkage",
    )
    fig_shrink_store.update_xaxes(tickangle=-45)
    fig_shrink_store.update_layout(height=350)
    st.plotly_chart(fig_shrink_store, key="sales_shrink_store_chart")

st.markdown("---")

# ============================================================================
# DETAILED STORE PERFORMANCE TABLE
# ============================================================================

st.subheader("Detailed Store Performance")

store_detail = df.groupby('store').agg(
    sales=('sales', 'sum'),
    gp=('gp', 'sum'),
    budget_sales=('budget_sales', 'sum'),
    budget_gp=('budget_gp', 'sum'),
    shrinkage=('shrinkage', 'sum'),
).reset_index()

store_detail['gp_pct'] = (
    store_detail['gp'] / store_detail['sales'] * 100
).where(store_detail['sales'] > 0, 0)
store_detail['budget_var'] = (
    (store_detail['sales'] - store_detail['budget_sales']) / store_detail['budget_sales'] * 100
).where(store_detail['budget_sales'] > 0, 0)
store_detail['display_name'] = store_detail['store'].apply(store_display_name)
store_detail = store_detail.sort_values('sales', ascending=False)

display_df = store_detail[['display_name', 'sales', 'gp', 'gp_pct',
                            'budget_sales', 'budget_var', 'shrinkage']].copy()
display_df['sales'] = display_df['sales'].apply(lambda x: f"${x:,.0f}")
display_df['gp'] = display_df['gp'].apply(lambda x: f"${x:,.0f}")
display_df['gp_pct'] = display_df['gp_pct'].apply(lambda x: f"{x:.1f}%")
display_df['budget_sales'] = display_df['budget_sales'].apply(lambda x: f"${x:,.0f}")
display_df['budget_var'] = display_df['budget_var'].apply(lambda x: f"{x:+.1f}%")
display_df['shrinkage'] = display_df['shrinkage'].apply(lambda x: f"${x:,.0f}")

display_df.columns = ['Store', 'Sales', 'Gross Profit', 'GP %',
                       'Budget', 'Budget Var', 'Shrinkage']

st.dataframe(display_df, hide_index=True)

# ============================================================================
# NATURAL LANGUAGE QUERY INTERFACE
# ============================================================================

render_voice_data_box("sales")
render_ask_question("sales")

# ============================================================================
# CROSS-DASHBOARD LINKS
# ============================================================================

st.markdown("---")
st.markdown("**Dig Deeper**")
_pages = st.session_state.get("_pages", {})
c1, c2, c3 = st.columns(3)
if "profitability" in _pages:
    c1.page_link(_pages["profitability"], label="Margin Deep-Dive", icon="\U0001f4b0")
if "plu-intel" in _pages:
    c2.page_link(_pages["plu-intel"], label="PLU Wastage Detail", icon="\U0001f4ca")
if "revenue-bridge" in _pages:
    c3.page_link(_pages["revenue-bridge"], label="Revenue Bridge", icon="\U0001f309")

# ============================================================================
# FOOTER
# ============================================================================

render_footer("Sales Performance", f"Data: {data_min} to {data_max}", user=user)
