"""
TRINETRA Phase 8 — Annotation & Review Service
Coordinates analyst notes, verification status flags, and follow-up queues.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from backend.workspace.models import Annotation, ReviewRecord, ReviewStatus, FollowUp
    from backend.workspace.annotations.validator import AnnotationValidator
except ImportError:
    from workspace.models import Annotation, ReviewRecord, ReviewStatus, FollowUp
    from workspace.annotations.validator import AnnotationValidator


class AnnotationService:
    """
    Coordinates creation and persistence of annotations, reviews, and follow-ups.
    """

    def __init__(self, repository=None, activity_tracker=None):
        self.repository = repository
        self.activity_tracker = activity_tracker

    def add_annotation(
        self,
        workspace_id: str,
        text: str,
        type: str = "TEXT",
        geometry: Optional[Dict[str, Any]] = None,
        linked_entity_type: Optional[str] = None,
        linked_entity_id: Optional[str] = None,
    ) -> Annotation:
        AnnotationValidator.validate_annotation(workspace_id, text, type)

        ann = Annotation(
            annotation_id=f"ann-{uuid.uuid4().hex[:12]}",
            workspace_id=workspace_id,
            geometry=geometry or {},
            text=text,
            type=type,
            linked_entity_type=linked_entity_type,
            linked_entity_id=linked_entity_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

        if self.repository:
            self.repository.save_annotation(ann)

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=workspace_id,
                activity_type="ANNOTATION_ADDED",
                entity_type="ANNOTATION",
                entity_id=ann.annotation_id,
                details={"text": text[:50], "type": type},
            )

        return ann

    def set_review_status(
        self,
        workspace_id: str,
        entity_type: str,
        entity_id: str,
        status: ReviewStatus,
        review_note: str = "",
        analyst_id: str = "analyst",
    ) -> ReviewRecord:
        AnnotationValidator.validate_review(workspace_id, entity_type, entity_id, status)

        existing = None
        if self.repository:
            existing = self.repository.get_review(workspace_id, entity_type, entity_id)

        review_id = existing.review_id if existing else f"rev-{uuid.uuid4().hex[:12]}"
        rev = ReviewRecord(
            review_id=review_id,
            workspace_id=workspace_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            review_note=review_note,
            reviewed_at=datetime.now(timezone.utc).isoformat(),
            analyst_id=analyst_id,
        )

        if self.repository:
            self.repository.save_review(rev)

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=workspace_id,
                activity_type="REVIEW_STATUS_UPDATED",
                entity_type=entity_type,
                entity_id=entity_id,
                details={"status": rev.status.value, "note": review_note[:50]},
            )

        return rev

    def create_follow_up(
        self,
        workspace_id: str,
        linked_entity_type: str,
        linked_entity_id: str,
        note: str,
        status: str = "OPEN",
    ) -> FollowUp:
        AnnotationValidator.validate_follow_up(workspace_id, note, status)

        fu = FollowUp(
            follow_up_id=f"fu-{uuid.uuid4().hex[:12]}",
            workspace_id=workspace_id,
            linked_entity_type=linked_entity_type,
            linked_entity_id=linked_entity_id,
            note=note,
            status=status,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

        if self.repository:
            self.repository.save_follow_up(fu)

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=workspace_id,
                activity_type="FOLLOWUP_CREATED",
                entity_type=linked_entity_type,
                entity_id=linked_entity_id,
                details={"note": note[:50], "status": status},
            )

        return fu
