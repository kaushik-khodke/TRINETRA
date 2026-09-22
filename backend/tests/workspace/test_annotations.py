"""
TRINETRA Phase 8 Tests — Annotations, Review Status & Follow-Ups
Verifies review workflows, analyst notes, follow-up queues, and schema validations.
"""

import pytest
from workspace.models import ReviewStatus
from workspace.annotations.validator import AnnotationValidator, AnnotationValidationError
from workspace.annotations.service import AnnotationService
from workspace.repository import WorkspaceRepository


@pytest.fixture
def repo():
    return WorkspaceRepository(":memory:")


@pytest.fixture
def service(repo):
    return AnnotationService(repository=repo)


def test_annotation_creation_and_validation(service):
    ann = service.add_annotation(
        workspace_id="ws-ann-test",
        text="Check cloud shadow misclassification along eastern ridge",
        type="QUESTION",
        linked_entity_type="FINDING",
        linked_entity_id="f-302",
    )
    assert ann.annotation_id.startswith("ann-")
    assert ann.type == "QUESTION"

    # Empty text rejection
    with pytest.raises(AnnotationValidationError):
        AnnotationValidator.validate_annotation("ws-1", "", "TEXT")

    # Invalid type rejection
    with pytest.raises(AnnotationValidationError):
        AnnotationValidator.validate_annotation("ws-1", "Valid text", "UNKNOWN_TYPE")


def test_review_status_lifecycle(service):
    ws_id = "ws-rev-test"

    # Initial review
    rev = service.set_review_status(
        workspace_id=ws_id,
        entity_type="FINDING",
        entity_id="find-99",
        status=ReviewStatus.REVIEWED,
        review_note="Confirmed with multi-sensor SAR overlay",
        analyst_id="analyst_lead",
    )
    assert rev.status == ReviewStatus.REVIEWED
    assert rev.analyst_id == "analyst_lead"

    # Transition to NEEDS_FOLLOWUP
    rev2 = service.set_review_status(
        workspace_id=ws_id,
        entity_type="FINDING",
        entity_id="find-99",
        status=ReviewStatus.NEEDS_FOLLOWUP,
        review_note="Needs Sentinel-1 repeat pass",
    )
    assert rev2.status == ReviewStatus.NEEDS_FOLLOWUP
    assert rev2.review_id == rev.review_id  # Overwrites existing review for same entity


def test_follow_up_queue_lifecycle(service):
    fu = service.create_follow_up(
        workspace_id="ws-fu-test",
        linked_entity_type="EVENT",
        linked_entity_id="evt-404",
        note="Schedule automated optical tasking next week",
        status="OPEN",
    )
    assert fu.follow_up_id.startswith("fu-")
    assert fu.status == "OPEN"

    # Empty note rejected
    with pytest.raises(AnnotationValidationError):
        AnnotationValidator.validate_follow_up("ws-1", "", "OPEN")
