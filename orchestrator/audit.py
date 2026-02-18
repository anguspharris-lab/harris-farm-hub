"""Thread-safe audit logging for the orchestrator."""
import threading
from datetime import datetime
from pathlib import Path

_lock = threading.Lock()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIT_LOG = PROJECT_ROOT / "watchdog" / "audit.log"


def log_audit(tag: str, message: str, agent: str = "ORCHESTRATOR") -> None:
    """Append a timestamped entry to watchdog/audit.log."""
    timestamp = datetime.now().isoformat()
    line = f"[{tag}] {timestamp} | {agent} | {message}\n"
    with _lock:
        with open(AUDIT_LOG, "a") as f:
            f.write(line)


def log_phase_start(phase_num: int, phase_name: str, task_count: int) -> None:
    log_audit("ORCH_PHASE", f"Phase {phase_num} ({phase_name}) starting | {task_count} tasks")


def log_phase_end(phase_num: int, phase_name: str, verdict: str) -> None:
    log_audit("ORCH_PHASE", f"Phase {phase_num} ({phase_name}) ended | verdict: {verdict}")


def log_task_start(task_id: str, agent_role: str, branch: str) -> None:
    log_audit("ORCH_TASK", f"Task {task_id} started | role: {agent_role} | branch: {branch}")


def log_task_end(task_id: str, exit_code: int, duration: float) -> None:
    log_audit("ORCH_TASK", f"Task {task_id} ended | exit: {exit_code} | duration: {duration:.1f}s")


def log_safety(check_name: str, verdict: str, details: str) -> None:
    log_audit("ORCH_SAFETY", f"{check_name} | {verdict} | {details}")


def log_git(action: str, details: str) -> None:
    log_audit("ORCH_GIT", f"{action} | {details}")


def log_error(context: str, error: str) -> None:
    log_audit("ORCH_ERROR", f"{context} | {error}")
