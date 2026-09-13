# SatQuery AI (TRINETRA)
### 100% Local-First Agentic Vision-Language Assistant for Multimodal Remote Sensing
**SIH 2026 • Problem Statement ID: 26167**  
**Organization:** Indian Space Research Organisation (ISRO)  
**Theme:** Space Technology / Software • **Air-Gapped & Secure**

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
   │  • Planner: qwen3.5:9b        │ │  • satquery_analysis_<id>        │
   │  • Fast Router: qwen3.5:4b    │ │  • Step latency & tokens         │
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
   └─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Local LLM Setup with Ollama

SatQuery AI leverages the local Ollama daemon for inference across specialized roles:

| Role | Configured Model | Primary Responsibility | Context |
| :--- | :--- | :--- | :--- |
| **Planner** | `qwen3.5:9b` | Multi-step query decomposition, tool sequencing, synthesis | 8K |
| **Fast Router** | `qwen3.5:4b` | High-speed task classification and parameter parsing | 4K |
| **Lightweight** | `llama3.2` | Fast summaries, schema validation, fallback reasoning | 4K |

### Setup Steps:
1. Ensure [Ollama](https://ollama.com) is installed and running (`ollama serve` or Windows system service).
2. Pull the required models:
   ```bash
   ollama pull qwen3.5:9b
   ollama pull qwen3.5:4b
   ollama pull llama3.2
   ```
3. Verify connection:
   ```bash
   curl http://localhost:11434/api/tags
   ```

*Note:* If Ollama has not loaded a model yet or is temporarily stopped, SatQuery AI gracefully falls back to its deterministic spatial physics reasoning engine (computing exact NDVI, NDWI, SAR dB, and connected components) with zero hallucinations and zero crashes.

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

### A. Start the Backend API
In `backend/`:
```bash
cd backend
python run_backend.py
```
- API live at: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health & LLM Status: `http://127.0.0.1:8000/api/v1/health`

### B. Start the Frontend Command Center
In `frontend/`:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 5. Verification & Test Suite

Run the full end-to-end integration and local migration test suite:
```bash
python backend/tests/test_local_agent_migration.py
```
Tests systematically verify:
1. **Complete Cloud Purge**: Zero references to Google Gemini keys, imports, or endpoints across codebase.
2. **Local LLM Provider**: Ollama provider and dynamic model registry behavior.
3. **Multi-Step Agent Planner**: Decomposition and tool sequencing with local fallbacks.
4. **Tool Safety & Parameter Validation**: Boundary checks and path traversal protection.
5. **Non-Blocking Telemetry**: Langfuse tracing resilience when server is offline.
6. **4 Core Workflows**: End-to-end execution of Single VQA, Text Grounding, Bi-temporal Change, and Optical-SAR Fusion.

