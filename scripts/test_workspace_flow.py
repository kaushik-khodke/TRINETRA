"""
TRINETRA Phase 8 — End-to-End Analyst Workspace Workflow Test
Verifies:
1. Workspace lifecycle (create, update, activate)
2. Operational context initialization
3. Evidence board pinning & relationship linking
4. Investigation DAG plan creation & execution
5. Claim-grounded report dossier assembly
6. Cryptographic SHA-256 manifest generation
7. Standalone HTML presentation rendering
8. Tamper-evident ZIP evidence package export
"""

import sys
import os
import tempfile

# Ensure backend in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from workspace.service import WorkspaceService
from workspace.repository import WorkspaceRepository
from workspace.models import (
    WorkspaceStatus,
    PlanStepType,
    InvestigationStep,
    ReportClaim,
    ReportSection,
    ReviewStatus,
)


def run_test():
    print("=" * 70)
    print("TRINETRA Phase 8 — End-to-End Analyst Workspace Flow Verification")
    print("=" * 70)

    # 1. Initialize repository & service
    repo = WorkspaceRepository(":memory:")
    service = WorkspaceService(repository=repo)
    print(" [1/8] Workspace repository & service initialized in-memory.")

    # 2. Create Workspace
    ws = service.create_workspace(
        name="Sikkim Glacial Lake Outburst Risk Assessment",
        description="Comprehensive analyst investigation of South Lhonak glacial lake evolution",
        current_aoi={"type": "Polygon", "coordinates": [[[88.1, 27.8], [88.3, 27.8], [88.3, 28.0], [88.1, 28.0], [88.1, 27.8]]]},
    )
    assert ws.workspace_id.startswith("ws-")
    print(f" [2/8] Workspace created: {ws.workspace_id} ('{ws.name}') [Status: {ws.status.value}]")

    # Activate workspace
    ws_active = service.update_workspace(ws.workspace_id, status="ACTIVE")
    assert ws_active.status == WorkspaceStatus.ACTIVE
    print(f"       Workspace transitioned to: {ws_active.status.value}")

    # 3. Pin Evidence Items to Board
    item_obs = service.pin_item(
        ws.workspace_id,
        item_type="OBSERVATION",
        source_id="obs_sentinel2_2025_09_15",
        title="Sentinel-2 L2A Post-Monsoon Scene",
    )
    item_find = service.pin_item(
        ws.workspace_id,
        item_type="FINDING",
        source_id="find_water_expansion_14ha",
        title="Glacial Lake Surface Expansion +14.8 ha",
    )
    item_evt = service.pin_item(
        ws.workspace_id,
        item_type="EVENT",
        source_id="evt_lhonak_expansion",
        title="South Lhonak Moraine Dam Weakening",
    )
    print(f" [3/8] Pinned 3 evidence items to board: {item_obs.item_id}, {item_find.item_id}, {item_evt.item_id}")

    # Link items
    rel1 = service.link_items(ws.workspace_id, item_obs.item_id, item_find.item_id, "supports")
    rel2 = service.link_items(ws.workspace_id, item_find.item_id, item_evt.item_id, "supports")
    print(f"       Created evidence relationships: {rel1.relation_type} -> {rel2.relation_type}")

    # 4. Review item & record follow-up
    rev = service.set_review_status(
        ws.workspace_id,
        entity_type="FINDING",
        entity_id="find_water_expansion_14ha",
        status=ReviewStatus.REVIEWED,
        review_note="Verified by lead analyst with thermal infrared corroboration",
    )
    fu = service.create_follow_up(
        ws.workspace_id,
        linked_entity_type="EVENT",
        linked_entity_id="evt_lhonak_expansion",
        note="Schedule repeat SAR acquisition in next orbital pass",
    )
    print(f" [4/8] Review status updated: {rev.status.value} (Audited by {rev.analyst_id})")
    print(f"       Follow-up task created: {fu.follow_up_id} [{fu.status}]")

    # 5. Create & Execute Investigation Plan
    step1 = InvestigationStep("fetch-obs", PlanStepType.OBSERVATION_SEARCH)
    step2 = InvestigationStep("analyze-change", PlanStepType.ANALYZE_BITEMPORAL, depends_on=["fetch-obs"])
    step3 = InvestigationStep("synthesize", PlanStepType.BUILD_SYNTHESIS, depends_on=["analyze-change"])

    plan = service.create_plan(
        ws.workspace_id,
        title="Glacial Lake Expansion Verification Workflow",
        question="Is the moraine barrier retreating under hydrostatic expansion?",
        steps=[step1, step2, step3],
    )
    print(f" [5/8] DAG Investigation plan created: {plan.plan_id} ({len(plan.steps)} steps)")

    run = service.execute_plan(plan.plan_id)
    assert run.status.value == "COMPLETED"
    print(f"       Plan run completed successfully: {run.run_id} [Status: {run.status.value}]")

    # 6. Assemble Report with Claim Grounding
    claim = ReportClaim(
        claim_id="clm-lake-expansion",
        text="South Lhonak water surface area expanded by 14.8 hectares (+18.2%) between pre-monsoon and post-monsoon.",
        evidence_ids=[item_obs.source_id, item_find.source_id],
        type="FINDING",
    )
    sec_sum = ReportSection(
        section_id="sec-exec-summary",
        type="SUMMARY",
        title="Executive Summary & Strategic Alert",
        content="Multi-temporal optical and SAR analysis corroborates rapid expansion of South Lhonak proglacial lake.",
        claims=[claim],
    )
    sec_lim = ReportSection(
        section_id="sec-limitations",
        type="LIMITATIONS",
        title="Analytical Constraints & Sensor Limitations",
        content="Cloud cover on eastern peaks obscured perimeter between Aug 10 and Aug 28.",
        claims=[],
    )

    report = service.create_report(
        ws.workspace_id,
        title="South Lhonak Glacial Lake Outburst Flood Risk Dossier",
        sections=[sec_sum, sec_lim],
        strict_claims=True,
    )
    assert report.status.value == "VALIDATED"
    print(f" [6/8] Structured report dossier assembled: {report.report_id} [Status: {report.status.value}]")
    print(f"       SHA-256 Manifest: {report.manifest['overall_sha256']}")

    # 7. Render Standalone Presentation HTML
    html_text = service.render_report_html(report.report_id)
    assert "<!DOCTYPE html>" in html_text
    assert "Presentation Mode" in html_text
    assert "South Lhonak" in html_text
    print(f" [7/8] Standalone presentation HTML generated ({len(html_text):,} bytes).")

    # 8. Export Tamper-Evident ZIP Evidence Package
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = service.export_report_package(report.report_id, output_dir=tmpdir)
        assert os.path.exists(zip_path)
        zip_size_kb = os.path.getsize(zip_path) / 1024
        print(f" [8/8] Exported ZIP Evidence Package: {os.path.basename(zip_path)} ({zip_size_kb:.1f} KB)")

    print("=" * 70)
    print(" ALL 8 WORKSPACE WORKFLOW VERIFICATION STAGES PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_test()
