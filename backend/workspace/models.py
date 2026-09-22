"""
TRINETRA Phase 8 — Analyst Workspace Domain Models
Entity models, state enumerations, investigation plans, task queues,
evidence board items, report documents, and review records.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime


class WorkspaceStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class PlanStepType(str, Enum):
    OBSERVATION_SEARCH = "OBSERVATION_SEARCH"
    ANALYZE_BITEMPORAL = "ANALYZE_BITEMPORAL"
    ANALYZE_SAR_OPTICAL = "ANALYZE_SAR_OPTICAL"
    ANALYZE_SINGLE_IMAGE = "ANALYZE_SINGLE_IMAGE"
    SEARCH_INTELLIGENCE = "SEARCH_INTELLIGENCE"
    FIND_SIMILAR = "FIND_SIMILAR"
    CHECK_PERSISTENCE = "CHECK_PERSISTENCE"
    CHECK_ANOMALY = "CHECK_ANOMALY"
    COMPARE_REGIONS = "COMPARE_REGIONS"
    COMPARE_EVENTS = "COMPARE_EVENTS"
    BUILD_SYNTHESIS = "BUILD_SYNTHESIS"
    BUILD_REPORT = "BUILD_REPORT"


class TaskPriority(str, Enum):
    INTERACTIVE = "INTERACTIVE"
    NORMAL = "NORMAL"
    BACKGROUND = "BACKGROUND"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ReviewStatus(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    REVIEWED = "REVIEWED"
    NEEDS_FOLLOWUP = "NEEDS_FOLLOWUP"
    RESOLVED_BY_ANALYST = "RESOLVED_BY_ANALYST"


class ReportStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    FINAL = "FINAL"
    ARCHIVED = "ARCHIVED"


class EntityReference:
    def __init__(self, type: str, id: str):
        self.type = type
        self.id = id

    def to_dict(self) -> Dict[str, str]:
        return {"type": self.type, "id": self.id}


class Workspace:
    def __init__(
        self,
        workspace_id: str,
        name: str,
        description: str = "",
        status: WorkspaceStatus = WorkspaceStatus.CREATED,
        current_aoi: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        created_by: str = "analyst",
    ):
        now = datetime.utcnow().isoformat()
        self.workspace_id = workspace_id
        self.name = name
        self.description = description
        self.status = status if isinstance(status, WorkspaceStatus) else WorkspaceStatus(status)
        self.current_aoi = current_aoi or {}
        self.created_at = created_at or now
        self.updated_at = updated_at or now
        self.created_by = created_by

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "current_aoi": self.current_aoi,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
        }


class WorkspaceContext:
    def __init__(
        self,
        workspace_id: str,
        current_aoi: Optional[Dict[str, Any]] = None,
        active_regions: Optional[List[str]] = None,
        selected_observations: Optional[List[str]] = None,
        selected_events: Optional[List[str]] = None,
        selected_findings: Optional[List[str]] = None,
        open_investigation_id: Optional[str] = None,
        active_comparison_id: Optional[str] = None,
        active_report_id: Optional[str] = None,
    ):
        self.workspace_id = workspace_id
        self.current_aoi = current_aoi or {}
        self.active_regions = active_regions or []
        self.selected_observations = selected_observations or []
        self.selected_events = selected_events or []
        self.selected_findings = selected_findings or []
        self.open_investigation_id = open_investigation_id
        self.active_comparison_id = active_comparison_id
        self.active_report_id = active_report_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "current_aoi": self.current_aoi,
            "active_regions": self.active_regions,
            "selected_observations": self.selected_observations,
            "selected_events": self.selected_events,
            "selected_findings": self.selected_findings,
            "open_investigation_id": self.open_investigation_id,
            "active_comparison_id": self.active_comparison_id,
            "active_report_id": self.active_report_id,
        }


class InvestigationStep:
    def __init__(
        self,
        step_id: str,
        type: PlanStepType,
        depends_on: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        status: StepStatus = StepStatus.PENDING,
        result_reference: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.step_id = step_id
        self.type = type if isinstance(type, PlanStepType) else PlanStepType(type)
        self.depends_on = depends_on or []
        self.parameters = parameters or {}
        self.status = status if isinstance(status, StepStatus) else StepStatus(status)
        self.result_reference = result_reference
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "type": self.type.value,
            "depends_on": self.depends_on,
            "parameters": self.parameters,
            "status": self.status.value,
            "result_reference": self.result_reference,
            "error": self.error,
        }


class InvestigationPlan:
    def __init__(
        self,
        plan_id: str,
        workspace_id: str,
        title: str,
        question: str,
        steps: Optional[List[InvestigationStep]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        required_evidence: Optional[List[str]] = None,
        status: PlanStatus = PlanStatus.DRAFT,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        now = datetime.utcnow().isoformat()
        self.plan_id = plan_id
        self.workspace_id = workspace_id
        self.title = title
        self.question = question
        self.steps = steps or []
        self.constraints = constraints or {}
        self.required_evidence = required_evidence or []
        self.status = status if isinstance(status, PlanStatus) else PlanStatus(status)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "workspace_id": self.workspace_id,
            "title": self.title,
            "question": self.question,
            "steps": [s.to_dict() for s in self.steps],
            "constraints": self.constraints,
            "required_evidence": self.required_evidence,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class InvestigationPlanRun:
    def __init__(
        self,
        run_id: str,
        plan_id: str,
        execution_index: int = 1,
        status: PlanStatus = PlanStatus.RUNNING,
        step_results: Optional[Dict[str, Any]] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
    ):
        now = datetime.utcnow().isoformat()
        self.run_id = run_id
        self.plan_id = plan_id
        self.execution_index = execution_index
        self.status = status if isinstance(status, PlanStatus) else PlanStatus(status)
        self.step_results = step_results or {}
        self.started_at = started_at or now
        self.completed_at = completed_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "plan_id": self.plan_id,
            "execution_index": self.execution_index,
            "status": self.status.value,
            "step_results": self.step_results,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class BatchJob:
    def __init__(
        self,
        batch_id: str,
        workspace_id: str,
        template_id: str,
        targets: List[Dict[str, Any]],
        status: str = "QUEUED",
        concurrency: int = 2,
        results: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        now = datetime.utcnow().isoformat()
        self.batch_id = batch_id
        self.workspace_id = workspace_id
        self.template_id = template_id
        self.targets = targets
        self.status = status
        self.concurrency = concurrency
        self.results = results or {"completed": [], "failed": [], "skipped": []}
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "workspace_id": self.workspace_id,
            "template_id": self.template_id,
            "targets": self.targets,
            "status": self.status,
            "concurrency": self.concurrency,
            "results": self.results,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class RegionComparison:
    def __init__(
        self,
        comparison_id: str,
        workspace_id: str,
        region_a_id: str,
        region_b_id: str,
        period: str = "last_12_months",
        metrics: Optional[Dict[str, Any]] = None,
        differences: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
        created_at: Optional[str] = None,
    ):
        self.comparison_id = comparison_id
        self.workspace_id = workspace_id
        self.region_a_id = region_a_id
        self.region_b_id = region_b_id
        self.period = period
        self.metrics = metrics or {}
        self.differences = differences or {}
        self.warnings = warnings or []
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "workspace_id": self.workspace_id,
            "region_a_id": self.region_a_id,
            "region_b_id": self.region_b_id,
            "period": self.period,
            "metrics": self.metrics,
            "differences": self.differences,
            "warnings": self.warnings,
            "created_at": self.created_at,
        }


class AnalysisScenario:
    def __init__(
        self,
        scenario_id: str,
        workspace_id: str,
        base_run_id: str,
        parameter_overrides: Dict[str, Any],
        results: Optional[Dict[str, Any]] = None,
        difference_summary: str = "",
        created_at: Optional[str] = None,
    ):
        self.scenario_id = scenario_id
        self.workspace_id = workspace_id
        self.base_run_id = base_run_id
        self.parameter_overrides = parameter_overrides
        self.results = results or {}
        self.difference_summary = difference_summary
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "workspace_id": self.workspace_id,
            "base_run_id": self.base_run_id,
            "parameter_overrides": self.parameter_overrides,
            "results": self.results,
            "difference_summary": self.difference_summary,
            "created_at": self.created_at,
        }


class EvidenceBoardItem:
    def __init__(
        self,
        item_id: str,
        workspace_id: str,
        type: str,
        source_id: str,
        position: Optional[Dict[str, float]] = None,
        title: str = "",
        annotation: str = "",
        created_at: Optional[str] = None,
    ):
        self.item_id = item_id
        self.workspace_id = workspace_id
        self.type = type  # FINDING, EVENT, OBSERVATION, REGION, EVIDENCE, NOTE, IMAGE, TIMELINE_EVENT, CHART
        self.source_id = source_id
        self.position = position or {"x": 100.0, "y": 100.0}
        self.title = title
        self.annotation = annotation
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "workspace_id": self.workspace_id,
            "type": self.type,
            "source_id": self.source_id,
            "position": self.position,
            "title": self.title,
            "annotation": self.annotation,
            "created_at": self.created_at,
        }


class EvidenceBoardRelation:
    def __init__(
        self,
        relation_id: str,
        workspace_id: str,
        source_item_id: str,
        target_item_id: str,
        relation_type: str = "supports",  # supports, related_to, contradicts, follow_up
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
    ):
        self.relation_id = relation_id
        self.workspace_id = workspace_id
        self.source_item_id = source_item_id
        self.target_item_id = target_item_id
        self.relation_type = relation_type
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "workspace_id": self.workspace_id,
            "source_item_id": self.source_item_id,
            "target_item_id": self.target_item_id,
            "relation_type": self.relation_type,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class Annotation:
    def __init__(
        self,
        annotation_id: str,
        workspace_id: str,
        geometry: Optional[Dict[str, Any]] = None,
        text: str = "",
        type: str = "TEXT",  # TEXT, LABEL, REGION_NOTE, QUESTION
        linked_entity_type: Optional[str] = None,
        linked_entity_id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        now = datetime.utcnow().isoformat()
        self.annotation_id = annotation_id
        self.workspace_id = workspace_id
        self.geometry = geometry or {}
        self.text = text
        self.type = type
        self.linked_entity_type = linked_entity_type
        self.linked_entity_id = linked_entity_id
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "annotation_id": self.annotation_id,
            "workspace_id": self.workspace_id,
            "geometry": self.geometry,
            "text": self.text,
            "type": self.type,
            "linked_entity_type": self.linked_entity_type,
            "linked_entity_id": self.linked_entity_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ReviewRecord:
    def __init__(
        self,
        review_id: str,
        workspace_id: str,
        entity_type: str,
        entity_id: str,
        status: ReviewStatus = ReviewStatus.UNREVIEWED,
        review_note: str = "",
        reviewed_at: Optional[str] = None,
        analyst_id: str = "analyst",
    ):
        self.review_id = review_id
        self.workspace_id = workspace_id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.status = status if isinstance(status, ReviewStatus) else ReviewStatus(status)
        self.review_note = review_note
        self.reviewed_at = reviewed_at or datetime.utcnow().isoformat()
        self.analyst_id = analyst_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_id": self.review_id,
            "workspace_id": self.workspace_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "status": self.status.value,
            "review_note": self.review_note,
            "reviewed_at": self.reviewed_at,
            "analyst_id": self.analyst_id,
        }


class FollowUp:
    def __init__(
        self,
        follow_up_id: str,
        workspace_id: str,
        linked_entity_type: str,
        linked_entity_id: str,
        note: str,
        status: str = "OPEN",  # OPEN, IN_PROGRESS, COMPLETE, CANCELLED
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        now = datetime.utcnow().isoformat()
        self.follow_up_id = follow_up_id
        self.workspace_id = workspace_id
        self.linked_entity_type = linked_entity_type
        self.linked_entity_id = linked_entity_id
        self.note = note
        self.status = status
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "follow_up_id": self.follow_up_id,
            "workspace_id": self.workspace_id,
            "linked_entity_type": self.linked_entity_type,
            "linked_entity_id": self.linked_entity_id,
            "note": self.note,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ReportClaim:
    def __init__(
        self,
        claim_id: str,
        text: str,
        evidence_ids: Optional[List[str]] = None,
        type: str = "FINDING",  # OBSERVATION, MEASUREMENT, FINDING, INTERPRETATION, LIMITATION, ANALYST_NOTE
    ):
        self.claim_id = claim_id
        self.text = text
        self.evidence_ids = evidence_ids or []
        self.type = type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "evidence_ids": self.evidence_ids,
            "type": self.type,
        }


class ReportSection:
    def __init__(
        self,
        section_id: str,
        type: str,  # TITLE, SUMMARY, AOI, CONTEXT, METHODOLOGY, FINDINGS, EVENTS, EVIDENCE, MAPS, CHARTS, TIMELINE, CONFLICTS, LIMITATIONS, NOTES, PROVENANCE
        title: str,
        content: str = "",
        source_ids: Optional[List[str]] = None,
        claims: Optional[List[ReportClaim]] = None,
        author_type: str = "SYSTEM_GENERATED",  # AI_GENERATED, ANALYST_AUTHORED, MIXED, SYSTEM_GENERATED
    ):
        self.section_id = section_id
        self.type = type
        self.title = title
        self.content = content
        self.source_ids = source_ids or []
        self.claims = claims or []
        self.author_type = author_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "source_ids": self.source_ids,
            "claims": [c.to_dict() for c in self.claims],
            "author_type": self.author_type,
        }


class ReportDocument:
    def __init__(
        self,
        report_id: str,
        workspace_id: str,
        title: str,
        status: ReportStatus = ReportStatus.DRAFT,
        sections: Optional[List[ReportSection]] = None,
        version: int = 1,
        manifest: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        now = datetime.utcnow().isoformat()
        self.report_id = report_id
        self.workspace_id = workspace_id
        self.title = title
        self.status = status if isinstance(status, ReportStatus) else ReportStatus(status)
        self.sections = sections or []
        self.version = version
        self.manifest = manifest or {}
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "workspace_id": self.workspace_id,
            "title": self.title,
            "status": self.status.value,
            "sections": [s.to_dict() for s in self.sections],
            "version": self.version,
            "manifest": self.manifest,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class WorkspaceTask:
    def __init__(
        self,
        task_id: str,
        workspace_id: str,
        type: str,  # SEARCH, ANALYSIS, INVESTIGATION, BATCH, REPORT, EXPORT, MONITOR
        priority: TaskPriority = TaskPriority.NORMAL,
        status: TaskStatus = TaskStatus.PENDING,
        progress: Optional[Dict[str, Any]] = None,
        result_reference: Optional[str] = None,
        error: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        created_at: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
    ):
        now = datetime.utcnow().isoformat()
        self.task_id = task_id
        self.workspace_id = workspace_id
        self.type = type
        self.priority = priority if isinstance(priority, TaskPriority) else TaskPriority(priority)
        self.status = status if isinstance(status, TaskStatus) else TaskStatus(status)
        self.progress = progress or {"stage": "QUEUED", "percentage": 0}
        self.result_reference = result_reference
        self.error = error
        self.idempotency_key = idempotency_key
        self.created_at = created_at or now
        self.started_at = started_at
        self.completed_at = completed_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "workspace_id": self.workspace_id,
            "type": self.type,
            "priority": self.priority.value,
            "status": self.status.value,
            "progress": self.progress,
            "result_reference": self.result_reference,
            "error": self.error,
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class WorkspaceSnapshot:
    def __init__(
        self,
        snapshot_id: str,
        workspace_id: str,
        state: Dict[str, Any],
        created_at: Optional[str] = None,
    ):
        self.snapshot_id = snapshot_id
        self.workspace_id = workspace_id
        self.state = state
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "workspace_id": self.workspace_id,
            "state": self.state,
            "created_at": self.created_at,
        }


class WorkspaceActivity:
    def __init__(
        self,
        activity_id: str,
        workspace_id: str,
        activity_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ):
        self.activity_id = activity_id
        self.workspace_id = workspace_id
        self.activity_type = activity_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.details = details or {}
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "workspace_id": self.workspace_id,
            "activity_type": self.activity_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "timestamp": self.timestamp,
        }
