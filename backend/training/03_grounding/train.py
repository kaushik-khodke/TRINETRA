"""
TRINETRA / SatQuery AI — Text-Guided Region Grounding Training Pipeline
Trains bounding box detector on genuine DIOR-RSVG / VRSBench dataset on laptop GPU.
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
from PIL import Image, ImageDraw

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.seed import set_seed
from common.profiling import get_profile_config
from common.metrics import grounding_metrics
from common.checkpoint import CheckpointManager
from common.reporting import TrainingReporter

from dataset import RSGroundingGenuineDataset
from model import RSGroundingDetector, GiouLoss

DATASET_NAME = "DIOR-RSVG (Referring Remote Sensing Visual Grounding)"

def evaluate_grounding(model: nn.Module, loader: DataLoader, device: torch.device) -> dict:
    """Evaluates grounding model on dataloader without data leakage."""
    model.eval()
    all_preds, all_gts = [], []
    device_type = "cuda" if device.type == "cuda" else "cpu"
    with torch.no_grad():
        for imgs, tokens, gt_boxes in loader:
            imgs, tokens = imgs.to(device), tokens.to(device)
            with torch.amp.autocast(device_type=device_type, enabled=(device_type == "cuda")):
                pred_boxes = model(imgs, tokens)
            all_preds.append(pred_boxes.cpu().numpy())
            all_gts.append(gt_boxes.numpy())

    preds_arr = np.concatenate(all_preds, axis=0)
    gts_arr = np.concatenate(all_gts, axis=0)
    return grounding_metrics(preds_arr, gts_arr)

def save_visual_examples(model: nn.Module, dataset: RSGroundingGenuineDataset, output_dir: str, device: torch.device, num_samples: int = 5):
    """Saves visual comparison images showing ground-truth box vs predicted box."""
    examples_dir = os.path.join(output_dir, "examples")
    os.makedirs(examples_dir, exist_ok=True)
    model.eval()

    with torch.no_grad():
        for idx in range(min(num_samples, len(dataset))):
            img_tensor, token_tensor, gt_box = dataset[idx]
            pred_box = model(img_tensor.unsqueeze(0).to(device), token_tensor.unsqueeze(0).to(device))[0].cpu().numpy()
            gt_np = gt_box.numpy()

            # Render comparison image
            img_np = (img_tensor.permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)
            pil_img = Image.fromarray(img_np)
            draw = ImageDraw.Draw(pil_img)
            w, h = pil_img.size

            # GT in Green: [ymin, xmin, ymax, xmax] -> [x0, y0, x1, y1]
            gt_x0 = float(min(gt_np[1], gt_np[3]) * w)
            gt_y0 = float(min(gt_np[0], gt_np[2]) * h)
            gt_x1 = float(max(gt_np[1], gt_np[3]) * w)
            gt_y1 = float(max(gt_np[0], gt_np[2]) * h)
            draw.rectangle([gt_x0, gt_y0, gt_x1, gt_y1], outline="#10B981", width=3)

            # Pred in Red: [ymin, xmin, ymax, xmax] -> [x0, y0, x1, y1]
            pred_x0 = float(min(pred_box[1], pred_box[3]) * w)
            pred_y0 = float(min(pred_box[0], pred_box[2]) * h)
            pred_x1 = float(max(pred_box[1], pred_box[3]) * w)
            pred_y1 = float(max(pred_box[0], pred_box[2]) * h)
            draw.rectangle([pred_x0, pred_y0, pred_x1, pred_y1], outline="#EF4444", width=2)

            out_file = os.path.join(examples_dir, f"grounding_sample_{idx+1:03d}.png")
            pil_img.save(out_file)
    print(f"[EXAMPLES] Saved visual overlay samples to: {examples_dir}")

def train_grounding(args):
    set_seed(args.seed)
    profile = get_profile_config(args.profile)

    epochs = args.epochs if args.epochs else profile.epochs
    batch_size = args.batch_size if args.batch_size else profile.batch_size
    lr = args.lr if args.lr else profile.lr
    output_dir = args.output_dir or os.path.join(os.path.dirname(__file__), "runs", f"run_{args.profile}")
    manifest_dir = args.manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — Text-Guided Region Grounding Training")
    print(f"Profile: {profile.name.upper()} ({profile.target_runtime})")
    print(f"Hardware: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print("============================================================\n")

    patience = args.patience if args.patience is not None else profile.patience
    max_train = args.max_train_samples if args.max_train_samples is not None else profile.max_train_samples

    # 1. Load Genuine Datasets
    train_manifest = os.path.join(manifest_dir, "grounding_train.txt")
    val_manifest = os.path.join(manifest_dir, "grounding_val.txt")
    test_manifest = os.path.join(manifest_dir, "grounding_test.txt")

    train_ds = RSGroundingGenuineDataset(args.data_dir, train_manifest, image_size=profile.image_size, max_samples=max_train)
    val_ds = RSGroundingGenuineDataset(args.data_dir, val_manifest, image_size=profile.image_size, max_samples=profile.max_val_samples)
    test_ds = RSGroundingGenuineDataset(args.data_dir, test_manifest, image_size=profile.image_size, max_samples=profile.max_test_samples)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=profile.num_workers, pin_memory=torch.cuda.is_available())
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=profile.num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=profile.num_workers)

    model = RSGroundingDetector().to(device)
    if args.weights and os.path.exists(args.weights):
        weights = torch.load(args.weights, map_location=device)
        model.load_state_dict(weights, strict=False)
        print(f"[WARM-START] Continuing finetuning from existing checkpoint: {args.weights}")

    # 2. Section 16 Mandatory: BASELINE EVALUATION (Untrained / Center Prior)
    print("------------------------------------------------------------")
    print("MANDATORY BASELINE EVALUATION (Untrained Detector Prior)")
    print("------------------------------------------------------------")
    baseline_metrics = evaluate_grounding(model, val_loader, device)
    print(f"BASELINE Validation -> Mean IoU: {baseline_metrics['mean_iou']:.4f} | Recall@0.5: {baseline_metrics['recall_at_0.50_pct']:.2f}%")

    # 3. Training Loop with SmoothL1 + GIoU Loss + Cosine LR Scheduler
    l1_crit = nn.SmoothL1Loss()
    giou_crit = GiouLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=lr * 0.05)
    device_type = "cuda" if device.type == "cuda" else "cpu"
    use_scaler = profile.use_amp and (device_type == "cuda")
    scaler = torch.amp.GradScaler('cuda', enabled=True) if use_scaler else None

    ckpt_mgr = CheckpointManager(output_dir, "rs_grounding_model")
    reporter = TrainingReporter(output_dir)

    history = {"train_loss": [], "val_loss": [], "val_metric": []}
    best_miou = baseline_metrics["mean_iou"] if args.weights else -1.0
    patience_counter = 0

    if args.weights:
        ckpt_mgr.save_checkpoint(model, 0, is_best=True, metric_val=best_miou)
        print(f"[WARM-START LOCKED] Initial best model preserved at mIoU: {best_miou:.4f} (patience={patience})")

    t_start = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        e_start = time.time()

        for imgs, tokens, gt_boxes in train_loader:
            imgs, tokens, gt_boxes = imgs.to(device), tokens.to(device), gt_boxes.to(device)
            optimizer.zero_grad()
            with torch.amp.autocast(device_type=device_type, enabled=use_scaler):
                preds = model(imgs, tokens)
                loss = 2.0 * l1_crit(preds, gt_boxes) + 1.0 * giou_crit(preds, gt_boxes)

            if scaler is not None:
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                loss.backward()
                optimizer.step()
            total_loss += loss.item()

        scheduler.step()
        avg_loss = total_loss / len(train_loader)
        val_metrics = evaluate_grounding(model, val_loader, device)
        cur_miou = val_metrics["mean_iou"]

        history["train_loss"].append(round(avg_loss, 4))
        history["val_loss"].append(round(1.0 - cur_miou, 4))
        history["val_metric"].append(cur_miou)

        elapsed = time.time() - e_start
        cur_lr = scheduler.get_last_lr()[0]
        print(f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s, lr={cur_lr:.6f}) - Loss: {avg_loss:.4f} | Val mIoU: {cur_miou:.4f} | Recall@0.5: {val_metrics['recall_at_0.50_pct']:.2f}%")

        is_best = cur_miou > best_miou
        if is_best:
            best_miou = cur_miou
            patience_counter = 0
        else:
            patience_counter += 1

        ckpt_mgr.save_checkpoint(model, epoch, is_best, cur_miou)

        if patience_counter >= patience:
            print(f"\n[EARLY STOPPING] Validation mIoU started decreasing / plateaued for {patience} epochs. Stopping to keep the best model.")
            break

    total_time = time.time() - t_start
    print(f"\nTraining completed in {total_time / 60:.2f} minutes.")

    # 4. Final Held-Out Test Evaluation
    print("\n------------------------------------------------------------")
    print("FINAL TEST EVALUATION (On strictly held-out test split)")
    print("------------------------------------------------------------")
    best_weights = torch.load(ckpt_mgr.best_model_path, map_location=device)
    model.load_state_dict(best_weights)
    test_metrics = evaluate_grounding(model, test_loader, device)

    print(f"FINAL TEST -> Mean IoU: {test_metrics['mean_iou']:.4f} | Recall@0.50: {test_metrics['recall_at_0.50_pct']:.2f}% | Recall@0.75: {test_metrics['recall_at_0.75_pct']:.2f}%")

    delta_miou = test_metrics["mean_iou"] - baseline_metrics["mean_iou"]
    print("------------------------------------------------------------")
    print(f"Baseline mIoU: {baseline_metrics['mean_iou']:.4f}")
    print(f"Trained mIoU:  {test_metrics['mean_iou']:.4f}")
    print(f"Improvement:   {'+' if delta_miou >= 0 else ''}{delta_miou * 100:.2f}%")
    print("============================================================\n")

    reporter.save_history(history)
    reporter.save_evaluation(test_metrics, baseline_metrics)
    save_visual_examples(model, test_ds, output_dir, device, num_samples=5)

    ckpt_mgr.save_config({
        "dataset": DATASET_NAME,
        "profile": profile.name,
        "epochs_trained": epoch,
        "best_val_mIoU": best_miou,
        "final_test_mIoU": test_metrics["mean_iou"],
        "training_time_min": round(total_time / 60, 2),
        "seed": args.seed,
        "device": str(device)
    })

    if args.export:
        ckpt_mgr.deploy_to_backend("rs_grounding_model")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train text-guided region grounding detector.")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to real DIOR_RSVG directory.")
    parser.add_argument("--manifest_dir", type=str, default=None)
    parser.add_argument("--profile", type=str, default="balanced", choices=["fast", "balanced", "quality"])
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--patience", type=int, default=None, help="Early stopping patience (epochs to wait when metric decreases).")
    parser.add_argument("--max_train_samples", type=int, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--weights", type=str, default=None, help="Path to existing checkpoint to continue finetuning from.")
    parser.add_argument("--export", action="store_true", help="Deploy best model directly to backend/models/checkpoints/rs_grounding_model/")
    args = parser.parse_args()

    train_grounding(args)
