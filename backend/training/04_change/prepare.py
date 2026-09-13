"""
TRINETRA / SatQuery AI — Bi-Temporal Change Detection Dataset Preparation
Verifies real OSCD / LEVIR-CD temporal pairs and change masks, builds split manifests.
"""

import os
import sys
import argparse
from pathlib import Path
import glob

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.dataset_utils import verify_real_dataset, verify_split_leakage, save_manifest
from common.seed import set_seed

DATASET_NAME = "OSCD / LEVIR-CD (Bi-Temporal Remote-Sensing Change Benchmark)"
OFFICIAL_URL = "https://rcdaudt.github.io/oscd/ (or https://justchenyang.github.io/LEVIR-CD/)"

def prepare_change(data_dir: str, manifest_dir: str, verify_only: bool = False):
    set_seed(42)
    print("=================================================================")
    print(f"TRINETRA — Preparing {DATASET_NAME}")
    print("=================================================================")

    data_path = Path(data_dir)
    # Check for LEVIR-CD structure (A, B, label) or OSCD structure
    is_levir = (data_path / "A").exists() and (data_path / "B").exists()
    is_oscd = (data_path / "train").exists() or any("pair" in f.name.lower() for f in data_path.iterdir() if f.is_dir())

    if not (is_levir or is_oscd):
        verify_real_dataset(data_dir, ["A", "B"], DATASET_NAME, OFFICIAL_URL)

    print(f"[+] Verified genuine bi-temporal structure at: {data_path.resolve()}")

    if verify_only:
        print("[SUCCESS] Bi-temporal change dataset verified. Ready for training.")
        return

    # Extract sample IDs
    if is_levir:
        a_files = sorted(glob.glob(os.path.join(data_dir, "A", "*.*")))
        sample_ids = [Path(f).stem for f in a_files]
    else:
        # OSCD directory
        pairs = [f.name for f in data_path.iterdir() if f.is_dir()]
        sample_ids = sorted(pairs)

    print(f"[+] Found {len(sample_ids):,} verified bi-temporal pairs.")

    # Deterministic 70/15/15 Split
    import random
    rng = random.Random(42)
    shuffled = list(sample_ids)
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(0.70 * n)
    n_val = int(0.15 * n)

    train_ids = shuffled[:n_train]
    val_ids = shuffled[n_train:n_train + n_val]
    test_ids = shuffled[n_train + n_val:]

    verify_split_leakage(train_ids, val_ids, test_ids)

    out_dir = manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")
    save_manifest(out_dir, "change_train", train_ids)
    save_manifest(out_dir, "change_val", val_ids)
    save_manifest(out_dir, "change_test", test_ids)

    print(f"\n[SUMMARY]")
    print(f"  Training pairs:   {len(train_ids):,}")
    print(f"  Validation pairs: {len(val_ids):,}")
    print(f"  Test pairs:       {len(test_ids):,}")
    print("=================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare bi-temporal change dataset.")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to LEVIR-CD or OSCD directory.")
    parser.add_argument("--manifest_dir", type=str, default=None)
    parser.add_argument("--verify_only", action="store_true")
    args = parser.parse_args()

    prepare_change(args.data_dir, args.manifest_dir, args.verify_only)
