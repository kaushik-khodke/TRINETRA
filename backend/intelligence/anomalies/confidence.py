"""
TRINETRA Phase 7 — Anomaly Confidence Scoring
Weights anomaly magnitude by baseline statistical depth to avoid false certainty on sparse samples.
"""

from typing import Dict, Any


class AnomalyConfidenceEvaluator:
    """
    Computes calibrated confidence for flagged anomalies.
    """

    @classmethod
    def evaluate(
        cls,
        z_score: float,
        sample_count: int,
        has_seasonal_match: bool = False,
    ) -> float:
        # 1. Baseline quality factor
        if sample_count >= 12:
            base_quality = 0.92
        elif sample_count >= 8:
            base_quality = 0.82
        elif sample_count >= 4:
            base_quality = 0.65
        else:
            base_quality = 0.40

        # Seasonal alignment bonus
        if has_seasonal_match:
            base_quality = min(0.98, base_quality + 0.08)

        # 2. Deviation magnitude factor
        mag_factor = min(1.0, abs(z_score) / 3.5)

        raw_conf = base_quality * mag_factor
        return round(max(0.15, min(0.96, raw_conf)), 3)
