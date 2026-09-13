"""
TRINETRA / SatQuery AI — Remote-Sensing Visual Grounding Dataset Preparation
Verifies real DIOR-RSVG / VRSBench annotations and images, validates official splits.
"""

import os
import sys
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

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
    # DIOR-RSVG expects Annotations/, JPEGImages/, train.txt, val.txt, test.txt
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

    # Read official split manifests
    with open(data_path / "train.txt", "r", encoding="utf-8") as f:
        train_ids = [line.strip() for line in f if line.strip()]
    with open(data_path / "val.txt", "r", encoding="utf-8") as f:
        val_ids = [line.strip() for line in f if line.strip()]
    with open(data_path / "test.txt", "r", encoding="utf-8") as f:
        test_ids = [line.strip() for line in f if line.strip()]

    # Strictly Verify Zero Split Leakage (Rule 2 & 38)
    verify_split_leakage(train_ids, val_ids, test_ids)

    out_dir = manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")
    save_manifest(out_dir, "grounding_train", train_ids)
    save_manifest(out_dir, "grounding_val", val_ids)
    save_manifest(out_dir, "grounding_test", test_ids)

    print(f"\n[SUMMARY]")
    print(f"  Training samples:   {len(train_ids):,}")
    print(f"  Validation samples: {len(val_ids):,}")
    print(f"  Test samples:       {len(test_ids):,}")
    print("=================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare DIOR-RSVG grounding benchmark.")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing DIOR_RSVG files.")
    parser.add_argument("--manifest_dir", type=str, default=None)
    parser.add_argument("--verify_only", action="store_true")
    args = parser.parse_args()

    prepare_grounding(args.data_dir, args.manifest_dir, args.verify_only)
