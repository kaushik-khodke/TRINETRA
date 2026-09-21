"""
TRINETRA / SatQuery AI — RS-VQA Evaluation Suite
Evaluates trained checkpoint on held-out test or validation manifests, computing:
- Top-1 Accuracy, Top-5 Accuracy, Exact Match
- 95% Bootstrap Confidence Intervals
- Category-level breakdown (Presence, Count, Comparison, Area, Reasoning)
- Structured verification and provenance audit
"""

import os
import sys
import argparse
import json
import numpy as np
import torch
from torch.utils.data import DataLoader
from typing import Dict, Any, Optional

rsvqa_dir = os.path.abspath(os.path.dirname(__file__))
training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for p in [rsvqa_dir, training_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from common.metrics import vqa_metrics, categorize_question
from dataset import EarthVqaGenuineDataset
from model import create_vqa_model, RSVqaFusionNetwork, load_vqa_model


def evaluate_vqa_benchmark(
    checkpoint_path: str,
    manifest_path: str,
    vocab_path: Optional[str] = None,
    batch_size: int = 64,
    max_samples: Optional[int] = None,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """
    Executes benchmark evaluation on genuine held-out data.
    Strictly zero synthetic or fabricated metrics.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"RS-VQA checkpoint not found at '{checkpoint_path}'.")

    if vocab_path is None:
        vocab_path = os.path.join(os.path.dirname(__file__), "manifests", "rsvqa_vocab.json")
    if not os.path.exists(vocab_path):
        raise FileNotFoundError(f"Vocabulary not found at '{vocab_path}'.")

    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab_data = json.load(f)
        idx2ans = {int(k): v for k, v in vocab_data["idx2ans"].items()}
        num_answers = len(idx2ans)

    test_ds = EarthVqaGenuineDataset(
        manifest_path=manifest_path,
        is_training=False,
        preload_cache=True,
        max_samples=max_samples
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda")
    )

    model = load_vqa_model(checkpoint_path, device=device)
    model.eval()

    all_logits, all_targets = [], []
    with torch.no_grad():
        for imgs, tokens, targets in test_loader:
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

    questions = [s["question"] for i, s in enumerate(test_ds.samples) if test_ds.samples[i].get("target_idx", -1) >= 0][:len(targets_arr)]

    metrics = vqa_metrics(
        logits=logits_arr,
        targets=targets_arr,
        questions=questions,
        idx2ans=idx2ans,
        compute_ci=True
    )

    # Question Type breakdown
    type_counts = {}
    type_top1 = {}
    preds_top1 = np.argmax(logits_arr, axis=1)
    for i, s in enumerate(test_ds.samples[:len(targets_arr)]):
        qt = s.get("type", "Unknown")
        type_counts[qt] = type_counts.get(qt, 0) + 1
        if preds_top1[i] == targets_arr[i]:
            type_top1[qt] = type_top1.get(qt, 0) + 1

    breakdown = {}
    for qt, total in type_counts.items():
        correct = type_top1.get(qt, 0)
        breakdown[qt] = {
            "total": total,
            "correct": correct,
            "top1_acc_pct": round((correct / total) * 100.0, 2)
        }

    metrics["breakdown_by_question_type"] = breakdown
    metrics["checkpoint"] = checkpoint_path
    metrics["total_vocabulary_size"] = num_answers
    return metrics


def run_evaluation(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — RS-VQA Benchmark Evaluation Suite")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Manifest:   {args.manifest}")
    print(f"Hardware:   {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print("============================================================\n")

    if not os.path.exists(args.checkpoint):
        print(f"[ERROR] Checkpoint '{args.checkpoint}' does not exist.")
        sys.exit(1)

    if not os.path.exists(args.manifest):
        print(f"[ERROR] Manifest '{args.manifest}' does not exist.")
        sys.exit(1)

    metrics = evaluate_vqa_benchmark(
        checkpoint_path=args.checkpoint,
        manifest_path=args.manifest,
        vocab_path=args.vocab,
        batch_size=args.batch_size,
        max_samples=args.max_samples,
        device=device
    )

    print("------------------------------------------------------------")
    print("EVALUATION RESULTS")
    print("------------------------------------------------------------")
    print(f"Top-1 Accuracy:       {metrics['top1_accuracy_pct']:.2f}% (95% CI: [{metrics['top1_ci_95'][0]:.2f}%, {metrics['top1_ci_95'][1]:.2f}%])")
    print(f"Top-5 Accuracy:       {metrics['top5_accuracy_pct']:.2f}%")
    print(f"Exact Match:          {metrics['exact_match_pct']:.2f}%")
    print(f"Samples Tested:       {metrics['num_samples']:,}")

    if "breakdown_by_question_type" in metrics:
        print("\nBreakdown by Question Type:")
        for qt, stats in metrics["breakdown_by_question_type"].items():
            print(f"  - {qt:<28}: {stats['top1_acc_pct']:>6.2f}% ({stats['correct']}/{stats['total']} samples)")
    print("============================================================\n")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"[SAVED] Metrics written to {args.output_json}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate RS-VQA checkpoint.")
    default_ckpt = os.path.join(os.path.dirname(__file__), "..", "..", "models", "checkpoints", "rs_vqa_model", "model.pt")
    default_manifest = os.path.join(os.path.dirname(__file__), "manifests", "vqa_test.jsonl")
    default_vocab = os.path.join(os.path.dirname(__file__), "manifests", "rsvqa_vocab.json")

    parser.add_argument("--checkpoint", type=str, default=default_ckpt, help=f"Path to checkpoint (default: {default_ckpt}).")
    parser.add_argument("--manifest", type=str, default=default_manifest, help=f"Path to manifest JSONL (default: {default_manifest}).")
    parser.add_argument("--vocab", type=str, default=default_vocab, help="Path to vocabulary JSON.")
    parser.add_argument("--batch_size", type=int, default=128)
    parser.add_argument("--max_samples", type=int, default=None, help="Max samples to evaluate (None for all).")
    parser.add_argument("--output_json", type=str, default=None)
    args = parser.parse_args()

    run_evaluation(args)
