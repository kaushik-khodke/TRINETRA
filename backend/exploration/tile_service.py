"""
TRINETRA / Shanetra Geospatial Exploration Engine
Tile Service — Slippy Map Raster Tile Generation
Phase 2: Translates (z, x, y) requests to geographic bounding boxes, invokes windowed reads, and encodes PNG tiles.
"""

import io
import math
from typing import Optional, Tuple, List, Dict, Any
from PIL import Image
import numpy as np

try:
    import morecantile
    tms = morecantile.tms.get("WebMercatorQuad")
    HAS_MORECANTILE = True
except ImportError:
    HAS_MORECANTILE = False

from exploration.models import RasterSource
from exploration.raster_service import RasterService
from exploration.cache import tile_cache, negative_cache, build_tile_cache_key


class TileService:
    """Calculates tile bounds, coordinates windowed reads, and produces PNG tiles."""

    @staticmethod
    def validate_tile_coords(z: int, x: int, y: int) -> Tuple[bool, Optional[str]]:
        """Strict validation of slippy map tile coordinates."""
        if not (0 <= z <= 22):
            return False, f"Invalid zoom level {z}. Must be between 0 and 22."
        max_coord = (1 << z) - 1
        if not (0 <= x <= max_coord):
            return False, f"Invalid x coordinate {x} for zoom {z}. Max is {max_coord}."
        if not (0 <= y <= max_coord):
            return False, f"Invalid y coordinate {y} for zoom {z}. Max is {max_coord}."
        return True, None

    @staticmethod
    def tile_to_wgs84_bounds(z: int, x: int, y: int) -> List[float]:
        """
        Calculates WGS-84 [min_lon, min_lat, max_lon, max_lat] for slippy tile (z, x, y).
        Uses Morecantile if available, else standard spherical Mercator inverse projection.
        """
        if HAS_MORECANTILE:
            bounds = tms.bounds(x, y, z)
            return [bounds.left, bounds.bottom, bounds.right, bounds.top]

        n = 2.0 ** z
        min_lon = x / n * 360.0 - 180.0
        max_lon = (x + 1) / n * 360.0 - 180.0
        lat_rad_top = math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / n)))
        lat_rad_bottom = math.atan(math.sinh(math.pi * (1.0 - 2.0 * (y + 1) / n)))
        max_lat = math.degrees(lat_rad_top)
        min_lat = math.degrees(lat_rad_bottom)
        return [min_lon, min_lat, max_lon, max_lat]

    @classmethod
    def get_tile(
        cls,
        layer_id: str,
        source: RasterSource,
        z: int,
        x: int,
        y: int,
        render_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[bytes]:
        """
        Retrieves or renders a 256x256 PNG tile for the given raster source.
        Returns cached bytes if available; otherwise performs windowed extraction.
        """
        is_valid, err = cls.validate_tile_coords(z, x, y)
        if not is_valid:
            return None

        cache_key = build_tile_cache_key(layer_id, source.asset_id, z, x, y, render_params)

        # 1. Check positive cache
        cached_tile = tile_cache.get(cache_key)
        if cached_tile is not None:
            return cached_tile

        # 2. Check negative cache
        if negative_cache.get(cache_key) is not None:
            return None

        # 3. Calculate geographic bounds for this tile
        tile_bounds = cls.tile_to_wgs84_bounds(z, x, y)

        # 4. Check bounding box intersection with raster coverage
        s_min_lon, s_min_lat, s_max_lon, s_max_lat = source.bounds
        t_min_lon, t_min_lat, t_max_lon, t_max_lat = tile_bounds

        if (
            t_max_lon < s_min_lon
            or t_min_lon > s_max_lon
            or t_max_lat < s_min_lat
            or t_min_lat > s_max_lat
        ):
            # Tile is outside raster extent — store in negative cache
            negative_cache.set(cache_key, True, ttl_seconds=60.0)
            return None

        # 5. Read windowed array
        window_arr = RasterService.read_window(source.path, tile_bounds, out_shape=(256, 256))
        if window_arr is None:
            negative_cache.set(cache_key, True, ttl_seconds=60.0)
            return None

        # 6. Normalize display values
        rgb_arr = RasterService.normalize_for_display(window_arr, modality=source.modality)

        # 7. Encode to PNG
        img = Image.fromarray(rgb_arr, mode="RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        tile_bytes = buf.getvalue()

        # 8. Cache result
        tile_cache.set(cache_key, tile_bytes)
        return tile_bytes
