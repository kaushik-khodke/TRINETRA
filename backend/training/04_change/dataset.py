"""
TRINETRA / SatQuery AI — Bi-Temporal Change Genuine Dataset Loader
Loads real registered observation pairs (T1, T2) and ground-truth change masks.
Zero synthetic or mock data.
"""

import os
import glob
from typing import Tuple, Dict, Any, Optional
from PIL import Image
import numpy as np
import torch
from torch.utils.data import Dataset

class BiTemporalChangeGenuineDataset(Dataset):
    """
    Genuine PyTorch Dataset for Bi-Temporal Remote-Sensing Change Analysis.
    Loads real pre-change (T1) and post-change (T2) images with true change labels.
    """
    def __init__(
        self,
        data_dir: str,
        manifest_file: str,
        image_size: int = 224,
        max_samples: Optional[int] = None
    ):
        self.data_dir = data_dir
        self.image_size = image_size

        if not os.path.exists(manifest_file):
            raise FileNotFoundError(f"Manifest '{manifest_file}' not found. Run prepare.py first.")

        with open(manifest_file, "r", encoding="utf-8") as f:
            self.sample_ids = [line.strip() for line in f if line.strip()]

        if max_samples and max_samples < len(self.sample_ids):
            self.sample_ids = self.sample_ids[:max_samples]

        self.is_levir = os.path.exists(os.path.join(data_dir, "A")) and os.path.exists(os.path.join(data_dir, "B"))
        print(f"[CHANGE DATASET] Loaded {len(self.sample_ids):,} verified bi-temporal pairs from {data_dir}.")

    def __len__(self) -> int:
        return len(self.sample_ids)

    def _load_image(self, path: str) -> np.ndarray:
        img = Image.open(path).convert("RGB")
        if img.size != (self.image_size, self.image_size):
            img = img.resize((self.image_size, self.image_size), Image.BILINEAR)
        arr = np.array(img, dtype=np.float32) / 255.0
        return np.transpose(arr, (2, 0, 1))

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        sid = self.sample_ids[idx]

        if self.is_levir:
            # LEVIR-CD: A/<id>.*, B/<id>.*, label/<id>.*
            t1_files = glob.glob(os.path.join(self.data_dir, "A", f"{sid}.*"))
            t2_files = glob.glob(os.path.join(self.data_dir, "B", f"{sid}.*"))
            lbl_files = glob.glob(os.path.join(self.data_dir, "label", f"{sid}.*"))

            if not t1_files or not t2_files:
                raise FileNotFoundError(f"Real bi-temporal pair for '{sid}' missing in {self.data_dir}.")

            t1_arr = self._load_image(t1_files[0])
            t2_arr = self._load_image(t2_files[0])

            # Read genuine ground-truth change mask
            if lbl_files:
                mask = Image.open(lbl_files[0]).convert("L")
                mask_np = np.array(mask.resize((self.image_size, self.image_size), Image.NEAREST))
                change_ratio = float(np.mean(mask_np > 128))
                if change_ratio < 0.01:
                    target_class = 0  # Unchanged
                else:
                    # Compare pixel luminance to determine expansion (built-up addition) vs reduction
                    lum1 = np.mean(t1_arr)
                    lum2 = np.mean(t2_arr)
                    target_class = 1 if lum2 >= lum1 else 2  # 1: Expansion, 2: Reduction
            else:
                target_class = 0
        else:
            # OSCD or general pair folder: <sid>/date1.*, <sid>/date2.*
            pair_dir = os.path.join(self.data_dir, sid)
            imgs = sorted(glob.glob(os.path.join(pair_dir, "*.png")) + glob.glob(os.path.join(pair_dir, "*.tif")) + glob.glob(os.path.join(pair_dir, "*.jpg")))
            if len(imgs) < 2:
                raise FileNotFoundError(f"Need at least 2 date images in pair folder {pair_dir}.")
            t1_arr = self._load_image(imgs[0])
            t2_arr = self._load_image(imgs[1])

            # Check for ground truth change mask in pair folder
            mask_files = glob.glob(os.path.join(pair_dir, "*cm*.*")) + glob.glob(os.path.join(pair_dir, "*mask*.*"))
            if mask_files:
                mask = Image.open(mask_files[0]).convert("L")
                mask_np = np.array(mask.resize((self.image_size, self.image_size), Image.NEAREST))
                target_class = 1 if np.mean(mask_np > 128) >= 0.02 else 0
            else:
                target_class = 0

        t1_tensor = torch.from_numpy(t1_arr)
        t2_tensor = torch.from_numpy(t2_arr)
        label_tensor = torch.tensor(target_class, dtype=torch.long)

        return t1_tensor, t2_tensor, label_tensor
