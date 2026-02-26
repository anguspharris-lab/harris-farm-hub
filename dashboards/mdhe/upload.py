"""
Harris Farm Hub -- MDHE Data Upload
Upload master data files (CSV/Excel) for validation and health scoring.
Source types: PLU Master, Barcode Register, Price Book, Supplier Master, etc.
"""

import io
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

import pandas as pd
import streamlit as st

# Backend imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from mdhe_db import (
    init_mdhe_db, add_data_source, update_data_source_status,
    add_validations_bulk, save_scores, create_issues_from_validations,
    save_plu_records, seed_dummy_data, clear_dummy_data,
)
from mdhe.engine import validate_plu_data
from shared.styles import (
    render_header, render_footer,
    GREEN, BLUE, GOLD, RED, ORANGE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    NAVY_CARD, NAVY_MID, BORDER,
)

# Ensure MDHE tables exist
init_mdhe_db()

# ============================================================================
# Expected columns for PLU Master File mapping
# ============================================================================

PLU_EXPECTED_COLUMNS = [
    "plu_code",
    "barcode",
    "description",
    "category",
    "subcategory",
    "unit_of_measure",
    "pack_size",
    "supplier_code",
    "status",
    "retail_price",
    "cost_price",
]

SOURCE_TYPES = [
    "PLU Master File",
    "Barcode Register",
    "Price Book",
    "Supplier Master",
    "Vision Scan Data",
    "POS Scan Report",
    "Store Master",
    "Product Hierarchy",
]


# ============================================================================
# Helpers
# ============================================================================

def _normalise_col(name):
    # type: (str) -> str
    """Lowercase, strip whitespace, replace spaces/hyphens with underscores."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _auto_match_columns(upload_cols, expected_cols):
    # type: (List[str], List[str]) -> Dict[str, Optional[str]]
    """
    Auto-match uploaded column names to expected columns.
    Case-insensitive, strips underscores/spaces for comparison.
    Returns {expected_col: matched_upload_col or None}.
    """
    normalised_upload = {_normalise_col(c): c for c in upload_cols}
    mapping = {}  # type: Dict[str, Optional[str]]
    for expected in expected_cols:
        norm_expected = _normalise_col(expected)
        if norm_expected in normalised_upload:
            mapping[expected] = normalised_upload[norm_expected]
        else:
            mapping[expected] = None
    return mapping


def _parse_upload(uploaded_file):
    """Parse an uploaded CSV or Excel file into a DataFrame."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        raw = uploaded_file.getvalue()
        df = pd.read_csv(io.BytesIO(raw))
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        raw = uploaded_file.getvalue()
        df = pd.read_excel(io.BytesIO(raw))
    else:
        raise ValueError("Unsupported file type. Please upload CSV or Excel (.xlsx).")
    return df


def _file_size_str(size_bytes):
    # type: (int) -> str
    if size_bytes < 1024:
        return "%d B" % size_bytes
    elif size_bytes < 1024 * 1024:
        return "%.1f KB" % (size_bytes / 1024)
    else:
        return "%.1f MB" % (size_bytes / (1024 * 1024))


# ============================================================================
# Main render function
# ============================================================================

