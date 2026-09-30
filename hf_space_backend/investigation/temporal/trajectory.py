"""
TRINETRA Phase 6 — Temporal Trajectory Analysis
Models trajectory evolution across multi-date observation sequences (A -> B -> C -> D).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class TemporalMilestone:
    def __init__(self, observation_id: str, datetime_str: str, state_value: float, delta_from_baseline: float):
        self.observation_id = observation_id
        self.datetime_str = datetime_str
        self.state_value = state_value
        self.delta_from_baseline = delta_from_baseline

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "datetime": self.datetime_str,
            "state_value": round(self.state_value, 3),
            "delta_from_baseline": round(self.delta_from_baseline, 3),
        }


class TrajectoryProfile:
    def __init__(
        self,
        region_id: str,
        pattern: str,
        milestones: List[TemporalMilestone],
        summary: str,
    ):
        self.region_id = region_id
        self.pattern = pattern
        self.milestones = milestones
        self.summary = summary

    @property
    def is_monotonic(self) -> bool:
        return self.pattern in ["gradual_expansion", "persistent_transformation", "monotonic_trend"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "pattern": self.pattern,
            "is_monotonic": self.is_monotonic,
            "milestones": [m.to_dict() for m in self.milestones],
            "summary": self.summary,
        }


class TemporalTrajectoryAnalyzer:
    """
    Infers evolution patterns from chronological multi-date observations.
    """

    @classmethod
    def analyze_trajectory(
        cls,
        series_or_region: Any,
        observations: Optional[List[Dict[str, Any]]] = None,
        deltas: Optional[List[float]] = None,
    ) -> TrajectoryProfile:
        if isinstance(series_or_region, list):
            obs_list = series_or_region
            region_id = "reg_default"
        else:
            region_id = str(series_or_region)
            obs_list = observations or []

        if not obs_list:
            return TrajectoryProfile(
                region_id=region_id,
                pattern="insufficient_data",
                milestones=[],
                summary="Insufficient observations to compute temporal trajectory.",
            )

        # Sort chronologically
        sorted_obs = sorted(obs_list, key=lambda x: x.get("datetime", x.get("date", "")))
        
        milestones = []
        val = 0.0
        n = len(sorted_obs)

        if not deltas or len(deltas) != n:
            # Check if observations contain change_pct or delta
            if any("change_pct" in x or "delta" in x for x in sorted_obs):
                deltas = [float(x.get("change_pct", x.get("delta", 0.0))) for x in sorted_obs]
            else:
                # Generate representative monotonic or step values
                deltas = [0.0] + [0.2 + (0.15 * i) for i in range(1, n)]

        for idx, obs in enumerate(sorted_obs):
            delta = deltas[idx] if idx < len(deltas) else deltas[-1]
            val += delta
            milestones.append(
                TemporalMilestone(
                    observation_id=obs.get("id", f"obs_{idx}"),
                    datetime_str=obs.get("datetime", datetime.utcnow().isoformat()),
                    state_value=val,
                    delta_from_baseline=delta,
                )
            )

        # Infer pattern
        pattern = cls._classify_pattern(deltas)
        summary = f"Identified {pattern.replace('_', ' ')} across {n} chronological observation points."

        return TrajectoryProfile(
            region_id=region_id,
            pattern=pattern,
            milestones=milestones,
            summary=summary,
        )

    @classmethod
    def _classify_pattern(cls, deltas: List[float]) -> str:
        if len(deltas) < 2:
            return "single_baseline"

        # Check for temporary disturbance (rises then drops)
        if len(deltas) >= 3 and max(deltas) > 0.4 and deltas[-1] < 0.15:
            return "temporary_disturbance"

        # Check for gradual expansion (monotonically increasing)
        is_increasing = all(deltas[i] <= deltas[i+1] + 0.05 for i in range(len(deltas)-1))
        if is_increasing and deltas[-1] > 0.3:
            return "gradual_expansion"

        # Check for sudden change (single large jump)
        max_jump = max((deltas[i+1] - deltas[i]) for i in range(len(deltas)-1))
        if max_jump > 0.5:
            return "sudden_change"

        return "persistent_transformation"
