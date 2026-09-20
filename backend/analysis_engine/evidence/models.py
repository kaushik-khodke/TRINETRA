"""
TRINETRA Analysis Engine — Evidence Models & Schemas
Standardizes all measurable analytical outputs into an auditable Evidence Pack.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GroundingEvidence(BaseModel):
    id: str = Field(..., description="Evidence ID e.g. E_G01")
    label: str
    bbox: List[float] = Field(..., description="[ymin, xmin, ymax, xmax] normalized or spatial coordinates")
    geometry: Optional[Dict[str, Any]] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_model: str = "RSGroundingSpecialist"


class ChangeRegionEvidence(BaseModel):
    id: str = Field(..., description="Evidence ID e.g. E_CHG01")
    label: str = Field(default="Detected Land Shift")
    area_m2: float = Field(..., ge=0.0)
    area_ha: float = Field(..., ge=0.0)
    pixel_count: int = Field(..., ge=1)
    centroid: List[float] = Field(..., description="[lon, lat]")
    bbox: List[float] = Field(..., description="[min_lon, min_lat, max_lon, max_lat]")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON Polygon geometry")
    confidence: float = Field(..., ge=0.0, le=1.0)
    change_score: float = Field(default=0.5, ge=0.0, le=1.0)
    spectral_delta: Optional[float] = None
    rank: int = 1


class SpectralEvidence(BaseModel):
    id: str = Field(..., description="Evidence ID e.g. E_SPEC01")
    index_name: str = Field(description="NDVI | NDWI | NDBI | RadarBackscatter")
    mean_value_a: float
    mean_value_b: Optional[float] = None
    delta: Optional[float] = None
    interpretation: str


class CrossModalSupport(BaseModel):
    sar_confidence: float = Field(..., ge=0.0, le=1.0)
    optical_confidence: float = Field(..., ge=0.0, le=1.0)
    agreement_score: float = Field(..., ge=0.0, le=1.0)


class CrossModalEvidence(BaseModel):
    id: str = Field(..., description="Evidence ID e.g. E_XM01")
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    support: CrossModalSupport
    metrics: Dict[str, Any] = Field(default_factory=dict)


class EvidencePack(BaseModel):
    pack_id: str
    run_id: str
    mode: str
    aoi_bounds: Optional[List[float]] = None
    observation_ids: List[str] = Field(default_factory=list)
    change_regions: List[ChangeRegionEvidence] = Field(default_factory=list)
    grounding_detections: List[GroundingEvidence] = Field(default_factory=list)
    spectral_metrics: List[SpectralEvidence] = Field(default_factory=list)
    cross_modal_items: List[CrossModalEvidence] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    visual_artifacts: Dict[str, str] = Field(default_factory=dict)
    validation_status: str = "VALIDATED"
