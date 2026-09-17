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
        for d in [self.checkpoints_dir, self.uploads_dir, self.reports_dir, self.samples_dir, self.outputs_dir]:
            os.makedirs(d, exist_ok=True)


# Singleton instance loaded once at startup
settings = Settings()
settings.ensure_directories()
