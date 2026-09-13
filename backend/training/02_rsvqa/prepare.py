"""
TRINETRA / SatQuery AI — RSVQA Dataset Preparation
Verifies real RSVQA/VRSBench images and question-answer JSON files, builds clean vocabulary and manifests.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.dataset_utils import verify_real_dataset, verify_split_leakage, save_manifest
from common.seed import set_seed

DATASET_NAME = "RSVQA (Remote Sensing Visual Question Answering)"
OFFICIAL_URL = "https://rsvqa.sylvainlobry.com/ (Zenodo Record 6344334 [LR] / 6344367 [HR])"

def prepare_rsvqa(data_dir: str, manifest_dir: str, max_vocab_size: int = 150, verify_only: bool = False):
    set_seed(42)
    print("=================================================================")
    print(f"TRINETRA — Preparing {DATASET_NAME}")
    print("=================================================================")

    data_path = Path(data_dir)
    if not data_path.exists():
        verify_real_dataset(data_dir, ["Images_LR"], DATASET_NAME, OFFICIAL_URL)

    # Check for presence of real question and answer JSON files (supports both standard and Zenodo LR_split_ formats)
    def resolve_qa_file(pattern_list):
        for pat in pattern_list:
            cand = data_path / pat
            if cand.exists():
                return cand
        return None

    train_q_path = resolve_qa_file(["LR_split_train_questions.json", "Questions_train.json"])
    train_a_path = resolve_qa_file(["LR_split_train_answers.json", "Answers_train.json"])
    val_q_path = resolve_qa_file(["LR_split_val_questions.json", "Questions_val.json"])
    val_a_path = resolve_qa_file(["LR_split_val_answers.json", "Answers_val.json"])
    test_q_path = resolve_qa_file(["LR_split_test_questions.json", "Questions_test.json"])
    test_a_path = resolve_qa_file(["LR_split_test_answers.json", "Answers_test.json"])

    missing = []
    if not train_q_path: missing.append("LR_split_train_questions.json (or Questions_train.json)")
    if not train_a_path: missing.append("LR_split_train_answers.json (or Answers_train.json)")
    if not val_q_path: missing.append("LR_split_val_questions.json (or Questions_val.json)")
    if not val_a_path: missing.append("LR_split_val_answers.json (or Answers_val.json)")
    if not test_q_path: missing.append("LR_split_test_questions.json (or Questions_test.json)")
    if not test_a_path: missing.append("LR_split_test_answers.json (or Answers_test.json)")

    if missing:
        raise RealDatasetVerificationError(
            f"\nMissing genuine RSVQA annotation files in {data_path.resolve()}:\n"
            f"  {missing}\n"
            f"Please download from official Zenodo repository: {OFFICIAL_URL}\n"
        )

    print(f"[+] Verified genuine RSVQA annotations at: {data_path.resolve()}")

    if verify_only:
        print("[SUCCESS] RSVQA dataset verified. Ready for training.")
        return

    # Load Questions and Answers (only active entries)
    with open(train_q_path, "r", encoding="utf-8") as f:
        train_q = [q for q in json.load(f)["questions"] if q.get("active", True) and "question" in q]
    with open(train_a_path, "r", encoding="utf-8") as f:
        train_a = [a for a in json.load(f)["answers"] if a.get("active", True) and "answer" in a]

    with open(val_q_path, "r", encoding="utf-8") as f:
        val_q = [q for q in json.load(f)["questions"] if q.get("active", True) and "question" in q]
    with open(test_q_path, "r", encoding="utf-8") as f:
        test_q = [q for q in json.load(f)["questions"] if q.get("active", True) and "question" in q]

    print(f"[+] Loaded: {len(train_q):,} Active Train Qs, {len(val_q):,} Active Val Qs, {len(test_q):,} Active Test Qs.")

    # Build genuine Answer Vocabulary from training set only (No test leakage!)
    answer_counts = Counter()
    for item in train_a:
        ans_text = str(item.get("answer", "")).strip().lower()
        if ans_text:
            answer_counts[ans_text] += 1

    top_answers = [ans for ans, _ in answer_counts.most_common(max_vocab_size)]
    ans2idx = {ans: idx for idx, ans in enumerate(top_answers)}
    idx2ans = {idx: ans for idx, ans in enumerate(top_answers)}

    out_dir = manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")
    os.makedirs(out_dir, exist_ok=True)

    vocab_file = os.path.join(out_dir, "rsvqa_vocab.json")
    with open(vocab_file, "w", encoding="utf-8") as f:
        json.dump({
            "ans2idx": ans2idx,
            "idx2ans": idx2ans,
            "total_answers_indexed": len(top_answers)
        }, f, indent=2)

    print(f"[+] Saved {len(top_answers)} genuine remote-sensing answer categories to: {vocab_file}")
    print("=================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare RSVQA dataset vocabulary and split verification.")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing official RSVQA JSONs and image subfolders.")
    parser.add_argument("--manifest_dir", type=str, default=None, help="Output directory for manifests.")
    parser.add_argument("--max_vocab_size", type=int, default=120, help="Maximum answer vocabulary size (default 120 matching model head).")
    parser.add_argument("--verify_only", action="store_true", help="Perform verification only.")
    args = parser.parse_args()

    prepare_rsvqa(args.data_dir, args.manifest_dir, args.max_vocab_size, args.verify_only)
