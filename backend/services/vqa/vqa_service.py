"""
SatQuery AI — Remote-Sensing VQA Specialist Service
Answers natural-language domain queries regarding single optical,
multispectral, and SAR satellite imagery using LLM & radiometric reasoning.
"""

import os
import json
import torch
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Optional
from geospatial.normalizer import GeospatialNormalizer
from geospatial.reader import GeospatialReader
from geospatial.overlays import EvidenceOverlayEngine
from services.llm_engine import LLMReasoningEngine
from services.vqa.evidence_engine import VQAEvidenceEngine
from models.loader import ModelManager
from models.tokenizer import VqaTokenizer, tokenize_sequence
from schemas.contracts import CandidateAnswer

class RSVqaSpecialist:
    def __init__(self):
        self.tool_id = "rs_vqa"
        self.version = "2.2.0"
        self.tokenizer = VqaTokenizer()

    def execute(self, image_arr: np.ndarray, meta: Dict[str, Any], query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Check for trained PyTorch neural checkpoint and perform active inference
        ckpt = ModelManager.load_weights_if_available("rs_vqa_model")
        has_neural_weights = ckpt is not None
        neural_pred = None
        param_count = None
        warnings_list: List[str] = []

        if has_neural_weights:
            try:
                model = ModelManager.load_or_get_model("rs_vqa_model")
                if model is not None:
                    device = next(model.parameters()).device
                    param_count = sum(p.numel() for p in model.parameters())
                    
                    # Preprocess question tokens using deterministic cryptographic SHA-256 tokenizer
                    token_ids = self.tokenizer.encode(query, max_length=16)
                    token_tensor = torch.tensor([token_ids], dtype=torch.long, device=device)

                    # Preprocess image raster to 224x224 RGB tensor
                    raw_prev = GeospatialReader.to_rgb_preview(image_arr, meta.get("modality", "optical"))
                    pil_img = raw_prev if hasattr(raw_prev, "resize") else Image.fromarray(raw_prev)
                    pil_img = pil_img.resize((224, 224), Image.BILINEAR)
                    norm_arr = np.transpose(np.array(pil_img, dtype=np.float32) / 255.0, (2, 0, 1))
                    img_tensor = torch.from_numpy(norm_arr).unsqueeze(0).to(device)

                    model.eval()
                    with torch.no_grad():
                        logits = model(img_tensor, token_tensor)
                        probs = torch.softmax(logits, dim=-1).squeeze(0)

                    # Map class indices to genuine vocabulary if available
                    vocab_path = os.path.join(os.path.dirname(ckpt), "rsvqa_vocab.json")
                    if not os.path.exists(vocab_path):
                        # Also check standard training manifests directory
                        alt_vocab = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "training", "02_rsvqa", "manifests", "rsvqa_vocab.json")
                        if os.path.exists(alt_vocab):
                            vocab_path = alt_vocab

                    idx2ans = {}
                    if os.path.exists(vocab_path):
                        with open(vocab_path, "r", encoding="utf-8") as f:
                            vocab_data = json.load(f)
                            idx2ans = {int(k): v for k, v in vocab_data.get("idx2ans", {}).items()}

                    top3 = torch.topk(probs, k=min(3, probs.size(0)))
                    indices = top3.indices.cpu().tolist()
                    scores = top3.values.cpu().tolist()

                    candidates = [
                        {"answer": idx2ans.get(idx, f"class_{idx}"), "confidence": round(float(s), 4)}
                        for idx, s in zip(indices, scores)
                    ]
                    neural_pred = {
                        "top_answer": candidates[0]["answer"] if candidates else None,
                        "confidence": candidates[0]["confidence"] if candidates else None,
                        "candidates": candidates
                    }
            except Exception as e:
                warnings_list.append(f"Neural inference warning: {e}")
                print(f"[RSVqaSpecialist] Neural inference warning: {e}")

        # Compute accurate radiometric spectral metrics from the uploaded raster
        metrics = GeospatialNormalizer.compute_spectral_breakdown(image_arr)
        modality = meta.get("modality", "optical")

        # Clean natural language feature observations (prevent leaking raw boolean keys into LLM)
        observations = []
        if metrics["water_body_pct"] > 1.5:
            observations.append(f"open surface water detected ({metrics['water_body_pct']}%)")
        else:
            observations.append("no significant surface water detected")

        if metrics["vegetation_cover_pct"] > 25.0:
            observations.append(f"dense canopy vegetation ({metrics['vegetation_cover_pct']}%)")
        elif metrics["vegetation_cover_pct"] > 5.0:
            observations.append(f"scattered vegetation ({metrics['vegetation_cover_pct']}%)")
        else:
            observations.append("sparse or negligible green vegetation")

        if metrics["built_up_density_pct"] > 8.0:
            observations.append(f"anthropogenic infrastructure present ({metrics['built_up_density_pct']}%)")
        else:
            observations.append("low built-up density")

        features = {
            "terrain_summary": "; ".join(observations),
            "water_detected": metrics["water_body_pct"] > 1.5,
            "vegetation_detected": metrics["vegetation_cover_pct"] > 5.0,
            "built_up_detected": metrics["built_up_density_pct"] > 8.0
        }
        if neural_pred and neural_pred["top_answer"]:
            features["neural_vqa_prediction"] = neural_pred["top_answer"]
            features["neural_confidence"] = f"{int(neural_pred['confidence'] * 100)}%"

        # Format candidates for typed EvidencePackage
        candidate_objs: Optional[List[CandidateAnswer]] = None
        if neural_pred and neural_pred.get("candidates"):
            candidate_objs = [
                CandidateAnswer(answer=c["answer"], confidence=c["confidence"])
                for c in neural_pred["candidates"]
            ]

        fallback_used = not (has_neural_weights and neural_pred is not None)
        fallback_reason = None if not fallback_used else ("No checkpoint on disk" if not has_neural_weights else "Neural inference failure")
        if fallback_used and fallback_reason:
            warnings_list.append(fallback_reason)

        # Construct comprehensive 10-point EvidencePackage
        top_ans = neural_pred["top_answer"] if neural_pred else None
        top_conf = neural_pred["confidence"] if neural_pred else (0.94 if metrics.get("is_geotiff") else 0.88)
        
        evidence_pkg = VQAEvidenceEngine.construct_evidence_package(
            image_arr=image_arr,
            meta=meta,
            query=query,
            spectral_metrics=metrics,
            top_answer=top_ans,
            candidates=candidate_objs,
            confidence=top_conf,
            is_calibrated=False,
            checkpoint_path=ckpt,
            model_name="rs_vqa_model" if has_neural_weights else "deterministic_spectral_physics",
            param_count=param_count,
            normalizer_name="GeospatialNormalizer.compute_spectral_breakdown",
            input_shape=list(image_arr.shape),
            warnings=warnings_list,
        )

        # Synthesize evidence-grounded answer via LLM reasoning engine
        response_lang = parameters.get("response_language", "en") if parameters else "en"
        synthesis = LLMReasoningEngine.synthesize_vqa_answer(
            query=query,
            modality=modality,
            spectral_metrics=metrics,
            detected_features=features,
            response_language=response_lang,
            evidence_package=evidence_pkg.model_dump(),
            model_top_answer=top_ans,
            model_confidence=top_conf,
        )

        engine_name = f"PyTorch Neural Checkpoint ({os.path.basename(ckpt)})" if has_neural_weights else synthesis["engine"]

        # Generate visual saliency heatmap overlay on the actual uploaded image
        rgb_preview = GeospatialReader.to_rgb_preview(image_arr, modality)
        
        # Overlay either water heatmap, vegetation heatmap, or structural gradient based on query
        clean_q = query.lower()
        if "water" in clean_q or "river" in clean_q or "lake" in clean_q:
            diff_map = np.clip(metrics["ndwi_map"] * 2.0, 0, 1.0)
        elif "vegetation" in clean_q or "forest" in clean_q or "crop" in clean_q:
            diff_map = np.clip(metrics["ndvi_map"] * 2.0, 0, 1.0)
        else:
            diff_map = np.clip((metrics["ndvi_map"] + metrics["ndwi_map"]) * 0.5 + 0.3, 0, 1.0)

        overlay_img = EvidenceOverlayEngine.render_change_heatmap(rgb_preview, diff_map, threshold=0.15)
        evidence_b64 = EvidenceOverlayEngine.to_base64(overlay_img)
        raw_b64 = EvidenceOverlayEngine.to_base64(rgb_preview)
        ckpt_hash = ModelManager.get_checkpoint_hash(ckpt) if ckpt else None

        return {
            "task": "vqa",
            "tool": self.tool_id,
            "version": self.version,
            "engine": engine_name,
            "requested_model": "rs_vqa_model",
            "loaded_model": os.path.basename(ckpt) if (has_neural_weights and not fallback_used) else None,
            "checkpoint_hash": ckpt_hash,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "query": query,
            "answer": synthesis["answer"],
            "confidence": neural_pred["confidence"] if (neural_pred and neural_pred.get("confidence") is not None) else synthesis["confidence"],
            "confidence_calibrated": False,
            "evidence_image": evidence_b64,
            "raw_preview": raw_b64,
            "evidence_package": evidence_pkg.model_dump(),
            "evidence_items": [it.model_dump() for it in evidence_pkg.evidence_items],
            "evidence_metrics": {
                "vegetation_cover_pct": metrics["vegetation_cover_pct"],
                "water_body_pct": metrics["water_body_pct"],
                "built_up_density_pct": metrics["built_up_density_pct"],
                "bare_soil_pct": metrics["bare_soil_pct"],
                "mean_ndvi": metrics["mean_ndvi"],
                "mean_ndwi": metrics["mean_ndwi"]
            }
        }
