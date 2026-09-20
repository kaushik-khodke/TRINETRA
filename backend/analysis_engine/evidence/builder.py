"""
TRINETRA Analysis Engine — Evidence Pack Builder
Constructs, validates, and seals the comprehensive EvidencePack for downstream consumption.
"""

import uuid
from typing import List, Dict, Any, Optional
from analysis_engine.evidence.models import (
    EvidencePack,
    ChangeRegionEvidence,
    GroundingEvidence,
    SpectralEvidence,
    CrossModalEvidence,
)
from analysis_engine.evidence.validator import EvidenceValidator
from analysis_engine.evidence.ranking import EvidenceRanker


class EvidenceBuilder:
    @staticmethod
    def build_pack(
        run_id: str,
        mode: str,
        observation_ids: List[str],
        statistics: Dict[str, Any],
        change_regions: Optional[List[ChangeRegionEvidence]] = None,
        grounding_detections: Optional[List[GroundingEvidence]] = None,
        spectral_metrics: Optional[List[SpectralEvidence]] = None,
        cross_modal_items: Optional[List[CrossModalEvidence]] = None,
        aoi_bounds: Optional[List[float]] = None,
        visual_artifacts: Optional[Dict[str, str]] = None,
    ) -> EvidencePack:
        """
        Builds, ranks, and validates the complete EvidencePack.
        """
        # 1. Rank change regions if present
        ranked_regions = EvidenceRanker.rank_change_regions(change_regions or [])

        pack = EvidencePack(
            pack_id=f"pack_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            mode=mode,
            aoi_bounds=aoi_bounds,
            observation_ids=observation_ids,
            change_regions=ranked_regions,
            grounding_detections=grounding_detections or [],
            spectral_metrics=spectral_metrics or [],
            cross_modal_items=cross_modal_items or [],
            statistics=statistics,
            visual_artifacts=visual_artifacts or {},
            validation_status="PENDING",
        )

        # 2. Enforce strict mathematical and geometric gate
        EvidenceValidator.validate_pack(pack)
        pack.validation_status = "VALIDATED"

        return pack
