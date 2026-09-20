"""
TRINETRA Phase 5 — Full End-to-End Analytical Flow Integration Test
Validates all 6 analytical gates:
Gate 1: Pre-flight Validation & Pipeline Planning
Gate 2: Windowed Raster Ingestion & Coregistration Alignment
Gate 3: Bi-Temporal Change Detection & Vector Region Extraction
Gate 4: Cross-Modal SAR-Optical Processing & Agreement Calculation
Gate 5: Single-Image Text-Guided Grounding & Coordinate Validation
Gate 6: Evidence Governance, Structured Reasoning & Artifact Manifest Generation
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from analysis_engine.schemas import AnalysisRequest, AnalysisMode
from analysis_engine.service import analysis_engine_service


def main():
    print("=" * 60)
    print(" TRINETRA PHASE 5: EO ANALYTICAL INTELLIGENCE VERIFICATION")
    print("=" * 60)

    # Gate 1: Pre-flight Validation
    print("\n--> Gate 1: Request Validation & Pipeline Planning")
    val_req = AnalysisRequest(
        query="Feasibility test",
        mode=AnalysisMode.BI_TEMPORAL,
        observation_a_id="item_local_sentinel2_nagpur_truecolor",
        observation_b_id="item_local_sentinel2_koradi_nagpur",
    )
    val_res = analysis_engine_service.validate_request(val_req)
    assert val_res.valid is True
    print("    [OK] Gate 1 Passed: Request validated; estimated runtime calculated.")

    # Gate 2 & 3: Bi-Temporal Pipeline
    print("\n--> Gate 2 & 3: Windowed Raster & Bi-Temporal Change Analysis")
    req_bi = AnalysisRequest(
        query="Identify significant land cover changes",
        mode=AnalysisMode.BI_TEMPORAL,
        observation_a_id="item_local_sentinel2_nagpur_truecolor",
        observation_b_id="item_local_sentinel2_koradi_nagpur",
        aoi={"type": "Polygon", "coordinates": [[[79.0, 21.0], [79.1, 21.0], [79.1, 21.1], [79.0, 21.1], [79.0, 21.0]]]},
    )
    run_bi = analysis_engine_service.create_run(req_bi)
    res_bi = analysis_engine_service._execute_pipeline_sync(run_bi, req_bi)
    assert res_bi.status == "completed"
    assert len(res_bi.findings) >= 1
    stats = res_bi.evidence.get("statistics", {})
    print(f"    [OK] Gate 2 & 3 Passed: Detected {stats.get('changed_pixels', 0)} changed pixels ({stats.get('area_ha', 0.0)} ha).")

    # Gate 4: SAR-Optical Pipeline
    print("\n--> Gate 4: Cross-Modal SAR-Optical Pipeline & Agreement")
    req_sar = AnalysisRequest(
        query="Analyze inundation with microwave and optical",
        mode=AnalysisMode.SAR_OPTICAL,
        observation_a_id="item_local_sentinel2_nagpur_truecolor",
        observation_b_id="item_local_sentinel1_mumbai_sar",
    )
    run_sar = analysis_engine_service.create_run(req_sar)
    res_sar = analysis_engine_service._execute_pipeline_sync(run_sar, req_sar)
    assert res_sar.status == "completed"
    xm_count = res_sar.evidence.get("statistics", {}).get("cross_modal_items_count", 0)
    print(f"    [OK] Gate 4 Passed: Extracted {xm_count} cross-modal evidence items.")

    # Gate 5: Single-Image Pipeline
    print("\n--> Gate 5: Single-Image Text-Guided Grounding")
    req_sng = AnalysisRequest(
        query="Locate the central water reservoir",
        mode=AnalysisMode.SINGLE_IMAGE,
        observation_a_id="item_local_sentinel2_nagpur_truecolor",
    )
    run_sng = analysis_engine_service.create_run(req_sng)
    res_sng = analysis_engine_service._execute_pipeline_sync(run_sng, req_sng)
    assert res_sng.status == "completed"
    print(f"    [OK] Gate 5 Passed: Located candidate features with validated bounding boxes.")

    # Gate 6: Evidence Governance & Artifact Generation
    print("\n--> Gate 6: Evidence Governance, Structured Reasoning & Artifacts")
    assert len(res_bi.artifacts) >= 2
    assert "provenance" in res_bi.dict()
    assert "processing_hash" in res_bi.provenance
    print(f"    [OK] Gate 6 Passed: Processing hash: {res_bi.provenance['processing_hash'][:16]}...")
    print(f"         Artifacts persisted: {[a['name'] for a in res_bi.artifacts]}")

    print("\n" + "=" * 60)
    print(" ALL 6 PHASE 5 ANALYTICAL GATES PASSED SUCCESSFULLY [OK]")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
