"""
Harris Farm Hub — Portal Content Loader
Reads and structures existing documentation, procedures, learnings, rubrics,
and audit metrics for the Hub Documentation Portal.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DOCS_DIR = PROJECT_ROOT / "docs"
PROCEDURES_DIR = PROJECT_ROOT / "watchdog" / "procedures"
LEARNINGS_DIR = PROJECT_ROOT / "watchdog" / "learnings"
RUBRICS_DIR = PROJECT_ROOT / "watchdog" / "rubrics"
AUDIT_LOG = PROJECT_ROOT / "watchdog" / "audit.log"


# ---------------------------------------------------------------------------
# DOCUMENT LOADERS
# ---------------------------------------------------------------------------

def load_doc(name):
    """Read a markdown file from docs/ and return its content.

    Args:
        name: filename without extension, e.g. "USER_GUIDE"

    Returns:
        str content or None if not found.
    """
    path = DOCS_DIR / "{}.md".format(name)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_procedure(name):
    """Read a procedure from watchdog/procedures/.

    Args:
        name: filename without extension, e.g. "task_execution"
    """
    path = PROCEDURES_DIR / "{}.md".format(name)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_learning(name):
    """Read a learning file from watchdog/learnings/.

    Args:
        name: filename with extension, e.g. "data_context.md"
    """
    path = LEARNINGS_DIR / name
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_rubric(name):
    """Read and parse a rubric JSON from watchdog/rubrics/.

    Args:
        name: filename without extension, e.g. "code_quality"

    Returns:
        dict or None.
    """
    path = RUBRICS_DIR / "{}.json".format(name)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# INDEXES
# ---------------------------------------------------------------------------

def _file_meta(path):
    """Return metadata dict for a file."""
    stat = path.stat()
    return {
        "name": path.stem,
        "filename": path.name,
        "path": str(path),
        "size_kb": round(stat.st_size / 1024, 1),
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
            "%Y-%m-%d %H:%M"),
    }


def get_doc_index():
    """Return list of all docs with metadata."""
    if not DOCS_DIR.exists():
        return []
    files = sorted(DOCS_DIR.glob("*.md"))
    return [_file_meta(f) for f in files]


def get_procedure_index():
    """Return list of all procedures with metadata."""
    if not PROCEDURES_DIR.exists():
        return []
    files = sorted(PROCEDURES_DIR.glob("*.md"))
    return [_file_meta(f) for f in files]


def get_learning_index():
    """Return list of all learning files with metadata."""
    if not LEARNINGS_DIR.exists():
        return []
    files = sorted(LEARNINGS_DIR.glob("*"))
    return [_file_meta(f) for f in files if f.is_file()]


# ---------------------------------------------------------------------------
# SEARCH
# ---------------------------------------------------------------------------

def search_all_docs(query):
    """Search across all documentation, procedures, and learnings.

    Returns list of {source, name, line_number, context} dicts.
    """
    if not query or len(query.strip()) < 2:
        return []

    q = query.strip().lower()
    results = []

    # Search docs/
    for f in DOCS_DIR.glob("*.md"):
        _search_file(f, q, "Documentation", results)

    # Search procedures/
    if PROCEDURES_DIR.exists():
        for f in PROCEDURES_DIR.glob("*.md"):
            _search_file(f, q, "Procedure", results)

    # Search learnings/
    if LEARNINGS_DIR.exists():
        for f in LEARNINGS_DIR.glob("*"):
            if f.is_file():
                _search_file(f, q, "Learning", results)

    return results[:50]


def _search_file(path, query_lower, source_type, results):
    """Helper: search a single file for matches."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return
    for i, line in enumerate(lines):
        if query_lower in line.lower():
            # Grab 1 line before and after for context
            start = max(0, i - 1)
            end = min(len(lines), i + 2)
            context = "\n".join(lines[start:end])
            results.append({
                "source": source_type,
                "name": path.stem,
                "filename": path.name,
                "line_number": i + 1,
                "context": context[:300],
            })


# ---------------------------------------------------------------------------
# AUDIT METRICS
# ---------------------------------------------------------------------------

