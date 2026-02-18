#!/usr/bin/env python3
"""Harris Farm Hub — WATCHDOG Dashboard Scanner

Statically analyses Streamlit dashboard files for:
- Nested expander violations (including cross-function detection)
- Component inventory (tabs, buttons, inputs, selectors)
- API call extraction
- Report generation

Usage:
    python3 scripts/watchdog.py                           # Full scan, all dashboards
    python3 scripts/watchdog.py --check dashboards/X.py   # Scan a single file
    python3 scripts/watchdog.py --report                   # Write report to watchdog/scan_report.md
    python3 scripts/watchdog.py --stubs                    # Generate test stubs for uncovered components
"""

import argparse
import ast
import os
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# AST VISITORS
# ---------------------------------------------------------------------------

def _is_st_call(node, method_name):
    """Check if an AST node is a call to st.<method_name>()."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    # st.method_name(...)
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return func.value.id == "st" and func.attr == method_name
    return False


def _is_any_st_call(node):
    """Check if an AST node is any st.*() call. Returns method name or None."""
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        if func.value.id == "st":
            return func.attr
    return None


def _get_string_arg(node):
    """Extract the first string argument from a call node, if any."""
    if not isinstance(node, ast.Call):
        return None
    for arg in node.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    return None


def _get_keyword_arg(node, keyword):
    """Extract a keyword argument value from a call node."""
    if not isinstance(node, ast.Call):
        return None
    for kw in node.keywords:
        if kw.arg == keyword and isinstance(kw.value, ast.Constant):
            return kw.value.value
    return None


class FunctionExpanderScanner(ast.NodeVisitor):
    """First pass: identify which function definitions contain st.expander calls."""

    def __init__(self):
        self.functions_with_expander = set()
        self._current_function = None

    def visit_FunctionDef(self, node):
        old = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old

    def visit_With(self, node):
        if self._current_function:
            for item in node.items:
                if _is_st_call(item.context_expr, "expander"):
                    self.functions_with_expander.add(self._current_function)
        self.generic_visit(node)

    def visit_Call(self, node):
        if self._current_function and _is_st_call(node, "expander"):
            self.functions_with_expander.add(self._current_function)
        self.generic_visit(node)


class StreamlitVisitor(ast.NodeVisitor):
    """Main visitor: collects components, detects nested expanders."""

    def __init__(self, functions_with_expander=None):
        self.functions_with_expander = functions_with_expander or set()
        self.components = []    # [{type, line, label, key}]
        self.issues = []        # [{type, line, detail}]
        self.api_calls = []     # [{line, path}]
        self.page_config = {}   # {title, port, icon}
        self._expander_depth = 0
        self._expander_stack = []  # [(line, label)]

    def _record_component(self, comp_type, line, label=None, key=None):
        self.components.append({
            "type": comp_type,
            "line": line,
            "label": label,
            "key": key,
        })

    def visit_Call(self, node):
        st_method = _is_any_st_call(node)
        if st_method:
            label = _get_string_arg(node)
            key = _get_keyword_arg(node, "key")
            line = node.lineno

            if st_method == "set_page_config":
                self.page_config["title"] = _get_keyword_arg(node, "page_title") or ""
                self.page_config["icon"] = _get_keyword_arg(node, "page_icon") or ""

            elif st_method == "tabs":
                # Extract tab names from list argument
                tab_names = []
                if node.args and isinstance(node.args[0], ast.List):
                    for elt in node.args[0].elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            tab_names.append(elt.value)
                self._record_component("tabs", line, label=", ".join(tab_names))

            elif st_method in ("button", "selectbox", "radio", "text_input",
                               "text_area", "slider", "multiselect", "checkbox",
                               "number_input", "date_input", "file_uploader"):
                self._record_component(st_method, line, label=label, key=key)

            elif st_method == "expander":
                self._record_component("expander", line, label=label, key=key)

        # Check for API calls: api_get("path"), api_post("path"), requests.get/post
        if isinstance(node, ast.Call):
            func = node.func
            path = _get_string_arg(node)
            if path and isinstance(func, ast.Name) and func.id in ("api_get", "api_post"):
                self.api_calls.append({"line": node.lineno, "path": path})
            elif path and isinstance(func, ast.Attribute):
                if (isinstance(func.value, ast.Name) and
                        func.value.id == "requests" and
                        func.attr in ("get", "post")):
                    self.api_calls.append({"line": node.lineno, "path": path})

        # Check cross-function nesting: function call inside expander that itself has expander
        if self._expander_depth > 0 and isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in self.functions_with_expander:
                parent_line, parent_label = self._expander_stack[-1]
                self.issues.append({
                    "type": "nested_expander",
                    "line": node.lineno,
                    "detail": (
                        f"Function '{func.id}()' (which contains st.expander) "
                        f"is called inside st.expander at line {parent_line}"
                        f" ({parent_label!r})"
                    ),
                })

        self.generic_visit(node)

    def visit_With(self, node):
        is_expander = False
        expander_label = None
        expander_line = node.lineno

        for item in node.items:
            if _is_st_call(item.context_expr, "expander"):
                is_expander = True
                expander_label = _get_string_arg(item.context_expr)

        if is_expander:
            if self._expander_depth > 0:
                parent_line, parent_label = self._expander_stack[-1]
                self.issues.append({
                    "type": "nested_expander",
                    "line": expander_line,
                    "detail": (
                        f"st.expander({expander_label!r}) nested inside "
                        f"st.expander at line {parent_line} ({parent_label!r})"
                    ),
                })
            self._expander_depth += 1
            self._expander_stack.append((expander_line, expander_label))

        self.generic_visit(node)

        if is_expander:
            self._expander_depth -= 1
            self._expander_stack.pop()


# ---------------------------------------------------------------------------
# SCANNER
# ---------------------------------------------------------------------------

def scan_file(file_path):
    """Scan a single Python file. Returns a dict with components, issues, etc."""
    path = Path(file_path)
    result = {
        "file": str(path),
        "name": path.stem,
        "exists": path.exists(),
        "components": [],
        "issues": [],
        "api_calls": [],
        "page_config": {},
        "line_count": 0,
    }

    if not path.exists() or not path.suffix == ".py":
        return result

    source = path.read_text()
    result["line_count"] = len(source.splitlines())

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        result["issues"].append({
            "type": "syntax_error",
            "line": e.lineno or 0,
            "detail": str(e),
        })
        return result

    # First pass: find functions that contain st.expander
    func_scanner = FunctionExpanderScanner()
    func_scanner.visit(tree)

    # Second pass: full component scan + nesting detection
    visitor = StreamlitVisitor(func_scanner.functions_with_expander)
    visitor.visit(tree)

    result["components"] = visitor.components
    result["issues"] = visitor.issues
    result["api_calls"] = visitor.api_calls
    result["page_config"] = visitor.page_config

    return result


def scan_all_dashboards(dashboards_dir):
    """Scan all .py files in the dashboards directory."""
    results = []
    dash_path = Path(dashboards_dir)
    if not dash_path.is_dir():
        return results

    for py_file in sorted(dash_path.glob("*.py")):
        if py_file.name.startswith("__"):
            continue
        results.append(scan_file(py_file))

    return results


# ---------------------------------------------------------------------------
# REPORT GENERATION
# ---------------------------------------------------------------------------

def generate_report(results):
    """Generate a markdown scan report."""
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    total_components = sum(len(r["components"]) for r in results)
    total_issues = sum(len(r["issues"]) for r in results)
    critical = sum(
        1 for r in results for i in r["issues"] if i["type"] == "nested_expander"
    )

    lines = [
        "# WATCHDOG Dashboard Scan Report",
        f"Generated: {now}",
        "",
        "## Summary",
        f"- Dashboards scanned: {len(results)}",
        f"- Total components: {total_components}",
        f"- Total issues: {total_issues}",
        f"- Critical (nested expanders): {critical}",
        "",
    ]

    # Issues section
    if total_issues > 0:
        lines.append("## Issues")
        lines.append("")
        for r in results:
            for issue in r["issues"]:
                severity = "CRITICAL" if issue["type"] == "nested_expander" else "WARNING"
                lines.append(
                    f"- **{severity}**: {r['name']}.py:{issue['line']} — "
                    f"{issue['detail']}"
                )
        lines.append("")
    else:
        lines.append("## Issues")
        lines.append("No issues found.")
        lines.append("")

    # Per-dashboard inventory
    lines.append("## Component Inventory")
    lines.append("")

    for r in results:
        if not r["components"]:
            continue
        title = r["page_config"].get("title", r["name"])
        lines.append(f"### {r['name']}.py ({r['line_count']} lines)")
        if title:
            lines.append(f"Page title: {title}")
        lines.append("")

        # Group by type
        by_type = {}
        for comp in r["components"]:
            by_type.setdefault(comp["type"], []).append(comp)

        for ctype, comps in sorted(by_type.items()):
            if ctype == "tabs":
                for c in comps:
                    lines.append(f"- **Tabs** (line {c['line']}): {c['label']}")
            else:
                lines.append(f"- **{ctype}**: {len(comps)} instance(s)")
                for c in comps[:5]:  # Show first 5
                    detail = f"line {c['line']}"
                    if c.get("key"):
                        detail += f", key={c['key']!r}"
                    if c.get("label"):
                        detail += f": {c['label'][:50]}"
                    lines.append(f"  - {detail}")
                if len(comps) > 5:
                    lines.append(f"  - ... and {len(comps) - 5} more")

        if r["api_calls"]:
            unique_paths = sorted(set(c["path"] for c in r["api_calls"]))
            lines.append(f"- **API calls**: {len(unique_paths)} endpoint(s)")
            for p in unique_paths:
                lines.append(f"  - {p}")

        lines.append("")

    return "\n".join(lines)


def generate_stubs(results):
    """Generate pytest test stubs for components that may lack coverage."""
    lines = [
        '"""',
        "Auto-generated test stubs from WATCHDOG dashboard scanner.",
        f"Generated: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}",
        "",
        "These stubs identify testable components. Implement as needed.",
        '"""',
        "",
        "import sys",
        "from pathlib import Path",
        "",
        "import pytest",
        "",
        "sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))",
        "",
    ]

    for r in results:
        if not r["components"]:
            continue

        class_name = "Test" + "".join(
            w.capitalize() for w in r["name"].replace("_", " ").split()
        )

        lines.append(f"class {class_name}:")
        lines.append(f'    """Component stubs for {r["name"]}.py."""')
        lines.append("")

        buttons = [c for c in r["components"] if c["type"] == "button"]
        for btn in buttons:
            key = btn.get("key", "unknown")
            label = btn.get("label", "button")
            safe_name = key.replace("-", "_").replace(" ", "_") if key else "unnamed"
            lines.append(f"    def test_button_{safe_name}(self):")
            lines.append(f'        """Verify button at line {btn["line"]}: {label}"""')
            lines.append("        pass  # TODO: implement")
            lines.append("")

        selectboxes = [c for c in r["components"] if c["type"] == "selectbox"]
        for sb in selectboxes:
            key = sb.get("key", "unknown")
            safe_name = key.replace("-", "_").replace(" ", "_") if key else "unnamed"
            lines.append(f"    def test_selectbox_{safe_name}(self):")
            lines.append(f'        """Verify selectbox at line {sb["line"]}"""')
            lines.append("        pass  # TODO: implement")
            lines.append("")

        if not buttons and not selectboxes:
            lines.append("    def test_placeholder(self):")
            lines.append("        pass  # No interactive components to stub")
            lines.append("")

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="WATCHDOG Dashboard Scanner — static analysis for Streamlit apps"
    )
    parser.add_argument(
        "--check", type=str, default=None,
        help="Scan a single file (path relative to project root)"
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Write scan report to watchdog/scan_report.md"
    )
    parser.add_argument(
        "--stubs", action="store_true",
        help="Generate test stubs for uncovered components"
    )
    parser.add_argument(
        "--dashboards-dir", type=str, default=None,
        help="Path to dashboards directory (default: auto-detect)"
    )

    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    dash_dir = args.dashboards_dir or str(project_root / "dashboards")

    if args.check:
        # Single file scan
        target = Path(args.check)
        if not target.is_absolute():
            target = project_root / target
        result = scan_file(target)
        results = [result]

        print(f"Scanning: {target}")
        print(f"  Lines: {result['line_count']}")
        print(f"  Components: {len(result['components'])}")
        print(f"  API calls: {len(result['api_calls'])}")

        if result["issues"]:
            print(f"\n  ISSUES FOUND: {len(result['issues'])}")
            for issue in result["issues"]:
                severity = "CRITICAL" if issue["type"] == "nested_expander" else "WARNING"
                print(f"    [{severity}] Line {issue['line']}: {issue['detail']}")
            sys.exit(1)
        else:
            print("\n  No issues found.")
            sys.exit(0)
    else:
        # Full scan
        results = scan_all_dashboards(dash_dir)
        total_issues = sum(len(r["issues"]) for r in results)

        print(f"Scanned {len(results)} dashboard files in {dash_dir}")
        print(f"Total components: {sum(len(r['components']) for r in results)}")
        print(f"Total issues: {total_issues}")

        if total_issues > 0:
            print("\nISSUES:")
            for r in results:
                for issue in r["issues"]:
                    severity = "CRITICAL" if issue["type"] == "nested_expander" else "WARNING"
                    print(f"  [{severity}] {r['name']}.py:{issue['line']} — {issue['detail']}")

    if args.report:
        report = generate_report(results)
        report_path = project_root / "watchdog" / "scan_report.md"
        report_path.write_text(report)
        print(f"\nReport written to: {report_path}")

    if args.stubs:
        stubs = generate_stubs(results)
        print("\n--- TEST STUBS ---")
        print(stubs)

    if any(len(r["issues"]) > 0 for r in results):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
