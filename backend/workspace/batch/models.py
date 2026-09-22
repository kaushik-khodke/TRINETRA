"""
TRINETRA Phase 8 — Batch Execution Subsystem Models
Data structures for batch targets, individual item outcomes, and aggregate batch summaries.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class BatchTarget:
    def __init__(
        self,
        target_id: str,
        region_id: Optional[str] = None,
        aoi: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        estimated_pixels: int = 1_000_000,
    ):
        self.target_id = target_id
        self.region_id = region_id
        self.aoi = aoi or {}
        self.parameters = parameters or {}
        self.estimated_pixels = estimated_pixels

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "region_id": self.region_id,
            "aoi": self.aoi,
            "parameters": self.parameters,
            "estimated_pixels": self.estimated_pixels,
        }


class BatchItemResult:
    def __init__(
        self,
        target_id: str,
        status: str,  # COMPLETED, FAILED, SKIPPED
        result_ref: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        runtime_seconds: float = 0.0,
    ):
        self.target_id = target_id
        self.status = status
        self.result_ref = result_ref
        self.metrics = metrics or {}
        self.error = error
        self.runtime_seconds = runtime_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "status": self.status,
            "result_ref": self.result_ref,
            "metrics": self.metrics,
            "error": self.error,
            "runtime_seconds": round(self.runtime_seconds, 2),
        }


class BatchSummary:
    def __init__(
        self,
        total_targets: int,
        completed_count: int,
        failed_count: int,
        skipped_count: int,
        total_runtime_seconds: float,
        aggregate_metrics: Optional[Dict[str, Any]] = None,
    ):
        self.total_targets = total_targets
        self.completed_count = completed_count
        self.failed_count = failed_count
        self.skipped_count = skipped_count
        self.total_runtime_seconds = total_runtime_seconds
        self.aggregate_metrics = aggregate_metrics or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_targets": self.total_targets,
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "total_runtime_seconds": round(self.total_runtime_seconds, 2),
            "aggregate_metrics": self.aggregate_metrics,
        }
