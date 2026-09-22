"""
Unit tests for EventLifecycleManager state machine and transitions.
Validates legal transitions, illegal transition rejection, and empirical state evaluation.
"""

import pytest
from intelligence.models import EventState, EOEvent
from intelligence.lifecycle import EventLifecycleManager, InvalidLifecycleTransitionError


def test_allowed_transitions():
    assert EventLifecycleManager.can_transition(EventState.CANDIDATE, EventState.OBSERVED) is True
    assert EventLifecycleManager.can_transition(EventState.OBSERVED, EventState.CORROBORATED) is True
    assert EventLifecycleManager.can_transition(EventState.CORROBORATED, EventState.PERSISTENT) is True
    assert EventLifecycleManager.can_transition(EventState.PERSISTENT, EventState.RESOLVED) is True
    assert EventLifecycleManager.can_transition(EventState.CANDIDATE, EventState.RESOLVED) is True


def test_prohibited_transitions():
    # Candidate cannot jump straight to Persistent
    assert EventLifecycleManager.can_transition(EventState.CANDIDATE, EventState.PERSISTENT) is False

    # Resolved events cannot transition back to Candidate
    assert EventLifecycleManager.can_transition(EventState.RESOLVED, EventState.CANDIDATE) is False


def test_transition_validation_and_exception():
    # Valid transition does not raise
    EventLifecycleManager.validate_transition(EventState.CANDIDATE, EventState.OBSERVED)

    # Invalid transition raises InvalidLifecycleTransitionError
    with pytest.raises(InvalidLifecycleTransitionError):
        EventLifecycleManager.validate_transition(EventState.CANDIDATE, EventState.PERSISTENT)


def test_infer_next_state():
    # 1. Single observation -> OBSERVED
    s1 = EventLifecycleManager.infer_next_state(
        current_state=EventState.CANDIDATE,
        observation_count=1,
        duration_days=1,
        persistence_ratio=0.5,
    )
    assert s1 == EventState.OBSERVED

    # 2. Multiple observations -> CORROBORATED
    s2 = EventLifecycleManager.infer_next_state(
        current_state=EventState.OBSERVED,
        observation_count=2,
        duration_days=5,
        persistence_ratio=0.5,
    )
    assert s2 == EventState.CORROBORATED

    # 3. Persistent observation (count >= 3, days >= 20, ratio >= 0.55) -> PERSISTENT
    s3 = EventLifecycleManager.infer_next_state(
        current_state=EventState.CORROBORATED,
        observation_count=4,
        duration_days=25,
        persistence_ratio=0.7,
    )
    assert s3 == EventState.PERSISTENT

    # 4. Inactive detections -> RESOLVED
    s4 = EventLifecycleManager.infer_next_state(
        current_state=EventState.PERSISTENT,
        observation_count=4,
        duration_days=30,
        persistence_ratio=0.7,
        has_active_detections=False,
    )
    assert s4 == EventState.RESOLVED
