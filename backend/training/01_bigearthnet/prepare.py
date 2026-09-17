"""
TRINETRA / SatQuery AI — BigEarthNet-S2 Dataset Preparation
Verifies real BigEarthNet-S2 imagery and metadata, builds deterministic manifests without data leakage.
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd

# Add training parent directory to path
training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.dataset_utils import (
    verify_real_dataset,
    verify_split_leakage,
    save_manifest,
    RealDatasetVerificationError
)
from common.seed import set_seed

DATASET_NAME = "BigEarthNet-S2 v2.0 (Sentinel-2 Multispectral)"
OFFICIAL_URL = "https://zenodo.org/records/10891137 (or https://bigearth.net/)"

CORINE_19_CLASSES = [
    "Agro-forestry areas", "Arable land", "Beaches, dunes, sands", "Broad-leaved forest",
    "Coastal wetlands", "Complex cultivation patterns", "Coniferous forest",
    "Industrial or commercial units", "Inland waters", "Inland wetlands",
    "Land principally occupied by agriculture, with significant areas of natural vegetation",
    "Marine waters", "Mixed forest", "Moors, heathland and sclerophyllous vegetation",
    "Natural grassland and sparsely vegetated areas", "Pastures", "Permanent crops",
    "Transitional woodland, shrub", "Urban fabric"
]

def prepare_bigearthnet(data_dir: str, metadata_path: str, manifest_dir: str, verify_only: bool = False):
    set_seed(42)
    print("=================================================================")
    print(f"TRINETRA — Preparing {DATASET_NAME}")
    print("=================================================================")

    # 1. Enforce Real-Data Requirement
    data_path = Path(data_dir)
    if not data_path.exists():
        verify_real_dataset(data_dir, [], DATASET_NAME, OFFICIAL_URL)

    meta_path = Path(metadata_path)
    if not meta_path.exists():
        raise FileNotFoundError(
            f"\nERROR: Metadata file not found at: {meta_path.resolve()}\n"
            f"Please download 'metadata.parquet' from official Zenodo repository:\n"
            f"  -> {OFFICIAL_URL}\n"
            f"And specify --metadata <path_to_metadata.parquet>\n"
        )

    print(f"[+] Loading genuine metadata from: {meta_path}")
    if str(meta_path).endswith(".parquet"):
        df = pd.read_parquet(meta_path)
    elif str(meta_path).endswith(".csv"):
        df = pd.read_csv(meta_path)
    else:
        raise ValueError("Unsupported metadata format. Please supply .parquet or .csv")

    id_col = "patch_id" if "patch_id" in df.columns else ("patch_name" if "patch_name" in df.columns else df.columns[0])
    print(f"[+] Total benchmark patches registered in metadata: {len(df):,}")

    # Check for physically downloaded patches in data_dir (allows real laptop subsets without 120GB extraction)
    available_patches = set(p.name for p in data_path.iterdir() if p.is_dir() or p.suffix == ".tif")
    if available_patches:
        total_on_disk = len(available_patches)
        print(f"[+] Found {total_on_disk:,} physical image patch directories/files in {data_path}")
        if total_on_disk < len(df):
            print(f"[!] Laptop Subset Mode: Filtering metadata to {total_on_disk:,} physically available patches.")
            stemmed_set = {p.replace(".tif", "") for p in available_patches}
            df = df[df[id_col].astype(str).isin(stemmed_set)].reset_index(drop=True)
            print(f"[+] Verified matched patches on disk: {len(df):,}")
            if len(df) == 0:
                raise RealDatasetVerificationError(
                    f"None of the {total_on_disk} folders in {data_path} matched patch names in {metadata_path}.\n"
                    f"Please ensure folder names match the BigEarthNet patch naming format (e.g. S2A_MSIL2A_...)."
                )

    if verify_only:
        print("[SUCCESS] Dataset and metadata verified. Ready for training.")
        return

    # 2. Extract official splits if available or create stratified deterministic splits
    if "split" in df.columns:
        train_df = df[df["split"] == "train"]
        val_df = df[df["split"] == "validation"]
        test_df = df[df["split"] == "test"]
    else:
        # Deterministic 70/15/15 partition
        df_shuffled = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
        n = len(df_shuffled)
        n_train = int(0.70 * n)
        n_val = int(0.15 * n)
        train_df = df_shuffled.iloc[:n_train]
        val_df = df_shuffled.iloc[n_train:n_train + n_val]
        test_df = df_shuffled.iloc[n_train + n_val:]

    train_ids = train_df[id_col].astype(str).tolist()
    val_ids = val_df[id_col].astype(str).tolist()
    test_ids = test_df[id_col].astype(str).tolist()

    # 3. Strictly Verify Zero Split Leakage (Rule 2 & 38)
    verify_split_leakage(train_ids, val_ids, test_ids)

    # 4. Save Verified Manifests
    out_dir = manifest_dir or os.path.join(os.path.dirname(__file__), "manifests")
    save_manifest(out_dir, "bigearthnet_train", train_ids)
    save_manifest(out_dir, "bigearthnet_val", val_ids)
    save_manifest(out_dir, "bigearthnet_test", test_ids)

    print(f"\n[SUMMARY]")
    print(f"  Training patches:   {len(train_ids):,}")
    print(f"  Validation patches: {len(val_ids):,}")
    print(f"  Test patches:       {len(test_ids):,}")
    print("=================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare BigEarthNet-S2 dataset manifests.")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing real BigEarthNet-S2 image patches.")
    parser.add_argument("--metadata", type=str, required=True, help="Path to metadata.parquet or metadata.csv.")
    parser.add_argument("--manifest_dir", type=str, default=None, help="Output directory for manifests.")
    parser.add_argument("--verify_only", action="store_true", help="Perform verification without rewriting manifests.")
    args = parser.parse_args()

    prepare_bigearthnet(args.data_dir, args.metadata, args.manifest_dir, args.verify_only)
