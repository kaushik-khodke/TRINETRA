"""
TRINETRA / SatQuery AI — RSVQA & EarthVQA Genuine Dataset Loader
Loads real remote-sensing satellite imagery and genuine question-answer pairs.
Features high-performance in-memory caching and real-time data augmentation.
Zero synthetic data.
"""

import os
import sys
import json
from typing import Tuple, Dict, Any, Optional, List
from PIL import Image
import numpy as np
import torch
from torch.utils.data import Dataset
import torchvision.transforms as T

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from models.tokenizer import tokenize_sequence, VqaTokenizer
except ImportError:
    from backend.models.tokenizer import tokenize_sequence, VqaTokenizer


class EarthVqaGenuineDataset(Dataset):
    """
    Genuine PyTorch Dataset for Remote-Sensing VQA (EarthVQA / RSVQA).
    Reads real imagery and verified questions/answers from manifests.
    """
    def __init__(
        self,
        manifest_path: str,
        image_size: int = 224,
        max_seq_len: int = 16,
        is_training: bool = False,
        preload_cache: bool = True,
        max_samples: Optional[int] = None
    ):
        self.manifest_path = manifest_path
        self.image_size = image_size
        self.max_seq_len = max_seq_len
        self.is_training = is_training
        self.preload_cache = preload_cache

        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        self.samples: List[Dict[str, Any]] = []
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.samples.append(json.loads(line))

        if max_samples and max_samples < len(self.samples):
            self.samples = self.samples[:max_samples]

        # Standard ImageNet normalization
        self.normalize = T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

        # Training augmentation
        if is_training:
            self.spatial_aug = T.Compose([
                T.RandomHorizontalFlip(p=0.5),
                T.RandomVerticalFlip(p=0.5),
                T.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1)
            ])
        else:
            self.spatial_aug = None

        # Image cache: stores uint8 numpy arrays or pre-resized PIL images to conserve memory
        self.img_cache: Dict[str, Image.Image] = {}
        self.tensor_cache: Dict[str, torch.Tensor] = {}

        if preload_cache:
            unique_paths = set(s["image_path"] for s in self.samples)
            print(f"[DATASET] Preloading {len(unique_paths)} unique images for {len(self.samples):,} QA samples...")
            for path in unique_paths:
                if os.path.exists(path):
                    im = Image.open(path).convert("RGB").resize((self.image_size, self.image_size), Image.BILINEAR)
                    self.img_cache[path] = im
                    if not self.is_training:
                        # Pre-normalize for instant zero-overhead retrieval in validation/testing
                        arr = np.transpose(np.array(im, dtype=np.float32) / 255.0, (2, 0, 1))
                        t = self.normalize(torch.from_numpy(arr))
                        self.tensor_cache[path] = t

        # Pre-tokenize all sample questions once to avoid string hashing overhead during training
        for sample in self.samples:
            sample["_token_ids"] = tokenize_sequence(sample["question"], max_length=self.max_seq_len, vocab_size=5000, offset=100)

        print(f"[DATASET] Ready: {len(self.samples):,} samples (training={is_training}, cached_images={len(self.img_cache)}).")

    def __len__(self) -> int:
        return len(self.samples)

    def _get_image(self, path: str) -> Image.Image:
        if path in self.img_cache:
            return self.img_cache[path]
        if os.path.exists(path):
            im = Image.open(path).convert("RGB").resize((self.image_size, self.image_size), Image.BILINEAR)
            if self.preload_cache:
                self.img_cache[path] = im
            return im
        raise FileNotFoundError(f"Satellite image not found: {path}")

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        sample = self.samples[idx]
        image_path = sample["image_path"]

        if not self.is_training and image_path in self.tensor_cache:
            img_tensor = self.tensor_cache[image_path]
        else:
            pil_img = self._get_image(image_path)
            # Augmentation (training only)
            if self.is_training and self.spatial_aug is not None:
                pil_img = self.spatial_aug(pil_img)
            # To Tensor [C, H, W] in [0, 1]
            img_arr = np.transpose(np.array(pil_img, dtype=np.float32) / 255.0, (2, 0, 1))
            img_tensor = self.normalize(torch.from_numpy(img_arr))

        # Question tokenization (from precomputed cache)
        token_ids = sample.get("_token_ids")
        if token_ids is None:
            token_ids = tokenize_sequence(sample["question"], max_length=self.max_seq_len, vocab_size=5000, offset=100)
            sample["_token_ids"] = token_ids
        token_tensor = torch.tensor(token_ids, dtype=torch.long)

        target_idx = sample.get("target_idx", -1)
        label_tensor = torch.tensor(target_idx, dtype=torch.long)

        return img_tensor, token_tensor, label_tensor

    def get_sample_metadata(self, idx: int) -> Dict[str, Any]:
        """Returns detailed metadata for evaluation analysis."""
        return self.samples[idx]


# Backward compatibility alias
RSVqaGenuineDataset = EarthVqaGenuineDataset
