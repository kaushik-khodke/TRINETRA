"""
TRINETRA Phase 6 — Multi-Temporal Object Tracker
Tracks discrete spatial instances across chronological acquisition epochs.
"""

from typing import Dict, Any, List, Optional
import uuid
from investigation.objects.registry import DetectedObject
from investigation.objects.matching import ObjectMatcher
from investigation.objects.change import ObjectChangeClassifier, ObjectChangeItem, ObjectChangeType


class ObjectTrack:
    def __init__(self, track_id: str, category: str):
        self.track_id = track_id
        self.category = category
        self.observations: List[str] = []
        self.detections: List[DetectedObject] = []
        self.change_summary: Optional[ObjectChangeItem] = None

    def add_detection(self, det: DetectedObject) -> None:
        self.observations.append(getattr(det, "observation_id", getattr(det, "date", "obs_0")))
        self.detections.append(det)

    @property
    def status(self) -> str:
        if self.change_summary:
            return self.change_summary.change_type.value if hasattr(self.change_summary.change_type, "value") else str(self.change_summary.change_type)
        return "PERSISTENT"

    @property
    def confidence(self) -> float:
        if self.change_summary:
            return self.change_summary.confidence
        return self.detections[-1].confidence if self.detections else 0.85

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "category": self.category,
            "status": self.status,
            "confidence": self.confidence,
            "observation_count": len(self.observations),
            "observations": self.observations,
            "latest_bbox": self.detections[-1].bounding_box if self.detections else None,
            "change_summary": self.change_summary.to_dict() if self.change_summary else None,
        }


class ObjectTracker:
    """
    Builds temporal trajectories of discrete ground objects across observation pairs or series.
    """

    def __init__(self):
        self.detections_by_date: Dict[str, List[DetectedObject]] = {}

    def add_observation_detections(self, date: str, objects: List[DetectedObject]) -> None:
        self.detections_by_date[date] = objects

    def build_tracks(self) -> List[ObjectTrack]:
        dates = sorted(self.detections_by_date.keys())
        if len(dates) < 2:
            tracks: List[ObjectTrack] = []
            if dates:
                for obj in self.detections_by_date[dates[0]]:
                    t = ObjectTrack(f"trk_{obj.object_id}", obj.category)
                    t.add_detection(obj)
                    tracks.append(t)
            return tracks
        return self.track_pair(self.detections_by_date[dates[0]], self.detections_by_date[dates[1]])

    @classmethod
    def track_pair(
        cls,
        objects_a: List[DetectedObject],
        objects_b: List[DetectedObject],
    ) -> List[ObjectTrack]:
        tracks: List[ObjectTrack] = []
        matches = ObjectMatcher.match_pair(objects_a, objects_b)

        matched_a_ids = set()
        matched_b_ids = set()

        # 1. Matched objects
        for obj_a, obj_b, score in matches:
            t_id = f"trk_{uuid.uuid4().hex[:8]}"
            track = ObjectTrack(t_id, obj_a.category)
            track.add_detection(obj_a)
            track.add_detection(obj_b)
            track.change_summary = ObjectChangeClassifier.classify_pair(obj_a, obj_b, t_id)
            tracks.append(track)
            matched_a_ids.add(obj_a.object_id)
            matched_b_ids.add(obj_b.object_id)

        # 2. Orphaned objects in A (Removal Candidates)
        for obj_a in objects_a:
            if obj_a.object_id not in matched_a_ids:
                t_id = f"trk_{uuid.uuid4().hex[:8]}"
                track = ObjectTrack(t_id, obj_a.category)
                track.add_detection(obj_a)
                track.change_summary = ObjectChangeClassifier.classify_pair(obj_a, None, t_id)
                tracks.append(track)

        # 3. New objects in B (New Object Candidates)
        for obj_b in objects_b:
            if obj_b.object_id not in matched_b_ids:
                t_id = f"trk_{uuid.uuid4().hex[:8]}"
                track = ObjectTrack(t_id, obj_b.category)
                track.add_detection(obj_b)
                track.change_summary = ObjectChangeClassifier.classify_pair(None, obj_b, t_id)
                tracks.append(track)

        return tracks
