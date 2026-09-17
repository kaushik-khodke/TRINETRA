"""
TRINETRA — Bi-Temporal Change Detection Training Pipeline
Trains SiameseUNetBaseline or BitemporalInteractionTransformer on genuine bi-temporal datasets.
Governed by Stage 4 Change Detection Protocol. Zero synthetic data. Strictly evaluates baseline first.
"""

import os
import sys
import time
import argparse
from typing import Dict, Any, Tuple
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.cuda.amp import autocast, GradScaler
from PIL import Image

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.seed import set_seed
from common.profiling import get_profile_config
from common.metrics import binary_change_mask_metrics
from common.checkpoint import CheckpointManager
from common.reporting import TrainingReporter

from dataset import BiTemporalChangeGenuineDataset
from model import (
    SiameseUNetBaseline,
    BitemporalInteractionTransformer,
    create_change_model,
    HybridBCEDiceLoss
)


def evaluate_dense_change(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Evaluates model on validation loader computing dense binary change metrics.
    """
    model.eval()
    all_preds = []
    all_gts = []

    with torch.no_grad():
        for t1, t2, targets in loader:
            t1 = t1.to(device)
            t2 = t2.to(device)
            logits = model(t1, t2)
            probs = torch.sigmoid(logits).cpu().numpy()
            all_preds.append(probs)
            all_gts.append(targets.numpy())

    preds_arr = np.concatenate(all_preds, axis=0)
    gts_arr = np.concatenate(all_gts, axis=0)
    return binary_change_mask_metrics(preds_arr, gts_arr, threshold=threshold)


def save_visual_examples(
    model: nn.Module,
    dataset: BiTemporalChangeGenuineDataset,
    output_dir: str,
    device: torch.device,
    num_samples: int = 5
) -> None:
    """Saves visual inspection composites: [T1 | T2 | Ground Truth | Prediction]."""
    examples_dir = os.path.join(output_dir, "examples")
    os.makedirs(examples_dir, exist_ok=True)
    model.eval()

    with torch.no_grad():
        for idx in range(min(num_samples, len(dataset))):
            t1_tensor, t2_tensor, mask_tensor = dataset[idx]
            t1_in = t1_tensor.unsqueeze(0).to(device)
            t2_in = t2_tensor.unsqueeze(0).to(device)
            logits = model(t1_in, t2_in)
            prob_mask = torch.sigmoid(logits).squeeze().cpu().numpy()
            pred_bin = (prob_mask >= 0.5).astype(np.uint8) * 255

            t1_np = (t1_tensor.permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)
            t2_np = (t2_tensor.permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)
            gt_np = (mask_tensor.squeeze().numpy() * 255.0).astype(np.uint8)

            # Convert 1-channel masks to 3-channel for composite
            gt_rgb = np.stack([gt_np, gt_np, gt_np], axis=-1)
            pred_rgb = np.stack([pred_bin, np.zeros_like(pred_bin), np.zeros_like(pred_bin)], axis=-1)

            h, w = t1_np.shape[:2]
            composite = Image.new("RGB", (w * 4, h))
            composite.paste(Image.fromarray(t1_np), (0, 0))
            composite.paste(Image.fromarray(t2_np), (w, 0))
            composite.paste(Image.fromarray(gt_rgb), (w * 2, 0))
            composite.paste(Image.fromarray(pred_rgb), (w * 3, 0))

            out_file = os.path.join(examples_dir, f"change_val_sample_{idx+1:03d}.png")
            composite.save(out_file)
    print(f"[EXAMPLES] Saved validation composites to: {examples_dir}")


def train_change(args):
    set_seed(args.seed)
    profile = get_profile_config(args.profile)

    epochs = args.epochs if args.epochs else profile.epochs
    batch_size = args.batch_size if args.batch_size else profile.batch_size
    lr = args.lr if args.lr else profile.lr
    output_dir = args.output_dir or os.path.join(os.path.dirname(__file__), "runs", f"run_{args.model}_{args.profile}")
    manifest_dir = args.manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — Bi-Temporal Change Detection Training")
    print(f"Model Architecture: {args.model.upper()}")
    print(f"Profile:            {profile.name.upper()} ({profile.target_runtime})")
    print(f"Hardware:           {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print("============================================================\n")

    # 1. Load Genuine Datasets
    train_manifest = os.path.join(manifest_dir, "change_train.txt")
    val_manifest = os.path.join(manifest_dir, "change_val.txt")

    train_ds = BiTemporalChangeGenuineDataset(
        args.data_dir,
        train_manifest if os.path.isfile(train_manifest) else None,
        image_size=profile.image_size,
        max_samples=profile.max_train_samples
    )
    val_ds = BiTemporalChangeGenuineDataset(
        args.data_dir,
        val_manifest if os.path.isfile(val_manifest) else None,
        image_size=profile.image_size,
        max_samples=profile.max_val_samples
    )

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=profile.num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=profile.num_workers)

    # 2. Instantiate Model
    model = create_change_model(args.model, in_channels=3, num_classes=1).to(device)
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[MODEL] Trainable Parameters: {param_count:,}")

    # 3. Mandatory Untrained Baseline Evaluation (Section 16 requirement)
    print("------------------------------------------------------------")
    print("MANDATORY BASELINE EVALUATION (Untrained Change Prior)")
    print("------------------------------------------------------------")
    baseline_metrics = evaluate_dense_change(model, val_loader, device)
    print(f"BASELINE Validation -> F1: {baseline_metrics['f1']:.4f} | IoU: {baseline_metrics['iou']:.4f} | Acc: {baseline_metrics['accuracy']:.4f}")

    # 4. Training Setup: Hybrid BCE + Dice Loss
    criterion = HybridBCEDiceLoss(bce_weight=0.5, dice_weight=0.5)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scaler = GradScaler(enabled=profile.use_amp)

    ckpt_mgr = CheckpointManager(output_dir, f"change_{args.model}_model")
    reporter = TrainingReporter(output_dir)

    history = {"train_loss": [], "val_loss": [], "val_metric": []}
    best_f1 = -1.0
    patience_counter = 0

    t_start = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        e_start = time.time()

        for t1, t2, targets in train_loader:
            t1, t2, targets = t1.to(device), t2.to(device), targets.to(device)
            optimizer.zero_grad()
            with autocast(enabled=profile.use_amp):
                logits = model(t1, t2)
                loss = criterion(logits, targets)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            total_loss += loss.item()

        avg_loss = total_loss / max(1, len(train_loader))
        val_metrics = evaluate_dense_change(model, val_loader, device)
        cur_f1 = val_metrics["f1"]
        cur_iou = val_metrics["iou"]

        history["train_loss"].append(round(avg_loss, 4))
        history["val_loss"].append(round(1.0 - cur_f1, 4))
        history["val_metric"].append(cur_f1)

        elapsed = time.time() - e_start
        print(f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s) - Loss: {avg_loss:.4f} | Val F1: {cur_f1:.4f} | Val IoU: {cur_iou:.4f}")

        is_best = cur_f1 > best_f1
        if is_best:
            best_f1 = cur_f1
            patience_counter = 0
        else:
            patience_counter += 1

        ckpt_mgr.save_checkpoint(model, epoch, is_best, cur_f1)

        if patience_counter >= profile.patience:
            print(f"\n[EARLY STOPPING] Validation F1 plateaued for {profile.patience} epochs.")
            break

    total_time = time.time() - t_start
    print(f"\nTraining completed in {total_time / 60:.2f} minutes.")
    print(f"Best Validation F1: {best_f1:.4f}")

    reporter.save_history(history)
    save_visual_examples(model, val_ds, output_dir, device, num_samples=5)

    ckpt_mgr.save_config({
        "model_architecture": args.model,
        "parameter_count": param_count,
        "profile": profile.name,
        "epochs_trained": epoch,
        "best_val_f1": best_f1,
        "training_time_min": round(total_time / 60, 2),
        "seed": args.seed,
        "device": str(device)
    })

    if args.export:
        ckpt_mgr.deploy_to_backend("change_specialist_model")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train bi-temporal change detection specialist.")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to genuine change dataset directory.")
    parser.add_argument("--manifest_dir", type=str, default=None)
    parser.add_argument("--model", type=str, default="baseline", choices=["baseline", "bit"], help="Architecture choice")
    parser.add_argument("--profile", type=str, default="balanced", choices=["fast", "balanced", "quality"])
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--export", action="store_true", help="Deploy best model to backend/models/checkpoints/change_specialist_model/")
    args = parser.parse_args()

    train_change(args)
