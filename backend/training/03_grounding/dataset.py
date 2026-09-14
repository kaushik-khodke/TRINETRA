"""
TRINETRA / SatQuery AI — DIOR-RSVG Genuine Dataset Loader
Loads real remote-sensing imagery, referring expressions, and bounding boxes.
Zero synthetic or dummy data permitted.
"""

import os
import json
from typing import Tuple, Dict, Any, Optional, List
from PIL import Image
import numpy as np
import torch
from torch.utils.data import Dataset

class RSGroundingGenuineDataset(Dataset):
    """
    Genuine PyTorch Dataset for Remote Sensing Visual Grounding.
    Loads real images and referring expressions with true bounding boxes [ymin, xmin, ymax, xmax].
    """
    def __init__(
        self,
        data_dir: str,
        manifest_file: str,
        image_size: int = 256,
        max_seq_len: int = 12,
        max_samples: Optional[int] = None
    ):
        self.data_dir = data_dir
        self.image_size = image_size
        self.max_seq_len = max_seq_len
        self.img_dir = os.path.join(data_dir, "JPEGImages")

        if not os.path.exists(self.img_dir):
            raise FileNotFoundError(f"Required 'JPEGImages/' directory not found in {data_dir}.")

        # Check for optimized .jsonl manifest
        jsonl_manifest = manifest_file.replace(".txt", ".jsonl") if manifest_file.endswith(".txt") else manifest_file
        if os.path.exists(jsonl_manifest):
            with open(jsonl_manifest, "r", encoding="utf-8") as f:
                self.records = [json.loads(line) for line in f if line.strip()]
        elif os.path.exists(manifest_file):
            with open(manifest_file, "r", encoding="utf-8") as f:
                self.records = [json.loads(line) for line in f if line.strip()]
        else:
            raise FileNotFoundError(f"Manifest '{manifest_file}' not found. Run prepare.py first.")

        if max_samples and max_samples < len(self.records):
            self.records = self.records[:max_samples]

        print(f"[GROUNDING DATASET] Indexed {len(self.records):,} genuine referring expression samples.")

    def __len__(self) -> int:
        return len(self.records)

    def _tokenize(self, text: str) -> torch.Tensor:
        words = text.lower().replace(".", "").replace(",", "").split()
        token_ids = []
        for w in words[:self.max_seq_len]:
            token_ids.append(abs(hash(w)) % 3900 + 100)
        while len(token_ids) < self.max_seq_len:
            token_ids.append(0)
        return torch.tensor(token_ids, dtype=torch.long)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        rec = self.records[idx]
        img_fn = rec["img"]
        box_coords = rec["box"]  # [ymin, xmin, ymax, xmax]
        query_text = rec["query"]

        img_path = os.path.join(self.img_dir, img_fn)
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image '{img_fn}' not found in {self.img_dir}.")

        # 1. Load Genuine Image
        img = Image.open(img_path).convert("RGB")
        if img.size != (self.image_size, self.image_size):
            img = img.resize((self.image_size, self.image_size), Image.BILINEAR)

        arr = np.array(img, dtype=np.float32) / 255.0
        arr = np.transpose(arr, (2, 0, 1))
        img_tensor = torch.from_numpy(arr)

        token_tensor = self._tokenize(query_text)
        box_tensor = torch.tensor(box_coords, dtype=torch.float32)

        return img_tensor, token_tensor, box_tensor
