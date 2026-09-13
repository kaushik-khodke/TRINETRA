"""
TRINETRA / SatQuery AI — RS-VQA Training Pipeline
Trains multimodal VQA specialist on genuine RSVQA/VRSBench triplets on laptop GPU.
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
from common.metrics import vqa_metrics
from common.checkpoint import CheckpointManager
from common.reporting import TrainingReporter

from dataset import RSVqaGenuineDataset
from model import RSVqaFusionNetwork

def evaluate_vqa(model: nn.Module, loader: DataLoader, device: torch.device) -> dict:
    """Evaluates VQA model on dataloader."""
    model.eval()
    all_logits = []
    all_targets = []
    with torch.no_grad():
        for imgs, tokens, targets in loader:
            imgs, tokens = imgs.to(device), tokens.to(device)
            with autocast(enabled=(device.type == "cuda")):
                logits = model(imgs, tokens)
            all_logits.append(logits.cpu().numpy())
            all_targets.append(targets.numpy())

    logits_arr = np.concatenate(all_logits, axis=0)
    targets_arr = np.concatenate(all_targets, axis=0)
    return vqa_metrics(logits_arr, targets_arr)

def train_rsvqa(args):
    set_seed(args.seed)
    profile = get_profile_config(args.profile)

    epochs = args.epochs if args.epochs else profile.epochs
    batch_size = args.batch_size if args.batch_size else profile.batch_size
    lr = args.lr if args.lr else profile.lr
    output_dir = args.output_dir or os.path.join(os.path.dirname(__file__), "runs", f"run_{args.profile}")
    manifest_dir = args.manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")
    vocab_path = os.path.join(manifest_dir, "rsvqa_vocab.json")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — RS-VQA Specialist Training")
    print(f"Profile: {profile.name.upper()} ({profile.target_runtime})")
    print(f"Hardware: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print("============================================================\n")

    # 1. Load Genuine Datasets
    train_ds = RSVqaGenuineDataset(args.data_dir, split="train", vocab_path=vocab_path, max_samples=profile.max_train_samples)
    val_ds = RSVqaGenuineDataset(args.data_dir, split="val", vocab_path=vocab_path, max_samples=profile.max_val_samples)
    test_ds = RSVqaGenuineDataset(args.data_dir, split="test", vocab_path=vocab_path, max_samples=profile.max_test_samples)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=profile.num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=profile.num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=profile.num_workers)

    num_answers = len(train_ds.ans2idx)
    model = RSVqaFusionNetwork(num_answers=num_answers).to(device)

    # 2. Section 16 Mandatory: BASELINE EVALUATION (Untrained / Prior Distribution)
    print("------------------------------------------------------------")
    print("MANDATORY BASELINE EVALUATION")
    print("------------------------------------------------------------")
    baseline_metrics = evaluate_vqa(model, val_loader, device)
    print(f"BASELINE Validation -> Top-1 Acc: {baseline_metrics['top1_accuracy_pct']:.2f}% | Top-5 Acc: {baseline_metrics['top5_accuracy_pct']:.2f}%")

    # 3. Training Loop with AMP & Early Stopping
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scaler = GradScaler(enabled=profile.use_amp)

    ckpt_mgr = CheckpointManager(output_dir, "rs_vqa_model")
    reporter = TrainingReporter(output_dir)

    history = {"train_loss": [], "val_loss": [], "val_metric": []}
    best_acc = -1.0
    patience_counter = 0

    t_start = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        e_start = time.time()

        for imgs, tokens, targets in train_loader:
            imgs, tokens, targets = imgs.to(device), tokens.to(device), targets.to(device)
            optimizer.zero_grad()
            with autocast(enabled=(device.type == "cuda" and profile.use_amp)):
                logits = model(imgs, tokens)
                loss = criterion(logits, targets)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        val_metrics = evaluate_vqa(model, val_loader, device)
        cur_acc = val_metrics["top1_accuracy_pct"]

        history["train_loss"].append(round(avg_loss, 4))
        history["val_loss"].append(round(100.0 - cur_acc, 4))
        history["val_metric"].append(cur_acc)

        elapsed = time.time() - e_start
        print(f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s) - Loss: {avg_loss:.4f} | Val Top-1: {cur_acc:.2f}% | Top-5: {val_metrics['top5_accuracy_pct']:.2f}%")

        is_best = cur_acc > best_acc
        if is_best:
            best_acc = cur_acc
            patience_counter = 0
        else:
            patience_counter += 1

        ckpt_mgr.save_checkpoint(model, epoch, is_best, cur_acc)

        if patience_counter >= profile.patience:
            print(f"\n[EARLY STOPPING] Validation accuracy plateaued for {profile.patience} epochs.")
            break

    total_time = time.time() - t_start
    print(f"\nTraining completed in {total_time / 60:.2f} minutes.")

    # 4. Final Held-Out Test Evaluation
    print("\n------------------------------------------------------------")
    print("FINAL TEST EVALUATION (On strictly held-out test split)")
    print("------------------------------------------------------------")
    best_weights = torch.load(ckpt_mgr.best_model_path, map_location=device)
    model.load_state_dict(best_weights)
    test_metrics = evaluate_vqa(model, test_loader, device)

    print(f"FINAL TEST -> Top-1 Accuracy: {test_metrics['top1_accuracy_pct']:.2f}% | Top-5: {test_metrics['top5_accuracy_pct']:.2f}%")

    delta_acc = test_metrics["top1_accuracy_pct"] - baseline_metrics["top1_accuracy_pct"]
    print("------------------------------------------------------------")
    print(f"Baseline Top-1: {baseline_metrics['top1_accuracy_pct']:.2f}%")
    print(f"Trained Top-1:  {test_metrics['top1_accuracy_pct']:.2f}%")
    print(f"Improvement:    {'+' if delta_acc >= 0 else ''}{delta_acc:.2f}%")
    print("============================================================\n")

    reporter.save_history(history)
    reporter.save_evaluation(test_metrics, baseline_metrics)
    ckpt_mgr.save_config({
        "dataset": DATASET_NAME,
        "profile": profile.name,
        "num_answers": num_answers,
        "epochs_trained": epoch,
        "best_val_acc": best_acc,
        "final_test_acc": test_metrics["top1_accuracy_pct"],
        "training_time_min": round(total_time / 60, 2),
        "seed": args.seed,
        "device": str(device)
    })

    if args.export:
        ckpt_mgr.deploy_to_backend("rs_vqa_model")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train RS-VQA specialist on genuine dataset.")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing RSVQA JSONs and Images.")
    parser.add_argument("--manifest_dir", type=str, default=None)
    parser.add_argument("--profile", type=str, default="balanced", choices=["fast", "balanced", "quality"])
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--export", action="store_true", help="Deploy best model directly to backend/models/checkpoints/rs_vqa_model/")
    args = parser.parse_args()

    train_rsvqa(args)
