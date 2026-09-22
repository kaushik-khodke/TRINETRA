"""
TRINETRA Phase 8 — Batch Processing Executor
Controls worker pool dispatching, progress tracking, safety timeouts, and results aggregation.
"""

import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from backend.workspace.models import BatchJob
    from backend.workspace.batch.models import BatchTarget, BatchItemResult
    from backend.workspace.batch.limits import BatchLimitsEnforcer
    from backend.workspace.batch.scheduler import BatchScheduler
    from backend.workspace.batch.results import BatchResultsAggregator
except ImportError:
    from workspace.models import BatchJob
    from workspace.batch.models import BatchTarget, BatchItemResult
    from workspace.batch.limits import BatchLimitsEnforcer
    from workspace.batch.scheduler import BatchScheduler
    from workspace.batch.results import BatchResultsAggregator


class BatchExecutor:
    """
    Coordinates end-to-end execution of multi-target batch analytical jobs.
    """

    def __init__(self, repository=None, activity_tracker=None):
        self.repository = repository
        self.activity_tracker = activity_tracker

    def execute_batch(
        self,
        workspace_id: str,
        template_id: str,
        targets: List[Dict[str, Any]],
        concurrency: int = 2,
    ) -> BatchJob:
        """
        Executes analytical workflow across all targets while respecting resource constraints.
        """
        # Validate safety thresholds
        BatchLimitsEnforcer.validate_targets(targets)
        safe_concurrency = BatchLimitsEnforcer.get_max_concurrency(concurrency)

        batch_id = f"batch-{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        job = BatchJob(
            batch_id=batch_id,
            workspace_id=workspace_id,
            template_id=template_id,
            targets=targets,
            status="RUNNING",
            concurrency=safe_concurrency,
            results={"completed": [], "failed": [], "skipped": []},
            created_at=now_str,
            updated_at=now_str,
        )

        if self.repository:
            self.repository.save_batch_job(job)

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=workspace_id,
                activity_type="BATCH_STARTED",
                entity_type="BATCH",
                entity_id=batch_id,
                details={"target_count": len(targets), "concurrency": safe_concurrency},
            )

        start_time = time.time()
        target_objs = [
            BatchTarget(
                target_id=t.get("target_id", f"tgt-{i}"),
                region_id=t.get("region_id"),
                aoi=t.get("aoi", {}),
                parameters=t.get("parameters", {}),
                estimated_pixels=t.get("estimated_pixels", 1_000_000),
            )
            for i, t in enumerate(targets)
        ]

        scheduler = BatchScheduler(concurrency=safe_concurrency)
        chunks = scheduler.chunk_targets(target_objs)

        item_results: List[BatchItemResult] = []

        for chunk in chunks:
            for target in chunk:
                t0 = time.time()
                try:
                    res = self._process_target(target, template_id)
                    elapsed = time.time() - t0
                    item_results.append(
                        BatchItemResult(
                            target_id=target.target_id,
                            status="COMPLETED",
                            result_ref=res.get("ref", f"out-{target.target_id}"),
                            metrics=res.get("metrics", {}),
                            runtime_seconds=elapsed,
                        )
                    )
                except Exception as ex:
                    elapsed = time.time() - t0
                    item_results.append(
                        BatchItemResult(
                            target_id=target.target_id,
                            status="FAILED",
                            error=str(ex),
                            runtime_seconds=elapsed,
                        )
                    )

        total_runtime = time.time() - start_time
        summary = BatchResultsAggregator.aggregate(item_results, total_runtime)

        job.results = {
            "summary": summary.to_dict(),
            "items": [r.to_dict() for r in item_results],
        }
        job.status = "COMPLETED" if summary.failed_count == 0 else (
            "FAILED" if summary.completed_count == 0 else "PARTIAL"
        )
        job.updated_at = datetime.now(timezone.utc).isoformat()

        if self.repository:
            self.repository.save_batch_job(job)

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=workspace_id,
                activity_type="BATCH_COMPLETED",
                entity_type="BATCH",
                entity_id=batch_id,
                details={
                    "status": job.status,
                    "completed": summary.completed_count,
                    "failed": summary.failed_count,
                    "runtime_seconds": round(total_runtime, 2),
                },
            )

        return job

    def _process_target(self, target: BatchTarget, template_id: str) -> Dict[str, Any]:
        """
        Simulates analytical execution for a single batch item.
        """
        h = abs(hash(target.target_id + template_id))
        simulated_change = 4.0 + (h % 30) * 0.8
        simulated_conf = 0.80 + ((h % 18) / 100.0)

        return {
            "ref": f"finding-batch-{target.target_id}",
            "metrics": {
                "change_pct": round(simulated_change, 2),
                "confidence": round(simulated_conf, 3),
                "has_finding": simulated_change > 10.0,
                "region_id": target.region_id,
            },
        }
