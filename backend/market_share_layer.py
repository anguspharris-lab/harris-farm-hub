"""
Harris Farm Hub — Market Share Data Layer
Query engine for market share postcode data with spatial analysis,
trade area calculations, trend detection, and opportunity scoring.

Data: 1,040 postcodes × 37 months × 3 channels (76K rows)
Source: CBAS modelled estimates — Market Share % is the primary reliable metric.
"""

import json
import math
import os
import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "harris_farm.db")
COORDS_PATH = str(Path(__file__).resolve().parent.parent / "data" / "postcode_coords.json")

# ---------------------------------------------------------------------------
# Store coordinates — retail stores only (geocoded from known addresses)
# ---------------------------------------------------------------------------

STORE_LOCATIONS = {
    "HFM Pennant Hills":    {"postcode": "2120", "lat": -33.7380, "lon": 151.0722, "state": "NSW"},
    "HFM Merrylands":       {"postcode": "2160", "lat": -33.8363, "lon": 150.9916, "state": "NSW"},
    "HFM St Ives":          {"postcode": "2075", "lat": -33.7287, "lon": 151.1658, "state": "NSW"},
    "HFM Mosman":           {"postcode": "2088", "lat": -33.8291, "lon": 151.2440, "state": "NSW"},
    "HFM Bondi Junction":   {"postcode": "2022", "lat": -33.8917, "lon": 151.2475, "state": "NSW"},
    "HFM Willoughby":       {"postcode": "2068", "lat": -33.8006, "lon": 151.1957, "state": "NSW"},
    "HFM Broadway":         {"postcode": "2007", "lat": -33.8835, "lon": 151.1946, "state": "NSW"},
    "HFM Glendale":         {"postcode": "2285", "lat": -32.9316, "lon": 151.6375, "state": "NSW"},
    "HFM Erina":            {"postcode": "2250", "lat": -33.4375, "lon": 151.3922, "state": "NSW"},
    "HFM Orange":           {"postcode": "2800", "lat": -33.2836, "lon": 149.1013, "state": "NSW"},
    "HFM Penrith":          {"postcode": "2750", "lat": -33.7507, "lon": 150.6879, "state": "NSW"},
    "HFM Manly":            {"postcode": "2095", "lat": -33.7969, "lon": 151.2881, "state": "NSW"},
    "HFM Mona Vale":        {"postcode": "2103", "lat": -33.6774, "lon": 151.3030, "state": "NSW"},
    "HFM Baulkham Hills":   {"postcode": "2153", "lat": -33.7628, "lon": 150.9932, "state": "NSW"},
    "HFM Bowral":           {"postcode": "2576", "lat": -34.4783, "lon": 150.4183, "state": "NSW"},
    "HFM Cammeray":         {"postcode": "2062", "lat": -33.8223, "lon": 151.2122, "state": "NSW"},
    "HFM Potts Point":      {"postcode": "2011", "lat": -33.8709, "lon": 151.2270, "state": "NSW"},
    "HFM Dee Why":          {"postcode": "2099", "lat": -33.7520, "lon": 151.2868, "state": "NSW"},
    "HFM Boronia Park":     {"postcode": "2111", "lat": -33.8152, "lon": 151.1422, "state": "NSW"},
    "HFM Bondi Beach":      {"postcode": "2026", "lat": -33.8913, "lon": 151.2744, "state": "NSW"},
    "HFM Drummoyne":        {"postcode": "2047", "lat": -33.8538, "lon": 151.1505, "state": "NSW"},
    "HFM Randwick":         {"postcode": "2031", "lat": -33.9116, "lon": 151.2412, "state": "NSW"},
    "HFM Leichhardt":       {"postcode": "2040", "lat": -33.8830, "lon": 151.1570, "state": "NSW"},
    "HFM Bondi Westfield":  {"postcode": "2022", "lat": -33.8917, "lon": 151.2475, "state": "NSW"},
    "HFM Newcastle":        {"postcode": "2300", "lat": -32.9283, "lon": 151.7817, "state": "NSW"},
    "HFM Lindfield":        {"postcode": "2070", "lat": -33.7750, "lon": 151.1650, "state": "NSW"},
    "HFM Albury":           {"postcode": "2640", "lat": -36.0737, "lon": 146.9135, "state": "NSW"},
    "HFM Rose Bay":         {"postcode": "2029", "lat": -33.8716, "lon": 151.2693, "state": "NSW"},
    "HFM West End":         {"postcode": "4101", "lat": -27.4826, "lon": 153.0053, "state": "QLD"},
    "HFM Isle of Capri":    {"postcode": "4217", "lat": -28.0189, "lon": 153.4238, "state": "QLD"},
    "HFM Clayfield":        {"postcode": "4011", "lat": -27.4177, "lon": 153.0575, "state": "QLD"},
    "HFM Lane Cove":        {"postcode": "2066", "lat": -33.8166, "lon": 151.1670, "state": "NSW"},
}


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_available():
    return os.path.exists(DB_PATH)


