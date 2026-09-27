"""
TRINETRA Analysis Engine — Evidence Ranking Engine
Ranks detected change and grounding regions deterministically using measurable factors:
Priority = (w1 * area_normalized) + (w2 * confidence) + (w3 * change_score)
"""

from typing import List
from analysis_engine.evidence.models import ChangeRegionEvidence


class EvidenceRanker:
    @staticmethod
    def rank_change_regions(
        regions: List[ChangeRegionEvidence],
        w_area: float = 0.4,
        w_conf: float = 0.4,
        w_score: float = 0.2,
    ) -> List[ChangeRegionEvidence]:
        """
        Ranks regions deterministically and assigns sequential rank indices.
        """
        if not regions:
            return []

        # Find max area for normalization
        max_area = max(r.area_m2 for r in regions) if regions else 1.0
        if max_area <= 0.0:
            max_area = 1.0

        def score_fn(r: ChangeRegionEvidence) -> float:
            norm_area = min(1.0, r.area_m2 / max_area)
            return (w_area * norm_area) + (w_conf * r.confidence) + (w_score * r.change_score)

        # Sort descending by priority score
        sorted_regions = sorted(regions, key=score_fn, reverse=True)

        # Update 1-indexed ranks
        for idx, r in enumerate(sorted_regions):
            r.rank = idx + 1

        return sorted_regions
