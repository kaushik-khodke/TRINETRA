"""
Unit tests for Statistical Anomaly Detection Subsystem.
Tests statistical baseline builder, sample sufficiency gating, Z-score thresholds, and anomaly explanation.
"""

import pytest
from intelligence.models import Baseline
from intelligence.anomalies.statistical import StatisticalBaselineBuilder
from intelligence.anomalies.detector import AnomalyDetector
from intelligence.anomalies.confidence import AnomalyConfidenceEvaluator
from intelligence.anomalies.explain import AnomalyExplainer


def test_baseline_builder_insufficient_samples():
    # Fewer than 4 samples must return None to prevent spurious anomalies
    samples = [1.2, 1.4, 1.1]
    base = StatisticalBaselineBuilder.build(
        metric_name="change_rate",
        spatial_unit="sector_01",
        values=samples,
    )
    assert base is None


def test_baseline_builder_valid():
    samples = [10.0, 12.0, 11.0, 10.5, 11.5, 13.0, 10.8, 11.2]
    base = StatisticalBaselineBuilder.build(
        metric_name="monthly_change_ha",
        spatial_unit="sector_01",
        values=samples,
    )
    assert base is not None
    assert base.sample_count == 8
    assert 10.0 < base.mean < 12.0
    assert base.median > 0.0
    assert base.mad > 0.0


def test_anomaly_detection_trigger():
    # Build a calibrated baseline with 10 normal samples around 10.0
    samples = [10.0, 10.2, 9.8, 10.1, 9.9, 10.3, 9.7, 10.0, 10.1, 9.9]
    base = StatisticalBaselineBuilder.build(
        metric_name="change_area_ha",
        spatial_unit="region_test",
        values=samples,
    )
    assert base is not None

    # Normal value -> no anomaly
    normal_res = AnomalyDetector.evaluate_metric(
        metric_name="change_area_ha",
        observed_value=10.05,
        baseline=base,
        region_id="region_test",
    )
    assert normal_res is None

    # Extreme value (25.0 vs median 10.0, diff=15, robust_z = 0.6745 * 15 / 0.7 = 14.45)
    anom = AnomalyDetector.evaluate_metric(
        metric_name="change_area_ha",
        observed_value=25.0,
        baseline=base,
        region_id="region_test",
        event_id="evt_01",
    )
    assert anom is not None
    assert anom.anomaly_score > 0.5
    assert anom.confidence > 0.5
    assert len(anom.explanation) > 0


def test_confidence_scorer():
    # Low sample count (4) -> lower confidence
    c_low = AnomalyConfidenceEvaluator.evaluate(z_score=3.5, sample_count=4)
    # High sample count (20) -> higher confidence
    c_high = AnomalyConfidenceEvaluator.evaluate(z_score=3.5, sample_count=20)
    assert c_high > c_low
