"""
TRINETRA Phase 5 — Cross-Modal SAR-Optical Analysis CLI
Runs joint microwave and optical analysis directly from the terminal without a web browser.
"""

import os
import sys
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from analysis_engine.schemas import AnalysisRequest, AnalysisMode
from analysis_engine.service import analysis_engine_service


def run_cli():
    parser = argparse.ArgumentParser(description="TRINETRA SAR-Optical Cross-Modal Analysis CLI")
    parser.add_argument("--query", default="Analyze this region using SAR and optical imagery.", help="Analytical question")
    parser.add_argument("--optical", default="local_sentinel2_nagpur_truecolor", help="Optical Observation ID")
    parser.add_argument("--sar", default="local_sentinel1_nagpur_sar", help="SAR Observation ID")

    args = parser.parse_args()

    req = AnalysisRequest(
        query=args.query,
        mode=AnalysisMode.SAR_OPTICAL,
        observation_a_id=args.optical,
        observation_b_id=args.sar,
    )

    run = analysis_engine_service.create_run(req)
    result = analysis_engine_service._execute_pipeline_sync(run, req)

    print("\n" + "=" * 50)
    print("        TRINETRA SAR-OPTICAL FUSION REPORT")
    print("=" * 50)
    print(f"Run ID:      {result.run_id}")
    print(f"Mode:        {result.mode.value}")
    print(f"Status:      {result.status.upper()}")
    print(f"Optical:     {args.optical}")
    print(f"SAR:         {args.sar}")
    print("-" * 50)
    print(f"Confidence:  {result.confidence.get('overall', 'MEDIUM')}")
    print("-" * 50)
    print("FINDINGS:")
    for idx, f in enumerate(result.findings):
        print(f"  {idx+1}. {f.title} (Confidence: {f.confidence})")
        print(f"     Statement: {f.statement}")
        print(f"     Evidence:  {', '.join(f.evidence_ids)}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_cli()
