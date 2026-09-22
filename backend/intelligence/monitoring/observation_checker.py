"""
TRINETRA Phase 7 — Observation Checker
Detects newly available satellite observations over monitored AOIs and prevents duplicate re-processing.
"""

from typing import List, Dict, Any
from intelligence.models import MonitorDefinition
from intelligence.search.spatial import SpatialSearchFilter
from intelligence.repository import IntelligenceRepository


class ObservationChecker:
    """
    Validates spatial intersection and enforces observation deduplication.
    """

    @classmethod
    def should_process_observation(
        cls,
        monitor: MonitorDefinition,
        observation: Dict[str, Any],
        repository: IntelligenceRepository,
    ) -> bool:
        obs_id = observation.get("id")
        if not obs_id:
            return False

        # 1. Deduplication check: Has this observation already been processed by this monitor?
        if repository.has_processed_observation(monitor.monitor_id, obs_id):
            return False

        # 2. Spatial intersection check
        obs_bbox = observation.get("bbox")
        if obs_bbox and monitor.bounding_box:
            if not SpatialSearchFilter.intersects_bbox(monitor.bounding_box, obs_bbox):
                return False

        return True
