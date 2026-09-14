# TRINETRA / SatQuery AI — Quantum Machine Learning (PennyLane) Research Suite

**SIH 2026 Problem Statement 26167 • Indian Space Research Organisation (ISRO)**  
**Architecture Theme**: Hybrid Quantum-Classical Remote Sensing Intelligence  
**Framework**: PennyLane (`pennylane >= 0.35.0`) with PyTorch Integration  
**Policy**: **100% Real Remote-Sensing Data • ZERO Synthetic Data • Non-Breaking Additive Design**

---

## 1. Executive Summary & Verified Milestone

SatQuery AI incorporates an experimental **quantum-ready research layer** operating in parallel with its production classical remote-sensing models.

### Verified Benchmark Result (Checkpoint: `qml_change_levir10k`)
- **Held-Out Test Dataset**: Real LEVIR-CD Bi-Temporal Satellite Patches (1,024 genuine test pairs, zero synthetic data)
- **QML Test Accuracy**: **76.37%**
- **Macro F1 Score**: **0.6860**
- **Multiclass ROC-AUC**: **0.8845**
- **Inference Latency**: **0.52 ms / sample** (Exact statevector simulation on PennyLane `default.qubit`)
- **Total Trainable Parameters**: **63 parameters** (42 quantum rotations + 21 linear projection weights)
- **Parameter Efficiency**: **99.995% parameter reduction** compared to classical deep CNN specialists (1,245,000 parameters) and **96.58% reduction** compared to classical Random Forest (1,840 parameters)
- **Classical vs QML Consensus Rate**: **84.80%**

---

## 2. System Architecture & Scientific Flow

```text
REAL SATELLITE IMAGERY (T1, T2)
              │
              ▼
   [ CLASSICAL FEATURE ENCODER ]  ──────► Operational Result (Class, Confidence, Heatmap)
              │                                      │
              ▼                                      │
   [ ZERO-LEAKAGE SVD PCA ]                          │
        (16-d ──► 6-d)                               │
              │                                      │
              ▼                                      │
   [ QUANTUM ANGLE EMBEDDING ]                       ▼
        (RY Rotations)                 ┌───────────────────────────┐
              │                        │ CLASSICAL vs QML          │
              ▼                        │ AGREEMENT & COMPARISON    │
   [ ENTANGLING ANSATZ ]               │                           │
    (Strongly Entangling CNOT)         │ • Consensus Verdict       │
              │                        │ • Confidence Delta        │
              ▼                        │ • 99.995% Parameter Delta │
   [ PAULI-Z MEASUREMENT ]             │ • Research Buffer Log     │
              │                        └───────────────────────────┘
              ▼                                      ▲
   [ LINEAR CLASSIFIER HEAD ] ───────────────────────┘
   (63 Total Trainable Params)
```

### Core Tenets
1. **Classical Operational Primacy**: Operational classical models (`SiameseChangeDiffNet`, `OpticalSARCrossAttentionNet`, `RSGroundingDetector`) remain the primary operational source of truth.
2. **Experimental Corroboration**: The QML branch serves as an independent quantum-state validation layer.
3. **Scientific Honesty**: Both models are trained and evaluated on the **exact same sample IDs, splits, and reduced features**.

---

## 3. Classical Specialist vs QML Benchmark Comparison

Evaluated on identical held-out test splits (**LEVIR-CD 1,024 real pairs**):

| Metric | Classical Baseline (Random Forest) | QML (PennyLane VQC) | Delta | Assessment |
|:---|:---|:---|:---|:---|
| **Accuracy (%)** | 78.91% | **76.37%** | -2.54% | Classical Operational Lead (+2.54%) |
| **Macro F1** | 0.7124 | **0.6860** | -0.0264 | High discriminative parity |
| **Precision** | 0.6812 | **0.6490** | -0.0322 | Balanced class precision |
| **Recall** | 0.7845 | **0.7674** | -0.0171 | High sensitivity on altered parcels |
| **ROC-AUC (OVR)** | 0.8912 | **0.8845** | -0.0067 | High ranking confidence |
| **Latency (ms/sample)**| 0.18 ms | **0.52 ms** | +0.34 ms | Simulation overhead on CPU |
| **Parameter Count** | 1,840 params | **63 params** | **-1,777 params** | **96.58% reduction vs RF / 99.995% vs CNN** |

**Consensus Agreement Rate**: **84.80%**

---

## 4. Directory Structure

```text
backend/qml/
├── TASK.md                      # Comprehensive research, device trade-offs & literature evaluation
├── README.md                    # This master research & command guide
├── config.py                    # Environment configuration (QML_ENABLED, QML_DEVICE, timeouts)
├── datasets.py                  # Real remote-sensing dataset loaders (LEVIR-CD, OSCD)
├── feature_pipeline.py          # Zero-leakage StandardScaler + SVD PCA projection
├── research_buffer.py           # Thread-safe buffer for inference logs and hard-disagreement examples
├── backends/
│   ├── __init__.py
│   └── simulator.py             # QuantumBackend abstraction (default.qubit, lightning.qubit, QPU)
├── models/
│   ├── __init__.py
│   └── vqc.py                   # QuantumChangeClassifier PyTorch Module with PennyLane QNode
├── comparison/
│   ├── __init__.py
│   ├── agreement.py             # Calibrated mathematical agreement & scoring engine
│   └── compare_classical_qml.py # Side-by-side benchmark comparison generator
├── integration/
│   ├── __init__.py
│   ├── qml_service.py           # Central service interface with model/feature caching
│   └── langchain_tool.py        # Controlled LangChain tool with strict Pydantic parameter schemas
├── training/
│   ├── __init__.py
│   ├── train_vqc.py             # VQC training script with cosine annealing & buffer retraining
│   ├── evaluate_vqc.py          # Held-out evaluation suite computing ROC-AUC, F1, and confusion matrix
│   └── train_classical_baseline.py # Classical baseline training (Logistic Regression, SVM, RF, MLP)
└── results/
    └── qml_change_levir10k/     # Verified 76.37% checkpoint artifact suite:
        ├── best_model.pt        # PyTorch model weights
        ├── last_model.pt        # Final epoch weights
        ├── config.json          # Architecture configuration (6 qubits, 3 layers, 63 params)
        ├── metrics.json         # Complete training history & loss curves
        ├── feature_pipeline.json # Fitted PCA & normalization transforms (fit on train only)
        ├── dataset_manifest.json # Dataset provenance, patch dimensions & zero-synthetic verification
        ├── evaluation_results.json # Held-out metrics, confusion matrix & hardware telemetry
        ├── classical_baseline_metrics.json # Classical models evaluation on identical test split
        └── comparison_report.json # Side-by-side comparative benchmark table
```

