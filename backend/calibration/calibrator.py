"""
TRINETRA Statistical Calibration Engine (Stage 9)
Governed by 09_STAGE_9_CALIBRATION.md and NON_NEGOTIABLE_PRINCIPLES.md.

Implements empirical confidence calibration methods:
- Temperature Scaling (Guo et al., 2017)
- Isotonic Regression Calibration
- Platt Logistic Scaling
- Reliability Diagram Computation (ECE, MCE, Bin Statistics)
- Multi-class and Binary Brier Scores
- Class-wise Calibration Error (ECE per class)

STRICT ANTI-LEAKAGE POLICY:
Calibration parameters (T, isotonic maps, Platt weights) MUST be fit strictly
on VALIDATION data only, never on test data.
"""

from typing import Dict, List, Optional, Any, Union, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

try:
    from backend.schemas.contracts import ReliabilityDiagramData
    from backend.core.exceptions import DataLeakageError
except ImportError:
    from schemas.contracts import ReliabilityDiagramData
    from core.exceptions import DataLeakageError

try:
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def compute_brier_score(
    probs: np.ndarray,
    targets: np.ndarray,
    num_classes: Optional[int] = None
) -> float:
    """
    Computes multi-class or binary Brier calibration score:
    Multi-class: (1/N) * sum_{i=1}^N sum_{k=1}^K (p_{ik} - y_{ik})^2
    Binary:      (1/N) * sum_{i=1}^N (p_i - y_i)^2
    Range: [0.0, 2.0] for multi-class, [0.0, 1.0] for binary. Lower is better.
    """
    probs = np.asarray(probs, dtype=np.float64)
    targets = np.asarray(targets)
    n_samples = len(targets)
    if n_samples == 0:
        return 0.0

    # Binary classification / segmentation case
    if probs.ndim == 1 or (probs.ndim == 2 and probs.shape[1] == 1):
        p = probs.squeeze()
        y = targets.squeeze().astype(np.float64)
        brier = float(np.mean((p - y) ** 2))
        return round(brier, 4)

    # Multi-class case
    k = num_classes or probs.shape[1]
    # One-hot encode targets if they are 1D class indices
    if targets.ndim == 1:
        y_one_hot = np.zeros((n_samples, k), dtype=np.float64)
        for i, t in enumerate(targets):
            t_int = int(t)
            if 0 <= t_int < k:
                y_one_hot[i, t_int] = 1.0
    else:
        y_one_hot = targets.astype(np.float64)

    # Sum of squared errors across classes, averaged over samples
    brier = float(np.mean(np.sum((probs - y_one_hot) ** 2, axis=1)))
    return round(brier, 4)


class ReliabilityDiagram:
    """
    Computes empirical reliability diagrams, Expected Calibration Error (ECE),
    and Maximum Calibration Error (MCE) across confidence intervals.
    """

    @staticmethod
    def compute(
        confidences: np.ndarray,
        correctness: np.ndarray,
        n_bins: int = 10
    ) -> ReliabilityDiagramData:
        """
        Partitions confidences into n_bins equal intervals in [0, 1].
        Computes per-bin empirical accuracy, mean confidence, and sample count.
        """
        confidences = np.asarray(confidences, dtype=np.float64)
        correctness = np.asarray(correctness, dtype=np.float64)
        n_samples = len(confidences)

        if n_samples == 0:
            return ReliabilityDiagramData(
                bin_edges=list(np.linspace(0.0, 1.0, n_bins + 1)),
                bin_accuracies=[0.0] * n_bins,
                bin_confidences=[0.0] * n_bins,
                bin_counts=[0] * n_bins,
                ece=0.0,
                mce=0.0,
                brier_score=0.0
            )

        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        bin_accuracies: List[float] = []
        bin_confidences: List[float] = []
        bin_counts: List[int] = []

        ece = 0.0
        mce = 0.0

        for i in range(n_bins):
            lower = bin_edges[i]
            upper = bin_edges[i + 1]

            # Use half-open intervals [lower, upper), except for the last bin which includes 1.0
            if i == n_bins - 1:
                mask = (confidences >= lower) & (confidences <= upper)
            else:
                mask = (confidences >= lower) & (confidences < upper)

            count = int(np.sum(mask))
            bin_counts.append(count)

            if count > 0:
                bin_acc = float(np.mean(correctness[mask]))
                bin_conf = float(np.mean(confidences[mask]))
                bin_accuracies.append(round(bin_acc, 4))
                bin_confidences.append(round(bin_conf, 4))

                gap = abs(bin_acc - bin_conf)
                ece += (count / n_samples) * gap
                mce = max(mce, gap)
            else:
                bin_accuracies.append(0.0)
                bin_confidences.append(round((lower + upper) / 2.0, 4))

        brier = compute_brier_score(confidences, correctness)

        return ReliabilityDiagramData(
            bin_edges=[round(float(b), 4) for b in bin_edges],
            bin_accuracies=bin_accuracies,
            bin_confidences=bin_confidences,
            bin_counts=bin_counts,
            ece=round(float(ece), 4),
            mce=round(float(mce), 4),
            brier_score=brier
        )


