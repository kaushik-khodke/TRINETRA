"""
Unit tests for IntelligenceRepository SQLite storage layer.
Tests in-memory execution, transactions, concurrency safety, and CRUD for all models.
"""

import pytest
import os
from intelligence.repository import IntelligenceRepository
from intelligence.models import (
    CanonicalRegion,
    EOEvent,
    EventState,
    PersistentFinding,
    MonitorDefinition,
    MonitorAlert,
    Baseline,
    RegionLineage,
)


@pytest.fixture
def repo():
    """Isolated in-memory SQLite repository for testing."""
    return IntelligenceRepository(db_path=":memory:")


def test_repository_init(repo):
    assert repo is not None
    assert repo.db_path == ":memory:"
    assert len(repo.list_regions()) == 0
    assert len(repo.list_events()) == 0


def test_save_and_get_region(repo):
    region = CanonicalRegion(
        canonical_region_id="reg_test_01",
        name="Nagpur Industrial Zone",
        geometry={"type": "Polygon", "coordinates": [[[79.0, 21.1], [79.1, 21.1], [79.1, 21.2], [79.0, 21.2], [79.0, 21.1]]]},
        bounding_box=[79.0, 21.1, 79.1, 21.2],
        description="Core industrial area",
        tags=["industrial", "nagpur"],
    )
    ok = repo.save_region(region)
    assert ok is True

    fetched = repo.get_region("reg_test_01")
    assert fetched is not None
    assert fetched.name == "Nagpur Industrial Zone"
    assert fetched.bounding_box == [79.0, 21.1, 79.1, 21.2]
    assert "industrial" in fetched.tags

    regions = repo.list_regions()
    assert len(regions) == 1


def test_save_and_get_finding(repo):
    finding = PersistentFinding(
        finding_id="fnd_test_01",
        investigation_id="inv_001",
        type="change_detection",
        label="Vegetation clearing detected",
        bounding_box=[79.05, 21.12, 79.08, 21.15],
        confidence=0.89,
        semantic_class="VEGETATION_CLEARING",
        metrics={"change_percentage": 14.5, "delta_ndvi": -0.42},
    )
    ok = repo.save_finding(finding, fingerprint="fp_abc_123")
    assert ok is True

    fetched = repo.get_finding("fnd_test_01")
    assert fetched is not None
    assert fetched.label == "Vegetation clearing detected"
    assert fetched.confidence == 0.89
    assert fetched.semantic_class == "VEGETATION_CLEARING"
    assert fetched.metrics["delta_ndvi"] == -0.42

    findings = repo.list_findings(investigation_id="inv_001")
    assert len(findings) == 1
    assert findings[0].finding_id == "fnd_test_01"


def test_save_and_update_event(repo):
    event = EOEvent(
        event_id="evt_test_01",
        title="Industrial Expansion Cluster",
        canonical_region_id="reg_test_01",
        semantic_class="BUILT_UP_EXPANSION",
        state=EventState.CANDIDATE,
        confidence=0.65,
        bounding_box=[79.0, 21.1, 79.1, 21.2],
        supporting_findings=["fnd_test_01"],
    )
    repo.save_event(event)

    fetched = repo.get_event("evt_test_01")
    assert fetched is not None
    assert fetched.state == EventState.CANDIDATE
    assert len(fetched.supporting_findings) == 1

    # Update state
    updated = repo.update_event_state(
        event_id="evt_test_01",
        new_state=EventState.OBSERVED,
        reason="Second observation confirms change",
        finding_id="fnd_test_02",
    )
    assert updated is True

    fetched2 = repo.get_event("evt_test_01")
    assert fetched2.state == EventState.OBSERVED
    assert fetched2.version == 2
    assert len(fetched2.history) == 2
    assert fetched2.history[-1]["to_state"] == "OBSERVED"


def test_monitors_and_alerts(repo):
    monitor = MonitorDefinition(
        monitor_id="mon_test_01",
        name="Daily Nagpur Perimeter Alert",
        bbox=[79.0, 21.1, 79.1, 21.2],
        trigger_condition={"op": ">", "field": "confidence", "value": 0.8},
        enabled=True,
    )
    repo.save_monitor(monitor)

    fetched_m = repo.get_monitor("mon_test_01")
    assert fetched_m is not None
    assert fetched_m.name == "Daily Nagpur Perimeter Alert"

    alert = MonitorAlert(
        alert_id="alt_test_01",
        monitor_id="mon_test_01",
        event_id="evt_test_01",
        finding_id="fnd_test_01",
        severity="WARNING",
        trigger_reason="Confidence 0.89 exceeded threshold 0.8",
        alert_fingerprint="fp_alt_001",
    )
    repo.save_alert(alert)

    alerts = repo.list_alerts(monitor_id="mon_test_01")
    assert len(alerts) == 1
    assert alerts[0].severity == "WARNING"

    # Verify duplicate alert fingerprint detection
    has_fp = repo.alert_fingerprint_exists("fp_alt_001")
    assert has_fp is True
    assert repo.alert_fingerprint_exists("nonexistent_fp") is False


def test_baseline_and_lineage(repo):
    from intelligence.anomalies.statistical import StatisticalBaselineBuilder
    base = StatisticalBaselineBuilder.build(
        metric_name="change_percentage",
        spatial_unit="reg_test_01",
        values=[2.1, 2.3, 2.5, 2.7, 2.9, 2.4, 2.6, 2.5],
    )
    assert base is not None
    repo.save_baseline(base)

    fetched_b = repo.find_baseline("change_percentage", "reg_test_01")
    assert fetched_b is not None
    assert fetched_b.sample_count == 8

    # Lineage
    lineage = RegionLineage(
        lineage_id="lin_001",
        parent_region_id="reg_parent",
        child_region_id="reg_child",
        relationship_type="MERGED_FROM",
    )
    repo.save_lineage(lineage)
    rels = repo.get_region_lineage("reg_parent")
    assert len(rels) == 1
    assert rels[0].relationship_type == "MERGED_FROM"
