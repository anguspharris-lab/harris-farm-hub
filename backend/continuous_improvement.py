"""
Harris Farm Hub — Continuous Improvement Agent
Automated codebase auditing across safety, documentation, performance,
and health dimensions. Generates trackable findings that can be promoted
to agent proposals.
"""

import ast
import hashlib
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..")
)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
DASHBOARDS_DIR = os.path.join(PROJECT_ROOT, "dashboards")
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
AUDIT_LOG = os.path.join(PROJECT_ROOT, "watchdog", "audit.log")
HUB_DB = os.path.join(os.path.dirname(__file__), "hub_data.db")


def _py_files(directory):
    """Yield .py file paths in a directory (non-recursive)."""
    if not os.path.isdir(directory):
        return
    for name in sorted(os.listdir(directory)):
        if name.endswith(".py") and not name.startswith("__"):
            yield os.path.join(directory, name)


def _relative(path):
    """Return path relative to PROJECT_ROOT."""
    try:
        return os.path.relpath(path, PROJECT_ROOT)
    except ValueError:
        return path


# ---------------------------------------------------------------------------
# SAFETY PATTERNS (reused from watchdog_safety)
# ---------------------------------------------------------------------------

CREDENTIAL_PATTERNS = [
    r"password\s*=\s*['\"][^'\"]+['\"]",
    r"api_key\s*=\s*['\"][^'\"]+['\"]",
    r"secret\s*=\s*['\"][^'\"]+['\"]",
    r"token\s*=\s*['\"][A-Za-z0-9+/=]{20,}['\"]",
    r"AWS_SECRET",
    r"PRIVATE_KEY",
]

SQL_FORMAT_PATTERNS = [
    r'\.format\([^)]*\).*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)',
    r'(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP).*\.format\(',
    r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*\{',
]


# ============================================================================
# 1A: CODE SAFETY AUDITOR
# ============================================================================

class CodeSafetyAuditor:
    """AST + regex based code safety scanner."""

    def __init__(self, directories=None):
        self.directories = directories or [BACKEND_DIR, DASHBOARDS_DIR]

    def audit(self):
        """Run all safety checks. Returns list of finding dicts."""
        findings = []
        for directory in self.directories:
            for filepath in _py_files(directory):
                findings.extend(self._scan_file(filepath))
        return findings

    def _scan_file(self, filepath):
        """Scan a single Python file."""
        findings = []
        rel = _relative(filepath)

        # Read source
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
                lines = source.split("\n")
        except Exception:
            return findings

        # File length check
        if len(lines) > 500:
            findings.append({
                "category": "safety",
                "severity": "low",
                "file": rel,
                "line": 1,
                "title": "Large file ({} lines)".format(len(lines)),
                "detail": "Files over 500 lines are harder to maintain.",
                "recommendation": "Consider splitting into smaller modules.",
            })

        # AST analysis
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return findings

        findings.extend(self._ast_scan(tree, rel))

        # Regex: credentials
        for i, line in enumerate(lines, 1):
            for pattern in CREDENTIAL_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip .env loading patterns and os.getenv
                    if "os.getenv" in line or "load_dotenv" in line:
                        continue
                    findings.append({
                        "category": "safety",
                        "severity": "high",
                        "file": rel,
                        "line": i,
                        "title": "Potential hardcoded credential",
                        "detail": "Line may contain hardcoded secrets.",
                        "recommendation": "Use environment variables via .env.",
                    })

        # Regex: SQL string formatting
        for i, line in enumerate(lines, 1):
            for pattern in SQL_FORMAT_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "category": "safety",
                        "severity": "medium",
                        "file": rel,
                        "line": i,
                        "title": "SQL string formatting detected",
                        "detail": "SQL built with .format() or f-string.",
                        "recommendation": "Use parameterized queries (?, ?).",
                    })

        return findings

    def _ast_scan(self, tree, filepath):
        """AST-based checks."""
        findings = []

        for node in ast.walk(tree):
            # eval/exec calls
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("eval", "exec"):
                    findings.append({
                        "category": "safety",
                        "severity": "high",
                        "file": filepath,
                        "line": node.lineno,
                        "title": "{}() call detected".format(func.id),
                        "detail": "Dangerous built-in that executes arbitrary code.",
                        "recommendation": "Remove or replace with safe alternative.",
                    })
                # os.system()
                if (isinstance(func, ast.Attribute)
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "os"
                        and func.attr == "system"):
                    findings.append({
                        "category": "safety",
                        "severity": "high",
                        "file": filepath,
                        "line": node.lineno,
                        "title": "os.system() call detected",
                        "detail": "Shell command execution via os.system().",
                        "recommendation": "Use subprocess.run() with shell=False.",
                    })

            # Bare except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                findings.append({
                    "category": "safety",
                    "severity": "low",
                    "file": filepath,
                    "line": node.lineno,
                    "title": "Bare except clause",
                    "detail": "Catches all exceptions including SystemExit.",
                    "recommendation": "Catch specific exceptions (e.g. Exception).",
                })

            # Long functions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = node.end_lineno - node.lineno + 1
                if func_lines > 100:
                    findings.append({
                        "category": "safety",
                        "severity": "low",
                        "file": filepath,
                        "line": node.lineno,
                        "title": "Long function: {} ({} lines)".format(
                            node.name, func_lines),
                        "detail": "Functions over 100 lines are hard to test.",
                        "recommendation": "Extract helper functions.",
                    })

        return findings


