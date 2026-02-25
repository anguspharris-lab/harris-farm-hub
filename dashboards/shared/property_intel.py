"""
Property Intelligence — Data Loading Module
Loads Phase 2 (ROC) and Phase 3 (Market Share) outputs for the Store Network dashboard.
Census demographics (Phase 4) will be added when available.
"""

import json
from pathlib import Path
from typing import Optional

import pandas as pd

_BASE = Path(__file__).resolve().parent.parent.parent / "data"
_ROC_DIR = _BASE / "outputs" / "roc"
_MS_DIR = _BASE / "outputs" / "market_share"
_CBAS_PATH = _BASE / "cbas_network.json"

_cache = {}


# ── ROC Data ──────────────────────────────────────────────────────────────────

def get_roc_df():
    """Load full store ROC table (29 stores, 44 columns)."""
    if "roc_df" not in _cache:
        path = _ROC_DIR / "store_roc_full.csv"
        if path.exists():
            _cache["roc_df"] = pd.read_csv(path)
        else:
            _cache["roc_df"] = pd.DataFrame()
    return _cache["roc_df"]


def get_roc_summary():
    """Load ROC summary JSON (dashboard-ready stats)."""
    if "roc_summary" not in _cache:
        path = _ROC_DIR / "store_roc_summary.json"
        if path.exists():
            with open(path) as f:
                _cache["roc_summary"] = json.load(f)
        else:
            _cache["roc_summary"] = {}
    return _cache["roc_summary"]


def get_department_gp():
    """Load department-level GP analysis."""
    if "dept_gp" not in _cache:
        path = _ROC_DIR / "department_gp.csv"
        if path.exists():
            _cache["dept_gp"] = pd.read_csv(path)
        else:
            _cache["dept_gp"] = pd.DataFrame()
    return _cache["dept_gp"]


def get_format_analysis():
    """Load format segmentation results."""
    if "format_analysis" not in _cache:
        path = _ROC_DIR / "format_analysis.json"
        if path.exists():
            with open(path) as f:
                _cache["format_analysis"] = json.load(f)
        else:
            _cache["format_analysis"] = {}
    return _cache["format_analysis"]


def get_fix_candidates():
    """Load fix candidate stores (Drummoyne pattern)."""
    if "fix_candidates" not in _cache:
        path = _ROC_DIR / "fix_candidates.json"
        if path.exists():
            with open(path) as f:
                _cache["fix_candidates"] = json.load(f)
        else:
            _cache["fix_candidates"] = {}
    return _cache["fix_candidates"]


# ── Market Share Data ─────────────────────────────────────────────────────────

def get_postcode_analysis():
    """Load postcode-level market share analysis (890 postcodes)."""
    if "postcode_analysis" not in _cache:
        path = _MS_DIR / "postcode_analysis.csv"
        if path.exists():
            _cache["postcode_analysis"] = pd.read_csv(path)
        else:
            _cache["postcode_analysis"] = pd.DataFrame()
    return _cache["postcode_analysis"]


def get_store_catchments():
    """Load per-store catchment health data."""
    if "store_catchments" not in _cache:
        path = _MS_DIR / "store_catchments.csv"
        if path.exists():
            _cache["store_catchments"] = pd.read_csv(path)
        else:
            _cache["store_catchments"] = pd.DataFrame()
    return _cache["store_catchments"]


def get_quadrant_matrix():
    """Load 2x2 matrix (ROC x Market Share) classification."""
    if "quadrant_matrix" not in _cache:
        path = _MS_DIR / "quadrant_matrix.json"
        if path.exists():
            with open(path) as f:
                _cache["quadrant_matrix"] = json.load(f)
        else:
            _cache["quadrant_matrix"] = {}
    return _cache["quadrant_matrix"]


def get_cannibalisation():
    """Load cannibalisation analysis (store pairs + whitespace risks)."""
    if "cannibalisation" not in _cache:
        path = _MS_DIR / "cannibalisation.json"
        if path.exists():
            with open(path) as f:
                _cache["cannibalisation"] = json.load(f)
        else:
            _cache["cannibalisation"] = {}
    return _cache["cannibalisation"]


def get_investigation_postcodes():
    """Load investigation postcodes (low share, unvalidated)."""
    if "investigation_postcodes" not in _cache:
        path = _MS_DIR / "investigation_postcodes.csv"
        if path.exists():
            _cache["investigation_postcodes"] = pd.read_csv(path)
        else:
            _cache["investigation_postcodes"] = pd.DataFrame()
    return _cache["investigation_postcodes"]


# ── Merged Data ───────────────────────────────────────────────────────────────

