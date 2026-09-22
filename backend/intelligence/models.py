"""
TRINETRA Phase 7 — Persistent EO Intelligence Domain Models
Durable spatiotemporal entities: CanonicalRegion, EOEvent, Finding, Monitor, Alert, Baseline.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class EventState(str, Enum):
    CANDIDATE = "CANDIDATE"
    OBSERVED = "OBSERVED"
    CORROBORATED = "CORROBORATED"
    PERSISTENT = "PERSISTENT"
    RESOLVED = "RESOLVED"


class CanonicalRegion:
    def __init__(
        self,
        canonical_region_id: str,
        name: str = "",
        geometry: Optional[Dict[str, Any]] = None,
        bounding_box: Optional[List[float]] = None,
        observed_region_ids: Optional[List[str]] = None,
        first_seen: Optional[str] = None,
        last_seen: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        now = datetime.utcnow().isoformat()
        self.canonical_region_id = canonical_region_id
        self.name = name or f"Region {canonical_region_id[-6:]}"
        self.geometry = geometry or {}
        self.bounding_box = bounding_box or []
        self.observed_region_ids = observed_region_ids or []
        self.first_seen = first_seen or now
        self.last_seen = last_seen or now
        self.description = description
        self.tags = tags or []
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_region_id": self.canonical_region_id,
            "name": self.name,
            "geometry": self.geometry,
            "bounding_box": self.bounding_box,
            "observed_region_ids": self.observed_region_ids,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class EOEvent:
    def __init__(
        self,
        event_id: str,
        title: str,
        canonical_region_id: str,
        semantic_class: str,
        state: EventState = EventState.CANDIDATE,
        confidence: float = 0.5,
        confidence_dimensions: Optional[Dict[str, float]] = None,
        first_seen: Optional[str] = None,
        last_seen: Optional[str] = None,
        supporting_findings: Optional[List[str]] = None,
        supporting_analyses: Optional[List[str]] = None,
        geometry: Optional[Dict[str, Any]] = None,
        bounding_box: Optional[List[float]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: int = 1,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        now = datetime.utcnow().isoformat()
        self.event_id = event_id
        self.title = title
        self.canonical_region_id = canonical_region_id
        self.semantic_class = semantic_class
        self.state = state if isinstance(state, EventState) else EventState(state)
        self.confidence = max(0.05, min(1.0, round(confidence, 3)))
        self.confidence_dimensions = confidence_dimensions or {
            "evidence_strength": self.confidence,
            "temporal_persistence": 0.5,
            "spatial_consistency": 0.8,
            "cross_modal_support": 0.5,
            "model_quality": 0.85,
            "contradiction_penalty": 0.0,
        }
        self.first_seen = first_seen or now
        self.last_seen = last_seen or now
        self.supporting_findings = supporting_findings or []
        self.supporting_analyses = supporting_analyses or []
        self.geometry = geometry or {}
        self.bounding_box = bounding_box or []
        self.history = history or [
            {
                "timestamp": now,
                "from_state": None,
                "to_state": self.state.value,
                "reason": "Event initialization",
                "finding_id": self.supporting_findings[0] if self.supporting_findings else None,
            }
        ]
        self.metadata = metadata or {}
        self.version = version
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "canonical_region_id": self.canonical_region_id,
            "semantic_class": self.semantic_class,
            "state": self.state.value if hasattr(self.state, "value") else str(self.state),
            "confidence": self.confidence,
            "confidence_dimensions": self.confidence_dimensions,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "supporting_findings": self.supporting_findings,
            "supporting_analyses": self.supporting_analyses,
            "geometry": self.geometry,
            "bounding_box": self.bounding_box,
            "history": self.history,
            "metadata": self.metadata,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class PersistentFinding:
    def __init__(
        self,
        finding_id: str,
        investigation_id: str,
        type: str,
        label: str,
        geometry: Optional[Dict[str, Any]] = None,
        bounding_box: Optional[List[float]] = None,
        confidence: float = 0.8,
        evidence_ids: Optional[List[str]] = None,
        observation_ids: Optional[List[str]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        semantic_class: str = "GENERAL_CHANGE",
        created_at: Optional[str] = None,
        model_provenance: Optional[Dict[str, Any]] = None,
    ):
        self.finding_id = finding_id
        self.investigation_id = investigation_id
        self.type = type
        self.label = label
        self.geometry = geometry or {}
        self.bounding_box = bounding_box or []
        self.confidence = round(confidence, 3)
        self.evidence_ids = evidence_ids or []
        self.observation_ids = observation_ids or []
        self.metrics = metrics or {}
        self.semantic_class = semantic_class
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.model_provenance = model_provenance or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "investigation_id": self.investigation_id,
            "type": self.type,
            "label": self.label,
            "geometry": self.geometry,
            "bounding_box": self.bounding_box,
            "confidence": self.confidence,
            "evidence_ids": self.evidence_ids,
            "observation_ids": self.observation_ids,
            "metrics": self.metrics,
            "semantic_class": self.semantic_class,
            "created_at": self.created_at,
            "model_provenance": self.model_provenance,
        }


class PersistentEvidence:
    def __init__(
        self,
        evidence_id: str,
        source: str,
        type: str,
        observation_id: str = "",
        geometry: Optional[Dict[str, Any]] = None,
        bounding_box: Optional[List[float]] = None,
        value: Optional[Dict[str, Any]] = None,
        quality: float = 0.9,
        confidence: float = 0.85,
        provenance: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
    ):
        self.evidence_id = evidence_id
        self.source = source
        self.type = type
        self.observation_id = observation_id
        self.geometry = geometry or {}
        self.bounding_box = bounding_box or []
        self.value = value or {}
        self.quality = round(quality, 3)
        self.confidence = round(confidence, 3)
        self.provenance = provenance or {}
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "type": self.type,
            "observation_id": self.observation_id,
            "geometry": self.geometry,
            "bounding_box": self.bounding_box,
            "value": self.value,
            "quality": self.quality,
            "confidence": self.confidence,
            "provenance": self.provenance,
            "created_at": self.created_at,
        }


class RegionLineage:
    def __init__(
        self,
        lineage_id: str,
        parent_region_id: str,
        child_region_id: str,
        relationship_type: str,  # MERGED_FROM, SPLIT_FROM, PERSISTED_AS, EXPANDED_TO, CONTRACTED_TO, REAPPEARED_AS
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
    ):
        self.lineage_id = lineage_id
        self.parent_region_id = parent_region_id
        self.child_region_id = child_region_id
        self.relationship_type = relationship_type
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lineage_id": self.lineage_id,
            "parent_region_id": self.parent_region_id,
            "child_region_id": self.child_region_id,
            "relationship_type": self.relationship_type,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class EventRelationship:
    def __init__(
        self,
        relationship_id: str,
        source_event_id: str,
        target_event_id: str,
        relationship_type: str,  # DERIVED_FROM, SUPPORTS, CORROBORATES, CONTRADICTS, SAME_EVENT, SAME_REGION, TEMPORALLY_FOLLOWS, SPATIALLY_OVERLAPS, SIMILAR_TO, TRIGGERED_BY
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
    ):
        self.relationship_id = relationship_id
        self.source_event_id = source_event_id
        self.target_event_id = target_event_id
        self.relationship_type = relationship_type
        self.weight = round(weight, 3)
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "source_event_id": self.source_event_id,
            "target_event_id": self.target_event_id,
            "relationship_type": self.relationship_type,
            "weight": self.weight,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class InvestigationTemplate:
    def __init__(
        self,
        template_id: str,
        name: str,
        question: str,
        analysis_mode: str = "BI_TEMPORAL",
        required_evidence: Optional[List[str]] = None,
        time_configuration: Optional[Dict[str, Any]] = None,
        semantic_targets: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
    ):
        self.template_id = template_id
        self.name = name
        self.question = question
        self.analysis_mode = analysis_mode
        self.required_evidence = required_evidence or ["change_map", "spectral_indices"]
        self.time_configuration = time_configuration or {}
        self.semantic_targets = semantic_targets or []
        self.filters = filters or {}
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "question": self.question,
            "analysis_mode": self.analysis_mode,
            "required_evidence": self.required_evidence,
            "time_configuration": self.time_configuration,
            "semantic_targets": self.semantic_targets,
            "filters": self.filters,
            "created_at": self.created_at,
        }


class MonitorDefinition:
    def __init__(
        self,
        monitor_id: str,
        name: str,
        aoi: Optional[Dict[str, Any]] = None,
        bounding_box: Optional[List[float]] = None,
        bbox: Optional[List[float]] = None,
        observation_collection: str = "sentinel-2-l2a",
        schedule_cadence: str = "daily",  # daily, weekly, hourly
        template_id: str = "",
        trigger_condition: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        max_runs: int = 100,
        cooldown_hours: int = 24,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        now = datetime.utcnow().isoformat()
        self.monitor_id = monitor_id
        self.name = name
        self.aoi = aoi or {}
        self.bounding_box = bounding_box or bbox or []
        self.observation_collection = observation_collection
        self.schedule_cadence = schedule_cadence
        self.template_id = template_id
        self.trigger_condition = trigger_condition or {
            "operator": "AND",
            "conditions": [
                {"field": "confidence", "operator": ">=", "value": 0.65},
                {"field": "change_area_ha", "operator": ">", "value": 1.0},
            ],
        }
        self.enabled = enabled
        self.max_runs = max_runs
        self.cooldown_hours = cooldown_hours
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "monitor_id": self.monitor_id,
            "name": self.name,
            "aoi": self.aoi,
            "bounding_box": self.bounding_box,
            "observation_collection": self.observation_collection,
            "schedule_cadence": self.schedule_cadence,
            "template_id": self.template_id,
            "trigger_condition": self.trigger_condition,
            "enabled": self.enabled,
            "max_runs": self.max_runs,
            "cooldown_hours": self.cooldown_hours,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class MonitorRun:
    def __init__(
        self,
        run_id: str,
        monitor_id: str,
        observation_id: str,
        status: str = "PENDING",  # PENDING, PROCESSING, COMPLETED, FAILED, SKIPPED
        analysis_run_id: Optional[str] = None,
        triggered: bool = False,
        alert_id: Optional[str] = None,
        error_category: Optional[str] = None,
        error_message: Optional[str] = None,
        executed_at: Optional[str] = None,
    ):
        self.run_id = run_id
        self.monitor_id = monitor_id
        self.observation_id = observation_id
        self.status = status
        self.analysis_run_id = analysis_run_id
        self.triggered = triggered
        self.alert_id = alert_id
        self.error_category = error_category
        self.error_message = error_message
        self.executed_at = executed_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "monitor_id": self.monitor_id,
            "observation_id": self.observation_id,
            "status": self.status,
            "analysis_run_id": self.analysis_run_id,
            "triggered": self.triggered,
            "alert_id": self.alert_id,
            "error_category": self.error_category,
            "error_message": self.error_message,
            "executed_at": self.executed_at,
        }


class MonitorAlert:
    def __init__(
        self,
        alert_id: str,
        monitor_id: str,
        event_id: Optional[str] = None,
        finding_id: Optional[str] = None,
        severity: str = "WARNING",  # CRITICAL, WARNING, INFO
        trigger_reason: str = "",
        alert_fingerprint: str = "",
        evidence: Optional[Dict[str, Any]] = None,
        acknowledged: bool = False,
        created_at: Optional[str] = None,
    ):
        self.alert_id = alert_id
        self.monitor_id = monitor_id
        self.event_id = event_id
        self.finding_id = finding_id
        self.severity = severity
        self.trigger_reason = trigger_reason
        self.alert_fingerprint = alert_fingerprint
        self.evidence = evidence or {}
        self.acknowledged = acknowledged
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "monitor_id": self.monitor_id,
            "event_id": self.event_id,
            "finding_id": self.finding_id,
            "severity": self.severity,
            "trigger_reason": self.trigger_reason,
            "alert_fingerprint": self.alert_fingerprint,
            "evidence": self.evidence,
            "acknowledged": self.acknowledged,
            "created_at": self.created_at,
        }


class Baseline:
    def __init__(
        self,
        baseline_id: str,
        metric_name: str,
        spatial_unit: str,
        temporal_window: str,
        sample_count: int,
        mean: float,
        std: float,
        median: float,
        mad: float,
        p90: float,
        min_val: float,
        max_val: float,
        seasonal_grouping: Optional[str] = None,
        version: str = "v1.0",
        created_at: Optional[str] = None,
    ):
        self.baseline_id = baseline_id
        self.metric_name = metric_name
        self.spatial_unit = spatial_unit
        self.temporal_window = temporal_window
        self.seasonal_grouping = seasonal_grouping
        self.sample_count = sample_count
        self.mean = round(mean, 4)
        self.std = round(std, 4)
        self.median = round(median, 4)
        self.mad = round(mad, 4)
        self.p90 = round(p90, 4)
        self.min_val = round(min_val, 4)
        self.max_val = round(max_val, 4)
        self.version = version
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "metric_name": self.metric_name,
            "spatial_unit": self.spatial_unit,
            "temporal_window": self.temporal_window,
            "seasonal_grouping": self.seasonal_grouping,
            "sample_count": self.sample_count,
            "mean": self.mean,
            "std": self.std,
            "median": self.median,
            "mad": self.mad,
            "p90": self.p90,
            "min_val": self.min_val,
            "max_val": self.max_val,
            "version": self.version,
            "created_at": self.created_at,
        }


class AnomalyRecord:
    def __init__(
        self,
        anomaly_id: str,
        baseline_id: str,
        metric_name: str,
        observed_value: float,
        baseline_mean: float,
        baseline_std: float,
        baseline_range: List[float],
        anomaly_score: float,
        confidence: float,
        anomaly_type: str,  # TEMPORAL_ACCELERATION, SPATIAL_OUTLIER, SUDDEN_REVERSAL, UNUSUAL_MAGNITUDE
        explanation: str,
        region_id: Optional[str] = None,
        event_id: Optional[str] = None,
        finding_id: Optional[str] = None,
        status: str = "ACTIVE",  # ACTIVE, INVESTIGATED, DISMISSED
        created_at: Optional[str] = None,
    ):
        self.anomaly_id = anomaly_id
        self.baseline_id = baseline_id
        self.region_id = region_id
        self.event_id = event_id
        self.finding_id = finding_id
        self.metric_name = metric_name
        self.observed_value = round(observed_value, 4)
        self.baseline_mean = round(baseline_mean, 4)
        self.baseline_std = round(baseline_std, 4)
        self.baseline_range = [round(x, 4) for x in baseline_range]
        self.anomaly_score = round(anomaly_score, 3)
        self.confidence = round(confidence, 3)
        self.anomaly_type = anomaly_type
        self.explanation = explanation
        self.status = status
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "baseline_id": self.baseline_id,
            "region_id": self.region_id,
            "event_id": self.event_id,
            "finding_id": self.finding_id,
            "metric_name": self.metric_name,
            "observed_value": self.observed_value,
            "baseline_mean": self.baseline_mean,
            "baseline_std": self.baseline_std,
            "baseline_range": self.baseline_range,
            "anomaly_score": self.anomaly_score,
            "confidence": self.confidence,
            "anomaly_type": self.anomaly_type,
            "explanation": self.explanation,
            "status": self.status,
            "created_at": self.created_at,
        }
