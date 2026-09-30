"""
TRINETRA Phase 6 — Object Change Classifier
Infers object-level transformations with uncertainty preservation and occlusion defense.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from investigation.objects.registry import DetectedObject


class ObjectChangeType(str, Enum):
    NEW_OBJECT_CANDIDATE = "NEW_OBJECT_CANDIDATE"
    REMOVAL_CANDIDATE = "REMOVAL_CANDIDATE"
    PERSISTENT = "PERSISTENT"
    EXPANDED = "EXPANDED"
    REDUCED = "REDUCED"
    SHIFTED = "SHIFTED"
    UNCERTAIN = "UNCERTAIN"


class ObjectChangeItem:
    def __init__(
        self,
        track_id: str,
        category: str,
        change_type: ObjectChangeType,
        confidence: float,
        initial_area_m2: float,
        final_area_m2: float,
        bounding_box: List[float],
        caveat: Optional[str] = None,
    ):
        self.track_id = track_id
        self.category = category
        self.change_type = change_type
        self.confidence = confidence
        self.initial_area_m2 = initial_area_m2
        self.final_area_m2 = final_area_m2
        self.bounding_box = bounding_box
        self.caveat = caveat

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "category": self.category,
            "change_type": self.change_type.value if hasattr(self.change_type, "value") else str(self.change_type),
            "confidence": round(self.confidence, 3),
            "initial_area_m2": round(self.initial_area_m2, 1),
            "final_area_m2": round(self.final_area_m2, 1),
            "bounding_box": self.bounding_box,
            "caveat": self.caveat,
        }


class ObjectChangeClassifier:
    """
    Classifies lifecycle transformations between matched or orphaned objects.
    """

    @classmethod
    def classify_pair(
        cls,
        obj_a: Optional[DetectedObject],
        obj_b: Optional[DetectedObject],
        track_id: str,
    ) -> ObjectChangeItem:
        if obj_a is None and obj_b is not None:
            return ObjectChangeItem(
                track_id=track_id,
                category=obj_b.category,
                change_type=ObjectChangeType.NEW_OBJECT_CANDIDATE,
                confidence=min(obj_b.confidence, 0.80),
                initial_area_m2=0.0,
                final_area_m2=obj_b.area_m2,
                bounding_box=obj_b.bounding_box,
                caveat="Requires secondary corroboration to eliminate shadow/registration artifacts.",
            )

        if obj_a is not None and obj_b is None:
            return ObjectChangeItem(
                track_id=track_id,
                category=obj_a.category,
                change_type=ObjectChangeType.REMOVAL_CANDIDATE,
                confidence=min(obj_a.confidence, 0.75),
                initial_area_m2=obj_a.area_m2,
                final_area_m2=0.0,
                bounding_box=obj_a.bounding_box,
                caveat="Absence may be caused by cloud obscuration or contrast attenuation rather than true demolition.",
            )

        # Matched pair
        area_a = obj_a.area_m2
        area_b = obj_b.area_m2
        area_ratio = area_b / max(1.0, area_a)

        if area_ratio > 1.25:
            chg = ObjectChangeType.EXPANDED
        elif area_ratio < 0.75:
            chg = ObjectChangeType.REDUCED
        else:
            chg = ObjectChangeType.PERSISTENT

        return ObjectChangeItem(
            track_id=track_id,
            category=obj_a.category,
            change_type=chg,
            confidence=round((obj_a.confidence + obj_b.confidence) / 2.0, 3),
            initial_area_m2=area_a,
            final_area_m2=area_b,
            bounding_box=obj_b.bounding_box,
        )
