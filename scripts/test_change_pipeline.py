"""
TRINETRA Phase 5 — Standalone Bi-Temporal Change Pipeline Verification Script
Executes change map generation, vectorization, and evidence assembly without UI or browser.
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
    print("[RUN] Testing Bi-Temporal Change Pipeline...")

    req = AnalysisRequest(
        query="Verify urban change detection pipeline",
        mode=AnalysisMode.BI_TEMPORAL,
        observation_a_id="local_sentinel2_nagpur_truecolor",
        observation_b_id="local_sentinel2_nagpur_falsecolor",
        aoi={
            "type": "Polygon",
            "coordinates": [[[79.0, 21.0], [79.1, 21.0], [79.1, 21.1], [79.0, 21.1], [79.0, 21.0]]],
        },
    )

    run = analysis_engine_service.create_run(req)
    result = analysis_engine_service._execute_pipeline_sync(run, req)

    assert result.status == "completed", f"Status expected completed, got {result.status}"
    assert result.mode == AnalysisMode.BI_TEMPORAL
    assert len(result.findings) >= 1, "Expected at least 1 finding"
    assert "evidence" in result.dict()
    assert len(result.artifacts) >= 2, "Expected at least 2 artifacts (regions.geojson, manifest.json)"

    print(f"[OK] Change pipeline verified successfully! Run ID: {result.run_id}")
    print(f"     Findings count: {len(result.findings)}")
    print(f"     Executive summary: {result.summary[:80]}...")


if __name__ == "__main__":
    main()
