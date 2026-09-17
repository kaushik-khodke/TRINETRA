"""
TRINETRA Unified Benchmark and Evaluation Framework (Stage 8)
Governed by 08_STAGE_8_BENCHMARK_FRAMEWORK.md and NON_NEGOTIABLE_PRINCIPLES.md.
"""

from backend.evaluation.benchmark_registry import BenchmarkRegistry, default_registry
from backend.evaluation.runner import UnifiedBenchmarkRunner, default_runner
from backend.evaluation.reporter import BenchmarkReporter

__all__ = [
    "BenchmarkRegistry",
    "default_registry",
    "UnifiedBenchmarkRunner",
    "default_runner",
    "BenchmarkReporter",
]
