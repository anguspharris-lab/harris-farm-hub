"""Worker module — wraps Claude CLI invocation with git worktree isolation."""
import subprocess
import time
import os
from pathlib import Path
from datetime import datetime
from .models import Task, WorkerResult, TaskStatus
from .audit import log_task_start, log_task_end, log_error

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_CLI = "/usr/local/bin/claude"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def build_prompt(task: Task) -> str:
    """Assemble the full prompt for a Claude CLI agent.

    Structure: base preamble + role prompt + task instructions.
    """
    base_path = PROMPTS_DIR / "base.md"
    base_prompt = base_path.read_text() if base_path.exists() else ""

    role_path = PROMPTS_DIR / f"{task.agent_role}.md"
    role_prompt = role_path.read_text() if role_path.exists() else ""

    files_list = "\n".join(f"- {f}" for f in task.files_to_touch) if task.files_to_touch else "- (as needed)"

    return f"""{base_prompt}

## Your Role
{role_prompt}

## Your Task
Task ID: {task.id}
Task Name: {task.name}
Branch: {task.branch_name}

## Instructions
{task.description}

## Files You May Modify
{files_list}

## Rules
- Work ONLY on your branch. Do NOT merge to main. Do NOT push.
- Commit your changes with a clear message when done.
- Log actions to watchdog/audit.log.
- Run tests after changes: python3 -m pytest tests/ -v
- Do NOT modify: CLAUDE.md, watchdog/scan.sh, watchdog/shutdown.sh, watchdog/health.sh
"""


def run_worker(task: Task, worktree_path: Path, timeout: int = 300) -> WorkerResult:
    """Execute a Claude CLI agent in an isolated git worktree.

    Args:
        task: The Task to execute (branch_name must be set).
        worktree_path: Path to the git worktree directory.
        timeout: Max seconds before killing the process.

    Returns:
        WorkerResult with captured output and metadata.
    """
    start_time = time.time()
    task.status = TaskStatus.IN_PROGRESS
    task.started_at = datetime.now()

    log_task_start(task.id, task.agent_role, task.branch_name)
    prompt = build_prompt(task)

    try:
        result = subprocess.run(
            [CLAUDE_CLI, "--dangerously-skip-permissions", "-p",
             "--model", "sonnet",
             "--allowedTools", "Bash,Edit,Write,Read,Glob,Grep"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(worktree_path),
            env={**os.environ, "GIT_BRANCH": task.branch_name},
        )
        stdout = result.stdout
        stderr = result.stderr
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = f"TIMEOUT: Task {task.id} exceeded {timeout}s"
        exit_code = -1
        log_error(f"task_{task.id}", f"Timeout after {timeout}s")
    except Exception as e:
        stdout = ""
        stderr = str(e)
        exit_code = -1
        log_error(f"task_{task.id}", str(e))

    # Commit any changes in the worktree
    subprocess.run(
        ["git", "add", "-A"],
        cwd=str(worktree_path),
        capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"[{task.id}] {task.name}",
         "--allow-empty"],
        cwd=str(worktree_path),
        capture_output=True, text=True,
    )

    # Get changed files
    diff_result = subprocess.run(
        ["git", "diff", "--name-only", "main", task.branch_name],
        cwd=str(worktree_path),
        capture_output=True, text=True,
    )
    files_changed = [f for f in diff_result.stdout.strip().split("\n") if f]

    duration = time.time() - start_time
    task.status = TaskStatus.COMPLETED if exit_code == 0 else TaskStatus.FAILED
    task.completed_at = datetime.now()
    task.exit_code = exit_code
    task.worker_output = stdout
    task.error_message = stderr if exit_code != 0 else ""

    log_task_end(task.id, exit_code, duration)

    return WorkerResult(
        task=task,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        branch_name=task.branch_name,
        duration_seconds=duration,
        files_changed=files_changed,
    )
