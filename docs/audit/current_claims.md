# TRINETRA Current Claims Audit (Stage 1)

## Purpose
This document audits all public, UI, and code claims made regarding system performance, model accuracy, verification status, and benchmarks. Each claim is evaluated for factual accuracy, data provenance, and alignment with the **Non-Negotiable Principles**.

---

## 1. System Claims vs Scientific Reality

| Claim ID | Source / Location | Claim Text / Assertion | Evaluation | Required Correction |
| :--- | :--- | :--- | :--- | :--- |
| **CLM-01** | `backend/models/loader.py` | Model engine reported as `"loaded": True` when no weights file exists. | **False / Deceptive**. Heuristic fallback was falsely reported as a loaded neural engine. | Report `"loaded": False` and explicitly declare fallback mode. |
| **CLM-02** | `backend/services/optical_sar/` | Optical-SAR correlation claimed to be `0.84`, with `"Verified cross-modal radiometric registration"`. | **Unsubstantiated / Hardcoded**. 0.84 is a static constant in code. | Compute real Pearson correlation and SSIM dynamically; do not claim verified registration without geometric header validation. |
| **CLM-03** | `backend/services/llm_engine.py` | Confidence values of `91%`–`95%` returned across various specialist outputs. | **Uncalibrated / Arbitrary**. Hardcoded constants in synthesis functions. | Derive confidences from actual model output logits or feature variance; flag as uncalibrated when not empirically scaled. |
| **CLM-04** | `backend/qml/integration/` | Log message asserts `(Acc: 76.37%)` on QML checkpoint load. | **Partially Verified**. 76.37% was achieved on a specific local LEVIR evaluation, but embedding it as a static log message is misleading if a different checkpoint is loaded. | Load metrics strictly from the checkpoint's accompanying `evaluation_results.json`. |
| **CLM-05** | Docs & UI Presentations | "ISRO-Certified / Guaranteed SOTA performance". | **Unpermitted Claim**. SOTA claims are only valid under strictly matched benchmark protocols. ISRO certification cannot be claimed without official government evaluation. | Restrict claims to: *"Independently benchmarked against published ground-truth datasets using reproducible evaluation protocols."* |
| **CLM-06** | Bitemporal Spatial Coregistration | Bitemporal images assumed aligned if array dimensions match. | **Invalid Heuristic**. Equal shape does not guarantee CRS alignment or spatial extent overlap. | Require explicit bounding box intersection and CRS checks. |

---

## 2. Claim Sanitization Directives

1. **Eliminate All Absolute Claims**:
   - Disallow terms like "Always correct", "100% verified", "Fully coregistered" unless proven by geometric transforms or ground truth masks.
2. **Explicit Uncertainty**:
   - Whenever reference ground truth is absent (e.g. ad-hoc user raster upload), report predictions with explicit uncertainty and mark results as *"Inference without verified ground-truth reference"*.
3. **Transparent Fallback Attribution**:
   - When running heuristic or radiometric CV algorithms in place of unmounted neural networks, the engine must state:
     - `engine: "Heuristic / Radiometric CV Engine (Fallback)"`
     - `fallback_used: true`
     - `fallback_reason: "Model weights not present on disk"`
