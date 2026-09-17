import unittest
import os
import sys
import numpy as np
from PIL import Image

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from agent.controller import AgentController
from services.reports.report_service import MissionReportGenerator

class TestStructuredIntelligenceWorkstation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.controller = AgentController()
        cls.tmp_dir = os.path.join(BACKEND_DIR, "scratch", "test_intel_assets")
        os.makedirs(cls.tmp_dir, exist_ok=True)

        # Create a test synthetic satellite image:
        # Green vegetation background, blue water body in NE quadrant (rows 10..50, cols 150..220)
        # and built-up structures in SW quadrant (rows 150..220, cols 10..80)
        arr = np.zeros((256, 256, 3), dtype=np.uint8)
        arr[:, :] = [34, 139, 34]  # Forest Green
        arr[10:50, 150:220] = [30, 144, 255]  # Dodger Blue (Water in NE)
        arr[150:220, 10:80] = [180, 180, 180]  # Light Gray (Structures in SW)

        cls.test_img_path = os.path.join(cls.tmp_dir, "test_scene.png")
        Image.fromarray(arr).save(cls.test_img_path)

    def test_water_body_grounding_and_structured_schema(self):
        query = "Highlight all water bodies and tell me which one is the largest."
        res = self.controller.process_request(
            file_paths=[self.test_img_path],
            query=query,
            input_mode="single",
            declared_modalities=["optical"],
            response_language="en"
        )

        self.assertEqual(res["status"], "completed")
        self.assertIn("structured_intelligence", res)
        intel = res["structured_intelligence"]

        # Check schema
        self.assertIn("summary", intel)
        self.assertIn("findings", intel)
        self.assertIn("regions", intel)
        self.assertIn("evidence", intel)
        self.assertIn("measurements", intel)
        self.assertIn("spatial_context", intel)
        self.assertIn("uncertainty", intel)
        self.assertIn("recommendations", intel)
        self.assertIn("visual_outputs", intel)

        # Findings taxonomy check
        types = [f["type"] for f in intel["findings"]]
        self.assertTrue(any(t in ["observed", "inferred", "uncertain"] for t in types))

        # Backward compatibility check
        self.assertIn("answer", res)
        self.assertIn("regions", res["result"])
        self.assertIn("bounding_box", res["result"])
        self.assertIn("evidence_image", res["result"])

    def test_spatial_query_northeast(self):
        query = "What is in the north-east corner?"
        res = self.controller.process_request(
            file_paths=[self.test_img_path],
            query=query,
            input_mode="single",
            declared_modalities=["optical"],
            response_language="en"
        )
        self.assertEqual(res["status"], "completed")
        self.assertIn("structured_intelligence", res)

    def test_html_report_generation_with_evidence_gallery(self):
        query = "Locate the water body in the east."
        res = self.controller.process_request(
            file_paths=[self.test_img_path],
            query=query,
            input_mode="single",
            declared_modalities=["optical"],
            response_language="en"
        )
        report_path = os.path.join(self.tmp_dir, "mission_report_test.html")
        MissionReportGenerator.generate_html_report(res, report_path)
        self.assertTrue(os.path.isfile(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("Evidence Gallery", html)
        self.assertIn("Traceable Radiometric", html)
        self.assertIn("Detected Regions", html)

if __name__ == "__main__":
    unittest.main()
