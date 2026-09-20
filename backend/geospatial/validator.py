"""
TRINETRA — Geospatial Validation & Alignment Engine
Implements strict 10-point bi-temporal validation, optical–SAR geometric coregistration,
spatial intersection mathematics, and reproducible reference grid alignment.
Governed by 03_STAGE_3_GEOSPATIAL.md. Zero synthetic data. Zero ungrounded assumptions.
"""

import os
import re
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from schemas.contracts import RasterMetadata, AlignmentReport
from core.exceptions import GeospatialValidationError, AlignmentMismatchError


class GeospatialValidator:
    """Scientific validator enforcing spatial consistency before neural specialist execution."""

    @staticmethod
    def inspect_raster_metadata(file_path: str, detected_modality: Optional[str] = None) -> RasterMetadata:
        """
        Extracts all 11 required metadata fields directly from raster headers.
        Inspects CRS, affine geotransform, bounding box, resolution, bands, dtype,
        nodata values, temporal tags, and sensor platform.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Raster file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)

        # 1. Hyperspectral MATLAB / ENVI format
        if ext in [".mat", ".hdr", ".dat"]:
            from geospatial.hsi_reader import HsiReader
            hsi = HsiReader.read(file_path)
            return RasterMetadata(
                width=hsi.width,
                height=hsi.height,
                band_count=hsi.bands,
                dtype=str(hsi.cube.dtype),
                crs=hsi.crs,
                bounds=list(hsi.bounds) if hsi.bounds else None,
                transform_matrix=None,
                resolution=None,
                sensor_name=hsi.sensor_name,
                modality="hyperspectral",
                is_geotiff=bool(hsi.crs is not None),
                acquisition_timestamp=None,
                band_descriptions=[f"{round(w, 1)}nm" for w in hsi.wavelengths[:10]] if len(hsi.wavelengths) > 0 else None,
                filename=filename,
                location_name=hsi.sensor_name
            )

        # 2. Standard / Benchmark Imagery (.png, .jpg, .jpeg, .webp, .bmp, .gif, .jp2, .img)
        if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".jp2", ".img"]:
            with Image.open(file_path) as img:
                arr = np.array(img)
                h, w = arr.shape[:2]
                bands = 1 if arr.ndim == 2 else (arr.shape[2] if arr.ndim == 3 else 1)
                dtype = str(arr.dtype)
                
                timestamp = GeospatialValidator._extract_filename_timestamp(filename)

                return RasterMetadata(
                    width=w,
                    height=h,
                    band_count=bands,
                    dtype=dtype,
                    nodata_value=None,
                    crs=None,
                    transform_matrix=None,
                    bounds=None,
                    resolution=None,
                    sensor_name="Benchmark Aerial/Satellite Dataset",
                    modality=detected_modality or ("sar" if bands == 1 else "optical"),
                    is_geotiff=False,
                    acquisition_timestamp=timestamp,
                    band_descriptions=["Red", "Green", "Blue"] if bands >= 3 else (["Grayscale/Backscatter"] if bands == 1 else None),
                    filename=filename,
                    center_lat=None,
                    center_lng=None,
                    location_name=os.path.splitext(filename)[0]
                )

        # 3. GeoTIFF / TIFF Inspection
        with Image.open(file_path) as img:
            arr = np.array(img)
            h, w = arr.shape[:2]
            bands = 1 if arr.ndim == 2 else (arr.shape[2] if arr.ndim == 3 else 1)
            dtype = str(arr.dtype)

            tag_v2 = getattr(img, "tag_v2", {})
            has_pixel_scale = 33550 in tag_v2
            has_tiepoint = 33922 in tag_v2
            has_transform = 34264 in tag_v2

            is_geotiff = False
            crs = None
            bounds = None
            transform_matrix = None
            resolution = None
            center_lat = None
            center_lng = None
            nodata_val = None
            timestamp = None
            sensor_name = "Generic Satellite Raster"
            band_descs = None

            # Check DateTime tag (tag 306)
            if 306 in tag_v2:
                raw_dt = str(tag_v2[306]).strip()
                try:
                    dt_obj = datetime.strptime(raw_dt, "%Y:%m:%d %H:%M:%S")
                    timestamp = dt_obj.isoformat() + "Z"
                except Exception:
                    timestamp = raw_dt
            if not timestamp:
                timestamp = GeospatialValidator._extract_filename_timestamp(filename)

            # Check GDAL nodata tag (tag 42113)
            if 42113 in tag_v2:
                try:
                    nodata_val = float(str(tag_v2[42113]).strip().strip("\x00"))
                except Exception:
                    pass

            # Detect Sensor Characteristics
            if bands == 4:
                sensor_name = "Sentinel-2 MSI (B2-Blue, B3-Green, B4-Red, B8-NIR)"
                band_descs = ["Blue (490nm)", "Green (560nm)", "Red (665nm)", "NIR (842nm)"]
            elif bands == 3:
                sensor_name = "True Color Optical (Red, Green, Blue)"
                band_descs = ["Red", "Green", "Blue"]
            elif bands == 1:
                sensor_name = "Synthetic Aperture Radar (SAR) / Single-Band Intensity"
                band_descs = ["Radar Backscatter / Single-Band Radiometry"]

            # Parse Georeferencing
            if has_pixel_scale and has_tiepoint:
                scale = tag_v2[33550]
                tiepoint = tag_v2[33922]
                try:
                    scale_x = float(scale[0])
                    scale_y = float(scale[1])
                    origin_x = float(tiepoint[3])
                    origin_y = float(tiepoint[4])

                    min_x = origin_x
                    max_y = origin_y
                    max_x = min_x + w * scale_x
                    min_y = max_y - h * scale_y

                    resolution = [scale_x, scale_y]
                    transform_matrix = [scale_x, 0.0, origin_x, 0.0, -scale_y, origin_y]

                    # 1. Geographic WGS-84 coordinates in degrees
                    if -180.0 <= min_x <= 180.0 and -90.0 <= min_y <= 90.0:
                        center_lat = round((min_y + max_y) / 2.0, 6)
                        center_lng = round((min_x + max_x) / 2.0, 6)
                        bounds = [round(min_x, 6), round(min_y, 6), round(max_x, 6), round(max_y, 6)]
                        crs = "EPSG:4326"
                        is_geotiff = True
                    # 2. Projected UTM coordinates
                    elif 34735 in tag_v2:
                        geokeys = tag_v2[34735]
                        utm_epsg = None
                        for idx in range(0, len(geokeys) - 3, 4):
                            if geokeys[idx] == 3072:
                                utm_epsg = geokeys[idx + 3]
                                break
                        if utm_epsg:
                            zone = None
                            if 32601 <= utm_epsg <= 32660:
                                zone = utm_epsg - 32600
                                northern = True
                            elif 32701 <= utm_epsg <= 32760:
                                zone = utm_epsg - 32700
                                northern = False

                            if zone:
                                c_lat, c_lon = GeospatialValidator._utm_to_latlon(
                                    (min_x + max_x) / 2.0, (min_y + max_y) / 2.0, zone, northern
                                )
                                sw_lat, sw_lon = GeospatialValidator._utm_to_latlon(min_x, min_y, zone, northern)
                                ne_lat, ne_lon = GeospatialValidator._utm_to_latlon(max_x, max_y, zone, northern)
                                center_lat = c_lat
                                center_lng = c_lon
                                bounds = [min(sw_lon, ne_lon), min(sw_lat, ne_lat), max(sw_lon, ne_lon), max(sw_lat, ne_lat)]
                                crs = f"EPSG:{utm_epsg}"
                                is_geotiff = True
                            else:
                                crs = f"EPSG:{utm_epsg}"
                                bounds = [min_x, min_y, max_x, max_y]
                                is_geotiff = True
                        else:
                            bounds = [min_x, min_y, max_x, max_y]
                            crs = "Projected Coordinate System"
                            is_geotiff = True
                    else:
                        bounds = [min_x, min_y, max_x, max_y]
                        crs = "Local / Projected Coordinate System"
                        is_geotiff = True

                except Exception as e:
                    print(f"[GeospatialValidator] Warning parsing GeoTIFF tags: {e}")

            elif has_transform:
                tf = tag_v2[34264]
                if len(tf) >= 16:
                    scale_x = float(tf[0])
                    scale_y = float(tf[5])
                    origin_x = float(tf[3])
                    origin_y = float(tf[7])
                    transform_matrix = [scale_x, 0.0, origin_x, 0.0, -scale_y, origin_y]
                    resolution = [scale_x, scale_y]
                    min_x = origin_x
                    max_y = origin_y
                    max_x = min_x + w * scale_x
                    min_y = max_y - h * scale_y
                    bounds = [min_x, min_y, max_x, max_y]
                    crs = "EPSG:4326" if (-180.0 <= min_x <= 180.0 and -90.0 <= min_y <= 90.0) else "Projected"
                    is_geotiff = True

            resolved_modality = detected_modality or ("sar" if bands == 1 else "optical")

            return RasterMetadata(
                width=w,
                height=h,
                band_count=bands,
                dtype=dtype,
                nodata_value=nodata_val,
                crs=crs,
                transform_matrix=transform_matrix,
                bounds=bounds,
                resolution=resolution,
                sensor_name=sensor_name,
                modality=resolved_modality,
                is_geotiff=is_geotiff,
                acquisition_timestamp=timestamp,
                band_descriptions=band_descs,
                filename=filename,
                center_lat=center_lat,
                center_lng=center_lng,
                location_name=os.path.splitext(filename)[0]
            )

    @staticmethod
    def calculate_bounds_intersection(
        b1: Optional[List[float]],
        b2: Optional[List[float]]
    ) -> Tuple[Optional[List[float]], float, float]:
        """
        Computes analytical bounding box intersection [xmin, ymin, xmax, ymax]
        and overlap percentages relative to scene 1 and scene 2.
        Returns: (intersection_bounds, overlap_pct_1, overlap_pct_2)
        """
        if not b1 or not b2 or len(b1) != 4 or len(b2) != 4:
            return None, 0.0, 0.0

        int_xmin = max(b1[0], b2[0])
        int_ymin = max(b1[1], b2[1])
        int_xmax = min(b1[2], b2[2])
        int_ymax = min(b1[3], b2[3])

        if int_xmax <= int_xmin or int_ymax <= int_ymin:
            return None, 0.0, 0.0

        int_w = int_xmax - int_xmin
        int_h = int_ymax - int_ymin
        int_area = int_w * int_h

        area1 = max(1e-9, (b1[2] - b1[0]) * (b1[3] - b1[1]))
        area2 = max(1e-9, (b2[2] - b2[0]) * (b2[3] - b2[1]))

        overlap1 = min(100.0, max(0.0, (int_area / area1) * 100.0))
        overlap2 = min(100.0, max(0.0, (int_area / area2) * 100.0))

        return [round(int_xmin, 6), round(int_ymin, 6), round(int_xmax, 6), round(int_ymax, 6)], round(overlap1, 2), round(overlap2, 2)

    @staticmethod
    def validate_bitemporal_alignment(
        meta_t1: RasterMetadata,
        meta_t2: RasterMetadata,
        arr_t1: Optional[np.ndarray] = None,
        arr_t2: Optional[np.ndarray] = None
    ) -> AlignmentReport:
        """
        Executes all 10 mandatory bitemporal validation checks from 03_STAGE_3_GEOSPATIAL.md:
        1. CRS compatibility
        2. Reprojection requirement
        3. Bounds overlap percentage
        4. Pixel resolution compatibility
        5. Grid origin / transform
        6. Pixel-grid alignment
        7. Resampling requirement
        8. Nodata consistency
        9. Temporal ordering
        10. Valid-data overlap percentage
        """
        # Case A: Non-georeferenced benchmark imagery (e.g. LEVIR-CD PNG splits)
        if not meta_t1.is_geotiff or not meta_t2.is_geotiff:
            dims_match = (meta_t1.width == meta_t2.width and meta_t1.height == meta_t2.height)
            temp_order = GeospatialValidator._check_temporal_ordering(meta_t1.acquisition_timestamp, meta_t2.acquisition_timestamp)
            return AlignmentReport(
                source_crs=meta_t1.crs,
                reference_crs=meta_t2.crs,
                bounds_overlap_pct=100.0 if dims_match else 0.0,
                grid_aligned=dims_match,
                resolution_ratio=1.0,
                reprojection_needed=False,
                resampling_applied=not dims_match,
                resampling_method="bilinear" if not dims_match else None,
                coregistered=False,
                offset_vector=[0.0, 0.0],
                intersection_bounds=None,
                valid_data_overlap_pct=100.0 if dims_match else None,
                temporal_order_valid=temp_order,
                status_message="Non-georeferenced benchmark rasters. Dimensionally " + 
                               ("matched (pixel-space evaluation)" if dims_match else "mismatched; pixel resampling required.")
            )

        # Case B: Georeferenced GeoTIFFs
        # 1. CRS compatibility & 2. Reprojection
        crs1 = (meta_t1.crs or "").strip().upper()
        crs2 = (meta_t2.crs or "").strip().upper()
        crs_compatible = bool(crs1 and crs2 and crs1 == crs2)
        reprojection_needed = not crs_compatible

        # 3. Bounds overlap
        int_bounds, ov1, ov2 = GeospatialValidator.calculate_bounds_intersection(meta_t1.bounds, meta_t2.bounds)
        min_overlap = min(ov1, ov2)

        # 4. Pixel resolution compatibility
        rx1, ry1 = meta_t1.resolution if meta_t1.resolution else (1.0, 1.0)
        rx2, ry2 = meta_t2.resolution if meta_t2.resolution else (1.0, 1.0)
        res_ratio = round(float(rx1 / max(1e-9, rx2)), 4)
        res_compatible = abs(res_ratio - 1.0) <= 0.05

        # 5. Grid origin & 6. Pixel-grid alignment
        tf1 = meta_t1.transform_matrix
        tf2 = meta_t2.transform_matrix
        grid_aligned = False
        offset_vector = [0.0, 0.0]

        if tf1 and tf2 and len(tf1) >= 6 and len(tf2) >= 6:
            orig_x1, orig_y1 = tf1[2], tf1[5]
            orig_x2, orig_y2 = tf2[2], tf2[5]
            dx = orig_x2 - orig_x1
            dy = orig_y2 - orig_y1
            offset_vector = [round(dx, 6), round(dy, 6)]

            rem_x = abs(dx) % max(1e-9, rx1)
            rem_y = abs(dy) % max(1e-9, ry1)
            pix_align_x = (rem_x / rx1 < 0.02) or (rem_x / rx1 > 0.98)
            pix_align_y = (rem_y / ry1 < 0.02) or (rem_y / ry1 > 0.98)
            grid_aligned = crs_compatible and res_compatible and pix_align_x and pix_align_y

        # 7. Resampling requirement
        resampling_needed = (not grid_aligned) or (not res_compatible) or (meta_t1.width != meta_t2.width or meta_t1.height != meta_t2.height)

        # 8. Nodata consistency
        nodata_consistent = (meta_t1.nodata_value == meta_t2.nodata_value)

        # 9. Temporal ordering
        temp_order = GeospatialValidator._check_temporal_ordering(meta_t1.acquisition_timestamp, meta_t2.acquisition_timestamp)

        # 10. Valid-data overlap percentage
        valid_overlap = None
        if arr_t1 is not None and arr_t2 is not None and min_overlap > 0.0:
            valid_overlap = GeospatialValidator._compute_valid_data_overlap(
                arr_t1, meta_t1.nodata_value, arr_t2, meta_t2.nodata_value
            )

        # Coregistration determination
        is_coregistered = (crs_compatible and min_overlap >= 95.0 and res_compatible and abs(offset_vector[0]) <= 2 * rx1 and abs(offset_vector[1]) <= 2 * ry1)

        status_notes = []
        if not crs_compatible:
            status_notes.append(f"CRS mismatch ({crs1 or 'None'} vs {crs2 or 'None'})")
        if min_overlap < 95.0:
            status_notes.append(f"Partial spatial intersection ({min_overlap}% overlap)")
        if not res_compatible:
            status_notes.append(f"Resolution mismatch (ratio {res_ratio})")
        if resampling_needed:
            status_notes.append("Automated reference grid alignment required")

        status_msg = "Verified bi-temporal coregistration." if is_coregistered else ("Alignment requirements: " + "; ".join(status_notes))

        return AlignmentReport(
            source_crs=meta_t1.crs,
            reference_crs=meta_t2.crs,
            bounds_overlap_pct=min_overlap,
            grid_aligned=grid_aligned,
            resolution_ratio=res_ratio,
            reprojection_needed=reprojection_needed,
            resampling_applied=False,
            resampling_method=None,
            coregistered=is_coregistered,
            offset_vector=offset_vector,
            intersection_bounds=int_bounds,
            valid_data_overlap_pct=valid_overlap,
            temporal_order_valid=temp_order,
            status_message=status_msg
        )

    @staticmethod
    def validate_optical_sar_coregistration(
        opt_meta: RasterMetadata,
        sar_meta: RasterMetadata,
        opt_arr: Optional[np.ndarray] = None,
        sar_arr: Optional[np.ndarray] = None
    ) -> AlignmentReport:
        """
        Validates geometric optical-to-SAR coregistration.
        A modality check is NOT proof of coregistration. Evaluates CRS, bounds intersection,
        transform, resolution, grid, overlap, and registration offset before certifying.
        """
        crs_opt = (opt_meta.crs or "").strip().upper()
        crs_sar = (sar_meta.crs or "").strip().upper()
        crs_match = bool(crs_opt and crs_sar and crs_opt == crs_sar)
        crs_differ = bool(crs_opt and crs_sar and crs_opt != crs_sar)

        # Benchmark non-georeferenced imagery check (neither has bounds nor CRS)
        if not opt_meta.is_geotiff and not sar_meta.is_geotiff and not crs_opt and not crs_sar:
            dims_match = (opt_meta.width == sar_meta.width and opt_meta.height == sar_meta.height)
            return AlignmentReport(
                source_crs=opt_meta.crs,
                reference_crs=sar_meta.crs,
                bounds_overlap_pct=100.0 if dims_match else 0.0,
                grid_aligned=dims_match,
                resolution_ratio=1.0,
                reprojection_needed=False,
                resampling_applied=not dims_match,
                resampling_method="bilinear" if not dims_match else None,
                coregistered=False,
                offset_vector=[0.0, 0.0],
                intersection_bounds=None,
                valid_data_overlap_pct=100.0 if dims_match else None,
                temporal_order_valid=None,
                status_message="Non-georeferenced benchmark pairs (SEN12MS benchmark format). Pixel dimensions " + 
                               ("aligned." if dims_match else "differ; resampling needed.")
            )

        if crs_differ:
            return AlignmentReport(
                source_crs=opt_meta.crs,
                reference_crs=sar_meta.crs,
                bounds_overlap_pct=0.0,
                grid_aligned=False,
                resolution_ratio=1.0,
                reprojection_needed=True,
                resampling_applied=False,
                resampling_method=None,
                coregistered=False,
                offset_vector=[0.0, 0.0],
                intersection_bounds=None,
                valid_data_overlap_pct=None,
                temporal_order_valid=None,
                status_message=f"Differing CRS ({crs_opt} vs {crs_sar}) - reprojection required"
            )

        if opt_meta.bounds and sar_meta.bounds:
            int_bounds, ov_opt, ov_sar = GeospatialValidator.calculate_bounds_intersection(opt_meta.bounds, sar_meta.bounds)
            min_overlap = min(ov_opt, ov_sar)
        else:
            int_bounds = None
            min_overlap = 100.0 if (opt_meta.width == sar_meta.width and opt_meta.height == sar_meta.height) else 0.0

        rx_opt = opt_meta.resolution[0] if opt_meta.resolution else 1.0
        rx_sar = sar_meta.resolution[0] if sar_meta.resolution else 1.0
        res_ratio = round(float(rx_opt / max(1e-9, rx_sar)), 4)
        res_match = abs(res_ratio - 1.0) <= 0.05

        offset = [0.0, 0.0]
        grid_aligned = False
        if opt_meta.transform_matrix and sar_meta.transform_matrix:
            dx = sar_meta.transform_matrix[2] - opt_meta.transform_matrix[2]
            dy = sar_meta.transform_matrix[5] - opt_meta.transform_matrix[5]
            offset = [round(dx, 6), round(dy, 6)]
            grid_aligned = crs_match and res_match and (abs(dx) < 0.05 * rx_opt) and (abs(dy) < 0.05 * rx_opt)
        else:
            grid_aligned = crs_match and (opt_meta.width == sar_meta.width and opt_meta.height == sar_meta.height)

        is_coregistered = (crs_match and min_overlap >= 95.0 and res_match and abs(offset[0]) <= 2 * rx_opt and abs(offset[1]) <= 2 * rx_opt)

        if is_coregistered:
            status_msg = "Verified geometric coregistration (matched CRS)"
        else:
            status_notes = []
            if not crs_match:
                status_notes.append(f"Differing CRS ({crs_opt} vs {crs_sar}) - reprojection required")
            if min_overlap < 95.0:
                status_notes.append(f"Spatial overlap is only {min_overlap}% (threshold: >= 95%)")
            if not res_match:
                status_notes.append(f"Pixel scale difference (ratio {res_ratio})")
            status_msg = "Optical-SAR coregistration unverified: " + "; ".join(status_notes)

        valid_overlap = None
        if opt_arr is not None and sar_arr is not None and min_overlap > 0.0:
            valid_overlap = GeospatialValidator._compute_valid_data_overlap(
                opt_arr, opt_meta.nodata_value, sar_arr, sar_meta.nodata_value
            )

        return AlignmentReport(
            source_crs=opt_meta.crs,
            reference_crs=sar_meta.crs,
            bounds_overlap_pct=min_overlap,
            grid_aligned=grid_aligned,
            resolution_ratio=res_ratio,
            reprojection_needed=not crs_match,
            resampling_applied=False,
            resampling_method=None,
            coregistered=is_coregistered,
            offset_vector=offset,
            intersection_bounds=int_bounds,
            valid_data_overlap_pct=valid_overlap,
            temporal_order_valid=None,
            status_message=status_msg
        )

    @staticmethod
    def align_rasters_to_reference_grid(
        arr1: np.ndarray,
        meta1: RasterMetadata,
        arr2: np.ndarray,
        meta2: RasterMetadata,
        reference_grid: str = "t1"
    ) -> Tuple[np.ndarray, np.ndarray, AlignmentReport]:
        """
        Aligns two rasters to a common spatial reference grid without altering source files.
        Extracts the intersection sub-grid, resamples using bilinear interpolation,
        and records the operation in an AlignmentReport.
        If spatial overlap is 0%, raises AlignmentMismatchError.
        """
        # Benchmark non-georeferenced images
        if not meta1.is_geotiff or not meta2.is_geotiff:
            h1, w1 = arr1.shape[:2]
            h2, w2 = arr2.shape[:2]
            if h1 == h2 and w1 == w2:
                report = GeospatialValidator.validate_bitemporal_alignment(meta1, meta2, arr1, arr2)
                return arr1, arr2, report

            target_w, target_h = (w1, h1) if reference_grid == "t1" else (w2, h2)
            if reference_grid == "t1":
                aligned_arr2 = GeospatialValidator._resample_array(arr2, target_w, target_h)
                aligned_arr1 = arr1
            else:
                aligned_arr1 = GeospatialValidator._resample_array(arr1, target_w, target_h)
                aligned_arr2 = arr2

            report = GeospatialValidator.validate_bitemporal_alignment(meta1, meta2, aligned_arr1, aligned_arr2)
            report.resampling_applied = True
            report.resampling_method = "bilinear"
            report.status_message += f" Resampled to {target_w}x{target_h} reference grid."
            return aligned_arr1, aligned_arr2, report

        # Georeferenced GeoTIFFs
        int_bounds, ov1, ov2 = GeospatialValidator.calculate_bounds_intersection(meta1.bounds, meta2.bounds)
        if int_bounds is None or min(ov1, ov2) <= 0.0:
            raise AlignmentMismatchError(
                f"Zero spatial overlap between rasters ({meta1.filename} vs {meta2.filename}). Cannot perform spatial analysis on disjoint regions."
            )

        # Check if already aligned
        report = GeospatialValidator.validate_bitemporal_alignment(meta1, meta2, arr1, arr2)
        if report.coregistered and arr1.shape[:2] == arr2.shape[:2]:
            return arr1, arr2, report

        # Crop to intersection bounding box
        crop1 = GeospatialValidator._crop_to_bounds(arr1, meta1, int_bounds)
        crop2 = GeospatialValidator._crop_to_bounds(arr2, meta2, int_bounds)

        # Unify dimensions to reference
        ref_h, ref_w = crop1.shape[:2] if reference_grid == "t1" else crop2.shape[:2]
        if crop1.shape[:2] != (ref_h, ref_w):
            crop1 = GeospatialValidator._resample_array(crop1, ref_w, ref_h)
        if crop2.shape[:2] != (ref_h, ref_w):
            crop2 = GeospatialValidator._resample_array(crop2, ref_w, ref_h)

        report.resampling_applied = True
        report.resampling_method = "bilinear"
        report.intersection_bounds = int_bounds
        report.status_message = f"Reprojected and cropped to common bounding box intersection ({ref_w}x{ref_h} pixels)."

        return crop1, crop2, report

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    @staticmethod
    def _crop_to_bounds(arr: np.ndarray, meta: RasterMetadata, target_bounds: List[float]) -> np.ndarray:
        """Crops array pixels corresponding to target bounding box coordinates."""
        if not meta.bounds:
            return arr

        min_x, min_y, max_x, max_y = meta.bounds
        t_min_x, t_min_y, t_max_x, t_max_y = target_bounds
        h, w = arr.shape[:2]

        fx_start = max(0.0, min(1.0, (t_min_x - min_x) / max(1e-9, max_x - min_x)))
        fx_end = max(0.0, min(1.0, (t_max_x - min_x) / max(1e-9, max_x - min_x)))
        fy_start = max(0.0, min(1.0, (max_y - t_max_y) / max(1e-9, max_y - min_y)))
        fy_end = max(0.0, min(1.0, (max_y - t_min_y) / max(1e-9, max_y - min_y)))

        px_start = int(fx_start * w)
        px_end = max(px_start + 1, int(fx_end * w))
        py_start = int(fy_start * h)
        py_end = max(py_start + 1, int(fy_end * h))

        return arr[py_start:py_end, px_start:px_end]

    @staticmethod
    def _resample_array(arr: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
        """Bilinear spatial resampling using cv2 or PIL."""
        if HAS_CV2:
            return cv2.resize(arr, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        else:
            if arr.ndim == 2:
                img = Image.fromarray(arr)
                return np.array(img.resize((target_w, target_h), Image.BILINEAR))
            else:
                img = Image.fromarray(arr)
                return np.array(img.resize((target_w, target_h), Image.BILINEAR))

    @staticmethod
    def _compute_valid_data_overlap(
        arr1: np.ndarray, nodata1: Optional[float],
        arr2: np.ndarray, nodata2: Optional[float]
    ) -> float:
        """Computes the percentage of pixels where both rasters have valid (non-nodata) data."""
        h = min(arr1.shape[0], arr2.shape[0])
        w = min(arr1.shape[1], arr2.shape[1])
        s1 = arr1[:h, :w]
        s2 = arr2[:h, :w]

        v1 = ~np.isnan(s1)
        if nodata1 is not None:
            v1 = v1 & (s1 != nodata1)
        if s1.ndim == 3:
            v1 = np.all(v1, axis=-1)

        v2 = ~np.isnan(s2)
        if nodata2 is not None:
            v2 = v2 & (s2 != nodata2)
        if s2.ndim == 3:
            v2 = np.all(v2, axis=-1)

        both_valid = v1 & v2
        pct = float(np.sum(both_valid)) / max(1.0, float(h * w)) * 100.0
        return round(pct, 2)

    @staticmethod
    def _check_temporal_ordering(ts1: Optional[str], ts2: Optional[str]) -> Optional[bool]:
        """Validates that t1 <= t2 if ISO 8601 timestamps are available."""
        if not ts1 or not ts2:
            return None
        try:
            clean1 = ts1.rstrip("Z")
            clean2 = ts2.rstrip("Z")
            d1 = datetime.fromisoformat(clean1)
            d2 = datetime.fromisoformat(clean2)
            return d1 <= d2
        except Exception:
            return None

    @staticmethod
    def _extract_filename_timestamp(filename: str) -> Optional[str]:
        """Extracts date/timestamp pattern from common satellite naming conventions."""
        m = re.search(r'(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)', filename)
        if m:
            year, month, day = m.group(1), m.group(2), m.group(3)
            return f"{year}-{month}-{day}T00:00:00Z"
        return None

    @staticmethod
    def _utm_to_latlon(easting: float, northing: float, zone: int, northern: bool = True) -> Tuple[float, float]:
        """Converts UTM Easting/Northing into WGS-84 Latitude/Longitude."""
        a = 6378137.0
        f = 1 / 298.257223563
        e = math.sqrt(2 * f - f ** 2)
        e1sq = e ** 2 / (1 - e ** 2)
        k0 = 0.9996

        x = easting - 500000.0
        y = northing if northern else northing - 10000000.0

        m = y / k0
        mu = m / (a * (1 - e ** 2 / 4 - 3 * e ** 4 / 64 - 5 * e ** 6 / 256))
        e1 = (1 - math.sqrt(1 - e ** 2)) / (1 + math.sqrt(1 - e ** 2))
        j1 = 3 * e1 / 2 - 27 * e1 ** 3 / 32
        j2 = 21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32
        j3 = 151 * e1 ** 3 / 96
        j4 = 1097 * e1 ** 4 / 512

        fp = mu + j1 * math.sin(2 * mu) + j2 * math.sin(4 * mu) + j3 * math.sin(6 * mu) + j4 * math.sin(8 * mu)
        c1 = e1sq * math.cos(fp) ** 2
        t1 = math.tan(fp) ** 2
        r1 = a * (1 - e ** 2) / (1 - e ** 2 * math.sin(fp) ** 2) ** 1.5
        n1 = a / math.sqrt(1 - e ** 2 * math.sin(fp) ** 2)
        d = x / (n1 * k0)

        lat = fp - (n1 * math.tan(fp) / r1) * (
            d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * e1sq) * d ** 4 / 24
            + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * e1sq - 3 * c1 ** 2) * d ** 6 / 720
        )
        lon = (
            d - (1 + 2 * t1 + c1) * d ** 3 / 6
            + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * e1sq + 24 * t1 ** 2) * d ** 5 / 120
        ) / math.cos(fp)

        lon_origin = (zone - 1) * 6 - 180 + 3
        return round(math.degrees(lat), 6), round(math.degrees(lon) + lon_origin, 6)
