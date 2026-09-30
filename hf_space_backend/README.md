---
title: TRINETRA Satellite Intelligence Backend
emoji: 🛰️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
short_description: FastAPI backend for multimodal remote-sensing AI and satellite models
---

# 🛰️ TRINETRA — FastAPI Backend Server

**SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)**

FastAPI backend serving 5 specialist PyTorch remote-sensing neural networks:
- **Bi-Temporal Change Detection** (Siamese Differential Net)
- **RS-VQA** (Bilinear Multimodal Question Answering)
- **RS-Grounding** (Visual Target Localization)
- **Optical + SAR Fusion** (Cross-Attention Dual-Encoder)
- **HyperFree-B Hyperspectral Foundation** (AVIRIS 200+ Band Analysis)

Exposes REST APIs on port `7860`.
