"""
TRINETRA Phase 8 Tests — Batch Execution Subsystem
Verifies resource limits, concurrency scheduling, and aggregate metric synthesis.
"""

import pytest
from workspace.batch.limits import BatchLimitsEnforcer, BatchLimitExceededError
from workspace.batch.models import BatchTarget
from workspace.batch.scheduler import BatchScheduler
from workspace.batch.executor import BatchExecutor
from workspace.repository import WorkspaceRepository


@pytest.fixture
def repo():
    return WorkspaceRepository(":memory:")


@pytest.fixture
def executor(repo):
    return BatchExecutor(repository=repo)


def test_batch_limits_target_count_violation():
    # Attempt 55 targets (limit is 50)
    targets = [{"target_id": f"t-{i}", "estimated_pixels": 500_000} for i in range(55)]
    with pytest.raises(BatchLimitExceededError) as exc:
        BatchLimitsEnforcer.validate_targets(targets)
    assert "exceeds maximum permitted threshold" in str(exc.value)


def test_batch_limits_pixel_quota_violation():
    # 2 targets with 30,000,000 pixels each = 60M (limit is 50M)
    targets = [
        {"target_id": "t-1", "estimated_pixels": 30_000_000},
        {"target_id": "t-2", "estimated_pixels": 30_000_000},
    ]
    with pytest.raises(BatchLimitExceededError) as exc:
        BatchLimitsEnforcer.validate_targets(targets)
    assert "exceeds quota" in str(exc.value)


def test_batch_scheduler_partitioning():
    targets = [BatchTarget(f"t-{i}") for i in range(7)]
    scheduler = BatchScheduler(concurrency=3)
    chunks = scheduler.chunk_targets(targets)

    assert len(chunks) == 3
    assert len(chunks[0]) == 3
    assert len(chunks[1]) == 3
    assert len(chunks[2]) == 1


def test_batch_executor_run_and_synthesis(executor):
    targets = [
        {"target_id": "tgt-delhi", "region_id": "reg-delhi", "estimated_pixels": 1_000_000},
        {"target_id": "tgt-mumbai", "region_id": "reg-mumbai", "estimated_pixels": 1_000_000},
        {"target_id": "tgt-chennai", "region_id": "reg-chennai", "estimated_pixels": 1_000_000},
    ]

    job = executor.execute_batch(
        workspace_id="ws-batch-test",
        template_id="tpl-urban-surface-change",
        targets=targets,
        concurrency=2,
    )

    assert job.status in ["COMPLETED", "PARTIAL"]
    assert "summary" in job.results
    summary = job.results["summary"]
    assert summary["total_targets"] == 3
    assert summary["completed_count"] == 3
    assert "average_change_percentage" in summary["aggregate_metrics"]
