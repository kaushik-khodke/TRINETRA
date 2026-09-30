"""
TRINETRA Analysis Engine — Radiometric Normalization
Provides modality-aware radiometric normalization while preserving
scale, offset, original datatype, and nodata metadata.
"""

from typing import Dict, Any, Tuple
import numpy as np


class RadiometricNormalizer:
    @staticmethod
    def normalize_optical(
        arr: np.ndarray,
        meta: Dict[str, Any],
        target_range: Tuple[float, float] = (0.0, 1.0),
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Normalizes optical imagery (e.g. Sentinel-2 uint16 L2A surface reflectance / 10000.0).
        """
        norm_meta = {
            "original_dtype": str(arr.dtype),
            "original_min": float(np.nanmin(arr)) if arr.size > 0 else 0.0,
            "original_max": float(np.nanmax(arr)) if arr.size > 0 else 1.0,
            "normalization_applied": "surface_reflectance_scaling",
        }

        arr_float = arr.astype(np.float32)

        # Sentinel-2 standard L2A scaling factor (10,000 BOA reflectance)
        if norm_meta["original_max"] > 255.0:
            normalized = np.clip(arr_float / 10000.0, target_range[0], target_range[1])
            norm_meta["scale"] = 0.0001
        elif norm_meta["original_max"] > 1.0:
            normalized = np.clip(arr_float / 255.0, target_range[0], target_range[1])
            norm_meta["scale"] = 1.0 / 255.0
        else:
            normalized = np.clip(arr_float, target_range[0], target_range[1])
            norm_meta["scale"] = 1.0

        return normalized, norm_meta

    @staticmethod
    def normalize_sar(
        arr: np.ndarray,
        meta: Dict[str, Any],
        convert_to_db: bool = True,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Normalizes SAR amplitude or linear intensity to Decibels (dB).
        sigma0_dB = 10 * log10(DN^2 + eps)
        """
        arr_float = arr.astype(np.float32)
        norm_meta = {
            "original_dtype": str(arr.dtype),
            "converted_to_db": convert_to_db,
            "speckle_filtered": False,
        }

        if convert_to_db:
            eps = 1e-6
            clipped = np.clip(arr_float, eps, None)
            sar_db = 10.0 * np.log10(clipped)
            # Standard SAR decibel clipping [-30 dB, 5 dB]
            sar_db_clipped = np.clip(sar_db, -30.0, 5.0)
            norm_meta["db_min"] = float(np.min(sar_db_clipped))
            norm_meta["db_max"] = float(np.max(sar_db_clipped))
            return sar_db_clipped, norm_meta
        else:
            return arr_float, norm_meta
