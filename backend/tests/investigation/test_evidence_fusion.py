"""
TRINETRA Phase 6 — Tests for Evidence Fusion Engine & Conflict Detection
"""

import pytest
from investigation.evidence.models import EvidenceItem, EvidenceType
from investigation.evidence.fusion import EvidenceFusionEngine
from investigation.evidence.scoring import EvidenceScorer
from investigation.evidence.validator import EvidenceConflictValidator


def test_evidence_scoring_formula():
    """
    Validates formula:
    Composite = 0.30 C_model + 0.20 Q_evidence + 0.20 S_spatial + 0.15 T_temporal + 0.15 X_cross - 0.25 P_contradiction
    """
    breakdown = EvidenceScorer.compute_composite_score(
        model_confidence=1.0,
        evidence_quality=1.0,
        spatial_consistency=1.0,
        temporal_consistency=1.0,
        cross_modal_agreement=1.0,
        has_contradictions=False,
    )
    assert pytest.approx(breakdown.composite_score, 0.01) == 1.0

    # With contradiction penalty
    breakdown_penalty = EvidenceScorer.compute_composite_score(
        model_confidence=1.0,
        evidence_quality=1.0,
        spatial_consistency=1.0,
        temporal_consistency=1.0,
        cross_modal_agreement=1.0,
        has_contradictions=True,
    )
    assert pytest.approx(breakdown_penalty.composite_score, 0.01) == 0.75
    assert breakdown_penalty.contradiction_penalty == 0.25


def test_evidence_conflict_optical_change_vs_sar_silence():
    """
    Validates explicit discrepancy detection: Optical change with high delta,
    while SAR shows stable/silence backscatter.
    """
    ev_optical = EvidenceItem(
        id="ev_opt_1",
        type=EvidenceType.CHANGE,
        source="change_detection",
        value={"change_percentage": 14.5, "change_area_ha": 3.8},
        confidence=0.90,
    )
    ev_sar = EvidenceItem(
        id="ev_sar_1",
        type=EvidenceType.SAR,
        source="sar_analysis",
        value={"delta_sigma0_db": -0.1},  # Negligible change (< 0.5 dB)
        confidence=0.88,
    )

    conflicts = EvidenceConflictValidator.detect_conflicts([ev_optical, ev_sar])
    assert len(conflicts) > 0
    conflict = conflicts[0]
    assert conflict.conflict_type == "OPTICAL_SAR_DISCREPANCY"
    assert "ev_opt_1" in [conflict.evidence_a_id, conflict.evidence_b_id]
    assert "ev_sar_1" in [conflict.evidence_a_id, conflict.evidence_b_id]


def test_evidence_fusion_graph_clustering():
    """
    Validates clustering and graph derivation across multiple evidence items.
    """
    items = [
        EvidenceItem(
            id="ev_1",
            type=EvidenceType.CHANGE,
            source="change_detection",
            bounding_box=[79.09, 21.14, 79.11, 21.16],
            value={"change_percentage": 5.2},
            confidence=0.85,
        ),
        EvidenceItem(
            id="ev_2",
            type=EvidenceType.OBJECT,
            source="grounding",
            bounding_box=[79.095, 21.145, 79.105, 21.155],
            value={"label": "structure"},
            confidence=0.88,
        ),
        EvidenceItem(
            id="ev_3",
            type=EvidenceType.SPECTRAL,
            source="spectral_analysis",
            value={"delta_ndvi": -0.28},
            confidence=0.92,
        ),
    ]

    result = EvidenceFusionEngine.fuse_evidence(items)
    assert len(result.clusters) > 0
    assert len(result.relationships) > 0
    assert any(r.relationship_type == "SPATIALLY_OVERLAPS" for r in result.relationships)
