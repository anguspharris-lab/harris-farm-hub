"""Import HFM Job Roles from Excel into the Hub database.

Usage:
    python3 backend/import_roles.py                      # replace mode (default)
    python3 backend/import_roles.py --mode append         # append only

Also callable from the API via POST /api/roles/import.
"""

import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import openpyxl

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_XLSX = Path(os.path.expanduser(
    "~/Desktop/Working files/HFM Job Roles.xlsx"
))
DEFAULT_DB = PROJECT_ROOT / "hub_data.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "roles"


def _log(lines: list, msg: str):
    """Append a timestamped message to the log buffer."""
    entry = f"[{datetime.now().isoformat()}] {msg}"
    lines.append(entry)


def read_xlsx(xlsx_path: Path) -> list[dict]:
    """Read the Excel file and return a list of row dicts."""
    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True)
    ws = wb.active

    rows = []
    header = None
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            header = [str(c).strip() if c else "" for c in row]
            continue
        if not any(cell is not None for cell in row):
            continue
        rows.append(dict(zip(header, row)))

    wb.close()
    return rows


def validate_and_clean(raw_rows: list[dict], log: list) -> tuple[list[dict], list[str]]:
    """Validate rows, trim whitespace, reject rows missing required fields.

    Returns (clean_rows, warnings).
    """
    required = ["Function", "Department", "Job"]
    clean = []
    warnings = []

    for i, row in enumerate(raw_rows, start=2):  # Excel row 2+
        missing = [f for f in required if not row.get(f) or str(row[f]).strip() == ""]
        if missing:
            msg = f"Row {i}: missing {', '.join(missing)} — skipped"
            warnings.append(msg)
            _log(log, f"WARN: {msg}")
            continue

        clean.append({
            "function": str(row["Function"]).strip(),
            "department": str(row["Department"]).strip(),
            "job": str(row["Job"]).strip(),
        })

    _log(log, f"Validated {len(clean)} rows, {len(warnings)} warnings")
    return clean, warnings


def deduplicate(rows: list[dict], log: list) -> tuple[list[dict], list[dict]]:
    """Remove duplicate Function+Department+Job combos.

    Returns (unique_rows, duplicate_rows).
    """
    seen = set()
    unique = []
    dupes = []

    for row in rows:
        key = (row["function"], row["department"], row["job"])
        if key in seen:
            dupes.append(row)
        else:
            seen.add(key)
            unique.append(row)

    if dupes:
        _log(log, f"Removed {len(dupes)} duplicates")
    else:
        _log(log, "No duplicates found")

    return unique, dupes


def insert_roles(db_path: str, rows: list[dict], mode: str, log: list) -> int:
    """Insert rows into employee_roles table. Returns count inserted."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Ensure table exists
    c.execute('''CREATE TABLE IF NOT EXISTS employee_roles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  function TEXT NOT NULL,
                  department TEXT NOT NULL,
                  job TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  UNIQUE(function, department, job))''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_roles_function ON employee_roles(function)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_roles_department ON employee_roles(department)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_roles_job ON employee_roles(job)")

    if mode == "replace":
        c.execute("DELETE FROM employee_roles")
        _log(log, "Cleared existing employee_roles data (replace mode)")

    now = datetime.now().isoformat()
    inserted = 0

    for row in rows:
        try:
            c.execute(
                """INSERT OR IGNORE INTO employee_roles
                   (function, department, job, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (row["function"], row["department"], row["job"], now, now),
            )
            if c.rowcount > 0:
                inserted += 1
        except sqlite3.IntegrityError:
            pass  # skip duplicates in append mode

    conn.commit()
    conn.close()

    _log(log, f"Inserted {inserted} rows into employee_roles")
    return inserted


def build_metadata(rows: list[dict], source_file: str) -> dict:
    """Build the role_metadata.json content."""
    functions = sorted(set(r["function"] for r in rows))
    departments = sorted(set(r["department"] for r in rows))
    jobs = sorted(set(r["job"] for r in rows))

    return {
        "total_roles": len(rows),
        "unique_functions": len(functions),
        "unique_departments": len(departments),
        "unique_jobs": len(jobs),
        "functions": functions,
        "departments": departments,
        "jobs": jobs,
        "import_timestamp": datetime.now().isoformat(),
        "source_file": source_file,
    }