# ---------------------------------------------------------------------------
# Postcode coordinates
# ---------------------------------------------------------------------------

_postcode_coords = None

def get_postcode_coords():
    """Load postcode coordinate lookup (lazy singleton)."""
    global _postcode_coords
    if _postcode_coords is None:
        if os.path.exists(COORDS_PATH):
            with open(COORDS_PATH) as f:
                _postcode_coords = json.load(f)
        else:
            _postcode_coords = {}
    return _postcode_coords


def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def distance_tier(km):
    """Classify distance into trade area tier per CLAUDE.md Rule 5."""
    if km <= 3:
        return "Core (0-3km)"
    elif km <= 5:
        return "Primary (3-5km)"
    elif km <= 10:
        return "Secondary (5-10km)"
    elif km <= 20:
        return "Extended (10-20km)"
    else:
        return "No Presence (20km+)"


def nearest_store(postcode):
    """Find the nearest HFM store to a postcode. Returns (store_name, distance_km, tier)."""
    coords = get_postcode_coords()
    pc_coord = coords.get(str(postcode))
    if not pc_coord:
        return None, None, None

    best_dist = float('inf')
    best_store = None
    for store_name, store_info in STORE_LOCATIONS.items():
        d = haversine_km(pc_coord["lat"], pc_coord["lon"],
                         store_info["lat"], store_info["lon"])
        if d < best_dist:
            best_dist = d
            best_store = store_name

    return best_store, round(best_dist, 1), distance_tier(best_dist)


# ---------------------------------------------------------------------------
# Core queries
# ---------------------------------------------------------------------------

def get_periods():
    """All available periods sorted."""
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT period FROM market_share ORDER BY period").fetchall()
    conn.close()
    return [r["period"] for r in rows]


