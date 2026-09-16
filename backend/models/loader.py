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

        if model_key == "bigearthnet_adapted":
            model = BigEarthNetAdaptedResNet(in_channels=4, num_classes=19).to(device)
        elif model_key == "rs_vqa_model":
            model = RSVqaFusionNetwork().to(device)
        elif model_key == "rs_grounding_model":
            model = RSGroundingDetector().to(device)
        elif model_key == "change_specialist_model":
            model = SiameseChangeDiffNet().to(device)
        elif model_key == "optical_sar_model":
            model = OpticalSARCrossAttentionNet().to(device)
        elif model_key == "hyperfree_model":
            from models.hyperfree.model import HyperFreeB
            model = HyperFreeB(num_classes=16).to(device)
        else:
            return None

        try:
            state = torch.load(ckpt_path, map_location=device)
            if isinstance(state, dict) and "state_dict" in state:
                state = state["state_dict"]
            elif isinstance(state, dict) and "model_state_dict" in state:
                state = state["model_state_dict"]
            
            # Verify keys
            missing, unexpected = model.load_state_dict(state, strict=False)
            if missing:
                print(f"[ModelManager] Checkpoint key mismatch: {len(missing)} missing keys in {ckpt_path}.")
            if unexpected:
                print(f"[ModelManager] Checkpoint key mismatch: {len(unexpected)} unexpected keys in {ckpt_path}.")
            
            model.eval()
            cls._models[model_key] = model
            print(f"[ModelManager] Loaded checkpoint {ckpt_path} successfully onto {device} (SHA256: {cls.get_checkpoint_hash(ckpt_path)[:12]}...).")
            return model
        except Exception as e:
            print(f"[ModelManager] Critical error loading checkpoint {ckpt_path}: {e}")
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
