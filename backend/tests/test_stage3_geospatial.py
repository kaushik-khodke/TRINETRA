"""
TRINETRA — Stage 3 Geospatial Validation & Preprocessing Test Suite
Verifies:
1. True raster metadata inspection (CRS, affine transform, bounds, resolution, nodata, temporal).
2. Bounds intersection mathematics and overlap percentages.
3. 10-point bi-temporal validation checks and disjoint rejection.
4. Optical-SAR geometric coregistration verification without naive assumptions.
5. Sensor-aware optical and SAR preprocessing (bit-depth scaling, dB conversion, speckle policy).
6. Dynamic spectral physics indices on genuine multispectral vs RGB proxies.
7. Specialist service integration with typed AlignmentReport manifests.
Governed by 03_STAGE_3_GEOSPATIAL.md.
"""

import os
import sys
import pytest
import numpy as np

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from schemas.contracts import RasterMetadata, AlignmentReport
from core.exceptions import AlignmentMismatchError
from geospatial.reader import GeospatialReader
from geospatial.validator import GeospatialValidator
from geospatial.normalizer import GeospatialNormalizer
from services.change.change_service import BiTemporalChangeSpecialist
from services.optical_sar.optical_sar_service import OpticalSarFusionSpecialist
from services.validator.validator import InputValidator

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data")


class TestStage3RasterInspection:
    """Verifies complete 11-point raster header inspection."""

    def test_sentinel2_metadata_inspection(self):
        s2_path = os.path.join(SAMPLE_DIR, "sentinel2_koradi_nagpur.tif")
        if not os.path.exists(s2_path):
            pytest.skip("sentinel2_koradi_nagpur.tif not found")

        meta = GeospatialValidator.inspect_raster_metadata(s2_path)
        assert meta.schema_version == "2.0.0"
        assert meta.is_geotiff is True
        assert meta.band_count == 4
        assert meta.crs == "EPSG:4326"
        assert meta.bounds is not None
        assert len(meta.bounds) == 4
        assert meta.bounds[0] < meta.bounds[2]  # minx < maxx
        assert meta.bounds[1] < meta.bounds[3]  # miny < maxy
        assert meta.resolution is not None
        assert len(meta.resolution) == 2
        assert meta.resolution[0] > 0
        assert meta.transform_matrix is not None
        assert len(meta.transform_matrix) == 6
        assert "Sentinel-2" in meta.sensor_name
        assert meta.band_descriptions is not None
        assert len(meta.band_descriptions) == 4

    def test_bitemporal_samples_metadata(self):
        t1_path = os.path.join(SAMPLE_DIR, "sample_t1.tif")
        meta1 = GeospatialValidator.inspect_raster_metadata(t1_path)
        assert meta1.is_geotiff is True
        assert meta1.crs == "EPSG:4326"
        assert meta1.width == 256
        assert meta1.height == 256
        assert meta1.center_lat is not None
        assert meta1.center_lng is not None
        assert meta1.has_geographic_location is True

    def test_benchmark_image_inspection(self):
        png_path = os.path.join(SAMPLE_DIR, "sample_optical.png")
        if not os.path.exists(png_path):
            pytest.skip("sample_optical.png not found")

        meta = GeospatialValidator.inspect_raster_metadata(png_path)
        assert meta.is_geotiff is False
        assert meta.crs is None
        assert meta.bounds is None
        assert meta.has_geographic_location is False
        assert "Benchmark" in meta.sensor_name


