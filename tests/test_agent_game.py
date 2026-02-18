"""Tests for the Gamified Agent Ecosystem: agents, points, achievements, API."""

import os
import sys
import sqlite3
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


# ---------------------------------------------------------------------------
# Game Agents Registry Tests
# ---------------------------------------------------------------------------

class TestGameAgentsRegistry:
    """Verify the 6 game agent definitions."""

    def test_six_agents_defined(self):
        from agent_game import GAME_AGENTS
        assert len(GAME_AGENTS) == 6

    def test_all_agents_have_required_fields(self):
        from agent_game import GAME_AGENTS
        required = {"name", "specialty", "category", "analysis_types", "system_prompt"}
        for agent in GAME_AGENTS:
            for field in required:
                assert field in agent, "{} missing {}".format(agent.get("name"), field)
                assert agent[field], "{} has empty {}".format(agent.get("name"), field)

    def test_categories_are_valid(self):
        from agent_game import GAME_AGENTS
        valid = {"REVENUE_OPTIMIZATION", "DATA_VISIBILITY",
                 "OPERATIONAL_EFFICIENCY", "STRATEGIC_PLANNING", "INSIGHTS"}
        for agent in GAME_AGENTS:
            assert agent["category"] in valid, (
                "{} has invalid category {}".format(agent["name"], agent["category"])
            )

    def test_agent_names_are_unique(self):
        from agent_game import GAME_AGENTS
        names = [a["name"] for a in GAME_AGENTS]
        assert len(names) == len(set(names))


# ---------------------------------------------------------------------------
# Points Calculation Tests
# ---------------------------------------------------------------------------

class TestPointsCalculation:
    """Test the calculate_points function."""

    def test_base_completion_points(self):
        from agent_game import calculate_points
        points, breakdown = calculate_points("ANALYSIS", "Draft", 5.0, 0)
        assert points == 100
        assert "base:100" in breakdown

    def test_board_ready_bonus(self):
        from agent_game import calculate_points
        points, _ = calculate_points("ANALYSIS", "Board-ready", 9.5, 0)
        assert points == 100 + 300  # base + board_ready

    def test_reviewed_bonus(self):
        from agent_game import calculate_points
        points, _ = calculate_points("ANALYSIS", "Reviewed", 7.5, 0)
        assert points == 100 + 150  # base + reviewed

    def test_revenue_bonus(self):
        from agent_game import calculate_points
        points, breakdown = calculate_points("ANALYSIS", "Draft", 5.0, 50000)
        # 50000 / 10000 = 5 units * 1000 = 5000
        assert points == 100 + 5000
        assert "revenue:5000" in breakdown

    def test_dashboard_task_bonus(self):
        from agent_game import calculate_points
        points, breakdown = calculate_points("DASHBOARD_DESIGN", "Draft", 5.0, 0)
        assert points == 100 + 150
        assert "dashboard:150" in breakdown

    def test_planning_task_bonus(self):
        from agent_game import calculate_points
        points, _ = calculate_points("PLANNING", "Draft", 5.0, 0)
        assert points == 100 + 400

    def test_combined_bonuses(self):
        from agent_game import calculate_points
        # Board-ready + revenue
        points, _ = calculate_points("ANALYSIS", "Board-ready", 9.2, 30000)
        # 100 base + 300 board_ready + 3000 revenue
        assert points == 3400


# ---------------------------------------------------------------------------
# Seed Agents Tests
# ---------------------------------------------------------------------------

