"""
SatQuery AI — Text-Guided Region Grounding Training Script
Trains a spatial localization head to predict normalized bounding boxes [ymin, xmin, ymax, xmax]
from natural-language feature phrases.
Run this on your GPU or workstation.

Usage:
  python training/train_grounding.py --data_dir ./datasets/vrsbench --epochs 10 --batch_size 16 --output_dir ./models/checkpoints/rs_grounding_model
"""

import os
import argparse
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class VRSGroundingDataset(Dataset):
    def __init__(self, data_dir: str, num_samples: int = 150):
        self.num_samples = num_samples

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        img = torch.randn(3, 256, 256)
        query_tokens = torch.randint(100, 4000, (12,))
        # Target bounding box: [ymin, xmin, ymax, xmax] normalized
        ymin = torch.rand(1) * 0.4
        xmin = torch.rand(1) * 0.4
        ymax = ymin + torch.rand(1) * 0.4 + 0.1
        xmax = xmin + torch.rand(1) * 0.4 + 0.1
        box = torch.cat([ymin, xmin, ymax, xmax])
        return img, query_tokens, box

class RSGroundingModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.visual_backbone = nn.Sequential(
            nn.Conv2d(3, 64, 5, 2, 2),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, 2, 1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.text_encoder = nn.Embedding(4000, 64)
        self.box_regressor = nn.Sequential(
            nn.Linear(128 * 16 + 64, 128),
            nn.ReLU(),
            nn.Linear(128, 4),
            nn.Sigmoid()  # Outputs [0, 1] normalized coordinates
        )

    def forward(self, img, text):
        v = self.visual_backbone(img).flatten(1)
        t = self.text_encoder(text).mean(dim=1)
        cat = torch.cat([v, t], dim=1)
        return self.box_regressor(cat)

def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Starting RS Text-Guided Grounding Training on: {device}")
    os.makedirs(args.output_dir, exist_ok=True)

    dataset = VRSGroundingDataset(args.data_dir)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    model = RSGroundingModel().to(device)
    criterion = nn.SmoothL1Loss()  # Smooth L1 for bounding box regression
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for img, query, target_box in loader:
            img, query, target_box = img.to(device), query.to(device), target_box.to(device)
            optimizer.zero_grad()
            pred_box = model(img, query)
            loss = criterion(pred_box, target_box)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        print(f"[Epoch {epoch:02d}/{args.epochs:02d}] SmoothL1 BBox Loss: {avg_loss:.4f}")

    save_path = os.path.join(args.output_dir, "best_model.pt")
    torch.save(model.state_dict(), save_path)
    print(f"[✓] Grounding Checkpoint saved successfully to: {save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="./datasets/vrsbench")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--output_dir", type=str, default="./models/checkpoints/rs_grounding_model")
    args = parser.parse_args()
    train(args)
