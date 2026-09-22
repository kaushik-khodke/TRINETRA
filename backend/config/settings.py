"""
TRINETRA — Centralized System Configuration Engine
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)
Consolidates all environment-dependent settings, hardware parameters,
geospatial policies, security thresholds, and QML flags into a validated Pydantic model.
Eliminates magic numbers and undocumented defaults across algorithms.
"""

import os
import json
import hashlib
from typing import List, Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel as BaseSettings  # type: ignore
    SettingsConfigDict = dict  # type: ignore

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)


class Settings(BaseSettings):
    """
    Typed system configuration with environment variable overrides
    and validated operational defaults.
    """
    model_config = SettingsConfigDict(
        env_file=os.path.join(BACKEND_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # 1. Application Identity & Versioning
    app_name: str = Field(default="TRINETRA", description="Canonical application identifier")
    app_version: str = Field(default="2.2.0", description="Semantic software release version")
    environment: str = Field(default="production", description="Runtime environment: development | testing | production")
    debug: bool = Field(default=False, description="Enable verbose diagnostic logs")
    seed: int = Field(default=42, description="Global deterministic pseudo-random seed")

    # 2. Filesystem Layout & Storage Boundaries
    backend_dir: str = Field(default=BACKEND_DIR)
    project_root: str = Field(default=PROJECT_ROOT)
    checkpoints_dir: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "models", "checkpoints")
    )
    uploads_dir: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "uploads")
    )
    reports_dir: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "outputs", "reports")
    )
    samples_dir: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "sample_data")
    )
    outputs_dir: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "outputs")
    )

    # 3. Geospatial Processing Policies
    default_crs: str = Field(default="EPSG:4326", description="Default geographic coordinate reference system")
    max_raster_dimension: int = Field(default=4096, description="Max width/height permitted for full-scene loads")
    resampling_method: str = Field(default="bilinear", description="Standard grid alignment interpolation method")
    nodata_policy: str = Field(default="mask", description="Default nodata treatment: mask | zero | ignore")
    min_coregistration_overlap_pct: float = Field(default=0.85, description="Minimum spatial overlap to claim alignment")

    # 4. Compute & Hardware Target
    device: str = Field(
        default_factory=lambda: os.getenv("DEVICE", "cuda" if os.getenv("FORCE_CPU") != "1" else "cpu")
    )
    precision: str = Field(default="fp32", description="Inference numerical precision: fp32 | fp16")
    max_batch_size: int = Field(default=4, description="Maximum GPU batch size for tiling inference")
    max_vram_gb: float = Field(default=12.0, description="Target GPU VRAM hardware allocation limit")

    # 5. Security & Ingest Guardrails
    max_upload_size_bytes: int = Field(default=524_288_000, description="Max upload size (500 MB)")
    decompression_bomb_limit_bytes: int = Field(default=1_073_741_824, description="Decompression ceiling (1 GB)")
    allowed_extensions: List[str] = Field(
        default_factory=lambda: [".tif", ".tiff", ".png", ".jpg", ".jpeg", ".h5", ".mat", ".geojson", ".json"]
    )

    # 6. QML Research Branch
    qml_enabled: bool = Field(default=True, description="Enable PennyLane QML experimental validation layer")
    qml_device: str = Field(default="default.qubit", description="Quantum simulator device backend")
    qml_qubits: int = Field(default=6, description="Active qubit wire count for VQC")
    qml_layers: int = Field(default=3, description="Variational ansatz strongly entangling layer depth")
    qml_timeout_seconds: float = Field(default=3.0, description="Quantum circuit execution timeout ceiling")
    qml_results_dir: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "qml", "results")
    )

    # 7. Exploration & Shanetra Phase 4 Parameters
    exploration_max_aoi_area_km2: float = Field(default=250_000.0, description="Max AOI area in sq km")
    exploration_max_aoi_vertices: int = Field(default=500, description="Max vertex count for AOI polygons")
    exploration_max_temporal_span_days: int = Field(default=365, description="Max allowed temporal query window in days")
    exploration_max_observations: int = Field(default=100, description="Hard limit on temporal observation results")
    exploration_search_timeout_seconds: float = Field(default=15.0, description="STAC temporal search timeout")
    exploration_cache_ttl_seconds: int = Field(default=600, description="TTL for temporal search query cache")

    # 8. Analysis Engine & Shanetra Phase 5 Parameters
    analysis_max_concurrent_jobs: int = Field(default=2, description="Max concurrent EO analysis runs")
    analysis_max_runtime_seconds: float = Field(default=120.0, description="Max timeout per analysis run")
    analysis_max_pixels: int = Field(default=16_000_000, description="Max total pixels for windowed read")
    analysis_max_aoi_area_km2: float = Field(default=2500.0, description="Max permitted AOI area for full analysis")
    analysis_max_artifact_size_bytes: int = Field(default=104_857_600, description="Max size per artifact file (100MB)")
    analysis_artifacts_dir: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "outputs", "analysis")
    )
    analysis_tile_size: int = Field(default=512, description="Model input tile size in pixels")
    analysis_tile_overlap: int = Field(default=64, description="Tile stride overlap in pixels")
    analysis_change_threshold: float = Field(default=0.35, description="Default binary change probability threshold")
    analysis_min_region_pixels: int = Field(default=20, description="Minimum connected component region area in pixels")

    # 9. Investigation & Shanetra Phase 6 Parameters
    investigation_max_concurrent_jobs: int = Field(default=2, description="Max concurrent investigation pipelines")
    investigation_max_runtime_seconds: float = Field(default=180.0, description="Max timeout per investigation in seconds")
    investigation_max_specialists: int = Field(default=4, description="Max analytical specialists per investigation")
    investigation_max_regions: int = Field(default=100, description="Max detected regions retained per investigation")
    investigation_artifacts_dir: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "outputs", "investigations")
    )
    investigation_notes_dir: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "outputs", "analyst_notes")
    )

    # 10. Intelligence & Monitoring Phase 7 Parameters
    intelligence_db_path: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "outputs", "intelligence.db")
    )
    intelligence_max_monitors: int = Field(default=50, description="Max allowed active monitoring definitions")
    intelligence_max_events: int = Field(default=10000, description="Max persisted intelligence events threshold")
    intelligence_max_search_results: int = Field(default=100, description="Max search result entities returned per query")
    intelligence_max_concurrent_monitor_runs: int = Field(default=2, description="Max concurrent monitoring analyses")
    intelligence_artifacts_dir: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "outputs", "intelligence")
    )

    # -------------------------------------------------------------------------
    # 11. Analyst Workspace & Multi-Region Workflows (Phase 8)
    # -------------------------------------------------------------------------
    workspace_db_path: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "outputs", "workspace.db")
    )
    workspace_artifacts_dir: str = Field(
        default_factory=lambda: os.path.join(BACKEND_DIR, "outputs", "workspaces")
    )
    workspace_max_batch_targets: int = Field(default=50, description="Max allowed targets in a single batch job")
    workspace_max_concurrent_tasks: int = Field(default=4, description="Max concurrent tasks executed in task queue")
    workspace_max_batch_runtime: int = Field(default=1800, description="Max batch execution timeout in seconds")
    workspace_max_batch_pixels: int = Field(default=50_000_000, description="Max cumulative pixel budget for batch runs")
    workspace_max_plan_steps: int = Field(default=20, description="Max step count allowed in an investigation plan")
    workspace_max_board_items: int = Field(default=200, description="Max items on a single evidence board")
    workspace_max_report_size_mb: int = Field(default=50, description="Max report package export size in MB")

    def get_config_hash(self) -> str:
        """
        Computes a deterministic SHA-256 hash of all runtime configurations.
        Used to bind every model run and benchmark to an exact configuration state.
        """
        config_dict = {
            "app_version": self.app_version,
            "seed": self.seed,
            "default_crs": self.default_crs,
            "resampling_method": self.resampling_method,
            "device": self.device,
            "precision": self.precision,
            "qml_qubits": self.qml_qubits,
            "qml_layers": self.qml_layers,
            "qml_device": self.qml_device
        }
        serialized = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def ensure_directories(self) -> None:
        """Creates necessary filesystem directories if missing."""
        for d in [
            self.checkpoints_dir,
            self.uploads_dir,
            self.reports_dir,
            self.samples_dir,
            self.outputs_dir,
            self.analysis_artifacts_dir,
            self.investigation_artifacts_dir,
            self.investigation_notes_dir,
            self.intelligence_artifacts_dir,
            self.workspace_artifacts_dir,
        ]:
            os.makedirs(d, exist_ok=True)


# Singleton instance loaded once at startup
settings = Settings()
settings.ensure_directories()


