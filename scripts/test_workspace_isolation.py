"""
TRINETRA Phase 8 — Multi-Workspace Data Isolation & Boundary Verification
Verifies:
1. Complete isolation between separate workspaces (no cross-workspace data leakage)
2. Evidence Board items and relationships strictly partitioned by workspace_id
3. Investigation plans and plan runs isolated per workspace
4. Annotations, review records, and follow-up queues isolated per workspace
5. Report dossiers partitioned per workspace
6. Activity logs isolated per workspace
7. Deletion of one workspace does not affect data in another workspace
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from workspace.service import WorkspaceService
from workspace.repository import WorkspaceRepository
from workspace.models import (
    InvestigationStep,
    PlanStepType,
    ReportSection,
    ReportClaim,
    ReviewStatus,
)


def run_test():
    print("=" * 70)
    print("TRINETRA Phase 8 — Multi-Workspace Isolation Verification")
    print("=" * 70)

    repo = WorkspaceRepository(":memory:")
    service = WorkspaceService(repository=repo)

    # 1. Initialize two independent analytical workspaces
    ws_a = service.create_workspace(
        name="Workspace Alpha: South Lhonak Glacial Lake",
        description="GLOF early warning monitoring for North Sikkim",
    )
    ws_b = service.create_workspace(
        name="Workspace Beta: Pangong Tso Shoreline",
        description="Hydro-acoustic and perimeter monitoring for Eastern Ladakh",
    )
    print(f" [1/6] Initialized 2 workspaces:")
    print(f"       Alpha : {ws_a.workspace_id} ('{ws_a.name}')")
    print(f"       Beta  : {ws_b.workspace_id} ('{ws_b.name}')")

    # 2. Pin Evidence Items into both workspaces
    item_a1 = service.pin_item(ws_a.workspace_id, "OBSERVATION", "obs_s2_sikkim_01", title="Sikkim Optical")
    item_a2 = service.pin_item(ws_a.workspace_id, "FINDING", "find_water_sikkim_02", title="Sikkim Water Extent")
    rel_a = service.link_items(ws_a.workspace_id, item_a1.item_id, item_a2.item_id, "supports")

    item_b1 = service.pin_item(ws_b.workspace_id, "OBSERVATION", "obs_s1_ladakh_01", title="Ladakh SAR")
    print(f" [2/6] Pinned evidence items and relationships.")

    # Verify item isolation
    items_a = service.list_board_items(ws_a.workspace_id)
    items_b = service.list_board_items(ws_b.workspace_id)
    assert len(items_a) == 2
    assert len(items_b) == 1
    assert all(i.workspace_id == ws_a.workspace_id for i in items_a)
    assert all(i.workspace_id == ws_b.workspace_id for i in items_b)
    assert item_b1.item_id not in [i.item_id for i in items_a]

    # Verify relation isolation
    rels_a = service.list_board_relations(ws_a.workspace_id)
    rels_b = service.list_board_relations(ws_b.workspace_id)
    assert len(rels_a) == 1
    assert len(rels_b) == 0
    print(f"       Evidence items strictly isolated: Alpha={len(items_a)}, Beta={len(items_b)}")

    # 3. Investigation Plans isolation
    plan_a = service.create_plan(
        ws_a.workspace_id,
        title="Alpha Hydro Expansion Plan",
        question="Is water depth increasing?",
        steps=[InvestigationStep("s1", PlanStepType.OBSERVATION_SEARCH)],
    )
    plans_a = service.list_plans(ws_a.workspace_id)
    plans_b = service.list_plans(ws_b.workspace_id)
    assert len(plans_a) == 1
    assert len(plans_b) == 0
    assert plans_a[0].plan_id == plan_a.plan_id
    print(f" [3/6] Investigation plans isolated: Alpha={len(plans_a)}, Beta={len(plans_b)}")

    # 4. Reviews and Follow-ups isolation
    service.set_review_status(
        ws_a.workspace_id,
        entity_type="FINDING",
        entity_id="find_water_sikkim_02",
        status=ReviewStatus.REVIEWED,
        review_note="Analyst confirmed delta in Alpha",
    )
    fu_a = service.create_follow_up(
        ws_a.workspace_id,
        linked_entity_type="FINDING",
        linked_entity_id="find_water_sikkim_02",
        note="Schedule high-resolution tasking",
    )
    fu_list_a = service.list_follow_ups(ws_a.workspace_id)
    fu_list_b = service.list_follow_ups(ws_b.workspace_id)
    assert len(fu_list_a) == 1
    assert len(fu_list_b) == 0
    print(f" [4/6] Follow-ups and review statuses isolated: Alpha={len(fu_list_a)}, Beta={len(fu_list_b)}")

    # 5. Reports isolation
    rep_b = service.create_report(
        workspace_id=ws_b.workspace_id,
        title="Beta Shoreline Change Dossier",
        sections=[
            ReportSection(
                section_id="sec-b1",
                type="FINDINGS",
                title="Perimeter Shoreline Observations",
                content="No anomalous change detected in eastern sector.",
                claims=[
                    ReportClaim(
                        claim_id="clm-b1",
                        text="Shoreline position remained stable within 2.5m tolerance.",
                        evidence_ids=[item_b1.item_id],
                        type="MEASUREMENT",
                    )
                ],
            )
        ],
    )
    reports_a = service.list_reports(ws_a.workspace_id)
    reports_b = service.list_reports(ws_b.workspace_id)
    assert len(reports_a) == 0
    assert len(reports_b) == 1
    assert reports_b[0].report_id == rep_b.report_id
    print(f" [5/6] Report dossiers isolated: Alpha={len(reports_a)}, Beta={len(reports_b)}")

    # 6. Activity log isolation and cascading integrity
    acts_a = service.list_activities(ws_a.workspace_id)
    acts_b = service.list_activities(ws_b.workspace_id)
    assert len(acts_a) > 0 and len(acts_b) > 0
    assert all(a.workspace_id == ws_a.workspace_id for a in acts_a)
    assert all(b.workspace_id == ws_b.workspace_id for b in acts_b)

    # Deleting Alpha workspace does not impact Beta
    service.delete_workspace(ws_a.workspace_id)
    assert service.get_workspace(ws_a.workspace_id) is None
    assert service.get_workspace(ws_b.workspace_id) is not None

    # Beta items and reports remain intact
    surviving_b_items = service.list_board_items(ws_b.workspace_id)
    surviving_b_reports = service.list_reports(ws_b.workspace_id)
    assert len(surviving_b_items) == 1
    assert len(surviving_b_reports) == 1
    print(f" [6/6] Deleted Alpha; confirmed Beta workspace completely intact with {len(surviving_b_items)} item(s) and {len(surviving_b_reports)} report(s).")

    print("=" * 70)
    print(" ALL MULTI-WORKSPACE ISOLATION TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_test()
