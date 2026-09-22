"""
TRINETRA Phase 8 — Task Queue Data Structures
Priority wrappers and queue item ordering for heapq scheduling.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

try:
    from backend.workspace.models import WorkspaceTask, TaskPriority
except ImportError:
    from workspace.models import WorkspaceTask, TaskPriority


class QueueItem:
    """
    Heap priority queue element ordered by TaskPriority (INTERACTIVE < NORMAL < BACKGROUND)
    and insertion sequence.
    """

    PRIORITY_WEIGHTS = {
        TaskPriority.INTERACTIVE: 1,
        TaskPriority.NORMAL: 2,
        TaskPriority.BACKGROUND: 3,
    }

    def __init__(self, task: WorkspaceTask, sequence: int = 0):
        self.task = task
        self.sequence = sequence
        pri = task.priority if isinstance(task.priority, TaskPriority) else TaskPriority(task.priority)
        self.weight = self.PRIORITY_WEIGHTS.get(pri, 2)

    def __lt__(self, other: "QueueItem") -> bool:
        if self.weight != other.weight:
            return self.weight < other.weight
        return self.sequence < other.sequence
