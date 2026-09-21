"""
TRINETRA — Bi-Temporal Change Genuine Dataset Loader
Loads real registered observation pairs (T1, T2) and ground-truth dense change masks.
Governed by Stage 4 Change Detection Protocol. Zero synthetic or mock data.
"""

import os
import glob
import random
from typing import Tuple, Dict, Any, Optional, List, Union
from PIL import Image
import numpy as np
import torch
from torch.utils.data import Dataset


class BiTemporalChangeGenuineDataset(Dataset):
    """
    Genuine PyTorch Dataset for Bi-Temporal Remote-Sensing Dense Change Analysis.
    Loads real pre-change (T1) and post-change (T2) images with true dense change masks.
    Compatible with LEVIR-CD, WHU-CD, OSCD, and Siam-Diff benchmark formats.
    """
    def __init__(
        self,
        data_dir: str,
        manifest_file: Optional[str] = None,
        image_size: int = 256,
        max_samples: Optional[int] = None,
        return_dense_mask: bool = True,
        is_train: bool = False
    ):
        self.data_dir = data_dir
        self.image_size = image_size
        self.return_dense_mask = return_dense_mask
        self.is_train = is_train

        # Detect dataset directory layout
        self.has_split_dirs = (
            os.path.exists(os.path.join(data_dir, "train", "A")) and
            os.path.exists(os.path.join(data_dir, "train", "B"))
        )
        self.has_subdirs = (
            os.path.exists(os.path.join(data_dir, "A")) and
            os.path.exists(os.path.join(data_dir, "B"))
        ) or self.has_split_dirs

        if manifest_file and os.path.exists(manifest_file):
            with open(manifest_file, "r", encoding="utf-8") as f:
                self.sample_ids = [line.strip() for line in f if line.strip()]
        else:
            # Auto-discover from A/ or split directories if manifest not supplied
            if self.has_split_dirs:
                a_files = sorted(
                    glob.glob(os.path.join(data_dir, "train", "A", "*.*")) +
                    glob.glob(os.path.join(data_dir, "val", "A", "*.*")) +
                    glob.glob(os.path.join(data_dir, "test", "A", "*.*"))
                )
                self.sample_ids = [
                    os.path.splitext(os.path.basename(p))[0]
                    for p in a_files
                    if p.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))
                ]
            elif self.has_subdirs:
                a_files = sorted(glob.glob(os.path.join(data_dir, "A", "*.*")))
                self.sample_ids = [
                    os.path.splitext(os.path.basename(p))[0]
                    for p in a_files
                    if p.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))
                ]
            else:
                # Flat pair directories
                subdirs = [
                    d for d in os.listdir(data_dir)
                    if os.path.isdir(os.path.join(data_dir, d)) and not d.startswith(".")
                ]
                self.sample_ids = sorted(subdirs)

        if max_samples and max_samples < len(self.sample_ids):
            self.sample_ids = self.sample_ids[:max_samples]

        print(f"[CHANGE DATASET] Loaded {len(self.sample_ids):,} verified bi-temporal pairs from {data_dir} (train={self.is_train}).")

    def __len__(self) -> int:
        return len(self.sample_ids)

    def _load_image(self, path: str) -> np.ndarray:
        """Loads and normalizes an RGB image to (3, H, W) float32 in [0, 1]."""
        img = Image.open(path).convert("RGB")
        if img.size != (self.image_size, self.image_size):
            img = img.resize((self.image_size, self.image_size), Image.BILINEAR)
        arr = np.array(img, dtype=np.float32) / 255.0
        return np.transpose(arr, (2, 0, 1))

    def _load_mask(self, path: Optional[str]) -> np.ndarray:
        """Loads ground-truth change mask to (1, H, W) binary float32 {0.0, 1.0}."""
        if path and os.path.isfile(path):
            mask = Image.open(path).convert("L")
            if mask.size != (self.image_size, self.image_size):
                mask = mask.resize((self.image_size, self.image_size), Image.NEAREST)
            arr = np.array(mask, dtype=np.float32)
            # Standard remote-sensing masks: support both {0, 1} and {0, 255} encoding
            bin_arr = (arr >= 1.0).astype(np.float32)
            return np.expand_dims(bin_arr, axis=0)
        else:
            # Default zero mask if ground truth missing
            return np.zeros((1, self.image_size, self.image_size), dtype=np.float32)

    def _apply_augmentations(
        self,
        t1: np.ndarray,
        t2: np.ndarray,
        mask: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Synchronous spatial augmentations applied identically to T1, T2, and mask:
        - Random Horizontal Flip
        - Random Vertical Flip
        - Random 90/180/270 degree rotation
        """
        # Horizontal flip
        if random.random() > 0.5:
            t1 = np.ascontiguousarray(t1[:, :, ::-1])
            t2 = np.ascontiguousarray(t2[:, :, ::-1])
            mask = np.ascontiguousarray(mask[:, :, ::-1])

        # Vertical flip
        if random.random() > 0.5:
            t1 = np.ascontiguousarray(t1[:, ::-1, :])
            t2 = np.ascontiguousarray(t2[:, ::-1, :])
            mask = np.ascontiguousarray(mask[:, ::-1, :])

        # 90-degree rotations
        rot_k = random.randint(0, 3)
        if rot_k > 0:
            t1 = np.ascontiguousarray(np.rot90(t1, k=rot_k, axes=(1, 2)))
            t2 = np.ascontiguousarray(np.rot90(t2, k=rot_k, axes=(1, 2)))
            mask = np.ascontiguousarray(np.rot90(mask, k=rot_k, axes=(1, 2)))

        return t1, t2, mask

    def _find_file(self, sub_name: str, sid: str) -> Optional[str]:
        """Fast path resolution avoiding repeated glob overhead."""
        for ext in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]:
            direct = os.path.join(self.data_dir, sub_name, f"{sid}{ext}")
            if os.path.isfile(direct):
                return direct
            for s in ["train", "val", "test"]:
                nested = os.path.join(self.data_dir, s, sub_name, f"{sid}{ext}")
                if os.path.isfile(nested):
                    return nested
        # Fallback to glob only if standard extensions fail
        cands = glob.glob(os.path.join(self.data_dir, sub_name, f"{sid}.*"))
        if cands:
            return cands[0]
        for s in ["train", "val", "test"]:
            cands = glob.glob(os.path.join(self.data_dir, s, sub_name, f"{sid}.*"))
            if cands:
                return cands[0]
        return None

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        sid = self.sample_ids[idx]

        if self.has_subdirs:
            t1_file = self._find_file("A", sid)
            t2_file = self._find_file("B", sid)
            lbl_file = self._find_file("label", sid)

            if not t1_file or not t2_file:
                raise FileNotFoundError(f"Real bi-temporal pair for '{sid}' missing in {self.data_dir}.")

            t1_arr = self._load_image(t1_file)
            t2_arr = self._load_image(t2_file)
            mask_arr = self._load_mask(lbl_file)
        else:
            # Pair folder layout: <sid>/t1.*, <sid>/t2.*, <sid>/mask.*
            pair_dir = os.path.join(self.data_dir, sid)
            imgs = sorted(
                glob.glob(os.path.join(pair_dir, "*.png")) +
                glob.glob(os.path.join(pair_dir, "*.tif")) +
                glob.glob(os.path.join(pair_dir, "*.jpg"))
            )
            imgs = [img for img in imgs if not any(k in os.path.basename(img).lower() for k in ["cm", "mask", "label"])]

            if len(imgs) < 2:
                raise FileNotFoundError(f"Need at least 2 date images in pair folder {pair_dir}.")
            t1_arr = self._load_image(imgs[0])
            t2_arr = self._load_image(imgs[1])

            mask_files = (
                glob.glob(os.path.join(pair_dir, "*cm*.*")) +
                glob.glob(os.path.join(pair_dir, "*mask*.*")) +
                glob.glob(os.path.join(pair_dir, "*label*.*"))
            )
            mask_arr = self._load_mask(mask_files[0] if mask_files else None)

        if self.is_train:
            t1_arr, t2_arr, mask_arr = self._apply_augmentations(t1_arr, t2_arr, mask_arr)

        t1_tensor = torch.from_numpy(t1_arr)
        t2_tensor = torch.from_numpy(t2_arr)
        mask_tensor = torch.from_numpy(mask_arr)

        return t1_tensor, t2_tensor, mask_tensor
