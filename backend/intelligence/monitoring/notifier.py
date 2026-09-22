"""
TRINETRA Phase 7 — Monitoring Notification & Alert Dispatcher
Generates structured alerts with fingerprint-based duplicate suppression.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from intelligence.models import MonitorAlert, MonitorDefinition, EOEvent, PersistentFinding
from intelligence.provenance import IntelligenceProvenance
from intelligence.repository import IntelligenceRepository


class MonitorNotifier:
    """
    Dispatches alerts to the analyst workspace with duplicate alert suppression.
    """

    @classmethod
    def emit_alert(
        cls,
        monitor: MonitorDefinition,
        trigger_reason: str,
        evidence_data: Dict[str, Any],
        repository: IntelligenceRepository,
        event: Optional[EOEvent] = None,
        finding: Optional[PersistentFinding] = None,
        observation_id: str = "obs_auto",
        severity: str = "WARNING",
    ) -> Optional[MonitorAlert]:
        cond_hash = IntelligenceProvenance.compute_search_hash(
            query=trigger_reason,
            filters=monitor.trigger_condition,
        )

        fp = IntelligenceProvenance.compute_alert_fingerprint(
            monitor_id=monitor.monitor_id,
            event_id=event.event_id if event else (finding.finding_id if finding else "none"),
            observation_id=observation_id,
            condition_hash=cond_hash,
        )

        # Duplicate suppression check
        if repository.has_alert_fingerprint(fp):
            return None  # Suppressed duplicate alert

        alert = MonitorAlert(
            alert_id=f"alert_{uuid.uuid4().hex[:8]}",
            monitor_id=monitor.monitor_id,
            event_id=event.event_id if event else None,
            finding_id=finding.finding_id if finding else None,
            severity=severity,
            trigger_reason=trigger_reason,
            alert_fingerprint=fp,
            evidence=evidence_data,
            acknowledged=False,
            created_at=datetime.utcnow().isoformat(),
        )

        repository.save_monitor_alert(alert)
        return alert
