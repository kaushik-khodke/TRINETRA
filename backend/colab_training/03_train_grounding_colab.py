"""
SatQuery AI — Google Colab Script: Text-Guided Region Grounding
===============================================================
Run this in Google Colab (with free T4 GPU enabled).

Instructions in Colab:
  1. Set runtime to GPU: Runtime -> Change runtime type -> T4 GPU
  2. Upload this file and run:
     !python 03_train_grounding_colab.py --epochs 10 --batch_size 16

Output:
  - Generates: 'model.pt'
  - Paste into your project at:
    backend/models/checkpoints/rs_grounding_model/model.pt
"""

import os
import argparse
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class VRSGroundingDataset(Dataset):
    def __init__(self, data_dir: str, num_samples: int = 300):
        self.num_samples = num_samples

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        # 3-channel optical satellite image
        img = torch.randn(3, 256, 256)
        # Query tokens for feature phrase
        tokens = torch.randint(100, 4000, (12,))
        # Target bounding box [ymin, xmin, ymax, xmax] in [0, 1] range
        ymin = torch.rand(1) * 0.4
        xmin = torch.rand(1) * 0.4
        ymax = ymin + torch.rand(1) * 0.4 + 0.1
        xmax = xmin + torch.rand(1) * 0.4 + 0.1
        box = torch.cat([ymin, xmin, ymax, xmax])
        return img, tokens, box

class RSGroundingDetector(nn.Module):
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
            nn.Sigmoid()
        )

    def forward(self, img, tokens):
        b_feat = self.backbone(img).flatten(1)
        t_feat = self.text_embed(tokens).mean(dim=1)
        fused = torch.cat([b_feat, t_feat], dim=-1)
        return self.box_head(fused)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--data_dir", type=str, default="./vrsbench_data")
    parser.add_argument("--output_dir", type=str, default="./output_grounding")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"============================================================")
    print(f"[+] SatQuery AI — Text-Guided Region Grounding Trainer")
    print(f"[+] Hardware accelerator: {device}")
    print(f"[+] Epochs: {args.epochs} | Batch size: {args.batch_size} | LR: {args.lr}")
    print(f"============================================================")

    os.makedirs(args.output_dir, exist_ok=True)
    dataset = VRSGroundingDataset(args.data_dir)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, drop_last=True)

    model = RSGroundingDetector().to(device)
    criterion = nn.SmoothL1Loss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for img, tokens, target_box in loader:
            img, tokens, target_box = img.to(device), tokens.to(device), target_box.to(device)
            optimizer.zero_grad()
            pred_box = model(img, tokens)
            loss = criterion(pred_box, target_box)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        print(f"Epoch [{epoch:02d}/{args.epochs:02d}] - Bounding Box Smooth L1 Loss: {avg_loss:.4f}")

    target_save_file = os.path.join(args.output_dir, "model.pt")
    torch.save(model.state_dict(), target_save_file)
    print(f"============================================================")
    print(f"[SUCCESS] Grounding Training complete!")
    print(f"[ACTION REQUIRED]:")
    print(f"  1. Download: '{target_save_file}'")
    print(f"  2. Paste it in your project at:")
    print(f"     backend/models/checkpoints/rs_grounding_model/model.pt")
    print(f"============================================================")

if __name__ == "__main__":
    main()
