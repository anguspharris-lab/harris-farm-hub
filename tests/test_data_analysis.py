"""
Tests for Data Analysis Engine, Report Generator, and Presentation Rubric.
Law 3: min 1 success + 1 failure per function.
"""

import json
import os
import sys
from datetime import datetime

import pytest

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboards'))

from data_analysis import (
    ANALYSIS_TYPES, _get_date_range, _build_result, _store_name,
)
from report_generator import (
    generate_markdown_report, generate_html_report,
    generate_csv_export, generate_json_export,
    _format_currency, _format_evidence_table_md,
    _format_evidence_table_html, _html_escape,
)
from presentation_rubric import (
    evaluate_report, grade_label, DIMENSIONS,
    _score_audience, _score_story, _score_action,
    _score_visual, _score_complete, _score_brief,
    _score_data, _score_honest,
)


# ---------------------------------------------------------------------------
# FIXTURES: Sample result dicts
# ---------------------------------------------------------------------------

@pytest.fixture
def complete_result():
    """A well-formed analysis result with all sections."""
    return {
        "analysis_type": "basket_analysis",
        "title": "Cross-sell Opportunities — Mosman (30 days)",
        "executive_summary": (
            "Analysed 28,503 baskets at Mosman over 30 days. Found 50 "
            "product pairs with lift > 1.0."
        ),
        "findings": [
            {"item_a": "100", "item_b": "200", "lift": 5.0},
            {"item_a": "300", "item_b": "400", "lift": 3.2},
        ],
        "evidence_tables": [{
            "name": "Top Product Pairs",
            "columns": ["Product A", "Product B", "Lift"],
            "rows": [
                ["Bananas", "Milk", "5.0"],
                ["Bread", "Butter", "3.2"],
                ["Apples", "Oranges", "2.8"],
                ["Cheese", "Wine", "2.5"],
                ["Pasta", "Sauce", "2.1"],
            ],
        }],
        "financial_impact": {
            "estimated_annual_value": 125000.0,
            "confidence": "medium",
            "basis": "Top 10 pairs lift-weighted",
        },
        "recommendations": [
            {"action": "Co-locate top products", "owner": "Store Manager",
             "timeline": "2 weeks", "priority": "high"},
            {"action": "Create bundles", "owner": "Category Manager",
             "timeline": "4 weeks", "priority": "medium"},
        ],
        "methodology": {
            "data_source": "POS Transactions (DuckDB/Parquet)",
            "query_window": "2026-01-15 to 2026-02-15",
            "records_analyzed": 28503,
            "limitations": [
                "Single store analysis",
                "Does not account for promotions",
                "Minimum support threshold",
            ],
            "sql_used": "Self-join on Reference2, CTE-based pair counting",
        },
        "confidence_level": 0.85,
        "generated_at": "2026-02-16T10:00:00",
    }


@pytest.fixture
def empty_result():
    """An empty analysis result (no findings)."""
    return {
        "analysis_type": "basket_analysis",
        "title": "Empty Analysis",
        "executive_summary": "",
        "findings": [],
        "evidence_tables": [],
        "financial_impact": {},
        "recommendations": [],
        "methodology": {},
        "confidence_level": 0.0,
        "generated_at": "2026-02-16T10:00:00",
    }


@pytest.fixture
def minimal_result():
    """A result with only the bare minimum fields."""
    return {
        "analysis_type": "demand_pattern",
        "title": "Minimal Report",
    }


# =========================================================================
# TEST: DATA ANALYSIS HELPERS
# =========================================================================

class TestAnalysisTypes:
    """Test the analysis type registry."""

    def test_analysis_types_count(self):
        assert len(ANALYSIS_TYPES) == 11

    def test_required_keys(self):
        for key, info in ANALYSIS_TYPES.items():
            assert "name" in info
            assert "agent_id" in info
            assert "description" in info

    def test_basket_analysis_exists(self):
        assert "basket_analysis" in ANALYSIS_TYPES

    def test_stockout_detection_exists(self):
        assert "stockout_detection" in ANALYSIS_TYPES

    def test_price_dispersion_exists(self):
        assert "price_dispersion" in ANALYSIS_TYPES

    def test_demand_pattern_exists(self):
        assert "demand_pattern" in ANALYSIS_TYPES

    def test_slow_movers_exists(self):
        assert "slow_movers" in ANALYSIS_TYPES


