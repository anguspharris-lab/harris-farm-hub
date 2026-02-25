"""
Phase 4 — Demographic Scoring & Integration Engine
====================================================
Generates 5 outputs to data/outputs/demographics/:
  1. store_demographic_profiles.csv   — weighted demographic profiles per store
  2. demographic_correlations.json    — correlation analysis vs performance
  3. demographic_blueprint.json       — HFM ideal demographic blueprint
  4. postcode_demographic_scores.csv  — 0-100 demographic fit score per postcode
  5. validated_opportunities.json     — ranked expansion opportunities

Usage:
    python3 scripts/demographic_scoring.py

Data lineage:
    Census  -> data/census/processed/census_postcode_demographics.parquet (1,075 postcodes)
    ROC     -> data/outputs/roc/store_roc_full.csv (29 stores)
    Share   -> data/outputs/market_share/store_catchments.csv (26 stores)
    Share   -> data/outputs/market_share/postcode_analysis.csv (890 postcodes)
    Coords  -> data/postcode_coords.json (1,040 postcodes lat/lon)
    CBAS    -> data/cbas_network.json (31 stores + 16 whitespace targets)
"""

import json
import math
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import numpy as np
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).resolve().parent.parent / "data"
_CENSUS = _BASE / "census" / "processed" / "census_postcode_demographics.parquet"
_ROC = _BASE / "outputs" / "roc" / "store_roc_full.csv"
_CATCHMENTS = _BASE / "outputs" / "market_share" / "store_catchments.csv"
_POSTCODES = _BASE / "outputs" / "market_share" / "postcode_analysis.csv"
_COORDS = _BASE / "postcode_coords.json"
_CBAS = _BASE / "cbas_network.json"
_OUT = _BASE / "outputs" / "demographics"

# Demographic columns used for profiling
PROFILE_COLS = [
    "pct_professional",
    "pct_degree",
    "median_hh_income_weekly",
    "pct_wfh",
    "pct_high_income_hh",
    "seifa_irsad_score",
    "seifa_irsad_decile",
    "median_age",
    "median_rent_weekly",
    "median_mortgage_monthly",
    "avg_household_size",
    "labour_force_participation_pct",
    "unemployment_pct",
    "total_population",
]

# Scoring weights for demographic fit (must sum to 1.0)
SCORE_WEIGHTS = {
    "pct_professional": 0.25,
    "pct_high_income_hh": 0.20,
    "median_hh_income_weekly": 0.15,
    "pct_degree": 0.15,
    "seifa_irsad_decile": 0.15,
    "pct_wfh": 0.10,
}


