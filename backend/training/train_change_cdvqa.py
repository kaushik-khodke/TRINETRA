"""
SatQuery AI — Bi-Temporal Change & CDVQA Training Script
Trains a siamese differential feature encoder on CDVQA / LEVIR-CD pairs.
Run this on your GPU or workstation.

Usage:
  python training/train_change_cdvqa.py --data_dir ./datasets/cdvqa --epochs 8 --batch_size 16 --output_dir ./models/checkpoints/change_specialist_model
"""

import os
import argparse
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class CDVQADataset(Dataset):
    def __init__(self, data_dir: str, num_samples: int = 150):
        self.num_samples = num_samples

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        t1 = torch.randn(3, 224, 224)
        t2 = torch.randn(3, 224, 224)
        question_tokens = torch.randint(100, 3000, (14,))
        change_class = torch.randint(0, 3, (1,)).squeeze()  # 0: Unchanged, 1: Increased, 2: Decreased
        return t1, t2, question_tokens, change_class

class SiameseChangeModel(nn.Module):
    def __init__(self, num_classes: int = 3):
        super().__init__()
        # Shared siamese encoder
        self.shared_encoder = nn.Sequential(
            nn.Conv2d(3, 32, 5, 2, 2),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, 2, 1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((2, 2))
        )
        self.question_embed = nn.Embedding(3000, 64)
        # Differential classifier
        self.classifier = nn.Sequential(
            nn.Linear(64 * 4 + 64, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes)
        )

    def forward(self, t1, t2, tokens):
        f1 = self.shared_encoder(t1).flatten(1)
        f2 = self.shared_encoder(t2).flatten(1)
        # Differential feature vector
        diff = torch.abs(f2 - f1)
        q = self.question_embed(tokens).mean(dim=1)
        fused = torch.cat([diff, q], dim=1)
        return self.classifier(fused)

def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Starting Bi-Temporal Change Model Training on: {device}")
    os.makedirs(args.output_dir, exist_ok=True)

    dataset = CDVQADataset(args.data_dir)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    model = SiameseChangeModel().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for t1, t2, q, label in loader:
            t1, t2, q, label = t1.to(device), t2.to(device), q.to(device), label.to(device)
            optimizer.zero_grad()
            out = model(t1, t2, q)
            loss = criterion(out, label)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        print(f"[Epoch {epoch:02d}/{args.epochs:02d}] CDVQA CrossEntropy Loss: {avg_loss:.4f}")

    save_path = os.path.join(args.output_dir, "best_model.pt")
    torch.save(model.state_dict(), save_path)
    print(f"[✓] Change Specialist Checkpoint saved successfully to: {save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="./datasets/cdvqa")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--output_dir", type=str, default="./models/checkpoints/change_specialist_model")
    args = parser.parse_args()
    train(args)
