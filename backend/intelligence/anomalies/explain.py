"""
TRINETRA Phase 7 — Anomaly Explanation Generator
Produces deterministic, human-readable explanations comparing empirical observation against historical baselines.
"""

from typing import Dict, Any, List
from intelligence.models import Baseline


class AnomalyExplainer:
    """
    Generates transparent diagnostic narratives for detected statistical anomalies.
    """

    @classmethod
    def explain(
        cls,
        metric_name: str,
        observed_val: float,
        baseline: Baseline,
        z_score: float,
    ) -> str:
        readable_metric = metric_name.replace("_", " ")
        lower_bound = round(max(0.0, baseline.mean - (2.0 * baseline.std)), 2)
        upper_bound = round(baseline.mean + (2.0 * baseline.std), 2)

        narrative = (
            f"Observed {readable_metric} ({round(observed_val, 2)}) deviates significantly "
            f"from the typical historical range of {lower_bound} to {upper_bound}. "
            f"Baseline constructed from {baseline.sample_count} historical acquisitions "
            f"(mean: {round(baseline.mean, 2)}, std: {round(baseline.std, 2)}, Z-score: {round(z_score, 2)})."
        )

        return narrative
