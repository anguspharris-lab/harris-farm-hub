"""
Harris Farm Hub — Product Hierarchy Module
Loads the 72,911-product hierarchy from parquet and provides browsing,
search, and statistics functions.

Source: Product Hierarchy 20260215.xlsx → data/product_hierarchy.parquet
Hierarchy: Department (9) → Major Group (30) → Minor Group (405) →
           HFM Item (4,465) → Product/SKU (72,911)
"""

import logging
from functools import lru_cache
from pathlib import Path

import pandas as pd

logger = logging.getLogger("hub_api")

HIERARCHY_PARQUET = Path(__file__).parent.parent / "data" / "product_hierarchy.parquet"


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_hierarchy() -> pd.DataFrame:
    """Load product hierarchy parquet into a cached DataFrame.

    Returns DataFrame with 72,911 rows × 12 columns.
    ProductNumber is string-typed to match PLUItem_ID in transactions.
    Cached in memory (~15 MB) after first call.
    """
    if not HIERARCHY_PARQUET.exists():
        logger.warning("Product hierarchy not found: %s", HIERARCHY_PARQUET)
        return pd.DataFrame()

    df = pd.read_parquet(HIERARCHY_PARQUET)
    df["ProductNumber"] = df["ProductNumber"].astype(str).str.strip()
    return df


# ---------------------------------------------------------------------------
# HIERARCHY BROWSING
# ---------------------------------------------------------------------------

def get_departments() -> list[dict]:
    """Return departments that have at least one active product.

    Returns list of dicts with: code, name, total_products (active only),
    active_products, deleted_products.
    """
    df = load_hierarchy()
    if df.empty:
        return []

    active_df = df[df["ProductLifecycleStateId"] == "Active"]
    if active_df.empty:
        return []

    result = []
    for (code, name), group in active_df.groupby(["DepartmentCode", "DepartmentDesc"]):
        result.append({
            "code": str(code),
            "name": str(name),
            "total_products": len(group),
            "active_products": len(group),
            "deleted_products": 0,
            "new_inactive": 0,
            "derange": 0,
        })
    return sorted(result, key=lambda d: d["total_products"], reverse=True)


def get_major_groups(dept_code: str) -> list[dict]:
    """Return major groups within a department that have active products."""
    df = load_hierarchy()
    if df.empty:
        return []

    dept_df = df[
        (df["DepartmentCode"] == str(dept_code))
        & (df["ProductLifecycleStateId"] == "Active")
    ]
    if dept_df.empty:
        return []

    result = []
    for (code, name), group in dept_df.groupby(
        ["MajorGroupCode", "MajorGroupDesc"]
    ):
        result.append({
            "code": str(code),
            "name": str(name),
            "total_products": len(group),
            "active_products": len(group),
        })
    return sorted(result, key=lambda d: d["total_products"], reverse=True)


def get_minor_groups(dept_code: str, major_code: str) -> list[dict]:
    """Return minor groups within a major group that have active products."""
    df = load_hierarchy()
    if df.empty:
        return []

    filtered = df[
        (df["DepartmentCode"] == str(dept_code))
        & (df["MajorGroupCode"] == str(major_code))
        & (df["ProductLifecycleStateId"] == "Active")
    ]
    if filtered.empty:
        return []

    result = []
    for (code, name), group in filtered.groupby(
        ["MinorGroupCode", "MinorGroupDesc"]
    ):
        result.append({
            "code": str(code),
            "name": str(name),
            "total_products": len(group),
        })
    return sorted(result, key=lambda d: d["total_products"], reverse=True)


def get_hfm_items(dept_code, major_code, minor_code):
    """Return HFM Items within a minor group that have active products."""
    df = load_hierarchy()
    if df.empty:
        return []

    filtered = df[
        (df["DepartmentCode"] == str(dept_code))
        & (df["MajorGroupCode"] == str(major_code))
        & (df["MinorGroupCode"] == str(minor_code))
        & (df["ProductLifecycleStateId"] == "Active")
    ]
    if filtered.empty:
        return []

    result = []
    for (code, name), group in filtered.groupby(["HFMItem", "HFMItemDesc"]):
        result.append({
            "code": str(code),
            "name": str(name),
            "total_products": len(group),
        })
    return sorted(result, key=lambda d: d["name"])


