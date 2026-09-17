# SatQuery AI / TRINETRA — Project Documentation Index

This directory centralizes all architectural, functional, technical, and domain specifications for **SatQuery AI (TRINETRA)** — developed for **Smart India Hackathon (SIH) 2026, Problem Statement 26167, Indian Space Research Organisation (ISRO)**.

---

## Document Index

| Document | Purpose | Key Contents |
|---|---|---|
| [`ps.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/ps.md) | **Official Problem Statement** | SIH 26167 requirements: Vision-Language Assistant for multimodal remote-sensing image analysis, natural language queries, temporal change, fusion. |
| [`SatQuery_AI_PRD.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/SatQuery_AI_PRD.md) | **Product Requirements Document (PRD)** | Mission objectives, user personas (analysts, disaster responders, planners), core functional capabilities, success criteria. |
| [`SatQuery_AI_TRD.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/SatQuery_AI_TRD.md) | **Technical Requirements Document (TRD)** | System architecture, raster processing standards (GeoTIFF, WGS84), API endpoints, multimodal neural network topologies. |
| [`SatQuery_AI_App_Flow.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/SatQuery_AI_App_Flow.md) | **Application Workflow & User Journey** | Complete screen transitions: Landing $\to$ Upload $\to$ Multi-Tier Validation $\to$ Specialist Reasoning $\to$ Evidence Display $\to$ PDF/HTML Report Export. |
| [`SatQuery_AI_UI_UX_Brief.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/SatQuery_AI_UI_UX_Brief.md) | **UI/UX Design System Brief** | Design tokens, color palette (Dark Slate, Cyan-400, Emerald-400, Amber-400), typography, responsive layout standards, interactive evidence viewers. |
| [`SatQuery_AI_Detailed_Requirements.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/SatQuery_AI_Detailed_Requirements.md) | **Detailed Functional Requirements** | Specific capabilities for Single-image VQA, Captioning, Grounding, Bi-temporal Change, Optical+SAR Fusion, and Hyperspectral analysis. |
| [`TRINETRA_INTEGRATION.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/TRINETRA_INTEGRATION.md) | **TRINETRA 3D Globe Integration** | Deep linking and coordinate sharing between SatQuery AI analysis workspace and TRINETRA 3D geospatial visualization globe. |
| [`TRINETRA_Local_Agentic_AI_Migration_Task.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/TRINETRA_Local_Agentic_AI_Migration_Task.md) | **100% Air-Gapped Local Architecture** | Zero cloud dependency, local Ollama runtime, LangGraph explicit StateGraph workflow, allow-listed tool registry, Langfuse tracing. |
| [`TRINETRA_All_Model_Training_MASTER_TASK.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/TRINETRA_All_Model_Training_MASTER_TASK.md) | **Local GPU Model Training Suite** | Real-dataset training pipelines (BigEarthNet-S2, RSVQA, DIOR-RSVG, OSCD, SEN1-2), zero synthetic data rules, AMP FP16, hardware profiles. |
| [`TRINETRA_Dataset_Plan_and_Training_Protocol.md`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/docs/TRINETRA_Dataset_Plan_and_Training_Protocol.md) | **Dataset Acquisition & Training Protocol** | Zero automatic download rule, Tier 1–3 benchmark registry, 10-step manual developer training lifecycle, spatial split leakage rules, VRAM targets. |

---

## Project Structure Overview

```text
TRINETRA/
├── backend/                  # FastAPI 100% Local Python Backend
│   ├── agent/               # LangGraph StateGraph Orchestrator & Tool Registry
│   ├── app/                 # FastAPI routes, schemas, and lifecycle handlers
│   ├── geospatial/          # Rasterio/GDAL, HSI cube reader, spectral physics engine
│   ├── llm/                 # Local Ollama planner, prompt templates, model registry
│   ├── models/              # PyTorch specialist checkpoints (VQA, Grounding, Change, HyperFree)
│   ├── observability/       # Langfuse tracing & execution telemetry
│   ├── outputs/             # Generated mission intelligence reports (HTML & JSON)
│   ├── sample_data/         # Calibrated GeoTIFF & HSI benchmark samples
│   ├── services/            # Specialist domain perception services
│   ├── tests/               # Automated unit & regression test suites
│   └── training/            # Standalone GPU training pipelines
│
├── frontend/                 # Next.js 16 (Turbopack) Interactive Analysis UI
│   ├── app/                 # App Router pages (Workspace, History, Evaluation)
│   ├── components/          # UI components (EvidenceViewer, HsiViewer)
│   └── lib/                 # Type definitions, API client, multilingual i18n
│
├── docs/                     # Consolidated Project Documentation (You are here)
│
└── 06_train_hyperspectral_colab.py # Standalone Colab training script for HyperFree-B
```
