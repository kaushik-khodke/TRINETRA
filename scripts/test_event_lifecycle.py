"""
TRINETRA Phase 7 — Verification Script: Event Lifecycle, Split & Merge
Validates the canonical event state machine transitions, lineage tracking,
spatial event splitting, and provenance-preserving merging.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from intelligence.models import EOEvent, EventState
from intelligence.lifecycle import EventLifecycleManager, InvalidLifecycleTransitionError
from intelligence.events.merger import EventMerger
from intelligence.events.splitter import EventSplitter
from intelligence.repository import IntelligenceRepository


def run_lifecycle_test():
    print("================================================================")
    print("  TRINETRA Phase 7: Event Lifecycle, Split & Merge Test")
    print("================================================================")

    # 1. State machine validation
    print("[1] Validating State Machine Transitions...")
    assert EventLifecycleManager.can_transition(EventState.CANDIDATE, EventState.OBSERVED)
    assert EventLifecycleManager.can_transition(EventState.OBSERVED, EventState.CORROBORATED)
    assert EventLifecycleManager.can_transition(EventState.CORROBORATED, EventState.PERSISTENT)
    assert EventLifecycleManager.can_transition(EventState.PERSISTENT, EventState.RESOLVED)
    assert EventLifecycleManager.can_transition(EventState.OBSERVED, EventState.RESOLVED)

    # Illegal transition: RESOLVED -> CANDIDATE
    assert not EventLifecycleManager.can_transition(EventState.RESOLVED, EventState.CANDIDATE)
    try:
        EventLifecycleManager.validate_transition(EventState.RESOLVED, EventState.CANDIDATE)
        assert False, "Should have raised InvalidLifecycleTransitionError"
    except InvalidLifecycleTransitionError:
        print("✓ Illegal transition RESOLVED -> CANDIDATE rejected correctly")

    # 2. Database lifecycle persistence
    repo = IntelligenceRepository(db_path=":memory:")
    event_1 = EOEvent(
        event_id="evt_lifecycle_01",
        title="Urban Encroachment Sector Alpha",
        canonical_region_id="reg_alpha_01",
        semantic_class="built_up",
        state=EventState.OBSERVED,
        confidence=0.72,
        first_seen="2026-01-01T00:00:00",
        last_seen="2026-01-10T00:00:00",
        supporting_findings=["find_101"],
        supporting_analyses=["ana_201"],
        bounding_box=[77.58, 12.96, 77.62, 13.00],
    )
    repo.save_event(event_1)

    # Transition to CORROBORATED
    repo.update_event_state(
        event_id="evt_lifecycle_01",
        new_state=EventState.CORROBORATED,
        reason="Multi-spectral indices corroboration",
    )
    loaded = repo.get_event("evt_lifecycle_01")
    assert loaded is not None
    assert loaded.state == EventState.CORROBORATED
    assert len(loaded.history) == 2, f"Expected 2 history items, got {len(loaded.history)}"
    print(f"✓ Event state progressed to {loaded.state.value} with reason: '{loaded.history[-1]['reason']}'")

    # 3. Test Event Splitting
    print("\n[2] Testing Event Splitting...")
    child_defs = [
        {
            "title": "Urban Encroachment Sector Alpha (North)",
            "bounding_box": [77.58, 12.98, 77.62, 13.00],
            "confidence": 0.85,
        },
        {
            "title": "Urban Encroachment Sector Alpha (South)",
            "bounding_box": [77.58, 12.96, 77.62, 12.98],
            "confidence": 0.82,
        },
    ]
    children = EventSplitter.split_event(
        parent_event=loaded,
        split_definitions=child_defs,
        repository=repo,
    )
    assert len(children) == 2
    # Verify parent is RESOLVED
    parent_after_split = repo.get_event("evt_lifecycle_01")
    assert parent_after_split.state == EventState.RESOLVED
    print(f"✓ Parent event resolved due to split. Generated {len(children)} child events:")
    for c in children:
        print(f"  Child '{c.event_id}' ('{c.title}'), bbox: {c.bounding_box}")

    # 4. Test Event Merging
    print("\n[3] Testing Event Merging...")
    ev_a = children[0]
    ev_b = children[1]
    # Check merge compatibility
    can_merge = EventMerger.can_merge(ev_a, ev_b)
    print(f"✓ Merge compatibility evaluated: {can_merge}")

    merged_primary, merged_secondary = EventMerger.merge_events(
        primary_event=ev_a,
        secondary_event=ev_b,
        repository=repo,
    )
    assert merged_secondary.state == EventState.RESOLVED
    assert merged_primary.bounding_box == [77.58, 12.96, 77.62, 13.00]
    print(f"✓ Merged secondary '{merged_secondary.event_id}' into primary '{merged_primary.event_id}'")
    print(f"  Primary bbox restored to full union: {merged_primary.bounding_box}")

    print("\n>>> ALL EVENT LIFECYCLE VERIFICATIONS PASSED SUCCESSFULLY! <<<\n")


if __name__ == "__main__":
    run_lifecycle_test()
