"""
Harris Farm Hub — Product Hierarchy Converter
One-time script to convert Product Hierarchy Excel to Parquet for DuckDB.

Usage:
    python3 scripts/convert_hierarchy.py

Source: Product Hierarchy 20260215.xlsx (72,911 products, 12 columns)
Output: data/product_hierarchy.parquet
"""

import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

EXCEL_PATH = (
    Path.home() / "Desktop" / "Working files"
    / "Product Hierarchy 20260215.xlsx"
)

OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_PATH = OUTPUT_DIR / "product_hierarchy.parquet"

REQUIRED_COLUMNS = [
    "ProductNumber", "ProductName", "DepartmentDesc", "MajorGroupDesc",
    "MinorGroupDesc", "HFMItemDesc", "BuyerId", "ProductLifecycleStateId",
    "DepartmentCode", "MajorGroupCode", "MinorGroupCode", "HFMItem",
]


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def validate(df: pd.DataFrame) -> list[str]:
    """Validate hierarchy DataFrame. Returns list of errors (empty = OK)."""
    errors = []

    # Column check
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        errors.append(f"Missing columns: {missing}")

    # Row count sanity
    if len(df) < 50_000:
        errors.append(f"Only {len(df):,} rows — expected ~72,911")

    # Duplicate ProductNumber
    dupes = df["ProductNumber"].duplicated().sum()
    if dupes > 0:
        errors.append(f"{dupes} duplicate ProductNumber values")

    # Null ProductNumber
    null_pn = df["ProductNumber"].isna().sum()
    if null_pn > 0:
        errors.append(f"{null_pn} null ProductNumber values")

    # Department count
    dept_count = df["DepartmentDesc"].nunique()
    if dept_count < 5:
        errors.append(f"Only {dept_count} departments — expected ~9")

    return errors


# ---------------------------------------------------------------------------
# CONVERSION
# ---------------------------------------------------------------------------

def convert():
    """Read Excel, validate, write Parquet."""
    print(f"Reading: {EXCEL_PATH}")
    if not EXCEL_PATH.exists():
        print(f"ERROR: File not found: {EXCEL_PATH}")
        sys.exit(1)

    df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    print(f"  Rows: {len(df):,}")
    print(f"  Columns: {list(df.columns)}")

    # Validate
    errors = validate(df)
    if errors:
        print("\nVALIDATION ERRORS:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    # Cast ProductNumber to string (must match PLUItem_ID VARCHAR in transactions)
    df["ProductNumber"] = df["ProductNumber"].astype(str).str.strip()

    # Cast code columns to clean strings (remove .0 suffix from floats)
    for col in ["DepartmentCode", "MajorGroupCode", "MinorGroupCode", "HFMItem"]:
        def clean_code(val):
            if pd.isna(val):
                return ""
            s = str(val).strip()
            # Remove .0 suffix from float-converted integers
            if s.endswith(".0"):
                s = s[:-2]
            return s
        df[col] = df[col].apply(clean_code)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write parquet
    df.to_parquet(OUTPUT_PATH, index=False, compression="snappy")
    print(f"\nWritten: {OUTPUT_PATH}")
    print(f"  Size: {OUTPUT_PATH.stat().st_size / 1024 / 1024:.1f} MB")

    # Summary stats
    print(f"\n--- Summary ---")
    print(f"Total products: {len(df):,}")

    print(f"\nBy Lifecycle:")
    for state, count in df["ProductLifecycleStateId"].value_counts().items():
        print(f"  {state}: {count:,}")

    print(f"\nBy Department ({df['DepartmentDesc'].nunique()}):")
    for dept, count in df["DepartmentDesc"].value_counts().items():
        print(f"  {dept}: {count:,}")

    print(f"\nHierarchy levels:")
    print(f"  Departments: {df['DepartmentDesc'].nunique()}")
    print(f"  Major Groups: {df['MajorGroupDesc'].nunique()}")
    print(f"  Minor Groups: {df['MinorGroupDesc'].nunique()}")
    print(f"  HFM Items: {df['HFMItemDesc'].nunique()}")

    null_counts = df.isnull().sum()
    non_zero = null_counts[null_counts > 0]
    if len(non_zero) > 0:
        print(f"\nNull values:")
        for col, count in non_zero.items():
            print(f"  {col}: {count}")
    else:
        print(f"\nNull values: none")

    print(f"\nDone. Product hierarchy ready for DuckDB integration.")


if __name__ == "__main__":
    convert()
