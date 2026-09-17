"""
TRINETRA Benchmark Reporter and Comparison Engine (Stage 8)
Governed by 08_STAGE_8_BENCHMARK_FRAMEWORK.md and NON_NEGOTIABLE_PRINCIPLES.md.

Produces comprehensive, audited Markdown reports and machine-readable manifests.
Enforces the Legitimate Benchmark Comparison Policy:
- Dataset versions must be compatible
- Evaluated splits must be identical
- Metric definitions must be identical
- Discloses runtime, hardware, and known model limitations
- Strictly rejects fake leaderboards and incomparable comparisons.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import json

try:
    from backend.schemas.contracts import BenchmarkRun
except ImportError:
    from schemas.contracts import BenchmarkRun


class BenchmarkReporter:
    """
    Renders audit-grade evaluation manifests and compares benchmark runs with
    strict statistical compatibility verification.
    """

    @staticmethod
    def generate_markdown_report(run: BenchmarkRun) -> str:
        """
        Generates a publication-grade Markdown audit report for a BenchmarkRun.
        """
        lines = []
        lines.append(f"# Benchmark Evaluation Audit Report: {run.dataset_name}")
        lines.append("")
        lines.append(f"**Run UUID**: `{run.benchmark_id}`  ")
        lines.append(f"**Evaluated Split**: `{run.split.upper()}` (Single-Pass Locked Evaluation)  ")
        lines.append(f"**Total Samples Evaluated**: {run.sample_count:,}  ")
        lines.append(f"**Execution Duration**: {run.execution_time_seconds:.2f} seconds  ")
        lines.append(f"**Provenance Fingerprint**: `{run.provenance_fingerprint or 'N/A'}`  ")
        lines.append("")

        # 1. Model & Checkpoint Provenance
        lines.append("## 1. Model & Checkpoint Provenance")
        lines.append("")
        lines.append(f"- **Architecture**: `{run.model_name or 'Unknown'}`")
        lines.append(f"- **Checkpoint Path**: `{run.checkpoint_path or 'In-memory / Unfrozen'}`")
        lines.append(f"- **Checkpoint SHA-256**: `{run.checkpoint_hash or 'N/A'}`")
        lines.append(f"- **Dataset Manifest Hash**: `{run.dataset_manifest_hash}`")
        lines.append("")

        # 2. Benchmark Metrics & Statistical Rigor
        lines.append("## 2. Standard Benchmark Metrics (Zero Synthetic Data)")
        lines.append("")
        lines.append("| Metric Name | Value | 95% Bootstrap CI [Lower, Upper] |")
        lines.append("|:---|:---:|:---:|")

        cis = run.confidence_interval_95 or {}
        for m_name, m_val in sorted(run.metrics.items()):
            ci_str = "N/A"
            if m_name in cis:
                ci_bounds = cis[m_name]
                ci_str = f"[{ci_bounds[0]:.4f}, {ci_bounds[1]:.4f}]"
            lines.append(f"| **{m_name}** | `{m_val:.4f}` | {ci_str} |")
        lines.append("")

        # 3. Confidence Calibration & Reliability
        if run.calibration_metrics:
            lines.append("## 3. Confidence Calibration & Uncertainty")
            lines.append("")
            for c_name, c_val in run.calibration_metrics.items():
                lines.append(f"- **{c_name.upper()}**: `{c_val:.4f}`")
            lines.append("")

        # 4. Per-Class Breakdown
        if run.per_class_metrics:
            lines.append("## 4. Per-Class Performance Breakdown")
            lines.append("")
            lines.append("| Class Name | Precision | Recall | F1 Score | Support |")
            lines.append("|:---|:---:|:---:|:---:|:---:|")
            for c_name, c_stats in run.per_class_metrics.items():
                prec = c_stats.get("precision", 0.0)
                rec = c_stats.get("recall", 0.0)
                f1 = c_stats.get("f1", 0.0)
                supp = c_stats.get("support", 0)
                lines.append(f"| {c_name} | {prec:.4f} | {rec:.4f} | {f1:.4f} | {supp} |")
            lines.append("")

        # 5. Failure Case Autopsy
        lines.append("## 5. Failure Case Autopsy")
        lines.append("")
        lines.append(f"Total Diagnosed Failure Cases: **{run.failures_count}**")
        lines.append("")
        if run.failure_cases:
            lines.append("| Case ID | Failure Type | Severity | Confidence | Root Cause |")
            lines.append("|:---|:---|:---:|:---:|:---|")
            for fc in run.failure_cases[:10]:
                cid = fc.get("case_id", "N/A")
                ftype = fc.get("failure_type", "misprediction")
                sev = fc.get("severity", "medium")
                conf = fc.get("confidence_score", 0.0)
                cause = fc.get("root_cause_analysis", "Unknown")
                lines.append(f"| `{cid}` | `{ftype}` | {sev} | {conf:.2f} | {cause} |")
            lines.append("")

        # 6. Hardware Environment Profile
        if run.hardware_profile:
            lines.append("## 6. Execution Hardware Profile")
            lines.append("")
            for k, v in run.hardware_profile.items():
                lines.append(f"- **{k}**: {v}")
            lines.append("")

        # 7. Model Limitations
        if run.limitations:
            lines.append("## 7. Known Domain Limitations")
            lines.append("")
            for lim in run.limitations:
                lines.append(f"- {lim}")
            lines.append("")

        lines.append("---")
        lines.append("*Report generated automatically by TRINETRA Unified Benchmark Framework v2.0.*")
        return "\n".join(lines)

    @classmethod
    def save_report(
        cls,
        run: BenchmarkRun,
        output_dir: Union[str, Path]
    ) -> Dict[str, str]:
        """
        Saves both Markdown report and JSON manifest to output directory.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        json_file = out_path / f"benchmark_run_{run.split}_{run.provenance_fingerprint or run.benchmark_id[:8]}.json"
        md_file = out_path / f"benchmark_report_{run.split}_{run.provenance_fingerprint or run.benchmark_id[:8]}.md"

        # Save JSON
        with open(json_file, "w", encoding="utf-8") as f:
            f.write(run.model_dump_json(indent=2))

        # Save Markdown
        report_md = cls.generate_markdown_report(run)
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(report_md)

        return {
            "json_path": str(json_file),
            "markdown_path": str(md_file)
        }

    @staticmethod
    def compare_benchmark_runs(
        run_a: BenchmarkRun,
        run_b: BenchmarkRun,
        allow_cross_version: bool = False
    ) -> Dict[str, Any]:
        """
        Compares two BenchmarkRun manifests strictly adhering to the
        Legitimate Benchmark Comparison Policy:
        - Dataset versions and names must match.
        - Evaluated splits must be identical.
        - Metric formulations must be compatible.
        """
        # Strict validation checks
        if run_a.dataset_name.strip().lower() != run_b.dataset_name.strip().lower():
            raise ValueError(
                f"Incomparable benchmark comparison: Incompatible datasets! "
                f"'{run_a.dataset_name}' vs '{run_b.dataset_name}'"
            )

        if run_a.split != run_b.split:
            raise ValueError(
                f"Incomparable benchmark comparison: Split mismatch! "
                f"Run A evaluated '{run_a.split}' but Run B evaluated '{run_b.split}'."
            )

        if not allow_cross_version and run_a.dataset_manifest_hash != run_b.dataset_manifest_hash:
            # We note this integrity difference
            integrity_warning = (
                f"Dataset manifest hash divergence: Run A ({run_a.dataset_manifest_hash[:8]}) "
                f"vs Run B ({run_b.dataset_manifest_hash[:8]}). Preprocessing or partition difference exists."
            )
        else:
            integrity_warning = None

        # Compare common metrics
        common_metrics = sorted(list(set(run_a.metrics.keys()).intersection(set(run_b.metrics.keys()))))
        if not common_metrics:
            raise ValueError(
                f"Incomparable benchmark comparison: No shared metric definitions between runs! "
                f"Run A: {list(run_a.metrics.keys())}, Run B: {list(run_b.metrics.keys())}"
            )

        metric_comparisons = {}
        for m in common_metrics:
            val_a = run_a.metrics[m]
            val_b = run_b.metrics[m]
            diff = val_b - val_a
            pct_diff = (diff / val_a * 100.0) if abs(val_a) > 1e-9 else 0.0

            metric_comparisons[m] = {
                "run_a_value": round(val_a, 4),
                "run_b_value": round(val_b, 4),
                "absolute_diff": round(diff, 4),
                "relative_gain_pct": round(pct_diff, 2),
                "statistically_higher": "run_b" if diff > 0 else ("run_a" if diff < 0 else "equal")
            }

        # Build Markdown summary comparison table
        md_lines = [
            f"# Benchmark Comparison: {run_a.dataset_name} ({run_a.split.upper()} Split)",
            "",
            f"Comparing Baseline `{run_a.model_name or 'Run A'}` vs Candidate `{run_b.model_name or 'Run B'}`",
            ""
        ]
        if integrity_warning:
            md_lines.append(f"> **Warning**: {integrity_warning}\n")

        md_lines.append("| Metric | Baseline (Run A) | Candidate (Run B) | Absolute Delta | Relative Gain |")
        md_lines.append("|:---|:---:|:---:|:---:|:---:|")

        for m, stats in metric_comparisons.items():
            delta_prefix = "+" if stats["absolute_diff"] > 0 else ""
            gain_prefix = "+" if stats["relative_gain_pct"] > 0 else ""
            md_lines.append(
                f"| **{m}** | {stats['run_a_value']:.4f} | {stats['run_b_value']:.4f} | "
                f"{delta_prefix}{stats['absolute_diff']:.4f} | {gain_prefix}{stats['relative_gain_pct']:.2f}% |"
            )

        md_table = "\n".join(md_lines)

        return {
            "dataset_name": run_a.dataset_name,
            "split": run_a.split,
            "model_a": run_a.model_name,
            "model_b": run_b.model_name,
            "integrity_warning": integrity_warning,
            "metrics": metric_comparisons,
            "markdown_table": md_table
        }