def build_report(rows: list[dict], dupes: list[dict], warnings: list[str],
                 inserted: int) -> str:
    """Build the human-readable import report."""
    lines = []
    lines.append("=" * 60)
    lines.append("HFM Job Roles Import Report")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    lines.append("SUMMARY")
    lines.append(f"  Rows processed:     {len(rows) + len(dupes) + len(warnings)}")
    lines.append(f"  Successful imports: {inserted}")
    lines.append(f"  Duplicates found:   {len(dupes)}")
    lines.append(f"  Validation errors:  {len(warnings)}")
    lines.append("")

    # Breakdown by Function
    func_counts = Counter(r["function"] for r in rows)
    lines.append("BREAKDOWN BY FUNCTION")
    for func, count in func_counts.most_common():
        lines.append(f"  {func}: {count}")
    lines.append("")

    # Breakdown by Department
    dept_counts = Counter(r["department"] for r in rows)
    lines.append("BREAKDOWN BY DEPARTMENT")
    for dept, count in dept_counts.most_common():
        lines.append(f"  {dept}: {count}")
    lines.append("")

    # Sample data
    lines.append("SAMPLE DATA (first 5 rows)")
    lines.append(f"  {'Function':<25} {'Department':<25} {'Job'}")
    lines.append(f"  {'-'*25} {'-'*25} {'-'*30}")
    for row in rows[:5]:
        lines.append(f"  {row['function']:<25} {row['department']:<25} {row['job']}")
    lines.append("")

    if warnings:
        lines.append("VALIDATION WARNINGS")
        for w in warnings:
            lines.append(f"  {w}")
        lines.append("")

    if dupes:
        lines.append("DUPLICATES REMOVED")
        for d in dupes:
            lines.append(f"  {d['function']} / {d['department']} / {d['job']}")
        lines.append("")

    return "\n".join(lines)


def run_import(
    xlsx_path: str = None,
    db_path: str = None,
    mode: str = "replace",
    output_dir: str = None,
) -> dict:
    """Main import function. Returns a result dict."""
    xlsx_path = Path(xlsx_path) if xlsx_path else DEFAULT_XLSX
    db_path = str(db_path) if db_path else str(DEFAULT_DB)
    output_dir = Path(output_dir) if output_dir else OUTPUT_DIR

    log_lines = []
    _log(log_lines, f"Starting import from {xlsx_path.name} (mode={mode})")

    # 1. Read
    if not xlsx_path.exists():
        error = f"File not found: {xlsx_path}"
        _log(log_lines, f"ERROR: {error}")
        return {"error": error, "log": log_lines}

    raw_rows = read_xlsx(xlsx_path)
    _log(log_lines, f"Read {len(raw_rows)} rows from {xlsx_path.name}")

    # 2. Validate
    clean_rows, warnings = validate_and_clean(raw_rows, log_lines)

    # 3. Deduplicate
    unique_rows, dupes = deduplicate(clean_rows, log_lines)

    # 4. Insert
    inserted = insert_roles(db_path, unique_rows, mode, log_lines)

    # 5. Generate outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = build_metadata(unique_rows, xlsx_path.name)
    metadata_path = output_dir / "role_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    _log(log_lines, f"Wrote {metadata_path}")

    report = build_report(unique_rows, dupes, warnings, inserted)
    report_path = output_dir / "import_report.txt"
    with open(report_path, "w") as f:
        f.write(report)
    _log(log_lines, f"Wrote {report_path}")

    log_path = output_dir / "import_log.txt"
    with open(log_path, "w") as f:
        f.write("\n".join(log_lines) + "\n")
    _log(log_lines, f"Wrote {log_path}")

    _log(log_lines, "Import complete")

    return {
        "status": "success",
        "rows_read": len(raw_rows),
        "rows_imported": inserted,
        "duplicates": len(dupes),
        "warnings": len(warnings),
        "mode": mode,
        "metadata": metadata,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import HFM Job Roles")
    parser.add_argument("--mode", choices=["replace", "append"], default="replace")
    parser.add_argument("--xlsx", default=None, help="Path to xlsx file")
    parser.add_argument("--db", default=None, help="Path to SQLite database")
    args = parser.parse_args()

    result = run_import(
        xlsx_path=args.xlsx,
        db_path=args.db,
        mode=args.mode,
    )

    if result.get("error"):
        print(f"ERROR: {result['error']}")
        sys.exit(1)

    print(f"Imported {result['rows_imported']} roles ({result['mode']} mode)")
    print(f"  Duplicates removed: {result['duplicates']}")
    print(f"  Warnings: {result['warnings']}")
    print(f"  Output: {OUTPUT_DIR}")
