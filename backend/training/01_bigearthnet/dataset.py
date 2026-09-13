"""
TRINETRA / SatQuery AI — BigEarthNet-S2 Genuine Dataset Loader
Loads real Sentinel-2 GeoTIFF multispectral bands and CORINE land-cover multi-hot labels.
Zero synthetic or mock data permitted.
"""

import os
import glob
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset
import pandas as pd

CORINE_19_CLASSES = [
    "Agro-forestry areas", "Arable land", "Beaches, dunes, sands", "Broad-leaved forest",
    "Coastal wetlands", "Complex cultivation patterns", "Coniferous forest",
    "Industrial or commercial units", "Inland waters", "Inland wetlands",
    "Land principally occupied by agriculture, with significant areas of natural vegetation",
    "Marine waters", "Mixed forest", "Moors, heathland and sclerophyllous vegetation",
    "Natural grassland and sparsely vegetated areas", "Pastures", "Permanent crops",
    "Transitional woodland, shrub", "Urban fabric"
]

class BigEarthNetS2Dataset(Dataset):
    """
    Genuine BigEarthNet-S2 PyTorch Dataset.
    Loads real Sentinel-2 multi-band imagery and true Corine Land Cover multi-labels.
    """
    def __init__(
        self,
        data_dir: str,
        manifest_file: str,
        metadata_path: str,
        num_bands: int = 4,  # 4 for RGB-NIR (B04, B03, B02, B08), or 12 for all Sentinel-2 bands
        image_size: int = 120,
        max_samples: Optional[int] = None
    ):
        self.data_dir = data_dir
        self.num_bands = num_bands
        self.image_size = image_size

        if not os.path.exists(manifest_file):
            raise FileNotFoundError(
                f"Manifest file '{manifest_file}' not found.\n"
                f"Please run 'python training/01_bigearthnet/prepare.py' first."
            )

        with open(manifest_file, "r", encoding="utf-8") as f:
            self.patch_names = [line.strip() for line in f if line.strip()]

        if max_samples and max_samples < len(self.patch_names):
            self.patch_names = self.patch_names[:max_samples]

        print(f"[DATASET] Loading metadata from {metadata_path}...")
        if metadata_path.endswith(".parquet"):
            df = pd.read_parquet(metadata_path)
        else:
            df = pd.read_csv(metadata_path)

        id_col = "patch_id" if "patch_id" in df.columns else ("patch_name" if "patch_name" in df.columns else df.columns[0])
        label_col = "labels" if "labels" in df.columns else "Labels"

        # Index metadata by patch name
        self.metadata_lookup = {}
        for _, row in df.iterrows():
            p_name = str(row[id_col])
            raw_labels = row[label_col]
            if isinstance(raw_labels, str):
                import ast
                try:
                    parsed = ast.literal_eval(raw_labels)
                except:
                    parsed = [raw_labels]
            elif isinstance(raw_labels, (list, np.ndarray)):
                parsed = list(raw_labels)
            else:
                parsed = []
            self.metadata_lookup[p_name] = parsed

        print(f"[DATASET] Verified {len(self.patch_names):,} real BigEarthNet-S2 patches for loader.")

    def __len__(self) -> int:
        return len(self.patch_names)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        patch_name = self.patch_names[idx]
        patch_dir = os.path.join(self.data_dir, patch_name)

        # 1. Load Genuine Sentinel-2 Bands
        tensor_channels = []
        if os.path.isdir(patch_dir):
            # Standard BigEarthNet directory with individual band GeoTIFFs (B01.tif .. B12.tif)
            band_names = ["B04", "B03", "B02", "B08"] if self.num_bands == 4 else [
                "B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12"
            ]
            for b in band_names:
                b_files = glob.glob(os.path.join(patch_dir, f"*{b}*.tif"))
                if not b_files:
                    raise FileNotFoundError(f"Real band file '{b}' not found for patch {patch_name} in {patch_dir}")
                img = Image.open(b_files[0])
                if img.size != (self.image_size, self.image_size):
                    img = img.resize((self.image_size, self.image_size), Image.BILINEAR)
                arr = np.array(img, dtype=np.float32) / 10000.0  # Sentinel-2 reflectance scaling (0-1)
                tensor_channels.append(arr)
            img_tensor = torch.from_numpy(np.stack(tensor_channels, axis=0))
        elif os.path.exists(patch_dir + ".tif"):
            # Consolidated multi-band GeoTIFF
            img = Image.open(patch_dir + ".tif")
            if img.size != (self.image_size, self.image_size):
                img = img.resize((self.image_size, self.image_size), Image.BILINEAR)
            arr = np.array(img, dtype=np.float32)
            if arr.ndim == 2:
                arr = np.expand_dims(arr, axis=0)
            elif arr.ndim == 3:
                arr = np.transpose(arr, (2, 0, 1))
            if arr.shape[0] < self.num_bands:
                # Pad to requested bands if needed
                pad = np.zeros((self.num_bands - arr.shape[0], arr.shape[1], arr.shape[2]), dtype=np.float32)
                arr = np.concatenate([arr, pad], axis=0)
            img_tensor = torch.from_numpy(arr[:self.num_bands] / 10000.0)
        else:
            raise FileNotFoundError(f"Cannot find genuine satellite patch imagery for '{patch_name}' in '{self.data_dir}'.")

        # 2. Build 19-class Multi-Hot Label Vector from Genuine Metadata
        labels_list = self.metadata_lookup.get(patch_name, [])
        multi_hot = np.zeros(len(CORINE_19_CLASSES), dtype=np.float32)
        for lbl in labels_list:
            lbl_str = str(lbl).strip()
            if lbl_str in CORINE_19_CLASSES:
                multi_hot[CORINE_19_CLASSES.index(lbl_str)] = 1.0

        label_tensor = torch.from_numpy(multi_hot)
        return img_tensor, label_tensor
