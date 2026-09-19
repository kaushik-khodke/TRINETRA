"""
TRINETRA — Hugging Face LEVIR-CD+ Downloader & Preprocessor
Downloads genuine bi-temporal remote-sensing change benchmark from blanchon/LEVIR_CDPlus.
Tiles 1024x1024 image pairs into 256x256 non-overlapping patches (15,760 total) to preserve
native 0.5m/pixel ground resolution. Prevents data leakage via strict parent-scene isolation.
Governed by Stage 4 Change Detection Protocol. Zero synthetic data.
"""

import os
import sys
import io
import argparse
import random
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from PIL import Image
from huggingface_hub import hf_hub_download
import pyarrow.parquet as pq

# Add backend and training roots
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from common.seed import set_seed
from common.dataset_utils import save_manifest, verify_split_leakage

REPO_ID = "blanchon/LEVIR_CDPlus"
PARQUET_FILES = {
    "train": [
        "data/train-00000-of-00005.parquet",
        "data/train-00001-of-00005.parquet",
        "data/train-00002-of-00005.parquet",
        "data/train-00003-of-00005.parquet",
        "data/train-00004-of-00005.parquet",
    ],
    "test": [
        "data/test-00000-of-00003.parquet",
        "data/test-00001-of-00003.parquet",
        "data/test-00002-of-00003.parquet",
    ]
}


def tile_and_save_scene(
    im1_bytes: bytes,
    im2_bytes: bytes,
    mask_bytes: bytes,
    scene_id: str,
    output_dir: Path,
    patch_size: int = 256
) -> List[Dict[str, any]]:
    """
    Tiles 1024x1024 T1, T2, and Mask into 4x4 non-overlapping 256x256 patches.
    Saves directly to A/, B/, and label/ subdirectories.
    Returns metadata list for all 16 generated patches.
    """
    dir_a = output_dir / "A"
    dir_b = output_dir / "B"
    dir_lbl = output_dir / "label"

    dir_a.mkdir(parents=True, exist_ok=True)
    dir_b.mkdir(parents=True, exist_ok=True)
    dir_lbl.mkdir(parents=True, exist_ok=True)

    im1 = Image.open(io.BytesIO(im1_bytes)).convert("RGB")
    im2 = Image.open(io.BytesIO(im2_bytes)).convert("RGB")
    mask = Image.open(io.BytesIO(mask_bytes)).convert("L")

    w, h = im1.size
    patch_info = []

    patch_idx = 0
    for y in range(0, h, patch_size):
        for x in range(0, w, patch_size):
            box = (x, y, x + patch_size, y + patch_size)
            p_im1 = im1.crop(box)
            p_im2 = im2.crop(box)
            p_mask = mask.crop(box)

            patch_id = f"{scene_id}_p{patch_idx:02d}"

            # Calculate change statistics (support both {0, 1} and {0, 255} masks)
            mask_arr = np.array(p_mask, dtype=np.uint8)
            changed_pixels = int(np.sum(mask_arr > 0))
            total_pixels = patch_size * patch_size
            change_ratio = changed_pixels / total_pixels

            # Calculate visual complexity / gradient for hard negative prioritization
            im1_arr = np.array(p_im1, dtype=np.float32)
            texture_variance = float(np.var(im1_arr))

            # Save cropped patches
            p_im1.save(dir_a / f"{patch_id}.png", format="PNG", optimize=True)
            p_im2.save(dir_b / f"{patch_id}.png", format="PNG", optimize=True)
            p_mask.save(dir_lbl / f"{patch_id}.png", format="PNG", optimize=True)

            patch_info.append({
                "patch_id": patch_id,
                "scene_id": scene_id,
                "has_change": changed_pixels > 0,
                "changed_pixels": changed_pixels,
                "change_ratio": change_ratio,
                "texture_variance": texture_variance
            })
            patch_idx += 1

    return patch_info


def process_parquet_shard(
    file_path: str,
    split_prefix: str,
    start_scene_idx: int,
    output_dir: Path,
    max_scenes: int = None
) -> Tuple[List[Dict[str, any]], int]:
    """Reads a Parquet shard and tiles all images within it."""
    table = pq.read_table(file_path)
    num_rows = table.num_rows

    all_patches = []
    current_scene_idx = start_scene_idx

    for row_idx in range(num_rows):
        if max_scenes and current_scene_idx >= max_scenes:
            break

        row = table.slice(row_idx, 1).to_pydict()
        im1_bytes = row["image1"][0]["bytes"]
        im2_bytes = row["image2"][0]["bytes"]
        mask_bytes = row["mask"][0]["bytes"]

        scene_id = f"{split_prefix}_{current_scene_idx:04d}"
        patches = tile_and_save_scene(im1_bytes, im2_bytes, mask_bytes, scene_id, output_dir)
        all_patches.extend(patches)
        current_scene_idx += 1

        if current_scene_idx % 25 == 0 or current_scene_idx == num_rows:
            print(f"  [+] Processed {current_scene_idx} parent scenes -> {len(all_patches):,} patches created.")

    return all_patches, current_scene_idx


