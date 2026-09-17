"""
TRINETRA Confidence Semantics & Multi-Source Uncertainty Engine (Stage 9)
Governed by 09_STAGE_9_CALIBRATION.md and NON_NEGOTIABLE_PRINCIPLES.md.

Disambiguates confidence semantics and separates uncertainty into orthogonal sources:
1. Aleatoric Uncertainty (data noise, inherent boundary ambiguity, Shannon entropy)
2. Epistemic Uncertainty (model unfamiliarity, out-of-distribution distance, MC Dropout)
3. Data-Quality Uncertainty (cloud cover, sensor saturation, shadows, low dynamic range)
4. Registration Uncertainty (geometric misalignment, spatial coregistration offset)

CRITICAL RULE:
Always expose data-quality warnings separately from model confidence so operators
can distinguish poor satellite acquisition from model deficiency.
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import numpy as np

try:
    from backend.schemas.contracts import UncertaintyReport
except ImportError:
    from schemas.contracts import UncertaintyReport


class ConfidenceSemantics(str, Enum):
    """Explicitly disambiguates what a numerical confidence value signifies."""
    PROBABILITY_CLASS_CORRECTNESS = "probability_class_correctness"
    PROBABILITY_PIXEL_CORRECTNESS = "probability_pixel_correctness"
    PROBABILITY_REGION_DETECTION = "probability_region_detection"


class UncertaintyDecompositionEngine:
    """
    Decomposes total predictive uncertainty into aleatoric, epistemic,
    data-quality, and spatial registration components.
    """

    @staticmethod
    def compute_aleatoric_uncertainty(probs: np.ndarray) -> float:
        """
        Computes aleatoric uncertainty from prediction entropy.
        Normalized Shannon Entropy in [0.0, 1.0].
        0.0 = total certainty (one-hot), 1.0 = maximum ambiguity (uniform distribution).
        """
        probs = np.asarray(probs, dtype=np.float64).flatten()
        eps = 1e-12

        # Binary single probability case
        if len(probs) == 1:
            p = float(np.clip(probs[0], eps, 1.0 - eps))
            # Binary entropy normalized by log(2)
            ent = -(p * np.log2(p) + (1.0 - p) * np.log2(1.0 - p))
            return float(round(np.clip(ent, 0.0, 1.0), 4))

        k = len(probs)
        if k <= 1:
            return 0.0

        p = np.clip(probs, eps, 1.0)
        p = p / np.sum(p)
        entropy = -np.sum(p * np.log(p))
        max_entropy = np.log(k)

        normalized_entropy = float(entropy / (max_entropy + eps))
        return float(round(np.clip(normalized_entropy, 0.0, 1.0), 4))

    @staticmethod
    def compute_epistemic_uncertainty(
        mc_predictions: Optional[np.ndarray] = None,
        feature_vector: Optional[np.ndarray] = None,
        reference_centroids: Optional[np.ndarray] = None,
        top_prob: float = 1.0,
        second_prob: float = 0.0
    ) -> float:
        """
        Quantifies epistemic (model) uncertainty:
        - If MC Dropout samples are provided: variance across passes.
        - If feature vector and reference centroids are provided: normalized Euclidean/Cosine distance.
        - Fallback: margin gap (1.0 - (top_prob - second_prob)).
        """
        if mc_predictions is not None and len(mc_predictions) > 1:
            # Variance across stochastic forward passes
            var = np.var(mc_predictions, axis=0)
            # Normalize variance: maximum variance of Bernoulli is 0.25
            mean_var = float(np.mean(var))
            epistemic = float(np.clip(mean_var / 0.25, 0.0, 1.0))
            return round(epistemic, 4)

        if feature_vector is not None and reference_centroids is not None:
            # Normalized minimum distance to training distribution centroids
            feat = feature_vector.flatten()
            dists = [np.linalg.norm(feat - c) for c in reference_centroids]
            min_dist = float(min(dists)) if dists else 1.0
            # S-curve normalization into [0, 1]
            epistemic = float(1.0 - np.exp(-min_dist / 10.0))
            return round(float(np.clip(epistemic, 0.0, 1.0)), 4)

        # Margin-based heuristic fallback
        margin = max(0.0, top_prob - second_prob)
        return round(float(np.clip(1.0 - margin, 0.0, 1.0)), 4)

    @staticmethod
    def compute_data_quality_uncertainty(
        raster_data: Optional[np.ndarray] = None,
        nodata_value: Optional[float] = None
    ) -> Tuple[float, List[str]]:
        """
        Analyzes satellite raster acquisition quality:
        - Cloud cover (excessive brightness in optical channels)
        - Shadow occlusion (near-zero reflectance across all bands)
        - Sensor dynamic range clipping / saturation
        - Nodata fill fraction
        Returns: (quality_uncertainty in [0, 1], quality_flags).
        """
        if raster_data is None or raster_data.size == 0:
            return 0.0, []

        arr = np.asarray(raster_data, dtype=np.float32)
        flags: List[str] = []
        penalty = 0.0

        # Nodata inspection
        if nodata_value is not None:
            nodata_mask = (arr == nodata_value)
            nodata_frac = float(np.mean(nodata_mask))
            if nodata_frac > 0.05:
                flags.append(f"HIGH_NODATA_RATIO_{int(nodata_frac*100)}PCT")
                penalty += min(0.4, nodata_frac)

        # Dynamic range and saturation
        v_min, v_max = float(np.min(arr)), float(np.max(arr))
        spread = v_max - v_min
        if spread < 1e-4:
            flags.append("ZERO_DYNAMIC_RANGE_BLANK_RASTER")
            penalty += 0.8
        elif spread < 10.0 and v_max > 100:
            flags.append("SEVERE_CONTRAST_COMPRESSION")
            penalty += 0.3

        # Detect clipping / saturation at 255 (uint8) or 65535 (uint16)
        sat_high = np.mean(arr >= 254.0) if v_max <= 256.0 else np.mean(arr >= 65500.0)
        if sat_high > 0.15:
            flags.append(f"SENSOR_SATURATION_{int(sat_high*100)}PCT")
            penalty += min(0.35, sat_high)

        # Extreme cloud reflection proxy (top 5% brightness in optical)
        if v_max > 240.0 and np.mean(arr > 240.0) > 0.30:
            flags.append("POTENTIAL_CLOUD_OR_HAZE_OCCLUSION")
            penalty += 0.3

        # Extreme deep shadow proxy
        if np.mean(arr < 5.0) > 0.25:
            flags.append("EXTREME_TERRAIN_OR_CLOUD_SHADOW")
            penalty += 0.25

        quality_uncertainty = float(round(np.clip(penalty, 0.0, 1.0), 4))
        return quality_uncertainty, flags

    @staticmethod
    def compute_registration_uncertainty(
        alignment_report: Optional[Dict[str, Any]] = None,
        estimated_offset_pixels: float = 0.0
    ) -> Tuple[float, List[str]]:
        """
        Quantifies spatial alignment uncertainty between multi-temporal or multi-modal rasters.
        """
        flags: List[str] = []
        if alignment_report is None:
            if estimated_offset_pixels > 0.0:
                score = min(1.0, estimated_offset_pixels / 5.0)
                if score > 0.2:
                    flags.append(f"SPATIAL_OFFSET_{estimated_offset_pixels:.1f}PX")
                return round(score, 4), flags
            return 0.0, []

        is_aligned = alignment_report.get("is_aligned", True)
        dx = abs(alignment_report.get("pixel_offset_x", 0.0))
        dy = abs(alignment_report.get("pixel_offset_y", 0.0))
        offset = float(np.sqrt(dx**2 + dy**2))

        if not is_aligned:
            flags.append("UNALIGNED_SOURCE_RASTERS")
            return 0.75, flags

        if offset > 1.5:
            flags.append(f"SUBPIXEL_REGISTRATION_DRIFT_{offset:.1f}PX")
            reg_score = min(0.6, offset / 4.0)
            return round(reg_score, 4), flags

        return 0.0, []

    @classmethod
    def decompose(
        cls,
        probs: np.ndarray,
        semantics: ConfidenceSemantics = ConfidenceSemantics.PROBABILITY_CLASS_CORRECTNESS,
        raster_data: Optional[np.ndarray] = None,
        alignment_report: Optional[Dict[str, Any]] = None,
        mc_predictions: Optional[np.ndarray] = None,
        feature_vector: Optional[np.ndarray] = None,
        reference_centroids: Optional[np.ndarray] = None
    ) -> UncertaintyReport:
        """
        Assembles complete decomposed UncertaintyReport with explicit semantics
        and isolated data-quality indicators.
        """
        p_arr = np.asarray(probs, dtype=np.float64).flatten()
        if len(p_arr) == 0:
            top_prob = 0.0
            second_prob = 0.0
        elif len(p_arr) == 1:
            top_prob = float(p_arr[0])
            second_prob = 1.0 - top_prob
        else:
            sorted_p = np.sort(p_arr)[::-1]
            top_prob = float(sorted_p[0])
            second_prob = float(sorted_p[1]) if len(sorted_p) > 1 else 0.0

        # 1. Aleatoric uncertainty (entropy)
        aleatoric = cls.compute_aleatoric_uncertainty(p_arr)

        # 2. Epistemic uncertainty (model familiarization)
        epistemic = cls.compute_epistemic_uncertainty(
            mc_predictions=mc_predictions,
            feature_vector=feature_vector,
            reference_centroids=reference_centroids,
            top_prob=top_prob,
            second_prob=second_prob
        )

        # 3. Data-quality uncertainty (clouds, saturation, shadows)
        data_qual, qual_flags = cls.compute_data_quality_uncertainty(raster_data)

        # 4. Spatial registration uncertainty
        reg_unc, reg_flags = cls.compute_registration_uncertainty(alignment_report)
        all_flags = qual_flags + reg_flags

        return UncertaintyReport(
            confidence_semantics=str(semantics.value if isinstance(semantics, ConfidenceSemantics) else semantics),
            overall_confidence=round(top_prob, 4),
            aleatoric_uncertainty=aleatoric,
            epistemic_uncertainty=epistemic,
            data_quality_uncertainty=data_qual,
            registration_uncertainty=reg_unc,
            quality_flags=all_flags
        )
