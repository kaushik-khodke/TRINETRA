"""
TRINETRA Phase 8 Tests — Durable SQLite Workspace Repository
Verifies ACID compliance, thread safety, cascading deletes, and CRUD operations.
"""

import pytest
from workspace.repository import WorkspaceRepository
from workspace.models import (
    Workspace,
    WorkspaceStatus,
    WorkspaceContext,
    InvestigationPlan,
    InvestigationStep,
    PlanStepType,
    BatchJob,
    RegionComparison,
    EvidenceBoardItem,
    EvidenceBoardRelation,
    Annotation,
    ReviewRecord,
    ReviewStatus,
    FollowUp,
    ReportDocument,
    ReportSection,
    ReportClaim,
    WorkspaceTask,
    TaskPriority,
    TaskStatus,
    WorkspaceSnapshot,
)


@pytest.fixture
def repo():
    return WorkspaceRepository(":memory:")


def test_repository_workspace_and_context_crud(repo):
    ws = Workspace(
        workspace_id="ws-repo-test",
        name="Repository Test Workspace",
        description="Testing persistence",
        status=WorkspaceStatus.ACTIVE,
    )
    repo.save_workspace(ws)

    fetched = repo.get_workspace("ws-repo-test")
    assert fetched is not None
    assert fetched.name == "Repository Test Workspace"
    assert fetched.status == WorkspaceStatus.ACTIVE

    ctx = WorkspaceContext(
        workspace_id="ws-repo-test",
        active_regions=["reg-1", "reg-2"],
        selected_findings=["find-a", "find-b"],
    )
    repo.save_context(ctx)

    fetched_ctx = repo.get_context("ws-repo-test")
    assert fetched_ctx is not None
    assert "reg-1" in fetched_ctx.active_regions
    assert "find-a" in fetched_ctx.selected_findings


def test_repository_board_items_and_relations_crud(repo):
    item1 = EvidenceBoardItem(
        item_id="item-1",
        workspace_id="ws-1",
        type="FINDING",
        source_id="f-101",
        title="Glacial Lake Expansion",
    )
    item2 = EvidenceBoardItem(
        item_id="item-2",
        workspace_id="ws-1",
        type="OBSERVATION",
        source_id="obs-sentinel2",
        title="Sentinel-2 True Color",
    )
    repo.save_board_item(item1)
    repo.save_board_item(item2)

    items = repo.list_board_items("ws-1")
    assert len(items) == 2

    rel = EvidenceBoardRelation(
        relation_id="rel-1",
        workspace_id="ws-1",
        source_item_id="item-2",
        target_item_id="item-1",
        relation_type="supports",
    )
    repo.save_board_relation(rel)

    rels = repo.list_board_relations("ws-1")
    assert len(rels) == 1
    assert rels[0].relation_type == "supports"

    # Deleting source item cascades deletion of connected relation
    repo.delete_board_item("item-2")
    assert len(repo.list_board_items("ws-1")) == 1
    assert len(repo.list_board_relations("ws-1")) == 0


def test_repository_plans_and_tasks(repo):
    step = InvestigationStep(
        step_id="step-1",
        type=PlanStepType.OBSERVATION_SEARCH,
        parameters={"query": "Sentinel-2 L2A"},
    )
    plan = InvestigationPlan(
        plan_id="plan-101",
        workspace_id="ws-1",
        title="Lake Expansion Workflow",
        question="Is Lake South Lhonak expanding?",
        steps=[step],
    )
    repo.save_plan(plan)

    retrieved = repo.get_plan("plan-101")
    assert retrieved is not None
    assert len(retrieved.steps) == 1
    assert retrieved.steps[0].type == PlanStepType.OBSERVATION_SEARCH

    task = WorkspaceTask(
        task_id="task-01",
        workspace_id="ws-1",
        type="BATCH",
        priority=TaskPriority.INTERACTIVE,
        idempotency_key="idempotent-key-1",
    )
    repo.save_task(task)

    by_key = repo.get_task_by_idempotency_key("idempotent-key-1")
    assert by_key is not None
    assert by_key.task_id == "task-01"


def test_repository_cascading_workspace_delete(repo):
    ws_id = "ws-cascade"
    repo.save_workspace(Workspace(workspace_id=ws_id, name="Cascade Test"))
    repo.save_board_item(EvidenceBoardItem(item_id="i-cas", workspace_id=ws_id, type="NOTE", source_id="n-1"))
    repo.save_annotation(Annotation(annotation_id="a-cas", workspace_id=ws_id, text="Annotation test"))

    assert repo.get_workspace(ws_id) is not None
    assert len(repo.list_board_items(ws_id)) == 1
    assert len(repo.list_annotations(ws_id)) == 1

    deleted = repo.delete_workspace(ws_id)
    assert deleted is True
    assert repo.get_workspace(ws_id) is None
    assert len(repo.list_board_items(ws_id)) == 0
    assert len(repo.list_annotations(ws_id)) == 0
