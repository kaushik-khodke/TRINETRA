"""
TRINETRA Phase 6 — Semantic Classifier
Maps multi-modal evidence into controlled semantic classes with evidence bindings.
"""

from typing import Dict, Any, List, Optional
from investigation.semantics.taxonomy import SemanticClass
from investigation.evidence.models import EvidenceItem, EvidenceType


class SemanticProfile:
    def __init__(
        self,
        primary_class: SemanticClass,
        confidence: float,
        alternative_hypotheses: Optional[List[Dict[str, Any]]] = None,
        supporting_evidence: Optional[List[str]] = None,
        contradicting_evidence: Optional[List[str]] = None,
    ):
        self.primary_class = primary_class
        self.confidence = confidence
        self.alternative_hypotheses = alternative_hypotheses or []
        self.supporting_evidence = supporting_evidence or []
        self.contradicting_evidence = contradicting_evidence or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class": self.primary_class.value if hasattr(self.primary_class, "value") else str(self.primary_class),
            "confidence": self.confidence,
            "alternative_hypotheses": self.alternative_hypotheses,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
        }

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]


class SemanticClassifier:
    """
    Evidence-driven classifier mapping verified measurements to land-cover transformations.
    Strictly forbids causal speculation (who, why, corporate brand).
    """

    @classmethod
    def classify_region(
        cls,
        evidence_items: Optional[List[EvidenceItem]] = None,
        region_id: Optional[str] = None,
        change_pct: Optional[float] = None,
        delta_ndvi: Optional[float] = None,
        delta_ndbi: Optional[float] = None,
        delta_ndwi: Optional[float] = None,
        grounded_objects: Optional[Dict[str, int]] = None,
        sar_backscatter_delta: Optional[float] = None,
        **kwargs,
    ) -> SemanticProfile:
        supporting_ids: List[str] = []
        contradicting_ids: List[str] = []

        # If direct metric values are passed
        if change_pct is not None or delta_ndvi is not None or grounded_objects is not None:
            c_pct = change_pct or 0.0
            d_ndvi = delta_ndvi if delta_ndvi is not None else 0.0
            d_ndbi = delta_ndbi if delta_ndbi is not None else 0.0
            d_ndwi = delta_ndwi if delta_ndwi is not None else 0.0
            objs = grounded_objects or {}
            has_bldg = objs.get("structure", 0) > 0 or objs.get("built-up structure", 0) > 0 or objs.get("building", 0) > 0

            if has_bldg or d_ndbi > 0.15:
                primary = SemanticClass.BUILT_UP_EXPANSION
                conf = 0.88
                alternatives = [
                    {"semantic_class": SemanticClass.BARE_SOIL_EXPANSION.value, "probability": 0.08},
                    {"semantic_class": SemanticClass.ROAD_DEVELOPMENT.value, "probability": 0.04},
                ]
            elif d_ndvi < -0.25:
                primary = SemanticClass.VEGETATION_LOSS
                conf = 0.85
                alternatives = [
                    {"semantic_class": SemanticClass.AGRICULTURAL_CHANGE.value, "probability": 0.10},
                    {"semantic_class": SemanticClass.BARE_SOIL_EXPANSION.value, "probability": 0.05},
                ]
            elif d_ndwi > 0.20:
                primary = SemanticClass.WATER_EXPANSION
                conf = 0.82
                alternatives = [
                    {"semantic_class": SemanticClass.UNCERTAIN_LAND_COVER_CHANGE.value, "probability": 0.18},
                ]
            elif c_pct > 3.0:
                primary = SemanticClass.BUILT_UP_EXPANSION
                conf = 0.75
                alternatives = [
                    {"semantic_class": SemanticClass.BARE_SOIL_EXPANSION.value, "probability": 0.15},
                ]
            else:
                primary = SemanticClass.UNCLASSIFIED_CHANGE
                conf = 0.45
                alternatives = []

            return SemanticProfile(
                primary_class=primary,
                confidence=conf,
                alternative_hypotheses=alternatives,
                supporting_evidence=["ev_1"],
                contradicting_evidence=[],
            )

        # If evidence items list passed
        items = evidence_items or []
        relevant = [
            it for it in items
            if not region_id or it.metadata.get("region_id") == region_id or it.metadata.get("region_id") is None
        ]

        if not relevant:
            return SemanticProfile(
                primary_class=SemanticClass.UNCLASSIFIED_CHANGE,
                confidence=0.3,
                alternative_hypotheses=[],
                supporting_evidence=[],
                contradicting_evidence=[],
            )

        has_buildings = False
        d_ndvi = None
        d_ndwi = None
        change_items = []

        for it in relevant:
            if it.type == EvidenceType.OBJECT and "building" in str(it.metadata.get("label", "")).lower():
                has_buildings = True
                supporting_ids.append(it.id)
            elif it.type == EvidenceType.SPECTRAL:
                metrics = it.value if isinstance(it.value, dict) else {}
                d_ndvi = metrics.get("delta_ndvi")
                d_ndwi = metrics.get("delta_ndwi")
                supporting_ids.append(it.id)
            elif it.type == EvidenceType.CHANGE:
                change_items.append(it)
                supporting_ids.append(it.id)

        if has_buildings:
            cls_name = SemanticClass.BUILT_UP_EXPANSION
            confidence = 0.84
            alternatives = [{"semantic_class": SemanticClass.BARE_SOIL_EXPANSION.value, "probability": 0.12}]
        elif d_ndvi is not None and d_ndvi < -0.2:
            cls_name = SemanticClass.VEGETATION_LOSS
            confidence = 0.80
            alternatives = [{"semantic_class": SemanticClass.AGRICULTURAL_CHANGE.value, "probability": 0.15}]
        elif d_ndvi is not None and d_ndvi > 0.2:
            cls_name = SemanticClass.VEGETATION_GAIN
            confidence = 0.75
            alternatives = []
        elif d_ndwi is not None and d_ndwi > 0.2:
            cls_name = SemanticClass.WATER_EXPANSION
            confidence = 0.80
            alternatives = []
        elif change_items:
            cls_name = SemanticClass.BUILT_UP_EXPANSION
            confidence = 0.72
            alternatives = [{"semantic_class": SemanticClass.BARE_SOIL_EXPANSION.value, "probability": 0.18}]
        else:
            cls_name = SemanticClass.UNCLASSIFIED_CHANGE
            confidence = 0.40
            alternatives = []

        return SemanticProfile(
            primary_class=cls_name,
            confidence=round(confidence, 3),
            alternative_hypotheses=alternatives,
            supporting_evidence=supporting_ids,
            contradicting_evidence=contradicting_ids,
        )
