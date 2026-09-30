"""
TRINETRA / Shanetra Geospatial Exploration Engine
Temporal Sorter & Deduplication Engine
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
Deterministic sorting and composite deduplication across multi-source observations.
"""

from typing import List
from exploration.temporal.normalizer import ObservationSummary


class TemporalSorter:
    """Sorts and deduplicates observation items deterministically."""

    @classmethod
    def sort_and_deduplicate(
        cls,
        observations: List[ObservationSummary],
        sort_order: str = "datetime_desc",
    ) -> List[ObservationSummary]:
        if not observations:
            return []

        # 1. Deduplicate by observation ID and collection
        seen_keys = set()
        deduped: List[ObservationSummary] = []
        for obs in observations:
            key = f"{obs.collection}:{obs.id}"
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(obs)

        # 2. Sort
        if sort_order == "datetime_asc":
            deduped.sort(key=lambda o: o.datetime)
        elif sort_order == "cloud_asc":
            # Float with None pushed to end
            deduped.sort(key=lambda o: (o.cloud_cover if o.cloud_cover is not None else 999.0, o.datetime), reverse=False)
        else:  # default datetime_desc
            deduped.sort(key=lambda o: o.datetime, reverse=True)

        return deduped
