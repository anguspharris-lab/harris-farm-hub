"""Tests for the multi-agent orchestrator."""
import json
import os
import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Import orchestrator modules
from orchestrator.models import (
    Task, Phase, Mission, SafetyReport, SafetyCheckResult,
    WorkerResult, TaskStatus, SafetyVerdict,
)
from orchestrator.config import load_mission, _parse_mission, VALID_ROLES
from orchestrator.task_queue import TaskQueue
from orchestrator.audit import log_audit, AUDIT_LOG
from orchestrator.worker import build_prompt


# ============================================================================
# MODELS
# ============================================================================

class TestTaskModel:
    def test_task_creation_defaults(self):
        """Success: Task initialises with correct defaults."""
        task = Task(id="t1", phase=1, name="Test", description="Desc", agent_role="architect")
        assert task.status == TaskStatus.PENDING
        assert task.exit_code == -1
        assert task.branch_name == ""
        assert task.files_to_touch == []
        assert task.depends_on == []

    def test_task_status_transitions(self):
        """Success: Task status can be set to any valid value."""
        task = Task(id="t1", phase=1, name="Test", description="Desc", agent_role="architect")
        task.status = TaskStatus.IN_PROGRESS
        assert task.status == TaskStatus.IN_PROGRESS
        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED

    def test_task_with_dependencies(self):
        """Success: Task tracks its dependencies."""
        task = Task(id="t2", phase=1, name="Test", description="Desc",
                    agent_role="architect", depends_on=["t1"])
        assert task.depends_on == ["t1"]


class TestSafetyReportModel:
    def test_report_passed_when_all_pass(self):
        """Success: passed is True when overall verdict is PASS."""
        report = SafetyReport(
            phase=1,
            checks=[SafetyCheckResult("pytest", SafetyVerdict.PASS, "52 passed")],
            overall_verdict=SafetyVerdict.PASS,
        )
        assert report.passed is True

    def test_report_failed_when_verdict_fail(self):
        """Failure: passed is False when overall verdict is FAIL."""
        report = SafetyReport(
            phase=1,
            checks=[SafetyCheckResult("pytest", SafetyVerdict.FAIL, "3 failed")],
            overall_verdict=SafetyVerdict.FAIL,
        )
        assert report.passed is False


class TestWorkerResultModel:
    def test_worker_result_creation(self):
        """Success: WorkerResult holds all fields."""
        task = Task(id="t1", phase=1, name="Test", description="D", agent_role="architect")
        wr = WorkerResult(
            task=task, stdout="output", stderr="", exit_code=0,
            branch_name="orch/t1/architect", duration_seconds=5.0,
            files_changed=["file.py"],
        )
        assert wr.exit_code == 0
        assert wr.files_changed == ["file.py"]


# ============================================================================
# CONFIG
# ============================================================================

