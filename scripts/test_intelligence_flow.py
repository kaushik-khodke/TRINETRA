"""
TRINETRA Phase 7 — Verification Script: End-to-End Intelligence Flow
Validates ingestion of findings into canonical events, regional assignment,
provenance recording, and database persistence.
"""

import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from intelligence.models import PersistentFinding, CanonicalRegion, EventState
from intelligence.repository import IntelligenceRepository
from intelligence.service import IntelligenceService


def run_flow_test():
    print("================================================================")
    print("  TRINETRA Phase 7: Persistent EO Intelligence Flow Test")
    print("================================================================")

    # 1. Initialize isolated in-memory repository & service
    repo = IntelligenceRepository(db_path=":memory:")
    service = IntelligenceService(repo=repo)
    print("✓ Initialized IntelligenceRepository and IntelligenceService (in-memory mode)")

    # 2. Ingest first finding
    finding_1 = PersistentFinding(
        finding_id="find_test_nagpur_01",
        investigation_id="inv_demo_nagpur_001",
        type="vegetation_loss",
        label="Severe vegetation depletion observed near agricultural parcel",
        geometry={"type": "Polygon", "coordinates": [[[79.05, 21.12], [79.08, 21.12], [79.08, 21.15], [79.05, 21.15], [79.05, 21.12]]]},
        bounding_box=[79.05, 21.12, 79.08, 21.15],
        confidence=0.88,
        evidence_ids=["evi_ndvi_drop_01"],
        observation_ids=["obs_s2_nagpur_t1", "obs_s2_nagpur_t2"],
        metrics={"delta_ndvi": -0.42, "area_ha": 3.4},
        semantic_class="vegetation_loss",
    )

    events_1 = service.ingest_findings([finding_1])
    assert len(events_1) == 1, "Expected 1 event generated"
    evt1 = events_1[0]
    print(f"✓ Ingested finding 1 -> Event '{evt1.event_id}' ('{evt1.title}')")
    print(f"  State: {evt1.state.value}, Confidence: {evt1.confidence:.2f}, Semantic: {evt1.semantic_class}")
    assert evt1.state == EventState.OBSERVED, f"Expected OBSERVED, got {evt1.state}"

    # 3. Ingest corroborating SAR finding in overlapping region
    finding_2 = PersistentFinding(
        finding_id="find_test_nagpur_02",
        investigation_id="inv_demo_nagpur_002",
        type="vegetation_loss",
        label="Cross-modal corroboration: Radar backscatter decrease in vegetation zone",
        geometry={"type": "Polygon", "coordinates": [[[79.055, 21.125], [79.082, 21.125], [79.082, 21.152], [79.055, 21.152], [79.055, 21.125]]]},
        bounding_box=[79.055, 21.125, 79.082, 21.152],
        confidence=0.91,
        evidence_ids=["evi_sar_drop_02"],
        observation_ids=["obs_s1_nagpur_sar_t2"],
        metrics={"delta_vh_db": -2.8, "cross_modal_agreement": 0.89},
        semantic_class="vegetation_loss",
    )

    events_2 = service.ingest_findings([finding_2])
    assert len(events_2) == 1
    evt2 = events_2[0]
    print(f"✓ Ingested finding 2 -> Corroborated Event '{evt2.event_id}'")
    print(f"  State: {evt2.state.value}, Confidence: {evt2.confidence:.2f}")
    assert evt2.event_id == evt1.event_id, "Corroborating finding should update the existing canonical event"
    assert evt2.state == EventState.CORROBORATED, f"Expected CORROBORATED state after multi-evidence corroboration, got {evt2.state}"
    assert len(evt2.supporting_findings) == 2, "Expected 2 supporting findings recorded"

    # 4. Verify canonical region persistence
    regions = repo.list_regions()
    print(f"✓ Canonical Regions persisted: {len(regions)}")
    assert len(regions) >= 1
    reg = regions[0]
    print(f"  Canonical Region '{reg.canonical_region_id}' ({reg.name}), bbox: {reg.bounding_box}")

    # 5. Verify repository query
    all_events = repo.list_events()
    print(f"✓ Total canonical events in index: {len(all_events)}")
    assert len(all_events) == 1

    print("\n>>> ALL INTELLIGENCE FLOW VERIFICATIONS PASSED SUCCESSFULLY! <<<\n")


if __name__ == "__main__":
    run_flow_test()
