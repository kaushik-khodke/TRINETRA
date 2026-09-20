"""
TRINETRA Analysis Engine — Change Probability & Mask Generation
Computes continuous change probability maps, binary change masks, and confidence distributions.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np



class ChangeMapGenerator:
    @staticmethod
    def generate_change_map(
        arr_t1: np.ndarray,
        arr_t2: np.ndarray,
        threshold: float = 0.35,
        neural_dense_mask: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Calculates:
        1. change_probability: float32 [0.0, 1.0]
        2. change_mask: bool (probability >= threshold)
        3. confidence_map: float32 [0.0, 1.0] (higher distance from threshold = higher confidence)
        """
        # If active dense neural prediction is provided by Siamese UNet
        if neural_dense_mask is not None:
            prob_map = neural_dense_mask.astype(np.float32)
        else:
            # Multi-spectral differential feature fusion
            # Normalized Euclidean difference across active spectral channels
            diff = np.abs(arr_t2.astype(np.float32) - arr_t1.astype(np.float32))
            if diff.ndim == 3:
                # Spectral magnitude
                magnitude = np.sqrt(np.sum(diff ** 2, axis=-1)) / np.sqrt(diff.shape[-1])
            else:
                magnitude = diff

            # Sigmoidal response to smooth probability around threshold
            prob_map = np.clip(magnitude, 0.0, 1.0)

        # Binary decision
        change_mask = prob_map >= threshold

        # Confidence: highest at 0.0 (certainly unchanged) and 1.0 (certainly changed), lowest at threshold
        conf_map = np.abs(prob_map - threshold) / max(threshold, 1.0 - threshold)
        conf_map = np.clip(conf_map, 0.5, 0.98)

        metadata = {
            "threshold_used": threshold,
            "min_probability": float(np.min(prob_map)),
            "max_probability": float(np.max(prob_map)),
            "mean_probability": float(np.mean(prob_map)),
            "neural_model_used": neural_dense_mask is not None,
        }

        return prob_map, change_mask, conf_map, metadata
