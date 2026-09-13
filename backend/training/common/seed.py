"""
TRINETRA / SatQuery AI — Deterministic Reproducibility
Ensures reproducible training, sampling, and evaluation splits across runs.
"""

import os
import random
import numpy as np
import torch

def set_seed(seed: int = 42) -> None:
    """Set random seed across all libraries for deterministic execution."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    print(f"[REPRODUCIBILITY] Master random seed locked to {seed}.")
