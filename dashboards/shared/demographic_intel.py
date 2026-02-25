"""
Demographic Intelligence — Data Loading Module
Loads Phase 4 demographic scoring outputs for dashboard consumption.
Mirrors the pattern of dashboards/shared/property_intel.py.
"""

import json
from pathlib import Path
from typing import Optional

import pandas as pd

_BASE = Path(__file__).resolve().parent.parent.parent / "data"
_DEMO_DIR = _BASE / "outputs" / "demographics"

_cache = {}


# ── Store Profiles ───────────────────────────────────────────────────────────

def get_store_profiles() -> pd.DataFrame:
    """Load per-store weighted demographic profiles (26 stores)."""
    if "store_profiles" not in _cache:
        path = _DEMO_DIR / "store_demographic_profiles.csv"
        if path.exists():
            _cache["store_profiles"] = pd.read_csv(path)
        else:
            _cache["store_profiles"] = pd.DataFrame()
    return _cache["store_profiles"]


# ── Correlations ─────────────────────────────────────────────────────────────

def get_correlations() -> dict:
    """Load demographic-to-performance correlation analysis."""
    if "correlations" not in _cache:
        path = _DEMO_DIR / "demographic_correlations.json"
        if path.exists():
            with open(path) as f:
                _cache["correlations"] = json.load(f)
        else:
            _cache["correlations"] = {}
    return _cache["correlations"]


def get_top_predictors(n: int = 5) -> list:
    """Return the top N demographic predictors ranked by avg absolute correlation."""
    corr = get_correlations()
    predictors = corr.get("top_predictors", [])
    return predictors[:n]


# ── Blueprint ────────────────────────────────────────────────────────────────

def get_blueprint() -> dict:
    """Load the HFM ideal demographic blueprint."""
    if "blueprint" not in _cache:
        path = _DEMO_DIR / "demographic_blueprint.json"
        if path.exists():
            with open(path) as f:
                _cache["blueprint"] = json.load(f)
        else:
            _cache["blueprint"] = {}
    return _cache["blueprint"]


def get_ideal_ranges() -> dict:
    """Extract ideal demographic ranges from blueprint."""
    bp = get_blueprint()
    return bp.get("ideal_ranges", {})


def get_top_quartile_stores() -> list:
    """Return list of top-quartile store names (by GPM ROC)."""
    bp = get_blueprint()
    return bp.get("top_quartile_stores", [])


# ── Postcode Scores ──────────────────────────────────────────────────────────

def get_postcode_scores() -> pd.DataFrame:
    """Load demographic fit scores for all 1,075 postcodes."""
    if "postcode_scores" not in _cache:
        path = _DEMO_DIR / "postcode_demographic_scores.csv"
        if path.exists():
            _cache["postcode_scores"] = pd.read_csv(path)
        else:
            _cache["postcode_scores"] = pd.DataFrame()
    return _cache["postcode_scores"]


def get_top_postcodes(n: int = 20, min_population: int = 1000) -> pd.DataFrame:
    """Return top N postcodes by demographic score (filtered by min population)."""
    df = get_postcode_scores()
    if df.empty:
        return df
    filtered = df[df["total_population"] >= min_population]
    return filtered.head(n)


def get_postcode_score(postcode: str) -> Optional[dict]:
    """Look up demographic score for a single postcode. Returns dict or None."""
    df = get_postcode_scores()
    if df.empty:
        return None
    match = df[df["postcode"].astype(str) == str(postcode)]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


# ── Validated Opportunities ──────────────────────────────────────────────────

def get_opportunities() -> dict:
    """Load validated whitespace opportunities."""
    if "opportunities" not in _cache:
        path = _DEMO_DIR / "validated_opportunities.json"
        if path.exists():
            with open(path) as f:
                _cache["opportunities"] = json.load(f)
        else:
            _cache["opportunities"] = {}
    return _cache["opportunities"]


def get_ranked_opportunities(n: int = 20) -> list:
    """Return top N ranked expansion/growth opportunities."""
    opps = get_opportunities()
    ranked = opps.get("ranked_opportunities", [])
    return ranked[:n]


def get_cbas_whitespace_enriched() -> list:
    """Return CBAS 16 whitespace targets enriched with demographic scores."""
    opps = get_opportunities()
    return opps.get("cbas_whitespace_enriched", [])


def get_opportunity_summary() -> dict:
    """Return summary counts of opportunity types."""
    opps = get_opportunities()
    return opps.get("summary", {})


# ── Merged Views ─────────────────────────────────────────────────────────────

def get_store_scorecard_with_demographics() -> pd.DataFrame:
    """Merge store demographic profiles with ROC + catchment data for unified view.

    Returns a DataFrame with store, demographics, ROC, and market share columns.
    Useful for the Store Network / Mission Control dashboards.
    """
    if "scorecard_demo" not in _cache:
        profiles = get_store_profiles()
        if profiles.empty:
            _cache["scorecard_demo"] = pd.DataFrame()
            return _cache["scorecard_demo"]

        # Load ROC and catchments
        roc_path = _BASE / "outputs" / "roc" / "store_roc_full.csv"
        catch_path = _BASE / "outputs" / "market_share" / "store_catchments.csv"

        merged = profiles.copy()

        if roc_path.exists():
            roc = pd.read_csv(roc_path)
            roc_slim = roc[["short_name", "gpm_roc_primary_4k", "rev_roc_primary_4k",
                            "gpm_pct", "revenue", "format_segment"]].rename(
                columns={"short_name": "store"}
            )
            merged = merged.merge(roc_slim, on="store", how="left")

        if catch_path.exists():
            catch = pd.read_csv(catch_path)
            catch_slim = catch[["store", "weighted_avg_share_pct",
                                "catchment_health_score"]].copy()
            merged = merged.merge(catch_slim, on="store", how="left")

        _cache["scorecard_demo"] = merged
    return _cache["scorecard_demo"]


# ── Cache Management ─────────────────────────────────────────────────────────

def clear_cache():
    """Clear all cached data. Useful during development / data refresh."""
    _cache.clear()


# ── Score Tier Labels ────────────────────────────────────────────────────────

DEMO_SCORE_TIERS = {
    "Excellent": (80, 100),
    "Strong": (65, 80),
    "Moderate": (50, 65),
    "Below Average": (35, 50),
    "Weak": (0, 35),
}

DEMO_SCORE_COLOURS = {
    "Excellent": "#2ECC71",
    "Strong": "#3B82F6",
    "Moderate": "#d97706",
    "Below Average": "#dc2626",
    "Weak": "#6B7280",
}


def score_to_tier(score: float) -> str:
    """Convert a 0-100 demographic score to a tier label."""
    for tier, (lo, hi) in DEMO_SCORE_TIERS.items():
        if lo <= score <= hi:
            return tier
    return "Unknown"
