"""
TRINETRA Analysis Engine — Coordinate Reprojection Engine
Transforms coordinates and rasters across geospatial reference frames (e.g. UTM to WGS-84).
"""

from typing import List, Tuple, Optional
import numpy as np
from analysis_engine.errors import PreprocessingFailureError

try:
    import pyproj
    from pyproj import Transformer
    HAS_PYPROJ = True
except ImportError:
    HAS_PYPROJ = False


class CoordinateReprojector:
    """Manages exact spatial transformations across projection systems."""

    @staticmethod
    def reproject_point(
        x: float,
        y: float,
        src_crs: str = "EPSG:4326",
        dst_crs: str = "EPSG:3857",
    ) -> Tuple[float, float]:
        """Reprojects a single (lon, lat) or (x, y) point."""
        if src_crs == dst_crs:
            return x, y

        if not HAS_PYPROJ:
            return x, y

        try:
            transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
            new_x, new_y = transformer.transform(x, y)
            return float(new_x), float(new_y)
        except Exception as e:
            raise PreprocessingFailureError(f"Point reprojection failed ({src_crs} -> {dst_crs}): {e}")

    @staticmethod
    def reproject_bounds(
        bounds: List[float],
        src_crs: str,
        dst_crs: str,
    ) -> List[float]:
        """
        Reprojects [min_x, min_y, max_x, max_y] bounding box.
        """
        if src_crs == dst_crs:
            return bounds

        min_x, min_y, max_x, max_y = bounds
        p1 = CoordinateReprojector.reproject_point(min_x, min_y, src_crs, dst_crs)
        p2 = CoordinateReprojector.reproject_point(max_x, max_y, src_crs, dst_crs)
        return [min(p1[0], p2[0]), min(p1[1], p2[1]), max(p1[0], p2[0]), max(p1[1], p2[1])]
