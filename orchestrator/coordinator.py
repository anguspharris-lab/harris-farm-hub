"""Coordinator — manages parallel workers via git worktrees, merge/rollback."""
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List
from .models import Task, WorkerResult, TaskStatus, Phase
from .task_queue import TaskQueue
from .worker import run_worker
from .audit import log_phase_start, log_git, log_error

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKTREE_DIR = PROJECT_ROOT / ".worktrees"


def setup_worktree(task: Task) -> Path:
    """Create an isolated git worktree for a worker.

    Each worker gets a separate directory branched from main.
    This allows true parallel git operations.
    """
    branch_name = f"orch/{task.id}/{task.agent_role}".replace(" ", "_").lower()
    task.branch_name = branch_name
    worktree_path = WORKTREE_DIR / task.id

    # Clean up if exists from previous run
    if worktree_path.exists():
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
        )

    # Delete old branch if exists
    subprocess.run(
        ["git", "branch", "-D", branch_name],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )

    # Create worktree with new branch from main
    result = subprocess.run(
        ["git", "worktree", "add", "-b", branch_name, str(worktree_path), "main"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to create worktree: {result.stderr}")

    log_git("worktree_create", f"{worktree_path} on {branch_name}")
    return worktree_path


def teardown_worktree(task: Task) -> None:
    """Remove a worker's worktree after completion."""
    worktree_path = WORKTREE_DIR / task.id
    if worktree_path.exists():
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
        )
        log_git("worktree_remove", str(worktree_path))


def merge_branch(branch_name: str) -> bool:
    """Merge a worker's branch into main. Returns True on success."""
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )

    result = subprocess.run(
        ["git", "merge", "--no-ff", branch_name,
         "-m", f"Merge {branch_name} (orchestrator)"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        subprocess.run(
            ["git", "merge", "--abort"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
        )
        log_git("merge_fail", f"{branch_name}: {result.stderr.strip()}")
        return False

    log_git("merge_success", branch_name)
    return True


def rollback_to_commit(commit_hash: str) -> None:
    """Roll back main to a specific commit."""
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "reset", "--hard", commit_hash],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    log_git("rollback", f"Reset main to {commit_hash}")


def get_current_commit() -> str:
    """Get the current HEAD commit hash on main."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def execute_phase(
    phase: Phase,
    task_queue: TaskQueue,
    max_parallel: int = 3,
    timeout_per_task: int = 300,
) -> List[WorkerResult]:
    """Execute all tasks in a phase with parallel workers.

    Uses ThreadPoolExecutor with git worktrees for isolation.
    Handles dependencies: only tasks with met deps are dispatched.
    """
    all_results: List[WorkerResult] = []

    log_phase_start(phase.number, phase.name, len(phase.tasks))

    WORKTREE_DIR.mkdir(exist_ok=True)

    while not task_queue.phase_complete(phase.number):
        ready = task_queue.get_ready_tasks(phase.number)

        if not ready:
            # Dependency deadlock — skip remaining
            remaining = [t for t in phase.tasks if t.status == TaskStatus.PENDING]
            for t in remaining:
                t.status = TaskStatus.SKIPPED
                t.error_message = "Dependency deadlock — skipped"
                log_error(f"task_{t.id}", "Dependency deadlock")
            break

        with ThreadPoolExecutor(max_workers=min(max_parallel, len(ready))) as executor:
            future_map = {}
            for task in ready:
                task.status = TaskStatus.IN_PROGRESS
                worktree_path = setup_worktree(task)
                future = executor.submit(run_worker, task, worktree_path, timeout_per_task)
                future_map[future] = task

            for future in as_completed(future_map):
                task = future_map[future]
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error_message = str(e)
                    log_error(f"task_{task.id}", str(e))
                finally:
                    teardown_worktree(task)

    return all_results
