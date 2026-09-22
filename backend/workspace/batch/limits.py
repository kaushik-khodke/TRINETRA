"""
TRINETRA Phase 8 — Batch Quota & Resource Limits
Validates target counts, pixel budgets, and timeout constraints.
"""

from typing import List, Dict, Any

try:
    from backend.config.settings import settings
except ImportError:
    from config.settings import settings


class BatchLimitExceededError(Exception):
    """Raised when a batch job request violates system safety thresholds."""
    pass


class BatchLimitsEnforcer:
    """
    Guards computational resources for batch multi-target execution.
    """

    @classmethod
    def validate_targets(cls, targets: List[Dict[str, Any]]) -> None:
        """
        Validates target count and estimated pixel resource usage.
        """
        if not targets:
            raise BatchLimitExceededError("Batch job must contain at least 1 target.")

        max_targets = getattr(settings, "workspace_max_batch_targets", 50)
        if len(targets) > max_targets:
            raise BatchLimitExceededError(
                f"Batch target count ({len(targets)}) exceeds maximum permitted threshold ({max_targets})."
            )

        max_pixels = getattr(settings, "workspace_max_batch_pixels", 50_000_000)
        total_pixels = sum(t.get("estimated_pixels", 1_000_000) for t in targets)
        if total_pixels > max_pixels:
            raise BatchLimitExceededError(
                f"Estimated batch pixel workload ({total_pixels:,}) exceeds quota ({max_pixels:,}). "
                "Reduce target AOI extents or number of targets."
            )

    @classmethod
    def get_max_concurrency(cls, requested: int = 2) -> int:
        """
        Ensures concurrency does not exceed settings.workspace_max_concurrent_tasks.
        """
        configured_max = getattr(settings, "workspace_max_concurrent_tasks", 4)
        return min(max(1, requested), configured_max)
