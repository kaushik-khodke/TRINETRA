"""
TRINETRA / SatQuery AI — Optical + SAR Training Pipeline
Trains cross-modal attention network on genuine SEN1-2 / BigEarthNet-MM pairs on laptop GPU.
Zero synthetic data. Strictly evaluates Optical-only and SAR-only baselines first.
"""

import os
import sys
import time
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.seed import set_seed
from common.profiling import get_profile_config
from common.metrics import fusion_metrics, change_metrics
from common.checkpoint import CheckpointManager
from common.reporting import TrainingReporter

from dataset import OpticalSARGenuineDataset
from model import OpticalSARCrossAttentionNet, OpticalOnlyBaseline, SAROnlyBaseline

DATASET_NAME = "SEN1-2 (Paired Sentinel-1 SAR & Sentinel-2 Optical)"

def evaluate_fusion(model: nn.Module, loader: DataLoader, device: torch.device, criterion: nn.Module = None):
    model.eval()
    correct = 0
    total = 0
    total_loss = 0.0
    with torch.no_grad():
        for opt, sar, targets in loader:
            opt, sar, targets = opt.to(device), sar.to(device), targets.to(device)
            with torch.amp.autocast(device_type=device.type, enabled=(device.type == 'cuda')):
                logits = model(opt, sar)
                if criterion is not None:
                    loss = criterion(logits, targets)
                    total_loss += loss.item() * len(targets)
            preds = torch.argmax(logits, dim=-1)
            correct += int((preds == targets).sum().item())
            total += len(targets)
    acc = float(correct / total) * 100.0 if total > 0 else 0.0
    avg_loss = float(total_loss / total) if (total > 0 and criterion is not None) else 0.0
    return (acc, avg_loss) if criterion is not None else acc

def evaluate_single_modality(model: nn.Module, loader: DataLoader, device: torch.device, is_opt: bool = True) -> float:
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for opt, sar, targets in loader:
            x = opt.to(device) if is_opt else sar.to(device)
            targets = targets.to(device)
            with torch.amp.autocast(device_type=device.type, enabled=(device.type == 'cuda')):
                logits = model(x)
            preds = torch.argmax(logits, dim=-1)
            correct += int((preds == targets).sum().item())
            total += len(targets)
    return float(correct / total) * 100.0 if total > 0 else 0.0

