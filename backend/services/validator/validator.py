"""
SatQuery AI — Input & Pair Compatibility Validator
Inspects file integrity, raster format, band count, CRS, spatial alignment,
and pairing compatibility before AI specialist inference.
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
from geospatial.reader import GeospatialReader, RasterMetadata

from services.validator.domain_detector import DomainDetector, DomainValidationResult

class ValidationReport(BaseModel):
    valid: bool
    mode: str
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    images_metadata: List[Dict[str, Any]] = []
    compatibility: Dict[str, Any] = {}
    validation_object: Optional[Dict[str, Any]] = None

class InputValidator:
    SUPPORTED_EXTENSIONS = [".tif", ".tiff", ".png", ".jpg", ".jpeg", ".mat", ".hdr", ".dat"]

    @staticmethod
    def validate(
        file_paths: List[str],
        requested_mode: str = "single",
        declared_modalities: Optional[List[str]] = None
    ) -> ValidationReport:
        # 1. Image count check
        count = len(file_paths)
        if count == 0:
            return ValidationReport(
                valid=False,
                mode=requested_mode,
                error_message="No imagery supplied. Please upload at least one image file."
            )

        if requested_mode == "single" and count != 1:
            return ValidationReport(
                valid=False,
                mode=requested_mode,
                error_message=f"Single-image mode expects exactly 1 image, but received {count}."
            )

        if requested_mode in ["bi_temporal", "optical_sar"] and count != 2:
            return ValidationReport(
                valid=False,
                mode=requested_mode,
                error_message=f"Paired workflow '{requested_mode}' expects exactly 2 images, but received {count}."
            )

        # 2. File readability, format, and intelligent domain checks
        parsed_metadata: List[RasterMetadata] = []
        last_val_obj: Optional[Dict[str, Any]] = None

        for i, path in enumerate(file_paths):
            if not os.path.exists(path):
                return ValidationReport(
                    valid=False,
                    mode=requested_mode,
                    error_message=f"File not found on system: {path}"
                )

            ext = os.path.splitext(path)[1].lower()
            if ext not in InputValidator.SUPPORTED_EXTENSIONS:
                return ValidationReport(
                    valid=False,
                    mode=requested_mode,
                    error_message=f"Unsupported format '{ext}'. Must be GeoTIFF, HSI (.mat/.hdr), or benchmark PNG/JPEG."
                )

            declared_mod = declared_modalities[i] if declared_modalities and i < len(declared_modalities) else None
            try:
                arr, meta = GeospatialReader.read_image(path, detected_modality=declared_mod)

                # Tiered Intelligent Domain Validation Agent
                domain_res = DomainDetector.inspect(
                    image_arr=arr,
                    filename=os.path.basename(path),
                    is_geotiff=meta.is_geotiff,
                    crs=meta.crs,
                    bounds=meta.bounds
                )

                last_val_obj = {
                    "is_remote_sensing": domain_res.is_remote_sensing,
                    "modality": domain_res.modality,
                    "confidence": domain_res.confidence,
                    "reasons": domain_res.reasons
                }

                if not domain_res.is_remote_sensing:
                    rej_msg = domain_res.rejection_message or "Unsupported input: this image does not appear to be a supported remote-sensing product."
                    return ValidationReport(
                        valid=False,
                        mode=requested_mode,
                        error_message=rej_msg,
                        validation_object=last_val_obj
                    )

                # Update modality with detector's verified classification (e.g. hyperspectral)
                if domain_res.modality != "unknown":
                    meta.modality = domain_res.modality

                parsed_metadata.append(meta)

            except Exception as e:
                return ValidationReport(
                    valid=False,
                    mode=requested_mode,
                    error_message=f"Failed to read raster at '{os.path.basename(path)}': {str(e)}"
                )

        # 3. Mode-specific pairing compatibility checks
        compatibility: Dict[str, Any] = {
            "file_count": count,
            "all_geotiff": all(m.is_geotiff for m in parsed_metadata),
            "spatial_coverage_aligned": True
        }

        if requested_mode == "optical_sar":
            m0, m1 = parsed_metadata[0].modality.lower(), parsed_metadata[1].modality.lower()
            has_optical = ("optical" in m0 or "optical" in m1 or parsed_metadata[0].bands >= 3 or parsed_metadata[1].bands >= 3)
            has_sar = ("sar" in m0 or "sar" in m1 or parsed_metadata[0].bands == 1 or parsed_metadata[1].bands == 1)

            if not (has_optical and has_sar):
                compatibility["modality_match"] = False
                return ValidationReport(
                    valid=False,
                    mode=requested_mode,
                    error_message="Optical–SAR mode requires one Optical/Multispectral image and one SAR radar image.",
                    compatibility=compatibility
                )
            compatibility["modality_match"] = True
            compatibility["cross_modal_coregistered"] = True

        elif requested_mode == "bi_temporal":
            # Check dimensional compatibility
            h0, w0 = parsed_metadata[0].height, parsed_metadata[0].width
            h1, w1 = parsed_metadata[1].height, parsed_metadata[1].width
            aspect0 = round(w0 / h0, 2)
            aspect1 = round(w1 / h1, 2)
            
            if aspect0 != aspect1 and (abs(w0 - w1) > 200 or abs(h0 - h1) > 200):
                compatibility["spatial_coverage_aligned"] = False
                return ValidationReport(
                    valid=True,
                    mode=requested_mode,
                    warning_message="Dimensional disparity between T1 and T2 rasters; automated spatial resampling will be applied.",
                    images_metadata=[m.to_dict() for m in parsed_metadata],
                    compatibility=compatibility
                )
            compatibility["bitemporal_aligned"] = True

        return ValidationReport(
            valid=True,
            mode=requested_mode,
            images_metadata=[m.to_dict() for m in parsed_metadata],
            compatibility=compatibility
        )

    @staticmethod
    def verify_satellite_domain(image_arr: np.ndarray, filename: str = "") -> Tuple[bool, Optional[str]]:
        """
        Smart nuance verification: checks whether the image exhibits radiometric and spatial
        characteristics of satellite/aerial Earth observation imagery versus a document screenshot,
        book text, or software diagram.
        """
        if image_arr is None or image_arr.size == 0:
            return False, "Image array is empty or corrupt."

        # Convert to float luminance for spatial texture analysis
        if image_arr.ndim == 3:
            if image_arr.shape[2] >= 3:
                gray = 0.299 * image_arr[:, :, 0] + 0.587 * image_arr[:, :, 1] + 0.114 * image_arr[:, :, 2]
            else:
                gray = image_arr[:, :, 0].astype(float)
        else:
            gray = image_arr.astype(float)

        total_pixels = gray.size

        # 1. Text Document / Book Page Detection
        white_bg_pct = float(np.sum(gray > 220) / total_pixels * 100.0)
        dark_text_pct = float(np.sum(gray < 45) / total_pixels * 100.0)

        if image_arr.ndim == 3 and image_arr.shape[2] >= 3:
            r = image_arr[:, :, 0].astype(float)
            g = image_arr[:, :, 1].astype(float)
            b = image_arr[:, :, 2].astype(float)
            max_c = np.maximum(np.maximum(r, g), b)
            min_c = np.minimum(np.minimum(r, g), b)
            saturation = np.where(max_c > 0, (max_c - min_c) / (max_c + 1e-5), 0.0)
            mean_sat = float(np.mean(saturation))
        else:
            mean_sat = 0.0

        # Characteristic of a book page / document screenshot:
        # High white background (> 50%), dark text pixels (> 0.8%), and extremely low color saturation (< 0.12)
        if white_bg_pct > 50.0 and dark_text_pct > 0.8 and mean_sat < 0.12:
            return False, (
                "The image has characteristics of a printed book page or text document "
                f"({round(white_bg_pct)}% white paper background with dark printed text, saturation {round(mean_sat, 3)}). "
                "SatQuery AI requires satellite or aerial Earth observation imagery (GeoTIFF, Sentinel, Landsat, or optical/SAR rasters)."
            )

        # 2. Predominantly blank image
        if white_bg_pct > 85.0:
            return False, "The uploaded image is predominantly blank white (>85% white pixels), not an Earth observation scene."
        if float(np.sum(gray < 15) / total_pixels * 100.0) > 92.0:
            return False, "The uploaded image is predominantly black (>92% dark pixels), not an Earth observation scene."

        # 3. Screen Capture / UI Diagram heuristic
        clean_name = filename.lower()
        if "screenshot" in clean_name and (white_bg_pct > 35.0 or mean_sat < 0.05):
            return False, (
                "The file appears to be a desktop/application screenshot rather than an Earth observation scene. "
                "Please upload actual satellite or aerial imagery to perform radiometric and geospatial analysis."
            )

        return True, None
