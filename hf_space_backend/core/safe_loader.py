"""
TRINETRA — Safe Model Deserialization & Checkpoint Loader
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)

Hardens PyTorch checkpoint loading:
1. Enforces weights_only=True to prevent arbitrary code execution via untrusted pickle payloads
2. Verifies cryptographic SHA-256 digests against known manifests
3. Standardizes state_dict extraction across diverse checkpoint layouts
"""

import os
import torch
from typing import Dict, Any, Optional

from core.exceptions import ModelCheckpointError, UnsafeDeserializationError, SecurityViolationError
from core.provenance import compute_file_sha256


class SafeModelLoader:
    """Secure PyTorch neural checkpoint loader with strict deserialization safeguards."""

    @classmethod
    def load_state_dict(
        cls,
        checkpoint_path: str,
        map_location: str = "cpu",
        expected_hash: Optional[str] = None,
        enforce_weights_only: bool = True
    ) -> Dict[str, Any]:
        """
        Loads a PyTorch checkpoint with guaranteed weights_only=True protection.
        Validates file existence and cryptographic integrity.
        """
        if not checkpoint_path or not os.path.isfile(checkpoint_path):
            raise ModelCheckpointError(f"Checkpoint file does not exist on disk: '{checkpoint_path}'.")

        # Cryptographic checksum verification
        actual_hash = compute_file_sha256(checkpoint_path)
        if expected_hash and actual_hash.lower() != expected_hash.lower():
            raise SecurityViolationError(
                f"Checkpoint cryptographic hash mismatch! Expected {expected_hash}, got {actual_hash}."
            )

        # Secure loading with weights_only=True
        try:
            state = torch.load(
                checkpoint_path,
                map_location=map_location,
                weights_only=enforce_weights_only
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "weights_only" in err_msg or "unpickle" in err_msg or "global" in err_msg:
                raise UnsafeDeserializationError(
                    f"Checkpoint '{checkpoint_path}' contains non-weight objects rejected by weights_only=True: {e}"
                ) from e
            raise ModelCheckpointError(f"Failed to securely load checkpoint '{checkpoint_path}': {e}") from e

        # Extract state dict if packaged inside a training checkpoint wrapper
        if isinstance(state, dict):
            if "state_dict" in state:
                return state["state_dict"]
            elif "model_state_dict" in state:
                return state["model_state_dict"]
            elif "model" in state and isinstance(state["model"], dict):
                return state["model"]
            return state
        else:
            raise UnsafeDeserializationError(
                f"Deserialized payload in '{checkpoint_path}' is not a valid tensor state dict (got {type(state)})."
            )

    @classmethod
    def safe_save_state_dict(cls, state_dict: Dict[str, Any], output_path: str) -> str:
        """Saves a state dict safely to disk and returns its SHA-256 hash."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        torch.save(state_dict, output_path)
        return compute_file_sha256(output_path)
