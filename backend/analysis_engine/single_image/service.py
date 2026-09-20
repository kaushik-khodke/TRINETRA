"""
TRINETRA Analysis Engine — Single-Image Service
Orchestrates single-observation analysis by dispatching to Grounding, Captioning, or VQA specialists.
"""

from typing import Dict, Any, List
import numpy as np
from analysis_engine.context import AnalysisContext
from analysis_engine.single_image.vqa import VqaSpecialistAdapter
from analysis_engine.single_image.caption import CaptionSpecialistAdapter
from analysis_engine.single_image.grounding import GroundingSpecialistAdapter
from analysis_engine.single_image.evidence import SingleImageEvidenceNormalizer
from analysis_engine.evidence.builder import EvidenceBuilder
from analysis_engine.evidence.models import EvidencePack, GroundingEvidence


class SingleImageAnalysisService:
    def __init__(self):
        self.vqa = VqaSpecialistAdapter()
        self.caption = CaptionSpecialistAdapter()
        self.grounding = GroundingSpecialistAdapter()

    def execute_pipeline(self, context: AnalysisContext) -> EvidencePack:
        """
        Executes the appropriate single-image specialist and packages results.
        """
        arr = context.tensors.get("arr_a")
        if arr is None:
            arr = np.zeros((256, 256, 3), dtype=np.float32)

        obs_ids = list(context.observations.keys())
        meta = {"id": obs_ids[0] if obs_ids else "single_obs", "modality": "optical"}
        query = context.query.lower()

        grounding_items: List[GroundingEvidence] = []
        specialist_out: Dict[str, Any] = {}

        # 1. Routing based on query intent
        if any(w in query for w in ["where", "locate", "box", "find", "highlight", "detect"]):
            grounding_items = self.grounding.locate_features(arr, meta, context.query)
            specialist_out["task"] = "grounding"
            specialist_out["count"] = len(grounding_items)

        elif any(w in query for w in ["describe", "caption", "scene", "overview"]):
            caption_res = self.caption.generate_caption(arr, meta, context.query)
            specialist_out = caption_res
            specialist_out["task"] = "captioning"

        else:  # Default to VQA
            vqa_res = self.vqa.answer_question(arr, meta, context.query)
            specialist_out = vqa_res
            specialist_out["task"] = "vqa"

        # 2. Extract spectral evidence
        spectral_metrics = SingleImageEvidenceNormalizer.extract_spectral_evidence(arr)

        stats = {
            "mode": "SINGLE_IMAGE",
            "task": specialist_out.get("task", "vqa"),
            "detections_count": len(grounding_items),
            "answer": specialist_out.get("answer"),
            "confidence": specialist_out.get("confidence", 0.85),
        }

        # 3. Build sealed EvidencePack
        pack = EvidenceBuilder.build_pack(
            run_id=context.run_id,
            mode="SINGLE_IMAGE",
            observation_ids=obs_ids,
            statistics=stats,
            grounding_detections=grounding_items,
            spectral_metrics=spectral_metrics,
            aoi_bounds=context.aoi_bounds,
        )

        context.model_outputs["specialist_out"] = specialist_out
        return pack