def compute_classwise_ece(
    probs: np.ndarray,
    targets: np.ndarray,
    num_classes: int,
    n_bins: int = 10
) -> Dict[str, float]:
    """
    Computes class-wise Expected Calibration Error (ECE) for each class
    in a one-vs-rest manner to expose class-imbalanced overconfidence.
    """
    probs = np.asarray(probs, dtype=np.float64)
    targets = np.asarray(targets)
    class_ece = {}

    for c in range(num_classes):
        prob_c = probs[:, c]
        true_c = (targets == c).astype(np.float64)
        rel = ReliabilityDiagram.compute(prob_c, true_c, n_bins=n_bins)
        class_ece[f"class_{c}"] = rel.ece

    return class_ece


class TemperatureScaler(nn.Module):
    """
    Parametric post-hoc calibration via learnable scalar temperature T > 0.
    Softmax: p_i = exp(z_i / T) / sum_j exp(z_j / T)
    Strictly rank-preserving: accuracy does not change, but probabilities align with accuracy.
    """

    def __init__(self, init_temp: float = 1.5):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * float(init_temp))
        self._is_fitted = False

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def get_temperature(self) -> float:
        return float(self.temperature.item())

    def fit(
        self,
        val_logits: Union[torch.Tensor, np.ndarray],
        val_labels: Union[torch.Tensor, np.ndarray],
        lr: float = 0.01,
        max_iter: int = 100,
        is_binary: bool = False,
        is_val_split: bool = True
    ) -> float:
        """
        Optimizes temperature T on VALIDATION set using NLL loss.
        Raises DataLeakageError if is_val_split is False.
        """
        if not is_val_split:
            raise DataLeakageError(
                "Severe anti-leakage violation: Temperature scaling parameters must be fitted "
                "strictly on VALIDATION data, never on the test set!"
            )

        # Convert to PyTorch tensors
        if isinstance(val_logits, np.ndarray):
            logits_t = torch.from_numpy(val_logits).float()
        else:
            logits_t = val_logits.float().detach()

        if isinstance(val_labels, np.ndarray):
            labels_t = torch.from_numpy(val_labels)
        else:
            labels_t = val_labels.detach()

        if is_binary:
            criterion = nn.BCEWithLogitsLoss()
            labels_t = labels_t.float().view(-1, 1)
            logits_t = logits_t.view(-1, 1)
        else:
            criterion = nn.CrossEntropyLoss()
            labels_t = labels_t.long().view(-1)

        # Optimize T using L-BFGS
        optimizer = optim.LBFGS([self.temperature], lr=lr, max_iter=max_iter)

        def eval_loss():
            optimizer.zero_grad()
            # Constrain T > 0.05
            temp_clamped = torch.clamp(self.temperature, min=0.05, max=20.0)
            scaled_logits = logits_t / temp_clamped
            loss = criterion(scaled_logits, labels_t)
            loss.backward()
            return loss

        optimizer.step(eval_loss)

        # Final clamp
        with torch.no_grad():
            self.temperature.clamp_(min=0.05, max=20.0)

        self._is_fitted = True
        return self.get_temperature()

    def calibrate(self, logits: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Applies learned temperature to multi-class logits, returning softmax probabilities."""
        if isinstance(logits, np.ndarray):
            logits_t = torch.from_numpy(logits).float()
        else:
            logits_t = logits.float()

        with torch.no_grad():
            t = torch.clamp(self.temperature, min=0.05, max=20.0)
            scaled = logits_t / t
            probs = torch.softmax(scaled, dim=-1).cpu().numpy()
        return probs

    def calibrate_binary(self, logits: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Applies learned temperature to binary logits, returning sigmoid probabilities."""
        if isinstance(logits, np.ndarray):
            logits_t = torch.from_numpy(logits).float()
        else:
            logits_t = logits.float()

        with torch.no_grad():
            t = torch.clamp(self.temperature, min=0.05, max=20.0)
            scaled = logits_t / t
            probs = torch.sigmoid(scaled).cpu().numpy()
        return probs


class IsotonicCalibrator:
    """
    Non-parametric probability calibration via monotonic piecewise-linear mapping.
    """

    def __init__(self):
        self._calibrators: Dict[int, Any] = {}
        self._is_fitted = False
        self._is_binary = True

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def fit(
        self,
        val_probs: np.ndarray,
        val_labels: np.ndarray,
        is_val_split: bool = True
    ) -> None:
        """Fits isotonic regression models on validation probabilities."""
        if not is_val_split:
            raise DataLeakageError("Isotonic calibration must be fit strictly on validation data!")

        val_probs = np.asarray(val_probs, dtype=np.float64)
        val_labels = np.asarray(val_labels)

        if not HAS_SKLEARN:
            # Fallback identity if sklearn is missing
            self._is_fitted = True
            return

        if val_probs.ndim == 1 or (val_probs.ndim == 2 and val_probs.shape[1] == 1):
            self._is_binary = True
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            iso.fit(val_probs.flatten(), val_labels.flatten().astype(np.float64))
            self._calibrators[0] = iso
        else:
            self._is_binary = False
            num_classes = val_probs.shape[1]
            for c in range(num_classes):
                iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
                iso.fit(val_probs[:, c], (val_labels == c).astype(np.float64))
                self._calibrators[c] = iso

        self._is_fitted = True

    def calibrate(self, probs: np.ndarray) -> np.ndarray:
        """Transforms uncalibrated probabilities into monotonically calibrated values."""
        if not self._is_fitted or not HAS_SKLEARN:
            return np.asarray(probs, dtype=np.float64)

        probs = np.asarray(probs, dtype=np.float64)
        if self._is_binary:
            cal_p = self._calibrators[0].predict(probs.flatten())
            return np.clip(cal_p.reshape(probs.shape), 0.0, 1.0)
        else:
            calibrated_cols = []
            num_classes = probs.shape[1]
            for c in range(num_classes):
                col = self._calibrators[c].predict(probs[:, c])
                calibrated_cols.append(col)
            out = np.column_stack(calibrated_cols)
            # Re-normalize across classes so sum = 1.0
            row_sums = out.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1e-8
            return out / row_sums


class PlattScaler:
    """
    Parametric logistic calibration fitting sigmoid(A * score + B).
    """

    def __init__(self):
        self._model = None
        self._is_fitted = False

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def fit(
        self,
        val_scores: np.ndarray,
        val_labels: np.ndarray,
        is_val_split: bool = True
    ) -> None:
        """Fits logistic regression on validation decision scores."""
        if not is_val_split:
            raise DataLeakageError("Platt scaling must be fit strictly on validation data!")

        if not HAS_SKLEARN:
            self._is_fitted = True
            return

        scores = np.asarray(val_scores, dtype=np.float64).reshape(-1, 1)
        labels = np.asarray(val_labels).ravel()

        lr = LogisticRegression(solver="lbfgs")
        lr.fit(scores, labels)
        self._model = lr
        self._is_fitted = True

    def calibrate(self, scores: np.ndarray) -> np.ndarray:
        """Transforms decision scores to calibrated posterior probabilities."""
        if not self._is_fitted or not HAS_SKLEARN or self._model is None:
            # Fallback sigmoid
            s = np.asarray(scores, dtype=np.float64)
            return 1.0 / (1.0 + np.exp(-s))

        scores = np.asarray(scores, dtype=np.float64).reshape(-1, 1)
        probs = self._model.predict_proba(scores)[:, 1]
        return probs