class TestConfigLoading:
    def test_load_valid_mission(self, tmp_path):
        """Success: Valid JSON loads into Mission object."""
        config = {
            "name": "Test Mission",
            "description": "A test",
            "phases": [{
                "name": "Phase 1",
                "tasks": [{
                    "name": "Task 1",
                    "description": "Do something",
                    "agent_role": "architect"
                }]
            }]
        }
        config_file = tmp_path / "mission.json"
        config_file.write_text(json.dumps(config))

        mission = load_mission(str(config_file))
        assert mission.name == "Test Mission"
        assert len(mission.phases) == 1
        assert len(mission.phases[0].tasks) == 1
        assert mission.phases[0].tasks[0].agent_role == "architect"

    def test_load_missing_file(self):
        """Failure: FileNotFoundError on nonexistent path."""
        with pytest.raises(FileNotFoundError):
            load_mission("/nonexistent/mission.json")

    def test_invalid_agent_role(self, tmp_path):
        """Failure: ValueError on unknown agent_role."""
        config = {
            "name": "Bad Mission",
            "description": "Test",
            "phases": [{
                "name": "Phase 1",
                "tasks": [{
                    "name": "Task 1",
                    "description": "Desc",
                    "agent_role": "hacker"
                }]
            }]
        }
        config_file = tmp_path / "bad.json"
        config_file.write_text(json.dumps(config))

        with pytest.raises(ValueError, match="Invalid agent_role"):
            load_mission(str(config_file))

    def test_missing_required_fields(self, tmp_path):
        """Failure: ValueError when required fields are missing."""
        config = {"name": "Incomplete"}  # missing description and phases
        config_file = tmp_path / "incomplete.json"
        config_file.write_text(json.dumps(config))

        with pytest.raises(ValueError, match="Missing required field"):
            load_mission(str(config_file))

    def test_valid_roles_defined(self):
        """Success: VALID_ROLES contains expected agent types."""
        assert "data_engineer" in VALID_ROLES
        assert "test_engineer" in VALID_ROLES
        assert "safety_reviewer" in VALID_ROLES
        assert "architect" in VALID_ROLES

    def test_task_ids_auto_generated(self, tmp_path):
        """Success: Task IDs are auto-generated from phase/task index."""
        config = {
            "name": "Test", "description": "Test",
            "phases": [{
                "name": "P1",
                "tasks": [
                    {"name": "T1", "description": "D", "agent_role": "architect"},
                    {"name": "T2", "description": "D", "agent_role": "architect"},
                ]
            }]
        }
        config_file = tmp_path / "m.json"
        config_file.write_text(json.dumps(config))
        mission = load_mission(str(config_file))
        assert mission.phases[0].tasks[0].id == "phase1_task1"
        assert mission.phases[0].tasks[1].id == "phase1_task2"

    def test_mission_defaults(self, tmp_path):
        """Success: Mission has correct defaults when optional fields omitted."""
        config = {
            "name": "Minimal", "description": "Test",
            "phases": [{"name": "P1", "tasks": [
                {"name": "T", "description": "D", "agent_role": "architect"}
            ]}]
        }
        config_file = tmp_path / "m.json"
        config_file.write_text(json.dumps(config))
        mission = load_mission(str(config_file))
        assert mission.abort_on_safety_fail is True
        assert mission.max_retries_per_task == 1
        assert mission.timeout_seconds_per_task == 300


# ============================================================================
# TASK QUEUE
# ============================================================================

class TestTaskQueue:
    def _make_mission(self, tasks_phase1, tasks_phase2=None):
        """Helper to create a Mission with 1-2 phases."""
        phases = [Phase(number=1, name="P1", tasks=tasks_phase1)]
        if tasks_phase2:
            phases.append(Phase(number=2, name="P2", tasks=tasks_phase2))
        return Mission(name="Test", description="Test", phases=phases)

    def test_get_ready_tasks_no_deps(self):
        """Success: All pending tasks are ready when no dependencies."""
        t1 = Task(id="p1_t1", phase=1, name="T1", description="D", agent_role="architect")
        t2 = Task(id="p1_t2", phase=1, name="T2", description="D", agent_role="architect")
        mission = self._make_mission([t1, t2])
        queue = TaskQueue(mission)

        ready = queue.get_ready_tasks(1)
        assert len(ready) == 2

    def test_get_ready_tasks_with_deps(self):
        """Success: Dependent task not ready until dependency completes."""
        t1 = Task(id="p1_t1", phase=1, name="T1", description="D", agent_role="architect")
        t2 = Task(id="p1_t2", phase=1, name="T2", description="D",
                  agent_role="architect", depends_on=["p1_t1"])
        mission = self._make_mission([t1, t2])
        queue = TaskQueue(mission)

        ready = queue.get_ready_tasks(1)
        assert len(ready) == 1
        assert ready[0].id == "p1_t1"

        # Complete t1, now t2 should be ready
        t1.status = TaskStatus.COMPLETED
        ready = queue.get_ready_tasks(1)
        assert len(ready) == 1
        assert ready[0].id == "p1_t2"

    def test_phase_complete(self):
        """Success: Phase is complete when all tasks are terminal."""
        t1 = Task(id="p1_t1", phase=1, name="T1", description="D", agent_role="architect")
        mission = self._make_mission([t1])
        queue = TaskQueue(mission)

        assert queue.phase_complete(1) is False
        t1.status = TaskStatus.COMPLETED
        assert queue.phase_complete(1) is True

    def test_phase_complete_with_failed(self):
        """Success: Phase is complete even with failed tasks."""
        t1 = Task(id="p1_t1", phase=1, name="T1", description="D", agent_role="architect")
        mission = self._make_mission([t1])
        queue = TaskQueue(mission)

        t1.status = TaskStatus.FAILED
        assert queue.phase_complete(1) is True

    def test_phase_all_succeeded(self):
        """Failure: phase_all_succeeded is False when a task failed."""
        t1 = Task(id="p1_t1", phase=1, name="T1", description="D", agent_role="architect")
        t2 = Task(id="p1_t2", phase=1, name="T2", description="D", agent_role="architect")
        mission = self._make_mission([t1, t2])
        queue = TaskQueue(mission)

        t1.status = TaskStatus.COMPLETED
        t2.status = TaskStatus.FAILED
        assert queue.phase_all_succeeded(1) is False

    def test_nonexistent_phase(self):
        """Success: Nonexistent phase returns empty/True gracefully."""
        t1 = Task(id="p1_t1", phase=1, name="T1", description="D", agent_role="architect")
        mission = self._make_mission([t1])
        queue = TaskQueue(mission)

        assert queue.get_ready_tasks(99) == []
        assert queue.phase_complete(99) is True

    def test_summary(self):
        """Success: Summary produces readable output."""
        t1 = Task(id="p1_t1", phase=1, name="T1", description="D", agent_role="architect")
        t1.status = TaskStatus.COMPLETED
        t2 = Task(id="p1_t2", phase=1, name="T2", description="D", agent_role="architect")
        mission = self._make_mission([t1, t2])
        queue = TaskQueue(mission)

        summary = queue.summary()
        assert "Phase 1" in summary
        assert "completed" in summary
        assert "pending" in summary


