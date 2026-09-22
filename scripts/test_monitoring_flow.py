"""
TRINETRA Phase 7 — Verification Script: Continuous Monitoring & Alert Deduplication
Validates monitor definition, observation evaluation, trigger condition parsing,
fingerprint-based duplicate suppression, and analyst alert acknowledgment.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from intelligence.models import PersistentFinding, EOEvent, EventState, MonitorDefinition, MonitorAlert
from intelligence.repository import IntelligenceRepository
from intelligence.monitoring.service import MonitoringService
from intelligence.monitoring.conditions import TriggerConditionEvaluator


def run_monitoring_test():
    print("================================================================")
    print("  TRINETRA Phase 7: Continuous Monitoring & Alerts Verification")
    print("================================================================")

    repo = IntelligenceRepository(db_path=":memory:")
    monitoring_svc = MonitoringService(repo=repo)

    # 1. Create a continuous monitor
    print("[1] Registering Continuous Monitor...")
    mon = monitoring_svc.create_monitor(
        name="Western Ghats Deforestation Watcher",
        bounding_box=[73.80, 15.00, 74.50, 15.80],
        observation_collection="sentinel-2-l2a",
        schedule_cadence="daily",
        trigger_condition={
            "operator": "AND",
            "conditions": [
                {"field": "confidence", "operator": ">=", "value": 0.70},
                {"field": "change_area_ha", "operator": ">", "value": 2.0},
            ],
        },
        cooldown_hours=24,
    )
    assert mon is not None
    print(f"✓ Monitor registered: '{mon.monitor_id}' ({mon.name})")
    print(f"  Cadence: {mon.schedule_cadence}, BBox: {mon.bounding_box}")

    # 2. Test Trigger Condition Evaluator
    print("\n[2] Testing Trigger Condition Evaluator...")
    passing_metrics = {"confidence": 0.85, "change_area_ha": 5.4}
    failing_metrics = {"confidence": 0.60, "change_area_ha": 1.2}

    assert TriggerConditionEvaluator.evaluate(mon.trigger_condition, passing_metrics)
    assert not TriggerConditionEvaluator.evaluate(mon.trigger_condition, failing_metrics)
    print("✓ Boolean trigger condition logic evaluated correctly (passes on 0.85/5.4ha, fails on 0.60/1.2ha)")

    # 3. Simulate incoming observation finding inside monitor area
    print("\n[3] Ingesting Finding Inside Monitor AOI...")
    finding = PersistentFinding(
        finding_id="find_mon_test_01",
        investigation_id="inv_mon_01",
        type="vegetation_loss",
        label="Rapid clearing in protected buffer zone",
        confidence=0.88,
        metrics={"confidence": 0.88, "change_area_ha": 8.5, "delta_ndvi": -0.45},
        semantic_class="vegetation_loss",
        bounding_box=[74.00, 15.20, 74.10, 15.30],  # Inside monitor bbox
    )
    event = EOEvent(
        event_id="evt_mon_test_01",
        title="Canopy Loss in Western Ghats",
        canonical_region_id="reg_ghats_01",
        semantic_class="vegetation_loss",
        state=EventState.OBSERVED,
        confidence=0.88,
        bounding_box=[74.00, 15.20, 74.10, 15.30],
        supporting_findings=[finding.finding_id],
    )
    repo.save_finding(finding)
    repo.save_event(event)

    # Evaluate monitors against this finding
    alerts_1 = monitoring_svc.evaluate_monitors_for_finding(finding, event)
    print(f"✓ First evaluation generated {len(alerts_1)} alert(s)")
    assert len(alerts_1) == 1
    alert_1 = alerts_1[0]
    print(f"  Alert ID: '{alert_1.alert_id}', Severity: {alert_1.severity}")
    print(f"  Trigger reason: {alert_1.trigger_reason}")
    print(f"  Fingerprint: {alert_1.alert_fingerprint}")

    # 4. Test Duplicate Alert Suppression
    print("\n[4] Testing Duplicate Alert Suppression...")
    # Re-evaluating same finding within cooldown should be suppressed
    alerts_2 = monitoring_svc.evaluate_monitors_for_finding(finding, event)
    print(f"✓ Second evaluation with duplicate fingerprint generated {len(alerts_2)} alert(s)")
    assert len(alerts_2) == 0, "Duplicate alert should be suppressed by fingerprint check"
    print("✓ Alert deduplication confirmed: duplicate alert was suppressed.")

    # 5. Analyst Acknowledgment
    print("\n[5] Testing Analyst Alert Acknowledgment...")
    repo.acknowledge_alert(alert_1.alert_id)
    all_alerts = repo.list_monitor_alerts()
    assert len(all_alerts) == 1
    assert all_alerts[0].acknowledged == True
    print(f"✓ Alert '{alert_1.alert_id}' successfully marked as acknowledged.")

    print("\n>>> ALL CONTINUOUS MONITORING & ALERT TESTS PASSED! <<<\n")


if __name__ == "__main__":
    run_monitoring_test()
