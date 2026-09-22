"""
Unit tests for Similarity Subsystem.
Tests 5D fingerprint generation, cosine vector comparison, match explanation factors, and LocalSimilarityIndex.
"""

import pytest
from intelligence.models import EOEvent, PersistentFinding, EventState
from intelligence.similarity.fingerprint import EOFingerprint
from intelligence.similarity.similarity import SimilarityScorer, cosine_similarity
from intelligence.similarity.index import LocalSimilarityIndex


def test_fingerprint_generation():
    event = EOEvent(
        event_id="evt_sim_01",
        title="Industrial Expansion",
        canonical_region_id="reg_01",
        semantic_class="BUILT_UP_EXPANSION",
        state=EventState.CORROBORATED,
        confidence=0.88,
        bounding_box=[79.0, 21.0, 79.1, 21.1],
    )
    fp = EOFingerprint.from_event(event)
    assert len(fp.vector) == 5
    assert 0.0 <= fp.vector[0] <= 1.0  # Normalized confidence
    assert fp.semantic_class == "BUILT_UP_EXPANSION"


def test_similarity_calculator():
    fp1 = EOFingerprint(
        entity_id="item_01",
        semantic_class="CONSTRUCTION",
        area_ha=5.0,
        change_magnitude=8.0,
        confidence=0.88,
    )
    # Very similar vector
    fp2 = EOFingerprint(
        entity_id="item_02",
        semantic_class="CONSTRUCTION",
        area_ha=5.2,
        change_magnitude=8.2,
        confidence=0.85,
    )
    # Dissimilar vector with different class
    fp3 = EOFingerprint(
        entity_id="item_03",
        semantic_class="WATER_BODY_VARIATION",
        area_ha=150.0,
        change_magnitude=1.0,
        confidence=0.4,
    )

    score_12, rationale_12, factors_12 = SimilarityScorer.compare_fingerprints(fp1, fp2)
    score_13, rationale_13, factors_13 = SimilarityScorer.compare_fingerprints(fp1, fp3)

    assert score_12 > 0.80
    assert score_13 < 0.70
    assert score_12 > score_13
    assert any("semantic class" in f.lower() for f in factors_12)


def test_local_similarity_index():
    index = LocalSimilarityIndex()

    fp_target = EOFingerprint(
        entity_id="target",
        semantic_class="INFRASTRUCTURE",
        area_ha=10.0,
        confidence=0.9,
    )
    fp_close = EOFingerprint(
        entity_id="close",
        semantic_class="INFRASTRUCTURE",
        area_ha=10.5,
        confidence=0.88,
    )
    fp_far = EOFingerprint(
        entity_id="far",
        semantic_class="WATER_BODY_DYNAMICS",
        area_ha=200.0,
        confidence=0.3,
    )

    index.insert(fp_close.entity_id, fp_close)
    index.insert(fp_far.entity_id, fp_far)

    results = index.search(fp_target, top_k=2)
    assert len(results) == 2
    assert results[0][0] == "close"
    assert results[0][1] > results[1][1]