# ============================================================================
# WORKER (prompt building only — CLI invocation mocked)
# ============================================================================

class TestWorkerPromptBuilding:
    def test_build_prompt_includes_task_info(self):
        """Success: Built prompt contains task name and description."""
        task = Task(
            id="p1_t1", phase=1, name="Extract stores",
            description="Move store list to shared module",
            agent_role="architect", branch_name="orch/p1_t1/architect",
        )
        prompt = build_prompt(task)
        assert "Extract stores" in prompt
        assert "Move store list to shared module" in prompt
        assert "orch/p1_t1/architect" in prompt

    def test_build_prompt_includes_files_list(self):
        """Success: Built prompt lists files to touch."""
        task = Task(
            id="p1_t1", phase=1, name="Test",
            description="Desc", agent_role="architect",
            branch_name="b", files_to_touch=["a.py", "b.py"],
        )
        prompt = build_prompt(task)
        assert "a.py" in prompt
        assert "b.py" in prompt

    def test_build_prompt_includes_rules(self):
        """Success: Built prompt includes safety rules."""
        task = Task(
            id="p1_t1", phase=1, name="Test",
            description="Desc", agent_role="architect",
            branch_name="b",
        )
        prompt = build_prompt(task)
        assert "Do NOT merge to main" in prompt
        assert "Do NOT modify: CLAUDE.md" in prompt


# ============================================================================
# AUDIT
# ============================================================================

class TestAudit:
    def test_log_audit_writes_to_file(self, tmp_path, monkeypatch):
        """Success: log_audit appends to audit log file."""
        test_log = tmp_path / "audit.log"
        test_log.touch()
        monkeypatch.setattr("orchestrator.audit.AUDIT_LOG", test_log)

        log_audit("TEST", "hello world")
        content = test_log.read_text()
        assert "[TEST]" in content
        assert "hello world" in content
        assert "ORCHESTRATOR" in content

    def test_log_audit_appends_not_overwrites(self, tmp_path, monkeypatch):
        """Success: Multiple log calls append, not overwrite."""
        test_log = tmp_path / "audit.log"
        test_log.write_text("existing line\n")
        monkeypatch.setattr("orchestrator.audit.AUDIT_LOG", test_log)

        log_audit("TEST", "new entry")
        content = test_log.read_text()
        assert "existing line" in content
        assert "new entry" in content


# ============================================================================
# SAFETY (unit tests — subprocess calls mocked)
# ============================================================================

