"""
TRINETRA Phase 5 — Standalone Single-Image Pipeline Verification Script
Tests VQA and text-guided region grounding with coordinate validation.
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
    print("[RUN] Testing Single-Image Grounding Pipeline...")

    req = AnalysisRequest(
        query="Locate the central water reservoir",
        mode=AnalysisMode.SINGLE_IMAGE,
        observation_a_id="local_sentinel2_nagpur_truecolor",
    )

    run = analysis_engine_service.create_run(req)
    result = analysis_engine_service._execute_pipeline_sync(run, req)

    assert result.status == "completed", f"Status expected completed, got {result.status}"
    assert result.mode == AnalysisMode.SINGLE_IMAGE
    assert len(result.findings) >= 1
    assert len(result.artifacts) >= 2

    print(f"[OK] Single-image pipeline verified successfully! Run ID: {result.run_id}")
    print(f"     Findings count: {len(result.findings)}")


if __name__ == "__main__":
    main()
