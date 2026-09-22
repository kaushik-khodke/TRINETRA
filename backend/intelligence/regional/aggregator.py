"""
TRINETRA Phase 7 — Regional Intelligence Aggregator
Queries repository and aggregates events, anomalies, and trajectories for canonical regions.
"""

from typing import Dict, Any, Optional
from intelligence.repository import IntelligenceRepository
from intelligence.regional.summaries import RegionalSummaryAssembler
from intelligence.models import CanonicalRegion


class RegionalAggregator:
    """
    Coordinates aggregation queries for specific geographic areas or saved regions.
    """

    @classmethod
    def aggregate_region(
        cls,
        region_id: str,
        repository: IntelligenceRepository,
    ) -> Optional[Dict[str, Any]]:
        region = repository.get_region(region_id)
        if not region:
            return None

        events = repository.list_events(region_id=region_id, limit=200)
        anomalies = repository.list_anomalies(region_id=region_id, limit=50)

        return RegionalSummaryAssembler.assemble(
            region=region,
            events=events,
            anomalies=anomalies,
        )
