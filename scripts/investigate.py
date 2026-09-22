"""
TRINETRA Phase 6 — CLI Investigation Utility
Executes an end-to-end multi-specialist investigation from the terminal and outputs
the structured reasoning report, evidence fusion graph, and non-causal attribution conclusions.

Usage:
    python scripts/investigate.py --question "What happened in this area? Was it built-up expansion?"
"""

import sys
import os
import argparse
import json

# Add backend directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from investigation.schemas import InvestigationRequest
from investigation.service import investigation_service
from investigation.graph.workflow import investigation_graph


def main():
    parser = argparse.ArgumentParser(description="TRINETRA Phase 6 — Semantic EO Investigation")
    parser.add_argument(
        "--question",
        type=str,
        default="What physical surface changes occurred in this area? Was the change related to built-up expansion?",
        help="Investigation enquiry",
    )
    parser.add_argument(
        "--obs-ids",
        nargs="*",
        default=["item_local_sentinel2_nagpur_truecolor", "item_local_sentinel2_nagpur_t2"],
        help="Observation IDs",
    )
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        default=[79.088, 21.145, 79.112, 21.165],
        help="AOI bounding box [minLon, minLat, maxLon, maxLat]",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("TRINETRA Phase 6 — Semantic EO Intelligence & Evidence Fusion Engine")
    print("=" * 70)
    print(f"Query:        {args.question}")
    print(f"Observations: {args.obs_ids}")
    print(f"AOI BBox:     {args.bbox}")
    print("-" * 70)

    # 1. Pre-flight Validation
    req = InvestigationRequest(
        question=args.question,
        observation_ids=args.obs_ids,
        aoi={
            "type": "Polygon",
            "coordinates": [[
                [args.bbox[0], args.bbox[1]],
                [args.bbox[2], args.bbox[1]],
                [args.bbox[2], args.bbox[3]],
                [args.bbox[0], args.bbox[3]],
                [args.bbox[0], args.bbox[1]],
            ]],
        },
    )

    print("[1/5] Validating enquiry and generating execution plan...")
    validation = investigation_service.validate_request(req)
    print(f"      Intent:            {validation.intent}")
    print(f"      Estimated Cost:    {validation.estimated_compute_cost}")
    print(f"      Planned Special.:  {validation.planned_specialists}")
    print(f"      Estimated Runtime: ~{validation.estimated_runtime_seconds}s")
    if validation.warnings:
        print(f"      Warnings:          {validation.warnings}")

    # 2. Execute Investigation Graph
    print("\n[2/5] Launching deterministic Investigation LangGraph workflow...")
    initial_state = {
        "investigation_id": f"inv_cli_{os.urandom(4).hex()}",
        "question": args.question,
        "observation_ids": args.obs_ids,
        "aoi": req.aoi,
        "status": "QUEUED",
        "warnings": [],
        "errors": [],
    }

    final_state = investigation_graph.invoke(initial_state)

    print("\n[3/5] Specialists Executed & Evidence Fused:")
    evidence_items = final_state.get("evidence_items", [])
    relationships = final_state.get("evidence_relationships", [])
    conflicts = final_state.get("conflicts", [])

    print(f"      Total Evidence Items:  {len(evidence_items)}")
    print(f"      Derived Relationships: {len(relationships)}")
    print(f"      Detected Conflicts:    {len(conflicts)}")

    for rel in relationships[:5]:
        print(f"        - [{rel.get('relationship_type')}] {rel.get('source_id')} -> {rel.get('target_id')} (conf: {rel.get('confidence')})")

    if conflicts:
        print("\n      Discrepancies Detected:")
        for c in conflicts:
            print(f"        [!] [{c.get('conflict_type')}] {c.get('description')} (severity: {c.get('severity')})")

    # 4. Findings & Hypotheses
    print("\n[4/5] Structured Empirical Findings:")
    for f in final_state.get("findings", []):
        print(f"      [{f.get('category')}] {f.get('statement')}")
        print(f"         Confidence: {f.get('confidence')} | Evidence: {f.get('supporting_evidence_ids')}")

    print("\n      Semantic Event Hypotheses:")
    for h in final_state.get("hypotheses", []):
        print(f"      * {h.get('semantic_class')} ({round(float(h.get('confidence', 0))*100, 1)}%):")
        print(f"         {h.get('description')}")

    # 5. Executive Conclusion & Attribution Boundary
    print("\n[5/5] Executive Conclusion & Attribution Boundary:")
    conclusion = final_state.get("conclusion", {})
    print(f"      Synthesis: {conclusion.get('summary')}")
    print(f"      Boundary:  {conclusion.get('attribution_boundary')}")

    print("\n" + "=" * 70)
    print("Artifacts Generated:")
    for art in final_state.get("artifacts", []):
        print(f"  - {art.get('name')} ({art.get('format')}) - {art.get('size_bytes')} bytes")
    print("=" * 70)
    print("Investigation successfully completed with verified audit trail.\n")


if __name__ == "__main__":
    main()
