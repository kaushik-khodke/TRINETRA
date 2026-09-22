"""
TRINETRA Phase 6 — Detected Object Entity & Registry
Maintains atomic object instances identified across temporal observations.
"""

from typing import Dict, Any, List, Optional
import uuid
from pydantic import BaseModel, Field


class DetectedObject(BaseModel):
    object_id: str = Field(default_factory=lambda: f"obj_{uuid.uuid4().hex[:8]}")
    observation_id: str = "obs_default"
    category: str = "structure"  # e.g., "building", "aircraft", "vessel", "storage_tank"
    bounding_box: List[float] = Field(..., min_length=4, max_length=4)  # [minLon, minLat, maxLon, maxLat]
    area_m2: float = Field(default=100.0, ge=0.0)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    date: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object_id": self.object_id,
            "observation_id": self.observation_id,
            "category": self.category,
            "bounding_box": self.bounding_box,
            "area_m2": round(self.area_m2, 2),
            "confidence": round(self.confidence, 3),
            "metadata": self.metadata,
        }


class ObjectRegistry:
    """
    In-memory store of object instances keyed by observation ID.
    """
    def __init__(self):
        self._objects_by_obs: Dict[str, List[DetectedObject]] = {}

    def register(self, obj: DetectedObject) -> None:
        if obj.observation_id not in self._objects_by_obs:
            self._objects_by_obs[obj.observation_id] = []
        self._objects_by_obs[obj.observation_id].append(obj)

    def get_for_observation(self, observation_id: str) -> List[DetectedObject]:
        return self._objects_by_obs.get(observation_id, [])

    def all_objects(self) -> List[DetectedObject]:
        res = []
        for lst in self._objects_by_obs.values():
            res.extend(lst)
        return res
