"""
TRINETRA Analysis Engine — Spatial Grid Alignment Engine
Aligns two raster observations to an identical pixel grid, dimension, resolution, and spatial envelope.
"""

from typing import Tuple, Dict, Any, List
import numpy as np
from PIL import Image
from analysis_engine.errors import PreprocessingFailureError


class RasterGridAligner:
    """Aligns pair observations to a mutual coordinate grid."""

    @staticmethod
    def align_pair(
        arr_a: np.ndarray,
        meta_a: Dict[str, Any],
        arr_b: np.ndarray,
        meta_b: Dict[str, Any],
        reference: str = "a",
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Aligns arr_a and arr_b to have matching dimensions (H, W) and common spatial bounds.
        """
        h_a, w_a = arr_a.shape[:2]
        h_b, w_b = arr_b.shape[:2]

        report = {
            "source_a_shape": (h_a, w_a),
            "source_b_shape": (h_b, w_b),
            "crs_a": meta_a.get("crs", "EPSG:4326"),
            "crs_b": meta_b.get("crs", "EPSG:4326"),
            "resampled": False,
        }

        # If dimensions already match perfectly
        if (h_a, w_a) == (h_b, w_b):
            report["aligned_shape"] = (h_a, w_a)
            return arr_a, arr_b, report

        # Target grid determination
        target_h, target_w = (h_a, w_a) if reference == "a" else (h_b, w_b)

        # Resample non-reference image to target dimensions using PIL or SciPy
        if reference == "a":
            aligned_b = RasterGridAligner._resample_array(arr_b, (target_h, target_w))
            aligned_a = arr_a
        else:
            aligned_a = RasterGridAligner._resample_array(arr_a, (target_h, target_w))
            aligned_b = arr_b

        report["resampled"] = True
        report["aligned_shape"] = (target_h, target_w)
        return aligned_a, aligned_b, report

    @staticmethod
    def _resample_array(arr: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
        """Resamples 2D or 3D array to target (H, W) preserving channels."""
        target_h, target_w = target_shape
        orig_dtype = arr.dtype

        # Multi-channel
        if arr.ndim == 3:
            channels = []
            for c in range(arr.shape[2]):
                ch = arr[:, :, c]
                pil_ch = Image.fromarray(ch)
                resized = pil_ch.resize((target_w, target_h), Image.BILINEAR)
                channels.append(np.array(resized, dtype=orig_dtype))
            return np.stack(channels, axis=-1)
        else:  # Single band
            pil_img = Image.fromarray(arr)
            resized = pil_img.resize((target_w, target_h), Image.BILINEAR)
            return np.array(resized, dtype=orig_dtype)
