"""
TRINETRA / SatQuery AI — RSVL-VQA Dataset Ingestion & Unified Manifest Generator
Parses 13,820 satellite scenes across INRIA, LoveDA, WHU, and iSAID.
Extracts high-signal canonical VQA pairs and partitions by disjoint scene ID.
Blends with EarthVQA to produce unified hackathon-ready manifests.
"""

import os
import sys
import json
import re
import random
from collections import Counter
from typing import Dict, List, Any, Tuple

def resolve_rsvl_image_path(base_dir: str, img_rel: str) -> str:
    """Resolves relative image paths across INRIA, LoveDA, WHU, and iSAID."""
    parts = img_rel.replace("\\", "/").split("/")
    if parts[0] in ["RSVLM-QA", "RSVL-VQA"]:
        parts = parts[1:]
    
    # Try direct join
    p1 = os.path.join(base_dir, *parts)
    if os.path.exists(p1):
        return p1
    
    # LoveDA case adjustment: 'LoveDA/Train/...' -> 'LoveDA/train/Train/...'
    if len(parts) >= 2 and parts[0] == "LoveDA":
        p2 = os.path.join(base_dir, "LoveDA", parts[1].lower(), *parts[1:])
        if os.path.exists(p2):
            return p2
            
    return None

def extract_canonical_qa(q: str, a: str, qt: str) -> str:
    """Extracts crisp, high-signal canonical answers for classification."""
    a_lower = a.strip().lower()
    
    if qt == "presence":
        if a_lower.startswith("yes"):
            return "yes"
        elif a_lower.startswith("no"):
            return "no"
            
    elif qt == "count":
        m = re.search(r"there are (\d+) ", a_lower)
        if m:
            val = int(m.group(1))
            if val <= 10:
                return str(val)
            elif val <= 20:
                return "11-20"
            elif val <= 50:
                return "21-50"
            elif val <= 100:
                return "51-100"
            else:
                return "more than 100"
                
    elif qt == "comparison":
        if "equal" in a_lower or "same" in a_lower:
            return "equal"
        m = re.search(r"there are more ([a-z\s_]+)\s*\(\d+\)\s*than", a_lower)
        if m:
            obj = m.group(1).strip()
            return f"more {obj}"
            
    elif qt in ["overall", "object"]:
        if "urban" in a_lower and "rural" not in a_lower:
            return "urban"
        elif "rural" in a_lower and "urban" not in a_lower:
            return "rural"
        elif "residential" in a_lower and len(a_lower.split()) <= 6:
            return "residential"
        elif "agricultural" in a_lower and len(a_lower.split()) <= 6:
            return "agricultural"
        elif "commercial" in a_lower and len(a_lower.split()) <= 6:
            return "commercial"
        elif "industrial" in a_lower and len(a_lower.split()) <= 6:
            return "industrial"
            
    elif qt == "spatial":
        if "upper left" in a_lower:
            return "upper left"
        elif "upper right" in a_lower:
            return "upper right"
        elif "lower left" in a_lower:
            return "lower left"
        elif "lower right" in a_lower:
            return "lower right"
        elif "center" in a_lower or "central" in a_lower:
            return "center"

    return None

