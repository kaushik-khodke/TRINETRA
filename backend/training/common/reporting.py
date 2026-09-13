"""
TRINETRA / SatQuery AI — Training Reporting & Visualization
Generates loss curves, metric plots, and JSON evaluation reports without fabricated metrics.
"""

import os
import json
from typing import Dict, Any, List
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for terminal execution
import matplotlib.pyplot as plt

class TrainingReporter:
    def __init__(self, run_dir: str):
        self.run_dir = run_dir
        os.makedirs(run_dir, exist_ok=True)

    def save_history(self, history: Dict[str, List[float]]) -> str:
        """Saves epoch loss and metric progression to training_history.json."""
        hist_path = os.path.join(self.run_dir, "training_history.json")
        with open(hist_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        # Generate plots
        epochs = list(range(1, len(history.get("train_loss", [])) + 1))
        if epochs:
            # 1. Loss curves
            plt.figure(figsize=(8, 5))
            plt.plot(epochs, history.get("train_loss", []), "b-o", label="Train Loss")
            if "val_loss" in history:
                plt.plot(epochs, history["val_loss"], "r--s", label="Validation Loss")
            plt.title("Training & Validation Loss")
            plt.xlabel("Epoch")
            plt.ylabel("Loss")
            plt.grid(True, linestyle=":", alpha=0.6)
            plt.legend()
            loss_plot = os.path.join(self.run_dir, "loss_curve.png")
            plt.savefig(loss_plot, dpi=200, bbox_inches="tight")
            plt.close()

            # 2. Metric curve
            if "val_metric" in history:
                plt.figure(figsize=(8, 5))
                plt.plot(epochs, history["val_metric"], "g-^", label="Validation Metric")
                plt.title("Validation Metric Progression")
                plt.xlabel("Epoch")
                plt.ylabel("Score")
                plt.grid(True, linestyle=":", alpha=0.6)
                plt.legend()
                metric_plot = os.path.join(self.run_dir, "metric_curve.png")
                plt.savefig(metric_plot, dpi=200, bbox_inches="tight")
                plt.close()

        print(f"[REPORTS] Saved history and curve plots in {self.run_dir}")
        return hist_path

    def save_evaluation(self, eval_results: Dict[str, Any], baseline_results: Dict[str, Any] = None) -> None:
        """Saves evaluation_results.json and baseline_vs_trained.json."""
        eval_path = os.path.join(self.run_dir, "evaluation_results.json")
        with open(eval_path, "w", encoding="utf-8") as f:
            json.dump(eval_results, f, indent=2)

        if baseline_results:
            comparison = {
                "baseline": baseline_results,
                "trained": eval_results,
                "summary": {}
            }
            # Compute deltas
            for k in eval_results:
                if k in baseline_results and isinstance(eval_results[k], (int, float)):
                    delta = eval_results[k] - baseline_results[k]
                    comparison["summary"][f"{k}_delta"] = round(delta, 4)
                    comparison["summary"][f"{k}_improved"] = bool(delta > 0)

            comp_path = os.path.join(self.run_dir, "baseline_vs_trained.json")
            with open(comp_path, "w", encoding="utf-8") as f:
                json.dump(comparison, f, indent=2)
            print(f"[REPORTS] Saved baseline comparison to {comp_path}")
