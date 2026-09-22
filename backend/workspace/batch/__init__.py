"""
TRINETRA Phase 8 — Batch Processing Subsystem.
Enforces resource quotas, concurrency limits, and cross-regional aggregate synthesis.
"""

from .limits import BatchLimitsEnforcer, BatchLimitExceededError
from .models import BatchTarget, BatchItemResult, BatchSummary
from .scheduler import BatchScheduler
from .results import BatchResultsAggregator
from .executor import BatchExecutor

__all__ = [
    "BatchLimitsEnforcer",
    "BatchLimitExceededError",
    "BatchTarget",
    "BatchItemResult",
    "BatchSummary",
    "BatchScheduler",
    "BatchResultsAggregator",
    "BatchExecutor",
]
