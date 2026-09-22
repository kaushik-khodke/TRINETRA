"""
TRINETRA Phase 7 — Event Construction & Evolution
Builds or evolves persistent EOEvents from incoming empirical findings.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from intelligence.models import EOEvent, CanonicalRegion, PersistentFinding, EventState
from intelligence.events.matcher import RegionMatcher, EventMatcher
from intelligence.lifecycle import EventLifecycleManager
from intelligence.repository import IntelligenceRepository


class EventBuilder:
    """
    Constructs new EOEvents or evolves existing active events when new findings are ingested.
    """

    @classmethod
    def ingest_finding(
        cls,
        finding: PersistentFinding,
        repository: IntelligenceRepository,
    ) -> EOEvent:
        # 1. Resolve or establish CanonicalRegion
        regions = repository.list_regions(limit=200)
        matched_region = RegionMatcher.match_region(finding.bounding_box, regions)

        now = datetime.utcnow().isoformat()

        if not matched_region:
            reg_id = f"reg_{uuid.uuid4().hex[:8]}"
            matched_region = CanonicalRegion(
                canonical_region_id=reg_id,
                name=f"Region {reg_id[-4:].upper()}",
                geometry=finding.geometry,
                bounding_box=finding.bounding_box,
                observed_region_ids=[finding.finding_id],
                first_seen=finding.created_at or now,
                last_seen=finding.created_at or now,
            )
            repository.save_region(matched_region)
        else:
            if finding.finding_id not in matched_region.observed_region_ids:
                matched_region.observed_region_ids.append(finding.finding_id)
            matched_region.last_seen = finding.created_at or now
            matched_region.updated_at = now
            repository.save_region(matched_region)

        # 2. Match to existing active event
        active_events = [e for e in repository.list_events(limit=200) if e.state != EventState.RESOLVED]
        match_result = EventMatcher.match_finding_to_event(finding, active_events)

        if match_result.matched_event:
            event = match_result.matched_event
            cls._update_existing_event(event, finding, matched_region, repository)
            return event
        else:
            return cls._create_new_event(finding, matched_region, repository)

    @classmethod
    def _create_new_event(
        cls,
        finding: PersistentFinding,
        region: CanonicalRegion,
        repository: IntelligenceRepository,
    ) -> EOEvent:
        now = datetime.utcnow().isoformat()
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        class_readable = finding.semantic_class.replace("_", " ").title()
        title = f"{class_readable} in {region.name}"

        initial_state = EventState.OBSERVED if len(finding.observation_ids) >= 1 else EventState.CANDIDATE

        event = EOEvent(
            event_id=event_id,
            title=title,
            canonical_region_id=region.canonical_region_id,
            semantic_class=finding.semantic_class,
            state=initial_state,
            confidence=finding.confidence,
            confidence_dimensions={
                "evidence_strength": finding.confidence,
                "temporal_persistence": 0.5,
                "spatial_consistency": 0.85,
                "cross_modal_support": 0.5,
                "model_quality": 0.88,
                "contradiction_penalty": 0.0,
            },
            first_seen=finding.created_at or now,
            last_seen=finding.created_at or now,
            supporting_findings=[finding.finding_id],
            supporting_analyses=list(finding.observation_ids),
            geometry=finding.geometry,
            bounding_box=finding.bounding_box,
            history=[
                {
                    "timestamp": now,
                    "from_state": None,
                    "to_state": initial_state.value,
                    "reason": f"Created from finding {finding.finding_id}",
                    "finding_id": finding.finding_id,
                }
            ],
        )
        repository.save_event(event)
        return event

    @classmethod
    def _update_existing_event(
        cls,
        event: EOEvent,
        finding: PersistentFinding,
        region: CanonicalRegion,
        repository: IntelligenceRepository,
    ) -> None:
        now = datetime.utcnow().isoformat()
        if finding.finding_id not in event.supporting_findings:
            event.supporting_findings.append(finding.finding_id)

        for obs_id in finding.observation_ids:
            if obs_id not in event.supporting_analyses:
                event.supporting_analyses.append(obs_id)

        event.last_seen = finding.created_at or now
        event.updated_at = now
        event.version += 1

        # Expand bounding box envelope if needed
        if finding.bounding_box and len(finding.bounding_box) >= 4:
            if not event.bounding_box or len(event.bounding_box) < 4:
                event.bounding_box = list(finding.bounding_box)
            else:
                event.bounding_box = [
                    min(event.bounding_box[0], finding.bounding_box[0]),
                    min(event.bounding_box[1], finding.bounding_box[1]),
                    max(event.bounding_box[2], finding.bounding_box[2]),
                    max(event.bounding_box[3], finding.bounding_box[3]),
                ]

        # Calculate empirical duration days
        try:
            d0 = datetime.fromisoformat(event.first_seen.replace("Z", "+00:00"))
            d1 = datetime.fromisoformat(event.last_seen.replace("Z", "+00:00"))
            duration_days = max(1, abs((d1 - d0).days))
        except Exception:
            duration_days = 30

        obs_count = len(event.supporting_analyses)
        persistence_ratio = min(1.0, obs_count / max(1, obs_count + 1))

        # Infer next lifecycle state
        old_state = event.state
        new_state = EventLifecycleManager.infer_next_state(
            current_state=old_state,
            observation_count=obs_count,
            duration_days=duration_days,
            persistence_ratio=persistence_ratio,
        )

        if new_state != old_state:
            event.state = new_state
            event.history.append({
                "timestamp": now,
                "from_state": old_state.value,
                "to_state": new_state.value,
                "reason": f"Corroborated by finding {finding.finding_id}",
                "finding_id": finding.finding_id,
            })

        # Multi-dimensional confidence refinement
        boost = 0.05 * min(3, len(event.supporting_findings))
        event.confidence = max(0.05, min(0.98, round(event.confidence + boost, 3)))
        event.confidence_dimensions["evidence_strength"] = event.confidence
        event.confidence_dimensions["temporal_persistence"] = round(persistence_ratio, 3)

        repository.save_event(event)
