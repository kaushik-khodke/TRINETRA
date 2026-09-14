"""
SatQuery AI / TRINETRA — QML Feature Reduction Pipeline
Strict Zero-Leakage Preprocessing & PCA Dimension Reduction.
Compresses high-dimensional classical remote-sensing feature representations (e.g. 128-d)
into 4–8 quantum-encodable continuous features.
"""

import os
import json
import numpy as np
from typing import Dict, Any, Tuple, Optional

class QMLFeaturePipeline:
    """
    Standardizes and projects high-dimensional classical embeddings into quantum state rotations.
    Guarantees strict zero-leakage: transformations are fitted exclusively on training splits.
    """

    def __init__(self, target_dim: int = 4, seed: int = 42):
        self.target_dim = target_dim
        self.seed = seed
        self.mean: Optional[np.ndarray] = None
        self.std: Optional[np.ndarray] = None
        self.components: Optional[np.ndarray] = None  # Shape: (input_dim, target_dim)
        self.explained_variance_ratio: Optional[np.ndarray] = None
        self.input_dim: Optional[int] = None
        self.is_fitted: bool = False

    def fit(self, X_train: np.ndarray) -> "QMLFeaturePipeline":
        """
        Fits StandardScaler and PCA projection exclusively on the training feature matrix.
        X_train shape: (num_samples, input_features)
        """
        if X_train.ndim != 2:
            raise ValueError(f"Expected 2D array of shape (N, D), got {X_train.shape}")
        
        N, D = X_train.shape
        self.input_dim = D
        if self.target_dim > D:
            raise ValueError(f"target_dim ({self.target_dim}) cannot exceed input_dim ({D})")

        # 1. Clean NaNs or Infs if any
        X_clean = np.nan_to_num(X_train, nan=0.0, posinf=1.0, neginf=-1.0)

        # 2. Fit Standardization
        self.mean = np.mean(X_clean, axis=0)
        self.std = np.std(X_clean, axis=0)
        self.std[self.std < 1e-8] = 1.0  # Guard against division by zero

        X_scaled = (X_clean - self.mean) / self.std

        # 3. Fit PCA via SVD (Zero-leakage, exact NumPy formulation)
        # Center is already 0 after scaling
        U, S, Vt = np.linalg.svd(X_scaled, full_matrices=False)
        self.components = Vt[:self.target_dim, :].T  # Shape: (D, target_dim)

        total_variance = np.sum(S ** 2)
        if total_variance > 1e-12:
            self.explained_variance_ratio = (S[:self.target_dim] ** 2) / total_variance
        else:
            self.explained_variance_ratio = np.ones(self.target_dim) / self.target_dim

        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Projects arbitrary samples into [0, pi] bounded feature space for AngleEmbedding.
        """
        if not self.is_fitted:
            # If not yet fitted with a training set, apply a deterministic fallback projection
            D = X.shape[-1] if X.ndim > 1 else len(X)
            return self._fallback_transform(X, D)

        X_2d = X if X.ndim == 2 else X.reshape(1, -1)
        X_clean = np.nan_to_num(X_2d, nan=0.0, posinf=1.0, neginf=-1.0)
        if self.mean is not None and X_clean.shape[1] != self.mean.shape[0]:
            expected_dim = self.mean.shape[0]
            if X_clean.shape[1] < expected_dim:
                pad_width = ((0, 0), (0, expected_dim - X_clean.shape[1]))
                X_clean = np.pad(X_clean, pad_width, mode='constant')
            else:
                X_clean = X_clean[:, :expected_dim]
        X_scaled = (X_clean - self.mean) / self.std
        X_proj = X_scaled @ self.components  # Shape: (N, target_dim)

        # Non-linear squash to [0, np.pi] for quantum AngleEmbedding
        # tanh maps to [-1, 1], then scale and shift to [0, pi]
        q_features = np.pi * (0.5 * np.tanh(X_proj) + 0.5)
        return q_features if X.ndim == 2 else q_features[0]

    def _fallback_transform(self, X: np.ndarray, input_dim: int) -> np.ndarray:
        """Deterministic dimensional compression when checkpoint pipeline is not loaded."""
        X_flat = np.nan_to_num(X.flatten(), nan=0.0)
        L = len(X_flat)
        q_feats = np.zeros(self.target_dim, dtype=float)
        chunk_size = max(1, L // self.target_dim)
        for i in range(self.target_dim):
            chunk = X_flat[i * chunk_size : (i + 1) * chunk_size]
            if len(chunk) > 0:
                val = float(np.mean(chunk))
                # Map to [0, pi]
                q_feats[i] = np.pi * (0.5 * np.tanh(val) + 0.5)
            else:
                q_feats[i] = np.pi / 2.0
        return q_feats

    def save(self, filepath: str):
        """Saves fitted transformation to a JSON manifest."""
        data = {
            "input_features": int(self.input_dim) if self.input_dim else self.target_dim,
            "reduced_features": int(self.target_dim),
            "mean": self.mean.tolist() if self.mean is not None else [],
            "std": self.std.tolist() if self.std is not None else [],
            "components": self.components.tolist() if self.components is not None else [],
            "explained_variance_ratio": self.explained_variance_ratio.tolist() if self.explained_variance_ratio is not None else [],
            "seed": self.seed,
            "is_fitted": self.is_fitted
        }
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "QMLFeaturePipeline":
        """Loads fitted transformation from JSON manifest."""
        if not os.path.exists(filepath):
            return cls()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        inst = cls(target_dim=data.get("reduced_features", 4), seed=data.get("seed", 42))
        inst.input_dim = data.get("input_features")
        if data.get("is_fitted"):
            inst.mean = np.array(data["mean"])
            inst.std = np.array(data["std"])
            inst.components = np.array(data["components"])
            inst.explained_variance_ratio = np.array(data["explained_variance_ratio"])
            inst.is_fitted = True
        return inst
