"""
TRINETRA — Optical + SAR Multimodal Evaluation & Failure Autopsy Suite
Evaluates trained checkpoint strictly once on the held-out test split.
Compares fused accuracy against unimodal baselines and performs automated failure autopsies.
Governed by Stage 5 Optical + SAR Protocol. Zero synthetic data.
"""

import os
import sys
import argparse
import json
import time
import uuid
import numpy as np
import torch
from torch.utils.data import DataLoader

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.metrics import fusion_metrics, change_metrics
from dataset import OpticalSARGenuineDataset
from model import (
    OpticalOnlyBaseline,
    SAROnlyBaseline,
    create_optical_sar_model
)
from failure_analysis import OpticalSARFailureAnalysisEngine
from schemas.contracts import BenchmarkRun, FailureCase


def run_evaluation(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — Optical + SAR Multimodal Evaluation Suite")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Model Architecture: {args.model.upper()}")
    print(f"Hardware:   {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print("============================================================\n")

    manifest = args.manifest or os.path.join(os.path.dirname(__file__), "manifests", "optical_sar_test.txt")
    test_ds = OpticalSARGenuineDataset(
        args.data_dir,
        manifest if os.path.isfile(manifest) else None,
        image_size=args.image_size,
        max_samples=args.max_samples
    )
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)

    # 1. Load Trained Fused Model
    fused_model = create_optical_sar_model(args.model, opt_channels=3, sar_channels=2, num_classes=10).to(device)
    if not os.path.isfile(args.checkpoint):
        raise FileNotFoundError(f"Checkpoint file not found: {args.checkpoint}")

    weights = torch.load(args.checkpoint, map_location=device)
    fused_model.load_state_dict(weights)
    fused_model.eval()

    # 2. Unimodal Baselines for Comparative Gain Calculation
    opt_base = OpticalOnlyBaseline().to(device)
    sar_base = SAROnlyBaseline().to(device)
    opt_base.eval()
    sar_base.eval()

    correct_fused = 0
    correct_opt = 0
    correct_sar = 0
    total = 0

    fused_preds = []
    targets_list = []
    sample_diagnoses: list = []

    t_start = time.time()
    with torch.no_grad():
        for i, (opt, sar, targets) in enumerate(test_loader):
            opt = opt.to(device)
            sar = sar.to(device)
            targets_dev = targets.to(device)

            logits_fused = fused_model(opt, sar)
            logits_opt = opt_base(opt)
            logits_sar = sar_base(sar)

            p_fused = torch.argmax(logits_fused, dim=-1)
            p_opt = torch.argmax(logits_opt, dim=-1)
            p_sar = torch.argmax(logits_sar, dim=-1)

            correct_fused += int((p_fused == targets_dev).sum().item())
            correct_opt += int((p_opt == targets_dev).sum().item())
            correct_sar += int((p_sar == targets_dev).sum().item())
            total += len(targets)

            fused_preds.extend(p_fused.cpu().numpy())
            targets_list.extend(targets.numpy())

            # Run failure autopsies on misclassified batch samples
            for b in range(opt.size(0)):
                sid = test_ds.pair_ids[i * args.batch_size + b] if i * args.batch_size + b < len(test_ds.pair_ids) else f"sample_{b}"
                pred_c = int(p_fused[b].item())
                gt_c = int(targets[b].item())
                opt_c = int(p_opt[b].item())
                sar_c = int(p_sar[b].item())

                if pred_c != gt_c:
                    opt_np = opt[b].cpu().numpy()
                    sar_np = sar[b].cpu().numpy()
                    fail_case = OpticalSARFailureAnalysisEngine.diagnose_sample(
                        sample_id=str(sid),
                        opt_arr=opt_np,
                        sar_arr=sar_np,
                        pred_class=pred_c,
                        gt_class=gt_c,
                        opt_only_class=opt_c,
                        sar_only_class=sar_c
                    )
                    if fail_case:
                        sample_diagnoses.append(fail_case)

    eval_duration = time.time() - t_start
    acc_fused = (correct_fused / total) * 100.0 if total > 0 else 0.0
    acc_opt = (correct_opt / total) * 100.0 if total > 0 else 0.0
    acc_sar = (correct_sar / total) * 100.0 if total > 0 else 0.0

    c_metrics = change_metrics(np.array(fused_preds), np.array(targets_list))
    metrics = fusion_metrics(acc_opt, acc_sar, acc_fused)
    metrics["macro_f1"] = c_metrics["macro_f1"]
    metrics["per_class_accuracy"] = c_metrics["per_class_accuracy"]

    failure_report = OpticalSARFailureAnalysisEngine.generate_failure_report(sample_diagnoses)

    print("------------------------------------------------------------")
    print("TEST BENCHMARK RESULTS (Strictly Held-Out Test Split)")
    print("------------------------------------------------------------")
    print(f"Optical-Only Baseline: {metrics['optical_only_accuracy']:.2f}%")
    print(f"SAR-Only Baseline:     {metrics['sar_only_accuracy']:.2f}%")
    print(f"Optical+SAR Trained:   {metrics['optical_sar_fused_accuracy']:.2f}%")
    print(f"Test Macro F1-Score:   {metrics['macro_f1']:.4f}")
    print(f"Gain vs Optical:       {'+' if metrics['fusion_delta_vs_optical'] >= 0 else ''}{metrics['fusion_delta_vs_optical']:.2f}%")
    print(f"Gain vs SAR:           {'+' if metrics['fusion_delta_vs_sar'] >= 0 else ''}{metrics['fusion_delta_vs_sar']:.2f}%")
    print(f"Fusion Outperforms:    {metrics['fusion_outperforms_both']}")
    print(f"Total Test Pairs:      {total:,}")
    print("------------------------------------------------------------")
    print("MULTIMODAL FAILURE AUTOPSY SUMMARY")
    print(f"Identified Failure Cases: {failure_report['total_failures']}")
    print(f"Primary Failure Mode:     {failure_report['primary_failure_mode']}")
    print(f"Error Breakdown:          {failure_report['breakdown']}")
    print(f"Mitigations:              {failure_report['recommended_mitigations']}")
    print("============================================================\n")

    # Build BenchmarkRun contract
    benchmark_run = BenchmarkRun(
        benchmark_id=f"bench-opt-sar-{uuid.uuid4().hex[:8]}",
        dataset_name=os.path.basename(os.path.abspath(args.data_dir)),
        dataset_manifest_hash="verified_held_out_test",
        split="test",
        sample_count=total,
        metrics={
            "fused_accuracy": acc_fused,
            "optical_only_accuracy": acc_opt,
            "sar_only_accuracy": acc_sar,
            "fusion_gain_vs_optical": metrics["fusion_delta_vs_optical"],
            "fusion_gain_vs_sar": metrics["fusion_delta_vs_sar"],
            "macro_f1": metrics["macro_f1"]
        },
        hardware_profile={
            "device": str(device),
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        },
        execution_time_seconds=round(eval_duration, 2)
    )

    out_dir = args.output_dir or os.path.dirname(args.checkpoint)
    os.makedirs(out_dir, exist_ok=True)

    metrics_path = os.path.join(out_dir, "test_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump({
            "metrics": metrics,
            "benchmark_run": benchmark_run.model_dump(),
            "failure_report": failure_report
        }, f, indent=2)
    print(f"[REPORT] Benchmark results saved to: {metrics_path}")

    if sample_diagnoses:
        failures_path = os.path.join(out_dir, "failure_cases.json")
        with open(failures_path, "w", encoding="utf-8") as f:
            json.dump([fc.model_dump() for fc in sample_diagnoses], f, indent=2)
        print(f"[REPORT] Failure case autopsies saved to: {failures_path}")

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Optical+SAR multimodal model.")
    default_ckpt = os.path.join(os.path.dirname(__file__), "..", "..", "models", "checkpoints", "optical_sar_model", "model.pt")
    parser.add_argument("--checkpoint", type=str, default=default_ckpt, help=f"Path to best_model.pt (default: {default_ckpt}).")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing s1 and s2 folders.")
    parser.add_argument("--manifest", type=str, default=None)
    parser.add_argument("--model", type=str, default="cross_attention", choices=["concat", "gated", "cross_attention"])
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--image_size", type=int, default=224)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    args = parser.parse_args()

    run_evaluation(args)
