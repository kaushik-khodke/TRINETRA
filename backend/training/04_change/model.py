"""
TRINETRA — Bi-Temporal Change Detection Models & Losses
Exposes:
1. SiameseUNetBaseline: Siamese U-Net difference baseline encoder-decoder.
2. BitemporalInteractionTransformer (BIT): Tokenized spatial-temporal interaction transformer.
3. HybridBCEDiceLoss: Mathematically rigorous loss for class-imbalanced change masks.
4. SiameseChangeDiffNet: Legacy 1D differential classifier (retained for backward compatibility).
Governed by Stage 4 Change Detection Protocol. Zero synthetic data.
"""

import sys
import os
from typing import Tuple, Optional, Dict, Any
import torch
import torch.nn as nn
import torch.nn.functional as F

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from models.change_models import (
    SiameseUNetBaseline,
    BitemporalInteractionTransformer,
    create_change_model
)


class DiceLoss(nn.Module):
    """
    Sørensen–Dice Loss for binary change detection masks.
    Penalizes contour and region overlap errors independently of background scale.
    """
    def __init__(self, smooth: float = 1.0, eps: float = 1e-7):
        super().__init__()
        self.smooth = smooth
        self.eps = eps

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        logits: (B, 1, H, W) or (B, H, W) unnormalized logits.
        targets: (B, 1, H, W) or (B, H, W) binary ground truth {0.0, 1.0}.
        """
        probs = torch.sigmoid(logits).view(-1)
        targets_flat = targets.view(-1).float()

        intersection = (probs * targets_flat).sum()
        cardinality = probs.sum() + targets_flat.sum()

        dice = (2.0 * intersection + self.smooth) / (cardinality + self.smooth + self.eps)
        return 1.0 - dice


class HybridBCEDiceLoss(nn.Module):
    """
    Combined Binary Cross-Entropy with Logits and Dice Loss.
    Combines pixel-wise calibration with global intersection-over-union optimization.
    Formula: L = bce_weight * BCEWithLogits + dice_weight * DiceLoss
    """
    def __init__(self, bce_weight: float = 0.5, dice_weight: float = 0.5, pos_weight: Optional[float] = None):
        super().__init__()
        self.bce_weight = bce_weight
        self.dice_weight = dice_weight
        pw = torch.tensor([pos_weight]) if pos_weight is not None else None
        self.bce = nn.BCEWithLogitsLoss(pos_weight=pw)
        self.dice = DiceLoss()

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce_loss = self.bce(logits, targets.float())
        dice_loss = self.dice(logits, targets.float())
        return self.bce_weight * bce_loss + self.dice_weight * dice_loss


# Legacy 1D differential classifier retained for backward compatibility
class SiameseChangeDiffNet(nn.Module):
    """
    Legacy 1D Siamese differential network for change class prediction.
    """
    def __init__(self, vocab_size: int = 5000, text_dim: int = 128, num_change_classes: int = 3):
        super().__init__()
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
            nn.Linear(256, num_change_classes)
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
