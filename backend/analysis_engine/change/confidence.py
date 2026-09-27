"""
TRINETRA Analysis Engine — Confidence Assessment
Distinguishes between:
1. Model Confidence (neural activation certainty)
2. Evidence Quality (spatial coverage, validity ratio, registration quality)
3. Overall Finding Confidence (HIGH, MEDIUM, LOW, INSUFFICIENT)
"""

from typing import Dict, Any
from analysis_engine.schemas import ConfidenceLevel


class ChangeConfidenceEvaluator:
    @staticmethod
    def evaluate(
        model_confidence: float,
        valid_pixel_ratio: float,
        contamination_ratio: float,
        changed_pixels: int,
        min_pixels_required: int = 20,
    ) -> Dict[str, Any]:
        """
        Computes composite confidence and maps to structured ConfidenceLevel.
        """
        # Evidence Quality
        evidence_quality_score = valid_pixel_ratio * (1.0 - contamination_ratio)
        if changed_pixels < min_pixels_required:
            evidence_quality_score *= 0.5

        # Overall composite score
        overall_score = (0.5 * model_confidence) + (0.5 * evidence_quality_score)

        if overall_score >= 0.80 and evidence_quality_score >= 0.70:
            level = ConfidenceLevel.HIGH
        elif overall_score >= 0.55:
            level = ConfidenceLevel.MEDIUM
        elif overall_score >= 0.30:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.INSUFFICIENT

        return {
            "model_confidence": round(model_confidence, 4),
            "evidence_quality_score": round(evidence_quality_score, 4),
            "overall_score": round(overall_score, 4),
            "level": level.value,
        }
