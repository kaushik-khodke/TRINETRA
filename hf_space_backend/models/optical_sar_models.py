"""
TRINETRA — Cross-Modal Optical + SAR Multimodal Architectures
Implements:
1. Baseline: OpticalSARConcatBaseline (feature concatenation reference).
2. Intermediate: OpticalSARGatedFusionNet (adaptive modality gating).
3. Modern: OpticalSARCrossAttentionNet (bidirectional / multihead cross-attention).
4. Single-Sensor Ablations: OpticalOnlyBaseline, SAROnlyBaseline (for genuine fusion gain measurement).
5. create_optical_sar_model: Unified factory adapter.
Governed by 05_STAGE_5_OPTICAL_SAR.md. Zero synthetic data.
"""

from typing import Tuple, Optional, Dict, Any, Literal
import torch
import torch.nn as nn
import torch.nn.functional as F


# ==============================================================================
# Shared Modality Encoders
# ==============================================================================
class ModalityEncoder(nn.Module):
    """
    Convolutional feature extractor adapted for specific remote-sensing sensor modalities.
    Extracts high-level spatial-spectral representations.
    """
    def __init__(self, in_channels: int, embed_dim: int = 64):
        super().__init__()
        self.conv_net = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=5, stride=2, padding=2, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, embed_dim, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(inplace=True),
            nn.Conv2d(embed_dim, embed_dim, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1))
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Returns pooled representation (B, embed_dim)."""
        return self.conv_net(x).flatten(1)


# ==============================================================================
# 1. Baseline: Simple Feature Concatenation Fusion
# ==============================================================================
class OpticalSARConcatBaseline(nn.Module):
    """
    Conventional Fusion Baseline: Concatenates independent Optical and SAR embeddings.
    Reference: Standard early/intermediate feature fusion baseline.
    """
    def __init__(
        self,
        opt_channels: int = 3,
        sar_channels: int = 2,
        embed_dim: int = 64,
        num_classes: int = 10
    ):
        super().__init__()
        self.architecture_name = "OpticalSARConcatBaseline"
        self.fusion_type = "concatenation"
        self.license = "MIT"

        self.opt_encoder = ModalityEncoder(opt_channels, embed_dim)
        self.sar_encoder = ModalityEncoder(sar_channels, embed_dim)

        self.classifier = nn.Sequential(
            nn.Linear(embed_dim * 2, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )

    def forward(self, optical: torch.Tensor, sar: torch.Tensor) -> torch.Tensor:
        opt_feat = self.opt_encoder(optical)
        sar_feat = self.sar_encoder(sar)
        fused = torch.cat([opt_feat, sar_feat], dim=-1)
        return self.classifier(fused)


# ==============================================================================
# 2. Intermediate Model: Gated Multimodal Fusion Network
# ==============================================================================
class OpticalSARGatedFusionNet(nn.Module):
    """
    Gated Fusion Architecture: Dynamically weights optical vs SAR features
    using a learnable gating mechanism to handle modality degradation or occlusion.
    Formula: g = Sigmoid(W_g [f_opt, f_sar]), f_fused = g * f_opt + (1 - g) * f_sar
    """
    def __init__(
        self,
        opt_channels: int = 3,
        sar_channels: int = 2,
        embed_dim: int = 64,
        num_classes: int = 10
    ):
        super().__init__()
        self.architecture_name = "OpticalSARGatedFusionNet"
        self.fusion_type = "gated"
        self.license = "MIT"

        self.opt_encoder = ModalityEncoder(opt_channels, embed_dim)
        self.sar_encoder = ModalityEncoder(sar_channels, embed_dim)

        # Gating layer computing dynamic weight per channel
        self.gate_layer = nn.Sequential(
            nn.Linear(embed_dim * 2, embed_dim),
            nn.Sigmoid()
        )

        self.classifier = nn.Sequential(
            nn.Linear(embed_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )

    def forward(self, optical: torch.Tensor, sar: torch.Tensor) -> torch.Tensor:
        opt_feat = self.opt_encoder(optical)
        sar_feat = self.sar_encoder(sar)

        cat_feat = torch.cat([opt_feat, sar_feat], dim=-1)
        gate = self.gate_layer(cat_feat)

        fused = gate * opt_feat + (1.0 - gate) * sar_feat
        return self.classifier(fused)


# ==============================================================================
# 3. Modern Model: Cross-Modal Cross-Attention Network
# ==============================================================================
class OpticalSARCrossAttentionNet(nn.Module):
    """
    Modern Architecture: Multihead Cross-Attention Network.
    Optical queries attend to SAR keys/values to extract radar surface structural context.
    Reference: Vaswani et al., 2017 / Multimodal Remote Sensing Cross-Attention.
    """
    def __init__(
        self,
        opt_channels: int = 3,
        sar_channels: int = 2,
        embed_dim: int = 64,
        num_heads: int = 4,
        num_classes: int = 10
    ):
        super().__init__()
        self.architecture_name = "OpticalSARCrossAttentionNet"
        self.fusion_type = "cross_attention"
        self.license = "MIT"

        self.opt_encoder = ModalityEncoder(opt_channels, embed_dim)
        self.sar_encoder = ModalityEncoder(sar_channels, embed_dim)

        self.cross_attn = nn.MultiheadAttention(
            embed_dim=embed_dim,
            num_heads=num_heads,
            batch_first=True
        )

        self.classifier = nn.Sequential(
            nn.Linear(embed_dim * 2, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )

    def forward(self, optical: torch.Tensor, sar: torch.Tensor) -> torch.Tensor:
        opt_feat = self.opt_encoder(optical).unsqueeze(1)  # (B, 1, C)
        sar_feat = self.sar_encoder(sar).unsqueeze(1)      # (B, 1, C)

        attn_out, _ = self.cross_attn(query=opt_feat, key=sar_feat, value=sar_feat)
        fused = torch.cat([opt_feat.squeeze(1), attn_out.squeeze(1)], dim=-1)
        return self.classifier(fused)


# ==============================================================================
# 4. Single-Sensor Ablation Baselines
# ==============================================================================
class OpticalOnlyBaseline(nn.Module):
    """Single-sensor ablation using only optical spectral channels."""
    def __init__(self, opt_channels: int = 3, embed_dim: int = 64, num_classes: int = 10):
        super().__init__()
        self.architecture_name = "OpticalOnlyBaseline"
        self.encoder = ModalityEncoder(opt_channels, embed_dim)
        self.classifier = nn.Sequential(
            nn.Linear(embed_dim, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, num_classes)
        )

    def forward(self, optical: torch.Tensor, sar: Optional[torch.Tensor] = None) -> torch.Tensor:
        feat = self.encoder(optical)
        return self.classifier(feat)


class SAROnlyBaseline(nn.Module):
    """Single-sensor ablation using only SAR microwave radar backscatter."""
    def __init__(self, sar_channels: int = 2, embed_dim: int = 64, num_classes: int = 10):
        super().__init__()
        self.architecture_name = "SAROnlyBaseline"
        self.encoder = ModalityEncoder(sar_channels, embed_dim)
        self.classifier = nn.Sequential(
            nn.Linear(embed_dim, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, num_classes)
        )

    def forward(self, sar: torch.Tensor, optical: Optional[torch.Tensor] = None) -> torch.Tensor:
        feat = self.encoder(sar)
        return self.classifier(feat)


# ==============================================================================
# 5. Factory Adapter
# ==============================================================================
def create_optical_sar_model(
    model_name: str,
    opt_channels: int = 3,
    sar_channels: int = 2,
    embed_dim: int = 64,
    num_classes: int = 10,
    **kwargs
) -> nn.Module:
    """
    Factory adapter producing the requested Optical-SAR fusion or ablation architecture.
    """
    key = model_name.lower().strip()
    if key in ["concat", "baseline", "concat_baseline"]:
        return OpticalSARConcatBaseline(opt_channels, sar_channels, embed_dim, num_classes)
    elif key in ["gated", "gated_fusion"]:
        return OpticalSARGatedFusionNet(opt_channels, sar_channels, embed_dim, num_classes)
    elif key in ["cross_attention", "cross_attn", "modern"]:
        num_heads = kwargs.get("num_heads", 4)
        return OpticalSARCrossAttentionNet(opt_channels, sar_channels, embed_dim, num_heads, num_classes)
    elif key in ["optical_only", "optical"]:
        return OpticalOnlyBaseline(opt_channels, embed_dim, num_classes)
    elif key in ["sar_only", "sar"]:
        return SAROnlyBaseline(sar_channels, embed_dim, num_classes)
    else:
        raise ValueError(
            f"Unknown Optical-SAR architecture '{model_name}'. "
            f"Supported options: 'concat', 'gated', 'cross_attention', 'optical_only', 'sar_only'."
        )