# ============================================================================
# 1B: DOCUMENTATION AUDITOR
# ============================================================================

class DocumentationAuditor:
    """Checks documentation freshness and completeness."""

    def __init__(self, docs_dir=None, backend_dir=None, app_path=None):
        self.docs_dir = docs_dir or DOCS_DIR
        self.backend_dir = backend_dir or BACKEND_DIR
        self.app_path = app_path or os.path.join(BACKEND_DIR, "app.py")

    def audit(self):
        """Run all documentation checks."""
        findings = []
        findings.extend(self._check_staleness())
        findings.extend(self._check_missing_docstrings())
        findings.extend(self._check_broken_links())
        return findings

    def _check_staleness(self):
        """Flag docs older than 14 days."""
        findings = []
        if not os.path.isdir(self.docs_dir):
            return findings

        now = datetime.now().timestamp()
        threshold = 14 * 86400  # 14 days in seconds

        for name in sorted(os.listdir(self.docs_dir)):
            if not name.endswith(".md"):
                continue
            path = os.path.join(self.docs_dir, name)
            mtime = os.path.getmtime(path)
            age_days = int((now - mtime) / 86400)
            if age_days > 14:
                findings.append({
                    "category": "documentation",
                    "severity": "low",
                    "file": "docs/{}".format(name),
                    "line": 0,
                    "title": "Stale documentation ({} days)".format(age_days),
                    "detail": "File not updated in {} days.".format(age_days),
                    "recommendation": "Review and update if content is outdated.",
                })
        return findings

    def _check_missing_docstrings(self):
        """Scan backend modules for public functions without docstrings."""
        findings = []
        for filepath in _py_files(self.backend_dir):
            rel = _relative(filepath)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                tree = ast.parse(source)
            except Exception:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                # Skip private functions
                if node.name.startswith("_"):
                    continue
                # Check for docstring
                if (node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)):
                    continue
                findings.append({
                    "category": "documentation",
                    "severity": "low",
                    "file": rel,
                    "line": node.lineno,
                    "title": "Missing docstring: {}()".format(node.name),
                    "detail": "Public function lacks documentation.",
                    "recommendation": "Add a docstring explaining purpose and args.",
                })
        return findings

    def _check_broken_links(self):
        """Check internal markdown links in docs/."""
        findings = []
        if not os.path.isdir(self.docs_dir):
            return findings

        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

        for name in sorted(os.listdir(self.docs_dir)):
            if not name.endswith(".md"):
                continue
            path = os.path.join(self.docs_dir, name)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception:
                continue

            for i, line in enumerate(lines, 1):
                for match in link_pattern.finditer(line):
                    target = match.group(2)
                    # Skip external URLs and anchors
                    if target.startswith(("http://", "https://", "#", "mailto:")):
                        continue
                    # Resolve relative to docs dir or project root
                    if target.startswith("../"):
                        resolved = os.path.normpath(
                            os.path.join(self.docs_dir, target))
                    else:
                        resolved = os.path.normpath(
                            os.path.join(self.docs_dir, target))
                    if not os.path.exists(resolved):
                        findings.append({
                            "category": "documentation",
                            "severity": "medium",
                            "file": "docs/{}".format(name),
                            "line": i,
                            "title": "Broken link: {}".format(target),
                            "detail": "Link target does not exist.",
                            "recommendation": "Fix or remove broken link.",
                        })
        return findings


# ============================================================================
# 1C: PERFORMANCE AUDITOR
# ============================================================================

