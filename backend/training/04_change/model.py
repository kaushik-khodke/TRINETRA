"""
TRINETRA / SatQuery AI — Bi-Temporal Siamese Change Differential Network
Dual-stream shared-weight encoder with absolute difference classifier and optional text conditioning.
Matches backend/models/architectures.py for seamless deployment.
"""

from typing import Tuple, Optional
import torch
import torch.nn as nn

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
