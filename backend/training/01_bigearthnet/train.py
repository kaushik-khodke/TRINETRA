"""
TRINETRA / SatQuery AI — BigEarthNet-S2 Training Pipeline
Trains adapted multi-spectral ResNet18 on genuine BigEarthNet-S2 dataset on laptop GPU.
Zero synthetic data. Strictly evaluates baseline first.
"""

import os
import sys
import time
import argparse
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.cuda.amp import autocast, GradScaler

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.seed import set_seed
from common.profiling import get_profile_config
from common.metrics import multilabel_metrics
from common.checkpoint import CheckpointManager
from common.reporting import TrainingReporter

from dataset import BigEarthNetS2Dataset, CORINE_19_CLASSES
from model import BigEarthNetAdaptedResNet, get_baseline_rgb_model

def evaluate_model(model: nn.Module, loader: DataLoader, device: torch.device) -> dict:
    """Evaluates multi-label model on a dataloader without data leakage."""
    model.eval()
    all_probs = []
    all_targets = []
    with torch.no_grad():
        for imgs, targets in loader:
            imgs = imgs.to(device)
            with autocast():
                logits = model(imgs)
                probs = torch.sigmoid(logits)
            all_probs.append(probs.cpu().numpy())
            all_targets.append(targets.numpy())

    probs_arr = np.concatenate(all_probs, axis=0)
    targets_arr = np.concatenate(all_targets, axis=0)
    return multilabel_metrics(probs_arr, targets_arr)

