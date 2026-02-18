"""Tests for Learning Centre — content integrity, database, and API endpoints."""

import ast
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from shared.learning_content import (
    MODULES,
    LESSONS,
    PILLARS,
    DIFFICULTY_META,
    ROLE_MAPPINGS,
    RUBRIC_EVALUATOR_PROMPT,
    get_role_priorities,
)

DASHBOARD_PATH = Path(__file__).parent.parent / "dashboards" / "learning_centre.py"


# ---------------------------------------------------------------------------
# MODULE CONTENT INTEGRITY
# ---------------------------------------------------------------------------

class TestModules:
    def test_twelve_modules(self):
        assert len(MODULES) == 12

    def test_unique_codes(self):
        codes = [m["code"] for m in MODULES]
        assert len(codes) == len(set(codes))

    def test_all_codes_present(self):
        codes = {m["code"] for m in MODULES}
        expected = {"L1", "L2", "L3", "L4", "D1", "D2", "D3", "D4",
                    "K1", "K2", "K3", "K4"}
        assert codes == expected

    def test_three_pillars(self):
        pillars = {m["pillar"] for m in MODULES}
        assert pillars == {"core_ai", "data", "knowledge"}

    def test_four_per_pillar(self):
        for pillar in ("core_ai", "data", "knowledge"):
            count = sum(1 for m in MODULES if m["pillar"] == pillar)
            assert count == 4, f"{pillar} should have 4 modules"

    def test_required_fields(self):
        required = {"code", "pillar", "name", "description", "duration_minutes",
                    "difficulty", "prerequisites", "sort_order"}
        for m in MODULES:
            assert required.issubset(m.keys()), f"{m['code']} missing fields"

    def test_valid_difficulties(self):
        valid = {"beginner", "intermediate", "advanced"}
        for m in MODULES:
            assert m["difficulty"] in valid, f"{m['code']} has invalid difficulty"

    def test_prerequisites_are_valid_json(self):
        for m in MODULES:
            prereqs = json.loads(m["prerequisites"])
            assert isinstance(prereqs, list)

    def test_prerequisites_reference_existing_codes(self):
        codes = {m["code"] for m in MODULES}
        for m in MODULES:
            prereqs = json.loads(m["prerequisites"])
            for p in prereqs:
                assert p in codes, f"{m['code']} has unknown prerequisite {p}"


# ---------------------------------------------------------------------------
# LESSON CONTENT INTEGRITY
# ---------------------------------------------------------------------------

class TestLessons:
    def test_at_least_one_per_module(self):
        module_codes = {m["code"] for m in MODULES}
        lesson_codes = {ls["module_code"] for ls in LESSONS}
        assert module_codes == lesson_codes, (
            f"Missing lessons for: {module_codes - lesson_codes}"
        )

    def test_required_fields(self):
        required = {"module_code", "lesson_number", "title", "content_type", "content"}
        for ls in LESSONS:
            assert required.issubset(ls.keys()), f"Lesson missing fields: {ls.get('title', '?')}"

    def test_content_is_valid_json(self):
        for ls in LESSONS:
            content = json.loads(ls["content"]) if isinstance(ls["content"], str) else ls["content"]
            assert "sections" in content, f"Lesson '{ls['title']}' missing sections"
            assert len(content["sections"]) > 0

    def test_lesson_numbers_start_at_one(self):
        for ls in LESSONS:
            assert ls["lesson_number"] >= 1

    def test_valid_content_types(self):
        valid = {"theory", "exercise", "quiz"}
        for ls in LESSONS:
            assert ls["content_type"] in valid


# ---------------------------------------------------------------------------
# PILLARS AND DIFFICULTY METADATA
# ---------------------------------------------------------------------------

class TestPillars:
    def test_three_pillars_defined(self):
        assert len(PILLARS) == 3
        assert set(PILLARS.keys()) == {"core_ai", "data", "knowledge"}

    def test_pillar_has_required_fields(self):
        for key, p in PILLARS.items():
            assert "name" in p
            assert "icon" in p
            assert "color" in p


class TestDifficultyMeta:
    def test_three_levels(self):
        assert set(DIFFICULTY_META.keys()) == {"beginner", "intermediate", "advanced"}


# ---------------------------------------------------------------------------
# ROLE MAPPINGS
# ---------------------------------------------------------------------------

