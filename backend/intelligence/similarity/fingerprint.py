"""
TRINETRA Phase 7 — Structured EO Fingerprinting
Builds multi-attribute spatial, spectral, temporal, and semantic fingerprints for similarity search.
"""

import math
from typing import Dict, Any, List, Optional
from intelligence.models import PersistentFinding, EOEvent


class EOFingerprint:
    """
    Normalized multi-dimensional fingerprint representing an Earth Observation entity.
    """

    SEMANTIC_ENCODING = {
        "BUILT_UP_EXPANSION": 1.0,
        "CONSTRUCTION": 0.9,
        "SURFACE_INFRASTRUCTURE": 0.8,
        "VEGETATION_LOSS": -1.0,
        "DEFORESTATION": -0.9,
        "AGRICULTURAL_DECLINE": -0.8,
        "WATER_BODY_DYNAMICS": 0.0,
        "FLOOD_EXPANSION": 0.1,
        "GENERAL_CHANGE": 0.5,
    }

    def __init__(
        self,
        entity_id: str,
        semantic_class: str,
        area_ha: float = 1.0,
        aspect_ratio: float = 1.0,
        change_magnitude: float = 5.0,
        confidence: float = 0.8,
        persistence_score: float = 0.5,
    ):
        self.entity_id = entity_id
        self.semantic_class = semantic_class
        self.area_ha = max(0.01, area_ha)
        self.aspect_ratio = max(0.1, min(10.0, aspect_ratio))
        self.change_magnitude = max(0.1, change_magnitude)
        self.confidence = max(0.05, min(1.0, confidence))
        self.persistence_score = max(0.0, min(1.0, persistence_score))

        # 5-element normalized feature vector: [log_area, aspect_ratio/5, magnitude/20, confidence, persistence]
        log_area = math.log10(self.area_ha + 1.0) / 3.0  # normalize up to 1000 ha
        norm_aspect = self.aspect_ratio / 5.0
        norm_mag = min(1.0, self.change_magnitude / 20.0)

        self.vector: List[float] = [
            round(log_area, 4),
            round(norm_aspect, 4),
            round(norm_mag, 4),
            round(self.confidence, 4),
            round(self.persistence_score, 4),
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "semantic_class": self.semantic_class,
            "area_ha": round(self.area_ha, 3),
            "aspect_ratio": round(self.aspect_ratio, 3),
            "change_magnitude": round(self.change_magnitude, 3),
            "confidence": round(self.confidence, 3),
            "persistence_score": round(self.persistence_score, 3),
            "vector": self.vector,
        }

    @classmethod
    def from_finding(cls, finding: PersistentFinding) -> "EOFingerprint":
        bbox = finding.bounding_box or [0, 0, 0, 0]
        w = max(0.0001, abs(bbox[2] - bbox[0])) if len(bbox) >= 4 else 0.01
        h = max(0.0001, abs(bbox[3] - bbox[1])) if len(bbox) >= 4 else 0.01
        aspect = w / h

        area_ha = float(finding.metrics.get("change_area_ha", finding.metrics.get("area_ha", 2.5)))
        mag = float(finding.metrics.get("change_percentage", 5.0))

        return cls(
            entity_id=finding.finding_id,
            semantic_class=finding.semantic_class,
            area_ha=area_ha,
            aspect_ratio=aspect,
            change_magnitude=mag,
            confidence=finding.confidence,
            persistence_score=0.6,
        )

    @classmethod
    def from_event(cls, event: EOEvent) -> "EOFingerprint":
        bbox = event.bounding_box or [0, 0, 0, 0]
        w = max(0.0001, abs(bbox[2] - bbox[0])) if len(bbox) >= 4 else 0.01
        h = max(0.0001, abs(bbox[3] - bbox[1])) if len(bbox) >= 4 else 0.01
        aspect = w / h

        area_ha = float(event.metadata.get("total_area_ha", 5.0))
        mag = float(event.metadata.get("change_percentage", 8.0))
        persist = float(event.confidence_dimensions.get("temporal_persistence", 0.7))

        return cls(
            entity_id=event.event_id,
            semantic_class=event.semantic_class,
            area_ha=area_ha,
            aspect_ratio=aspect,
            change_magnitude=mag,
            confidence=event.confidence,
            persistence_score=persist,
        )
