"""Shared data models for the orchestrator."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SafetyVerdict(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class Task:
    """A single unit of work assigned to one agent."""
    id: str
    phase: int
    name: str
    description: str
    agent_role: str
    files_to_touch: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    branch_name: str = ""
    worker_output: str = ""
    exit_code: int = -1
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: str = ""


@dataclass
class SafetyCheckResult:
    """Result of a single safety check."""
    check_name: str
    verdict: SafetyVerdict
    details: str
    duration_seconds: float = 0.0


@dataclass
class SafetyReport:
    """Aggregated safety report for a phase transition."""
    phase: int
    checks: List[SafetyCheckResult]
    overall_verdict: SafetyVerdict
    scores: Dict[str, int] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def passed(self) -> bool:
        return self.overall_verdict == SafetyVerdict.PASS


@dataclass
class WorkerResult:
    """Result returned from a completed worker process."""
    task: Task
    stdout: str
    stderr: str
    exit_code: int
    branch_name: str
    duration_seconds: float
    files_changed: List[str] = field(default_factory=list)


@dataclass
class Phase:
    """A group of tasks that execute together."""
    number: int
    name: str
    tasks: List[Task]
    success_criteria: str = ""


@dataclass
class Mission:
    """Complete mission definition loaded from config."""
    name: str
    description: str
    phases: List[Phase]
    abort_on_safety_fail: bool = True
    max_retries_per_task: int = 1
    timeout_seconds_per_task: int = 300
