"""
Unit tests for Cross-Modal SAR-Optical Pipeline, Modality Preprocessing, and Coregistration.
"""

import numpy as np
import pytest
from analysis_engine.sar_optical.preprocessing import CrossModalPreprocessor
from analysis_engine.sar_optical.alignment import CrossModalAlignmentChecker
from analysis_engine.sar_optical.feature_builder import CrossModalFeatureBuilder
from analysis_engine.errors import PreprocessingFailureError


def test_cross_modal_preprocessing():
    """Verifies that optical reflectance and SAR dB conversions run independently."""
    opt_arr = np.full((50, 50, 3), 5000, dtype=np.uint16)
    sar_arr = np.full((50, 50), 0.1, dtype=np.float32)

    norm_opt, norm_sar_db, meta = CrossModalPreprocessor.preprocess(
        opt_arr=opt_arr,
        opt_meta={"modality": "optical"},
        sar_arr=sar_arr,
        sar_meta={"modality": "sar"},
    )

    assert meta["modality_aware"] is True
    assert norm_opt.max() <= 1.0
    assert norm_sar_db.min() < 0.0  # Decibels are negative for low backscatter


def test_cross_modal_alignment_check():
    # Overlapping bounds
    res = CrossModalAlignmentChecker.verify_alignment(
        opt_bounds=[79.0, 21.0, 79.2, 21.2],
        sar_bounds=[79.1, 21.1, 79.3, 21.3],
        opt_crs="EPSG:4326",
        sar_crs="EPSG:4326",
    )
    assert res["compatible"] is True
    assert res["spatial_overlap_pct"] > 0.0

    # Completely disjoint bounds must raise PreprocessingFailureError
    with pytest.raises(PreprocessingFailureError):
        CrossModalAlignmentChecker.verify_alignment(
            opt_bounds=[79.0, 21.0, 79.1, 21.1],
            sar_bounds=[85.0, 25.0, 85.1, 25.1],
            opt_crs="EPSG:4326",
            sar_crs="EPSG:4326",
        )


def test_cross_modal_feature_builder():
    opt_arr = np.zeros((64, 64, 3), dtype=np.float32)
    sar_db = np.full((64, 64), -10.0, dtype=np.float32)

    # Simulate low backscatter water
    sar_db[10:30, 10:30] = -25.0

    features = CrossModalFeatureBuilder.extract_features(opt_arr, sar_db)
    assert "sar_water_ratio" in features
    assert "cross_modal_agreement" in features
    assert features["sar_water_ratio"] > 0.0