def train_bigearthnet(args):
    set_seed(args.seed)
    profile = get_profile_config(args.profile)

    epochs = args.epochs if args.epochs else profile.epochs
    batch_size = args.batch_size if args.batch_size else profile.batch_size
    lr = args.lr if args.lr else profile.lr
    output_dir = args.output_dir or os.path.join(os.path.dirname(__file__), "runs", f"run_{args.profile}")
    manifest_dir = args.manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print(f"TRINETRA — BigEarthNet-S2 Remote-Sensing Training")
    print(f"Profile: {profile.name.upper()} ({profile.target_runtime})")
    print(f"Hardware Accelerator: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print(f"Max Samples: Train={profile.max_train_samples:,} | Val={profile.max_val_samples:,}")
    print("============================================================\n")

    # 1. Load Real Datasets via Verified Manifests
    train_manifest = os.path.join(manifest_dir, "bigearthnet_train.txt")
    val_manifest = os.path.join(manifest_dir, "bigearthnet_val.txt")
    test_manifest = os.path.join(manifest_dir, "bigearthnet_test.txt")

    train_ds = BigEarthNetS2Dataset(args.data_dir, train_manifest, args.metadata, num_bands=args.bands, image_size=profile.image_size, max_samples=profile.max_train_samples)
    val_ds = BigEarthNetS2Dataset(args.data_dir, val_manifest, args.metadata, num_bands=args.bands, image_size=profile.image_size, max_samples=profile.max_val_samples)
    test_ds = BigEarthNetS2Dataset(args.data_dir, test_manifest, args.metadata, num_bands=args.bands, image_size=profile.image_size, max_samples=profile.max_test_samples)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=profile.num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=profile.num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=profile.num_workers)

    # 2. Section 16 Mandatory: BASELINE-FIRST EVALUATION
    print("------------------------------------------------------------")
    print("MANDATORY BASELINE EVALUATION (Pretrained ImageNet RGB)")
    print("------------------------------------------------------------")
    baseline_model = get_baseline_rgb_model(num_classes=19).to(device)
    # Evaluate baseline using first 3 channels (RGB)
    baseline_metrics = evaluate_model(baseline_model, val_loader, device)
    print(f"BASELINE Validation -> mAP: {baseline_metrics['mAP']:.4f} | Micro F1: {baseline_metrics['micro_f1']:.4f} | Macro F1: {baseline_metrics['macro_f1']:.4f}")
    del baseline_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 3. Initialize Adapted Model & Optimizer
    print("\n------------------------------------------------------------")
    print(f"TRAINING ADAPTED RESNET18 ({args.bands} Sentinel-2 Bands)")
    print("------------------------------------------------------------")
    model = BigEarthNetAdaptedResNet(in_channels=args.bands, num_classes=19, pretrained=True).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scaler = GradScaler(enabled=profile.use_amp)

    ckpt_mgr = CheckpointManager(output_dir, "bigearthnet_adapted")
    reporter = TrainingReporter(output_dir)

    history = {"train_loss": [], "val_loss": [], "val_metric": []}
    best_map = -1.0
    patience_counter = 0

    t_start = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        e_start = time.time()

        for imgs, targets in train_loader:
            imgs, targets = imgs.to(device), targets.to(device)
            optimizer.zero_grad()
            with autocast(enabled=profile.use_amp):
                logits = model(imgs)
                loss = criterion(logits, targets)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            total_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)
        val_metrics = evaluate_model(model, val_loader, device)
        cur_map = val_metrics["mAP"]

        history["train_loss"].append(round(avg_train_loss, 4))
        history["val_loss"].append(round(1.0 - cur_map, 4))
        history["val_metric"].append(cur_map)

        elapsed = time.time() - e_start
        print(f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s) - Loss: {avg_train_loss:.4f} | Val mAP: {cur_map:.4f} | Micro F1: {val_metrics['micro_f1']:.4f}")

        is_best = cur_map > best_map
        if is_best:
            best_map = cur_map
            patience_counter = 0
        else:
            patience_counter += 1

        ckpt_mgr.save_checkpoint(model, epoch, is_best, cur_map)

        if patience_counter >= profile.patience:
            print(f"\n[EARLY STOPPING] Validation metric plateaued for {profile.patience} epochs.")
            break

    total_training_time = time.time() - t_start
    print(f"\nTraining completed in {total_training_time / 60:.2f} minutes.")

    # 4. Final Held-out Test Evaluation
    print("\n------------------------------------------------------------")
    print("FINAL TEST EVALUATION (On strictly held-out test split)")
    print("------------------------------------------------------------")
    best_weights = torch.load(ckpt_mgr.best_model_path, map_location=device)
    model.load_state_dict(best_weights)
    test_metrics = evaluate_model(model, test_loader, device)

    print(f"FINAL TEST -> mAP: {test_metrics['mAP']:.4f} | Micro F1: {test_metrics['micro_f1']:.4f} | Macro F1: {test_metrics['macro_f1']:.4f}")

    # 5. Baseline vs Trained Comparison
    delta_map = test_metrics["mAP"] - baseline_metrics["mAP"]
    print("------------------------------------------------------------")
    print("BASE-VS-TRAINED COMPARISON")
    print(f"Baseline mAP: {baseline_metrics['mAP']:.4f}")
    print(f"Trained mAP:  {test_metrics['mAP']:.4f}")
    print(f"Delta:        {'+' if delta_map >= 0 else ''}{delta_map * 100:.2f}%")
    print("============================================================\n")

    # 6. Save Artifacts & Reports
    reporter.save_history(history)
    reporter.save_evaluation(test_metrics, baseline_metrics)
    ckpt_mgr.save_config({
        "dataset": DATASET_NAME,
        "profile": profile.name,
        "bands": args.bands,
        "epochs_trained": epoch,
        "best_val_mAP": best_map,
        "final_test_mAP": test_metrics["mAP"],
        "training_time_min": round(total_training_time / 60, 2),
        "seed": args.seed,
        "device": str(device)
    })

    if args.export:
        ckpt_mgr.deploy_to_backend("bigearthnet_adapted")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train BigEarthNet-S2 multi-label land cover classifier.")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to real BigEarthNet-S2 directory.")
    parser.add_argument("--metadata", type=str, required=True, help="Path to metadata.parquet or metadata.csv.")
    parser.add_argument("--manifest_dir", type=str, default=None, help="Path to manifest directory.")
    parser.add_argument("--bands", type=int, default=4, help="Number of input bands (4 for RGB-NIR, 12 for all).")
    parser.add_argument("--profile", type=str, default="balanced", choices=["fast", "balanced", "quality"])
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--export", action="store_true", help="Deploy best model directly to backend/models/checkpoints/")
    args = parser.parse_args()

    train_bigearthnet(args)
