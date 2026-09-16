# TRINETRA Bug & Vulnerability Audit (Stage 1)

This audit documents all critical bugs, deceptive states, and data-integrity flaws identified in the TRINETRA codebase prior to Stage 1 remediation.

---

### Finding BUG-01: Deceptive Model Loading Status When No Checkpoint Exists
- **File**: `backend/models/loader.py`
- **Function/Class**: `ModelManager.get_status()`
- **Severity**: Critical (High Risk of Scientific Misrepresentation)
- **Reproducibility**: 100% (deterministic)
- **Root Cause**: When a checkpoint directory contains no weight file (`*.pt`, `*.bin`, `*.safetensors`), `ModelManager.get_status()` returns:
  ```python
  report[key] = {
      "name": name,
      "loaded": True,  # Misleading
      "engine": "Algorithmic CV / Radiometric Engine",
      "checkpoint_file": "None (Awaiting user checkpoint upload)",
      ...
  }
  ```
  This misleads consumers and API callers into believing a neural network is loaded when in reality fallback heuristics are executing.
- **Proposed Repair**: Report `"loaded": False`, `"checkpoint_file": None`, `"fallback_active": True`, `"engine": "Heuristic / Algorithmic CV Engine (Fallback)"`, and `"fallback_reason": "No checkpoint found on disk"`.
- **Test Required**: `test_model_manager_status_unloaded()` verifying that absent checkpoints yield `loaded == False` and explicit fallback flags.
- **Status**: Remediation in progress.

---

### Finding BUG-02: Silent Exception Catching & Uninitialized Model Caching
- **File**: `backend/models/loader.py`
- **Function/Class**: `ModelManager.load_or_get_model()`
- **Severity**: Critical (Silent Failure & Random Inferences)
- **Reproducibility**: 100% when weights file is corrupt or keys mismatch
- **Root Cause**: Checkpoints are loaded using `model.load_state_dict(state, strict=False)`. If an exception occurs, it is caught with a print statement, and the uninitialized PyTorch model with random weights is cached into `_models[model_key]` and returned for active inference.
- **Proposed Repair**: Enforce key verification or strict loading. When weights fail to load, do not cache the random-weight model; return `None` or raise a typed `CheckpointLoadError`, triggering explicit and logged fallback execution.
- **Test Required**: `test_corrupt_checkpoint_fails_gracefully()` verifying uninitialized models are never cached or treated as loaded.
- **Status**: Remediation in progress.

---

### Finding BUG-03: Non-Deterministic VQA Tokenizer Using Python Runtime `hash()`
- **File**: `backend/services/vqa/vqa_service.py`
- **Function/Class**: `RSVqaSpecialist.execute()`
- **Severity**: Critical (Irreproducible Inference)
- **Reproducibility**: 100% across different Python process executions
- **Root Cause**: Question tokenization maps words to IDs using:
  ```python
  token_ids = [abs(hash(w)) % 4900 + 100 for w in words[:16]]
  ```
  In Python 3.3+, string hashing is salted per process invocation (`PYTHONHASHSEED`). The exact same question produces completely different token embeddings on every server restart, destroying all reproducibility and neural checkpoint compatibility.
- **Proposed Repair**: Implement a deterministic vocabulary lookup matching the trained vocabulary (`rsvqa_vocab.json`). For out-of-vocabulary words, use a stable hashing function (e.g. integer conversion of SHA-256) with fixed seed mapping.
- **Test Required**: `test_vqa_tokenizer_deterministic()` verifying that word sequences produce identical token vectors across process restarts.
- **Status**: Remediation in progress.

---

### Finding BUG-04: Hardcoded Optical-SAR Correlation & Fabricated Concordance
- **File**: `backend/services/optical_sar/optical_sar_service.py`
- **Function/Class**: `OpticalSarFusionSpecialist.execute()`
- **Severity**: Critical (Fabricated Scientific Evidence)
- **Reproducibility**: 100% (constant static return)
- **Root Cause**: Lines 100–104 return static fabricated values:
  ```python
  "fusion_correlations": {
      "optical_sar_correlation": 0.84,
      "structural_coherence": "High dual-sensor concordance",
      "spectral_radar_alignment": "Verified cross-modal radiometric registration"
  }
  ```
  The values `0.84` and "High dual-sensor concordance" are returned regardless of whether the images are correlated, orthogonal, or completely mismatched.
- **Proposed Repair**: Compute real statistical correlation (Pearson correlation coefficient between optical luminance/NIR and SAR dB backscatter) and normalized mutual information. If geometric metadata shows misalignment, report `alignment_verified: False`.
- **Test Required**: `test_optical_sar_dynamic_correlation()` verifying calculated correlation differs appropriately across identical vs uncorrelated arrays.
- **Status**: Remediation in progress.

---

### Finding BUG-05: Arbitrary Hardcoded Confidence Scores in LLM Synthesis
- **File**: `backend/services/llm_engine.py`
- **Function/Class**: `LLMReasoningEngine` (multiple methods)
- **Severity**: High (Deceptive Confidence Metrics)
- **Reproducibility**: 100%
- **Root Cause**: Several synthesis methods hardcode confidence values:
  - `synthesize_optical_sar_answer`: `"confidence": 0.95`
  - `synthesize_grounding_answer`: `"confidence": 0.91`
  - `synthesize_caption_answer`: `"confidence": 0.93`
  - `synthesize_hyperspectral_answer`: `"confidence": 0.94`
  - `synthesize_vqa_answer`: `"confidence": 0.92`
- **Proposed Repair**: Derive confidence from model output probabilities (e.g. softmax entropy or top-1 probability). If running heuristic fallback, explicitly report `confidence_calibrated: False` and compute confidence from heuristic support (e.g. signal-to-noise ratio or feature variance).
- **Test Required**: `test_confidence_not_static()` verifying confidences vary based on input data and are marked uncalibrated if not empirically verified.
- **Status**: Remediation in progress.

---

### Finding BUG-06: Unvalidated Spatial Alignment in Bi-temporal Change Detection
- **File**: `backend/services/change/change_service.py`, `backend/geospatial/normalizer.py`
- **Function/Class**: `BiTemporalChangeSpecialist.execute()`
- **Severity**: High (Potential Spatial Mismatch)
- **Reproducibility**: 100% when input rasters have differing extents or projections
- **Root Cause**: Arrays are bilinearly resized to $256 \times 256$ without verifying whether coordinate reference systems (CRS), affine transforms, or bounding boxes match.
- **Proposed Repair**: Add geospatial header inspection verifying CRS and bounds overlap. If misaligned, raise a warning or invoke geometric reprojection prior to difference analysis.
- **Test Required**: `test_bitemporal_alignment_validation()`.
- **Status**: Scheduled for Stage 1 / Stage 3.

---

### Finding BUG-07: Static Accuracy Log String in QML Service
- **File**: `backend/qml/integration/qml_service.py`
- **Function/Class**: `QMLService.get_or_create_model()`
- **Severity**: Medium (Misleading Log Metadata)
- **Reproducibility**: 100% upon loading checkpoint
- **Root Cause**: Line 67 prints:
  ```python
  print(f"[QMLService] Loaded verified QML checkpoint (Acc: 76.37%) from {ckpt_path}")
  ```
  The string `(Acc: 76.37%)` is hardcoded in the print statement rather than read from the checkpoint's accompanying `evaluation_results.json`.
- **Proposed Repair**: Load metrics dynamically from `evaluation_results.json` or omit static metric assertions during weight loading.
- **Test Required**: Code review and static analysis.
- **Status**: Remediation in progress.