def train_optical_sar(args):
    set_seed(args.seed)
    profile = get_profile_config(args.profile)

    epochs = args.epochs if args.epochs else profile.epochs
    batch_size = args.batch_size if args.batch_size else profile.batch_size
    lr = args.lr if args.lr else profile.lr
    patience = args.patience if args.patience is not None else max(profile.patience, 5)
    output_dir = args.output_dir or os.path.join(os.path.dirname(__file__), "runs", f"run_{args.profile}")
    manifest_dir = args.manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — Optical + SAR Cross-Modal Fusion Training")
    print(f"Profile: {profile.name.upper()} ({profile.target_runtime})")
    print(f"Hardware: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print("============================================================\n")

    # 1. Load Genuine Datasets
    train_manifest = os.path.join(manifest_dir, "optical_sar_train.txt")
    val_manifest = os.path.join(manifest_dir, "optical_sar_val.txt")
    test_manifest = os.path.join(manifest_dir, "optical_sar_test.txt")

    train_ds = OpticalSARGenuineDataset(args.data_dir, train_manifest, image_size=profile.image_size, max_samples=profile.max_train_samples, augment=True)
    val_ds = OpticalSARGenuineDataset(args.data_dir, val_manifest, image_size=profile.image_size, max_samples=profile.max_val_samples)
    test_ds = OpticalSARGenuineDataset(args.data_dir, test_manifest, image_size=profile.image_size, max_samples=profile.max_test_samples)

    eff_batch = min(batch_size, max(1, len(train_ds)))
    val_batch = min(batch_size, max(1, len(val_ds)))
    test_batch = min(batch_size, max(1, len(test_ds)))

    train_loader = DataLoader(train_ds, batch_size=eff_batch, shuffle=True, num_workers=profile.num_workers, pin_memory=torch.cuda.is_available())
    val_loader = DataLoader(val_ds, batch_size=val_batch, shuffle=False, num_workers=profile.num_workers)
    test_loader = DataLoader(test_ds, batch_size=test_batch, shuffle=False, num_workers=profile.num_workers)

    # 2. Section 15 & 16 Mandatory: OPTICAL-ONLY & SAR-ONLY BASELINE EVALUATION
    print("------------------------------------------------------------")
    print("MANDATORY BASELINE EVALUATIONS (Single Modality Baselines)")
    print("------------------------------------------------------------")
    opt_base = OpticalOnlyBaseline().to(device)
    sar_base = SAROnlyBaseline().to(device)

    opt_base_acc = evaluate_single_modality(opt_base, val_loader, device, is_opt=True)
    sar_base_acc = evaluate_single_modality(sar_base, val_loader, device, is_opt=False)
    print(f"BASELINE Validation -> Optical-Only Accuracy: {opt_base_acc:.2f}% | SAR-Only Accuracy: {sar_base_acc:.2f}%")
    del opt_base, sar_base
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 3. Training Loop with Cross-Attention Fusion
    model = OpticalSARCrossAttentionNet().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scaler = torch.amp.GradScaler('cuda', enabled=(profile.use_amp and device.type == "cuda"))
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    ckpt_mgr = CheckpointManager(output_dir, "optical_sar_model")
    reporter = TrainingReporter(output_dir)

    history = {"train_loss": [], "val_loss": [], "val_metric": []}
    best_acc = -1.0
    best_val_loss = 999.0
    patience_counter = 0

    t_start = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        e_start = time.time()

        for opt, sar, targets in train_loader:
            opt, sar, targets = opt.to(device), sar.to(device), targets.to(device)
            optimizer.zero_grad()
            with torch.amp.autocast(device_type=device.type, enabled=(profile.use_amp and device.type == "cuda")):
                logits = model(opt, sar)
                loss = criterion(logits, targets)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            total_loss += loss.item()

        scheduler.step()
        avg_loss = total_loss / len(train_loader)
        cur_acc, cur_val_loss = evaluate_fusion(model, val_loader, device, criterion=criterion)

        history["train_loss"].append(round(avg_loss, 4))
        history["val_loss"].append(round(cur_val_loss, 4))
        history["val_metric"].append(cur_acc)

        elapsed = time.time() - e_start
        print(f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s) - Train Loss: {avg_loss:.4f} | Val Loss: {cur_val_loss:.4f} | Val Fused Acc: {cur_acc:.2f}%")

        is_best = False
        if cur_acc > best_acc:
            best_acc = cur_acc
            best_val_loss = cur_val_loss
            is_best = True
            patience_counter = 0
        elif abs(cur_acc - best_acc) < 1e-4 and cur_val_loss < (best_val_loss - 0.005):
            best_val_loss = cur_val_loss
            is_best = True
            patience_counter = 0
        else:
            patience_counter += 1

        ckpt_mgr.save_checkpoint(model, epoch, is_best, cur_acc)

        if patience_counter >= patience:
            print(f"\n[EARLY STOPPING] Validation metrics plateaued for {patience} epochs.")
            break

    total_time = time.time() - t_start
    print(f"\nTraining completed in {total_time / 60:.2f} minutes.")

    # 4. Final Held-Out Test Evaluation
    print("\n------------------------------------------------------------")
    print("FINAL TEST EVALUATION (On strictly held-out test split)")
    print("------------------------------------------------------------")
    best_weights = torch.load(ckpt_mgr.best_model_path, map_location=device)
    model.load_state_dict(best_weights)
    model.eval()

    test_preds, test_targets = [], []
    with torch.no_grad():
        for opt, sar, targets in test_loader:
            opt, sar = opt.to(device), sar.to(device)
            with torch.amp.autocast(device_type=device.type, enabled=(profile.use_amp and device.type == "cuda")):
                logits = model(opt, sar)
            preds = torch.argmax(logits, dim=-1)
            test_preds.extend(preds.cpu().numpy())
            test_targets.extend(targets.numpy())

    test_preds = np.array(test_preds)
    test_targets = np.array(test_targets)
    c_metrics = change_metrics(test_preds, test_targets)
    fused_test_acc = c_metrics["accuracy_pct"]

    comp_metrics = fusion_metrics(opt_base_acc, sar_base_acc, fused_test_acc)
    comp_metrics["test_macro_f1"] = c_metrics["macro_f1"]
    print(f"Optical-Only Baseline: {comp_metrics['optical_only_accuracy']:.2f}%")
    print(f"SAR-Only Baseline:     {comp_metrics['sar_only_accuracy']:.2f}%")
    print(f"Optical+SAR Trained:   {comp_metrics['optical_sar_fused_accuracy']:.2f}%")
    print(f"Test Macro F1-Score:   {comp_metrics['test_macro_f1']:.4f}")
    print(f"Improvement vs Opt:    {'+' if comp_metrics['fusion_delta_vs_optical'] >= 0 else ''}{comp_metrics['fusion_delta_vs_optical']:.2f}%")
    print(f"Improvement vs SAR:    {'+' if comp_metrics['fusion_delta_vs_sar'] >= 0 else ''}{comp_metrics['fusion_delta_vs_sar']:.2f}%")
    print("============================================================\n")

    reporter.save_history(history)
    reporter.save_evaluation(comp_metrics)
    ckpt_mgr.save_config({
        "dataset": DATASET_NAME,
        "profile": profile.name,
        "epochs_trained": epoch,
        "best_val_acc": best_acc,
        "test_fused_acc": fused_test_acc,
        "training_time_min": round(total_time / 60, 2),
        "seed": args.seed,
        "device": str(device)
    })

    if args.export:
        ckpt_mgr.deploy_to_backend("optical_sar_model")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Optical+SAR cross-attention model.")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing s1 and s2 folders.")
    parser.add_argument("--manifest_dir", type=str, default=None)
    parser.add_argument("--profile", type=str, default="balanced", choices=["fast", "balanced", "quality"])
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--patience", type=int, default=None, help="Epochs to wait before early stopping (default: max(profile, 5))")
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--export", action="store_true", help="Deploy best model to backend/models/checkpoints/optical_sar_model/")
    args = parser.parse_args()

    train_optical_sar(args)