def main():
    random.seed(42)
    rsvl_dir = r"C:\Users\student\Downloads\datasets\RSVL-VQA"
    jsonl_path = os.path.join(rsvl_dir, "RSVLM-QA.jsonl")
    manifest_dir = os.path.join(os.path.dirname(__file__), "manifests")
    base_vocab_path = os.path.join(manifest_dir, "rsvqa_vocab.json")

    print("============================================================")
    print("TRINETRA — RSVL-VQA Ingestion & Unified Manifest Generator")
    print(f"Dataset Root:   {rsvl_dir}")
    print(f"Annotation:     {jsonl_path}")
    print(f"Manifest Dir:   {manifest_dir}")
    print("============================================================\n")

    # 1. Load Base 147 Vocabulary
    with open(base_vocab_path, "r", encoding="utf-8") as f:
        base_vocab = json.load(f)
    
    idx2ans = {int(k): v for k, v in base_vocab["idx2ans"].items()}
    ans2idx = {v: int(k) for k, v in base_vocab["idx2ans"].items()}
    next_idx = len(ans2idx)
    print(f"[+] Loaded baseline vocabulary: {len(ans2idx)} classes.")

    # 2. Parse RSVL-VQA by Scenes
    scenes: Dict[str, List[Dict[str, Any]]] = {}
    total_raw_pairs = 0
    total_valid_pairs = 0
    ans_counter = Counter()

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            img_rel = data.get("image", "")
            resolved_img = resolve_rsvl_image_path(rsvl_dir, img_rel)
            if not resolved_img:
                continue

            scene_qa = []
            for qa in data.get("vqa_pairs", []):
                total_raw_pairs += 1
                q = qa.get("question", "").strip()
                a = qa.get("answer", "").strip()
                qt = qa.get("question_type", "unknown")
                
                canon = extract_canonical_qa(q, a, qt)
                if canon:
                    ans_counter[canon] += 1
                    scene_qa.append({
                        "image_path": resolved_img,
                        "image_name": os.path.basename(resolved_img),
                        "question": q,
                        "raw_answer": a,
                        "answer": canon,
                        "type": qt,
                        "source": "RSVL-VQA"
                    })
                    total_valid_pairs += 1

            if scene_qa:
                scenes[resolved_img] = scene_qa

    print(f"[+] Parsed {len(scenes):,} valid scenes with {total_valid_pairs:,} high-signal QA pairs (from {total_raw_pairs:,} raw).")

    # 3. Expand Vocabulary with New Frequent Classes (count >= 50)
    new_classes_added = 0
    for ans, count in ans_counter.most_common():
        if count >= 50 and ans not in ans2idx:
            ans2idx[ans] = next_idx
            idx2ans[next_idx] = ans
            next_idx += 1
            new_classes_added += 1

    print(f"[+] Added {new_classes_added} new classes to vocabulary. Total Unified Classes: {len(ans2idx)}")

    # Save Unified Vocabulary
    unified_vocab_path = os.path.join(manifest_dir, "rsvqa_vocab_unified.json")
    with open(unified_vocab_path, "w", encoding="utf-8") as f:
        json.dump({"idx2ans": {str(k): v for k, v in idx2ans.items()}, "ans2idx": ans2idx}, f, indent=2)
    print(f"[+] Saved Unified Vocabulary to: {unified_vocab_path}")

    # Assign target_idx to all scene samples (filter out any below frequency threshold)
    filtered_scenes = {}
    for img_path, qa_list in scenes.items():
        valid_qa = []
        for item in qa_list:
            if item["answer"] in ans2idx:
                item["target_idx"] = ans2idx[item["answer"]]
                valid_qa.append(item)
        if valid_qa:
            filtered_scenes[img_path] = valid_qa

    # 4. Disjoint Scene Splitting: 70% Train, 15% Val, 15% Test
    scene_keys = list(filtered_scenes.keys())
    random.shuffle(scene_keys)
    n_total = len(scene_keys)
    n_train = int(n_total * 0.70)
    n_val = int(n_total * 0.15)

    train_scenes = scene_keys[:n_train]
    val_scenes = scene_keys[n_train:n_train + n_val]
    test_scenes = scene_keys[n_train + n_val:]

    rsvl_train_samples = [qa for s in train_scenes for qa in filtered_scenes[s]]
    rsvl_val_samples = [qa for s in val_scenes for qa in filtered_scenes[s]]
    rsvl_test_samples = [qa for s in test_scenes for qa in filtered_scenes[s]]

    print(f"\n[RSVL-VQA Split]")
    print(f"  Train: {len(train_scenes):,} scenes -> {len(rsvl_train_samples):,} QA samples")
    print(f"  Val:   {len(val_scenes):,} scenes -> {len(rsvl_val_samples):,} QA samples")
    print(f"  Test:  {len(test_scenes):,} scenes -> {len(rsvl_test_samples):,} QA samples")

    # Save RSVL standalone manifests
    for name, samples in [("rsvl_train.jsonl", rsvl_train_samples), ("rsvl_val.jsonl", rsvl_val_samples), ("rsvl_test.jsonl", rsvl_test_samples)]:
        out_p = os.path.join(manifest_dir, name)
        with open(out_p, "w", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s) + "\n")
        print(f"[+] Saved {name}: {len(samples):,} samples")

    # 5. Blend with EarthVQA for Master Unified Dataset
    earth_train_p = os.path.join(manifest_dir, "vqa_train.jsonl")
    earth_val_p = os.path.join(manifest_dir, "vqa_val.jsonl")
    earth_test_p = os.path.join(manifest_dir, "vqa_test.jsonl")

    earth_train = []
    if os.path.exists(earth_train_p):
        with open(earth_train_p, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    item = json.loads(l)
                    item["source"] = "EarthVQA"
                    earth_train.append(item)

    earth_val = []
    if os.path.exists(earth_val_p):
        with open(earth_val_p, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    item = json.loads(l)
                    item["source"] = "EarthVQA"
                    earth_val.append(item)

    earth_test = []
    if os.path.exists(earth_test_p):
        with open(earth_test_p, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    item = json.loads(l)
                    item["source"] = "EarthVQA"
                    earth_test.append(item)

    unified_train = earth_train + rsvl_train_samples
    unified_val = earth_val + rsvl_val_samples
    unified_test = earth_test + rsvl_test_samples

    random.shuffle(unified_train)

    for name, samples in [
        ("vqa_unified_train.jsonl", unified_train),
        ("vqa_unified_val.jsonl", unified_val),
        ("vqa_unified_test.jsonl", unified_test)
    ]:
        out_p = os.path.join(manifest_dir, name)
        with open(out_p, "w", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s) + "\n")
        print(f"[+] Saved Master Manifest {name}: {len(samples):,} samples")

    print("\n============================================================")
    print("UNIFIED DATASET READY FOR 200-EPOCH RETRAINING")
    print(f"Master Train Samples: {len(unified_train):,} ({len(earth_train):,} EarthVQA + {len(rsvl_train_samples):,} RSVL)")
    print(f"Master Val Samples:   {len(unified_val):,} ({len(earth_val):,} EarthVQA + {len(rsvl_val_samples):,} RSVL)")
    print(f"Master Test Samples:  {len(unified_test):,} ({len(earth_test):,} EarthVQA + {len(rsvl_test_samples):,} RSVL)")
    print(f"Target Vocabulary:    {len(ans2idx)} Classes")
    print("============================================================\n")

if __name__ == "__main__":
    main()
