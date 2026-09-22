"""
TRINETRA Phase 7 — Event Merger
Merges overlapping, compatible events with strict lineage and provenance recording.
"""

import uuid
from datetime import datetime
from typing import Tuple
from intelligence.models import EOEvent, EventState, EventRelationship
from intelligence.events.matcher import compute_bbox_iou, haversine_distance_km, EventMatcher
from intelligence.repository import IntelligenceRepository


class EventMerger:
    """
    Merges two compatible EOEvents into a unified canonical event entity.
    """

    @classmethod
    def can_merge(cls, event_a: EOEvent, event_b: EOEvent) -> bool:
        if event_a.event_id == event_b.event_id:
            return False

        if not EventMatcher.are_semantics_compatible(event_a.semantic_class, event_b.semantic_class):
            return False

        box_a = event_a.bounding_box
        box_b = event_b.bounding_box
        if not box_a or not box_b or len(box_a) < 4 or len(box_b) < 4:
            return False

        iou = compute_bbox_iou(box_a, box_b)
        if iou >= 0.20:
            return True

        lat_a = (box_a[1] + box_a[3]) / 2.0
        lon_a = (box_a[0] + box_a[2]) / 2.0
        lat_b = (box_b[1] + box_b[3]) / 2.0
        lon_b = (box_b[0] + box_b[2]) / 2.0
        dist = haversine_distance_km(lat_a, lon_a, lat_b, lon_b)
        return dist <= 2.0

    @classmethod
    def merge_events(
        cls,
        primary_event: EOEvent,
        secondary_event: EOEvent,
        repository: IntelligenceRepository,
    ) -> Tuple[EOEvent, EOEvent]:
        now = datetime.utcnow().isoformat()

        # Combine supporting findings and analyses
        for fid in secondary_event.supporting_findings:
            if fid not in primary_event.supporting_findings:
                primary_event.supporting_findings.append(fid)

        for aid in secondary_event.supporting_analyses:
            if aid not in primary_event.supporting_analyses:
                primary_event.supporting_analyses.append(aid)

        # Expand bbox
        b1 = primary_event.bounding_box
        b2 = secondary_event.bounding_box
        if b1 and b2 and len(b1) >= 4 and len(b2) >= 4:
            primary_event.bounding_box = [
                min(b1[0], b2[0]),
                min(b1[1], b2[1]),
                max(b1[2], b2[2]),
                max(b1[3], b2[3]),
            ]

        # Update timestamps
        primary_event.first_seen = min(primary_event.first_seen, secondary_event.first_seen)
        primary_event.last_seen = max(primary_event.last_seen, secondary_event.last_seen)
        primary_event.version += 1
        primary_event.updated_at = now

        primary_event.history.append({
            "timestamp": now,
            "from_state": primary_event.state.value,
            "to_state": primary_event.state.value,
            "reason": f"Merged secondary event {secondary_event.event_id}",
            "finding_id": None,
        })

        # Retire secondary event
        secondary_event.state = EventState.RESOLVED
        secondary_event.updated_at = now
        secondary_event.version += 1
        secondary_event.history.append({
            "timestamp": now,
            "from_state": secondary_event.state.value,
            "to_state": EventState.RESOLVED.value,
            "reason": f"Merged into primary event {primary_event.event_id}",
            "finding_id": None,
        })

        # Save relationship
        rel = EventRelationship(
            relationship_id=f"rel_{uuid.uuid4().hex[:8]}",
            source_event_id=secondary_event.event_id,
            target_event_id=primary_event.event_id,
            relationship_type="MERGED_FROM",
            weight=1.0,
            metadata={"merged_at": now},
        )

        repository.save_event(primary_event)
        repository.save_event(secondary_event)

        return primary_event, secondary_event
