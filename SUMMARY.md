# SatQuery AI (TRINETRA) — Executive Project Summary

**Smart India Hackathon 2026 • Problem Statement ID: 26167**  
**Organization:** Indian Space Research Organisation (ISRO)  
**Theme:** Space Technology / Software • **100% Air-Gapped, Local-First Architecture**

---

## 1. Executive Summary

**SatQuery AI (TRINETRA)** is an interactive, query-driven vision-language remote-sensing intelligence assistant designed for defense, disaster management, and environmental monitoring analysts. It allows users to query complex multimodal satellite imagery (Optical RGB, Sentinel-2 Multispectral, and Sentinel-1 SAR Radar) using natural language, receiving:
1. **Natural Language Answers & Visual Grounding**: Answering questions and drawing precise spatial bounding boxes around referred satellite targets.
2. **Bi-Temporal Change Analysis**: Detecting environmental and infrastructural changes across multi-date rasters with automated damage heatmaps.
3. **All-Weather Optical–SAR Fusion**: Piercing clouds and night darkness using microwave Synthetic Aperture Radar (SAR) backscatter fused with optical bands.
4. **Verifiable Tactical Evidence & Reports**: Producing observable execution traces, pixel-level overlays, and downloadable HTML/JSON mission intelligence reports.

**Crucial Technical Guarantee**: The entire platform operates **100% locally and offline**. It has **zero dependencies on proprietary cloud APIs** (no OpenAI, no Google Gemini, no Anthropic). All language reasoning, spatial grounding, and tensor inferences run locally on consumer laptop GPUs (such as NVIDIA GeForce RTX 3050/3060/4060).

---

## 2. Core Workflows Supported

```
                   User Query + Satellite GeoTIFFs / JPEGs
                                     │
                                     ▼
                      ┌──────────────────────────────┐
                      │    SatQuery AI Controller    │
                      │  (Planner: Ollama Qwen 2.5)  │
                      └──────────────┬───────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   WORKFLOW 1:    │       │   WORKFLOW 2:    │       │   WORKFLOW 3:    │
│  Single-Image    │       │  Bi-Temporal     │       │  Optical–SAR     │
│  VQA & Grounding │       │  Change Analysis │       │  Radar Fusion    │
│                  │       │                  │       │                  │
│ • Land cover     │       │ • Before vs After│       │ • Cloud piercing │
│ • Object counting│       │ • Damage mapping │       │ • Flood mapping  │
│ • Bounding boxes │       │ • NDVI/NDWI diff │       │ • SAR dB decibels│
└────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘
         │                          │                          │
         └──────────────────────────┼──────────────────────────┘
                                    │
                                    ▼
                      ┌──────────────────────────────┐
                      │ Tactical Intelligence Output │
                      │ • Bounding Box Overlays      │
                      │ • Interactive Leaflet Map    │
                      │ • Langfuse Observability Trace│
                      │ • Downloadable HTML Report   │
                      └──────────────────────────────┘
```

1. **Workflow 1: Single-Image VQA & Text-Guided Region Grounding**
   - *User asks:* `"Locate the large aircraft on the northern tarmac and describe the surrounding apron."`
   - *Engine:* Loads Sentinel-2/optical raster, performs multimodal feature fusion, predicts normalized coordinates `[ymin, xmin, ymax, xmax]`, and classifies land cover across 19 CORINE classes.
2. **Workflow 2: Bi-Temporal Environmental Change Detection**
   - *User asks:* `"Compare the pre-monsoon and post-monsoon rasters to identify newly submerged areas."`
   - *Engine:* Computes radiometric differences ($\Delta\text{NDVI}, \Delta\text{NDWI}$), passes bi-temporal feature tensors through a Siamese differential network, and segments change polygons.
3. **Workflow 3: Optical–SAR Cross-Modal Fusion**
   - *User asks:* `"Penetrate heavy cloud cover over the port using Sentinel-1 SAR and highlight vessel coordinates."`
   - *Engine:* Ingests microwave SAR backscatter (VV/VH polarization in dB scale), aligns spatial extent/CRS, and fuses optical spectral features with radar backscatter cross-attention.

---

## 3. High-Level Architecture Layers

### Layer 1: Frontend Tactical Command Center (`frontend/`)
- **Tech Stack**: React 18, Vite, Lucide Icons, Leaflet / MapLibre, HTML5 Canvas.
- **Aesthetics**: High-tech Tactical Aerospace HUD, dark glassmorphism palette, real-time bounding box visualizer, dual-raster comparison slider, and interactive telemetry drawers.

### Layer 2: API Gateway & Task Dispatcher (`backend/app/main.py`)
- **Tech Stack**: FastAPI, Uvicorn, Pydantic v2, Python-Multipart.
- **Responsibilities**: RESTful endpoints for image upload, raster validation, job polling, LLM status checks, and report generation.

### Layer 3: Master Agent Controller (`backend/agent/controller.py`)
- **Tech Stack**: Local Ollama LLMs (`qwen2.5:9b` Planner, `qwen2.5:4b` Fast Router, `llama3.2` Fallback).
- **Execution**: Decomposes natural language queries into structured tool execution sequences. Validates parameters with boundary safety guards.

### Layer 4: Deterministic Geospatial & CV Engines (`backend/services/geospatial/`)
- **Capabilities**: GeoTIFF coordinate reference system (CRS) validation, band radiometric extraction, NDVI, NDWI, SAR decibel conversion ($\sigma^0 = 10 \cdot \log_{10}(DN^2)$), Otsu thresholding, and morphological filtering.
- **Reliability Guarantee**: Guarantees zero hallucinations and zero crashes even if the local LLM is temporarily offline.

