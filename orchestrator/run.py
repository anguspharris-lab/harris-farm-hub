#!/usr/bin/env python3
"""
Harris Farm Hub — Multi-Agent Orchestrator

Usage:
    python3 orchestrator/run.py missions/fabric_prep.json
    python3 orchestrator/run.py missions/fabric_prep.json --dry-run
    python3 orchestrator/run.py missions/fabric_prep.json --max-parallel 2 --timeout 600
"""
import sys
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.config import load_mission
from orchestrator.task_queue import TaskQueue
from orchestrator.coordinator import (
    execute_phase, merge_branch, rollback_to_commit,
    get_current_commit, WORKTREE_DIR,
)
from orchestrator.safety import run_safety_pipeline
from orchestrator.audit import log_audit, log_phase_end, log_error
from orchestrator.models import SafetyVerdict


def verify_claude_md() -> bool:
    """Verify CLAUDE.md integrity per session start protocol."""
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    checksum_file = PROJECT_ROOT / "watchdog" / ".claude_md_checksum"

    if not claude_md.exists() or not checksum_file.exists():
        return False

    actual = hashlib.sha256(claude_md.read_bytes()).hexdigest()
    expected = checksum_file.read_text().strip()
    return actual == expected


def print_report(results_by_phase: dict, safety_reports: list) -> None:
    """Print a human-readable summary of the mission execution."""
    print("\n" + "=" * 60)
    print("MISSION EXECUTION REPORT")
    print("=" * 60)

    for phase_num, results in sorted(results_by_phase.items()):
        print(f"\nPhase {phase_num}:")
        for r in results:
            status = "PASS" if r.exit_code == 0 else "FAIL"
            print(f"  [{status}] {r.task.name} ({r.duration_seconds:.1f}s)")
            if r.files_changed:
                for f in r.files_changed:
                    print(f"        changed: {f}")

    print("\nSafety Reports:")
    for report in safety_reports:
        verdict = "PASS" if report.passed else "FAIL"
        print(f"  Phase {report.phase}: {verdict}")
        for check in report.checks:
            icon = "+" if check.verdict == SafetyVerdict.PASS else ("-" if check.verdict == SafetyVerdict.FAIL else "~")
            print(f"    [{icon}] {check.check_name}: {check.details[:80]}")
        if report.scores:
            scores_str = " ".join(f"{k}:{v}" for k, v in report.scores.items())
            print(f"    Scores: {scores_str}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Harris Farm Hub Multi-Agent Orchestrator"
    )
    parser.add_argument("mission", help="Path to mission config JSON file")
    parser.add_argument("--max-parallel", type=int, default=3,
                        help="Max parallel workers per phase (default: 3)")
    parser.add_argument("--timeout", type=int, default=0,
                        help="Timeout per task in seconds (0 = use mission config)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate config without executing")
    args = parser.parse_args()

    # Step 0: Verify CLAUDE.md integrity
    if not verify_claude_md():
        print("WARNING: CLAUDE.md checksum verification failed or missing.")
        print("Proceeding with caution — watchdog governance may not be enforced.")
        log_audit("ORCH_WARN", "CLAUDE.md checksum mismatch — proceeding anyway")

    # Step 1: Load mission
    log_audit("ORCH_START", f"Loading mission: {args.mission}")
    try:
        mission = load_mission(args.mission)
    except (FileNotFoundError, ValueError) as e:
        print(f"FATAL: {e}")
        log_error("config", str(e))
        sys.exit(1)

    print(f"\nMission: {mission.name}")
    print(f"Description: {mission.description}")
    print(f"Phases: {len(mission.phases)}")
    for phase in mission.phases:
        print(f"  Phase {phase.number}: {phase.name} ({len(phase.tasks)} tasks)")

    if args.dry_run:
        print("\n[DRY RUN] Config valid. Exiting.")
        sys.exit(0)

    # Step 2: Initialize
    task_queue = TaskQueue(mission)
    results_by_phase: dict = {}
    safety_reports = []
    timeout = args.timeout or mission.timeout_seconds_per_task

    WORKTREE_DIR.mkdir(exist_ok=True)

    # Step 3: Phase loop
    for phase in mission.phases:
        print(f"\n{'='*40}")
        print(f"Phase {phase.number}: {phase.name}")
        print(f"{'='*40}")

        pre_phase_commit = get_current_commit()
        log_audit("ORCH_PHASE", f"Pre-phase commit: {pre_phase_commit[:8]}")

        # Execute tasks
        results = execute_phase(
            phase, task_queue,
            max_parallel=args.max_parallel,
            timeout_per_task=timeout,
        )
        results_by_phase[phase.number] = results

        # Safety pipeline
        print("Running safety checks...")
        safety_report = run_safety_pipeline(phase.number, results)
        safety_reports.append(safety_report)

        if safety_report.passed:
            print(f"Safety: PASSED")
            log_phase_end(phase.number, phase.name, "PASS")

            # Merge successful branches
            for r in results:
                if r.exit_code == 0 and r.branch_name:
                    merged = merge_branch(r.branch_name)
                    if not merged:
                        print(f"  WARNING: Merge conflict on {r.branch_name}")
        else:
            print(f"Safety: FAILED")
            log_phase_end(phase.number, phase.name, "FAIL")

            if mission.abort_on_safety_fail:
                print(f"Rolling back to {pre_phase_commit[:8]}...")
                rollback_to_commit(pre_phase_commit)
                log_audit("ORCH_ABORT", f"Mission aborted at phase {phase.number}")
                break
            else:
                print("Continuing despite safety failure (abort_on_safety_fail=false)")

    # Step 4: Report
    print_report(results_by_phase, safety_reports)

    # Step 5: Final audit
    total_tasks = sum(len(r) for r in results_by_phase.values())
    passed_tasks = sum(
        1 for rs in results_by_phase.values() for r in rs if r.exit_code == 0
    )
    log_audit(
        "ORCH_COMPLETE",
        f"Mission '{mission.name}' complete | "
        f"{passed_tasks}/{total_tasks} tasks passed | "
        f"{len(safety_reports)} phases checked"
    )

    print(f"\nDone. {passed_tasks}/{total_tasks} tasks passed.")


if __name__ == "__main__":
    main()
