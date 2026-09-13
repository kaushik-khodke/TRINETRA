"""
TRINETRA / SatQuery AI — BigEarthNet-S2 Evaluation Suite
Evaluates trained checkpoint on held-out test split, generates per-class metrics and confusion matrix.
"""

import os
import sys
import argparse
import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.metrics import multilabel_metrics
from dataset import BigEarthNetS2Dataset, CORINE_19_CLASSES
from model import BigEarthNetAdaptedResNet

def run_evaluation(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print(f"TRINETRA — BigEarthNet-S2 Evaluation")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Hardware:   {device}")
    print("============================================================\n")

    manifest_file = args.manifest or os.path.join(os.path.dirname(__file__), "manifests", "bigearthnet_test.txt")
    test_ds = BigEarthNetS2Dataset(args.data_dir, manifest_file, args.metadata, num_bands=args.bands, max_samples=args.max_samples)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)

    model = BigEarthNetAdaptedResNet(in_channels=args.bands, num_classes=19, pretrained=False).to(device)
    weights = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(weights)
    model.eval()

    all_probs, all_targets = [], []
    with torch.no_grad():
        for imgs, targets in test_loader:
            imgs = imgs.to(device)
            probs = torch.sigmoid(model(imgs))
            all_probs.append(probs.cpu().numpy())
            all_targets.append(targets.numpy())

    probs_arr = np.concatenate(all_probs, axis=0)
    targets_arr = np.concatenate(all_targets, axis=0)

    metrics = multilabel_metrics(probs_arr, targets_arr)

    print("------------------------------------------------------------")
    print("EVALUATION RESULTS (Held-Out Test Set)")
    print("------------------------------------------------------------")
    print(f"Mean Average Precision (mAP): {metrics['mAP']:.4f}")
    print(f"Micro F1 Score:               {metrics['micro_f1']:.4f}")
    print(f"Macro F1 Score:               {metrics['macro_f1']:.4f}")
    print(f"Micro Precision:              {metrics['micro_precision']:.4f}")
    print(f"Micro Recall:                 {metrics['micro_recall']:.4f}")
    print(f"Total Test Patches Evaluated: {len(targets_arr):,}")
    print("============================================================\n")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"[SAVED] Metrics written to {args.output_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate BigEarthNet-S2 trained model.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to best_model.pt.")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to real image patches.")
    parser.add_argument("--metadata", type=str, required=True, help="Path to metadata.parquet.")
    parser.add_argument("--manifest", type=str, default=None, help="Path to test manifest.")
    parser.add_argument("--bands", type=int, default=4)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--output_json", type=str, default=None)
    args = parser.parse_args()

    run_evaluation(args)
