"""
TRINETRA / SatQuery AI — RS-VQA Evaluation Suite
Evaluates trained checkpoint on held-out test split, computing Top-1 & Top-5 accuracy.
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

from common.metrics import vqa_metrics
from dataset import RSVqaGenuineDataset
from model import RSVqaFusionNetwork

def run_evaluation(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("============================================================")
    print("TRINETRA — RS-VQA Evaluation Suite")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Hardware:   {device}")
    print("============================================================\n")

    vocab_path = args.vocab or os.path.join(os.path.dirname(__file__), "manifests", "rsvqa_vocab.json")
    test_ds = RSVqaGenuineDataset(args.data_dir, split="test", vocab_path=vocab_path, max_samples=args.max_samples)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)

    num_answers = len(test_ds.ans2idx)
    model = RSVqaFusionNetwork(num_answers=num_answers).to(device)
    weights = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(weights)
    model.eval()

    all_logits, all_targets = [], []
    with torch.no_grad():
        for imgs, tokens, targets in test_loader:
            imgs, tokens = imgs.to(device), tokens.to(device)
            logits = model(imgs, tokens)
            all_logits.append(logits.cpu().numpy())
            all_targets.append(targets.numpy())

    logits_arr = np.concatenate(all_logits, axis=0)
    targets_arr = np.concatenate(all_targets, axis=0)
    metrics = vqa_metrics(logits_arr, targets_arr)

    print("------------------------------------------------------------")
    print("TEST RESULTS (Held-Out Benchmark Set)")
    print("------------------------------------------------------------")
    print(f"Top-1 Accuracy:   {metrics['top1_accuracy_pct']:.2f}%")
    print(f"Top-5 Accuracy:   {metrics['top5_accuracy_pct']:.2f}%")
    print(f"Samples Tested:   {metrics['num_samples']:,}")
    print("============================================================\n")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"[SAVED] Metrics written to {args.output_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate RS-VQA checkpoint.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to best_model.pt.")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing RSVQA JSONs.")
    parser.add_argument("--vocab", type=str, default=None)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--output_json", type=str, default=None)
    args = parser.parse_args()

    run_evaluation(args)
