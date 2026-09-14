# SatQuery AI (TRINETRA)
### 100% Local-First Multimodal Agentic Remote-Sensing Intelligence Platform
**Smart India Hackathon (SIH) 2026 • Problem Statement ID: 26167**  
**Organization:** Indian Space Research Organisation (ISRO)  
**Theme:** Space Technology / Software • **100% Air-Gapped & Secure**

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
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
 ┌───────────────────────────────┐               ┌──────────────────────────────────┐
 │ 4-TIER DOMAIN VALIDATOR       │               │    LANGFUSE TRACING & SPANS      │
 │ • CRS & internal GeoTIFF tags │               │  • satquery_analysis_<id>        │
 │ • Band count (HSI/MSI/SAR/RGB)│               │  • Step latency & telemetry      │
 │ • Rejects non-nadir horizon/  │               │  • Non-blocking / offline safe   │
 │   sky, documents, selfies     │               └──────────────────────────────────┘
 └───────────────────────────────┘
         │ (Valid Nadir Remote Sensing)
         ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │               ALLOW-LISTED TOOL REGISTRY & SPECIALIST PERCEPTION                 │
 │  • hyperfree_hsi: HyperFree-B (ViT-B CASP) 3D HSI Cube Foundation Specialist    │
 │  • spectral_signature_tool: Continuous λ vs. Reflectance & absorption dips      │
 │  • gdal_rasterio_gis: Covariance RX anomaly detection & GeoJSON vectorization   │
 │  • rs_vqa: Radiometric spectral index & land-cover question answering           │
 │  • rs_ground: Text-guided region isolation & tactical bounding box overlays     │
 │  • rs_caption: Corine Land Cover breakdown & structured scene description       │
 │  • change_ai: Bi-temporal Siamese difference & solar amber change heatmaps      │
 │  • optical_sar: Cross-modal optical spectral + SAR microwave backscatter fusion │
 └──────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                     EVIDENCE SYNTHESIS & REPORT ENGINE                           │
 │  • Downloadable HTML & JSON Mission Intelligence Reports (backend/outputs/)      │
 │  • Dedicated HSI Viewer: λ vs. Reflectance SVG curves, True Color & CIR toggles  │
 └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Six Supported Earth Observation Modalities

| Modality | Specialist Engine | Output Evidence & Visualizations |
|---|---|---|
| **Hyperspectral (HSI)** | `HyperFree-B` (ViT-B Channel-Adaptive) | Continuous spectral signature $(\lambda \text{ vs. } R)$, absorption dips (670nm Chlorophyll, 960/1400nm Water), RX anomaly map, True Color RGB & False-Color CIR composites |
| **Bi-Temporal Change** | `change_ai` (Siamese Neural Encoder) | Surface modification percentages, differential index matrix, and solar-amber change heatmaps |
| **Optical–SAR Fusion** | `optical_sar` (Dual-Encoder Cross-Attention) | Joint multi-spectral reflectance + SAR radar backscatter $(\text{dB})$ with structural feature isolation |
| **Single-Image VQA** | `rs_vqa` (Multimodal Bilinear Fusion) | Natural-language query answers grounded in real radiometric calculations and spectral indices (NDVI, NDWI) |
| **Text-Guided Grounding** | `rs_ground` (Connected Component Spatializer) | Tactical bounding boxes identifying targets matching user text expressions |
| **Scene Captioning** | `rs_caption` (Corine Land Cover Synthesizer) | Comprehensive scene descriptions with quantitative class distribution breakdown |

---

## 3. Local LLM Setup with Ollama

SatQuery AI leverages the local Ollama daemon for natural language reasoning across specialized roles:

| Role | Configured Model | Primary Responsibility | Context |
| :--- | :--- | :--- | :--- |
| **Planner** | `qwen3.5:9b` | Multi-step query decomposition, tool sequencing, synthesis | 8K |
| **Fast Router** | `qwen3.5:4b` | High-speed task classification and parameter parsing | 4K |
| **Lightweight** | `llama3.2` | Fast summaries, schema validation, fallback reasoning | 4K |

```bash
# Pull recommended local models
ollama pull qwen3.5:9b
ollama pull qwen3.5:4b
ollama pull llama3.2
```

*Deterministic Fallback:* If Ollama is offline, SatQuery AI automatically falls back to its deterministic spatial-physics reasoning engine (computing exact NDVI, NDWI, SAR dB backscatter, and absorption dips) with zero hallucinations and zero crashes.

---

## 4. Quickstart Guide

### A. Start the Backend API
In `backend/`:
```powershell
cd backend
python run_backend.py
```
- API live at: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health & Registry Status: `http://127.0.0.1:8000/api/v1/health`

### B. Start the Frontend Command Center
In `frontend/`:
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 5. Automated Verification & Test Suite

Run the regression and integration test suites:
```powershell
# 1. Existing modalities regression test (VQA, Grounding, Captioning, Change, Fusion)
python -m unittest backend/tests/test_agent_pipeline.py

# 2. Hyperspectral, non-remote-sensing rejection, and LangGraph tests
python -m unittest backend/tests/test_hyperspectral_langgraph.py
```

---

## 6. Project Documentation

Comprehensive documentation for all architectural specifications, training suites, and integration guidelines is organized in the [`docs/`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs) directory:
- [`docs/ps.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/ps.md) — Official ISRO Problem Statement 26167
- [`docs/SatQuery_AI_PRD.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/SatQuery_AI_PRD.md) — Product Requirements Document
- [`docs/SatQuery_AI_TRD.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/SatQuery_AI_TRD.md) — Technical Requirements Document
- [`docs/SatQuery_AI_App_Flow.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/SatQuery_AI_App_Flow.md) — Application Workflow & User Journey
- [`docs/SatQuery_AI_UI_UX_Brief.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/SatQuery_AI_UI_UX_Brief.md) — UI/UX Design System Brief
- [`docs/TRINETRA_INTEGRATION.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/TRINETRA_INTEGRATION.md) — TRINETRA 3D Globe Deep-Linking
- [`docs/TRINETRA_Local_Agentic_AI_Migration_Task.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/TRINETRA_Local_Agentic_AI_Migration_Task.md) — Local Agentic AI Architecture
- [`docs/TRINETRA_All_Model_Training_MASTER_TASK.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/TRINETRA_All_Model_Training_MASTER_TASK.md) — Real-Data Local GPU Training Suite
