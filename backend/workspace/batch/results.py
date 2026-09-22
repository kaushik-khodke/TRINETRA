"""
TRINETRA Phase 8 — Batch Results Aggregator
Aggregates target results, computes cross-regional statistics, and synthesizes batch summaries.
"""

from typing import Dict, Any, List
from .models import BatchItemResult, BatchSummary


class BatchResultsAggregator:
    """
    Computes summary metrics and statistical aggregations across processed batch items.
    """

    @classmethod
    def aggregate(
        cls,
        results: List[BatchItemResult],
        total_runtime: float,
    ) -> BatchSummary:
        completed = [r for r in results if r.status == "COMPLETED"]
        failed = [r for r in results if r.status == "FAILED"]
        skipped = [r for r in results if r.status == "SKIPPED"]

        change_percentages: List[float] = []
        confidences: List[float] = []

        for item in completed:
            if "change_pct" in item.metrics:
                change_percentages.append(float(item.metrics["change_pct"]))
            if "confidence" in item.metrics:
                confidences.append(float(item.metrics["confidence"]))

        avg_change = sum(change_percentages) / len(change_percentages) if change_percentages else 0.0
        max_change = max(change_percentages) if change_percentages else 0.0
        min_change = min(change_percentages) if change_percentages else 0.0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        agg_metrics = {
            "average_change_percentage": round(avg_change, 2),
            "max_change_percentage": round(max_change, 2),
            "min_change_percentage": round(min_change, 2),
            "average_confidence": round(avg_confidence, 4),
            "items_with_findings": len([c for c in completed if c.metrics.get("has_finding", False)]),
        }

        return BatchSummary(
            total_targets=len(results),
            completed_count=len(completed),
            failed_count=len(failed),
            skipped_count=len(skipped),
            total_runtime_seconds=total_runtime,
            aggregate_metrics=agg_metrics,
        )
