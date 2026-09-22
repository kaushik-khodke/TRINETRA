"""
TRINETRA Phase 8 — Workspace Activity Tracker
Auditable activity logging and timeline management for analyst workspaces.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .models import WorkspaceActivity


class WorkspaceActivityTracker:
    """
    Manages audit logging for analyst workspace events and operations.
    Integrates directly with the WorkspaceRepository.
    """

    def __init__(self, repository=None):
        self.repository = repository

    def log(
        self,
        workspace_id: str,
        activity_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        actor: str = "analyst",
    ) -> WorkspaceActivity:
        """
        Record a new activity record for the workspace.
        """
        log_details = dict(details or {})
        if actor:
            log_details["actor"] = actor

        activity = WorkspaceActivity(
            activity_id=f"act-{uuid.uuid4().hex[:12]}",
            workspace_id=workspace_id,
            activity_type=activity_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=log_details,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        if self.repository:
            self.repository.save_activity(activity)

        return activity

    def list_activities(
        self,
        workspace_id: str,
        limit: int = 50,
        offset: int = 0,
        activity_type: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> List[WorkspaceActivity]:
        """
        Retrieve paginated activities for a workspace.
        """
        if not self.repository:
            return []
        return self.repository.list_activities(
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
            activity_type=activity_type,
            entity_type=entity_type,
        )
