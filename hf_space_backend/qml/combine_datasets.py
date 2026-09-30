"""
SatQuery AI / TRINETRA — Massive Multi-Dataset Aggregator
Combines multiple real satellite change datasets (LEVIR-CD, OSCD Dense, Ultra-Dense Sentinel-2)
into a unified Master Benchmark dataset (50,000+ to 100,000+ genuine satellite pairs).
Uses NTFS hardlinks for instant, zero-extra-disk-space merging whenever possible.
Strict Zero-Synthetic-Data Compliance.
"""

import os
import sys
import glob
import shutil
import argparse
from typing import List

def link_or_copy(src: str, dst: str):
    """Creates a hardlink for instant zero-disk duplication, falling back to copy."""
    if os.path.exists(dst):
        return
    try:
        os.link(src, dst)
    except Exception:
        shutil.copy2(src, dst)

def combine_datasets(sources: List[str], dest_dir: str):
    print("=" * 70)
    print(" TRINETRA: MASTER SATELLITE DATASET AGGREGATION")
    print(f" Target Master Dir : {dest_dir}")
    print(f" Source Repositories: {len(sources)}")
    for s in sources:
        print(f"   -> {s} ({'FOUND' if os.path.exists(s) else 'NOT FOUND'})")
    print("=" * 70)

    grand_total = 0
    splits = ["train", "val", "test"]

    for split in splits:
        dst_a = os.path.join(dest_dir, split, "A")
        dst_b = os.path.join(dest_dir, split, "B")
        dst_lbl = os.path.join(dest_dir, split, "label")

        os.makedirs(dst_a, exist_ok=True)
        os.makedirs(dst_b, exist_ok=True)
        os.makedirs(dst_lbl, exist_ok=True)

        split_count = 0

        for src_idx, src in enumerate(sources, 1):
            if not os.path.exists(src):
                continue

            src_name = os.path.basename(os.path.normpath(src))
            s_a = os.path.join(src, split, "A")
            s_b = os.path.join(src, split, "B")
            s_lbl = os.path.join(src, split, "label")

            if not os.path.exists(s_a):
                continue

            files_a = sorted(glob.glob(os.path.join(s_a, "*.png")) + glob.glob(os.path.join(s_a, "*.tif*")))
            sub_count = 0

            for f_a in files_a:
                fname = os.path.basename(f_a)
                f_b = os.path.join(s_b, fname)
                if not os.path.exists(f_b):
                    continue

                f_lbl = os.path.join(s_lbl, fname)

                # Prefix with source index and name to guarantee zero filename collisions
                new_name = f"src{src_idx:02d}_{src_name}_{fname}"
                target_a = os.path.join(dst_a, new_name)
                target_b = os.path.join(dst_b, new_name)
                target_lbl = os.path.join(dst_lbl, new_name)

                link_or_copy(f_a, target_a)
                link_or_copy(f_b, target_b)
                if os.path.exists(f_lbl):
                    link_or_copy(f_lbl, target_lbl)

                sub_count += 1

            split_count += sub_count
            print(f"  [{split.upper()}] Merged {sub_count} pairs from {src_name}")

        print(f"[{split.upper()} TOTAL] {split_count} genuine satellite change pairs.\n")
        grand_total += split_count

    print("=" * 70)
    print(f" [SUCCESS] Master Dataset Aggregation Complete! Total: {grand_total} genuine pairs.")
    print(f" Location: {dest_dir}")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine Remote Sensing Datasets")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=[
            r"D:\datasets\LEVIR_CD_patches",
            r"D:\datasets\OSCD_dense",
            r"D:\datasets\OSCD_ultra"
        ],
        help="List of source dataset folders"
    )
    parser.add_argument(
        "--dest",
        default=r"D:\datasets\SATELLITE_MASTER_50K",
        help="Destination directory for merged dataset"
    )
    args = parser.parse_args()

    combine_datasets(args.sources, args.dest)
