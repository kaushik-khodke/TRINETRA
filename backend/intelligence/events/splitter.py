"""
TRINETRA Phase 7 — Event Splitter
Splits divergent events into distinct child events with lineage tracking.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any
from intelligence.models import EOEvent, EventState, EventRelationship
from intelligence.repository import IntelligenceRepository


class EventSplitter:
    """
    Splits an existing event into multiple child events when spatial or semantic divergence occurs.
    """

    @classmethod
    def split_event(
        cls,
        parent_event: EOEvent,
        split_definitions: List[Dict[str, Any]],
        repository: IntelligenceRepository,
    ) -> List[EOEvent]:
        now = datetime.utcnow().isoformat()
        child_events: List[EOEvent] = []

        for idx, sdef in enumerate(split_definitions):
            child_id = f"evt_{uuid.uuid4().hex[:8]}"
            child = EOEvent(
                event_id=child_id,
                title=sdef.get("title", f"{parent_event.title} (Part {idx + 1})"),
                canonical_region_id=sdef.get("canonical_region_id", parent_event.canonical_region_id),
                semantic_class=sdef.get("semantic_class", parent_event.semantic_class),
                state=EventState(sdef.get("state", parent_event.state)),
                confidence=float(sdef.get("confidence", parent_event.confidence)),
                first_seen=parent_event.first_seen,
                last_seen=now,
                supporting_findings=list(sdef.get("supporting_findings", parent_event.supporting_findings)),
                supporting_analyses=list(sdef.get("supporting_analyses", parent_event.supporting_analyses)),
                geometry=sdef.get("geometry", parent_event.geometry),
                bounding_box=sdef.get("bounding_box", parent_event.bounding_box),
                history=[
                    {
                        "timestamp": now,
                        "from_state": None,
                        "to_state": parent_event.state.value,
                        "reason": f"Split from parent event {parent_event.event_id}",
                        "finding_id": None,
                    }
                ],
                metadata={"split_from_parent": parent_event.event_id},
            )
            repository.save_event(child)
            child_events.append(child)

        # Mark parent event as resolved due to split
        parent_event.state = EventState.RESOLVED
        parent_event.version += 1
        parent_event.updated_at = now
        parent_event.history.append({
            "timestamp": now,
            "from_state": parent_event.state.value,
            "to_state": EventState.RESOLVED.value,
            "reason": f"Split into {len(child_events)} child events",
            "finding_id": None,
        })
        repository.save_event(parent_event)

        return child_events
