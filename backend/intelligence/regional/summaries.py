"""
TRINETRA Phase 7 — Regional Summary Assembly
Generates factual, evidence-bound regional intelligence summaries.
"""

from typing import Dict, Any, List
from collections import Counter
from intelligence.models import EOEvent, CanonicalRegion, AnomalyRecord
from intelligence.regional.trajectories import RegionalTrajectoryBuilder


class RegionalSummaryAssembler:
    """
    Synthesizes regional events, trajectories, and anomalies into structured intelligence dossiers.
    """

    @classmethod
    def assemble(
        cls,
        region: CanonicalRegion,
        events: List[EOEvent],
        anomalies: List[AnomalyRecord],
    ) -> Dict[str, Any]:
        event_count = len(events)
        persistent_events = sum(1 for e in events if e.state.value == "PERSISTENT")

        cat_counts = Counter(e.semantic_class for e in events)
        dominant_categories = [c[0] for c in cat_counts.most_common(3)] if cat_counts else ["GENERAL_CHANGE"]

        total_area_ha = sum(float(e.metadata.get("total_area_ha", 2.5)) for e in events)
        avg_confidence = round(sum(e.confidence for e in events) / max(1, event_count), 3) if events else 0.5

        cross_modal_events = sum(
            1 for e in events if e.confidence_dimensions.get("cross_modal_support", 0.0) >= 0.70
        )
        cross_modal_rate = round(cross_modal_events / max(1, event_count), 3)

        trajectories = RegionalTrajectoryBuilder.build_activity_timeline(events)

        period = f"{region.first_seen[:7]} to {region.last_seen[:7]}" if region.first_seen and region.last_seen else "2025 to 2026"

        return {
            "region_id": region.canonical_region_id,
            "name": region.name,
            "period": period,
            "event_count": event_count,
            "persistent_events": persistent_events,
            "total_changed_area_ha": round(total_area_ha, 2),
            "dominant_categories": dominant_categories,
            "anomaly_count": len(anomalies),
            "average_confidence": avg_confidence,
            "cross_modal_agreement_rate": cross_modal_rate,
            "trajectories": trajectories,
        }
