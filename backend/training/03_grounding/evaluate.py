"""
TRINETRA / SatQuery AI — Text-Guided Region Grounding Evaluation Suite
Evaluates trained checkpoint on held-out test split, computing mIoU, Recall@0.50, and Recall@0.75.
"""

import os
import sys
import argparse
import json
import numpy as np
import torch
from torch.utils.data import DataLoader

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.metrics import grounding_metrics
from dataset import RSGroundingGenuineDataset
from model import RSGroundingDetector

def run_evaluation(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — Region Grounding Evaluation Suite")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Hardware:   {device}")
    print("============================================================\n")

    manifest = args.manifest or os.path.join(os.path.dirname(__file__), "manifests", "grounding_test.txt")
    test_ds = RSGroundingGenuineDataset(args.data_dir, manifest, max_samples=args.max_samples)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)

    model = RSGroundingDetector().to(device)
    weights = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(weights)
    model.eval()

    all_preds, all_gts = [], []
    with torch.no_grad():
        for imgs, tokens, gt_boxes in test_loader:
            imgs, tokens = imgs.to(device), tokens.to(device)
            preds = model(imgs, tokens)
            all_preds.append(preds.cpu().numpy())
            all_gts.append(gt_boxes.numpy())

    preds_arr = np.concatenate(all_preds, axis=0)
    gts_arr = np.concatenate(all_gts, axis=0)
    metrics = grounding_metrics(preds_arr, gts_arr)

    print("------------------------------------------------------------")
    print("TEST RESULTS (Held-Out Benchmark Set)")
    print("------------------------------------------------------------")
    print(f"Mean IoU (mIoU):     {metrics['mean_iou']:.4f}")
    print(f"Median IoU:          {metrics['median_iou']:.4f}")
    print(f"Recall@0.50 (Acc):   {metrics['recall_at_0.50_pct']:.2f}%")
    print(f"Recall@0.75:         {metrics['recall_at_0.75_pct']:.2f}%")
    print(f"Failure Count:       {metrics['failure_count']}")
    print(f"Total Evaluated:     {metrics['total_samples']:,}")
    print("============================================================\n")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"[SAVED] Metrics written to {args.output_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate region grounding model.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to best_model.pt.")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to DIOR_RSVG directory.")
    parser.add_argument("--manifest", type=str, default=None)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--output_json", type=str, default=None)
    args = parser.parse_args()

    run_evaluation(args)
