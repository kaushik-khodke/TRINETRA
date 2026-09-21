"""
TRINETRA / SatQuery AI — Hyperspectral Failure Analysis Engine
Module: backend/training/06_hyperspectral/failure_analysis.py

Diagnoses spectral and spatial misclassifications in hyperspectral evaluation:
1. rare_class_starvation (insufficient training representation)
2. spatial_boundary_confusion (mixed pixel boundary proximity)
3. spectral_metamerism (high spectral angle / cosine similarity between classes)
4. water_absorption_noise (high noise in atmospheric absorption bands ~940nm, ~1400nm, ~1900nm)
5. model_divergence (decision boundary breakdown)

Returns typed FailureCase contracts from schemas.contracts.
"""

import os
import sys
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from schemas.contracts import FailureCase


def spectral_angle_mapper(s1: np.ndarray, s2: np.ndarray) -> float:
    """
    Computes the Spectral Angle Mapper (SAM) in radians between two 1D spectral vectors.
    Range: [0, pi]. Lower values indicate higher spectral shape similarity.
    """
    v1 = np.asarray(s1, dtype=np.float64).ravel()
    v2 = np.asarray(s2, dtype=np.float64).ravel()
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 < 1e-10 or norm2 < 1e-10:
        return float(np.pi / 2)
    cos_theta = np.clip(np.dot(v1, v2) / (norm1 * norm2), -1.0, 1.0)
    return float(np.arccos(cos_theta))


