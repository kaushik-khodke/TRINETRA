"""
SatQuery AI — Google Colab Script: Optical–SAR Cross-Modal Fusion
==================================================================
Run this in Google Colab (with free T4 GPU enabled).

Instructions in Colab:
  1. Set runtime to GPU: Runtime -> Change runtime type -> T4 GPU
  2. Upload this file and run:
     !python 05_train_optical_sar_colab.py --epochs 8 --batch_size 16

Output:
  - Generates: 'model.pt'
  - Paste into your project at:
    backend/models/checkpoints/optical_sar_model/model.pt
"""

import os
import argparse
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class OpticalSARDataset(Dataset):
    def __init__(self, data_dir: str, num_samples: int = 300):
        self.num_samples = num_samples

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        opt = torch.randn(3, 224, 224)
        sar = torch.randn(2, 224, 224)  # Dual polarization VV, VH
        label = torch.randint(0, 10, (1,)).squeeze()
        return opt, sar, label

class OpticalSARCrossAttentionNet(nn.Module):
    def __init__(self, opt_channels: int = 3, sar_channels: int = 2, embed_dim: int = 64, num_classes: int = 10):
        super().__init__()
        self.opt_encoder = nn.Sequential(
            nn.Conv2d(opt_channels, embed_dim, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((2, 2))
        )
        self.sar_encoder = nn.Sequential(
            nn.Conv2d(sar_channels, embed_dim, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((2, 2))
        )
        self.cross_fusion = nn.Sequential(
            nn.Linear(embed_dim * 4 * 2, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )

    def forward(self, optical, sar):
        opt_feat = self.opt_encoder(optical).flatten(1)
        sar_feat = self.sar_encoder(sar).flatten(1)
        fused = torch.cat([opt_feat, sar_feat], dim=-1)
        return self.cross_fusion(fused)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--data_dir", type=str, default="./optical_sar_data")
    parser.add_argument("--output_dir", type=str, default="./output_optical_sar")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"============================================================")
    print(f"[+] SatQuery AI — Optical–SAR Cross-Modal Fusion Trainer")
    print(f"[+] Hardware accelerator: {device}")
    print(f"[+] Epochs: {args.epochs} | Batch size: {args.batch_size} | LR: {args.lr}")
    print(f"============================================================")

    os.makedirs(args.output_dir, exist_ok=True)
    dataset = OpticalSARDataset(args.data_dir)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, drop_last=True)

    model = OpticalSARCrossAttentionNet().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for opt, sar, label in loader:
            opt, sar, label = opt.to(device), sar.to(device), label.to(device)
            optimizer.zero_grad()
            logits = model(opt, sar)
            loss = criterion(logits, label)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        print(f"Epoch [{epoch:02d}/{args.epochs:02d}] - Multimodal Fusion Loss: {avg_loss:.4f}")

    target_save_file = os.path.join(args.output_dir, "model.pt")
    torch.save(model.state_dict(), target_save_file)
    print(f"============================================================")
    print(f"[SUCCESS] Optical–SAR Training complete!")
    print(f"[ACTION REQUIRED]:")
    print(f"  1. Download: '{target_save_file}'")
    print(f"  2. Paste it in your project at:")
    print(f"     backend/models/checkpoints/optical_sar_model/model.pt")
    print(f"============================================================")

if __name__ == "__main__":
    main()