class TestDateRange:
    """Test _get_date_range helper."""

    def test_returns_two_dates(self):
        start, end = _get_date_range(30)
        assert isinstance(start, str)
        assert isinstance(end, str)

    def test_start_before_end(self):
        start, end = _get_date_range(30)
        assert start < end

    def test_zero_days(self):
        start, end = _get_date_range(0)
        assert start == end

    def test_iso_format(self):
        start, end = _get_date_range(7)
        # Should be YYYY-MM-DD format
        assert len(start) == 10
        assert start[4] == "-"
        assert start[7] == "-"


class TestBuildResult:
    """Test _build_result helper."""

    def test_has_required_keys(self):
        result = _build_result(
            "test", "Title", "Summary", [], [], {}, [], {}, 0.5)
        required = [
            "analysis_type", "title", "executive_summary", "findings",
            "evidence_tables", "financial_impact", "recommendations",
            "methodology", "confidence_level", "generated_at",
        ]
        for key in required:
            assert key in result

    def test_includes_timestamp(self):
        result = _build_result(
            "test", "Title", "Summary", [], [], {}, [], {}, 0.5)
        assert result["generated_at"]
        # Should be parseable as ISO datetime
        datetime.fromisoformat(result["generated_at"])

    def test_preserves_values(self):
        result = _build_result(
            "basket_analysis", "My Title", "My Summary",
            [{"a": 1}], [{"name": "T1"}],
            {"value": 100}, [{"action": "Do X"}],
            {"source": "test"}, 0.75,
        )
        assert result["analysis_type"] == "basket_analysis"
        assert result["title"] == "My Title"
        assert result["confidence_level"] == 0.75
        assert len(result["findings"]) == 1


class TestStoreName:
    """Test _store_name helper."""

    def test_known_store(self):
        name = _store_name("28")
        assert name == "Mosman"

    def test_unknown_store(self):
        name = _store_name("999")
        assert "999" in name


# =========================================================================
# TEST: REPORT GENERATOR
# =========================================================================

class TestFormatCurrency:
    """Test currency formatting."""

    def test_large_value(self):
        assert "$125,000" == _format_currency(125000)

    def test_small_value(self):
        assert "$12.50" == _format_currency(12.50)

    def test_none_value(self):
        assert "$0" == _format_currency(None)

    def test_million(self):
        result = _format_currency(1_500_000)
        assert "$1,500,000" == result


class TestHtmlEscape:
    """Test HTML escaping."""

    def test_escapes_angle_brackets(self):
        assert "&lt;script&gt;" == _html_escape("<script>")

    def test_escapes_ampersand(self):
        assert "A &amp; B" == _html_escape("A & B")

    def test_escapes_quotes(self):
        assert "&quot;hello&quot;" == _html_escape('"hello"')