def get_network_scorecard():
    """Build unified scorecard merging ROC + Market Share + CBAS data.
    Classification: Invest / Hold / Rationalise / Exit."""
    if "scorecard" not in _cache:
        roc = get_roc_df()
        catch = get_store_catchments()
        quad = get_quadrant_matrix()

        if roc.empty:
            _cache["scorecard"] = pd.DataFrame()
            return _cache["scorecard"]

        # Start with ROC data
        sc = roc[["short_name", "revenue", "gpm_pct", "gpm_roc_primary_4k",
                   "rev_roc_primary_4k", "retail_sqm", "format_segment",
                   "centre_type", "market_share", "share_of_wallet",
                   "performance_tier", "profitability_tier", "data_source",
                   "is_new_2025"]].copy()

        # Merge catchment health
        if not catch.empty:
            catch_slim = catch[["store", "weighted_avg_share_pct", "share_trend_pp",
                                "catchment_health_score"]].copy()
            catch_slim = catch_slim.rename(columns={"store": "short_name"})
            sc = sc.merge(catch_slim, on="short_name", how="left")

        # Add quadrant classification
        quad_map = {}
        if quad and "quadrants" in quad:
            for quadrant, stores in quad["quadrants"].items():
                for s in stores:
                    store_name = s.get("store", "")
                    quad_map[store_name] = quadrant
        sc["quadrant"] = sc["short_name"].map(quad_map)

        # Derive classification
        def classify(row):
            q = row.get("quadrant", "")
            new = row.get("is_new_2025", False)
            if new:
                return "Monitor (New)"
            if q == "Star":
                return "Invest"
            elif q == "Cash Cow":
                return "Hold"
            elif q == "Question Mark":
                return "Rationalise"
            elif q == "Fix or Exit":
                return "Exit Review"
            return "Unclassified"

        sc["classification"] = sc.apply(classify, axis=1)
        _cache["scorecard"] = sc
    return _cache["scorecard"]


# ── Real P&L Integration ──────────────────────────────────────────────────────

def get_real_pl_by_store(fy_year=None):
    """Load actual GL P&L data per store from store_pl_service.
    Returns DataFrame with: store_id, store_name, revenue, gross_profit,
    gp_pct, ebitda, ebitda_pct, net_profit, net_pct.
    Returns empty DataFrame if service not available."""
    if "real_pl" not in _cache:
        try:
            import sys
            backend_path = str(Path(__file__).resolve().parent.parent.parent / "backend")
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            from store_pl_service import get_store_pl_annual
            _cache["real_pl"] = get_store_pl_annual(fy_year)
        except Exception:
            _cache["real_pl"] = pd.DataFrame()
    return _cache["real_pl"]


def get_enriched_scorecard(fy_year=None):
    """Scorecard merged with actual GL P&L data where available.
    Adds: actual_revenue, actual_gp_pct, actual_ebitda_pct, actual_net_pct."""
    sc = get_network_scorecard()
    if sc.empty:
        return sc

    pl = get_real_pl_by_store(fy_year)
    if pl.empty:
        return sc

    # Build name-matching: strip "HFM " from P&L names to match short_name
    pl_slim = pl[["store_name", "revenue", "gross_profit", "gp_pct",
                   "ebitda", "ebitda_pct", "net_profit", "net_pct"]].copy()
    pl_slim["match_name"] = pl_slim["store_name"].str.replace("HFM ", "", regex=False)
    pl_slim = pl_slim.rename(columns={
        "revenue": "actual_revenue",
        "gross_profit": "actual_gp",
        "gp_pct": "actual_gp_pct",
        "ebitda": "actual_ebitda",
        "ebitda_pct": "actual_ebitda_pct",
        "net_profit": "actual_net_profit",
        "net_pct": "actual_net_pct",
    })

    enriched = sc.merge(pl_slim, left_on="short_name", right_on="match_name", how="left")
    enriched.drop(columns=["match_name", "store_name"], errors="ignore", inplace=True)
    return enriched


# ── Colour Constants ──────────────────────────────────────────────────────────

CLASSIFICATION_COLOURS = {
    "Invest": "#2ECC71",
    "Hold": "#3B82F6",
    "Rationalise": "#d97706",
    "Exit Review": "#dc2626",
    "Monitor (New)": "#8B5CF6",
    "Unclassified": "#6B7280",
}

FORMAT_COLOURS = {
    "Express": "#2ECC71",
    "Standard": "#3B82F6",
    "Large": "#d97706",
}

QUADRANT_COLOURS = {
    "Star": "#2ECC71",
    "Cash Cow": "#3B82F6",
    "Question Mark": "#d97706",
    "Fix or Exit": "#dc2626",
}
