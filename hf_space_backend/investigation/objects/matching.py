"""
TRINETRA Phase 6 — Object Matching Engine
Multi-factor spatial, geometric, and semantic cross-temporal matching.
"""

from typing import Dict, Any, List, Optional, Tuple
from investigation.objects.registry import DetectedObject


class ObjectMatcher:
    """
    Computes bipartite associations between objects detected across two dates.
    """

    @classmethod
    def match_pair(
        cls,
        objects_a: List[DetectedObject],
        objects_b: List[DetectedObject],
        iou_threshold: float = 0.25,
    ) -> List[Tuple[DetectedObject, DetectedObject, float]]:
        matches = []
        used_b = set()

        for obj_a in objects_a:
            best_match = None
            best_score = 0.0

            for obj_b in objects_b:
                if obj_b.object_id in used_b:
                    continue
                if obj_a.category.lower() != obj_b.category.lower():
                    continue

                iou = cls.compute_iou(obj_a.bounding_box, obj_b.bounding_box)
                if iou >= iou_threshold and iou > best_score:
                    best_score = iou
                    best_match = obj_b

            if best_match and best_score >= iou_threshold:
                matches.append((obj_a, best_match, best_score))
                used_b.add(best_match.object_id)

        return matches

    @staticmethod
    def compute_iou(box_a: List[float], box_b: List[float]) -> float:
        # box: [minLon, minLat, maxLon, maxLat]
        x_left = max(box_a[0], box_b[0])
        y_bottom = max(box_a[1], box_b[1])
        x_right = min(box_a[2], box_b[2])
        y_top = min(box_a[3], box_b[3])

        if x_right < x_left or y_top < y_bottom:
            return 0.0

        intersection_area = (x_right - x_left) * (y_top - y_bottom)
        area_a = max(1e-9, (box_a[2] - box_a[0]) * (box_a[3] - box_a[1]))
        area_b = max(1e-9, (box_b[2] - box_b[0]) * (box_b[3] - box_b[1]))
        union_area = area_a + area_b - intersection_area

        return max(0.0, min(1.0, intersection_area / union_area))
