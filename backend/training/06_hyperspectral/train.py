"""
TRINETRA / SatQuery AI — Hyperspectral Model Training Pipeline
Module: backend/training/06_hyperspectral/train.py

Trains specialist hyperspectral models:
- spectral_mlp: 1D Pure Spectral Baseline
- hybridsn: 3D-2D Hybrid Spectral-Spatial CNN (Roy et al., IEEE GRSL 2019)
- hyperfree: Channel-Adaptive ViT-B Hyperspectral Foundation Model

Enforces:
1. Spatial block partitioning with boundary buffer margins (zero cross-split leakage).
2. Train-only spectral normalization (mu_b, sigma_b).
3. Checkpoint management, reproducibility seeding, and training reporting.
"""

import os
import sys
import time
import argparse
from pathlib import Path

from typing import Dict, Any, List, Tuple, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.seed import set_seed
from common.profiling import get_profile_config
from common.metrics import hyperspectral_metrics
from common.checkpoint import CheckpointManager
from common.reporting import TrainingReporter

from models.hyperspectral_models import create_hsi_model
from dataset import HyperspectralSpatialDataset


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, float]:
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for batch in loader:
        # Handles (data, target, coords) or (data, target)
        data, target = batch[0], batch[1]
        data, target = data.to(device), target.to(device)

        optimizer.zero_grad()
        logits = model(data)
        loss = criterion(logits, target)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * len(target)
        preds = torch.argmax(logits, dim=-1)
        correct += int((preds == target).sum().item())
        total += len(target)

    avg_loss = total_loss / (total + 1e-8)
    acc = (correct / (total + 1e-8)) * 100.0
    return avg_loss, acc


def evaluate_split(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    num_classes: int
) -> Dict[str, Any]:
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in loader:
            data, target = batch[0], batch[1]
            data = data.to(device)
            logits = model(data)
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(target.numpy())

    return hyperspectral_metrics(
        y_pred=np.array(all_preds),
        y_true=np.array(all_targets),
        num_classes=num_classes
    )


