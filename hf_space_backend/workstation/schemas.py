"""
TRINETRA Workstation — Domain Schemas & Contracts
Implements typed contracts for Missions, AOIs, Assets, Pipelines, Analysis Plans,
Execution Runs, Notebook Entries, and Provenance Manifests based on implementation-plan.md.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
from pydantic import BaseModel, Field


class MissionStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class AOISourceType(str, Enum):
    DRAWN = "drawn"
    UPLOADED = "uploaded"
    DERIVED = "derived"


class AssetType(str, Enum):
    UPLOADED = "uploaded"
    CATALOG_ITEM = "catalog_item"
    DERIVED = "derived"


class AssetStatus(str, Enum):
    REGISTERED = "registered"
    VALIDATING = "validating"
    READY = "ready"
    WARNING = "warning"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"


class PlanStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class RunStatus(str, Enum):
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    SUCCEEDED_WITH_WARNINGS = "succeeded_with_warnings"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"


# --- Core Entities ---

class AreaOfInterest(BaseModel):
    id: str = Field(default_factory=lambda: f"aoi_{uuid.uuid4().hex[:8]}")
    mission_id: str
    name: str
    geometry: Dict[str, Any]  # GeoJSON Polygon / MultiPolygon
    bbox: Optional[List[float]] = None  # [minLon, minLat, maxLon, maxLat]
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    source_type: AOISourceType = AOISourceType.DRAWN
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AssetBand(BaseModel):
    id: str = Field(default_factory=lambda: f"band_{uuid.uuid4().hex[:8]}")
    band_index: int
    name: str
    common_name: Optional[str] = None  # e.g. "red", "nir", "VV"
    wavelength_min_nm: Optional[float] = None
    wavelength_max_nm: Optional[float] = None
    scale_factor: float = 1.0
    add_offset: float = 0.0
    unit: Optional[str] = None


class AssetVersion(BaseModel):
    id: str = Field(default_factory=lambda: f"ast_v_{uuid.uuid4().hex[:8]}")
    asset_id: str
    version_number: int = 1
    object_uri: str
    thumbnail_uri: Optional[str] = None
    mime_type: str = "image/tiff; application=geotiff; profile=cloud-optimized"
    size_bytes: int = 0
    sha256: Optional[str] = None
    crs_code: str = "EPSG:4326"
    width: int = 1024
    height: int = 1024
    band_count: int = 4
    bands: List[AssetBand] = Field(default_factory=list)
    resolution_x: float = 10.0
    resolution_y: float = 10.0
    nodata_value: Optional[float] = 0.0
    validation_report: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Asset(BaseModel):
    id: str = Field(default_factory=lambda: f"ast_{uuid.uuid4().hex[:8]}")
    mission_id: str
    asset_type: AssetType = AssetType.CATALOG_ITEM
    title: str
    source_provider: str = "ESA/Copernicus"  # e.g. "sentinel-2-l2a", "sentinel-1-grd"
    external_id: Optional[str] = None
    collection_id: str = "sentinel-2-l2a"
    footprint: Optional[Dict[str, Any]] = None  # GeoJSON
    acquired_at: Optional[str] = None
    status: AssetStatus = AssetStatus.READY
    versions: List[AssetVersion] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Mission(BaseModel):
    id: str = Field(default_factory=lambda: f"msn_{uuid.uuid4().hex[:8]}")
    name: str
    slug: str
    description: str = ""
    status: MissionStatus = MissionStatus.ACTIVE
    default_srid: int = 4326
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_by: str = "analyst_admin"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# --- Pipeline & Planning Schemas ---

class PipelineDefinition(BaseModel):
    key: str
    version: str = "1.0.0"
    label: str
    description: str = ""
    supportedCollections: List[str] = Field(default_factory=list)
    requiredBands: List[str] = Field(default_factory=list)
    inputRoles: List[str] = Field(default_factory=list)
    outputTypes: List[str] = Field(default_factory=list)
    parameterBounds: Dict[str, Any] = Field(default_factory=dict)
    scientificNotes: List[str] = Field(default_factory=list)


class AnalysisPlanInputBinding(BaseModel):
    role: str  # e.g. "before_scene", "after_scene", "mask", "source_scene"
    assetVersionId: str
    assetId: Optional[str] = None
    label: Optional[str] = None


class AnalysisPlanPipelineRef(BaseModel):
    key: str
    version: str = "1.0.0"
    label: Optional[str] = None


class AnalysisPlan(BaseModel):
    schemaVersion: str = "1.0"
    planId: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    missionId: str
    questionId: Optional[str] = None
    questionText: Optional[str] = None
    aoiId: Optional[str] = None
    pipeline: AnalysisPlanPipelineRef
    inputs: List[AnalysisPlanInputBinding] = Field(default_factory=list)
    timeRange: Dict[str, Any] = Field(default_factory=dict)  # {"before": {"start", "end"}, "after": {...}}
    parameters: Dict[str, Any] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    blockingErrors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    expectedOutputs: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# --- Execution, Outputs & Provenance ---

class RunOutput(BaseModel):
    id: str = Field(default_factory=lambda: f"out_{uuid.uuid4().hex[:8]}")
    run_id: str
    output_type: str  # "raster", "vector", "table", "chart", "report"
    name: str
    object_uri: str
    tile_uri: Optional[str] = None
    mime_type: str
    geometry: Optional[Dict[str, Any]] = None
    statistics: Dict[str, Any] = Field(default_factory=dict)
    quality_flags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    run_id: str
    stage: str
    message: str
    progress_percent: int
    payload: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ProvenanceRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"prv_{uuid.uuid4().hex[:8]}")
    run_id: str
    manifest_uri: str
    pipeline: Dict[str, Any]
    source_assets: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    software_digest: str = "trinetra-eo-engine:v2.4.0@sha256:7f49cb"
    environment: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AnalysisRun(BaseModel):
    id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:8]}")
    mission_id: str
    question_id: Optional[str] = None
    analysis_plan_id: str
    run_number: int = 1
    status: RunStatus = RunStatus.QUEUED
    pipeline_key: str
    pipeline_version: str = "1.0.0"
    plan_snapshot: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    progress_percent: int = 0
    current_stage: str = "queued"
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    outputs: List[RunOutput] = Field(default_factory=list)
    events: List[RunEvent] = Field(default_factory=list)
    provenance: Optional[ProvenanceRecord] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class NotebookEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"nb_{uuid.uuid4().hex[:8]}")
    mission_id: str
    question_id: Optional[str] = None
    run_id: Optional[str] = None
    title: str
    body: str
    entry_type: str = "finding"  # "question", "result", "note", "finding", "decision"
    findings_data: Dict[str, Any] = Field(default_factory=dict)
    created_by: str = "analyst"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# --- API Request & Response Payloads ---

class CreateMissionRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: Optional[str] = ""
    settings: Optional[Dict[str, Any]] = None


class CreateAOIRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    geometry: Dict[str, Any]
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DraftPlanRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    aoi_id: Optional[str] = None
    time_range: Optional[Dict[str, Any]] = None
    pipeline_key: Optional[str] = None
    context_options: Optional[Dict[str, Any]] = None


class ValidatePlanRequest(BaseModel):
    plan: AnalysisPlan


class ApprovePlanRequest(BaseModel):
    approved_by: Optional[str] = "analyst"


class SubmitRunRequest(BaseModel):
    plan_id: str


class AddNotebookEntryRequest(BaseModel):
    title: str
    body: str
    entry_type: str = "note"
    run_id: Optional[str] = None
    findings_data: Optional[Dict[str, Any]] = None
