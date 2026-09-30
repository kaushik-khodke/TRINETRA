"""
SatQuery AI — Bi-Temporal Change Specialist Service
Performs differential change analysis, answers change-based questions,
quantifies urban/land shifts, and generates visual change maps.
"""

import os
import torch
import numpy as np
from PIL import Image
from typing import Dict, Any, List
from geospatial.normalizer import GeospatialNormalizer
from geospatial.overlays import EvidenceOverlayEngine
from geospatial.reader import GeospatialReader
from geospatial.validator import GeospatialValidator
from schemas.contracts import RasterMetadata
from core.exceptions import AlignmentMismatchError
from models.loader import ModelRegistryStatus
from services.llm_engine import LLMReasoningEngine

class BiTemporalChangeSpecialist:
    def __init__(self):
        self.tool_id = "change_ai"
        self.version = "2.1.0"

    def execute(
        self,
        images_arr: List[np.ndarray],
        metas: List[Dict[str, Any]],
        query: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        ckpt = ModelRegistryStatus.load_weights_if_available("change_specialist_model")
        has_neural_weights = ckpt is not None
        neural_change = None

        raw_t1 = images_arr[0]
        raw_t2 = images_arr[1]
        def _build_meta(arr: np.ndarray, m: Any) -> RasterMetadata:
            if isinstance(m, RasterMetadata):
                return m
            h, w = arr.shape[:2]
            bands = 1 if arr.ndim == 2 else (arr.shape[2] if arr.ndim == 3 else 1)
            d = dict(m) if isinstance(m, dict) else {}
            d.setdefault("width", w)
            d.setdefault("height", h)
            d.setdefault("band_count", d.get("bands", bands))
            d.setdefault("dtype", str(arr.dtype))
            return RasterMetadata(**d)

        meta1 = _build_meta(raw_t1, metas[0])
        meta2 = _build_meta(raw_t2, metas[1])

        # Stage 3 Geospatial Validation & Reference Grid Alignment
        arr_t1, arr_t2, alignment_report = GeospatialValidator.align_rasters_to_reference_grid(
            raw_t1, meta1, raw_t2, meta2, reference_grid="t1"
        )

        # Active forward pass through trained Siamese Neural Network
        if has_neural_weights:
            try:
                model = ModelRegistryStatus.load_or_get_model("change_specialist_model")
                if model is not None:
                    device = next(model.parameters()).device
                    raw_p1 = GeospatialReader.to_rgb_preview(arr_t1, metas[0].get("modality", "optical"))
                    p1 = raw_p1 if hasattr(raw_p1, "resize") else Image.fromarray(raw_p1)
                    p1 = p1.resize((256, 256), Image.BILINEAR)

                    raw_p2 = GeospatialReader.to_rgb_preview(arr_t2, metas[1].get("modality", "optical"))
                    p2 = raw_p2 if hasattr(raw_p2, "resize") else Image.fromarray(raw_p2)
                    p2 = p2.resize((256, 256), Image.BILINEAR)
                    t1_arr = np.transpose(np.array(p1, dtype=np.float32) / 255.0, (2, 0, 1))
                    t2_arr = np.transpose(np.array(p2, dtype=np.float32) / 255.0, (2, 0, 1))
                    t1_tensor = torch.from_numpy(t1_arr).unsqueeze(0).to(device)
                    t2_tensor = torch.from_numpy(t2_arr).unsqueeze(0).to(device)

                    model.eval()
                    with torch.no_grad():
                        out = model(t1_tensor, t2_tensor)
                        logits = out[0] if isinstance(out, tuple) else out

                        if logits.ndim == 4:
                            # Dense change mask model (SiameseUNetBaseline or BIT): shape (B, 1, H, W)
                            dense_probs = torch.sigmoid(logits).squeeze().cpu().numpy()
                            change_ratio = float(np.mean(dense_probs >= 0.5))
                            mean_conf = float(np.mean(dense_probs[dense_probs >= 0.5])) if change_ratio > 0.0 else float(1.0 - np.mean(dense_probs))
                            detected_cls = "Detected Dense Structural Change" if change_ratio > 0.01 else "Unchanged / Stable"
                            neural_change = {
                                "detected_class": detected_cls,
                                "confidence": round(mean_conf, 4),
                                "change_area_ratio": round(change_ratio, 4),
                                "dense_change_mask": (dense_probs >= 0.5).astype(np.uint8)
                            }
                        else:
                            # Legacy 1D differential classifier
                            probs = torch.softmax(logits, dim=-1).squeeze(0).cpu().tolist()
                            classes = ["Unchanged / Stable", "Increased Development / New Structures", "Decreased / Cleared / Receded"]
                            top_idx = int(np.argmax(probs))
                            neural_change = {
                                "detected_class": classes[top_idx],
                                "confidence": round(float(probs[top_idx]), 4),
                                "class_probabilities": {cls_name: round(float(p), 4) for cls_name, p in zip(classes, probs)}
                            }
            except Exception as e:
                print(f"[BiTemporalChangeSpecialist] Neural inference warning: {e}")

        # Compute difference matrix & statistics with alignment report
        diff_matrix, stats = GeospatialNormalizer.compute_bitemporal_change(
            arr_t1, arr_t2, alignment_report=alignment_report
        )
        if neural_change:
            stats["neural_classification"] = neural_change["detected_class"]
            stats["neural_confidence"] = f"{int(neural_change['confidence'] * 100)}%"
            if "change_area_ratio" in neural_change:
                stats["neural_change_ratio"] = f"{round(neural_change['change_area_ratio'] * 100, 2)}%"


        # Synthesize evidence-grounded answer via LLM reasoning engine
        spatial_dist = {
            "quadrants": stats.get("quadrants", {}),
            "top_sectors": stats.get("top_sectors", []),
            "trend": neural_change["detected_class"] if neural_change else stats.get("trend", "expansion")
        }

        response_lang = parameters.get("response_language", "en") if parameters else "en"
        synthesis = LLMReasoningEngine.synthesize_change_answer(
            query=query,
            change_stats=stats,
            spatial_distribution=spatial_dist,
            response_language=response_lang
        )

        engine_type = f"PyTorch Neural Checkpoint ({os.path.basename(ckpt)})" if has_neural_weights else synthesis["engine"]
        answer = synthesis["answer"]
        confidence = neural_change["confidence"] if neural_change else synthesis["confidence"]
        status = stats.get("trend", "detected")

        # Render visual change heatmap overlay on T2
        rgb_t1 = GeospatialReader.to_rgb_preview(arr_t1, metas[0].get("modality", "optical"))
        rgb_t2 = GeospatialReader.to_rgb_preview(arr_t2, metas[1].get("modality", "optical"))
        
        change_map_img = EvidenceOverlayEngine.render_change_heatmap(rgb_t2, diff_matrix, threshold=0.25)
        
        preview_t1_b64 = EvidenceOverlayEngine.to_base64(rgb_t1)
        preview_t2_b64 = EvidenceOverlayEngine.to_base64(rgb_t2)
        change_map_b64 = EvidenceOverlayEngine.to_base64(change_map_img)

        fallback_used = not (has_neural_weights and neural_change is not None)
        fallback_reason = None if not fallback_used else ("No change_specialist_model checkpoint found on disk" if not has_neural_weights else "Neural inference failure")
        ckpt_hash = ModelRegistryStatus.get_checkpoint_hash(ckpt) if ckpt else None

        return {
            "task": "change_analysis",
            "tool": self.tool_id,
            "version": self.version,
            "engine": engine_type,
            "requested_model": "change_specialist_model",
            "loaded_model": os.path.basename(ckpt) if (has_neural_weights and not fallback_used) else None,
            "checkpoint_hash": ckpt_hash,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "query": query,
            "answer": answer,
            "change_status": status,
            "confidence": round(confidence, 2),
            "confidence_calibrated": False,
            "change_statistics": stats,
            "alignment_report": alignment_report.model_dump(),
            "evidence": {
                "t1_preview": preview_t1_b64,
                "t2_preview": preview_t2_b64,
                "change_heatmap": change_map_b64
            }
        }