class TestSafetyDiffReview:
    def test_diff_review_detects_protected_file(self, monkeypatch):
        """Failure: Diff review catches CLAUDE.md modification."""
        from orchestrator import safety

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "--name-only" in cmd:
                result.stdout = "CLAUDE.md\nsome_file.py"
                result.returncode = 0
            else:
                result.stdout = "diff content"
                result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)
        check = safety.review_git_diff("test-branch")
        assert check.verdict == SafetyVerdict.FAIL
        assert "PROTECTED FILE MODIFIED" in check.details

    def test_diff_review_passes_clean_diff(self, monkeypatch):
        """Success: Clean diff passes review."""
        from orchestrator import safety

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "--name-only" in cmd:
                result.stdout = "dashboards/sales_dashboard.py"
                result.returncode = 0
            else:
                result.stdout = "--- a/dashboards/sales_dashboard.py\n+++ b/dashboards/sales_dashboard.py\n+new line"
                result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)
        check = safety.review_git_diff("test-branch")
        assert check.verdict == SafetyVerdict.PASS

    def test_diff_review_detects_secret(self, monkeypatch):
        """Failure: Diff review catches hardcoded API key."""
        from orchestrator import safety

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "--name-only" in cmd:
                result.stdout = "config.py"
                result.returncode = 0
            else:
                result.stdout = '+db_password = "hunter2verysecretvalue99"'
                result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)
        check = safety.review_git_diff("test-branch")
        assert check.verdict == SafetyVerdict.FAIL
        assert "POTENTIAL SECRET" in check.details


class TestSafetyPipeline:
    def test_pipeline_passes_when_all_pass(self, monkeypatch):
        """Success: Overall verdict is PASS when all hard gates pass."""
        from orchestrator import safety

        monkeypatch.setattr(safety, "run_pytest",
                            lambda: SafetyCheckResult("pytest", SafetyVerdict.PASS, "52 passed"))
        monkeypatch.setattr(safety, "run_scan_sh",
                            lambda: SafetyCheckResult("scan_sh", SafetyVerdict.PASS, "clean"))
        monkeypatch.setattr(safety, "run_health_sh",
                            lambda: SafetyCheckResult("health_sh", SafetyVerdict.WARN, "down"))

        report = safety.run_safety_pipeline(1, [])
        assert report.passed is True

    def test_pipeline_fails_on_pytest_failure(self, monkeypatch):
        """Failure: Overall verdict is FAIL when pytest fails."""
        from orchestrator import safety

        monkeypatch.setattr(safety, "run_pytest",
                            lambda: SafetyCheckResult("pytest", SafetyVerdict.FAIL, "3 failed"))
        monkeypatch.setattr(safety, "run_scan_sh",
                            lambda: SafetyCheckResult("scan_sh", SafetyVerdict.PASS, "clean"))
        monkeypatch.setattr(safety, "run_health_sh",
                            lambda: SafetyCheckResult("health_sh", SafetyVerdict.PASS, "ok"))

        report = safety.run_safety_pipeline(1, [])
        assert report.passed is False


# ============================================================================
# INTEGRATION — dry-run and config validation
# ============================================================================

class TestIntegration:
    def test_dry_run_validates_config(self):
        """Success: --dry-run exits 0 on valid config."""
        mission_path = PROJECT_ROOT / "orchestrator" / "missions" / "fabric_prep.json"
        if not mission_path.exists():
            pytest.skip("fabric_prep.json not found")

        result = subprocess.run(
            ["python3", "orchestrator/run.py", str(mission_path), "--dry-run"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "DRY RUN" in result.stdout

    def test_dry_run_fails_on_bad_config(self, tmp_path):
        """Failure: --dry-run exits 1 on invalid config."""
        bad_config = tmp_path / "bad.json"
        bad_config.write_text('{"name": "bad"}')

        result = subprocess.run(
            ["python3", "orchestrator/run.py", str(bad_config), "--dry-run"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "FATAL" in result.stdout

    def test_dry_run_fails_on_missing_config(self):
        """Failure: --dry-run exits 1 on missing file."""
        result = subprocess.run(
            ["python3", "orchestrator/run.py", "/nonexistent.json", "--dry-run"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
            timeout=10,
        )
        assert result.returncode == 1
