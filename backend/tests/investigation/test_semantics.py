"""
TRINETRA Phase 6 — Tests for Semantics Subsystem & Attribution Boundaries
"""

import pytest
from investigation.semantics.taxonomy import SemanticClass
from investigation.semantics.classifier import SemanticClassifier
from investigation.semantics.event_semantics import EventSemanticsEngine
from investigation.semantics.confidence import ConfidenceExplainer


def test_semantic_classifier_built_up_expansion():
    profile = SemanticClassifier.classify_region(
        change_pct=12.5,
        delta_ndvi=-0.35,
        delta_ndbi=0.28,
        delta_ndwi=0.01,
        grounded_objects={"structure": 4},
        sar_backscatter_delta=1.5,
    )
    assert profile.primary_class == SemanticClass.BUILT_UP_EXPANSION
    assert profile.confidence >= 0.70
    assert len(profile.alternative_hypotheses) > 0


def test_semantic_classifier_vegetation_loss():
    profile = SemanticClassifier.classify_region(
        change_pct=18.0,
        delta_ndvi=-0.50,
        delta_ndbi=0.05,
        delta_ndwi=-0.02,
        grounded_objects={},
        sar_backscatter_delta=-0.8,
    )
    assert profile.primary_class == SemanticClass.VEGETATION_LOSS


def test_event_semantics_attribution_boundary():
    result = EventSemanticsEngine.classify_event(
        change_pct=8.5,
        change_ha=3.2,
        delta_ndvi=-0.30,
        delta_ndbi=0.25,
        grounding_counts={"structure": 2},
        sar_backscatter_delta=-0.3,
    )
    assert "hypotheses" in result
    assert "findings" in result
    hypotheses = result["hypotheses"]
    assert len(hypotheses) > 0

    # Ensure attribution boundaries are strictly observed (no speculation on ownership or contractor)
    for hyp in hypotheses:
        desc_lower = hyp.description.lower()
        forbidden_speculations = ["owned by", "contractor", "illegal", "permitted by", "developed by"]
        for forbidden in forbidden_speculations:
            assert forbidden not in desc_lower


def test_confidence_explainer():
    explanation = ConfidenceExplainer.explain(
        composite_score=0.88,
        breakdown={
            "model_confidence": 0.90,
            "evidence_quality": 0.92,
            "spatial_consistency": 0.88,
            "temporal_consistency": 0.85,
            "cross_modal_agreement": 0.82,
            "contradiction_penalty": 0.0,
        },
        has_conflicts=False,
    )
    assert explanation["level"] == "HIGH"
    assert "narrative" in explanation
    assert len(explanation["narrative"]) > 20
