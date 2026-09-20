"""
TRINETRA / SatQuery AI — RS-VQA Multimodal Architectures
Provides both the production RSVqaFusionNetwork and the advanced
RSVqaResNetFusionNetwork (transfer learning visual backbone).
Fully compatible with SatQuery backend model loader.
"""

import os
import sys
import torch
import torch.nn as nn
import torchvision.models as models
from typing import Tuple, Union, Dict, Optional, List

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


class RSVqaFusionNetwork(nn.Module):
    """
    Multimodal VQA architecture combining deep spatial visual features with query embeddings.
    Matches backend/models/architectures.py exactly for 100% plug-and-play production compatibility.
    """
    def __init__(self, vocab_size: int = 5000, num_answers: int = 147, text_dim: int = 128, img_dim: int = 256):
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
        t_feat = t_hidden[-1]  # [batch_size, text_dim]

        fused = torch.cat([v_feat, t_feat], dim=-1)
        logits = self.fusion(fused)
        return logits


class RSVqaResNetFusionNetwork(nn.Module):
    """
    Modern candidate architecture utilizing a pretrained ResNet backbone with
    multimodal cross-feature fusion and question conditioning.
    """
    def __init__(self, vocab_size: int = 5000, num_answers: int = 147, text_dim: int = 128, pretrained: bool = True):
        super().__init__()
        try:
            weights = models.ResNet18_Weights.DEFAULT if pretrained else None
            base_resnet = models.resnet18(weights=weights)
        except Exception:
            base_resnet = models.resnet18(weights=None)

        # Truncate classifier and pool to get 512-dim visual features
        self.visual_encoder = nn.Sequential(*list(base_resnet.children())[:-1])

        self.text_embedding = nn.Embedding(vocab_size, text_dim)
        self.text_encoder = nn.GRU(text_dim, text_dim, batch_first=True, bidirectional=True)

        # Cross-modal projection & fusion
        self.fusion = nn.Sequential(
            nn.Linear(512 + text_dim * 2, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_answers)
        )

    def forward(self, img: torch.Tensor, token_ids: torch.Tensor) -> torch.Tensor:
        v_feat = self.visual_encoder(img).flatten(1)  # [B, 512]
        embed = self.text_embedding(token_ids)
        _, t_hidden = self.text_encoder(embed)
        # Bidirectional concatenation: [B, text_dim * 2]
        t_feat = torch.cat([t_hidden[-2], t_hidden[-1]], dim=-1)

        fused = torch.cat([v_feat, t_feat], dim=-1)
        logits = self.fusion(fused)
        return logits


def create_vqa_model(model_name: str = "baseline", vocab_size: int = 5000, num_answers: int = 147) -> nn.Module:
    """Factory function for VQA models."""
    name = model_name.lower().strip()
    if name in ["resnet", "modern", "candidate", "resnet18"]:
        return RSVqaResNetFusionNetwork(vocab_size=vocab_size, num_answers=num_answers)
    else:
        return RSVqaFusionNetwork(vocab_size=vocab_size, num_answers=num_answers)


def load_vqa_model(checkpoint: Union[str, Dict[str, torch.Tensor]], device: Optional[torch.device] = None) -> nn.Module:
    """
    Intelligently inspects checkpoint state_dict and instantiates the correct architecture.
    Fully supports both RSVqaFusionNetwork and RSVqaResNetFusionNetwork.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if isinstance(checkpoint, str):
        state_dict = torch.load(checkpoint, map_location=device, weights_only=True)
    else:
        state_dict = checkpoint

    vocab_size = state_dict.get("text_embedding.weight", torch.zeros(5000, 128)).shape[0]
    keys = list(state_dict.keys())
    keys_str = " ".join(keys)

    # Unambiguous architecture detection:
    # RSVqaResNetFusionNetwork has bidirectional GRU (reverse weights) and fusion.0 in_features=768
    is_resnet = False
    if "text_encoder.weight_ih_l0_reverse" in state_dict:
        is_resnet = True
    elif "fusion.0.weight" in state_dict and state_dict["fusion.0.weight"].shape[1] == 768:
        is_resnet = True
    elif "visual_encoder.0.weight" in state_dict and state_dict["visual_encoder.0.weight"].shape[2] == 7:
        is_resnet = True

    if is_resnet:
        num_answers = 147
        if "fusion.4.weight" in state_dict:
            num_answers = state_dict["fusion.4.weight"].shape[0]
        model = RSVqaResNetFusionNetwork(vocab_size=vocab_size, num_answers=num_answers, pretrained=False)
    else:
        num_answers = 147
        if "fusion.3.weight" in state_dict:
            num_answers = state_dict["fusion.3.weight"].shape[0]
        model = RSVqaFusionNetwork(vocab_size=vocab_size, num_answers=num_answers)

    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model

