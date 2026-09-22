"""
TRINETRA Phase 7 — Anomaly Detection Coordinator
Orchestrates statistical, temporal, and spatial anomaly evaluation against durable baselines.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from intelligence.models import Baseline, AnomalyRecord, PersistentFinding, EOEvent
from intelligence.anomalies.statistical import StatisticalBaselineBuilder
from intelligence.anomalies.confidence import AnomalyConfidenceEvaluator
from intelligence.anomalies.explain import AnomalyExplainer
from intelligence.anomalies.temporal import TemporalAnomalyDetector
from intelligence.anomalies.spatial import SpatialAnomalyDetector


class AnomalyDetector:
    """
    Evaluates empirical observation values against historical baselines and spatial envelopes.
    """

    @classmethod
    def evaluate_metric(
        cls,
        metric_name: str,
        observed_value: float,
        baseline: Baseline,
        region_id: Optional[str] = None,
        event_id: Optional[str] = None,
        finding_id: Optional[str] = None,
    ) -> Optional[AnomalyRecord]:
        is_anom, z_score, robust_z = StatisticalBaselineBuilder.evaluate_deviation(observed_value, baseline)

        if not is_anom:
            return None

        confidence = AnomalyConfidenceEvaluator.evaluate(
            z_score=z_score,
            sample_count=baseline.sample_count,
            has_seasonal_match=bool(baseline.seasonal_grouping),
        )

        explanation = AnomalyExplainer.explain(
            metric_name=metric_name,
            observed_val=observed_value,
            baseline=baseline,
            z_score=z_score,
        )

        lower_b = max(0.0, baseline.mean - (2.0 * baseline.std))
        upper_b = baseline.mean + (2.0 * baseline.std)

        anomaly = AnomalyRecord(
            anomaly_id=f"anom_{uuid.uuid4().hex[:8]}",
            baseline_id=baseline.baseline_id,
            region_id=region_id,
            event_id=event_id,
            finding_id=finding_id,
            metric_name=metric_name,
            observed_value=observed_value,
            baseline_mean=baseline.mean,
            baseline_std=baseline.std,
            baseline_range=[lower_b, upper_b],
            anomaly_score=abs(z_score),
            confidence=confidence,
            anomaly_type="STATISTICAL_OUTLIER",
            explanation=explanation,
            status="ACTIVE",
        )

        return anomaly
