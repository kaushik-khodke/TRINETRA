"""
SatQuery AI / TRINETRA — Hyperspectral Geospatial Cube Reader
Reads multi-band GeoTIFF, ENVI (.hdr/.dat), and MATLAB (.mat) hyperspectral data cubes.
Preserves the full 3D spectral cube (H x W x Bands). Generates RGB and false-color CIR
composites strictly as visualization derivatives without altering the underlying cube.
"""

import os
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image

try:
    import scipy.io as sio
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

try:
    import tifffile
    HAS_TIFFFILE = True
except ImportError:
    HAS_TIFFFILE = False

class HsiCubeData:
    """Represents an authentic hyperspectral data cube with full spectral fidelity."""
    def __init__(
        self,
        cube: np.ndarray,
        wavelengths: Optional[np.ndarray] = None,
        crs: Optional[str] = None,
        bounds: Optional[Tuple[float, float, float, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        sensor_name: str = "Hyperspectral Sensor"
    ):
        # Shape should be (H, W, Bands)
        if cube.ndim == 3 and cube.shape[0] > cube.shape[1] and cube.shape[0] > cube.shape[2]:
            # Bands first (B, H, W) -> transpose to (H, W, B)
            if cube.shape[1] > 10 and cube.shape[2] > 10:
                cube = np.transpose(cube, (1, 2, 0))
        
        self.cube = cube.astype(np.float32)
        self.height, self.width, self.bands = self.cube.shape
        self.crs = crs
        self.bounds = bounds
        self.metadata = metadata or {}
        self.sensor_name = sensor_name

        # Normalization: ensure reflectance is scaled into [0, 1]
        c_max = float(np.nanmax(self.cube))
        c_min = float(np.nanmin(self.cube))
        if c_max > 1.5:
            # Data is likely scaled (e.g. 0-10000 or DN integers)
            if c_max > 255:
                self.cube = np.clip((self.cube - c_min) / (c_max - c_min + 1e-5), 0.0, 1.0)
            else:
                self.cube = np.clip(self.cube / 255.0, 0.0, 1.0)

        # Wavelengths in nanometers
        if wavelengths is not None and len(wavelengths) == self.bands:
            self.wavelengths = np.array(wavelengths, dtype=np.float32)
        else:
            # Estimate default standard optical-to-SWIR distribution (400nm to 2500nm)
            self.wavelengths = np.linspace(400.0, 2450.0, self.bands, dtype=np.float32)

    def get_band_index_for_wavelength(self, target_nm: float) -> int:
        """Finds band index with wavelength closest to target_nm."""
        return int(np.argmin(np.abs(self.wavelengths - target_nm)))

    def to_rgb_composite(self, red_nm: float = 640.0, green_nm: float = 550.0, blue_nm: float = 470.0) -> np.ndarray:
        """
        Renders a display-only True Color RGB composite.
        Does NOT alter the underlying 3D spectral cube.
        """
        r_idx = self.get_band_index_for_wavelength(red_nm)
        g_idx = self.get_band_index_for_wavelength(green_nm)
        b_idx = self.get_band_index_for_wavelength(blue_nm)

        r = self.cube[:, :, r_idx]
        g = self.cube[:, :, g_idx]
        b = self.cube[:, :, b_idx]

        rgb = np.stack([r, g, b], axis=-1)
        return self._percentile_stretch(rgb)

    def to_cir_false_color(self, nir_nm: float = 850.0, red_nm: float = 650.0, green_nm: float = 550.0) -> np.ndarray:
        """
        Renders a Color-Infrared (CIR) false-color composite (NIR, Red, Green).
        Highlights vegetation vigor in red.
        """
        nir_idx = self.get_band_index_for_wavelength(nir_nm)
        r_idx = self.get_band_index_for_wavelength(red_nm)
        g_idx = self.get_band_index_for_wavelength(green_nm)

        nir = self.cube[:, :, nir_idx]
        r = self.cube[:, :, r_idx]
        g = self.cube[:, :, g_idx]

        cir = np.stack([nir, r, g], axis=-1)
        return self._percentile_stretch(cir)

    def to_single_band_preview(self, band_idx: int) -> np.ndarray:
        """Renders single grayscale band slice with contrast stretch."""
        idx = max(0, min(self.bands - 1, band_idx))
        b = self.cube[:, :, idx]
        stretched = self._percentile_stretch(b)
        return np.stack([stretched, stretched, stretched], axis=-1)

    @staticmethod
    def _percentile_stretch(img: np.ndarray, lower: float = 2.0, upper: float = 98.0) -> np.ndarray:
        """2% - 98% contrast stretch to uint8 [0, 255]."""
        p_low = np.percentile(img, lower)
        p_high = np.percentile(img, upper)
        if p_high - p_low > 1e-5:
            stretched = np.clip((img - p_low) / (p_high - p_low), 0.0, 1.0)
        else:
            stretched = np.clip(img, 0.0, 1.0)
        return (stretched * 255.0).astype(np.uint8)

class HsiReader:
    """Universal Hyperspectral File Reader for GeoTIFF, MATLAB, and ENVI."""

    @staticmethod
    def is_hsi_file(path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        if ext in [".mat", ".hdr"]:
            return True
        if ext in [".tif", ".tiff"]:
            try:
                if HAS_RASTERIO:
                    with rasterio.open(path) as src:
                        return src.count >= 40
            except Exception:
                pass
        return False

    @classmethod
    def read(cls, file_path: str) -> HsiCubeData:
        """Reads HSI file into HsiCubeData without data destruction."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Hyperspectral file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        # 1. MATLAB (.mat) format (Indian Pines, Salinas, Pavia University)
        if ext == ".mat":
            return cls._read_mat(file_path)

        # 2. ENVI (.hdr) format
        if ext == ".hdr":
            return cls._read_envi(file_path)

        # 3. GeoTIFF with 40+ bands
        if ext in [".tif", ".tiff"]:
            return cls._read_geotiff(file_path)

        raise ValueError(f"Unsupported file format for HSI reading: {ext}")

    @classmethod
    def read_cube(cls, file_path: str) -> HsiCubeData:
        """Alias for read() method."""
        return cls.read(file_path)

    @classmethod
    def _read_mat(cls, file_path: str) -> HsiCubeData:
        if not HAS_SCIPY:
            raise ImportError("scipy is required to read MATLAB .mat hyperspectral files.")

        mat_dict = sio.loadmat(file_path)
        # Find 3D array in the MATLAB dictionary
        cube_arr = None
        cube_key = ""
        for k, v in mat_dict.items():
            if not k.startswith("__") and isinstance(v, np.ndarray) and v.ndim == 3:
                cube_arr = v
                cube_key = k
                break

        if cube_arr is None:
            # Check for 2D arrays that might be shaped (pixels, bands)
            for k, v in mat_dict.items():
                if not k.startswith("__") and isinstance(v, np.ndarray) and v.ndim == 2 and min(v.shape) >= 40:
                    cube_arr = v
                    cube_key = k
                    break

        if cube_arr is None:
            raise ValueError(f"Could not find 3D hyperspectral cube in MATLAB file '{file_path}'. Keys: {list(mat_dict.keys())}")

        # Check for wavelengths vector
        wl = None
        for k in ["wavelength", "wavelengths", "bands", "wl", "Wavelengths"]:
            if k in mat_dict and isinstance(mat_dict[k], np.ndarray):
                wl = mat_dict[k].flatten()
                break

        # Detect dataset identity
        fn = os.path.basename(file_path).lower()
        sensor = "AVIRIS Hyperspectral Sensor" if ("indian" in fn or "salinas" in fn) else ("ROSIS Sensor" if "pavia" in fn else "Hyperspectral Sensor")

        return HsiCubeData(
            cube=cube_arr,
            wavelengths=wl,
            metadata={"dataset_key": cube_key, "source_format": "matlab"},
            sensor_name=sensor
        )

    @classmethod
    def _read_geotiff(cls, file_path: str) -> HsiCubeData:
        crs = None
        bounds = None
        metadata = {}

        if HAS_RASTERIO:
            with rasterio.open(file_path) as src:
                arr = src.read()  # Shape (Bands, H, W)
                arr = np.transpose(arr, (1, 2, 0))  # Shape (H, W, Bands)
                crs = str(src.crs) if src.crs else None
                bounds = (src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)
                metadata = dict(src.meta)
        elif HAS_TIFFFILE:
            arr = tifffile.imread(file_path)
            if arr.ndim == 3 and arr.shape[0] > arr.shape[1]:
                arr = np.transpose(arr, (1, 2, 0))
        else:
            raise ImportError("rasterio or tifffile is required to read GeoTIFF hyperspectral data.")

        return HsiCubeData(
            cube=arr,
            crs=crs,
            bounds=bounds,
            metadata=metadata,
            sensor_name="Hyperspectral Spaceborne / Airborne Sensor"
        )

    @classmethod
    def _read_envi(cls, file_path: str) -> HsiCubeData:
        # Check corresponding .dat or .img binary
        base = os.path.splitext(file_path)[0]
        dat_path = base + ".dat" if os.path.exists(base + ".dat") else (base + ".img" if os.path.exists(base + ".img") else base)
        
        # Parse .hdr text
        header = {}
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "=" in line:
                    parts = line.split("=", 1)
                    header[parts[0].strip().lower()] = parts[1].strip()

        lines = int(header.get("lines", 0))
        samples = int(header.get("samples", 0))
        bands = int(header.get("bands", 0))

        if not os.path.exists(dat_path) or lines == 0 or samples == 0 or bands == 0:
            raise ValueError(f"Incomplete ENVI dataset at '{file_path}'. Missing companion data file or raster dimensions.")

        dtype_map = {"1": np.uint8, "2": np.int16, "3": np.int32, "4": np.float32, "5": np.float64, "12": np.uint16}
        dt = dtype_map.get(header.get("data type", "4"), np.float32)

        raw = np.fromfile(dat_path, dtype=dt)
        cube = raw.reshape((lines, samples, bands))

        return HsiCubeData(
            cube=cube,
            metadata=header,
            sensor_name=header.get("sensor type", "ENVI Airborne/Spaceborne HSI")
        )
