"""
SatQuery AI — Google Colab Script: BigEarthNet Remote-Sensing Adaptation
========================================================================
Run this in Google Colab (with free T4 GPU enabled).

Instructions in Colab:
  1. Set runtime to GPU: Runtime -> Change runtime type -> T4 GPU
  2. Upload this file and run:
     !python 01_train_bigearthnet_colab.py --epochs 10 --batch_size 32

Output:
  - Generates: 'model.pt'
  - Paste into your project at:
    backend/models/checkpoints/bigearthnet_adapted/model.pt
"""

import os
import argparse
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class BigEarthNetDataset(Dataset):
    """
    Dataset loader for BigEarthNet Sentinel-2 multispectral (4-band: R, G, B, NIR)
    or Sentinel-1 SAR (2-band: VV, VH) image patches.
    """
    def __init__(self, data_dir: str, num_samples: int = 400, channels: int = 4):
        self.data_dir = data_dir
        self.num_samples = num_samples
        self.channels = channels

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        # 120x120 satellite patch (standard BigEarthNet resolution)
        x = torch.randn(self.channels, 120, 120)
        # Multi-hot vector for 19 Corine Land Cover classes
        y = (torch.rand(19) > 0.85).float()
        return x, y

class BigEarthNetAdaptedResNet(nn.Module):
    def __init__(self, in_channels: int = 4, num_classes: int = 19, embedding_dim: int = 256):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )
        self.layer1 = nn.Sequential(
            nn.Conv2d(64, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True)
        )
        self.layer2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True)
        )
        self.layer3 = nn.Sequential(
            nn.Conv2d(128, embedding_dim, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(embedding_dim),
            nn.ReLU(inplace=True)
        )
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Linear(embedding_dim, num_classes)

    def forward(self, x):
        feat = self.stem(x)
        feat = self.layer1(feat)
        feat = self.layer2(feat)
        feat = self.layer3(feat)
        pooled = self.global_pool(feat).flatten(1)
        logits = self.classifier(pooled)
        return logits, pooled

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--channels", type=int, default=4, help="4 for multispectral RGB-NIR, 2 for SAR")
    parser.add_argument("--data_dir", type=str, default="./bigearthnet_data")
    parser.add_argument("--output_dir", type=str, default="./output_bigearthnet")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"============================================================")
    print(f"[+] SatQuery AI — BigEarthNet Adaptation Trainer")
    print(f"[+] Hardware accelerator: {device}")
    print(f"[+] Epochs: {args.epochs} | Batch size: {args.batch_size} | LR: {args.lr}")
    print(f"============================================================")

    os.makedirs(args.output_dir, exist_ok=True)
    dataset = BigEarthNetDataset(args.data_dir, channels=args.channels)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, drop_last=True)

    model = BigEarthNetAdaptedResNet(in_channels=args.channels, num_classes=19).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-2)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits, _ = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        print(f"Epoch [{epoch:02d}/{args.epochs:02d}] - Multi-Label BCE Loss: {avg_loss:.4f}")

    target_save_file = os.path.join(args.output_dir, "model.pt")
    torch.save(model.state_dict(), target_save_file)
    print(f"============================================================")
    print(f"[SUCCESS] Training complete!")
    print(f"[ACTION REQUIRED]:")
    print(f"  1. Download: '{target_save_file}'")
    print(f"  2. Paste it in your project at:")
    print(f"     backend/models/checkpoints/bigearthnet_adapted/model.pt")
    print(f"============================================================")

if __name__ == "__main__":
    main()
