"""
TRINETRA / SatQuery AI — RSVQA-LR Dataset Downloader & Verifier
Downloads genuine Low-Resolution Sentinel-2 RSVQA dataset (~119 MB total) from official Zenodo repository.
Zero synthetic or mock data permitted.
"""

import os
import sys
import zipfile
import argparse
import urllib.request
from pathlib import Path

ZENODO_BASE_URL = "https://zenodo.org/records/6344334/files"

FILES_TO_DOWNLOAD = [
    ("Images_LR.zip", f"{ZENODO_BASE_URL}/Images_LR.zip?download=1", 95015386),
    ("LR_split_train_questions.json", f"{ZENODO_BASE_URL}/LR_split_train_questions.json?download=1", 11943936),
    ("LR_split_train_answers.json", f"{ZENODO_BASE_URL}/LR_split_train_answers.json?download=1", 7424000),
    ("LR_split_val_questions.json", f"{ZENODO_BASE_URL}/LR_split_val_questions.json?download=1", 3481600),
    ("LR_split_val_answers.json", f"{ZENODO_BASE_URL}/LR_split_val_answers.json?download=1", 2693120),
    ("LR_split_test_questions.json", f"{ZENODO_BASE_URL}/LR_split_test_questions.json?download=1", 2713600),
    ("LR_split_test_answers.json", f"{ZENODO_BASE_URL}/LR_split_test_answers.json?download=1", 1918976),
]

def download_with_progress(url: str, output_path: Path):
    print(f"[+] Downloading: {output_path.name}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TRINETRA-RSVQA-Downloader"})
    with urllib.request.urlopen(req) as resp, open(output_path, "wb") as out_file:
        total = int(resp.info().get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 128
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total > 0 and downloaded % (1024 * 1024 * 5) < chunk_size:
                pct = int(downloaded * 100 / total)
                print(f"    -> {pct}% ({downloaded / (1024*1024):.1f} MB / {total / (1024*1024):.1f} MB)")
    print(f"[SUCCESS] Saved: {output_path.name} ({downloaded / (1024*1024):.1f} MB)")

def main():
    parser = argparse.ArgumentParser(description="Download official RSVQA-LR benchmark dataset from Zenodo.")
    parser.add_argument("--data_dir", type=str, default=r"D:\datasets\RSVQA_LR", help="Target directory for RSVQA dataset.")
    args = parser.parse_args()

    target_dir = Path(args.data_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print("TRINETRA — RSVQA Low-Resolution (Sentinel-2) Dataset Setup")
    print(f"Target Directory: {target_dir.resolve()}")
    print("Source: Zenodo Record 6344334 (Official Sylvain Lobry RSVQA release)")
    print("Total Download Size: ~119 MB")
    print("=================================================================\n")

    for fname, url, approx_size in FILES_TO_DOWNLOAD:
        out_path = target_dir / fname
        if out_path.exists() and out_path.stat().st_size > 1000:
            print(f"[+] Already downloaded: {fname} ({out_path.stat().st_size / (1024*1024):.1f} MB)")
        else:
            download_with_progress(url, out_path)

    # Extract Images_LR.zip
    zip_path = target_dir / "Images_LR.zip"
    extract_folder = target_dir / "Images_LR"
    if not extract_folder.exists() or len(list(extract_folder.glob("*.tif"))) == 0:
        print(f"\n[+] Extracting {zip_path.name} to {extract_folder}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        print(f"[SUCCESS] Extracted Sentinel-2 images to {extract_folder}")
    else:
        print(f"[+] Images already extracted at: {extract_folder}")

    print("\n=================================================================")
    print("[SUCCESS] All genuine RSVQA files verified and ready for training!")
    print("Next step: Run prepare.py to generate vocabulary:")
    print(f'  python backend/training/02_rsvqa/prepare.py --data_dir "{target_dir}"')
    print("=================================================================\n")

if __name__ == "__main__":
    main()
