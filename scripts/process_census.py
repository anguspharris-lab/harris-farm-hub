"""
ABS Census 2021 — SA1 Demographic Processing Pipeline
Parses G-series DataPack CSVs for NSW, QLD, ACT.
Builds SA1→Postcode concordance. Outputs parquet files.

Tables used:
  G01  — Total population, age
  G02  — Medians (income, rent, mortgage, household size)
  G33  — Household income distribution
  G43  — Labour force, qualifications
  G60A — Occupation by category
  G62  — Method of travel to work (WFH)
  SEIFA — IRSAD decile per SA1
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

BASE = Path(__file__).resolve().parent.parent / "data" / "census"
RAW = BASE / "raw"
OUT = BASE / "processed"
OUT.mkdir(parents=True, exist_ok=True)

STATES = {
    "NSW": BASE / "2021_NSW" / "2021 Census GCP Statistical Area 1 for NSW",
    "QLD": BASE / "2021_QLD" / "2021 Census GCP Statistical Area 1 for QLD",
    "ACT": BASE / "2021_ACT" / "2021 Census GCP Statistical Area 1 for ACT",
}

# Column abbreviation varies slightly between states — state suffix changes
STATE_SUFFIX = {"NSW": "NSW", "QLD": "QLD", "ACT": "ACT"}


def _csv(state_dir, table, state_code):
    """Resolve a Census CSV path. E.g. 2021Census_G01_NSW_SA1.csv"""
    return state_dir / f"2021Census_{table}_{state_code}_SA1.csv"


def load_g01(state_dir, sc):
    """G01 — Total persons, age bands."""
    df = pd.read_csv(_csv(state_dir, "G01", sc), low_memory=False)
    return df[["SA1_CODE_2021", "Tot_P_P"]].rename(
        columns={"Tot_P_P": "total_population"}
    )


def load_g02(state_dir, sc):
    """G02 — Medians and averages."""
    df = pd.read_csv(_csv(state_dir, "G02", sc), low_memory=False)
    return df.rename(columns={
        "Median_age_persons": "median_age",
        "Median_mortgage_repay_monthly": "median_mortgage_monthly",
        "Median_tot_prsnl_inc_weekly": "median_personal_income_weekly",
        "Median_rent_weekly": "median_rent_weekly",
        "Median_tot_fam_inc_weekly": "median_family_income_weekly",
        "Median_tot_hhd_inc_weekly": "median_hh_income_weekly",
        "Average_household_size": "avg_household_size",
    })


def load_g33(state_dir, sc):
    """G33 — Household income distribution. Derive pct_high_income_hh (>$2500/wk = $130K+/yr)."""
    df = pd.read_csv(_csv(state_dir, "G33", sc), low_memory=False)
    # High income bands: $2,500-$2,999, $3,000-$3,499, $3,500-$3,999, $4,000+
    high_cols = [c for c in df.columns if any(
        x in c for x in ["HI_2500_2999", "HI_3000_3499", "HI_3500_3999", "HI_4000_more"]
    ) and c.endswith("_Tot")]
    total_col = [c for c in df.columns if c.startswith("Tot_") and c.endswith("_Tot")
                 or c == "Total_Total"]
    # Find the total households column
    all_tot_cols = [c for c in df.columns if "Tot" in c and "HI_" not in c
                    and "Neg" not in c and c != "SA1_CODE_2021"]
    # The last total column should be the grand total
    # ABS naming: Partial_income_stated_Tot, All_incomes_not_stated_Tot, Tot_Tot
    tot_col_name = None
    for c in df.columns:
        if c in ("Tot_Tot", "Total_Total"):
            tot_col_name = c
            break
    if tot_col_name is None:
        # Try finding it
        for c in df.columns:
            if c.endswith("_Tot") and c.startswith("Tot"):
                tot_col_name = c
                break
    if tot_col_name is None:
        tot_col_name = df.columns[-1]  # fallback

    result = df[["SA1_CODE_2021"]].copy()
    result["hh_high_income"] = df[high_cols].sum(axis=1) if high_cols else 0
    result["hh_total"] = df[tot_col_name]
    result["pct_high_income_hh"] = np.where(
        result["hh_total"] > 0,
        result["hh_high_income"] / result["hh_total"] * 100,
        np.nan
    )
    return result[["SA1_CODE_2021", "pct_high_income_hh", "hh_total"]]


def load_g43(state_dir, sc):
    """G43 — Labour force status + qualifications."""
    df = pd.read_csv(_csv(state_dir, "G43", sc), low_memory=False)
    result = df[["SA1_CODE_2021"]].copy()

    # Population 15+
    result["pop_15_plus"] = df["P_15_yrs_over_P"]

    # Labour force participation
    result["labour_force_participation_pct"] = df["Percnt_LabForc_prticipation_P"]
    result["unemployment_pct"] = df["Percent_Unem_loyment_P"]

    # Qualifications — degree holders (PostGrad + GradDip/GradCert + Bachelor)
    result["n_postgrad"] = df["non_sch_qual_PostGrad_Dgre_P"]
    result["n_grad_dip"] = df["non_sch_qual_Gr_Dip_Gr_Crt_P"]
    result["n_bachelor"] = df["non_sch_qual_Bchelr_Degree_P"]
    result["n_degree_total"] = result["n_postgrad"] + result["n_grad_dip"] + result["n_bachelor"]
    result["pct_degree"] = np.where(
        result["pop_15_plus"] > 0,
        result["n_degree_total"] / result["pop_15_plus"] * 100,
        np.nan
    )
    return result[["SA1_CODE_2021", "pop_15_plus", "labour_force_participation_pct",
                    "unemployment_pct", "pct_degree", "n_degree_total"]]


def load_g60b(state_dir, sc):
    """G60B — Occupation by category (Person totals). Derive pct_professional (Managers + Professionals).
    G60A has M/F breakdown; G60B has P (person) totals with columns:
      P_Tot_Managers, P_Tot_Professionals, P_Tot_Tot etc."""
    df = pd.read_csv(_csv(state_dir, "G60B", sc), low_memory=False)
    result = df[["SA1_CODE_2021"]].copy()
    result["n_managers"] = df["P_Tot_Managers"]
    result["n_professionals"] = df["P_Tot_Professionals"]
    result["n_total_employed_occ"] = df["P_Tot_Tot"]
    result["n_prof_managerial"] = result["n_managers"] + result["n_professionals"]
    result["pct_professional"] = np.where(
        result["n_total_employed_occ"] > 0,
        result["n_prof_managerial"] / result["n_total_employed_occ"] * 100,
        np.nan
    )
    return result[["SA1_CODE_2021", "n_prof_managerial", "n_total_employed_occ", "pct_professional"]]


def load_g62(state_dir, sc):
    """G62 — Method of travel to work. Derive pct_wfh."""
    df = pd.read_csv(_csv(state_dir, "G62", sc), low_memory=False)
    result = df[["SA1_CODE_2021"]].copy()
    result["n_wfh"] = df["Worked_home_P"]
    result["n_travel_total"] = df["Tot_P"]
    result["pct_wfh"] = np.where(
        result["n_travel_total"] > 0,
        result["n_wfh"] / result["n_travel_total"] * 100,
        np.nan
    )
    return result[["SA1_CODE_2021", "pct_wfh", "n_wfh"]]


def load_seifa():
    """Load SEIFA 2021 IRSAD deciles per SA1."""
    path = RAW / "seifa_2021_sa1.xlsx"
    if not path.exists():
        print("  SEIFA file not found, skipping")
        return pd.DataFrame(columns=["SA1_CODE_2021", "seifa_irsad_score", "seifa_irsad_decile"])
    # Try different sheet names
    try:
        df = pd.read_excel(path, sheet_name="Table 1", header=5, engine="openpyxl")
    except Exception:
        try:
            df = pd.read_excel(path, sheet_name=0, header=5, engine="openpyxl")
        except Exception:
            df = pd.read_excel(path, sheet_name=0, header=4, engine="openpyxl")

    # Find SA1 code column and IRSAD columns
    cols = df.columns.tolist()
    sa1_col = None
    score_col = None
    decile_col = None
    for c in cols:
        cl = str(c).lower()
        if "sa1" in cl and ("code" in cl or "2021" in cl):
            sa1_col = c
        if "score" in cl and "irsad" in cl.replace(" ", ""):
            score_col = c
        if "decile" in cl:
            decile_col = c

    if sa1_col is None:
        # Try first column
        sa1_col = cols[0]
    if score_col is None:
        # Try second column
        for c in cols[1:]:
            if "score" in str(c).lower():
                score_col = c
                break
    if decile_col is None:
        for c in cols:
            if "decile" in str(c).lower():
                decile_col = c
                break

    result = pd.DataFrame()
    result["SA1_CODE_2021"] = df[sa1_col]
    if score_col:
        result["seifa_irsad_score"] = pd.to_numeric(df[score_col], errors="coerce")
    else:
        result["seifa_irsad_score"] = np.nan
    if decile_col:
        result["seifa_irsad_decile"] = pd.to_numeric(df[decile_col], errors="coerce")
    else:
        result["seifa_irsad_decile"] = np.nan

    result = result.dropna(subset=["SA1_CODE_2021"])
    result["SA1_CODE_2021"] = result["SA1_CODE_2021"].astype(str).str.strip()
    return result


def build_sa1_postcode_concordance():
    """Build SA1→Postcode mapping using Mesh Block allocation files.
    Each MB belongs to exactly one SA1 and one POA (postcode area).
    """
    mb_path = RAW / "MB_2021_AUST.xlsx"
    poa_path = RAW / "POA_2021_AUST.xlsx"

    if not mb_path.exists() or not poa_path.exists():
        print("  Allocation files not found, skipping concordance")
        return pd.DataFrame()

    print("  Loading MB → SA1 mapping...")
    mb = pd.read_excel(mb_path, engine="openpyxl", dtype=str)
    mb_cols = mb.columns.tolist()
    print(f"    MB columns: {mb_cols[:10]}...")

    # Find SA1 code column in MB file
    sa1_col = None
    mb_col = None
    for c in mb_cols:
        cl = c.upper()
        if "SA1" in cl and "CODE" in cl and "2021" in cl:
            sa1_col = c
        if "MB" in cl and "CODE" in cl and "2021" in cl:
            mb_col = c

    if mb_col is None:
        mb_col = mb_cols[0]
    if sa1_col is None:
        # SA1 might be derivable from MB code
        for c in mb_cols:
            if "SA1" in c.upper():
                sa1_col = c
                break

    print(f"    MB col: {mb_col}, SA1 col: {sa1_col}")

    # Check if POA is already in MB file
    poa_col_in_mb = None
    for c in mb_cols:
        if "POA" in c.upper():
            poa_col_in_mb = c

    if poa_col_in_mb:
        print(f"    POA found directly in MB file: {poa_col_in_mb}")
        concordance = mb[[mb_col, sa1_col, poa_col_in_mb]].copy()
        concordance.columns = ["mb_code", "sa1_code", "postcode"]
    else:
        print("  Loading POA → MB mapping...")
        poa = pd.read_excel(poa_path, engine="openpyxl", dtype=str)
        poa_cols = poa.columns.tolist()
        print(f"    POA columns: {poa_cols[:10]}...")

        poa_mb_col = None
        poa_poa_col = None
        for c in poa_cols:
            cl = c.upper()
            if "MB" in cl and "CODE" in cl:
                poa_mb_col = c
            if "POA" in cl and "CODE" in cl:
                poa_poa_col = c

        if poa_mb_col is None:
            poa_mb_col = poa_cols[0]
        if poa_poa_col is None:
            poa_poa_col = poa_cols[1]

        # Join on MB code
        mb_slim = mb[[mb_col, sa1_col]].copy()
        mb_slim.columns = ["mb_code", "sa1_code"]
        poa_slim = poa[[poa_mb_col, poa_poa_col]].copy()
        poa_slim.columns = ["mb_code", "postcode"]

        concordance = mb_slim.merge(poa_slim, on="mb_code", how="inner")

    # Clean postcodes — remove non-numeric, leading zeros
    concordance["postcode"] = concordance["postcode"].str.strip()
    concordance = concordance[concordance["postcode"].str.match(r"^\d{4}$", na=False)]
    concordance["sa1_code"] = concordance["sa1_code"].str.strip()

    # Create SA1→Postcode mapping (many-to-many via mesh blocks)
    # Group: for each SA1, list all postcodes it touches
    sa1_poa = concordance[["sa1_code", "postcode"]].drop_duplicates()
    print(f"    SA1→Postcode pairs: {len(sa1_poa):,}")
    print(f"    Unique SA1s: {sa1_poa['sa1_code'].nunique():,}")
    print(f"    Unique Postcodes: {sa1_poa['postcode'].nunique():,}")

    return sa1_poa


def process_state(state_code):
    """Process all Census tables for one state, return merged SA1 DataFrame."""
    state_dir = STATES[state_code]
    sc = STATE_SUFFIX[state_code]
    print(f"\n{'='*60}")
    print(f"Processing {state_code}...")
    print(f"{'='*60}")

    if not state_dir.exists():
        print(f"  Directory not found: {state_dir}")
        return pd.DataFrame()

    # Load each table
    print("  G01 — Population...")
    g01 = load_g01(state_dir, sc)
    print(f"    {len(g01):,} SA1s")

    print("  G02 — Medians...")
    g02 = load_g02(state_dir, sc)

    print("  G33 — Household income...")
    g33 = load_g33(state_dir, sc)

    print("  G43 — Labour force & qualifications...")
    g43 = load_g43(state_dir, sc)

    print("  G60B — Occupation (Person totals)...")
    g60 = load_g60b(state_dir, sc)

    print("  G62 — Travel to work / WFH...")
    g62 = load_g62(state_dir, sc)

    # Merge all on SA1_CODE_2021
    merged = g01.copy()
    for df in [g02, g33, g43, g60, g62]:
        merged = merged.merge(df, on="SA1_CODE_2021", how="left")

    merged["state"] = state_code
    print(f"  Merged: {len(merged):,} SA1s × {len(merged.columns)} columns")
    return merged


def main():
    print("=" * 60)
    print("ABS Census 2021 — SA1 Demographic Processing")
    print("=" * 60)

    # Process each state
    frames = []
    for sc in STATES:
        df = process_state(sc)
        if not df.empty:
            frames.append(df)

    if not frames:
        print("\nERROR: No state data processed!")
        return

    all_sa1 = pd.concat(frames, ignore_index=True)
    print(f"\n{'='*60}")
    print(f"Combined: {len(all_sa1):,} SA1s across {all_sa1['state'].nunique()} states")

    # Add SEIFA
    print("\nLoading SEIFA IRSAD...")
    seifa = load_seifa()
    if not seifa.empty:
        seifa["SA1_CODE_2021"] = seifa["SA1_CODE_2021"].astype(str)
        all_sa1["SA1_CODE_2021"] = all_sa1["SA1_CODE_2021"].astype(str)
        all_sa1 = all_sa1.merge(seifa, on="SA1_CODE_2021", how="left")
        matched = all_sa1["seifa_irsad_decile"].notna().sum()
        print(f"  SEIFA matched: {matched:,} / {len(all_sa1):,} SA1s")

    # Save SA1-level parquet
    sa1_path = OUT / "census_sa1_demographics.parquet"
    all_sa1.to_parquet(sa1_path, index=False)
    print(f"\nSaved SA1-level: {sa1_path} ({len(all_sa1):,} rows)")

    # Build SA1→Postcode concordance
    print("\nBuilding SA1→Postcode concordance...")
    concordance = build_sa1_postcode_concordance()
    if not concordance.empty:
        conc_path = OUT / "sa1_postcode_concordance.parquet"
        concordance.to_parquet(conc_path, index=False)
        print(f"Saved concordance: {conc_path}")

        # Aggregate to postcode level (population-weighted where appropriate)
        print("\nAggregating to postcode level...")
        all_sa1["SA1_CODE_2021"] = all_sa1["SA1_CODE_2021"].astype(str)
        concordance["sa1_code"] = concordance["sa1_code"].astype(str)

        # Join SA1 demographics to concordance
        sa1_poa = concordance.merge(
            all_sa1, left_on="sa1_code", right_on="SA1_CODE_2021", how="inner"
        )
        print(f"  Joined: {len(sa1_poa):,} SA1-postcode pairs with demographics")

        # Population-weighted aggregation to postcode
        # For medians, use population-weighted mean as approximation
        pop_col = "total_population"
        sa1_poa["weight"] = sa1_poa[pop_col].fillna(0)

        def weighted_mean(group, col):
            w = group["weight"]
            v = group[col]
            mask = v.notna() & (w > 0)
            if mask.sum() == 0:
                return np.nan
            return np.average(v[mask], weights=w[mask])

        agg_cols = [
            "median_age", "median_personal_income_weekly", "median_hh_income_weekly",
            "median_rent_weekly", "median_mortgage_monthly", "median_family_income_weekly",
            "avg_household_size", "pct_high_income_hh", "pct_degree",
            "pct_professional", "pct_wfh", "labour_force_participation_pct",
            "unemployment_pct", "seifa_irsad_score", "seifa_irsad_decile",
        ]

        postcode_rows = []
        for postcode, grp in sa1_poa.groupby("postcode"):
            row = {"postcode": postcode}
            row["total_population"] = grp[pop_col].sum()
            row["num_sa1s"] = grp["sa1_code"].nunique()
            row["state"] = grp["state"].mode().iloc[0] if len(grp) > 0 else ""

            for col in agg_cols:
                if col in grp.columns:
                    row[col] = weighted_mean(grp, col)
                else:
                    row[col] = np.nan

            # Sum counts for degree + professional
            row["n_degree_total"] = grp["n_degree_total"].sum() if "n_degree_total" in grp.columns else 0
            row["n_prof_managerial"] = grp["n_prof_managerial"].sum() if "n_prof_managerial" in grp.columns else 0
            row["n_wfh"] = grp["n_wfh"].sum() if "n_wfh" in grp.columns else 0
            row["hh_total"] = grp["hh_total"].sum() if "hh_total" in grp.columns else 0
            postcode_rows.append(row)

        postcode_df = pd.DataFrame(postcode_rows)
        poa_path = OUT / "census_postcode_demographics.parquet"
        postcode_df.to_parquet(poa_path, index=False)
        print(f"Saved postcode-level: {poa_path} ({len(postcode_df):,} postcodes)")

        # Summary stats
        print(f"\n{'='*60}")
        print("Summary Statistics (postcode-level)")
        print(f"{'='*60}")
        for col in ["median_hh_income_weekly", "pct_professional", "pct_degree",
                     "pct_wfh", "seifa_irsad_decile", "pct_high_income_hh"]:
            if col in postcode_df.columns:
                vals = postcode_df[col].dropna()
                if len(vals) > 0:
                    print(f"  {col}: mean={vals.mean():.1f}, median={vals.median():.1f}, "
                          f"min={vals.min():.1f}, max={vals.max():.1f}")

    # Also save a CSV for easy inspection
    csv_path = OUT / "census_postcode_demographics.csv"
    if 'postcode_df' in dir():
        postcode_df.round(2).to_csv(csv_path, index=False)
        print(f"\nAlso saved CSV: {csv_path}")

    print(f"\n{'='*60}")
    print("DONE — Phase 1 Census processing complete")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