class TestMarkdownReport:
    """Test markdown report generation."""

    def test_has_title(self, complete_result):
        md = generate_markdown_report(complete_result)
        assert "# Cross-sell Opportunities" in md

    def test_has_executive_summary(self, complete_result):
        md = generate_markdown_report(complete_result)
        assert "## Executive Summary" in md
        assert "28,503 baskets" in md

    def test_has_evidence_section(self, complete_result):
        md = generate_markdown_report(complete_result)
        assert "## Evidence" in md
        assert "Product A" in md

    def test_has_financial_impact(self, complete_result):
        md = generate_markdown_report(complete_result)
        assert "## Financial Impact" in md
        assert "$125,000" in md

    def test_has_recommendations(self, complete_result):
        md = generate_markdown_report(complete_result)
        assert "## Recommendations" in md
        assert "Store Manager" in md

    def test_has_methodology(self, complete_result):
        md = generate_markdown_report(complete_result)
        assert "## Methodology" in md
        assert "POS Transactions" in md

    def test_has_limitations(self, complete_result):
        md = generate_markdown_report(complete_result)
        assert "Limitations" in md
        assert "Single store" in md

    def test_empty_result_still_renders(self, empty_result):
        md = generate_markdown_report(empty_result)
        assert "# Empty Analysis" in md
        assert "Executive Summary" in md

    def test_minimal_result(self, minimal_result):
        md = generate_markdown_report(minimal_result)
        assert "# Minimal Report" in md

    def test_footer(self, complete_result):
        md = generate_markdown_report(complete_result)
        assert "Harris Farm Hub" in md


class TestHtmlReport:
    """Test HTML report generation."""

    def test_is_standalone_html(self, complete_result):
        html = generate_html_report(complete_result)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_has_style_tag(self, complete_result):
        html = generate_html_report(complete_result)
        assert "<style>" in html
        assert "</style>" in html

    def test_has_title_tag(self, complete_result):
        html = generate_html_report(complete_result)
        assert "<title>" in html

    def test_has_evidence_table(self, complete_result):
        html = generate_html_report(complete_result)
        assert '<table class="evidence-table">' in html
        assert "Product A" in html

    def test_has_impact_box(self, complete_result):
        html = generate_html_report(complete_result)
        assert "impact-box" in html
        assert "$125,000" in html

    def test_has_recommendations_table(self, complete_result):
        html = generate_html_report(complete_result)
        assert '<table class="recommendations-table">' in html

    def test_has_branding(self, complete_result):
        html = generate_html_report(complete_result)
        assert "Harris Farm Hub" in html

    def test_empty_result(self, empty_result):
        html = generate_html_report(empty_result)
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html


class TestCsvExport:
    """Test CSV export."""

    def test_has_header_info(self, complete_result):
        csv_text = generate_csv_export(complete_result)
        assert "Cross-sell Opportunities" in csv_text
        assert "basket_analysis" in csv_text

    def test_has_column_headers(self, complete_result):
        csv_text = generate_csv_export(complete_result)
        assert "Product A" in csv_text
        assert "Lift" in csv_text

    def test_has_data_rows(self, complete_result):
        csv_text = generate_csv_export(complete_result)
        assert "Bananas" in csv_text
        assert "Milk" in csv_text

    def test_has_financial_impact(self, complete_result):
        csv_text = generate_csv_export(complete_result)
        assert "Financial Impact" in csv_text

    def test_has_recommendations(self, complete_result):
        csv_text = generate_csv_export(complete_result)
        assert "Store Manager" in csv_text

    def test_empty_result(self, empty_result):
        csv_text = generate_csv_export(empty_result)
        assert "Empty Analysis" in csv_text


class TestJsonExport:
    """Test JSON export."""

    def test_valid_json(self, complete_result):
        json_text = generate_json_export(complete_result)
        parsed = json.loads(json_text)
        assert isinstance(parsed, dict)

    def test_contains_all_keys(self, complete_result):
        json_text = generate_json_export(complete_result)
        parsed = json.loads(json_text)
        assert "analysis_type" in parsed
        assert "title" in parsed
        assert "findings" in parsed

    def test_is_formatted(self, complete_result):
        json_text = generate_json_export(complete_result)
        # Should have indentation
        assert "\n" in json_text
        assert "  " in json_text

    def test_empty_result(self, empty_result):
        json_text = generate_json_export(empty_result)
        parsed = json.loads(json_text)
        assert parsed["findings"] == []


