"""
SatQuery AI / TRINETRA — Hyperspectral Spectral Physics & Anomaly Engine
Calculates true spectral curves, absorption dips, covariance-grounded Reed-Xiaoli (RX)
anomaly maps, and Spectral Angle Mapper (SAM) similarities from genuine 3D HSI cubes.
Zero simulation. Pure radiometric physics.
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from geospatial.hsi_reader import HsiCubeData

class SpectralPhysicsEngine:
    """Computes genuine physical spectroscopic metrics across hyperspectral data cubes."""

    @staticmethod
    def extract_spectral_signature(
        hsi_cube: HsiCubeData,
        roi_box: Optional[Tuple[float, float, float, float]] = None,
        point_yx: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Extracts real spectral reflectance signature.
        roi_box: normalized [ymin, xmin, ymax, xmax] in [0, 1] range.
        point_yx: absolute pixel (row, col).
        """
        cube = hsi_cube.cube  # (H, W, Bands)
        h, w, b = cube.shape

        if point_yx is not None:
            r = max(0, min(h - 1, point_yx[0]))
            c = max(0, min(w - 1, point_yx[1]))
            mean_sig = cube[r, c, :].astype(float)
            std_sig = np.zeros_like(mean_sig)
            num_pixels = 1
        elif roi_box is not None:
            ymin, xmin, ymax, xmax = roi_box
            y1, y2 = int(ymin * h), max(int(ymin * h) + 1, int(ymax * h))
            x1, x2 = int(xmin * w), max(int(xmin * w) + 1, int(xmax * w))
            y1, y2 = max(0, y1), min(h, y2)
            x1, x2 = max(0, x1), min(w, x2)
            region = cube[y1:y2, x1:x2, :]
            mean_sig = np.mean(region, axis=(0, 1)).astype(float)
            std_sig = np.std(region, axis=(0, 1)).astype(float)
            num_pixels = (y2 - y1) * (x2 - x1)
        else:
            # Whole scene average
            mean_sig = np.mean(cube, axis=(0, 1)).astype(float)
            std_sig = np.std(cube, axis=(0, 1)).astype(float)
            num_pixels = h * w

        wavelengths = [round(float(w), 1) for w in hsi_cube.wavelengths]
        reflectances = [round(float(r), 4) for r in mean_sig]
        std_devs = [round(float(s), 4) for s in std_sig]

        # Identify physical absorption dips (local minima in spectral reflectance)
        absorption_dips = []
        for i in range(1, b - 1):
            if mean_sig[i] < mean_sig[i - 1] and mean_sig[i] < mean_sig[i + 1]:
                wl = wavelengths[i]
                depth = float(0.5 * (mean_sig[i - 1] + mean_sig[i + 1]) - mean_sig[i])
                if depth > 0.015:
                    feature = "General Absorption"
                    if 650 <= wl <= 690:
                        feature = "Chlorophyll Red Absorption Dip (Photosynthetic Pigment)"
                    elif 940 <= wl <= 980:
                        feature = "Atmospheric / Liquid Water Vapor Absorption Band"
                    elif 1180 <= wl <= 1220:
                        feature = "Weak Liquid Water Absorption Band"
                    elif 1380 <= wl <= 1450:
                        feature = "Hydroxyl / Strong Atmospheric Water Vapor Attenuation"
                    elif 1900 <= wl <= 1960:
                        feature = "Clay / Strong Water Absorption Band"
                    elif 2180 <= wl <= 2240:
                        feature = "Al-OH Mineral / Clay Mineral Absorption Feature"
                    elif 2300 <= wl <= 2360:
                        feature = "Carbonate / Mg-OH Mineral Feature"

                    absorption_dips.append({
                        "wavelength_nm": wl,
                        "reflectance": reflectances[i],
                        "dip_depth": round(depth, 4),
                        "diagnostic_feature": feature
                    })

        # Sort by dip prominence
        absorption_dips = sorted(absorption_dips, key=lambda x: x["dip_depth"], reverse=True)[:5]

        return {
            "wavelengths_nm": wavelengths,
            "mean_reflectance": reflectances,
            "std_deviation": std_devs,
            "sample_count": num_pixels,
            "absorption_features": absorption_dips,
            "peak_reflectance_nm": wavelengths[int(np.argmax(mean_sig))],
            "min_reflectance_nm": wavelengths[int(np.argmin(mean_sig))]
        }

    @staticmethod
    def compute_rx_anomaly(
        hsi_cube: HsiCubeData,
        subsample_step: int = 2
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Genuine Reed-Xiaoli (RX) Anomaly Detection:
        r(x) = (x - mu)^T * Sigma^-1 * (x - mu)
        Computed from actual spectral covariance of the scene.
        Returns:
            anomaly_map: normalized [0.0, 1.0] float array (H, W)
            anomaly_boxes: bounding boxes for salient anomalous clusters
        """
        cube = hsi_cube.cube  # (H, W, Bands)
        h, w, b = cube.shape

        # Subsample pixels for background statistics estimation (covariance)
        sub_pixels = cube[::subsample_step, ::subsample_step, :].reshape(-1, b)
        mu = np.mean(sub_pixels, axis=0)

        # Centered covariance
        diff = sub_pixels - mu
        cov = np.cov(diff, rowvar=False)

        # Regularized matrix inversion to avoid singular covariance
        reg = 1e-4 * np.trace(cov) / b
        cov_reg = cov + np.eye(b) * reg
        try:
            inv_cov = np.linalg.inv(cov_reg)
        except np.linalg.LinAlgError:
            inv_cov = np.linalg.pinv(cov_reg)

        # Compute RX score across all pixels
        all_pixels = cube.reshape(-1, b)
        x_minus_mu = all_pixels - mu

        # Quadratic form: sum( (x-mu) * (inv_cov @ (x-mu).T).T, axis=1 )
        temp = np.dot(x_minus_mu, inv_cov)
        rx_scores = np.sum(temp * x_minus_mu, axis=1)
        rx_map = rx_scores.reshape(h, w)

        # Normalize score into [0, 1] using robust 99.5th percentile
        p99 = float(np.percentile(rx_map, 99.5))
        p01 = float(np.percentile(rx_map, 1.0))
        denom = max(1e-5, p99 - p01)
        norm_map = np.clip((rx_map - p01) / denom, 0.0, 1.0).astype(np.float32)

        # Extract top anomalous clusters (pixels > 95th percentile)
        thresh = float(np.percentile(norm_map, 95.0))
        mask = norm_map >= thresh

        boxes: List[Dict[str, Any]] = []
        y_idxs, x_idxs = np.where(mask)
        if y_idxs.size > 0:
            ymin = float(np.percentile(y_idxs, 5) / h)
            ymax = float(np.percentile(y_idxs, 95) / h)
            xmin = float(np.percentile(x_idxs, 5) / w)
            xmax = float(np.percentile(x_idxs, 95) / w)

            # Ensure box dimensions
            ymin, xmin = max(0.02, ymin - 0.02), max(0.02, xmin - 0.02)
            ymax, xmax = min(0.98, ymax + 0.02), min(0.98, xmax + 0.02)

            boxes.append({
                "bbox": [round(ymin, 3), round(xmin, 3), round(ymax, 3), round(xmax, 3)],
                "score": round(float(np.max(norm_map)), 3),
                "label": "Spectrally Anomalous Target Cluster"
            })

        return norm_map, boxes

    @classmethod
    def extract_mean_spectral_signature(cls, hsi_cube: HsiCubeData) -> Dict[str, Any]:
        """Extracts mean spectral signature across the cube."""
        sig = cls.extract_spectral_signature(hsi_cube)
        return {
            "wavelengths": sig["wavelengths_nm"],
            "mean_curve": sig["mean_reflectance"],
            "std_curve": sig["std_deviation"],
            "absorption_features": sig["absorption_features"]
        }

    @staticmethod
    def detect_absorption_dips(
        wavelengths: List[float],
        mean_curve: List[float],
        prominence_threshold: float = 0.015
    ) -> List[Dict[str, Any]]:
        """Detects physical absorption dips along a given reflectance curve."""
        b = len(mean_curve)
        dips = []
        for i in range(1, b - 1):
            if mean_curve[i] < mean_curve[i - 1] and mean_curve[i] < mean_curve[i + 1]:
                wl = wavelengths[i]
                depth = float(0.5 * (mean_curve[i - 1] + mean_curve[i + 1]) - mean_curve[i])
                if depth >= prominence_threshold:
                    if abs(wl - 670.0) <= 60.0:
                        feature = "Chlorophyll-a Red Absorption (Photosynthetic Activity)"
                    elif abs(wl - 960.0) <= 80.0 or abs(wl - 1400.0) <= 90.0:
                        feature = "Liquid Water / Moisture Vapor Absorption Band"
                    elif abs(wl - 1900.0) <= 90.0:
                        feature = "Atmospheric Water / OH Molecular Absorption"
                    elif abs(wl - 2200.0) <= 80.0:
                        feature = "Al-OH Clay / Hydrothermal Alteration Mineral Band"
                    else:
                        feature = "Spectral Minimum / Diagnostic Feature"
                    dips.append({
                        "wavelength_nm": round(float(wl), 1),
                        "reflectance": round(float(mean_curve[i]), 4),
                        "dip_depth": round(depth, 4),
                        "diagnostic_feature": feature
                    })
        return dips

    @classmethod
    def reed_xiaoli_anomaly_detector(cls, hsi_cube: HsiCubeData, regularize_cov: float = 1e-4) -> np.ndarray:
        """Alias for compute_rx_anomaly returning anomaly score map."""
        norm_map, _ = cls.compute_rx_anomaly(hsi_cube)
        return norm_map