class TestSeedAgents:
    """Test seeding game agents into the database."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB

    def test_seed_creates_six_agents(self):
        from agent_game import seed_game_agents
        seed_game_agents(self.db_path)
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM game_agents").fetchone()[0]
        conn.close()
        assert count >= 6

    def test_seed_is_idempotent(self):
        from agent_game import seed_game_agents
        first = seed_game_agents(self.db_path)
        second = seed_game_agents(self.db_path)
        # Second run should insert 0 (all already exist)
        assert second == 0

    def test_agents_have_system_prompts(self):
        from agent_game import seed_game_agents
        seed_game_agents(self.db_path)
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT name, system_prompt FROM game_agents"
        ).fetchall()
        conn.close()
        for name, prompt in rows:
            assert prompt and len(prompt) > 50, (
                "{} has no system prompt".format(name)
            )


# ---------------------------------------------------------------------------
# Seed Tasks Tests
# ---------------------------------------------------------------------------

class TestSeedTasks:
    """Test seeding initial analysis tasks."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB
        from agent_game import seed_game_agents
        seed_game_agents(self.db_path)

    def test_seed_creates_eighteen_tasks(self):
        from agent_game import seed_initial_tasks
        seed_initial_tasks(self.db_path)
        conn = sqlite3.connect(self.db_path)
        from agent_game import GAME_AGENTS
        agent_names = [a["name"] for a in GAME_AGENTS]
        placeholders = ",".join(["?"] * len(agent_names))
        count = conn.execute(
            "SELECT COUNT(*) FROM agent_proposals WHERE agent_name IN ({})".format(
                placeholders
            ),
            agent_names,
        ).fetchone()[0]
        conn.close()
        assert count >= 18

    def test_all_tasks_approved(self):
        from agent_game import seed_initial_tasks
        seed_initial_tasks(self.db_path)
        conn = sqlite3.connect(self.db_path)
        from agent_game import GAME_AGENTS
        agent_names = [a["name"] for a in GAME_AGENTS]
        placeholders = ",".join(["?"] * len(agent_names))
        rows = conn.execute(
            "SELECT status FROM agent_proposals "
            "WHERE agent_name IN ({}) AND status IN ('APPROVED', 'COMPLETED')".format(
                placeholders),
            agent_names,
        ).fetchall()
        conn.close()
        assert len(rows) >= 18

    def test_three_tasks_per_agent(self):
        from agent_game import seed_initial_tasks, GAME_AGENTS
        seed_initial_tasks(self.db_path)
        conn = sqlite3.connect(self.db_path)
        for agent in GAME_AGENTS:
            count = conn.execute(
                "SELECT COUNT(*) FROM agent_proposals WHERE agent_name = ?",
                (agent["name"],),
            ).fetchone()[0]
            assert count >= 3, "{} has only {} tasks".format(agent["name"], count)
        conn.close()


# ---------------------------------------------------------------------------
# Award Points Tests
# ---------------------------------------------------------------------------

class TestAwardPoints:
    """Test point awarding and totals."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB
        from agent_game import seed_game_agents
        seed_game_agents(self.db_path)
        # Reset points for test agent
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE game_agents SET total_points = 0, reports_completed = 0 "
            "WHERE name = 'StockoutRevenueHunter'"
        )
        conn.commit()
        conn.close()

    def test_points_logged(self):
        from agent_game import award_game_points
        result = award_game_points(
            self.db_path, "StockoutRevenueHunter", 9999, 250, "test:250"
        )
        assert result == 250

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT points, breakdown FROM game_points_log "
            "WHERE agent_name = 'StockoutRevenueHunter' AND proposal_id = 9999"
        ).fetchone()
        conn.close()
        assert row[0] == 250
        assert row[1] == "test:250"

    def test_agent_totals_updated(self):
        from agent_game import award_game_points
        award_game_points(
            self.db_path, "StockoutRevenueHunter", 9998, 100, "base:100"
        )
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT total_points, reports_completed FROM game_agents "
            "WHERE name = 'StockoutRevenueHunter'"
        ).fetchone()
        conn.close()
        assert row[0] >= 100
        assert row[1] >= 1

    def test_multiplier_applied(self):
        from agent_game import award_game_points
        result = award_game_points(
            self.db_path, "StockoutRevenueHunter", 9997, 100, "base:100",
            multiplier=2.0,
        )
        assert result == 200


# ---------------------------------------------------------------------------
# Achievement Tests
# ---------------------------------------------------------------------------

class TestAchievements:
    """Test achievement checking and awarding."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB
        from agent_game import seed_game_agents
        seed_game_agents(self.db_path)

    def test_first_analysis_badge(self):
        from agent_game import check_game_achievements
        # Ensure at least 1 report completed
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE game_agents SET reports_completed = 1 "
            "WHERE name = 'CrossSellRevenueEngine'"
        )
        conn.commit()
        conn.close()

        awarded = check_game_achievements(self.db_path, "CrossSellRevenueEngine")
        # Should include first_analysis (or it was already earned)
        conn = sqlite3.connect(self.db_path)
        has_it = conn.execute(
            "SELECT COUNT(*) FROM game_achievements "
            "WHERE agent_name = 'CrossSellRevenueEngine' "
            "AND achievement_code = 'first_analysis'"
        ).fetchone()[0]
        conn.close()
        assert has_it >= 1

    def test_duplicate_achievement_idempotent(self):
        from agent_game import check_game_achievements
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE game_agents SET reports_completed = 1 "
            "WHERE name = 'BuyerInsightDashboarder'"
        )
        conn.commit()
        conn.close()

        check_game_achievements(self.db_path, "BuyerInsightDashboarder")
        check_game_achievements(self.db_path, "BuyerInsightDashboarder")

        conn = sqlite3.connect(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM game_achievements "
            "WHERE agent_name = 'BuyerInsightDashboarder' "
            "AND achievement_code = 'first_analysis'"
        ).fetchone()[0]
        conn.close()
        assert count == 1  # Only awarded once

    def test_achievements_list(self):
        from agent_game import ACHIEVEMENTS
        assert len(ACHIEVEMENTS) >= 5
        for ach in ACHIEVEMENTS:
            assert "code" in ach
            assert "name" in ach
            assert "points" in ach
            assert ach["points"] > 0


