"""
TRINETRA Phase 6 — Tests for Object Tracking Subsystem
"""

import pytest
from investigation.objects.registry import DetectedObject
from investigation.objects.tracking import ObjectTracker
from investigation.objects.matching import ObjectMatcher


def test_object_matcher_iou():
    box_a = [79.090, 21.140, 79.100, 21.150]
    box_b = [79.092, 21.142, 79.102, 21.152]  # Heavy overlap

    iou = ObjectMatcher.compute_iou(box_a, box_b)
    assert iou > 0.40

    box_far = [80.0, 22.0, 80.01, 22.01]
    assert ObjectMatcher.compute_iou(box_a, box_far) == 0.0


def test_object_tracker_lifecycle_states():
    tracker = ObjectTracker()

    # Date 1
    tracker.add_observation_detections(
        date="2025-06-15",
        objects=[
            DetectedObject(
                object_id="obj_1",
                category="structure",
                bounding_box=[79.090, 21.140, 79.100, 21.150],
                area_m2=500.0,
                confidence=0.85,
                date="2025-06-15",
            )
        ],
    )

    # Date 2
    tracker.add_observation_detections(
        date="2026-01-10",
        objects=[
            # Same object slightly expanded
            DetectedObject(
                object_id="obj_1_t2",
                category="structure",
                bounding_box=[79.090, 21.140, 79.101, 21.151],
                area_m2=540.0,
                confidence=0.90,
                date="2026-01-10",
            ),
            # Brand new object
            DetectedObject(
                object_id="obj_2_t2",
                category="structure",
                bounding_box=[79.120, 21.170, 79.128, 21.178],
                area_m2=320.0,
                confidence=0.88,
                date="2026-01-10",
            ),
        ],
    )

    tracks = tracker.build_tracks()
    assert len(tracks) == 2

    # Verify candidate classifications
    statuses = [t.status for t in tracks]
    assert "PERSISTENT" in statuses or "EXPANDED" in statuses
    assert "NEW_OBJECT_CANDIDATE" in statuses
