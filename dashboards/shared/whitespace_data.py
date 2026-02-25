"""
Whitespace Analysis — Data Loading & Helper Functions
Loads CBAS network data from data/cbas_network.json and provides
DataFrames, scoring helpers, and comparison utilities for the dashboard.
"""

import json
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go

_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "cbas_network.json"
_COORDS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "postcode_coords.json"

_cache = {}


def load_cbas_data():
    """Load full CBAS network JSON (cached in module)."""
    if "data" not in _cache:
        with open(_DATA_PATH) as f:
            _cache["data"] = json.load(f)
    return _cache["data"]


def get_stores_df():
    """Return 31 CBAS stores as a DataFrame with computed rev/sqm."""
    data = load_cbas_data()
    df = pd.DataFrame(data["stores"])
    # Clean nulls stored as string "null"
    for col in df.columns:
        df[col] = df[col].replace("null", None)
    # Compute revenue per sqm
    df["Store Size (SQM)"] = pd.to_numeric(df["Store Size (SQM)"], errors="coerce")
    df["Annual Sales ($M)"] = pd.to_numeric(df["Annual Sales ($M)"], errors="coerce")
    df["Rev per SQM"] = (df["Annual Sales ($M)"] * 1_000_000 / df["Store Size (SQM)"]).round(0)
    # Short name (strip "Harris Farm Markets ")
    df["Short Name"] = df["Store Name"].str.replace("Harris Farm Markets ", "", regex=False)
    return df


def get_opportunities_df():
    """Return 16 whitespace opportunities as a DataFrame."""
    data = load_cbas_data()
    df = pd.DataFrame(data["whitespace_opportunities"])
    return df


def get_ideal_profile():
    """Return ideal store profile benchmarks."""
    data = load_cbas_data()
    return data.get("ideal_profile", {})


def get_catchments():
    """Return store → catchment dict."""
    data = load_cbas_data()
    return data.get("catchments", {})


def get_reconciliation():
    """Return store reconciliation data."""
    data = load_cbas_data()
    return data.get("store_reconciliation", {})


def get_meta():
    """Return metadata about the dataset."""
    data = load_cbas_data()
    return data.get("meta", {})


def get_postcode_coords():
    """Load postcode → {lat, lon} lookup from coords file."""
    if "coords" not in _cache:
        with open(_COORDS_PATH) as f:
            _cache["coords"] = json.load(f)
    return _cache["coords"]


def get_store_coords():
    """Return dict of store short name → {lat, lon} from CBAS data + postcode coords."""
    coords = get_postcode_coords()
    catchments = get_catchments()
    stores_df = get_stores_df()
    result = {}
    for _, row in stores_df.iterrows():
        short = row["Short Name"]
        full = row["Store Name"]
        # Try to get coords from catchment locality postcode
        catch = catchments.get(full, {})
        postcodes_str = catch.get("postcodes", "")
        if postcodes_str:
            first_pc = postcodes_str.split(",")[0].strip()
            if first_pc in coords:
                result[short] = {
                    "lat": coords[first_pc]["lat"],
                    "lon": coords[first_pc]["lon"],
                    "locality": catch.get("locality", row.get("Locality", "")),
                }
                continue
        # Fallback: try store locality postcode from the store data
        locality = str(row.get("Locality", ""))
        for pc, c in coords.items():
            if pc == str(row.get("Store Size (SQM)", "")):
                continue
        # If no coord found, skip
        result[short] = {"lat": None, "lon": None, "locality": locality}
    return result


def score_breakdown_chart(opp):
    """Create a horizontal bar chart of score breakdown for one opportunity."""
    breakdown = opp.get("score_breakdown", {})
    if not breakdown:
        return None
    labels = {
        "population_density": "Population Density",
        "income_alignment": "Income Alignment",
        "existing_share_signal": "Existing Share Signal",
        "competitor_saturation": "Competitor Saturation",
        "distance_from_hfm": "Distance from HFM",
        "population_growth": "Population Growth",
        "site_feasibility": "Site Feasibility",
    }
    max_scores = {
        "population_density": 20,
        "income_alignment": 20,
        "existing_share_signal": 15,
        "competitor_saturation": 15,
        "distance_from_hfm": 10,
        "population_growth": 10,
        "site_feasibility": 10,
    }
    cats = list(labels.keys())
    values = [breakdown.get(c, 0) for c in cats]
    maxes = [max_scores.get(c, 10) for c in cats]
    names = [labels.get(c, c) for c in cats]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=maxes, orientation="h",
        marker_color="rgba(255,255,255,0.08)", name="Max",
        hoverinfo="skip",
    ))
    fig.add_trace(go.Bar(
        y=names, x=values, orientation="h",
        marker_color="#2ECC71", name="Score",
        text=[str(v) for v in values], textposition="auto",
    ))
    fig.update_layout(
        barmode="overlay",
        height=280,
        margin=dict(l=0, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FFFFFF", size=12),
        showlegend=False,
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, autorange="reversed"),
    )
    return fig


def performance_tier_summary():
    """Group stores by performance tier with summary stats."""
    df = get_stores_df()
    df["Performance Tier"] = pd.to_numeric(df["Performance Tier"], errors="coerce")
    grouped = df.groupby("Performance Tier").agg(
        Count=("Store Name", "count"),
        Avg_Sales=("Annual Sales ($M)", "mean"),
        Avg_RevSQM=("Rev per SQM", "mean"),
        Avg_Share=("Market Share", "mean"),
    ).reset_index()
    grouped.columns = ["Tier", "Stores", "Avg Sales ($M)", "Avg Rev/SQM", "Avg Share"]
    return grouped.round(1)


def format_comparison(store_name):
    """Compare one store's metrics against the ideal profile."""
    df = get_stores_df()
    profile = get_ideal_profile()
    row = df[df["Short Name"] == store_name]
    if row.empty:
        row = df[df["Store Name"].str.contains(store_name, case=False, na=False)]
    if row.empty:
        return None
    row = row.iloc[0]
    tq = profile.get("top_quartile_metrics", {})
    return {
        "store": store_name,
        "metrics": {
            "Sales ($M)": {"store": row.get("Annual Sales ($M)"), "benchmark": tq.get("avg_sales_m")},
            "SQM": {"store": row.get("Store Size (SQM)"), "benchmark": profile.get("sqm_range", [900, 1500])},
            "Rev/SQM": {"store": row.get("Rev per SQM"), "benchmark": tq.get("avg_rev_per_sqm")},
            "Market Share": {"store": row.get("Market Share"), "benchmark": tq.get("avg_share")},
            "Share of Wallet": {"store": row.get("Share of Wallet"), "benchmark": tq.get("avg_sow")},
            "Spend/Customer": {"store": row.get("Spend per Customer ($)"), "benchmark": tq.get("avg_spend_per_customer")},
        },
    }


TIER_COLOURS = {1: "#2ECC71", 2: "#65a30d", 3: "#d97706", 4: "#ea580c", 5: "#dc2626"}
PHASE_COLOURS = {1: "#2ECC71", 2: "#3B82F6", 3: "#8B5CF6"}
CONFIDENCE_COLOURS = {"High": "#2ECC71", "Medium": "#d97706", "Low": "#dc2626"}