def download_and_preprocess_levir_cdplus(
    output_dir: str,
    manifest_dir: str,
    max_scenes: int = None,
    seed: int = 42,
    negative_ratio: float = 1.2
):
    set_seed(seed)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print(f"TRINETRA — Ingesting Hugging Face LEVIR-CD+ ({REPO_ID})")
    print(f"Target Directory: {out_path.resolve()}")
    print("=================================================================\n")

    # 1. Download and process TRAIN shards
    print("[1/4] Ingesting TRAIN shards...")
    train_parent_scenes: Dict[str, List[Dict[str, any]]] = {}
    scene_counter = 0

    for shard in PARQUET_FILES["train"]:
        print(f"  -> Downloading/reading {shard}...")
        parquet_path = hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename=shard)
        patches, scene_counter = process_parquet_shard(
            parquet_path,
            split_prefix="train",
            start_scene_idx=scene_counter,
            output_dir=out_path,
            max_scenes=max_scenes
        )
        for p in patches:
            s_id = p["scene_id"]
            if s_id not in train_parent_scenes:
                train_parent_scenes[s_id] = []
            train_parent_scenes[s_id].append(p)

        if max_scenes and scene_counter >= max_scenes:
            break

    total_train_scenes = len(train_parent_scenes)
    print(f"\n[+] Total Train Parent Scenes Processed: {total_train_scenes}")

    # 2. Download and process TEST shards
    print("\n[2/4] Ingesting TEST shards...")
    test_parent_scenes: Dict[str, List[Dict[str, any]]] = {}
    test_scene_counter = 0

    for shard in PARQUET_FILES["test"]:
        if max_scenes and test_scene_counter >= (max_scenes // 2):
            break
        print(f"  -> Downloading/reading {shard}...")
        parquet_path = hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename=shard)
        patches, test_scene_counter = process_parquet_shard(
            parquet_path,
            split_prefix="test",
            start_scene_idx=test_scene_counter,
            output_dir=out_path,
            max_scenes=max_scenes // 2 if max_scenes else None
        )
        for p in patches:
            s_id = p["scene_id"]
            if s_id not in test_parent_scenes:
                test_parent_scenes[s_id] = []
            test_parent_scenes[s_id].append(p)

    total_test_scenes = len(test_parent_scenes)
    print(f"\n[+] Total Test Parent Scenes Processed: {total_test_scenes}")

    # 3. Partition Parent Scenes with Strict Spatial Isolation
    print("\n[3/4] Partitioning Parent Scenes (Zero Data Leakage)...")
    train_scene_keys = sorted(list(train_parent_scenes.keys()))
    rng = random.Random(seed)
    rng.shuffle(train_scene_keys)

    # Dedicate 15% of train scenes to validation (or min 50 scenes)
    n_val_scenes = max(10, int(0.15 * len(train_scene_keys)))
    val_keys = train_scene_keys[:n_val_scenes]
    actual_train_keys = train_scene_keys[n_val_scenes:]
    test_keys = sorted(list(test_parent_scenes.keys()))

    print(f"  Train Scenes: {len(actual_train_keys)}")
    print(f"  Val Scenes:   {len(val_keys)}")
    print(f"  Test Scenes:  {len(test_keys)}")

    # 4. Construct Balanced Training Patches & Full Val/Test Patches
    # For training: Keep 100% of change patches; sample hard negatives to avoid class collapse
    train_patch_ids = []
    change_patches = []
    no_change_patches = []

    for sk in actual_train_keys:
        for p in train_parent_scenes[sk]:
            if p["has_change"]:
                change_patches.append(p["patch_id"])
            else:
                no_change_patches.append((p["patch_id"], p["texture_variance"]))

    # Sort no-change patches by texture variance (prioritize non-trivial scenes over flat background)
    no_change_patches.sort(key=lambda x: x[1], reverse=True)
    n_negatives = min(len(no_change_patches), int(len(change_patches) * negative_ratio))
    selected_negatives = [pid for pid, _ in no_change_patches[:n_negatives]]

    train_patch_ids = sorted(change_patches + selected_negatives)

    # For validation and testing: Keep ALL patches so evaluation reflects real geospatial coverage
    val_patch_ids = []
    for sk in val_keys:
        for p in train_parent_scenes[sk]:
            val_patch_ids.append(p["patch_id"])
    val_patch_ids = sorted(val_patch_ids)

    test_patch_ids = []
    for sk in test_keys:
        for p in test_parent_scenes[sk]:
            test_patch_ids.append(p["patch_id"])
    test_patch_ids = sorted(test_patch_ids)

    # Verify split leakage
    verify_split_leakage(train_patch_ids, val_patch_ids, test_patch_ids)

    # Save manifests
    manifest_path = Path(manifest_dir) if manifest_dir else Path(__file__).parent / "manifests"
    manifest_path.mkdir(parents=True, exist_ok=True)

    save_manifest(str(manifest_path), "change_train", train_patch_ids)
    save_manifest(str(manifest_path), "change_val", val_patch_ids)
    save_manifest(str(manifest_path), "change_test", test_patch_ids)

    # Also save inside dataset folder for portability
    ds_manifest_path = out_path / "manifests"
    ds_manifest_path.mkdir(parents=True, exist_ok=True)
    save_manifest(str(ds_manifest_path), "change_train", train_patch_ids)
    save_manifest(str(ds_manifest_path), "change_val", val_patch_ids)
    save_manifest(str(ds_manifest_path), "change_test", test_patch_ids)

    print("\n=================================================================")
    print("[SUCCESS] LEVIR-CD+ INGESTION & PREPROCESSING COMPLETE")
    print("=================================================================")
    print(f"Total 256x256 Patches in Dataset: {len(train_patch_ids) + len(val_patch_ids) + len(test_patch_ids):,}")
    print(f"  -> Curated Training Patches:    {len(train_patch_ids):,} ({len(change_patches):,} change + {len(selected_negatives):,} balanced no-change)")
    print(f"  -> Held-Out Validation Patches: {len(val_patch_ids):,}")
    print(f"  -> Strictly Held-Out Test:      {len(test_patch_ids):,}")
    print(f"Manifests Saved To:               {manifest_path.resolve()}")
    print("=================================================================\n")