def get_products_in_hfm_item(dept_code, major_code, minor_code, hfm_item_code):
    """Return active products/SKUs within an HFM item."""
    df = load_hierarchy()
    if df.empty:
        return []

    filtered = df[
        (df["DepartmentCode"] == str(dept_code))
        & (df["MajorGroupCode"] == str(major_code))
        & (df["MinorGroupCode"] == str(minor_code))
        & (df["HFMItem"] == str(hfm_item_code))
        & (df["ProductLifecycleStateId"] == "Active")
    ]
    if filtered.empty:
        return []

    result = []
    for _, row in filtered.iterrows():
        result.append({
            "product_number": str(row.ProductNumber),
            "product_name": str(row.ProductName),
            "lifecycle": str(row.ProductLifecycleStateId),
        })
    return sorted(result, key=lambda d: d["product_name"])


def get_products(
    dept_code: str = None,
    major_code: str = None,
    minor_code: str = None,
    lifecycle: str = None,
    limit: int = 100,
) -> list[dict]:
    """Return products with optional filters."""
    df = load_hierarchy()
    if df.empty:
        return []

    mask = pd.Series(True, index=df.index)
    if dept_code:
        mask &= df["DepartmentCode"] == str(dept_code)
    if major_code:
        mask &= df["MajorGroupCode"] == str(major_code)
    if minor_code:
        mask &= df["MinorGroupCode"] == str(minor_code)
    if lifecycle:
        mask &= df["ProductLifecycleStateId"] == lifecycle

    filtered = df[mask].head(limit)
    return filtered.to_dict("records")


def search_products(query: str, limit: int = 20) -> list[dict]:
    """Case-insensitive product name search.

    Returns list of dicts with ProductNumber, ProductName,
    DepartmentDesc, MajorGroupDesc, lifecycle.
    """
    df = load_hierarchy()
    if df.empty:
        return []

    mask = df["ProductName"].str.contains(query, case=False, na=False)
    matches = df[mask].head(limit)

    return [
        {
            "product_number": row.ProductNumber,
            "product_name": row.ProductName,
            "department": row.DepartmentDesc,
            "major_group": row.MajorGroupDesc,
            "minor_group": row.MinorGroupDesc,
            "lifecycle": row.ProductLifecycleStateId,
            "buyer_id": row.BuyerId,
        }
        for row in matches.itertuples()
    ]


