"""
Unit tests for Bi-Temporal Change Detection algorithms, Region Extraction, and Mathematical Statistics.
"""

import numpy as np
import pytest
from analysis_engine.change.change_map import ChangeMapGenerator
from analysis_engine.change.regions import ChangeRegionExtractor
from analysis_engine.change.confidence import ChangeConfidenceEvaluator
from analysis_engine.evidence.statistics import EvidenceStatisticsCalculator
from analysis_engine.schemas import ConfidenceLevel


def test_zero_change_detection():
    """Two identical images must produce 0.0 change probability and 0 changed pixels."""
    arr = np.full((100, 100, 3), 120, dtype=np.float32)
    prob_map, change_mask, conf_map, meta = ChangeMapGenerator.generate_change_map(arr, arr, threshold=0.35)

    assert np.all(change_mask == False)
    assert np.max(prob_map) == 0.0

    stats = EvidenceStatisticsCalculator.compute_change_statistics(
        change_mask=change_mask,
        validity_mask=np.ones((100, 100), dtype=bool),
        pixel_size_meters=10.0,
    )
    assert stats["changed_pixels"] == 0
    assert stats["area_m2"] == 0.0
    assert stats["change_percentage"] == 0.0


def test_known_synthetic_change_extraction():
    """Verifies that a 30x30 change patch (900 pixels) is detected and converted to an authentic region."""
    arr_t1 = np.zeros((100, 100, 3), dtype=np.float32)
    arr_t2 = arr_t1.copy()
    arr_t2[20:50, 20:50] = 1.0  # 30x30 change = 900 pixels

    prob_map, change_mask, conf_map, meta = ChangeMapGenerator.generate_change_map(arr_t1, arr_t2, threshold=0.35)
    assert np.sum(change_mask) == 900

    bounds = [79.0, 21.0, 79.1, 21.1]
    regions = ChangeRegionExtractor.extract_regions(
        change_mask=change_mask,
        bounds_wgs84=bounds,
        pixel_size_meters=10.0,
        min_pixels=20,
        confidence_map=conf_map,
    )

    assert len(regions) == 1
    reg = regions[0]
    assert reg.pixel_count == 900
    assert reg.area_m2 == 90000.0  # 900 * 100 m² = 90,000 m²
    assert reg.area_ha == 9.0      # 9 hectares
    assert reg.geometry["type"] == "Polygon"


def test_tiny_region_suppression():
    """Verifies that noise clusters smaller than min_pixels are filtered out."""
    change_mask = np.zeros((100, 100), dtype=bool)
    change_mask[10:13, 10:13] = True  # 3x3 = 9 pixels (< 20)

    regions = ChangeRegionExtractor.extract_regions(
        change_mask=change_mask,
        bounds_wgs84=[79.0, 21.0, 79.1, 21.1],
        pixel_size_meters=10.0,
        min_pixels=20,
    )
    assert len(regions) == 0


def test_confidence_evaluation():
    # High confidence scenario
    res_high = ChangeConfidenceEvaluator.evaluate(
        model_confidence=0.92,
        valid_pixel_ratio=0.98,
        contamination_ratio=0.02,
        changed_pixels=500,
        min_pixels_required=20,
    )
    assert res_high["level"] == ConfidenceLevel.HIGH.value

    # Low confidence scenario due to heavy contamination
    res_low = ChangeConfidenceEvaluator.evaluate(
        model_confidence=0.50,
        valid_pixel_ratio=0.40,
        contamination_ratio=0.60,
        changed_pixels=10,
        min_pixels_required=20,
    )
    assert res_low["level"] in (ConfidenceLevel.LOW.value, ConfidenceLevel.INSUFFICIENT.value)
