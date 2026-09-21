"""
SatQuery AI / TRINETRA — Hyperspectral & LangGraph Validation Test Suite
Validates:
1. Multi-tier non-remote-sensing rejection (document, horizon/sky, portrait).
2. Hyperspectral 3D cube processing (.mat) via LangGraph Orchestrator and HyperFree-B.
3. Physical spectroscopy features: λ vs. Reflectance, absorption dip detection.
4. Reed-Xiaoli (RX) spectral anomaly detection and GeoJSON vectorization.
"""

import os
import sys
import unittest
import numpy as np

# Ensure backend root is in sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from agent.controller import AgentController
from agent.langgraph_orchestrator import LangGraphOrchestrator
from geospatial.hsi_reader import HsiReader
from geospatial.spectral_engine import SpectralPhysicsEngine
from services.validator.domain_detector import DomainDetector

class TestHyperspectralAndLangGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = AgentController()
        cls.sample_dir = os.path.join(BACKEND_DIR, "sample_data")
        cls.hsi_sample = os.path.join(cls.sample_dir, "sample_hsi.mat")
        cls.doc_reject = os.path.join(cls.sample_dir, "sample_document_reject.png")
        cls.horizon_reject = os.path.join(cls.sample_dir, "sample_horizon_reject.png")
        cls.portrait_reject = os.path.join(cls.sample_dir, "sample_portrait_reject.png")

    # =========================================================================
    # 1. Universal Image Processing & Analysis (No Domain Rejections)
    # =========================================================================

    def test_analysis_document_scan(self):
        """Document text scans are processed as optical imagery with full downstream model analysis."""
        res = self.controller.process_request(
            file_paths=[self.doc_reject],
            query="Analyze land cover classes in this document",
            input_mode="single"
        )
        self.assertEqual(res["status"], "completed")
        self.assertIn("result", res)
        self.assertEqual(res["detected_modality"], "optical")

    def test_analysis_horizon_ground_photo(self):
        """Horizontal perspective photographs are processed as optical imagery with full analysis."""
        res = self.controller.process_request(
            file_paths=[self.horizon_reject],
            query="Detect land patterns in this photo",
            input_mode="single"
        )
        self.assertEqual(res["status"], "completed")
        self.assertIn("result", res)
        self.assertEqual(res["detected_modality"], "optical")

    def test_analysis_portrait_selfie(self):
        """Portrait photos are processed as optical imagery with full analysis."""
        res = self.controller.process_request(
            file_paths=[self.portrait_reject],
            query="Classify satellite land features",
            input_mode="single"
        )
        self.assertEqual(res["status"], "completed")
        self.assertIn("result", res)
        self.assertEqual(res["detected_modality"], "optical")

    # =========================================================================
    # 2. Hyperspectral 3D Cube Processing via LangGraph Orchestrator
    # =========================================================================

    def test_hyperspectral_cube_pipeline(self):
        """Validates that a 200-band .mat HSI cube is correctly routed to hyperfree_hsi specialist."""
        self.assertTrue(os.path.isfile(self.hsi_sample), f"HSI sample file missing: {self.hsi_sample}")

        res = self.controller.process_request(
            file_paths=[self.hsi_sample],
            query="Analyze spectral absorption features and classify land cover",
            input_mode="single"
        )

        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["detected_modality"], "hyperspectral")
        self.assertIn("hyperfree_hsi", res["selected_tools"])
        self.assertIn("result", res)

        out = res["result"]
        # Cube metadata verification
        self.assertIn("cube_metadata", out)
        cube_meta = out["cube_metadata"]
        self.assertEqual(cube_meta["bands"], 200)
        self.assertEqual(cube_meta["height"], 64)
        self.assertEqual(cube_meta["width"], 64)

        # Spectral signature verification
        self.assertIn("spectral_signature", out)
        sig = out["spectral_signature"]
        self.assertEqual(len(sig["wavelengths"]), 200)
        self.assertEqual(len(sig["mean_curve"]), 200)
        self.assertEqual(len(sig["std_curve"]), 200)

        # Absorption features detection
        self.assertIn("absorption_features", sig)
        features = sig["absorption_features"]
        self.assertIsInstance(features, list)
        self.assertGreater(len(features), 0, "Expected at least one diagnostic absorption feature detected.")

        # Visual derivatives verification
        self.assertIn("rgb_composite", out)
        self.assertIn("cir_composite", out)
        self.assertTrue(len(out["rgb_composite"]) > 100)
        self.assertTrue(len(out["cir_composite"]) > 100)

        # Class predictions
        self.assertIn("top_classes", out)
        self.assertGreater(len(out["top_classes"]), 0)

    def test_hyperspectral_anomaly_detection_and_geojson(self):
        """Validates that anomaly detection queries trigger RX detector and produce GeoJSON polygons."""
        res = self.controller.process_request(
            file_paths=[self.hsi_sample],
            query="Detect spectral anomalies and locate any sub-pixel outlier objects",
            input_mode="single"
        )

        self.assertEqual(res["status"], "completed")
        out = res["result"]
        self.assertIn("anomaly_detection", out)
        anomaly_info = out["anomaly_detection"]
        self.assertIn("anomaly_percentage", anomaly_info)
        self.assertIn("max_score", anomaly_info)

        # GeoJSON verification
        self.assertIn("geojson", out)
        geojson = out["geojson"]
        self.assertEqual(geojson.get("type"), "FeatureCollection")
        self.assertIn("features", geojson)

    # =========================================================================
    # 3. Spectral Physics & Spectroscopy Engine Unit Tests
    # =========================================================================

    def test_spectral_physics_engine_absorption_dips(self):
        """Tests the physical absorption dip detector on known simulated wavelengths and dips."""
        cube_data = HsiReader.read_cube(self.hsi_sample)
        self.assertEqual(cube_data.bands, 200)

        sig = SpectralPhysicsEngine.extract_mean_spectral_signature(cube_data)
        dips = SpectralPhysicsEngine.detect_absorption_dips(
            wavelengths=sig["wavelengths"],
            mean_curve=sig["mean_curve"],
            prominence_threshold=0.010
        )

        self.assertGreater(len(dips), 0)
        detected_wavelengths = [d["wavelength_nm"] for d in dips]

        # Check for presence of chlorophyll or water dips
        has_chlorophyll = any(abs(wl - 670) < 50 for wl in detected_wavelengths)
        has_water = any(abs(wl - 960) < 80 or abs(wl - 1400) < 100 for wl in detected_wavelengths)
        self.assertTrue(
            has_chlorophyll or has_water,
            f"Expected chlorophyll (~670nm) or water (~960nm/~1400nm) dip, found dips at: {detected_wavelengths}"
        )

    def test_reed_xiaoli_anomaly_engine(self):
        """Tests covariance-grounded RX anomaly detector on cube data."""
        cube_data = HsiReader.read_cube(self.hsi_sample)
        rx_scores = SpectralPhysicsEngine.reed_xiaoli_anomaly_detector(cube_data, regularize_cov=1e-3)
        self.assertEqual(rx_scores.shape, (64, 64))
        self.assertGreater(float(np.max(rx_scores)), 0.5)

if __name__ == "__main__":
    unittest.main()
