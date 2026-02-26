"""
MDHE (Master Data Health Engine) — 4-Layer Validation Engine

Validates PLU master data across 4 layers and computes health scores.
Pure Python — no Streamlit imports — usable from both backend API and dashboard pages.

Layers:
    1. Rules (35% weight)      — Deterministic checks
    2. Standards (30% weight)  — Business logic
    3. AI/Claude (20% weight)  — Anomaly detection (heuristic approximation)
    4. Reconciliation (15%)    — Cross-system scan verification

Author: Harris Farm Hub — AI Centre of Excellence
"""

import json
import re
from typing import Optional, List, Dict, Any, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LAYER_WEIGHTS = {
    "rules": 0.35,
    "standards": 0.30,
    "ai": 0.20,
    "recon": 0.15,
}

VALID_UOMS = {"ea", "kg", "g", "l", "ml", "bunch", "pack", "each"}

# Produce categories where weight-based UOM (kg/g) is expected
WEIGHT_CATEGORIES = {"fruit", "vegetables", "meat", "seafood"}
# Categories where each-based UOM (ea/each) is expected
EACH_CATEGORIES = {"bakery", "grocery", "deli"}

# Keyword -> expected category mapping for AI layer
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Meat": ["chicken", "beef", "lamb", "pork"],
    "Seafood": ["salmon", "fish", "prawn", "oyster"],
    "Bakery": ["bread", "loaf", "roll", "croissant"],
    "Fruit": ["apple", "banana", "orange", "avocado", "berry"],
    "Vegetables": ["potato", "carrot", "onion", "tomato", "lettuce"],
}

