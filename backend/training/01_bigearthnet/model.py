"""
TRINETRA / SatQuery AI — BigEarthNet Model Architecture
Multi-spectral adapted ResNet18 and ImageNet-pretrained baseline for land-cover classification.
"""

import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights

class BigEarthNetAdaptedResNet(nn.Module):
    """
    ResNet18 adapted for multi-spectral remote-sensing imagery (e.g. 4-band RGB-NIR or 12-band).
    Initializes input conv weights from ImageNet RGB channels, averaging across NIR/SWIR bands.
    """
    def __init__(self, in_channels: int = 4, num_classes: int = 19, pretrained: bool = True):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        base = resnet18(weights=weights)

        # Adapt first conv layer for in_channels
        old_conv = base.conv1
        new_conv = nn.Conv2d(
            in_channels,
            old_conv.out_channels,
            kernel_size=old_conv.kernel_size,
            stride=old_conv.stride,
            padding=old_conv.padding,
            bias=False
        )

        with torch.no_grad():
            if in_channels == 3:
                new_conv.weight.copy_(old_conv.weight)
            else:
                # Copy RGB weights to first 3 channels
                new_conv.weight[:, :3, :, :].copy_(old_conv.weight)
                # Initialize remaining channels with mean of RGB weights
                mean_w = old_conv.weight.mean(dim=1, keepdim=True)
                for c in range(3, in_channels):
                    new_conv.weight[:, c:c+1, :, :].copy_(mean_w)

        base.conv1 = new_conv
        in_features = base.fc.in_features
        base.fc = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(in_features, num_classes)
        )
        self.model = base

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

def get_baseline_rgb_model(num_classes: int = 19) -> nn.Module:
    """Returns an ImageNet-pretrained standard RGB ResNet18 baseline."""
    return BigEarthNetAdaptedResNet(in_channels=3, num_classes=num_classes, pretrained=True)