class PerformanceAuditor:
    """Detects common performance anti-patterns."""

    def __init__(self, directories=None):
        self.directories = directories or [BACKEND_DIR, DASHBOARDS_DIR]

    def audit(self):
        """Run all performance checks."""
        findings = []
        for directory in self.directories:
            for filepath in _py_files(directory):
                findings.extend(self._scan_file(filepath))
        return findings

    def _scan_file(self, filepath):
        """Scan a single Python file for performance issues."""
        findings = []
        rel = _relative(filepath)

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
                lines = source.split("\n")
        except Exception:
            return findings

        # Unbounded SELECT *
        select_star = re.compile(
            r'SELECT\s+\*\s+FROM\s+\w+(?!\s+.*LIMIT)', re.IGNORECASE)
        for i, line in enumerate(lines, 1):
            if select_star.search(line):
                # Skip if LIMIT appears later on same line
                if re.search(r'LIMIT\s+\d+', line, re.IGNORECASE):
                    continue
                findings.append({
                    "category": "performance",
                    "severity": "medium",
                    "file": rel,
                    "line": i,
                    "title": "Unbounded SELECT *",
                    "detail": "SELECT * without LIMIT can return huge result sets.",
                    "recommendation": "Add LIMIT clause or select specific columns.",
                })

        # N+1 pattern: loop with DB execute
        try:
            tree = ast.parse(source)
            findings.extend(self._check_n_plus_one(tree, rel))
        except SyntaxError:
            pass

        return findings

    def _check_n_plus_one(self, tree, filepath):
        """Detect for loops containing database execute calls."""
        findings = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.For):
                continue
            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                func = child.func
                if (isinstance(func, ast.Attribute)
                        and func.attr == "execute"
                        and child is not node):
                    findings.append({
                        "category": "performance",
                        "severity": "medium",
                        "file": filepath,
                        "line": node.lineno,
                        "title": "Potential N+1 query pattern",
                        "detail": "Database execute() inside a for loop.",
                        "recommendation": "Batch queries or use JOINs instead.",
                    })
                    break  # One finding per loop
        return findings


# ============================================================================
# 1D: HEALTH METRICS COLLECTOR
# ============================================================================

