"""
TRINETRA / SatQuery AI — Geographic Spatial Hyperspectral Dataset
Module: backend/training/06_hyperspectral/dataset.py

Implements spatial block grid partitioning with boundary buffer margins to
completely eliminate spatial autocorrelation leakage between train, validation,
and test sets. Enforces train-only spectral normalization (no data leakage).
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
import scipy.io as sio
import torch
from torch.utils.data import Dataset


def partition_spatial_grid(
    height: int,
    width: int,
    grid_rows: int = 4,
    grid_cols: int = 4,
    train_ratio: float = 0.65,
    val_ratio: float = 0.15,
    test_ratio: float = 0.20,
    custom_split_blocks: Optional[Dict[str, List[int]]] = None
) -> Tuple[np.ndarray, Dict[str, List[int]], List[Tuple[int, int, int, int]]]:
    """
    Partitions an (H, W) spatial image into grid_rows x grid_cols disjoint rectangular blocks.
    Assigns each block deterministically to 'train', 'val', or 'test'.

    Returns:
        block_grid: (H, W) array of block IDs (0 to grid_rows * grid_cols - 1)
        split_blocks: Dict mapping 'train', 'val', 'test' to lists of block IDs
        block_bounds: List of (r_min, r_max, c_min, c_max) bounding boxes for each block ID
    """
    total_blocks = grid_rows * grid_cols
    r_step = height // grid_rows
    c_step = width // grid_cols

    block_grid = np.zeros((height, width), dtype=np.int32)
    block_bounds = []

    for b in range(total_blocks):
        r_idx = b // grid_cols
        c_idx = b % grid_cols

        r_min = r_idx * r_step
        r_max = (r_idx + 1) * r_step if r_idx < grid_rows - 1 else height
        c_min = c_idx * c_step
        c_max = (c_idx + 1) * c_step if c_idx < grid_cols - 1 else width

        block_grid[r_min:r_max, c_min:c_max] = b
        block_bounds.append((r_min, r_max, c_min, c_max))

    if custom_split_blocks is not None:
        split_blocks = {
            "train": list(custom_split_blocks.get("train", [])),
            "val": list(custom_split_blocks.get("val", [])),
            "test": list(custom_split_blocks.get("test", []))
        }
    else:
        # Default structured spatial block partition
        # For a 4x4 grid (16 blocks):
        # Train: 10 blocks [0, 1, 2, 4, 5, 6, 8, 9, 10, 12] (top-left & west)
        # Val:   2 blocks  [3, 7] (northeast column)
        # Test:  4 blocks  [11, 13, 14, 15] (southeast block cluster)
        if grid_rows == 4 and grid_cols == 4:
            split_blocks = {
                "train": [0, 1, 2, 4, 5, 6, 8, 9, 10, 12],
                "val": [3, 7],
                "test": [11, 13, 14, 15]
            }
        else:
            n_train = max(1, int(round(total_blocks * train_ratio)))
            n_val = max(1, int(round(total_blocks * val_ratio)))
            all_b = list(range(total_blocks))
            split_blocks = {
                "train": all_b[:n_train],
                "val": all_b[n_train:n_train + n_val],
                "test": all_b[n_train + n_val:]
            }

    return block_grid, split_blocks, block_bounds


def compute_train_normalization_stats(
    cube: np.ndarray,
    block_grid: np.ndarray,
    train_blocks: List[int]
) -> Dict[str, np.ndarray]:
    """
    Computes band-wise mean and std strictly on pixels inside training spatial blocks.
    Zero information leakage into validation or testing sets.
    """
    train_mask = np.isin(block_grid, train_blocks)
    train_pixels = cube[train_mask]  # Shape: (N_train_pixels, B)

    if train_pixels.size == 0:
        raise ValueError("No pixels found in designated train blocks for normalization stats.")

    mean = np.mean(train_pixels, axis=0, dtype=np.float64).astype(np.float32)
    std = np.std(train_pixels, axis=0, dtype=np.float64).astype(np.float32)
    # Prevent divide by zero in flat or dead bands
    std = np.where(std < 1e-6, 1.0, std)

    return {"mean": mean, "std": std}


class HyperspectralSpatialDataset(Dataset):
    """
    Spatial block partitioned Hyperspectral Dataset.
    Guarantees:
    1. Zero spatial autocorrelation leakage via block grid assignment and boundary buffer margins.
    2. Train-only spectral normalization (mu_b, sigma_b).
    3. Multi-architecture extraction: 'pixel' (1D), 'patch_2d' (B, P, P), or 'patch_3d' (1, B, P, P).
    """
    def __init__(
        self,
        cube_or_path: Union[str, Path, np.ndarray],
        gt_or_path: Union[str, Path, np.ndarray],
        split: str = "train",
        patch_size: int = 11,
        mode: str = "patch_3d",
        grid_rows: int = 4,
        grid_cols: int = 4,
        boundary_margin: Optional[int] = None,
        ignore_index: int = 0,
        custom_split_blocks: Optional[Dict[str, List[int]]] = None,
        norm_stats: Optional[Dict[str, np.ndarray]] = None,
        return_coords: bool = True
    ):
        super().__init__()
        assert split in ("train", "val", "test"), f"Invalid split: {split}"
        assert mode in ("pixel", "patch_2d", "patch_3d"), f"Invalid mode: {mode}"

        self.split = split
        self.patch_size = patch_size
        self.mode = mode
        self.ignore_index = ignore_index
        self.return_coords = return_coords
        self.half_p = patch_size // 2
        self.margin = boundary_margin if boundary_margin is not None else self.half_p

        # 1. Load HSI Cube
        self.cube = self._load_array(cube_or_path, is_gt=False).astype(np.float32)
        if self.cube.ndim == 3 and self.cube.shape[0] > self.cube.shape[2]:
            # Already (H, W, B)
            pass
        elif self.cube.ndim == 3 and self.cube.shape[0] < self.cube.shape[1] and self.cube.shape[0] < self.cube.shape[2]:
            # Convert (B, H, W) -> (H, W, B)
            self.cube = np.transpose(self.cube, (1, 2, 0))

        self.height, self.width, self.num_bands = self.cube.shape

        # 2. Load Ground Truth Map
        self.gt = self._load_array(gt_or_path, is_gt=True).astype(np.int64)
        if self.gt.shape != (self.height, self.width):
            raise ValueError(f"Spatial dimension mismatch: cube is {(self.height, self.width)}, gt is {self.gt.shape}")

        # 3. Partition Grid
        self.block_grid, self.split_blocks, self.block_bounds = partition_spatial_grid(
            height=self.height,
            width=self.width,
            grid_rows=grid_rows,
            grid_cols=grid_cols,
            custom_split_blocks=custom_split_blocks
        )
        self.assigned_blocks = set(self.split_blocks[split])

        # 4. Enforce Train-Only Normalization
        if norm_stats is not None:
            self.norm_stats = norm_stats
        else:
            self.norm_stats = compute_train_normalization_stats(
                self.cube,
                self.block_grid,
                self.split_blocks["train"]
            )

        # Apply band-wise normalization
        self.normalized_cube = (self.cube - self.norm_stats["mean"]) / self.norm_stats["std"]

        # 5. Extract Valid Patch Centers with Boundary Buffer Margin
        self.samples: List[Tuple[int, int, int]] = []  # (row, col, class_label)
        self._extract_samples()

    def _load_array(self, source: Union[str, Path, np.ndarray], is_gt: bool = False) -> np.ndarray:
        if isinstance(source, np.ndarray):
            return source
        path_str = str(source)
        if not os.path.exists(path_str):
            raise FileNotFoundError(f"File not found: {path_str}")

        if path_str.endswith(".mat"):
            mat = sio.loadmat(path_str)
            keys = [k for k in mat.keys() if not k.startswith("__")]
            if is_gt:
                preferred = [k for k in keys if "gt" in k.lower() or "mask" in k.lower() or "label" in k.lower()]
                target_key = preferred[0] if preferred else keys[0]
            else:
                preferred = [k for k in keys if "corrected" in k.lower() or "data" in k.lower() or "cube" in k.lower()]
                target_key = preferred[0] if preferred else keys[0]
            return mat[target_key]
        elif path_str.endswith(".npy"):
            return np.load(path_str)
        else:
            raise ValueError(f"Unsupported file format: {path_str}")

    def _extract_samples(self):
        """
        Gathers valid sample coordinates for this split, enforcing:
        - Center pixel label != ignore_index
        - Center pixel lies inside an assigned block of this split
        - Center pixel distance from any cross-split boundary >= margin
        - Patch stays entirely within cube borders (half_p margin from edges)
        """
        h_min = self.half_p
        h_max = self.height - self.half_p
        w_min = self.half_p
        w_max = self.width - self.half_p

        # Find unique classes (excluding ignore_index)
        unique_labels = [int(lbl) for lbl in np.unique(self.gt) if lbl != self.ignore_index]
        self.unique_labels = sorted(unique_labels)
        # 0-indexed class mapping
        self.label_to_idx = {lbl: idx for idx, lbl in enumerate(self.unique_labels)}

        for b_id in self.assigned_blocks:
            r_min, r_max, c_min, c_max = self.block_bounds[b_id]

            # Determine buffer margins for this specific block:
            # If the block borders an edge or a block belonging to another split, enforce buffer
            r_start = max(h_min, r_min + self.margin)
            r_end = min(h_max, r_max - self.margin)
            c_start = max(w_min, c_min + self.margin)
            c_end = min(w_max, c_max - self.margin)

            if r_start >= r_end or c_start >= c_end:
                continue

            for r in range(r_start, r_end):
                for c in range(c_start, c_end):
                    raw_label = int(self.gt[r, c])
                    if raw_label == self.ignore_index:
                        continue
                    class_idx = self.label_to_idx.get(raw_label, raw_label - 1)
                    self.samples.append((r, c, class_idx))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Union[Tuple[torch.Tensor, torch.Tensor], Tuple[torch.Tensor, torch.Tensor, Tuple[int, int]]]:
        r, c, class_idx = self.samples[idx]
        target = torch.tensor(class_idx, dtype=torch.long)

        if self.mode == "pixel":
            # 1D spectral vector: shape (B,)
            spec = self.normalized_cube[r, c, :]
            data = torch.from_numpy(spec).float()

        elif self.mode == "patch_2d":
            # 2D patch for ViT: shape (B, P, P)
            patch = self.normalized_cube[
                r - self.half_p : r + self.half_p + (1 if self.patch_size % 2 != 0 else 0),
                c - self.half_p : c + self.half_p + (1 if self.patch_size % 2 != 0 else 0),
                :
            ]
            # Transpose (P, P, B) -> (B, P, P)
            data = torch.from_numpy(patch).permute(2, 0, 1).float()

        elif self.mode == "patch_3d":
            # 3D patch for HybridSN: shape (1, B, P, P)
            patch = self.normalized_cube[
                r - self.half_p : r + self.half_p + (1 if self.patch_size % 2 != 0 else 0),
                c - self.half_p : c + self.half_p + (1 if self.patch_size % 2 != 0 else 0),
                :
            ]
            # Transpose (P, P, B) -> (1, B, P, P)
            data = torch.from_numpy(patch).permute(2, 0, 1).unsqueeze(0).float()

        if self.return_coords:
            return data, target, (r, c)
        return data, target
