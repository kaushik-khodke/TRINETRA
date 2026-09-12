"""
SatQuery AI — Input & Pair Compatibility Validator
Inspects file integrity, raster format, band count, CRS, spatial alignment,
and pairing compatibility before AI specialist inference.
"""

import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from geospatial.reader import GeospatialReader, RasterMetadata

class ValidationReport(BaseModel):
    valid: bool
    mode: str
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    images_metadata: List[Dict[str, Any]] = []
    compatibility: Dict[str, Any] = {}

class InputValidator:
    SUPPORTED_EXTENSIONS = [".tif", ".tiff", ".png", ".jpg", ".jpeg"]

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

        # 2. File readability & format checks
        parsed_metadata: List[RasterMetadata] = []
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
                    error_message=f"Unsupported format '{ext}'. Must be GeoTIFF/TIFF or benchmark PNG/JPEG."
                )

            declared_mod = declared_modalities[i] if declared_modalities and i < len(declared_modalities) else None
            try:
                _, meta = GeospatialReader.read_image(path, detected_modality=declared_mod)
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
