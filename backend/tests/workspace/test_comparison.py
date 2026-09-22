"""
TRINETRA Phase 8 Tests — Comparison Subsystem
Verifies area normalization, disparity warnings, and multi-threshold sensitivity curves.
"""

import pytest
from workspace.comparison.metrics import ComparisonMetricsEngine
from workspace.comparison.regions import RegionComparator
from workspace.comparison.events import EventComparator
from workspace.comparison.findings import FindingComparator
from workspace.comparison.validator import ComparisonValidator, ComparisonValidationError
from workspace.repository import WorkspaceRepository


@pytest.fixture
def repo():
    return WorkspaceRepository(":memory:")


@pytest.fixture
def comparator(repo):
    return RegionComparator(repository=repo)


def test_area_normalization():
    # 20 detections in 50 km² = 40 per 100 km²
    norm = ComparisonMetricsEngine.normalize_by_area(raw_value=20.0, area_km2=50.0, scale_factor=100.0)
    assert norm == 40.0

    # Zero area guard
    assert ComparisonMetricsEngine.normalize_by_area(10.0, 0.0) == 0.0


def test_metric_difference_computation():
    res = ComparisonMetricsEngine.compute_metric_difference(val_a=25.0, val_b=35.0, name="events_density")
    assert res["absolute_difference"] == 10.0
    assert res["percentage_difference"] == 40.0
    assert res["higher_region"] == "B"


def test_multi_threshold_sensitivity_curve():
    thresholds = [0.1, 0.2, 0.3, 0.4]
    curve = ComparisonMetricsEngine.compute_sensitivity_curve(thresholds=thresholds, base_area_km2=10.0)

    assert len(curve) == 4
    for pt in curve:
        assert "threshold" in pt
        assert "detected_area_km2" in pt
        assert "rate_of_change" in pt
        assert pt["stability"] in ["STABLE", "MODERATELY_SENSITIVE", "HYPERSENSITIVE"]

    # Strict monotonicity: area should decrease as threshold increases
    areas = [pt["detected_area_km2"] for pt in curve]
    for i in range(len(areas) - 1):
        assert areas[i] >= areas[i + 1]


def test_coverage_disparity_warnings():
    meta_a = {"cloud_cover_percentage": 5.0, "resolution_meters": 10.0, "area_km2": 40.0, "sensor_type": "OPTICAL"}
    meta_b = {"cloud_cover_percentage": 28.0, "resolution_meters": 30.0, "area_km2": 250.0, "sensor_type": "SAR"}

    warnings = ComparisonMetricsEngine.detect_coverage_warnings(meta_a, meta_b)
    assert len(warnings) >= 3

    warning_text = " ".join(warnings)
    assert "Cloud cover disparity" in warning_text
    assert "Resolution mismatch" in warning_text
    assert "Cross-sensor modality comparison" in warning_text


def test_region_comparator_execution(comparator):
    comp = comparator.compare_regions(
        workspace_id="ws-comp-test",
        region_a_id="reg-kashmir",
        region_b_id="reg-ladakh",
        period="last_6_months",
    )

    assert comp.comparison_id.startswith("comp-")
    assert "region_a" in comp.metrics
    assert "region_b" in comp.metrics
    assert "events_per_100km2" in comp.metrics["region_a"]
    assert "findings_per_100km2" in comp.metrics["region_b"]
    assert len(comp.metrics["region_a"]["sensitivity_curve"]) > 0


def test_comparison_validation_self_comparison():
    with pytest.raises(ComparisonValidationError) as exc:
        ComparisonValidator.validate_region_comparison("ws-1", "reg-same", "reg-same")
    assert "Cannot compare a region to itself" in str(exc.value)
