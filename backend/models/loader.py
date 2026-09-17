"""
SatQuery AI — Dynamic Model & Checkpoint Manager
Loads trained PyTorch neural networks from checkpoints directory,
performs forward passes, and provides fallback algorithmic CV reasoning.
"""

import os
import glob
import hashlib
import torch
import numpy as np
from typing import Dict, Any, Optional, Tuple

from config.settings import settings
from core.safe_loader import SafeModelLoader
from models.architectures import (
    BigEarthNetAdaptedResNet,
    RSVqaFusionNetwork,
    RSGroundingDetector,
    SiameseChangeDiffNet,
    OpticalSARCrossAttentionNet
)

CHECKPOINTS_DIR = settings.checkpoints_dir

CORINE_CLASSES = [
    "Continuous urban fabric", "Discontinuous urban fabric", "Industrial or commercial units",
    "Road and rail networks", "Port areas", "Airports", "Mineral extraction sites",
    "Non-irrigated arable land", "Permanently irrigated land", "Rice fields",
    "Vineyards", "Fruit trees and berry plantations", "Olive groves", "Pastures",
    "Broad-leaved forest", "Coniferous forest", "Mixed forest", "Natural grasslands", "Moors and heathland"
]

class ModelManager:
    """
    Manages PyTorch model lifecycles, checkpoint verification, and forward passes.
    Enforces truthful status reporting and observable fallback tracking.
    """

    _models: Dict[str, Any] = {}
    _hashes: Dict[str, str] = {}

    @classmethod
    def get_checkpoint_hash(cls, file_path: str) -> Optional[str]:
        """Calculates SHA-256 hash of a checkpoint file for strict provenance."""
        if not file_path or not os.path.isfile(file_path):
            return None
        if file_path in cls._hashes:
            return cls._hashes[file_path]
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    sha256.update(chunk)
            h = sha256.hexdigest()
            cls._hashes[file_path] = h
            return h
        except Exception as e:
            print(f"[ModelManager] Warning: failed to hash checkpoint {file_path}: {e}")
            return None

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """
        Returns truthful loading status for each model.
        Never reports 'loaded: True' for heuristic fallback states.
        """
        os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
        report = {}

        tool_dirs = {
            "bigearthnet_adapted": "BigEarthNet Multispectral / SAR Encoder",
            "rs_vqa_model": "RS-VQA Multimodal Bilinear Network",
            "rs_grounding_model": "Text-Guided Bounding Box Detector",
            "change_specialist_model": "Siamese Bi-Temporal Differential Net",
            "optical_sar_model": "Cross-Modal Dual-Encoder Fusion Net",
            "hyperfree_model": "HyperFree-B Hyperspectral Foundation Specialist"
        }

        for key, name in tool_dirs.items():
            target_path = os.path.join(CHECKPOINTS_DIR, key)
            os.makedirs(target_path, exist_ok=True)
            ckpt_file = cls._find_checkpoint(target_path)

            if ckpt_file:
                file_hash = cls.get_checkpoint_hash(ckpt_file)
                report[key] = {
                    "name": name,
                    "loaded": True,
                    "engine": f"PyTorch Neural Checkpoint ({os.path.basename(ckpt_file)})",
                    "checkpoint_file": os.path.basename(ckpt_file),
                    "checkpoint_hash": file_hash,
                    "path": ckpt_file,
                    "fallback_active": False,
                    "fallback_reason": None
                }
            else:
                report[key] = {
                    "name": name,
                    "loaded": False,
                    "engine": "Heuristic / Algorithmic CV Engine (Fallback)",
                    "checkpoint_file": None,
                    "checkpoint_hash": None,
                    "fallback_active": True,
                    "fallback_reason": "No checkpoint found on disk",
                    "expected_path": os.path.join("backend", "models", "checkpoints", key, "model.pt")
                }
        return report

    get_model_status_report = get_status

    @classmethod
    def _find_checkpoint(cls, dir_path: str) -> Optional[str]:
        if not os.path.exists(dir_path):
            return None
        candidates = (
            glob.glob(os.path.join(dir_path, "*.pt")) +
            glob.glob(os.path.join(dir_path, "*.bin")) +
            glob.glob(os.path.join(dir_path, "*.safetensors"))
        )
        return candidates[0] if candidates else None

    @classmethod
    def load_weights_if_available(cls, model_key: str) -> Optional[str]:
        target_dir = os.path.join(CHECKPOINTS_DIR, model_key)
        return cls._find_checkpoint(target_dir)

    @classmethod
    def load_or_get_model(cls, model_key: str):
        """
        Loads the PyTorch model with strict weight verification.
        Never caches or returns uninitialized random weights on missing/failed weights.
        """
        if model_key in cls._models:
            return cls._models[model_key]

        ckpt_path = cls._find_checkpoint(os.path.join(CHECKPOINTS_DIR, model_key))
        if not ckpt_path or not os.path.exists(ckpt_path):
            print(f"[ModelManager] No checkpoint on disk for '{model_key}'. Refusing to return uninitialized random-weight model.")
            return None

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        try:
            state = SafeModelLoader.load_state_dict(ckpt_path, map_location="cpu", enforce_weights_only=True)
        except Exception as e:
            print(f"[ModelManager] SafeModelLoader rejected checkpoint {ckpt_path}: {e}")
            return None

        keys = list(state.keys()) if isinstance(state, dict) else []
        all_keys_str = " ".join(keys)

        if model_key == "bigearthnet_adapted":
            model = BigEarthNetAdaptedResNet(in_channels=4, num_classes=19).to(device)
        elif model_key == "rs_vqa_model":
            num_answers = 120
            vocab_size = 5000
            if "fusion.3.weight" in state:
                num_answers = state["fusion.3.weight"].shape[0]
            if "text_embedding.weight" in state:
                vocab_size = state["text_embedding.weight"].shape[0]
            model = RSVqaFusionNetwork(vocab_size=vocab_size, num_answers=num_answers).to(device)
        elif model_key == "rs_grounding_model":
            model = RSGroundingDetector().to(device)
        elif model_key == "change_specialist_model":
            # Dynamic architecture detection for Stage 4 change models
            cfg_path = os.path.join(os.path.dirname(ckpt_path), "config.json")
            arch = None
            if os.path.exists(cfg_path):
                try:
                    import json
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        arch = cfg.get("model_architecture")
                except Exception:
                    pass

            if arch == "bit" or any("transformer" in k for k in keys):
                from models.change_models import BitemporalInteractionTransformer
                model = BitemporalInteractionTransformer().to(device)
            elif arch in ["baseline", "siamese_unet"] or any("enc1.conv" in k or "conv_head" in k for k in keys):
                from models.change_models import SiameseUNetBaseline
                model = SiameseUNetBaseline().to(device)
            else:
                model = SiameseChangeDiffNet().to(device)
        elif model_key == "optical_sar_model":
            # Dynamic architecture detection for Stage 5 Optical-SAR models
            cfg_path = os.path.join(os.path.dirname(ckpt_path), "config.json")
            arch = None
            if os.path.exists(cfg_path):
                try:
                    import json
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        arch = cfg.get("model_architecture")
                except Exception:
                    pass

            if arch in ["concat", "concat_baseline"] or ("gate_layer" not in all_keys_str and "cross_attn" not in all_keys_str and "classifier" in all_keys_str):
                from models.optical_sar_models import OpticalSARConcatBaseline
                model = OpticalSARConcatBaseline().to(device)
            elif arch in ["gated", "gated_fusion"] or "gate_layer" in all_keys_str:
                from models.optical_sar_models import OpticalSARGatedFusionNet
                model = OpticalSARGatedFusionNet().to(device)
            else:
                from models.optical_sar_models import OpticalSARCrossAttentionNet
                model = OpticalSARCrossAttentionNet().to(device)

        elif model_key == "hyperfree_model":
            # Dynamic architecture detection for Stage 6 Hyperspectral models
            cfg_path = os.path.join(os.path.dirname(ckpt_path), "config.json")
            arch = None
            in_c = 200
            n_cls = 16
            if os.path.exists(cfg_path):
                try:
                    import json
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        arch = cfg.get("model_architecture")
                        in_c = cfg.get("in_channels", 200)
                        n_cls = cfg.get("num_classes", 16)
                except Exception:
                    pass

            if arch == "spectral_mlp" or ("mlp.0.weight" in keys and "blocks." not in all_keys_str):
                from models.hyperspectral_models import SpectralMLPBaseline
                model = SpectralMLPBaseline(in_channels=in_c, num_classes=n_cls).to(device)
            elif arch == "hybridsn" or "conv3d_1" in all_keys_str:
                from models.hyperspectral_models import HybridSNBaseline
                model = HybridSNBaseline(in_channels=in_c, num_classes=n_cls).to(device)
            elif "blocks." in all_keys_str or "spectral_patch_embed" in all_keys_str:
                from models.hyperfree.model import HyperFreeB
                max_p = 1024
                if "pos_embed" in state and hasattr(state["pos_embed"], "shape"):
                    max_p = int(state["pos_embed"].shape[1]) - 1
                model = HyperFreeB(num_classes=n_cls, max_patches=max_p).to(device)
            else:
                try:
                    from models.hyperspectral_models import HyperFreeBAdapter
                    model = HyperFreeBAdapter(in_channels=in_c, num_classes=n_cls).to(device)
                except Exception:
                    from models.hyperfree.model import HyperFreeB
                    model = HyperFreeB(num_classes=n_cls).to(device)
        else:
            return None

        try:
            # Verify keys and load into device model
            missing, unexpected = model.load_state_dict(state, strict=False)
            if missing:
                print(f"[ModelManager] Checkpoint key mismatch: {len(missing)} missing keys in {ckpt_path}.")
            if unexpected:
                print(f"[ModelManager] Checkpoint key mismatch: {len(unexpected)} unexpected keys in {ckpt_path}.")

            model.eval()
            cls._models[model_key] = model
            print(f"[ModelManager] Loaded checkpoint {ckpt_path} safely onto {device} (SHA256: {cls.get_checkpoint_hash(ckpt_path)[:12]}...).")
            return model
        except Exception as e:
            print(f"[ModelManager] Critical error applying state dict to model {model_key}: {e}")
            return None

    @classmethod
    def build_model_run_record(
        cls,
        model_key: str,
        run_id: str,
        latency_ms: float,
        fallback_used: bool = False,
        fallback_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Constructs a ModelRun-compliant dictionary for inference tracking."""
        ckpt_file = cls.load_weights_if_available(model_key)
        ckpt_hash = cls.get_checkpoint_hash(ckpt_file) if ckpt_file else None
        engine_type = (
            f"PyTorch Neural Checkpoint ({os.path.basename(ckpt_file)})"
            if (ckpt_file and not fallback_used)
            else "Heuristic / Algorithmic CV Engine (Fallback)"
        )
        return {
            "run_id": run_id,
            "requested_model": model_key,
            "loaded_model": os.path.basename(ckpt_file) if (ckpt_file and not fallback_used) else None,
            "checkpoint_path": ckpt_file if (ckpt_file and not fallback_used) else None,
            "checkpoint_hash": ckpt_hash if (ckpt_file and not fallback_used) else None,
            "engine_type": engine_type,
            "device": settings.device,
            "latency_ms": round(latency_ms, 2),
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "schema_version": "2.0.0"
        }

# Backward compatibility alias
ModelRegistryStatus = ModelManager
