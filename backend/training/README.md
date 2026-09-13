# TRINETRA / SatQuery AI — Real-Data Local GPU Training Suite

**SIH 26167 — ISRO — SatQuery AI: Interactive Vision-Language Assistant for Multimodal Remote-Sensing Image Analysis**

This directory contains the production-grade local GPU training pipeline for all remote-sensing specialist models. Every pipeline is engineered to train **exclusively on real, legitimate public datasets and annotations** with zero synthetic data.

---

## Architecture Overview

```text
backend/training/
├── common/                  # Shared evaluation, metrics, seeding, and profiling
│   ├── metrics.py           # mAP, Micro/Macro F1, Top-1/Top-5 Acc, IoU@0.5/0.75, Dice
│   ├── seed.py              # Master deterministic reproducibility seed (seed=42)
│   ├── profiling.py         # Hardware profiles (fast, balanced, quality), AMP, VRAM management
│   ├── checkpoint.py        # Best/last checkpoint manager & live backend deployment
│   ├── reporting.py         # Loss & metric curves (matplotlib) and JSON reporting
│   └── dataset_utils.py     # Real-data verification and split leakage checkers
│
├── 01_bigearthnet/          # BigEarthNet-S2 v2.0 Multi-Label Land Cover (19 CORINE Classes)
├── 02_rsvqa/                # RSVQA (LR/HR) Natural Language Remote Sensing VQA
├── 03_grounding/            # DIOR-RSVG / VRSBench Text-Guided Region Grounding
├── 04_change/               # OSCD / LEVIR-CD Bi-Temporal Change Detection
├── 05_optical_sar/          # SEN1-2 / BigEarthNet-MM Optical + SAR Cross-Modal Fusion
└── README.md                # Master training & execution documentation
```

---

## Hardware Profiles (Target: Laptop GPU)

To guarantee training runs within the **1–2 hour window** on an NVIDIA laptop GPU (RTX 3050/3060/4060/4070/etc.), every training script supports `--profile`:

| Profile | Target Runtime | Batch Size | Image Resolution | Target Subset | Epochs | Patience | Description |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `--profile fast` | **~45–60 min** | 32 | 128x128 | ~5,000 samples | 5 | 2 | Rapid dry-run and hyperparameter check. |
| `--profile balanced` | **~1.5–2 hours** | 32 | 224x224 | ~20,000 samples | 10 | 2 | **Recommended Default**: Optimal balance of real-data exposure and speed. |
| `--profile quality` | **~3–5 hours** | 16 | 224x224 | ~50,000+ samples | 20 | 3 | Extended full-convergence run. |

All profiles use **Automatic Mixed Precision (AMP FP16)** via `torch.cuda.amp.autocast()` and `GradScaler` to minimize VRAM footprint and prevent CUDA Out Of Memory (OOM) errors.

---

## Model 1: BigEarthNet-S2 (Multi-Label Land Cover)

