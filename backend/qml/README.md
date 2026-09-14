# TRINETRA / SatQuery AI — Quantum Machine Learning (PennyLane) Research Suite

**SIH 2026 Problem Statement 26167 • Indian Space Research Organisation (ISRO)**  
**Architecture Theme**: Hybrid Quantum-Classical Remote Sensing Intelligence  
**Framework**: PennyLane (`pennylane >= 0.35.0`) with PyTorch Integration  
**Policy**: **100% Real Data Only • ZERO Synthetic Data • Non-Breaking Additive Design**

---

## 1. Objective & Research Motivation

SatQuery AI introduces a **quantum-ready research layer** alongside its operational classical remote-sensing models. 

- **Operational Baseline**: Classical specialist models (`SiameseChangeDiffNet`, `BigEarthNetAdaptedResNet`, `OpticalSARCrossAttentionNet`, `RSGroundingDetector`) remain the primary operational source of truth.
- **Quantum Research Branch**: A Variational Quantum Classifier (VQC) running on PennyLane simulates parameterized quantum circuits on compact features extracted from real satellite imagery.
- **Continuous Comparison**: For every query, the system evaluates the classical model first, evaluates the quantum circuit on the same inputs, and computes a formal **Agreement Report** tracking consensus, confidence delta, parameter reduction, and simulation latency.

```
REAL SATELLITE RASTER (T1, T2)
              │
              ▼
   [ CLASSICAL FEATURE ENCODER ]  ──────► Operational Result (Class, Confidence, Heatmap)
              │                                      │
              ▼                                      │
   [ PCA FEATURE PIPELINE ]                          │
        (16-d ──► 4-d)                               │
              │                                      │
              ▼                                      │
   [ QUANTUM ANGLE EMBEDDING ]                       ▼
        (RY Rotations)                 ┌───────────────────────────┐
              │                        │ CLASSICAL vs QML          │
              ▼                        │ AGREEMENT & COMPARISON    │
   [ ENTANGLING ANSATZ ]               │                           │
    (Strongly Entangling CNOT)         │ • Consensus Verdict       │
              │                        │ • Confidence Delta        │
              ▼                        │ • 99.9% Parameter Delta   │
   [ PAULI-Z MEASUREMENT ]             │ • NISQ Hardware Outlook   │
              │                        └───────────────────────────┘
              ▼                                      ▲
   [ LINEAR CLASSIFIER HEAD ] ───────────────────────┘
   (35 Total Trainable Params)
```

---

## 2. Selected Algorithm & Circuit Architecture

### Algorithm: Variational Quantum Classifier (VQC)
- **Qubit Allocation**: **4 Qubits** (default, scalable to 6 or 8 qubits).
- **Embedding Scheme**: `qml.AngleEmbedding(features, wires=range(4), rotation='Y')`. Non-linearly maps continuous remote-sensing differential indices ($\Delta\text{NDVI}, \Delta\text{NDWI}$, spectral distance) into $[0, \pi]$ rotation angles on the Bloch sphere.
- **Ansatz**: Multi-layer parameterized rotations ($R_y(\theta), R_z(\phi)$) coupled with circular nearest-neighbor $CNOT$ entangling gates.
- **Measurement**: Single-qubit Pauli-Z expectation values $\langle \sigma_z^{(i)} \rangle \in [-1, 1]$.
- **Parameters**: **35 parameters total** (20 quantum rotation angles + 15 linear projection weights) vs. **1.25 Million parameters** in the classical model ($\mathbf{99.997\%}$ parameter reduction).

---

## 3. Directory Structure

```text
backend/qml/
├── TASK.md                      # Formal research & API evaluation document
├── README.md                    # This master documentation
├── config.py                    # Environment settings (QML_ENABLED, QML_DEVICE, timeouts)
├── datasets.py                  # Real remote-sensing dataset loaders (OSCD, LEVIR-CD)
├── feature_pipeline.py          # Zero-leakage StandardScaler + PCA feature reducer
├── backends/
│   ├── __init__.py
│   └── simulator.py             # QuantumBackend abstraction (default.qubit, lightning.qubit, QPU)
├── models/
│   ├── __init__.py
│   └── vqc.py                   # QuantumChangeClassifier PyTorch Module with PennyLane QNode
├── comparison/
│   ├── __init__.py
│   ├── agreement.py             # Calibrated mathematical agreement analyzer
│   └── compare_classical_qml.py # Side-by-side benchmark comparison generator
├── integration/
│   ├── __init__.py
│   └── qml_service.py           # Controller service interface with caching & safety
├── training/
│   ├── __init__.py
│   ├── train_vqc.py             # Standalone local GPU/CPU VQC training script
│   └── evaluate_vqc.py          # Benchmark evaluation on held-out test split
└── results/
    └── qml_change_v001/         # Production checkpoints, configs, and metrics
```

---

## 4. Execution Commands (Run Locally)

Using your local Python environment (`D:\satquery_env`):

### 1. Train the Variational Quantum Classifier (VQC)
```powershell
& "D:\satquery_env\Scripts\python.exe" backend/qml/training/train_vqc.py `
  --data_dir "D:\datasets\LEVIR_CD" `
  --qubits 4 `
  --layers 2 `
  --epochs 10 `
  --lr 0.02 `
  --output_dir "backend/qml/results/qml_change_v001"
```

### 2. Evaluate on Held-Out Test Split
```powershell
& "D:\satquery_env\Scripts\python.exe" backend/qml/training/evaluate_vqc.py `
  --checkpoint "backend/qml/results/qml_change_v001/best_model.pt" `
  --data_dir "D:\datasets\LEVIR_CD"
```

### 3. Generate Classical vs. QML Comparative Benchmark Table
```powershell
& "D:\satquery_env\Scripts\python.exe" backend/qml/comparison/compare_classical_qml.py `
  --classical "backend/training/04_change/runs/run_balanced/metrics.json" `
  --qml "backend/qml/results/qml_change_v001/evaluation_results.json" `
  --output "backend/qml/results/comparison_summary.json"
```

---

## 5. 15–20 Year Hardware Migration Roadmap

| Era | Architecture | Quantum Hardware Target | Execution Latency | Role in TRINETRA |
| :--- | :--- | :--- | :--- | :--- |
| **TODAY (NISQ Era)** | Hybrid Classical Feature Reduction + PennyLane Statevector Simulation | Local CPU (`default.qubit`) / GPU (`lightning.gpu`) | 15–80 ms (simulation overhead) | **Experimental Research**: Validates ansatz expressivity and agreement without changing application logic. |
| **NEXT 3–5 YEARS (Early Fault-Tolerant QPUs)** | Quantum Feature Maps + Physical QPU execution via cloud APIs | 50–127 Qubit QPUs (IBM Quantum, Rigetti, IonQ) | 100–300 ms (network/shot overhead) | **Hardware Verification**: Parameter-shift gradient optimization on real superconducting / trapped-ion qubits. |
| **10–20 YEARS (Fault-Tolerant Quantum Advantage)** | End-to-End Multimodal Quantum Machine Learning | Fault-Tolerant Quantum Computers ($>10^4$ logical qubits) | Sub-millisecond coherent gate depth | **Direct Processing**: Direct quantum Fourier transforms and full-resolution satellite tensor analysis. |
