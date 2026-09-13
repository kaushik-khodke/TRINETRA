"""
TRINETRA / SatQuery AI — BigEarthNet-S2 Download & Extraction Helper
Assists in downloading genuine metadata.parquet and extracting real patch subsets from official Zenodo archives.
Zero synthetic or mock data permitted.
"""

import os
import sys
import argparse
import hashlib
import urllib.request
from pathlib import Path

ZENODO_METADATA_URL = "https://zenodo.org/records/10891137/files/metadata.parquet?download=1"
ZENODO_METADATA_MD5 = "55687065e77b6d0b0f1ff604a6e7b49c"
ZENODO_ARCHIVE_URL = "https://zenodo.org/records/10891137/files/BigEarthNet-S2.tar.zst?download=1"

def check_md5(filepath: Path, expected_md5: str) -> bool:
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192 * 16), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected_md5.lower()

def download_file_with_progress(url: str, output_path: Path):
    print(f"[+] Connecting to official source: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TRINETRA-Dataset-Downloader"})
    
    with urllib.request.urlopen(req) as resp, open(output_path, "wb") as out_file:
        total_size = int(resp.info().get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 64
        last_pct = -1

        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                pct = int(downloaded * 100 / total_size)
                if pct != last_pct and pct % 10 == 0:
                    print(f"    Progress: {pct}% ({downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB)")
                    last_pct = pct

    print(f"[SUCCESS] Download completed: {output_path}")

def extract_subset_from_tar_zst(archive_path: Path, output_dir: Path, max_patches: int = 5000):
    """
    Stream-decompresses a .tar.zst archive and extracts up to max_patches real Sentinel-2 patches.
    Avoids filling 120GB on a laptop hard drive.
    """
    try:
        import zstandard as zstd
        import tarfile
    except ImportError:
        print("\n[!] 'zstandard' library required for .tar.zst extraction.")
        print("    Please run: pip install zstandard\n")
        sys.exit(1)

    print("============================================================")
    print(f"TRINETRA — Stream Extracting Real Subset from {archive_path.name}")
    print(f"Target Directory: {output_dir}")
    print(f"Requested Subset Limit: {max_patches:,} patches")
    print("============================================================")

    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_patches = set()

    with open(archive_path, "rb") as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            with tarfile.open(fileobj=reader, mode="r|") as tar:
                for member in tar:
                    parts = Path(member.name).parts
                    if len(parts) >= 1:
                        patch_folder = parts[0]
                        if patch_folder not in extracted_patches:
                            if len(extracted_patches) >= max_patches:
                                print(f"[+] Reached requested subset quota ({max_patches:,} patches). Halting stream.")
                                break
                            extracted_patches.add(patch_folder)
                            if len(extracted_patches) % 500 == 0:
                                print(f"    Extracted {len(extracted_patches):,} / {max_patches:,} patch folders...")

                    tar.extract(member, path=str(output_dir))

    print(f"[SUCCESS] Extracted {len(extracted_patches):,} genuine Sentinel-2 patch folders to {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="TRINETRA BigEarthNet-S2 Dataset Download & Extraction Helper")
    parser.add_argument("--data_dir", type=str, default=r"D:\datasets\BigEarthNet-S2", help="Target dataset directory")
    parser.add_argument("--download_metadata", action="store_true", help="Download metadata.parquet (3.6 MB) from Zenodo")
    parser.add_argument("--archive", type=str, default=None, help="Path to downloaded BigEarthNet-S2.tar.zst")
    parser.add_argument("--extract_subset", type=int, default=0, help="Number of real patches to stream-extract (e.g. 5000 or 10000)")
    args = parser.parse_args()

    target_dir = Path(args.data_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if args.download_metadata:
        meta_out = target_dir / "metadata.parquet"
        if meta_out.exists() and check_md5(meta_out, ZENODO_METADATA_MD5):
            print(f"[+] metadata.parquet already exists and verified MD5: {meta_out}")
        else:
            print(f"[+] Downloading metadata.parquet (3.61 MB) to {meta_out}...")
            download_file_with_progress(ZENODO_METADATA_URL, meta_out)
            if check_md5(meta_out, ZENODO_METADATA_MD5):
                print("[+] Verified MD5 checksum matches official Zenodo release.")
            else:
                print("[WARNING] MD5 checksum did not match official release. File may be corrupted.")

    if args.archive and args.extract_subset > 0:
        arc_path = Path(args.archive)
        if not arc_path.exists():
            raise FileNotFoundError(f"Archive file not found: {arc_path}")
        extract_subset_from_tar_zst(arc_path, target_dir, args.extract_subset)

    if not args.download_metadata and not (args.archive and args.extract_subset > 0):
        print("==================================================================")
        print("TRINETRA BigEarthNet-S2 Download & Extraction Helper")
        print("==================================================================")
        print("Usage Examples:")
        print(f"  1. Download metadata.parquet (3.6 MB):")
        print(f"     python backend/training/01_bigearthnet/download_helper.py --data_dir \"{target_dir}\" --download_metadata\n")
        print(f"  2. Stream-extract 5,000 real patches from BigEarthNet-S2.tar.zst:")
        print(f"     python backend/training/01_bigearthnet/download_helper.py --data_dir \"{target_dir}\" --archive \"{target_dir / 'BigEarthNet-S2.tar.zst'}\" --extract_subset 5000")
        print("==================================================================")

if __name__ == "__main__":
    main()
