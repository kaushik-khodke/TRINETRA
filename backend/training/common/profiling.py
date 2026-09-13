"""
TRINETRA / SatQuery AI — Hardware Profiling & Resource Management
Configures optimal batch sizes, mixed precision, and subset targets for laptop GPUs.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class HardwareProfile:
    name: str
    target_runtime: str
    max_train_samples: int
    max_val_samples: int
    max_test_samples: int
    batch_size: int
    image_size: int
    epochs: int
    patience: int
    lr: float
    use_amp: bool
    num_workers: int
    grad_accum_steps: int

PROFILES: Dict[str, HardwareProfile] = {
    "fast": HardwareProfile(
        name="fast",
        target_runtime="~45–60 minutes on Laptop GPU",
        max_train_samples=5000,
        max_val_samples=1000,
        max_test_samples=1000,
        batch_size=32,
        image_size=128,
        epochs=5,
        patience=2,
        lr=3e-4,
        use_amp=True,
        num_workers=2 if os.name != "nt" else 0,
        grad_accum_steps=1
    ),
    "balanced": HardwareProfile(
        name="balanced",
        target_runtime="~1–2 hours on Laptop GPU (Recommended Default)",
        max_train_samples=20000,
        max_val_samples=4000,
        max_test_samples=4000,
        batch_size=32,
        image_size=224,
        epochs=10,
        patience=2,
        lr=2e-4,
        use_amp=True,
        num_workers=2 if os.name != "nt" else 0,
        grad_accum_steps=1
    ),
    "quality": HardwareProfile(
        name="quality",
        target_runtime="~3–5 hours / Extended Training",
        max_train_samples=50000,
        max_val_samples=8000,
        max_test_samples=8000,
        batch_size=16,
        image_size=224,
        epochs=20,
        patience=3,
        lr=1e-4,
        use_amp=True,
        num_workers=4 if os.name != "nt" else 0,
        grad_accum_steps=2
    )
}

def get_profile_config(profile_name: str = "balanced") -> HardwareProfile:
    """Retrieve profile config with fallback to balanced."""
    key = profile_name.lower().strip()
    if key not in PROFILES:
        print(f"[WARN] Unknown profile '{profile_name}'. Falling back to 'balanced'.")
        key = "balanced"
    return PROFILES[key]
