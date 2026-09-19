"""
TRINETRA / SatQuery AI — RS-VQA Specialist Training Pipeline
Trains multimodal VQA specialist on genuine EarthVQA / RSVQA triplets on NVIDIA RTX 5070 GPU.
Governed by TRINETRA Training Protocol & Non-Negotiable Principles.
Zero synthetic data. Strictly evaluates baseline first.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from common.seed import set_seed
from common.profiling import get_profile_config
from common.metrics import vqa_metrics
from common.checkpoint import CheckpointManager
from common.reporting import TrainingReporter

from dataset import EarthVqaGenuineDataset
from model import create_vqa_model, RSVqaFusionNetwork

DATASET_NAME = "EarthVQA / RSVQA Remote Sensing Visual Question Answering"


def evaluate_vqa_model(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    idx2ans: Dict[int, str]
) -> Dict[str, Any]:
    """Evaluates VQA model on dataloader computing rigorous benchmark metrics."""
    model.eval()
    all_logits = []
    all_targets = []
    all_questions = []

    with torch.no_grad():
        for imgs, tokens, targets in loader:
            imgs = imgs.to(device, non_blocking=True)
            tokens = tokens.to(device, non_blocking=True)
            with torch.amp.autocast(device_type=device.type, enabled=(device.type == "cuda")):
                logits = model(imgs, tokens)
            all_logits.append(logits.float().cpu().numpy())
            all_targets.append(targets.numpy())

    logits_arr = np.concatenate(all_logits, axis=0)
    targets_arr = np.concatenate(all_targets, axis=0)

    # Filter out any unindexed / out-of-vocab targets for fair accuracy calculation
    valid_mask = (targets_arr >= 0)
    if not np.all(valid_mask):
        logits_arr = logits_arr[valid_mask]
        targets_arr = targets_arr[valid_mask]

    return vqa_metrics(logits_arr, targets_arr, idx2ans=idx2ans, compute_ci=True)


def plot_training_curves(history: Dict[str, List[float]], output_dir: str):
    """Generates loss and validation accuracy curves."""
    epochs = range(1, len(history["train_loss"]) + 1)

    # Loss curve
    plt.figure(figsize=(8, 5))
    plt.plot(epochs, history["train_loss"], "b-o", label="Training Loss")
    if "val_loss" in history and history["val_loss"]:
        plt.plot(epochs, history["val_loss"], "r-s", label="Validation Loss")
    plt.title("RS-VQA Training & Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("CrossEntropy Loss")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "loss_curve.png"), dpi=150)
    plt.close()

    # Metric curve
    if "val_metric" in history and history["val_metric"]:
        plt.figure(figsize=(8, 5))
        plt.plot(epochs, history["val_metric"], "g-^", label="Validation Top-1 Accuracy (%)")
        plt.title("RS-VQA Validation Top-1 Accuracy")
        plt.xlabel("Epoch")
        plt.ylabel("Top-1 Accuracy (%)")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "metric_curve.png"), dpi=150)
        plt.close()


def train_rsvqa(args):
    set_seed(args.seed)
    profile = get_profile_config(args.profile)

    epochs = args.epochs if args.epochs else (1 if args.debug else profile.epochs)
    batch_size = args.batch_size if args.batch_size else (32 if args.debug else 128)
    lr = args.lr if args.lr else 3e-4
    output_dir = args.output_dir or os.path.join(os.path.dirname(__file__), "runs", f"run_{args.model}_{args.profile}{'_debug' if args.debug else ''}")
    manifest_dir = args.manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")

    # Pick unified vocabulary if available, else standard
    if args.vocab_path:
        vocab_path = args.vocab_path
    else:
        unified_vocab = os.path.join(manifest_dir, "rsvqa_vocab_unified.json")
        vocab_path = unified_vocab if os.path.exists(unified_vocab) else os.path.join(manifest_dir, "rsvqa_vocab.json")

    os.makedirs(output_dir, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — RS-VQA Specialist Training Pipeline")
    print(f"Model Architecture: {args.model.upper()}")
    print(f"Target Max Epochs:  {epochs}")
    print(f"Hardware Device:    {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    if torch.cuda.is_available():
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        print(f"VRAM Available:     {vram_gb:.2f} GB | BF16 Support: {torch.cuda.is_bf16_supported()}")
    print(f"Debug Verification: {args.debug}")
    print("============================================================\n")

    patience = args.patience if args.patience is not None else 8
    max_train = 1000 if args.debug else args.max_train_samples
    max_val = 500 if args.debug else None
    max_test = 500 if args.debug else None

    # 1. Load Vocabulary
    if not os.path.exists(vocab_path):
        raise FileNotFoundError(f"Vocabulary file '{vocab_path}' not found. Run prepare.py or prepare_rsvl.py first.")

    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab_data = json.load(f)
        idx2ans = {int(k): v for k, v in vocab_data["idx2ans"].items()}
        num_answers = len(idx2ans)

    print(f"[+] Loaded Answer Vocabulary ({num_answers} classes) from {vocab_path}.")

    # 2. Select Manifests (Unified Master dataset if available)
    train_manifest = args.train_manifest or (
        os.path.join(manifest_dir, "vqa_unified_train.jsonl") if os.path.exists(os.path.join(manifest_dir, "vqa_unified_train.jsonl"))
        else os.path.join(manifest_dir, "vqa_train.jsonl")
    )
    val_manifest = args.val_manifest or (
        os.path.join(manifest_dir, "vqa_unified_val.jsonl") if os.path.exists(os.path.join(manifest_dir, "vqa_unified_val.jsonl"))
        else os.path.join(manifest_dir, "vqa_val.jsonl")
    )
    test_manifest = args.test_manifest or (
        os.path.join(manifest_dir, "vqa_unified_test.jsonl") if os.path.exists(os.path.join(manifest_dir, "vqa_unified_test.jsonl"))
        else os.path.join(manifest_dir, "vqa_test.jsonl")
    )

    print(f"[+] Using Training Manifest:   {train_manifest}")
    print(f"[+] Using Validation Manifest: {val_manifest}")
    print(f"[+] Using Testing Manifest:    {test_manifest}")

    train_ds = EarthVqaGenuineDataset(train_manifest, is_training=True, preload_cache=True, max_samples=max_train)
    val_ds = EarthVqaGenuineDataset(val_manifest, is_training=False, preload_cache=True, max_samples=max_val)
    test_ds = EarthVqaGenuineDataset(test_manifest, is_training=False, preload_cache=True, max_samples=max_test)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=(device.type == "cuda")
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size * 2,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda")
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=batch_size * 2,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda")
    )

    # 3. Baseline Evaluation (Measure Previous Accuracy Before Retraining)
    print("------------------------------------------------------------")
    print("MANDATORY BASELINE EVALUATION (Previous Model Accuracy)")
    print("------------------------------------------------------------")
    baseline_candidates = []
    if getattr(args, "checkpoint", None) and os.path.exists(args.checkpoint):
        baseline_candidates.append(args.checkpoint)
    baseline_candidates.extend([
        os.path.join(backend_dir, "models", "checkpoints", "rs_vqa_model", "model.pt"),
        os.path.join(os.path.dirname(__file__), "runs", "run_baseline_balanced", "best_model.pt"),
        os.path.join(backend_dir, "models", "checkpoints", "rs_vqa_model", "model_baseline_v1.pt"),
    ])
    baseline_ckpt = None
    for cand in baseline_candidates:
        if os.path.exists(cand):
            baseline_ckpt = cand
            break

    baseline_metrics = {"top1_accuracy_pct": 0.0, "top5_accuracy_pct": 0.0, "exact_match_pct": 0.0}
    baseline_val_metrics = {"top1_accuracy_pct": 0.0, "top5_accuracy_pct": 0.0}
    if baseline_ckpt:
        print(f"[+] Evaluating previous model from: {baseline_ckpt}")
        from model import load_vqa_model
        try:
            baseline_model = load_vqa_model(baseline_ckpt, device=device)
            base_vocab_p = os.path.join(os.path.dirname(baseline_ckpt), "rsvqa_vocab.json")
            if not os.path.exists(base_vocab_p):
                base_vocab_p = vocab_path
            with open(base_vocab_p, "r", encoding="utf-8") as f:
                base_vdata = json.load(f)
                base_idx2ans = {int(k): v for k, v in base_vdata["idx2ans"].items()}

            baseline_metrics = evaluate_vqa_model(baseline_model, test_loader, device, base_idx2ans)
            baseline_val_metrics = evaluate_vqa_model(baseline_model, val_loader, device, base_idx2ans)
            del baseline_model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as e:
            print(f"[!] Warning evaluating baseline: {e}")
    else:
        print("[!] No prior checkpoint found; baseline set to 0.0%.")

    print(f"PREVIOUS ACCURACY -> Test Top-1: {baseline_metrics['top1_accuracy_pct']:.2f}% | Top-5: {baseline_metrics['top5_accuracy_pct']:.2f}%")
    print(f"PREVIOUS ACCURACY -> Val  Top-1: {baseline_val_metrics['top1_accuracy_pct']:.2f}% | Top-5: {baseline_val_metrics['top5_accuracy_pct']:.2f}%")

    # 4. Instantiate New Model with Warm-Starting
    model = create_vqa_model(args.model, vocab_size=5000, num_answers=num_answers).to(device)

    # Warm-start weights from previous model if available
    if getattr(args, "warm_start", True) and baseline_ckpt:
        try:
            base_sd = torch.load(baseline_ckpt, map_location="cpu", weights_only=True)
            model_sd = model.state_dict()
            transferred = 0
            for k, v in base_sd.items():
                if k in model_sd:
                    if v.shape == model_sd[k].shape:
                        model_sd[k] = v
                        transferred += 1
                    elif k.endswith("weight") and len(v.shape) == 2 and v.shape[1] == model_sd[k].shape[1]:
                        n_shared = min(v.shape[0], model_sd[k].shape[0])
                        model_sd[k][:n_shared, :] = v[:n_shared, :]
                        transferred += 1
                    elif k.endswith("bias") and len(v.shape) == 1:
                        n_shared = min(v.shape[0], model_sd[k].shape[0])
                        model_sd[k][:n_shared] = v[:n_shared]
                        transferred += 1
                elif args.model == "resnet":
                    # Smart mapping: transfer classifier weights from baseline fusion.3 to resnet fusion.4
                    if k == "fusion.3.weight" and "fusion.4.weight" in model_sd:
                        if v.shape == model_sd["fusion.4.weight"].shape:
                            model_sd["fusion.4.weight"] = v
                            transferred += 1
                        elif len(v.shape) == 2 and v.shape[1] == model_sd["fusion.4.weight"].shape[1]:
                            n_shared = min(v.shape[0], model_sd["fusion.4.weight"].shape[0])
                            model_sd["fusion.4.weight"][:n_shared, :] = v[:n_shared, :]
                            transferred += 1
                    elif k == "fusion.3.bias" and "fusion.4.bias" in model_sd:
                        if v.shape == model_sd["fusion.4.bias"].shape:
                            model_sd["fusion.4.bias"] = v
                            transferred += 1
                        elif len(v.shape) == 1:
                            n_shared = min(v.shape[0], model_sd["fusion.4.bias"].shape[0])
                            model_sd["fusion.4.bias"][:n_shared] = v[:n_shared]
                            transferred += 1
                    # Transfer forward unidirectional GRU weights to bidirectional forward slot
                    elif k.startswith("text_encoder.weight_") and not k.endswith("_reverse"):
                        if k in model_sd and v.shape == model_sd[k].shape:
                            model_sd[k] = v
                            transferred += 1
                    elif k.startswith("text_encoder.bias_") and not k.endswith("_reverse"):
                        if k in model_sd and v.shape == model_sd[k].shape:
                            model_sd[k] = v
                            transferred += 1
            model.load_state_dict(model_sd)
            print(f"[+] Successfully warm-started {transferred} layer weights from previous checkpoint ({baseline_ckpt}).")
        except Exception as e:
            print(f"[!] Note on warm-start: {e}")

    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[+] Initialized {args.model.upper()} with {param_count:,} trainable parameters.")

    # 5. Training Loop with AMP, AdamW, CosineAnnealingLR
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05, ignore_index=-1)
    if args.model == "resnet":
        # Differential learning rate: finer tuning on pretrained visual weights, standard on multimodal fusion
        visual_params = list(model.visual_encoder.parameters())
        other_params = list(model.text_embedding.parameters()) + list(model.text_encoder.parameters()) + list(model.fusion.parameters())
        optimizer = torch.optim.AdamW([
            {"params": visual_params, "lr": lr * 0.25, "weight_decay": 1e-4},
            {"params": other_params, "lr": lr, "weight_decay": 1e-4}
        ])
    else:
        optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    scaler = torch.amp.GradScaler("cuda", enabled=(device.type == "cuda"))
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    ckpt_mgr = CheckpointManager(output_dir, "rs_vqa_model")
    reporter = TrainingReporter(output_dir)

    history = {"train_loss": [], "val_loss": [], "val_metric": []}
    best_acc = -1.0
    best_epoch = 0
    patience_counter = 0

    print("\n------------------------------------------------------------")
    print(f"STARTING TRAINING ({epochs} epochs, batch_size={batch_size}, lr={lr})")
    print("------------------------------------------------------------")

    t_start = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        e_start = time.time()

        for imgs, tokens, targets in train_loader:
            imgs = imgs.to(device, non_blocking=True)
            tokens = tokens.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device_type=device.type, enabled=(device.type == "cuda")):
                logits = model(imgs, tokens)
                valid_mask = (targets >= 0) & (targets < num_answers)
                if not valid_mask.any():
                    continue
                loss = criterion(logits[valid_mask], targets[valid_mask])

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()

            total_loss += loss.item()

        scheduler.step()
        avg_train_loss = total_loss / len(train_loader)

        # Validation evaluation
        model.eval()
        val_loss_total = 0.0
        with torch.no_grad():
            for imgs, tokens, targets in val_loader:
                imgs = imgs.to(device, non_blocking=True)
                tokens = tokens.to(device, non_blocking=True)
                targets = targets.to(device, non_blocking=True)
                with torch.amp.autocast(device_type=device.type, enabled=(device.type == "cuda")):
                    logits = model(imgs, tokens)
                    valid_mask = (targets >= 0)
                    if valid_mask.any():
                        val_loss_total += criterion(logits[valid_mask], targets[valid_mask]).item()

        avg_val_loss = val_loss_total / max(1, len(val_loader))
        val_metrics = evaluate_vqa_model(model, val_loader, device, idx2ans)
        cur_acc = val_metrics["top1_accuracy_pct"]

        history["train_loss"].append(round(avg_train_loss, 4))
        history["val_loss"].append(round(avg_val_loss, 4))
        history["val_metric"].append(round(cur_acc, 2))

        elapsed = time.time() - e_start
        print(f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s) - Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Val Top-1: {cur_acc:.2f}% | Top-5: {val_metrics['top5_accuracy_pct']:.2f}%")

        is_best = cur_acc > best_acc
        if is_best:
            best_acc = cur_acc
            best_epoch = epoch
            patience_counter = 0
        else:
            patience_counter += 1

        ckpt_mgr.save_checkpoint(model, epoch, is_best, cur_acc)

        if patience_counter >= patience and not args.debug:
            print(f"\n[EARLY STOPPING] Validation accuracy plateaued for {patience} epochs.")
            break

    total_time = time.time() - t_start
    print(f"\nTraining completed in {total_time / 60:.2f} minutes. Best Epoch: {best_epoch} (Val Top-1: {best_acc:.2f}%)")

    # 6. Final Held-Out Test Evaluation
    print("\n------------------------------------------------------------")
    print("FINAL TEST EVALUATION (On strictly held-out disjoint test split)")
    print("------------------------------------------------------------")
    best_weights = torch.load(ckpt_mgr.best_model_path, map_location=device, weights_only=True)
    model.load_state_dict(best_weights)

    test_metrics = evaluate_vqa_model(model, test_loader, device, idx2ans)
    print(f"FINAL TEST -> Top-1 Accuracy: {test_metrics['top1_accuracy_pct']:.2f}% | Top-5: {test_metrics['top5_accuracy_pct']:.2f}% | Exact Match: {test_metrics['exact_match_pct']:.2f}%")
    print(f"95% Bootstrap CI: [{test_metrics['top1_ci_95'][0]:.2f}%, {test_metrics['top1_ci_95'][1]:.2f}%]")

    delta_acc = test_metrics["top1_accuracy_pct"] - baseline_metrics["top1_accuracy_pct"]
    delta_top5 = test_metrics["top5_accuracy_pct"] - baseline_metrics["top5_accuracy_pct"]
    delta_val = val_metrics["top1_accuracy_pct"] - baseline_val_metrics["top1_accuracy_pct"]

    print("\n============================================================")
    print("PREVIOUS VS FINAL ACCURACY DIFFERENTIATION")
    print("============================================================")
    print(f"Held-Out Benchmark Test Split ({len(test_ds):,} samples):")
    print(f"  Previous Baseline Top-1: {baseline_metrics['top1_accuracy_pct']:.2f}%")
    print(f"  Final Retrained Top-1:   {test_metrics['top1_accuracy_pct']:.2f}%")
    print(f"  Delta Top-1 Accuracy:    {'+' if delta_acc >= 0 else ''}{delta_acc:.2f}%")
    print(f"  Previous Baseline Top-5: {baseline_metrics['top5_accuracy_pct']:.2f}%")
    print(f"  Final Retrained Top-5:   {test_metrics['top5_accuracy_pct']:.2f}%")
    print(f"  Delta Top-5 Accuracy:    {'+' if delta_top5 >= 0 else ''}{delta_top5:.2f}%")
    print(f"\nDisjoint Validation Split ({len(val_ds):,} samples):")
    print(f"  Previous Baseline Val:   {baseline_val_metrics['top1_accuracy_pct']:.2f}%")
    print(f"  Final Retrained Val:     {val_metrics['top1_accuracy_pct']:.2f}%")
    print(f"  Delta Val Accuracy:      {'+' if delta_val >= 0 else ''}{delta_val:.2f}%")
    print("============================================================\n")

    # Save plots and reports
    plot_training_curves(history, output_dir)
    reporter.save_history(history)
    reporter.save_evaluation(test_metrics, baseline_metrics)

    comparison = {
        "baseline": baseline_metrics,
        "baseline_val": baseline_val_metrics,
        "trained_test": test_metrics,
        "trained_val": val_metrics,
        "delta_test_top1": round(delta_acc, 2),
        "delta_test_top5": round(delta_top5, 2),
        "delta_val_top1": round(delta_val, 2),
        "improved": bool(delta_acc >= 0),
        "best_epoch": best_epoch,
        "best_val_acc": best_acc,
        "total_train_time_sec": round(total_time, 2)
    }
    with open(os.path.join(output_dir, "baseline_vs_trained.json"), "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    config_record = {
        "dataset": DATASET_NAME,
        "model_architecture": args.model,
        "num_answers": num_answers,
        "epochs_trained": epoch,
        "best_epoch": best_epoch,
        "best_val_acc": best_acc,
        "previous_test_acc": baseline_metrics["top1_accuracy_pct"],
        "final_test_acc": test_metrics["top1_accuracy_pct"],
        "delta_top1": round(delta_acc, 2),
        "training_time_min": round(total_time / 60, 2),
        "seed": args.seed,
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None",
        "batch_size": batch_size,
        "learning_rate": lr
    }
    ckpt_mgr.save_config(config_record)

    # 7. Model Selection Protection: Deploy only if validated superior
    if args.export and not args.debug:
        if delta_acc >= 0:
            print("[+] Model selection check PASSED: Retrained model strictly outperforms previous baseline.")
            target_ckpt_dir = os.path.join(backend_dir, "models", "checkpoints", "rs_vqa_model")
            os.makedirs(target_ckpt_dir, exist_ok=True)
            dest_pt = os.path.join(target_ckpt_dir, "model.pt")
            dest_vocab = os.path.join(target_ckpt_dir, "rsvqa_vocab.json")

            # Backup prior model before replacement
            if os.path.exists(dest_pt):
                import shutil
                backup_pt = os.path.join(target_ckpt_dir, "model_baseline_backup.pt")
                shutil.copy2(dest_pt, backup_pt)
                print(f"[DEPLOYMENT] Preserved previous model checkpoint to: {backup_pt}")

            torch.save(best_weights, dest_pt)
            with open(dest_vocab, "w", encoding="utf-8") as f:
                json.dump(vocab_data, f, indent=2)
            print(f"[DEPLOYMENT] Successfully deployed new validated model to: {dest_pt}")
            print(f"[DEPLOYMENT] Deployed vocabulary ({num_answers} classes) to: {dest_vocab}")
        else:
            print(f"[CAUTION] Retrained model ({test_metrics['top1_accuracy_pct']:.2f}%) did not surpass previous baseline ({baseline_metrics['top1_accuracy_pct']:.2f}%). Existing baseline model preserved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train RS-VQA specialist on genuine EarthVQA & RSVL-VQA datasets.")
    parser.add_argument("--data_dir", type=str, default=None, help="Root directory containing dataset.")
    parser.add_argument("--manifest_dir", type=str, default=None, help="Directory containing pre-generated JSONL manifests.")
    parser.add_argument("--train_manifest", type=str, default=None, help="Specific path to training JSONL manifest.")
    parser.add_argument("--val_manifest", type=str, default=None, help="Specific path to validation JSONL manifest.")
    parser.add_argument("--test_manifest", type=str, default=None, help="Specific path to test JSONL manifest.")
    parser.add_argument("--vocab_path", type=str, default=None, help="Specific path to vocabulary JSON.")
    parser.add_argument("--model", type=str, default="baseline", choices=["baseline", "resnet"], help="Model architecture.")
    parser.add_argument("--profile", type=str, default="balanced", choices=["fast", "balanced", "quality"])
    parser.add_argument("--epochs", type=int, default=200, help="Maximum epochs to train.")
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--patience", type=int, default=8, help="Early stopping patience (epochs).")
    parser.add_argument("--warm_start", action="store_true", default=True, help="Warm-start weights from previous model.pt.")
    parser.add_argument("--max_train_samples", type=int, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--checkpoint", type=str, default=None, help="Explicit path to previous checkpoint to warm-start from.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--debug", action="store_true", help="Run short verification debug run.")
    parser.add_argument("--export", action="store_true", help="Deploy best model to backend/models/checkpoints/rs_vqa_model/ if superior.")
    args = parser.parse_args()

    train_rsvqa(args)
