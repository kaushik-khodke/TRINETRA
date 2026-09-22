"""
TRINETRA Phase 8 — Comparative Intelligence & Sensitivity Analysis Verification
Verifies:
1. Area-normalized metric calculation (events & findings per 100 km²)
2. Disparity and observational coverage warning detection (cloud cover, resolution, modality, area ratio)
3. Multi-threshold stability curves (sensitivity analysis with rate-of-change and stability classifications)
4. End-to-end multi-region comparison execution via WorkspaceService
5. Multi-event and multi-finding comparative synthesis
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from workspace.service import WorkspaceService
from workspace.repository import WorkspaceRepository
from workspace.comparison.metrics import ComparisonMetricsEngine


def run_test():
    print("=" * 70)
    print("TRINETRA Phase 8 — Comparative Intelligence & Sensitivity Analysis")
    print("=" * 70)

    # 1. Area Normalization
    raw_findings = 25
    area_large = 500.0   # 500 km² -> 5 per 100 km²
    area_small = 50.0    # 50 km²  -> 50 per 100 km²

    norm_large = ComparisonMetricsEngine.normalize_by_area(raw_findings, area_large, 100.0)
    norm_small = ComparisonMetricsEngine.normalize_by_area(raw_findings, area_small, 100.0)

    assert norm_large == 5.0
    assert norm_small == 50.0
    print(f" [1/5] Area normalization verified:")
    print(f"       - 25 findings over 500 km² = {norm_large} per 100 km²")
    print(f"       - 25 findings over 50 km²  = {norm_small} per 100 km²")

    # 2. Coverage Disparity Warnings
    meta_sikkim = {
        "region_id": "reg-sikkim",
        "cloud_cover_percentage": 28.5,
        "resolution_meters": 10.0,
        "modality": "OPTICAL",
        "area_km2": 450.0,
    }
    meta_ladakh = {
        "region_id": "reg-ladakh",
        "cloud_cover_percentage": 4.0,     # Delta = 24.5% (> 15% threshold)
        "resolution_meters": 2.5,          # Ratio = 4x (>= 2x threshold)
        "modality": "SAR",                 # Modality mismatch: OPTICAL vs SAR
        "area_km2": 1800.0,                # Ratio = 4x (>= 3x threshold)
    }

    warnings = ComparisonMetricsEngine.detect_coverage_warnings(meta_sikkim, meta_ladakh)
    assert len(warnings) == 4
    print(f" [2/5] Coverage & Disparity Engine flagged all 4 observation biases:")
    for w in warnings:
        print(f"       - {w}")

    # 3. Sensitivity Stability Curve Computation
    thresholds = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    curve = ComparisonMetricsEngine.compute_sensitivity_curve(
        thresholds=thresholds,
        base_area_km2=15.0,
        decay_factor=1.8,
    )
    assert len(curve) == len(thresholds)
    stabilities = [pt["stability"] for pt in curve]
    assert any(s in ("STABLE", "MODERATELY_SENSITIVE", "HYPERSENSITIVE") for s in stabilities)

    print(f" [3/5] Multi-threshold sensitivity curve calculated ({len(curve)} points):")
    for pt in curve:
        print(
            f"       Thresh: {pt['threshold']:.2f} | Area: {pt['detected_area_km2']:.2f} km² | "
            f"RoC: {pt['rate_of_change']:6.2f} | Stability: {pt['stability']}"
        )

    # 4. Service-Level Multi-Region Comparison
    repo = WorkspaceRepository(":memory:")
    service = WorkspaceService(repository=repo)
    ws = service.create_workspace(name="Himalayan Comparative Study")

    comparison = service.compare_regions(
        workspace_id=ws.workspace_id,
        region_a_id="reg-sikkim",
        region_b_id="reg-ladakh",
        period="last_12_months",
        thresholds=thresholds,
    )

    assert comparison.comparison_id.startswith("comp-")
    assert comparison.workspace_id == ws.workspace_id
    assert comparison.region_a_id == "reg-sikkim"
    assert comparison.region_b_id == "reg-ladakh"
    assert len(comparison.metrics) > 0
    assert len(comparison.metrics["region_a"]["sensitivity_curve"]) == len(thresholds)
    assert len(comparison.metrics["region_b"]["sensitivity_curve"]) == len(thresholds)
    print(f" [4/5] Multi-region comparison persisted: {comparison.comparison_id}")
    print(f"       Normalized metrics evaluated: {list(comparison.metrics.keys())}")
    print(f"       Coverage warnings recorded : {len(comparison.warnings)}")

    # 5. Multi-Event & Multi-Finding Comparison
    event_comp = service.compare_events(
        workspace_id=ws.workspace_id,
        event_ids=["evt_glacial_outburst_01", "evt_glacial_outburst_02"],
    )
    assert "events" in event_comp or "event_count" in event_comp or "comparison" in event_comp

    finding_comp = service.compare_findings(
        finding_ids=["find_water_01", "find_water_02"],
    )
    assert "findings" in finding_comp or "count" in finding_comp or "comparison" in finding_comp

    print(f" [5/5] Multi-event & multi-finding comparative synthesis executed successfully.")

    print("=" * 70)
    print(" ALL SENSITIVITY ANALYSIS & COMPARISON TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_test()