def run_training(args):
    set_seed(args.seed)
    profile = get_profile_config(args.profile)

    epochs = args.epochs if args.epochs else profile.epochs
    batch_size = args.batch_size if args.batch_size else profile.batch_size
    lr = args.lr if args.lr else profile.lr
    patience = args.patience if args.patience is not None else max(profile.patience, 5)

    output_dir = args.output_dir or os.path.join(os.path.dirname(__file__), "runs", f"run_{args.model}_{args.profile}")
    os.makedirs(output_dir, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — Hyperspectral Remote Sensing Specialist Training")
    print(f"Model Architecture: {args.model.upper()}")
    print(f"Profile:            {profile.name.upper()} ({profile.target_runtime})")
    print(f"Hardware:           {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print(f"Data Cube:          {args.cube}")
    print("============================================================\n")

    # Determine mode and patch size
    if args.model == "spectral_mlp":
        mode = "pixel"
        patch_size = 1
    elif args.model == "hybridsn":
        mode = "patch_3d"
        patch_size = args.patch_size if args.patch_size else 11
    elif args.model == "hyperfree":
        mode = "patch_2d"
        patch_size = args.patch_size if args.patch_size else 16
    else:
        raise ValueError(f"Unknown model: {args.model}")

    # Build Training Dataset (computes train-only normalization stats)
    train_ds = HyperspectralSpatialDataset(
        cube_or_path=args.cube,
        gt_or_path=args.gt,
        split="train",
        patch_size=patch_size,
        mode=mode,
        grid_rows=args.grid_rows,
        grid_cols=args.grid_cols,
        ignore_index=args.ignore_index
    )

    # Build Validation Dataset (uses strict train-only normalization stats)
    val_ds = HyperspectralSpatialDataset(
        cube_or_path=args.cube,
        gt_or_path=args.gt,
        split="val",
        patch_size=patch_size,
        mode=mode,
        grid_rows=args.grid_rows,
        grid_cols=args.grid_cols,
        ignore_index=args.ignore_index,
        custom_split_blocks=train_ds.split_blocks,
        norm_stats=train_ds.norm_stats
    )

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    num_classes = len(train_ds.unique_labels)
    num_bands = train_ds.num_bands

    print(f"[DATASET] Cube bands: {num_bands}, Classes: {num_classes}")
    print(f"[DATASET] Train samples: {len(train_ds)}, Val samples: {len(val_ds)}")
    print(f"[DATASET] Extraction Mode: {mode}, Patch Size: {patch_size}x{patch_size}")

    # Instantiate Model
    model = create_hsi_model(
        model_name=args.model,
        in_channels=num_bands,
        num_classes=num_classes,
        patch_size=patch_size
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[MODEL] Created {args.model} with {total_params:,} trainable parameters.\n")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    ckpt_mgr = CheckpointManager(run_dir=output_dir, model_name=args.model)
    reporter = TrainingReporter(run_dir=output_dir)

    best_oa = 0.0
    patience_counter = 0
    history = {
        "train_loss": [],
        "train_acc": [],
        "val_oa": [],
        "val_aa": [],
        "val_kappa": [],
        "val_metric": []
    }

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion, device)
        scheduler.step()

        val_metrics = evaluate_split(model, val_loader, device, num_classes)
        val_oa = val_metrics["overall_accuracy"] * 100.0
        val_aa = val_metrics["average_accuracy"] * 100.0
        val_kappa = val_metrics["kappa_coefficient"]

        history["train_loss"].append(round(train_loss, 4))
        history["train_acc"].append(round(train_acc, 2))
        history["val_oa"].append(round(val_oa, 2))
        history["val_aa"].append(round(val_aa, 2))
        history["val_kappa"].append(round(val_kappa, 4))
        history["val_metric"].append(round(val_oa, 2))

        elapsed = time.time() - t0
        print(
            f"Epoch {epoch:3d}/{epochs:3d} [{elapsed:4.1f}s] | "
            f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.2f}% | "
            f"Val OA: {val_oa:.2f}%, AA: {val_aa:.2f}%, Kappa: {val_kappa:.4f}"
        )

        # Checkpoint if best validation OA
        is_best = (val_oa > best_oa)
        ckpt_mgr.save_checkpoint(model, epoch=epoch, is_best=is_best, metric_val=val_oa)
        if is_best:
            best_oa = val_oa
            patience_counter = 0
            ckpt_path = os.path.join(output_dir, f"best_{args.model}.pt")
            torch.save(model.state_dict(), ckpt_path)
            print(f"  -> Saved new best model checkpoint to {ckpt_path} (Val OA: {val_oa:.2f}%)")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\n[EARLY STOPPING] Validation OA did not improve for {patience} consecutive epochs.")
                break

    print(f"\n[TRAINING COMPLETE] Best Validation OA: {best_oa:.2f}%")
    reporter.save_history(history)
    ckpt_mgr.save_config({
        "dataset": f"HSI-{Path(args.cube).stem}",
        "model_architecture": args.model,
        "parameter_count": total_params,
        "profile": profile.name,
        "epochs_trained": epoch,
        "best_val_oa": round(best_oa, 2),
        "patch_size": patch_size,
        "seed": args.seed,
        "device": str(device)
    })
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="TRINETRA Hyperspectral Training Pipeline")
    parser.add_argument("--cube", type=str, default="sample_data/sample_hsi.mat", help="Path to HSI cube")
    parser.add_argument("--gt", type=str, default="sample_data/sample_hsi_gt.mat", help="Path to ground truth mask")
    parser.add_argument("--model", type=str, default="hybridsn", choices=["spectral_mlp", "hybridsn", "hyperfree"], help="Model architecture")
    parser.add_argument("--patch_size", type=int, default=11, help="Spatial patch dimension")
    parser.add_argument("--grid_rows", type=int, default=4, help="Grid rows for spatial block partition")
    parser.add_argument("--grid_cols", type=int, default=4, help="Grid cols for spatial block partition")
    parser.add_argument("--ignore_index", type=int, default=0, help="Background ignore index")
    parser.add_argument("--profile", type=str, default="fast", choices=["fast", "balanced", "quality"], help="Hardware profile")
    parser.add_argument("--epochs", type=int, default=None, help="Override epoch count")
    parser.add_argument("--batch_size", type=int, default=None, help="Override batch size")
    parser.add_argument("--lr", type=float, default=None, help="Override learning rate")
    parser.add_argument("--patience", type=int, default=None, help="Early stopping patience")
    parser.add_argument("--seed", type=int, default=42, help="Reproducible seed")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    run_training(args)


if __name__ == "__main__":
    main()
