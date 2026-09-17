# TRINETRA Architecture Audit (Stage 1 Baseline)

## 1. System Overview

TRINETRA (SatQuery AI) is a multimodal remote-sensing AI decision support system designed for earth observation query processing, bi-temporal change detection, optical-SAR multimodal fusion, hyperspectral characterization, and visual question answering (VQA).

```
[ User / Analyst ]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Frontend Clients                                       │
│  - Next.js Intelligence Dashboard (frontend/)          │
│  - Shatnetra Cesium 3D Geospatial Globe (shatnetra/)   │
└───────────────────────┬────────────────────────────────┘
                        │ HTTP / JSON API
                        ▼
┌────────────────────────────────────────────────────────┐
│ FastAPI Gateway (backend/app/main.py)                  │
│  - Request routing, raster uploads, session state      │
│  - LangGraph Orchestration & Task Classification       │
└───────────┬────────────────────────────────────────────┘
            │
            ├───────────────────────────────────────────────────┐
            │ Operational Classical Pipeline                    │ Experimental Research
            ▼                                                   ▼
┌───────────────────────────────────────────────┐ ┌──────────────────────────────────────┐
│ Specialist Model Engines (backend/services/)   │ │ QML Research Branch (backend/qml/)   │
│  - Change Specialist (Siamese Differential)   │ │  - PennyLane VQC (4-8 qubits)        │
│  - Optical-SAR Specialist (Cross-Attention)   │ │  - AngleEmbedding & StronglyEntangled│
│  - Hyperspectral Specialist (HyperFree-B)     │ │  - Zero-leakage PCA feature pipeline │
│  - RS-VQA Specialist (Bilinear Fusion)        │ │  - Classical baseline comparison     │
│  - RS Grounding Specialist (Text-Guided BBox) │ │  - Agreement / Disagreement analysis │
│  - Captioning Specialist (Vision-Language)    │ │  - Controlled LangChain Tool         │
└───────────────────────┬───────────────────────┘ └──────────────────┬───────────────────┘
                        │                                            │
                        ▼                                            │
┌───────────────────────────────────────────────┐                    │
│ Geospatial Processing (backend/geospatial/)   │                    │
│  - GDAL / Rasterio / NumPy readers            │                    │
│  - Radiometric normalizers & spectral indices │                    │
│  - Evidence visual overlays & heatmap renders │                    │
└───────────────────────┬───────────────────────┘                    │
                        │                                            │
                        ▼                                            │
┌───────────────────────────────────────────────┐                    │
│ Evidence & LLM Reasoning (backend/services/)  │                    │
│  - LLMReasoningEngine (synthesizer)           │                    │
│  - Structured Evidence Assembly               │◄───────────────────┘
│  - Final Analytical Report Formulation        │
└───────────────────────────────────────────────┘
```

---

## 2. Component Breakdown

### 2.1 API & Orchestration Layer
- **File**: `backend/app/main.py`
- **Responsibilities**: Multipart file upload handling, task resolution (via regex and routing heuristics), orchestrating specialist execution, and aggregating JSON responses.
- **Current Observation**: Coordinates workflow execution; however, error-handling across missing modalities and partial raster loads needs standardized typing.

### 2.2 Model Management & Weights Lifecycle
- **Files**: `backend/models/architectures.py`, `backend/models/loader.py`
- **Architectures**:
  - `SiameseChangeDiffNet`: ResNet-based bi-temporal Siamese feature extractor with differential head.
  - `OpticalSARCrossAttentionNet`: Dual-stream encoder with cross-attention fusion between optical RGB/NIR and SAR VV/VH.
  - `RSVqaFusionNetwork`: Dual-branch image and question embedding network with multi-modal bilinear pooling.
  - `RSGroundingDetector`: Visual-text grounding bounding box regressor.
  - `HyperFreeB`: Spectral-spatial 3D/2D CNN for hyperspectral data cubes.
- **Current Observation**: Model loading in `loader.py` uses `strict=False` and catches loading errors silently. It reports `loaded: True` even when no checkpoint exists on disk.

### 2.3 Specialist Services
- **Change Detection**: `backend/services/change/change_service.py`
- **Optical-SAR Fusion**: `backend/services/optical_sar/optical_sar_service.py`
- **Hyperspectral**: `backend/services/hyperspectral/`
- **RS-VQA**: `backend/services/vqa/vqa_service.py`
- **Grounding & Captioning**: `backend/services/grounding/`, `backend/services/captioning/`
- **Current Observation**: Each service wraps both a PyTorch neural path and a heuristic radiometric/algorithmic CV fallback path. The fallback path was previously disguised as high-confidence neural outputs.

### 2.4 Geospatial Processing
- **Files**: `backend/geospatial/reader.py`, `normalizer.py`, `overlays.py`
- **Responsibilities**: GeoTIFF ingestion, dynamic radiometric stretching (percentile-based), spectral indices ($\text{NDVI}$, $\text{NDWI}$, $\text{NDBI}$), SAR decibel ($\text{dB}$) conversion, and heatmap/overlay rendering.
- **Current Observation**: Array resizing currently relies on PIL bilinear interpolation without strict CRS validation or geospatial grid alignment checking.

### 2.5 Quantum Machine Learning (QML) Research Branch
- **Directory**: `backend/qml/`
- **Design**: PennyLane-based Variational Quantum Classifier (VQC) using parameterized quantum circuits (`AngleEmbedding` + `StronglyEntanglingLayers` / `BasicEntanglerLayers`).
- **Data Flow**: Consumes real 4–8 dimensional feature vectors produced from real satellite data via training-set-fitted PCA.
- **Decoupling**: Operational classical pipeline runs independently; QML runs as an experimental research layer.

---

## 3. Architecture Strengths & Deficiencies

### Strengths
1. Clear domain modularization across remote-sensing specializations.
2. Dual-path design allowing the system to operate even when heavy neural checkpoints are unmounted.
3. Clean experimental isolation of the QML research layer from the primary operational classical path.
4. Rich visual evidence generation (overlays, heatmaps, composites).

### Deficiencies Identified (Targeted in Stage 1 & 2)
1. **Unchecked Boundaries**: Services lack Pydantic validation schemas across inputs and intermediate outputs.
2. **Deceptive State**: Fallbacks report `"loaded": True` and mimic neural inference instead of declaring heuristic execution.
3. **Magic Numbers**: Preprocessing, thresholds, and confidence values are scattered as constants across service files.
4. **Geospatial Assumptions**: Equal pixel dimensions are assumed to mean spatial coregistration, ignoring CRS and geospatial affine transforms.
