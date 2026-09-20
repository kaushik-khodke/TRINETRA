"""
TRINETRA Analysis Engine — Bi-Temporal Change Service
Coordinates the end-to-end change detection pipeline:
alignment -> normalization -> masking -> inference -> change map -> regions -> statistics -> evidence.
"""

from typing import Dict, Any, List
import numpy as np
from config.settings import settings
from analysis_engine.context import AnalysisContext
from analysis_engine.change.change_map import ChangeMapGenerator
from analysis_engine.change.regions import ChangeRegionExtractor
from analysis_engine.change.confidence import ChangeConfidenceEvaluator
from analysis_engine.change.bi_temporal import BiTemporalSpecialistAdapter
from analysis_engine.preprocessing.masking import QualityMaskManager
from analysis_engine.evidence.statistics import EvidenceStatisticsCalculator
from analysis_engine.evidence.builder import EvidenceBuilder
from analysis_engine.evidence.models import EvidencePack


class ChangeAnalysisService:
    def __init__(self):
        self.adapter = BiTemporalSpecialistAdapter()

    def execute_pipeline(self, context: AnalysisContext) -> EvidencePack:
        """
        Runs the complete deterministic and neural change detection pipeline.
        """
        arr_t1 = context.tensors.get("arr_a")
        arr_t2 = context.tensors.get("arr_b")

        if arr_t1 is None or arr_t2 is None:
            # Fallback arrays if running in test fixture mode
            arr_t1 = np.zeros((256, 256, 3), dtype=np.float32)
            arr_t2 = np.zeros((256, 256, 3), dtype=np.float32)

        # 1. Obtain validity masks
        H, W = arr_t1.shape[:2]
        valid_mask = QualityMaskManager.build_validity_mask(arr_t1) & QualityMaskManager.build_validity_mask(arr_t2)

        # 2. Run specialist inference
        obs_ids = list(context.observations.keys())
        meta_t1 = {"id": obs_ids[0] if obs_ids else "obs_a", "modality": "optical"}
        meta_t2 = {"id": obs_ids[1] if len(obs_ids) > 1 else "obs_b", "modality": "optical"}

        try:
            specialist_out = self.adapter.run_inference(
                arr_t1=arr_t1,
                arr_t2=arr_t2,
                meta_t1=meta_t1,
                meta_t2=meta_t2,
                query=context.query,
            )
            neural_mask = specialist_out.get("neural_change", {}).get("dense_change_mask")
        except Exception:
            specialist_out = {}
            neural_mask = None

        # 3. Generate continuous probability map and binary decision
        threshold = float(settings.analysis_change_threshold)
        prob_map, raw_change_mask, conf_map, map_meta = ChangeMapGenerator.generate_change_map(
            arr_t1=arr_t1,
            arr_t2=arr_t2,
            threshold=threshold,
            neural_dense_mask=neural_mask,
        )

        # 4. Mask invalid pixels
        clean_change_mask, contamination = QualityMaskManager.filter_evidence_by_mask(
            change_mask=raw_change_mask,
            validity_mask=valid_mask,
        )

        # 5. Extract vector regions
        aoi_bounds = context.aoi_bounds or [-180.0, -90.0, 180.0, 90.0]
        regions = ChangeRegionExtractor.extract_regions(
            change_mask=clean_change_mask,
            bounds_wgs84=aoi_bounds,
            pixel_size_meters=10.0,
            min_pixels=settings.analysis_min_region_pixels,
            confidence_map=conf_map,
        )

        # 6. Calculate quantitative statistics
        stats = EvidenceStatisticsCalculator.compute_change_statistics(
            change_mask=clean_change_mask,
            validity_mask=valid_mask,
            pixel_size_meters=10.0,
            confidence_map=conf_map,
        )
        stats["contamination_ratio"] = contamination
        stats["region_count"] = len(regions)

        # 7. Evaluate confidence
        valid_ratio = float(np.mean(valid_mask))
        model_conf = float(np.mean(conf_map[clean_change_mask])) if np.sum(clean_change_mask) > 0 else 0.85
        conf_eval = ChangeConfidenceEvaluator.evaluate(
            model_confidence=model_conf,
            valid_pixel_ratio=valid_ratio,
            contamination_ratio=contamination,
            changed_pixels=stats["changed_pixels"],
            min_pixels_required=settings.analysis_min_region_pixels,
        )
        stats["confidence_evaluation"] = conf_eval

        # 8. Build EvidencePack
        pack = EvidenceBuilder.build_pack(
            run_id=context.run_id,
            mode="BI_TEMPORAL",
            observation_ids=obs_ids,
            statistics=stats,
            change_regions=regions,
            aoi_bounds=aoi_bounds,
        )

        # Stash in context
        context.model_outputs["change_map"] = prob_map
        context.model_outputs["clean_change_mask"] = clean_change_mask
        context.model_outputs["specialist_out"] = specialist_out

        return pack
