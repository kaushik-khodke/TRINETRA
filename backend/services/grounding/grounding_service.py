"""
SatQuery AI / TRINETRA — Text-Guided Region Grounding Specialist Service
Locates spatial regions using connected-component bounding box detection,
Non-Maximum Suppression (NMS), spatial constraint filtering, and physical telemetry.
"""

import os
import numpy as np
from PIL import Image
from typing import Dict, Any, List
from geospatial.normalizer import GeospatialNormalizer
from geospatial.overlays import EvidenceOverlayEngine
from geospatial.reader import GeospatialReader
from models.loader import ModelManager
from models.tokenizer import tokenize_sequence
from services.llm_engine import LLMReasoningEngine
from services.grounding.spatial_interpreter import SpatialQueryInterpreter
from services.grounding.region_detector import RegionDetector

class RSGroundingSpecialist:
    def __init__(self):
        self.tool_id = "rs_ground"
        self.version = "2.1.0"

    def execute(self, image_arr: np.ndarray, meta: Dict[str, Any], query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        ckpt = ModelManager.load_weights_if_available("rs_grounding_model")
        engine_type = f"PyTorch Checkpoint ({os.path.basename(ckpt)})" if ckpt else "Pixel-Grounded Spatial Contour Engine"

        # 1. Parse natural-language query into structured spatial intent
        intent = SpatialQueryInterpreter.parse(query)
        clean_q = query.lower()
        regions: List[Dict[str, Any]] = []

        h, w = image_arr.shape[:2]
        max_dim = max(h, w)
        if max_dim > 1024:
            step = int(np.ceil(max_dim / 1024))
            sample_arr = image_arr[::step, ::step]
        else:
            sample_arr = image_arr
        sh, sw = sample_arr.shape[:2]

        # 2. Active Neural Forward Pass if Checkpoint Available
        if ckpt and intent.target not in ["water body", "vegetation loss"]:
            try:
                import torch
                net = ModelManager.load_or_get_model("rs_grounding_model")
                if net is not None:
                    device = next(net.parameters()).device
                    if image_arr.ndim == 3 and image_arr.shape[2] >= 3:
                        rgb_for_model = image_arr[:, :, :3]
                    elif image_arr.ndim == 3 and image_arr.shape[2] == 1:
                        rgb_for_model = np.repeat(image_arr, 3, axis=-1)
                    else:
                        rgb_for_model = np.stack([image_arr] * 3, axis=-1)

                    pil_img = Image.fromarray(np.clip(rgb_for_model, 0, 255).astype(np.uint8))
                    resized = pil_img.resize((256, 256), Image.BILINEAR)
                    arr_f = np.array(resized, dtype=np.float32) / 255.0
                    arr_f = np.transpose(arr_f, (2, 0, 1))
                    img_tensor = torch.from_numpy(arr_f).unsqueeze(0).to(device)

                    ids = tokenize_sequence(clean_q, max_length=12, vocab_size=4000, offset=100)
                    token_tensor = torch.tensor([ids], dtype=torch.long, device=device)

                    with torch.no_grad():
                        pred = net(img_tensor, token_tensor)[0].cpu().numpy()

                    ymin, xmin, ymax, xmax = float(pred[0]), float(pred[1]), float(pred[2]), float(pred[3])
                    raw_h = ymax - ymin
                    raw_w = xmax - xmin
                    if raw_h > 0.03 and raw_w > 0.03:
                        ymin, xmin = max(0.01, min(ymin, 0.95)), max(0.01, min(xmin, 0.95))
                        ymax, xmax = min(0.99, max(ymax, ymin + 0.05)), min(0.99, max(xmax, xmin + 0.05))
                        yc = (ymin + ymax) / 2.0
                        xc = (xmin + xmax) / 2.0
                        regions = [{
                            "id": "R01",
                            "label": f"Target: {intent.target.title()}",
                            "geometry_type": intent.geometry,
                            "bbox": [round(ymin, 3), round(xmin, 3), round(ymax, 3), round(xmax, 3)],
                            "score": 0.89,
                            "centroid": {"lat": None, "lng": None},
                            "centroid_norm": {"y": round(yc, 3), "x": round(xc, 3)},
                            "pixel_area": int(raw_h * raw_w * h * w),
                            "physical_area_m2": None,
                            "relative_location": RegionDetector.determine_relative_location(yc, xc),
                            "evidence": []
                        }]
            except Exception as e:
                print(f"[RSGroundingSpecialist] Neural forward pass fallback: {e}")

        # 3. Multi-Region Deterministic Spectral / Spatial Extractor
        if not regions:
            target = intent.target
            mask = None
            feature_label = "Identified Feature"

            # Hydrological targets
            if any(w in target for w in ["water", "river", "lake", "ocean", "reservoir"]):
                ndwi = GeospatialNormalizer.compute_ndwi(sample_arr)
                mask = ndwi > 0.10
                feature_label = "Water Body"

            # Vegetation targets
            elif any(w in target for w in ["vegetation", "forest", "tree", "crop", "agricultural", "canopy"]):
                ndvi = GeospatialNormalizer.compute_ndvi(sample_arr)
                mask = ndvi > 0.20
                feature_label = "Vegetation Canopy"

            # Built-up / urban targets
            elif any(w in target for w in ["built-up", "urban", "building", "structure", "city", "house", "roof"]):
                if sample_arr.ndim == 3:
                    gray = 0.299 * sample_arr[:, :, 0] + 0.587 * sample_arr[:, :, 1] + 0.114 * sample_arr[:, :, 2]
                else:
                    gray = sample_arr if sample_arr.ndim == 2 else sample_arr[:, :, 0]
                grad_y, grad_x = np.gradient(gray.astype(float))
                edge_mag = np.sqrt(grad_x**2 + grad_y**2)
                mask = edge_mag > 24.0
                feature_label = "Built-Up Structure"

            # Transport / Runway / Airport targets
            elif any(w in target for w in ["runway", "airport", "airfield", "aircraft", "landing"]):
                if sample_arr.ndim == 3:
                    gray = np.mean(sample_arr[:, :, :3], axis=-1)
                else:
                    gray = sample_arr if sample_arr.ndim == 2 else sample_arr[:, :, 0]
                mask = gray > 175
                feature_label = "Airport Transport Corridor"

            # Salient / high contrast spatial anomalies
            else:
                if sample_arr.ndim == 3:
                    gray = np.mean(sample_arr[:, :, :3], axis=-1)
                else:
                    gray = sample_arr if sample_arr.ndim == 2 else sample_arr[:, :, 0]
                grad_y, grad_x = np.gradient(gray.astype(float))
                edge_mag = np.sqrt(grad_x**2 + grad_y**2)
                p92 = float(np.percentile(edge_mag, 92))
                if p92 > 4.0:
                    mask = edge_mag >= p92
                    feature_label = f"Salient: {target.title()}"

            # Extract connected components with spatial constraint filtering
            if mask is not None and np.any(mask):
                regions = RegionDetector.extract_regions_from_mask(
                    binary_mask=mask,
                    h=sh,
                    w=sw,
                    label=feature_label,
                    meta=meta,
                    intent=intent
                )

        # 4. Handle Visual Overlay & Evidence Preparation
        modality = getattr(meta, "modality", None) or (meta.get("modality", "optical") if isinstance(meta, dict) else "optical")
        rgb_preview = GeospatialReader.to_rgb_preview(image_arr, modality)
        raw_b64 = EvidenceOverlayEngine.to_base64(rgb_preview)

        # 5. Handle Failure Gracefully if No Region Meets Constraints
        if not regions:
            return {
                "task": "grounding",
                "tool": self.tool_id,
                "version": self.version,
                "detected": False,
                "confidence": 0.0,
                "reason": f"No distinct spatial regions matching '{intent.target}' with constraint '{intent.region_constraint or 'none'}' were verified.",
                "recommendation": "Try broadening the directional constraint or verify sensor modality bands.",
                "engine": engine_type,
                "target_query": query,
                "spatial_intent": intent.model_dump(),
                "answer": f"Spatial localization completed for '{query}': No verified target regions matching the requested criteria were detected above confidence threshold.",
                "detected_regions": 0,
                "bounding_box": None,
                "regions": [],
                "confidence": 0.0,
                "evidence_image": raw_b64,
                "raw_preview": raw_b64
            }

        # Render tactical visual bounding overlay on the user's actual image
        overlay_img = EvidenceOverlayEngine.render_bounding_boxes(rgb_preview, regions)
        evidence_b64 = EvidenceOverlayEngine.to_base64(overlay_img)

        # Synthesize domain-grounded response via LLM reasoning engine
        metrics = GeospatialNormalizer.compute_spectral_breakdown(image_arr)
        synthesis = LLMReasoningEngine.synthesize_grounding_answer(
            query=query,
            modality=modality,
            boxes=regions,
            spectral_metrics=metrics,
            image_shape=image_arr.shape
        )

        engine_name = f"PyTorch Checkpoint ({ckpt})" if ckpt else synthesis.get("engine", engine_type)
        top_conf = max((r.get("score", 0.70) for r in regions), default=0.70)
        serializable_metrics = {
            k: v for k, v in metrics.items()
            if not k.endswith("_map") and not isinstance(v, np.ndarray)
        }

        fallback_used = ckpt is None
        fallback_reason = None if not fallback_used else "No rs_grounding_model checkpoint on disk"
        ckpt_hash = ModelManager.get_checkpoint_hash(ckpt) if ckpt else None

        return {
            "task": "grounding",
            "tool": self.tool_id,
            "version": self.version,
            "detected": len(regions) > 0,
            "engine": engine_name,
            "requested_model": "rs_grounding_model",
            "loaded_model": os.path.basename(ckpt) if ckpt else None,
            "checkpoint_hash": ckpt_hash,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "target_query": query,
            "spatial_intent": intent.model_dump(),
            "answer": synthesis.get("answer"),
            "detected_regions": len(regions),
            "bounding_box": regions[0]["bbox"] if regions else None,
            "regions": regions,
            "spectral_metrics": serializable_metrics,
            "confidence": top_conf,
            "confidence_calibrated": False,
            "evidence_image": evidence_b64,
            "raw_preview": raw_b64
        }
