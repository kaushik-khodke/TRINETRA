"""
TRINETRA / Shanetra Geospatial Exploration Engine
AOI (Area of Interest) Subsystem
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
"""

from exploration.aoi.validator import AOIValidator, AOIPolicy, AOIValidationResult
from exploration.aoi.geometry import (
    get_bbox,
    calculate_centroid,
    calculate_area_km2,
    normalize_longitudes,
    geometry_hash,
    geometry_to_geojson,
)
from exploration.aoi.simplifier import AOISimplifier

__all__ = [
    "AOIValidator",
    "AOIPolicy",
    "AOIValidationResult",
    "get_bbox",
    "calculate_centroid",
    "calculate_area_km2",
    "normalize_longitudes",
    "geometry_hash",
    "geometry_to_geojson",
    "AOISimplifier",
]
