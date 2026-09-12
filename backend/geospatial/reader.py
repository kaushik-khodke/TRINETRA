"""
SatQuery AI — Geospatial Raster Reader
Reads GeoTIFF, TIFF, and standard benchmark imagery (PNG/JPEG),
extracts geospatial metadata, bounds, CRS, and creates visual web previews.
"""

import os
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple, Optional

# Optional tifffile / rasterio support
try:
    import tifffile
    HAS_TIFFFILE = True
except ImportError:
    HAS_TIFFFILE = False

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

class RasterMetadata:
    def __init__(self, width: int, height: int, bands: int, dtype: str, 
                 crs: Optional[str] = None, bounds: Optional[Tuple[float, float, float, float]] = None,
                 transform: Optional[Any] = None, is_geotiff: bool = False, modality: str = "optical",
                 filename: Optional[str] = None):
        self.filename = filename or ""
        self.width = width
        self.height = height
        self.bands = bands
        self.dtype = dtype
        self.crs = crs or "EPSG:4326 (WGS 84)"
        self.bounds = bounds or (77.1025, 28.7041, 77.2025, 28.8041)  # Default geospatial extent
        self.transform = transform
        self.is_geotiff = is_geotiff
        self.modality = modality

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
            "bands": self.bands,
            "dtype": self.dtype,
            "crs": self.crs,
            "bounds": list(self.bounds) if self.bounds else None,
            "is_geotiff": self.is_geotiff,
            "modality": self.modality
        }

class GeospatialReader:
    """Ingests geospatial rasters with metadata extraction and web preview rendering."""

    @staticmethod
    def read_image(file_path: str, detected_modality: Optional[str] = None) -> Tuple[np.ndarray, RasterMetadata]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        
        # 1. GeoTIFF / TIFF reading
        if ext in [".tif", ".tiff"]:
            return GeospatialReader._read_tiff(file_path, detected_modality)
        # 2. Benchmark PNG / JPEG reading
        elif ext in [".png", ".jpg", ".jpeg"]:
            return GeospatialReader._read_standard(file_path, detected_modality)
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Must be GeoTIFF/TIFF or benchmark PNG/JPEG.")

    @staticmethod
    def _read_tiff(file_path: str, detected_modality: Optional[str] = None) -> Tuple[np.ndarray, RasterMetadata]:
        if HAS_RASTERIO:
            try:
                with rasterio.open(file_path) as src:
                    arr = src.read()  # Shape: (bands, height, width)
                    bands, height, width = arr.shape
                    crs = str(src.crs) if src.crs else "EPSG:4326"
                    bounds = (src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)
                    
                    # Convert to (height, width, bands)
                    if bands == 1:
                        data = arr[0]
                    else:
                        data = np.transpose(arr, (1, 2, 0))
                    
                    modality = detected_modality or ("sar" if bands == 1 else "optical")
                    meta = RasterMetadata(
                        width=width,
                        height=height,
                        bands=bands,
                        dtype=str(arr.dtype),
                        crs=crs,
                        bounds=bounds,
                        transform=src.transform,
                        is_geotiff=True,
                        modality=modality,
                        filename=os.path.basename(file_path)
                    )
                    return data, meta
            except Exception:
                pass  # Fallback to tifffile / PIL

        if HAS_TIFFFILE:
            arr = tifffile.imread(file_path)
            if arr.ndim == 2:
                height, width = arr.shape
                bands = 1
                data = arr
            elif arr.ndim == 3:
                # Could be (H, W, C) or (C, H, W)
                if arr.shape[0] < arr.shape[2]:
                    data = np.transpose(arr, (1, 2, 0))
                else:
                    data = arr
                height, width, bands = data.shape
            else:
                data = arr
                height, width, bands = data.shape[0], data.shape[1], 1

            modality = detected_modality or ("sar" if bands == 1 else "optical")
            meta = RasterMetadata(
                width=width,
                height=height,
                bands=bands,
                dtype=str(arr.dtype),
                is_geotiff=True,
                modality=modality,
                filename=os.path.basename(file_path)
            )
            return data, meta

        # Fallback to PIL
        img = Image.open(file_path)
        arr = np.array(img)
        if arr.ndim == 2:
            height, width = arr.shape
            bands = 1
        else:
            height, width, bands = arr.shape
        modality = detected_modality or ("sar" if bands == 1 else "optical")
        meta = RasterMetadata(
            width=width,
            height=height,
            bands=bands,
            dtype=str(arr.dtype),
            is_geotiff=False,
            modality=modality,
            filename=os.path.basename(file_path)
        )
        return arr, meta

    @staticmethod
    def _read_standard(file_path: str, detected_modality: Optional[str] = None) -> Tuple[np.ndarray, RasterMetadata]:
        img = Image.open(file_path).convert("RGB")
        arr = np.array(img)
        height, width, bands = arr.shape
        meta = RasterMetadata(
            width=width,
            height=height,
            bands=bands,
            dtype=str(arr.dtype),
            crs="EPSG:4326 (Public Benchmark Standard)",
            is_geotiff=False,
            modality=detected_modality or "optical",
            filename=os.path.basename(file_path)
        )
        return arr, meta

    @staticmethod
    def to_rgb_preview(arr: np.ndarray, modality: str = "optical") -> Image.Image:
        """Converts arbitrary bit-depth / multispectral / SAR array into 8-bit RGB preview."""
        if arr.ndim == 2:
            # Grayscale or SAR amplitude
            norm = GeospatialReader._normalize_band(arr)
            if modality == "sar":
                # Give SAR a subtle radar luminescence preview
                colored = np.stack([norm, norm, (norm * 0.9).astype(np.uint8)], axis=-1)
                return Image.fromarray(colored)
            return Image.fromarray(norm).convert("RGB")

        if arr.ndim == 3:
            bands = arr.shape[2]
            if bands == 1:
                norm = GeospatialReader._normalize_band(arr[:, :, 0])
                return Image.fromarray(norm).convert("RGB")
            elif bands >= 3:
                # Take first 3 bands as RGB (or bands 4,3,2 for multispectral)
                r = GeospatialReader._normalize_band(arr[:, :, 0])
                g = GeospatialReader._normalize_band(arr[:, :, 1])
                b = GeospatialReader._normalize_band(arr[:, :, 2])
                rgb = np.stack([r, g, b], axis=-1)
                return Image.fromarray(rgb)
        
        # Fallback
        return Image.fromarray((arr % 256).astype(np.uint8)).convert("RGB")

    @staticmethod
    def _normalize_band(band: np.ndarray) -> np.ndarray:
        valid = band[~np.isnan(band)]
        if valid.size == 0:
            return np.zeros_like(band, dtype=np.uint8)
        
        p2, p98 = np.percentile(valid, (2, 98))
        if p98 > p2:
            clipped = np.clip(band, p2, p98)
            norm = ((clipped - p2) / (p98 - p2) * 255.0).astype(np.uint8)
            return norm
        return ((band / (np.max(valid) + 1e-6)) * 255.0).astype(np.uint8)
