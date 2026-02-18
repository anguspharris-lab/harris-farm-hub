"""
Tests for Hub Documentation Portal
Law 3: min 1 success + 1 failure per function

Tests cover:
- Portal content loader (portal_content.py)
- Portal API endpoints (prompt history, scores, achievements)
- Gamification constants
"""

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboards'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from shared.portal_content import (
    load_doc, load_procedure, load_learning, load_rubric,
    get_doc_index, get_procedure_index, get_learning_index,
    search_all_docs, parse_audit_metrics, get_data_sources,
    MILESTONES, POINT_ACTIONS_AI, POINT_ACTIONS_HUMAN,
    SHOWCASE_IMPLEMENTATIONS, DATA_SOURCES,
    DOCS_DIR, PROCEDURES_DIR, LEARNINGS_DIR, RUBRICS_DIR,
)


# ============================================================================
# CONTENT LOADER TESTS
# ============================================================================

class TestLoadDoc:
    """Test load_doc() reads markdown files from docs/."""

    def test_load_existing_doc(self):
        """Success: load a known doc that exists."""
        # data_catalog.md is known to exist
        content = load_doc("data_catalog")
        if content is not None:
            assert isinstance(content, str)
            assert len(content) > 0
        else:
            pytest.skip("data_catalog.md not present in docs/")

    def test_load_nonexistent_doc(self):
        """Failure: returns None for a doc that doesn't exist."""
        result = load_doc("nonexistent_doc_abc123")
        assert result is None


class TestLoadProcedure:
    """Test load_procedure() reads from watchdog/procedures/."""

    def test_load_existing_procedure(self):
        """Success: load a known procedure."""
        content = load_procedure("task_execution")
        if content is not None:
            assert isinstance(content, str)
            assert len(content) > 0
        else:
            pytest.skip("task_execution.md not present in procedures/")

    def test_load_nonexistent_procedure(self):
        """Failure: returns None for missing procedure."""
        result = load_procedure("nonexistent_proc_xyz")
        assert result is None


class TestLoadLearning:
    """Test load_learning() reads from watchdog/learnings/."""

    def test_load_existing_learning(self):
        """Success: load a known learning file."""
        content = load_learning("data_context.md")
        if content is not None:
            assert isinstance(content, str)
            assert len(content) > 0
        else:
            pytest.skip("data_context.md not present in learnings/")

    def test_load_nonexistent_learning(self):
        """Failure: returns None for missing learning file."""
        result = load_learning("nonexistent_learning.md")
        assert result is None


class TestLoadRubric:
    """Test load_rubric() reads and parses JSON from watchdog/rubrics/."""

    def test_load_existing_rubric(self):
        """Success: load and parse a known rubric JSON."""
        rubric = load_rubric("code_quality")
        if rubric is not None:
            assert isinstance(rubric, dict)
        else:
            pytest.skip("code_quality.json not present in rubrics/")

    def test_load_nonexistent_rubric(self):
        """Failure: returns None for missing rubric."""
        result = load_rubric("nonexistent_rubric_abc")
        assert result is None


# ============================================================================
# INDEX TESTS
# ============================================================================

class TestDocIndex:
    """Test get_doc_index() returns list of docs with metadata."""

    def test_returns_list(self):
        """Success: returns a list."""
        result = get_doc_index()
        assert isinstance(result, list)

    def test_docs_have_metadata(self):
        """Success: each doc has required metadata keys."""
        docs = get_doc_index()
        if not docs:
            pytest.skip("No docs found in docs/ directory")
        for d in docs:
            assert "name" in d
            assert "filename" in d
            assert "size_kb" in d
            assert "modified" in d

    def test_no_fake_docs(self):
        """Failure: bogus file not in index."""
        docs = get_doc_index()
        names = [d["filename"] for d in docs]
        assert "FAKE_NONEXISTENT.md" not in names


class TestProcedureIndex:
    """Test get_procedure_index()."""

    def test_returns_list(self):
        """Success: returns a list."""
        result = get_procedure_index()
        assert isinstance(result, list)

    def test_known_procedure_present(self):
        """Success: task_execution is in the index if procedures/ exists."""
        procs = get_procedure_index()
        if not procs:
            pytest.skip("No procedures found")
        names = [p["name"] for p in procs]
        assert "task_execution" in names


class TestLearningIndex:
    """Test get_learning_index()."""

    def test_returns_list(self):
        """Success: returns a list."""
        result = get_learning_index()
        assert isinstance(result, list)

    def test_no_directories_in_index(self):
        """Failure: directories should not appear in learning index."""
        learnings = get_learning_index()
        for l in learnings:
            # All entries should be files, not directories
            p = Path(l["path"])
            assert p.is_file() or not p.exists()


# ============================================================================
# SEARCH TESTS
# ============================================================================

class TestSearchAllDocs:
    """Test search_all_docs() cross-document search."""

    def test_search_finds_results(self):
        """Success: common term returns results."""
        results = search_all_docs("Harris Farm")
        # Should find at least something in the docs
        if not results:
            pytest.skip("No documents contain 'Harris Farm'")
        assert len(results) > 0
        for r in results:
            assert "source" in r
            assert "name" in r
            assert "line_number" in r
            assert "context" in r

    def test_search_no_results(self):
        """Failure: gibberish term returns empty list."""
        results = search_all_docs("zzz_xxyy_no_match_999")
        assert results == []

    def test_search_short_query_rejected(self):
        """Failure: single character query returns empty."""
        results = search_all_docs("a")
        assert results == []

    def test_search_empty_query_rejected(self):
        """Failure: empty query returns empty."""
        results = search_all_docs("")
        assert results == []

    def test_search_results_capped_at_50(self):
        """Success: results never exceed 50 entries."""
        # Use a very common word
        results = search_all_docs("the")
        assert len(results) <= 50


# ============================================================================
# AUDIT METRICS TESTS
# ============================================================================

