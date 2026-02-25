"""
Harris Farm Hub - Transport & Logistics Cost Dashboard
Routes between Sydney Markets distribution centre and all 21 HFM store sites.
Seeded RNG (42) for deterministic data. 454 retail fiscal calendar for period selection.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

from shared.stores import STORES, REGIONS
from shared.styles import render_header, render_footer
from shared.ask_question import render_ask_question
from shared.voice_realtime import render_voice_data_box
from shared.fiscal_selector import render_fiscal_selector

# Approximate km from Sydney Markets (Flemington) to each store
STORE_DISTANCE_KM = {
    "Allambie Heights": 22, "Bondi Beach": 14, "Bondi Junction": 12,
    "Brookvale": 24, "Castle Hill": 38, "Crows Nest": 8,
    "Double Bay": 10, "Drummoyne": 9, "Edgecliff": 10,
    "Gladesville": 14, "Hornsby": 32, "Leichhardt": 7,
    "Lindfield": 20, "Manly": 22, "Miranda": 28,
    "Neutral Bay": 9, "North Sydney": 8, "Parramatta": 25,
    "Richmond": 65, "Rozelle": 7, "Willoughby": 12,
}

def compute_period_delta(current_val, previous_val):
    """Return percentage change string for metric deltas."""
    if previous_val == 0:
        return None
    pct = (current_val - previous_val) / abs(previous_val) * 100
    return f"{pct:+.1f}%"


# ============================================================================
# MOCK TRANSPORT DATA — delivery runs from Sydney Markets to stores
# ============================================================================

@st.cache_data(ttl=300)
def generate_transport_data():
    """
    Generate delivery cost data. Each row = 1 delivery run to 1 store on 1 day.
    Seed 42 for deterministic output.
    """
    rng = np.random.RandomState(42)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    dates = pd.date_range(end=today, periods=90, freq='D')

    data = []
    for date in dates:
        dow = date.dayofweek
        # More deliveries on weekdays (restocking before weekends)
        for store in STORES:
            distance = STORE_DISTANCE_KM[store]
            region = REGIONS[store]

            # Number of deliveries per day depends on store volume
            base_deliveries = 2 if distance < 15 else 1
            if dow <= 4:  # weekdays get extra runs
                n_deliveries = base_deliveries + int(rng.choice([0, 1], p=[0.4, 0.6]))
            else:
                n_deliveries = max(1, base_deliveries - int(rng.choice([0, 1], p=[0.5, 0.5])))

            for _ in range(n_deliveries):
                # Fuel cost: distance-based with variability
                fuel_cost = distance * 2.1 + rng.normal(0, distance * 0.15)
                fuel_cost = max(5, round(fuel_cost, 2))

                # Driver cost: hourly rate x estimated travel time
                travel_time_hrs = distance / 35 + rng.uniform(0.3, 1.0)  # avg 35 km/h urban
                driver_cost = round(travel_time_hrs * 42, 2)  # $42/hr

                # Vehicle type probability: closer stores more likely small van
                if distance < 12:
                    vtype = rng.choice(['Small Van', 'Medium Truck', 'Large Truck'], p=[0.5, 0.35, 0.15])
                elif distance < 25:
                    vtype = rng.choice(['Small Van', 'Medium Truck', 'Large Truck'], p=[0.3, 0.45, 0.25])
                else:
                    vtype = rng.choice(['Small Van', 'Medium Truck', 'Large Truck'], p=[0.1, 0.4, 0.5])

                vehicle_cost = {'Small Van': 15, 'Medium Truck': 25, 'Large Truck': 40}[vtype]

                # Maintenance allocation
                maintenance = round(distance * 0.8 + rng.uniform(0, 3), 2)

                total_cost = round(fuel_cost + driver_cost + vehicle_cost + maintenance, 2)

                # Pallet volume
                pallets = max(1, int(rng.uniform(2, 12)))
                cost_per_pallet = round(total_cost / pallets, 2)

                data.append({
                    'date': date,
                    'store': store,
                    'region': region,
                    'route': f"Sydney Markets\u2192{store}",
                    'distance_km': distance,
                    'vehicle_type': vtype,
                    'fuel_cost': fuel_cost,
                    'driver_cost': driver_cost,
                    'vehicle_cost': vehicle_cost,
                    'maintenance': maintenance,
                    'total_cost': total_cost,
                    'pallets': pallets,
                    'cost_per_pallet': cost_per_pallet,
                    'cost_per_km': round(total_cost / distance, 2),
                    'delivery_time_hrs': round(travel_time_hrs, 2),
                })

    return pd.DataFrame(data)


# ============================================================================
# HEADER
# ============================================================================

user = st.session_state.get("auth_user")

render_header(
    "Transport & Logistics",
    "**Operations Team** | Delivery costs, route efficiency & fleet analysis",
    goals=["G4"],
    strategy_context="Every route, every delivery, every cost — visible. AI optimises the path from Sydney Markets to store shelf.",
)
st.caption("Step 5: Review this data. Add your judgment. Your experience makes this useful.")
st.info("Transport data is simulated (seed 42). Connect to real logistics system for production use.")

# ============================================================================
# LOAD DATA
# ============================================================================

raw_df = generate_transport_data()

# ============================================================================
# FILTERS — Fiscal Period Selector
# ============================================================================

filters = render_fiscal_selector(
    key_prefix="transport",
    show_comparison=True,
    show_store=False,
)

if not filters["start_date"]:
    st.stop()

col_store, col_vehicle = st.columns(2)

with col_store:
    store_filter = st.multiselect(
        "Stores",
        ["All Stores"] + sorted(STORES),
        default=["All Stores"]
    )

with col_vehicle:
    vehicle_filter = st.selectbox(
        "Vehicle Type",
        ["All Vehicles", "Small Van", "Medium Truck", "Large Truck"]
    )

# Apply date filter — map fiscal selector dates to mock data range
df = raw_df.copy()
latest_date = df['date'].max()

fs_start = pd.Timestamp(filters["start_date"])
fs_end = pd.Timestamp(filters["end_date"])

# Mock data only covers 90 days — clip to available range
if fs_start < df['date'].min():
    fs_start = df['date'].min()
if fs_end > latest_date:
    fs_end = latest_date

df = df[(df['date'] >= fs_start) & (df['date'] <= fs_end)]

# Comparison period
if filters["comparison"]:
    comp_start = pd.Timestamp(filters["comparison"]["start"])
    comp_end = pd.Timestamp(filters["comparison"]["end"])
    if comp_start < raw_df['date'].min():
        comp_start = raw_df['date'].min()
    prev_df = raw_df[(raw_df['date'] >= comp_start) & (raw_df['date'] <= comp_end)]
else:
    period_days = (fs_end - fs_start).days
    prev_start = fs_start - pd.Timedelta(days=period_days + 1)
    prev_end = fs_start - pd.Timedelta(days=1)
    prev_df = raw_df[(raw_df['date'] >= prev_start) & (raw_df['date'] <= prev_end)]

# Coverage indicator
if filters.get("caveats"):
    for c in filters["caveats"]:
        st.caption(f"Note: {c}")
n_days = (fs_end - fs_start).days + 1
st.caption(f"Showing {n_days} days | {len(df)} delivery records | Mock data (seed 42)")

# Apply store filter
if "All Stores" not in store_filter and store_filter:
    df = df[df['store'].isin(store_filter)]
    prev_df = prev_df[prev_df['store'].isin(store_filter)]

# Apply vehicle filter
if vehicle_filter != "All Vehicles":
    df = df[df['vehicle_type'] == vehicle_filter]
    prev_df = prev_df[prev_df['vehicle_type'] == vehicle_filter]

# ============================================================================
# KEY METRICS — computed from data with period deltas
# ============================================================================

st.subheader("Cost Overview")

total_cost = df['total_cost'].sum()
total_deliveries = len(df)
avg_cost_delivery = df['total_cost'].mean() if len(df) > 0 else 0
total_distance = df['distance_km'].sum()
avg_cost_km = df['cost_per_km'].mean() if len(df) > 0 else 0

prev_total_cost = prev_df['total_cost'].sum()
prev_deliveries = len(prev_df)
prev_avg_cost_delivery = prev_df['total_cost'].mean() if len(prev_df) > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Transport Cost", f"${total_cost:,.0f}",
              delta=compute_period_delta(total_cost, prev_total_cost),
              delta_color="inverse")

with col2:
    st.metric("Deliveries", f"{total_deliveries:,}",
              delta=compute_period_delta(total_deliveries, prev_deliveries))

with col3:
    st.metric("Avg Cost/Delivery", f"${avg_cost_delivery:.2f}",
              delta=compute_period_delta(avg_cost_delivery, prev_avg_cost_delivery),
              delta_color="inverse")

with col4:
    st.metric("Total Distance", f"{total_distance:,.0f} km")

with col5:
    st.metric("Cost per KM", f"${avg_cost_km:.2f}")

st.markdown("---")

# ============================================================================
# COST BREAKDOWN
# ============================================================================

st.subheader("Cost Component Breakdown")

cost_components = {
    'Fuel': df['fuel_cost'].sum(),
    'Driver Labor': df['driver_cost'].sum(),
    'Vehicle': df['vehicle_cost'].sum(),
    'Maintenance': df['maintenance'].sum()
}

col1, col2 = st.columns([2, 1])

with col1:
    fig_pie = px.pie(
        values=list(cost_components.values()),
        names=list(cost_components.keys()),
        title="Transport Cost Components",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(height=400)
    st.plotly_chart(fig_pie, key="transport_cost_components_pie")

with col2:
    st.markdown("### Cost Breakdown")
    for component, cost in cost_components.items():
        pct = (cost / total_cost * 100) if total_cost > 0 else 0
        st.metric(component, f"${cost:,.0f}", delta=f"{pct:.1f}%")

st.markdown("---")

# ============================================================================
# STORE-LEVEL TRANSPORT COSTS
# ============================================================================

st.subheader("Transport Cost by Store")

store_summary = df.groupby(['store', 'region']).agg(
    total_cost=('total_cost', 'sum'),
    distance_km=('distance_km', 'mean'),
    cost_per_km=('cost_per_km', 'mean'),
    pallets=('pallets', 'sum'),
    cost_per_pallet=('cost_per_pallet', 'mean'),
    delivery_time_hrs=('delivery_time_hrs', 'mean'),
).reset_index()
store_summary['deliveries'] = df.groupby('store').size().reindex(store_summary['store']).values

col1, col2 = st.columns(2)

with col1:
    fig_stores = px.bar(
        store_summary.sort_values('total_cost', ascending=False),
        x='store', y='total_cost',
        color='cost_per_km', color_continuous_scale='RdYlGn_r',
        title="Total Cost by Store (coloured by $/km efficiency)",
        labels={'total_cost': 'Total Cost ($)', 'cost_per_km': '$/km'}
    )
    fig_stores.update_xaxes(tickangle=-45)
    fig_stores.update_layout(height=450)
    st.plotly_chart(fig_stores, key="transport_cost_by_store")

with col2:
    fig_efficiency = px.scatter(
        store_summary,
        x='distance_km', y='cost_per_km',
        size='deliveries', color='region',
        hover_data=['store'],
        title="Distance vs Cost Efficiency",
        labels={
            'distance_km': 'Average Distance (km)',
            'cost_per_km': 'Cost per KM ($)',
            'deliveries': 'Total Deliveries',
        },
    )
    fig_efficiency.update_layout(height=450)
    st.plotly_chart(fig_efficiency, key="transport_distance_vs_efficiency")

st.markdown("---")

# ============================================================================
# TIME SERIES
# ============================================================================

st.subheader("Cost Trends Over Time")

daily_costs = df.groupby('date').agg(
    total_cost=('total_cost', 'sum'),
    fuel_cost=('fuel_cost', 'sum'),
    driver_cost=('driver_cost', 'sum'),
).reset_index()

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=daily_costs['date'], y=daily_costs['total_cost'],
    name='Total Cost', line=dict(color='#1e3a8a', width=3), fill='tonexty'
))
fig_trend.add_trace(go.Scatter(
    x=daily_costs['date'], y=daily_costs['driver_cost'],
    name='Driver Cost', line=dict(color='#10b981', width=2)
))
fig_trend.add_trace(go.Scatter(
    x=daily_costs['date'], y=daily_costs['fuel_cost'],
    name='Fuel Cost', line=dict(color='#f59e0b', width=2)
))
fig_trend.update_layout(
    height=400, hovermode='x unified',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig_trend, key="transport_cost_trends")

st.markdown("---")

# ============================================================================
# OPTIMIZATION OPPORTUNITIES
# ============================================================================

st.subheader("Cost Reduction Opportunities")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Route Consolidation Analysis")
    current_cost = df['total_cost'].sum()

    # Identify routes that could share deliveries (same region, similar distance)
    region_costs = df.groupby('region')['total_cost'].sum().sort_values(ascending=False)
    consolidation_savings = region_costs.head(3).sum() * 0.20  # 20% savings on top 3 regions

    st.info(f"""
    **Opportunity:** Consolidate deliveries within regions
    - **Current Cost:** ${current_cost:,.0f}
    - **Potential Savings:** ${consolidation_savings:,.0f} (20% on top regions)
    - **Payback Period:** Immediate
    """)

    st.markdown("**Recommended Actions:**")
    for region in region_costs.head(3).index:
        region_stores = [s for s in STORES if REGIONS[s] == region]
        st.markdown(f"- Combine **{region}** runs ({', '.join(region_stores)})")

with col2:
    st.markdown("### Fleet Optimization")

    vehicle_analysis = df.groupby('vehicle_type').agg(
        total_cost=('total_cost', 'sum'),
        cost_per_pallet=('cost_per_pallet', 'mean'),
        pallets=('pallets', 'sum'),
    ).reset_index()

    fig_vehicles = px.bar(
        vehicle_analysis,
        x='vehicle_type', y='cost_per_pallet',
        color='vehicle_type',
        title="Cost per Pallet by Vehicle Type",
        labels={'cost_per_pallet': 'Cost per Pallet ($)'},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_vehicles.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig_vehicles, key="transport_cost_per_pallet_vehicle")

    if not vehicle_analysis.empty:
        best_vehicle = vehicle_analysis.loc[vehicle_analysis['cost_per_pallet'].idxmin(), 'vehicle_type']
        st.markdown(f"**Finding:** {best_vehicle}s offer best cost-per-pallet ratio")

# ============================================================================
# SCENARIO MODELING
# ============================================================================

st.markdown("---")
st.subheader("Scenario Modeling: Cost Reduction Target")

reduction_target = st.slider("Target Cost Reduction %", 5, 30, 15)

current_cost = df['total_cost'].sum()
optimized_cost = current_cost * (1 - reduction_target / 100)
period_savings = current_cost - optimized_cost

fig_scenario = go.Figure()

fig_scenario.add_trace(go.Bar(
    name='Current',
    x=['Fuel', 'Driver', 'Vehicle'],
    y=[df['fuel_cost'].sum(), df['driver_cost'].sum(), df['vehicle_cost'].sum()],
    marker_color='lightcoral'
))
fig_scenario.add_trace(go.Bar(
    name='Optimized',
    x=['Fuel', 'Driver', 'Vehicle'],
    y=[
        df['fuel_cost'].sum() * 0.90,
        df['driver_cost'].sum() * (1 - reduction_target / 100 * 1.5),
        df['vehicle_cost'].sum() * 0.85,
    ],
    marker_color='lightblue'
))
fig_scenario.update_layout(
    barmode='group', title=f"Impact of {reduction_target}% Cost Reduction",
    yaxis_title="Cost ($)", height=400
)
st.plotly_chart(fig_scenario, key="transport_scenario_model")

st.success(f"""
**Projected Savings (current period):** ${period_savings:,.0f}