def parse_audit_metrics():
    """Parse watchdog/audit.log and extract aggregate metrics.

    Returns dict with:
        task_count, avg_scores, latest_task, score_entries
    """
    if not AUDIT_LOG.exists():
        return {"task_count": 0, "avg_scores": {}, "latest_task": None,
                "score_entries": []}

    content = AUDIT_LOG.read_text(encoding="utf-8")

    # Universal score pattern — catches all audit.log format variations
    score_pattern = re.compile(
        r"(?:SCORES?:\s*)?"
        r"H[=:]?(\d+)\s+"
        r"R[=:]?(\d+)\s+"
        r"S[=:]?(\d+)\s+"
        r"C[=:]?(\d+)\s+"
        r"D[=:]?(\d+|N/?A)\s+"
        r"U[=:]?(\d+)\s+"
        r"X[=:]?(\d+)",
        re.IGNORECASE)
    matches = score_pattern.findall(content)

    score_entries = []
    for m in matches:
        d_raw = m[4]
        d_val = 0 if d_raw.upper().replace("/", "") == "NA" else int(d_raw)
        scores = {
            "H": int(m[0]), "R": int(m[1]), "S": int(m[2]),
            "C": int(m[3]), "D": d_val, "U": int(m[5]),
            "X": int(m[6]),
        }
        valid = [v for v in scores.values() if v > 0]
        scores["avg"] = round(sum(valid) / len(valid), 1) if valid else 0
        score_entries.append(scores)

    # Calculate averages
    avg_scores = {}
    if score_entries:
        for key in ["H", "R", "S", "C", "D", "U", "X"]:
            vals = [e[key] for e in score_entries if e.get(key, 0) > 0]
            avg_scores[key] = round(sum(vals) / len(vals), 1) if vals else 0
        vals = [e["avg"] for e in score_entries if e.get("avg", 0) > 0]
        avg_scores["avg"] = round(sum(vals) / len(vals), 1) if vals else 0

    # Count [TASK] entries
    task_count = content.count("[TASK]")

    # Find latest task line
    task_lines = [l for l in content.splitlines() if "[TASK]" in l]
    latest_task = task_lines[-1] if task_lines else None

    return {
        "task_count": task_count,
        "avg_scores": avg_scores,
        "latest_task": latest_task,
        "score_entries": score_entries,
    }


# ---------------------------------------------------------------------------
# DATA SOURCES
# ---------------------------------------------------------------------------

