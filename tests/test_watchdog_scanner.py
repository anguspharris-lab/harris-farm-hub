"""Tests for scripts/watchdog.py — WATCHDOG Dashboard Scanner."""

import sys
import textwrap
import tempfile
from pathlib import Path

import pytest

# Ensure scripts directory is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from watchdog import (
    scan_file,
    scan_all_dashboards,
    generate_report,
    generate_stubs,
    FunctionExpanderScanner,
    StreamlitVisitor,
)

PROJECT_ROOT = Path(__file__).parent.parent


# ============================================================================
# NESTED EXPANDER DETECTION
# ============================================================================

class TestNestedExpanderDetection:
    """Test that the scanner detects nested st.expander violations."""

    def test_detects_direct_nesting(self, tmp_path):
        """A file with directly nested expanders triggers a violation."""
        code = textwrap.dedent("""\
            import streamlit as st
            with st.expander("Outer"):
                st.write("hello")
                with st.expander("Inner"):
                    st.write("nested")
        """)
        f = tmp_path / "nested.py"
        f.write_text(code)
        result = scan_file(str(f))
        assert len(result["issues"]) >= 1
        assert result["issues"][0]["type"] == "nested_expander"
        assert "Inner" in result["issues"][0]["detail"]

    def test_detects_cross_function_nesting(self, tmp_path):
        """Function called inside expander that itself contains expander is caught."""
        code = textwrap.dedent("""\
            import streamlit as st

            def my_render():
                with st.expander("Hints"):
                    st.write("hint")

            with st.expander("Module"):
                my_render()
        """)
        f = tmp_path / "cross_func.py"
        f.write_text(code)
        result = scan_file(str(f))
        assert len(result["issues"]) >= 1
        assert "my_render" in result["issues"][0]["detail"]
        assert result["issues"][0]["type"] == "nested_expander"

    def test_clean_file_passes(self, tmp_path):
        """A file with no nesting passes without issues."""
        code = textwrap.dedent("""\
            import streamlit as st
            with st.expander("First"):
                st.write("one")
            with st.expander("Second"):
                st.write("two")
        """)
        f = tmp_path / "clean.py"
        f.write_text(code)
        result = scan_file(str(f))
        assert len(result["issues"]) == 0

    def test_function_without_expander_in_expander_is_ok(self, tmp_path):
        """Calling a non-expander function inside an expander is fine."""
        code = textwrap.dedent("""\
            import streamlit as st

            def safe_render():
                st.write("no expander here")

            with st.expander("Module"):
                safe_render()
        """)
        f = tmp_path / "safe_func.py"
        f.write_text(code)
        result = scan_file(str(f))
        assert len(result["issues"]) == 0


# ============================================================================
# COMPONENT INVENTORY
# ============================================================================

class TestComponentInventory:
    """Test that the scanner correctly inventories Streamlit components."""

    def test_counts_tabs(self, tmp_path):
        """Scanner finds st.tabs and extracts tab names."""
        code = textwrap.dedent("""\
            import streamlit as st
            t1, t2, t3 = st.tabs(["Alpha", "Beta", "Gamma"])
        """)
        f = tmp_path / "tabs.py"
        f.write_text(code)
        result = scan_file(str(f))
        tabs = [c for c in result["components"] if c["type"] == "tabs"]
        assert len(tabs) == 1
        assert "Alpha" in tabs[0]["label"]
        assert "Beta" in tabs[0]["label"]
        assert "Gamma" in tabs[0]["label"]

    def test_counts_buttons(self, tmp_path):
        """Scanner finds buttons with keys."""
        code = textwrap.dedent("""\
            import streamlit as st
            st.button("Click me", key="btn1")
            st.button("Another", key="btn2")
        """)
        f = tmp_path / "buttons.py"
        f.write_text(code)
        result = scan_file(str(f))
        buttons = [c for c in result["components"] if c["type"] == "button"]
        assert len(buttons) == 2
        keys = {b["key"] for b in buttons}
        assert "btn1" in keys
        assert "btn2" in keys

    def test_extracts_api_calls(self, tmp_path):
        """Scanner finds api_get/api_post calls."""
        code = textwrap.dedent("""\
            import streamlit as st
            def api_get(path, params=None):
                pass
            api_get("/api/learning/modules")
            api_get("/api/learning/progress/user1")
        """)
        f = tmp_path / "api.py"
        f.write_text(code)
        result = scan_file(str(f))
        paths = [c["path"] for c in result["api_calls"]]
        assert "/api/learning/modules" in paths
        assert "/api/learning/progress/user1" in paths

    def test_extracts_page_config(self, tmp_path):
        """Scanner extracts page_title from st.set_page_config."""
        code = textwrap.dedent("""\
            import streamlit as st
            st.set_page_config(page_title="My Dashboard", page_icon="icon")
        """)
        f = tmp_path / "config.py"
        f.write_text(code)
        result = scan_file(str(f))
        assert result["page_config"]["title"] == "My Dashboard"

    def test_counts_interactive_elements(self, tmp_path):
        """Scanner finds selectbox, radio, text_input, text_area."""
        code = textwrap.dedent("""\
            import streamlit as st
            st.selectbox("Pick one", [1, 2, 3], key="sel1")
            st.radio("Choose", ["A", "B"], key="rad1")
            st.text_input("Name", key="name")
            st.text_area("Story", key="story")
            st.slider("Range", key="slider1")
        """)
        f = tmp_path / "inputs.py"
        f.write_text(code)
        result = scan_file(str(f))
        types = [c["type"] for c in result["components"]]
        assert "selectbox" in types
        assert "radio" in types
        assert "text_input" in types
        assert "text_area" in types
        assert "slider" in types


