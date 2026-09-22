"""
TRINETRA Phase 8 — Annotation & Review Validator
Validates annotations, analyst review state changes, and follow-up entries.
"""

from typing import Any

try:
    from backend.workspace.models import ReviewStatus
except ImportError:
    from workspace.models import ReviewStatus


class AnnotationValidationError(Exception):
    """Raised when an annotation or review transition is invalid."""
    pass


class AnnotationValidator:
    """
    Validates annotation texts, review state transitions, and follow-up tasks.
    """

    ALLOWED_ANNOTATION_TYPES = {"TEXT", "LABEL", "REGION_NOTE", "QUESTION"}
    ALLOWED_FOLLOWUP_STATUSES = {"OPEN", "IN_PROGRESS", "COMPLETE", "CANCELLED"}

    @classmethod
    def validate_annotation(cls, workspace_id: str, text: str, ann_type: str) -> None:
        if not workspace_id or not workspace_id.strip():
            raise AnnotationValidationError("Workspace ID must not be empty.")
        if not text or not text.strip():
            raise AnnotationValidationError("Annotation text must not be empty.")
        if ann_type not in cls.ALLOWED_ANNOTATION_TYPES:
            raise AnnotationValidationError(
                f"Invalid annotation type '{ann_type}'. Allowed: {cls.ALLOWED_ANNOTATION_TYPES}"
            )

    @classmethod
    def validate_review(cls, workspace_id: str, entity_type: str, entity_id: str, status: Any) -> None:
        if not workspace_id or not workspace_id.strip():
            raise AnnotationValidationError("Workspace ID must not be empty.")
        if not entity_type or not entity_id:
            raise AnnotationValidationError("Entity type and ID must be specified for review.")

        val = status.value if isinstance(status, ReviewStatus) else str(status)
        try:
            ReviewStatus(val)
        except ValueError:
            raise AnnotationValidationError(f"Invalid review status '{val}'.")

    @classmethod
    def validate_follow_up(cls, workspace_id: str, note: str, status: str) -> None:
        if not workspace_id or not workspace_id.strip():
            raise AnnotationValidationError("Workspace ID must not be empty.")
        if not note or not note.strip():
            raise AnnotationValidationError("Follow-up note must not be empty.")
        if status not in cls.ALLOWED_FOLLOWUP_STATUSES:
            raise AnnotationValidationError(
                f"Invalid follow-up status '{status}'. Allowed: {cls.ALLOWED_FOLLOWUP_STATUSES}"
            )
