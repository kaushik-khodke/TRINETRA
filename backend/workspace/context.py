"""
TRINETRA Phase 8 — Workspace Analytical Context Manager
Provides a compact, active operational view of the current analytical workspace:
active AOI, active regions, selected observations/events/findings, and active artifacts.
"""

from typing import Dict, Any, List, Optional
from .models import WorkspaceContext


class WorkspaceContextManager:
    """
    Manages lightweight, active operational context within a workspace.
    Does not duplicate canonical records; maintains references.
    """

    @classmethod
    def create_initial_context(
        cls,
        workspace_id: str,
        current_aoi: Optional[Dict[str, Any]] = None,
    ) -> WorkspaceContext:
        return WorkspaceContext(
            workspace_id=workspace_id,
            current_aoi=current_aoi or {},
            active_regions=[],
            selected_observations=[],
            selected_events=[],
            selected_findings=[],
            open_investigation_id=None,
            active_comparison_id=None,
            active_report_id=None,
        )

    @classmethod
    def patch_context(
        cls,
        current: WorkspaceContext,
        patch: Dict[str, Any],
    ) -> WorkspaceContext:
        if "current_aoi" in patch and patch["current_aoi"] is not None:
            current.current_aoi = patch["current_aoi"]
        if "active_regions" in patch and patch["active_regions"] is not None:
            current.active_regions = list(patch["active_regions"])
        if "selected_observations" in patch and patch["selected_observations"] is not None:
            current.selected_observations = list(patch["selected_observations"])
        if "selected_events" in patch and patch["selected_events"] is not None:
            current.selected_events = list(patch["selected_events"])
        if "selected_findings" in patch and patch["selected_findings"] is not None:
            current.selected_findings = list(patch["selected_findings"])
        if "open_investigation_id" in patch:
            current.open_investigation_id = patch["open_investigation_id"]
        if "active_comparison_id" in patch:
            current.active_comparison_id = patch["active_comparison_id"]
        if "active_report_id" in patch:
            current.active_report_id = patch["active_report_id"]
        return current
