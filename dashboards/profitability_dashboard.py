"""
Harris Farm Hub - Store Profitability Dashboard
P&L analysis at store level, derived from real transactional data in harris_farm.db.
Gross margin, shrinkage impact, budget variance, department profitability.
27 retail stores. Weekly data FY2017-FY2024.
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

st.markdown("<style>.profit-positive { color: #10b981; font-weight: bold; }\n    .profit-negative { color: #ef4444; font-weight: bold; }</style>", unsafe_allow_html=True)
user = st.session_state.get("auth_user")


# ============================================================================
# DATABASE PATH & HELPERS
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


def dept_display_name(full_name: str) -> str:
    """'10 - Fruit & Vegetables' -> 'Fruit & Vegetables'"""
    parts = full_name.split(" - ", 1)
    return parts[1] if len(parts) == 2 else full_name


def compute_period_delta(current_val, previous_val):
    """Return percentage change string for metric deltas."""
    if previous_val == 0:
        return None
    pct = (current_val - previous_val) / abs(previous_val) * 100
    return f"{pct:+.1f}%"


# ============================================================================
# 5/4/4 RETAIL FISCAL CALENDAR
# ============================================================================

def _fy_anchor(year, fy_start_month=7):
    """Monday closest to 1st of fy_start_month in given year."""
    anchor = datetime(year, fy_start_month, 1)
    dow = anchor.weekday()
    if dow <= 3:
        return anchor - timedelta(days=dow)
    else:
        return anchor + timedelta(days=(7 - dow))


def build_454_calendar(reference_date=None):
    """Build 5/4/4 retail calendar for the FY containing reference_date."""
    if reference_date is None:
        reference_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    anchor = _fy_anchor(reference_date.year)
    if reference_date < anchor:
        anchor = _fy_anchor(reference_date.year - 1)
    pattern = [5, 4, 4] * 4
    periods = []
    current = anchor
    for i, weeks in enumerate(pattern):
        period_end = current + timedelta(weeks=weeks) - timedelta(days=1)
        periods.append({
            'quarter': i // 3 + 1,
            'period': i + 1,
            'weeks': weeks,
            'start': current,
            'end': period_end,
            'label': f"P{i+1} (Q{i//3+1}) {current.strftime('%d %b')}\u2013{period_end.strftime('%d %b')}",
        })
        current = period_end + timedelta(days=1)
    return anchor, periods


def get_454_period(reference_date=None):
    """Return the 454 period dict containing reference_date."""
    if reference_date is None:
        reference_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    _, periods = build_454_calendar(reference_date)
    for p in periods:
        if p['start'] <= reference_date <= p['end']:
            return p
    return periods[-1]


def get_454_quarter(reference_date=None):
    """Return (start, end) for the 454 quarter containing reference_date."""
    if reference_date is None:
        reference_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    _, periods = build_454_calendar(reference_date)
    for p in periods:
        if p['start'] <= reference_date <= p['end']:
            q = p['quarter']
            q_periods = [pp for pp in periods if pp['quarter'] == q]
            return q_periods[0]['start'], q_periods[-1]['end']
    return periods[0]['start'], periods[-1]['end']


# ============================================================================
# DATA LOADING — Real SQLite queries
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
        cursor.execute("SELECT DISTINCT department FROM sales ORDER BY department")
        return [row[0] for row in cursor.fetchall()]


@st.cache_data(ttl=300)
def get_date_range():
    """Get min/max week_ending from sales data."""
    db = _get_db_path()
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(week_ending), MAX(week_ending) FROM sales")
        row = cursor.fetchone()
        return row[0], row[1]


@st.cache_data(ttl=300)
def load_profitability_data(date_from, date_to, stores=None, promo='N'):
    """
    Load weekly profitability data pivoted wide.
    Returns DataFrame with: store, department, major_group, week_ending,
    sales, initial_gp, gp, budget_sales, budget_gp, shrinkage.
    """
    db = _get_db_path()

    query = """
        SELECT store, department, major_group, week_ending, measure, value
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

    with sqlite3.connect(db) as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if df.empty:
        return pd.DataFrame()

    measure_map = {
        'Sales - Val': 'sales',
        'Final Gross Prod - Val': 'gp',
        'Initial Gross Profit - Val': 'initial_gp',
        'Bgt Sales - Val': 'budget_sales',
        'Bgt Final GP - Val': 'budget_gp',
        'Total Shrinkage \u2013 Val': 'shrinkage',
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

    for col in measure_map.values():
        if col not in pivoted.columns:
            pivoted[col] = 0.0

    pivoted['week_ending'] = pd.to_datetime(pivoted['week_ending'])
    return pivoted


# ============================================================================
# HEADER
# ============================================================================

render_header("💰 Store Profitability", "**Finance Team** | Store-level P&L, margins, shrinkage & budget variance")

# ============================================================================
# FILTERS
# ============================================================================

stores_list = load_stores()
data_min, data_max = get_date_range()
latest_date = pd.Timestamp(data_max)

col1, col2, col3 = st.columns(3)

with col1:
    period_options = [
        "Last 13 Weeks",
        "Last 4 Weeks",
        "Last 26 Weeks",
        "Last 52 Weeks",
        "This Period (454)",
        "This Quarter (454)",
        "FY2024 (Jul 23 - Jun 24)",
        "FY2023 (Jul 22 - Jun 23)",
    ]
    date_range_sel = st.selectbox("Analysis Period", period_options, index=0)

with col2:
    store_filter = st.multiselect(
        "Stores",
        ["All Stores"] + [store_display_name(s) + f" [{s.split(' - ')[0]}]" for s in stores_list],
        default=["All Stores"]
    )

with col3:
    view_type = st.radio(
        "View By",
        ["Individual Stores", "By Department", "All Stores Combined"],
        horizontal=True
    )

# Resolve date range
if date_range_sel == "Last 4 Weeks":
    date_from = (latest_date - pd.Timedelta(weeks=4)).strftime('%Y-%m-%d')
    date_to = data_max
    prev_from = (latest_date - pd.Timedelta(weeks=8)).strftime('%Y-%m-%d')
    prev_to = (latest_date - pd.Timedelta(weeks=4) - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
elif date_range_sel == "Last 13 Weeks":
    date_from = (latest_date - pd.Timedelta(weeks=13)).strftime('%Y-%m-%d')
    date_to = data_max
    prev_from = (latest_date - pd.Timedelta(weeks=26)).strftime('%Y-%m-%d')
    prev_to = (latest_date - pd.Timedelta(weeks=13) - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
elif date_range_sel == "Last 26 Weeks":
    date_from = (latest_date - pd.Timedelta(weeks=26)).strftime('%Y-%m-%d')
    date_to = data_max
    prev_from = (latest_date - pd.Timedelta(weeks=52)).strftime('%Y-%m-%d')
    prev_to = (latest_date - pd.Timedelta(weeks=26) - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
elif date_range_sel == "Last 52 Weeks":
    date_from = (latest_date - pd.Timedelta(weeks=52)).strftime('%Y-%m-%d')
    date_to = data_max
    prev_from = (latest_date - pd.Timedelta(weeks=104)).strftime('%Y-%m-%d')
    prev_to = (latest_date - pd.Timedelta(weeks=52) - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
elif date_range_sel == "This Period (454)":
    current_period = get_454_period(latest_date.to_pydatetime())
    date_from = current_period['start'].strftime('%Y-%m-%d')
    date_to = current_period['end'].strftime('%Y-%m-%d')
    prev_period = get_454_period(current_period['start'] - timedelta(days=1))
    prev_from = prev_period['start'].strftime('%Y-%m-%d')
    prev_to = prev_period['end'].strftime('%Y-%m-%d')
elif date_range_sel == "This Quarter (454)":
    q_start, q_end = get_454_quarter(latest_date.to_pydatetime())
    date_from = q_start.strftime('%Y-%m-%d')
    date_to = q_end.strftime('%Y-%m-%d')
    prev_q_start, prev_q_end = get_454_quarter(q_start - timedelta(days=1))
    prev_from = prev_q_start.strftime('%Y-%m-%d')
    prev_to = prev_q_end.strftime('%Y-%m-%d')
elif date_range_sel == "FY2024 (Jul 23 - Jun 24)":
    date_from = "2023-07-02"
    date_to = "2024-06-30"
    prev_from = "2022-07-03"
    prev_to = "2023-07-01"
elif date_range_sel == "FY2023 (Jul 22 - Jun 23)":
    date_from = "2022-07-03"
    date_to = "2023-07-01"
    prev_from = "2021-07-04"
    prev_to = "2022-07-02"
else:
    date_from = (latest_date - pd.Timedelta(weeks=13)).strftime('%Y-%m-%d')
    date_to = data_max
    prev_from = (latest_date - pd.Timedelta(weeks=26)).strftime('%Y-%m-%d')
    prev_to = (latest_date - pd.Timedelta(weeks=13) - pd.Timedelta(days=1)).strftime('%Y-%m-%d')

# Resolve store filter
selected_stores = None
if "All Stores" not in store_filter and store_filter:
    selected_stores = []
    for sf in store_filter:
        code = sf.split("[")[-1].rstrip("]") if "[" in sf else ""
        for s in stores_list:
            if s.startswith(code + " - "):
                selected_stores.append(s)
                break

# Show calendar context
current_454 = get_454_period(latest_date.to_pydatetime())
st.caption(
    f"454 Calendar: {current_454['label']} | "
    f"Viewing: {date_from} to {date_to} | "
    f"Data range: {data_min} to {data_max}"
)

# ============================================================================
# LOAD DATA
# ============================================================================

df = load_profitability_data(date_from, date_to, selected_stores)
prev_df = load_profitability_data(prev_from, prev_to, selected_stores)

if df.empty:
    st.warning("No data found for the selected filters. Try broadening your selection.")
    st.stop()

# ============================================================================
# KEY METRICS
# ============================================================================

st.subheader("Network Performance")

total_sales = df['sales'].sum()
total_initial_gp = df['initial_gp'].sum()
total_gp = df['gp'].sum()
total_shrinkage = df['shrinkage'].sum()
total_budget_sales = df['budget_sales'].sum()
total_budget_gp = df['budget_gp'].sum()

gp_pct = (total_gp / total_sales * 100) if total_sales > 0 else 0
initial_gp_pct = (total_initial_gp / total_sales * 100) if total_sales > 0 else 0
shrinkage_pct = (total_shrinkage / total_sales * 100) if total_sales > 0 else 0
margin_erosion = initial_gp_pct - gp_pct
sales_var = ((total_sales - total_budget_sales) / total_budget_sales * 100) if total_budget_sales > 0 else 0
gp_var = ((total_gp - total_budget_gp) / total_budget_gp * 100) if total_budget_gp > 0 else 0

# Previous period
prev_sales = prev_df['sales'].sum() if not prev_df.empty else 0
prev_gp = prev_df['gp'].sum() if not prev_df.empty else 0
prev_gp_pct = (prev_gp / prev_sales * 100) if prev_sales > 0 else 0
prev_shrinkage = prev_df['shrinkage'].sum() if not prev_df.empty else 0

# Best/worst by GP%
store_gp = df.groupby('store').agg(sales=('sales', 'sum'), gp=('gp', 'sum')).reset_index()
store_gp['gp_pct'] = (store_gp['gp'] / store_gp['sales'] * 100).where(store_gp['sales'] > 0, 0)
best_store = store_gp.loc[store_gp['gp_pct'].idxmax(), 'store'] if len(store_gp) > 0 else "N/A"
worst_store = store_gp.loc[store_gp['gp_pct'].idxmin(), 'store'] if len(store_gp) > 0 else "N/A"

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Network Sales", f"${total_sales:,.0f}",
              delta=compute_period_delta(total_sales, prev_sales))

with col2:
    st.metric("Final GP", f"${total_gp:,.0f}",
              delta=compute_period_delta(total_gp, prev_gp))

with col3:
    st.metric("GP %", f"{gp_pct:.1f}%",
              delta=compute_period_delta(gp_pct, prev_gp_pct),
              delta_color="normal")

with col4:
    st.metric("Shrinkage", f"${total_shrinkage:,.0f}",
              delta=compute_period_delta(total_shrinkage, prev_shrinkage),
              delta_color="inverse")

with col5:
    st.metric("Sales vs Budget", f"{sales_var:+.1f}%",
              delta_color="normal")

with col6:
    st.metric("GP vs Budget", f"{gp_var:+.1f}%",
              delta_color="normal")

st.markdown("---")

# ============================================================================
# WATERFALL CHART - PROFITABILITY BREAKDOWN
# ============================================================================

st.subheader("Profitability Waterfall (Network Total)")

fig_waterfall = go.Figure(go.Waterfall(
    name="Profitability",
    orientation="v",
    measure=["relative", "total", "relative", "total"],
    x=["Sales", "Initial GP", "Shrinkage / Markdowns", "Final GP"],
    y=[total_sales, 0, -(total_initial_gp - total_gp), 0],
    connector={"line": {"color": "rgb(63, 63, 63)"}},
    decreasing={"marker": {"color": "#ef4444"}},
    increasing={"marker": {"color": "#10b981"}},
    totals={"marker": {"color": "#1e3a8a"}},
))

fig_waterfall.update_layout(
    title=f"Revenue to Final GP | Margin erosion: {margin_erosion:.1f}pp from shrinkage",
    height=400,
    showlegend=False
)

st.plotly_chart(fig_waterfall, key="profit_waterfall")

# ============================================================================
# STORE COMPARISON
# ============================================================================

col1, col2 = st.columns(2)

# Aggregate per store
store_pnl = df.groupby('store').agg(
    sales=('sales', 'sum'),
    initial_gp=('initial_gp', 'sum'),
    gp=('gp', 'sum'),
    budget_sales=('budget_sales', 'sum'),
    budget_gp=('budget_gp', 'sum'),
    shrinkage=('shrinkage', 'sum'),
).reset_index()

store_pnl['gp_pct'] = (store_pnl['gp'] / store_pnl['sales'] * 100).where(store_pnl['sales'] > 0, 0)
store_pnl['initial_gp_pct'] = (store_pnl['initial_gp'] / store_pnl['sales'] * 100).where(store_pnl['sales'] > 0, 0)
store_pnl['shrinkage_pct'] = (store_pnl['shrinkage'] / store_pnl['sales'] * 100).where(store_pnl['sales'] > 0, 0)
store_pnl['sales_var'] = ((store_pnl['sales'] - store_pnl['budget_sales']) / store_pnl['budget_sales'] * 100).where(store_pnl['budget_sales'] > 0, 0)
store_pnl['gp_var'] = ((store_pnl['gp'] - store_pnl['budget_gp']) / store_pnl['budget_gp'] * 100).where(store_pnl['budget_gp'] > 0, 0)
store_pnl['display_name'] = store_pnl['store'].apply(store_display_name)

with col1:
    st.subheader("Store GP Comparison")

    if view_type == "Individual Stores":
        plot_df = store_pnl.sort_values('gp', ascending=True)
        fig_stores = go.Figure(go.Bar(
            y=plot_df['display_name'],
            x=plot_df['gp'],
            orientation='h',
            marker_color=plot_df['gp_pct'].apply(
                lambda x: '#10b981' if x > store_pnl['gp_pct'].mean() else '#ef4444'
            ),
            text=plot_df.apply(lambda r: f"${r['gp']/1000:.0f}k ({r['gp_pct']:.1f}%)", axis=1),
            textposition='auto'
        ))
        fig_stores.update_layout(
            height=max(400, len(plot_df) * 22),
            xaxis_title="Gross Profit ($)",
            showlegend=False
        )
        st.plotly_chart(fig_stores, key="profit_store_gp_comparison")
    elif view_type == "By Department":
        dept_pnl = df.groupby('department').agg(
            sales=('sales', 'sum'), gp=('gp', 'sum'),
            shrinkage=('shrinkage', 'sum'),
        ).reset_index()
        dept_pnl['gp_pct'] = (dept_pnl['gp'] / dept_pnl['sales'] * 100).where(dept_pnl['sales'] > 0, 0)
        dept_pnl['dept_name'] = dept_pnl['department'].apply(dept_display_name)
        dept_pnl = dept_pnl.sort_values('gp', ascending=True)

        fig_dept = go.Figure(go.Bar(
            y=dept_pnl['dept_name'],
            x=dept_pnl['gp'],
            orientation='h',
            marker_color=dept_pnl['gp_pct'].apply(
                lambda x: '#10b981' if x > dept_pnl['gp_pct'].mean() else '#ef4444'
            ),
            text=dept_pnl.apply(lambda r: f"${r['gp']/1000:.0f}k ({r['gp_pct']:.1f}%)", axis=1),
            textposition='auto'
        ))
        fig_dept.update_layout(
            height=400, xaxis_title="Gross Profit ($)", showlegend=False
        )
        st.plotly_chart(fig_dept, key="profit_dept_gp_comparison")
    else:
        st.metric("Network GP", f"${total_gp:,.0f}")
        st.metric("Network GP %", f"{gp_pct:.1f}%")
        st.metric("Margin Erosion", f"{margin_erosion:.1f}pp",
                   help="Difference between initial GP% and final GP% (shrinkage + markdowns)")

with col2:
    st.subheader("GP % vs Sales Volume")

    if view_type != "All Stores Combined":
        if view_type == "By Department":
            scatter_df = dept_pnl
            x_col, y_col, name_col = 'sales', 'gp_pct', 'dept_name'
        else:
            scatter_df = store_pnl
            x_col, y_col, name_col = 'sales', 'gp_pct', 'display_name'

        fig_scatter = px.scatter(
            scatter_df, x=x_col, y=y_col,
            hover_data=[name_col],
            labels={'sales': 'Sales ($)', 'gp_pct': 'GP %'},
        )
        avg_gp = scatter_df['gp_pct'].mean()
        fig_scatter.add_hline(
            y=avg_gp, line_dash="dash", line_color="red",
            annotation_text=f"Avg: {avg_gp:.1f}%"
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, key="profit_gp_vs_sales_scatter")

st.markdown("---")

# ============================================================================
# SHRINKAGE IMPACT ANALYSIS
# ============================================================================

st.subheader("Shrinkage Impact on Profitability")

col1, col2 = st.columns(2)

with col1:
    # Shrinkage by department
    dept_shrink = df.groupby('department').agg(
        sales=('sales', 'sum'),
        initial_gp=('initial_gp', 'sum'),
        gp=('gp', 'sum'),
        shrinkage=('shrinkage', 'sum'),
    ).reset_index()
    dept_shrink['margin_erosion'] = (
        (dept_shrink['initial_gp'] - dept_shrink['gp']) / dept_shrink['sales'] * 100
    ).where(dept_shrink['sales'] > 0, 0)
    dept_shrink['dept_name'] = dept_shrink['department'].apply(dept_display_name)
    dept_shrink = dept_shrink.sort_values('margin_erosion', ascending=False)

    fig_erosion = px.bar(
        dept_shrink, x='dept_name', y='margin_erosion',
        color='margin_erosion', color_continuous_scale='Reds',
        labels={'margin_erosion': 'Margin Erosion (pp)', 'dept_name': 'Department'},
        title="Margin Erosion by Department (Initial GP% - Final GP%)",
    )
    fig_erosion.update_layout(height=350)
    st.plotly_chart(fig_erosion, key="profit_margin_erosion")

with col2:
    # Shrinkage by store (top 10)
    store_shrink = store_pnl.sort_values('shrinkage_pct', ascending=False).head(10)

    fig_shrink = px.bar(
        store_shrink, x='display_name', y='shrinkage_pct',
        color='shrinkage_pct', color_continuous_scale='Reds',
        labels={'shrinkage_pct': 'Shrinkage % of Sales', 'display_name': 'Store'},
        title="Top 10 Stores by Shrinkage Rate",
    )
    fig_shrink.update_xaxes(tickangle=-45)
    fig_shrink.update_layout(height=350)
    st.plotly_chart(fig_shrink, key="profit_shrinkage_by_store")

st.markdown("---")

# ============================================================================
# BUDGET VARIANCE ANALYSIS
# ============================================================================

st.subheader("Budget Variance")

col1, col2 = st.columns(2)

with col1:
    # Sales variance by store
    var_df = store_pnl.sort_values('sales_var', ascending=True)

    fig_sales_var = go.Figure(go.Bar(
        y=var_df['display_name'],
        x=var_df['sales_var'],
        orientation='h',
        marker_color=var_df['sales_var'].apply(
            lambda x: '#10b981' if x >= 0 else '#ef4444'
        ),
        text=var_df['sales_var'].apply(lambda x: f"{x:+.1f}%"),
        textposition='auto'
    ))
    fig_sales_var.update_layout(
        height=max(400, len(var_df) * 22),
        title="Sales vs Budget by Store",
        xaxis_title="Variance (%)",
        showlegend=False
    )
    st.plotly_chart(fig_sales_var, key="profit_sales_budget_variance")

with col2:
    # GP variance by store
    gp_var_df = store_pnl.sort_values('gp_var', ascending=True)

    fig_gp_var = go.Figure(go.Bar(
        y=gp_var_df['display_name'],
        x=gp_var_df['gp_var'],
        orientation='h',
        marker_color=gp_var_df['gp_var'].apply(
            lambda x: '#10b981' if x >= 0 else '#ef4444'
        ),
        text=gp_var_df['gp_var'].apply(lambda x: f"{x:+.1f}%"),
        textposition='auto'
    ))
    fig_gp_var.update_layout(
        height=max(400, len(gp_var_df) * 22),
        title="GP vs Budget by Store",
        xaxis_title="Variance (%)",
        showlegend=False
    )
    st.plotly_chart(fig_gp_var, key="profit_gp_budget_variance")

st.markdown("---")

# ============================================================================
# DETAILED P&L TABLE
# ============================================================================

st.subheader("Store-by-Store P&L")

display_tbl = store_pnl[['display_name', 'sales', 'initial_gp', 'gp',
                          'shrinkage', 'gp_pct', 'initial_gp_pct',
                          'sales_var', 'gp_var']].copy()
display_tbl = display_tbl.sort_values('gp', ascending=False)

display_tbl['sales'] = display_tbl['sales'].apply(lambda x: f"${x:,.0f}")
display_tbl['initial_gp'] = display_tbl['initial_gp'].apply(lambda x: f"${x:,.0f}")
display_tbl['gp'] = display_tbl['gp'].apply(lambda x: f"${x:,.0f}")
display_tbl['shrinkage'] = display_tbl['shrinkage'].apply(lambda x: f"${x:,.0f}")
display_tbl['gp_pct'] = display_tbl['gp_pct'].apply(lambda x: f"{x:.1f}%")
display_tbl['initial_gp_pct'] = display_tbl['initial_gp_pct'].apply(lambda x: f"{x:.1f}%")
display_tbl['sales_var'] = display_tbl['sales_var'].apply(lambda x: f"{x:+.1f}%")
display_tbl['gp_var'] = display_tbl['gp_var'].apply(lambda x: f"{x:+.1f}%")

display_tbl.columns = ['Store', 'Sales', 'Initial GP', 'Final GP',
                        'Shrinkage', 'GP %', 'Initial GP %',
                        'Sales vs Bgt', 'GP vs Bgt']

st.dataframe(display_tbl, hide_index=True, key="profit_store_pnl_table")

# ============================================================================
# INSIGHTS & RECOMMENDATIONS
# ============================================================================

st.markdown("---")
st.subheader("Key Insights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Strongest GP Performers:**")
    top_3 = store_pnl.nlargest(3, 'gp_pct')
    for _, row in top_3.iterrows():
        st.markdown(
            f"- **{row['display_name']}**: {row['gp_pct']:.1f}% GP "
            f"(${row['gp']:,.0f})"
        )

with col2:
    st.markdown("**Highest Shrinkage (Needs Attention):**")
    worst_shrink = store_pnl.nlargest(3, 'shrinkage_pct')
    for _, row in worst_shrink.iterrows():
        st.markdown(
            f"- **{row['display_name']}**: {row['shrinkage_pct']:.1f}% shrinkage "
            f"(${row['shrinkage']:,.0f})"
        )

# ============================================================================
# DEPARTMENT PROFITABILITY DETAIL
# ============================================================================

st.markdown("---")
st.subheader("Department Profitability Detail")

dept_detail = df.groupby('department').agg(
    sales=('sales', 'sum'),
    initial_gp=('initial_gp', 'sum'),
    gp=('gp', 'sum'),
    budget_sales=('budget_sales', 'sum'),
    budget_gp=('budget_gp', 'sum'),
    shrinkage=('shrinkage', 'sum'),
).reset_index()

dept_detail['gp_pct'] = (dept_detail['gp'] / dept_detail['sales'] * 100).where(dept_detail['sales'] > 0, 0)
dept_detail['initial_gp_pct'] = (dept_detail['initial_gp'] / dept_detail['sales'] * 100).where(dept_detail['sales'] > 0, 0)
dept_detail['shrinkage_pct'] = (dept_detail['shrinkage'] / dept_detail['sales'] * 100).where(dept_detail['sales'] > 0, 0)
dept_detail['sales_var'] = ((dept_detail['sales'] - dept_detail['budget_sales']) / dept_detail['budget_sales'] * 100).where(dept_detail['budget_sales'] > 0, 0)
dept_detail['dept_name'] = dept_detail['department'].apply(dept_display_name)

dept_tbl = dept_detail[['dept_name', 'sales', 'gp', 'gp_pct', 'initial_gp_pct',
                          'shrinkage', 'shrinkage_pct', 'sales_var']].copy()
dept_tbl = dept_tbl.sort_values('sales', ascending=False)

dept_tbl['sales'] = dept_tbl['sales'].apply(lambda x: f"${x:,.0f}")
dept_tbl['gp'] = dept_tbl['gp'].apply(lambda x: f"${x:,.0f}")
dept_tbl['gp_pct'] = dept_tbl['gp_pct'].apply(lambda x: f"{x:.1f}%")
dept_tbl['initial_gp_pct'] = dept_tbl['initial_gp_pct'].apply(lambda x: f"{x:.1f}%")
dept_tbl['shrinkage'] = dept_tbl['shrinkage'].apply(lambda x: f"${x:,.0f}")
dept_tbl['shrinkage_pct'] = dept_tbl['shrinkage_pct'].apply(lambda x: f"{x:.1f}%")
dept_tbl['sales_var'] = dept_tbl['sales_var'].apply(lambda x: f"{x:+.1f}%")

dept_tbl.columns = ['Department', 'Sales', 'Final GP', 'GP %', 'Initial GP %',
                      'Shrinkage', 'Shrinkage %', 'Sales vs Bgt']

st.dataframe(dept_tbl, hide_index=True, key="profit_dept_detail_table")

# ============================================================================
# PLU WASTAGE HOTSPOTS (from PLU Intelligence — 27.3M rows)
# ============================================================================

try:
    from plu_layer import db_available, top_plus_by_wastage
    if db_available():
        st.markdown("---")
        st.subheader("PLU Wastage Hotspots")
        st.caption("Top items destroying margin — from 27.3M weekly PLU records")

        wastage_items = top_plus_by_wastage(limit=10)
        if wastage_items:
            wdf = pd.DataFrame(wastage_items)
            wdf["total_wastage"] = wdf["total_wastage"].apply(lambda x: f"${abs(x or 0):,.0f}")
            wdf["total_sales"] = wdf["total_sales"].apply(lambda x: f"${(x or 0):,.0f}")
            wdf["wastage_pct"] = wdf["wastage_pct"].apply(lambda x: f"{abs(x or 0):.1f}%")
            wdf = wdf.rename(columns={
                "plu_code": "PLU", "description": "Item", "department": "Dept",
                "total_wastage": "Wastage $", "total_sales": "Sales $",
                "wastage_pct": "Wastage %", "store_count": "Stores",
            })
            st.dataframe(
                wdf[["PLU", "Item", "Dept", "Wastage $", "Sales $", "Wastage %", "Stores"]],
                hide_index=True, key="profit_plu_wastage_table",
            )
            _pages = st.session_state.get("_pages", {})
            if "plu-intel" in _pages:
                st.page_link(_pages["plu-intel"], label="View full PLU Wastage Analysis", icon="📊")
        else:
            st.info("No significant wastage items found.")
except ImportError:
    pass

# ============================================================================
# ASK A QUESTION
# ============================================================================

render_voice_data_box("profitability")
render_ask_question("profitability")

# ============================================================================
# CROSS-DASHBOARD LINKS
# ============================================================================

st.markdown("---")
st.markdown("**Dig Deeper**")
_pages = st.session_state.get("_pages", {})
c1, c2, c3 = st.columns(3)
if "plu-intel" in _pages:
    c1.page_link(_pages["plu-intel"], label="PLU Wastage Hotspots", icon="📊")
if "sales" in _pages:
    c2.page_link(_pages["sales"], label="Sales Trends", icon="📈")
if "buying-hub" in _pages:
    c3.page_link(_pages["buying-hub"], label="Buying Hub", icon="🛒")

# ============================================================================
# FOOTER
# ============================================================================

render_footer("Store Profitability", f"Data: {data_min} to {data_max}", user=user)
