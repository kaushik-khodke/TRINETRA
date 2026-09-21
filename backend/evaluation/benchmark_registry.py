"""
TRINETRA Unified Benchmark Registry (Stage 8)
Governed by 08_STAGE_8_BENCHMARK_FRAMEWORK.md and NON_NEGOTIABLE_PRINCIPLES.md.

Maintains canonical metadata for official remote sensing benchmark datasets:
- LEVIR-CD, LEVIR-CD+, WHU-CD (Bi-Temporal Change Detection)
- SEN12MS, SpaceNet-6 (Multimodal Optical-SAR Fusion)
- Indian Pines, Pavia University, Salinas (Hyperspectral Classification)
- RSVQA-LR, RSVQA-HR (Remote Sensing Visual Question Answering)
- BigEarthNet-S2 (Multi-label Land Cover Classification)

STRICT RULE: The IDE and framework MUST NOT download datasets automatically.
Datasets must be provided locally by the user per MANUAL_TRAINING_PROTOCOL.md.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import hashlib
import json
import os

try:
    from backend.schemas.contracts import BenchmarkMetadata
    from backend.core.exceptions import DatasetValidationError, DataLeakageError
except ImportError:
    from schemas.contracts import BenchmarkMetadata
    from core.exceptions import DatasetValidationError, DataLeakageError


class BenchmarkRegistry:
    """
    Central repository of official remote sensing benchmarks, split definitions,
    and integrity validation schemas.
    """

    def __init__(self):
        self._registry: Dict[str, BenchmarkMetadata] = {}
        self._init_canonical_benchmarks()

    def _init_canonical_benchmarks(self) -> None:
        """Register the standard benchmark suite."""
        canonical_benchmarks = [
            # 1. Change Detection
            BenchmarkMetadata(
                benchmark_id="levir_cd",
                dataset_name="LEVIR-CD Building Change Detection Benchmark",
                official_source="https://justchenhao.github.io/LEVIR/",
                citation="Chen, H., & Shi, Z. (2020). A spatial-temporal attention-based method and a new dataset for remote sensing image change detection. Remote Sensing, 12(10), 1662.",
                license_terms="Creative Commons Attribution 4.0 International (CC BY 4.0)",
                task="change_detection",
                modality="optical_bitemporal",
                sensors=["Google Earth VHR Sensors"],
                spatial_resolution_meters=0.5,
                split_definitions={
                    "train": {"ratio": 0.70, "expected_tiles_1024": 445},
                    "val": {"ratio": 0.10, "expected_tiles_1024": 64},
                    "test": {"ratio": 0.20, "expected_tiles_1024": 128}
                },
                label_schema={"0": "no_change", "1": "change_building"},
                expected_metrics=["f1", "iou", "precision", "recall", "oa"],
                anti_leakage_policy="Disjoint geographic patch tiles; strict single-pass test evaluation"
            ),
            BenchmarkMetadata(
                benchmark_id="levir_cd_plus",
                dataset_name="LEVIR-CD+ Large-Scale Building Change Detection",
                official_source="https://github.com/S2Looking/LEVIR-CD-plus",
                citation="Shen, Q., et al. (2021). S2Looking: A High-Resolution Remote Sensing Dataset for Change Detection. IEEE JSTARS.",
                license_terms="CC BY 4.0",
                task="change_detection",
                modality="optical_bitemporal",
                sensors=["Google Earth VHR Sensors"],
                spatial_resolution_meters=0.5,
                split_definitions={"train": {"ratio": 0.68}, "test": {"ratio": 0.32}},
                label_schema={"0": "no_change", "1": "change_building"},
                expected_metrics=["f1", "iou", "precision", "recall", "oa"]
            ),
            BenchmarkMetadata(
                benchmark_id="whu_cd",
                dataset_name="WHU Building Change Detection Dataset",
                official_source="http://gpcv.whu.edu.cn/data/building_dataset.html",
                citation="Ji, S., Wei, S., & Lu, M. (2018). Fully convolutional networks for multisource building extraction from an open aerial and satellite imagery dataset. IEEE TGRS, 57(1), 574-586.",
                license_terms="Academic Research Use Only",
                task="change_detection",
                modality="optical_bitemporal",
                sensors=["Aerial Orthophotos"],
                spatial_resolution_meters=0.2,
                split_definitions={"train": {"ratio": 0.75}, "test": {"ratio": 0.25}},
                label_schema={"0": "no_change", "1": "change_building"},
                expected_metrics=["f1", "iou", "precision", "recall", "oa"]
            ),

            # 2. Multimodal Optical-SAR Fusion
            BenchmarkMetadata(
                benchmark_id="sen12ms",
                dataset_name="SEN12MS Multi-Sensor Earth Observation Archive",
                official_source="https://mediatum.ub.tum.de/1474000",
                citation="Schmitt, M., Hughes, L. H., Qiu, C., & Zhu, X. X. (2019). SEN12MS--a curated dataset of georeferenced multi-spectral sentinel-1/2 imagery for deep learning and data fusion. ISPRS Annals, IV-2/W7, 153-160.",
                license_terms="Creative Commons Attribution 4.0 International (CC BY 4.0)",
                task="multimodal_fusion",
                modality="optical_sar",
                sensors=["Sentinel-1 C-band SAR", "Sentinel-2 Multispectral MSI"],
                spatial_resolution_meters=10.0,
                split_definitions={
                    "train": {"seasons": ["spring", "summer", "fall"], "holdout_scheme": "spatial_holdout"},
                    "val": {"seasons": ["winter"], "holdout_scheme": "spatial_holdout"},
                    "test": {"seasons": ["winter"], "holdout_scheme": "geographic_unseen"}
                },
                label_schema={
                    "0": "water",
                    "1": "trees",
                    "2": "grassland",
                    "3": "cropland",
                    "4": "built_up",
                    "5": "bare_soil"
                },
                expected_metrics=["overall_accuracy", "macro_f1", "kappa_coefficient", "mean_iou"],
                anti_leakage_policy="Disjoint geographic meteorological scenes; no overlapping Sentinel patches"
            ),
            BenchmarkMetadata(
                benchmark_id="spacenet6",
                dataset_name="SpaceNet 6: Multi-Sensor All-Weather Mapping",
                official_source="https://spacenet.ai/sn6-challenge/",
                citation="Shermeyer, J., et al. (2020). SpaceNet 6: Multi-sensor all weather mapping dataset. CVPRW 2020.",
                license_terms="CC BY-SA 4.0",
                task="multimodal_fusion",
                modality="optical_sar",
                sensors=["Capella Space X-band SAR", "WorldView-2 0.5m Optical"],
                spatial_resolution_meters=0.5,
                split_definitions={"train": {"ratio": 0.80}, "test": {"ratio": 0.20}},
                label_schema={"0": "background", "1": "building_footprint"},
                expected_metrics=["f1", "precision", "recall", "iou"]
            ),

            # 3. Hyperspectral Classification
            BenchmarkMetadata(
                benchmark_id="indian_pines",
                dataset_name="Indian Pines Hyperspectral AVIRIS Scene",
                official_source="https://www.ehu.eus/ccwintco/index.php/Hyperspectral_Remote_Sensing_Scenes",
                citation="Purpur, D. (1992). Indian Pines Hyperspectral AVIRIS Dataset. Purdue University.",
                license_terms="Public Domain / Academic Research",
                task="hyperspectral_classification",
                modality="hyperspectral",
                sensors=["AVIRIS (224 bands, 0.4-2.5 um)"],
                spatial_resolution_meters=20.0,
                split_definitions={
                    "train": {"method": "spatial_block_grid", "ratio": 0.20},
                    "val": {"method": "spatial_block_grid", "ratio": 0.10},
                    "test": {"method": "spatial_block_grid", "ratio": 0.70}
                },
                label_schema={
                    "0": "unclassified",
                    "1": "Alfalfa", "2": "Corn-notill", "3": "Corn-mintill", "4": "Corn",
                    "5": "Grass-pasture", "6": "Grass-trees", "7": "Grass-pasture-mowed",
                    "8": "Hay-windrowed", "9": "Oats", "10": "Soybean-notill",
                    "11": "Soybean-mintill", "12": "Soybean-clean", "13": "Wheat",
                    "14": "Woods", "15": "Buildings-Grass-Trees-Drives", "16": "Stone-Steel-Towers"
                },
                expected_metrics=["overall_accuracy", "average_accuracy", "kappa_coefficient", "macro_f1"],
                anti_leakage_policy="Rigid spatial block grid partition; zero random pixel split; boundary margins"
            ),
            BenchmarkMetadata(
                benchmark_id="pavia_university",
                dataset_name="Pavia University ROSIS Hyperspectral Scene",
                official_source="https://www.ehu.eus/ccwintco/index.php/Hyperspectral_Remote_Sensing_Scenes",
                citation="Gamba, P., et al. (2004). Collection of Pavia University ROSIS data. University of Pavia.",
                license_terms="Academic Research Use Only",
                task="hyperspectral_classification",
                modality="hyperspectral",
                sensors=["ROSIS (103 bands, 0.43-0.86 um)"],
                spatial_resolution_meters=1.3,
                split_definitions={"train": {"ratio": 0.20}, "val": {"ratio": 0.10}, "test": {"ratio": 0.70}},
                label_schema={
                    "0": "unclassified", "1": "Asphalt", "2": "Meadows", "3": "Gravel", "4": "Trees",
                    "5": "Painted metal sheets", "6": "Bare Soil", "7": "Bitumen", "8": "Self-Blocking Bricks", "9": "Shadows"
                },
                expected_metrics=["overall_accuracy", "average_accuracy", "kappa_coefficient", "macro_f1"],
                anti_leakage_policy="Rigid spatial block partition"
            ),
            BenchmarkMetadata(
                benchmark_id="salinas",
                dataset_name="Salinas Valley Hyperspectral AVIRIS Scene",
                official_source="https://www.ehu.eus/ccwintco/index.php/Hyperspectral_Remote_Sensing_Scenes",
                citation="Purpur, D. (1998). Salinas AVIRIS Dataset. Purdue University.",
                license_terms="Public Domain / Academic Research",
                task="hyperspectral_classification",
                modality="hyperspectral",
                sensors=["AVIRIS (224 bands, 0.4-2.5 um)"],
                spatial_resolution_meters=3.7,
                split_definitions={"train": {"ratio": 0.20}, "val": {"ratio": 0.10}, "test": {"ratio": 0.70}},
                label_schema={
                    "0": "unclassified", "1": "Brocoli_green_weeds_1", "2": "Brocoli_green_weeds_2",
                    "3": "Fallow", "4": "Fallow_rough_plow", "5": "Fallow_smooth", "6": "Stubble",
                    "7": "Celery", "8": "Grapes_untrained", "9": "Soil_vinyard_develop",
                    "10": "Corn_senesced_green_weeds", "11": "Lettuce_romaine_4wk",
                    "12": "Lettuce_romaine_5wk", "13": "Lettuce_romaine_6wk",
                    "14": "Lettuce_romaine_7wk", "15": "Vinyard_untrained", "16": "Vinyard_vertical_trellis"
                },
                expected_metrics=["overall_accuracy", "average_accuracy", "kappa_coefficient", "macro_f1"],
                anti_leakage_policy="Rigid spatial block partition"
            ),

            # 4. Remote Sensing VQA
            BenchmarkMetadata(
                benchmark_id="rsvqa_lr",
                dataset_name="RSVQA Low Resolution Benchmark",
                official_source="https://zenodo.org/record/6344367",
                citation="Lobry, S., Marcos, D., Murray, J., & Tuia, D. (2020). RSVQA: Visual question answering for remote sensing data. IEEE TGRS, 58(12), 8555-8566.",
                license_terms="Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)",
                task="vqa",
                modality="rgb",
                sensors=["Sentinel-2 MSI (RGB bands)"],
                spatial_resolution_meters=10.0,
                split_definitions={
                    "train": {"expected_images": 772, "ratio": 0.72},
                    "val": {"expected_images": 100, "ratio": 0.09},
                    "test": {"expected_images": 200, "ratio": 0.19}
                },
                label_schema={"answer_types": ["presence", "count", "comparison", "area"]},
                expected_metrics=["top1_accuracy_pct", "top5_accuracy_pct", "exact_match_pct", "presence_acc", "count_acc", "comparison_acc", "area_acc"],
                anti_leakage_policy="Disjoint geographic Sentinel-2 tiles; test evaluated strictly once"
            ),
            BenchmarkMetadata(
                benchmark_id="rsvqa_hr",
                dataset_name="RSVQA High Resolution Benchmark",
                official_source="https://zenodo.org/record/6344367",
                citation="Lobry, S., Marcos, D., Murray, J., & Tuia, D. (2020). RSVQA: Visual question answering for remote sensing data. IEEE TGRS, 58(12), 8555-8566.",
                license_terms="CC BY-NC 4.0",
                task="vqa",
                modality="rgb",
                sensors=["High-Resolution Aerial Orthophotos"],
                spatial_resolution_meters=0.15,
                split_definitions={"train": {"ratio": 0.70}, "val": {"ratio": 0.10}, "test": {"ratio": 0.20}},
                label_schema={"answer_types": ["presence", "count", "comparison", "area"]},
                expected_metrics=["top1_accuracy_pct", "top5_accuracy_pct", "exact_match_pct"],
                anti_leakage_policy="Disjoint image scenes; single-pass test evaluation"
            ),

            # 5. Multi-label Land Cover
            BenchmarkMetadata(
                benchmark_id="bigearthnet_s2",
                dataset_name="BigEarthNet Sentinel-2 Multi-Label Archive",
                official_source="https://bigearth.net/",
                citation="Sumbul, G., et al. (2019). BigEarthNet: A large-scale benchmark archive for remote sensing image understanding. IGARSS 2019.",
                license_terms="Community Data License Agreement – Permissive – Version 1.0 (CDLA-Permissive-1.0)",
                task="multilabel_landcover",
                modality="optical_multispectral",
                sensors=["Sentinel-2 L2A (12 spectral bands)"],
                spatial_resolution_meters=10.0,
                split_definitions={"train": {"ratio": 0.70}, "val": {"ratio": 0.10}, "test": {"ratio": 0.20}},
                label_schema={"corine_classes": 19},
                expected_metrics=["mAP", "micro_f1", "macro_f1"],
                anti_leakage_policy="Country/tile disjoint holdout"
            )
        ]

        for bm in canonical_benchmarks:
            self.register_benchmark(bm)

    def register_benchmark(self, meta: BenchmarkMetadata) -> None:
        """Register a new or custom benchmark dataset specification."""
        self._registry[meta.benchmark_id] = meta

    def get_benchmark_metadata(self, benchmark_id: str) -> BenchmarkMetadata:
        """Retrieve metadata for a benchmark by ID."""
        if benchmark_id not in self._registry:
            raise KeyError(
                f"Benchmark '{benchmark_id}' not found in registry. "
                f"Available benchmarks: {list(self._registry.keys())}"
            )
        return self._registry[benchmark_id]

    def list_benchmarks(self, task: Optional[str] = None) -> List[BenchmarkMetadata]:
        """List registered benchmarks, optionally filtered by task."""
        if task is None:
            return list(self._registry.values())
        return [bm for bm in self._registry.values() if bm.task == task]

    def compute_dataset_manifest_hash(self, dataset_path: Union[str, Path]) -> str:
        """
        Computes deterministic SHA-256 digest over the directory filenames,
        relative paths, and file sizes to lock dataset integrity.
        """
        path = Path(dataset_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset path does not exist: {path}")

        hasher = hashlib.sha256()
        all_files = sorted([p for p in path.rglob("*") if p.is_file()])
        if not all_files:
            return "empty_dir_hash_0000000000000000"

        for f in all_files:
            rel = str(f.relative_to(path)).replace("\\", "/")
            stat = f.stat()
            hasher.update(f"{rel}:{stat.st_size}".encode("utf-8"))

        return hasher.hexdigest()

    def validate_dataset_path(
        self,
        benchmark_id: str,
        local_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Validates whether a manually provided local dataset path conforms to
        the required structure for benchmark execution without downloading.
        """
        meta = self.get_benchmark_metadata(benchmark_id)
        path = Path(local_path)

        if not path.exists():
            return {
                "is_valid": False,
                "benchmark_id": benchmark_id,
                "dataset_name": meta.dataset_name,
                "path": str(path),
                "error": f"Directory not found: {path}",
                "remediation": f"Manually place dataset files at '{path}' per MANUAL_TRAINING_PROTOCOL.md."
            }

        if not path.is_dir():
            return {
                "is_valid": False,
                "benchmark_id": benchmark_id,
                "dataset_name": meta.dataset_name,
                "path": str(path),
                "error": f"Path is a file, not a directory: {path}",
                "remediation": f"Provide root directory of the benchmark."
            }

        # Task-specific folder and file inspection
        missing_elements = []
        task = meta.task

        if task == "change_detection":
            # Expect subfolders or manifest
            # Either subdirectories train/val/test or A, B, label
            has_split_dirs = any((path / s).is_dir() for s in ["train", "val", "test"])
            has_pair_dirs = any((path / s).is_dir() for s in ["A", "B", "label", "list"])
            has_manifest = (path / "manifest.json").is_file() or (path / "train.txt").is_file()
            if not (has_split_dirs or has_pair_dirs or has_manifest):
                missing_elements.append("Expected 'train'/'val'/'test' or 'A'/'B'/'label' subfolders or manifest.json")

        elif task == "multimodal_fusion":
            # SEN12MS expects optical/sar imagery or seasonal folders
            has_subs = any(path.iterdir())
            if not has_subs:
                missing_elements.append("SEN12MS / Optical-SAR root directory is empty.")

        elif task == "hyperspectral_classification":
            # Expect .mat, .npz, or .tif files
            valid_exts = {".mat", ".npz", ".npy", ".tif", ".tiff", ".hdr"}
            matching_files = [p for p in path.rglob("*") if p.suffix.lower() in valid_exts]
            if not matching_files:
                missing_elements.append(f"No hyperspectral data files ({valid_exts}) found in {path}")

        elif task == "vqa":
            # Expect images folder and question/answers json
            has_json = any(p.suffix.lower() == ".json" for p in path.glob("*.json")) or any(p.suffix.lower() == ".json" for p in path.rglob("*.json"))
            if not has_json:
                missing_elements.append("No question/answer JSON manifest files found.")

        if missing_elements:
            return {
                "is_valid": False,
                "benchmark_id": benchmark_id,
                "dataset_name": meta.dataset_name,
                "path": str(path),
                "error": "Dataset structure incomplete",
                "missing_elements": missing_elements,
                "remediation": f"Refer to {meta.official_source} or MANUAL_TRAINING_PROTOCOL.md."
            }

        manifest_hash = self.compute_dataset_manifest_hash(path)
        return {
            "is_valid": True,
            "benchmark_id": benchmark_id,
            "dataset_name": meta.dataset_name,
            "path": str(path),
            "manifest_hash": manifest_hash,
            "total_files": len(list(path.rglob("*")))
        }

    def validate_split_isolation(
        self,
        split_samples: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Verifies that train, val, and test splits are strictly pairwise disjoint.
        Raises DataLeakageError if overlap is detected.
        """
        train_set = set(split_samples.get("train", []))
        val_set = set(split_samples.get("val", []))
        test_set = set(split_samples.get("test", []))

        train_val_overlap = train_set.intersection(val_set)
        train_test_overlap = train_set.intersection(test_set)
        val_test_overlap = val_set.intersection(test_set)

        if train_val_overlap or train_test_overlap or val_test_overlap:
            overlap_details = {
                "train_val_overlap_count": len(train_val_overlap),
                "train_test_overlap_count": len(train_test_overlap),
                "val_test_overlap_count": len(val_test_overlap),
                "sample_leakages": list(train_test_overlap | val_test_overlap)[:5]
            }
            raise DataLeakageError(
                f"Severe anti-leakage violation: Split overlap detected across partitions! "
                f"Details: {overlap_details}"
            )

        return {
            "leakage_detected": False,
            "train_count": len(train_set),
            "val_count": len(val_set),
            "test_count": len(test_set)
        }


# Canonical singleton instance
default_registry = BenchmarkRegistry()
