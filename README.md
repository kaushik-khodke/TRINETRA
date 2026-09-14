# SatQuery AI (TRINETRA)
### 100% Local-First Agentic Vision-Language Assistant for Multimodal Remote Sensing
**SIH 2026 • Problem Statement ID: 26167**  
**Organization:** Indian Space Research Organisation (ISRO)  
**Theme:** Space Technology / Software • **Air-Gapped & Secure**

---

## 1. System Architecture: LangGraph StateGraph & Local AI

SatQuery AI (TRINETRA) is an air-gapped, query-driven Earth observation intelligence platform built strictly with **100% local models, real satellite rasters, and offline-capable frameworks**. It eliminates all external cloud API dependencies (zero Google Gemini, OpenAI, or Anthropic calls).

```text
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
        │      LANGGRAPH STATEGRAPH WORKFLOW ORCHESTRATOR         │
        │         (backend/agent/langgraph_orchestrator.py)       │
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
   │  • HyperFree-B Hyperspectral Foundation Specialist (224 bands)      │
   │  • Experimental PennyLane Quantum Machine Learning (QML) VQC       │
   └─────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │            MISSION REPORT GENERATOR & TACTICAL HUD                  │
   │  • Downloadable HTML & JSON Mission Intelligence Reports            │
   │  • Observable Execution Traces with verifiable pixel evidence       │
   │  • Direct Deep-Linking to Shatnetra 3D Earth Globe Engine           │
   └─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Local LLM Setup with Ollama

SatQuery AI leverages the local Ollama daemon for natural language reasoning across specialized roles:

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

## 3. Observability with Langfuse

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

## 4. Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- (Optional, for GPU training) NVIDIA GPU with CUDA 12.1+

### A. Start the Backend API
In `backend/`:
```powershell
cd backend
python run_backend.py
```
- API live at: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health & LLM Status: `http://127.0.0.1:8000/api/v1/health`

### B. Start the Frontend Command Center
In `frontend/`:
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

### C. Start the Shatnetra 3D Earth Globe
In `shatnetra/`:
```powershell
cd shatnetra
npm run dev -- --port 4173
```
Open `http://localhost:4173` in your browser.

---

## 5. GPU Training & D: Drive Environment Setup

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

### Evaluating Checkpoints
```powershell
& "D:\satquery_env\Scripts\python.exe" backend/training/03_grounding/evaluate.py `
  --checkpoint "backend/models/checkpoints/rs_grounding_model/model.pt" `
  --data_dir "D:\datasets\DIOR_RSVG"
```

---

## 6. Verification & Test Suite

Run the full end-to-end integration and regression test suites:
```powershell
# 1. Existing modalities regression test (VQA, Grounding, Captioning, Change, Fusion)
python -m unittest backend/tests/test_agent_pipeline.py

# 2. Hyperspectral, non-remote-sensing rejection, and LangGraph tests
python -m unittest backend/tests/test_hyperspectral_langgraph.py

# 3. Local agent migration and cloud purge tests
python backend/tests/test_local_agent_migration.py
```

Tests systematically verify:
1. **Complete Cloud Purge**: Zero references to Google Gemini keys, imports, or endpoints across codebase.
2. **Local LLM Provider**: Ollama provider and dynamic model registry behavior.
3. **Multi-Step Agent Planner**: Decomposition and tool sequencing with local fallbacks.
4. **Tool Safety & Parameter Validation**: Boundary checks and path traversal protection.
5. **Non-Blocking Telemetry**: Langfuse tracing resilience when server is offline.
6. **Core Workflows**: End-to-end execution of Single VQA, Text Grounding, Bi-temporal Change, Optical-SAR Fusion, and Hyperspectral (HSI) analysis.

---

## 7. Key Project References & Guides

- **[`SUMMARY.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/SUMMARY.md)**: High-level executive overview, workflows, and system design.
- **[`TRINETRA_QML_PennyLane.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/TRINETRA_QML_PennyLane.md)**: PennyLane Quantum Machine Learning research documentation.
- **[`backend/training/README.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/backend/training/README.md)**: Complete guide for training all deep learning models on genuine benchmark datasets.
- **[`docs/TRINETRA_INTEGRATION.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/TRINETRA_INTEGRATION.md)**: TRINETRA 3D Globe Deep-Linking and coordinates handling.