class TestStage3IntersectionMath:
    """Verifies analytical bounding box intersection and overlap mathematics."""

    def test_identical_bounds_full_overlap(self):
        b1 = [72.86, 19.06, 72.88, 19.09]
        b2 = [72.86, 19.06, 72.88, 19.09]
        int_box, ov1, ov2 = GeospatialValidator.calculate_bounds_intersection(b1, b2)
        assert int_box == b1
        assert ov1 == 100.0
        assert ov2 == 100.0

    def test_partial_overlap(self):
        b1 = [0.0, 0.0, 10.0, 10.0]  # area = 100
        b2 = [5.0, 0.0, 15.0, 10.0]  # area = 100, intersection = [5, 0, 10, 10] -> area 50
        int_box, ov1, ov2 = GeospatialValidator.calculate_bounds_intersection(b1, b2)
        assert int_box == [5.0, 0.0, 10.0, 10.0]
        assert ov1 == 50.0
        assert ov2 == 50.0

    def test_completely_disjoint_bounds(self):
        b1 = [72.86, 19.06, 72.88, 19.09]  # Mumbai
        b2 = [80.25, 13.07, 80.27, 13.10]  # Chennai
        int_box, ov1, ov2 = GeospatialValidator.calculate_bounds_intersection(b1, b2)
        assert int_box is None
        assert ov1 == 0.0
        assert ov2 == 0.0


class TestStage3BitemporalValidation:
    """Verifies 10-point bitemporal alignment checks and disjoint rejection."""

    def test_bitemporal_identical_pair_passes(self):
        t1_path = os.path.join(SAMPLE_DIR, "sample_t1.tif")
        t2_path = os.path.join(SAMPLE_DIR, "sample_t2.tif")
        arr1, meta1 = GeospatialReader.read_image(t1_path)
        arr2, meta2 = GeospatialReader.read_image(t2_path)

        report = GeospatialValidator.validate_bitemporal_alignment(meta1, meta2, arr1, arr2)
        assert report.bounds_overlap_pct == 100.0
        assert report.grid_aligned is True
        assert report.resolution_ratio == 1.0
        assert report.reprojection_needed is False
        assert report.coregistered is True
        assert report.valid_data_overlap_pct == 100.0

    def test_bitemporal_disjoint_rejection(self):
        t1_path = os.path.join(SAMPLE_DIR, "sample_t1.tif")
        chennai_path = os.path.join(SAMPLE_DIR, "sample_opt_pair.tif")
        arr1, meta1 = GeospatialReader.read_image(t1_path)
        arr2, meta2 = GeospatialReader.read_image(chennai_path)

        report = GeospatialValidator.validate_bitemporal_alignment(meta1, meta2, arr1, arr2)
        assert report.bounds_overlap_pct == 0.0
        assert report.coregistered is False

        # Verify align_rasters_to_reference_grid raises AlignmentMismatchError on 0% overlap
        with pytest.raises(AlignmentMismatchError):
            GeospatialValidator.align_rasters_to_reference_grid(arr1, meta1, arr2, meta2)

    def test_bitemporal_temporal_ordering(self):
        assert GeospatialValidator._check_temporal_ordering("2023-01-01T00:00:00Z", "2023-06-01T00:00:00Z") is True
        assert GeospatialValidator._check_temporal_ordering("2024-01-01T00:00:00Z", "2023-01-01T00:00:00Z") is False
        assert GeospatialValidator._check_temporal_ordering(None, "2023-01-01T00:00:00Z") is None


class TestStage3OpticalSarCoregistration:
    """Verifies true geometric Optical-SAR coregistration without naive CRS assumption."""

    def test_optical_sar_valid_pair_coregistered(self):
        opt_path = os.path.join(SAMPLE_DIR, "sample_opt_pair.tif")
        sar_path = os.path.join(SAMPLE_DIR, "sample_sar_pair.tif")
        arr_opt, meta_opt = GeospatialReader.read_image(opt_path)
        arr_sar, meta_sar = GeospatialReader.read_image(sar_path)

        report = GeospatialValidator.validate_optical_sar_coregistration(meta_opt, meta_sar, arr_opt, arr_sar)
        assert report.coregistered is True
        assert report.bounds_overlap_pct == 100.0
        assert report.resolution_ratio == 1.0

    def test_optical_sar_disjoint_not_coregistered_despite_same_crs(self):
        # Both are EPSG:4326, but t1 is Mumbai and sar_pair is Chennai
        t1_path = os.path.join(SAMPLE_DIR, "sample_t1.tif")
        sar_path = os.path.join(SAMPLE_DIR, "sample_sar_pair.tif")
        arr_t1, meta_t1 = GeospatialReader.read_image(t1_path)
        arr_sar, meta_sar = GeospatialReader.read_image(sar_path)

        assert meta_t1.crs == meta_sar.crs  # Both EPSG:4326
        report = GeospatialValidator.validate_optical_sar_coregistration(meta_t1, meta_sar, arr_t1, arr_sar)
        assert report.coregistered is False
        assert report.bounds_overlap_pct == 0.0
        assert "Spatial overlap is only 0.0%" in report.status_message


