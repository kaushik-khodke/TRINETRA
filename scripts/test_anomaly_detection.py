"""
TRINETRA Phase 7 — Verification Script: Statistical Anomaly Detection
Validates historical baseline calculation, deviation scoring (Z-score & MAD),
outlier detection, confidence evaluation, and non-causal contextual explanation.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from intelligence.anomalies.statistical import StatisticalBaselineBuilder
from intelligence.anomalies.detector import AnomalyDetector
from intelligence.anomalies.confidence import AnomalyConfidenceEvaluator
from intelligence.anomalies.explain import AnomalyExplainer
from intelligence.models import Baseline


def run_anomaly_test():
    print("================================================================")
    print("  TRINETRA Phase 7: Statistical Anomaly Detection Verification")
    print("================================================================")

    # 1. Build statistical baseline from historical observations (10 samples)
    print("[1] Building Statistical Baseline from Historical Samples...")
    historical_samples = [1.2, 1.4, 1.1, 1.3, 1.5, 1.2, 1.3, 1.4, 1.1, 1.5]
    baseline = StatisticalBaselineBuilder.build(
        metric_name="delta_ndvi_rate",
        spatial_unit="district_nagpur",
        values=historical_samples,
        temporal_window="seasonal_monsoon",
    )
    assert baseline is not None
    print(f"✓ Baseline constructed for '{baseline.metric_name}':")
    print(f"  Samples: {baseline.sample_count}, Mean: {baseline.mean:.3f}, Std: {baseline.std:.3f}")
    print(f"  Median: {baseline.median:.3f}, MAD: {baseline.mad:.3f}, P90: {baseline.p90:.3f}")
    assert baseline.sample_count == 10
    assert baseline.mean > 1.0

    # 2. Test normal observation (within normal distribution)
    print("\n[2] Evaluating Normal Observation (value=1.35)...")
    normal_val = 1.35
    normal_anomaly = AnomalyDetector.evaluate_metric(
        metric_name="delta_ndvi_rate",
        observed_value=normal_val,
        baseline=baseline,
    )
    assert normal_anomaly is None
    print("✓ Normal value 1.35 within normal variation -> No anomaly flagged.")

    # 3. Test anomalous observation (extreme outlier value=4.50)
    print("\n[3] Evaluating Extreme Outlier Observation (value=4.50)...")
    extreme_val = 4.50
    anomaly = AnomalyDetector.evaluate_metric(
        metric_name="delta_ndvi_rate",
        observed_value=extreme_val,
        baseline=baseline,
        region_id="reg_nagpur_rural",
        event_id="evt_extreme_loss_01",
    )
    assert anomaly is not None
    print(f"✓ Anomaly triggered! ID: '{anomaly.anomaly_id}'")
    print(f"  Z-Score: {anomaly.anomaly_score:+.2f}σ")
    print(f"  Anomaly Type: {anomaly.anomaly_type}, Status: {anomaly.status}")
    assert anomaly.anomaly_score > 2.0

    # 4. Confidence Evaluation
    print("\n[4] Evaluating Anomaly Confidence...")
    conf = AnomalyConfidenceEvaluator.evaluate(
        z_score=anomaly.anomaly_score,
        sample_count=baseline.sample_count,
        has_seasonal_match=True,
    )
    print(f"✓ Evaluated Anomaly Confidence: {conf:.3f}")
    assert conf >= 0.70

    # 5. Non-causal explanation check
    print("\n[5] Verifying Non-Causal Explanation...")
    explanation = AnomalyExplainer.explain(
        metric_name="delta_ndvi_rate",
        observed_val=extreme_val,
        baseline=baseline,
        z_score=anomaly.anomaly_score,
    )
    print(f"✓ Plain-Language Explanation:\n   \"{explanation}\"")
    # Verify non-causal compliance: no speculation on motives or intent
    forbidden_words = ["deliberate", "intentional", "illegal", "sabotage", "malicious"]
    for word in forbidden_words:
        assert word not in explanation.lower(), f"Violation of non-causal protocol: found '{word}'"
    print("✓ Non-causal attribution protocol strictly verified (no subjective intent inferred).")

    print("\n>>> ALL STATISTICAL ANOMALY DETECTION TESTS PASSED! <<<\n")


if __name__ == "__main__":
    run_anomaly_test()
