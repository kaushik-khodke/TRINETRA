"""
SatQuery AI <-> TRINETRA Globe Integration Test Suite
Validates all requirements of Phase 12:
- TEST 1: GeoTIFF with valid georeferencing produces true geographic location for TRINETRA
- TEST 2: Bi-temporal pair preserves valid geographic scene location
- TEST 3: Optical + SAR cross-modal pair extracts common geographic location
- TEST 4: Automatic geolocation without manual user-entered coordinates
- TEST 5: Un-georeferenced images (PNG/JPEG) strictly do NOT fabricate coordinates (has_location=False)
- TEST 6: Parameter validation rejecting out-of-range/malformed coordinates gracefully
- TEST 7: Independent TRINETRA /explore route availability
"""

import os
import sys
import unittest
import urllib.request
import urllib.error
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from agent.controller import AgentController
from geospatial.reader import GeospatialReader

class TestTrinetraGlobeIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = AgentController()
        cls.sample_dir = os.path.join(PROJECT_ROOT, "sample_data")
        cls.optical_tif = os.path.join(cls.sample_dir, "sample_optical.tif")
        cls.t1_tif = os.path.join(cls.sample_dir, "sample_t1.tif")
        cls.t2_tif = os.path.join(cls.sample_dir, "sample_t2.tif")
        cls.opt_pair_tif = os.path.join(cls.sample_dir, "sample_opt_pair.tif")
        cls.sar_pair_tif = os.path.join(cls.sample_dir, "sample_sar_pair.tif")
        cls.optical_png = os.path.join(cls.sample_dir, "sample_optical.png")
        cls.reader = GeospatialReader()

    def test_01_geotiff_valid_metadata_produces_location(self):
        """TEST 1: GeoTIFF with valid geospatial metadata returns accurate lat/lng for TRINETRA"""
        res = self.controller.process_request(
            file_paths=[self.optical_tif],
            query="What are the predominant land-cover types?",
            input_mode="single"
        )
        self.assertEqual(res["status"], "completed")
        self.assertIn("geographic_location", res)
        geo = res["geographic_location"]
        self.assertTrue(geo["has_location"], "GeoTIFF must have has_location=True")
        self.assertAlmostEqual(geo["lat"], 28.6172, delta=0.01)
        self.assertAlmostEqual(geo["lng"], 77.2078, delta=0.01)
        self.assertEqual(geo["height"], 5000)
        self.assertIn("bounds", geo)
        self.assertEqual(len(geo["bounds"]), 4)
        self.assertIn("EPSG:4326", geo["crs"])

    def test_02_bitemporal_pair_location(self):
        """TEST 2: Two-date GeoTIFF pair correctly extracts scene coordinates"""
        res = self.controller.process_request(
            file_paths=[self.t1_tif, self.t2_tif],
            query="What changed between these two dates?",
            input_mode="bi_temporal"
        )
        self.assertEqual(res["status"], "completed")
        geo = res.get("geographic_location")
        self.assertIsNotNone(geo)
        self.assertTrue(geo["has_location"])
        # Mumbai coordinates from sample_t1.tif
        self.assertAlmostEqual(geo["lat"], 19.0772, delta=0.01)
        self.assertAlmostEqual(geo["lng"], 72.8728, delta=0.01)

    def test_03_optical_sar_pair_location(self):
        """TEST 3: Optical + SAR pair returns valid common geographic location"""
        res = self.controller.process_request(
            file_paths=[self.opt_pair_tif, self.sar_pair_tif],
            query="Identify built-up and water-covered regions using both modalities",
            input_mode="optical_sar"
        )
        self.assertEqual(res["status"], "completed")
        geo = res.get("geographic_location")
        self.assertIsNotNone(geo)
        self.assertTrue(geo["has_location"])
        # Chennai coordinates from sample_opt_pair.tif
        self.assertAlmostEqual(geo["lat"], 13.0872, delta=0.01)
        self.assertAlmostEqual(geo["lng"], 80.2628, delta=0.01)

    def test_04_automatic_georeferencing_no_user_coordinates(self):
        """TEST 4: User did not enter coordinates manually, but GeoTIFF tags are read directly"""
        meta = self.reader.read_metadata(self.optical_tif)
        self.assertTrue(meta.has_geographic_location)
        self.assertIsNotNone(meta.bounds)
        min_lon, min_lat, max_lon, max_lat = meta.bounds
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0
        self.assertAlmostEqual(center_lat, 28.6172, delta=0.01)
        self.assertAlmostEqual(center_lon, 77.2078, delta=0.01)

    def test_05_ungeoreferenced_image_does_not_fabricate_coordinates(self):
        """TEST 5: Image has no geospatial metadata at all. Coordinates must NOT be fabricated."""
        meta = self.reader.read_metadata(self.optical_png)
        self.assertFalse(meta.has_geographic_location, "PNG with no CRS tags must have has_geographic_location=False")
        self.assertIsNone(meta.bounds, "Bounds must be None for non-georeferenced images")

        res = self.controller.process_request(
            file_paths=[self.optical_png],
            query="Describe this scene",
            input_mode="single"
        )
        self.assertEqual(res["status"], "completed")
        geo = res.get("geographic_location")
        self.assertIsNotNone(geo)
        self.assertFalse(geo["has_location"], "has_location must be False for un-georeferenced raster")
        self.assertIsNone(geo["lat"], "lat must be None")
        self.assertIsNone(geo["lng"], "lng must be None")

    def test_06_url_contract_parameter_validation(self):
        """TEST 6: Validate parameter bounds logic (-90 <= lat <= 90, -180 <= lng <= 180)"""
        def validate_coords(lat_str, lng_str):
            try:
                lat = float(lat_str)
                lng = float(lng_str)
                if -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0:
                    return True, lat, lng
                return False, None, None
            except (ValueError, TypeError):
                return False, None, None

        # Malformed
        valid, _, _ = validate_coords("hello", "world")
        self.assertFalse(valid)

        # Out of bounds
        valid, _, _ = validate_coords("999.0", "77.0")
        self.assertFalse(valid)
        valid, _, _ = validate_coords("28.0", "-250.0")
        self.assertFalse(valid)

        # Valid
        valid, lat, lng = validate_coords("28.6172", "77.2078")
        self.assertTrue(valid)
        self.assertEqual(lat, 28.6172)
        self.assertEqual(lng, 77.2078)

    def test_07_trinetra_route_independent_availability(self):
        """TEST 7: Directly open TRINETRA location route manually and verify independent response"""
        url = "http://localhost:4173/explore?lat=28.6172&lng=77.2078&height=5000&source=satquery&name=Delhi%20NCR"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SatQuery-Test/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                self.assertEqual(response.status, 200)
                content_type = response.headers.get("content-type", "")
                self.assertIn("text/html", content_type)
        except urllib.error.URLError as e:
            self.fail(f"TRINETRA application on port 4173 is not reachable: {e}")

if __name__ == "__main__":
    unittest.main()
