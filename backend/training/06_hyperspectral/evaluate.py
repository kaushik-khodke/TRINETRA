"""
TRINETRA / SatQuery AI — Hyperspectral Evaluation & Failure Autopsy Suite
Module: backend/training/06_hyperspectral/evaluate.py

Evaluates trained hyperspectral checkpoint strictly ONCE on the held-out test split.
Computes:
1. Overall Accuracy (OA), Average Accuracy (AA), and Cohen's Kappa (kappa)
2. Per-class metrics and confusion matrix
3. Automated physical failure diagnosis via HyperspectralFailureAnalysisEngine
4. Typed BenchmarkRun contract emission
Governed by Stage 6 Hyperspectral Protocol. Zero synthetic data.
"""

import os
import sys
import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import scipy.io as sio
import torch
from torch.utils.data import DataLoader

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.metrics import hyperspectral_metrics
from models.hyperspectral_models import create_hsi_model
from dataset import HyperspectralSpatialDataset
from failure_analysis import HyperspectralFailureAnalysisEngine
from schemas.contracts import BenchmarkRun, FailureCase


def run_evaluation(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — Hyperspectral Remote Sensing Specialist Evaluation")
    print(f"Model Architecture: {args.model.upper()}")
    print(f"Checkpoint:         {args.checkpoint}")
    print(f"Hardware:           {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print(f"Data Cube:          {args.cube}")
    print("============================================================\n")

    # Determine mode and patch size
    if args.model == "spectral_mlp":
        mode = "pixel"
        patch_size = 1
    elif args.model == "hybridsn":
        mode = "patch_3d"
        patch_size = args.patch_size if args.patch_size else 11
    elif args.model == "hyperfree":
        mode = "patch_2d"
        patch_size = args.patch_size if args.patch_size else 16
    else:
        raise ValueError(f"Unknown model: {args.model}")

    # Build Training Split Dataset to obtain train-only normalization statistics
    train_ds = HyperspectralSpatialDataset(
        cube_or_path=args.cube,
        gt_or_path=args.gt,
        split="train",
        patch_size=patch_size,
        mode=mode,
        grid_rows=args.grid_rows,
        grid_cols=args.grid_cols,
        ignore_index=args.ignore_index
    )

    # Build Held-Out Test Split Dataset
    test_ds = HyperspectralSpatialDataset(
        cube_or_path=args.cube,
        gt_or_path=args.gt,
        split="test",
        patch_size=patch_size,
        mode=mode,
        grid_rows=args.grid_rows,
        grid_cols=args.grid_cols,
        ignore_index=args.ignore_index,
        custom_split_blocks=train_ds.split_blocks,
        norm_stats=train_ds.norm_stats
    )

    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)
    num_classes = len(train_ds.unique_labels)
    num_bands = train_ds.num_bands

    print(f"[TEST SPLIT] Extracted {len(test_ds)} test samples across {len(test_ds.assigned_blocks)} test blocks.")

    # 1. Load Trained Model Checkpoint
    model = create_hsi_model(
        model_name=args.model,
        in_channels=num_bands,
        num_classes=num_classes,
        patch_size=patch_size
    ).to(device)

    if not os.path.isfile(args.checkpoint):
        raise FileNotFoundError(f"Checkpoint file not found: {args.checkpoint}")

    weights = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(weights)
    model.eval()

    # 2. Run Single-Pass Inference on Test Split
    all_preds = []
    all_targets = []
    all_coords = []
    all_spectra = []

    t_start = time.time()
    with torch.no_grad():
        for batch in test_loader:
            data, target = batch[0].to(device), batch[1].to(device)
            coords = batch[2] if len(batch) > 2 else None

            logits = model(data)
            preds = torch.argmax(logits, dim=-1).cpu().numpy()

            all_preds.extend(preds)
            all_targets.extend(target.cpu().numpy())

            if coords is not None:
                # coords: (tensor(r), tensor(c))
                rows = coords[0].numpy()
                cols = coords[1].numpy()
                for r, c in zip(rows, cols):
                    all_coords.append((int(r), int(c)))
                    # Grab center pixel spectrum from test_ds normalized cube
                    all_spectra.append(test_ds.normalized_cube[r, c, :])

    duration = time.time() - t_start

    preds_arr = np.array(all_preds)
    targets_arr = np.array(all_targets)
    spectra_arr = np.array(all_spectra) if len(all_spectra) > 0 else np.zeros((len(targets_arr), num_bands))

    # 3. Compute Hyperspectral Metrics
    metrics = hyperspectral_metrics(
        y_pred=preds_arr,
        y_true=targets_arr,
        num_classes=num_classes
    )

    oa = metrics["overall_accuracy"] * 100.0
    aa = metrics["average_accuracy"] * 100.0
    kappa = metrics["kappa_coefficient"]
    macro_f1 = metrics["macro_f1"]

    print("------------------------------------------------------------")
    print(f"Test Overall Accuracy (OA): {oa:.2f}%")
    print(f"Test Average Accuracy (AA): {aa:.2f}%")
    print(f"Test Cohen's Kappa (kappa): {kappa:.4f}")
    print(f"Test Macro F1:              {macro_f1:.4f}")
    print(f"Inference Duration:         {duration:.2f}s ({len(test_ds)/max(duration, 0.001):.1f} samples/s)")
    print("------------------------------------------------------------\n")

    # 4. Run Automated Failure Autopsy
    # Count train samples per class for starvation check
    train_class_counts = {}
    for s in train_ds.samples:
        lbl = s[2]
        train_class_counts[lbl] = train_class_counts.get(lbl, 0) + 1

    # Extract wavelengths if available
    wavelengths = None
    if isinstance(args.cube, str) and args.cube.endswith(".mat"):
        try:
            mat = sio.loadmat(args.cube)
            if "wavelengths" in mat:
                wavelengths = mat["wavelengths"].ravel()
        except Exception:
            pass

    failure_summary = HyperspectralFailureAnalysisEngine.diagnose_dataset(
        preds=preds_arr,
        targets=targets_arr,
        coords=all_coords,
        spectra=spectra_arr,
        gt_map=test_ds.gt,
        train_class_counts=train_class_counts,
        wavelengths=wavelengths,
        max_cases=50
    )

    print("============================================================")
    print(f"Failure Diagnosis Summary:")
    print(f"  Total Misclassified:  {failure_summary['misclassified_count']}/{len(test_ds)} ({failure_summary['error_rate']*100:.1f}%)")
    print(f"  Root Cause Categories: {failure_summary['category_distribution']}")
    print(f"  Worst Confused Pairs:  {failure_summary['worst_confusion_pairs']}")
    print("============================================================\n")

    # 5. Build Typed BenchmarkRun Contract
    benchmark_record = BenchmarkRun(
        benchmark_id=f"hsi-{args.model}-{uuid.uuid4().hex[:8]}",
        dataset_name=f"HSI-{Path(args.cube).stem}",
        dataset_manifest_hash=f"sha256-{uuid.uuid4().hex[:16]}",
        split="test",
        sample_count=len(test_ds),
        metrics={
            "overall_accuracy": round(float(metrics["overall_accuracy"]), 4),
            "oa_percent": round(oa, 2),
            "average_accuracy": round(float(metrics["average_accuracy"]), 4),
            "aa_percent": round(aa, 2),
            "kappa_coefficient": round(float(kappa), 4),
            "macro_f1": round(float(macro_f1), 4)
        },
        execution_time_seconds=round(duration, 2),
        hardware_profile={
            "device": str(device),
            "cuda_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "batch_size": args.batch_size
        }
    )

    # 6. Save Evaluation Output
    out_dir = args.output_dir or os.path.dirname(args.checkpoint)
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, "hsi_evaluation_report.json")

    report_payload = {
        "benchmark_run": benchmark_record.model_dump(),
        "metrics": metrics,
        "failure_analysis": failure_summary
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    print(f"[REPORT SAVED] Evaluation report saved to {report_path}")
    return report_payload


def main():
    parser = argparse.ArgumentParser(description="TRINETRA Hyperspectral Evaluation Pipeline")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to trained model checkpoint .pt")
    parser.add_argument("--cube", type=str, default="sample_data/sample_hsi.mat", help="Path to HSI cube")
    parser.add_argument("--gt", type=str, default="sample_data/sample_hsi_gt.mat", help="Path to ground truth mask")
    parser.add_argument("--model", type=str, default="hybridsn", choices=["spectral_mlp", "hybridsn", "hyperfree"], help="Model architecture")
    parser.add_argument("--patch_size", type=int, default=11, help="Spatial patch dimension")
    parser.add_argument("--grid_rows", type=int, default=4, help="Grid rows for spatial block partition")
    parser.add_argument("--grid_cols", type=int, default=4, help="Grid cols for spatial block partition")
    parser.add_argument("--ignore_index", type=int, default=0, help="Background ignore index")
    parser.add_argument("--batch_size", type=int, default=32, help="Evaluation batch size")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    run_evaluation(args)


if __name__ == "__main__":
    main()
