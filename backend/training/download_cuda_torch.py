"""
TRINETRA / SatQuery AI — Resilient PyTorch CUDA Downloader & Installer
Downloads CUDA 12.1 wheels with automatic resume on network drops, then installs them.
"""

import os
import sys
import time
import urllib.request
import urllib.error
import subprocess

TORCH_WHEEL_URL = "https://download.pytorch.org/whl/cu121/torch-2.5.1%2Bcu121-cp310-cp310-win_amd64.whl"
VISION_WHEEL_URL = "https://download.pytorch.org/whl/cu121/torchvision-0.20.1%2Bcu121-cp310-cp310-win_amd64.whl"

def download_with_resume(url: str, dest_path: str, max_retries: int = 20):
    """Downloads a file with HTTP Range resume support across network drops."""
    filename = os.path.basename(dest_path)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            total_size = int(resp.headers.get("Content-Length", 0))
    except Exception as e:
        print(f"[!] Could not determine total size ({e}), proceeding with standard fetch.")
        total_size = 0

    retries = 0
    while retries < max_retries:
        current_size = os.path.getsize(dest_path) if os.path.exists(dest_path) else 0
        if total_size > 0 and current_size >= total_size:
            print(f"[SUCCESS] {filename} is already fully downloaded ({current_size / (1024**2):.1f} MB).")
            return True

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        if current_size > 0:
            req.add_header("Range", f"bytes={current_size}-")
            print(f"[RESUME] Resuming {filename} from {current_size / (1024**2):.1f} MB / {total_size / (1024**2):.1f} MB...")
        else:
            print(f"[DOWNLOAD] Starting download of {filename} ({total_size / (1024**2):.1f} MB)...")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                mode = "ab" if current_size > 0 else "wb"
                with open(dest_path, mode) as f:
                    chunk_size = 1024 * 1024  # 1 MB chunks
                    last_print = time.time()
                    downloaded = current_size
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        now = time.time()
                        if now - last_print >= 3.0:
                            pct = (downloaded / total_size * 100) if total_size > 0 else 0
                            print(f"  --> Progress: {downloaded / (1024**2):.1f} MB / {total_size / (1024**2):.1f} MB ({pct:.1f}%)")
                            last_print = now

            final_size = os.path.getsize(dest_path)
            if total_size > 0 and final_size < total_size:
                raise IOError(f"Connection ended early: {final_size} of {total_size} bytes downloaded.")
            
            print(f"[COMPLETE] Finished downloading {filename} ({final_size / (1024**2):.1f} MB).")
            return True

        except (urllib.error.URLError, urllib.error.HTTPError, IOError, TimeoutError) as e:
            retries += 1
            print(f"[WARNING] Network drop ({e}). Retry {retries}/{max_retries} in 3 seconds...")
            time.sleep(3)

    print(f"[ERROR] Exceeded maximum retries ({max_retries}) for {filename}.")
    return False

def main():
    dest_dir = r"D:\torch_wheels"
    torch_file = os.path.join(dest_dir, "torch-2.5.1+cu121-cp310-cp310-win_amd64.whl")
    vision_file = os.path.join(dest_dir, "torchvision-0.20.1+cu121-cp310-cp310-win_amd64.whl")

    print("=" * 65)
    print("TRINETRA — Resilient PyTorch CUDA 12.1 Downloader for RTX 3050")
    print(f"Destination Folder: {dest_dir}")
    print("=" * 65)

    print("\n[STEP 1/2] Downloading PyTorch CUDA 12.1 (~2.4 GB)...")
    if not download_with_resume(TORCH_WHEEL_URL, torch_file):
        sys.exit(1)

    print("\n[STEP 2/2] Downloading TorchVision CUDA 12.1 (~8 MB)...")
    if not download_with_resume(VISION_WHEEL_URL, vision_file):
        sys.exit(1)

    print("\n" + "=" * 65)
    print("[INSTALLATION] Installing downloaded CUDA wheels into Python 3.10...")
    print("=" * 65)

    cmd = [
        sys.executable, "-m", "pip", "install",
        torch_file, vision_file,
        "--force-reinstall", "--no-deps"
    ]
    print(f"Running: {' '.join(cmd)}")
    res = subprocess.run(cmd)

    if res.returncode == 0:
        print("\n" + "=" * 65)
        print("[TEST] Verifying CUDA on your NVIDIA RTX 3050...")
        print("=" * 65)
        test_cmd = [sys.executable, "-c", "import torch; print('CUDA Available:', torch.cuda.is_available(), '| GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"]
        subprocess.run(test_cmd)
        print("=" * 65)
    else:
        print(f"[!] Installation failed with code {res.returncode}. You can manually run:")
        print(f'py -3.10 -m pip install "{torch_file}" "{vision_file}" --force-reinstall --no-deps')

if __name__ == "__main__":
    main()
