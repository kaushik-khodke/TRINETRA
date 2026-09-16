"""
TRINETRA / SatQuery AI — RS-VQA Evaluation Suite
Evaluates trained checkpoint on held-out test split, computing:
- Top-1 Accuracy, Top-5 Accuracy, Exact Match
- 95% Bootstrap Confidence Intervals
- Category-level breakdown (Presence, Count, Comparison, Area)
- Structured BenchmarkRun verification contract
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
from schemas.contracts import BenchmarkRun, VQAAnswerVerification

import importlib.util
def _load_rsvqa_local(mod_name: str, filename: str):
    p = os.path.join(rsvqa_dir, filename)
    spec = importlib.util.spec_from_file_location(mod_name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

RSVqaGenuineDataset = _load_rsvqa_local("rsvqa_dataset_mod", "dataset.py").RSVqaGenuineDataset
RSVqaFusionNetwork = _load_rsvqa_local("rsvqa_model_mod", "model.py").RSVqaFusionNetwork

def evaluate_vqa_benchmark(
    checkpoint_path: str,
    data_dir: str,
    vocab_path: Optional[str] = None,
    batch_size: int = 32,
    max_samples: Optional[int] = 1000,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """
    Executes benchmark evaluation on genuine held-out test data.
    Strictly zero synthetic or fabricated metrics.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(
            f"RS-VQA checkpoint not found at '{checkpoint_path}'. "
            "Please train the model using manual protocol per MANUAL_TRAINING_PROTOCOL.md."
        )

    if vocab_path is None:
        vocab_path = os.path.join(os.path.dirname(__file__), "manifests", "rsvqa_vocab.json")

    test_ds = RSVqaGenuineDataset(
        data_dir=data_dir,
        split="test",
        vocab_path=vocab_path,
        max_samples=max_samples
    )
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    # Invert ans2idx for exact answer verification
    idx2ans = {idx: ans for ans, idx in test_ds.ans2idx.items()}
    num_answers = len(test_ds.ans2idx)

    model = RSVqaFusionNetwork(num_answers=num_answers).to(device)
    weights = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(weights)
    model.eval()

    all_logits, all_targets, all_questions = [], [], []
    with torch.no_grad():
        for i, (imgs, tokens, targets) in enumerate(test_loader):
            imgs, tokens = imgs.to(device), tokens.to(device)
            logits = model(imgs, tokens)
            all_logits.append(logits.cpu().numpy())
            all_targets.append(targets.numpy())

    logits_arr = np.concatenate(all_logits, axis=0)
    targets_arr = np.concatenate(all_targets, axis=0)
    questions = [s["question"] for s in test_ds.samples[:len(targets_arr)]]

    metrics = vqa_metrics(
        logits=logits_arr,
        targets=targets_arr,
        questions=questions,
        idx2ans=idx2ans,
        compute_ci=True
    )

    # Compute per-sample verification details for auditability
    preds_top1 = np.argmax(logits_arr, axis=1)
    k = min(5, logits_arr.shape[1])
    top5_indices = np.argpartition(-logits_arr, kth=k-1, axis=1)[:, :k]

    verifications = []
    for idx in range(min(50, len(targets_arr))):  # Provenance sample audit
        q = questions[idx]
        target_idx = int(targets_arr[idx])
        pred_idx = int(preds_top1[idx])
        pred_ans = idx2ans.get(pred_idx, f"class_{pred_idx}")
        gt_ans = idx2ans.get(target_idx, f"class_{target_idx}")
        top5_cands = [idx2ans.get(int(c), f"class_{c}") for c in top5_indices[idx]]
        
        v = VQAAnswerVerification(
            question=q,
            predicted_answer=pred_ans,
            ground_truth_answer=gt_ans,
            is_correct=bool(pred_idx == target_idx),
            is_top5_correct=bool(target_idx in top5_indices[idx]),
            top5_candidates=top5_cands,
            question_category=categorize_question(q),
        )
        verifications.append(v.model_dump())

    metrics["sample_verifications"] = verifications
    metrics["checkpoint"] = checkpoint_path
    metrics["total_vocabulary_size"] = num_answers
    return metrics

def run_evaluation(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — RS-VQA Benchmark Evaluation Suite")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Hardware:   {device}")
    print("============================================================\n")

    if not os.path.exists(args.checkpoint):
        print(f"[ERROR] Checkpoint '{args.checkpoint}' does not exist.")
        print("Please train the model following MANUAL_TRAINING_PROTOCOL.md before running evaluation.")
        sys.exit(1)

    if not os.path.exists(args.data_dir):
        print(f"[ERROR] Dataset directory '{args.data_dir}' does not exist.")
        print("Please ensure genuine RSVQA benchmark files are available.")
        sys.exit(1)

    metrics = evaluate_vqa_benchmark(
        checkpoint_path=args.checkpoint,
        data_dir=args.data_dir,
        vocab_path=args.vocab,
        batch_size=args.batch_size,
        max_samples=args.max_samples,
        device=device
    )

    print("------------------------------------------------------------")
    print("TEST RESULTS (Held-Out Benchmark Set — Zero Synthetic Data)")
    print("------------------------------------------------------------")
    print(f"Top-1 Accuracy:       {metrics['top1_accuracy_pct']:.2f}% (95% CI: [{metrics['top1_ci_95'][0]:.2f}%, {metrics['top1_ci_95'][1]:.2f}%])")
    print(f"Top-5 Accuracy:       {metrics['top5_accuracy_pct']:.2f}%")
    print(f"Exact Match:          {metrics['exact_match_pct']:.2f}%")
    print(f"Samples Tested:       {metrics['num_samples']:,}")
    
    if "category_breakdown" in metrics:
        print("\nBreakdown by Question Category:")
        for cat, stats in metrics["category_breakdown"].items():
            print(f"  - {cat.capitalize():<12}: {stats['top1_accuracy_pct']:>6.2f}% ({stats['count']} samples)")
    print("============================================================\n")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"[SAVED] Metrics written to {args.output_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate RS-VQA checkpoint.")
    default_ckpt = os.path.join(os.path.dirname(__file__), "..", "..", "models", "checkpoints", "rs_vqa_model", "model.pt")
    if not os.path.exists(default_ckpt):
        default_ckpt = os.path.join(os.path.dirname(__file__), "runs", "run_balanced", "best_model.pt")
    default_data = r"D:\datasets\RSVQA_LR"
    default_vocab = os.path.join(os.path.dirname(__file__), "manifests", "rsvqa_vocab.json")

    parser.add_argument("--checkpoint", type=str, default=default_ckpt, help=f"Path to best_model.pt (default: {default_ckpt}).")
    parser.add_argument("--data_dir", type=str, default=default_data, help=f"Directory containing RSVQA JSONs (default: {default_data}).")
    parser.add_argument("--vocab", type=str, default=default_vocab, help="Path to vocabulary JSON.")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--max_samples", type=int, default=1000, help="Number of test samples to evaluate (default: 1000, None for all).")
    parser.add_argument("--output_json", type=str, default=None)
    args = parser.parse_args()

    run_evaluation(args)