class TestEvidenceTableFormatting:
    """Test evidence table formatting helpers."""

    def test_markdown_table(self):
        table = {
            "columns": ["A", "B"],
            "rows": [["1", "2"], ["3", "4"]],
        }
        md = _format_evidence_table_md(table)
        assert "| A | B |" in md
        assert "| 1 | 2 |" in md

    def test_html_table(self):
        table = {
            "columns": ["A", "B"],
            "rows": [["1", "2"]],
        }
        html = _format_evidence_table_html(table)
        assert "<table" in html
        assert "<th>A</th>" in html
        assert "<td>1</td>" in html

    def test_empty_columns(self):
        md = _format_evidence_table_md({"columns": [], "rows": []})
        assert md == ""

    def test_html_empty_columns(self):
        html = _format_evidence_table_html({"columns": [], "rows": []})
        assert html == ""


# =========================================================================
# TEST: PRESENTATION RUBRIC
# =========================================================================

class TestGradeLabel:
    """Test grade label function."""

    def test_board_ready(self):
        assert grade_label(9.0) == "Board-ready"
        assert grade_label(10.0) == "Board-ready"

    def test_reviewed(self):
        assert grade_label(7.0) == "Reviewed"
        assert grade_label(8.9) == "Reviewed"

    def test_draft(self):
        assert grade_label(6.9) == "Draft"
        assert grade_label(0.0) == "Draft"


class TestRubricDimensions:
    """Test that all 8 dimensions are present."""

    def test_eight_dimensions(self):
        assert len(DIMENSIONS) == 8

    def test_dimension_names(self):
        names = [d[0] for d in DIMENSIONS]
        expected = ["audience", "story", "action", "visual",
                    "complete", "brief", "data", "honest"]
        assert names == expected


class TestScoreAudience:
    """Test audience dimension scoring."""

    def test_good_summary(self, complete_result):
        score, _ = _score_audience(complete_result)
        assert 7 <= score <= 10

    def test_no_summary(self, empty_result):
        score, _ = _score_audience(empty_result)
        assert score == 0

    def test_verbose_summary(self):
        result = {"executive_summary": "x" * 1500}
        score, _ = _score_audience(result)
        assert score < 8


class TestScoreStory:
    """Test story dimension scoring."""

    def test_complete_story(self, complete_result):
        score, rationale = _score_story(complete_result)
        assert score == 10
        assert "situation" in rationale
        assert "action" in rationale

    def test_empty_story(self, empty_result):
        score, _ = _score_story(empty_result)
        assert score == 0


class TestScoreAction:
    """Test action dimension scoring."""

    def test_complete_recs(self, complete_result):
        score, _ = _score_action(complete_result)
        assert score == 10  # 2/2 fully specified

    def test_no_recs(self, empty_result):
        score, _ = _score_action(empty_result)
        assert score == 0

    def test_partial_recs(self):
        result = {"recommendations": [
            {"action": "Do X", "owner": "Team A"},  # missing timeline, priority
            {"action": "Do Y", "owner": "Team B", "timeline": "1w", "priority": "high"},
        ]}
        score, rationale = _score_action(result)
        assert "1/2" in rationale


class TestScoreVisual:
    """Test visual dimension scoring."""

    def test_good_tables(self, complete_result):
        score, _ = _score_visual(complete_result)
        assert score >= 7

    def test_no_tables(self, empty_result):
        score, _ = _score_visual(empty_result)
        assert score == 0


class TestScoreComplete:
    """Test completeness scoring."""

    def test_all_sections(self, complete_result):
        score, rationale = _score_complete(complete_result)
        assert score >= 9
        assert "Missing" not in rationale

    def test_missing_sections(self, empty_result):
        score, rationale = _score_complete(empty_result)
        assert score < 5


class TestScoreBrief:
    """Test brevity scoring."""

    def test_concise_report(self, complete_result):
        score, _ = _score_brief(complete_result)
        assert score >= 8

    def test_verbose_report(self):
        result = {
            "executive_summary": "x" * 1000,
            "findings": list(range(120)),
            "recommendations": list(range(12)),
        }
        score, _ = _score_brief(result)
        assert score < 7