class HyperspectralFailureAnalysisEngine:
    """
    Analytical autopsy engine for Hyperspectral remote-sensing models.
    """

    DEFAULT_CLASSES = [
        "Alfalfa", "Corn-notill", "Corn-mintill", "Corn", "Grass-pasture",
        "Grass-trees", "Grass-pasture-mowed", "Hay-windrowed", "Oats",
        "Soybean-notill", "Soybean-mintill", "Soybean-clean", "Wheat",
        "Woods", "Buildings-Grass-Trees-Drives", "Stone-Steel-Towers"
    ]

    @classmethod
    def diagnose_sample(
        cls,
        sample_id: str,
        pixel_spectrum: np.ndarray,
        coords: Tuple[int, int],
        pred_class: int,
        gt_class: int,
        gt_map: Optional[np.ndarray] = None,
        train_class_counts: Optional[Dict[int, int]] = None,
        class_spectral_profiles: Optional[Dict[int, np.ndarray]] = None,
        wavelengths: Optional[np.ndarray] = None,
        class_names: Optional[List[str]] = None
    ) -> Optional[FailureCase]:
        """
        Diagnoses a single misclassified HSI pixel sample.
        Returns FailureCase if misclassified, else None.
        """
        if pred_class == gt_class:
            return None

        classes = class_names if class_names is not None else cls.DEFAULT_CLASSES
        pred_name = classes[pred_class] if pred_class < len(classes) else f"Class_{pred_class}"
        gt_name = classes[gt_class] if gt_class < len(classes) else f"Class_{gt_class}"
        r, c = coords
        spec = np.asarray(pixel_spectrum, dtype=np.float32).ravel()

        # 1. Rare Class Starvation Check
        if train_class_counts is not None:
            train_cnt = train_class_counts.get(gt_class, 0)
            if train_cnt < 50:
                return FailureCase(
                    case_id=f"fail-hsi-{sample_id}-{uuid.uuid4().hex[:6]}",
                    asset_id=f"pixel_r{r}_c{c}",
                    expected_output=gt_name,
                    actual_output=pred_name,
                    error_category="rare_class_starvation",
                    severity="high" if train_cnt < 20 else "medium",
                    explanation=(
                        f"Ground truth class '{gt_name}' suffered from training data starvation "
                        f"({train_cnt} training samples), leading to misclassification as '{pred_name}'."
                    ),
                    mitigation="Apply class-frequency focal loss weighting or synthetic spectral SMOTE augmentation."
                )

        # 2. Spatial Boundary / Mixed-Pixel Confusion Check
        if gt_map is not None:
            h, w = gt_map.shape
            r_min = max(0, r - 1)
            r_max = min(h, r + 2)
            c_min = max(0, c - 1)
            c_max = min(w, c + 2)
            local_window = gt_map[r_min:r_max, c_min:c_max]
            # If multiple classes in 3x3 window, this is a boundary mixed pixel
            unique_in_window = np.unique(local_window)
            if len(unique_in_window) > 1:
                return FailureCase(
                    case_id=f"fail-hsi-{sample_id}-{uuid.uuid4().hex[:6]}",
                    asset_id=f"pixel_r{r}_c{c}",
                    expected_output=gt_name,
                    actual_output=pred_name,
                    error_category="spatial_boundary_confusion",
                    severity="medium",
                    explanation=(
                        f"Pixel at ({r}, {c}) is located on a spatial class transition boundary "
                        f"(3x3 window contains classes {unique_in_window.tolist()}), causing mixed-pixel spectral blur."
                    ),
                    mitigation="Use higher spatial resolution sensor or soft sub-pixel unmixing endmember decomposition."
                )

        # 3. Spectral Metamerism Check (True vs Pred class profile similarity)
        if class_spectral_profiles is not None:
            true_profile = class_spectral_profiles.get(gt_class)
            pred_profile = class_spectral_profiles.get(pred_class)

            if true_profile is not None and pred_profile is not None:
                inter_class_sam = spectral_angle_mapper(true_profile, pred_profile)
                if inter_class_sam < 0.08:  # Highly similar spectral signature
                    return FailureCase(
                        case_id=f"fail-hsi-{sample_id}-{uuid.uuid4().hex[:6]}",
                        asset_id=f"pixel_r{r}_c{c}",
                        expected_output=gt_name,
                        actual_output=pred_name,
                        error_category="spectral_metamerism",
                        severity="high",
                        explanation=(
                            f"Classes '{gt_name}' and '{pred_name}' exhibit extreme spectral metamerism "
                            f"(Spectral Angle Mapper: {inter_class_sam:.4f} rad < 0.08 rad limit)."
                        ),
                        mitigation="Incorporate spatial context CNN/ViT representations or narrow derivative spectroscopy."
                    )

        # 4. Atmospheric Water Vapor Absorption Noise Check
        if wavelengths is not None and len(wavelengths) == len(spec):
            wl = np.asarray(wavelengths).ravel()
            water_mask = (np.abs(wl - 940) < 30) | (np.abs(wl - 1400) < 40) | (np.abs(wl - 1900) < 40)
            clean_mask = ~water_mask

            if np.sum(water_mask) > 3 and np.sum(clean_mask) > 10:
                water_std = float(np.std(spec[water_mask]))
                clean_std = float(np.std(spec[clean_mask]))
                if water_std > 2.5 * (clean_std + 1e-4):
                    return FailureCase(
                        case_id=f"fail-hsi-{sample_id}-{uuid.uuid4().hex[:6]}",
                        asset_id=f"pixel_r{r}_c{c}",
                        expected_output=gt_name,
                        actual_output=pred_name,
                        error_category="water_absorption_noise",
                        severity="medium",
                        explanation=(
                            f"High spectral variance ({water_std:.3f} vs {clean_std:.3f} in window) "
                            f"concentrated in atmospheric water absorption bands (940nm, 1400nm, 1900nm)."
                        ),
                        mitigation="Apply atmospheric correction (e.g. FLAASH / ATCOR) or prune noisy water absorption bands."
                    )

        # 5. Default Model Divergence
        return FailureCase(
            case_id=f"fail-hsi-{sample_id}-{uuid.uuid4().hex[:6]}",
            asset_id=f"pixel_r{r}_c{c}",
            expected_output=gt_name,
            actual_output=pred_name,
            error_category="model_divergence",
            severity="low",
            explanation=(
                f"Model misclassified pixel at ({r}, {c}) as '{pred_name}' instead of '{gt_name}'. "
                "Feature representation collapsed or fell outside established class clusters."
            ),
            mitigation="Increase network receptive field depth or expand training epochs with cosine decay."
        )

    @classmethod
    def diagnose_dataset(
        cls,
        preds: np.ndarray,
        targets: np.ndarray,
        coords: List[Tuple[int, int]],
        spectra: np.ndarray,
        gt_map: Optional[np.ndarray] = None,
        train_class_counts: Optional[Dict[int, int]] = None,
        wavelengths: Optional[np.ndarray] = None,
        class_names: Optional[List[str]] = None,
        max_cases: int = 50
    ) -> Dict[str, Any]:
        """
        Runs comprehensive failure analysis across a test dataset.
        """
        preds = np.asarray(preds).ravel()
        targets = np.asarray(targets).ravel()
        total_samples = len(targets)

        # Precompute mean class profiles from provided spectra
        unique_classes = np.unique(targets)
        class_profiles = {}
        for c in unique_classes:
            c_mask = (targets == c)
            if np.any(c_mask):
                class_profiles[int(c)] = np.mean(spectra[c_mask], axis=0)

        failure_cases: List[FailureCase] = []
        category_counts: Dict[str, int] = {}
        confusion_pairs: Dict[str, int] = {}
        misclassified_count = 0

        for i in range(total_samples):
            p = int(preds[i])
            t = int(targets[i])
            if p == t:
                continue

            misclassified_count += 1
            pair_key = f"{t}->{p}"
            confusion_pairs[pair_key] = confusion_pairs.get(pair_key, 0) + 1

            if len(failure_cases) < max_cases:
                coord = coords[i] if i < len(coords) else (0, 0)
                spec = spectra[i] if i < len(spectra) else np.zeros(10)
                fc = cls.diagnose_sample(
                    sample_id=str(i),
                    pixel_spectrum=spec,
                    coords=coord,
                    pred_class=p,
                    gt_class=t,
                    gt_map=gt_map,
                    train_class_counts=train_class_counts,
                    class_spectral_profiles=class_profiles,
                    wavelengths=wavelengths,
                    class_names=class_names
                )
                if fc is not None:
                    cat = fc.error_category
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                    failure_cases.append(fc)

        # Sort worst confusion pairs
        sorted_pairs = sorted(confusion_pairs.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_samples": total_samples,
            "misclassified_count": misclassified_count,
            "error_rate": round(misclassified_count / (total_samples + 1e-8), 4),
            "category_distribution": category_counts,
            "worst_confusion_pairs": dict(sorted_pairs),
            "sample_failure_cases": [fc.model_dump() for fc in failure_cases]
        }
