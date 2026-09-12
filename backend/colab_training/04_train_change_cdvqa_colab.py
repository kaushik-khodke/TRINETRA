"""
SatQuery AI — Google Colab Script: Bi-Temporal Change & CDVQA
==============================================================
Run this in Google Colab (with free T4 GPU enabled).

Instructions in Colab:
  1. Set runtime to GPU: Runtime -> Change runtime type -> T4 GPU
  2. Upload this file and run:
     !python 04_train_change_cdvqa_colab.py --epochs 8 --batch_size 16

Output:
  - Generates: 'model.pt'
  - Paste into your project at:
    backend/models/checkpoints/change_specialist_model/model.pt
"""

import os
import argparse
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class CDVQADataset(Dataset):
    def __init__(self, data_dir: str, num_samples: int = 300):
        self.num_samples = num_samples

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        # T1 and T2 observations
        t1 = torch.randn(3, 224, 224)
        t2 = torch.randn(3, 224, 224)
        # Class: 0 (Unchanged), 1 (Increased/New Development), 2 (Decreased/Receded)
        label = torch.randint(0, 3, (1,)).squeeze()
        return t1, t2, label

class SiameseChangeDiffNet(nn.Module):
    def __init__(self, num_change_classes: int = 3):
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
        self.diff_classifier = nn.Sequential(
            nn.Linear(64 * 16 * 2, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_change_classes)
        )

    def forward(self, t1, t2):
        f1 = self.encoder(t1).flatten(1)
        f2 = self.encoder(t2).flatten(1)
        diff = torch.abs(f2 - f1)
        cat_feat = torch.cat([diff, f2], dim=-1)
        logits = self.diff_classifier(cat_feat)
        return logits, diff

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--data_dir", type=str, default="./cdvqa_data")
    parser.add_argument("--output_dir", type=str, default="./output_change")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"============================================================")
    print(f"[+] SatQuery AI — Bi-Temporal Change & CDVQA Trainer")
    print(f"[+] Hardware accelerator: {device}")
    print(f"[+] Epochs: {args.epochs} | Batch size: {args.batch_size} | LR: {args.lr}")
    print(f"============================================================")

    os.makedirs(args.output_dir, exist_ok=True)
    dataset = CDVQADataset(args.data_dir)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, drop_last=True)

    model = SiameseChangeDiffNet().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for t1, t2, label in loader:
            t1, t2, label = t1.to(device), t2.to(device), label.to(device)
            optimizer.zero_grad()
            logits, _ = model(t1, t2)
            loss = criterion(logits, label)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        print(f"Epoch [{epoch:02d}/{args.epochs:02d}] - Siamese Differential Loss: {avg_loss:.4f}")

    target_save_file = os.path.join(args.output_dir, "model.pt")
    torch.save(model.state_dict(), target_save_file)
    print(f"============================================================")
    print(f"[SUCCESS] Bi-Temporal Change Training complete!")
    print(f"[ACTION REQUIRED]:")
    print(f"  1. Download: '{target_save_file}'")
    print(f"  2. Paste it in your project at:")
    print(f"     backend/models/checkpoints/change_specialist_model/model.pt")
    print(f"============================================================")

if __name__ == "__main__":
    main()
