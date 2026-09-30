"""
TRINETRA / Shanetra Geospatial Exploration Engine
AOI Geometry Simplifier
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
Adaptive Douglas-Peucker simplification reducing STAC query payload while preserving spatial bounds.
"""

from typing import Any, Dict
from shapely.geometry import shape, mapping


class AOISimplifier:
    """Simplifies high-vertex polygons to compact spatial filters for STAC queries."""

    @classmethod
    def simplify(cls, geometry: Dict[str, Any], max_vertices: int = 50) -> Dict[str, Any]:
        """
        Simplifies geometry if vertex count exceeds max_vertices.
        Returns simplified GeoJSON dictionary.
        """
        s = shape(geometry)

        # Count vertices
        vertex_count = cls._count_vertices(s)
        if vertex_count <= max_vertices:
            return geometry

        # Compute adaptive tolerance from bounding box diagonal
        minx, miny, maxx, maxy = s.bounds
        diag = ((maxx - minx)**2 + (maxy - miny)**2) ** 0.5
        base_tolerance = max(0.0001, diag / 100.0)

        # Iteratively simplify until vertex count is bounded
        current_geom = s
        for factor in [1.0, 2.0, 4.0, 8.0]:
            tol = base_tolerance * factor
            simplified = current_geom.simplify(tol, preserve_topology=True)
            if simplified.is_valid and not simplified.is_empty and cls._count_vertices(simplified) <= max_vertices:
                return mapping(simplified)
            current_geom = simplified if simplified.is_valid and not simplified.is_empty else current_geom

        return mapping(current_geom)

    @classmethod
    def _count_vertices(cls, geom: Any) -> int:
        if geom.geom_type == "Polygon":
            return len(geom.exterior.coords) + sum(len(r.coords) for r in geom.interiors)
        elif geom.geom_type == "MultiPolygon":
            return sum(cls._count_vertices(p) for p in geom.geoms)
        return 0
