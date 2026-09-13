"""
TRINETRA / SatQuery AI — Text-Guided Region Grounding Network
Spatial localization network predicting normalized bounding boxes [ymin, xmin, ymax, xmax].
Fully compatible with SatQuery backend model loader.
"""

import torch
import torch.nn as nn

class RSGroundingDetector(nn.Module):
    """
    Spatial localization network predicting normalized bounding boxes [ymin, xmin, ymax, xmax].
    Matches backend/models/architectures.py for seamless deployment.
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
        return self.box_head(fused)

class GiouLoss(nn.Module):
    """Generalized IoU loss for bounding box regression."""
    def forward(self, preds: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # Format: [ymin, xmin, ymax, xmax]
        pred_y1, pred_x1, pred_y2, pred_x2 = preds[:, 0], preds[:, 1], preds[:, 2], preds[:, 3]
        target_y1, target_x1, target_y2, target_x2 = targets[:, 0], targets[:, 1], targets[:, 2], targets[:, 3]

        inter_y1 = torch.max(pred_y1, target_y1)
        inter_x1 = torch.max(pred_x1, target_x1)
        inter_y2 = torch.min(pred_y2, target_y2)
        inter_x2 = torch.min(pred_x2, target_x2)

        inter_area = torch.clamp(inter_x2 - inter_x1, min=0) * torch.clamp(inter_y2 - inter_y1, min=0)
        area_pred = torch.clamp(pred_x2 - pred_x1, min=0) * torch.clamp(pred_y2 - pred_y1, min=0)
        area_target = torch.clamp(target_x2 - target_x1, min=0) * torch.clamp(target_y2 - target_y1, min=0)
        union_area = area_pred + area_target - inter_area + 1e-7

        iou = inter_area / union_area

        # Smallest enclosing box
        enc_y1 = torch.min(pred_y1, target_y1)
        enc_x1 = torch.min(pred_x1, target_x1)
        enc_y2 = torch.max(pred_y2, target_y2)
        enc_x2 = torch.max(pred_x2, target_x2)
        enc_area = torch.clamp(enc_x2 - enc_x1, min=0) * torch.clamp(enc_y2 - enc_y1, min=0) + 1e-7

        giou = iou - (enc_area - union_area) / enc_area
        return torch.mean(1.0 - giou)
