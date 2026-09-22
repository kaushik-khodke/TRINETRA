"""
TRINETRA Phase 7 — Monitoring Service Coordinator
Manages monitor lifecycles, observation checking, trigger condition evaluation, and alert dispatch.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from intelligence.models import MonitorDefinition, MonitorRun, MonitorAlert, PersistentFinding, EOEvent
from intelligence.repository import IntelligenceRepository, intelligence_repo
from intelligence.monitoring.conditions import ConditionEvaluator
from intelligence.monitoring.observation_checker import ObservationChecker
from intelligence.monitoring.notifier import MonitorNotifier
from intelligence.monitoring.scheduler import MonitoringScheduler
from intelligence.search.spatial import SpatialSearchFilter


class MonitoringService:
    """
    Central orchestrator for Earth Observation continuous monitoring.
    """

    def __init__(self, repository: Optional[IntelligenceRepository] = None, repo: Optional[IntelligenceRepository] = None):
        self.repo = repository or repo or intelligence_repo

    def create_monitor(
        self,
        name: str,
        aoi: Optional[Dict[str, Any]] = None,
        bounding_box: Optional[List[float]] = None,
        observation_collection: str = "sentinel-2-l2a",
        schedule_cadence: str = "daily",
        template_id: str = "",
        trigger_condition: Optional[Dict[str, Any]] = None,
        cooldown_hours: int = 24,
    ) -> MonitorDefinition:
        if not MonitoringScheduler.can_create_monitor(self.repo):
            raise ValueError("Maximum monitor limit reached. Please remove inactive monitors before creating new ones.")

        # Compute bbox if missing
        if not bounding_box and aoi and aoi.get("type") == "Polygon" and aoi.get("coordinates"):
            coords = aoi["coordinates"][0]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            bounding_box = [min(lons), min(lats), max(lons), max(lats)]

        monitor_id = f"mon_{uuid.uuid4().hex[:8]}"
        monitor = MonitorDefinition(
            monitor_id=monitor_id,
            name=name,
            aoi=aoi,
            bounding_box=bounding_box or [],
            observation_collection=observation_collection,
            schedule_cadence=schedule_cadence,
            template_id=template_id,
            trigger_condition=trigger_condition,
            enabled=True,
            cooldown_hours=cooldown_hours,
        )
        self.repo.save_monitor(monitor)
        return monitor

    def get_monitor(self, monitor_id: str) -> Optional[MonitorDefinition]:
        return self.repo.get_monitor(monitor_id)

    def list_monitors(self, enabled_only: bool = False) -> List[MonitorDefinition]:
        return self.repo.list_monitors(enabled_only=enabled_only)

    def enable_monitor(self, monitor_id: str) -> bool:
        m = self.get_monitor(monitor_id)
        if not m:
            return False
        m.enabled = True
        m.updated_at = datetime.utcnow().isoformat()
        return self.repo.save_monitor(m)

    def disable_monitor(self, monitor_id: str) -> bool:
        m = self.get_monitor(monitor_id)
        if not m:
            return False
        m.enabled = False
        m.updated_at = datetime.utcnow().isoformat()
        return self.repo.save_monitor(m)

    def delete_monitor(self, monitor_id: str) -> bool:
        m = self.get_monitor(monitor_id)
        if not m:
            return False
        m.enabled = False
        # Soft-delete by disabling or updating
        return self.repo.save_monitor(m)

    def evaluate_monitors_for_finding(
        self,
        finding: PersistentFinding,
        event: Optional[EOEvent] = None,
    ) -> List[MonitorAlert]:
        """
        Spatially routes a newly ingested finding to all relevant active monitors and evaluates conditions.
        """
        active_monitors = self.repo.list_monitors(enabled_only=True)
        alerts: List[MonitorAlert] = []

        context: Dict[str, Any] = {
            "finding_id": finding.finding_id,
            "semantic_class": finding.semantic_class,
            "confidence": finding.confidence,
            "change_area_ha": float(finding.metrics.get("change_area_ha", finding.metrics.get("area_ha", 0.0))),
            "change_percentage": float(finding.metrics.get("change_percentage", 0.0)),
            "event_state": event.state.value if event else "OBSERVED",
            "metrics": finding.metrics,
        }

        for monitor in active_monitors:
            # Check spatial intersection
            if monitor.bounding_box and finding.bounding_box:
                if not SpatialSearchFilter.intersects_bbox(monitor.bounding_box, finding.bounding_box):
                    continue

            # Evaluate deterministic condition tree
            is_match = ConditionEvaluator.evaluate(monitor.trigger_condition, context)
            if is_match:
                reason = (
                    f"Trigger condition matched for '{monitor.name}': "
                    f"{finding.semantic_class.replace('_', ' ').title()} "
                    f"with {round(finding.confidence * 100)}% confidence."
                )

                alert = MonitorNotifier.emit_alert(
                    monitor=monitor,
                    trigger_reason=reason,
                    evidence_data={
                        "finding_id": finding.finding_id,
                        "semantic_class": finding.semantic_class,
                        "confidence": finding.confidence,
                        "metrics": finding.metrics,
                        "bounding_box": finding.bounding_box,
                    },
                    repository=self.repo,
                    event=event,
                    finding=finding,
                    observation_id=finding.observation_ids[0] if finding.observation_ids else "obs_latest",
                    severity="CRITICAL" if finding.confidence >= 0.85 else "WARNING",
                )

                if alert:
                    alerts.append(alert)

                # Record successful monitor run
                run = MonitorRun(
                    run_id=f"run_{uuid.uuid4().hex[:8]}",
                    monitor_id=monitor.monitor_id,
                    observation_id=finding.observation_ids[0] if finding.observation_ids else "obs_latest",
                    status="COMPLETED",
                    analysis_run_id=finding.investigation_id,
                    triggered=is_match,
                    alert_id=alert.alert_id if alert else None,
                )
                self.repo.save_monitor_run(run)

        return alerts

    def list_alerts(self, monitor_id: Optional[str] = None, limit: int = 50) -> List[MonitorAlert]:
        return self.repo.list_monitor_alerts(monitor_id=monitor_id, limit=limit)


monitoring_service = MonitoringService()
