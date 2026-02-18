"""Tests for training content module — data integrity and prompt quality heuristic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "dashboards"))

from shared.training_content import (
    BUILDING_BLOCKS,
    PROMPT_EXAMPLES,
    CHALLENGES,
    RUBRIC_CRITERIA,
    BADGES,
    COACH_SYSTEM_PROMPT,
    check_prompt_quality,
)


# ---------------------------------------------------------------------------
# BUILDING BLOCKS CONTENT INTEGRITY
# ---------------------------------------------------------------------------

class TestBuildingBlocks:
    def test_five_blocks(self):
        assert len(BUILDING_BLOCKS) == 5

    def test_required_fields(self):
        required = {"name", "icon", "short", "explanation", "example", "tip", "keywords"}
        for block in BUILDING_BLOCKS:
            assert required.issubset(block.keys()), f"{block['name']} missing fields"

    def test_keywords_not_empty(self):
        for block in BUILDING_BLOCKS:
            assert len(block["keywords"]) >= 2, f"{block['name']} needs at least 2 keywords"

    def test_block_names(self):
        names = [b["name"] for b in BUILDING_BLOCKS]
        assert names == ["Role", "Context", "Task", "Format", "Constraints"]


# ---------------------------------------------------------------------------
# PROMPT EXAMPLES INTEGRITY
# ---------------------------------------------------------------------------

class TestPromptExamples:
    def test_at_least_five_examples(self):
        assert len(PROMPT_EXAMPLES) >= 5

    def test_required_fields(self):
        for ex in PROMPT_EXAMPLES:
            assert "department" in ex
            assert "bad" in ex
            assert "good" in ex
            assert "why" in ex

    def test_good_longer_than_bad(self):
        for ex in PROMPT_EXAMPLES:
            assert len(ex["good"]) > len(ex["bad"]), (
                f"{ex['department']}: good prompt should be longer than bad"
            )


# ---------------------------------------------------------------------------
# CHALLENGES INTEGRITY
# ---------------------------------------------------------------------------

class TestChallenges:
    def test_three_difficulty_levels(self):
        assert set(CHALLENGES.keys()) == {"Beginner", "Intermediate", "Advanced"}

    def test_three_per_level(self):
        for level, scenarios in CHALLENGES.items():
            assert len(scenarios) == 3, f"{level} should have 3 challenges"

    def test_required_fields(self):
        required = {"id", "title", "scenario", "hints", "criteria"}
        for level, scenarios in CHALLENGES.items():
            for s in scenarios:
                assert required.issubset(s.keys()), f"{s.get('id', '?')} missing fields"

    def test_unique_ids(self):
        ids = []
        for scenarios in CHALLENGES.values():
            ids.extend(s["id"] for s in scenarios)
        assert len(ids) == len(set(ids)), "Challenge IDs must be unique"

    def test_hints_not_empty(self):
        for level, scenarios in CHALLENGES.items():
            for s in scenarios:
                assert len(s["hints"]) >= 2, f"{s['id']} needs at least 2 hints"


# ---------------------------------------------------------------------------
# RUBRIC CRITERIA INTEGRITY
# ---------------------------------------------------------------------------

class TestRubricCriteria:
    def test_five_criteria(self):
        assert len(RUBRIC_CRITERIA) == 5

    def test_required_fields(self):
        for c in RUBRIC_CRITERIA:
            assert "name" in c
            assert "description" in c
            assert "guide" in c

    def test_guide_has_five_levels(self):
        for c in RUBRIC_CRITERIA:
            assert set(c["guide"].keys()) == {1, 2, 3, 4, 5}, (
                f"{c['name']} guide must have scores 1-5"
            )


# ---------------------------------------------------------------------------
# BADGES INTEGRITY
# ---------------------------------------------------------------------------

class TestBadges:
    def test_at_least_five_badges(self):
        assert len(BADGES) >= 5

    def test_unique_ids(self):
        ids = [b["id"] for b in BADGES]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# COACH SYSTEM PROMPT
# ---------------------------------------------------------------------------

class TestCoachPrompt:
    def test_has_placeholders(self):
        assert "{scenario}" in COACH_SYSTEM_PROMPT
        assert "{user_prompt}" in COACH_SYSTEM_PROMPT

    def test_mentions_five_criteria(self):
        for name in ["ROLE", "CONTEXT", "TASK", "FORMAT", "CONSTRAINTS"]:
            assert name in COACH_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# PROMPT QUALITY HEURISTIC
# ---------------------------------------------------------------------------

class TestCheckPromptQuality:
    def test_excellent_prompt(self):
        prompt = (
            "You are a Harris Farm fresh produce specialist. "
            "Analyse the top 3 causes of stone fruit wastage at our store "
            "over the last 4 weeks. Present as a numbered list."
        )
        result = check_prompt_quality(prompt)
        assert result["score"] >= 4
        assert result["level"] == "Excellent"

    def test_poor_prompt(self):
        prompt = "Tell me about fruit"
        result = check_prompt_quality(prompt)
        assert result["score"] <= 1
        assert result["level"] == "Needs work"

    def test_returns_all_blocks(self):
        result = check_prompt_quality("anything")
        assert set(result["checks"].keys()) == {"Role", "Context", "Task", "Format", "Constraints"}

    def test_max_score_is_five(self):
        result = check_prompt_quality("anything")
        assert result["max_score"] == 5

    def test_role_detected(self):
        result = check_prompt_quality("You are an expert in fruit")
        assert result["checks"]["Role"]["present"] is True

    def test_role_missing(self):
        result = check_prompt_quality("Tell me about sales")
        assert result["checks"]["Role"]["present"] is False

    def test_context_detected(self):
        result = check_prompt_quality("At our Harris Farm store")
        assert result["checks"]["Context"]["present"] is True

    def test_task_detected_by_verb(self):
        result = check_prompt_quality("Analyse the sales data")
        assert result["checks"]["Task"]["present"] is True

    def test_task_detected_by_question_mark(self):
        result = check_prompt_quality("What are the issues?")
        assert result["checks"]["Task"]["present"] is True

    def test_format_detected(self):
        result = check_prompt_quality("Give me a numbered list")
        assert result["checks"]["Format"]["present"] is True

    def test_constraints_detected(self):
        result = check_prompt_quality("Only show the last 30 days")
        assert result["checks"]["Constraints"]["present"] is True

    def test_empty_prompt(self):
        result = check_prompt_quality("")
        assert result["score"] == 0
        assert result["level"] == "Needs work"

    def test_getting_there_level(self):
        # Has exactly 2 blocks: context + task
        prompt = "At our Harris Farm store, analyse the wastage"
        result = check_prompt_quality(prompt)
        assert result["score"] == 2
        assert result["level"] == "Getting there"

    def test_good_level(self):
        # Has 3 blocks: context + task + constraints
        prompt = "At our Harris Farm store, analyse the wastage over the last 30 days"
        result = check_prompt_quality(prompt)
        assert result["score"] == 3
        assert result["level"] == "Good"

    def test_tips_present(self):
        result = check_prompt_quality("anything")
        for check in result["checks"].values():
            assert "tip" in check
            assert len(check["tip"]) > 0
