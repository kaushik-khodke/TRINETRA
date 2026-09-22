"""
TRINETRA Phase 8 — Analyst Workspace API Schemas
Pydantic v2 validation models for workspace management, planning,
comparison, evidence boards, annotations, reporting, and task execution.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# 1. Workspace Core
# =============================================================================

class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, description="Workspace title")
    description: Optional[str] = Field("", max_length=1000)
    current_aoi: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Active GeoJSON AOI polygon")


class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    description: Optional[str] = Field(None, max_length=1000)
    current_aoi: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, description="CREATED, ACTIVE, PAUSED, COMPLETED, ARCHIVED")


class WorkspaceResponse(BaseModel):
    workspace_id: str
    name: str
    description: str = ""
    status: str
    current_aoi: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    created_by: str = "analyst"


class WorkspaceContextResponse(BaseModel):
    workspace_id: str
    current_aoi: Dict[str, Any] = Field(default_factory=dict)
    active_regions: List[str] = Field(default_factory=list)
    selected_observations: List[str] = Field(default_factory=list)
    selected_events: List[str] = Field(default_factory=list)
    selected_findings: List[str] = Field(default_factory=list)
    open_investigation_id: Optional[str] = None
    active_comparison_id: Optional[str] = None
    active_report_id: Optional[str] = None


class WorkspaceActivityResponse(BaseModel):
    activity_id: str
    workspace_id: str
    activity_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str


# =============================================================================
# 2. Investigation Plans & DAG Execution
# =============================================================================

class InvestigationStepSchema(BaseModel):
    step_id: str = Field(..., min_length=2, max_length=64)
    type: str = Field(..., description="PlanStepType enumeration string")
    depends_on: List[str] = Field(default_factory=list, description="IDs of steps that must complete before this step")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field("PENDING", description="StepStatus string")
    result_reference: Optional[str] = None
    error: Optional[str] = None


class InvestigationPlanCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    question: str = Field(..., min_length=5, max_length=500)
    steps: List[InvestigationStepSchema] = Field(..., min_length=1, max_length=20)
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)
    required_evidence: Optional[List[str]] = Field(default_factory=list)


class InvestigationPlanResponse(BaseModel):
    plan_id: str
    workspace_id: str
    title: str
    question: str
    steps: List[InvestigationStepSchema]
    constraints: Dict[str, Any] = Field(default_factory=dict)
    required_evidence: List[str] = Field(default_factory=list)
    status: str
    created_at: str
    updated_at: str


class PlanValidationResponse(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    estimated_resources: Dict[str, Any] = Field(default_factory=dict)


class PlanRunResponse(BaseModel):
    run_id: str
    plan_id: str
    execution_index: int
    status: str
    step_results: Dict[str, Any] = Field(default_factory=dict)
    started_at: str
    completed_at: Optional[str] = None


InvestigationPlanRunResponse = PlanRunResponse


# =============================================================================
# 3. Batch Processing
# =============================================================================

class BatchJobCreateRequest(BaseModel):
    template_id: str = Field(..., min_length=2, max_length=64)
    targets: List[Dict[str, Any]] = Field(..., min_length=1, max_length=50)
    concurrency: int = Field(2, ge=1, le=4)


class BatchJobResponse(BaseModel):
    batch_id: str
    workspace_id: str
    template_id: str
    targets: List[Dict[str, Any]]
    status: str
    concurrency: int
    results: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


# =============================================================================
# 4. Comparisons & Sensitivity
# =============================================================================

class RegionComparisonRequest(BaseModel):
    region_a_id: str = Field(..., description="First canonical region ID")
    region_b_id: str = Field(..., description="Second canonical region ID")
    period: str = Field("last_12_months")


class RegionComparisonResponse(BaseModel):
    comparison_id: str
    workspace_id: str
    region_a_id: str
    region_b_id: str
    period: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    differences: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    created_at: str


class EventComparisonRequest(BaseModel):
    event_ids: List[str] = Field(..., min_length=2, max_length=10)


class FindingComparisonRequest(BaseModel):
    finding_ids: List[str] = Field(..., min_length=2, max_length=10)


class ScenarioCreateRequest(BaseModel):
    base_run_id: str = Field(..., min_length=2)
    parameter_overrides: Dict[str, Any] = Field(...)


class AnalysisScenarioResponse(BaseModel):
    scenario_id: str
    workspace_id: str
    base_run_id: str
    parameter_overrides: Dict[str, Any]
    results: Dict[str, Any]
    difference_summary: str
    created_at: str


# =============================================================================
# 5. Evidence Board
# =============================================================================

class BoardItemCreateRequest(BaseModel):
    type: str = Field(..., description="FINDING, EVENT, OBSERVATION, REGION, EVIDENCE, NOTE, IMAGE, TIMELINE_EVENT, CHART")
    source_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=150)
    position: Optional[Dict[str, float]] = Field(default_factory=lambda: {"x": 100.0, "y": 100.0})
    annotation: Optional[str] = Field("", max_length=1000)


class BoardItemUpdateRequest(BaseModel):
    position: Optional[Dict[str, float]] = None
    title: Optional[str] = Field(None, max_length=150)
    annotation: Optional[str] = Field(None, max_length=1000)


class BoardItemResponse(BaseModel):
    item_id: str
    workspace_id: str
    type: str
    source_id: str
    position: Dict[str, float]
    title: str
    annotation: str
    created_at: str


class BoardRelationCreateRequest(BaseModel):
    source_item_id: str
    target_item_id: str
    relation_type: str = Field("supports", description="supports, related_to, contradicts, follow_up")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BoardRelationResponse(BaseModel):
    relation_id: str
    workspace_id: str
    source_item_id: str
    target_item_id: str
    relation_type: str
    metadata: Dict[str, Any]
    created_at: str


# =============================================================================
# 6. Annotations, Reviews & Follow-Ups
# =============================================================================

class AnnotationCreateRequest(BaseModel):
    geometry: Optional[Dict[str, Any]] = Field(default_factory=dict)
    text: str = Field(..., min_length=1, max_length=2000)
    type: str = Field("TEXT", description="TEXT, LABEL, REGION_NOTE, QUESTION")
    linked_entity_type: Optional[str] = None
    linked_entity_id: Optional[str] = None


class AnnotationResponse(BaseModel):
    annotation_id: str
    workspace_id: str
    geometry: Dict[str, Any]
    text: str
    type: str
    linked_entity_type: Optional[str] = None
    linked_entity_id: Optional[str] = None
    created_at: str
    updated_at: str


class ReviewStatusUpdateRequest(BaseModel):
    entity_type: str = Field(..., description="finding, event, region")
    entity_id: str
    status: str = Field(..., description="UNREVIEWED, REVIEWED, NEEDS_FOLLOWUP, RESOLVED_BY_ANALYST")
    review_note: Optional[str] = Field("", max_length=1000)


class ReviewRecordResponse(BaseModel):
    review_id: str
    workspace_id: str
    entity_type: str
    entity_id: str
    status: str
    review_note: str
    reviewed_at: str
    analyst_id: str


class FollowUpCreateRequest(BaseModel):
    linked_entity_type: str
    linked_entity_id: str
    note: str = Field(..., min_length=3, max_length=1000)


class FollowUpResponse(BaseModel):
    follow_up_id: str
    workspace_id: str
    linked_entity_type: str
    linked_entity_id: str
    note: str
    status: str
    created_at: str
    updated_at: str


# =============================================================================
# 7. Reports & Evidence Packages
# =============================================================================

class ReportClaimSchema(BaseModel):
    claim_id: str
    text: str
    evidence_ids: List[str] = Field(default_factory=list)
    type: str = "FINDING"


class ReportSectionSchema(BaseModel):
    section_id: str
    type: str
    title: str
    content: str = ""
    source_ids: List[str] = Field(default_factory=list)
    claims: List[ReportClaimSchema] = Field(default_factory=list)
    author_type: str = "SYSTEM_GENERATED"


class ReportCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    section_types: Optional[List[str]] = Field(default_factory=list)
    selected_entity_ids: Optional[List[str]] = Field(default_factory=list)


class ReportResponse(BaseModel):
    report_id: str
    workspace_id: str
    title: str
    status: str
    sections: List[ReportSectionSchema]
    version: int
    manifest: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ReportValidationResponse(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# =============================================================================
# 8. Unified Task Queue & Search
# =============================================================================

class WorkspaceTaskResponse(BaseModel):
    task_id: str
    workspace_id: str
    type: str
    priority: str
    status: str
    progress: Dict[str, Any]
    result_reference: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class WorkspaceSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    entity_types: Optional[List[str]] = Field(default_factory=list)
    semantic_class: Optional[str] = None
    limit: int = Field(25, ge=1, le=100)


class WorkspaceSearchResultItem(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    snippet: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkspaceSearchResponse(BaseModel):
    query: str
    results: List[WorkspaceSearchResultItem]
    total: int


class WorkspaceTaskCreateRequest(BaseModel):
    type: str = Field(..., description="SEARCH, ANALYSIS, INVESTIGATION, BATCH, REPORT, EXPORT, MONITOR")
    priority: str = Field("NORMAL", description="INTERACTIVE, NORMAL, BACKGROUND")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None


class WorkspaceSnapshotResponse(BaseModel):
    snapshot_id: str
    workspace_id: str
    state: Dict[str, Any]
    created_at: str


class ReportDocumentCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    sections: List[ReportSectionSchema] = Field(default_factory=list)


# Backward-compatible convenience aliases
EvidenceBoardItemCreateRequest = BoardItemCreateRequest
EvidenceBoardItemResponse = BoardItemResponse
EvidenceBoardRelationCreateRequest = BoardRelationCreateRequest
EvidenceBoardRelationResponse = BoardRelationResponse
ReviewRecordCreateRequest = ReviewStatusUpdateRequest
ReportDocumentResponse = ReportResponse
