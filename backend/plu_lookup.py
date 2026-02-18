"""
Harris Farm Hub — PLU Name Resolver
Maps PLUItem_ID codes to product names using the full product hierarchy
(72,911 products). Falls back to data/product_lines.csv (491 F&V items)
if hierarchy parquet is not available.
"""

import csv
from functools import lru_cache
from pathlib import Path

HIERARCHY_PARQUET = Path(__file__).parent.parent / "data" / "product_hierarchy.parquet"
PLU_CSV = Path(__file__).parent.parent / "data" / "product_lines.csv"


@lru_cache(maxsize=1)
def load_plu_names() -> dict:
    """Load PLU name mapping.

    Primary: data/product_hierarchy.parquet (72,911 products).
    Fallback: data/product_lines.csv (491 F&V items).
    Returns dict mapping ProductNumber/item_family_code -> name.
    """
    # Try full hierarchy first
    if HIERARCHY_PARQUET.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(
                HIERARCHY_PARQUET,
                columns=["ProductNumber", "ProductName"],
            )
            return {
                str(row.ProductNumber).strip(): str(row.ProductName)
                for row in df.itertuples()
                if pd.notna(row.ProductName)
            }
        except Exception:
            pass  # Fall through to CSV fallback

    # Fallback: 491 F&V items
    mapping = {}
    if not PLU_CSV.exists():
        return mapping
    with open(PLU_CSV, newline="") as f:
        for row in csv.DictReader(f):
            code = row.get("item_family_code", "").strip()
            name = row.get("item_family_name", "").strip()
            if code and name:
                mapping[code] = name
    return mapping


@lru_cache(maxsize=1)
def load_plu_details() -> dict:
    """Load full hierarchy details per PLU.

    Returns dict mapping ProductNumber -> {
        product_name, department, department_code, major_group,
        minor_group, hfm_item, buyer_id, lifecycle
    }.
    Returns empty dict if hierarchy parquet not available.
    """
    if not HIERARCHY_PARQUET.exists():
        return {}
    try:
        import pandas as pd
        df = pd.read_parquet(HIERARCHY_PARQUET)
        details = {}
        for row in df.itertuples():
            details[str(row.ProductNumber).strip()] = {
                "product_name": str(row.ProductName) if pd.notna(row.ProductName) else "",
                "department": str(row.DepartmentDesc) if pd.notna(row.DepartmentDesc) else "",
                "department_code": str(row.DepartmentCode),
                "major_group": str(row.MajorGroupDesc) if pd.notna(row.MajorGroupDesc) else "",
                "minor_group": str(row.MinorGroupDesc) if pd.notna(row.MinorGroupDesc) else "",
                "hfm_item": str(row.HFMItemDesc) if pd.notna(row.HFMItemDesc) else "",
                "buyer_id": str(row.BuyerId) if pd.notna(row.BuyerId) else "",
                "lifecycle": str(row.ProductLifecycleStateId) if pd.notna(row.ProductLifecycleStateId) else "",
            }
        return details
    except Exception:
        return {}


def resolve_plu(plu_id: str) -> str:
    """Return product name if known, else 'PLU {id}'.

    >>> resolve_plu("105")
    'Beans French'
    >>> resolve_plu("99999")
    'PLU 99999'
    """
    names = load_plu_names()
    return names.get(str(plu_id).strip(), f"PLU {plu_id}")


def enrich_items(items: list, plu_key: str = "plu_item_id",
                 include_hierarchy: bool = False) -> list:
    """Add 'product_name' field to each item dict.

    Args:
        items: list of dicts, each containing a PLU ID field
        plu_key: key name for the PLU ID in each dict
        include_hierarchy: if True, also adds department, major_group,
                          minor_group fields from hierarchy

    Returns:
        Same list with 'product_name' (and optionally hierarchy fields) added.
    """
    names = load_plu_names()
    details = load_plu_details() if include_hierarchy else {}
    for item in items:
        pid = str(item.get(plu_key, "")).strip()
        item["product_name"] = names.get(pid, f"PLU {pid}")
        if include_hierarchy and pid in details:
            item["department"] = details[pid]["department"]
            item["major_group"] = details[pid]["major_group"]
            item["minor_group"] = details[pid]["minor_group"]
    return items


def plu_coverage_stats() -> dict:
    """Return stats about PLU name coverage."""
    names = load_plu_names()
    using_hierarchy = HIERARCHY_PARQUET.exists()
    source = "data/product_hierarchy.parquet" if using_hierarchy else "data/product_lines.csv"
    note = (
        f"Full product hierarchy ({len(names):,} products)."
        if using_hierarchy
        else "F&V items only (~491). Other PLUs shown as codes."
    )
    return {
        "known_plus": len(names),
        "source": source,
        "coverage_note": note,
    }
