"""
TRINETRA — Bi-Temporal Change Detection Architectures
Implements:
1. Baseline: SiameseUNetBaseline (reproducible reference encoder-decoder).
2. Modern Model: BitemporalInteractionTransformer (BIT) with spatial-temporal token cross-attention.
3. ChangeModelAdapter: unified adapter factory for clean model swapping.
Governed by 04_STAGE_4_CHANGE_DETECTION.md. Zero synthetic data.
"""

import math
from typing import Tuple, Optional, Dict, Any, Literal
import torch
import torch.nn as nn
import torch.nn.functional as F


# ==============================================================================
# 1. Baseline Model: Siamese U-Net Change Detector (FC-Siam-Diff style)
# ==============================================================================
class DoubleConvBlock(nn.Module):
    """(Conv2D -> BatchNorm -> ReLU) * 2 with residual connection."""
    def __init__(self, in_c: int, out_c: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_c, out_c, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
        )
        self.residual = nn.Conv2d(in_c, out_c, kernel_size=1, bias=False) if in_c != out_c else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x) + self.residual(x)


class SiameseUNetBaseline(nn.Module):
    """
    Conventional Baseline Architecture: Siamese U-Net Encoder-Decoder.
    Features:
    - Shared convolutional encoder for T1 and T2
    - Multi-scale absolute differential fusion: |f2 - f1|
    - Transposed convolution decoder with skip connections
    - Dense binary change mask logits: (B, 1, H, W)
    Reference: Daudt et al., 'Fully Convolutional Siamese Networks for Change Detection', 2018.
    """
    def __init__(self, in_channels: int = 3, num_classes: int = 1, base_channels: int = 32):
        super().__init__()
        self.architecture_name = "SiameseUNetBaseline"
        self.paper_reference = "Daudt et al., 2018 (Fully Convolutional Siamese Difference)"
        self.license = "MIT"

        # Shared Siamese Encoder
        self.enc1 = DoubleConvBlock(in_channels, base_channels)
        self.pool1 = nn.MaxPool2d(2)

        self.enc2 = DoubleConvBlock(base_channels, base_channels * 2)
        self.pool2 = nn.MaxPool2d(2)

        self.enc3 = DoubleConvBlock(base_channels * 2, base_channels * 4)
        self.pool3 = nn.MaxPool2d(2)

        self.bottleneck = DoubleConvBlock(base_channels * 4, base_channels * 8)

        # Decoder with skip connections from absolute difference features
        self.up3 = nn.ConvTranspose2d(base_channels * 8, base_channels * 4, kernel_size=2, stride=2)
        self.dec3 = DoubleConvBlock(base_channels * 8, base_channels * 4)

        self.up2 = nn.ConvTranspose2d(base_channels * 4, base_channels * 2, kernel_size=2, stride=2)
        self.dec2 = DoubleConvBlock(base_channels * 4, base_channels * 2)

        self.up1 = nn.ConvTranspose2d(base_channels * 2, base_channels, kernel_size=2, stride=2)
        self.dec1 = DoubleConvBlock(base_channels * 2, base_channels)

        # Final 1x1 convolution head producing pixel change logits
        self.head = nn.Conv2d(base_channels, num_classes, kernel_size=1)

    def forward_encoder(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))
        bot = self.bottleneck(self.pool3(e3))
        return e1, e2, e3, bot

    def forward(self, t1: torch.Tensor, t2: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for bi-temporal image pair.
        t1, t2: (B, C, H, W)
        Returns: logits of shape (B, 1, H, W)
        """
        e1_1, e2_1, e3_1, bot_1 = self.forward_encoder(t1)
        e1_2, e2_2, e3_2, bot_2 = self.forward_encoder(t2)

        # Multi-scale absolute feature differencing
        diff_bot = torch.abs(bot_2 - bot_1)
        diff_e3 = torch.abs(e3_2 - e3_1)
        diff_e2 = torch.abs(e2_2 - e2_1)
        diff_e1 = torch.abs(e1_2 - e1_1)

        d3 = self.up3(diff_bot)
        d3 = torch.cat([d3, diff_e3], dim=1)
        d3 = self.dec3(d3)

        d2 = self.up2(d3)
        d2 = torch.cat([d2, diff_e2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        d1 = torch.cat([d1, diff_e1], dim=1)
        d1 = self.dec1(d1)

        logits = self.head(d1)
        return logits


# ==============================================================================
# 2. Modern Model: Bitemporal Interaction Transformer (BIT)
# ==============================================================================
class SpatialTemporalTokenizer(nn.Module):
    """
    Extracts L semantic visual tokens from spatial feature maps via learned attention pooling.
    Input: (B, C, H, W) -> Output: (B, L, C)
    """
    def __init__(self, in_channels: int, token_len: int = 4):
        super().__init__()
        self.token_len = token_len
        self.pool_conv = nn.Conv2d(in_channels, token_len, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        # Compute spatial attention weights: (B, L, H*W)
        attn = self.pool_conv(x).view(b, self.token_len, -1)
        attn = F.softmax(attn, dim=-1)
        # Reshape features: (B, C, H*W)
        x_flat = x.view(b, c, -1)
        # Token representations: (B, L, C)
        tokens = torch.bmm(attn, x_flat.transpose(1, 2))
        return tokens


class TransformerInteractionBlock(nn.Module):
    """Multi-Head Self-Attention + Cross-Temporal Attention Block."""
    def __init__(self, dim: int, num_heads: int = 4, mlp_ratio: float = 2.0):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(dim, num_heads=num_heads, batch_first=True)
        self.norm1 = nn.LayerNorm(dim)

        self.cross_attn = nn.MultiheadAttention(dim, num_heads=num_heads, batch_first=True)
        self.norm2 = nn.LayerNorm(dim)

        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(dim, mlp_hidden_dim),
            nn.GELU(),
            nn.Linear(mlp_hidden_dim, dim)
        )
        self.norm3 = nn.LayerNorm(dim)

    def forward(self, q: torch.Tensor, k_cross: torch.Tensor) -> torch.Tensor:
        # Self-attention
        sa_out, _ = self.self_attn(q, q, q)
        q = self.norm1(q + sa_out)

        # Cross-temporal interaction attention
        ca_out, _ = self.cross_attn(q, k_cross, k_cross)
        q = self.norm2(q + ca_out)

        # MLP feedforward
        mlp_out = self.mlp(q)
        q = self.norm3(q + mlp_out)
        return q


class TokenToPixelDecoder(nn.Module):
    """
    Projects spatiotemporal tokens back into the spatial pixel domain.
    Y = Softmax(X * Tokens^T) * Tokens
    """
    def __init__(self, dim: int):
        super().__init__()
        self.proj = nn.Conv2d(dim, dim, kernel_size=1)
        self.norm = nn.BatchNorm2d(dim)

    def forward(self, x: torch.Tensor, tokens: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        x_proj = self.proj(x).view(b, c, -1)  # (B, C, HW)
        # Token attention over pixels: (B, HW, L)
        attn = torch.bmm(x_proj.transpose(1, 2), tokens.transpose(1, 2)) / math.sqrt(c)
        attn = F.softmax(attn, dim=-1)
        # Project tokens to spatial map: (B, HW, C) -> (B, C, H, W)
        projected = torch.bmm(attn, tokens).transpose(1, 2).view(b, c, h, w)
        return self.norm(projected + x)


class BitemporalInteractionTransformer(nn.Module):
    """
    Modern Architecture: Bitemporal Interaction Transformer (BIT).
    Features:
    - Shallow CNN feature stem for efficient representation learning
    - Spatial-temporal context tokenizer (L visual tokens per observation)
    - Dual-stream Transformer Interaction module
    - Token-to-pixel projection decoder
    - Dense pixel change prediction logits: (B, 1, H, W)
    Reference: Chen & Shi, 'Remote Sensing Image Change Detection with Transformers', IEEE TGRS 2021.
    License: MIT
    """
    def __init__(
        self,
        in_channels: int = 3,
        num_classes: int = 1,
        embed_dim: int = 64,
        token_len: int = 4,
        num_layers: int = 2,
        num_heads: int = 4
    ):
        super().__init__()
        self.architecture_name = "BitemporalInteractionTransformer"
        self.paper_reference = "Chen & Shi, IEEE TGRS 2021 (BIT: Bitemporal Image Transformer)"
        self.license = "MIT"

        # Shared CNN Backbone Stem (stride 4 reduction)
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, embed_dim, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(inplace=True),
        )

        # Context Tokenizers
        self.tokenizer1 = SpatialTemporalTokenizer(embed_dim, token_len=token_len)
        self.tokenizer2 = SpatialTemporalTokenizer(embed_dim, token_len=token_len)

        # Spatiotemporal Transformer Blocks
        self.t1_layers = nn.ModuleList([
            TransformerInteractionBlock(embed_dim, num_heads=num_heads) for _ in range(num_layers)
        ])
        self.t2_layers = nn.ModuleList([
            TransformerInteractionBlock(embed_dim, num_heads=num_heads) for _ in range(num_layers)
        ])

        # Token-to-Pixel Projection Decoders
        self.decoder1 = TokenToPixelDecoder(embed_dim)
        self.decoder2 = TokenToPixelDecoder(embed_dim)

        # Difference fusion head with bilinear upsampling back to (H, W)
        self.diff_head = nn.Sequential(
            nn.Conv2d(embed_dim * 2, embed_dim, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(inplace=True),
            nn.Conv2d(embed_dim, num_classes, kernel_size=1)
        )

    def forward(self, t1: torch.Tensor, t2: torch.Tensor) -> torch.Tensor:
        orig_h, orig_w = t1.shape[2:]

        # 1. Feature stem
        f1 = self.stem(t1)  # (B, embed_dim, H/4, W/4)
        f2 = self.stem(t2)

        # 2. Tokenize spatial maps into compact visual tokens
        tok1 = self.tokenizer1(f1)  # (B, L, embed_dim)
        tok2 = self.tokenizer2(f2)

        # 3. Transformer cross-temporal interaction
        for l1, l2 in zip(self.t1_layers, self.t2_layers):
            tok1 = l1(tok1, tok2)
            tok2 = l2(tok2, tok1)

        # 4. Project interacted tokens back into pixel space
        y1 = self.decoder1(f1, tok1)
        y2 = self.decoder2(f2, tok2)

        # 5. Differential fusion: absolute difference + concatenation
        diff = torch.abs(y2 - y1)
        fused = torch.cat([diff, y2], dim=1)
        low_res_logits = self.diff_head(fused)

        # 6. Upsample to original image resolution
        logits = F.interpolate(low_res_logits, size=(orig_h, orig_w), mode="bilinear", align_corners=False)
        return logits


# ==============================================================================
# 3. Model Adapter Factory
# ==============================================================================
def create_change_model(
    architecture: Literal["baseline", "modern_bit", "bit"] = "modern_bit",
    in_channels: int = 3,
    num_classes: int = 1
) -> nn.Module:
    """
    Factory creating either the conventional Siamese baseline or the modern BIT architecture.
    """
    arch = architecture.lower()
    if arch in ["baseline", "siamese_unet"]:
        return SiameseUNetBaseline(in_channels=in_channels, num_classes=num_classes)
    elif arch in ["modern_bit", "bit", "transformer"]:
        return BitemporalInteractionTransformer(in_channels=in_channels, num_classes=num_classes)
    else:
        raise ValueError(f"Unknown change detection architecture: {architecture}. Must be 'baseline' or 'modern_bit'.")
