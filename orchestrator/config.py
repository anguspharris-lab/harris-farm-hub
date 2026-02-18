"""Mission configuration loading and validation."""
import json
from pathlib import Path
from .models import Mission, Phase, Task


VALID_ROLES = {"data_engineer", "test_engineer", "safety_reviewer", "architect"}


def load_mission(config_path: str) -> Mission:
    """Load and validate a mission configuration from JSON."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Mission config not found: {config_path}")

    with open(path) as f:
        raw = json.load(f)

    return _parse_mission(raw)


def _parse_mission(raw: dict) -> Mission:
    """Parse raw JSON dict into Mission dataclass."""
    _validate_required(raw, ["name", "description", "phases"])

    phases = []
    for i, phase_raw in enumerate(raw["phases"], start=1):
        _validate_required(phase_raw, ["name", "tasks"])

        tasks = []
        for j, task_raw in enumerate(phase_raw["tasks"]):
            _validate_required(task_raw, ["name", "description", "agent_role"])
            _validate_role(task_raw["agent_role"])

            task = Task(
                id=task_raw.get("id", f"phase{i}_task{j+1}"),
                phase=i,
                name=task_raw["name"],
                description=task_raw["description"],
                agent_role=task_raw["agent_role"],
                files_to_touch=task_raw.get("files_to_touch", []),
                depends_on=task_raw.get("depends_on", []),
            )
            tasks.append(task)

        phase = Phase(
            number=i,
            name=phase_raw["name"],
            tasks=tasks,
            success_criteria=phase_raw.get("success_criteria", ""),
        )
        phases.append(phase)

    return Mission(
        name=raw["name"],
        description=raw["description"],
        phases=phases,
        abort_on_safety_fail=raw.get("abort_on_safety_fail", True),
        max_retries_per_task=raw.get("max_retries_per_task", 1),
        timeout_seconds_per_task=raw.get("timeout_seconds_per_task", 300),
    )


def _validate_role(role: str) -> None:
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid agent_role '{role}'. Must be one of: {VALID_ROLES}")


def _validate_required(d: dict, fields: list) -> None:
    for f in fields:
        if f not in d:
            raise ValueError(f"Missing required field: '{f}'")
