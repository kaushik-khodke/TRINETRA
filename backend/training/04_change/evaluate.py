"""
TRINETRA / SatQuery AI — Bi-Temporal Change Evaluation Suite
Evaluates trained checkpoint on held-out test split, computing Accuracy and Macro F1.
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

from common.metrics import change_metrics
from dataset import BiTemporalChangeGenuineDataset
from model import SiameseChangeDiffNet

def run_evaluation(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — Bi-Temporal Change Evaluation Suite")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Hardware:   {device}")
    print("============================================================\n")

    manifest = args.manifest or os.path.join(os.path.dirname(__file__), "manifests", "change_test.txt")
    test_ds = BiTemporalChangeGenuineDataset(args.data_dir, manifest, max_samples=args.max_samples)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)

    model = SiameseChangeDiffNet().to(device)
    weights = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(weights)
    model.eval()

    all_preds, all_gts = [], []
    with torch.no_grad():
        for t1, t2, targets in test_loader:
            t1, t2 = t1.to(device), t2.to(device)
            logits, _ = model(t1, t2)
            preds = torch.argmax(logits, dim=-1)
            all_preds.append(preds.cpu().numpy())
            all_gts.append(targets.numpy())

    preds_arr = np.concatenate(all_preds, axis=0)
    gts_arr = np.concatenate(all_gts, axis=0)
    metrics = change_metrics(preds_arr, gts_arr)

    print("------------------------------------------------------------")
    print("TEST RESULTS (Held-Out Benchmark Set)")
    print("------------------------------------------------------------")
    print(f"Change Accuracy:     {metrics['accuracy_pct']:.2f}%")
    print(f"Macro F1:            {metrics['macro_f1']:.4f}")
    print(f"Per-Class Breakdown: {metrics['per_class_accuracy']}")
    print(f"Pairs Tested:        {metrics['total_samples']:,}")
    print("============================================================\n")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"[SAVED] Metrics written to {args.output_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate bi-temporal change model.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to best_model.pt.")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to dataset directory.")
    parser.add_argument("--manifest", type=str, default=None)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--output_json", type=str, default=None)
    args = parser.parse_args()

    run_evaluation(args)
