"""
TRINETRA Analysis Engine — Masking & Data Quality Propagation
Tracks nodata, invalid values, and cloud contamination.
Ensures that changes or findings over invalid pixels are never reported as factual events.
"""

from typing import Optional, Tuple
import numpy as np


class QualityMaskManager:
    @staticmethod
    def build_validity_mask(
        arr: np.ndarray,
        nodata_val: Optional[float] = None,
        cloud_mask: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Creates a boolean mask where True = valid pixel, False = invalid / nodata / cloud.
        """
        H, W = arr.shape[:2]
        valid_mask = np.ones((H, W), dtype=bool)

        # 1. NaN or Infinite values
        if np.issubdtype(arr.dtype, np.floating):
            nan_mask = np.isnan(arr) | np.isinf(arr)
            if arr.ndim == 3:
                nan_mask = np.any(nan_mask, axis=-1)
            valid_mask &= ~nan_mask

        # 2. Explicit nodata values
        if nodata_val is not None:
            if arr.ndim == 3:
                nd_mask = np.all(arr == nodata_val, axis=-1)
            else:
                nd_mask = (arr == nodata_val)
            valid_mask &= ~nd_mask

        # 3. Cloud contamination
        if cloud_mask is not None:
            # Assume cloud_mask is True for cloudy pixels
            if cloud_mask.shape[:2] == (H, W):
                valid_mask &= ~cloud_mask

        return valid_mask

    @staticmethod
    def filter_evidence_by_mask(
        change_mask: np.ndarray,
        validity_mask: np.ndarray,
    ) -> Tuple[np.ndarray, float]:
        """
        Suppresses changes that occur over invalid or masked pixels.
        Returns (clean_change_mask, contamination_ratio).
        """
        clean_change = change_mask & validity_mask
        invalid_changes = change_mask & (~validity_mask)
        
        total_detected = np.sum(change_mask)
        contamination_ratio = float(np.sum(invalid_changes) / total_detected) if total_detected > 0 else 0.0

        return clean_change, round(contamination_ratio, 4)
