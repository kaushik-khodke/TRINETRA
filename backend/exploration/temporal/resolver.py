"""
TRINETRA / Shanetra Geospatial Exploration Engine
Temporal Observation Resolver
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
Deterministic helper methods for natural-language query resolution (e.g. latest, previous, pairs).
"""

from typing import List, Optional, Tuple
from exploration.temporal.normalizer import ObservationSummary
from exploration.temporal.sorter import TemporalSorter


class TemporalResolver:
    """Resolves relative temporal queries (latest, previous, pair) against observation lists."""

    @classmethod
    def resolve_latest(cls, observations: List[ObservationSummary]) -> Optional[ObservationSummary]:
        """Returns the most recent observation."""
        if not observations:
            return None
        sorted_obs = TemporalSorter.sort_and_deduplicate(observations, sort_order="datetime_desc")
        return sorted_obs[0]

    @classmethod
    def resolve_previous(
        cls, observations: List[ObservationSummary], current_id: str
    ) -> Optional[ObservationSummary]:
        """Returns the acquisition immediately preceding current_id in time."""
        if not observations or not current_id:
            return None
        sorted_obs = TemporalSorter.sort_and_deduplicate(observations, sort_order="datetime_desc")
        for i, obs in enumerate(sorted_obs):
            if obs.id == current_id and i + 1 < len(sorted_obs):
                return sorted_obs[i + 1]
        return None

    @classmethod
    def resolve_next(
        cls, observations: List[ObservationSummary], current_id: str
    ) -> Optional[ObservationSummary]:
        """Returns the acquisition immediately following current_id in time."""
        if not observations or not current_id:
            return None
        sorted_obs = TemporalSorter.sort_and_deduplicate(observations, sort_order="datetime_desc")
        for i, obs in enumerate(sorted_obs):
            if obs.id == current_id and i > 0:
                return sorted_obs[i - 1]
        return None

    @classmethod
    def resolve_pair(
        cls, observations: List[ObservationSummary]
    ) -> Optional[Tuple[ObservationSummary, ObservationSummary]]:
        """Returns the two newest acquisitions (latest, previous) for instant comparison."""
        if len(observations) < 2:
            return None
        sorted_obs = TemporalSorter.sort_and_deduplicate(observations, sort_order="datetime_desc")
        return sorted_obs[0], sorted_obs[1]
