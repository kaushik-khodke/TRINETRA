"""
TRINETRA Phase 8 — Workspace Task Execution Service
Coordinates task lifecycle, priority queue dispatch, progress updates, idempotency, and cancellation.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from backend.workspace.models import WorkspaceTask, TaskPriority, TaskStatus
    from backend.workspace.task_queue.queue import PriorityTaskQueue
except ImportError:
    from workspace.models import WorkspaceTask, TaskPriority, TaskStatus
    from workspace.task_queue.queue import PriorityTaskQueue


class WorkspaceTaskService:
    """
    Manages background and interactive task submissions with priority scheduling.
    """

    def __init__(self, repository=None, activity_tracker=None):
        self.repository = repository
        self.activity_tracker = activity_tracker
        self.queue = PriorityTaskQueue()

    def submit_task(
        self,
        workspace_id: str,
        type: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        parameters: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> WorkspaceTask:
        """
        Submits an analytical task. If an idempotency key matches an existing task,
        returns the existing task instead of re-submitting.
        """
        if idempotency_key and self.repository:
            existing = self.repository.get_task_by_idempotency_key(idempotency_key)
            if existing:
                return existing

        task_id = f"task-{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        task = WorkspaceTask(
            task_id=task_id,
            workspace_id=workspace_id,
            type=type,
            priority=priority,
            status=TaskStatus.QUEUED,
            progress={"stage": "QUEUED", "percentage": 0.0},
            result_reference=None,
            error=None,
            idempotency_key=idempotency_key,
            created_at=now_str,
        )

        if self.repository:
            self.repository.save_task(task)

        self.queue.push(task)

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=workspace_id,
                activity_type="TASK_SUBMITTED",
                entity_type="TASK",
                entity_id=task.task_id,
                details={"type": type, "priority": task.priority.value},
            )

        return task

    def update_progress(
        self,
        task_id: str,
        stage: str,
        percentage: float,
    ) -> Optional[WorkspaceTask]:
        """
        Updates task execution stage and completion percentage.
        """
        if not self.repository:
            return None

        task = self.repository.get_task(task_id)
        if not task:
            return None

        task.status = TaskStatus.RUNNING
        task.progress = {"stage": stage, "percentage": round(min(100.0, max(0.0, percentage)), 1)}
        if not task.started_at:
            task.started_at = datetime.now(timezone.utc).isoformat()

        self.repository.save_task(task)
        return task

    def complete_task(
        self,
        task_id: str,
        result_reference: Optional[str] = None,
    ) -> Optional[WorkspaceTask]:
        if not self.repository:
            return None

        task = self.repository.get_task(task_id)
        if not task:
            return None

        task.status = TaskStatus.COMPLETED
        task.progress = {"stage": "COMPLETED", "percentage": 100.0}
        task.result_reference = result_reference
        task.completed_at = datetime.now(timezone.utc).isoformat()

        self.repository.save_task(task)

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=task.workspace_id,
                activity_type="TASK_COMPLETED",
                entity_type="TASK",
                entity_id=task.task_id,
                details={"type": task.type, "result_reference": result_reference},
            )

        return task

    def fail_task(
        self,
        task_id: str,
        error: Optional[Dict[str, Any]] = None,
    ) -> Optional[WorkspaceTask]:
        if not self.repository:
            return None

        task = self.repository.get_task(task_id)
        if not task:
            return None

        task.status = TaskStatus.FAILED
        task.error = error or {"message": "Unknown task failure"}
        task.completed_at = datetime.now(timezone.utc).isoformat()

        self.repository.save_task(task)

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=task.workspace_id,
                activity_type="TASK_FAILED",
                entity_type="TASK",
                entity_id=task.task_id,
                details={"type": task.type, "error": task.error},
            )

        return task

    def cancel_task(self, task_id: str) -> bool:
        self.queue.remove(task_id)
        if not self.repository:
            return True

        task = self.repository.get_task(task_id)
        if not task:
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now(timezone.utc).isoformat()
        self.repository.save_task(task)

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=task.workspace_id,
                activity_type="TASK_CANCELLED",
                entity_type="TASK",
                entity_id=task.task_id,
                details={"type": task.type},
            )

        return True
