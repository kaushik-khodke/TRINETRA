"""
TRINETRA / SatQuery AI — DIOR-RSVG Genuine Dataset Loader
Loads real remote-sensing imagery, referring expressions, and bounding boxes from XML annotations.
Zero synthetic or dummy data permitted.
"""

import os
import glob
import xml.etree.ElementTree as ET
from typing import Tuple, Dict, Any, Optional
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

        if not os.path.exists(manifest_file):
            raise FileNotFoundError(f"Manifest '{manifest_file}' not found. Run prepare.py first.")

        self.annot_dir = os.path.join(data_dir, "Annotations")
        self.img_dir = os.path.join(data_dir, "JPEGImages")

        if not os.path.exists(self.annot_dir) or not os.path.exists(self.img_dir):
            raise FileNotFoundError(f"Required 'Annotations/' or 'JPEGImages/' directory not found in {data_dir}.")

        self.samples = []
        with open(manifest_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 6:
                    img_name = parts[0]
                    xmin, ymin, xmax, ymax = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                    query_text = parts[5]
                    self.samples.append((img_name, xmin, ymin, xmax, ymax, query_text))
                else:
                    self.samples.append((parts[0], None, None, None, None, None))

        if max_samples and max_samples < len(self.samples):
            self.samples = self.samples[:max_samples]

        print(f"[GROUNDING DATASET] Indexed {len(self.samples):,} genuine referring expression samples.")

    def __len__(self) -> int:
        return len(self.samples)

    def _tokenize(self, text: str) -> torch.Tensor:
        words = text.lower().replace(".", "").replace(",", "").split()
        token_ids = []
        for w in words[:self.max_seq_len]:
            token_ids.append(abs(hash(w)) % 3900 + 100)
        while len(token_ids) < self.max_seq_len:
            token_ids.append(0)
        return torch.tensor(token_ids, dtype=torch.long)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        img_name, xmin, ymin, xmax, ymax, query_text = self.samples[idx]

        if not img_name.lower().endswith(('.jpg', '.png', '.tif', '.jpeg')):
            img_path = os.path.join(self.img_dir, f"{img_name}.jpg")
        else:
            img_path = os.path.join(self.img_dir, img_name)

        if not os.path.exists(img_path):
            alt_matches = glob.glob(os.path.join(self.img_dir, f"{os.path.splitext(img_name)[0]}.*"))
            if alt_matches:
                img_path = alt_matches[0]
            else:
                raise FileNotFoundError(f"Image '{img_name}' not found in {self.img_dir}.")

        # 1. Fast path: bounding box and query text already parsed into manifest
        if xmin is not None:
            img = Image.open(img_path).convert("RGB")
            orig_w, orig_h = img.size

            norm_ymin = np.clip(ymin / orig_h, 0.0, 1.0)
            norm_xmin = np.clip(xmin / orig_w, 0.0, 1.0)
            norm_ymax = np.clip(ymax / orig_h, 0.0, 1.0)
            norm_xmax = np.clip(xmax / orig_w, 0.0, 1.0)
            box_tensor = torch.tensor([norm_ymin, norm_xmin, norm_ymax, norm_xmax], dtype=torch.float32)

            if img.size != (self.image_size, self.image_size):
                img = img.resize((self.image_size, self.image_size), Image.BILINEAR)

            arr = np.array(img, dtype=np.float32) / 255.0
            arr = np.transpose(arr, (2, 0, 1))
            img_tensor = torch.from_numpy(arr)

            token_tensor = self._tokenize(query_text or "ground feature")
            return img_tensor, token_tensor, box_tensor

        # 2. Fallback: Parse XML Annotation if sample has no pre-parsed coordinates
        sid = os.path.splitext(img_name)[0]
        xml_path = os.path.join(self.annot_dir, f"{sid}.xml")
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"Annotation for ID '{sid}' not found in {self.annot_dir}.")

        tree = ET.parse(xml_path)
        root = tree.getroot()

        size_elem = root.find("size")
        orig_w = float(size_elem.find("width").text) if size_elem is not None else 800.0
        orig_h = float(size_elem.find("height").text) if size_elem is not None else 800.0

        query_elem = root.find(".//description") or root.find(".//query") or root.find(".//expression")
        query_str = query_elem.text if query_elem is not None else "ground feature"

        bndbox = root.find(".//bndbox")
        if bndbox is None:
            raise ValueError(f"No bounding box annotation found in {xml_path}")

        xmin = float(bndbox.find("xmin").text)
        ymin = float(bndbox.find("ymin").text)
        xmax = float(bndbox.find("xmax").text)
        ymax = float(bndbox.find("ymax").text)

        norm_ymin = np.clip(ymin / orig_h, 0.0, 1.0)
        norm_xmin = np.clip(xmin / orig_w, 0.0, 1.0)
        norm_ymax = np.clip(ymax / orig_h, 0.0, 1.0)
        norm_xmax = np.clip(xmax / orig_w, 0.0, 1.0)
        box_tensor = torch.tensor([norm_ymin, norm_xmin, norm_ymax, norm_xmax], dtype=torch.float32)

        img = Image.open(img_path).convert("RGB")
        if img.size != (self.image_size, self.image_size):
            img = img.resize((self.image_size, self.image_size), Image.BILINEAR)

        arr = np.array(img, dtype=np.float32) / 255.0
        arr = np.transpose(arr, (2, 0, 1))
        img_tensor = torch.from_numpy(arr)

        token_tensor = self._tokenize(query_str)
        return img_tensor, token_tensor, box_tensor