class TestStage3SensorPreprocessing:
    """Verifies sensor-aware normalization, bit-depth handling, nodata masking, and SAR dB."""

    def test_optical_uint8_scaling(self):
        arr = np.array([[0, 127], [255, 64]], dtype=np.uint8)
        norm, manifest = GeospatialNormalizer.preprocess_optical(arr)
        assert norm.dtype == np.float32
        assert np.isclose(norm[0, 0], 0.0)
        assert np.isclose(norm[1, 0], 1.0)
        assert manifest["reflectance_scaling"] == round(1.0 / 255.0, 6)
        assert manifest["valid_pixel_pct"] == 100.0

    def test_optical_uint16_surface_reflectance_scaling(self):
        # Sentinel-2 L2A surface reflectance where 10000 = 100% reflectance
        arr = np.array([[1000, 2000], [5000, 10000]], dtype=np.uint16)
        norm, manifest = GeospatialNormalizer.preprocess_optical(arr)
        assert np.isclose(norm[1, 1], 1.0)
        assert np.isclose(norm[0, 0], 0.1)
        assert "Surface Reflectance" in manifest["normalization_strategy"]

    def test_optical_nodata_masking(self):
        arr = np.array([[100, -9999], [50, 80]], dtype=np.float32)
        meta = RasterMetadata(
            width=2, height=2, band_count=1, dtype="float32", nodata_value=-9999.0
        )
        norm, manifest = GeospatialNormalizer.preprocess_optical(arr, meta)
        assert manifest["nodata_mask_pct"] == 25.0
        assert manifest["valid_pixel_pct"] == 75.0

    def test_sar_linear_to_db_conversion(self):
        # Linear amplitude: 1.0 -> 0 dB, 10.0 -> 10 dB, 0.1 -> -10 dB
        arr = np.array([[1.0, 10.0], [0.1, 100.0]], dtype=np.float32)
        db, manifest = GeospatialNormalizer.preprocess_sar(arr, apply_speckle_filter=False)
        assert np.isclose(db[0, 0], 0.0, atol=1e-3)
        assert np.isclose(db[0, 1], 10.0, atol=1e-3)
        assert np.isclose(db[1, 0], -10.0, atol=1e-3)
        assert np.isclose(db[1, 1], 20.0, atol=1e-3)
        assert manifest["calibration_state"] == "Radiometrically Calibrated \u03c3\u2070 dB"
        assert "Raw radar radiometry preserved" in manifest["speckle_policy"]

    def test_sar_speckle_filter_policy(self):
        arr = np.random.uniform(0.1, 10.0, (16, 16)).astype(np.float32)
        _, manifest = GeospatialNormalizer.preprocess_sar(arr, apply_speckle_filter=True, filter_size=3)
        assert "Median Filter applied" in manifest["speckle_policy"]


