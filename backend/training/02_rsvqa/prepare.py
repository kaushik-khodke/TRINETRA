"""
TRINETRA / SatQuery AI — RSVQA & EarthVQA Dataset Preparation
Verifies real EarthVQA / RSVQA images and question-answer JSON files,
builds clean, leak-free vocabulary from training data only, and creates
versioned image-disjoint manifests.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter
import random

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.seed import set_seed

DATASET_NAME = "EarthVQA / RSVQA (Remote Sensing Visual Question Answering)"


def find_earthvqa_files(data_path: Path):
    """Locates EarthVQA QA JSON files and image directories."""
    train_qa = None
    val_qa = None
    test_qa = None

    # Search candidates
    for sub in ["2024EarthVQA/2024EarthVQA", "2024EarthVQA", ""]:
        base = data_path / sub
        cand_train = base / "Train_QA.json"
        cand_val = base / "Val_QA.json"
        cand_test = base / "Test_QA.json"
        if cand_train.exists():
            train_qa = cand_train
        if cand_val.exists():
            val_qa = cand_val
        if cand_test.exists():
            test_qa = cand_test

    # Locate image dirs
    train_img_dir = None
    val_img_dir = None
    test_img_dir = None

    for sub in ["Train-003/Train/images_png", "Train/images_png", "images_png/train", "images/train"]:
        cand = data_path / sub
        if cand.exists():
            train_img_dir = cand
            break

    for sub in ["Val-002/Val/images_png", "Val/images_png", "images_png/val", "images/val"]:
        cand = data_path / sub
        if cand.exists():
            val_img_dir = cand
            break

    for sub in ["Test-001/images_png", "Test/images_png", "images_png/test", "images/test"]:
        cand = data_path / sub
        if cand.exists():
            test_img_dir = cand
            break

    return train_qa, val_qa, test_qa, train_img_dir, val_img_dir, test_img_dir


def prepare_earthvqa(
    data_dir: str,
    manifest_dir: Optional[str] = None,
    seed: int = 42,
    verify_only: bool = False
):
    set_seed(seed)
    print("=================================================================")
    print(f"TRINETRA — Preparing {DATASET_NAME}")
    print("=================================================================")

    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset root directory not found: {data_dir}")

    # Check for EarthVQA dataset format first
    train_qa_p, val_qa_p, test_qa_p, train_img_d, val_img_d, test_img_d = find_earthvqa_files(data_path)

    if train_qa_p and val_qa_p and train_img_d and val_img_d:
        print(f"[+] Detected EarthVQA Dataset Format:")
        print(f"    Train QA:    {train_qa_p}")
        print(f"    Val QA:      {val_qa_p}")
        print(f"    Test QA:     {test_qa_p}")
        print(f"    Train Imgs:  {train_img_d}")
        print(f"    Val Imgs:    {val_img_d}")
        print(f"    Test Imgs:   {test_img_d}")

        with open(train_qa_p, "r", encoding="utf-8") as f:
            train_raw = json.load(f)
        with open(val_qa_p, "r", encoding="utf-8") as f:
            val_raw = json.load(f)

        total_train_qas = sum(len(qas) for qas in train_raw.values())
        total_val_qas = sum(len(qas) for qas in val_raw.values())

        print(f"[+] Loaded {len(train_raw):,} Train images ({total_train_qas:,} QA pairs).")
        print(f"[+] Loaded {len(val_raw):,} Val images ({total_val_qas:,} QA pairs).")

        if verify_only:
            print("[SUCCESS] Dataset verification passed.")
            return

        # Build genuine answer vocabulary from Train QA only (Rule 8: No test leakage)
        ans_counts = Counter()
        for img_name, qas in train_raw.items():
            for qa in qas:
                if qa.get("Answer") is not None:
                    ans_str = str(qa["Answer"]).strip().lower()
                    if ans_str != "":
                        ans_counts[ans_str] += 1

        print(f"[+] Found {len(ans_counts)} unique answers in training set.")
        
        # Sort answers by frequency descending for canonical indexing
        top_answers = [ans for ans, _ in ans_counts.most_common()]
        ans2idx = {ans: idx for idx, ans in enumerate(top_answers)}
        idx2ans = {idx: ans for idx, ans in enumerate(top_answers)}

        out_dir = manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")
        os.makedirs(out_dir, exist_ok=True)

        vocab_file = os.path.join(out_dir, "rsvqa_vocab.json")
        with open(vocab_file, "w", encoding="utf-8") as f:
            json.dump({
                "ans2idx": ans2idx,
                "idx2ans": idx2ans,
                "total_answers_indexed": len(top_answers),
                "dataset_name": "EarthVQA-2024",
                "derived_from": "Train_QA.json (zero test leakage)"
            }, f, indent=2)
        print(f"[+] Saved {len(top_answers)} genuine answers to: {vocab_file}")

        # Build Train Manifest
        train_manifest = os.path.join(out_dir, "vqa_train.jsonl")
        written_train = 0
        with open(train_manifest, "w", encoding="utf-8") as f:
            for img_name, qas in train_raw.items():
                img_path = str(train_img_d / img_name)
                for qa in qas:
                    if qa.get("Answer") is not None:
                        ans_str = str(qa["Answer"]).strip().lower()
                        if ans_str in ans2idx:
                            record = {
                                "image_path": img_path,
                                "image_name": img_name,
                                "question": qa["Question"],
                                "answer": ans_str,
                                "target_idx": ans2idx[ans_str],
                                "type": qa.get("Type", "Unknown")
                            }
                            f.write(json.dumps(record) + "\n")
                            written_train += 1
        print(f"[+] Wrote {written_train:,} training samples to: {train_manifest}")

        # Split Val into disjoint Validation (for early stopping) and Test (held out)
        val_img_list = sorted(list(val_raw.keys()))
        rng = random.Random(seed)
        rng.shuffle(val_img_list)

        n_val_split = len(val_img_list) // 2
        val_split_imgs = set(val_img_list[:n_val_split])
        test_split_imgs = set(val_img_list[n_val_split:])

        val_manifest = os.path.join(out_dir, "vqa_val.jsonl")
        test_manifest = os.path.join(out_dir, "vqa_test.jsonl")
        full_val_manifest = os.path.join(out_dir, "vqa_full_val.jsonl")

        written_val = 0
        written_test = 0
        written_full = 0

        with open(val_manifest, "w", encoding="utf-8") as f_val, \
             open(test_manifest, "w", encoding="utf-8") as f_test, \
             open(full_val_manifest, "w", encoding="utf-8") as f_full:
            
            for img_name, qas in val_raw.items():
                img_path = str(val_img_d / img_name)
                is_val = img_name in val_split_imgs
                for qa in qas:
                    if qa.get("Answer") is not None:
                        ans_str = str(qa["Answer"]).strip().lower()
                        target_idx = ans2idx.get(ans_str, -1)  # -1 if OOV
                        record = {
                            "image_path": img_path,
                            "image_name": img_name,
                            "question": qa["Question"],
                            "answer": ans_str,
                            "target_idx": target_idx,
                            "type": qa.get("Type", "Unknown")
                        }
                        line = json.dumps(record) + "\n"
                        f_full.write(line)
                        written_full += 1

                        if is_val:
                            f_val.write(line)
                            written_val += 1
                        else:
                            f_test.write(line)
                            written_test += 1

        print(f"[+] Wrote {written_val:,} disjoint Val samples ({len(val_split_imgs)} images) to: {val_manifest}")
        print(f"[+] Wrote {written_test:,} disjoint Test samples ({len(test_split_imgs)} images) to: {test_manifest}")
        print(f"[+] Wrote {written_full:,} Full Benchmark Val samples ({len(val_raw)} images) to: {full_val_manifest}")

        # Check for Test_QA (challenge submission set)
        if test_qa_p and test_img_d:
            with open(test_qa_p, "r", encoding="utf-8") as f:
                test_raw = json.load(f)
            test_sub_manifest = os.path.join(out_dir, "vqa_test_submission.jsonl")
            written_sub = 0
            with open(test_sub_manifest, "w", encoding="utf-8") as f:
                for img_name, qas in test_raw.items():
                    img_path = str(test_img_d / img_name)
                    for qa in qas:
                        record = {
                            "image_path": img_path,
                            "image_name": img_name,
                            "question": qa["Question"],
                            "type": qa.get("Type", "Unknown")
                        }
                        f.write(json.dumps(record) + "\n")
                        written_sub += 1
            print(f"[+] Wrote {written_sub:,} unlabeled Test challenge samples to: {test_sub_manifest}")

        print("\n[SUCCESS] Dataset preparation complete.")
        print("=================================================================\n")
        return

    # Fallback: Check for legacy RSVQA format (LR_split_* or Questions_*)
    raise FileNotFoundError(
        f"Could not locate EarthVQA files in {data_dir}. Expected Train_QA.json and image folders."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare RSVQA / EarthVQA dataset vocabulary and manifests.")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing EarthVQA or RSVQA files.")
    parser.add_argument("--manifest_dir", type=str, default=None, help="Output directory for manifests.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible split.")
    parser.add_argument("--verify_only", action="store_true", help="Perform verification only.")
    args = parser.parse_args()

    prepare_earthvqa(args.data_dir, args.manifest_dir, args.seed, args.verify_only)
