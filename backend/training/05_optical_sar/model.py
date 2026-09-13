"""
TRINETRA / SatQuery AI — Optical + SAR Cross-Modal Architecture
Dual-encoder with multihead cross-attention fusion.
Also provides Optical-only and SAR-only baseline models for comparative benchmarking.
Matches backend/models/architectures.py for seamless deployment.
"""

import torch
import torch.nn as nn

class OpticalSARCrossAttentionNet(nn.Module):
    """
    Dual-sensor cross-attention architecture fusing Optical spectral channels (RGB/NIR)
    with SAR microwave radar backscatter intensity.
    """
    def __init__(self, opt_channels: int = 3, sar_channels: int = 2, embed_dim: int = 64, num_classes: int = 10):
        super().__init__()
        self.opt_encoder = nn.Sequential(
            nn.Conv2d(opt_channels, embed_dim, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.sar_encoder = nn.Sequential(
            nn.Conv2d(sar_channels, embed_dim, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.cross_attn = nn.MultiheadAttention(embed_dim=embed_dim, num_heads=1, batch_first=True)
        self.cross_fusion = nn.Sequential(
            nn.Linear(embed_dim * 2, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )

    def forward(self, optical: torch.Tensor, sar: torch.Tensor) -> torch.Tensor:
        opt_feat = self.opt_encoder(optical).flatten(1).unsqueeze(1)
        sar_feat = self.sar_encoder(sar).flatten(1).unsqueeze(1)
        attn_out, _ = self.cross_attn(opt_feat, sar_feat, sar_feat)
        fused = torch.cat([opt_feat.squeeze(1), attn_out.squeeze(1)], dim=-1)
        return self.cross_fusion(fused)

class OpticalOnlyBaseline(nn.Module):
    """Single-sensor baseline using only optical RGB imagery."""
    def __init__(self, opt_channels: int = 3, embed_dim: int = 64, num_classes: int = 10):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(opt_channels, embed_dim, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.head = nn.Sequential(
            nn.Linear(embed_dim, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes)
        )

    def forward(self, optical: torch.Tensor) -> torch.Tensor:
        feat = self.encoder(optical).flatten(1)
        return self.head(feat)

class SAROnlyBaseline(nn.Module):
    """Single-sensor baseline using only SAR microwave radar backscatter."""
    def __init__(self, sar_channels: int = 2, embed_dim: int = 64, num_classes: int = 10):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(sar_channels, embed_dim, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.head = nn.Sequential(
            nn.Linear(embed_dim, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes)
        )

    def forward(self, sar: torch.Tensor) -> torch.Tensor:
        feat = self.encoder(sar).flatten(1)
        return self.head(feat)