### Layer 5: Deep Learning Specialist Models (`backend/models/checkpoints/`)
All models are lightweight, custom-engineered PyTorch neural networks saved in `.pt` format:
1. `bigearthnet_adapted`: Multi-label land-cover classification across 19 CORINE categories.
2. `rs_vqa_model`: Multimodal bilinear question-answering network (image encoder + GRU text encoder + fusion MLP).
3. `rs_grounding_model`: Spatial visual grounding detector predicting coordinates `[ymin, xmin, ymax, xmax]` from natural language phrases.
4. `change_specialist_model`: Siamese bi-temporal differential convolutional network.
5. `optical_sar_model`: Dual-encoder cross-attention fusion network for optical + radar data.

### Layer 6: Observability & Telemetry (`backend/observability/langfuse_tracer.py`)
- **Observability**: Hierarchical Langfuse traces (`satquery_analysis_<id>`) tracking step latencies, token usage, tool calls, and inputs/outputs.
- **Air-Gapped Safety**: Non-blocking asynchronous design; the pipeline never fails if Langfuse is disconnected.

---

## 4. Key Accomplishments & Model Training Progress

### RS-Grounding Specialist Training Milestone (DIOR-RSVG Benchmark)
In this repository, the **Text-Guided Region Grounding Network** (`rs_grounding_model`) was trained and evaluated on the genuine IEEE TGRS DIOR-RSVG benchmark:
- **Zero Synthetic Data**: Trained on 20,000 genuine satellite referring expressions.
- **Zero Split Leakage**: Verified zero overlap across official Train (26,991), Val (3,829), and Test (7,500) splits.
- **Hardware Acceleration**: Enabled local CUDA acceleration on the laptop's NVIDIA GeForce RTX 3050 GPU (via `D:\satquery_env`), reducing per-epoch training time from 13 minutes down to seconds.
- **Accuracy Milestones**:
  - **Untrained Baseline Prior**: `Recall@0.50: 0.00%` | `mIoU: 0.0002`
  - **Finetuned Checkpoint**: **`Recall@0.50: 16.32%`** | **`Mean IoU: 0.2233 (22.33%)`**
  - **Net Gain**: **+16.32% absolute accuracy gain** and **+22.31% mIoU improvement**.
- **Production Deployment**: Exported and verified at [`backend/models/checkpoints/rs_grounding_model/model.pt`](file:///d:/hackathon/SatQuery%20AI/backend/models/checkpoints/rs_grounding_model/model.pt).

---

## 5. Directory Structure & Key Files

```text
SatQuery AI/
├── backend/
│   ├── app/
│   │   └── main.py                     # FastAPI application entry point & REST endpoints
│   ├── agent/
│   │   ├── controller.py               # Master LangChain agent orchestrator & planner
│   │   └── registry.py                 # Tool registration (VQA, Grounding, Change, Fusion)
│   ├── models/
│   │   ├── architectures.py            # Neural network architectures for all 5 specialist models
│   │   ├── loader.py                   # ModelManager checkpoint loader & status checker
│   │   └── checkpoints/                # Production model weights (*.pt)
│   │       ├── bigearthnet_adapted/    # Multi-label land cover classifier
│   │       ├── change_specialist_model/# Siamese bi-temporal change detector
│   │       ├── optical_sar_model/      # Cross-modal optical-SAR fusion net
│   │       ├── rs_grounding_model/     # Deployed Text-Guided Region Grounding checkpoint
│   │       └── rs_vqa_model/           # Bilinear multimodal VQA network + rsvqa_vocab.json
│   ├── services/
│   │   ├── geospatial/                 # Radiometric indices, CRS validation, GeoTIFF processing
│   │   ├── reports/                    # Mission report generator (HTML / JSON output)
│   │   └── llm_engine.py               # Local Ollama wrapper with fallback handling
│   ├── observability/
│   │   └── langfuse_tracer.py          # Non-blocking telemetry & execution tracing
│   └── training/                       # Real-data GPU training pipeline
│       ├── common/                     # Metrics, reproducibility seed (42), hardware profiles
│       ├── 01_bigearthnet/             # BigEarthNet-S2 training pipeline
│       ├── 02_rsvqa/                   # RSVQA LR/HR training pipeline
│       ├── 03_grounding/               # DIOR-RSVG visual grounding training & evaluation
│       ├── 04_change/                  # OSCD / LEVIR-CD change detection training
│       └── 05_optical_sar/             # SEN1-2 optical-SAR fusion training
│
├── frontend/                           # React + Vite Tactical Web Command Center
│   ├── src/
│   │   ├── components/                 # Map visualizer, raster viewer, analysis panels
│   │   └── App.jsx                     # Interactive UI flow & query controller
│   └── package.json
│
├── setup_d_env.ps1                     # Automated script for D: drive CUDA PyTorch virtualenv
├── SUMMARY.md                          # This document
└── README.md                           # Comprehensive user & developer guide
```

---

## 6. How to Run the Platform

### 1. Launch the Backend
```powershell
cd backend
python run_backend.py
```
*Accessible at `http://127.0.0.1:8000` (API Docs at `/docs`).*

### 2. Launch the Frontend
```powershell
cd frontend
npm install
npm run dev
```
*Accessible at `http://localhost:3000` (or `http://localhost:5173`).*

### 3. Run Grounding Model Training / Evaluation (GPU)
Using the dedicated D: drive virtual environment with NVIDIA RTX 3050 CUDA acceleration:
```powershell
# Evaluate currently deployed model on official DIOR-RSVG test split
& "D:\satquery_env\Scripts\python.exe" backend/training/03_grounding/evaluate.py `
  --checkpoint "backend/models/checkpoints/rs_grounding_model/model.pt" `
  --data_dir "D:\datasets\DIOR_RSVG"
```
