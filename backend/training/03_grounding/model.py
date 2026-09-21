"""
TRINETRA / SatQuery AI — Text-Guided Region Grounding Network
Upgraded Spatial localization network predicting normalized bounding boxes [ymin, xmin, ymax, xmax].
Features a 4-stage Residual Convolutional Backbone, Bidirectional GRU language encoder,
Feature-wise Linear Modulation (FiLM) cross-modal conditioning, and Compound L1 + GIoU + DIoU loss.
Fully compatible with SatQuery backend model loader.
"""

import torch
import torch.nn as nn


class ResBlock(nn.Module):
    """Residual convolutional block with identity/projection skip connection."""
    def __init__(self, in_c: int, out_c: int, stride: int = 1):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_c, out_c, kernel_size=3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(out_c)
        )
        self.skip = nn.Sequential(
            nn.Conv2d(in_c, out_c, kernel_size=1, stride=stride, bias=False),
            nn.BatchNorm2d(out_c)
        ) if in_c != out_c or stride != 1 else nn.Identity()
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(self.conv(x) + self.skip(x))


class RSGroundingDetector(nn.Module):
    """
    Spatial localization network predicting normalized bounding boxes [ymin, xmin, ymax, xmax].
    Matches backend/models/architectures.py for seamless deployment.
    """
    def __init__(self, vocab_size: int = 4000, text_dim: int = 128):
        super().__init__()
        # 4-stage Residual Convolutional Backbone
        self.stem = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )
        self.stage1 = ResBlock(64, 64)
        self.stage2 = nn.Sequential(ResBlock(64, 128, stride=2), ResBlock(128, 128))
        self.stage3 = nn.Sequential(ResBlock(128, 256, stride=2), ResBlock(256, 256))
        self.stage4 = nn.Sequential(ResBlock(256, 256, stride=2), ResBlock(256, 256))

        # Bidirectional GRU Text Sequence Encoder
        self.text_embed = nn.Embedding(vocab_size, text_dim)
        self.gru = nn.GRU(text_dim, text_dim // 2, batch_first=True, bidirectional=True)

        # Feature-wise Linear Modulation (FiLM)
        self.film_gen = nn.Linear(text_dim, 256 * 2)

        # Multi-scale spatial pooling & regression head
        self.pool = nn.AdaptiveAvgPool2d((2, 2))
        self.box_head = nn.Sequential(
            nn.Linear(256 * 4 + text_dim, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 4),
            nn.Sigmoid()  # Normalizes to [0, 1] bounds
        )

    def forward(self, img: torch.Tensor, tokens: torch.Tensor) -> torch.Tensor:
        # Visual feature extraction
        x = self.stem(img)
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.stage3(x)
        feat_map = self.stage4(x)  # (B, 256, 7, 7)

        # Text sequence representation
        _, h_n = self.gru(self.text_embed(tokens))
        t_feat = torch.cat([h_n[0], h_n[1]], dim=-1)  # (B, text_dim)

        # FiLM cross-modal conditioning
        film = self.film_gen(t_feat).unsqueeze(-1).unsqueeze(-1)
        gamma, beta = film[:, :256], film[:, 256:]
        modulated = (1.0 + gamma) * feat_map + beta

        # Spatial fusion & box coordinate prediction
        spatial_fused = torch.cat([self.pool(modulated).flatten(1), t_feat], dim=-1)
        raw = self.box_head(spatial_fused)

        # Canonical [ymin, xmin, ymax, xmax] enforcement
        ymin = torch.min(raw[:, 0], raw[:, 2])
        ymax = torch.maximum(torch.max(raw[:, 0], raw[:, 2]), ymin + 1e-3).clamp(max=1.0)
        xmin = torch.min(raw[:, 1], raw[:, 3])
        xmax = torch.maximum(torch.max(raw[:, 1], raw[:, 3]), xmin + 1e-3).clamp(max=1.0)

        return torch.stack([ymin, xmin, ymax, xmax], dim=-1)


class CompoundGroundingLoss(nn.Module):
    """Compound SmoothL1 + GIoU + DIoU loss for robust bounding box regression."""
    def __init__(self, l1_weight: float = 2.0, giou_weight: float = 1.0, diou_weight: float = 1.0):
        super().__init__()
        self.l1_weight = l1_weight
        self.giou_weight = giou_weight
        self.diou_weight = diou_weight
        self.smooth_l1 = nn.SmoothL1Loss()

    def forward(self, preds: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        p_y1, p_y2 = torch.min(preds[:, 0], preds[:, 2]), torch.max(preds[:, 0], preds[:, 2])
        p_x1, p_x2 = torch.min(preds[:, 1], preds[:, 3]), torch.max(preds[:, 1], preds[:, 3])
        t_y1, t_y2 = torch.min(targets[:, 0], targets[:, 2]), torch.max(targets[:, 0], targets[:, 2])
        t_x1, t_x2 = torch.min(targets[:, 1], targets[:, 3]), torch.max(targets[:, 1], targets[:, 3])

        inter_y1 = torch.max(p_y1, t_y1)
        inter_x1 = torch.max(p_x1, t_x1)
        inter_y2 = torch.min(p_y2, t_y2)
        inter_x2 = torch.min(p_x2, t_x2)

        inter_w = torch.clamp(inter_x2 - inter_x1, min=0)
        inter_h = torch.clamp(inter_y2 - inter_y1, min=0)
        inter_area = inter_w * inter_h

        pred_area = (p_x2 - p_x1) * (p_y2 - p_y1)
        target_area = (t_x2 - t_x1) * (t_y2 - t_y1)
        union_area = pred_area + target_area - inter_area + 1e-7

        iou = inter_area / union_area

        # Smallest enclosing box
        enc_y1 = torch.min(p_y1, t_y1)
        enc_x1 = torch.min(p_x1, t_x1)
        enc_y2 = torch.max(p_y2, t_y2)
        enc_x2 = torch.max(p_x2, t_x2)
        enc_w = enc_x2 - enc_x1
        enc_h = enc_y2 - enc_y1
        enc_area = enc_w * enc_h + 1e-7
        giou = iou - (enc_area - union_area) / enc_area
        giou_loss = torch.mean(1.0 - giou)

        # DIoU: Center distance penalty
        p_yc, p_xc = (p_y1 + p_y2) / 2.0, (p_x1 + p_x2) / 2.0
        t_yc, t_xc = (t_y1 + t_y2) / 2.0, (t_x1 + t_x2) / 2.0
        rho2 = (p_xc - t_xc)**2 + (p_yc - t_yc)**2
        c2 = enc_w**2 + enc_h**2 + 1e-7
        diou = iou - (rho2 / c2)
        diou_loss = torch.mean(1.0 - diou)

        l1_loss = self.smooth_l1(preds, targets)
        return self.l1_weight * l1_loss + self.giou_weight * giou_loss + self.diou_weight * diou_loss


# Alias for backward compatibility
GiouLoss = CompoundGroundingLoss
