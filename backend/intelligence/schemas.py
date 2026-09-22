"""
TRINETRA Phase 7 — Intelligence API Schemas
Pydantic v2 schemas for events, findings, searches, similarity, anomalies, regions, and monitors.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class EventResponse(BaseModel):
    event_id: str
    title: str
    canonical_region_id: str
    semantic_class: str
    state: str
    confidence: float
    confidence_dimensions: Dict[str, float] = Field(default_factory=dict)
    first_seen: str
    last_seen: str
    supporting_findings: List[str] = Field(default_factory=list)
    supporting_analyses: List[str] = Field(default_factory=list)
    geometry: Dict[str, Any] = Field(default_factory=dict)
    bounding_box: List[float] = Field(default_factory=list)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    version: int = 1
    created_at: str
    updated_at: str


class EventStateUpdateRequest(BaseModel):
    new_state: str = Field(..., description="Target state: CANDIDATE, OBSERVED, CORROBORATED, PERSISTENT, RESOLVED")
    reason: str = Field(..., min_length=3, max_length=500)


class FindingResponse(BaseModel):
    finding_id: str
    investigation_id: str
    type: str
    label: str
    geometry: Dict[str, Any] = Field(default_factory=dict)
    bounding_box: List[float] = Field(default_factory=list)
    confidence: float
    evidence_ids: List[str] = Field(default_factory=list)
    observation_ids: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    semantic_class: str
    created_at: str
    model_provenance: Dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: Optional[str] = Field(None, max_length=500)
    semantic_class: Optional[str] = None
    state: Optional[str] = None
    aoi: Optional[Dict[str, Any]] = None
    bounding_box: Optional[List[float]] = None
    temporal_range: Optional[Dict[str, str]] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    modality: Optional[str] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


class SearchResultItem(BaseModel):
    type: str  # event, finding, investigation, region
    id: str
    title: str
    confidence: float
    semantic_class: str
    state: Optional[str] = None
    match_reasons: List[str] = Field(default_factory=list)
    score: float = 1.0
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    bounding_box: Optional[List[float]] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    total: int
    page: int
    limit: int
    generated_at: str
    data_as_of: str


class SimilarityRequest(BaseModel):
    entity_id: str
    entity_type: str = "finding"  # finding or event
    limit: int = Field(10, ge=1, le=50)
    threshold: float = Field(0.40, ge=0.0, le=1.0)


class SimilarEntityItem(BaseModel):
    id: str
    entity_type: str
    title: str
    similarity: float
    semantic_class: str
    similarity_level: str  # High, Medium, Low
    match_factors: List[str] = Field(default_factory=list)


class SimilarityResponse(BaseModel):
    source_id: str
    similar_items: List[SimilarEntityItem]
    evaluated_count: int


class RegionalSummaryResponse(BaseModel):
    region_id: str
    name: str
    period: str
    event_count: int
    persistent_events: int
    total_changed_area_ha: float
    dominant_categories: List[str]
    anomaly_count: int
    average_confidence: float
    cross_modal_agreement_rate: float
    trajectories: List[Dict[str, Any]] = Field(default_factory=list)


class HotspotResponse(BaseModel):
    hotspot_id: str
    title: str
    event_count: int
    area_km2: float
    bounding_box: List[float]
    dominant_category: str
    events: List[str] = Field(default_factory=list)
    density: float


class AnomalyResponse(BaseModel):
    anomaly_id: str
    baseline_id: str
    region_id: Optional[str] = None
    event_id: Optional[str] = None
    finding_id: Optional[str] = None
    metric_name: str
    observed_value: float
    baseline_mean: float
    baseline_range: List[float]
    anomaly_score: float
    confidence: float
    anomaly_type: str
    explanation: str
    status: str
    created_at: str


class MonitorCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    aoi: Optional[Dict[str, Any]] = Field(default_factory=dict, description="GeoJSON Polygon geometry")
    bounding_box: Optional[List[float]] = None
    bbox: Optional[List[float]] = None
    observation_collection: str = "sentinel-2-l2a"
    schedule_cadence: str = "daily"
    template_id: Optional[str] = ""
    trigger_condition: Dict[str, Any] = Field(
        default_factory=lambda: {
            "operator": "AND",
            "conditions": [
                {"field": "confidence", "operator": ">=", "value": 0.65},
                {"field": "change_area_ha", "operator": ">", "value": 1.0},
            ],
        }
    )
    cooldown_hours: int = Field(24, ge=1, le=720)


class MonitorResponse(BaseModel):
    monitor_id: str
    name: str
    aoi: Dict[str, Any]
    bounding_box: List[float] = Field(default_factory=list)
    observation_collection: str
    schedule_cadence: str
    template_id: str
    trigger_condition: Dict[str, Any]
    enabled: bool
    max_runs: int
    cooldown_hours: int
    total_runs: int = 0
    last_triggered_at: Optional[str] = None
    created_at: str
    updated_at: str


class MonitorAlertResponse(BaseModel):
    alert_id: str
    monitor_id: str
    event_id: Optional[str] = None
    finding_id: Optional[str] = None
    severity: str
    trigger_reason: str
    alert_fingerprint: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    acknowledged: bool = False
    created_at: str


class InvestigationTemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    question: str = Field(..., min_length=5, max_length=500)
    analysis_mode: str = "BI_TEMPORAL"
    required_evidence: List[str] = Field(default_factory=lambda: ["change_map", "spectral_indices"])
    time_configuration: Dict[str, Any] = Field(default_factory=dict)
    semantic_targets: List[str] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)


class InvestigationTemplateResponse(BaseModel):
    template_id: str
    name: str
    question: str
    analysis_mode: str
    required_evidence: List[str]
    time_configuration: Dict[str, Any]
    semantic_targets: List[str]
    filters: Dict[str, Any]
    created_at: str


class TemplateRunRequest(BaseModel):
    observation_ids: List[str] = Field(..., min_length=1)
    aoi: Optional[Dict[str, Any]] = None


class SavedSearchRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    query: str = Field("", max_length=500)
    filters: Dict[str, Any] = Field(default_factory=dict)


class SavedRegionRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    aoi: Dict[str, Any] = Field(...)
    bounding_box: Optional[List[float]] = None
    description: Optional[str] = ""
    tags: List[str] = Field(default_factory=list)


class SplitEventRequest(BaseModel):
    child_definitions: List[Dict[str, Any]] = Field(..., min_length=2, description="At least 2 child definitions required")


class MergeEventsRequest(BaseModel):
    secondary_event_id: str = Field(..., description="ID of the event to merge into this event")

