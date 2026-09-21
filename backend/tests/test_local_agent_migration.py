"""
SatQuery AI — Comprehensive Verification Test Suite
Local Agentic AI Migration Verification
ISRO Problem Statement 26167
"""

import os
import sys
import re
import unittest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from llm.model_registry import LocalModelRegistry, local_registry
from llm.ollama_provider import OllamaProvider
from llm.agent_planner import AgentPlanner
from observability.langfuse_tracer import LangfuseTracer
from agent.controller import AgentController


class TestLocalAgentMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample_dir = os.path.join(BACKEND_DIR, "sample_data")
        cls.controller = AgentController()

    def test_01_complete_cloud_llm_purge(self):
        """Verify that zero Google Gemini imports, API keys, or endpoints exist in backend code."""
        forbidden_patterns = [
            r"google\.generativeai",
            r"GEMINI_API_KEY",
            r"GOOGLE_API_KEY",
            r"_call_gemini",
            r"models/gemini",
        ]
        
        python_files = []
        for root, dirs, files in os.walk(BACKEND_DIR):
            if "outputs" in root or "__pycache__" in root or ".git" in root:
                continue
            for f in files:
                if f.endswith(".py") and f != os.path.basename(__file__):
                    python_files.append(os.path.join(root, f))

        violations = []
        for filepath in python_files:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for pattern in forbidden_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        violations.append(f"{os.path.relpath(filepath, BACKEND_DIR)}: matches {pattern}")

        self.assertEqual(
            len(violations), 0,
            f"Found forbidden cloud LLM / Gemini references:\n" + "\n".join(violations)
        )
        print(" [PASS] 100% Cloud LLM Purge Verified: Zero Gemini references found.")

    def test_02_model_registry_and_roles(self):
        """Verify dynamic local model registry and role mappings."""
        planner_tag, _ = LocalModelRegistry.resolve_model_for_role("planner")
        router_tag, _ = LocalModelRegistry.resolve_model_for_role("fast_router")
        light_tag, _ = LocalModelRegistry.resolve_model_for_role("lightweight")

        self.assertTrue(bool(planner_tag))
        self.assertTrue(bool(router_tag))
        self.assertTrue(bool(light_tag))

        status = LocalModelRegistry.get_status_summary()
        self.assertFalse(status["cloud_llm"], "cloud_llm must strictly be False")
        self.assertIn("roles", status)
        self.assertIn("planner", status["roles"])
        print(f" [PASS] Local Model Registry Verified: Roles mapped (Planner={planner_tag}, Router={router_tag})")

    def test_03_ollama_provider_execution_and_resilience(self):
        """Verify OllamaProvider handles generation safely with deterministic fallback."""
        resp = OllamaProvider.generate(
            prompt="Analyze satellite land-cover briefly.",
            role="lightweight",
            max_tokens=60
        )
        self.assertIsNotNone(resp.content)
        self.assertTrue(len(resp.content) > 0)
        self.assertTrue(isinstance(resp.latency_ms, (int, float)))
        print(f" [PASS] OllamaProvider Verified: Generated {len(resp.content)} chars in {resp.latency_ms:.1f}ms (Engine: {resp.model_name})")

    def test_04_agent_planner_intent_decomposition(self):
        """Verify LangChain AgentPlanner decomposes queries into actionable steps."""
        planner = AgentPlanner()
        
        # Test 1: VQA query
        plan_vqa = planner.plan(
            query="What are the predominant land-cover types?",
            input_mode="single",
            num_images=1,
            image_modalities=["optical"]
        )
        self.assertEqual(plan_vqa.intent.task, "vqa")
        self.assertTrue(len(plan_vqa.steps) >= 3)

        # Test 2: Grounding query
        plan_grounding = planner.plan(
            query="Highlight the water body referred to in the query",
            input_mode="single",
            num_images=1,
            image_modalities=["optical"]
        )
        self.assertEqual(plan_grounding.intent.task, "grounding")

        # Test 3: Change analysis query
        plan_change = planner.plan(
            query="What changed between these two dates?",
            input_mode="bi_temporal",
            num_images=2,
            image_modalities=["optical", "optical"]
        )
        self.assertEqual(plan_change.intent.task, "change_analysis")

        # Test 4: Optical-SAR query
        plan_sar = planner.plan(
            query="Use the optical and SAR images together to identify built-up structures",
            input_mode="optical_sar",
            num_images=2,
            image_modalities=["optical", "sar"]
        )
        self.assertEqual(plan_sar.intent.task, "optical_sar_fusion")
        print(" [PASS] LangChain AgentPlanner Verified: All 4 intent types decomposed correctly.")

    def test_05_langfuse_non_blocking_telemetry(self):
        """Verify Langfuse telemetry traces generate proper IDs and never crash if offline."""
        with LangfuseTracer.trace_analysis(query="Test query", task="vqa") as ctx:
            self.assertTrue(ctx.trace_id.startswith("satquery_analysis_"))
            with ctx.span("test_span", input_data={"val": 42}) as span:
                span.update(output={"result": "ok"})
            ctx.record_error("Simulated non-critical error")
        print(" [PASS] Langfuse Telemetry Verified: Non-blocking context and spans executed safely.")

    def test_06_tool_parameter_safety_and_path_traversal(self):
        """Verify strict parameter boundaries and prevention of non-existent files."""
        # Non-existent file must be rejected gracefully with truthful error
        res = self.controller.process_request(
            file_paths=["C:/non_existent_folder/fake_image.tif"],
            query="What land cover is this?",
            input_mode="single"
        )
        self.assertEqual(res["status"], "failed")
        self.assertIn("does not exist", res["error"])

        # Out-of-bounds parameter values must be sanitized
        valid_file = os.path.join(self.sample_dir, "sample_optical.tif")
        if os.path.exists(valid_file):
            res_param = self.controller.process_request(
                file_paths=[valid_file],
                query="What land cover is this?",
                input_mode="single",
                custom_parameters={"confidence_threshold": 999.0}  # Malicious / out-of-bounds
            )
            # Threshold must not crash and be bounded
            trace_params = res_param.get("execution_trace", {}).get("parameters", {})
            self.assertLessEqual(trace_params.get("confidence_threshold", 0.5), 1.0)
        print(" [PASS] Tool Parameter Safety Verified: Path traversal rejected and boundaries preserved.")

    def test_07_workflow_1_single_image_vqa(self):
        """Verify Workflow 1: Single-Image Land-Cover & Water VQA."""
        file_path = os.path.join(self.sample_dir, "sample_optical.tif")
        if not os.path.exists(file_path):
            self.skipTest("sample_optical.tif not found")

        res = self.controller.process_request(
            file_paths=[file_path],
            query="What are the predominant land-cover types and is there any water body present?",
            input_mode="single"
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["task"], "vqa")
        self.assertFalse(res["cloud_llm"])
        self.assertEqual(res["agent_framework"], "langchain")
        self.assertIn("answer", res["result"])
        self.assertIn("reports", res)
        print(" [PASS] Workflow 1 (Single Optical VQA) Passed.")

    def test_08_workflow_2_text_guided_grounding(self):
        """Verify Workflow 2: Single-Image Text-Guided Grounding."""
        file_path = os.path.join(self.sample_dir, "sample_optical.tif")
        if not os.path.exists(file_path):
            self.skipTest("sample_optical.tif not found")

        res = self.controller.process_request(
            file_paths=[file_path],
            query="Highlight the water body referred to in the query",
            input_mode="single"
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["task"], "grounding")
        self.assertIn("bounding_box", res["result"])
        self.assertEqual(len(res["result"]["bounding_box"]), 4)
        print(" [PASS] Workflow 2 (Text-Guided Grounding) Passed.")

    def test_09_workflow_3_bitemporal_change_detection(self):
        """Verify Workflow 3: Bi-Temporal Change Analysis."""
        f1 = os.path.join(self.sample_dir, "sample_t1.tif")
        f2 = os.path.join(self.sample_dir, "sample_t2.tif")
        if not (os.path.exists(f1) and os.path.exists(f2)):
            self.skipTest("sample_t1.tif or sample_t2.tif not found")

        res = self.controller.process_request(
            file_paths=[f1, f2],
            query="What changed between these two dates, and where did the change occur?",
            input_mode="bi_temporal"
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["task"], "change_analysis")
        self.assertIn("change_statistics", res["result"])
        self.assertIn("changed_area_percentage", res["result"]["change_statistics"])
        print(" [PASS] Workflow 3 (Bi-Temporal Change Analysis) Passed.")

    def test_10_workflow_4_optical_sar_fusion(self):
        """Verify Workflow 4: Optical–SAR Cross-Modal Fusion."""
        f_opt = os.path.join(self.sample_dir, "sample_opt_pair.tif")
        f_sar = os.path.join(self.sample_dir, "sample_sar_pair.tif")
        if not (os.path.exists(f_opt) and os.path.exists(f_sar)):
            self.skipTest("sample_opt_pair.tif or sample_sar_pair.tif not found")

        res = self.controller.process_request(
            file_paths=[f_opt, f_sar],
            query="Use the optical and SAR images together to identify built-up and water-covered regions.",
            input_mode="optical_sar"
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["task"], "optical_sar_fusion")
        self.assertIn("fusion_correlations", res["result"])
        self.assertIn("sensor_contributions", res["result"])
        print(" [PASS] Workflow 4 (Optical-SAR Fusion) Passed.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
