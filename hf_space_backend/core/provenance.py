"""
TRINETRA — Provenance & Reproducibility Fingerprint Engine
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)
Generates deterministic 16-character execution fingerprints and machine-readable
provenance manifests for every inference request, benchmark run, and training cycle.
"""

import os
import sys
import subprocess
import hashlib
import datetime
from typing import List, Dict, Any, Optional

from config.settings import settings


def compute_file_sha256(file_path: str) -> str:
    """Computes SHA-256 hash of a file streamed in 64KB chunks."""
    if not file_path or not os.path.isfile(file_path):
        return ""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def compute_data_sha256(data: bytes) -> str:
    """Computes SHA-256 hash of in-memory byte buffer."""
    return hashlib.sha256(data).hexdigest()


def get_git_commit(repo_dir: Optional[str] = None) -> str:
    """Retrieves current Git commit hash or returns a deterministic fallback."""
    target_dir = repo_dir or settings.backend_dir
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=target_dir,
            stderr=subprocess.DEVNULL
        )
        return out.decode("utf-8").strip()
    except Exception:
        # Check git HEAD file directly
        git_dir = os.path.join(settings.project_root, ".git")
        if os.path.isdir(git_dir):
            try:
                head_file = os.path.join(git_dir, "HEAD")
                if os.path.isfile(head_file):
                    with open(head_file, "r") as f:
                        ref = f.read().strip()
                    if ref.startswith("ref:"):
                        ref_path = os.path.join(git_dir, ref.split(" ")[1].strip())
                        if os.path.isfile(ref_path):
                            with open(ref_path, "r") as rf:
                                return rf.read().strip()
            except Exception:
                pass
        return "unversioned_git_tree"


def get_environment_lock_hash() -> str:
    """
    Computes a deterministic hash of the core scientific dependency versions
    (PyTorch, NumPy, Pillow, Scikit-learn, etc.).
    """
    import numpy
    import torch
    import PIL
    import pydantic

    pkg_versions = [
        f"python={sys.version.split()[0]}",
        f"torch={torch.__version__}",
        f"numpy={numpy.__version__}",
        f"pil={PIL.__version__}",
        f"pydantic={pydantic.__version__}"
    ]
    raw = ";".join(sorted(pkg_versions))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def generate_run_fingerprint(
    git_commit: str,
    config_hash: str,
    input_hashes: List[str],
    checkpoint_hashes: List[str]
) -> str:
    """
    Generates an immutable 16-character run fingerprint:
    SHA256(git_commit + config_hash + sorted(inputs) + sorted(checkpoints))[:16]
    """
    components = [
        git_commit,
        config_hash,
        ",".join(sorted(filter(None, input_hashes))),
        ",".join(sorted(filter(None, checkpoint_hashes)))
    ]
    combined = "|".join(components)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]


def create_provenance_record(
    run_id: str,
    input_hashes: List[str],
    checkpoint_hashes: List[str],
    fallback_active: bool = False,
    warnings: Optional[List[str]] = None,
    dataset_manifest_hash: Optional[str] = None
) -> Dict[str, Any]:
    """Assembles a full provenance dictionary matching the ProvenanceRecord schema."""
    git_commit = get_git_commit()
    config_hash = settings.get_config_hash()
    env_hash = get_environment_lock_hash()
    fingerprint = generate_run_fingerprint(git_commit, config_hash, input_hashes, checkpoint_hashes)

    return {
        "run_id": run_id,
        "run_fingerprint": fingerprint,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": git_commit,
        "environment_lock_hash": env_hash,
        "config_hash": config_hash,
        "dataset_manifest_hash": dataset_manifest_hash,
        "input_hashes": input_hashes,
        "checkpoint_hashes": checkpoint_hashes,
        "random_seed": settings.seed,
        "device_name": settings.device,
        "warnings": warnings or [],
        "fallback_active": fallback_active,
        "schema_version": "2.0.0"
    }


def compute_provenance_fingerprint(data: Any) -> str:
    """Computes a deterministic 16-character fingerprint for an arbitrary dictionary or object."""
    if isinstance(data, dict):
        raw = str(sorted([(k, str(v)) for k, v in data.items()]))
    else:
        raw = str(data)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def generate_deterministic_run_id(prefix: str = "run") -> str:
    """Generates a structured run identifier string."""
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
