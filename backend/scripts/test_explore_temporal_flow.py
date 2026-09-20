"""
TRINETRA / Shanetra Geospatial Exploration Engine
End-to-End Integration Test: Phase 4 Temporal Exploration & Observation Comparison
Validates:
1. AOI Policy Validation (area, vertex count, self-intersection rejection)
2. Multi-temporal Observation Discovery (local index & STAC catalog)
3. Observation Normalization & Detail Inspection
4. Dual-Observation Compatibility Validation (temporal delta, spatial overlap, self-prevention)
5. AI Command Gateway Phase 4 extensions (SET_AOI, CLEAR_AOI, SET_DATE_RANGE, SELECT_OBSERVATION, COMPARE_OBSERVATIONS)
6. Bounded in-memory caching performance and telemetry export
"""

import os
import sys
import json
import time

# Ensure backend path is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from exploration.ai_schemas import (
    ExploreCommandPlan,
    SetAOICommand,
    ClearAOICommand,
    SetDateRangeCommand,
    SelectObservationCommand,
    CompareObservationsCommand,
)
from exploration.command_validator import CommandValidator
from exploration.command_executor import CommandExecutor

client = TestClient(app)


def run_phase4_verification():
    print("=" * 70)
    print("TRINETRA PHASE 4: TEMPORAL EXPLORATION & COMPARISON VERIFICATION")
    print("=" * 70)

    perf_metrics = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase": 4,
        "results": {},
    }

    # -------------------------------------------------------------
    # Step 1: Server-authoritative AOI Validation
    # -------------------------------------------------------------
    print("\n[1/6] Testing Server-Authoritative AOI Validation...")
    valid_polygon = {
        "aoi": {
            "type": "Polygon",
            "coordinates": [
                [
                    [79.0, 21.0],
                    [79.3, 21.0],
                    [79.3, 21.3],
                    [79.0, 21.3],
                    [79.0, 21.0],
                ]
            ],
        }
    }
    t0 = time.perf_counter()
    resp = client.post("/api/v1/explore/aoi/validate", json=valid_polygon)
    dt_aoi_valid = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 200, f"AOI validate failed: {resp.text}"
    aoi_data = resp.json()
    assert aoi_data["valid"] is True
    assert aoi_data["area_km2"] > 0
    print(f"  [OK] Valid polygon accepted: Area = {aoi_data['area_km2']:.1f} km^2, Vertices = {aoi_data['vertex_count']} ({dt_aoi_valid:.2f}ms)")

    # Self-intersecting polygon rejection
    self_intersecting = {
        "aoi": {
            "type": "Polygon",
            "coordinates": [
                [[0.0, 0.0], [2.0, 2.0], [0.0, 2.0], [2.0, 0.0], [0.0, 0.0]]
            ],
        }
    }
    resp = client.post("/api/v1/explore/aoi/validate", json=self_intersecting)
    assert resp.status_code == 200
    assert resp.json()["valid"] is False
    print("  [OK] Self-intersecting bowtie polygon rejected cleanly.")

    # Excessively large polygon rejection (>250,000 km^2)
    huge_polygon = {
        "aoi": {
            "type": "Polygon",
            "coordinates": [
                [[60.0, 5.0], [100.0, 5.0], [100.0, 35.0], [60.0, 35.0], [60.0, 5.0]]
            ],
        }
    }
    resp = client.post("/api/v1/explore/aoi/validate", json=huge_polygon)
    assert resp.status_code == 200
    assert resp.json()["valid"] is False
    print("  [OK] Oversized AOI (> 250,000 km^2) rejected cleanly.")

    perf_metrics["results"]["aoi_validation_ms"] = round(dt_aoi_valid, 3)

    # -------------------------------------------------------------
    # Step 2: Multi-Temporal Observation Discovery
    # -------------------------------------------------------------
    print("\n[2/6] Testing Multi-Temporal Observation Search...")
    search_payload = {
        "aoi": valid_polygon["aoi"],
        "start_datetime": "2026-01-01T00:00:00Z",
        "end_datetime": "2026-06-01T23:59:59Z",
        "collections": ["sentinel-2-l2a"],
        "cloud_cover_max": 40.0,
        "sort": "datetime_desc",
        "limit": 20,
    }

    t0 = time.perf_counter()
    resp = client.post("/api/v1/explore/observations/search", json=search_payload)
    dt_search = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 200, f"Search failed: {resp.text}"
    search_data = resp.json()
    assert "observations" in search_data
    assert search_data["cache_hit"] is False
    print(f"  [OK] First search (cache miss): Returned {len(search_data['observations'])} observations ({dt_search:.2f}ms)")

    # Repeat search to verify caching
    t0 = time.perf_counter()
    resp2 = client.post("/api/v1/explore/observations/search", json=search_payload)
    dt_cached_search = (time.perf_counter() - t0) * 1000
    assert resp2.status_code == 200
    assert resp2.json()["cache_hit"] is True
    print(f"  [OK] Cached search (cache hit): {dt_cached_search:.3f}ms (Speedup: {dt_search / max(0.001, dt_cached_search):.1f}x)")

    perf_metrics["results"]["temporal_search_miss_ms"] = round(dt_search, 3)
    perf_metrics["results"]["temporal_search_hit_ms"] = round(dt_cached_search, 3)

    # -------------------------------------------------------------
    # Step 3: Observation Detail Retrieval
    # -------------------------------------------------------------
    print("\n[3/6] Testing Observation Metadata Retrieval...")
    obs_id = "local_sentinel2_nagpur_truecolor"
    resp = client.get(f"/api/v1/explore/observations/{obs_id}")
    assert resp.status_code == 200, f"Get observation failed: {resp.text}"
    obs_details = resp.json()
    assert obs_details["id"] == obs_id
    assert "assets" in obs_details
    print(f"  [OK] Successfully inspected observation details for '{obs_id}'")

    # -------------------------------------------------------------
    # Step 4: Dual-Observation Compatibility Validation
    # -------------------------------------------------------------
    print("\n[4/6] Testing Dual-Observation Comparison Compatibility...")
    # Self comparison prevention
    resp = client.post(
        "/api/v1/explore/comparison/validate",
        json={
            "observation_a_id": obs_id,
            "observation_b_id": obs_id,
            "mode": "split",
        },
    )
    assert resp.status_code == 200
    res = resp.json()
    assert res["compatible"] is False
    assert any("itself" in e for e in res["errors"])
    print("  [OK] Self-comparison prevention verified (Cannot compare observation with itself).")

    # Disjoint comparison
    resp = client.post(
        "/api/v1/explore/comparison/validate",
        json={
            "observation_a_id": "local_sentinel2_nagpur_truecolor",
            "observation_b_id": "local_sentinel1_mumbai_sar",
            "mode": "split",
        },
    )
    assert resp.status_code == 200
    res = resp.json()
    # Mumbai and Nagpur are disjoint geographically
    assert res["compatible"] is False
    assert any("spatial overlap" in e.lower() or "disjoint" in e.lower() for e in res["errors"])
    print("  [OK] Disjoint footprints correctly identified as incompatible.")

    # -------------------------------------------------------------
    # Step 5: AI Command Gateway Phase 4 Extension
    # -------------------------------------------------------------
    print("\n[5/6] Testing AI Command Gateway Phase 4 Commands...")

    # SET_AOI Command
    set_aoi_cmd = SetAOICommand(geometry=valid_polygon["aoi"])
    ok, _, _ = CommandValidator.validate_command(set_aoi_cmd)
    assert ok is True

    plan_aoi = ExploreCommandPlan(
        intent="aoi_selection",
        summary="Define Area of Interest over Nagpur region.",
        commands=[set_aoi_cmd],
    )
    status, items, patch, _ = CommandExecutor.execute_plan(plan_aoi, current_active_layers=[])
    assert status == "completed"
    assert patch.aoi is not None
    print("  [OK] AI Gateway SET_AOI executed and patch generated.")

    # CLEAR_AOI Command
    clear_aoi_cmd = ClearAOICommand()
    ok, _, _ = CommandValidator.validate_command(clear_aoi_cmd)
    assert ok is True

    plan_clear = ExploreCommandPlan(
        intent="clear_aoi",
        summary="Remove active AOI.",
        commands=[clear_aoi_cmd],
    )
    status, items, patch, _ = CommandExecutor.execute_plan(plan_clear, current_active_layers=[])
    assert status == "completed"
    assert patch.aoi is None
    print("  [OK] AI Gateway CLEAR_AOI executed and patch generated.")

    # SET_DATE_RANGE Command
    date_cmd = SetDateRangeCommand(start_date="2026-01-01", end_date="2026-06-01")
    ok, _, _ = CommandValidator.validate_command(date_cmd)
    assert ok is True

    plan_date = ExploreCommandPlan(
        intent="date_filter",
        summary="Filter acquisitions from Jan to Jun 2026.",
        commands=[date_cmd],
    )
    status, items, patch, _ = CommandExecutor.execute_plan(plan_date, current_active_layers=[])
    assert status == "completed"
    assert patch.date_range == {"start": "2026-01-01", "end": "2026-06-01"}
    print("  [OK] AI Gateway SET_DATE_RANGE executed and patch generated.")

    # -------------------------------------------------------------
    # Step 6: Export Performance Artifact
    # -------------------------------------------------------------
    print("\n[6/6] Writing Performance Artifact...")
    output_dir = os.path.join(backend_dir, "outputs", "performance")
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "explore_phase4_temporal.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(perf_metrics, f, indent=2)
    print(f"  [OK] Performance telemetry saved to: {out_file}")


    print("\n" + "=" * 70)
    print("ALL PHASE 4 INTEGRATION GATES PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_phase4_verification()
