"""
Unit tests for Persistent Monitoring and Alerting Subsystem.
Tests condition evaluation predicate tree, spatial observation filtering, alert generation, and duplicate suppression.
"""

import pytest
from intelligence.repository import IntelligenceRepository
from intelligence.models import MonitorDefinition, PersistentFinding, EOEvent, EventState
from intelligence.monitoring.conditions import ConditionEvaluator
from intelligence.monitoring.observation_checker import ObservationChecker
from intelligence.monitoring.notifier import MonitorNotifier
from intelligence.monitoring.service import MonitoringService


@pytest.fixture
def repo():
    return IntelligenceRepository(db_path=":memory:")


def test_condition_evaluator_comparisons():
    ctx = {"confidence": 0.88, "semantic_class": "BUILT_UP_EXPANSION", "area_ha": 12.5}

    # Simple greater than
    cond_gt = {"op": ">", "field": "confidence", "value": 0.8}
    assert ConditionEvaluator.evaluate(cond_gt, ctx) is True

    cond_gt_fail = {"op": ">", "field": "confidence", "value": 0.95}
    assert ConditionEvaluator.evaluate(cond_gt_fail, ctx) is False

    # Equals
    cond_eq = {"op": "==", "field": "semantic_class", "value": "BUILT_UP_EXPANSION"}
    assert ConditionEvaluator.evaluate(cond_eq, ctx) is True

    # In collection
    cond_in = {"op": "IN", "field": "semantic_class", "value": ["BUILT_UP_EXPANSION", "INFRASTRUCTURE"]}
    assert ConditionEvaluator.evaluate(cond_in, ctx) is True


def test_condition_evaluator_boolean_tree():
    ctx = {"confidence": 0.85, "area_ha": 5.0}

    tree_and = {
        "op": "AND",
        "conditions": [
            {"op": ">", "field": "confidence", "value": 0.8},
            {"op": ">", "field": "area_ha", "value": 2.0},
        ],
    }
    assert ConditionEvaluator.evaluate(tree_and, ctx) is True

    tree_or = {
        "op": "OR",
        "conditions": [
            {"op": ">", "field": "confidence", "value": 0.95},
            {"op": ">", "field": "area_ha", "value": 3.0},
        ],
    }
    assert ConditionEvaluator.evaluate(tree_or, ctx) is True


def test_observation_checker_spatial(repo):
    monitor = MonitorDefinition(
        monitor_id="mon_test_obs",
        name="Test Obs Monitor",
        bounding_box=[79.0, 21.0, 79.2, 21.2],
    )
    obs_inside = {"id": "obs_in_01", "bbox": [79.05, 21.05, 79.15, 21.15]}
    obs_outside = {"id": "obs_out_01", "bbox": [80.0, 22.0, 80.1, 22.1]}

    assert ObservationChecker.should_process_observation(monitor, obs_inside, repo) is True
    assert ObservationChecker.should_process_observation(monitor, obs_outside, repo) is False


def test_monitoring_service_triggers_and_deduplicates(repo):
    service = MonitoringService(repo=repo)

    # Create monitor with condition
    monitor = MonitorDefinition(
        monitor_id="mon_001",
        name="High Confidence Expansion Watch",
        bbox=[79.0, 21.0, 79.2, 21.2],
        trigger_condition={"op": ">", "field": "confidence", "value": 0.8},
        enabled=True,
    )
    repo.save_monitor(monitor)

    finding = PersistentFinding(
        finding_id="fnd_mon_01",
        investigation_id="inv_01",
        type="optical_change",
        label="Rapid development detected",
        bounding_box=[79.05, 21.05, 79.15, 21.15],
        confidence=0.9,
        semantic_class="BUILT_UP_EXPANSION",
    )
    event = EOEvent(
        event_id="evt_mon_01",
        title="Rapid development",
        canonical_region_id="reg_01",
        semantic_class="BUILT_UP_EXPANSION",
        state=EventState.OBSERVED,
        confidence=0.9,
        bounding_box=[79.05, 21.05, 79.15, 21.15],
    )

    # First evaluation -> generates alert
    alerts1 = service.evaluate_monitors_for_finding(finding, event)
    assert len(alerts1) == 1
    assert alerts1[0].monitor_id == "mon_001"

    all_alerts = repo.list_alerts()
    assert len(all_alerts) == 1

    # Second evaluation with same finding -> duplicate alert suppressed
    alerts2 = service.evaluate_monitors_for_finding(finding, event)
    assert len(alerts2) == 0
    assert len(repo.list_alerts()) == 1