def render_mdhe_upload():
    user = st.session_state.get("auth_user", {})

    render_header(
        "MDHE -- Data Upload",
        "Upload master data files for validation and health scoring",
    )

    # ------------------------------------------------------------------
    # Section 1: Upload New Data
    # ------------------------------------------------------------------

    st.subheader("Upload New Data")

    col_source, col_spacer = st.columns([3, 1])
    with col_source:
        source_type = st.selectbox(
            "Source Type",
            SOURCE_TYPES,
            key="mdhe_source_type",
            help="Select the type of master data file you are uploading.",
        )

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx"],
        key="mdhe_file_uploader",
        help="Upload a CSV or Excel (.xlsx) master data file.",
    )

    if uploaded_file is not None:
        try:
            df = _parse_upload(uploaded_file)
        except Exception as e:
            st.error("Failed to parse file: %s" % str(e))
            df = None

        if df is not None:
            # File info
            st.markdown("---")
            info_c1, info_c2, info_c3 = st.columns(3)
            with info_c1:
                st.metric("File Name", uploaded_file.name)
            with info_c2:
                st.metric("File Size", _file_size_str(uploaded_file.size))
            with info_c3:
                st.metric("Row Count", "{:,}".format(len(df)))

            # Preview first 20 rows
            st.markdown("**Preview** (first 20 rows)")
            st.dataframe(df.head(20), use_container_width=True)

            # Column list with detected types
            with st.expander("Column Details"):
                col_info = pd.DataFrame({
                    "Column": df.columns.tolist(),
                    "Type": [str(dt) for dt in df.dtypes.tolist()],
                    "Non-Null": [int(df[c].notna().sum()) for c in df.columns],
                    "Null": [int(df[c].isna().sum()) for c in df.columns],
                })
                st.dataframe(col_info, use_container_width=True, hide_index=True)

            # ----------------------------------------------------------
            # Column Mapping (PLU Master File only)
            # ----------------------------------------------------------
            column_mapping = {}  # type: Dict[str, Optional[str]]
            is_plu_type = (source_type == "PLU Master File")

            if is_plu_type:
                st.markdown("---")
                st.markdown("### Column Mapping")
                st.caption(
                    "Map your file columns to the expected PLU Master fields. "
                    "Auto-matched columns are pre-selected where names align."
                )

                auto_map = _auto_match_columns(df.columns.tolist(), PLU_EXPECTED_COLUMNS)
                upload_col_options = ["-- Not Mapped --"] + df.columns.tolist()

                map_cols = st.columns(2)
                for idx, expected_col in enumerate(PLU_EXPECTED_COLUMNS):
                    col_container = map_cols[idx % 2]
                    with col_container:
                        auto_val = auto_map.get(expected_col)
                        if auto_val and auto_val in upload_col_options:
                            default_idx = upload_col_options.index(auto_val)
                        else:
                            default_idx = 0

                        chosen = st.selectbox(
                            expected_col,
                            upload_col_options,
                            index=default_idx,
                            key="mdhe_map_%s" % expected_col,
                        )
                        if chosen != "-- Not Mapped --":
                            column_mapping[expected_col] = chosen
                        else:
                            column_mapping[expected_col] = None

            # ----------------------------------------------------------
            # Upload & Validate Button
            # ----------------------------------------------------------
            st.markdown("---")

            if st.button(
                "Upload & Validate",
                type="primary",
                key="mdhe_upload_validate_btn",
                use_container_width=True,
            ):
                user_email = user.get("email", "unknown") if isinstance(user, dict) else "unknown"

                with st.spinner("Uploading and validating..."):
                    try:
                        # 1. Register the data source
                        source_type_key = source_type.lower().replace(" ", "_")
                        source_id = add_data_source(
                            source_type=source_type_key,
                            filename=uploaded_file.name,
                            uploaded_by=user_email,
                            row_count=len(df),
                            notes="Uploaded via MDHE Dashboard",
                        )

                        if is_plu_type:
                            # 2. Remap columns and build record dicts
                            records = []
                            for _, row in df.iterrows():
                                rec = {}
                                for expected_col in PLU_EXPECTED_COLUMNS:
                                    mapped_col = column_mapping.get(expected_col)
                                    if mapped_col and mapped_col in df.columns:
                                        val = row[mapped_col]
                                        # Convert NaN to None
                                        if pd.isna(val):
                                            val = None
                                        rec[expected_col] = val
                                    else:
                                        rec[expected_col] = None
                                records.append(rec)

                            # 3. Save PLU records
                            save_plu_records(records, source_id, is_dummy=0)

                            # 4. Run validation
                            result = validate_plu_data(records)
                            all_validations = result["validations"]
                            scores = result["scores"]

                            # 5. Save validation results
                            if all_validations:
                                val_records = []
                                for v in all_validations:
                                    v_rec = dict(v)
                                    v_rec["source_id"] = source_id
                                    val_records.append(v_rec)
                                add_validations_bulk(val_records)

                            # 6. Save scores
                            today_str = datetime.utcnow().strftime("%Y-%m-%d")
                            save_scores(today_str, scores)

                            # 7. Create issues from validations
                            issue_ids = create_issues_from_validations(source_id, min_severity="medium")

                            # 8. Update source status
                            update_data_source_status(source_id, "validated", row_count=len(df))

                            # Success summary
                            overall_score = scores.get("overall", {}).get("score", 0)
                            total_issues = len(all_validations)
                            issues_created = len(issue_ids)

                            st.success(
                                "Validation complete. Overall health score: %.1f%%. "
                                "%d validation checks run, %d issues created."
                                % (overall_score, total_issues, issues_created)
                            )

                            # Score breakdown
                            score_cols = st.columns(5)
                            domain_names = ["plu", "barcode", "pricing", "hierarchy", "supplier"]
                            domain_labels = ["PLU", "Barcode", "Pricing", "Hierarchy", "Supplier"]
                            for i, (domain, label) in enumerate(zip(domain_names, domain_labels)):
                                d_score = scores.get(domain, {}).get("score", 0)
                                with score_cols[i]:
                                    st.metric(label, "%.0f%%" % d_score)

                            # Link to MDHE Issues page
                            _pages = st.session_state.get("_pages", {})
                            if "mdhe-issues" in _pages:
                                st.page_link(
                                    _pages["mdhe-issues"],
                                    label="View Issues in MDHE Issue Tracker",
                                )

                        else:
                            # Non-PLU file types: just register the upload
                            update_data_source_status(source_id, "uploaded", row_count=len(df))
                            st.success(
                                "File '%s' uploaded successfully (%d rows). "
                                "Validation engine for '%s' type coming soon."
                                % (uploaded_file.name, len(df), source_type)
                            )

                    except Exception as e:
                        st.error("Upload failed: %s" % str(e))
                        import traceback
                        st.code(traceback.format_exc())

    # ------------------------------------------------------------------
    # Section 2: Upload History
    # ------------------------------------------------------------------

    st.markdown("---")
    st.subheader("Upload History")

    try:
        from mdhe_db import _get_conn, _ensure_init
        _ensure_init()
        conn = _get_conn()
        rows = conn.execute(
            "SELECT source_type, filename, uploaded_at, row_count, status, uploaded_by "
            "FROM mdhe_data_sources ORDER BY id DESC LIMIT 50"
        ).fetchall()
        conn.close()

        if rows:
            history_data = []
            for r in rows:
                history_data.append({
                    "Source Type": r["source_type"],
                    "Filename": r["filename"],
                    "Uploaded At": r["uploaded_at"],
                    "Rows": r["row_count"],
                    "Status": r["status"],
                    "Uploaded By": r["uploaded_by"] or "N/A",
                })
            df_history = pd.DataFrame(history_data)
            st.dataframe(df_history, use_container_width=True, hide_index=True)
        else:
            st.info("No uploads yet. Upload a file above or seed demo data below.")
    except Exception as e:
        st.warning("Could not load upload history: %s" % str(e))

    # ------------------------------------------------------------------
    # Section 3: Quick Actions
    # ------------------------------------------------------------------

    st.markdown("---")
    st.subheader("Quick Actions")
    st.caption("For demo purposes: seed or clear sample data to explore the MDHE features.")

    qa_c1, qa_c2, qa_c3 = st.columns([1, 1, 2])

    with qa_c1:
        if st.button("Seed Demo Data", key="mdhe_seed_btn", use_container_width=True):
            with st.spinner("Seeding demo data..."):
                try:
                    seed_dummy_data()
                    st.success(
                        "Demo data seeded: 10 PLU records with deliberate quality issues, "
                        "validations, scores, scan data, and 14-day history."
                    )
                    st.rerun()
                except Exception as e:
                    st.error("Seed failed: %s" % str(e))

    with qa_c2:
        if st.button("Clear Demo Data", key="mdhe_clear_btn", use_container_width=True):
            with st.spinner("Clearing demo data..."):
                try:
                    clear_dummy_data()
                    st.success("All demo data cleared.")
                    st.rerun()
                except Exception as e:
                    st.error("Clear failed: %s" % str(e))

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------

    render_footer("MDHE Upload", user=user)


# ============================================================================
# Run
# ============================================================================

render_mdhe_upload()
