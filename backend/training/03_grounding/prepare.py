"""
TRINETRA / SatQuery AI — Remote-Sensing Visual Grounding Dataset Preparation
Parses genuine DIOR-RSVG annotations and images, maps official split IDs, and builds optimized manifests.
Zero synthetic or mock data permitted.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.dataset_utils import verify_real_dataset, verify_split_leakage, save_manifest
from common.seed import set_seed

DATASET_NAME = "DIOR-RSVG (Remote Sensing Visual Grounding Benchmark)"
OFFICIAL_URL = "https://github.com/ZhanYang-nwpu/RSVG-pytorch (IEEE TGRS 2023)"

def prepare_grounding(data_dir: str, manifest_dir: str, verify_only: bool = False):
    set_seed(42)
    print("=================================================================")
    print(f"TRINETRA — Preparing {DATASET_NAME}")
    print("=================================================================")

    data_path = Path(data_dir)
    required_files = ["Annotations", "JPEGImages", "train.txt", "val.txt", "test.txt"]
    if not data_path.exists():
        verify_real_dataset(data_dir, required_files, DATASET_NAME, OFFICIAL_URL)

    for req in required_files:
        if not (data_path / req).exists():
            verify_real_dataset(data_dir, required_files, DATASET_NAME, OFFICIAL_URL)

    print(f"[+] Verified genuine DIOR-RSVG structure at: {data_path.resolve()}")

    if verify_only:
        print("[SUCCESS] Grounding dataset verified. Ready for training.")
        return

    # 1. Read official split ID lists (indices 0 .. 38,319)
    with open(data_path / "train.txt", "r", encoding="utf-8") as f:
        train_ids = [int(line.strip()) for line in f if line.strip()]
    with open(data_path / "val.txt", "r", encoding="utf-8") as f:
        val_ids = [int(line.strip()) for line in f if line.strip()]
    with open(data_path / "test.txt", "r", encoding="utf-8") as f:
        test_ids = [int(line.strip()) for line in f if line.strip()]

    # Verify zero leakage
    verify_split_leakage([str(x) for x in train_ids], [str(x) for x in val_ids], [str(x) for x in test_ids])

    # 2. Parse all genuine XML annotations in deterministic sorted order
    annot_dir = data_path / "Annotations"
    xml_files = sorted(os.listdir(annot_dir))
    print(f"[+] Indexing {len(xml_files):,} genuine XML annotation files...")
    t0 = time.time()

    global_records = []
    for xml_file in xml_files:
        p = annot_dir / xml_file
        tree = ET.parse(p)
        root = tree.getroot()

        fn_elem = root.find("filename")
        img_fn = fn_elem.text if fn_elem is not None else xml_file.replace(".xml", ".jpg")
        if not img_fn.endswith(".jpg"):
            img_fn += ".jpg"

        sz = root.find("size")
        w = float(sz.find("width").text) if sz is not None else 800.0
        h = float(sz.find("height").text) if sz is not None else 800.0

        for obj in root.findall("object"):
            bb = obj.find("bndbox")
            if bb is None:
                continue
            xmin = float(bb.find("xmin").text)
            ymin = float(bb.find("ymin").text)
            xmax = float(bb.find("xmax").text)
            ymax = float(bb.find("ymax").text)

            # Normalized [ymin, xmin, ymax, xmax]
            ny1 = round(float(np.clip(ymin / h, 0.0, 1.0)), 4)
            nx1 = round(float(np.clip(xmin / w, 0.0, 1.0)), 4)
            ny2 = round(float(np.clip(ymax / h, 0.0, 1.0)), 4)
            nx2 = round(float(np.clip(xmax / w, 0.0, 1.0)), 4)

            desc = obj.find("description")
            query_text = desc.text.strip() if (desc is not None and desc.text) else obj.find("name").text.strip()

            global_records.append({
                "img": img_fn,
                "box": [ny1, nx1, ny2, nx2],
                "query": query_text
            })

    print(f"[+] Parsed {len(global_records):,} referring groundings in {time.time()-t0:.2f}s.")

    # 3. Save optimized manifests (.jsonl + .txt)
    out_dir = manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")
    os.makedirs(out_dir, exist_ok=True)

    splits = [
        ("grounding_train", train_ids),
        ("grounding_val", val_ids),
        ("grounding_test", test_ids)
    ]

    for split_name, id_list in splits:
        # Save raw IDs (.txt)
        txt_path = os.path.join(out_dir, f"{split_name}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            for idx in id_list:
                f.write(f"{idx}\n")

        # Save parsed samples (.jsonl)
        jsonl_path = os.path.join(out_dir, f"{split_name}.jsonl")
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for idx in id_list:
                if idx < len(global_records):
                    f.write(json.dumps(global_records[idx]) + "\n")

    print(f"\n[SUMMARY]")
    print(f"  Training samples:   {len(train_ids):,} -> {out_dir}/grounding_train.jsonl")
    print(f"  Validation samples: {len(val_ids):,} -> {out_dir}/grounding_val.jsonl")
    print(f"  Test samples:       {len(test_ids):,} -> {out_dir}/grounding_test.jsonl")
    print("=================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare DIOR-RSVG grounding benchmark.")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing DIOR_RSVG files.")
    parser.add_argument("--manifest_dir", type=str, default=None)
    parser.add_argument("--verify_only", action="store_true")
    args = parser.parse_args()

    prepare_grounding(args.data_dir, args.manifest_dir, args.verify_only)
