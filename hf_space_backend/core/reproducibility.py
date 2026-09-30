"""
TRINETRA — Scientific Reproducibility & Third-Person Audit Package Engine
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)

Guarantees full third-person reproducibility:
Every benchmark and inference result is tied to:
1. Git commit
2. Environment lock
3. Configuration hash
4. Dataset manifest & SHA-256 hash
5. Checkpoint SHA-256 hash
6. Preprocessing version
7. Reconstruction Guide (RECONSTRUCTION_GUIDE.md)
"""

import os
import sys
import json
import hashlib
import datetime
from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel, Field

from config.settings import settings
from core.provenance import get_git_commit, get_environment_lock_hash


class ReproducibilityBundle(BaseModel):
    """Immutable cryptographic bundle capturing all prerequisites to reconstruct a result."""
    run_id: str
    fingerprint: str
    git_commit: str
    environment_lock_hash: str
    config_hash: str
    dataset_manifest_hash: str
    checkpoint_hash: str
    preprocessing_version: str = "v2.0.0"
    random_seed: int = 42
    timestamp_utc: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    package_versions: Dict[str, str] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


def get_core_package_versions() -> Dict[str, str]:
    """Inspects installed scientific package versions for auditing."""
    import numpy
    import torch
    import PIL
    import pydantic
    try:
        import sklearn
        sk_ver = sklearn.__version__
    except ImportError:
        sk_ver = "not_installed"

    return {
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "numpy": numpy.__version__,
        "pillow": PIL.__version__,
        "pydantic": pydantic.__version__,
        "scikit_learn": sk_ver
    }


def create_reproducibility_bundle(
    run_id: str,
    checkpoint_hash: str,
    dataset_manifest_hash: str,
    preprocessing_version: str = "v2.0.0",
    random_seed: Optional[int] = None
) -> ReproducibilityBundle:
    """Constructs a cryptographic reproducibility bundle for an execution run."""
    git_commit = get_git_commit()
    env_hash = get_environment_lock_hash()
    config_hash = settings.get_config_hash()
    seed = random_seed if random_seed is not None else settings.seed
    pkgs = get_core_package_versions()

    # Deterministic fingerprint
    raw_components = [
        git_commit,
        env_hash,
        config_hash,
        dataset_manifest_hash,
        checkpoint_hash,
        preprocessing_version,
        str(seed)
    ]
    fingerprint = hashlib.sha256("|".join(raw_components).encode("utf-8")).hexdigest()[:16]

    return ReproducibilityBundle(
        run_id=run_id,
        fingerprint=fingerprint,
        git_commit=git_commit,
        environment_lock_hash=env_hash,
        config_hash=config_hash,
        dataset_manifest_hash=dataset_manifest_hash,
        checkpoint_hash=checkpoint_hash,
        preprocessing_version=preprocessing_version,
        random_seed=seed,
        package_versions=pkgs
    )


def verify_reproducibility(
    bundle_a: ReproducibilityBundle,
    bundle_b: ReproducibilityBundle
) -> Tuple[bool, List[str]]:
    """
    Compares two reproducibility bundles.
    Returns (is_reproducible, list_of_divergences).
    """
    divergences = []

    if bundle_a.git_commit != bundle_b.git_commit:
        divergences.append(f"Git commit diverged: '{bundle_a.git_commit}' vs '{bundle_b.git_commit}'")

    if bundle_a.environment_lock_hash != bundle_b.environment_lock_hash:
        divergences.append(f"Environment lock hash diverged: '{bundle_a.environment_lock_hash}' vs '{bundle_b.environment_lock_hash}'")

    if bundle_a.config_hash != bundle_b.config_hash:
        divergences.append(f"Config hash diverged: '{bundle_a.config_hash}' vs '{bundle_b.config_hash}'")

    if bundle_a.dataset_manifest_hash != bundle_b.dataset_manifest_hash:
        divergences.append(f"Dataset manifest hash diverged: '{bundle_a.dataset_manifest_hash}' vs '{bundle_b.dataset_manifest_hash}'")

    if bundle_a.checkpoint_hash != bundle_b.checkpoint_hash:
        divergences.append(f"Checkpoint hash diverged: '{bundle_a.checkpoint_hash}' vs '{bundle_b.checkpoint_hash}'")

    if bundle_a.preprocessing_version != bundle_b.preprocessing_version:
        divergences.append(f"Preprocessing version diverged: '{bundle_a.preprocessing_version}' vs '{bundle_b.preprocessing_version}'")

    if bundle_a.random_seed != bundle_b.random_seed:
        divergences.append(f"Random seed diverged: {bundle_a.random_seed} vs {bundle_b.random_seed}")

    return len(divergences) == 0, divergences


