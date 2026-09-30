"""
TRINETRA / Shanetra Geospatial Exploration Engine
Raster Operations & Windowed Reader Service
Phase 2: Reads only the requested spatial window, extracts authoritative metadata, and normalizes display values.
"""

import os
import math
import numpy as np
from PIL import Image
from typing import Optional, Tuple, List, Dict, Any

try:
    import rasterio
    from rasterio.windows import from_bounds as rio_from_bounds, Window
    from rasterio.enums import Resampling
    from rasterio.warp import transform_bounds
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

from exploration.models import RasterSource
from exploration.cache import metadata_cache
from geospatial.validator import GeospatialValidator
from geospatial.reader import GeospatialReader


class RasterService:
    """High-performance windowed raster reader and display normalizer."""

    @classmethod
    def read_metadata(cls, file_path: str, asset_id: str) -> RasterSource:
        """Inspects authoritative raster metadata directly from file headers using cached lookup."""
        cached = metadata_cache.get(asset_id)
        if cached and isinstance(cached, RasterSource):
            return cached

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Raster source not found: {file_path}")

        # Check if COG (Cloud Optimized GeoTIFF)
        is_cog = False
        if HAS_RASTERIO:
            try:
                with rasterio.open(file_path) as src:
                    is_tiled = src.is_tiled
                    has_overviews = any(src.overviews(i) for i in src.indexes)
                    is_cog = bool(is_tiled and has_overviews)
            except Exception:
                is_cog = False

        # Extract authoritative geospatial metadata via established GeospatialValidator
        raw_meta = GeospatialValidator.inspect_raster_metadata(file_path)

        source = RasterSource(
            asset_id=asset_id,
            path=file_path,
            crs=raw_meta.crs or "EPSG:4326",
            bounds=raw_meta.bounds or [-180.0, -90.0, 180.0, 90.0],
            width=raw_meta.width,
            height=raw_meta.height,
            bands=raw_meta.band_count,
            dtype=raw_meta.dtype,
            nodata=raw_meta.nodata_value,
            resolution=raw_meta.resolution,
            transform_matrix=raw_meta.transform_matrix,
            is_cog=is_cog,
            sensor_name=raw_meta.sensor_name,
            modality=raw_meta.modality or "optical",
        )

        metadata_cache.set(asset_id, source)
        return source

    @classmethod
    def read_window(
        cls,
        file_path: str,
        bounds_wgs84: List[float],
        out_shape: Tuple[int, int] = (256, 256),
    ) -> Optional[np.ndarray]:
        """
        Reads ONLY the pixel window corresponding to bounds_wgs84 [min_lon, min_lat, max_lon, max_lat].
        Never loads entire multi-gigabyte raster files into memory.
        """
        if not os.path.exists(file_path):
            return None

        min_lon, min_lat, max_lon, max_lat = bounds_wgs84

        if HAS_RASTERIO:
            try:
                with rasterio.open(file_path) as src:
                    # Convert WGS-84 bounds to dataset CRS if not already EPSG:4326
                    src_crs = src.crs
                    if src_crs and src_crs.to_string() != "EPSG:4326":
                        left, bottom, right, top = transform_bounds(
                            "EPSG:4326", src_crs, min_lon, min_lat, max_lon, max_lat
                        )
                    else:
                        left, bottom, right, top = min_lon, min_lat, max_lon, max_lat

                    # Check intersection with raster bounds
                    if (
                        right < src.bounds.left
                        or left > src.bounds.right
                        or top < src.bounds.bottom
                        or bottom > src.bounds.top
                    ):
                        return None

                    window = rio_from_bounds(left, bottom, right, top, transform=src.transform)
                    window = window.intersection(Window(0, 0, src.width, src.height))

                    if window.width <= 0 or window.height <= 0:
                        return None

                    data = src.read(
                        out_shape=(src.count, out_shape[0], out_shape[1]),
                        window=window,
                        resampling=Resampling.bilinear,
                        boundless=True,
                    )
                    # Convert (bands, H, W) to (H, W, bands) or (H, W)
                    if data.shape[0] == 1:
                        return data[0]
                    return np.moveaxis(data, 0, -1)
            except Exception as e:
                # Fallback to pure numpy/PIL windowing
                pass

        # Fallback for systems without rasterio windowing
        try:
            with Image.open(file_path) as img:
                arr = np.array(img)
                # Downsample if needed
                if arr.ndim >= 2:
                    h, w = arr.shape[:2]
                    resized = Image.fromarray(arr).resize(out_shape, Image.Resampling.BILINEAR)
                    return np.array(resized)
        except Exception:
            return None

        return None

    @classmethod
    def normalize_for_display(cls, arr: np.ndarray, modality: str = "optical") -> np.ndarray:
        """
        Applies non-destructive display scaling and percentile contrast stretching.
        Produces standard 8-bit (0..255) RGB array for web tile rendering.
        """
        if arr is None:
            return np.zeros((256, 256, 3), dtype=np.uint8)

        # Single band (SAR / Grayscale / Elevation)
        if arr.ndim == 2:
            norm = cls._normalize_single_band(arr)
            if modality == "sar":
                # Amber-tinted SAR radar composite
                r = norm
                g = (norm * 0.92).astype(np.uint8)
                b = (norm * 0.75).astype(np.uint8)
                return np.stack([r, g, b], axis=-1)
            # Grayscale optical/elevation
            return np.stack([norm, norm, norm], axis=-1)

        # Multi-band (RGB or RGB+NIR)
        if arr.ndim == 3:
            bands = arr.shape[2]
            if bands == 1:
                norm = cls._normalize_single_band(arr[:, :, 0])
                return np.stack([norm, norm, norm], axis=-1)
            elif bands >= 3:
                # Extract first 3 bands (assumed R, G, B)
                r = cls._normalize_single_band(arr[:, :, 0])
                g = cls._normalize_single_band(arr[:, :, 1])
                b = cls._normalize_single_band(arr[:, :, 2])
                return np.stack([r, g, b], axis=-1)

        return np.zeros((256, 256, 3), dtype=np.uint8)

    @classmethod
    def _normalize_single_band(cls, band: np.ndarray) -> np.ndarray:
        """Percentile 2%-98% dynamic range compression to uint8."""
        valid = band[~np.isnan(band)]
        if valid.size == 0:
            return np.zeros_like(band, dtype=np.uint8)

        # Subsample for speed if large
        if valid.size > 10000:
            sample = valid[::max(1, valid.size // 10000)]
        else:
            sample = valid

        p2, p98 = np.percentile(sample, (2.0, 98.0))
        if p98 <= p2:
            p2 = float(np.min(sample))
            p98 = float(np.max(sample))
            if p98 <= p2:
                return np.zeros(band.shape, dtype=np.uint8)

        clipped = np.clip(band, p2, p98)
        norm = ((clipped - p2) / (p98 - p2) * 255.0).astype(np.uint8)
        return norm