# Domain -> rule IDs mapping
DOMAIN_RULES: Dict[str, List[str]] = {
    "plu": ["RULES_001", "RULES_003", "RULES_004", "STD_002", "AI_003"],
    "barcode": ["RULES_002", "RULES_005", "RECON_001", "RECON_002", "RECON_003", "RECON_004"],
    "pricing": ["RULES_006", "RULES_007", "STD_005", "STD_006"],
    "hierarchy": ["RULES_008", "STD_003", "STD_004", "AI_001"],
    "supplier": [],  # Future — no rules yet, default 100%
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_validation(
    rule_id: str,
    layer: str,
    severity: str,
    field: str,
    record_key: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a single validation result dict."""
    return {
        "rule_id": rule_id,
        "layer": layer,
        "severity": severity,
        "field": field,
        "record_key": str(record_key),
        "message": message,
        "details": json.dumps(details) if details is not None else "{}",
    }


def validate_ean13(barcode: str) -> bool:
    """
    Validate EAN-13 barcode check digit using the standard algorithm.

    The check digit (13th digit) is calculated so that the weighted sum
    of all 13 digits (alternating weights 1 and 3) is a multiple of 10.

    Returns True if the barcode is a valid 13-digit EAN-13 with correct
    check digit, False otherwise.
    """
    if not barcode or len(barcode) != 13:
        return False
    if not barcode.isdigit():
        return False

    digits = [int(d) for d in barcode]
    # Weights alternate: 1, 3, 1, 3, ... for positions 0..11
    weighted_sum = sum(
        d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits[:12])
    )
    check = (10 - (weighted_sum % 10)) % 10
    return check == digits[12]


def _validate_upca(barcode: str) -> bool:
    """
    Validate UPC-A barcode (12 digits) using the standard check digit algorithm.

    Returns True if valid UPC-A, False otherwise.
    """
    if not barcode or len(barcode) != 12:
        return False
    if not barcode.isdigit():
        return False

    digits = [int(d) for d in barcode]
    # Odd positions (1-indexed) weight 3, even positions weight 1
    weighted_sum = sum(
        d * (3 if i % 2 == 0 else 1) for i, d in enumerate(digits[:11])
    )
    check = (10 - (weighted_sum % 10)) % 10
    return check == digits[11]


# Known internal barcode prefixes (common in Australian retail)
INTERNAL_PREFIXES = ("20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "02")


def _is_valid_barcode(barcode: str) -> bool:
    """Check if a barcode is valid EAN-13, UPC-A, or starts with an internal prefix."""
    if not barcode:
        return False
    barcode = barcode.strip()
    if validate_ean13(barcode):
        return True
    if _validate_upca(barcode):
        return True
    # Internal barcodes — accept if they start with a known prefix and are numeric
    if any(barcode.startswith(p) for p in INTERNAL_PREFIXES) and barcode.isdigit():
        return True
    return False


def _jaccard_similarity(words_a: List[str], words_b: List[str]) -> float:
    """Compute Jaccard similarity between two word lists."""
    set_a = set(words_a)
    set_b = set(words_b)
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _normalise_description(desc: str) -> str:
    """Lowercase, strip, remove 'organic' and other common modifiers."""
    text = desc.lower().strip()
    # Remove common modifiers
    for word in ("organic", "free range", "free-range", "premium", "local"):
        text = text.replace(word, "")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Layer 1: Rules — Deterministic checks (35% weight)
# ---------------------------------------------------------------------------

def run_rules_layer(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Layer 1: Deterministic rule checks.

    Rules:
        RULES_001: PLU code non-empty and alphanumeric
        RULES_002: Barcode valid (EAN-13 check digit, UPC-A, or internal prefix)
        RULES_003: Description non-empty
        RULES_004: No duplicate PLU codes
        RULES_005: No duplicate barcodes across different PLU codes
        RULES_006: Retail price > 0 for active items
        RULES_007: Cost price < Retail price (positive margin)
        RULES_008: Category non-empty
        RULES_009: UOM is one of the valid set

    Returns:
        List of validation dicts.
    """
    validations: List[Dict[str, Any]] = []

    # Pre-compute duplicate sets
    plu_seen: Dict[str, List[str]] = {}  # plu_code -> list of record keys
    barcode_seen: Dict[str, List[str]] = {}  # barcode -> list of plu_codes

    for rec in records:
        plu = str(rec.get("plu_code", "") or "").strip()
        barcode = str(rec.get("barcode", "") or "").strip()
        if plu:
            plu_seen.setdefault(plu, []).append(plu)
        if barcode:
            barcode_seen.setdefault(barcode, []).append(plu)

    duplicate_plus = {k for k, v in plu_seen.items() if len(v) > 1}
    duplicate_barcodes = {
        k for k, v in barcode_seen.items() if len(set(v)) > 1
    }

    for rec in records:
        plu = str(rec.get("plu_code", "") or "").strip()
        record_key = plu or str(rec.get("barcode", "unknown"))
        barcode = str(rec.get("barcode", "") or "").strip()
        description = str(rec.get("description", "") or "").strip()
        category = str(rec.get("category", "") or "").strip()
        uom = str(rec.get("unit_of_measure", "") or "").strip().lower()
        status = str(rec.get("status", "") or "").strip().lower()
        retail_price = rec.get("retail_price")
        cost_price = rec.get("cost_price")

        # RULES_001: PLU code non-empty and alphanumeric
        if not plu or not plu.replace("-", "").replace("_", "").isalnum():
            validations.append(_make_validation(
                rule_id="RULES_001",
                layer="rules",
                severity="critical",
                field="plu_code",
                record_key=record_key,
                message="PLU code is empty or not alphanumeric",
                details={"plu_code": plu, "field": "plu_code", "expected": "non-empty alphanumeric string"},
            ))

        # RULES_002: Barcode valid
        if barcode and not _is_valid_barcode(barcode):
            validations.append(_make_validation(
                rule_id="RULES_002",
                layer="rules",
                severity="high",
                field="barcode",
                record_key=record_key,
                message="Invalid barcode — failed EAN-13, UPC-A, and internal prefix checks",
                details={"plu_code": plu, "barcode": barcode, "field": "barcode"},
            ))

        # RULES_003: Description non-empty
        if not description:
            validations.append(_make_validation(
                rule_id="RULES_003",
                layer="rules",
                severity="critical",
                field="description",
                record_key=record_key,
                message="Missing description",
                details={"plu_code": plu, "field": "description", "expected": "non-empty string"},
            ))

        # RULES_004: Duplicate PLU code
        if plu in duplicate_plus:
            validations.append(_make_validation(
                rule_id="RULES_004",
                layer="rules",
                severity="critical",
                field="plu_code",
                record_key=record_key,
                message="Duplicate PLU code found",
                details={"plu_code": plu, "occurrences": plu_seen.get(plu, [])},
            ))

        # RULES_005: Duplicate barcode across different PLU codes
        if barcode and barcode in duplicate_barcodes:
            validations.append(_make_validation(
                rule_id="RULES_005",
                layer="rules",
                severity="critical",
                field="barcode",
                record_key=record_key,
                message="Duplicate barcode across different PLU codes",
                details={"plu_code": plu, "barcode": barcode, "other_plus": barcode_seen.get(barcode, [])},
            ))

        # RULES_006: Retail price > 0 for active items
        if status == "active":
            try:
                rp = float(retail_price) if retail_price is not None else 0.0
            except (ValueError, TypeError):
                rp = 0.0
            if rp <= 0:
                validations.append(_make_validation(
                    rule_id="RULES_006",
                    layer="rules",
                    severity="high",
                    field="retail_price",
                    record_key=record_key,
                    message="Retail price must be > 0 for active items",
                    details={"plu_code": plu, "retail_price": retail_price, "status": status},
                ))

        # RULES_007: Cost price < Retail price (positive margin)
        try:
            rp = float(retail_price) if retail_price is not None else None
            cp = float(cost_price) if cost_price is not None else None
        except (ValueError, TypeError):
            rp = None
            cp = None

        if rp is not None and cp is not None and rp > 0 and cp >= rp:
            validations.append(_make_validation(
                rule_id="RULES_007",
                layer="rules",
                severity="high",
                field="cost_price",
                record_key=record_key,
                message="Cost price >= retail price — negative or zero margin",
                details={"plu_code": plu, "cost_price": cost_price, "retail_price": retail_price},
            ))

        # RULES_008: Category non-empty
        if not category:
            validations.append(_make_validation(
                rule_id="RULES_008",
                layer="rules",
                severity="medium",
                field="category",
                record_key=record_key,
                message="Missing category",
                details={"plu_code": plu, "field": "category", "expected": "non-empty string"},
            ))

        # RULES_009: UOM is valid
        if uom and uom not in VALID_UOMS:
            validations.append(_make_validation(
                rule_id="RULES_009",
                layer="rules",
                severity="low",
                field="unit_of_measure",
                record_key=record_key,
                message="Invalid unit of measure",
                details={
                    "plu_code": plu,
                    "unit_of_measure": uom,
                    "valid_uoms": sorted(VALID_UOMS),
                },
            ))

    return validations


# ---------------------------------------------------------------------------
# Layer 2: Standards — Business logic (30% weight)
# ---------------------------------------------------------------------------

def run_standards_layer(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Layer 2: Business logic checks.

    Rules:
        STD_001: Description not ALL CAPS (>3 consecutive uppercase words)
        STD_002: Description minimum length >= 3 characters
        STD_003: Category/subcategory pair — if category present, subcategory should be too
        STD_004: UOM appropriate for category
        STD_005: Price within reasonable range ($0.10 - $500.00)
        STD_006: Margin between 5% and 80%
        STD_007: Pack size > 0 if provided

    Returns:
        List of validation dicts.
    """
    validations: List[Dict[str, Any]] = []

    for rec in records:
        plu = str(rec.get("plu_code", "") or "").strip()
        record_key = plu or str(rec.get("barcode", "unknown"))
        description = str(rec.get("description", "") or "").strip()
        category = str(rec.get("category", "") or "").strip()
        subcategory = str(rec.get("subcategory", "") or "").strip()
        uom = str(rec.get("unit_of_measure", "") or "").strip().lower()
        retail_price = rec.get("retail_price")
        cost_price = rec.get("cost_price")
        pack_size = rec.get("pack_size")

        # STD_001: Not ALL CAPS — flag if more than 3 consecutive uppercase words
        if description:
            words = description.split()
            consecutive_upper = 0
            max_consecutive_upper = 0
            for w in words:
                if w.isupper() and len(w) > 1:
                    consecutive_upper += 1
                    max_consecutive_upper = max(max_consecutive_upper, consecutive_upper)
                else:
                    consecutive_upper = 0
            if max_consecutive_upper > 3:
                validations.append(_make_validation(
                    rule_id="STD_001",
                    layer="standards",
                    severity="low",
                    field="description",
                    record_key=record_key,
                    message="Description appears to be ALL CAPS",
                    details={"plu_code": plu, "description": description},
                ))

        # STD_002: Description minimum length >= 3
        if description and len(description) < 3:
            validations.append(_make_validation(
                rule_id="STD_002",
                layer="standards",
                severity="medium",
                field="description",
                record_key=record_key,
                message="Description too short (minimum 3 characters)",
                details={"plu_code": plu, "description": description, "length": len(description)},
            ))

        # STD_003: Category/subcategory pair
        if category and not subcategory:
            validations.append(_make_validation(
                rule_id="STD_003",
                layer="standards",
                severity="medium",
                field="subcategory",
                record_key=record_key,
                message="Category present but subcategory is missing",
                details={"plu_code": plu, "category": category, "subcategory": subcategory},
            ))

        # STD_004: UOM appropriate for category
        if category and uom:
            cat_lower = category.lower()
            if cat_lower in WEIGHT_CATEGORIES and uom not in ("kg", "g", "ea", "each"):
                validations.append(_make_validation(
                    rule_id="STD_004",
                    layer="standards",
                    severity="medium",
                    field="unit_of_measure",
                    record_key=record_key,
                    message="UOM may not be appropriate for category — expected kg/g for produce",
                    details={
                        "plu_code": plu,
                        "category": category,
                        "unit_of_measure": uom,
                        "expected_uoms": ["kg", "g"],
                    },
                ))
            elif cat_lower in EACH_CATEGORIES and uom not in ("ea", "each", "pack", "bunch"):
                validations.append(_make_validation(
                    rule_id="STD_004",
                    layer="standards",
                    severity="medium",
                    field="unit_of_measure",
                    record_key=record_key,
                    message="UOM may not be appropriate for category — expected ea/each for this category",
                    details={
                        "plu_code": plu,
                        "category": category,
                        "unit_of_measure": uom,
                        "expected_uoms": ["ea", "each", "pack"],
                    },
                ))

        # STD_005: Price within reasonable range
        try:
            rp = float(retail_price) if retail_price is not None else None
        except (ValueError, TypeError):
            rp = None

        if rp is not None and rp > 0:
            if rp < 0.10 or rp > 500.00:
                validations.append(_make_validation(
                    rule_id="STD_005",
                    layer="standards",
                    severity="medium",
                    field="retail_price",
                    record_key=record_key,
                    message="Retail price outside reasonable range ($0.10 - $500.00)",
                    details={"plu_code": plu, "retail_price": rp, "range": [0.10, 500.00]},
                ))

        # STD_006: Margin between 5% and 80%
        try:
            rp = float(retail_price) if retail_price is not None else None
            cp = float(cost_price) if cost_price is not None else None
        except (ValueError, TypeError):
            rp = None
            cp = None

        if rp is not None and cp is not None and rp > 0:
            margin_pct = ((rp - cp) / rp) * 100.0
            if margin_pct < 5.0 or margin_pct > 80.0:
                validations.append(_make_validation(
                    rule_id="STD_006",
                    layer="standards",
                    severity="medium",
                    field="retail_price",
                    record_key=record_key,
                    message="Margin outside expected range (5% - 80%)",
                    details={
                        "plu_code": plu,
                        "margin_pct": round(margin_pct, 1),
                        "cost_price": cp,
                        "retail_price": rp,
                        "expected_range": [5.0, 80.0],
                    },
                ))

        # STD_007: Pack size > 0 if provided
        if pack_size is not None:
            try:
                ps = float(pack_size)
            except (ValueError, TypeError):
                ps = -1.0
            if ps <= 0:
                validations.append(_make_validation(
                    rule_id="STD_007",
                    layer="standards",
                    severity="medium",
                    field="pack_size",
                    record_key=record_key,
                    message="Pack size must be > 0",
                    details={"plu_code": plu, "pack_size": pack_size},
                ))

    return validations


# ---------------------------------------------------------------------------
# Layer 3: AI/Claude — Anomaly detection (20% weight)
# ---------------------------------------------------------------------------

def run_ai_layer(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Layer 3: AI-like heuristic checks (rule-based approximation).

    Rules:
        AI_001: Description doesn't match category (keyword matching)
        AI_002: Potential duplicate descriptions (fuzzy match)
        AI_003: Gibberish description (>50% digits/special chars)

    Returns:
        List of validation dicts.
    """
    validations: List[Dict[str, Any]] = []

    # --- AI_001: Description-category mismatch ---
    for rec in records:
        plu = str(rec.get("plu_code", "") or "").strip()
        record_key = plu or str(rec.get("barcode", "unknown"))
        description = str(rec.get("description", "") or "").strip()
        category = str(rec.get("category", "") or "").strip()

        if description and category:
            desc_lower = description.lower()
            for expected_cat, keywords in CATEGORY_KEYWORDS.items():
                for kw in keywords:
                    if kw in desc_lower and category.lower() != expected_cat.lower():
                        validations.append(_make_validation(
                            rule_id="AI_001",
                            layer="ai",
                            severity="high",
                            field="category",
                            record_key=record_key,
                            message="Description suggests category '%s' but assigned to '%s'" % (expected_cat, category),
                            details={
                                "plu_code": plu,
                                "description": description,
                                "current_category": category,
                                "suggested_category": expected_cat,
                                "matched_keyword": kw,
                            },
                        ))
                        break  # One match per expected_cat is enough
                else:
                    continue
                break  # Stop after first category mismatch found for this record

    # --- AI_002: Potential duplicate descriptions ---
    # Build normalised descriptions for comparison
    desc_index: List[Tuple[str, str, List[str]]] = []  # (record_key, normalised, words)
    for rec in records:
        plu = str(rec.get("plu_code", "") or "").strip()
        record_key = plu or str(rec.get("barcode", "unknown"))
        description = str(rec.get("description", "") or "").strip()
        if description:
            norm = _normalise_description(description)
            words = [w for w in norm.split() if w]
            desc_index.append((record_key, norm, words))

    # Pairwise comparison (O(n^2) — acceptable for PLU master data sets)
    flagged_pairs = set()  # type: set
    for i in range(len(desc_index)):
        key_a, norm_a, words_a = desc_index[i]
        for j in range(i + 1, len(desc_index)):
            key_b, norm_b, words_b = desc_index[j]
            if key_a == key_b:
                continue
            pair = tuple(sorted([key_a, key_b]))
            if pair in flagged_pairs:
                continue

            is_dup = False
            # Substring check
            if norm_a and norm_b:
                if norm_a in norm_b or norm_b in norm_a:
                    is_dup = True
                # Jaccard similarity on words
                elif words_a and words_b:
                    sim = _jaccard_similarity(words_a, words_b)
                    if sim > 0.6:
                        is_dup = True

            if is_dup:
                flagged_pairs.add(pair)
                validations.append(_make_validation(
                    rule_id="AI_002",
                    layer="ai",
                    severity="medium",
                    field="description",
                    record_key=key_a,
                    message="Potential duplicate of PLU %s" % key_b,
                    details={
                        "plu_a": key_a,
                        "plu_b": key_b,
                        "description_a": norm_a,
                        "description_b": norm_b,
                    },
                ))

    # --- AI_003: Gibberish description ---
    for rec in records:
        plu = str(rec.get("plu_code", "") or "").strip()
        record_key = plu or str(rec.get("barcode", "unknown"))
        description = str(rec.get("description", "") or "").strip()

        if description:
            total_chars = len(description)
            if total_chars > 0:
                non_alpha_count = sum(
                    1 for c in description if not c.isalpha() and not c.isspace()
                )
                ratio = non_alpha_count / total_chars
                if ratio > 0.5:
                    validations.append(_make_validation(
                        rule_id="AI_003",
                        layer="ai",
                        severity="high",
                        field="description",
                        record_key=record_key,
                        message="Description may be gibberish — over 50%% non-alpha characters",
                        details={
                            "plu_code": plu,
                            "description": description,
                            "non_alpha_ratio": round(ratio, 2),
                        },
                    ))

    return validations


# ---------------------------------------------------------------------------
# Layer 4: Cross-System Reconciliation (15% weight)
# ---------------------------------------------------------------------------

def run_recon_layer(
    records: List[Dict[str, Any]],
    scan_data: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Layer 4: Cross-system reconciliation against scan data.

    Rules:
        RECON_001: Barcode scanned in warehouse
        RECON_002: Barcode scanned at POS
        RECON_003: POS manual key rate < 10%
        RECON_004: Scan success rate > 80%

    Args:
        records: PLU record list.
        scan_data: Optional dict mapping barcode -> scan info dict.
                   If None, this layer is skipped entirely.

    Returns:
        List of validation dicts (empty if scan_data is None).
    """
    if scan_data is None:
        return []

    validations: List[Dict[str, Any]] = []

    for rec in records:
        plu = str(rec.get("plu_code", "") or "").strip()
        record_key = plu or str(rec.get("barcode", "unknown"))
        barcode = str(rec.get("barcode", "") or "").strip()

        if not barcode:
            continue

        scan_info = scan_data.get(barcode)

        # RECON_001: Barcode scanned in warehouse
        warehouse_scanned = False
        if scan_info is not None:
            source = str(scan_info.get("scan_source", "")).lower()
            if "warehouse" in source or source == "both":
                warehouse_scanned = True
        if not warehouse_scanned:
            validations.append(_make_validation(
                rule_id="RECON_001",
                layer="recon",
                severity="medium",
                field="barcode",
                record_key=record_key,
                message="Barcode never scanned in warehouse",
                details={"plu_code": plu, "barcode": barcode},
            ))

        # RECON_002: Barcode scanned at POS
        pos_scanned = False
        if scan_info is not None:
            source = str(scan_info.get("scan_source", "")).lower()
            if "pos" in source or source == "both":
                pos_scanned = True
        if not pos_scanned:
            validations.append(_make_validation(
                rule_id="RECON_002",
                layer="recon",
                severity="medium",
                field="barcode",
                record_key=record_key,
                message="Barcode never scanned at POS",
                details={"plu_code": plu, "barcode": barcode},
            ))

        # RECON_003: POS manual key rate < 10%
        if scan_info is not None:
            manual_rate = scan_info.get("manual_key_rate")
            if manual_rate is not None:
                try:
                    mr = float(manual_rate)
                except (ValueError, TypeError):
                    mr = 0.0
                if mr >= 10.0:
                    validations.append(_make_validation(
                        rule_id="RECON_003",
                        layer="recon",
                        severity="high",
                        field="barcode",
                        record_key=record_key,
                        message="POS manual key rate too high (%.1f%%) — barcode may be faulty" % mr,
                        details={
                            "plu_code": plu,
                            "barcode": barcode,
                            "manual_key_rate": mr,
                            "threshold": 10.0,
                        },
                    ))

        # RECON_004: Scan success rate > 80%
        if scan_info is not None:
            success_rate = scan_info.get("success_rate")
            if success_rate is not None:
                try:
                    sr = float(success_rate)
                except (ValueError, TypeError):
                    sr = 100.0
                if sr < 80.0:
                    validations.append(_make_validation(
                        rule_id="RECON_004",
                        layer="recon",
                        severity="high",
                        field="barcode",
                        record_key=record_key,
                        message="Scan success rate below 80%% (%.1f%%) — label quality issue" % sr,
                        details={
                            "plu_code": plu,
                            "barcode": barcode,
                            "success_rate": sr,
                            "threshold": 80.0,
                        },
                    ))

    return validations


# ---------------------------------------------------------------------------
# Score Calculation
# ---------------------------------------------------------------------------

def calculate_domain_scores(
    validations: List[Dict[str, Any]],
    total_records: int,
    has_scan_data: bool = False,
) -> Dict[str, Any]:
    """
    Calculate per-domain and overall scores from validation results.

    Domains: plu, barcode, pricing, hierarchy, supplier
    Each domain score = (total_records - unique_records_with_failures) / total_records * 100

    Layer scores within each domain follow the same formula but count only
    failures from that specific layer.

    Overall score = weighted average of layer scores:
        (rules * 0.35) + (standards * 0.30) + (ai * 0.20) + (recon * 0.15)

    If no scan data, recon is excluded and the remaining layers are re-weighted
    proportionally.

    Args:
        validations: Full list of validation dicts from all layers.
        total_records: Number of PLU records processed.
        has_scan_data: Whether scan_data was provided (affects recon scoring).

    Returns:
        Scores dict with per-domain and overall entries.
    """
    if total_records == 0:
        empty_domain = {
            "total": 0, "passed": 0, "failed": 0, "score": 100.0,
            "layer_scores": {"rules": 100.0, "standards": 100.0, "ai": 100.0, "recon": None},
        }
        return {
            "plu": dict(empty_domain),
            "barcode": dict(empty_domain),
            "pricing": dict(empty_domain),
            "hierarchy": dict(empty_domain),
            "supplier": {"total": 0, "passed": 0, "failed": 0, "score": 100.0, "layer_scores": {"rules": 100.0, "standards": 100.0, "ai": 100.0, "recon": None}},
            "overall": {"total": 0, "passed": 0, "failed": 0, "score": 100.0, "layer_scores": {"rules": 100.0, "standards": 100.0, "ai": 100.0, "recon": None}},
        }

    layers = ["rules", "standards", "ai", "recon"]

    # Build index: domain -> layer -> set of record_keys that failed
    domain_layer_failures: Dict[str, Dict[str, set]] = {}  # type: ignore
    for domain in DOMAIN_RULES:
        domain_layer_failures[domain] = {l: set() for l in layers}

    for v in validations:
        rule_id = v.get("rule_id", "")
        layer = v.get("layer", "")
        record_key = v.get("record_key", "")
        for domain, rule_ids in DOMAIN_RULES.items():
            if rule_id in rule_ids:
                domain_layer_failures[domain][layer].add(record_key)

    scores: Dict[str, Any] = {}

    for domain in DOMAIN_RULES:
        # All unique record_keys that failed in this domain (any layer)
        all_failed_keys = set()  # type: set
        for layer_set in domain_layer_failures[domain].values():
            all_failed_keys |= layer_set

        failed_count = len(all_failed_keys)
        passed_count = max(total_records - failed_count, 0)
        domain_score = (passed_count / total_records) * 100.0 if total_records > 0 else 100.0

        # Per-layer scores for this domain
        layer_scores: Dict[str, Optional[float]] = {}
        for layer in layers:
            if layer == "recon" and not has_scan_data:
                layer_scores[layer] = None
                continue
            lf = len(domain_layer_failures[domain][layer])
            ls = ((total_records - lf) / total_records) * 100.0 if total_records > 0 else 100.0
            layer_scores[layer] = round(ls, 1)

        # For supplier domain (no rules yet), default to 100%
        if domain == "supplier":
            domain_score = 100.0
            layer_scores = {l: (100.0 if l != "recon" or has_scan_data else None) for l in layers}

        scores[domain] = {
            "total": total_records,
            "passed": passed_count,
            "failed": failed_count,
            "score": round(domain_score, 1),
            "layer_scores": layer_scores,
        }

    # --- Overall score ---
    # Aggregate all failures across all domains by layer
    overall_layer_failures: Dict[str, set] = {l: set() for l in layers}  # type: ignore
    for domain in DOMAIN_RULES:
        for layer in layers:
            overall_layer_failures[layer] |= domain_layer_failures[domain][layer]

    overall_layer_scores: Dict[str, Optional[float]] = {}
    for layer in layers:
        if layer == "recon" and not has_scan_data:
            overall_layer_scores[layer] = None
            continue
        lf = len(overall_layer_failures[layer])
        ls = ((total_records - lf) / total_records) * 100.0 if total_records > 0 else 100.0
        overall_layer_scores[layer] = round(ls, 1)

    # Weighted average — exclude recon if no scan data and redistribute weight
    if has_scan_data:
        weights = dict(LAYER_WEIGHTS)
    else:
        # Redistribute recon weight proportionally across remaining layers
        remaining = {k: v for k, v in LAYER_WEIGHTS.items() if k != "recon"}
        total_remaining = sum(remaining.values())
        weights = {k: v / total_remaining for k, v in remaining.items()}

    weighted_score = 0.0
    for layer, weight in weights.items():
        ls_val = overall_layer_scores.get(layer)
        if ls_val is not None:
            weighted_score += ls_val * weight

    all_failed_overall = set()  # type: set
    for layer_set in overall_layer_failures.values():
        all_failed_overall |= layer_set
    overall_failed = len(all_failed_overall)
    overall_passed = max(total_records - overall_failed, 0)

    scores["overall"] = {
        "total": total_records,
        "passed": overall_passed,
        "failed": overall_failed,
        "score": round(weighted_score, 1),
        "layer_scores": overall_layer_scores,
    }

    return scores


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def validate_plu_data(
    records: List[Dict[str, Any]],
    scan_data: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Run full 4-layer validation on PLU records.

    Args:
        records: List of PLU record dicts. Each dict should have keys like
                 plu_code, barcode, description, category, subcategory,
                 unit_of_measure, pack_size, supplier_code, status,
                 retail_price, cost_price.
        scan_data: Optional dict mapping barcode string -> scan info dict.
                   If provided, Layer 4 (recon) will run.

    Returns:
        dict with two keys:
            'validations': list of validation result dicts
            'scores': dict with per-domain and overall scores
    """
    # Run each layer
    rules_results = run_rules_layer(records)
    standards_results = run_standards_layer(records)
    ai_results = run_ai_layer(records)
    recon_results = run_recon_layer(records, scan_data)

    # Combine all validations
    all_validations = rules_results + standards_results + ai_results + recon_results

    # Calculate scores
    has_scan_data = scan_data is not None
    scores = calculate_domain_scores(all_validations, len(records), has_scan_data)

    return {
        "validations": all_validations,
        "scores": scores,
    }
