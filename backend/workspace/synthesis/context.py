"""
TRINETRA Phase 8 — Synthesis Context Extractor
Compiles active workspace elements into a unified payload for report and synthesis generation.
"""

from typing import Dict, Any, List, Optional


class SynthesisContextExtractor:
    """
    Collects referenced intelligence entities across workspace tables.
    """

    @classmethod
    def extract_workspace_context(
        cls,
        workspace_id: str,
        repository=None,
    ) -> Dict[str, Any]:
        if not repository:
            return {"workspace_id": workspace_id, "items": [], "relations": [], "findings": []}

        ws = repository.get_workspace(workspace_id)
        ctx = repository.get_context(workspace_id)
        items = repository.list_board_items(workspace_id)
        relations = repository.list_board_relations(workspace_id)
        annotations = repository.list_annotations(workspace_id)
        reviews = repository.list_reviews(workspace_id)
        follow_ups = repository.list_follow_ups(workspace_id)

        return {
            "workspace_id": workspace_id,
            "workspace_name": ws.name if ws else workspace_id,
            "current_aoi": ws.current_aoi if ws else {},
            "active_regions": ctx.active_regions if ctx else [],
            "selected_observations": ctx.selected_observations if ctx else [],
            "selected_events": ctx.selected_events if ctx else [],
            "selected_findings": ctx.selected_findings if ctx else [],
            "board_items": [i.to_dict() for i in items],
            "board_relations": [r.to_dict() for r in relations],
            "annotations": [a.to_dict() for a in annotations],
            "reviews": [rv.to_dict() for rv in reviews],
            "follow_ups": [fu.to_dict() for fu in follow_ups],
        }
