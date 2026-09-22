"""
TRINETRA Phase 8 — Multi-Region & Multi-Event Comparison Subsystem.
Provides area-normalized comparisons, sensitivity analysis, difference matrices, and warning detection.
"""

from .metrics import ComparisonMetricsEngine
from .regions import RegionComparator
from .events import EventComparator
from .findings import FindingComparator
from .validator import ComparisonValidator, ComparisonValidationError

__all__ = [
    "ComparisonMetricsEngine",
    "RegionComparator",
    "EventComparator",
    "FindingComparator",
    "ComparisonValidator",
    "ComparisonValidationError",
]
