# SatQuery AI (TRINETRA)
### 100% Local-First Agentic Vision-Language Assistant for Multimodal Remote Sensing
**Smart India Hackathon 2026 • Problem Statement ID: 26167**  
**Organization:** Indian Space Research Organisation (ISRO)  
**Theme:** Space Technology / Software • **Air-Gapped, Local-First, Zero Cloud Dependencies**

---

## 1. System Architecture: 100% Local-First Agentic AI

SatQuery AI (TRINETRA) is an air-gapped, query-driven remote-sensing intelligence platform built strictly with **100% local models and offline-capable frameworks**. It eliminates all dependencies on external cloud APIs (zero Google Gemini, OpenAI, or Anthropic calls).

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      SATQUERY AI ARCHITECTURE                          │
 └────────────────────────────────────────────────────────────────────────┘
                                     │
                 User Query & Satellite Raster Inputs
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │        FASTAPI GATEWAY (backend/app/main.py)           │
        └─────────────────────────────────────────────────────────┘
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │       MASTER AGENT CONTROLLER (LangChain Agent)         │
        │           (backend/agent/controller.py)                 │
        └─────────────────────────────────────────────────────────┘
                   │                             │
                   ▼                             ▼
   ┌───────────────────────────────┐ ┌──────────────────────────────────┐
   │    LOCAL OLLAMA INFERENCE     │ │    LANGFUSE TRACING & SPANS      │
   │  • Planner: qwen2.5:9b        │ │  • satquery_analysis_<id>        │
   │  • Fast Router: qwen2.5:4b    │ │  • Step latency & tokens         │
   │  • Lightweight: llama3.2      │ │  • Non-blocking / air-gapped safe│
   └───────────────────────────────┘ └──────────────────────────────────┘
                   │
                   ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │       DETERMINISTIC SPECIALIST ENGINES & GEOSPATIAL PIPELINE        │
   │  • Input & Pair Compatibility Validator (CRS, spatial extent, bands)│
   │  • RS-VQA Specialist (Radiometric spectral index reasoning)        │
   │  • RS-Grounding Specialist (Hydrological & feature bounding boxes)  │
   │  • RS-Captioning Specialist (Corine-style land-cover statistics)    │
   │  • Bi-Temporal Change Specialist (NDVI/NDWI & Solar Amber heatmaps) │
   │  • Optical–SAR Fusion Specialist (Microwave backscatter dB + opt)   │
   └─────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │            MISSION REPORT GENERATOR & TACTICAL HUD                  │
   │  • Downloadable HTML & JSON Mission Intelligence Reports            │
   │  • Observable Execution Traces with verifiable pixel evidence       │
   │  • Live Interactive Leaflet Map & Dual Raster Slider                │
   └─────────────────────────────────────────────────────────────────────┘
