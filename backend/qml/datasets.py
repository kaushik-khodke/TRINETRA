"""
SatQuery AI / TRINETRA — QML Real Remote-Sensing Datasets
Strict Zero-Synthetic-Data Compliance.
Loads legitimate bi-temporal remote-sensing datasets (OSCD, LEVIR-CD)
and extracts classical deep features for QML training and evaluation.
"""

import os
import glob
import numpy as np
import torch
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image

try:
    import tifffile
    HAS_TIFF = True
except ImportError:
    HAS_TIFF = False

class RealChangeDataset:
    """
    Dataset loader for genuine bi-temporal remote-sensing rasters.
    Enforces the strict ZERO-SYNTHETIC-DATA policy:
    If genuine datasets are absent, provides verified acquisition instructions.
    """

    DATASET_SPECS = {
        "OSCD": {
            "name": "Onera Satellite Change Detection",
            "url": "https://ieee-dataport.org/open-access/oscd-onera-satellite-change-detection",
            "description": "24 Sentinel-2 multi-spectral image pairs with pixel-level ground truth.",
            "expected_subdirs": ["Onera Satellite Change Detection", "images_pair", "train", "test"]
        },
        "LEVIR_CD": {
            "name": "LEVIR-CD High-Resolution Change Detection",
            "url": "https://justchenhao.github.io/LEVIR/",
            "description": "637 ultra-high-resolution (0.5m) bi-temporal Google Earth image pairs (1024x1024).",
            "expected_subdirs": ["A", "B", "label"]
        }
    }

    def __init__(self, data_dir: str, split: str = "train", max_samples: Optional[int] = None):
        self.data_dir = data_dir
        self.split = split
        self.max_samples = max_samples
        self.samples: List[Dict[str, Any]] = []
        self._scan_dataset()

    def _scan_dataset(self):
        """Scans filesystem for genuine bi-temporal image pairs and labels."""
        if not os.path.exists(self.data_dir):
            return

        # Pattern 1: LEVIR-CD style (A/ and B/ and label/)
        dir_a = os.path.join(self.data_dir, self.split, "A")
        dir_b = os.path.join(self.data_dir, self.split, "B")
        dir_label = os.path.join(self.data_dir, self.split, "label")

        if os.path.exists(dir_a) and os.path.exists(dir_b):
            files_a = sorted(glob.glob(os.path.join(dir_a, "*.png")) + glob.glob(os.path.join(dir_a, "*.tif*")))
            for path_a in files_a:
                filename = os.path.basename(path_a)
                path_b = os.path.join(dir_b, filename)
                path_lbl = os.path.join(dir_label, filename) if os.path.exists(dir_label) else None
                if os.path.exists(path_b):
                    self.samples.append({
                        "id": os.path.splitext(filename)[0],
                        "t1_path": path_a,
                        "t2_path": path_b,
                        "label_path": path_lbl if (path_lbl and os.path.exists(path_lbl)) else None
                    })
            if self.max_samples and len(self.samples) > self.max_samples:
                self.samples = self.samples[:self.max_samples]
            return

        # Pattern 2: Direct A/ and B/ at root of data_dir
        if not self.samples:
            for pair in [("A", "B"), ("pre", "post"), ("before", "after"), ("time1", "time2"), ("t1", "t2")]:
                da = os.path.join(self.data_dir, pair[0])
                db = os.path.join(self.data_dir, pair[1])
                dl = os.path.join(self.data_dir, "label")
                if os.path.exists(da) and os.path.exists(db):
                    fa = sorted(glob.glob(os.path.join(da, "*.png")) + glob.glob(os.path.join(da, "*.tif*")) + glob.glob(os.path.join(da, "*.jpg*")))
                    for pa in fa:
                        fn = os.path.basename(pa)
                        pb = os.path.join(db, fn)
                        pl = os.path.join(dl, fn) if os.path.exists(dl) else None
                        if os.path.exists(pb):
                            self.samples.append({
                                "id": os.path.splitext(fn)[0],
                                "t1_path": pa,
                                "t2_path": pb,
                                "label_path": pl if (pl and os.path.exists(pl)) else None
                            })
                    if self.samples:
                        break

        # Pattern 3: Flat pairs (*_t1.* and *_t2.*)
        if not self.samples:
            t1_files = sorted(glob.glob(os.path.join(self.data_dir, "*t1*.*")))
            for p1 in t1_files:
                base = os.path.basename(p1)
                p2 = p1.replace("t1", "t2").replace("T1", "T2")
                if os.path.exists(p2) and p1 != p2:
                    self.samples.append({
                        "id": os.path.splitext(base)[0],
                        "t1_path": p1,
                        "t2_path": p2,
                        "label_path": None
                    })

        if self.max_samples and len(self.samples) > self.max_samples:
            self.samples = self.samples[:self.max_samples]

    def __len__(self) -> int:
        return len(self.samples)

    def is_available(self) -> bool:
        return len(self.samples) > 0

    @classmethod
    def get_acquisition_instructions(cls) -> str:
        """Clear dataset installation instructions when datasets are absent."""
        return """
================================================================================
REAL REMOTE-SENSING CHANGE DATASET ACQUISITION INSTRUCTIONS (ZERO SYNTHETIC DATA)
================================================================================
To train the QML Variational Quantum Classifier on legitimate satellite imagery:

1. OSCD Dataset (Onera Satellite Change Detection - Sentinel-2):
   Download: https://ieee-dataport.org/open-access/oscd-onera-satellite-change-detection
   Extract to: D:\\datasets\\OSCD\\

2. LEVIR-CD Dataset (Bi-temporal Optical Change Detection):
   Download: https://justchenhao.github.io/LEVIR/
   Extract to: D:\\datasets\\LEVIR_CD\\
   Folder structure:
     D:\\datasets\\LEVIR_CD\\train\\A\\ (Pre-change imagery)
     D:\\datasets\\LEVIR_CD\\train\\B\\ (Post-change imagery)
     D:\\datasets\\LEVIR_CD\\train\\label\\ (Change masks)

Per project policy, synthetic random tensors (torch.randn) are STRICTLY PROHIBITED.
================================================================================
"""