def search_hierarchy(query, limit=50):
    """Search active products across PLU, name, and all hierarchy level names.

    Matches against: ProductNumber, ProductName, DepartmentDesc,
    MajorGroupDesc, MinorGroupDesc, HFMItemDesc.
    Only returns products with Active lifecycle status.

    Returns list of dicts with all hierarchy codes needed for filter dict.
    """
    df = load_hierarchy()
    if df.empty or len(query.strip()) < 2:
        return []

    df = df[df["ProductLifecycleStateId"] == "Active"]
    if df.empty:
        return []

    q = query.strip()

    # Exact PLU match first (highest priority)
    plu_mask = df["ProductNumber"] == q

    # Substring match across name and hierarchy levels
    text_mask = (
        df["ProductName"].str.contains(q, case=False, na=False)
        | df["DepartmentDesc"].str.contains(q, case=False, na=False)
        | df["MajorGroupDesc"].str.contains(q, case=False, na=False)
        | df["MinorGroupDesc"].str.contains(q, case=False, na=False)
        | df["HFMItemDesc"].str.contains(q, case=False, na=False)
    )

    # PLU prefix match (e.g., "123" matches "12345")
    plu_prefix_mask = df["ProductNumber"].str.startswith(q, na=False)

    # Combine: exact PLU first, then PLU prefix, then text matches
    combined = df[plu_mask | text_mask | plu_prefix_mask].copy()

    # Priority sort: exact PLU > PLU prefix > name match > hierarchy match
    combined["_priority"] = 3  # default: hierarchy match
    combined.loc[
        combined["ProductName"].str.contains(q, case=False, na=False),
        "_priority"] = 2
    combined.loc[
        combined["ProductNumber"].str.startswith(q, na=False),
        "_priority"] = 1
    combined.loc[combined["ProductNumber"] == q, "_priority"] = 0
    combined = combined.sort_values("_priority").head(limit)

    results = []
    for _, row in combined.iterrows():
        results.append({
            "product_number": str(row.ProductNumber),
            "product_name": str(row.ProductName),
            "dept_code": str(row.DepartmentCode),
            "dept_name": str(row.DepartmentDesc),
            "major_code": str(row.MajorGroupCode),
            "major_name": str(row.MajorGroupDesc),
            "minor_code": str(row.MinorGroupCode),
            "minor_name": str(row.MinorGroupDesc),
            "hfm_item_code": str(row.HFMItem),
            "hfm_item_name": str(row.HFMItemDesc),
            "lifecycle": str(row.ProductLifecycleStateId),
        })
    return results


def get_product_by_plu(plu_id: str):
    """Lookup a single product by ProductNumber.

    POS systems often append a check digit to weighed/priced items
    (e.g. PLU 502771 in transactions maps to 50277 in the hierarchy).
    If exact match fails, we progressively truncate the last digit(s)
    to find the parent product.

    Returns dict with full hierarchy info, or None if not found.
    """
    df = load_hierarchy()
    if df.empty:
        return None

    plu = str(plu_id).strip()

    # Try exact match first
    match = df[df["ProductNumber"] == plu]

    # Fallback: truncate trailing digits (check digit / price suffix)
    if match.empty and len(plu) >= 5:
        for trim in range(1, 3):  # try removing 1 then 2 digits
            truncated = plu[: len(plu) - trim]
            if len(truncated) < 4:
                break
            match = df[df["ProductNumber"] == truncated]
            if not match.empty:
                break

    if match.empty:
        return None

    row = match.iloc[0]
    return {
        "product_number": row.ProductNumber,
        "product_name": row.ProductName,
        "department": row.DepartmentDesc,
        "department_code": str(row.DepartmentCode),
        "major_group": row.MajorGroupDesc,
        "major_group_code": str(row.MajorGroupCode),
        "minor_group": row.MinorGroupDesc,
        "minor_group_code": str(row.MinorGroupCode),
        "hfm_item": row.HFMItemDesc,
        "buyer_id": row.BuyerId,
        "lifecycle": row.ProductLifecycleStateId,
    }


# ---------------------------------------------------------------------------
# STATISTICS
# ---------------------------------------------------------------------------

def hierarchy_stats() -> dict:
    """Return hierarchy coverage summary."""
    df = load_hierarchy()
    if df.empty:
        return {
            "available": False,
            "source": str(HIERARCHY_PARQUET),
            "message": "Product hierarchy parquet not found",
        }

    lifecycle = df["ProductLifecycleStateId"].value_counts().to_dict()
    null_counts = {
        col: int(df[col].isna().sum())
        for col in df.columns
        if df[col].isna().sum() > 0
    }

    return {
        "available": True,
        "source": str(HIERARCHY_PARQUET),
        "total_products": len(df),
        "departments": int(df["DepartmentDesc"].nunique()),
        "major_groups": int(df["MajorGroupDesc"].nunique()),
        "minor_groups": int(df["MinorGroupDesc"].nunique()),
        "hfm_items": int(df["HFMItemDesc"].nunique()),
        "lifecycle": {str(k): int(v) for k, v in lifecycle.items()},
        "null_counts": null_counts,
    }
