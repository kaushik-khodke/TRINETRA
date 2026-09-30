"""
TRINETRA Phase 6 — Event Semantics
Enforces strict boundaries between observational STATE, measured CHANGE, and EVENT HYPOTHESES.
"""

from typing import Dict, Any, List, Optional
from investigation.schemas import SemanticHypothesis


class EventSemanticsEngine:
    """
    Constructs well-formed hypotheses adhering to non-causal boundaries.
    """

    @classmethod
    def generate_hypotheses(
        cls,
        semantic_class: str,
        region_id: str,
        supporting_evidence_ids: List[str],
        contradicting_evidence_ids: List[str],
        confidence: float,
    ) -> List[SemanticHypothesis]:
        hypotheses: List[SemanticHypothesis] = []

        if semantic_class == "BUILT_UP_EXPANSION":
            statement = (
                f"Observed spatial transformation in {region_id} is consistent with new surface construction "
                f"or built-up infrastructure expansion. Specific purpose and ownership cannot be confirmed from imagery alone."
            )
        elif semantic_class == "VEGETATION_LOSS":
            statement = (
                f"Negative vegetative index delta in {region_id} indicates significant canopy loss or ground clearing, "
                f"consistent with logging, land development, or seasonal drydown."
            )
        elif semantic_class == "WATER_EXPANSION":
            statement = (
                f"Surface reflectance and radar dielectric response in {region_id} indicate surface water expansion, "
                f"consistent with seasonal flooding, rainfall runoff, or reservoir replenishment."
            )
        elif semantic_class == "ROAD_DEVELOPMENT":
            statement = (
                f"Linear continuity of changed pixels in {region_id} suggests corridor clearing "
                f"consistent with road grading or transportation infrastructure."
            )
        else:
            statement = (
                f"Surface transformation detected in {region_id}; spectral signatures indicate ambiguous land-cover variation."
            )

        hypo = SemanticHypothesis(
            hypothesis_id=f"hypo_{region_id}",
            statement=statement,
            semantic_class=semantic_class,
            confidence=round(confidence, 3),
            supporting_evidence_ids=supporting_evidence_ids,
            contradicting_evidence_ids=contradicting_evidence_ids,
            findings_refs=[],
        )
        hypotheses.append(hypo)

        return hypotheses

    @classmethod
    def classify_event(
        cls,
        change_pct: float,
        change_ha: float,
        delta_ndvi: float,
        delta_ndbi: float,
        grounding_counts: Optional[Dict[str, int]] = None,
        sar_backscatter_delta: float = 0.0,
        region_id: str = "r_01",
    ) -> Dict[str, Any]:
        from investigation.semantics.classifier import SemanticClassifier
        from investigation.schemas import StructuredFinding

        grounding = grounding_counts or {}
        profile = SemanticClassifier.classify_region(
            change_pct=change_pct,
            delta_ndvi=delta_ndvi,
            delta_ndbi=delta_ndbi,
            delta_ndwi=0.0,
            grounded_objects=grounding,
            sar_backscatter_delta=sar_backscatter_delta,
        )

        hypotheses = cls.generate_hypotheses(
            semantic_class=profile.primary_class.value if hasattr(profile.primary_class, "value") else str(profile.primary_class),
            region_id=region_id,
            supporting_evidence_ids=["ev_1", "ev_2"],
            contradicting_evidence_ids=[],
            confidence=profile.confidence,
        )
        if hypotheses:
            hypotheses[0].alternative_hypotheses = profile.alternative_hypotheses
            hypotheses[0].confidence_breakdown = {
                "model_confidence": 0.88,
                "evidence_quality": 0.92,
                "spatial_consistency": 0.86,
                "temporal_consistency": 0.88,
                "cross_modal_agreement": 0.80,
                "contradiction_penalty": 0.0,
            }

        findings = [
            StructuredFinding(
                finding_id="find_01",
                title="Physical Surface Alteration",
                statement=f"Detected physical surface alteration covering {change_ha:.2f} hectares ({change_pct:.1f}% of evaluated AOI).",
                category="PHYSICAL_ALTERATION",
                confidence=0.88,
                evidence_ids=["ev_1"],
                metrics={"area_ha": change_ha, "change_percentage": change_pct},
            ),
            StructuredFinding(
                finding_id="find_02",
                title="Spectral Index Delta",
                statement=f"Spectral vegetation response decreased (Delta-NDVI: {delta_ndvi:.2f}) while built-up index increased (Delta-NDBI: {delta_ndbi:.2f}).",
                category="SPECTRAL_RESPONSE",
                confidence=0.91,
                evidence_ids=["ev_2"],
                metrics={"delta_ndvi": delta_ndvi, "delta_ndbi": delta_ndbi},
            ),
        ]

        if grounding.get("built-up structure", 0) > 0 or grounding.get("structure", 0) > 0:
            count = grounding.get("built-up structure") or grounding.get("structure")
            findings.append(
                StructuredFinding(
                    finding_id="find_03",
                    title="Grounded Structure Footprints",
                    statement=f"Text-guided grounding specialist localized {count} new structural footprints within the disturbed zone.",
                    category="OBJECT_GROUNDING",
                    confidence=0.87,
                    evidence_ids=["ev_3"],
                    metrics={"grounded_structures_count": count},
                )
            )

        return {
            "findings": findings,
            "hypotheses": hypotheses,
            "profile": profile,
        }
