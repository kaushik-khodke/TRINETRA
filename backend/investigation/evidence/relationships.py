"""
TRINETRA Phase 6 — Evidence Relationships
Explicit semantic and topological edges between evidence tokens.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class RelationshipType(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CORROBORATES = "CORROBORATES"
    DERIVED_FROM = "DERIVED_FROM"
    TEMPORALLY_PRECEDES = "TEMPORALLY_PRECEDES"
    SPATIALLY_OVERLAPS = "SPATIALLY_OVERLAPS"
    SAME_REGION = "SAME_REGION"
    SAME_OBJECT = "SAME_OBJECT"


class EvidenceRelationship(BaseModel):
    source_id: str
    target_id: str
    relationship: RelationshipType
    weight: float = Field(1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def relationship_type(self) -> str:
        return self.relationship.value if hasattr(self.relationship, "value") else str(self.relationship)

    @property
    def confidence(self) -> float:
        return self.weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship": self.relationship_type,
            "relationship_type": self.relationship_type,
            "weight": self.weight,
            "confidence": self.weight,
            "metadata": self.metadata,
        }