def get_regions():
    """All region names."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT DISTINCT region_code, region_name FROM market_share "
        "WHERE length(region_code) = 4 ORDER BY region_name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_period():
    conn = _get_conn()
    row = conn.execute("SELECT MAX(period) FROM market_share").fetchone()
    conn.close()
    return row[0]


def get_period_range():
    conn = _get_conn()
    row = conn.execute("SELECT MIN(period), MAX(period) FROM market_share").fetchone()
    conn.close()
    return row[0], row[1]


# ---------------------------------------------------------------------------
# Spatial data — postcodes with coordinates and nearest store
# ---------------------------------------------------------------------------

def postcode_map_data(period, channel="Total"):
    """Get all postcodes with coordinates, market share, and nearest store for mapping."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT region_code, region_name, market_share_pct,
               customer_penetration_pct, spend_per_customer,
               market_size_dollars, transactions_per_customer
        FROM market_share
        WHERE period = ? AND channel = ? AND length(region_code) = 4
        ORDER BY region_name
    """, (period, channel)).fetchall()
    conn.close()

    coords = get_postcode_coords()
    results = []
    for r in rows:
        pc = r["region_code"]
        pc_coord = coords.get(pc)
        if not pc_coord:
            continue

        store_name, dist_km, tier = nearest_store(pc)
        results.append({
            "postcode": pc,
            "region_name": r["region_name"],
            "lat": pc_coord["lat"],
            "lon": pc_coord["lon"],
            "market_share_pct": r["market_share_pct"] or 0,
            "penetration_pct": r["customer_penetration_pct"] or 0,
            "spend_per_customer": r["spend_per_customer"] or 0,
            "market_size": r["market_size_dollars"] or 0,
            "txn_per_customer": r["transactions_per_customer"] or 0,
            "nearest_store": store_name or "Unknown",
            "distance_km": dist_km or 999,
            "distance_tier": tier or "No Presence (20km+)",
        })
    return results


# ---------------------------------------------------------------------------
# Store trade area analysis
# ---------------------------------------------------------------------------

def store_trade_area(store_name, period, channel="Total"):
    """Get all postcodes within 20km of a store with their market share data."""
    store = STORE_LOCATIONS.get(store_name)
    if not store:
        return []

    coords = get_postcode_coords()
    nearby_postcodes = []
    for pc, coord in coords.items():
        d = haversine_km(store["lat"], store["lon"], coord["lat"], coord["lon"])
        if d <= 20:
            nearby_postcodes.append((pc, d))

    if not nearby_postcodes:
        return []

    conn = _get_conn()
    results = []
    for pc, dist in nearby_postcodes:
        row = conn.execute("""
            SELECT region_code, region_name, market_share_pct,
                   customer_penetration_pct, spend_per_customer,
                   market_size_dollars
            FROM market_share
            WHERE region_code = ? AND period = ? AND channel = ?
        """, (pc, period, channel)).fetchone()
        if row:
            results.append({
                "postcode": pc,
                "region_name": row["region_name"],
                "distance_km": round(dist, 1),
                "tier": distance_tier(dist),
                "market_share_pct": row["market_share_pct"] or 0,
                "penetration_pct": row["customer_penetration_pct"] or 0,
                "spend_per_customer": row["spend_per_customer"] or 0,
                "market_size": row["market_size_dollars"] or 0,
            })
    conn.close()
    return sorted(results, key=lambda x: x["distance_km"])


def store_trade_area_trend(store_name, channel="Total", tier_filter=None):
    """Monthly aggregate trend for a store's trade area."""
    store = STORE_LOCATIONS.get(store_name)
    if not store:
        return []

    coords = get_postcode_coords()
    nearby = []
    for pc, coord in coords.items():
        d = haversine_km(store["lat"], store["lon"], coord["lat"], coord["lon"])
        tier = distance_tier(d)
        if d <= 20:
            if tier_filter and tier != tier_filter:
                continue
            nearby.append(pc)

    if not nearby:
        return []

    conn = _get_conn()
    placeholders = ",".join("?" * len(nearby))
    rows = conn.execute(f"""
        SELECT period,
               AVG(market_share_pct) as avg_share,
               AVG(customer_penetration_pct) as avg_penetration,
               AVG(spend_per_customer) as avg_spend,
               SUM(market_size_dollars) as total_market,
               COUNT(*) as postcode_count
        FROM market_share
        WHERE region_code IN ({placeholders}) AND channel = ?
        GROUP BY period
        ORDER BY period
    """, nearby + [channel]).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# YoY trend & shift detection
# ---------------------------------------------------------------------------

def yoy_comparison(period_current, period_prior, channel="Total"):
    """Compare two periods — returns per-postcode share change."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT c.region_code, c.region_name,
               c.market_share_pct as current_share,
               p.market_share_pct as prior_share,
               c.market_share_pct - p.market_share_pct as share_change,
               c.customer_penetration_pct as current_penetration,
               p.customer_penetration_pct as prior_penetration,
               c.market_size_dollars as current_market,
               p.market_size_dollars as prior_market,
               c.spend_per_customer as current_spend,
               p.spend_per_customer as prior_spend
        FROM market_share c
        JOIN market_share p ON c.region_code = p.region_code
            AND p.channel = c.channel
        WHERE c.period = ? AND p.period = ? AND c.channel = ?
            AND length(c.region_code) = 4
        ORDER BY share_change ASC
    """, (period_current, period_prior, channel)).fetchall()
    conn.close()

    coords = get_postcode_coords()
    results = []
    for r in rows:
        pc = r["region_code"]
        store_name, dist_km, tier = nearest_store(pc)
        pc_coord = coords.get(pc, {})
        results.append({
            **dict(r),
            "lat": pc_coord.get("lat"),
            "lon": pc_coord.get("lon"),
            "nearest_store": store_name or "Unknown",
            "distance_km": dist_km or 999,
            "distance_tier": tier or "No Presence (20km+)",
        })
    return results


def detect_shifts(channel="Total", threshold_pp=2.0):
    """Find postcodes with significant month-on-month share changes across all periods."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT c.period as current_period, c.region_code, c.region_name,
               c.market_share_pct as current_share,
               p.market_share_pct as prior_share,
               c.market_share_pct - p.market_share_pct as shift
        FROM market_share c
        JOIN market_share p ON c.region_code = p.region_code
            AND p.channel = c.channel
        WHERE c.channel = ?
            AND length(c.region_code) = 4
            AND p.period = (
                SELECT MAX(m2.period) FROM market_share m2
                WHERE m2.period < c.period AND m2.region_code = c.region_code
                AND m2.channel = c.channel
            )
            AND ABS(c.market_share_pct - p.market_share_pct) >= ?
        ORDER BY ABS(c.market_share_pct - p.market_share_pct) DESC
    """, (channel, threshold_pp)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Issue flagging
