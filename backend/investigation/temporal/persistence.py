"""
TRINETRA Phase 6 — Persistence Analysis
Calculates temporal consistency, duration, and consecutive presence ratios.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class PersistenceReport:
    def __init__(
        self,
        region_id: str,
        first_seen: str,
        last_seen: str,
        total_observations: int,
        positive_detections: int,
        consecutive_presence: int,
        duration_days: int,
        is_persistent: bool,
    ):
        self.region_id = region_id
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.total_observations = total_observations
        self.positive_detections = positive_detections
        self.consecutive_presence = consecutive_presence
        self.duration_days = duration_days
        self.persistence_ratio = round(positive_detections / max(1, total_observations), 3)
        self.is_persistent = is_persistent

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "total_observations": self.total_observations,
            "positive_detections": self.positive_detections,
            "consecutive_presence": self.consecutive_presence,
            "duration_days": self.duration_days,
            "persistence_ratio": self.persistence_ratio,
            "is_persistent": self.is_persistent,
        }


class PersistenceEvaluator:
    """
    Evaluates how consistently a change region or object persists across multi-temporal sequences.
    """

    @classmethod
    def evaluate_region_persistence(
        cls,
        region_id: str,
        observations: List[Dict[str, Any]],
        presence_mask: Optional[List[bool]] = None,
    ) -> PersistenceReport:
        detections = []
        for idx, obs in enumerate(observations):
            det = dict(obs)
            if presence_mask and idx < len(presence_mask):
                det["detected"] = bool(presence_mask[idx])
            else:
                det["detected"] = True
            detections.append(det)
        return cls.evaluate(region_id=region_id, detections=detections)

    @classmethod
    def evaluate(
        cls,
        region_id: str,
        detections: List[Dict[str, Any]],
    ) -> PersistenceReport:
        if not detections:
            now = datetime.utcnow().isoformat()
            return PersistenceReport(
                region_id=region_id,
                first_seen=now,
                last_seen=now,
                total_observations=0,
                positive_detections=0,
                consecutive_presence=0,
                duration_days=0,
                is_persistent=False,
            )

        sorted_dets = sorted(detections, key=lambda x: x.get("datetime", ""))
        first_dt_str = sorted_dets[0].get("datetime", datetime.utcnow().isoformat())
        last_dt_str = sorted_dets[-1].get("datetime", datetime.utcnow().isoformat())

        try:
            d0 = datetime.fromisoformat(first_dt_str.replace("Z", "+00:00"))
            d1 = datetime.fromisoformat(last_dt_str.replace("Z", "+00:00"))
            duration_days = max(1, abs((d1 - d0).days))
        except Exception:
            duration_days = 30

        total = len(sorted_dets)
        positive = sum(1 for d in sorted_dets if d.get("detected", True))

        # Max consecutive detections
        consecutive = 0
        curr_consec = 0
        for d in sorted_dets:
            if d.get("detected", True):
                curr_consec += 1
                consecutive = max(consecutive, curr_consec)
            else:
                curr_consec = 0

        ratio = positive / max(1, total)
        is_persistent = ratio >= 0.60 and positive >= 2

        return PersistenceReport(
            region_id=region_id,
            first_seen=first_dt_str,
            last_seen=last_dt_str,
            total_observations=total,
            positive_detections=positive,
            consecutive_presence=consecutive,
            duration_days=duration_days,
            is_persistent=is_persistent,
        )
