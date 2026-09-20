"""
TRINETRA Analysis Engine — Evidence Sufficiency Gate
Determines if an EvidencePack contains sufficient verified data to warrant full LLM reasoning.
"""

from typing import Tuple
from analysis_engine.evidence.models import EvidencePack
from analysis_engine.schemas import ConfidenceLevel


class EvidenceSufficiencyGate:
    @staticmethod
    def evaluate_sufficiency(pack: EvidencePack) -> Tuple[ConfidenceLevel, bool]:
        """
        Returns (confidence_level, should_call_llm).
        """
        stats = pack.statistics

        # If zero evidence items and zero valid pixels
        if stats.get("total_valid_pixels", 1) == 0:
            return ConfidenceLevel.INSUFFICIENT, False

        # Bi-temporal checks
        if pack.mode == "BI_TEMPORAL":
            changed_pixels = stats.get("changed_pixels", 0)
            if changed_pixels == 0:
                # No change detected: sufficient evidence of stability!
                return ConfidenceLevel.HIGH, True
            if len(pack.change_regions) == 0:
                return ConfidenceLevel.LOW, False
            return ConfidenceLevel.MEDIUM, True

        # SAR-Optical checks
        if pack.mode == "SAR_OPTICAL":
            if not pack.cross_modal_items:
                return ConfidenceLevel.INSUFFICIENT, False
            return ConfidenceLevel.MEDIUM, True

        # Single-image checks
        if pack.mode == "SINGLE_IMAGE":
            if not pack.grounding_detections and not stats.get("answer"):
                return ConfidenceLevel.INSUFFICIENT, False
            return ConfidenceLevel.HIGH, True

        return ConfidenceLevel.MEDIUM, True
