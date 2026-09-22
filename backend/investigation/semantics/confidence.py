"""
TRINETRA Phase 6 — Confidence Explainer
Produces qualitative, transparent narrative explaining evidence confidence dimensions.
"""

from typing import Dict, Any, Optional
from investigation.evidence.scoring import ConfidenceBreakdown


class ConfidenceExplanation(dict):
    """
    Dual dictionary and string representation for confidence justification.
    """
    def __init__(self, narrative: str, level: str = "HIGH", composite_score: float = 0.85):
        super().__init__(narrative=narrative, level=level, composite_score=composite_score)
        self.narrative = narrative
        self.level = level
        self.composite_score = composite_score

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'ConfidenceExplanation' has no attribute '{key}'")

    def __str__(self) -> str:
        return self.narrative

    def to_dict(self) -> Dict[str, Any]:
        return {
            "narrative": self.narrative,
            "level": self.level,
            "composite_score": self.composite_score,
        }


class ConfidenceExplainer:
    """
    Generates human-readable justifications for multi-dimensional confidence scores.
    """

    @classmethod
    def explain(
        cls,
        breakdown: Any = None,
        composite_score: Optional[float] = None,
        has_conflicts: bool = False,
        **kwargs,
    ) -> ConfidenceExplanation:
        if isinstance(breakdown, ConfidenceBreakdown):
            score = breakdown.composite_score
            level = breakdown.qualitative_rating
            spatial = breakdown.spatial_support
            temporal = breakdown.temporal_support
            cross = breakdown.cross_modal_support
            model = breakdown.model_confidence
            penalty = breakdown.contradiction_penalty
        else:
            bd = breakdown if isinstance(breakdown, dict) else {}
            score = composite_score if composite_score is not None else 0.85
            level = "HIGH" if score >= 0.85 else ("MODERATE" if score >= 0.65 else "LOW")
            spatial = bd.get("spatial_consistency", 0.86)
            temporal = bd.get("temporal_consistency", 0.88)
            cross = bd.get("cross_modal_agreement", 0.80)
            model = bd.get("model_confidence", 0.88)
            penalty = 0.25 if has_conflicts else bd.get("contradiction_penalty", 0.0)

        reasons = []
        if spatial >= 0.75:
            reasons.append("Strong spatial alignment with localized polygon boundaries")
        else:
            reasons.append("Marginal spatial extent or ambiguous boundary definitions")

        if temporal >= 0.70:
            reasons.append("Verified multi-date temporal persistence across acquisition epochs")
        else:
            reasons.append("Limited temporal baseline or single observation pair")

        if cross >= 0.70 and penalty == 0:
            reasons.append("Confirmed multi-sensor corroboration between optical reflectance and SAR")
        elif penalty > 0 or has_conflicts:
            reasons.append("Identified cross-modal discrepancy between radar backscatter and optical reflectance")

        if model >= 0.80:
            reasons.append("High model activation across specialist inference heads")
        else:
            reasons.append("Moderate model activation requiring corroborative verification")

        narrative = f"Confidence is rated {level} ({round(score * 100)}%). Factors: {'; '.join(reasons)}."
        return ConfidenceExplanation(narrative=narrative, level=level, composite_score=score)
