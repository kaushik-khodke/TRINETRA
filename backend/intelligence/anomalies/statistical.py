"""
TRINETRA Phase 7 — Statistical Anomaly Detection
Computes Z-scores, robust Z-scores (median + MAD), and historical distribution baselines.
"""

import math
import uuid
from typing import List, Optional, Tuple, Dict, Any
from intelligence.models import Baseline


class StatisticalBaselineBuilder:
    """
    Constructs statistical baselines from empirical observation history.
    Enforces strict minimum sample sufficiency.
    """

    MIN_SAMPLES_THRESHOLD = 4

    @classmethod
    def build(
        cls,
        metric_name: str,
        spatial_unit: str,
        values: List[float],
        temporal_window: str = "365d",
        seasonal_grouping: Optional[str] = None,
    ) -> Optional[Baseline]:
        if not values or len(values) < cls.MIN_SAMPLES_THRESHOLD:
            return None  # INSUFFICIENT_BASELINE

        n = len(values)
        sorted_vals = sorted(values)
        mean_val = sum(values) / n

        variance = sum((x - mean_val) ** 2 for x in values) / max(1, n - 1)
        std_val = math.sqrt(variance)

        # Median
        mid = n // 2
        median_val = (sorted_vals[mid] if n % 2 != 0 else (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0)

        # Median Absolute Deviation (MAD)
        deviations = sorted(abs(x - median_val) for x in values)
        mad_val = deviations[mid] if n % 2 != 0 else (deviations[mid - 1] + deviations[mid]) / 2.0

        p90_idx = min(n - 1, int(0.90 * n))
        p90_val = sorted_vals[p90_idx]

        return Baseline(
            baseline_id=f"base_{uuid.uuid4().hex[:8]}",
            metric_name=metric_name,
            spatial_unit=spatial_unit,
            temporal_window=temporal_window,
            seasonal_grouping=seasonal_grouping,
            sample_count=n,
            mean=mean_val,
            std=std_val,
            median=median_val,
            mad=mad_val,
            p90=p90_val,
            min_val=sorted_vals[0],
            max_val=sorted_vals[-1],
        )

    @classmethod
    def evaluate_deviation(
        cls,
        value: float,
        baseline: Baseline,
    ) -> Tuple[bool, float, float]:
        """
        Returns: (is_anomalous, z_score, robust_z_score)
        """
        # Standard Z-score
        denom_std = max(0.001, baseline.std)
        z_score = (value - baseline.mean) / denom_std

        # Robust Z-score (using MAD)
        denom_mad = max(0.001, baseline.mad)
        robust_z = 0.6745 * (value - baseline.median) / denom_mad

        is_anomalous = abs(z_score) >= 2.5 or abs(robust_z) >= 3.0
        return is_anomalous, round(z_score, 3), round(robust_z, 3)
