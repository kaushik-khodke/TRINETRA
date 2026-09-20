"""
TRINETRA / Shanetra Geospatial Exploration Engine
AOI Validator & Spatial Policy Engine
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
Strict server-authoritative validation preventing malformed, infinite, or oversized geometries.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from shapely.geometry import shape, Polygon, MultiPolygon
from config.settings import settings


@dataclass
class AOIPolicy:
    """Configurable boundaries protecting STAC catalog and backend from query abuse."""
    max_vertices: int = settings.exploration_max_aoi_vertices
    max_area_km2: float = settings.exploration_max_aoi_area_km2
    max_bbox_width_deg: float = 15.0
    max_bbox_height_deg: float = 15.0
    max_polygon_rings: int = 10


@dataclass
class AOIValidationResult:
    """Structured response for AOI verification."""
    valid: bool
    area_km2: Optional[float] = None
    bbox: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    vertex_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    normalized_geometry: Optional[Dict[str, Any]] = None


class AOIValidator:
    """Server-authoritative validator for AOI geometries."""

    SUPPORTED_TYPES = {"Polygon", "MultiPolygon"}

    @classmethod
    def validate(
        cls,
        geom_input: Any,
        policy: Optional[AOIPolicy] = None,
    ) -> AOIValidationResult:
        """
        Validates GeoJSON geometry or Feature dictionary against strict spatial policies.
        """
        pol = policy or AOIPolicy()
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Existence and basic dictionary check
        if not geom_input or not isinstance(geom_input, dict):
            return AOIValidationResult(valid=False, errors=["AOI geometry must be a non-empty dictionary."])

        # If passed as GeoJSON Feature, extract geometry
        raw_geom = geom_input.get("geometry", geom_input) if geom_input.get("type") == "Feature" else geom_input
        geom_type = raw_geom.get("type")
        coords = raw_geom.get("coordinates")

        # 2. Geometry type check
        if not geom_type or geom_type not in cls.SUPPORTED_TYPES:
            return AOIValidationResult(
                valid=False,
                errors=[f"Unsupported geometry type '{geom_type}'. Only 'Polygon' and 'MultiPolygon' are supported for AOI selection."],
            )

        if not coords or not isinstance(coords, list):
            return AOIValidationResult(valid=False, errors=["Geometry coordinates must be a non-empty list."])

        # 3. Coordinate finiteness, numeric checks, and vertex counting
        vertex_count = 0
        ring_count = 0

        try:
            if geom_type == "Polygon":
                ring_count = len(coords)
                if ring_count > pol.max_polygon_rings:
                    errors.append(f"Polygon ring count ({ring_count}) exceeds limit of {pol.max_polygon_rings}.")
                for ring in coords:
                    err = cls._validate_ring(ring)
                    if err:
                        errors.extend(err)
                    vertex_count += len(ring)

            elif geom_type == "MultiPolygon":
                for poly in coords:
                    ring_count += len(poly)
                    for ring in poly:
                        err = cls._validate_ring(ring)
                        if err:
                            errors.extend(err)
                        vertex_count += len(ring)

        except Exception as e:
            return AOIValidationResult(valid=False, errors=[f"Malformed coordinate hierarchy: {e}"])

        if errors:
            return AOIValidationResult(valid=False, vertex_count=vertex_count, errors=errors)

        # 4. Vertex limit check
        if vertex_count > pol.max_vertices:
            return AOIValidationResult(
                valid=False,
                vertex_count=vertex_count,
                errors=[f"AOI vertex count ({vertex_count}) exceeds allowed maximum of {pol.max_vertices} vertices."],
            )

        # 5. Shapely topological validation and area computation
        try:
            s_geom = shape(raw_geom)
            if not s_geom.is_valid:
                # Attempt light fix if self-intersection
                from shapely.validation import explain_validity
                val_err = explain_validity(s_geom)
                return AOIValidationResult(
                    valid=False,
                    vertex_count=vertex_count,
                    errors=[f"Topologically invalid polygon: {val_err}"],
                )

            if s_geom.is_empty:
                return AOIValidationResult(valid=False, errors=["AOI geometry is topologically empty."])

            # Bounding box calculation
            minx, miny, maxx, maxy = s_geom.bounds
            bbox = [round(minx, 6), round(miny, 6), round(maxx, 6), round(maxy, 6)]
            width_deg = maxx - minx
            height_deg = maxy - miny

            if width_deg > pol.max_bbox_width_deg or height_deg > pol.max_bbox_height_deg:
                return AOIValidationResult(
                    valid=False,
                    vertex_count=vertex_count,
                    bbox=bbox,
                    errors=[f"AOI bounding box ({width_deg:.2f}° x {height_deg:.2f}°) exceeds exploration limits ({pol.max_bbox_width_deg}° x {pol.max_bbox_height_deg}°)."],
                )

            # Area calculation in km2
            area_km2 = cls._calculate_spherical_area_km2(s_geom)

            if area_km2 > pol.max_area_km2:
                return AOIValidationResult(
                    valid=False,
                    vertex_count=vertex_count,
                    bbox=bbox,
                    area_km2=round(area_km2, 2),
                    errors=[f"AOI area ({area_km2:,.1f} km²) exceeds maximum allowed exploration ceiling of {pol.max_area_km2:,.1f} km²."],
                )

            if area_km2 < 0.001:
                warnings.append("Extremely small AOI (< 1,000 m²).")

            return AOIValidationResult(
                valid=True,
                area_km2=round(area_km2, 2),
                bbox=bbox,
                vertex_count=vertex_count,
                errors=[],
                warnings=warnings,
                normalized_geometry=raw_geom,
            )

        except Exception as e:
            return AOIValidationResult(valid=False, errors=[f"Geometry validation failure: {e}"])

    @classmethod
    def _validate_ring(cls, ring: List[Any]) -> List[str]:
        errors = []
        if not isinstance(ring, list) or len(ring) < 4:
            return ["Polygon ring must contain at least 4 coordinates (3 vertices + closed endpoint)."]

        # Check all coords are numeric and finite
        for pt in ring:
            if not isinstance(pt, (list, tuple)) or len(pt) < 2:
                return ["Coordinate point must be a list or tuple of [lon, lat]."]
            lon, lat = pt[0], pt[1]

            if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
                return ["Coordinate values must be numeric."]

            if math.isnan(lon) or math.isinf(lon) or math.isnan(lat) or math.isinf(lat):
                return ["Coordinates must be finite (NaN and Infinity are strictly rejected)."]

            if lon < -180.0 or lon > 180.0:
                return [f"Longitude {lon} out of valid bounds [-180.0, 180.0]."]

            if lat < -90.0 or lat > 90.0:
                return [f"Latitude {lat} out of valid bounds [-90.0, 90.0]."]

        # Closure check
        first_pt = ring[0]
        last_pt = ring[-1]
        if abs(first_pt[0] - last_pt[0]) > 1e-7 or abs(first_pt[1] - last_pt[1]) > 1e-7:
            errors.append("Polygon linear ring is not closed: first coordinate does not equal last coordinate.")

        return errors

    @classmethod
    def _calculate_spherical_area_km2(cls, geom: Any) -> float:
        """
        Estimates geodesic surface area in square kilometers using WGS84 authalic sphere approximation.
        """
        try:
            import pyproj
            from shapely.ops import transform
            # Project from EPSG:4326 to equal-area projection centered on geometry centroid
            lon_c, lat_c = geom.centroid.x, geom.centroid.y
            proj_str = f"+proj=laea +lat_0={lat_c} +lon_0={lon_c} +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
            project = pyproj.Transformer.from_crs("EPSG:4326", proj_str, always_xy=True).transform
            projected = transform(project, geom)
            area_m2 = projected.area
            return float(area_m2 / 1_000_000.0)
        except Exception:
            # Fallback planar degree area conversion approximation near centroid
            bounds = geom.bounds
            mid_lat = (bounds[1] + bounds[3]) / 2.0
            km_per_deg_lat = 111.32
            km_per_deg_lon = 111.32 * math.cos(math.radians(mid_lat))
            deg2_to_km2 = km_per_deg_lat * km_per_deg_lon
            return float(geom.area * deg2_to_km2)
