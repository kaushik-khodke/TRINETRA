"""
TRINETRA / SatQuery AI — Optical + SAR Evaluation Suite
Evaluates trained checkpoint on held-out test split, comparing against single-modality baselines.
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

from common.metrics import fusion_metrics, change_metrics
from dataset import OpticalSARGenuineDataset
from model import OpticalSARCrossAttentionNet, OpticalOnlyBaseline, SAROnlyBaseline

def run_evaluation(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — Optical + SAR Evaluation Suite")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Hardware:   {device}")
    print("============================================================\n")

    manifest = args.manifest or os.path.join(os.path.dirname(__file__), "manifests", "optical_sar_test.txt")
    test_ds = OpticalSARGenuineDataset(args.data_dir, manifest, max_samples=args.max_samples)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)

    fused_model = OpticalSARCrossAttentionNet().to(device)
    weights = torch.load(args.checkpoint, map_location=device)
    fused_model.load_state_dict(weights)
    fused_model.eval()

    opt_base = OpticalOnlyBaseline().to(device)
    sar_base = SAROnlyBaseline().to(device)

    # Evaluate Fused model
    correct_fused, correct_opt, correct_sar, total = 0, 0, 0, 0
    fused_preds, targets_list = [], []
    with torch.no_grad():
        for opt, sar, targets in test_loader:
            opt, sar, targets = opt.to(device), sar.to(device), targets.to(device)
            p_fused = torch.argmax(fused_model(opt, sar), dim=-1)
            preds_opt = torch.argmax(opt_base(opt), dim=-1)
            preds_sar = torch.argmax(sar_base(sar), dim=-1)

            correct_fused += int((p_fused == targets).sum().item())
            correct_opt += int((preds_opt == targets).sum().item())
            correct_sar += int((preds_sar == targets).sum().item())
            total += len(targets)

            fused_preds.extend(p_fused.cpu().numpy())
            targets_list.extend(targets.cpu().numpy())

    acc_fused = (correct_fused / total) * 100.0 if total > 0 else 0.0
    acc_opt = (correct_opt / total) * 100.0 if total > 0 else 0.0
    acc_sar = (correct_sar / total) * 100.0 if total > 0 else 0.0

    c_metrics = change_metrics(np.array(fused_preds), np.array(targets_list))
    metrics = fusion_metrics(acc_opt, acc_sar, acc_fused)
    metrics["macro_f1"] = c_metrics["macro_f1"]

    print("------------------------------------------------------------")
    print("TEST RESULTS (Held-Out Benchmark Set)")
    print("------------------------------------------------------------")
    print(f"Optical-Only Baseline: {metrics['optical_only_accuracy']:.2f}%")
    print(f"SAR-Only Baseline:     {metrics['sar_only_accuracy']:.2f}%")
    print(f"Optical+SAR Trained:   {metrics['optical_sar_fused_accuracy']:.2f}%")
    print(f"Test Macro F1-Score:   {metrics['macro_f1']:.4f}")
    print(f"Improvement vs Opt:    {'+' if metrics['fusion_delta_vs_optical'] >= 0 else ''}{metrics['fusion_delta_vs_optical']:.2f}%")
    print(f"Improvement vs SAR:    {'+' if metrics['fusion_delta_vs_sar'] >= 0 else ''}{metrics['fusion_delta_vs_sar']:.2f}%")
    print(f"Pairs Tested:          {total:,}")
    print("============================================================\n")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"[SAVED] Metrics written to {args.output_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Optical+SAR model.")
    default_ckpt = os.path.join(os.path.dirname(__file__), "runs", "run_balanced", "checkpoints", "best_model.pt")
    if not os.path.exists(default_ckpt):
        fallback_ckpt = os.path.join(os.path.dirname(__file__), "..", "..", "models", "checkpoints", "optical_sar_model", "model.pt")
        if os.path.exists(fallback_ckpt):
            default_ckpt = fallback_ckpt
    parser.add_argument("--checkpoint", type=str, default=default_ckpt, help=f"Path to best_model.pt (default: {default_ckpt}).")
    parser.add_argument("--data_dir", type=str, default="data/sen1-2", help="Directory containing s1 and s2 folders (default: data/sen1-2).")
    parser.add_argument("--manifest", type=str, default=None)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--output_json", type=str, default=None)
    args = parser.parse_args()

    run_evaluation(args)