DATA_SOURCES = [
    {
        "name": "Transaction Data",
        "type": "Parquet / DuckDB",
        "size": "6.6 GB",
        "rows": "383.6M",
        "source": "Microsoft Fabric POS (fact_pos_sales)",
        "grain": "Individual POS line items",
        "period": "FY24 - FY26 YTD (Jul 2023 - Feb 2026)",
        "stores": 34,
        "columns": [
            ("Reference2", "TEXT", "Transaction ID"),
            ("SaleDate", "TIMESTAMP", "UTC sale datetime"),
            ("Store_ID", "TEXT", "Store identifier"),
            ("PLUItem_ID", "TEXT", "Product PLU code"),
            ("Quantity", "FLOAT", "Units sold"),
            ("SalesIncGST", "FLOAT", "Revenue incl. GST"),
            ("GST", "FLOAT", "GST component"),
            ("EstimatedCOGS", "FLOAT", "Estimated cost of goods"),
            ("CustomerCode", "TEXT", "Customer ID (88% null)"),
        ],
        "used_by": ["Store Ops", "Product Intel",
                     "Revenue Bridge", "Buying Hub"],
        "join_key": "PLUItem_ID = ProductNumber",
    },
    {
        "name": "Product Hierarchy",
        "type": "Parquet",
        "size": "2 MB",
        "rows": "72,911",
        "source": "Product Hierarchy 20260215.xlsx",
        "grain": "Individual product/SKU",
        "period": "Snapshot (Feb 2026)",
        "stores": None,
        "columns": [
            ("ProductNumber", "TEXT", "PLU code (join key)"),
            ("ProductName", "TEXT", "Product description"),
            ("DepartmentCode/Desc", "TEXT", "Level 1 (9 departments)"),
            ("MajorGroupCode/Desc", "TEXT", "Level 2 (30 groups)"),
            ("MinorGroupCode/Desc", "TEXT", "Level 3 (405 groups)"),
            ("HFMItem/HFMItemDesc", "TEXT", "Level 4 (4,465 items)"),
            ("BuyerId", "TEXT", "Buyer code (no name mapping)"),
            ("ProductLifecycleStateId", "TEXT", "Active/Deleted/New/Derange"),
        ],
        "used_by": ["Store Ops", "Product Intel",
                     "Revenue Bridge", "Buying Hub"],
        "join_key": "ProductNumber = PLUItem_ID (98.3% match)",
    },
    {
        "name": "Weekly Aggregated",
        "type": "SQLite",
        "size": "399 MB",
        "rows": "1.6M sales + 17K customer + 77K market share",
        "source": "harris_farm.db",
        "grain": "Store x Week x Department x Major Group",
        "period": "FY2017 - FY2024",
        "stores": 30,
        "columns": [
            ("Store", "TEXT", "Store name"),
            ("Week", "DATE", "Week ending date"),
            ("Department", "TEXT", "Department name"),
            ("MajorGroup", "TEXT", "Major group name"),
            ("Revenue", "FLOAT", "Weekly revenue"),
            ("COGS", "FLOAT", "Cost of goods sold"),
            ("GP", "FLOAT", "Gross profit"),
        ],
        "used_by": ["Sales", "Profitability",
                     "Customers", "Market Share"],
        "join_key": "Store + Week + Department",
    },
    {
        "name": "Fiscal Calendar",
        "type": "Parquet",
        "size": "165 KB",
        "rows": "4,018",
        "source": "Financial_Calendar_Exported_2025-05-29.xlsx",
        "grain": "Daily (one row per calendar date)",
        "period": "FY2016 - FY2026",
        "stores": None,
        "columns": [
            ("TheDate", "DATE", "Calendar date (join key)"),
            ("FinYear", "INT", "Financial year"),
            ("FinMonthOfYearNo/Name", "INT/TEXT", "5-4-4 month"),
            ("FinWeekOfYearNo", "INT", "Week 1-53"),
            ("FinQuarterOfYearNo", "INT", "Quarter 1-4"),
            ("BusinessDay", "TEXT", "Y/N"),
            ("Weekend", "TEXT", "Y/N"),
            ("SeasonName", "TEXT", "Summer/Autumn/Winter/Spring"),
            ("DayOfWeekName", "TEXT", "Monday-Sunday"),
        ],
        "used_by": ["Store Ops", "Product Intel",
                     "Revenue Bridge", "Buying Hub"],
        "join_key": "CAST(SaleDate AS DATE) = TheDate",
    },
    {
        "name": "Hub Metadata",
        "type": "SQLite",
        "size": "< 1 MB",
        "rows": "Variable",
        "source": "hub_data.db (auto-initialized)",
        "grain": "Various (modules, lessons, roles, prompts)",
        "period": "Current",
        "stores": None,
        "columns": [
            ("learning_modules", "TABLE", "12 modules (L1-L4, D1-D4, K1-K4)"),
            ("lessons", "TABLE", "14 structured lessons"),
            ("employee_roles", "TABLE", "211 roles (3 Functions, 36 Depts)"),
            ("user_progress", "TABLE", "Per-user module completion"),
            ("prompt_templates", "TABLE", "Saved analytical prompts"),
            ("knowledge_base", "TABLE", "Extracted policy documents (FTS5)"),
            ("chat_messages", "TABLE", "Hub Assistant conversation history"),
        ],
        "used_by": ["Learning Centre", "Hub Assistant",
                     "Prompt Builder", "The Rubric"],
        "join_key": "Various internal keys",
    },
]


def get_data_sources():
    """Return structured list of all data sources."""
    return DATA_SOURCES


# ---------------------------------------------------------------------------
# GAMIFICATION CONSTANTS
# ---------------------------------------------------------------------------

MILESTONES = [
    {"code": "bronze", "name": "Bronze", "icon": "\U0001f949",
     "points": 500, "label": "Communicating Better"},
    {"code": "silver", "name": "Silver", "icon": "\U0001f948",
     "points": 2000, "label": "Symbiotic Partnership"},
    {"code": "gold", "name": "Gold", "icon": "\U0001f947",
     "points": 5000, "label": "Thought Completion Mastery"},
    {"code": "platinum", "name": "Platinum", "icon": "\U0001f48e",
     "points": 10000, "label": "Autonomous Collaboration"},
    {"code": "legend", "name": "Legend", "icon": "\U0001f3c6",
     "points": 25000, "label": "Human-AI Singularity"},
]

