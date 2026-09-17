"""
SatQuery AI / TRINETRA — Geospatial Raster Reader
Reads GeoTIFF, TIFF, HSI cubes, and standard benchmark imagery (PNG/JPEG),
extracts geospatial metadata, bounds, CRS, and creates visual web previews.
"""

import os
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple, Optional

from schemas.contracts import RasterMetadata
from geospatial.validator import GeospatialValidator


class GeospatialReader:
    """Ingests geospatial rasters with metadata extraction and web preview rendering."""

    @staticmethod
    def read_metadata(file_path: str, detected_modality: Optional[str] = None) -> RasterMetadata:
        """Convenience method to inspect raster metadata directly without array retention."""
        return GeospatialValidator.inspect_raster_metadata(file_path, detected_modality)

    @staticmethod
    def read_image(file_path: str, detected_modality: Optional[str] = None) -> Tuple[np.ndarray, RasterMetadata]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        meta = GeospatialValidator.inspect_raster_metadata(file_path, detected_modality)

        # 1. Hyperspectral MATLAB (.mat) or ENVI (.hdr) reading
        if ext in [".mat", ".hdr", ".dat"]:
            from geospatial.hsi_reader import HsiReader
            hsi_data = HsiReader.read(file_path)
            return hsi_data.cube, meta

        # 2. GeoTIFF / TIFF reading
        elif ext in [".tif", ".tiff"]:
            with Image.open(file_path) as img:
                arr = np.array(img)
                return arr, meta

        # 3. Benchmark PNG / JPEG reading
        elif ext in [".png", ".jpg", ".jpeg"]:
            img = Image.open(file_path).convert("RGB")
            arr = np.array(img)
            return arr, meta

        else:
            raise ValueError(f"Unsupported file format '{ext}'. Must be GeoTIFF/TIFF, HSI (.mat/.hdr), or benchmark PNG/JPEG.")

    @staticmethod
    def to_rgb_preview(arr: np.ndarray, modality: str = "optical") -> Image.Image:
        """Converts arbitrary bit-depth / multispectral / SAR array into 8-bit RGB preview with downsampling for web."""
        # For huge satellite rasters (e.g. Landsat 9 / Sentinel with 60+ megapixels),
        # downsample for the web preview so that memory usage is ~2MB and rendering takes 0.05s
        h, w = arr.shape[:2]
        max_dim = max(h, w)
        if max_dim > 1024:
            step = int(np.ceil(max_dim / 1024))
            arr = arr[::step, ::step]

        if arr.ndim == 2:
            norm = GeospatialReader._normalize_band(arr)
            if modality == "sar":
                colored = np.stack([norm, norm, (norm * 0.9).astype(np.uint8)], axis=-1)
                return Image.fromarray(colored)
            return Image.fromarray(norm).convert("RGB")

        if arr.ndim == 3:
            bands = arr.shape[2]
            if bands >= 40 or modality == "hyperspectral":
                from geospatial.hsi_reader import HsiCubeData
                hsi = HsiCubeData(arr)
                return Image.fromarray(hsi.to_rgb_composite())
            elif bands == 1:
                norm = GeospatialReader._normalize_band(arr[:, :, 0])
                return Image.fromarray(norm).convert("RGB")
            elif bands >= 3:
                r = GeospatialReader._normalize_band(arr[:, :, 0])
                g = GeospatialReader._normalize_band(arr[:, :, 1])
                b = GeospatialReader._normalize_band(arr[:, :, 2])
                rgb = np.stack([r, g, b], axis=-1)
                return Image.fromarray(rgb)

        return Image.fromarray((arr % 256).astype(np.uint8)).convert("RGB")

    @staticmethod
    def _normalize_band(band: np.ndarray) -> np.ndarray:
        valid = band[~np.isnan(band)]
        if valid.size == 0:
            return np.zeros_like(band, dtype=np.uint8)

        # Subsample for percentile calculation if array is large
        if valid.size > 20000:
            sample = valid[::max(1, valid.size // 20000)]
        else:
            sample = valid

        p2, p98 = np.percentile(sample, (2, 98))
        if p98 > p2:
            clipped = np.clip(band, p2, p98)
            norm = ((clipped - p2) / (p98 - p2) * 255.0).astype(np.uint8)
            return norm
        return ((band / (np.max(valid) + 1e-6)) * 255.0).astype(np.uint8)
