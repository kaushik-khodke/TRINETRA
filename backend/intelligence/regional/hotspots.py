"""
TRINETRA Phase 7 — Regional Hotspots
Clusters persistent and recurring EO events into spatial change hotspots.
"""

from collections import Counter
from typing import List, Dict, Any
from intelligence.models import EOEvent
from intelligence.events.matcher import haversine_distance_km


class HotspotClusterer:
    """
    Groups proximate events into regional activity hotspots.
    """

    @classmethod
    def find_hotspots(
        cls,
        events: List[EOEvent],
        cluster_distance_km: float = 6.0,
        min_events: int = 2,
    ) -> List[Dict[str, Any]]:
        if not events:
            return []

        clusters: List[List[EOEvent]] = []

        for event in events:
            if not event.bounding_box or len(event.bounding_box) < 4:
                continue

            lat = (event.bounding_box[1] + event.bounding_box[3]) / 2.0
            lon = (event.bounding_box[0] + event.bounding_box[2]) / 2.0

            assigned = False
            for cluster in clusters:
                # Compare to cluster centroid
                c_lat = sum((e.bounding_box[1] + e.bounding_box[3]) / 2.0 for e in cluster) / len(cluster)
                c_lon = sum((e.bounding_box[0] + e.bounding_box[2]) / 2.0 for e in cluster) / len(cluster)
                if haversine_distance_km(lat, lon, c_lat, c_lon) <= cluster_distance_km:
                    cluster.append(event)
                    assigned = True
                    break

            if not assigned:
                clusters.append([event])

        hotspots: List[Dict[str, Any]] = []
        for idx, cluster in enumerate(clusters):
            if len(cluster) < min_events and len(events) >= min_events:
                continue

            min_x = min(e.bounding_box[0] for e in cluster)
            min_y = min(e.bounding_box[1] for e in cluster)
            max_x = max(e.bounding_box[2] for e in cluster)
            max_y = max(e.bounding_box[3] for e in cluster)

            cat_counts = Counter(e.semantic_class for e in cluster)
            dominant_cat = cat_counts.most_common(1)[0][0] if cat_counts else "GENERAL_CHANGE"

            # Approximate area in km2
            w_km = haversine_distance_km(min_y, min_x, min_y, max_x)
            h_km = haversine_distance_km(min_y, min_x, max_y, min_x)
            area_km2 = max(0.5, round(w_km * h_km, 2))

            hotspots.append({
                "hotspot_id": f"hotspot_{idx + 1:02d}",
                "title": f"Hotspot {idx + 1:02d}: {dominant_cat.replace('_', ' ').title()}",
                "event_count": len(cluster),
                "area_km2": area_km2,
                "bounding_box": [min_x, min_y, max_x, max_y],
                "dominant_category": dominant_cat,
                "events": [e.event_id for e in cluster],
                "density": round(len(cluster) / area_km2, 2),
            })

        hotspots.sort(key=lambda x: x["event_count"], reverse=True)
        return hotspots
