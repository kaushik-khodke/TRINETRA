"""
TRINETRA Phase 8 — Workspace Lifecycle State Machine
Governs allowable lifecycle transitions for analytical workspaces:
CREATED -> ACTIVE -> PAUSED -> COMPLETED -> ARCHIVED
"""

from typing import Set, Tuple
from .models import WorkspaceStatus


class InvalidWorkspaceTransitionError(Exception):
    """Raised when an illegal workspace lifecycle transition is attempted."""
    pass


class WorkspaceLifecycleManager:
    """
    Strict state transition validator for workspace entities.
    """

    ALLOWED_TRANSITIONS: Set[Tuple[WorkspaceStatus, WorkspaceStatus]] = {
        (WorkspaceStatus.CREATED, WorkspaceStatus.ACTIVE),
        (WorkspaceStatus.ACTIVE, WorkspaceStatus.PAUSED),
        (WorkspaceStatus.PAUSED, WorkspaceStatus.ACTIVE),
        (WorkspaceStatus.ACTIVE, WorkspaceStatus.COMPLETED),
        (WorkspaceStatus.COMPLETED, WorkspaceStatus.ACTIVE),
        (WorkspaceStatus.COMPLETED, WorkspaceStatus.ARCHIVED),
        (WorkspaceStatus.ACTIVE, WorkspaceStatus.ARCHIVED),
        (WorkspaceStatus.PAUSED, WorkspaceStatus.ARCHIVED),
        (WorkspaceStatus.CREATED, WorkspaceStatus.ARCHIVED),
    }

    @classmethod
    def can_transition(cls, from_status: WorkspaceStatus, to_status: WorkspaceStatus) -> bool:
        if from_status == to_status:
            return True
        return (from_status, to_status) in cls.ALLOWED_TRANSITIONS

    @classmethod
    def validate_transition(cls, from_status: WorkspaceStatus, to_status: WorkspaceStatus) -> None:
        if not cls.can_transition(from_status, to_status):
            raise InvalidWorkspaceTransitionError(
                f"Cannot transition workspace from {from_status.value} to {to_status.value}."
            )