class HealthMetricsCollector:
    """Gathers system health data from filesystem and DB."""

    def __init__(self, project_root=None, db_path=None):
        self.project_root = project_root or PROJECT_ROOT
        self.db_path = db_path or HUB_DB

    def collect(self):
        """Return dict of health metrics."""
        return {
            "file_counts": self._count_files(),
            "test_count": self._count_tests(),
            "table_count": self._count_tables(),
            "total_lines": self._count_lines(),
            "endpoint_count": self._count_endpoints(),
            "last_audit": self._last_audit_timestamp(),
            "collected_at": datetime.now().isoformat(),
        }

    def _count_files(self):
        """Count .py files in key directories."""
        counts = {}
        for name, subdir in [("backend", "backend"),
                              ("dashboards", "dashboards"),
                              ("tests", "tests")]:
            dirpath = os.path.join(self.project_root, subdir)
            if os.path.isdir(dirpath):
                counts[name] = len([f for f in os.listdir(dirpath)
                                     if f.endswith(".py")])
            else:
                counts[name] = 0
        return counts

    def _count_tests(self):
        """Count test functions across tests/*.py."""
        tests_dir = os.path.join(self.project_root, "tests")
        count = 0
        if not os.path.isdir(tests_dir):
            return count
        test_pattern = re.compile(r'^\s*def (test_\w+)')
        for name in os.listdir(tests_dir):
            if not name.endswith(".py"):
                continue
            try:
                with open(os.path.join(tests_dir, name), "r",
                          encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if test_pattern.match(line):
                            count += 1
            except Exception:
                pass
        return count

    def _count_tables(self):
        """Count tables in hub_data.db."""
        if not os.path.exists(self.db_path):
            return 0
        try:
            conn = sqlite3.connect(self.db_path)
            count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    def _count_lines(self):
        """Count total lines in backend + dashboards."""
        total = 0
        for subdir in ["backend", "dashboards"]:
            dirpath = os.path.join(self.project_root, subdir)
            if not os.path.isdir(dirpath):
                continue
            for name in os.listdir(dirpath):
                if not name.endswith(".py"):
                    continue
                try:
                    with open(os.path.join(dirpath, name), "r",
                              encoding="utf-8", errors="ignore") as f:
                        total += sum(1 for _ in f)
                except Exception:
                    pass
        return total

    def _count_endpoints(self):
        """Count @app.get/post decorators in app.py."""
        app_path = os.path.join(self.project_root, "backend", "app.py")
        if not os.path.exists(app_path):
            return 0
        pattern = re.compile(r'@app\.(get|post|put|delete|patch)\(')
        count = 0
        try:
            with open(app_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if pattern.search(line):
                        count += 1
        except Exception:
            pass
        return count

    def _last_audit_timestamp(self):
        """Read last timestamp from audit.log."""
        audit_path = os.path.join(self.project_root, "watchdog", "audit.log")
        if not os.path.exists(audit_path):
            return None
        try:
            with open(audit_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            if not lines:
                return None
            # Search backwards for timestamp
            ts_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2})')
            for line in reversed(lines):
                m = ts_pattern.search(line)
                if m:
                    return m.group(1)
        except Exception:
            pass
        return None


# ============================================================================
# 1E: FINDINGS MANAGER
# ============================================================================

class FindingsManager:
    """Manages the improvement_findings table."""

    def __init__(self, db_path=None):
        self.db_path = db_path or HUB_DB

    def store_findings(self, findings):
        """Bulk insert findings, deduplicating by content_hash.

        Returns count of newly inserted findings.
        """
        conn = sqlite3.connect(self.db_path)
        inserted = 0
        for f in findings:
            content_hash = self._hash_finding(f)
            try:
                conn.execute(
                    "INSERT INTO improvement_findings "
                    "(category, severity, file_path, line_number, title, "
                    "detail, recommendation, content_hash) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (
                        f.get("category", ""),
                        f.get("severity", "low"),
                        f.get("file", ""),
                        f.get("line", 0),
                        f.get("title", ""),
                        f.get("detail", ""),
                        f.get("recommendation", ""),
                        content_hash,
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                # Duplicate — already exists
                pass
        conn.commit()
        conn.close()
        return inserted

    def get_findings(self, status=None, category=None, limit=50):
        """Query findings with optional filters."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM improvement_findings WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()

    def update_status(self, finding_id, new_status):
        """Update finding status (open -> acknowledged -> resolved | promoted)."""
        valid = ("open", "acknowledged", "resolved", "promoted")
        if new_status not in valid:
            return {"error": "Invalid status. Must be one of: {}".format(
                ", ".join(valid))}

        conn = sqlite3.connect(self.db_path)
        resolved_at = datetime.now().isoformat() if new_status in (
            "resolved", "promoted") else None
        conn.execute(
            "UPDATE improvement_findings SET status = ?, resolved_at = ? "
            "WHERE id = ?",
            (new_status, resolved_at, finding_id),
        )
        conn.commit()
        changed = conn.total_changes
        conn.close()
        return {"finding_id": finding_id, "status": new_status,
                "updated": changed > 0}

    def promote_to_proposal(self, finding_id):
        """Create an agent_proposal from a finding."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM improvement_findings WHERE id = ?",
            (finding_id,),
        ).fetchone()
        if not row:
            conn.close()
            return {"error": "Finding not found"}

        finding = dict(row)
        # Create proposal
        conn.execute(
            "INSERT INTO agent_proposals "
            "(agent_name, task_type, description, risk_level, status) "
            "VALUES (?,?,?,?,?)",
            (
                "ContinuousImprovement",
                "IMPROVEMENT",
                "[CI Finding] {}: {}".format(
                    finding["title"], finding["detail"]),
                "LOW" if finding["severity"] == "low" else "MEDIUM",
                "PENDING",
            ),
        )
        # Mark finding as promoted
        conn.execute(
            "UPDATE improvement_findings SET status = 'promoted', "
            "resolved_at = ? WHERE id = ?",
            (datetime.now().isoformat(), finding_id),
        )
        conn.commit()
        conn.close()
        return {"finding_id": finding_id, "status": "promoted",
                "proposal_created": True}

    def _hash_finding(self, finding):
        """Generate deduplication hash from file + line + title."""
        raw = "{}:{}:{}".format(
            finding.get("file", ""),
            finding.get("line", 0),
            finding.get("title", ""),
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ============================================================================
# 1F: FULL AUDIT ORCHESTRATOR
# ============================================================================

def run_full_audit(db_path=None):
    """Run all auditors and store findings. Returns summary dict."""
    safety = CodeSafetyAuditor()
    docs = DocumentationAuditor()
    perf = PerformanceAuditor()
    health = HealthMetricsCollector()

    all_findings = []
    all_findings.extend(safety.audit())
    all_findings.extend(docs.audit())
    all_findings.extend(perf.audit())

    health_metrics = health.collect()

    # Store findings
    manager = FindingsManager(db_path=db_path)
    new_count = manager.store_findings(all_findings)

    # Categorize
    by_category = {}
    by_severity = {}
    for f in all_findings:
        cat = f.get("category", "other")
        sev = f.get("severity", "low")
        by_category[cat] = by_category.get(cat, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1

    return {
        "timestamp": datetime.now().isoformat(),
        "findings_count": len(all_findings),
        "by_category": by_category,
        "by_severity": by_severity,
        "health_metrics": health_metrics,
        "new_findings": new_count,
        "findings": all_findings,
    }
