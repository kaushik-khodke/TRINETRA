"""
TRINETRA / SatQuery AI — DIOR-RSVG Dataset Downloader & Verifier
Assists in obtaining genuine DIOR-RSVG benchmark dataset (~1.5 GB total) from official NWPU iOPEN release.
Zero synthetic or mock data permitted.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

OFFICIAL_GDRIVE_URL = "https://drive.google.com/drive/folders/1hTqtYsC6B-m4ED2ewx5oKuYZV13EoJp_?usp=sharing"
OFFICIAL_GITHUB_URL = "https://github.com/ZhanYang-nwpu/RSVG-pytorch"

REQUIRED_ELEMENTS = ["Annotations", "JPEGImages", "train.txt", "val.txt", "test.txt"]

def verify_dataset(data_dir: Path) -> bool:
    import zipfile
    for zip_name in ["Annotations.zip", "JPEGImages.zip"]:
        zip_path = data_dir / zip_name
        target_sub = data_dir / zip_name.replace(".zip", "")
        if zip_path.exists() and not target_sub.exists():
            print(f"[+] Found archive '{zip_name}' ({zip_path.stat().st_size / (1024*1024):.1f} MB). Extracting into {data_dir}...")
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(data_dir)
            print(f"[+] Successfully extracted {zip_name} -> {target_sub}")

    missing = [req for req in REQUIRED_ELEMENTS if not (data_dir / req).exists()]
    if missing:
        print(f"[!] Dataset incomplete at: {data_dir}")
        print(f"    Missing required items: {missing}")
        return False
    print(f"[SUCCESS] Verified complete genuine DIOR-RSVG dataset at: {data_dir}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Download & verify official DIOR-RSVG visual grounding dataset.")
    parser.add_argument("--data_dir", type=str, default=r"D:\datasets\DIOR_RSVG", help="Target dataset directory.")
    parser.add_argument("--use_gdown", action="store_true", help="Attempt automatic download using gdown package.")
    args = parser.parse_args()

    target_dir = Path(args.data_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print("TRINETRA — DIOR-RSVG Visual Grounding Dataset Setup")
    print(f"Target Directory: {target_dir.resolve()}")
    print(f"Official Paper: IEEE TGRS 2023 (Zhan et al., NWPU iOPEN)")
    print(f"Official Repository: {OFFICIAL_GITHUB_URL}")
    print(f"Official Google Drive: {OFFICIAL_GDRIVE_URL}")
    print("=================================================================\n")

    if verify_dataset(target_dir):
        print("\nDataset is already complete and verified. Ready to run prepare.py:")
        print(f'  python backend/training/03_grounding/prepare.py --data_dir "{target_dir}"')
        return

    if args.use_gdown:
        try:
            import gdown
            print(f"[+] Downloading official DIOR-RSVG folder via gdown into {target_dir}...")
            gdown.download_folder(url=OFFICIAL_GDRIVE_URL, output=str(target_dir), quiet=False)
            verify_dataset(target_dir)
            return
        except ImportError:
            print("[!] 'gdown' package not installed. Run: pip install gdown")
        except Exception as e:
            print(f"[!] gdown download encountered: {e}")

    print("-----------------------------------------------------------------")
    print("MANUAL DOWNLOAD INSTRUCTIONS (Recommended):")
    print("1. Open the official Google Drive folder in your browser:")
    print(f"   {OFFICIAL_GDRIVE_URL}")
    print("2. Download:")
    print("   - Annotations.zip (15 MB) -> Extract to: D:\\datasets\\DIOR_RSVG\\Annotations\\")
    print("   - JPEGImages.zip (1.5 GB) -> Extract to: D:\\datasets\\DIOR_RSVG\\JPEGImages\\")
    print("   - train.txt, val.txt, test.txt -> Save to: D:\\datasets\\DIOR_RSVG\\")
    print("3. Verify by running:")
    print(f'   python backend/training/03_grounding/download_dataset.py --data_dir "{target_dir}"')
    print("-----------------------------------------------------------------\n")

if __name__ == "__main__":
    main()
