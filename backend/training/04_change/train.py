"""
TRINETRA / SatQuery AI — Bi-Temporal Change Training Pipeline
Trains Siamese differential network on genuine LEVIR-CD/OSCD pairs on laptop GPU.
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
from PIL import Image

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.seed import set_seed
from common.profiling import get_profile_config
from common.metrics import change_metrics
from common.checkpoint import CheckpointManager
from common.reporting import TrainingReporter

from dataset import BiTemporalChangeGenuineDataset
from model import SiameseChangeDiffNet

def evaluate_change(model: nn.Module, loader: DataLoader, device: torch.device) -> dict:
    model.eval()
    all_preds, all_gts = [], []
    with torch.no_grad():
        for t1, t2, targets in loader:
            t1, t2 = t1.to(device), t2.to(device)
            with autocast():
                logits, _ = model(t1, t2)
            preds = torch.argmax(logits, dim=-1)
            all_preds.append(preds.cpu().numpy())
            all_gts.append(targets.numpy())

    preds_arr = np.concatenate(all_preds, axis=0)
    gts_arr = np.concatenate(all_gts, axis=0)
    return change_metrics(preds_arr, gts_arr)

def save_visual_examples(model: nn.Module, dataset: BiTemporalChangeGenuineDataset, output_dir: str, device: torch.device, num_samples: int = 5):
    examples_dir = os.path.join(output_dir, "examples")
    os.makedirs(examples_dir, exist_ok=True)
    model.eval()

    with torch.no_grad():
        for idx in range(min(num_samples, len(dataset))):
            t1_tensor, t2_tensor, label = dataset[idx]
            _, diff = model(t1_tensor.unsqueeze(0).to(device), t2_tensor.unsqueeze(0).to(device))
            diff_energy = torch.mean(diff[0]).item()

            t1_np = (t1_tensor.permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)
            t2_np = (t2_tensor.permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)

            # Create side-by-side composite
            w, h = t1_np.shape[1], t1_np.shape[0]
            composite = Image.new("RGB", (w * 2, h))
            composite.paste(Image.fromarray(t1_np), (0, 0))
            composite.paste(Image.fromarray(t2_np), (w, 0))

            out_file = os.path.join(examples_dir, f"change_pair_{idx+1:03d}.png")
            composite.save(out_file)
    print(f"[EXAMPLES] Saved change comparison composites to: {examples_dir}")

def train_change(args):
    set_seed(args.seed)
    profile = get_profile_config(args.profile)

    epochs = args.epochs if args.epochs else profile.epochs
    batch_size = args.batch_size if args.batch_size else profile.batch_size
    lr = args.lr if args.lr else profile.lr
    output_dir = args.output_dir or os.path.join(os.path.dirname(__file__), "runs", f"run_{args.profile}")
    manifest_dir = args.manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — Bi-Temporal Change Detection Training")
    print(f"Profile: {profile.name.upper()} ({profile.target_runtime})")
    print(f"Hardware: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print("============================================================\n")

    # 1. Load Genuine Datasets
    train_manifest = os.path.join(manifest_dir, "change_train.txt")
    val_manifest = os.path.join(manifest_dir, "change_val.txt")
    test_manifest = os.path.join(manifest_dir, "change_test.txt")

    train_ds = BiTemporalChangeGenuineDataset(args.data_dir, train_manifest, image_size=profile.image_size, max_samples=profile.max_train_samples)
    val_ds = BiTemporalChangeGenuineDataset(args.data_dir, val_manifest, image_size=profile.image_size, max_samples=profile.max_val_samples)
    test_ds = BiTemporalChangeGenuineDataset(args.data_dir, test_manifest, image_size=profile.image_size, max_samples=profile.max_test_samples)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=profile.num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=profile.num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=profile.num_workers)

    model = SiameseChangeDiffNet().to(device)

    # 2. Section 16 Mandatory: BASELINE EVALUATION (Untrained / Prior Distribution)
    print("------------------------------------------------------------")
    print("MANDATORY BASELINE EVALUATION (Untrained Change Prior)")
    print("------------------------------------------------------------")
    baseline_metrics = evaluate_change(model, val_loader, device)
    print(f"BASELINE Validation -> Accuracy: {baseline_metrics['accuracy_pct']:.2f}% | Macro F1: {baseline_metrics['macro_f1']:.4f}")

    # 3. Training Loop with CrossEntropy & AMP
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scaler = GradScaler(enabled=profile.use_amp)

    ckpt_mgr = CheckpointManager(output_dir, "change_specialist_model")
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
                logits, _ = model(t1, t2)
                loss = criterion(logits, targets)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        val_metrics = evaluate_change(model, val_loader, device)
        cur_f1 = val_metrics["macro_f1"]
        cur_acc = val_metrics["accuracy_pct"]

        history["train_loss"].append(round(avg_loss, 4))
        history["val_loss"].append(round(1.0 - cur_f1, 4))
        history["val_metric"].append(cur_f1)

        elapsed = time.time() - e_start
        print(f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s) - Loss: {avg_loss:.4f} | Val Acc: {cur_acc:.2f}% | Macro F1: {cur_f1:.4f}")

        is_best = cur_f1 > best_f1
        if is_best:
            best_f1 = cur_f1
            patience_counter = 0
        else:
            patience_counter += 1

        ckpt_mgr.save_checkpoint(model, epoch, is_best, cur_f1)

        if patience_counter >= profile.patience:
            print(f"\n[EARLY STOPPING] Validation Macro F1 plateaued for {profile.patience} epochs.")
            break

    total_time = time.time() - t_start
    print(f"\nTraining completed in {total_time / 60:.2f} minutes.")

    # 4. Final Held-Out Test Evaluation
    print("\n------------------------------------------------------------")
    print("FINAL TEST EVALUATION (On strictly held-out test split)")
    print("------------------------------------------------------------")
    best_weights = torch.load(ckpt_mgr.best_model_path, map_location=device)
    model.load_state_dict(best_weights)
    test_metrics = evaluate_change(model, test_loader, device)

    print(f"FINAL TEST -> Accuracy: {test_metrics['accuracy_pct']:.2f}% | Macro F1: {test_metrics['macro_f1']:.4f}")

    delta_acc = test_metrics["accuracy_pct"] - baseline_metrics["accuracy_pct"]
    print("------------------------------------------------------------")
    print(f"Baseline Acc: {baseline_metrics['accuracy_pct']:.2f}%")
    print(f"Trained Acc:  {test_metrics['accuracy_pct']:.2f}%")
    print(f"Improvement:  {'+' if delta_acc >= 0 else ''}{delta_acc:.2f}%")
    print("============================================================\n")

    reporter.save_history(history)
    reporter.save_evaluation(test_metrics, baseline_metrics)
    save_visual_examples(model, test_ds, output_dir, device, num_samples=5)

    ckpt_mgr.save_config({
        "dataset": "LEVIR-CD / OSCD",
        "profile": profile.name,
        "epochs_trained": epoch,
        "best_val_macro_f1": best_f1,
        "final_test_acc": test_metrics["accuracy_pct"],
        "training_time_min": round(total_time / 60, 2),
        "seed": args.seed,
        "device": str(device)
    })

    if args.export:
        ckpt_mgr.deploy_to_backend("change_specialist_model")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train bi-temporal change detection specialist.")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to LEVIR-CD or OSCD directory.")
    parser.add_argument("--manifest_dir", type=str, default=None)
    parser.add_argument("--profile", type=str, default="balanced", choices=["fast", "balanced", "quality"])
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--export", action="store_true", help="Deploy best model to backend/models/checkpoints/change_specialist_model/")
    args = parser.parse_args()

    train_change(args)
