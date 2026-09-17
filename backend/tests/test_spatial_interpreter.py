import unittest
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.grounding.spatial_interpreter import SpatialQueryInterpreter

class TestSpatialQueryInterpreter(unittest.TestCase):

    def test_water_body_in_east(self):
        intent = SpatialQueryInterpreter.parse("Find the water body in the east.")
        self.assertEqual(intent.target, "water body")
        self.assertEqual(intent.action, "locate")
        self.assertEqual(intent.region_constraint, "east")

    def test_show_all_buildings(self):
        intent = SpatialQueryInterpreter.parse("Show all buildings.")
        self.assertEqual(intent.target, "building")
        self.assertEqual(intent.action, "detect")
        self.assertEqual(intent.count, "all")

    def test_find_largest_lake(self):
        intent = SpatialQueryInterpreter.parse("Find the largest lake.")
        self.assertEqual(intent.target, "lake")
        self.assertEqual(intent.ranking, "largest")

    def test_where_is_the_airport(self):
        intent = SpatialQueryInterpreter.parse("Where is the airport?")
        self.assertEqual(intent.target, "airport")
        self.assertEqual(intent.action, "locate")

    def test_highlight_vegetation_loss_northwest(self):
        intent = SpatialQueryInterpreter.parse("Highlight vegetation loss in the northwest.")
        self.assertEqual(intent.target, "vegetation loss")
        self.assertEqual(intent.action, "highlight")
        self.assertEqual(intent.region_constraint, "northwest")

if __name__ == "__main__":
    unittest.main()