class TestStage3SpectralIndices:
    """Verifies spectral indices on physical multispectral bands vs RGB proxy."""

    def test_multispectral_ndvi_ndwi_physics(self):
        # 4 bands: B2-Blue, B3-Green, B4-Red, B8-NIR
        h, w = 10, 10
        cube = np.zeros((h, w, 4), dtype=np.float32)
        cube[:, :, 0] = 0.05  # Blue
        cube[:, :, 1] = 0.10  # Green
        cube[:, :, 2] = 0.05  # Red
        cube[:, :, 3] = 0.45  # NIR (Dense Vegetation)

        results = GeospatialNormalizer.compute_spectral_indices(cube)
        assert results["index_mode"] == "multispectral_physical_bands"
        # NDVI = (0.45 - 0.05) / (0.45 + 0.05) = 0.40 / 0.50 = 0.80
        assert np.isclose(results["mean_ndvi"], 0.80, atol=1e-2)
        # NDWI = (0.10 - 0.45) / (0.10 + 0.45) = -0.35 / 0.55 = -0.636
        assert np.isclose(results["mean_ndwi"], -0.636, atol=1e-2)

    def test_rgb_proxy_vari_and_disclaimer(self):
        rgb = np.full((10, 10, 3), 128, dtype=np.uint8)
        results = GeospatialNormalizer.compute_spectral_indices(rgb)
        assert results["index_mode"] == "RGB_visual_proxy"
        assert results["disclaimer"] is not None
        assert "VARI" in results["disclaimer"]


class TestStage3SpecialistIntegration:
    """Verifies specialist services return typed AlignmentReports and reject disjoint rasters."""

    def test_change_specialist_execution_with_alignment(self):
        t1_path = os.path.join(SAMPLE_DIR, "sample_t1.tif")
        t2_path = os.path.join(SAMPLE_DIR, "sample_t2.tif")
        arr1, meta1 = GeospatialReader.read_image(t1_path)
        arr2, meta2 = GeospatialReader.read_image(t2_path)

        specialist = BiTemporalChangeSpecialist()
        result = specialist.execute(
            images_arr=[arr1, arr2],
            metas=[meta1.to_dict(), meta2.to_dict()],
            query="What changed between T1 and T2?",
            parameters={"response_language": "en"}
        )

        assert "alignment_report" in result
        rep = result["alignment_report"]
        assert rep["coregistered"] is True
        assert rep["bounds_overlap_pct"] == 100.0
        assert result["task"] == "change_analysis"

    def test_change_specialist_disjoint_rejection(self):
        t1_path = os.path.join(SAMPLE_DIR, "sample_t1.tif")
        chennai_path = os.path.join(SAMPLE_DIR, "sample_opt_pair.tif")
        arr1, meta1 = GeospatialReader.read_image(t1_path)
        arr2, meta2 = GeospatialReader.read_image(chennai_path)

        specialist = BiTemporalChangeSpecialist()
        with pytest.raises(AlignmentMismatchError):
            specialist.execute(
                images_arr=[arr1, arr2],
                metas=[meta1.to_dict(), meta2.to_dict()],
                query="What changed?",
                parameters={"response_language": "en"}
            )

    def test_optical_sar_specialist_execution_with_alignment(self):
        opt_path = os.path.join(SAMPLE_DIR, "sample_opt_pair.tif")
        sar_path = os.path.join(SAMPLE_DIR, "sample_sar_pair.tif")
        arr_opt, meta_opt = GeospatialReader.read_image(opt_path)
        arr_sar, meta_sar = GeospatialReader.read_image(sar_path)

        specialist = OpticalSarFusionSpecialist()
        result = specialist.execute(
            images_arr=[arr_opt, arr_sar],
            metas=[meta_opt.to_dict(), meta_sar.to_dict()],
            query="Analyze fused optical and SAR imagery",
            parameters={"response_language": "en"}
        )

        assert "alignment_report" in result
        rep = result["alignment_report"]
        assert rep["coregistered"] is True
        assert rep["bounds_overlap_pct"] == 100.0
        assert "preprocessing_manifests" in result
        assert "optical" in result["preprocessing_manifests"]
        assert "sar" in result["preprocessing_manifests"]

    def test_input_validator_disjoint_geotiff_rejection(self):
        t1_path = os.path.join(SAMPLE_DIR, "sample_t1.tif")
        chennai_path = os.path.join(SAMPLE_DIR, "sample_opt_pair.tif")

        val = InputValidator.validate([t1_path, chennai_path], requested_mode="bi_temporal")
        assert val.valid is False
        assert "0.0% spatial overlap" in val.error_message
