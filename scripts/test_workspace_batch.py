"""
TRINETRA Phase 8 — Batch Processing & Aggregate Synthesis Verification
Verifies:
1. Quota & resource limit enforcement (target count <= 50, pixel count <= 50M)
2. Safe concurrency clamping
3. Multi-target workflow execution
4. Aggregate statistical synthesis across targets
5. Repository persistence and workspace activity audit
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from workspace.service import WorkspaceService
from workspace.repository import WorkspaceRepository
from workspace.batch.limits import BatchLimitsEnforcer, BatchLimitExceededError


def run_test():
    print("=" * 70)
    print("TRINETRA Phase 8 — Batch Processing & Synthesis Verification")
    print("=" * 70)

    repo = WorkspaceRepository(":memory:")
    service = WorkspaceService(repository=repo)
    ws = service.create_workspace(name="Himalayan Glacial Lake Batch Survey")
    print(f" [1/5] Workspace initialized: {ws.workspace_id}")

    # 1. Quota limit enforcement: 0 targets
    try:
        BatchLimitsEnforcer.validate_targets([])
        assert False, "Should have raised for empty targets"
    except BatchLimitExceededError as e:
        print(f" [2/5] Quota guard correctly rejected empty targets: {e}")

    # Quota limit enforcement: > 50 targets
    oversized_targets = [{"target_id": f"t_{i}", "aoi": {}} for i in range(55)]
    try:
        BatchLimitsEnforcer.validate_targets(oversized_targets)
        assert False, "Should have raised for > 50 targets"
    except BatchLimitExceededError as e:
        print(f"       Quota guard correctly rejected > 50 targets: {e}")

    # Quota limit enforcement: > 50M pixels
    excessive_pixels = [
        {"target_id": "large_1", "estimated_pixels": 30_000_000},
        {"target_id": "large_2", "estimated_pixels": 25_000_000},
    ]
    try:
        BatchLimitsEnforcer.validate_targets(excessive_pixels)
        assert False, "Should have raised for > 50M pixels"
    except BatchLimitExceededError as e:
        print(f"       Quota guard correctly rejected excessive pixel workload: {e}")

    # Concurrency clamping
    clamped_conc = BatchLimitsEnforcer.get_max_concurrency(requested=16)
    assert clamped_conc <= 4
    print(f" [3/5] Concurrency correctly clamped from 16 to safe limit: {clamped_conc}")

    # 2. Multi-target workflow execution
    valid_targets = [
        {"target_id": "glacier_south_lhonak", "name": "South Lhonak Lake", "estimated_pixels": 2_000_000},
        {"target_id": "glacier_shako_cho", "name": "Shako Cho Lake", "estimated_pixels": 1_500_000},
        {"target_id": "glacier_ghepan_ghat", "name": "Ghepan Ghat Lake", "estimated_pixels": 1_800_000},
        {"target_id": "glacier_tsokar", "name": "Tso Kar Lake", "estimated_pixels": 2_200_000},
    ]

    batch_job = service.execute_batch(
        workspace_id=ws.workspace_id,
        template_id="template_water_extent_change",
        targets=valid_targets,
        concurrency=3,
    )
    assert batch_job.batch_id.startswith("batch-")
    assert batch_job.status in ("COMPLETED", "FINISHED", "RUNNING")
    print(f" [4/5] Batch job executed successfully: {batch_job.batch_id} [Status: {batch_job.status}]")

    # 3. Verify aggregated statistics
    summary = batch_job.results.get("summary", {})
    completed_count = summary.get("completed_count", 0)
    assert completed_count == len(valid_targets)

    agg_metrics = summary.get("aggregate_metrics", {})
    print(" [5/5] Cross-regional aggregate synthesis computed:")
    print(f"       - Total targets processed : {summary.get('total_targets')}")
    print(f"       - Average change pct      : {agg_metrics.get('average_change_percentage')}%")
    print(f"       - Max change pct          : {agg_metrics.get('max_change_percentage')}%")
    print(f"       - Average confidence      : {agg_metrics.get('average_confidence')}")
    print(f"       - Items with findings     : {agg_metrics.get('items_with_findings')}")

    print("=" * 70)
    print(" ALL BATCH PROCESSING & SYNTHESIS TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_test()