# ── Utilities ────────────────────────────────────────────────────────────────

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points in kilometres."""
    R = 6371.0
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_coords() -> Dict[str, Dict[str, float]]:
    """Load postcode -> {lat, lon} mapping."""
    with open(_COORDS) as f:
        raw = json.load(f)
    # Keys may be strings, ensure consistent str postcodes
    return {str(k): v for k, v in raw.items()}


def load_cbas() -> dict:
    """Load CBAS network JSON."""
    with open(_CBAS) as f:
        return json.load(f)


def build_store_postcode_map(cbas: dict, coords: dict) -> Dict[str, str]:
    """Map store short_name -> postcode using CBAS locality + coords reverse lookup.

    Strategy: For each CBAS store, find the closest postcode to its locality
    by matching locality names in the region_name of postcode_analysis,
    or by using known locality->postcode mappings.
    """
    # Build known locality -> postcode from postcode_analysis region_name
    pc_df = pd.read_csv(_POSTCODES)
    # Filter out aggregate rows (state/country-level: ACT, NSW, QLD, AUS)
    pc_df = pc_df[pd.to_numeric(pc_df["postcode"], errors="coerce").notna()].copy()
    region_to_postcode = {}
    for _, row in pc_df.iterrows():
        region_to_postcode[str(row["region_name"]).strip().lower()] = str(int(float(row["postcode"])))

    # Also build from CBAS store names + catchments to find store postcodes
    catchments = cbas.get("catchments", {})

    # Manual mappings from CBAS locality to postcode (known Sydney/NSW suburbs)
    locality_postcode = {
        "Albury": "2640",
        "Bondi Beach": "2026",
        "Bondi Junction": "2022",
        "Gladesville": "2111",
        "Bowral": "2576",
        "Glebe (NSW)": "2037",
        "Cammeray": "2062",
        "Clayfield": "4011",
        "Cooks Hill": "2300",
        "Drummoyne": "2047",
        "Dural (Hornsby - NSW)": "2158",
        "Erina": "2250",
        "Surfers Paradise": "4217",
        "Lane Cove": "2066",
        "Leichhardt (NSW)": "2040",
        "Lindfield": "2070",
        "Canberra Airport": "2609",
        "Manly (NSW)": "2095",
        "Marrickville": "2204",
        "Miranda (NSW)": "2228",
        "Mona Vale": "2103",
        "Mosman": "2088",
        "Orange": "2800",
        "Pennant Hills": "2120",
        "Potts Point": "2011",
        "Randwick": "2031",
        "Redfern": "2016",
        "Rose Bay (NSW)": "2029",
        "St Ives (NSW)": "2075",
        "West End (Brisbane - Qld)": "4101",
        "North Willoughby": "2068",
    }

    store_map = {}
    for store in cbas["stores"]:
        short = store["Store Name"].replace("Harris Farm Markets ", "")
        locality = store["Locality"]
        pc = locality_postcode.get(locality)
        if pc:
            store_map[short] = pc
        else:
            # Fallback: try matching locality in region_to_postcode
            key = locality.strip().lower()
            if key in region_to_postcode:
                store_map[short] = region_to_postcode[key]

    return store_map


def round_dict(d: dict, decimals: int = 2) -> dict:
    """Round all float values in a dict to given decimal places."""
    out = {}
    for k, v in d.items():
        if isinstance(v, float):
            out[k] = round(v, decimals)
        elif isinstance(v, dict):
            out[k] = round_dict(v, decimals)
        elif isinstance(v, list):
            out[k] = [round_dict(i, decimals) if isinstance(i, dict) else (round(i, decimals) if isinstance(i, float) else i) for i in v]
        else:
            out[k] = v
    return out


# ── Output 1: Store Demographic Profiles ─────────────────────────────────────

def build_store_profiles(census: pd.DataFrame, pc_analysis: pd.DataFrame,
                         catchments: pd.DataFrame, store_pc_map: Dict[str, str],
                         coords: dict) -> pd.DataFrame:
    """Build weighted demographic profiles per store using catchment postcodes.

    For each store, find postcodes within 10km (from postcode_analysis nearest_store
    assignment or by haversine from store postcode), then compute
    population-weighted averages of demographic metrics.
    """
    print("  Building store demographic profiles...")

    # Ensure postcode columns are string
    census["postcode"] = census["postcode"].astype(str)
    pc_analysis["postcode"] = pc_analysis["postcode"].astype(int).astype(str)

    # Merge census onto postcodes in the analysis
    census_lookup = census.set_index("postcode")

    results = []

    for _, row in catchments.iterrows():
        store = row["store"]
        locality = row["locality"]
        store_pc = store_pc_map.get(store)

        # Find catchment postcodes: use postcode_analysis where nearest_store == store
        # AND distance <= 10km
        store_pcs = pc_analysis[
            (pc_analysis["nearest_store"] == store) &
            (pc_analysis["distance_km"] <= 10.0)
        ].copy()

        # Also, if we have the store postcode, find additional nearby postcodes
        # from census that are within 10km (via haversine) but not already included
        if store_pc and store_pc in coords:
            store_lat = coords[store_pc]["lat"]
            store_lon = coords[store_pc]["lon"]

            existing_pcs = set(store_pcs["postcode"].astype(str).tolist())

            extra_pcs = []
            for pc_str, c in coords.items():
                if pc_str in existing_pcs:
                    continue
                if pc_str not in census_lookup.index:
                    continue
                dist = haversine_km(store_lat, store_lon, c["lat"], c["lon"])
                if dist <= 10.0:
                    extra_pcs.append(pc_str)

            # Add extras with basic info
            if extra_pcs:
                extra_rows = []
                for pc_str in extra_pcs:
                    dist = haversine_km(store_lat, store_lon,
                                        coords[pc_str]["lat"], coords[pc_str]["lon"])
                    extra_rows.append({
                        "postcode": pc_str,
                        "nearest_store": store,
                        "distance_km": round(dist, 2),
                        "market_share_pct": 0.0,  # no market share data for these
                    })
                extra_df = pd.DataFrame(extra_rows)
                store_pcs = pd.concat([store_pcs, extra_df], ignore_index=True)

        if store_pcs.empty:
            continue

        # Merge census demographics
        store_pcs["postcode"] = store_pcs["postcode"].astype(str)
        demo = store_pcs.merge(
            census[["postcode", "total_population"] + [c for c in PROFILE_COLS if c != "total_population"]],
            on="postcode",
            how="inner",
        )

        if demo.empty:
            continue

        # Population-weighted averages
        pop = demo["total_population"].fillna(0).values
        total_pop = pop.sum()
        if total_pop == 0:
            continue

        weights = pop / total_pop

        profile = {
            "store": store,
            "locality": locality,
            "store_postcode": store_pc if store_pc else "",
            "catchment_postcodes": len(demo),
            "catchment_pop": int(total_pop),
        }

        # Weighted average for each metric
        for col in PROFILE_COLS:
            if col == "total_population":
                continue
            vals = pd.to_numeric(demo[col], errors="coerce").fillna(0).values
            wtd_avg = float(np.sum(vals * weights))
            col_name = col + "_catchment"
            profile[col_name] = round(wtd_avg, 2)

        results.append(profile)

    df = pd.DataFrame(results)
    # Sort by store name
    df = df.sort_values("store").reset_index(drop=True)
    return df


# ── Output 2: Correlation Analysis ──────────────────────────────────────────

def correlation_analysis(store_profiles: pd.DataFrame, roc: pd.DataFrame,
                         catchments: pd.DataFrame) -> dict:
    """Correlate store demographics with performance metrics."""
    print("  Running correlation analysis...")

    # Merge store profiles with ROC and catchment data
    merged = store_profiles.copy()

    # Join ROC metrics
    roc_cols = ["short_name", "gpm_roc_primary_4k", "rev_roc_primary_4k", "gpm_pct", "revenue"]
    roc_slim = roc[roc_cols].rename(columns={"short_name": "store"})
    merged = merged.merge(roc_slim, on="store", how="inner")

    # Join catchment health
    catch_cols = ["store", "weighted_avg_share_pct", "catchment_health_score"]
    merged = merged.merge(catchments[catch_cols], on="store", how="inner")

    # Performance columns
    perf_cols = ["gpm_roc_primary_4k", "rev_roc_primary_4k",
                 "weighted_avg_share_pct", "catchment_health_score"]

    # Demographic columns (catchment-weighted)
    demo_cols = [c for c in merged.columns if c.endswith("_catchment")]

    # Calculate correlations
    corr_matrix = {}
    for perf in perf_cols:
        corr_matrix[perf] = {}
        for demo in demo_cols:
            x = pd.to_numeric(merged[demo], errors="coerce")
            y = pd.to_numeric(merged[perf], errors="coerce")
            valid = x.notna() & y.notna()
            if valid.sum() < 5:
                corr_matrix[perf][demo] = None
                continue
            corr = float(x[valid].corr(y[valid]))
            corr_matrix[perf][demo] = round(corr, 4)

    # Rank top predictors by absolute correlation
    predictor_scores = {}
    for demo in demo_cols:
        abs_corrs = []
        for perf in perf_cols:
            val = corr_matrix[perf].get(demo)
            if val is not None:
                abs_corrs.append(abs(val))
        if abs_corrs:
            predictor_scores[demo] = round(float(np.mean(abs_corrs)), 4)

    ranked_predictors = sorted(predictor_scores.items(), key=lambda x: x[1], reverse=True)

    output = {
        "correlation_matrix": corr_matrix,
        "top_predictors": [
            {"demographic": k, "avg_abs_correlation": v}
            for k, v in ranked_predictors
        ],
        "n_stores_analysed": len(merged),
        "performance_metrics": perf_cols,
        "demographic_metrics": demo_cols,
    }
    return output


# ── Output 3: Demographic Blueprint ─────────────────────────────────────────

def demographic_blueprint(store_profiles: pd.DataFrame, roc: pd.DataFrame) -> dict:
    """Build ideal demographic blueprint using top/bottom quartile stores by GPM ROC."""
    print("  Building demographic blueprint...")

    # Merge profiles with ROC
    merged = store_profiles.merge(
        roc[["short_name", "gpm_roc_primary_4k", "rev_roc_primary_4k", "gpm_pct"]].rename(
            columns={"short_name": "store"}
        ),
        on="store",
        how="inner",
    )

    if merged.empty:
        return {"error": "No stores could be merged between profiles and ROC data"}

    # Quartile cutoffs
    q1_threshold = merged["gpm_roc_primary_4k"].quantile(0.75)
    q4_threshold = merged["gpm_roc_primary_4k"].quantile(0.25)

    top_q = merged[merged["gpm_roc_primary_4k"] >= q1_threshold]
    bottom_q = merged[merged["gpm_roc_primary_4k"] <= q4_threshold]

    demo_cols = [c for c in merged.columns if c.endswith("_catchment")]

    # Build profiles
    top_profile = {}
    bottom_profile = {}
    ideal_ranges = {}
    differentiators = []

    for col in demo_cols:
        top_vals = pd.to_numeric(top_q[col], errors="coerce").dropna()
        bottom_vals = pd.to_numeric(bottom_q[col], errors="coerce").dropna()
        all_vals = pd.to_numeric(merged[col], errors="coerce").dropna()

        top_mean = float(top_vals.mean()) if len(top_vals) > 0 else 0
        bottom_mean = float(bottom_vals.mean()) if len(bottom_vals) > 0 else 0
        all_mean = float(all_vals.mean()) if len(all_vals) > 0 else 0

        top_profile[col] = round(top_mean, 2)
        bottom_profile[col] = round(bottom_mean, 2)

        # Ideal range: from network mean to top quartile mean
        low_bound = round(min(all_mean, top_mean), 2)
        high_bound = round(float(top_vals.max()) if len(top_vals) > 0 else top_mean, 2)
        ideal_ranges[col] = {"min": low_bound, "max": high_bound, "top_q_avg": round(top_mean, 2)}

        # Difference as % of network mean to identify differentiators
        if all_mean != 0:
            diff_pct = round(((top_mean - bottom_mean) / all_mean) * 100, 1)
        else:
            diff_pct = 0.0

        differentiators.append({
            "metric": col,
            "top_quartile_avg": round(top_mean, 2),
            "bottom_quartile_avg": round(bottom_mean, 2),
            "network_avg": round(all_mean, 2),
            "difference_pct": diff_pct,
        })

    # Sort differentiators by absolute difference
    differentiators.sort(key=lambda x: abs(x["difference_pct"]), reverse=True)

    output = {
        "method": "Top quartile stores by GPM ROC (Primary @ $4k/sqm)",
        "top_quartile_threshold": round(float(q1_threshold), 2),
        "bottom_quartile_threshold": round(float(q4_threshold), 2),
        "top_quartile_stores": top_q["store"].tolist(),
        "bottom_quartile_stores": bottom_q["store"].tolist(),
        "top_quartile_profile": top_profile,
        "bottom_quartile_profile": bottom_profile,
        "ideal_ranges": ideal_ranges,
        "key_differentiators": differentiators[:10],
        "all_differentiators": differentiators,
        "n_top_quartile": len(top_q),
        "n_bottom_quartile": len(bottom_q),
    }
    return output


# ── Output 4: Postcode Demographic Scores ────────────────────────────────────

def score_postcodes(census: pd.DataFrame) -> pd.DataFrame:
    """Score all 1,075 postcodes on HFM demographic fit (0-100 scale).

    Uses min-max normalisation per metric, then weighted sum.
    Higher = better fit for HFM.
    """
    print("  Scoring postcodes on demographic fit...")

    df = census.copy()
    df["postcode"] = df["postcode"].astype(str)

    # Ensure numeric
    for col in SCORE_WEIGHTS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Min-max normalise each scoring column to 0-100
    normalised = {}
    for col, weight in SCORE_WEIGHTS.items():
        vals = df[col].copy()
        vmin = vals.min()
        vmax = vals.max()
        if vmax == vmin:
            normalised[col] = pd.Series(50.0, index=df.index)
        else:
            normalised[col] = ((vals - vmin) / (vmax - vmin)) * 100.0

    # Weighted sum
    score = pd.Series(0.0, index=df.index)
    for col, weight in SCORE_WEIGHTS.items():
        score += normalised[col].fillna(0) * weight

    df["demographic_score"] = score.round(2)

    # Build output
    output_cols = ["postcode", "state", "total_population", "demographic_score"]
    for col in SCORE_WEIGHTS:
        output_cols.append(col)
    # Add a few extra useful columns
    for extra in ["median_age", "avg_household_size", "unemployment_pct",
                   "labour_force_participation_pct", "median_rent_weekly"]:
        if extra not in output_cols:
            output_cols.append(extra)

    result = df[output_cols].copy()
    result["rank"] = result["demographic_score"].rank(ascending=False, method="min").astype(int)
    result = result.sort_values("demographic_score", ascending=False).reset_index(drop=True)

    # Round all floats
    float_cols = result.select_dtypes(include=["float64", "float32"]).columns
    result[float_cols] = result[float_cols].round(2)

    return result


# ── Output 5: Validated Opportunities ────────────────────────────────────────

def validated_opportunities(
    pc_scores: pd.DataFrame,
    pc_analysis: pd.DataFrame,
    cbas: dict,
    store_pc_map: Dict[str, str],
    coords: dict,
) -> dict:
    """Cross-reference demographic scores with market share to find opportunities."""
    print("  Validating whitespace opportunities...")

    # Build store coordinate lookup
    store_coords = {}
    for store, pc in store_pc_map.items():
        if pc in coords:
            store_coords[store] = coords[pc]

    # Merge demographic scores with postcode analysis
    pc_scores_copy = pc_scores.copy()
    pc_scores_copy["postcode"] = pc_scores_copy["postcode"].astype(str)

    pc_analysis_copy = pc_analysis.copy()
    pc_analysis_copy["postcode"] = pc_analysis_copy["postcode"].astype(int).astype(str)

    merged = pc_scores_copy.merge(
        pc_analysis_copy[["postcode", "region_name", "market_share_pct",
                          "nearest_store", "distance_km"]],
        on="postcode",
        how="left",
    )

    # ---- Category 1: High demo score + low HFM share (existing presence) ----
    existing = merged[merged["market_share_pct"].notna()].copy()
    opportunities = existing[
        (existing["demographic_score"] > 70) &
        (existing["market_share_pct"] < 5.0)
    ].copy()

    # ---- Category 2: High demo score + NO HFM presence (no share data) ----
    no_presence = merged[merged["market_share_pct"].isna()].copy()
    expansion = no_presence[no_presence["demographic_score"] > 70].copy()

    # For expansion targets, find nearest store and distance
    expansion_records = []
    for _, row in expansion.iterrows():
        pc = row["postcode"]
        if pc not in coords:
            continue
        lat, lon = coords[pc]["lat"], coords[pc]["lon"]
        nearest = None
        min_dist = float("inf")
        for s, sc in store_coords.items():
            d = haversine_km(lat, lon, sc["lat"], sc["lon"])
            if d < min_dist:
                min_dist = d
                nearest = s
        expansion_records.append({
            "postcode": pc,
            "state": row.get("state", ""),
            "demographic_score": row["demographic_score"],
            "hfm_share_pct": 0.0,
            "nearest_store": nearest,
            "distance_km": round(min_dist, 2),
            "category": "expansion_target",
        })

    # Opportunity records
    opp_records = []
    for _, row in opportunities.iterrows():
        pc = row["postcode"]
        if pc not in coords:
            # Use distance from postcode_analysis if available
            dist = row.get("distance_km", None)
            nearest = row.get("nearest_store", None)
        else:
            lat, lon = coords[pc]["lat"], coords[pc]["lon"]
            nearest = None
            min_dist = float("inf")
            for s, sc in store_coords.items():
                d = haversine_km(lat, lon, sc["lat"], sc["lon"])
                if d < min_dist:
                    min_dist = d
                    nearest = s
            dist = round(min_dist, 2)
            nearest = nearest

        opp_records.append({
            "postcode": pc,
            "suburb": str(row.get("region_name", "")),
            "state": row.get("state", ""),
            "demographic_score": row["demographic_score"],
            "hfm_share_pct": round(float(row["market_share_pct"]), 2),
            "nearest_store": nearest,
            "distance_km": dist,
            "category": "low_share_opportunity",
        })

    all_opps = opp_records + expansion_records

    # Add cannibalisation risk: within 5km of existing store
    for opp in all_opps:
        dist = opp.get("distance_km")
        if dist is not None and dist < 5.0:
            opp["cannibalisation_risk"] = True
        else:
            opp["cannibalisation_risk"] = False

    # Score: demographic_score * (1 - current_hfm_share/20)
    for opp in all_opps:
        share = opp.get("hfm_share_pct", 0)
        penalty = max(0, 1 - share / 20.0)
        opp["overall_opportunity_score"] = round(opp["demographic_score"] * penalty, 2)

    # Sort by overall score
    all_opps.sort(key=lambda x: x["overall_opportunity_score"], reverse=True)

    # Add rank
    for i, opp in enumerate(all_opps):
        opp["rank"] = i + 1

    # ---- Enrich CBAS whitespace targets with demographic scores ----
    cbas_whitespace = cbas.get("whitespace_opportunities", [])
    enriched_whitespace = []
    for w in cbas_whitespace:
        pc = str(w.get("postcode", ""))
        demo_row = pc_scores_copy[pc_scores_copy["postcode"] == pc]
        demo_score = float(demo_row["demographic_score"].iloc[0]) if not demo_row.empty else None
        demo_rank = int(demo_row["rank"].iloc[0]) if not demo_row.empty else None

        # Check if postcode is in our market share data
        share_row = pc_analysis_copy[pc_analysis_copy["postcode"] == pc]
        share_pct = float(share_row["market_share_pct"].iloc[0]) if not share_row.empty else None

        enriched_whitespace.append({
            "cbas_rank": w["rank"],
            "suburb": w["suburb"],
            "state": w["state"],
            "postcode": pc,
            "cbas_score": w["score"],
            "demographic_score": demo_score,
            "demographic_rank": demo_rank,
            "hfm_share_pct": round(share_pct, 2) if share_pct is not None else None,
            "nearest_hfm": w.get("nearest_hfm"),
            "distance_km": w.get("distance_km"),
            "recommended_format": w.get("recommended_format"),
            "addressable_revenue_m": w.get("addressable_revenue_m"),
            "cannibalisation_risk": w.get("distance_km", 999) < 5.0 if w.get("distance_km") else False,
        })

    # Summary stats
    summary = {
        "total_postcodes_scored": len(pc_scores),
        "postcodes_with_share_data": len(existing),
        "low_share_opportunities": len(opp_records),
        "expansion_targets": len(expansion_records),
        "high_cannibalisation_risk": sum(1 for o in all_opps if o.get("cannibalisation_risk")),
        "cbas_whitespace_targets": len(enriched_whitespace),
    }

    output = {
        "summary": summary,
        "ranked_opportunities": all_opps[:100],  # top 100
        "cbas_whitespace_enriched": enriched_whitespace,
        "scoring_method": "demographic_score * (1 - hfm_share_pct / 20)",
        "opportunity_threshold": "demographic_score > 70 AND hfm_share < 5%",
        "cannibalisation_radius_km": 5.0,
    }
    return output


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Phase 4: Demographic Scoring & Integration Engine")
    print("=" * 70)

    # Ensure output directory exists
    _OUT.mkdir(parents=True, exist_ok=True)

    # ── Load data ──
    print("\nLoading data...")
    census = pd.read_parquet(_CENSUS)
    print(f"  Census: {len(census)} postcodes, {len(census.columns)} columns")

    roc = pd.read_csv(_ROC)
    print(f"  ROC: {len(roc)} stores, {len(roc.columns)} columns")

    catchments = pd.read_csv(_CATCHMENTS)
    print(f"  Catchments: {len(catchments)} stores")

    pc_analysis = pd.read_csv(_POSTCODES)
    # Filter out aggregate rows (state/country-level: ACT, NSW, QLD, AUS)
    pc_analysis = pc_analysis[pd.to_numeric(pc_analysis["postcode"], errors="coerce").notna()].copy()
    print(f"  Postcode analysis: {len(pc_analysis)} postcodes")

    coords = load_coords()
    print(f"  Coordinates: {len(coords)} postcodes")

    cbas = load_cbas()
    print(f"  CBAS: {len(cbas['stores'])} stores, {len(cbas.get('whitespace_opportunities', []))} whitespace targets")

    store_pc_map = build_store_postcode_map(cbas, coords)
    print(f"  Store->postcode mapping: {len(store_pc_map)} stores mapped")

    # ── Output 1: Store Demographic Profiles ──
    print("\n[1/5] Store Demographic Profiles")
    store_profiles = build_store_profiles(census, pc_analysis, catchments, store_pc_map, coords)
    store_profiles.to_csv(_OUT / "store_demographic_profiles.csv", index=False)
    print(f"  -> {len(store_profiles)} stores profiled -> store_demographic_profiles.csv")

    # ── Output 2: Correlation Analysis ──
    print("\n[2/5] Correlation Analysis")
    corr_output = correlation_analysis(store_profiles, roc, catchments)
    with open(_OUT / "demographic_correlations.json", "w") as f:
        json.dump(corr_output, f, indent=2)
    top3 = corr_output["top_predictors"][:3]
    print(f"  -> Top predictors: {', '.join(p['demographic'] for p in top3)}")
    print(f"  -> {corr_output['n_stores_analysed']} stores analysed -> demographic_correlations.json")

    # ── Output 3: Demographic Blueprint ──
    print("\n[3/5] Demographic Blueprint")
    blueprint = demographic_blueprint(store_profiles, roc)
    with open(_OUT / "demographic_blueprint.json", "w") as f:
        json.dump(blueprint, f, indent=2)
    print(f"  -> Top quartile stores: {blueprint.get('top_quartile_stores', [])}")
    print(f"  -> Bottom quartile stores: {blueprint.get('bottom_quartile_stores', [])}")
    print(f"  -> demographic_blueprint.json")

    # ── Output 4: Postcode Demographic Scores ──
    print("\n[4/5] Postcode Demographic Scores")
    pc_scores = score_postcodes(census)
    pc_scores.to_csv(_OUT / "postcode_demographic_scores.csv", index=False)
    print(f"  -> {len(pc_scores)} postcodes scored -> postcode_demographic_scores.csv")
    print(f"  -> Score range: {pc_scores['demographic_score'].min():.1f} - {pc_scores['demographic_score'].max():.1f}")
    print(f"  -> Mean score: {pc_scores['demographic_score'].mean():.1f}")

    # ── Output 5: Validated Opportunities ──
    print("\n[5/5] Validated Whitespace Opportunities")
    opps = validated_opportunities(pc_scores, pc_analysis, cbas, store_pc_map, coords)
    with open(_OUT / "validated_opportunities.json", "w") as f:
        json.dump(opps, f, indent=2)
    s = opps["summary"]
    print(f"  -> Low-share opportunities: {s['low_share_opportunities']}")
    print(f"  -> Expansion targets: {s['expansion_targets']}")
    print(f"  -> Cannibalisation risks: {s['high_cannibalisation_risk']}")
    print(f"  -> CBAS whitespace enriched: {s['cbas_whitespace_targets']}")
    print(f"  -> validated_opportunities.json")

    print("\n" + "=" * 70)
    print("Phase 4 complete. All outputs in: data/outputs/demographics/")
    print("=" * 70)


if __name__ == "__main__":
    main()
