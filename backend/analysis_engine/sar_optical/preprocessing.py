"""
TRINETRA Analysis Engine — Cross-Modal Preprocessing
Applies modality-specific conversions to SAR and Optical observations separately.
"""

from typing import Dict, Any, Tuple
import numpy as np
from analysis_engine.preprocessing.normalization import RadiometricNormalizer


class CrossModalPreprocessor:
    @staticmethod
    def preprocess(
        opt_arr: np.ndarray,
        opt_meta: Dict[str, Any],
        sar_arr: np.ndarray,
        sar_meta: Dict[str, Any],
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Preprocesses Optical and SAR independently without naive channel stacking.
        """
        # Optical: scale surface reflectance
        norm_opt, opt_norm_meta = RadiometricNormalizer.normalize_optical(opt_arr, opt_meta)

        # SAR: convert linear amplitude to Decibels (dB)
        norm_sar_db, sar_norm_meta = RadiometricNormalizer.normalize_sar(sar_arr, sar_meta, convert_to_db=True)

        metadata = {
            "optical_processing": opt_norm_meta,
            "sar_processing": sar_norm_meta,
            "modality_aware": True,
        }

        return norm_opt, norm_sar_db, metadata
