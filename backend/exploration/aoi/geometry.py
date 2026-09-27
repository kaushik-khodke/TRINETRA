"""
TRINETRA / Shanetra Geospatial Exploration Engine
AOI Geometry Utilities & Deterministic Hashing
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
Geometric analysis, centroid extraction, area estimation, and deterministic hashing for caching.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
from shapely.geometry import shape, mapping
from exploration.aoi.validator import AOIValidator


def get_bbox(geometry: Dict[str, Any]) -> List[float]:
    """Computes [min_lon, min_lat, max_lon, max_lat] for a GeoJSON geometry."""
    s = shape(geometry)
    minx, miny, maxx, maxy = s.bounds
    return [round(minx, 6), round(miny, 6), round(maxx, 6), round(maxy, 6)]


def calculate_centroid(geometry: Dict[str, Any]) -> Dict[str, float]:
    """Computes latitude and longitude of the geometric centroid."""
    s = shape(geometry)
    c = s.centroid
    return {"latitude": round(c.y, 6), "longitude": round(c.x, 6)}


def calculate_area_km2(geometry: Dict[str, Any]) -> float:
    """Estimates geodesic area in square kilometers."""
    s = shape(geometry)
    return round(AOIValidator._calculate_spherical_area_km2(s), 2)


def normalize_longitudes(geometry: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes any coordinates outside [-180, 180] back into canonical range."""
    coords = geometry.get("coordinates")
    geom_type = geometry.get("type")

    def _norm_lon(lon: float) -> float:
        return ((lon + 180.0) % 360.0) - 180.0

    def _normalize_ring(ring: List[Any]) -> List[Any]:
        return [[_norm_lon(pt[0]), pt[1]] for pt in ring]

    if geom_type == "Polygon" and coords:
        new_coords = [_normalize_ring(ring) for ring in coords]
        return {"type": "Polygon", "coordinates": new_coords}
    elif geom_type == "MultiPolygon" and coords:
        new_coords = [[_normalize_ring(ring) for ring in poly] for poly in coords]
        return {"type": "MultiPolygon", "coordinates": new_coords}

    return geometry


def geometry_hash(geometry: Dict[str, Any]) -> str:
    """
    Produces an invariant SHA-256 hash of coordinate vertices rounded to 6 decimals.
    Ensures identical geometries produce identical cache keys regardless of whitespace.
    """
    coords = geometry.get("coordinates")
    geom_type = geometry.get("type", "Polygon")

    def _round_coords(val: Any) -> Any:
        if isinstance(val, (int, float)):
            return round(val, 6)
        if isinstance(val, (list, tuple)):
            return [_round_coords(v) for v in val]
        return val

    rounded = {
        "type": geom_type,
        "coordinates": _round_coords(coords),
    }
    serialized = json.dumps(rounded, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def geometry_to_geojson(geometry: Dict[str, Any], properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Wraps raw geometry in a standard GeoJSON Feature structure."""
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties or {},
    }
