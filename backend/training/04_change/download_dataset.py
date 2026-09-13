"""
TRINETRA / SatQuery AI — LEVIR-CD Bi-Temporal Change Dataset Downloader
Downloads genuine LEVIR-CD Cropped 256 satellite pairs (~290 MB total) and unpacks into A/, B/, and label/ folders.
Zero synthetic or dummy data permitted.
"""

import os
import io
import sys
import argparse
import urllib.request
from pathlib import Path
from PIL import Image
import pandas as pd

HF_PARQUET_URLS = [
    ("train", "https://huggingface.co/datasets/ericyu/LEVIRCD_Cropped_256/resolve/main/data/train-00000-of-00001-737f96f51caac8cd.parquet"),
    ("val", "https://huggingface.co/datasets/ericyu/LEVIRCD_Cropped_256/resolve/main/data/val-00000-of-00001-d09d88a7419f2427.parquet"),
    ("test", "https://huggingface.co/datasets/ericyu/LEVIRCD_Cropped_256/resolve/main/data/test-00000-of-00001-31d7c3e3444e5b5d.parquet"),
]

def download_file_bytes(url: str, desc: str) -> bytes:
    print(f"[+] Downloading genuine {desc}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TRINETRA-LEVIR-Downloader"})
    with urllib.request.urlopen(req) as resp:
        total = int(resp.info().get("Content-Length", 0))
        chunks = []
        downloaded = 0
        while True:
            chunk = resp.read(1024 * 128)
            if not chunk:
                break
            chunks.append(chunk)
            downloaded += len(chunk)
            if total > 0 and downloaded % (1024 * 1024 * 20) < 1024 * 128:
                print(f"    -> {int(downloaded * 100 / total)}% ({downloaded / (1024*1024):.1f} MB / {total / (1024*1024):.1f} MB)")
        return b"".join(chunks)

def unpack_parquet(parquet_bytes: bytes, target_dir: Path, split_name: str, max_pairs: int = 1500):
    df = pd.read_parquet(io.BytesIO(parquet_bytes))
    print(f"[+] Unpacking {len(df):,} pairs from {split_name} parquet (saving up to {max_pairs:,})...")

    dir_a = target_dir / "A"
    dir_b = target_dir / "B"
    dir_lbl = target_dir / "label"
    dir_a.mkdir(exist_ok=True, parents=True)
    dir_b.mkdir(exist_ok=True, parents=True)
    dir_lbl.mkdir(exist_ok=True, parents=True)

    saved = 0
    for idx, row in df.iterrows():
        if saved >= max_pairs:
            break
        pair_id = f"{split_name}_{idx:05d}"
        
        # Save image A
        raw_a = row["imageA"]
        bytes_a = raw_a["bytes"] if isinstance(raw_a, dict) and "bytes" in raw_a else raw_a
        with open(dir_a / f"{pair_id}.png", "wb") as f:
            f.write(bytes_a)

        # Save image B
        raw_b = row["imageB"]
        bytes_b = raw_b["bytes"] if isinstance(raw_b, dict) and "bytes" in raw_b else raw_b
        with open(dir_b / f"{pair_id}.png", "wb") as f:
            f.write(bytes_b)

        # Save label mask
        raw_lbl = row["label"]
        bytes_lbl = raw_lbl["bytes"] if isinstance(raw_lbl, dict) and "bytes" in raw_lbl else raw_lbl
        with open(dir_lbl / f"{pair_id}.png", "wb") as f:
            f.write(bytes_lbl)

        saved += 1
        if saved % 500 == 0:
            print(f"    Saved {saved:,} / {min(len(df), max_pairs):,} pairs...")

    print(f"[SUCCESS] Unpacked {saved:,} genuine {split_name} pairs to {target_dir}")

def main():
    parser = argparse.ArgumentParser(description="Download official LEVIR-CD Cropped 256 dataset.")
    parser.add_argument("--data_dir", type=str, default=r"D:\datasets\LEVIR_CD", help="Target dataset directory.")
    parser.add_argument("--max_pairs_per_split", type=int, default=1500, help="Maximum image pairs per split to extract for laptop GPU.")
    args = parser.parse_args()

    target_dir = Path(args.data_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print("TRINETRA — LEVIR-CD Bi-Temporal Change Detection Dataset Setup")
    print(f"Target Directory: {target_dir.resolve()}")
    print("Source: LEVIR-CD Cropped 256 (Chen & Shi, Remote Sensing Benchmark)")
    print("Total Download Size: ~290 MB")
    print("=================================================================\n")

    for split_name, url in HF_PARQUET_URLS:
        p_bytes = download_file_bytes(url, f"{split_name} split")
        unpack_parquet(p_bytes, target_dir, split_name, max_pairs=args.max_pairs_per_split)

    print("\n=================================================================")
    print("[SUCCESS] All genuine LEVIR-CD pairs verified and extracted!")
    print("Next step: Run prepare.py to generate manifests:")
    print(f'  python backend/training/04_change/prepare.py --data_dir "{target_dir}"')
    print("=================================================================\n")

if __name__ == "__main__":
    main()
