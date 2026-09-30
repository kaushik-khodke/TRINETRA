---
title: TRINETRA - Multimodal Satellite Intelligence Workstation
emoji: 🛰️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Multi-modal AI for satellite VQA, change detection, SAR fusion & HSI
---

# 🛰️ TRINETRA — Multimodal Satellite Intelligence Workstation

**SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)**

An interactive AI workstation for multimodal Earth observation, powered by 5 custom PyTorch neural networks trained on genuine scientific remote-sensing benchmarks.

## 🚀 Interactive Specialist Suites

1. **Bi-Temporal Satellite Change Detection**: Siamese Differential Feature Network trained on LEVIR-CD for pre/post disaster, urban expansion, and deforestration tracking.
2. **Remote-Sensing Visual Question Answering (RS-VQA)**: Dual-stream multimodal fusion network predicting answers from high-resolution and Sentinel-2 satellite imagery.
3. **Text-Guided Visual Grounding**: Cross-modal referring expression detector localizing specific geospatial features from natural language queries.
4. **Optical + SAR Cross-Modal Fusion**: Dual-encoder cross-attention network fusing optical multispectral (Sentinel-2) and synthetic aperture radar (Sentinel-1 VV/VH).
5. **HyperFree-B Hyperspectral Foundation Specialist**: Spectral-spatial representation analysis for 200+ channel AVIRIS/ROSIS cubes, continuum removal absorption curves, and Reed-Xiaoli (RX) anomaly detection.

## 🔬 Benchmark Provenance
- **RS-VQA**: Sylvain Lobry et al. (Zenodo 6344334)
- **DIOR-RSVG**: NWPU iOPEN Visual Grounding Benchmark
- **LEVIR-CD**: Chen & Shi (Cropped 256 Bitemporal Change)
- **SEN1-2**: TU Munich mediaTUM 1437045
- **AVIRIS / Indian Pines**: Purdue University LARS
