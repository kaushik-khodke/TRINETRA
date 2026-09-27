"""
TRINETRA Analysis Engine — Semantic Resampling Engine
Selects the mathematically correct resampling kernel based on data semantics:
- Bilinear / Cubic for continuous radiometric bands
- Nearest Neighbor for discrete categorical masks, land-use classifications, and nodata masks.
"""

from enum import Enum
from typing import Tuple
import numpy as np
from PIL import Image


class ResamplingStrategy(str, Enum):
    BILINEAR = "bilinear"
    BICUBIC = "bicubic"
    NEAREST = "nearest"


class SemanticResampler:
    @staticmethod
    def resample(
        arr: np.ndarray,
        target_shape: Tuple[int, int],
        is_discrete: bool = False,
    ) -> np.ndarray:
        """
        Resamples a 2D or 3D numpy array to target_shape (H, W).
        """
        target_h, target_w = target_shape
        orig_dtype = arr.dtype
        pil_resampling = Image.NEAREST if is_discrete else Image.BILINEAR

        if arr.ndim == 3:
            channels = []
            for c in range(arr.shape[2]):
                ch = arr[:, :, c]
                pil_ch = Image.fromarray(ch)
                resized = pil_ch.resize((target_w, target_h), pil_resampling)
                channels.append(np.array(resized, dtype=orig_dtype))
            return np.stack(channels, axis=-1)
        else:
            pil_img = Image.fromarray(arr)
            resized = pil_img.resize((target_w, target_h), pil_resampling)
            return np.array(resized, dtype=orig_dtype)
