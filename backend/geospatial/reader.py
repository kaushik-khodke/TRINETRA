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
                 filename: Optional[str] = None, center_lat: Optional[float] = None,
                 center_lng: Optional[float] = None, location_name: Optional[str] = None):
        self.filename = filename or ""
        self.width = width
        self.height = height
        self.bands = bands
        self.dtype = dtype
        self.crs = crs
        self.bounds = bounds  # (min_lon, min_lat, max_lon, max_lat)
        self.transform = transform
        self.is_geotiff = is_geotiff
        self.modality = modality
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.location_name = location_name
        self.has_geographic_location = bool(center_lat is not None and center_lng is not None)

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
            "modality": self.modality,
            "has_geographic_location": self.has_geographic_location,
            "center_lat": self.center_lat,
            "center_lng": self.center_lng,
            "location_name": self.location_name
        }

class GeospatialReader:
    """Ingests geospatial rasters with metadata extraction and web preview rendering."""

    @staticmethod
    def read_metadata(file_path: str, detected_modality: Optional[str] = None) -> RasterMetadata:
        """Convenience method to inspect raster metadata without keeping array in memory."""
        _, meta = GeospatialReader.read_image(file_path, detected_modality)
        return meta

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
        # 3. Hyperspectral MATLAB (.mat) or ENVI (.hdr) reading
        elif ext in [".mat", ".hdr", ".dat"]:
            from geospatial.hsi_reader import HsiReader
            hsi_data = HsiReader.read(file_path)
            meta = RasterMetadata(
                width=hsi_data.width,
                height=hsi_data.height,
                bands=hsi_data.bands,
                dtype=str(hsi_data.cube.dtype),
                crs=hsi_data.crs or "Sensor Coordinate System",
                bounds=hsi_data.bounds,
                is_geotiff=bool(hsi_data.crs is not None),
                modality="hyperspectral",
                filename=os.path.basename(file_path),
                location_name=hsi_data.sensor_name
            )
            return hsi_data.cube, meta
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Must be GeoTIFF/TIFF, HSI (.mat/.hdr), or benchmark PNG/JPEG.")

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
                    
                    min_lon, min_lat, max_lon, max_lat = bounds
                    # If CRS is EPSG:4326 or lon/lat ranges match physical bounds
                    if -180.0 <= min_lon <= 180.0 and -90.0 <= min_lat <= 90.0:
                        center_lat = round((min_lat + max_lat) / 2.0, 6)
                        center_lng = round((min_lon + max_lon) / 2.0, 6)
                    else:
                        center_lat = None
                        center_lng = None

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
                        filename=os.path.basename(file_path),
                        center_lat=center_lat,
                        center_lng=center_lng
                    )
                    return data, meta
            except Exception:
                pass  # Fallback to PIL GeoTIFF reader

        # Read using PIL and extract GeoTIFF tags directly
        with Image.open(file_path) as img:
            arr = np.array(img)
            if arr.ndim == 2:
                height, width = arr.shape
                bands = 1
                data = arr
            else:
                height, width, bands = arr.shape
                data = arr

            modality = detected_modality or ("sar" if bands == 1 else "optical")
            
            # Inspect standard OGC GeoTIFF tags
            tag_v2 = getattr(img, "tag_v2", {})
            has_pixel_scale = 33550 in tag_v2
            has_tiepoint = 33922 in tag_v2

            is_geotiff = False
            bounds = None
            center_lat = None
            center_lng = None
            crs = None

            if has_pixel_scale and has_tiepoint:
                scale = tag_v2[33550]
                tiepoint = tag_v2[33922]
                try:
                    # ModelTiepoint: (I, J, K, X, Y, Z)
                    # ModelPixelScale: (ScaleX, ScaleY, ScaleZ)
                    min_x = float(tiepoint[3])
                    max_y = float(tiepoint[4])
                    max_x = min_x + width * float(scale[0])
                    min_y = max_y - height * float(scale[1])

                    # 1. Geographic WGS-84 degrees
                    if -180.0 <= min_x <= 180.0 and -90.0 <= min_y <= 90.0:
                        center_lat = round((min_y + max_y) / 2.0, 6)
                        center_lng = round((min_x + max_x) / 2.0, 6)
                        bounds = (round(min_x, 6), round(min_y, 6), round(max_x, 6), round(max_y, 6))
                        crs = "EPSG:4326 (WGS 84)"
                        is_geotiff = True
                    # 2. Projected UTM (e.g. Landsat 8/9, Sentinel-2 Level-1C/2A)
                    elif 34735 in tag_v2:
                        geokeys = tag_v2[34735]
                        utm_epsg = None
                        for idx in range(0, len(geokeys) - 3, 4):
                            if geokeys[idx] == 3072:
                                utm_epsg = geokeys[idx + 3]
                                break
                        if utm_epsg:
                            zone = None
                            if 32601 <= utm_epsg <= 32660:
                                zone = utm_epsg - 32600
                                northern = True
                            elif 32701 <= utm_epsg <= 32760:
                                zone = utm_epsg - 32700
                                northern = False

                            if zone:
                                c_lat, c_lon = GeospatialReader._utm_to_latlon((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, zone, northern)
                                sw_lat, sw_lon = GeospatialReader._utm_to_latlon(min_x, min_y, zone, northern)
                                ne_lat, ne_lon = GeospatialReader._utm_to_latlon(max_x, max_y, zone, northern)
                                center_lat = c_lat
                                center_lng = c_lon
                                bounds = (min(sw_lon, ne_lon), min(sw_lat, ne_lat), max(sw_lon, ne_lon), max(sw_lat, ne_lat))
                                crs = f"EPSG:{utm_epsg} (WGS 84 / UTM Zone {zone}{'N' if northern else 'S'})"
                                is_geotiff = True
                except Exception as e:
                    print(f"[GeoTIFF Reader] Projection notice: {e}")

            meta = RasterMetadata(
                width=width,
                height=height,
                bands=bands,
                dtype=str(arr.dtype),
                crs=crs,
                bounds=bounds,
                is_geotiff=is_geotiff,
                modality=modality,
                filename=os.path.basename(file_path),
                center_lat=center_lat,
                center_lng=center_lng
            )
            return data, meta

    @staticmethod
    def _utm_to_latlon(easting: float, northing: float, zone: int, northern: bool = True) -> Tuple[float, float]:
        """Converts Universal Transverse Mercator (UTM) Easting/Northing to WGS-84 Latitude/Longitude."""
        import math
        a = 6378137.0
        f = 1 / 298.257223563
        e = math.sqrt(2 * f - f ** 2)
        e1sq = e ** 2 / (1 - e ** 2)
        k0 = 0.9996

        x = easting - 500000.0
        y = northing if northern else northing - 10000000.0

        m = y / k0
        mu = m / (a * (1 - e ** 2 / 4 - 3 * e ** 4 / 64 - 5 * e ** 6 / 256))
        e1 = (1 - math.sqrt(1 - e ** 2)) / (1 + math.sqrt(1 - e ** 2))
        j1 = 3 * e1 / 2 - 27 * e1 ** 3 / 32
        j2 = 21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32
        j3 = 151 * e1 ** 3 / 96
        j4 = 1097 * e1 ** 4 / 512

        fp = mu + j1 * math.sin(2 * mu) + j2 * math.sin(4 * mu) + j3 * math.sin(6 * mu) + j4 * math.sin(8 * mu)
        c1 = e1sq * math.cos(fp) ** 2
        t1 = math.tan(fp) ** 2
        r1 = a * (1 - e ** 2) / (1 - e ** 2 * math.sin(fp) ** 2) ** 1.5
        n1 = a / math.sqrt(1 - e ** 2 * math.sin(fp) ** 2)
        d = x / (n1 * k0)

        lat = fp - (n1 * math.tan(fp) / r1) * (
            d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * e1sq) * d ** 4 / 24
            + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * e1sq - 3 * c1 ** 2) * d ** 6 / 720
        )
        lon = (
            d - (1 + 2 * t1 + c1) * d ** 3 / 6
            + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * e1sq + 24 * t1 ** 2) * d ** 5 / 120
        ) / math.cos(fp)

        lon_origin = (zone - 1) * 6 - 180 + 3
        return round(math.degrees(lat), 6), round(math.degrees(lon) + lon_origin, 6)

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
            crs=None,
            bounds=None,
            is_geotiff=False,
            modality=detected_modality or "optical",
            filename=os.path.basename(file_path),
            center_lat=None,
            center_lng=None
        )
        return arr, meta

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
