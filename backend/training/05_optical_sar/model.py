"""
TRINETRA — Optical + SAR Cross-Modal Architecture Definitions
Exposes:
1. OpticalSARConcatBaseline: Feature concatenation baseline.
2. OpticalSARGatedFusionNet: Gated multimodal fusion network.
3. OpticalSARCrossAttentionNet: Multihead cross-attention fusion network.
4. OpticalOnlyBaseline: Single-sensor optical ablation.
5. SAROnlyBaseline: Single-sensor SAR ablation.
6. create_optical_sar_model: Model adapter factory.
Governed by Stage 5 Optical + SAR Protocol. Zero synthetic data.
"""

import os
import sys

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from models.optical_sar_models import (
    OpticalSARConcatBaseline,
    OpticalSARGatedFusionNet,
    OpticalSARCrossAttentionNet,
    OpticalOnlyBaseline,
    SAROnlyBaseline,
    create_optical_sar_model
)

__all__ = [
    "OpticalSARConcatBaseline",
    "OpticalSARGatedFusionNet",
    "OpticalSARCrossAttentionNet",
    "OpticalOnlyBaseline",
    "SAROnlyBaseline",
    "create_optical_sar_model"
]
