"""
TRINETRA Phase 7 — Temporal Anomaly Detection
Identifies sudden change accelerations, unexpected spikes, and abrupt land-cover reversals.
"""

from typing import List, Dict, Any, Optional, Tuple


class TemporalAnomalyDetector:
    """
    Evaluates multi-epoch change rate trajectories against historical velocities.
    """

    @classmethod
    def detect_rate_anomaly(
        cls,
        current_change_pct: float,
        historical_series: List[float],
    ) -> Tuple[bool, float, str]:
        if len(historical_series) < 3:
            return False, 0.0, "INSUFFICIENT_BASELINE"

        avg_rate = sum(historical_series) / len(historical_series)
        max_hist = max(historical_series)

        # Check for sudden surge
        if current_change_pct >= max(2.5 * avg_rate, max_hist * 1.8) and current_change_pct > 5.0:
            surge_factor = current_change_pct / max(0.1, avg_rate)
            return True, round(surge_factor, 2), f"Observed change rate ({current_change_pct}%) surges {round(surge_factor, 1)}x above historical mean ({round(avg_rate, 1)}%)."

        # Check for abrupt reversal (e.g. negative jump)
        if len(historical_series) >= 4 and all(x > 0 for x in historical_series[-3:]) and current_change_pct < -5.0:
            return True, abs(round(current_change_pct, 2)), "Abrupt reversal: sudden negative shift following sustained positive expansion."

        return False, 1.0, "Rate within historical operational boundaries."