class TestParseAuditMetrics:
    """Test parse_audit_metrics() extracts data from audit.log."""

    def test_returns_dict(self):
        """Success: returns a dict with expected keys."""
        metrics = parse_audit_metrics()
        assert isinstance(metrics, dict)
        assert "task_count" in metrics
        assert "avg_scores" in metrics
        assert "latest_task" in metrics
        assert "score_entries" in metrics

    def test_task_count_nonnegative(self):
        """Success: task count is non-negative integer."""
        metrics = parse_audit_metrics()
        assert isinstance(metrics["task_count"], int)
        assert metrics["task_count"] >= 0

    def test_avg_scores_is_dict(self):
        """Success: avg_scores is a dict."""
        metrics = parse_audit_metrics()
        assert isinstance(metrics["avg_scores"], dict)

    def test_score_entries_is_list(self):
        """Success: score_entries is a list."""
        metrics = parse_audit_metrics()
        assert isinstance(metrics["score_entries"], list)


# ============================================================================
# DATA SOURCES TESTS
# ============================================================================

class TestGetDataSources:
    """Test get_data_sources() returns structured source list."""

    def test_returns_five_sources(self):
        """Success: returns 5 data sources."""
        sources = get_data_sources()
        assert len(sources) == 5

    def test_sources_have_required_fields(self):
        """Success: each source has required metadata."""
        sources = get_data_sources()
        required = ["name", "type", "size", "rows", "source",
                     "grain", "period", "columns", "used_by", "join_key"]
        for src in sources:
            for key in required:
                assert key in src, "Missing '{}' in source '{}'".format(
                    key, src.get("name", "?"))

    def test_transaction_data_present(self):
        """Success: Transaction Data is in the sources."""
        sources = get_data_sources()
        names = [s["name"] for s in sources]
        assert "Transaction Data" in names

    def test_no_fake_source(self):
        """Failure: non-existent source is not returned."""
        sources = get_data_sources()
        names = [s["name"] for s in sources]
        assert "Fake Data Source" not in names


# ============================================================================
# GAMIFICATION CONSTANTS TESTS
# ============================================================================

class TestGamificationConstants:
    """Test gamification milestones and point actions."""

    def test_milestones_count(self):
        """Success: 5 milestones defined."""
        assert len(MILESTONES) == 5

    def test_milestones_ascending_points(self):
        """Success: milestones are in ascending point order."""
        points = [m["points"] for m in MILESTONES]
        assert points == sorted(points)
        assert points[0] < points[-1]

    def test_milestones_have_required_fields(self):
        """Success: each milestone has code, name, icon, points, label."""
        for m in MILESTONES:
            assert "code" in m
            assert "name" in m
            assert "icon" in m
            assert "points" in m
            assert "label" in m

    def test_milestone_codes_unique(self):
        """Failure: duplicate codes would break achievement lookups."""
        codes = [m["code"] for m in MILESTONES]
        assert len(codes) == len(set(codes))

    def test_point_actions_ai_not_empty(self):
        """Success: AI point actions defined."""
        assert len(POINT_ACTIONS_AI) > 0
        for a in POINT_ACTIONS_AI:
            assert "action" in a
            assert "points" in a
            assert a["points"] > 0

    def test_point_actions_human_not_empty(self):
        """Success: Human point actions defined."""
        assert len(POINT_ACTIONS_HUMAN) > 0
        for a in POINT_ACTIONS_HUMAN:
            assert "action" in a
            assert "points" in a
            assert a["points"] > 0

    def test_showcase_implementations_not_empty(self):
        """Success: showcase implementations are defined."""
        assert len(SHOWCASE_IMPLEMENTATIONS) > 0
        for impl in SHOWCASE_IMPLEMENTATIONS:
            assert "name" in impl
            assert "desc" in impl
            assert "stats" in impl
            assert "dashboard" in impl


# ============================================================================
# PORTAL API TESTS (using SQLite directly — no server needed)
# ============================================================================

