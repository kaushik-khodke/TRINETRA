"""
TRINETRA Phase 8 Tests — Workspace Task Queue Subsystem
Verifies priority scheduling, idempotency guards, stage progress, and task cancellations.
"""

import pytest
from workspace.models import TaskPriority, TaskStatus
from workspace.task_queue.service import WorkspaceTaskService
from workspace.repository import WorkspaceRepository


@pytest.fixture
def repo():
    return WorkspaceRepository(":memory:")


@pytest.fixture
def service(repo):
    return WorkspaceTaskService(repository=repo)


def test_priority_scheduling_order(service):
    ws_id = "ws-queue-test"

    # Push background, then normal, then interactive
    t_bg = service.submit_task(ws_id, "BACKGROUND_EXPORT", priority=TaskPriority.BACKGROUND)
    t_norm = service.submit_task(ws_id, "NORMAL_MONITOR", priority=TaskPriority.NORMAL)
    t_inter = service.submit_task(ws_id, "INTERACTIVE_SEARCH", priority=TaskPriority.INTERACTIVE)

    # Pop order must be INTERACTIVE -> NORMAL -> BACKGROUND
    p1 = service.queue.pop()
    p2 = service.queue.pop()
    p3 = service.queue.pop()

    assert p1.task_id == t_inter.task_id
    assert p2.task_id == t_norm.task_id
    assert p3.task_id == t_bg.task_id


def test_task_idempotency(service):
    ws_id = "ws-idem-test"
    key = "unique-run-2026-09"

    t1 = service.submit_task(ws_id, "ANALYSIS", idempotency_key=key)
    t2 = service.submit_task(ws_id, "ANALYSIS", idempotency_key=key)

    assert t1.task_id == t2.task_id
    assert service.queue.size() == 1  # Only queued once


def test_task_stage_progress_and_completion(service):
    ws_id = "ws-prog-test"
    task = service.submit_task(ws_id, "BATCH_ANALYSIS")

    # Update progress
    updated = service.update_progress(task.task_id, stage="FETCHING_DATASETS", percentage=25.0)
    assert updated.status == TaskStatus.RUNNING
    assert updated.progress["stage"] == "FETCHING_DATASETS"
    assert updated.progress["percentage"] == 25.0

    # Complete task
    completed = service.complete_task(task.task_id, result_reference="ref-out-77")
    assert completed.status == TaskStatus.COMPLETED
    assert completed.progress["percentage"] == 100.0
    assert completed.result_reference == "ref-out-77"


def test_task_cancellation(service):
    ws_id = "ws-cancel-test"
    task = service.submit_task(ws_id, "LONG_RUN")
    assert service.queue.size() == 1

    cancelled = service.cancel_task(task.task_id)
    assert cancelled is True
    assert service.queue.size() == 0

    fetched = service.repository.get_task(task.task_id)
    assert fetched.status == TaskStatus.CANCELLED
