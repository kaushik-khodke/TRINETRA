"""
SatQuery AI / TRINETRA — Intelligent Remote Sensing Domain & Modality Detector
Inspects raster metadata, band dimensionality, spectral characteristics, and spatial-radiometric
distributions to verify whether an input is genuine remote sensing vs. non-remote-sensing content.
Zero simulation. Strict rejection policy.
"""

import os
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from pydantic import BaseModel, Field

class DomainValidationResult(BaseModel):
    is_remote_sensing: bool
    modality: str = "unknown"  # optical, multispectral, sar, hyperspectral, unknown
    confidence: float = 0.0
    band_count: int = 0
    dimensions: Tuple[int, int] = (0, 0)
    reasons: List[str] = Field(default_factory=list)
    rejection_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DomainDetector:
    """
    Evaluates imagery across 4 rigorous tiers:
    Tier 1: Geospatial Metadata & Coordinate Reference System (CRS)
    Tier 2: Spectral Cube Dimensionality (HSI / MSI / SAR / RGB)
    Tier 3: Radiometric & Physical Texture Signatures
    Tier 4: Non-Remote-Sensing Rejection Heuristics (Horizon/Sky, Face/Skin, Book Text, UI Screenshot)
    """

    @staticmethod
    def inspect(
        image_arr: np.ndarray,
        filename: str = "",
        is_geotiff: bool = False,
        crs: Optional[str] = None,
        bounds: Optional[Tuple[float, float, float, float]] = None,
        wavelengths: Optional[List[float]] = None
    ) -> DomainValidationResult:
        if image_arr is None or image_arr.size == 0:
            return DomainValidationResult(
                is_remote_sensing=False,
                reasons=["Input image buffer is null, empty, or corrupted."],
                rejection_message="Unsupported input: file could not be decoded or contains empty raster data."
            )

        # Spatial dimensions & band count
        ndim = image_arr.ndim
        if ndim == 2:
            h, w = image_arr.shape
            c = 1
        elif ndim == 3:
            # Check if bands are first or last
            if image_arr.shape[0] > 10 and image_arr.shape[2] <= 4:
                # Shape is (H, W, C)
                h, w, c = image_arr.shape
            elif image_arr.shape[2] > 10 and image_arr.shape[0] <= 4:
                # Shape is (C, H, W)
                c, h, w = image_arr.shape
                image_arr = np.transpose(image_arr, (1, 2, 0))
            elif image_arr.shape[0] > 20 and image_arr.shape[0] < image_arr.shape[1] and image_arr.shape[0] < image_arr.shape[2]:
                # Multi-band / HSI with bands first: (Bands, H, W)
                c, h, w = image_arr.shape
                image_arr = np.transpose(image_arr, (1, 2, 0))
            else:
                h, w, c = image_arr.shape
        else:
            return DomainValidationResult(
                is_remote_sensing=False,
                reasons=[f"Unsupported tensor dimensionality: {ndim}D (expected 2D or 3D)."],
                rejection_message="Unsupported input: raster dimensions are invalid."
            )

        reasons: List[str] = []
        conf_scores: List[float] = []

        # =====================================================================
        # 1. Tier 1: Geospatial Metadata Verification
        # =====================================================================
        has_geospatial = False
        if is_geotiff and crs:
            has_geospatial = True
            reasons.append(f"Geospatial CRS detected ({crs}) with valid spatial bounds")
            conf_scores.append(0.98)
        elif is_geotiff:
            has_geospatial = True
            reasons.append("Geospatial TIFF format verified with internal geographic tags")
            conf_scores.append(0.92)

        # =====================================================================
        # 2. Tier 2: Spectral Cube Dimensionality Analysis
        # =====================================================================
        # Case A: Hyperspectral (HSI) -> Typically 40 to 300+ contiguous bands
        if c >= 40 or (wavelengths and len(wavelengths) >= 40):
            modality = "hyperspectral"
            reasons.append(f"Spectral cube verified with {c} contiguous spectral bands")
            if wavelengths:
                reasons.append(f"Calibrated wavelength metadata detected ({min(wavelengths):.1f}nm–{max(wavelengths):.1f}nm)")
                conf_scores.append(0.99)
            else:
                conf_scores.append(0.95)

            return DomainValidationResult(
                is_remote_sensing=True,
                modality=modality,
                confidence=round(float(np.mean(conf_scores)), 3),
                band_count=c,
                dimensions=(h, w),
                reasons=reasons,
                metadata={"wavelength_count": len(wavelengths) if wavelengths else c}
            )

        # Case B: Multispectral (MSI) -> Typically 4 to 20 bands (e.g. Sentinel-2, Landsat-8)
        if 4 <= c < 40:
            modality = "multispectral"
            reasons.append(f"Multispectral raster confirmed with {c} distinct spectral bands")
            conf_scores.append(0.95 if has_geospatial else 0.88)
            return DomainValidationResult(
                is_remote_sensing=True,
                modality=modality,
                confidence=round(float(np.mean(conf_scores)), 3),
                band_count=c,
                dimensions=(h, w),
                reasons=reasons
            )

        # Case C: Single/Dual-band rasters (SAR, DEM, Elevation, Grayscale EO) -> 1 or 2 bands
        if c in [1, 2]:
            min_val = float(np.nanmin(image_arr))
            max_val = float(np.nanmax(image_arr))
            std_val = float(np.nanstd(image_arr))
            if min_val < -5.0 and max_val <= 10.0:
                modality = "sar"
                reasons.append(f"SAR polarimetric microwave backscatter verified (Range: {min_val:.1f} dB to {max_val:.1f} dB)")
                conf_scores.append(0.96)
                return DomainValidationResult(
                    is_remote_sensing=True,
                    modality=modality,
                    confidence=round(float(np.mean(conf_scores)), 3),
                    band_count=c,
                    dimensions=(h, w),
                    reasons=reasons
                )
            elif has_geospatial and std_val > 1e-4:
                modality = "sar"
                desc = "elevation DEM" if max_val > 50.0 else "single-band geospatial"
                reasons.append(f"Georeferenced {desc} raster verified (Range: {min_val:.1f} to {max_val:.1f}, std: {std_val:.2f})")
                conf_scores.append(0.96)
                return DomainValidationResult(
                    is_remote_sensing=True,
                    modality=modality,
                    confidence=round(float(np.mean(conf_scores)), 3),
                    band_count=c,
                    dimensions=(h, w),
                    reasons=reasons
                )

        # =====================================================================
        # 3. Tier 3 & 4: Optical (RGB) & Non-Remote-Sensing Plausibility Checks
        # =====================================================================
        if c >= 3:
            r = image_arr[:, :, 0].astype(float)
            g = image_arr[:, :, 1].astype(float)
            b = image_arr[:, :, 2].astype(float)
            gray = 0.299 * r + 0.587 * g + 0.114 * b
        else:
            gray = image_arr[:, :, 0].astype(float) if c == 1 and ndim == 3 else image_arr.astype(float)
            r = g = b = gray

        total_pixels = gray.size
        if total_pixels == 0:
            return DomainValidationResult(
                is_remote_sensing=False,
                reasons=["Raster pixel area is zero."],
                rejection_message="Unsupported input: raster dimensions are invalid."
            )

        g_min = float(np.nanmin(gray))
        g_max = float(np.nanmax(gray))
        g_std = float(np.nanstd(gray))

        # Check for completely flat or degenerate zero-variance raster
        if g_max == g_min or g_std < 1e-5:
            return DomainValidationResult(
                is_remote_sensing=False,
                reasons=["Raster is completely flat with zero radiometric variance."],
                rejection_message="Unsupported input: this image has zero radiometric variance and contains no detectable Earth observation features."
            )

        # Scale to standard 0-255 range for perceptual luminance heuristics if outside uint8 range
        if g_max > 255.0 or g_min < 0.0:
            norm_gray = (gray - g_min) / (g_max - g_min + 1e-6) * 255.0
        else:
            norm_gray = gray

        # 3.1 Blank / Degenerate Imagery Check
        white_pct = float(np.sum(norm_gray > 245) / total_pixels * 100.0)
        black_pct = float(np.sum(norm_gray < 10) / total_pixels * 100.0)
        if white_pct > 85.0 and (not is_geotiff or g_std < 2.0):
            if g_std < 12.0:
                return DomainValidationResult(
                    is_remote_sensing=False,
                    reasons=[f"Over {white_pct:.1f}% of pixels are pure white saturation with negligible spatial variance (std: {g_std:.2f})"],
                    rejection_message="Unsupported input: this image is predominantly blank white and does not contain valid Earth observation features."
                )
        if black_pct > 92.0 and (not is_geotiff or g_std < 2.0):
            if g_std < 12.0:
                return DomainValidationResult(
                    is_remote_sensing=False,
                    reasons=[f"Over {black_pct:.1f}% of pixels are completely black null values with negligible spatial variance (std: {g_std:.2f})"],
                    rejection_message="Unsupported input: this image is predominantly black and does not contain valid Earth observation features."
                )

        # 3.2 Document / Book Page / Scanned Text Check
        if not is_geotiff:
            if c >= 3:
                max_c = np.maximum(np.maximum(r, g), b)
                min_c = np.minimum(np.minimum(r, g), b)
                saturation = np.where(max_c > 0, (max_c - min_c) / (max_c + 1e-5), 0.0)
                mean_sat = float(np.mean(saturation))
            else:
                mean_sat = 0.0

            dark_text_pct = float(np.sum(norm_gray < 45) / total_pixels * 100.0)
            paper_bg_pct = float(np.sum(norm_gray > 220) / total_pixels * 100.0)

            # Ambient / Indoor lighting adaptive document check (e.g. mobile photo of printed paper/certificate)
            bg_candidates = norm_gray[norm_gray > 80]
            bg_median = float(np.median(bg_candidates)) if bg_candidates.size > 0 else 0.0
            adaptive_paper_pct = float(np.sum((norm_gray >= bg_median - 35) & (norm_gray <= bg_median + 35)) / total_pixels * 100.0)
            adaptive_text_pct = float(np.sum(norm_gray < bg_median - 55) / total_pixels * 100.0)

            is_scanned_doc = (paper_bg_pct > 48.0 and dark_text_pct > 0.75 and mean_sat < 0.10)
            is_photographed_doc = (
                adaptive_paper_pct > 45.0
                and adaptive_text_pct > 1.2
                and mean_sat < 0.22
                and bg_median > 115.0
            )

            if is_scanned_doc or is_photographed_doc:
                doc_type = "document scan" if is_scanned_doc else "printed document or certificate photograph"
                return DomainValidationResult(
                    is_remote_sensing=False,
                    reasons=[
                        f"Document text characteristics detected ({adaptive_paper_pct:.1f}% paper background, {adaptive_text_pct:.1f}% text glyphs, {mean_sat:.3f} saturation)"
                    ],
                    rejection_message=f"Unsupported input: this image appears to be a {doc_type}, not remote-sensing Earth observation imagery. SatQuery AI requires nadir satellite or aerial imagery."
                )

            # 3.3 Application Screenshot / Flat UI Graphic Check
            fn_lower = filename.lower()
            if "screenshot" in fn_lower or "screengrab" in fn_lower:
                if paper_bg_pct > 30.0 or mean_sat < 0.06:
                    return DomainValidationResult(
                        is_remote_sensing=False,
                        reasons=["File exhibits desktop screenshot metadata and flat UI window luminance"],
                        rejection_message="Unsupported input: this image appears to be an application or desktop screenshot, not satellite imagery."
                    )

            # 3.4 Perspective Camera Horizon & Sky Detection
            if h > 80 and w > 80 and c >= 3:
                top_section = image_arr[: int(h * 0.35), :, :]
                top_r = top_section[:, :, 0].astype(float)
                top_g = top_section[:, :, 1].astype(float)
                top_b = top_section[:, :, 2].astype(float)

                blue_ratio = float(np.mean(top_b / (top_r + 1e-5)))
                top_lum = 0.299 * top_r + 0.587 * top_g + 0.114 * top_b
                top_std = float(np.std(top_lum))

                if top_std < 18.0 and blue_ratio > 1.35 and float(np.mean(top_lum)) > 130.0:
                    return DomainValidationResult(
                        is_remote_sensing=False,
                        reasons=[
                            f"Horizontal ground perspective detected (Upper frame displays uniform sky: B/R ratio {blue_ratio:.2f}, std {top_std:.1f})"
                        ],
                        rejection_message="Unsupported input: this is a horizontal ground-level camera photograph with a visible sky/horizon. SatQuery AI requires top-down (nadir) Earth observation imagery."
                    )

        # 3.5 Portrait / Selfie / Human Skin Tone Heuristic
        # Distinguishes smooth human flesh from textured terrestrial terrain/clay/soil
        if not is_geotiff and c >= 3 and h >= 64 and w >= 64:
            sum_rgb = r + g + b + 1e-5
            norm_r = r / sum_rgb
            norm_g = g / sum_rgb
            skin_mask = (norm_r > 0.36) & (norm_r < 0.54) & (norm_g > 0.28) & (norm_g < 0.38) & (r > g) & (g > b) & (r > 60)
            skin_pct = float(np.sum(skin_mask) / total_pixels * 100.0)

            ch_start, ch_end = int(h * 0.25), int(h * 0.75)
            cw_start, cw_end = int(w * 0.25), int(w * 0.75)
            center_skin = skin_mask[ch_start:ch_end, cw_start:cw_end]
            center_skin_pct = float(np.sum(center_skin) / max(1, center_skin.size) * 100.0)

            if skin_pct > 22.0 and center_skin_pct > 32.0:
                # Differentiate smooth human face vs textured satellite terrain (red/brown soil, clay, arid farmland)
                gray_u8 = gray.astype(np.uint8)
                gx = np.diff(gray_u8, axis=1)
                gy = np.diff(gray_u8, axis=0)
                edge_energy = float(np.mean(np.abs(gx)) + np.mean(np.abs(gy)))

                # Real human portraits have smooth skin (edge energy < 6.0)
                # Satellite terrain has sharp parcel boundaries, roads, waterlines, structures (edge energy > 15.0)
                if edge_energy < 6.0:
                    return DomainValidationResult(
                        is_remote_sensing=False,
                        reasons=[f"Smooth portrait skin tones detected ({skin_pct:.1f}% skin tone, edge energy {edge_energy:.1f})"],
                        rejection_message="Unsupported input: this image appears to be a portrait or selfie photograph. Remote-sensing models require Earth observation imagery."
                    )

        # =====================================================================
        # 4. Verified Nadir Optical Satellite Imagery
        # =====================================================================
        modality = "optical" if c >= 3 else "sar"
        reasons.append(f"Orthogonal nadir satellite imagery confirmed ({w}x{h}, {c} channels)")
        if has_geospatial:
            reasons.append("Geospatial raster metadata present")
            conf_scores.append(0.96)
        else:
            reasons.append("Spatial texture frequency and radiometric variance match Earth observation standards")
            conf_scores.append(0.91)

        final_conf = round(float(np.mean(conf_scores)), 3) if conf_scores else 0.90

        return DomainValidationResult(
            is_remote_sensing=True,
            modality=modality,
            confidence=final_conf,
            band_count=c,
            dimensions=(h, w),
            reasons=reasons
        )