def build_manifests_from_disk(
    output_dir: str,
    manifest_dir: str = None,
    seed: int = 42,
    negative_ratio: float = 1.2
):
    """
    Rapidly builds leak-free manifests directly from already extracted 256x256 tiles on disk.
    Identifies change patches, curates balanced negatives, and enforces parent-scene isolation.
    """
    set_seed(seed)
    out_path = Path(output_dir)
    lbl_dir = out_path / "label"
    if not lbl_dir.is_dir():
        raise FileNotFoundError(f"Label directory not found: {lbl_dir}")

    print("=================================================================")
    print("TRINETRA — Generating Split Manifests from Extracted Tiles")
    print(f"Dataset Root: {out_path.resolve()}")
    print("=================================================================")

    # Group patch filenames by parent scene
    train_parent_scenes: Dict[str, List[str]] = {}
    test_parent_scenes: Dict[str, List[str]] = {}

    all_labels = os.listdir(lbl_dir)
    for fname in all_labels:
        if not fname.endswith(".png"):
            continue
        pid = os.path.splitext(fname)[0]
        # Scene id: train_XXXX or test_XXXX
        parts = pid.split("_")
        if len(parts) >= 3:
            scene_id = f"{parts[0]}_{parts[1]}"
            if parts[0] == "train":
                train_parent_scenes.setdefault(scene_id, []).append(pid)
            elif parts[0] == "test":
                test_parent_scenes.setdefault(scene_id, []).append(pid)

    train_scene_keys = sorted(list(train_parent_scenes.keys()))
    test_scene_keys = sorted(list(test_parent_scenes.keys()))
    print(f"[+] Found {len(train_scene_keys)} Train parent scenes, {len(test_scene_keys)} Test parent scenes.")

    # Strict spatial isolation: partition parent scenes
    rng = random.Random(seed)
    rng.shuffle(train_scene_keys)

    n_val_scenes = max(10, int(0.15 * len(train_scene_keys)))
    val_keys = train_scene_keys[:n_val_scenes]
    actual_train_keys = train_scene_keys[n_val_scenes:]

    print(f"  -> Train Scenes: {len(actual_train_keys)}")
    print(f"  -> Val Scenes:   {len(val_keys)}")
    print(f"  -> Test Scenes:  {len(test_scene_keys)}")

    # Class balancing on train scenes
    print("  -> Scanning ground-truth change masks for training split...")
    change_patches = []
    no_change_patches = []

    for sk in actual_train_keys:
        for pid in train_parent_scenes[sk]:
            mask_path = lbl_dir / f"{pid}.png"
            mask_img = Image.open(mask_path).convert("L")
            mask_arr = np.array(mask_img, dtype=np.uint8)
            changed_pixels = int(np.sum(mask_arr > 0))

            if changed_pixels > 0:
                change_patches.append(pid)
            else:
                no_change_patches.append(pid)

    # Balance negatives
    rng.shuffle(no_change_patches)
    n_negatives = min(len(no_change_patches), int(len(change_patches) * negative_ratio))
    selected_negatives = no_change_patches[:n_negatives]
    train_patch_ids = sorted(change_patches + selected_negatives)

    # Full validation and test splits (for unbiased evaluation)
    val_patch_ids = []
    for sk in val_keys:
        val_patch_ids.extend(train_parent_scenes[sk])
    val_patch_ids = sorted(val_patch_ids)

    test_patch_ids = []
    for sk in test_scene_keys:
        test_patch_ids.extend(test_parent_scenes[sk])
    test_patch_ids = sorted(test_patch_ids)

    # Leakage check
    verify_split_leakage(train_patch_ids, val_patch_ids, test_patch_ids)

    # Save manifests
    manifest_path = Path(manifest_dir) if manifest_dir else Path(__file__).parent / "manifests"
    manifest_path.mkdir(parents=True, exist_ok=True)
    save_manifest(str(manifest_path), "change_train", train_patch_ids)
    save_manifest(str(manifest_path), "change_val", val_patch_ids)
    save_manifest(str(manifest_path), "change_test", test_patch_ids)

    ds_manifest_path = out_path / "manifests"
    ds_manifest_path.mkdir(parents=True, exist_ok=True)
    save_manifest(str(ds_manifest_path), "change_train", train_patch_ids)
    save_manifest(str(ds_manifest_path), "change_val", val_patch_ids)
    save_manifest(str(ds_manifest_path), "change_test", test_patch_ids)

    print("\n=================================================================")
    print("[SUCCESS] SPLIT MANIFESTS GENERATED SUCCESSFULLY")
    print("=================================================================")
    print(f"Total Tiles in Dataset:           {len(all_labels):,}")
    print(f"  -> Curated Training Tiles:      {len(train_patch_ids):,} ({len(change_patches):,} change + {len(selected_negatives):,} balanced no-change)")
    print(f"  -> Held-Out Validation Tiles:   {len(val_patch_ids):,}")
    print(f"  -> Strictly Held-Out Test:      {len(test_patch_ids):,}")
    print(f"Manifests Saved To:               {manifest_path.resolve()}")
    print("=================================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and tile blanchon/LEVIR_CDPlus from Hugging Face.")
    parser.add_argument("--output_dir", type=str, default=r"C:\Users\student\Downloads\datasets\LEVIR_CDPlus",
                        help="Path to directory where tiled patches (A, B, label) will be saved.")
    parser.add_argument("--manifest_dir", type=str, default=None,
                        help="Directory to save train/val/test manifests (default: backend/training/04_change/manifests).")
    parser.add_argument("--max_scenes", type=int, default=None,
                        help="Optional cap on number of parent scenes to process (for rapid testing).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--negative_ratio", type=float, default=1.2,
                        help="Ratio of no-change to change patches in training manifest.")
    parser.add_argument("--manifests_only", action="store_true",
                        help="Build manifests directly from existing tiles on disk without re-downloading.")
    args = parser.parse_args()

    # If all tiles already exist or manifests_only requested, generate manifests directly from disk
    tiles_exist = (Path(args.output_dir) / "A").is_dir() and len(os.listdir(Path(args.output_dir) / "A")) >= 15000
    if args.manifests_only or tiles_exist:
        print("[INFO] Extracted tiles already present on disk. Generating manifests from disk...")
        build_manifests_from_disk(
            output_dir=args.output_dir,
            manifest_dir=args.manifest_dir,
            seed=args.seed,
            negative_ratio=args.negative_ratio
        )
    else:
        download_and_preprocess_levir_cdplus(
            output_dir=args.output_dir,
            manifest_dir=args.manifest_dir,
            max_scenes=args.max_scenes,
            seed=args.seed,
            negative_ratio=args.negative_ratio
        )
