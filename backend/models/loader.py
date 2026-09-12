"""
SatQuery AI — Dynamic Model & Checkpoint Manager
Loads trained PyTorch neural networks from checkpoints directory,
performs forward passes, and provides fallback algorithmic CV reasoning.
"""

import os
import glob
import torch
import numpy as np
from typing import Dict, Any, Optional, Tuple

from models.architectures import (
    BigEarthNetAdaptedResNet,
    RSVqaFusionNetwork,
    RSGroundingDetector,
    SiameseChangeDiffNet,
    OpticalSARCrossAttentionNet
)

CHECKPOINTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints")

CORINE_CLASSES = [
    "Continuous urban fabric", "Discontinuous urban fabric", "Industrial or commercial units",
    "Road and rail networks", "Port areas", "Airports", "Mineral extraction sites",
    "Non-irrigated arable land", "Permanently irrigated land", "Rice fields",
    "Vineyards", "Fruit trees and berry plantations", "Olive groves", "Pastures",
    "Broad-leaved forest", "Coniferous forest", "Mixed forest", "Natural grasslands", "Moors and heathland"
]

class ModelManager:
    """Manages PyTorch model lifecycles, checkpoint weights, and neural forward passes."""

    _models = {}

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
        report = {}

        tool_dirs = {
            "bigearthnet_adapted": "BigEarthNet Multispectral / SAR Encoder",
            "rs_vqa_model": "RS-VQA Multimodal Bilinear Network",
            "rs_grounding_model": "Text-Guided Bounding Box Detector",
            "change_specialist_model": "Siamese Bi-Temporal Differential Net",
            "optical_sar_model": "Cross-Modal Dual-Encoder Fusion Net"
        }

        for key, name in tool_dirs.items():
            target_path = os.path.join(CHECKPOINTS_DIR, key)
            os.makedirs(target_path, exist_ok=True)
            ckpt_file = cls._find_checkpoint(target_path)

            if ckpt_file:
                report[key] = {
                    "name": name,
                    "loaded": True,
                    "engine": "PyTorch Neural Checkpoint",
                    "checkpoint_file": os.path.basename(ckpt_file),
                    "path": ckpt_file
                }
            else:
                report[key] = {
                    "name": name,
                    "loaded": True,
                    "engine": "Algorithmic CV / Radiometric Engine",
                    "checkpoint_file": "None (Awaiting user checkpoint upload)",
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
        if model_key in cls._models:
            return cls._models[model_key]

        ckpt_path = cls._find_checkpoint(os.path.join(CHECKPOINTS_DIR, model_key))
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
        else:
            return None

        if ckpt_path and os.path.exists(ckpt_path):
            try:
                state = torch.load(ckpt_path, map_location=device)
                model.load_state_dict(state, strict=False)
                model.eval()
                print(f"[ModelManager] Loaded checkpoint {ckpt_path} successfully onto {device}.")
            except Exception as e:
                print(f"[ModelManager] Warning: failed to load state dict from {ckpt_path}: {e}")

        cls._models[model_key] = model
        return model

# Backward compatibility alias
ModelRegistryStatus = ModelManager