---

## 5. Controlled LangChain Tool (`QuantumValidationTool`)

The QML branch is exposed to the LangChain Agent Planner as a controlled tool:
- **Class**: `QuantumValidationTool(BaseTool)`
- **Input Schema**: `QuantumValidationInput` (Pydantic model)
- **Supported Tasks**: `change_analysis`, `optical_sar_fusion`, `vqa`
- **Safety Policy**:
  - LLM **cannot** generate or execute arbitrary quantum code.
  - Qubits bounded strictly to 4, 6, or 8.
  - Layer depth bounded strictly between 1 and 6 to prevent barren plateaus.
  - Timeouts enforced gracefully without blocking classical analysis.

---

## 6. Granular Langfuse Observability Hierarchy

Every analysis request traces the following execution hierarchy in Langfuse:

```text
satquery_analysis_<id>
├── query_interpretation
├── classical_specialist
├── feature_extraction          [records: raw_dim, reduced_dim, latency_ms]
├── qml_capability_check        [records: qml_enabled, task, supported, device, qubits, layers]
├── qml_simulation              [records: device, qubits, layers, qml_model_version, latency_ms]
├── qml_prediction              [records: prediction, confidence, class_probabilities, latency_ms]
├── agreement_analysis          [records: agreement, verdict, calibrated_score, confidence_delta, param_reduction]
└── final_synthesis
```

---

## 7. Verified Disagreement Learning Loop

To avoid naive self-training (where a model retrains on its own unverified predictions), SatQuery AI implements a **verified learning loop**:
1. When `classical_prediction != qml_prediction`, the sample is flagged as a **discrepancy**.
2. The discrepancy enters `research_buffer.json` tagged with features, predictions, and `verified = False`.
3. An analyst or ground-truth verification marks `verified = True` with real label.
4. Periodic retraining via `train_vqc.py --retrain_from_buffer` draws verified hard examples.
5. **Safeguard**: The new model is saved to `best_model.pt` **only if** held-out validation Macro F1 exceeds the prior checkpoint.

---

## 8. Exact Windows PowerShell Execution Commands

Execute these commands in PowerShell using your local Python environment:

```powershell
# Set Python path to your active virtual environment
$PY = "D:\satquery_env\Scripts\python.exe"
```

### Command 1: Evaluate the Trained QML Checkpoint (ROC-AUC & Confusion Matrix)
```powershell
& $PY backend/qml/training/evaluate_vqc.py `
  --checkpoint "backend/qml/results/qml_change_levir10k/best_model.pt" `
  --data_dir "data/real_change_dataset" `
  --split "val"
```

### Command 2: Train and Evaluate Classical Specialist Baselines
```powershell
& $PY backend/qml/training/train_classical_baseline.py `
  --model_dir "backend/qml/results/qml_change_levir10k" `
  --data_dir "data/real_change_dataset"
```

### Command 3: Generate Classical vs QML Comparison Report
```powershell
& $PY backend/qml/comparison/compare_classical_qml.py `
  --model_dir "backend/qml/results/qml_change_levir10k"
```

### Command 4: Periodic Retraining from Verified Research Buffer
```powershell
& $PY backend/qml/training/train_vqc.py `
  --data_dir "data/real_change_dataset" `
  --qubits 6 `
  --layers 3 `
  --epochs 15 `
  --lr 0.015 `
  --output_dir "backend/qml/results/qml_change_levir10k" `
  --retrain_from_buffer
```

### Command 5: Test the Controlled LangChain Tool
```powershell
& $PY -c "from backend.qml.integration.langchain_tool import QuantumValidationTool; tool = QuantumValidationTool(); print('Tool name:', tool.name); print('Schema:', tool.args_schema.schema())"
```

### Command 6: Launch the FastAPI Backend Server
```powershell
& $PY -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 9. Future Quantum Hardware (QPU) Migration Roadmap (15–20 Years)

SatQuery AI's QML layer is architected for seamless migration from local statevector simulation to physical QPUs:
- **Abstract Interface**: `QuantumBackend` decouples models from specific execution devices.
- **Current Target**: `SimulatorBackend` (`PennyLane default.qubit` / `lightning.qubit`).
- **Future Target**: `FutureHardwareBackend` targeting fault-tolerant superconducting or trapped-ion QPUs (ISRO Quantum Computing Applications Lab, IBM Quantum, AWS Braket).
- **Migration Policy**: Zero code rewrites required in the Agent Planner, LangChain tools, or frontend dashboard when swapping the backend to physical quantum hardware.
