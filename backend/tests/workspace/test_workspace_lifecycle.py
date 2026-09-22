"""
TRINETRA Phase 8 Tests — Workspace Lifecycle & State Machine
Verifies allowable workspace transitions, illegal state rejections, and context updates.
"""

import pytest
from workspace.models import Workspace, WorkspaceStatus
from workspace.lifecycle import WorkspaceLifecycleManager, InvalidWorkspaceTransitionError
from workspace.repository import WorkspaceRepository
from workspace.service import WorkspaceService


@pytest.fixture
def repo():
    return WorkspaceRepository(":memory:")


@pytest.fixture
def service(repo):
    return WorkspaceService(repository=repo)


def test_workspace_creation_initial_state(service):
    ws = service.create_workspace(name="Sikkim Glacial Lake Outburst", description="Monitoring high-altitude lakes")
    assert ws.workspace_id.startswith("ws-")
    assert ws.name == "Sikkim Glacial Lake Outburst"
    assert ws.status == WorkspaceStatus.CREATED

    # Verify context auto-initialized
    ctx = service.get_context(ws.workspace_id)
    assert ctx is not None
    assert ctx.workspace_id == ws.workspace_id


def test_workspace_lifecycle_transitions(service):
    ws = service.create_workspace(name="Sundarbans Mangrove Loss")
    ws_id = ws.workspace_id

    # CREATED -> ACTIVE
    ws_active = service.update_workspace(ws_id, status="ACTIVE")
    assert ws_active.status == WorkspaceStatus.ACTIVE

    # ACTIVE -> PAUSED
    ws_paused = service.update_workspace(ws_id, status="PAUSED")
    assert ws_paused.status == WorkspaceStatus.PAUSED

    # PAUSED -> ACTIVE
    ws_resumed = service.update_workspace(ws_id, status="ACTIVE")
    assert ws_resumed.status == WorkspaceStatus.ACTIVE

    # ACTIVE -> COMPLETED
    ws_completed = service.update_workspace(ws_id, status="COMPLETED")
    assert ws_completed.status == WorkspaceStatus.COMPLETED

    # COMPLETED -> ARCHIVED
    ws_archived = service.update_workspace(ws_id, status="ARCHIVED")
    assert ws_archived.status == WorkspaceStatus.ARCHIVED


def test_invalid_lifecycle_transition_raises_error():
    # Direct transition from CREATED to COMPLETED is forbidden
    with pytest.raises(InvalidWorkspaceTransitionError):
        WorkspaceLifecycleManager.validate_transition(WorkspaceStatus.CREATED, WorkspaceStatus.COMPLETED)

    # ARCHIVED is terminal
    with pytest.raises(InvalidWorkspaceTransitionError):
        WorkspaceLifecycleManager.validate_transition(WorkspaceStatus.ARCHIVED, WorkspaceStatus.ACTIVE)


def test_workspace_activity_logged_on_transition(service):
    ws = service.create_workspace(name="Thar Desert Solar Farms")
    service.update_workspace(ws.workspace_id, status="ACTIVE")

    activities = service.list_activities(ws.workspace_id)
    actions = [a.activity_type for a in activities]
    assert "WORKSPACE_CREATED" in actions
    assert "WORKSPACE_UPDATED" in actions