POINT_ACTIONS_AI = [
    {"action": "code_improvement", "points": 5,
     "label": "Successfully improves code"},
    {"action": "proactive_suggestion", "points": 10,
     "label": "Proactive suggestion accepted"},
    {"action": "autonomous_code", "points": 15,
     "label": "Autonomous code passes review"},
    {"action": "minimal_prompt", "points": 20,
     "label": "Feature from <10 word prompt"},
    {"action": "predicted_need", "points": 25,
     "label": "Predicted user need"},
]

POINT_ACTIONS_HUMAN = [
    {"action": "clearer_prompt", "points": 3,
     "label": "Clearer prompt than previous"},
    {"action": "shorter_prompt", "points": 5,
     "label": "Reduced prompt length"},
    {"action": "effective_shorthand", "points": 8,
     "label": "Used shorthand effectively"},
    {"action": "quick_validation", "points": 10,
     "label": "Validated AI code quickly"},
    {"action": "constructive_feedback", "points": 15,
     "label": "Feedback improved system"},
    {"action": "reusable_template", "points": 20,
     "label": "Created reusable template"},
]

SHOWCASE_IMPLEMENTATIONS = [
    {
        "name": "Transaction Query Engine",
        "desc": "41 pre-built DuckDB queries across 383M POS rows with "
                "dynamic filter placeholders for hierarchy, time, and fiscal "
                "dimensions.",
        "stats": "41 queries | 383M rows | <2s response",
        "dashboard": "Store Ops",
    },
    {
        "name": "Product Hierarchy",
        "desc": "5-level product taxonomy (72,911 SKUs) joined to POS "
                "transactions with 98.3% PLU match rate. Searchable filter "
                "with priority-ranked results.",
        "stats": "72,911 products | 5 levels | 98.3% match",
        "dashboard": "Store Ops",
    },
    {
        "name": "Fiscal Calendar",
        "desc": "Harris Farm's 5-4-4 retail calendar with 4,018 daily rows "
                "covering FY2016-2026. Enables fiscal period comparison, "
                "week-over-week analysis, and seasonal filtering.",
        "stats": "4,018 days | 45 columns | 5-4-4 pattern",
        "dashboard": "All Transaction dashboards",
    },
    {
        "name": "Multi-LLM Evaluation",
        "desc": "Side-by-side comparison of Claude, ChatGPT, and Grok "
                "responses with latency tracking, token counting, and "
                "Chairman's Decision voting.",
        "stats": "3 providers | async parallel | scored rubric",
        "dashboard": "The Rubric",
    },
    {
        "name": "Weather Demand Forecasting",
        "desc": "Per-store weather-driven demand adjustment with compound "
                "multipliers for 43 products across 5 stores. Configurable "
                "thresholds and lead-time alerts.",
        "stats": "43 products | 5 stores | 3-day forecast",
        "dashboard": "Standalone (harris_farm_weather/)",
    },
    {
        "name": "WATCHDOG Governance",
        "desc": "7 immutable laws, 2 scoring rubrics (code quality + design "
                "usability), SHA-256 integrity verification, structured audit "
                "trail, and automated security scanning.",
        "stats": "7 laws | 15 criteria | 898+ audit entries",
        "dashboard": "System-wide",
    },
    {
        "name": "Learning Centre",
        "desc": "12 structured learning modules across 3 pillars (AI Skills, "
                "Data Skills, Company Knowledge) with role-based priorities, "
                "practice challenges, and progress tracking.",
        "stats": "12 modules | 14 lessons | 9 challenges",
        "dashboard": "Learning Centre",
    },
    {
        "name": "Knowledge Base",
        "desc": "FTS5-indexed document repository extracted from Harris Farm "
                "policy documents. Powers the Hub Assistant chatbot with "
                "BM25-ranked context retrieval.",
        "stats": "FTS5 search | BM25 ranking | multi-LLM",
        "dashboard": "Hub Assistant",
    },
]
