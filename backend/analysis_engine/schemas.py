"""
TRINETRA Analysis Engine — API Contracts & Pydantic Schemas
Defines request and response interfaces for all EO analytical operations.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AnalysisMode(str, Enum):
    BI_TEMPORAL = "BI_TEMPORAL"
    SAR_OPTICAL = "SAR_OPTICAL"
    SINGLE_IMAGE = "SINGLE_IMAGE"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


class LimitationCode(str, Enum):
    CLOUD_CONTAMINATION = "CLOUD_CONTAMINATION"
    LOW_OVERLAP = "LOW_OVERLAP"
    LOW_RESOLUTION = "LOW_RESOLUTION"
    REGISTRATION_WARNING = "REGISTRATION_WARNING"
    MODEL_UNCERTAINTY = "MODEL_UNCERTAINTY"
    MISSING_BAND = "MISSING_BAND"
    PARTIAL_COVERAGE = "PARTIAL_COVERAGE"


class AnalysisLimitation(BaseModel):
    code: LimitationCode
    description: str
    severity: str = Field(default="warning", description="info | warning | critical")
    affected_components: List[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    query: str = Field(..., description="User natural language analytical query")
    aoi: Optional[Dict[str, Any]] = Field(default=None, description="GeoJSON geometry of the AOI")
    mode: Optional[AnalysisMode] = Field(default=None, description="Analysis mode (auto-planned if omitted)")
    observation_a_id: Optional[str] = Field(default=None, description="Primary observation ID (T1 or Optical)")
    observation_b_id: Optional[str] = Field(default=None, description="Secondary observation ID (T2 or SAR)")
    options: Dict[str, Any] = Field(default_factory=dict, description="Pipeline overrides (e.g. threshold, language)")


class AnalysisValidationRequest(BaseModel):
    aoi: Optional[Dict[str, Any]] = None
    mode: AnalysisMode
    observation_a_id: Optional[str] = None
    observation_b_id: Optional[str] = None


class AnalysisValidationResponse(BaseModel):
    valid: bool
    mode: AnalysisMode
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    resolved_observations: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_pixel_count: int = 0
    estimated_runtime_seconds: float = 5.0


class AnalysisFinding(BaseModel):
    id: str = Field(..., description="Finding ID e.g. F01")
    title: str
    label: str
    statement: str
    confidence: ConfidenceLevel
    evidence_ids: List[str] = Field(default_factory=list, description="Mandatory list of supporting evidence IDs")
    area_m2: Optional[float] = None
    area_ha: Optional[float] = None
    geometry: Optional[Dict[str, Any]] = None
    supporting_metrics: Dict[str, Any] = Field(default_factory=dict)
    limitation_ids: List[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    run_id: str
    request_id: str
    status: str
    mode: AnalysisMode
    query: str
    summary: str
    observation_ids: List[str]
    evidence: Dict[str, Any] = Field(default_factory=dict)
    findings: List[AnalysisFinding] = Field(default_factory=list)
    confidence: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[AnalysisLimitation] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    visualizations: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    completed_at: Optional[str] = None
    execution_time_seconds: Optional[float] = None
