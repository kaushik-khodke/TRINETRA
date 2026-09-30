"""
TRINETRA — Out-of-Distribution & Sensor Robustness Evaluator
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)

Evaluates model resilience and uncertainty degradation under realistic remote sensing corruptions:
1. Gaussian thermal sensor noise
2. Atmospheric optical defocus blur
3. Cloud occlusion & shadow masking
4. Solar glare contrast attenuation
5. SAR multiplicative radar speckle
6. Hyperspectral detector band dropout
Computes Robustness Degradation Ratio (RDR) and validates uncertainty monotonicity.
"""

import numpy as np
from enum import Enum
from typing import Dict, Any, List, Callable, Tuple, Optional


class CorruptionType(str, Enum):
    GAUSSIAN_NOISE = "gaussian_noise"
    DEFOCUS_BLUR = "defocus_blur"
    CONTRAST_REDUCTION = "contrast_reduction"
    CLOUD_OCCLUSION = "cloud_occlusion"
    SAR_SPECKLE = "sar_speckle"
    BAND_DROPOUT = "band_dropout"


class RobustnessEvaluator:
    """Applies controlled physical corruptions and measures degradation curves and uncertainty monotonicity."""

    @classmethod
    def apply_corruption(
        cls,
        raster: np.ndarray,
        corruption: CorruptionType,
        severity: float = 0.5,
        seed: Optional[int] = 42
    ) -> np.ndarray:
        """
        Applies a physically grounded sensor corruption at severity [0.0, 1.0].
        Input raster can be 2D (H, W), 3D (H, W, C), or 3D HSI cube (H, W, B).
        """
        if seed is not None:
            np.random.seed(seed)

        severity = float(np.clip(severity, 0.0, 1.0))
        if severity == 0.0:
            return raster.copy()

        out = raster.astype(np.float32).copy()
        orig_dtype = raster.dtype
        is_uint8 = np.issubdtype(orig_dtype, np.integer) and raster.max() > 1.0

        if corruption == CorruptionType.GAUSSIAN_NOISE:
            # Additive sensor thermal noise
            sigma = severity * (40.0 if is_uint8 else 0.15)
            noise = np.random.normal(0.0, sigma, out.shape)
            out = out + noise

        elif corruption == CorruptionType.DEFOCUS_BLUR:
            # Atmospheric turbulence / lens defocus
            ksize = int(1 + 2 * int(severity * 4))  # 3, 5, 7, 9
            h, w = out.shape[:2]
            # Fast box blur approximation
            pad = ksize // 2
            if out.ndim == 2:
                padded = np.pad(out, pad, mode="reflect")
                out_blur = np.zeros_like(out)
                for di in range(-pad, pad + 1):
                    for dj in range(-pad, pad + 1):
                        out_blur += padded[pad + di: pad + di + h, pad + dj: pad + dj + w]
                out = out_blur / (ksize * ksize)
            elif out.ndim == 3:
                padded = np.pad(out, ((pad, pad), (pad, pad), (0, 0)), mode="reflect")
                out_blur = np.zeros_like(out)
                for di in range(-pad, pad + 1):
                    for dj in range(-pad, pad + 1):
                        out_blur += padded[pad + di: pad + di + h, pad + dj: pad + dj + w, :]
                out = out_blur / (ksize * ksize)

        elif corruption == CorruptionType.CONTRAST_REDUCTION:
            # Atmospheric haze and contrast reduction
            mean_val = np.mean(out)
            factor = 1.0 - (0.75 * severity)
            out = mean_val + (out - mean_val) * factor

        elif corruption == CorruptionType.CLOUD_OCCLUSION:
            # Cloud occlusion mask: patches of high reflectance white haze
            h, w = out.shape[:2]
            mask_size = int(min(h, w) * (0.2 + 0.6 * severity))
            y0 = np.random.randint(0, max(1, h - mask_size))
            x0 = np.random.randint(0, max(1, w - mask_size))
            cloud_val = 255.0 if is_uint8 else 1.0
            alpha = 0.4 + 0.5 * severity
            if out.ndim == 2:
                out[y0:y0+mask_size, x0:x0+mask_size] = (
                    (1.0 - alpha) * out[y0:y0+mask_size, x0:x0+mask_size] + alpha * cloud_val
                )
            elif out.ndim == 3:
                out[y0:y0+mask_size, x0:x0+mask_size, :] = (
                    (1.0 - alpha) * out[y0:y0+mask_size, x0:x0+mask_size, :] + alpha * cloud_val
                )

        elif corruption == CorruptionType.SAR_SPECKLE:
            # Multiplicative Rayleigh / Gamma radar speckle
            variance = 0.1 + (0.5 * severity)
            speckle = np.random.gamma(shape=1.0 / variance, scale=variance, size=out.shape)
            out = out * speckle

        elif corruption == CorruptionType.BAND_DROPOUT:
            # Dead sensor bands (e.g. hyperspectral or multispectral line dropout)
            if out.ndim == 3:
                channels = out.shape[2]
                drop_count = max(1, int(channels * 0.3 * severity))
                drop_indices = np.random.choice(channels, drop_count, replace=False)
                out[:, :, drop_indices] = 0.0

        if is_uint8:
            out = np.clip(out, 0.0, 255.0).astype(orig_dtype)

        return out

    @classmethod
    def evaluate_robustness(
        cls,
        eval_fn: Callable[[np.ndarray], Tuple[float, float]],
        clean_inputs: List[np.ndarray],
        corruption: CorruptionType,
        severities: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Executes eval_fn(corrupted_input) -> (metric_score, uncertainty_score).
        Calculates:
        - Baseline clean score and uncertainty
        - Degradation across severities [0.25, 0.50, 0.75, 1.0]
        - Robustness Degradation Ratio (RDR) = final_score / clean_score
        - Uncertainty Monotonicity: verifies uncertainty increases as corruption intensifies
        """
        levels = severities or [0.0, 0.25, 0.50, 0.75, 1.0]
        results_by_level = []

        for sev in levels:
            scores = []
            uncertainties = []
            for item in clean_inputs:
                corrupted = cls.apply_corruption(item, corruption, severity=sev)
                score, unc = eval_fn(corrupted)
                scores.append(score)
                uncertainties.append(unc)

            mean_score = float(np.mean(scores))
            mean_unc = float(np.mean(uncertainties))
            results_by_level.append({
                "severity": sev,
                "mean_score": round(mean_score, 4),
                "mean_uncertainty": round(mean_unc, 4)
            })

        clean_score = results_by_level[0]["mean_score"]
        severest_score = results_by_level[-1]["mean_score"]
        rdr = round(severest_score / max(1e-6, clean_score), 4) if clean_score > 0 else 0.0

        # Check uncertainty monotonicity (did uncertainty strictly or non-decreasingly grow?)
        unc_curve = [r["mean_uncertainty"] for r in results_by_level]
        is_monotonic = all(unc_curve[i] <= unc_curve[i+1] + 0.05 for i in range(len(unc_curve) - 1))

        return {
            "corruption_type": corruption.value,
            "clean_score": clean_score,
            "severest_score": severest_score,
            "robustness_degradation_ratio": rdr,
            "uncertainty_monotonic": is_monotonic,
            "severity_curve": results_by_level
        }
