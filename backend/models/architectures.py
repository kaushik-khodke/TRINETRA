"""
SatQuery AI — Neural Network Architectures
Production PyTorch neural network definitions for all specialist remote-sensing models.
These architectures match the Colab training scripts exactly and support state_dict loading.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Tuple, Optional

# ==============================================================================
# 1. BigEarthNet Remote-Sensing Adapted Backbone
# ==============================================================================
class BigEarthNetAdaptedResNet(nn.Module):
    """
    Adapted multi-spectral & SAR convolutional encoder trained on BigEarthNet.
    Supports arbitrary channel counts (e.g. 4-band RGB-NIR or 2-band SAR).
    Predicts 19 Corine Land Cover classes.
    """
    def __init__(self, in_channels: int = 4, num_classes: int = 19, embedding_dim: int = 256):
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes

        # Stem: adaptive projection for multispectral / SAR
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )

        # Residual Feature Extraction Blocks
        self.layer1 = self._make_res_block(64, 64)
        self.layer2 = self._make_res_block(64, 128, stride=2)
        self.layer3 = self._make_res_block(128, embedding_dim, stride=2)

        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Linear(embedding_dim, num_classes)

    def _make_res_block(self, in_c: int, out_c: int, stride: int = 1) -> nn.Sequential:
        downsample = None
        if stride != 1 or in_c != out_c:
            downsample = nn.Sequential(
                nn.Conv2d(in_c, out_c, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_c)
            )
        return nn.Sequential(
            nn.Conv2d(in_c, out_c, kernel_size=3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(out_c)
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        feat = self.stem(x)
        feat = self.layer1(feat)
        feat = self.layer2(feat)
        feat = self.layer3(feat)
        pooled = self.global_pool(feat).flatten(1)
        logits = self.classifier(pooled)
        return logits, pooled


# ==============================================================================
# 2. Remote-Sensing Visual Question Answering (RS-VQA) Network
# ==============================================================================
class RSVqaFusionNetwork(nn.Module):
    """
    Multimodal VQA architecture combining deep spatial visual features with query embeddings.
    """
    def __init__(self, vocab_size: int = 5000, num_answers: int = 120, text_dim: int = 128, img_dim: int = 256):
        super().__init__()
        self.visual_encoder = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, img_dim, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(img_dim),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.text_embedding = nn.Embedding(vocab_size, text_dim)
        self.text_encoder = nn.GRU(text_dim, text_dim, batch_first=True)

        # Bilinear Multimodal Fusion
        self.fusion = nn.Sequential(
            nn.Linear(img_dim + text_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.25),
            nn.Linear(256, num_answers)
        )

    def forward(self, img: torch.Tensor, token_ids: torch.Tensor) -> torch.Tensor:
        v_feat = self.visual_encoder(img).flatten(1)
        embed = self.text_embedding(token_ids)
        _, t_hidden = self.text_encoder(embed)
        t_feat = t_hidden.squeeze(0)

        fused = torch.cat([v_feat, t_feat], dim=-1)
        logits = self.fusion(fused)
        return logits


# ==============================================================================
# 3. Text-Guided Region Grounding Network
# ==============================================================================
class RSGroundingDetector(nn.Module):
    """
    Spatial localization network predicting normalized bounding boxes [ymin, xmin, ymax, xmax].
    """
    def __init__(self, vocab_size: int = 4000, text_dim: int = 64, feat_dim: int = 128):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, feat_dim, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(feat_dim),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.text_embed = nn.Embedding(vocab_size, text_dim)

        self.box_head = nn.Sequential(
            nn.Linear(feat_dim * 16 + text_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 4),
            nn.Sigmoid()  # Outputs [0, 1] normalized bounding box coordinates
        )

    def forward(self, img: torch.Tensor, tokens: torch.Tensor) -> torch.Tensor:
        b_feat = self.backbone(img).flatten(1)
        t_feat = self.text_embed(tokens).mean(dim=1)
        fused = torch.cat([b_feat, t_feat], dim=-1)
        raw = self.box_head(fused)
        # Enforce canonical [ymin, xmin, ymax, xmax] ordering where ymin < ymax and xmin < xmax
        y_min = torch.min(raw[:, 0], raw[:, 2])
        y_max = torch.max(raw[:, 0], raw[:, 2])
        x_min = torch.min(raw[:, 1], raw[:, 3])
        x_max = torch.max(raw[:, 1], raw[:, 3])

        # Guarantee non-zero positive area to eliminate inverted boxes
        y_max = torch.maximum(y_max, y_min + 1e-3).clamp(max=1.0)
        x_max = torch.maximum(x_max, x_min + 1e-3).clamp(max=1.0)

        return torch.stack([y_min, x_min, y_max, x_max], dim=-1)


# ==============================================================================
# 4. Bi-Temporal Siamese Change Differential Network
# ==============================================================================
# ==============================================================================
# 4. Bi-Temporal Siamese Change Differential Network
# ==============================================================================
class SiameseChangeDiffNet(nn.Module):
    """
    Siamese dual-stream network for bi-temporal remote-sensing observations.
    Computes absolute differential features and optional question conditioning
    to detect, ground, and classify temporal shifts.
    """
    def __init__(self, vocab_size: int = 5000, text_dim: int = 128, num_change_classes: int = 3):
        super().__init__()
        # Shared siamese weight encoder
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.text_embed = nn.Embedding(vocab_size, text_dim)
        self.text_encoder = nn.GRU(text_dim, text_dim, batch_first=True)
        self.diff_classifier = nn.Sequential(
            nn.Linear(64 * 16 * 2 + text_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_change_classes)  # 0: Unchanged, 1: Increased, 2: Decreased
        )

    def forward(self, t1: torch.Tensor, t2: torch.Tensor, tokens: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        f1 = self.encoder(t1).flatten(1)
        f2 = self.encoder(t2).flatten(1)
        diff = torch.abs(f2 - f1)
        if tokens is not None:
            emb = self.text_embed(tokens)
            _, h = self.text_encoder(emb)
            t_feat = h.squeeze(0)
        else:
            t_feat = torch.zeros(t1.size(0), 128, device=t1.device)
        cat_feat = torch.cat([diff, f2, t_feat], dim=-1)
        logits = self.diff_classifier(cat_feat)
        return logits, diff


# ==============================================================================
# 5. Cross-Modal Optical-SAR Fusion Network
# ==============================================================================
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