- **Dataset**: BigEarthNet-S2 v2.0 (reBEN, TU Berlin / BIFOLD)
- **Official Source**: [Zenodo Record 10891137](https://zenodo.org/records/10891137) or [BigEarth.net](https://bigearth.net/)
- **Required Files**:
  - `metadata.parquet` (Zenodo direct link: `https://zenodo.org/records/10891137/files/metadata.parquet?download=1`)
  - Sentinel-2 GeoTIFF patch folders (containing `*B02*.tif`, `*B03*.tif`, `*B04*.tif`, `*B08*.tif`)
- **Input / Output**: 4-band RGB-NIR (or 12-band Sentinel-2) $\rightarrow$ 19 CORINE Land Cover classes.

### Step 1: Verify & Generate Manifests
```powershell
python backend/training/01_bigearthnet/prepare.py `
  --data_dir "D:\datasets\BigEarthNet-S2" `
  --metadata "D:\datasets\BigEarthNet-S2\metadata.parquet"
```

### Step 2: Train Model
```powershell
python backend/training/01_bigearthnet/train.py `
  --data_dir "D:\datasets\BigEarthNet-S2" `
  --metadata "D:\datasets\BigEarthNet-S2\metadata.parquet" `
  --profile balanced `
  --export
```
*(The `--export` flag automatically copies the best checkpoint directly to `backend/models/checkpoints/bigearthnet_adapted/model.pt` for live backend inference).*

### Step 3: Evaluate on Held-Out Test Split
```powershell
python backend/training/01_bigearthnet/evaluate.py `
  --checkpoint "backend/training/01_bigearthnet/runs/run_balanced/best_model.pt" `
  --data_dir "D:\datasets\BigEarthNet-S2" `
  --metadata "D:\datasets\BigEarthNet-S2\metadata.parquet"
```

### Step 4: Single Patch Prediction Test
```powershell
python backend/training/01_bigearthnet/predict.py `
  --checkpoint "backend/training/01_bigearthnet/runs/run_balanced/best_model.pt" `
  --image "D:\datasets\BigEarthNet-S2\sample_patch.tif"
```

---

## Model 2: RS-VQA (Remote Sensing Visual Question Answering)

- **Dataset**: RSVQA Low Resolution (LR) or High Resolution (HR)
- **Official Source**: [Sylvain Lobry et al. / Zenodo Record 6344334](https://zenodo.org/record/6344334)
- **Required Files**: `Questions_train.json`, `Answers_train.json`, `Questions_val.json`, `Answers_val.json`, `Questions_test.json`, `Answers_test.json`, and the `Images_LR/` or `Images_HR/` directory.

### Step 1: Verify & Build Vocabulary
```powershell
python backend/training/02_rsvqa/prepare.py `
  --data_dir "D:\datasets\RSVQA_LR"
```

### Step 2: Train Model
```powershell
python backend/training/02_rsvqa/train.py `
  --data_dir "D:\datasets\RSVQA_LR" `
  --profile balanced `
  --export
```

### Step 3: Evaluate on Test Split
```powershell
python backend/training/02_rsvqa/evaluate.py `
  --checkpoint "backend/training/02_rsvqa/runs/run_balanced/best_model.pt" `
  --data_dir "D:\datasets\RSVQA_LR"
```

### Step 4: Query Prediction Test
```powershell
python backend/training/02_rsvqa/predict.py `
  --checkpoint "backend/training/02_rsvqa/runs/run_balanced/best_model.pt" `
  --image "D:\datasets\RSVQA_LR\Images_LR\1024.png" `
  --question "Is there a river in this image?"
```

---

## Model 3: Region Grounding (DIOR-RSVG / VRSBench)

- **Dataset**: DIOR-RSVG (Remote Sensing Visual Grounding Benchmark)
- **Official Source**: [Zhan Yang et al. / IEEE TGRS 2023](https://github.com/ZhanYang-nwpu/RSVG-pytorch)
- **Required Files**: `Annotations/` (XML bounding boxes), `JPEGImages/`, `train.txt`, `val.txt`, `test.txt`.

### Step 1: Verify Manifests
```powershell
python backend/training/03_grounding/prepare.py `
  --data_dir "D:\datasets\DIOR_RSVG"
```

### Step 2: Train Model
```powershell
python backend/training/03_grounding/train.py `
  --data_dir "D:\datasets\DIOR_RSVG" `
  --profile balanced `
  --export
```

### Step 3: Evaluate on Test Split
```powershell
python backend/training/03_grounding/evaluate.py `
  --checkpoint "backend/training/03_grounding/runs/run_balanced/best_model.pt" `
  --data_dir "D:\datasets\DIOR_RSVG"
```

### Step 4: Referring Expression Grounding Test
```powershell
python backend/training/03_grounding/predict.py `
  --checkpoint "backend/training/03_grounding/runs/run_balanced/best_model.pt" `
  --image "D:\datasets\DIOR_RSVG\JPEGImages\00042.jpg" `
  --query "the long horizontal runway near the terminal"
```

---

## Model 4: Bi-Temporal Change Detection (LEVIR-CD / OSCD)

- **Dataset**: LEVIR-CD or OSCD (Onera Satellite Change Detection)
- **Official Source**: [OSCD Dataset](https://rcdaudt.github.io/oscd/) or [LEVIR-CD](https://justchenyang.github.io/LEVIR-CD/)
- **Required Files**: `A/` (pre-change date), `B/` (post-change date), and `label/` (pixel-level change mask).

### Step 1: Verify Temporal Pairs
```powershell
python backend/training/04_change/prepare.py `
  --data_dir "D:\datasets\LEVIR-CD"
```

### Step 2: Train Siamese Differential Model
```powershell
python backend/training/04_change/train.py `
  --data_dir "D:\datasets\LEVIR-CD" `
  --profile balanced `
  --export
```

### Step 3: Evaluate on Test Split
```powershell
python backend/training/04_change/evaluate.py `
  --checkpoint "backend/training/04_change/runs/run_balanced/best_model.pt" `
  --data_dir "D:\datasets\LEVIR-CD"
```

### Step 4: Bi-Temporal Inference Test
```powershell
python backend/training/04_change/predict.py `
  --checkpoint "backend/training/04_change/runs/run_balanced/best_model.pt" `
  --image_t1 "D:\datasets\LEVIR-CD\A\test_001.png" `
  --image_t2 "D:\datasets\LEVIR-CD\B\test_001.png"
```

---

## Model 5: Optical + SAR Fusion (SEN1-2 / BigEarthNet-MM)

- **Dataset**: SEN1-2 (TU Munich) or BigEarthNet-MM
- **Official Source**: [SEN1-2 Dataset / mediaTUM 1437045](https://mediatum.ub.tum.de/1437045)
- **Required Files**: `s2/` (Optical RGB/NIR) and `s1/` (SAR radar VV/VH) co-registered directories.

### Step 1: Verify Co-Registered Pairs
```powershell
python backend/training/05_optical_sar/prepare.py `
  --data_dir "D:\datasets\SEN1-2"
```

### Step 2: Train Cross-Modal Attention Model
```powershell
python backend/training/05_optical_sar/train.py `
  --data_dir "D:\datasets\SEN1-2" `
  --profile balanced `
  --export
```

### Step 3: Evaluate 3-Way Comparative Benchmark
```powershell
python backend/training/05_optical_sar/evaluate.py `
  --checkpoint "backend/training/05_optical_sar/runs/run_balanced/best_model.pt" `
  --data_dir "D:\datasets\SEN1-2"
```
*(Computes Optical-only baseline vs SAR-only baseline vs Fused model, quantifying the exact fusion improvement delta).*

### Step 4: Joint Cross-Modal Inference Test
```powershell
python backend/training/05_optical_sar/predict.py `
  --checkpoint "backend/training/05_optical_sar/runs/run_balanced/best_model.pt" `
  --optical "D:\datasets\SEN1-2\s2\patch_01.png" `
  --sar "D:\datasets\SEN1-2\s1\patch_01.png"
```

---

## Static Quality & Compliance Checklist

- [x] **Zero Synthetic Training Data**: All loaders strictly require real files on disk and raise explicit download errors if missing.
- [x] **No Fake Evaluation**: Metrics computed strictly on isolated held-out test splits.
- [x] **Zero Split Leakage**: Deterministic verification ensures $\text{Train} \cap \text{Val} = \emptyset$ and $\text{Train} \cap \text{Test} = \emptyset$.
- [x] **Mandatory Baseline-First**: All trainers evaluate untrained/prior baselines prior to reporting trained gains.
- [x] **Direct Deployment**: Saved checkpoints match [`backend/models/architectures.py`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/backend/models/architectures.py) and [`backend/models/loader.py`](file:///d:/DEKSTOP_/PROJECT/SIH_2026/TRINETRA/backend/models/loader.py) 1:1.
