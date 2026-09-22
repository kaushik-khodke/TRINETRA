"""
TRINETRA Phase 8 — Comparison Validator
Validates multi-region and multi-event comparison inputs.
"""

from typing import List


class ComparisonValidationError(Exception):
    """Raised when comparison configuration or entity references are invalid."""
    pass


class ComparisonValidator:
    """
    Validates region and event comparison requests.
    """

    @classmethod
    def validate_region_comparison(cls, workspace_id: str, region_a_id: str, region_b_id: str) -> None:
        if not workspace_id or not workspace_id.strip():
            raise ComparisonValidationError("Workspace ID must not be empty.")
        if not region_a_id or not region_a_id.strip():
            raise ComparisonValidationError("Region A ID must be specified.")
        if not region_b_id or not region_b_id.strip():
            raise ComparisonValidationError("Region B ID must be specified.")
        if region_a_id == region_b_id:
            raise ComparisonValidationError("Cannot compare a region to itself. Specify two distinct regions.")

    @classmethod
    def validate_event_comparison(cls, workspace_id: str, event_ids: List[str]) -> None:
        if not workspace_id or not workspace_id.strip():
            raise ComparisonValidationError("Workspace ID must not be empty.")
        if not event_ids or len(event_ids) < 2:
            raise ComparisonValidationError("Event comparison requires at least 2 distinct event IDs.")
        if len(set(event_ids)) != len(event_ids):
            raise ComparisonValidationError("Duplicate event IDs provided for comparison.")