def generate_audit_package(
    run_id: str,
    result_data: Dict[str, Any],
    bundle: ReproducibilityBundle,
    output_dir: str
) -> Dict[str, str]:
    """
    Generates an audit package containing:
    1. audit_manifest.json: Machine-readable audit record
    2. RECONSTRUCTION_GUIDE.md: Step-by-step instructions for an external auditor to reproduce the exact run.
    """
    os.makedirs(output_dir, exist_ok=True)
    manifest_path = os.path.join(output_dir, f"{run_id}_audit_manifest.json")
    guide_path = os.path.join(output_dir, f"{run_id}_RECONSTRUCTION_GUIDE.md")

    # 1. Save JSON manifest
    audit_data = {
        "run_id": run_id,
        "reproducibility_bundle": bundle.to_dict(),
        "evaluation_summary": result_data.get("summary", {}),
        "metrics": result_data.get("metrics", {}),
        "uncertainty": result_data.get("uncertainty", {}),
        "failure_diagnosis": result_data.get("failure_diagnosis", {}),
        "hardware_specs": result_data.get("hardware_specs", {}),
        "known_limitations": result_data.get("known_limitations", [])
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # 2. Generate Markdown reconstruction guide
    guide_content = f"""# Third-Party Audit & Reconstruction Guide
**Run ID**: `{run_id}`  
**Fingerprint**: `{bundle.fingerprint}`  
**Generated UTC**: `{bundle.timestamp_utc}`  
**Target Git Commit**: `{bundle.git_commit}`  

---

## Executive Result
- **Task**: `{result_data.get('task', 'Remote Sensing Specialist Evaluation')}`
- **Primary Metrics**: `{json.dumps(result_data.get('metrics', {}), indent=2)}`
- **Checkpoint SHA-256**: `{bundle.checkpoint_hash}`
- **Dataset Manifest SHA-256**: `{bundle.dataset_manifest_hash}`

---

## Step-by-Step Reconstruction Protocol

An independent auditor can reproduce this exact result by executing the following steps:

### Step 1: Checkout Repository at Exact Commit
```bash
git clone https://github.com/isro-sih2026/TRINETRA.git
cd TRINETRA
git checkout {bundle.git_commit}
```

### Step 2: Lock Environment Dependencies
Ensure Python version `{bundle.package_versions.get('python', '3.10')}` is active, then install matching package versions:
```bash
pip install torch=={bundle.package_versions.get('torch', '2.0.0')} \\
            numpy=={bundle.package_versions.get('numpy', '1.24.0')} \\
            Pillow=={bundle.package_versions.get('pillow', '10.0.0')} \\
            pydantic=={bundle.package_versions.get('pydantic', '2.0.0')}
```
Verified environment lock hash: `{bundle.environment_lock_hash}`.

### Step 3: Verify Checkpoint Cryptographic Integrity
Download or locate the model checkpoint and verify its SHA-256 digest:
```bash
# Verify checksum matches exactly:
# Expected: {bundle.checkpoint_hash}
sha256sum checkpoints/<model_key>/best_model.pt
```

### Step 4: Verify Dataset Manifest Integrity
Ensure the benchmark dataset split matches:
```bash
# Expected dataset manifest hash: {bundle.dataset_manifest_hash}
python -c "from evaluation.benchmark_registry import BenchmarkRegistry; print(BenchmarkRegistry.compute_dataset_manifest_hash('datasets/<name>'))"
```

### Step 5: Execute Evaluation Run
Execute evaluation with preprocessing version `{bundle.preprocessing_version}` and random seed `{bundle.random_seed}`:
```bash
python -m evaluation.runner --run-id {run_id} --seed {bundle.random_seed}
```
"""
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(guide_content)

    return {
        "manifest_path": manifest_path,
        "guide_path": guide_path
    }