class TestScoreData:
    """Test data transparency scoring."""

    def test_full_methodology(self, complete_result):
        score, _ = _score_data(complete_result)
        assert score >= 9

    def test_no_methodology(self, empty_result):
        score, _ = _score_data(empty_result)
        assert score == 0


class TestScoreHonest:
    """Test honesty dimension scoring."""

    def test_honest_report(self, complete_result):
        score, _ = _score_honest(complete_result)
        assert score >= 8

    def test_no_confidence(self):
        result = {"confidence_level": None, "methodology": {},
                  "financial_impact": {}}
        score, _ = _score_honest(result)
        assert score < 3


class TestEvaluateReport:
    """Test the full rubric evaluation."""

    def test_returns_required_keys(self, complete_result):
        rubric = evaluate_report(complete_result)
        assert "dimensions" in rubric
        assert "total" in rubric
        assert "average" in rubric
        assert "grade" in rubric
        assert "summary" in rubric

    def test_eight_dimensions_scored(self, complete_result):
        rubric = evaluate_report(complete_result)
        assert len(rubric["dimensions"]) == 8

    def test_scores_in_range(self, complete_result):
        rubric = evaluate_report(complete_result)
        for key, dim in rubric["dimensions"].items():
            assert 0 <= dim["score"] <= 10, \
                "{} score {} out of range".format(key, dim["score"])

    def test_grade_assigned(self, complete_result):
        rubric = evaluate_report(complete_result)
        assert rubric["grade"] in ("Board-ready", "Reviewed", "Draft")

    def test_average_calculation(self, complete_result):
        rubric = evaluate_report(complete_result)
        total = sum(d["score"] for d in rubric["dimensions"].values())
        expected_avg = round(total / 8, 1)
        assert rubric["average"] == expected_avg

    def test_empty_report_is_draft(self, empty_result):
        rubric = evaluate_report(empty_result)
        assert rubric["grade"] == "Draft"
        assert rubric["average"] < 5.0

    def test_complete_report_high_score(self, complete_result):
        rubric = evaluate_report(complete_result)
        assert rubric["average"] >= 7.0

    def test_summary_string(self, complete_result):
        rubric = evaluate_report(complete_result)
        assert "/10 avg" in rubric["summary"]
        assert "of 8 dimensions" in rubric["summary"]

    def test_each_dimension_has_rationale(self, complete_result):
        rubric = evaluate_report(complete_result)
        for key, dim in rubric["dimensions"].items():
            assert "label" in dim
            assert "rationale" in dim
            assert isinstance(dim["rationale"], str)


# =========================================================================
# TEST: API ENDPOINTS (integration with backend)
# =========================================================================

class TestIntelligenceAPI:
    """Test intelligence API endpoints via FastAPI test client."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Set up test client."""
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), '..', 'backend'))
        from app import app as fastapi_app
        from starlette.testclient import TestClient
        self.client = TestClient(fastapi_app)

    def test_list_reports(self):
        resp = self.client.get("/api/intelligence/reports")
        assert resp.status_code == 200
        data = resp.json()
        assert "reports" in data
        assert isinstance(data["reports"], list)

    def test_invalid_analysis_type(self):
        resp = self.client.post(
            "/api/intelligence/run/invalid_type",
            json={"store_id": "28", "days": 14},
        )
        assert resp.status_code == 400
        assert "Invalid analysis_type" in resp.json()["detail"]

    def test_report_not_found(self):
        resp = self.client.get("/api/intelligence/reports/99999")
        assert resp.status_code == 404

    def test_export_invalid_format(self):
        resp = self.client.get("/api/intelligence/export/1/pdf")
        assert resp.status_code == 400
        assert "Format must be" in resp.json()["detail"]

    def test_export_not_found(self):
        resp = self.client.get("/api/intelligence/export/99999/html")
        assert resp.status_code == 404

    def test_list_reports_with_filter(self):
        resp = self.client.get(
            "/api/intelligence/reports",
            params={"analysis_type": "basket_analysis"},
        )
        assert resp.status_code == 200
