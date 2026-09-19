"""
TRINETRA / SatQuery AI — Checkpoint Management & Deployment
Manages saving best_model.pt, last_model.pt, config.json, and deployment to SatQuery models.
"""

import os
import json
import shutil
from typing import Dict, Any, Optional
import torch

class CheckpointManager:
    def __init__(self, run_dir: str, model_name: str):
        self.run_dir = run_dir
        self.model_name = model_name
        os.makedirs(run_dir, exist_ok=True)
        self.best_model_path = os.path.join(run_dir, "best_model.pt")
        self.last_model_path = os.path.join(run_dir, "last_model.pt")
        self.config_path = os.path.join(run_dir, "config.json")

    def save_checkpoint(self, model: torch.nn.Module, epoch: int, is_best: bool, metric_val: float) -> None:
        """Saves current epoch checkpoint and best checkpoint."""
        torch.save(model.state_dict(), self.last_model_path)
        if is_best:
            torch.save(model.state_dict(), self.best_model_path)
            print(f"[CHECKPOINT] Saved new best model to {self.best_model_path} (Metric: {metric_val:.4f})")

    def save_config(self, config_dict: Dict[str, Any]) -> str:
        """Saves comprehensive configuration for reproducibility."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)
        print(f"[CONFIG] Saved run config to {self.config_path}")
        return self.config_path

    def deploy_to_backend(self, target_checkpoint_key: str, backend_root: Optional[str] = None) -> str:
        """
        Deploys best_model.pt directly to backend/models/checkpoints/<key>/model.pt
        for live inference by SatQuery backend specialists.
        """
        if not os.path.exists(self.best_model_path):
            raise FileNotFoundError(f"Cannot deploy: {self.best_model_path} does not exist.")

        if backend_root is None:
            backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        dest_dir = os.path.join(backend_root, "models", "checkpoints", target_checkpoint_key)
        os.makedirs(dest_dir, exist_ok=True)
        dest_file = os.path.join(dest_dir, "model.pt")
        shutil.copyfile(self.best_model_path, dest_file)

        if os.path.exists(self.config_path):
            shutil.copyfile(self.config_path, os.path.join(dest_dir, "config.json"))

        print(f"[DEPLOY] Exported trained weights directly to: {dest_file}")
        return dest_file
