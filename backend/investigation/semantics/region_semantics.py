"""
TRINETRA Phase 6 — Region Semantics
Assigns primary and secondary semantic candidates with explicit uncertainty reporting.
"""

from typing import Dict, Any, List, Optional
from investigation.semantics.taxonomy import SemanticClass
from investigation.evidence.models import EvidenceItem
from investigation.semantics.classifier import SemanticClassifier


class RegionSemanticProfile:
    def __init__(
        self,
        region_id: str,
        primary_class: SemanticClass,
        primary_confidence: float,
        secondary_class: Optional[SemanticClass] = None,
        secondary_confidence: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        temporal_persistence: float = 1.0,
    ):
        self.region_id = region_id
        self.primary_class = primary_class
        self.primary_confidence = primary_confidence
        self.secondary_class = secondary_class
        self.secondary_confidence = secondary_confidence
        self.evidence_ids = evidence_ids or []
        self.temporal_persistence = temporal_persistence
        self.is_uncertain = (primary_confidence - secondary_confidence) < 0.20 or primary_confidence < 0.60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "primary_class": self.primary_class.value if hasattr(self.primary_class, "value") else str(self.primary_class),
            "primary_confidence": round(self.primary_confidence, 3),
            "secondary_class": self.secondary_class.value if hasattr(self.secondary_class, "value") and self.secondary_class else (str(self.secondary_class) if self.secondary_class else None),
            "secondary_confidence": round(self.secondary_confidence, 3),
            "evidence_ids": self.evidence_ids,
            "temporal_persistence": round(self.temporal_persistence, 3),
            "is_uncertain": self.is_uncertain,
        }


class RegionSemanticsMapper:
    """
    Builds structured profiles for all detected change regions.
    """

    @classmethod
    def map_regions(
        cls,
        region_ids: List[str],
        evidence_items: List[EvidenceItem],
    ) -> List[RegionSemanticProfile]:
        profiles = []

        for rid in region_ids:
            res = SemanticClassifier.classify_region(evidence_items, region_id=rid)
            prim_cls_val = res["class"]
            prim_conf = res["confidence"]

            # Derive plausible secondary candidate for uncertainty transparency
            if prim_cls_val == SemanticClass.BUILT_UP_EXPANSION.value:
                sec_cls = SemanticClass.BARE_SOIL_EXPANSION
                sec_conf = max(0.1, round(1.0 - prim_conf - 0.1, 2))
            elif prim_cls_val == SemanticClass.VEGETATION_LOSS.value:
                sec_cls = SemanticClass.AGRICULTURAL_CHANGE
                sec_conf = max(0.1, round(1.0 - prim_conf - 0.1, 2))
            else:
                sec_cls = SemanticClass.UNCLASSIFIED_CHANGE
                sec_conf = 0.2

            profile = RegionSemanticProfile(
                region_id=rid,
                primary_class=SemanticClass(prim_cls_val),
                primary_confidence=prim_conf,
                secondary_class=sec_cls,
                secondary_confidence=sec_conf,
                evidence_ids=res["supporting_evidence"],
            )
            profiles.append(profile)

        return profiles