# ============================================================================
# REAL DASHBOARD SCANNING
# ============================================================================

class TestRealDashboards:
    """Test scanner against actual project dashboards."""

    def test_learning_centre_has_no_issues(self):
        """The refactored learning_centre.py should have zero issues."""
        lc_path = PROJECT_ROOT / "dashboards" / "learning_centre.py"
        if not lc_path.exists():
            pytest.skip("learning_centre.py not found")
        result = scan_file(str(lc_path))
        assert len(result["issues"]) == 0, (
            f"Found issues: {result['issues']}"
        )

    def test_scan_all_dashboards_returns_results(self):
        """Scanning the full dashboards directory returns results."""
        dash_dir = PROJECT_ROOT / "dashboards"
        if not dash_dir.is_dir():
            pytest.skip("dashboards/ not found")
        results = scan_all_dashboards(str(dash_dir))
        assert len(results) > 0
        # Every result should have required keys
        for r in results:
            assert "file" in r
            assert "components" in r
            assert "issues" in r


# ============================================================================
# REPORT GENERATION
# ============================================================================

class TestReportGeneration:
    """Test the markdown report generator."""

    def test_report_is_markdown(self):
        """Generated report starts with markdown heading."""
        results = [{"file": "test.py", "name": "test", "line_count": 10,
                     "components": [], "issues": [], "api_calls": [],
                     "page_config": {}}]
        report = generate_report(results)
        assert report.startswith("# WATCHDOG Dashboard Scan Report")

    def test_report_includes_issues(self, tmp_path):
        """Report includes CRITICAL issues when present."""
        code = textwrap.dedent("""\
            import streamlit as st
            with st.expander("Outer"):
                with st.expander("Inner"):
                    st.write("bad")
        """)
        f = tmp_path / "bad.py"
        f.write_text(code)
        result = scan_file(str(f))
        report = generate_report([result])
        assert "CRITICAL" in report
        assert "nested_expander" in report or "nested" in report.lower()

    def test_report_no_issues_message(self):
        """Report says 'No issues found' when clean."""
        results = [{"file": "clean.py", "name": "clean", "line_count": 5,
                     "components": [], "issues": [], "api_calls": [],
                     "page_config": {}}]
        report = generate_report(results)
        assert "No issues found" in report


# ============================================================================
# STUB GENERATION
# ============================================================================

class TestStubGeneration:
    """Test the test stub generator."""

    def test_stubs_are_valid_python(self, tmp_path):
        """Generated stubs should be parseable Python."""
        code = textwrap.dedent("""\
            import streamlit as st
            st.button("Click", key="btn1")
            st.selectbox("Choose", [1, 2], key="sel1")
        """)
        f = tmp_path / "stubtest.py"
        f.write_text(code)
        result = scan_file(str(f))
        stubs = generate_stubs([result])
        # Should parse without SyntaxError
        compile(stubs, "<stubs>", "exec")

    def test_stubs_contain_test_classes(self, tmp_path):
        """Generated stubs have test class for each dashboard."""
        code = textwrap.dedent("""\
            import streamlit as st
            st.button("Click", key="btn1")
        """)
        f = tmp_path / "my_dashboard.py"
        f.write_text(code)
        result = scan_file(str(f))
        stubs = generate_stubs([result])
        assert "class TestMyDashboard" in stubs
        assert "def test_button_btn1" in stubs


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_file(self, tmp_path):
        """Empty file does not crash the scanner."""
        f = tmp_path / "empty.py"
        f.write_text("")
        result = scan_file(str(f))
        assert result["line_count"] == 0
        assert len(result["components"]) == 0
        assert len(result["issues"]) == 0

    def test_non_streamlit_file(self, tmp_path):
        """Non-Streamlit Python file returns empty component list."""
        code = textwrap.dedent("""\
            import os
            x = 1 + 2
            print(x)
        """)
        f = tmp_path / "plain.py"
        f.write_text(code)
        result = scan_file(str(f))
        assert len(result["components"]) == 0
        assert len(result["issues"]) == 0

    def test_nonexistent_file(self):
        """Non-existent file returns gracefully."""
        result = scan_file("/nonexistent/path/file.py")
        assert result["exists"] is False
        assert len(result["components"]) == 0

    def test_syntax_error_file(self, tmp_path):
        """File with syntax error is flagged."""
        f = tmp_path / "broken.py"
        f.write_text("def broken(:\n    pass")
        result = scan_file(str(f))
        assert len(result["issues"]) >= 1
        assert result["issues"][0]["type"] == "syntax_error"
