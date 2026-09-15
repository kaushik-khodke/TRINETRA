"""
SatQuery AI / TRINETRA — HyperFree-B Hyperspectral Foundation Model Architecture
Channel-Adaptive Vision Transformer (ViT-B) for Hyperspectral Remote Sensing.
Supports arbitrary input band counts (e.g. 103, 144, 220, 224 bands) via Channel-Adaptive
Spectral Projection (CASP), multi-head self-attention, and downstream task decoders.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Optional, Tuple

class ChannelAdaptiveSpectralProjection(nn.Module):
    """
    Channel-Adaptive Spectral Projection (CASP) layer.
    Maps an arbitrary number of hyperspectral spectral bands C_in into a fixed
    embedding dimension (embed_dim=768) and spatial patch grid (patch_size=16).
    """
    def __init__(self, embed_dim: int = 768, patch_size: int = 16):
        super().__init__()
        self.embed_dim = embed_dim
        self.patch_size = patch_size
        # Spectral continuous mapping kernel
        self.spectral_fc = nn.Sequential(
            nn.Linear(1, 32),
            nn.ReLU(),
            nn.Linear(32, 64)
        )
        self.spatial_proj = nn.Conv2d(64, embed_dim, kernel_size=patch_size, stride=patch_size)
        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (Batch, C_in, H, W)
        Returns: (Batch, num_patches, embed_dim)
        """
        b, c, h, w = x.shape
        # Normalize band coordinate positions in [-1, 1]
        band_coords = torch.linspace(-1.0, 1.0, c, device=x.device, dtype=x.dtype).view(1, c, 1, 1, 1)
        
        # Spatial-spectral compression: map C_in channels to 64 feature planes
        # Reshape to (B, H, W, C_in, 1)
        x_perm = x.permute(0, 2, 3, 1).unsqueeze(-1)  # (B, H, W, C, 1)
        
        # Fast 1D adaptive spectral projection
        # If C is large, use adaptive 1D pooling along spectral axis into 64 channels
        x_b_hw = x.reshape(b, c, h * w)
        if c != 64:
            x_proj = F.adaptive_avg_pool1d(x_b_hw.permute(0, 2, 1), 64).permute(0, 2, 1)
        else:
            x_proj = x_b_hw
        x_64 = x_proj.reshape(b, 64, h, w)

        # Spatial patch embedding
        patches = self.spatial_proj(x_64)  # (B, embed_dim, H/P, W/P)
        patches = patches.flatten(2).transpose(1, 2)  # (B, num_patches, embed_dim)
        return self.norm(patches)

class TransformerEncoderBlock(nn.Module):
    def __init__(self, embed_dim: int = 768, num_heads: int = 12, mlp_ratio: float = 4.0, dropout: float = 0.05):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = nn.MultiheadAttention(embed_dim, num_heads, dropout=dropout, batch_first=True)
        self.norm2 = nn.LayerNorm(embed_dim)
        mlp_hidden_dim = int(embed_dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, mlp_hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_hidden_dim, embed_dim),
            nn.Dropout(dropout)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        attn_out, _ = self.attn(self.norm1(x), self.norm1(x), self.norm1(x))
        x = x + attn_out
        x = x + self.mlp(self.norm2(x))
        return x

class HyperFreeB(nn.Module):
    """
    HyperFree-B (ViT-B) Hyperspectral Foundation Network.
    Architecture:
    - CASP Channel-Adaptive Input Layer (Arbitrary band input C -> 768)
    - 12 Vision Transformer Encoder Blocks (ViT-B standard, 12 heads, dim 768)
    - Task-specific decoders:
        * Scene & Multi-label Land-cover Head (16 classes)
        * Pixel-level Land-cover Segmentation Head (16 classes)
        * Anomaly Feature Residual Head
    """
    def __init__(
        self,
        num_classes: int = 16,
        embed_dim: int = 768,
        depth: int = 12,
        num_heads: int = 12,
        patch_size: int = 16,
        max_patches: int = 1024
    ):
        super().__init__()
        self.num_classes = num_classes
        self.embed_dim = embed_dim
        self.patch_size = patch_size

        # Channel-Adaptive Spectral Projection
        self.spectral_patch_embed = ChannelAdaptiveSpectralProjection(embed_dim, patch_size)

        # Learnable Class token & Positional embeddings
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed = nn.Parameter(torch.zeros(1, max_patches + 1, embed_dim))
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.pos_embed, std=0.02)

        # ViT-B Transformer Backbone
        self.blocks = nn.ModuleList([
            TransformerEncoderBlock(embed_dim, num_heads) for _ in range(depth)
        ])
        self.norm = nn.LayerNorm(embed_dim)

        # Task Heads:
        # 1. Scene Classification Head
        self.scene_head = nn.Sequential(
            nn.Linear(embed_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, num_classes)
        )

        # 2. Pixel-level Segmentation Decoder Head
        self.seg_decoder = nn.Sequential(
            nn.ConvTranspose2d(embed_dim, 256, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.ConvTranspose2d(64, num_classes, kernel_size=4, stride=2, padding=1)
        )

        # 3. Anomaly Detection Residual Head
        self.anomaly_head = nn.Sequential(
            nn.Linear(embed_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(
        self,
        x: torch.Tensor,
        task: str = "classification"
    ) -> Dict[str, torch.Tensor]:
        """
        x: (Batch, C_in, H, W)
        task: 'classification', 'segmentation', 'anomaly', 'all'
        """
        b, c, h, w = x.shape
        tokens = self.spectral_patch_embed(x)  # (B, N, embed_dim)
        n = tokens.shape[1]

        cls_tokens = self.cls_token.expand(b, -1, -1)
        tokens = torch.cat((cls_tokens, tokens), dim=1)  # (B, N+1, embed_dim)

        pos_tokens = self.pos_embed[:, : n + 1, :]
        tokens = tokens + pos_tokens

        # Transformer blocks
        for block in self.blocks:
            tokens = block(tokens)
        tokens = self.norm(tokens)

        cls_rep = tokens[:, 0]  # (B, embed_dim)
        patch_reps = tokens[:, 1:]  # (B, N, embed_dim)

        out = {}

        if task in ["classification", "all"]:
            out["scene_logits"] = self.scene_head(cls_rep)
            out["scene_probs"] = torch.sigmoid(out["scene_logits"])

        if task in ["segmentation", "all"]:
            gh = h // self.patch_size
            gw = w // self.patch_size
            if gh * gw == n:
                spatial_feat = patch_reps.permute(0, 2, 1).reshape(b, self.embed_dim, gh, gw)
                seg_logits = self.seg_decoder(spatial_feat)
                seg_logits = F.interpolate(seg_logits, size=(h, w), mode="bilinear", align_corners=False)
                out["seg_logits"] = seg_logits
                out["seg_mask"] = torch.argmax(seg_logits, dim=1)

        if task in ["anomaly", "all"]:
            out["anomaly_scores"] = self.anomaly_head(patch_reps)

        return out

    def freeze_backbone_for_peft(self):
        """Freezes heavy ViT backbone; enables fine-tuning of task decoders & CASP."""
        for param in self.blocks.parameters():
            param.requires_grad = False
        self.cls_token.requires_grad = False
        self.pos_embed.requires_grad = False
        print("[HyperFreeB] Pretrained ViT-B backbone frozen for parameter-efficient adaptation.")
