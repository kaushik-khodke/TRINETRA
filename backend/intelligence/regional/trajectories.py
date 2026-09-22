"""
TRINETRA Phase 7 — Regional Trajectories
Generates chronological activity histograms and multi-epoch progression timelines.
"""

from collections import defaultdict
from typing import List, Dict, Any
from intelligence.models import EOEvent


class RegionalTrajectoryBuilder:
    """
    Synthesizes event chronologies into monthly/quarterly temporal activity histograms.
    """

    @classmethod
    def build_activity_timeline(cls, events: List[EOEvent]) -> List[Dict[str, Any]]:
        if not events:
            return []

        monthly_buckets: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "month": "",
            "event_count": 0,
            "persistent_count": 0,
            "categories": set(),
        })

        for event in events:
            date_str = event.last_seen or event.first_seen
            month_key = date_str[:7] if len(date_str) >= 7 else "2025-01"

            monthly_buckets[month_key]["month"] = month_key
            monthly_buckets[month_key]["event_count"] += 1
            if event.state.value == "PERSISTENT":
                monthly_buckets[month_key]["persistent_count"] += 1
            monthly_buckets[month_key]["categories"].add(event.semantic_class)

        sorted_keys = sorted(monthly_buckets.keys())
        timeline = []
        for k in sorted_keys:
            b = monthly_buckets[k]
            timeline.append({
                "month": b["month"],
                "event_count": b["event_count"],
                "persistent_count": b["persistent_count"],
                "dominant_categories": sorted(list(b["categories"])),
            })

        return timeline
