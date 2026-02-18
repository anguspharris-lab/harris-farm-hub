"""Phase-based task queue with dependency resolution."""
from typing import List, Dict, Optional
from .models import Mission, Phase, Task, TaskStatus


class TaskQueue:
    """Manages task execution order within and across phases."""

    def __init__(self, mission: Mission):
        self.mission = mission
        self._index: Dict[str, Task] = {}
        for phase in mission.phases:
            for task in phase.tasks:
                self._index[task.id] = task

    def get_phase(self, phase_num: int) -> Optional[Phase]:
        for phase in self.mission.phases:
            if phase.number == phase_num:
                return phase
        return None

    def get_ready_tasks(self, phase_num: int) -> List[Task]:
        """Get all pending tasks whose dependencies are completed."""
        phase = self.get_phase(phase_num)
        if not phase:
            return []

        ready = []
        for task in phase.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            deps_met = all(
                self._index[dep].status == TaskStatus.COMPLETED
                for dep in task.depends_on
                if dep in self._index
            )
            if deps_met:
                ready.append(task)
        return ready

    def phase_complete(self, phase_num: int) -> bool:
        """True if all tasks in phase are in a terminal state."""
        phase = self.get_phase(phase_num)
        if not phase:
            return True
        terminal = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED}
        return all(t.status in terminal for t in phase.tasks)

    def phase_all_succeeded(self, phase_num: int) -> bool:
        phase = self.get_phase(phase_num)
        if not phase:
            return True
        return all(t.status == TaskStatus.COMPLETED for t in phase.tasks)

    def total_phases(self) -> int:
        return len(self.mission.phases)

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._index.get(task_id)

    def summary(self) -> str:
        lines = []
        for phase in self.mission.phases:
            counts: Dict[str, int] = {}
            for t in phase.tasks:
                s = t.status.value
                counts[s] = counts.get(s, 0) + 1
            counts_str = ", ".join(f"{v} {k}" for k, v in counts.items())
            lines.append(f"Phase {phase.number} ({phase.name}): {counts_str}")
        return "\n".join(lines)