@pytest.fixture
def portal_db():
    """Create a temporary SQLite database with portal tables."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prompt_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  prompt_text TEXT NOT NULL,
                  context TEXT,
                  outcome TEXT,
                  rating INTEGER,
                  ai_review TEXT,
                  tokens INTEGER,
                  latency_ms INTEGER,
                  created_at TEXT DEFAULT (datetime('now')))''')

    c.execute('''CREATE TABLE IF NOT EXISTS portal_scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  points INTEGER NOT NULL,
                  category TEXT NOT NULL,
                  reason TEXT,
                  created_at TEXT DEFAULT (datetime('now')))''')

    c.execute('''CREATE TABLE IF NOT EXISTS portal_achievements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  achievement_code TEXT NOT NULL,
                  achieved_at TEXT DEFAULT (datetime('now')),
                  UNIQUE(user_id, achievement_code))''')
    conn.commit()
    conn.close()

    yield db_path
    os.unlink(db_path)


class TestPromptHistoryDB:
    """Test prompt_history table operations directly."""

    def test_insert_and_retrieve(self, portal_db):
        """Success: insert a prompt and retrieve it."""
        conn = sqlite3.connect(portal_db)
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO prompt_history (user_id, prompt_text, context, "
            "outcome, rating) VALUES (?,?,?,?,?)",
            ("test@example.com", "Analyze sales trends", "retail", "good", 4),
        )
        conn.commit()

        rows = conn.execute(
            "SELECT * FROM prompt_history WHERE user_id = ?",
            ("test@example.com",),
        ).fetchall()
        conn.close()

        assert len(rows) == 1
        assert dict(rows[0])["prompt_text"] == "Analyze sales trends"
        assert dict(rows[0])["rating"] == 4

    def test_empty_history(self, portal_db):
        """Failure: no prompts for unknown user."""
        conn = sqlite3.connect(portal_db)
        rows = conn.execute(
            "SELECT * FROM prompt_history WHERE user_id = ?",
            ("nobody@example.com",),
        ).fetchall()
        conn.close()
        assert len(rows) == 0


class TestPortalScoresDB:
    """Test portal_scores table operations directly."""

    def test_award_points(self, portal_db):
        """Success: award points and check total."""
        conn = sqlite3.connect(portal_db)
        conn.execute(
            "INSERT INTO portal_scores (user_id, points, category, reason) "
            "VALUES (?,?,?,?)",
            ("user1", 10, "human", "clearer prompt"),
        )
        conn.execute(
            "INSERT INTO portal_scores (user_id, points, category, reason) "
            "VALUES (?,?,?,?)",
            ("user1", 5, "human", "shorter prompt"),
        )
        conn.commit()

        total = conn.execute(
            "SELECT COALESCE(SUM(points), 0) FROM portal_scores "
            "WHERE user_id = ?",
            ("user1",),
        ).fetchone()[0]
        conn.close()

        assert total == 15

    def test_zero_points_for_new_user(self, portal_db):
        """Failure: new user has zero points."""
        conn = sqlite3.connect(portal_db)
        total = conn.execute(
            "SELECT COALESCE(SUM(points), 0) FROM portal_scores "
            "WHERE user_id = ?",
            ("new_user",),
        ).fetchone()[0]
        conn.close()
        assert total == 0

    def test_leaderboard_query(self, portal_db):
        """Success: leaderboard aggregation works."""
        conn = sqlite3.connect(portal_db)
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO portal_scores (user_id, points, category, reason) "
            "VALUES (?,?,?,?)",
            ("alice", 20, "human", "test"),
        )
        conn.execute(
            "INSERT INTO portal_scores (user_id, points, category, reason) "
            "VALUES (?,?,?,?)",
            ("bob", 30, "ai", "test"),
        )
        conn.execute(
            "INSERT INTO portal_scores (user_id, points, category, reason) "
            "VALUES (?,?,?,?)",
            ("alice", 10, "human", "test2"),
        )
        conn.commit()

        rows = conn.execute(
            "SELECT user_id, category, SUM(points) AS total_points, "
            "COUNT(*) AS actions FROM portal_scores "
            "GROUP BY user_id, category ORDER BY total_points DESC"
        ).fetchall()
        conn.close()

        results = [dict(r) for r in rows]
        assert len(results) == 2
        # Bob has 30, Alice has 30 (20+10)
        totals = {r["user_id"]: r["total_points"] for r in results}
        assert totals["alice"] == 30
        assert totals["bob"] == 30


class TestPortalAchievementsDB:
    """Test portal_achievements table operations directly."""

    def test_award_achievement(self, portal_db):
        """Success: achievement is saved and retrievable."""
        conn = sqlite3.connect(portal_db)
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO portal_achievements (user_id, achievement_code) "
            "VALUES (?,?)",
            ("user1", "bronze"),
        )
        conn.commit()

        rows = conn.execute(
            "SELECT * FROM portal_achievements WHERE user_id = ?",
            ("user1",),
        ).fetchall()
        conn.close()

        assert len(rows) == 1
        assert dict(rows[0])["achievement_code"] == "bronze"

    def test_duplicate_achievement_ignored(self, portal_db):
        """Success: UNIQUE constraint prevents duplicate achievements."""
        conn = sqlite3.connect(portal_db)
        conn.execute(
            "INSERT OR IGNORE INTO portal_achievements "
            "(user_id, achievement_code) VALUES (?,?)",
            ("user1", "bronze"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO portal_achievements "
            "(user_id, achievement_code) VALUES (?,?)",
            ("user1", "bronze"),
        )
        conn.commit()

        count = conn.execute(
            "SELECT COUNT(*) FROM portal_achievements WHERE user_id = ?",
            ("user1",),
        ).fetchone()[0]
        conn.close()

        assert count == 1

    def test_empty_achievements(self, portal_db):
        """Failure: new user has no achievements."""
        conn = sqlite3.connect(portal_db)
        rows = conn.execute(
            "SELECT * FROM portal_achievements WHERE user_id = ?",
            ("nobody",),
        ).fetchall()
        conn.close()
        assert len(rows) == 0


# ============================================================================
# AGENT COMPETITION SYSTEM TESTS
# ============================================================================

from shared.agent_teams import (
    AGENT_TEAMS, DEPARTMENT_AGENTS, EVALUATION_TIERS, BUSINESS_UNITS,
    SEED_PROPOSALS, SEED_INSIGHTS,
    EVALUATION_MAX_SCORE, IMPLEMENTATION_THRESHOLD,
    ARENA_ACHIEVEMENTS, TEAM_POINT_ACTIONS,
    DATA_INTELLIGENCE_AGENTS, DATA_INTEL_CATEGORIES,
    SEED_DATA_INTEL_INSIGHTS,
    get_team, get_agent, get_agents_by_unit, get_agents_by_team,
    get_business_unit, get_data_intel_agent, calculate_proposal_score,
)


class TestAgentTeams:
    """Test AGENT_TEAMS constants."""

    def test_five_teams(self):
        """Success: exactly 5 competing teams defined."""
        assert len(AGENT_TEAMS) == 5

    def test_team_ids_unique(self):
        """Success: all team IDs are unique."""
        ids = [t["id"] for t in AGENT_TEAMS]
        assert len(ids) == len(set(ids))

    def test_teams_have_required_fields(self):
        """Success: each team has required fields."""
        required = ["id", "name", "firm", "color", "icon",
                     "philosophy", "strengths", "motto"]
        for team in AGENT_TEAMS:
            for field in required:
                assert field in team, (
                    "Team {} missing field '{}'".format(team["id"], field))

    def test_team_colors_valid_hex(self):
        """Success: all team colors are valid hex codes."""
        for team in AGENT_TEAMS:
            assert team["color"].startswith("#")
            assert len(team["color"]) == 7

    def test_nonexistent_team_returns_none(self):
        """Failure: get_team with bad ID returns None."""
        assert get_team("nonexistent_team_xyz") is None

    def test_get_team_returns_correct(self):
        """Success: get_team returns correct team."""
        team = get_team("alpha")
        assert team is not None
        assert team["firm"] == "AWS / Amazon"


class TestDepartmentAgents:
    """Test DEPARTMENT_AGENTS constants."""

    def test_forty_plus_agents(self):
        """Success: at least 40 agents defined."""
        assert len(DEPARTMENT_AGENTS) >= 40

    def test_agent_ids_unique(self):
        """Success: all agent IDs are unique."""
        ids = [a["id"] for a in DEPARTMENT_AGENTS]
        assert len(ids) == len(set(ids))

    def test_agents_reference_valid_teams(self):
        """Success: all agents reference a valid team_id."""
        team_ids = {t["id"] for t in AGENT_TEAMS}
        for agent in DEPARTMENT_AGENTS:
            assert agent["team_id"] in team_ids, (
                "Agent {} references invalid team '{}'".format(
                    agent["id"], agent["team_id"]))

    def test_agents_have_required_fields(self):
        """Success: each agent has required fields."""
        required = ["id", "name", "team_id", "department",
                     "business_unit", "role", "capabilities",
                     "data_sources", "status"]
        for agent in DEPARTMENT_AGENTS:
            for field in required:
                assert field in agent, (
                    "Agent {} missing field '{}'".format(
                        agent["id"], field))

    def test_get_agent_returns_correct(self):
        """Success: get_agent returns correct agent."""
        agent = get_agent("fp_demand")
        assert agent is not None
        assert agent["name"] == "Fresh Demand Analyst"

    def test_nonexistent_agent_returns_none(self):
        """Failure: get_agent with bad ID returns None."""
        assert get_agent("nonexistent_agent_xyz") is None

    def test_agents_by_unit_fresh_produce(self):
        """Success: fresh_produce has agents."""
        agents = get_agents_by_unit("fresh_produce")
        assert len(agents) > 0
        for a in agents:
            assert a["business_unit"] == "fresh_produce"

    def test_agents_by_team(self):
        """Success: each team has agents."""
        for team in AGENT_TEAMS:
            agents = get_agents_by_team(team["id"])
            assert len(agents) > 0, (
                "Team {} has no agents".format(team["id"]))


class TestBusinessUnits:
    """Test BUSINESS_UNITS constants."""

    def test_eight_business_units(self):
        """Success: 8 business units defined."""
        assert len(BUSINESS_UNITS) == 8

    def test_business_unit_ids_unique(self):
        """Success: all business unit IDs unique."""
        ids = [bu["id"] for bu in BUSINESS_UNITS]
        assert len(ids) == len(set(ids))

    def test_get_business_unit(self):
        """Success: lookup works for valid unit."""
        bu = get_business_unit("fresh_produce")
        assert bu is not None
        assert bu["name"] == "Fresh Produce"

    def test_nonexistent_unit_returns_none(self):
        """Failure: bad unit ID returns None."""
        assert get_business_unit("fake_unit") is None


class TestEvaluationTiers:
    """Test EVALUATION_TIERS and scoring logic."""

    def test_five_tiers(self):
        """Success: exactly 5 evaluation tiers."""
        assert len(EVALUATION_TIERS) == 5

    def test_tiers_sum_to_max_score(self):
        """Success: tier max_points sum to EVALUATION_MAX_SCORE (130)."""
        total = sum(t["max_points"] for t in EVALUATION_TIERS)
        assert total == EVALUATION_MAX_SCORE
        assert total == 130

    def test_tiers_have_criteria(self):
        """Success: each tier has criteria list."""
        for tier in EVALUATION_TIERS:
            assert "criteria" in tier
            assert len(tier["criteria"]) > 0

    def test_implementation_threshold(self):
        """Success: threshold is 110 (85% of 130)."""
        assert IMPLEMENTATION_THRESHOLD == 110

    def test_perfect_score_equals_130(self):
        """Success: all 5s across all criteria yields 130."""
        evals = []
        for tier in EVALUATION_TIERS:
            for criterion in tier["criteria"]:
                evals.append({
                    "tier": tier["id"],
                    "criterion": criterion,
                    "score": 5,
                })
        result = calculate_proposal_score(evals)
        assert result["total"] == 130.0

    def test_zero_score_yields_zero(self):
        """Success: all 1s yields minimum score."""
        evals = []
        for tier in EVALUATION_TIERS:
            for criterion in tier["criteria"]:
                evals.append({
                    "tier": tier["id"],
                    "criterion": criterion,
                    "score": 1,
                })
        result = calculate_proposal_score(evals)
        assert result["total"] == 26.0  # 1/5 * 130

    def test_empty_evaluations_yields_zero(self):
        """Failure: no evaluations = 0 total."""
        result = calculate_proposal_score([])
        assert result["total"] == 0.0

    def test_partial_evaluation(self):
        """Success: only some tiers evaluated, others are 0."""
        evals = []
        # Only evaluate first tier
        tier = EVALUATION_TIERS[0]
        for criterion in tier["criteria"]:
            evals.append({
                "tier": tier["id"],
                "criterion": criterion,
                "score": 5,
            })
        result = calculate_proposal_score(evals)
        assert result["total"] == tier["max_points"]
        # Other tiers should be 0
        for t in EVALUATION_TIERS[1:]:
            assert result["tier_scores"][t["id"]] == 0.0


class TestSeedData:
    """Test pre-seeded proposals and insights."""

    def test_ten_seed_proposals(self):
        """Success: 10 pre-seeded proposals."""
        assert len(SEED_PROPOSALS) == 10

    def test_proposals_reference_valid_teams(self):
        """Success: all proposals reference valid teams."""
        team_ids = {t["id"] for t in AGENT_TEAMS}
        for p in SEED_PROPOSALS:
            assert p["team_id"] in team_ids

    def test_proposals_reference_valid_agents(self):
        """Success: all proposals reference valid agent IDs."""
        agent_ids = {a["id"] for a in DEPARTMENT_AGENTS}
        for p in SEED_PROPOSALS:
            assert p["agent_id"] in agent_ids, (
                "Proposal '{}' references invalid agent '{}'".format(
                    p["title"], p["agent_id"]))

    def test_proposals_have_valid_statuses(self):
        """Success: all proposals have valid status values."""
        valid_statuses = {"submitted", "evaluating", "scored", "implemented"}
        for p in SEED_PROPOSALS:
            assert p["status"] in valid_statuses

    def test_fifteen_seed_insights(self):
        """Success: 15 pre-seeded insights."""
        assert len(SEED_INSIGHTS) == 15

    def test_insights_have_valid_types(self):
        """Success: all insights have valid type values."""
        valid_types = {"opportunity", "risk", "trend", "anomaly"}
        for ins in SEED_INSIGHTS:
            assert ins["insight_type"] in valid_types

    def test_insights_confidence_in_range(self):
        """Success: confidence values between 0 and 1."""
        for ins in SEED_INSIGHTS:
            assert 0 <= ins["confidence"] <= 1


class TestArenaDB:
    """Test arena database operations directly."""

    @pytest.fixture
    def arena_db(self):
        """Create a temp DB with arena tables."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE arena_proposals
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT NOT NULL, description TEXT,
                      team_id TEXT NOT NULL, agent_id TEXT,
                      department TEXT, category TEXT,
                      status TEXT DEFAULT 'submitted',
                      estimated_impact_aud REAL DEFAULT 0,
                      estimated_effort_weeks REAL DEFAULT 0,
                      complexity TEXT DEFAULT 'medium',
                      total_score REAL DEFAULT 0,
                      tier_scores TEXT DEFAULT '{}',
                      submitted_at TEXT DEFAULT (datetime('now')),
                      scored_at TEXT, is_seeded INTEGER DEFAULT 0)''')

        c.execute('''CREATE TABLE arena_evaluations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      proposal_id INTEGER NOT NULL,
                      tier TEXT NOT NULL,
                      evaluator TEXT DEFAULT 'system',
                      criterion TEXT NOT NULL,
                      score INTEGER NOT NULL,
                      comment TEXT,
                      evaluated_at TEXT DEFAULT (datetime('now')),
                      FOREIGN KEY (proposal_id) REFERENCES arena_proposals(id))''')

        c.execute('''CREATE TABLE arena_team_stats
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      team_id TEXT NOT NULL, period TEXT NOT NULL,
                      total_proposals INTEGER DEFAULT 0,
                      avg_score REAL DEFAULT 0,
                      total_impact_aud REAL DEFAULT 0,
                      implementations INTEGER DEFAULT 0,
                      multiplier REAL DEFAULT 1.0,
                      rank INTEGER DEFAULT 0,
                      updated_at TEXT DEFAULT (datetime('now')),
                      UNIQUE(team_id, period))''')

        c.execute('''CREATE TABLE arena_insights
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      agent_id TEXT NOT NULL, team_id TEXT NOT NULL,
                      department TEXT, insight_type TEXT,
                      title TEXT NOT NULL, description TEXT,
                      data_source TEXT, confidence REAL DEFAULT 0.8,
                      potential_impact_aud REAL DEFAULT 0,
                      status TEXT DEFAULT 'active',
                      created_at TEXT DEFAULT (datetime('now')),
                      is_seeded INTEGER DEFAULT 0)''')

        conn.commit()
        conn.close()
        yield db_path
        os.unlink(db_path)

    def test_insert_and_retrieve_proposal(self, arena_db):
        """Success: insert and retrieve a proposal."""
        conn = sqlite3.connect(arena_db)
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO arena_proposals (title, description, team_id, "
            "agent_id, department, category) "
            "VALUES (?,?,?,?,?,?)",
            ("Test Proposal", "A test.", "alpha", "fp_demand",
             "Fruit and Vegetables", "efficiency"),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM arena_proposals WHERE title = ?",
            ("Test Proposal",),
        ).fetchone()
        conn.close()
        assert row is not None
        assert dict(row)["team_id"] == "alpha"

    def test_insert_evaluation(self, arena_db):
        """Success: insert evaluation linked to proposal."""
        conn = sqlite3.connect(arena_db)
        conn.execute(
            "INSERT INTO arena_proposals (title, team_id) VALUES (?,?)",
            ("Eval Test", "beta"),
        )
        conn.execute(
            "INSERT INTO arena_evaluations "
            "(proposal_id, tier, criterion, score) VALUES (?,?,?,?)",
            (1, "cto", "Feasibility", 4),
        )
        conn.commit()
        count = conn.execute(
            "SELECT COUNT(*) FROM arena_evaluations WHERE proposal_id = 1"
        ).fetchone()[0]
        conn.close()
        assert count == 1

    def test_team_stats_unique_constraint(self, arena_db):
        """Success: UNIQUE(team_id, period) enforced."""
        conn = sqlite3.connect(arena_db)
        conn.execute(
            "INSERT INTO arena_team_stats (team_id, period, total_proposals) "
            "VALUES (?,?,?)",
            ("alpha", "all_time", 5),
        )
        conn.execute(
            "INSERT OR REPLACE INTO arena_team_stats "
            "(team_id, period, total_proposals) VALUES (?,?,?)",
            ("alpha", "all_time", 10),
        )
        conn.commit()
        count = conn.execute(
            "SELECT COUNT(*) FROM arena_team_stats WHERE team_id = 'alpha'"
        ).fetchone()[0]
        assert count == 1
        val = conn.execute(
            "SELECT total_proposals FROM arena_team_stats "
            "WHERE team_id = 'alpha'"
        ).fetchone()[0]
        conn.close()
        assert val == 10

    def test_insert_insight(self, arena_db):
        """Success: insert and retrieve insight."""
        conn = sqlite3.connect(arena_db)
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO arena_insights (agent_id, team_id, department, "
            "insight_type, title, confidence) VALUES (?,?,?,?,?,?)",
            ("fp_waste", "gamma", "F&V", "risk", "Test Insight", 0.85),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM arena_insights WHERE title = ?",
            ("Test Insight",),
        ).fetchone()
        conn.close()
        assert row is not None
        assert dict(row)["confidence"] == 0.85

    def test_empty_proposals(self, arena_db):
        """Failure: empty table returns no rows."""
        conn = sqlite3.connect(arena_db)
        rows = conn.execute("SELECT * FROM arena_proposals").fetchall()
        conn.close()
        assert len(rows) == 0

    def test_empty_insights(self, arena_db):
        """Failure: empty insights table returns no rows."""
        conn = sqlite3.connect(arena_db)
        rows = conn.execute("SELECT * FROM arena_insights").fetchall()
        conn.close()
        assert len(rows) == 0


# ============================================================================
# DATA INTELLIGENCE TEAM TESTS
# ============================================================================

class TestDataIntelligenceAgents:
    """Test DATA_INTELLIGENCE_AGENTS constants."""

    def test_six_di_agents(self):
        """Success: exactly 6 Data Intelligence agents defined."""
        assert len(DATA_INTELLIGENCE_AGENTS) == 6

    def test_di_agent_ids_unique(self):
        """Success: all DI agent IDs are unique."""
        ids = [a["id"] for a in DATA_INTELLIGENCE_AGENTS]
        assert len(ids) == len(set(ids))

    def test_di_agents_start_with_prefix(self):
        """Success: all DI agent IDs start with 'di_'."""
        for a in DATA_INTELLIGENCE_AGENTS:
            assert a["id"].startswith("di_"), (
                "Agent {} doesn't start with 'di_'".format(a["id"]))

    def test_di_agents_reference_valid_teams(self):
        """Success: all DI agents reference a valid team_id."""
        team_ids = {t["id"] for t in AGENT_TEAMS}
        for agent in DATA_INTELLIGENCE_AGENTS:
            assert agent["team_id"] in team_ids

    def test_di_agents_have_required_fields(self):
        """Success: each DI agent has required fields."""
        required = ["id", "name", "team_id", "department",
                     "business_unit", "role", "capabilities",
                     "data_sources", "status", "kpis", "scoring"]
        for agent in DATA_INTELLIGENCE_AGENTS:
            for field in required:
                assert field in agent, (
                    "DI Agent {} missing field '{}'".format(
                        agent["id"], field))

    def test_di_agents_have_scoring_rules(self):
        """Success: each DI agent has scoring rules."""
        for agent in DATA_INTELLIGENCE_AGENTS:
            scoring = agent.get("scoring", {})
            assert len(scoring) > 0, (
                "Agent {} has no scoring rules".format(agent["id"]))
            for rule, pts in scoring.items():
                assert pts > 0, (
                    "Agent {} has non-positive scoring: {}".format(
                        agent["id"], rule))

    def test_get_data_intel_agent(self):
        """Success: get_data_intel_agent returns correct agent."""
        agent = get_data_intel_agent("di_lost_sales")
        assert agent is not None
        assert agent["name"] == "Lost Sales Detective"

    def test_get_data_intel_agent_nonexistent(self):
        """Failure: nonexistent DI agent returns None."""
        assert get_data_intel_agent("nonexistent_xyz") is None

    def test_get_agent_finds_di_agents(self):
        """Success: get_agent (unified) also finds DI agents."""
        agent = get_agent("di_transactions")
        assert agent is not None
        assert agent["name"] == "Transaction Pattern Intelligence"

    def test_di_no_overlap_with_department_agents(self):
        """Success: DI agent IDs don't overlap with department agents."""
        dept_ids = {a["id"] for a in DEPARTMENT_AGENTS}
        di_ids = {a["id"] for a in DATA_INTELLIGENCE_AGENTS}
        assert dept_ids.isdisjoint(di_ids)


class TestDataIntelCategories:
    """Test DATA_INTEL_CATEGORIES constants."""

    def test_six_categories(self):
        """Success: 6 data intelligence categories."""
        assert len(DATA_INTEL_CATEGORIES) == 6

    def test_category_ids_unique(self):
        """Success: all category IDs unique."""
        ids = [c["id"] for c in DATA_INTEL_CATEGORIES]
        assert len(ids) == len(set(ids))

    def test_categories_have_required_fields(self):
        """Success: each category has id, name, icon, description."""
        for cat in DATA_INTEL_CATEGORIES:
            assert "id" in cat
            assert "name" in cat
            assert "icon" in cat
            assert "description" in cat


class TestSeedDataIntelInsights:
    """Test SEED_DATA_INTEL_INSIGHTS."""

    def test_twelve_seed_di_insights(self):
        """Success: 12 pre-seeded DI insights."""
        assert len(SEED_DATA_INTEL_INSIGHTS) == 12

    def test_di_insights_reference_di_agents(self):
        """Success: all DI insights reference DI agents."""
        di_agent_ids = {a["id"] for a in DATA_INTELLIGENCE_AGENTS}
        for ins in SEED_DATA_INTEL_INSIGHTS:
            assert ins["agent_id"] in di_agent_ids, (
                "Insight '{}' references non-DI agent '{}'".format(
                    ins["title"], ins["agent_id"]))

    def test_di_insights_have_categories(self):
        """Success: all DI insights have a category field."""
        valid_cats = {c["id"] for c in DATA_INTEL_CATEGORIES}
        for ins in SEED_DATA_INTEL_INSIGHTS:
            assert "category" in ins
            assert ins["category"] in valid_cats, (
                "Insight '{}' has invalid category '{}'".format(
                    ins["title"], ins["category"]))

    def test_di_insights_confidence_in_range(self):
        """Success: confidence values between 0 and 1."""
        for ins in SEED_DATA_INTEL_INSIGHTS:
            assert 0 <= ins["confidence"] <= 1

    def test_di_insights_have_impact(self):
        """Success: all DI insights have positive impact."""
        for ins in SEED_DATA_INTEL_INSIGHTS:
            assert ins.get("potential_impact_aud", 0) > 0


# ============================================================================
# WATCHDOG SAFETY SERVICE TESTS
# ============================================================================

from shared.watchdog_safety import (
    WatchdogService, RISK_SAFE, RISK_LOW, RISK_MEDIUM, RISK_HIGH,
    RISK_BLOCKED, RISK_LEVELS, RISK_COLORS, RISK_ICONS,
    BLOCKED_ACTIONS, REQUIRES_SENIOR_APPROVAL,
)


class TestWatchdogRiskLevels:
    """Test risk level constants and mappings."""

    def test_all_risk_levels_defined(self):
        """Success: 5 risk levels defined."""
        assert len(RISK_LEVELS) == 5
        assert RISK_SAFE in RISK_LEVELS
        assert RISK_BLOCKED in RISK_LEVELS

    def test_all_risk_levels_have_colors(self):
        """Success: every risk level has a color."""
        for level in RISK_LEVELS:
            assert level in RISK_COLORS
            assert RISK_COLORS[level].startswith("#")

    def test_all_risk_levels_have_icons(self):
        """Success: every risk level has an icon."""
        for level in RISK_LEVELS:
            assert level in RISK_ICONS
            assert len(RISK_ICONS[level]) > 0

    def test_blocked_actions_not_empty(self):
        """Success: blocked actions list is populated."""
        assert len(BLOCKED_ACTIONS) >= 8

    def test_senior_approval_not_empty(self):
        """Success: senior approval list is populated."""
        assert len(REQUIRES_SENIOR_APPROVAL) >= 5


class TestWatchdogSafeProposal:
    """Test that clean proposals get SAFE risk level."""

    def test_safe_proposal_returns_safe(self):
        """Success: normal proposal gets SAFE."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test_agent",
            "title": "Improve dashboard layout",
            "description": "Reorganize the KPI cards for better readability",
        })
        assert result["risk_level"] == RISK_SAFE
        assert result["finding_count"] == 0
        assert result["blocked"] is False

    def test_safe_proposal_has_tracking_id(self):
        """Success: result includes WD- tracking ID."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Test",
            "description": "Test proposal",
        })
        assert result["tracking_id"].startswith("WD-")
        assert len(result["tracking_id"]) >= 10

    def test_safe_proposal_recommendation(self):
        """Success: safe proposal gets APPROVE recommendation."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Test safe",
            "description": "A simple improvement",
        })
        assert "APPROVE" in result["recommendation"]["decision"]
        assert result["recommendation"]["can_approve"] is True

    def test_safe_proposal_has_report(self):
        """Success: report is generated for safe proposal."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Test",
            "description": "Test",
        })
        assert "WATCHDOG Safety Report" in result["report"]
        assert "SAFE" in result["report"]


class TestWatchdogUnsafeDetection:
    """Test that dangerous proposals are correctly flagged."""

    def test_sql_injection_blocked(self):
        """Success: SQL injection in description triggers BLOCKED."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Data query",
            "description": "Run this query: ; DROP TABLE users;",
        })
        assert result["risk_level"] == RISK_BLOCKED
        assert result["blocked"] is True
        assert result["finding_count"] > 0

    def test_drop_table_action_blocked(self):
        """Success: drop table action is blocked."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Drop table cleanup",
            "description": "We need to drop table the old data",
        })
        assert result["risk_level"] == RISK_BLOCKED
        assert result["blocked"] is True

    def test_eval_exec_detected(self):
        """Success: eval/exec in code changes detected."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Dynamic code",
            "description": "Use eval() to execute dynamic expressions",
            "code_changes": "result = eval(user_input)",
        })
        assert result["finding_count"] > 0
        assert result["risk_level"] in (RISK_MEDIUM, RISK_HIGH, RISK_BLOCKED)

    def test_hardcoded_credentials_detected(self):
        """Success: hardcoded credentials flagged."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "API integration",
            "description": "Connect with api_key = 'sk-abcdef1234567890abcdef'",
        })
        assert result["finding_count"] > 0
        assert result["risk_level"] == RISK_BLOCKED  # Critical security

    def test_blocked_proposal_cannot_approve(self):
        """Failure: blocked proposals cannot be approved."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Delete database records",
            "description": "delete database entries from all tables",
        })
        assert result["blocked"] is True
        assert result["recommendation"]["can_approve"] is False

    def test_modify_watchdog_blocked(self):
        """Success: attempts to modify watchdog are blocked."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "System config change",
            "description": "We should modify watchdog settings to be less strict",
        })
        assert result["risk_level"] == RISK_BLOCKED

    def test_disable_safety_blocked(self):
        """Success: attempts to disable safety are blocked."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Efficiency improvement",
            "description": "We should disable safety checks for faster processing",
        })
        assert result["risk_level"] == RISK_BLOCKED


class TestWatchdogPrivacyScan:
    """Test PII and customer data detection."""

    def test_email_pii_detected(self):
        """Success: email patterns detected in proposal."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Customer analysis",
            "description": "Send results to john.doe@example.com",
        })
        privacy_findings = [
            f for f in result["findings"]
            if f["category"] == "privacy"
        ]
        assert len(privacy_findings) > 0

    def test_customer_data_access_flagged(self):
        """Success: customer data access triggers finding."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Customer report",
            "description": "Export customer_email and customer_phone for marketing",
        })
        privacy_findings = [
            f for f in result["findings"]
            if f["category"] == "privacy"
        ]
        assert len(privacy_findings) >= 1


class TestWatchdogBusinessValidation:
    """Test business logic validation."""

    def test_high_impact_flagged(self):
        """Success: >$1M impact gets flagged for review."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Revenue boost",
            "description": "Implement new pricing strategy",
            "estimated_impact_aud": 2000000,
        })
        biz_findings = [
            f for f in result["findings"]
            if f["category"] == "business"
        ]
        assert len(biz_findings) > 0

    def test_complexity_effort_mismatch(self):
        """Success: high complexity + low effort triggers finding."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Complex rebuild",
            "description": "Rebuild the entire analytics platform",
            "complexity": "high",
            "estimated_effort_weeks": 2,
        })
        mismatch_findings = [
            f for f in result["findings"]
            if "mismatch" in f.get("title", "").lower()
        ]
        assert len(mismatch_findings) > 0

    def test_pricing_change_needs_senior(self):
        """Success: pricing change triggers senior approval."""
        watchdog = WatchdogService()
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "Pricing strategy update",
            "description": "Implement pricing change across all stores",
        })
        senior_findings = [
            f for f in result["findings"]
            if "senior" in f.get("title", "").lower()
        ]
        assert len(senior_findings) > 0


class TestWatchdogRiskScoring:
    """Test risk score calculation."""

    def test_no_findings_is_safe(self):
        """Success: empty findings = SAFE."""
        watchdog = WatchdogService()
        assert watchdog.calculate_risk_score([]) == RISK_SAFE

    def test_medium_finding_is_low(self):
        """Success: medium findings = LOW risk."""
        watchdog = WatchdogService()
        findings = [{"severity": "medium", "category": "business",
                      "title": "Test"}]
        assert watchdog.calculate_risk_score(findings) == RISK_LOW

    def test_high_finding_is_medium(self):
        """Success: single high finding = MEDIUM risk."""
        watchdog = WatchdogService()
        findings = [{"severity": "high", "category": "safety",
                      "title": "Test"}]
        assert watchdog.calculate_risk_score(findings) == RISK_MEDIUM

    def test_multiple_high_is_high(self):
        """Success: 3+ high findings = HIGH risk."""
        watchdog = WatchdogService()
        findings = [
            {"severity": "high", "category": "safety", "title": "1"},
            {"severity": "high", "category": "privacy", "title": "2"},
            {"severity": "high", "category": "security", "title": "3"},
        ]
        assert watchdog.calculate_risk_score(findings) == RISK_HIGH

    def test_critical_security_is_blocked(self):
        """Success: critical security finding = BLOCKED."""
        watchdog = WatchdogService()
        findings = [{"severity": "critical", "category": "security",
                      "title": "SQL injection"}]
        assert watchdog.calculate_risk_score(findings) == RISK_BLOCKED

    def test_blocked_action_is_blocked(self):
        """Success: blocked action finding = BLOCKED."""
        watchdog = WatchdogService()
        findings = [{"severity": "critical", "category": "safety",
                      "title": "Blocked action: drop_table"}]
        assert watchdog.calculate_risk_score(findings) == RISK_BLOCKED


class TestWatchdogAuditDB:
    """Test WATCHDOG database operations."""

    def _make_db(self):
        """Create a temp database with WATCHDOG tables."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(path)
        conn.execute("""CREATE TABLE watchdog_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT, agent_id TEXT, title TEXT,
            risk_level TEXT, finding_count INTEGER,
            report TEXT, proposal_json TEXT, analyzed_at TEXT)""")
        conn.execute("""CREATE TABLE watchdog_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT, decision TEXT, approver TEXT,
            comments TEXT, decided_at TEXT)""")
        conn.execute("""CREATE TABLE watchdog_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT UNIQUE, source_proposal_id INTEGER,
            agent_id TEXT, title TEXT, description TEXT,
            proposal_json TEXT, risk_level TEXT, finding_count INTEGER,
            report TEXT, recommendation TEXT, status TEXT,
            reviewed_by TEXT, reviewed_at TEXT, comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.commit()
        conn.close()
        return path

    def test_analysis_logged_to_audit(self):
        """Success: analysis creates audit record."""
        db_path = self._make_db()
        try:
            watchdog = WatchdogService(db_path=db_path)
            result = watchdog.analyze_proposal({
                "agent_id": "test_agent",
                "title": "Test proposal",
                "description": "A simple test",
            })
            conn = sqlite3.connect(db_path)
            count = conn.execute(
                "SELECT COUNT(*) FROM watchdog_audit").fetchone()[0]
            conn.close()
            assert count == 1
        finally:
            os.unlink(db_path)

    def test_decision_logged(self):
        """Success: approve/reject decision is logged."""
        db_path = self._make_db()
        try:
            watchdog = WatchdogService(db_path=db_path)
            watchdog.log_decision("WD-TEST123", "approved",
                                  "Gus Harris", "Looks good")
            conn = sqlite3.connect(db_path)
            row = conn.execute(
                "SELECT * FROM watchdog_decisions"
            ).fetchone()
            conn.close()
            assert row is not None
            assert row[2] == "approved"  # decision
            assert row[3] == "Gus Harris"  # approver
        finally:
            os.unlink(db_path)

    def test_audit_without_db_no_crash(self):
        """Success: WatchdogService works without db_path."""
        watchdog = WatchdogService(db_path=None)
        result = watchdog.analyze_proposal({
            "agent_id": "test",
            "title": "No DB test",
            "description": "Should not crash",
        })
        assert result["risk_level"] == RISK_SAFE

    def test_is_safe_to_proceed_approved(self):
        """Success: approved proposal returns True."""
        from shared.watchdog_safety import is_safe_to_proceed
        db_path = self._make_db()
        try:
            watchdog = WatchdogService(db_path=db_path)
            result = watchdog.analyze_proposal({
                "agent_id": "test",
                "title": "Safe proposal",
                "description": "A clean proposal",
            })
            tracking_id = result["tracking_id"]
            watchdog.log_decision(tracking_id, "approved",
                                  "Gus Harris", "OK")
            safe, reason = is_safe_to_proceed(tracking_id, db_path)
            assert safe is True
            assert "Approved" in reason
        finally:
            os.unlink(db_path)

    def test_is_safe_to_proceed_rejected(self):
        """Failure: rejected proposal returns False."""
        from shared.watchdog_safety import is_safe_to_proceed
        db_path = self._make_db()
        try:
            watchdog = WatchdogService(db_path=db_path)
            result = watchdog.analyze_proposal({
                "agent_id": "test",
                "title": "Test rejection",
                "description": "Will be rejected",
            })
            tracking_id = result["tracking_id"]
            watchdog.log_decision(tracking_id, "rejected",
                                  "Operator", "Not suitable")
            safe, reason = is_safe_to_proceed(tracking_id, db_path)
            assert safe is False
            assert "Rejected" in reason
        finally:
            os.unlink(db_path)

    def test_is_safe_to_proceed_no_decision(self):
        """Failure: proposal without decision returns False."""
        from shared.watchdog_safety import is_safe_to_proceed
        db_path = self._make_db()
        try:
            watchdog = WatchdogService(db_path=db_path)
            result = watchdog.analyze_proposal({
                "agent_id": "test",
                "title": "Pending test",
                "description": "No decision yet",
            })
            tracking_id = result["tracking_id"]
            safe, reason = is_safe_to_proceed(tracking_id, db_path)
            assert safe is False
            assert "Awaiting" in reason
        finally:
            os.unlink(db_path)