# ---------------------------------------------------------------------------
# Leaderboard Tests
# ---------------------------------------------------------------------------

class TestGameLeaderboard:
    """Test leaderboard retrieval."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        from app import config
        self.db_path = config.HUB_DB
        from agent_game import seed_game_agents
        seed_game_agents(self.db_path)

    def test_returns_ranked_list(self):
        from agent_game import get_game_leaderboard
        lb = get_game_leaderboard(self.db_path)
        assert len(lb) >= 6
        for entry in lb:
            assert "rank" in entry
            assert "name" in entry
            assert "total_points" in entry

    def test_correct_ordering(self):
        from agent_game import get_game_leaderboard
        # Give one agent clearly the most points
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE game_agents SET total_points = 999999 "
            "WHERE name = 'TransactionInsightMiner'"
        )
        conn.commit()
        conn.close()

        lb = get_game_leaderboard(self.db_path)
        assert lb[0]["name"] == "TransactionInsightMiner"
        assert lb[0]["rank"] == 1

    def test_game_status(self):
        from agent_game import get_game_status
        status = get_game_status(self.db_path)
        assert "agent_count" in status
        assert "total_points" in status
        assert "total_reports" in status
        assert "total_revenue" in status
        assert status["agent_count"] >= 6


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------

class TestGameAPI:
    """Test game API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        try:
            from app import app as fastapi_app
            from fastapi.testclient import TestClient
            self.client = TestClient(fastapi_app)
        except Exception:
            pytest.skip("FastAPI app not importable")

    def test_leaderboard_endpoint(self):
        # Seed first
        self.client.post("/api/game/seed")
        resp = self.client.get("/api/game/leaderboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "agents" in data
        assert len(data["agents"]) >= 6

    def test_seed_endpoint(self):
        resp = self.client.post("/api/game/seed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "agents_inserted" in data
        assert "tasks_inserted" in data

    def test_status_endpoint(self):
        self.client.post("/api/game/seed")
        resp = self.client.get("/api/game/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_count"] >= 6

    def test_agent_detail_endpoint(self):
        self.client.post("/api/game/seed")
        resp = self.client.get("/api/game/agents/StockoutRevenueHunter")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "StockoutRevenueHunter"
        assert "achievements" in data
        assert "recent_points" in data

    def test_agent_detail_not_found(self):
        resp = self.client.get("/api/game/agents/NonexistentAgent")
        assert resp.status_code == 404

    def test_achievements_endpoint(self):
        resp = self.client.get("/api/game/achievements")
        assert resp.status_code == 200
        data = resp.json()
        assert "achievements" in data
        assert isinstance(data["achievements"], list)
