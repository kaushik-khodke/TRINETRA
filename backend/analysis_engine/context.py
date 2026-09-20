"""
TRINETRA Analysis Engine — Raw State Context
Stores structured, raw, reproducible geospatial state without embedding prompt strings.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import numpy as np


@dataclass
class ObservationContext:
    observation_id: str
    modality: str  # optical | multispectral | sar | hyperspectral
    datetime_str: str
    platform: str
    crs: str
    bounds: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    resolution_meters: float
    asset_paths: Dict[str, str] = field(default_factory=dict)
    available_bands: List[str] = field(default_factory=list)
    cloud_cover: Optional[float] = None
    sun_elevation: Optional[float] = None


@dataclass
class PreprocessingState:
    reprojected_crs: Optional[str] = None
    common_bounds: Optional[List[float]] = None
    common_shape: Optional[tuple] = None
    aligned_grid_transform: Optional[List[float]] = None
    nodata_mask: Optional[np.ndarray] = None
    cloud_mask: Optional[np.ndarray] = None
    applied_normalizations: Dict[str, str] = field(default_factory=dict)
    scaling_factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class AnalysisContext:
    run_id: str
    query: str
    aoi_geometry: Optional[Dict[str, Any]] = None
    aoi_bounds: Optional[List[float]] = None
    aoi_area_km2: Optional[float] = None
    mode: str = "BI_TEMPORAL"
    
    # Observations
    observations: Dict[str, ObservationContext] = field(default_factory=dict)
    
    # Raster preparation
    pixel_window: Optional[Dict[str, Any]] = None
    preprocessing: PreprocessingState = field(default_factory=PreprocessingState)
    
    # Raw in-memory arrays during pipeline stages (discarded before artifact storage)
    tensors: Dict[str, np.ndarray] = field(default_factory=dict)
    
    # Specialist Model Output References
    model_outputs: Dict[str, Any] = field(default_factory=dict)
    
    # Evidence & Findings references
    evidence_items: List[Dict[str, Any]] = field(default_factory=list)
    limitations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Telemetry
    stage_latencies: Dict[str, float] = field(default_factory=dict)
