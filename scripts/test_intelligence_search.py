"""
TRINETRA Phase 7 — Verification Script: Semantic Search & Similarity Index
Validates natural language search parsing, multi-modal filtering,
relevance scoring, and multi-dimensional mathematical fingerprint similarity.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from intelligence.models import PersistentFinding, EOEvent, EventState
from intelligence.schemas import SearchRequest
from intelligence.repository import IntelligenceRepository
from intelligence.service import IntelligenceService
from intelligence.similarity.fingerprint import EOFingerprint
from intelligence.similarity.similarity import SimilarityScorer


def run_search_test():
    print("================================================================")
    print("  TRINETRA Phase 7: Semantic Search & Similarity Verification")
    print("================================================================")

    repo = IntelligenceRepository(db_path=":memory:")
    service = IntelligenceService(repo=repo)

    # 1. Ingest distinct semantic events
    print("[1] Ingesting diverse EO events...")
    e1 = EOEvent(
        event_id="evt_veg_01",
        title="Canopy Depletion & Vegetation Clearing",
        canonical_region_id="reg_forest_01",
        semantic_class="vegetation_loss",
        state=EventState.CORROBORATED,
        confidence=0.92,
        bounding_box=[78.10, 20.50, 78.15, 20.55],
    )
    e2 = EOEvent(
        event_id="evt_urban_02",
        title="Industrial Warehouse Construction",
        canonical_region_id="reg_industrial_02",
        semantic_class="built_up",
        state=EventState.PERSISTENT,
        confidence=0.88,
        bounding_box=[77.20, 28.50, 77.25, 28.55],
    )
    e3 = EOEvent(
        event_id="evt_water_03",
        title="Reservoir Surface Water Contraction",
        canonical_region_id="reg_lake_03",
        semantic_class="water_body",
        state=EventState.OBSERVED,
        confidence=0.79,
        bounding_box=[76.80, 15.20, 76.85, 15.25],
    )
    repo.save_event(e1)
    repo.save_event(e2)
    repo.save_event(e3)

    # Ingest findings
    f1 = PersistentFinding(
        finding_id="find_veg_101",
        investigation_id="inv_001",
        type="vegetation_loss",
        label="NDVI drop > 0.35 across 12 hectares of dense canopy",
        confidence=0.94,
        metrics={"area_ha": 12.0, "delta_ndvi": -0.4},
        semantic_class="vegetation_loss",
        bounding_box=[78.11, 20.51, 78.14, 20.54],
    )
    repo.save_finding(f1)
    print("✓ Test dataset populated.")

    # 2. Test natural language search
    print("\n[2] Executing Natural Language Semantic Queries...")
    query_text = "Find persistent built up or warehouse expansion"
    req = SearchRequest(query=query_text, limit=10)
    res = service.search(req)

    print(f"Query: '{query_text}' -> Found {res.total} results")
    assert res.total >= 1
    top_hit = res.results[0]
    print(f"✓ Top Hit: [{top_hit.type.upper()}] '{top_hit.title}' (Score: {top_hit.score:.2f})")
    assert top_hit.id == "evt_urban_02", "Expected built-up event to rank #1"
    print(f"  Match reasons: {top_hit.match_reasons}")

    # Query 2: Vegetation loss
    req2 = SearchRequest(query="vegetation canopy loss", limit=10)
    res2 = service.search(req2)
    print(f"\nQuery: 'vegetation canopy loss' -> Found {res2.total} results")
    assert res2.total >= 1
    veg_hit = res2.results[0]
    print(f"✓ Top Hit: [{veg_hit.type.upper()}] '{veg_hit.title}' (Score: {veg_hit.score:.2f})")
    assert "veg" in veg_hit.id

    # 3. Test mathematical similarity
    print("\n[3] Testing Mathematical EO Fingerprint Similarity...")
    fp1 = EOFingerprint(
        entity_id="test_veg_a",
        semantic_class="vegetation_loss",
        area_ha=10.0,
        aspect_ratio=1.5,
        change_magnitude=4.2,
        confidence=0.90,
        persistence_score=0.85,
    )
    fp2 = EOFingerprint(
        entity_id="test_veg_b",
        semantic_class="vegetation_loss",
        area_ha=11.2,
        aspect_ratio=1.6,
        change_magnitude=4.0,
        confidence=0.88,
        persistence_score=0.82,
    )
    fp_diff = EOFingerprint(
        entity_id="test_water_c",
        semantic_class="water_body",
        area_ha=150.0,
        aspect_ratio=4.0,
        change_magnitude=12.0,
        confidence=0.60,
        persistence_score=0.20,
    )

    score_high, level_high, factors_high = SimilarityScorer.compare_fingerprints(fp1, fp2)
    score_low, level_low, factors_low = SimilarityScorer.compare_fingerprints(fp1, fp_diff)

    print(f"✓ Homologous Vegetation similarity: {score_high:.3f} ({level_high})")
    print(f"  Match factors: {factors_high}")
    print(f"✓ Heterologous Water vs Veg similarity: {score_low:.3f} ({level_low})")
    assert score_high > score_low
    assert score_high >= 0.70

    print("\n>>> ALL SEMANTIC SEARCH & SIMILARITY TESTS PASSED! <<<\n")


if __name__ == "__main__":
    run_search_test()
