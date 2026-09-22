"""
TRINETRA Phase 8 — Priority Task Queue
Thread-safe priority queue managing analytical task scheduling.
"""

import heapq
import threading
from typing import Optional, List, Dict

try:
    from backend.workspace.models import WorkspaceTask
    from backend.workspace.task_queue.models import QueueItem
except ImportError:
    from workspace.models import WorkspaceTask
    from workspace.task_queue.models import QueueItem


class PriorityTaskQueue:
    """
    Thread-safe priority queue prioritizing INTERACTIVE > NORMAL > BACKGROUND tasks.
    """

    def __init__(self):
        self._heap: List[QueueItem] = []
        self._lock = threading.Lock()
        self._sequence = 0
        self._task_map: Dict[str, QueueItem] = {}

    def push(self, task: WorkspaceTask) -> None:
        with self._lock:
            self._sequence += 1
            item = QueueItem(task, sequence=self._sequence)
            heapq.heappush(self._heap, item)
            self._task_map[task.task_id] = item

    def pop(self) -> Optional[WorkspaceTask]:
        with self._lock:
            while self._heap:
                item = heapq.heappop(self._heap)
                if item.task.task_id in self._task_map:
                    del self._task_map[item.task.task_id]
                    return item.task
            return None

    def peek(self) -> Optional[WorkspaceTask]:
        with self._lock:
            if self._heap:
                return self._heap[0].task
            return None

    def size(self) -> int:
        with self._lock:
            return len(self._task_map)

    def remove(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self._task_map:
                del self._task_map[task_id]
                # Rebuild heap without deleted task
                self._heap = [item for item in self._heap if item.task.task_id != task_id]
                heapq.heapify(self._heap)
                return True
            return False