class TestRoleMappings:
    def test_at_least_one_mapping(self):
        assert len(ROLE_MAPPINGS) >= 1

    def test_default_mapping_exists(self):
        defaults = [m for m in ROLE_MAPPINGS
                    if m["function"] is None and m["department_pattern"] is None]
        assert len(defaults) == 1, "Must have exactly one default mapping"

    def test_all_codes_in_mappings_are_valid(self):
        valid_codes = {m["code"] for m in MODULES}
        for mapping in ROLE_MAPPINGS:
            for priority in ("essential", "recommended", "optional"):
                for code in mapping[priority]:
                    assert code in valid_codes, f"Invalid code {code} in mapping"

    def test_get_role_priorities_retail_store_mgmt(self):
        result = get_role_priorities("Retail", "Store Management")
        assert "L1" in result["essential"]
        assert "K1" in result["essential"]

    def test_get_role_priorities_support_office_it(self):
        result = get_role_priorities("Support Office", "IT")
        assert "D1" in result["essential"]
        assert "D2" in result["essential"]

    def test_get_role_priorities_unknown_defaults(self):
        result = get_role_priorities("Unknown", "Unknown")
        assert "L1" in result["essential"]
        assert "K1" in result["essential"]

    def test_all_priority_levels_returned(self):
        result = get_role_priorities("Retail", "Service")
        assert "essential" in result
        assert "recommended" in result
        assert "optional" in result


# ---------------------------------------------------------------------------
# RUBRIC EVALUATOR PROMPT
# ---------------------------------------------------------------------------

class TestRubricEvaluator:
    def test_has_placeholder(self):
        assert "{user_prompt}" in RUBRIC_EVALUATOR_PROMPT

    def test_mentions_five_criteria(self):
        for criterion in ["REQUEST CLARITY", "CONTEXT PROVISION",
                          "DATA SPECIFICATION", "OUTPUT FORMAT", "ACTIONABILITY"]:
            assert criterion in RUBRIC_EVALUATOR_PROMPT

    def test_mentions_scoring(self):
        assert "1-5" in RUBRIC_EVALUATOR_PROMPT
        assert "25" in RUBRIC_EVALUATOR_PROMPT


# ---------------------------------------------------------------------------
# API ENDPOINTS (via test client)
# ---------------------------------------------------------------------------

