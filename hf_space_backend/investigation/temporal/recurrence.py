"""
TRINETRA Phase 6 — Recurrence Detection
Detects cyclical fluctuations, seasonal signatures, and periodic disturbances.
"""

from typing import Dict, Any, List


class RecurrenceProfile:
    def __init__(
        self,
        region_id: str,
        is_recurrent: bool,
        cycle_type: str,
        confidence: float,
        estimated_period_days: int,
        oscillation_count: int = 0,
    ):
        self.region_id = region_id
        self.is_recurrent = is_recurrent
        self.cycle_type = cycle_type
        self.confidence = confidence
        self.estimated_period_days = estimated_period_days
        self.oscillation_count = oscillation_count

    @property
    def is_cyclical(self) -> bool:
        return self.is_recurrent

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "is_recurrent": self.is_recurrent,
            "is_cyclical": self.is_cyclical,
            "cycle_type": self.cycle_type,
            "confidence": round(self.confidence, 3),
            "estimated_period_days": self.estimated_period_days,
            "oscillation_count": self.oscillation_count,
        }


class RecurrenceDetector:
    """
    Identifies periodic land-cover transitions without forcing unproven seasonal claims.
    """

    @classmethod
    def detect_recurrence(
        cls,
        series_or_signals: Any,
        region_id: str = "reg_01",
    ) -> RecurrenceProfile:
        signals = []
        if isinstance(series_or_signals, list):
            for item in series_or_signals:
                if isinstance(item, (int, float)):
                    signals.append(float(item))
                elif isinstance(item, dict):
                    signals.append(float(item.get("change_pct", item.get("value", item.get("delta", 0.0)))))
        return cls.detect(region_id=region_id, temporal_signals=signals)

    @classmethod
    def detect(cls, region_id: str, temporal_signals: List[float]) -> RecurrenceProfile:
        if len(temporal_signals) < 4:
            return RecurrenceProfile(
                region_id=region_id,
                is_recurrent=False,
                cycle_type="insufficient_temporal_depth",
                confidence=0.2,
                estimated_period_days=0,
                oscillation_count=0,
            )

        # Count zero-crossings or directional switches
        switches = 0
        for i in range(1, len(temporal_signals) - 1):
            prev_d = temporal_signals[i] - temporal_signals[i - 1]
            next_d = temporal_signals[i + 1] - temporal_signals[i]
            if (prev_d * next_d) < 0:
                switches += 1

        is_recurrent = switches >= 1
        cycle_type = "cyclical_oscillation" if is_recurrent else "monotonic_trend"
        confidence = 0.75 if is_recurrent else 0.85

        return RecurrenceProfile(
            region_id=region_id,
            is_recurrent=is_recurrent,
            cycle_type=cycle_type,
            confidence=confidence,
            estimated_period_days=180 if is_recurrent else 0,
            oscillation_count=switches,
        )
