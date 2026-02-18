"""
Harris Farm Hub -- Agent Task Router
Maps natural-language analysis requests to analysis types via keyword matching.
No LLM required -- deterministic, fast, no API key needed.
"""

import re


# ---------------------------------------------------------------------------
# KEYWORD MAP — analysis_type -> keywords + weight
# ---------------------------------------------------------------------------

KEYWORD_MAP = {
    "basket_analysis": {
        "keywords": [
            "basket", "cross.?sell", "bought together", "co.?purchase",
            "pair", "bundle", "associate", "affinity",
            "frequently purchased", "complementary",
        ],
        "weight": 1.0,
    },
    "stockout_detection": {
        "keywords": [
            "stockout", "out of stock", "empty shelf", "zero.?sale day",
            "lost sale", "availability", "replenish",
        ],
        "weight": 1.0,
    },
    "intraday_stockout": {
        "keywords": [
            "intra.?day", "hourly", "mid.?day", "during the day",
            "stop selling", "run out", "gap hour", "suddenly",
            "penetration", "abnormal", "deviat",
        ],
        "weight": 1.2,
    },
    "price_dispersion": {
        "keywords": [
            "price", "pricing", "dispersion", "variation",
            "inconsisten", "markup", "discount",
        ],
        "weight": 1.0,
    },
    "demand_pattern": {
        "keywords": [
            "demand", "pattern", "peak", "trough", "seasonal",
            "day of week", "hourly trend", "traffic", "footfall",
            "when do", "busiest",
        ],
        "weight": 1.0,
    },
    "slow_movers": {
        "keywords": [
            "slow.?mov", "underperform", "range review", "delist",
            "low.?sell", "dead stock", "shelf space", "tail",
            "bottom performer",
        ],
        "weight": 1.0,
    },
    "halo_effect": {
        "keywords": [
            "halo", "basket grow", "basket size", "basket value",
            "basket lift", "drive basket", "basket builder",
            "basket uplift", "incremental spend",
        ],
        "weight": 1.0,
    },
    "specials_uplift": {
        "keywords": [
            "special", "price drop", "uplift", "forecast demand",
            "promo", "promotional", "how much to order",
            "order quantity", "on special",
        ],
        "weight": 1.0,
    },
    "margin_analysis": {
        "keywords": [
            "margin", "wastage", "gp%", "gross profit", "erosion",
            "cost of goods", "cogs", "shrink", "markdown",
            "profit", "margin erosi",
        ],
        "weight": 1.0,
    },
    "customer_analysis": {
        "keywords": [
            "customer", "segment", "rfm", "loyalty", "retention",
            "churn", "lapsed", "champion", "big spender",
            "at risk", "recency", "frequency",
        ],
        "weight": 1.0,
    },
    "store_benchmark": {
        "keywords": [
            "benchmark", "store compar", "store rank", "league table",
            "kpi", "percentile", "best store", "worst store",
            "all stores", "network", "performance rank",
        ],
        "weight": 1.0,
    },
}


# ---------------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------------

def route_query(user_query):
    """Route a natural-language query to analysis type(s).

    Args:
        user_query: Free-text description of the analysis task.

    Returns:
        dict with keys:
            matched_analyses: list of str (analysis_type keys)
            confidence: float 0.0-1.0
            reasoning: str explaining the match
    """
    if not user_query or not user_query.strip():
        return {
            "matched_analyses": list(KEYWORD_MAP.keys()),
            "confidence": 0.1,
            "reasoning": "Empty query -- defaulting to all analysis types.",
        }

    query_lower = user_query.lower()
    matches = []

    for analysis_type, config in KEYWORD_MAP.items():
        score = 0.0
        matched_keywords = []
        for kw in config["keywords"]:
            if re.search(kw, query_lower):
                score += config["weight"]
                matched_keywords.append(kw)
        if score > 0:
            matches.append({
                "type": analysis_type,
                "score": score,
                "keywords": matched_keywords,
            })

    if not matches:
        return {
            "matched_analyses": list(KEYWORD_MAP.keys()),
            "confidence": 0.2,
            "reasoning": "No keywords matched -- running all analysis types.",
        }

    # Sort by score descending
    matches.sort(key=lambda m: m["score"], reverse=True)

    # Take all matches above threshold (>= 50% of top score)
    top_score = matches[0]["score"]
    threshold = top_score * 0.5
    selected = [m for m in matches if m["score"] >= threshold]

    # Confidence based on top score vs max possible
    max_possible = max(
        len(c["keywords"]) * c["weight"] for c in KEYWORD_MAP.values()
    )
    confidence = min(top_score / max_possible, 1.0)
    if len(selected) == 1:
        confidence = min(confidence + 0.2, 1.0)

    reasoning_parts = []
    for m in selected:
        reasoning_parts.append("{}: matched [{}]".format(
            m["type"], ", ".join(m["keywords"][:3])))

    return {
        "matched_analyses": [m["type"] for m in selected],
        "confidence": round(confidence, 2),
        "reasoning": "; ".join(reasoning_parts),
    }
