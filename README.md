# SatQuery AI (TRINETRA)
### Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis
**SIH 2026 • Problem Statement ID: 26167**  
**Organization:** Indian Space Research Organisation (ISRO)  
**Theme:** Space Technology / Software

---

## 1. System Architecture

SatQuery AI is an agentic, query-driven vision-language platform designed for operational remote sensing. Unlike generic VLMs, SatQuery AI features:
- **Input & Pair Compatibility Validator**: GeoTIFF/TIFF multband parser verifying spatial coverage, modalities, and resolution.
- **Intent & Task Classifier**: Maps natural language queries to remote-sensing tasks (`vqa`, `captioning`, `grounding`, `change_analysis`, `optical_sar_fusion`).
- **Specialist Remote-Sensing Tool Registry**: Modular specialist models for single-image, bi-temporal, and cross-modal workflows.
- **Visual Evidence Engine**: Generates bounding boxes, segmentation masks, Solar Amber change heatmaps, and multimodal composites.
- **Observable Execution Trace**: Auditable step-by-step pipeline telemetry recording selected tools, parameters, and latency.
- **Mission Intelligence Reports**: Downloadable HTML and JSON mission reports.
- **Mission Control Aerospace UI**: Dark Carbon/Obsidian and Tactical Emerald theme designed for satellite ground stations.

---

## 2. Quickstart Guide

### A. Start the Backend API
In the repository root:
```bash
# Ensure virtual environment is activated
python -m uvicorn apps.backend.app:app --reload --port 8000
```
Backend API will be live at `http://127.0.0.1:8000`.  
Swagger docs available at `http://127.0.0.1:8000/docs`.

### B. Start the Frontend Command Center
In `apps/frontend`:
```bash
cd apps/frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 3. Machine Learning Model Training (For You to Run)

All self-contained training scripts and CLI commands are in `training/`. Refer to [`training/README_TRAINING.md`](training/README_TRAINING.md) for full instructions:

1. **BigEarthNet Remote-Sensing Adaptation**:
   ```bash
   python training/train_bigearthnet.py --data_dir ./datasets/bigearthnet --epochs 10 --batch_size 32 --lr 1e-4 --output_dir ./models/checkpoints/bigearthnet_adapted
   ```
2. **RS-VQA Specialist (RSVQA / VRSBench)**:
   ```bash
   python training/train_vqa_captioning.py --dataset rsvqa --data_dir ./datasets/rsvqa --output_dir ./models/checkpoints/rs_vqa_model
   ```
3. **RS-Grounding Specialist (VRSBench Grounding)**:
   ```bash
   python training/train_grounding.py --data_dir ./datasets/vrsbench --output_dir ./models/checkpoints/rs_grounding_model
   ```
4. **Bi-Temporal Change Specialist (CDVQA / LEVIR-CD)**:
   ```bash
   python training/train_change_cdvqa.py --data_dir ./datasets/cdvqa --output_dir ./models/checkpoints/change_specialist_model
   ```
5. **Optical–SAR Cross-Modal Fusion Specialist**:
   ```bash
   python training/train_optical_sar.py --data_dir ./datasets/optical_sar --output_dir ./models/checkpoints/optical_sar_model
   ```

*Note:* SatQuery AI includes dynamic checkpoint loading. When you place trained weights in `models/checkpoints/`, they are automatically mounted. In the meantime, the system runs with a high-fidelity remote-sensing heuristic reasoning engine for instant testing.

---

## 4. Running Verification Tests

Run the full end-to-end integration test suite:
```bash
python tests/test_agent_pipeline.py
```
Tests cover:
- Single-Image VQA
- Single-Image Text-Guided Grounding
- Single-Image Scene Captioning
- Bi-Temporal Change Detection & CDVQA
- Optical–SAR Multimodal Fusion
- Input Validation & Error Handling