# ---------------------------------------------------------------------------

def flag_issues(period, channel="Total"):
    """Identify postcodes with concerning metrics for the latest period."""
    # Get YoY data (same month prior year)
    period_str = str(period)
    prior_year = int(period_str[:4]) - 1
    prior_period = int(f"{prior_year}{period_str[4:]}")

    yoy = yoy_comparison(period, prior_period, channel)

    issues = []
    for r in yoy:
        flags = []
        share_change = r.get("share_change") or 0
        current_share = r.get("current_share") or 0
        tier = r.get("distance_tier", "")

        # Skip no-presence postcodes
        if "No Presence" in tier:
            continue

        # Significant share decline
        if share_change <= -2:
            flags.append(f"Share declined {share_change:+.1f}pp YoY")

        # Core/Primary with declining share — urgent
        if share_change <= -1 and ("Core" in tier or "Primary" in tier):
            flags.append(f"Trade area ({tier}) losing ground")

        # High share but declining penetration
        pen_change = (r.get("current_penetration") or 0) - (r.get("prior_penetration") or 0)
        if current_share > 5 and pen_change < -2:
            flags.append(f"Penetration fell {pen_change:+.1f}pp despite strong share")

        if flags:
            issues.append({
                "postcode": r["region_code"],
                "region_name": r["region_name"],
                "current_share": current_share,
                "share_change": share_change,
                "nearest_store": r.get("nearest_store", ""),
                "distance_km": r.get("distance_km", 999),
                "distance_tier": tier,
                "flags": flags,
                "severity": "Urgent" if any("Trade area" in f for f in flags) else "Warning",
            })

    return sorted(issues, key=lambda x: (0 if x["severity"] == "Urgent" else 1, x["share_change"]))


# ---------------------------------------------------------------------------
# Opportunity analysis
# ---------------------------------------------------------------------------

def opportunity_analysis(period, channel="Total"):
    """Identify opportunity and risk postcodes based on penetration vs share gaps."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT region_code, region_name, market_share_pct,
               customer_penetration_pct, spend_per_customer,
               market_size_dollars
        FROM market_share
        WHERE period = ? AND channel = ? AND length(region_code) = 4
            AND market_share_pct > 0
    """, (period, channel)).fetchall()
    conn.close()

    results = []
    for r in rows:
        store_name, dist_km, tier = nearest_store(r["region_code"])

        # Skip far-away postcodes
        if (dist_km or 999) > 20:
            continue

        share = r["market_share_pct"] or 0
        pen = r["customer_penetration_pct"] or 0
        spend = r["spend_per_customer"] or 0

        # Classify opportunity type
        if pen > 15 and share < 5:
            opp_type = "Growth Opportunity"
            opp_desc = "High penetration but low share — customers visit but spend elsewhere"
        elif pen < 5 and share > 10:
            opp_type = "Retention Risk"
            opp_desc = "High share from few customers — vulnerable if they churn"
        elif pen > 20 and spend < 100:
            opp_type = "Basket Opportunity"
            opp_desc = "Many customers but low spend — cross-sell/upsell potential"
        elif share > 10 and pen > 20:
            opp_type = "Stronghold"
            opp_desc = "High share and penetration — protect and grow"
        else:
            opp_type = "Monitor"
            opp_desc = ""

        results.append({
            "postcode": r["region_code"],
            "region_name": r["region_name"],
            "market_share_pct": share,
            "penetration_pct": pen,
            "spend_per_customer": spend,
            "market_size": r["market_size_dollars"] or 0,
            "nearest_store": store_name or "Unknown",
            "distance_km": dist_km or 999,
            "distance_tier": tier or "Unknown",
            "opportunity_type": opp_type,
            "opportunity_desc": opp_desc,
        })

    return results


# ---------------------------------------------------------------------------
# State summary
# ---------------------------------------------------------------------------

