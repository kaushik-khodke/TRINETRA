import unittest
import numpy as np
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.grounding.spatial_interpreter import SpatialQueryInterpreter
from services.grounding.region_detector import RegionDetector

class TestMultiRegionGrounding(unittest.TestCase):

    def setUp(self):
        # Create a synthetic 100x100 binary mask with two distinct blocks:
        # Block 1: in the West (rows 20..40, cols 10..30) -> small
        # Block 2: in the East (rows 60..90, cols 60..95) -> large
        self.mask = np.zeros((100, 100), dtype=bool)
        self.mask[20:40, 10:30] = True   # Area: 20 * 20 = 400 pixels
        self.mask[60:90, 60:95] = True   # Area: 30 * 35 = 1050 pixels

    def test_extract_all_regions(self):
        intent = SpatialQueryInterpreter.parse("Show all water bodies.")
        regions = RegionDetector.extract_regions_from_mask(self.mask, 100, 100, "Water Body", intent=intent)
        self.assertEqual(len(regions), 2)
        self.assertEqual(regions[0]["id"], "R01")
        self.assertEqual(regions[1]["id"], "R02")

    def test_spatial_constraint_east(self):
        intent = SpatialQueryInterpreter.parse("Find the water body in the east.")
        regions = RegionDetector.extract_regions_from_mask(self.mask, 100, 100, "Water Body", intent=intent)
        self.assertEqual(len(regions), 1)
        # Should only match the eastern block (cols 60..95)
        self.assertGreater(regions[0]["centroid_norm"]["x"], 0.5)

    def test_ranking_largest(self):
        intent = SpatialQueryInterpreter.parse("Find the largest lake.")
        regions = RegionDetector.extract_regions_from_mask(self.mask, 100, 100, "Lake", intent=intent)
        self.assertEqual(len(regions), 1)
        # Should pick the larger block
        self.assertGreater(regions[0]["pixel_area"], 800)

    def test_empty_mask_handling(self):
        empty_mask = np.zeros((100, 100), dtype=bool)
        intent = SpatialQueryInterpreter.parse("Find water.")
        regions = RegionDetector.extract_regions_from_mask(empty_mask, 100, 100, "Water", intent=intent)
        self.assertEqual(len(regions), 0)

if __name__ == "__main__":
    unittest.main()
