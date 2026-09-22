"""
TRINETRA Phase 6 — Multi-Dimensional Evidence Scoring
Rigorous, transparent, non-averaged scoring across orthogonal dimensions.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ConfidenceBreakdown(BaseModel):
    model_confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_quality: float = Field(..., ge=0.0, le=1.0)
    spatial_support: float = Field(..., ge=0.0, le=1.0)
    temporal_support: float = Field(..., ge=0.0, le=1.0)
    cross_modal_support: float = Field(..., ge=0.0, le=1.0)
    data_quality: float = Field(..., ge=0.0, le=1.0)
    contradiction_penalty: float = Field(0.0, ge=0.0, le=1.0)
    composite_score: float = Field(..., ge=0.0, le=1.0)
    qualitative_rating: str  # "HIGH", "MEDIUM", "LOW"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_confidence": self.model_confidence,
            "evidence_quality": self.evidence_quality,
            "spatial_support": self.spatial_support,
            "temporal_support": self.temporal_support,
            "cross_modal_support": self.cross_modal_support,
            "data_quality": self.data_quality,
            "contradiction_penalty": self.contradiction_penalty,
            "composite_score": self.composite_score,
            "qualitative_rating": self.qualitative_rating,
        }


class EvidenceScorer:
    """
    Transparent mathematical evaluator of multi-dimensional evidence confidence.
    Formula:
      Composite = 0.30 * C_model + 0.20 * Q_evidence + 0.20 * S_spatial
                + 0.15 * T_temporal + 0.15 * X_cross_modal - 0.25 * P_contradiction
    Bounded strictly in [0.05, 0.98].
    """

    @classmethod
    def evaluate(
        cls,
        model_confidence: float = 0.8,
        evidence_quality: float = 0.85,
        spatial_support: float = 0.8,
        temporal_support: float = 0.7,
        cross_modal_support: float = 0.5,
        data_quality: float = 0.9,
        has_contradiction: bool = False,
    ) -> ConfidenceBreakdown:
        penalty = 0.25 if has_contradiction else 0.0

        raw_score = (
            (0.30 * model_confidence)
            + (0.20 * evidence_quality)
            + (0.20 * spatial_support)
            + (0.15 * temporal_support)
            + (0.15 * cross_modal_support)
            - penalty
        )

        composite = max(0.05, min(1.0, round(raw_score, 3)))

        if composite >= 0.75 and not has_contradiction:
            rating = "HIGH"
        elif composite >= 0.50:
            rating = "MEDIUM"
        else:
            rating = "LOW"

        return ConfidenceBreakdown(
            model_confidence=round(model_confidence, 3),
            evidence_quality=round(evidence_quality, 3),
            spatial_support=round(spatial_support, 3),
            temporal_support=round(temporal_support, 3),
            cross_modal_support=round(cross_modal_support, 3),
            data_quality=round(data_quality, 3),
            contradiction_penalty=penalty,
            composite_score=composite,
            qualitative_rating=rating,
        )

    @classmethod
    def compute_composite_score(
        cls,
        model_confidence: float = 0.8,
        evidence_quality: float = 0.85,
        spatial_consistency: float = 0.8,
        temporal_consistency: float = 0.7,
        cross_modal_agreement: float = 0.5,
        data_quality: float = 0.9,
        has_contradictions: bool = False,
    ) -> ConfidenceBreakdown:
        return cls.evaluate(
            model_confidence=model_confidence,
            evidence_quality=evidence_quality,
            spatial_support=spatial_consistency,
            temporal_support=temporal_consistency,
            cross_modal_support=cross_modal_agreement,
            data_quality=data_quality,
            has_contradiction=has_contradictions,
        )
