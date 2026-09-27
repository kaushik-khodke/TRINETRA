"""
TRINETRA Phase 5 — Bi-Temporal Change Analysis CLI
Runs end-to-end bi-temporal change detection directly from the terminal without a web browser.
"""

import os
import sys
import argparse

# Add backend to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from analysis_engine.schemas import AnalysisRequest, AnalysisMode
from analysis_engine.service import analysis_engine_service


def run_cli():
    parser = argparse.ArgumentParser(description="TRINETRA Bi-Temporal Change Detection CLI")
    parser.add_argument("--query", default="What changed between these observations?", help="Analytical question")
    parser.add_argument("--obs-a", default="local_sentinel2_nagpur_truecolor", help="Observation A ID")
    parser.add_argument("--obs-b", default="local_sentinel2_nagpur_falsecolor", help="Observation B ID")
    parser.add_argument("--min-lon", type=float, default=79.0)
    parser.add_argument("--min-lat", type=float, default=21.0)
    parser.add_argument("--max-lon", type=float, default=79.1)
    parser.add_argument("--max-lat", type=float, default=21.1)

    args = parser.parse_args()

    aoi = {
        "type": "Polygon",
        "coordinates": [
            [
                [args.min_lon, args.min_lat],
                [args.max_lon, args.min_lat],
                [args.max_lon, args.max_lat],
                [args.min_lon, args.max_lat],
                [args.min_lon, args.min_lat],
            ]
        ],
    }

    req = AnalysisRequest(
        query=args.query,
        mode=AnalysisMode.BI_TEMPORAL,
        observation_a_id=args.obs_a,
        observation_b_id=args.obs_b,
        aoi=aoi,
    )

    run = analysis_engine_service.create_run(req)
    result = analysis_engine_service._execute_pipeline_sync(run, req)

    stats = result.evidence.get("statistics", {})

    print("\n" + "=" * 50)
    print("           TRINETRA ANALYSIS REPORT")
    print("=" * 50)
    print(f"Run ID:        {result.run_id}")
    print(f"Mode:          {result.mode.value}")
    print(f"Status:        {result.status.upper()}")
    print(f"Observation A: {args.obs_a}")
    print(f"Observation B: {args.obs_b}")
    print("-" * 50)
    print(f"Changed Area:    {stats.get('area_ha', 0.0)} ha ({stats.get('area_m2', 0.0)} m²)")
    print(f"Change Regions:  {len(result.evidence.get('change_regions', []))}")
    print(f"Confidence:      {result.confidence.get('overall', 'MEDIUM')}")
    print("-" * 50)
    print("FINDINGS:")
    for idx, f in enumerate(result.findings):
        eids = ", ".join(f.evidence_ids) if f.evidence_ids else "None"
        print(f"  {idx+1}. {f.title} (Confidence: {f.confidence})")
        print(f"     Statement: {f.statement}")
        print(f"     Evidence:  {eids}")
    print("-" * 50)
    if result.limitations:
        print("LIMITATIONS:")
        for lim in result.limitations:
            print(f"  - [{lim.code}] {lim.description}")
        print("-" * 50)
    print("ARTIFACTS:")
    for a in result.artifacts:
        print(f"  • {a.get('name')}: {a.get('file_path')}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_cli()
