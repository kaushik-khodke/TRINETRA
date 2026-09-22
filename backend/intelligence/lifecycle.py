"""
TRINETRA Phase 7 — Event Lifecycle State Machine
Governs deterministic state transitions: CANDIDATE -> OBSERVED -> CORROBORATED -> PERSISTENT -> RESOLVED.
"""

from typing import Dict, Any, Tuple
from investigation.errors import InvestigationError
from intelligence.models import EventState, EOEvent


class InvalidLifecycleTransitionError(InvestigationError):
    """Raised when an illegal event state transition is attempted."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, code="INVALID_LIFECYCLE_TRANSITION", details=details)


class EventLifecycleManager:
    """
    Deterministic validator and evaluator for EOEvent lifecycle progression.
    """

    ALLOWED_TRANSITIONS = {
        EventState.CANDIDATE: {EventState.OBSERVED, EventState.CORROBORATED, EventState.RESOLVED},
        EventState.OBSERVED: {EventState.CORROBORATED, EventState.PERSISTENT, EventState.RESOLVED},
        EventState.CORROBORATED: {EventState.PERSISTENT, EventState.RESOLVED},
        EventState.PERSISTENT: {EventState.RESOLVED},
        EventState.RESOLVED: {EventState.OBSERVED},  # Reappeared after resolution
    }

    @classmethod
    def can_transition(cls, current: EventState, target: EventState) -> bool:
        if current == target:
            return True
        allowed = cls.ALLOWED_TRANSITIONS.get(current, set())
        return target in allowed

    @classmethod
    def validate_transition(cls, current: EventState, target: EventState) -> None:
        if not cls.can_transition(current, target):
            raise InvalidLifecycleTransitionError(
                f"Illegal lifecycle transition from '{current.value}' to '{target.value}'. "
                f"Allowed transitions: {[s.value for s in cls.ALLOWED_TRANSITIONS.get(current, set())]}"
            )

    @classmethod
    def infer_next_state(
        cls,
        current_state: EventState,
        observation_count: int,
        duration_days: int,
        persistence_ratio: float,
        has_active_detections: bool = True,
    ) -> EventState:
        """
        Determines the appropriate lifecycle state based on empirical evidence.
        Rules:
        - If not observed recently and was persistent -> RESOLVED
        - If observation_count >= 3 and duration_days >= 30 and persistence_ratio >= 0.6 -> PERSISTENT
        - If observation_count >= 2 -> CORROBORATED
        - If observation_count == 1 -> OBSERVED
        - Default -> CANDIDATE
        """
        if not has_active_detections:
            return EventState.RESOLVED

        if observation_count >= 3 and duration_days >= 20 and persistence_ratio >= 0.55:
            target = EventState.PERSISTENT
        elif observation_count >= 2:
            target = EventState.CORROBORATED
        elif observation_count == 1:
            target = EventState.OBSERVED
        else:
            target = EventState.CANDIDATE

        # Verify transition validity
        if cls.can_transition(current_state, target):
            return target
        return current_state