**Implementation Timeline:**
- Month 1: Route analysis & planning
- Month 2: Pilot consolidated routes
- Month 3: Full rollout
- Month 4+: Monitor & optimise
""")

# ============================================================================
# DETAILED DATA TABLE
# ============================================================================

st.markdown("---")
st.subheader("Delivery Log (Recent)")

recent_deliveries = df.sort_values('date', ascending=False).head(30)

display_df = recent_deliveries[['date', 'store', 'region', 'vehicle_type', 'pallets',
                                 'distance_km', 'fuel_cost', 'driver_cost',
                                 'total_cost', 'cost_per_pallet']].copy()

display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
for col in ['fuel_cost', 'driver_cost', 'total_cost', 'cost_per_pallet']:
    display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}")

display_df.columns = ['Date', 'Store', 'Region', 'Vehicle', 'Pallets', 'Distance (km)',
                       'Fuel', 'Driver', 'Total Cost', '$/Pallet']

st.dataframe(display_df, hide_index=True, key="transport_delivery_log")

# ============================================================================
# NATURAL LANGUAGE QUERY
# ============================================================================

st.markdown("---")
st.subheader("Ask About Transport Costs")

query = st.text_input(
    "Question",
    placeholder="e.g., What are the most expensive routes per kilometer?"
)

if st.button("Analyze", type="primary"):
    if query:
        with st.spinner("Analysing transport data..."):
            st.info(f"**Question:** {query}")
            expensive = store_summary.nlargest(5, 'cost_per_km')
            st.success("**Answer:** Based on current data, the most expensive stores per kilometer are:")
            for _, row in expensive.iterrows():
                st.markdown(
                    f"- **Sydney Markets\u2192{row['store']}**: "
                    f"${row['cost_per_km']:.2f}/km (avg distance: {row['distance_km']:.0f}km)"
                )
            st.markdown("\n**Recommendation:** Prioritise these routes for consolidation or alternative delivery methods.")

# ============================================================================
# ASK A QUESTION
# ============================================================================

render_voice_data_box("general")
render_ask_question("general")

# ============================================================================
# FOOTER
# ============================================================================

render_footer("Transport & Logistics", "Data: Sydney Markets delivery runs (seed 42)", user=user)