```

---

## 2. The 5 Specialist Deep Learning Models

All specialist models in SatQuery AI are custom-engineered PyTorch neural networks deployed locally in `backend/models/checkpoints/`:

| Specialist Model | Architecture | Training Dataset | Input / Output | Deployed Status |
| :--- | :--- | :--- | :--- | :---: |
| **BigEarthNet Adapted** | ResNet Backbone + Multi-Label Head | BigEarthNet-S2 v2.0 (reBEN) | 4-Band Sentinel-2 $\rightarrow$ 19 CORINE Land Classes | ✅ `model.pt` |
| **RS-VQA Specialist** | CNN Visual Backbone + GRU Text Encoder + Bilinear Fusion MLP | RSVQA Low/High Resolution | Satellite Image + Natural Language Query $\rightarrow$ Top-1/Top-5 Answer Logits | ✅ `model.pt` + `vocab.json` |
| **RS-Grounding Specialist** | Multi-Scale CNN + Word Embeddings + Bounding Box Regressor Head | DIOR-RSVG Benchmark | Satellite Image + Referring Text Expression $\rightarrow$ Normalized `[ymin, xmin, ymax, xmax]` | ✅ `model.pt` (Finetuned) |
| **Change Specialist** | Siamese Bi-Temporal ResNet + Difference Attention Head | OSCD / LEVIR-CD | Time-1 + Time-2 Sentinel-2 Rasters $\rightarrow$ Binary Change Mask & Magnitude Map | ✅ `model.pt` |
| **Optical–SAR Fusion** | Dual-Encoder Cross-Modal Cross-Attention Network | SEN1-2 / BigEarthNet-MM | Optical RGB + SAR VV/VH Backscatter (dB) $\rightarrow$ Fused Feature Map | ✅ `model.pt` |

---

## 3. RS-Grounding Model Finetuning Achievements

The **Text-Guided Region Grounding Network** (`rs_grounding_model`) was finetuned and evaluated on the official IEEE TGRS **DIOR-RSVG** satellite visual grounding benchmark:

- **Benchmark Rules**: Strictly **Zero Synthetic Data** (trained on 20,000 genuine satellite referring expressions) and **Zero Split Leakage** across Train (26,991), Val (3,829), and Test (7,500) splits.
- **Hardware Acceleration**: Executed on local **NVIDIA GeForce RTX 3050 Laptop GPU** with Automatic Mixed Precision (AMP FP16).
- **Coordinate Sorting Fix**: Fixed bounding box metric sorting so that predicted intervals guarantee $y_{\text{min}} < y_{\text{max}}$ and $x_{\text{min}} < x_{\text{max}}$, allowing mathematical IoU to compute real spatial overlap without degenerate areas.

### Official Benchmark Evaluation Results (Held-Out Test Split):

| Evaluation Metric | Untrained Baseline (Prior) | Initial Fast Run | **Our Finetuned GPU Model** | Net Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **Recall@0.50 (Accuracy)** | 0.00% | 6.32% | **16.32%** | **+16.32% (From 0% to 16.32%)** |
| **Mean IoU (mIoU)** | 0.0002 (0.02%) | 0.1193 (11.93%) | **0.2233 (22.33%)** | **+22.31% absolute gain** |
| **Recall@0.75 (High Precision)** | 0.00% | 0.99% | **2.00%** | **+2.00%** |
| **Median IoU** | 0.0000 | 0.0294 | **0.1391** | **+0.1391** |
| **Training Loss** | — | 0.6702 | **0.4384** | **Substantial Convergence** |
| **Deployed Checkpoint** | — | — | [`backend/models/checkpoints/rs_grounding_model/model.pt`](file:///d:/hackathon/SatQuery%20AI/backend/models/checkpoints/rs_grounding_model/model.pt) | **Active in Backend** |

---

## 4. Local LLM Setup with Ollama

SatQuery AI leverages the local Ollama daemon for inference across specialized roles:

| Role | Configured Model | Primary Responsibility | Context |
| :--- | :--- | :--- | :--- |
| **Planner** | `qwen2.5:9b` | Multi-step query decomposition, tool sequencing, synthesis | 8K |
| **Fast Router** | `qwen2.5:4b` | High-speed task classification and parameter parsing | 4K |
| **Lightweight** | `llama3.2` | Fast summaries, schema validation, fallback reasoning | 4K |

### Setup Steps:
1. Ensure [Ollama](https://ollama.com) is installed and running (`ollama serve` or Windows system service).
2. Pull the required models:
   ```bash
   ollama pull qwen2.5:9b
   ollama pull qwen2.5:4b
   ollama pull llama3.2
   ```
3. Verify connection:
   ```bash
   curl http://localhost:11434/api/tags
   ```

*Deterministic Fallback Engine:* If Ollama has not loaded a model yet or is temporarily stopped, SatQuery AI automatically falls back to its deterministic spatial physics reasoning engine (computing exact NDVI, NDWI, SAR dB, and connected components) with zero hallucinations and zero crashes.

---

## 5. Observability with Langfuse

Every satellite analysis session is instrumented with hierarchical telemetry:
- **Trace ID**: `satquery_analysis_<id>`
- **Spans**: `input_validation`, `agent_planning`, `tool_parameter_safety`, `raster_ingestion`, `specialist_execution`, `report_generation`
- **Safe Non-Blocking Design**: Scientific geospatial computations will **never** fail or slow down if Langfuse is offline or unconfigured.

Configure via environment variables (`.env`):
```bash
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-local-telemetry
LANGFUSE_SECRET_KEY=sk-lf-local-telemetry
```

---

## 6. Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- (Optional, for GPU training) NVIDIA GPU with CUDA 12.1+

### A. Start the Backend API
In `backend/`:
```bash
cd backend
python run_backend.py
```
- API live at: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health & Model Status: `http://127.0.0.1:8000/api/v1/health`

### B. Start the Frontend Command Center
In `frontend/`:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` (or `http://localhost:5173`) in your browser.

---

## 7. GPU Training & D: Drive Virtual Environment Setup

To bypass Windows C: drive storage limitations when installing large PyTorch CUDA wheels (~5.5 GB uncompressed), SatQuery AI includes an automated D: drive virtual environment setup script:

```powershell
# Run the automated D: drive environment setup (uses 0 bytes on C:)
.\setup_d_env.ps1
```

### Running Model Training on GPU
```powershell
# Train RS-Grounding model with CUDA on RTX 3050 GPU
& "D:\satquery_env\Scripts\python.exe" backend/training/03_grounding/train.py `
  --data_dir "D:\datasets\DIOR_RSVG" `
  --profile balanced `
  --epochs 15 `
  --weights "backend/models/checkpoints/rs_grounding_model/model.pt" `
  --export
```

### Evaluating Any Checkpoint
```powershell
& "D:\satquery_env\Scripts\python.exe" backend/training/03_grounding/evaluate.py `
  --checkpoint "backend/models/checkpoints/rs_grounding_model/model.pt" `
  --data_dir "D:\datasets\DIOR_RSVG"
```

---

## 8. Verification & Integration Test Suite

Run the full end-to-end integration and local migration test suite:
```bash
python backend/tests/test_local_agent_migration.py
```
Tests systematically verify:
1. **Complete Cloud Purge**: Zero references to Google Gemini keys, imports, or endpoints across the codebase.
2. **Local LLM Provider**: Ollama provider and dynamic model registry behavior.
3. **Multi-Step Agent Planner**: Decomposition and tool sequencing with local fallbacks.
4. **Tool Safety & Parameter Validation**: Boundary checks and path traversal protection.
5. **Non-Blocking Telemetry**: Langfuse tracing resilience when the server is offline.
6. **4 Core Workflows**: End-to-end execution of Single VQA, Text Grounding, Bi-temporal Change, and Optical-SAR Fusion.

---

## 9. Key Project References & Guides

- **[`SUMMARY.md`](file:///d:/hackathon/SatQuery%20AI/SUMMARY.md)**: High-level executive overview, workflows, and system design.
- **[`backend/training/README.md`](file:///d:/hackathon/SatQuery%20AI/backend/training/README.md)**: Complete guide for training all 5 deep learning models on genuine benchmark datasets.
- **[`SatQuery_AI_PRD.md`](file:///d:/hackathon/SatQuery%20AI/SatQuery_AI_PRD.md)**: Product Requirements Document.
- **[`SatQuery_AI_TRD.md`](file:///d:/hackathon/SatQuery%20AI/SatQuery_AI_TRD.md)**: Technical Architecture Document.
