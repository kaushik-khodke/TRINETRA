"""
SatQuery AI — Pipeline Integration Tests
Validates Single-image VQA, Captioning, Grounding, Bi-Temporal Change,
Optical–SAR Fusion, and Input Validation failure handling.
"""

import os
import sys
import unittest

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from agent.controller import AgentController

class TestSatQueryAIPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = AgentController()
        cls.sample_dir = os.path.join(PROJECT_ROOT, "sample_data")
        cls.optical_sample = os.path.join(cls.sample_dir, "sample_optical.tif")
        cls.sar_sample = os.path.join(cls.sample_dir, "sample_sar.tif")
        cls.t1_sample = os.path.join(cls.sample_dir, "sample_t1.tif")
        cls.t2_sample = os.path.join(cls.sample_dir, "sample_t2.tif")
        cls.opt_pair = os.path.join(cls.sample_dir, "sample_opt_pair.tif")
        cls.sar_pair = os.path.join(cls.sample_dir, "sample_sar_pair.tif")

    def test_single_image_vqa(self):
        res = self.controller.process_request(
            file_paths=[self.optical_sample],
            query="What are the predominant land-cover types and is there any water body present?",
            input_mode="single"
        )
        self.assertEqual(res["status"], "completed")
        self.assertIn("vqa", res["task"])
        self.assertGreater(res["confidence"], 0.70)
        self.assertIn("execution_trace", res)

    def test_single_image_grounding(self):
        res = self.controller.process_request(
            file_paths=[self.optical_sample],
            query="Highlight the water body referred to in the query",
            input_mode="single"
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["task"], "grounding")
        self.assertIn("regions", res["result"])
        self.assertIn("evidence_image", res["result"])

    def test_single_image_captioning(self):
        res = self.controller.process_request(
            file_paths=[self.optical_sample],
            query="Provide a comprehensive scene description and land cover summary",
            input_mode="single"
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["task"], "captioning")
        self.assertIn("caption", res["result"])

    def test_bitemporal_change_detection(self):
        res = self.controller.process_request(
            file_paths=[self.t1_sample, self.t2_sample],
            query="What changed between these two dates, and where did the change occur?",
            input_mode="bi_temporal"
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["task"], "change_analysis")
        self.assertIn("change_statistics", res["result"])
        self.assertIn("evidence", res["result"])

    def test_optical_sar_fusion(self):
        res = self.controller.process_request(
            file_paths=[self.opt_pair, self.sar_pair],
            query="Use the optical and SAR images together to identify built-up and water-covered regions.",
            input_mode="optical_sar",
            declared_modalities=["optical", "sar"]
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["task"], "optical_sar_fusion")
        self.assertIn("sensor_contributions", res["result"])
        self.assertIn("evidence", res["result"])

    def test_invalid_input_rejection(self):
        # 1 image passed to paired mode should fail cleanly
        res = self.controller.process_request(
            file_paths=[self.optical_sample],
            query="What changed between these dates?",
            input_mode="bi_temporal"
        )
        self.assertEqual(res["status"], "failed")
        self.assertIn("error", res)

if __name__ == "__main__":
    unittest.main()
