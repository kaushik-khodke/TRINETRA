"""
Unit tests for Region and Event Spatial Matching, Merging, and Splitting.
Tests Haversine distance, IoU calculation, EventBuilder, EventMerger, and EventSplitter.
"""

import pytest
from intelligence.repository import IntelligenceRepository
from intelligence.models import CanonicalRegion, EOEvent, EventState, PersistentFinding
from intelligence.events.matcher import haversine_distance_km, compute_bbox_iou
from intelligence.events.builder import EventBuilder
from intelligence.events.merger import EventMerger
from intelligence.events.splitter import EventSplitter


@pytest.fixture
def repo():
    return IntelligenceRepository(db_path=":memory:")


def test_spatial_distance_and_iou():
    # Exactly identical boxes -> IoU = 1.0
    box_a = [79.0, 21.0, 79.1, 21.1]
    box_b = [79.0, 21.0, 79.1, 21.1]
    iou = compute_bbox_iou(box_a, box_b)
    assert pytest.approx(iou, 0.01) == 1.0

    # Non-overlapping boxes -> IoU = 0.0
    box_c = [80.0, 22.0, 80.1, 22.1]
    iou_none = compute_bbox_iou(box_a, box_c)
    assert iou_none == 0.0

    # Haversine distance between Nagpur center (21.1458, 79.0882) and 1 km away
    d_km = haversine_distance_km(21.1458, 79.0882, 21.1558, 79.0882)
    assert 1.0 <= d_km <= 1.3


def test_event_builder_ingest(repo):
    # Ingest first finding -> creates region + event
    f1 = PersistentFinding(
        finding_id="fnd_bld_01",
        investigation_id="inv_01",
        type="optical_change",
        label="New warehouse structure",
        bounding_box=[79.05, 21.12, 79.08, 21.15],
        confidence=0.82,
        semantic_class="BUILT_UP_EXPANSION",
        observation_ids=["obs_01"],
    )
    event1 = EventBuilder.ingest_finding(f1, repo)
    assert event1 is not None
    assert event1.state in (EventState.CANDIDATE, EventState.OBSERVED)
    assert len(event1.supporting_findings) == 1

    # Regions count should now be 1
    regions = repo.list_regions()
    assert len(regions) == 1
    assert event1.canonical_region_id == regions[0].canonical_region_id

    # Ingest second overlapping finding with same semantic class -> evolves same event
    f2 = PersistentFinding(
        finding_id="fnd_bld_02",
        investigation_id="inv_02",
        type="sar_backscatter",
        label="SAR coherence loss confirmed",
        bounding_box=[79.052, 21.121, 79.082, 21.151],
        confidence=0.91,
        semantic_class="BUILT_UP_EXPANSION",
        observation_ids=["obs_02"],
    )
    event2 = EventBuilder.ingest_finding(f2, repo)
    assert event2.event_id == event1.event_id
    assert len(event2.supporting_findings) == 2
    # State should advance from CANDIDATE to OBSERVED or CORROBORATED
    assert event2.state in (EventState.OBSERVED, EventState.CORROBORATED)


def test_event_merger(repo):
    evt_a = EOEvent(
        event_id="evt_merge_a",
        title="East Sector Building",
        canonical_region_id="reg_01",
        semantic_class="CONSTRUCTION",
        state=EventState.OBSERVED,
        confidence=0.8,
        bounding_box=[79.0, 21.0, 79.05, 21.05],
        supporting_findings=["fnd_a1"],
    )
    evt_b = EOEvent(
        event_id="evt_merge_b",
        title="East Sector Extension",
        canonical_region_id="reg_01",
        semantic_class="CONSTRUCTION",
        state=EventState.CANDIDATE,
        confidence=0.75,
        bounding_box=[79.04, 21.04, 79.08, 21.08],
        supporting_findings=["fnd_b1"],
    )
    repo.save_event(evt_a)
    repo.save_event(evt_b)

    primary, secondary = EventMerger.merge_events(evt_a, evt_b, repo)
    assert primary is not None
    assert "fnd_a1" in primary.supporting_findings
    assert "fnd_b1" in primary.supporting_findings

    # Secondary event should be retired as RESOLVED
    b_updated = repo.get_event("evt_merge_b")
    assert b_updated.state == EventState.RESOLVED


def test_event_splitter(repo):
    parent = EOEvent(
        event_id="evt_split_parent",
        title="Composite Regional Development",
        canonical_region_id="reg_01",
        semantic_class="MIXED",
        state=EventState.OBSERVED,
        confidence=0.85,
        bounding_box=[79.0, 21.0, 79.2, 21.2],
        supporting_findings=["fnd_p1", "fnd_p2", "fnd_p3"],
    )
    repo.save_event(parent)

    child_specs = [
        {"title": "Subzone North", "bounding_box": [79.0, 21.1, 79.1, 21.2], "supporting_findings": ["fnd_p1"]},
        {"title": "Subzone South", "bounding_box": [79.1, 21.0, 79.2, 21.1], "supporting_findings": ["fnd_p2", "fnd_p3"]},
    ]
    children = EventSplitter.split_event(parent, child_specs, repo)
    assert len(children) == 2
    assert children[0].title == "Subzone North"
    assert children[1].title == "Subzone South"

    # Parent should be marked RESOLVED
    p_updated = repo.get_event("evt_split_parent")
    assert p_updated.state == EventState.RESOLVED
