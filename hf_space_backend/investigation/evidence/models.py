"""
TRINETRA Phase 6 — Typed Evidence Models
Canonical evidence item representations.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
import uuid
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    SPATIAL = "SPATIAL"
    TEMPORAL = "TEMPORAL"
    SPECTRAL = "SPECTRAL"
    RADIOMETRIC = "RADIOMETRIC"
    OBJECT = "OBJECT"
    CHANGE = "CHANGE"
    SAR = "SAR"
    OPTICAL = "OPTICAL"
    MODEL = "MODEL"
    METADATA = "METADATA"
    GIS_STATISTIC = "GIS_STATISTIC"


class EvidenceItem(BaseModel):
    id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    type: EvidenceType
    source: str  # e.g., "change_specialist", "grounding", "spectral_calculator"
    observation_ids: List[str] = Field(default_factory=list)
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON geometry
    bounding_box: Optional[List[float]] = None  # [minLon, minLat, maxLon, maxLat]
    value: Any = None  # Quantitative measurement (e.g. float, dict, int)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    quality: float = Field(1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if hasattr(self.type, "value") else str(self.type),
            "source": self.source,
            "observation_ids": self.observation_ids,
            "geometry": self.geometry,
            "bounding_box": self.bounding_box,
            "value": self.value,
            "confidence": self.confidence,
            "quality": self.quality,
            "metadata": self.metadata,
        }
