"""
TRINETRA Phase 5 — Standalone Cross-Modal SAR-Optical Pipeline Verification Script
Tests modality-aware preprocessing and cross-modal evidence generation.
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
    print("[RUN] Testing Cross-Modal SAR-Optical Pipeline...")

    req = AnalysisRequest(
        query="Analyze inundation using SAR and optical sensors",
        mode=AnalysisMode.SAR_OPTICAL,
        observation_a_id="local_sentinel2_nagpur_truecolor",
        observation_b_id="local_sentinel1_nagpur_sar",
    )

    run = analysis_engine_service.create_run(req)
    result = analysis_engine_service._execute_pipeline_sync(run, req)

    assert result.status == "completed", f"Status expected completed, got {result.status}"
    assert result.mode == AnalysisMode.SAR_OPTICAL
    assert len(result.findings) >= 1
    assert len(result.artifacts) >= 2

    print(f"[OK] SAR-Optical pipeline verified successfully! Run ID: {result.run_id}")
    print(f"     Findings count: {len(result.findings)}")
    print(f"     Cross-modal items count: {result.evidence.get('statistics', {}).get('cross_modal_items_count')}")


if __name__ == "__main__":
    main()
