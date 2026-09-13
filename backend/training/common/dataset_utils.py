"""
TRINETRA / SatQuery AI — Dataset Verification & Manifest Utilities
Enforces Rule 1 (Zero Synthetic Data) and Rule 2 (No Data Leakage).
"""

import os
from pathlib import Path
from typing import List, Set, Dict, Any, Optional

class RealDatasetVerificationError(RuntimeError):
    """Raised when real dataset requirements are not met."""
    pass

def verify_real_dataset(data_dir: str, required_files: List[str], dataset_name: str, download_url: str) -> Path:
    """
    Verifies that real dataset directory and required benchmark files exist.
    If missing, halts immediately with explicit instructions.
    """
    path = Path(data_dir)
    if not path.exists():
        msg = (
            f"\n"
            f"========================================================================\n"
            f"ERROR: REAL DATASET REQUIREMENT NOT MET\n"
            f"Dataset '{dataset_name}' not found at path: {path.resolve()}\n"
            f"Please download the real dataset from official source:\n"
            f"  -> {download_url}\n"
            f"Place the extracted dataset at: {path.resolve()}\n"
            f"TRINETRA strictly prohibits synthetic or mock training data.\n"
            f"========================================================================\n"
        )
        raise RealDatasetVerificationError(msg)

    missing = []
    for req in required_files:
        target = path / req
        if not target.exists():
            missing.append(req)

    if missing:
        msg = (
            f"\n"
            f"========================================================================\n"
            f"ERROR: REAL DATASET REQUIREMENT NOT MET\n"
            f"Missing required benchmark files in {path.resolve()}:\n"
            f"  Missing: {missing}\n"
            f"Please verify dataset integrity from: {download_url}\n"
            f"========================================================================\n"
        )
        raise RealDatasetVerificationError(msg)

    print(f"[DATASET VERIFIED] Genuine {dataset_name} verified at: {path.resolve()}")
    return path

def verify_split_leakage(train_ids: List[str], val_ids: List[str], test_ids: List[str]) -> bool:
    """Verifies complete independence between train, validation, and test sets."""
    s_train = set(train_ids)
    s_val = set(val_ids)
    s_test = set(test_ids)

    leak_train_val = s_train.intersection(s_val)
    leak_train_test = s_train.intersection(s_test)
    leak_val_test = s_val.intersection(s_test)

    if leak_train_val or leak_train_test or leak_val_test:
        raise ValueError(
            f"CRITICAL: DATA LEAKAGE DETECTED!\n"
            f"  Train ∩ Val overlap: {len(leak_train_val)}\n"
            f"  Train ∩ Test overlap: {len(leak_train_test)}\n"
            f"  Val ∩ Test overlap: {len(leak_val_test)}"
        )
    print(f"[LEAKAGE CHECK PASSED] Zero overlap across Train ({len(s_train)}), Val ({len(s_val)}), and Test ({len(s_test)}) splits.")
    return True

def save_manifest(manifest_dir: str, name: str, sample_ids: List[str]) -> str:
    """Saves exact dataset subset IDs to manifest file."""
    os.makedirs(manifest_dir, exist_ok=True)
    file_path = os.path.join(manifest_dir, f"{name}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        for sid in sample_ids:
            f.write(f"{sid}\n")
    print(f"[MANIFEST] Saved {len(sample_ids)} verified IDs to: {file_path}")
    return file_path