class TestLearningAPI:
    @pytest.fixture
    def client(self, tmp_path):
        """FastAPI test client with seeded learning data."""
        from app import app, config, init_hub_database, seed_learning_data

        db_path = str(tmp_path / "test_learning.db")
        config.HUB_DB = db_path
        init_hub_database()
        seed_learning_data()

        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_get_all_modules(self, client):
        resp = client.get("/api/learning/modules")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 12

    def test_filter_by_pillar(self, client):
        resp = client.get("/api/learning/modules?pillar=core_ai")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 4
        assert all(m["pillar"] == "core_ai" for m in data["modules"])

    def test_filter_by_difficulty(self, client):
        resp = client.get("/api/learning/modules?difficulty=beginner")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0
        assert all(m["difficulty"] == "beginner" for m in data["modules"])

    def test_get_single_module(self, client):
        resp = client.get("/api/learning/modules/L1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "L1"
        assert "lessons" in data
        assert len(data["lessons"]) >= 1

    def test_get_module_not_found(self, client):
        resp = client.get("/api/learning/modules/X9")
        assert resp.status_code == 404

    def test_progress_empty(self, client):
        resp = client.get("/api/learning/progress/testuser")
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["completed"] == 0
        assert data["summary"]["total_modules"] == 12

    def test_update_progress(self, client):
        resp = client.post(
            "/api/learning/progress/testuser/L1",
            params={"status": "in_progress", "completion_pct": 50},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "updated"

        # Verify
        resp = client.get("/api/learning/progress/testuser")
        data = resp.json()
        assert data["summary"]["in_progress"] == 1

    def test_complete_module(self, client):
        client.post("/api/learning/progress/testuser/L1",
                     params={"status": "completed", "completion_pct": 100})
        resp = client.get("/api/learning/progress/testuser")
        data = resp.json()
        assert data["summary"]["completed"] == 1

    def test_invalid_status_rejected(self, client):
        resp = client.post(
            "/api/learning/progress/testuser/L1",
            params={"status": "invalid"},
        )
        assert resp.status_code == 400

    def test_recommended_modules(self, client):
        resp = client.get("/api/learning/recommended/Retail/Store Management/Supervisor")
        assert resp.status_code == 200
        data = resp.json()
        assert "essential" in data
        assert "recommended" in data
        assert "optional" in data
        assert len(data["essential"]) > 0

    def test_recommended_includes_role(self, client):
        resp = client.get("/api/learning/recommended/Retail/Service/Shop Assistant")
        data = resp.json()
        assert data["role"]["function"] == "Retail"
        assert data["role"]["department"] == "Service"


# ---------------------------------------------------------------------------
# STRUCTURAL VERIFICATION — NO NESTED EXPANDERS
# ---------------------------------------------------------------------------

class TestNoNestedExpanders:
    """AST-based verification that learning_centre.py has no nested expanders."""

    @pytest.fixture
    def tree(self):
        source = DASHBOARD_PATH.read_text()
        return ast.parse(source, filename=str(DASHBOARD_PATH))

    def test_no_direct_nested_expanders(self, tree):
        """Walk With nodes; no st.expander should be directly nested in another."""
        class NestChecker(ast.NodeVisitor):
            def __init__(self):
                self.depth = 0
                self.violations = []
            def visit_With(self, node):
                is_exp = any(
                    isinstance(item.context_expr, ast.Call)
                    and isinstance(getattr(item.context_expr, "func", None), ast.Attribute)
                    and getattr(item.context_expr.func, "attr", "") == "expander"
                    and isinstance(getattr(item.context_expr.func, "value", None), ast.Name)
                    and item.context_expr.func.value.id == "st"
                    for item in node.items
                )
                if is_exp:
                    if self.depth > 0:
                        self.violations.append(node.lineno)
                    self.depth += 1
                self.generic_visit(node)
                if is_exp:
                    self.depth -= 1

        checker = NestChecker()
        checker.visit(tree)
        assert checker.violations == [], (
            f"Nested expanders at lines: {checker.violations}"
        )

    def test_no_expander_wraps_render_lesson_content(self, tree):
        """render_lesson_content() must never be called inside st.expander."""
        class CallInExpanderChecker(ast.NodeVisitor):
            def __init__(self):
                self.in_expander = False
                self.violations = []
            def visit_With(self, node):
                is_exp = any(
                    isinstance(item.context_expr, ast.Call)
                    and isinstance(getattr(item.context_expr, "func", None), ast.Attribute)
                    and getattr(item.context_expr.func, "attr", "") == "expander"
                    and isinstance(getattr(item.context_expr.func, "value", None), ast.Name)
                    and item.context_expr.func.value.id == "st"
                    for item in node.items
                )
                old = self.in_expander
                if is_exp:
                    self.in_expander = True
                self.generic_visit(node)
                self.in_expander = old
            def visit_Call(self, node):
                if (self.in_expander
                        and isinstance(node.func, ast.Name)
                        and node.func.id == "render_lesson_content"):
                    self.violations.append(node.lineno)
                self.generic_visit(node)

        checker = CallInExpanderChecker()
        checker.visit(tree)
        assert checker.violations == [], (
            f"render_lesson_content called inside expander at lines: {checker.violations}"
        )


# ---------------------------------------------------------------------------
# CONTENT INTEGRATION
# ---------------------------------------------------------------------------

class TestContentIntegration:
    """Verify training_content.py is properly imported, not duplicated."""

    def test_building_blocks_available(self):
        """BUILDING_BLOCKS should be importable from training_content."""
        from shared.training_content import BUILDING_BLOCKS
        assert len(BUILDING_BLOCKS) == 5
        names = {b["name"] for b in BUILDING_BLOCKS}
        assert "Role" in names
        assert "Context" in names

    def test_challenges_available(self):
        """CHALLENGES dict should have difficulty keys."""
        from shared.training_content import CHALLENGES
        assert isinstance(CHALLENGES, dict)
        assert len(CHALLENGES) >= 2

    def test_no_content_duplication_in_dashboard(self):
        """Dashboard should import BUILDING_BLOCKS, not redefine them inline."""
        source = DASHBOARD_PATH.read_text()
        # The dashboard should import, not duplicate content
        assert "from shared.training_content import" in source
        # There should be no inline list defining all 5 building blocks
        assert source.count('"Role"') <= 2  # import reference + at most one display
        assert "BUILDING_BLOCKS = [" not in source

    def test_practice_lab_has_three_modes(self):
        """Practice Lab radio should offer 3 modes including Practice Challenges."""
        source = DASHBOARD_PATH.read_text()
        assert '"Practice Challenges"' in source
        assert '"Rubric Evaluator"' in source
        assert '"Prompt Sandbox"' in source


# ---------------------------------------------------------------------------
# GOAL TAB STRUCTURE
# ---------------------------------------------------------------------------

class TestGoalTabStructure:
    """Verify the 3-goal tab structure."""

    def test_tab_names_match_goals(self):
        """Tabs should be: My Dashboard, AI Prompting Skills, Data Prompting,
        Company Knowledge, Practice Lab."""
        source = DASHBOARD_PATH.read_text()
        assert '"AI Prompting Skills"' in source
        assert '"Data Prompting"' in source
        assert '"Company Knowledge"' in source
        assert '"My Dashboard"' in source
        assert '"Practice Lab"' in source

    def test_selectbox_navigation_not_expander(self):
        """Module navigation should use st.selectbox, not st.expander."""
        source = DASHBOARD_PATH.read_text()
        # render_module_tab uses selectbox for module selection
        assert "render_module_tab" in source
        # Verify the function exists and uses selectbox
        tree = ast.parse(source, filename=str(DASHBOARD_PATH))
        func_found = False
        uses_selectbox = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "render_module_tab":
                func_found = True
                for child in ast.walk(node):
                    if (isinstance(child, ast.Call)
                            and isinstance(getattr(child, "func", None), ast.Attribute)
                            and getattr(child.func, "attr", "") == "selectbox"
                            and isinstance(getattr(child.func, "value", None), ast.Name)
                            and child.func.value.id == "st"):
                        uses_selectbox = True
        assert func_found, "render_module_tab function not found"
        assert uses_selectbox, "render_module_tab should use st.selectbox for module navigation"
