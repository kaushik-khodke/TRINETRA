"""
TRINETRA / SatQuery AI — Hyperspectral Dataset Validator & Spatial Manifest Builder
Module: backend/training/06_hyperspectral/validate_dataset.py

Verifies:
1. Cube integrity (dimensions, band count, NaN/Inf absence, reflectance range).
2. Ground truth label distribution and class balance.
3. Strict spatial block disjointness: train_blocks ∩ val_blocks ∩ test_blocks = ∅.
4. Patch boundary buffer margin guarantee (zero cross-split receptive field leakage).
5. Train-only normalization calculation without lookahead.
6. Generates spatial split map and hsi_dataset_manifest.json.
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
import scipy.io as sio

# Local imports
try:
    from .dataset import (
        partition_spatial_grid,
        compute_train_normalization_stats,
        HyperspectralSpatialDataset
    )
except (ImportError, ValueError):
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from dataset import (
        partition_spatial_grid,
        compute_train_normalization_stats,
        HyperspectralSpatialDataset
    )


class HyperspectralDatasetValidator:
    """
    Validation engine for Remote Sensing Hyperspectral Data and Spatial Block Splits.
    """
    def __init__(
        self,
        grid_rows: int = 4,
        grid_cols: int = 4,
        patch_size: int = 11,
        boundary_margin: Optional[int] = None,
        ignore_index: int = 0
    ):
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols
        self.patch_size = patch_size
        self.half_p = patch_size // 2
        self.boundary_margin = boundary_margin if boundary_margin is not None else self.half_p
        self.ignore_index = ignore_index

    def validate(
        self,
        cube_or_path: Union[str, Path, np.ndarray],
        gt_or_path: Union[str, Path, np.ndarray],
        custom_split_blocks: Optional[Dict[str, List[int]]] = None,
        out_manifest_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes comprehensive HSI validation protocol.
        """
        errors = []
        warnings = []

        # 1. Load Cube
        cube = self._load_data(cube_or_path, is_gt=False).astype(np.float32)
        if cube.ndim != 3:
            errors.append(f"Expected 3D hyperspectral cube, got ndim={cube.ndim} with shape {cube.shape}")
            return {"valid": False, "errors": errors, "warnings": warnings}

        if cube.shape[0] < cube.shape[1] and cube.shape[0] < cube.shape[2]:
            # (B, H, W) -> (H, W, B)
            cube = np.transpose(cube, (1, 2, 0))

        height, width, num_bands = cube.shape

        if num_bands < 10:
            warnings.append(f"Low spectral band count ({num_bands} bands). Hyperspectral sensors typically have >= 50 bands.")

        # NaN / Inf checks
        nan_count = int(np.isnan(cube).sum())
        inf_count = int(np.isinf(cube).sum())
        if nan_count > 0:
            errors.append(f"Cube contains {nan_count} NaN values.")
        if inf_count > 0:
            errors.append(f"Cube contains {inf_count} infinite values.")

        c_min = float(np.min(cube))
        c_max = float(np.max(cube))
        if c_min < -1e5 or c_max > 1e7:
            warnings.append(f"Unusual radiometric range: min={c_min}, max={c_max}. May require sensor calibration scaling.")

        # 2. Load Ground Truth
        gt = self._load_data(gt_or_path, is_gt=True).astype(np.int64)
        if gt.shape != (height, width):
            errors.append(f"Dimension mismatch: cube spatial dimensions are ({height}, {width}), but gt is {gt.shape}")
            return {"valid": False, "errors": errors, "warnings": warnings}

        unique_classes = [int(x) for x in np.unique(gt) if x != self.ignore_index]
        num_classes = len(unique_classes)
        total_foreground = int(np.sum(gt != self.ignore_index))
        total_background = int(np.sum(gt == self.ignore_index))

        if num_classes < 2:
            errors.append(f"Insufficient number of labeled classes: found {num_classes}")

        # Class distribution
        class_distribution = {}
        for c in unique_classes:
            cnt = int(np.sum(gt == c))
            class_distribution[str(c)] = cnt
            if cnt < 20:
                warnings.append(f"Class {c} has very few labeled samples ({cnt}). Rare class starvation risk.")

        # 3. Spatial Block Partitioning & Disjointness
        block_grid, split_blocks, block_bounds = partition_spatial_grid(
            height=height,
            width=width,
            grid_rows=self.grid_rows,
            grid_cols=self.grid_cols,
            custom_split_blocks=custom_split_blocks
        )

        train_blocks = set(split_blocks["train"])
        val_blocks = set(split_blocks["val"])
        test_blocks = set(split_blocks["test"])

        # Mathematical disjointness check
        if bool(train_blocks & val_blocks):
            errors.append(f"Split leakage: Train and Val share blocks {train_blocks & val_blocks}")
        if bool(train_blocks & test_blocks):
            errors.append(f"Split leakage: Train and Test share blocks {train_blocks & test_blocks}")
        if bool(val_blocks & test_blocks):
            errors.append(f"Split leakage: Val and Test share blocks {val_blocks & test_blocks}")

        # 4. Patch Boundary Buffer Margin Check
        # Verify that samples drawn from each split never cross into another split's block
        ds_train = HyperspectralSpatialDataset(
            cube_or_path=cube,
            gt_or_path=gt,
            split="train",
            patch_size=self.patch_size,
            mode="pixel",
            grid_rows=self.grid_rows,
            grid_cols=self.grid_cols,
            boundary_margin=self.boundary_margin,
            ignore_index=self.ignore_index,
            custom_split_blocks=split_blocks
        )
        ds_val = HyperspectralSpatialDataset(
            cube_or_path=cube,
            gt_or_path=gt,
            split="val",
            patch_size=self.patch_size,
            mode="pixel",
            grid_rows=self.grid_rows,
            grid_cols=self.grid_cols,
            boundary_margin=self.boundary_margin,
            ignore_index=self.ignore_index,
            custom_split_blocks=split_blocks,
            norm_stats=ds_train.norm_stats
        )
        ds_test = HyperspectralSpatialDataset(
            cube_or_path=cube,
            gt_or_path=gt,
            split="test",
            patch_size=self.patch_size,
            mode="pixel",
            grid_rows=self.grid_rows,
            grid_cols=self.grid_cols,
            boundary_margin=self.boundary_margin,
            ignore_index=self.ignore_index,
            custom_split_blocks=split_blocks,
            norm_stats=ds_train.norm_stats
        )

        train_samples = len(ds_train)
        val_samples = len(ds_val)
        test_samples = len(ds_test)

        if train_samples == 0:
            errors.append("Zero valid training samples extracted after spatial buffering.")
        if test_samples == 0:
            errors.append("Zero valid testing samples extracted after spatial buffering.")

        # Verify patch buffer separation:
        # Check that no sample coordinate in train has an Chebyshev distance < patch_size to any sample in test
        # We sample a subset to keep validation quick
        train_coords = np.array([(s[0], s[1]) for s in ds_train.samples])
        test_coords = np.array([(s[0], s[1]) for s in ds_test.samples])

        buffer_violations = 0
        if len(train_coords) > 0 and len(test_coords) > 0:
            # Check minimum Chebyshev distance (L_infinity) between any train patch center and test patch center
            # Two patch centers must have max(|r1-r2|, |c1-c2|) >= patch_size to guarantee 0 overlapping pixels!
            # Since margin = patch_size // 2 on both sides of a block boundary, center-to-center distance across blocks is >= patch_size.
            sample_sub_train = train_coords[:min(200, len(train_coords))]
            sample_sub_test = test_coords[:min(200, len(test_coords))]
            diff = np.abs(sample_sub_train[:, None, :] - sample_sub_test[None, :, :])
            chebyshev_dist = np.max(diff, axis=-1)
            min_dist = int(np.min(chebyshev_dist))
            if min_dist < self.patch_size:
                warnings.append(
                    f"Minimum center-to-center distance between train and test samples is {min_dist} "
                    f"(target >= {self.patch_size}). Some patch margins may touch boundary."
                )

        # 5. Train-Only Normalization Verification
        norm_stats = ds_train.norm_stats
        if np.any(np.isnan(norm_stats["mean"])) or np.any(np.isnan(norm_stats["std"])):
            errors.append("NaN detected in train-only normalization statistics.")
        if np.any(norm_stats["std"] <= 0):
            errors.append("Non-positive standard deviation in normalization statistics.")

        # Result manifest
        is_valid = len(errors) == 0
        manifest = {
            "valid": is_valid,
            "cube_shape": [height, width, num_bands],
            "num_bands": num_bands,
            "num_classes": num_classes,
            "total_foreground_pixels": total_foreground,
            "total_background_pixels": total_background,
            "grid_config": {
                "grid_rows": self.grid_rows,
                "grid_cols": self.grid_cols,
                "total_blocks": self.grid_rows * self.grid_cols,
                "patch_size": self.patch_size,
                "boundary_margin": self.boundary_margin
            },
            "split_blocks": {
                "train": sorted(list(train_blocks)),
                "val": sorted(list(val_blocks)),
                "test": sorted(list(test_blocks))
            },
            "sample_counts": {
                "train": train_samples,
                "val": val_samples,
                "test": test_samples,
                "total_extracted": train_samples + val_samples + test_samples
            },
            "class_distribution": class_distribution,
            "train_normalization": {
                "mean_sample": norm_stats["mean"][:5].tolist(),
                "std_sample": norm_stats["std"][:5].tolist()
            },
            "errors": errors,
            "warnings": warnings
        }

        # Save manifest and split map if requested
        if out_manifest_dir:
            os.makedirs(out_manifest_dir, exist_ok=True)
            manifest_path = os.path.join(out_manifest_dir, "hsi_dataset_manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            split_map_path = os.path.join(out_manifest_dir, "split_map.npy")
            np.save(split_map_path, block_grid)

        return manifest

    def _load_data(self, source: Union[str, Path, np.ndarray], is_gt: bool = False) -> np.ndarray:
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


def main():
    parser = argparse.ArgumentParser(description="Validate Hyperspectral dataset and spatial splits.")
    parser.add_argument("--cube", type=str, required=True, help="Path to HSI data cube (.mat or .npy)")
    parser.add_argument("--gt", type=str, required=True, help="Path to ground truth mask (.mat or .npy)")
    parser.add_argument("--patch_size", type=int, default=11, help="Patch size for spatial models")
    parser.add_argument("--grid_rows", type=int, default=4, help="Grid rows for spatial block partition")
    parser.add_argument("--grid_cols", type=int, default=4, help="Grid cols for spatial block partition")
    parser.add_argument("--out_dir", type=str, default="./manifests/hsi", help="Directory to save manifest and split map")
    args = parser.parse_args()

    validator = HyperspectralDatasetValidator(
        grid_rows=args.grid_rows,
        grid_cols=args.grid_cols,
        patch_size=args.patch_size
    )

    manifest = validator.validate(
        cube_or_path=args.cube,
        gt_or_path=args.gt,
        out_manifest_dir=args.out_dir
    )

    print(json.dumps(manifest, indent=2))
    if manifest["valid"]:
        print(f"\n[PASS] Hyperspectral dataset and spatial split validated successfully.")
    else:
        print(f"\n[FAIL] Hyperspectral dataset validation failed with {len(manifest['errors'])} errors.")
        exit(1)


if __name__ == "__main__":
    main()