def state_summary(period, channel="Total"):
    """State-level aggregate performance."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT region_code as state, region_name, market_share_pct,
               customer_penetration_pct, spend_per_customer,
               market_size_dollars, transactions_per_customer
        FROM market_share
        WHERE period = ? AND channel = ?
            AND region_code IN ('NSW', 'QLD', 'ACT', 'AUS')
        ORDER BY region_code
    """, (period, channel)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def state_trend(channel="Total"):
    """Monthly state-level trends."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT period, region_code as state,
               market_share_pct as share,
               customer_penetration_pct as penetration,
               spend_per_customer as spend
        FROM market_share
        WHERE channel = ? AND region_code IN ('NSW', 'QLD', 'ACT')
        ORDER BY period, region_code
    """, (channel,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Store Health Scorecard
# ---------------------------------------------------------------------------

def store_health_scorecard(period, prior_period=None):
    """Compute a health scorecard for every store based on trade area metrics.

    Optimised: pre-computes all distances once, uses single DB connection,
    and batches queries by collecting all postcodes upfront.

    Returns one dict per store with:
    - core/primary share averages (Total channel)
    - instore/online core share
    - YoY share change
    - health grade (A-F) based on composite score
    """
    if prior_period is None:
        ps = str(period)
        prior_period = int(f"{int(ps[:4]) - 1}{ps[4:]}")

    coords = get_postcode_coords()

    # Step 1: Pre-compute all store → postcode distances
    store_postcodes = {}  # store_name → [(pc, dist, tier), ...]
    all_pcs = set()
    for store_name, store_info in STORE_LOCATIONS.items():
        nearby = []
        for pc, coord in coords.items():
            d = haversine_km(store_info["lat"], store_info["lon"],
                             coord["lat"], coord["lon"])
            if d <= 20:
                nearby.append((pc, d, distance_tier(d)))
                all_pcs.add(pc)
        store_postcodes[store_name] = nearby

    # Step 2: Bulk-fetch all market share data for relevant postcodes + periods
    conn = _get_conn()
    all_pcs_list = list(all_pcs)
    placeholders = ",".join("?" * len(all_pcs_list))

    # Fetch current and prior period data in two queries
    data = {}  # (pc, period, channel) → row dict
    for p in (period, prior_period):
        rows = conn.execute(f"""
            SELECT region_code, channel, market_share_pct,
                   customer_penetration_pct, spend_per_customer
            FROM market_share
            WHERE region_code IN ({placeholders})
              AND period = ?
        """, all_pcs_list + [p]).fetchall()
        for r in rows:
            data[(r["region_code"], p, r["channel"])] = dict(r)
    conn.close()

    # Step 3: Compute scorecard per store from pre-fetched data
    results = []
    for store_name, store_info in STORE_LOCATIONS.items():
        nearby = store_postcodes[store_name]
        if not nearby:
            continue

        record = {
            "store": store_name,
            "state": store_info["state"],
            "postcode": store_info["postcode"],
            "lat": store_info["lat"],
            "lon": store_info["lon"],
            "total_postcodes": len(nearby),
        }

        # Core+Primary postcodes (Total channel)
        cp_pcs = [pc for pc, _, t in nearby if t in ("Core (0-3km)", "Primary (3-5km)")]

        for tier_name, tier_label in [("Core (0-3km)", "core"), ("Primary (3-5km)", "primary")]:
            tier_pcs = [pc for pc, _, t in nearby if t == tier_name]
            shares = [data[(pc, period, "Total")]["market_share_pct"]
                      for pc in tier_pcs if (pc, period, "Total") in data
                      and data[(pc, period, "Total")]["market_share_pct"] is not None]
            record[f"total_{tier_label}_share"] = round(sum(shares) / len(shares), 2) if shares else None
            record[f"total_{tier_label}_count"] = len(tier_pcs)

        # Instore/Online core share
        core_pcs = [pc for pc, _, t in nearby if t == "Core (0-3km)"]
        for chan in ("Instore", "Online"):
            shares = [data[(pc, period, chan)]["market_share_pct"]
                      for pc in core_pcs if (pc, period, chan) in data
                      and data[(pc, period, chan)]["market_share_pct"] is not None]
            record[f"{chan.lower()}_core_share"] = round(sum(shares) / len(shares), 2) if shares else None

        # CP aggregate metrics
        if cp_pcs:
            cp_shares = [data[(pc, period, "Total")]["market_share_pct"]
                         for pc in cp_pcs if (pc, period, "Total") in data
                         and data[(pc, period, "Total")]["market_share_pct"] is not None]
            cp_pens = [data[(pc, period, "Total")]["customer_penetration_pct"]
                       for pc in cp_pcs if (pc, period, "Total") in data
                       and data[(pc, period, "Total")]["customer_penetration_pct"] is not None]
            cp_spends = [data[(pc, period, "Total")]["spend_per_customer"]
                         for pc in cp_pcs if (pc, period, "Total") in data
                         and data[(pc, period, "Total")]["spend_per_customer"] is not None]

            record["cp_share"] = round(sum(cp_shares) / len(cp_shares), 2) if cp_shares else 0
            record["cp_penetration"] = round(sum(cp_pens) / len(cp_pens), 2) if cp_pens else 0
            record["cp_spend"] = round(sum(cp_spends) / len(cp_spends), 2) if cp_spends else 0

            # Prior period
            prior_shares = [data[(pc, prior_period, "Total")]["market_share_pct"]
                            for pc in cp_pcs if (pc, prior_period, "Total") in data
                            and data[(pc, prior_period, "Total")]["market_share_pct"] is not None]
            prior_share = round(sum(prior_shares) / len(prior_shares), 2) if prior_shares else None
            record["cp_share_prior"] = prior_share
            record["cp_share_change"] = round(record["cp_share"] - prior_share, 2) if prior_share else None
        else:
            record["cp_share"] = 0
            record["cp_penetration"] = 0
            record["cp_spend"] = 0
            record["cp_share_prior"] = None
            record["cp_share_change"] = None

        # Health grade: composite of share level + trend + penetration
        score = 0
        s = record["cp_share"]
        if s >= 10:
            score += 40
        elif s >= 5:
            score += 30
        elif s >= 2:
            score += 20
        else:
            score += 10

        chg = record["cp_share_change"]
        if chg is not None:
            if chg >= 1:
                score += 30
            elif chg >= 0:
                score += 20
            elif chg >= -1:
                score += 10

        pen = record["cp_penetration"]
        if pen >= 20:
            score += 30
        elif pen >= 10:
            score += 20
        elif pen >= 5:
            score += 10

        if score >= 80:
            record["grade"] = "A"
        elif score >= 60:
            record["grade"] = "B"
        elif score >= 40:
            record["grade"] = "C"
        elif score >= 25:
            record["grade"] = "D"
        else:
            record["grade"] = "F"
        record["score"] = score

        results.append(record)

    return sorted(results, key=lambda x: x["score"], reverse=True)


def store_channel_comparison(store_name, period):
    """Compare Instore vs Online market share across a store's trade area."""
    store = STORE_LOCATIONS.get(store_name)
    if not store:
        return []

    coords = get_postcode_coords()
    nearby = []
    for pc, coord in coords.items():
        d = haversine_km(store["lat"], store["lon"], coord["lat"], coord["lon"])
        if d <= 10:  # Core + Primary + Secondary only
            nearby.append((pc, d, distance_tier(d)))

    if not nearby:
        return []

    conn = _get_conn()
    results = []
    for pc, dist, tier in nearby:
        rows = conn.execute("""
            SELECT channel, market_share_pct, customer_penetration_pct,
                   spend_per_customer, market_size_dollars
            FROM market_share
            WHERE region_code = ? AND period = ?
              AND channel IN ('Instore', 'Online')
        """, (pc, period)).fetchall()

        instore = next((dict(r) for r in rows if r["channel"] == "Instore"), None)
        online = next((dict(r) for r in rows if r["channel"] == "Online"), None)

        row = conn.execute("""
            SELECT region_name FROM market_share
            WHERE region_code = ? AND period = ? LIMIT 1
        """, (pc, period)).fetchone()
        region_name = row["region_name"] if row else pc

        results.append({
            "postcode": pc,
            "region_name": region_name,
            "distance_km": round(dist, 1),
            "tier": tier,
            "instore_share": round(instore["market_share_pct"], 2) if instore and instore["market_share_pct"] else 0,
            "online_share": round(online["market_share_pct"], 2) if online and online["market_share_pct"] else 0,
            "instore_pen": round(instore["customer_penetration_pct"], 2) if instore and instore["customer_penetration_pct"] else 0,
            "online_pen": round(online["customer_penetration_pct"], 2) if online and online["customer_penetration_pct"] else 0,
            "instore_spend": round(instore["spend_per_customer"], 2) if instore and instore["spend_per_customer"] else 0,
            "online_spend": round(online["spend_per_customer"], 2) if online and online["spend_per_customer"] else 0,
        })
    conn.close()
    return sorted(results, key=lambda x: x["distance_km"])


def network_macro_view(period, channel="Total"):
    """Aggregate stores into regional clusters for macro analysis.

    Clusters: Inner Sydney, Northern Beaches, North Shore, Eastern Suburbs,
    Inner West, Western Sydney, Central Coast, Hunter, Regional NSW, QLD.
    """
    CLUSTERS = {
        "Inner Sydney": ["HFM Broadway", "HFM Potts Point", "HFM Cammeray"],
        "Eastern Suburbs": ["HFM Bondi Junction", "HFM Bondi Beach", "HFM Bondi Westfield",
                            "HFM Rose Bay", "HFM Randwick"],
        "North Shore": ["HFM Willoughby", "HFM Lane Cove", "HFM Boronia Park",
                        "HFM Lindfield", "HFM St Ives"],
        "Northern Beaches": ["HFM Mosman", "HFM Manly", "HFM Dee Why", "HFM Mona Vale"],
        "Inner West": ["HFM Drummoyne", "HFM Leichhardt"],
        "Western Sydney": ["HFM Merrylands", "HFM Baulkham Hills", "HFM Pennant Hills", "HFM Penrith"],
        "Central Coast": ["HFM Erina"],
        "Hunter": ["HFM Newcastle", "HFM Glendale"],
        "Regional NSW": ["HFM Orange", "HFM Bowral", "HFM Albury"],
        "QLD": ["HFM West End", "HFM Isle of Capri", "HFM Clayfield"],
    }

    coords = get_postcode_coords()
    conn = _get_conn()
    results = []

    for cluster_name, store_list in CLUSTERS.items():
        # Collect all postcodes within 10km of any store in cluster
        cluster_pcs = set()
        store_count = 0
        for sn in store_list:
            store = STORE_LOCATIONS.get(sn)
            if not store:
                continue
            store_count += 1
            for pc, coord in coords.items():
                d = haversine_km(store["lat"], store["lon"], coord["lat"], coord["lon"])
                if d <= 10:
                    cluster_pcs.add(pc)

        if not cluster_pcs:
            continue

        pcs = list(cluster_pcs)
        placeholders = ",".join("?" * len(pcs))

        # Current period
        cur = conn.execute(f"""
            SELECT AVG(market_share_pct) as avg_share,
                   AVG(customer_penetration_pct) as avg_pen,
                   AVG(spend_per_customer) as avg_spend,
                   SUM(market_size_dollars) as total_market,
                   COUNT(*) as pc_count
            FROM market_share
            WHERE region_code IN ({placeholders})
              AND period = ? AND channel = ?
        """, pcs + [period, channel]).fetchone()

        # Prior year
        ps = str(period)
        prior_period = int(f"{int(ps[:4]) - 1}{ps[4:]}")
        pri = conn.execute(f"""
            SELECT AVG(market_share_pct) as avg_share
            FROM market_share
            WHERE region_code IN ({placeholders})
              AND period = ? AND channel = ?
        """, pcs + [prior_period, channel]).fetchone()

        prior_share = round(pri["avg_share"], 2) if pri and pri["avg_share"] else None

        results.append({
            "cluster": cluster_name,
            "stores": store_count,
            "postcodes": cur["pc_count"] if cur else 0,
            "avg_share": round(cur["avg_share"], 2) if cur and cur["avg_share"] else 0,
            "avg_penetration": round(cur["avg_pen"], 2) if cur and cur["avg_pen"] else 0,
            "avg_spend": round(cur["avg_spend"], 2) if cur and cur["avg_spend"] else 0,
            "total_market": cur["total_market"] or 0,
            "share_prior": prior_share,
            "share_change": round(cur["avg_share"] - prior_share, 2) if cur and cur["avg_share"] and prior_share else None,
        })

    conn.close()
    return sorted(results, key=lambda x: x["avg_share"], reverse=True)


def postcode_trend(postcode, channel="Total"):
    """Monthly trend for a single postcode."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT period, channel, market_share_pct, customer_penetration_pct,
               spend_per_customer, market_size_dollars, transactions_per_customer
        FROM market_share
        WHERE region_code = ? AND channel = ?
        ORDER BY period
    """, (postcode, channel)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
