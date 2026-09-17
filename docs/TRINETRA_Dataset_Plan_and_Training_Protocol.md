# TRINETRA — Dataset Acquisition Plan & Manual Training Protocol

**SIH 26167 — ISRO — SatQuery AI: Interactive Vision-Language Assistant for Multimodal Remote-Sensing Image Analysis**  
**Repository Document | Version: 2.0 | Status: Active & Enforced**

---

## 1. Executive Summary

This document establishes the official dataset acquisition policy, dataset registry schema, and manual training protocol for all remote-sensing specialist perception models in TRINETRA. 

The primary objective is **scientifically defensible, reproducible, and leak-free machine learning performance** across multimodal Earth observation tasks (Optical, SAR, Hyperspectral, VQA, Grounding, and Temporal Change Detection).

---

## 2. Non-Negotiable Scientific Principles

Every experiment, dataset loader, training script, and evaluation routine in TRINETRA strictly adheres to the following principles:

1. **Zero Automatic Downloads (Principle 15)**: The IDE and codebase must never silently or automatically download datasets from the internet. All datasets are obtained manually by the developer from official providers with verified licensing and integrity.
2. **Zero Synthetic Training Data**: No artificial noise (`torch.randn`), synthetic images, or fake labels may ever be substituted for genuine Earth observation data. If a dataset is absent, the system halts with an explicit configuration guide.
3. **Zero Fake Evaluation & No Test-Set Tuning**: All metrics are evaluated strictly on held-out test splits. Test data is never used for hyperparameter tuning, checkpoint selection, or threshold calibration.
4. **Spatial / Scene-Level Independence**: Random patch splitting is prohibited for spatially autocorrelated imagery. Splitting must strictly occur at the scene, tile, or geographic region level to eliminate data leakage ($\text{Train} \cap \text{Val} = \emptyset, \text{Train} \cap \text{Test} = \emptyset$).
5. **Mandatory Baseline-First Evaluation**: Every trained model must be evaluated against a simple, untrained, or pre-existing baseline to establish proven empirical gain.
6. **Confidence Calibration**: A raw confidence score is considered meaningless until calibrated against empirical reliability.
7. **Complete Provenance & Reproducibility**: Every stored checkpoint must record its exact git commit, dataset manifest hash, random seed (`seed=42`), hyperparameters, and execution environment.
8. **Visible Failures**: Systematic failure modes, corner cases, and out-of-domain degradations must be documented and exposed rather than concealed.

---

## 3. Dataset Priority Strategy & Benchmark Registry

Remote sensing spans diverse sensors, spatial resolutions, spectral bands, and geographic terrains. No single benchmark can validate a general multimodal system. TRINETRA organizes benchmarks into three distinct priority tiers:

### Tier 1 — Core Foundation Benchmarks (Must Do)

| Benchmark | Sensor / Modalities | Target Task | Primary Split Policy | Official Provider |
| :--- | :--- | :--- | :--- | :--- |
| **LEVIR-CD** | High-Res Bitemporal Optical (0.5m) | Binary Building Change Detection | Official Train / Val / Test scenes | [LEVIR-CD Official](https://justchenyang.github.io/LEVIR-CD/) |
| **WHU-CD** | Aerial Bitemporal Optical (0.2m) | Independent Building Change Validation | Spatial scene split | [WHU Building Dataset](http://gpcv.whu.edu.cn/data/building_dataset.html) |
| **Indian Pines** | AVIRIS Hyperspectral (220 bands, 0.4–2.5µm) | 16-Class Agricultural Material Mapping | Spatially disjoint sub-block extraction | [Purdue LARS / IEEE GIC](https://purr.purdue.edu/publications) |
| **Salinas** | AVIRIS Hyperspectral (224 bands, 3.7m) | 16-Class Crop & Vegetation Classification | Spatially disjoint patch split | [IEEE Computational Intelligence Group](http://www.ehu.eus/ccwintco/index.php/Hyperspectral_Remote_Sensing_Scenes) |
| **Pavia University** | ROSIS Hyperspectral (103 bands, 1.3m) | 9-Class Urban Material Mapping | Region-wise non-overlapping split | [University of Pavia / GIC](http://www.ehu.eus/ccwintco/index.php/Hyperspectral_Remote_Sensing_Scenes) |
| **SEN12MS** | Sentinel-1 SAR (VV/VH) + Sentinel-2 MSI | Optical–SAR Multimodal Fusion & Land Cover | Geographic non-overlapping tiles across 4 seasons | [TU Munich / mediaTUM](https://mediatum.ub.tum.de/1474000) |

### Tier 2 — Cross-Domain & Multimodal Extensions (Strongly Recommended)

| Benchmark | Sensor / Modalities | Target Task | Primary Split Policy | Official Provider |
| :--- | :--- | :--- | :--- | :--- |
| **SECOND** | Aerial Bitemporal Stereo Optical | Semantic Change Detection (6 land-cover categories) | Scene-level geographic split | [SECOND Benchmark](http://www.captain-whu.com/project/SCD/) |
| **BigEarthNet-S2 v2.0** | Sentinel-2 L2A (12 spectral bands) | 19-Class CORINE Multi-Label Classification | Official reBEN stratified split | [reBEN / BIFOLD / Zenodo 10891137](https://zenodo.org/records/10891137) |
| **RSVQA (LR & HR)** | Sentinel-2 (LR) / Aerial (HR) + Text QA | Remote Sensing Visual Question Answering | Official train/val/test split | [Sylvain Lobry et al. / Zenodo 6344334](https://zenodo.org/record/6344334) |
| **DIOR-RSVG** | High-Res Optical (0.5–1m) + Natural Language | Text-Guided Bounding Box Grounding | Official train/val/test split | [Zhan Yang et al. / NWPU](https://github.com/ZhanYang-nwpu/RSVG-pytorch) |

### Tier 3 — India-Specific Operational Validation

| Source | Sensor / Modalities | Target Task | Usage Policy | Provider |
| :--- | :--- | :--- | :--- | :--- |
| **ISRO Bhuvan / NRSC** | Resourcesat LISS-3/4, Cartosat, RISAT-1A SAR | Subcontinental Land-Use, Disaster & Flood Mapping | Verification with explicit reference labels only | [ISRO / NRSC Bhuvan Portal](https://bhuvan.nrsc.gov.in/) |

---

## 4. Dataset Registry Schema

For every dataset ingested into TRINETRA, a standardized entry must be documented and stored in the provenance manifest (`manifest.json`):

```json
{
  "canonical_name": "LEVIR-CD",
  "provider": "Beihang University (LEVIR Lab)",
  "official_url": "https://justchenyang.github.io/LEVIR-CD/",
  "citation": "Chen, H., & Shi, Z. (2020). A spatial-temporal attention-based method and a new dataset for remote sensing image change detection. Remote Sensing, 12(10), 1662.",
  "license": "Academic / Non-Commercial Research Use",
  "version": "1.0",
  "local_path": "D:/datasets/LEVIR-CD",
  "manifest_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "task": "binary_change_detection",
  "modalities": ["optical_bitemporal"],
  "sensor": "Google Earth high-resolution optical",
  "spatial_resolution_meters": 0.5,
  "split_policy": "official_scene_split",
  "label_classes": ["unchanged", "changed_building"],
  "preprocessing_requirements": "non-overlapping 256x256 tiles, min-max normalize [0, 1]",
  "allowed_usage": "research_and_evaluation"
}
```

---

## 5. Developer Manual Training Protocol (10-Step Workflow)

The developer maintains complete manual oversight over dataset downloading, validation, training execution, and checkpoint freezing.

```text
 ┌───────────────────────────────────────────────────────────────────┐
 │               DEVELOPER MANUAL TRAINING LIFECYCLE                 │
 └───────────────────────────────────────────────────────────────────┘
                                   │
 1. Manual Dataset Acquisition from Official Source (No auto-downloads)
                                   │
                                   ▼
 2. Run Pre-Flight Validation (`python prepare.py --data_dir ...`)
                                   │
                                   ▼
 3. Inspect Validation Report & Freeze Deterministic Split Manifest
                                   │
                                   ▼
 4. Execute Baseline Evaluation (Untrained / Heuristic Benchmark)
                                   │
                                   ▼
 5. Launch Training Script (`python train.py --profile balanced ...`)
                                   │
                                   ▼
 6. Monitor Loss Curves, AMP Stability, & Validation Convergence
                                   │
                                   ▼
 7. Select Best Checkpoint Using Validation Metrics Only (Early Stopping)
                                   │
                                   ▼
 8. Freeze Checkpoint Artifact (`model.pt`) & Generate SHA-256 Hash
                                   │
                                   ▼
 9. Run Final Evaluation on Held-Out Test Split (`python evaluate.py ...`)
                                   │
                                   ▼
 10. Generate Complete Provenance Package (Metrics, CIs, Confusion Matrix, Failure Cases)
```

### Detailed Step Guide

1. **Step 1 — Manual Acquisition**: Obtain files directly from official repositories (Zenodo, University portals, Bhuvan). Verify archive checksums and place into configured local directory (e.g., `D:\datasets\<benchmark>`).
2. **Step 2 — Pre-Flight Validation**: Run the specialist's `prepare.py` (or `validate_dataset.py`). The script verifies directory structure, required files, image dimensions, band counts, and nodata masks.
3. **Step 3 — Split Manifest Freezing**: Generate `train.json`, `val.json`, and `test.json`. Ensure zero sample overlap across splits ($\text{Train} \cap \text{Val} = \emptyset$).
4. **Step 4 — Baseline Recording**: Compute baseline metrics before training. For change detection: raw image difference baseline; for fusion: optical-only and SAR-only baselines; for classification: random/prior frequency baseline.
5. **Step 5 — Manual Training Launch**: Run the training command using the appropriate hardware profile (`--profile fast`, `--profile balanced`, or `--profile quality`).
6. **Step 6 — Curve & Overfitting Inspection**: Examine training loss vs. validation loss. Early stopping triggers automatically if validation loss fails to improve for $N$ consecutive epochs.
7. **Step 7 — Validation-Only Selection**: The best checkpoint (`best_model.pt`) is chosen purely based on peak validation score (e.g., Validation F1, Validation mAP, or Validation IoU). Test data is strictly untouched.
8. **Step 8 — Checkpoint Freezing**: Export checkpoint to `backend/models/checkpoints/<specialist>/model.pt`.
9. **Step 9 — Final Test Run**: Execute `evaluate.py` against the held-out test split. Compute primary metrics: mAP, Macro-F1, IoU@0.5, and Dice score.
10. **Step 10 — Provenance Documentation**: Store evaluation metrics, test loss, confusion matrices, and representative failure cases into `runs/<run_id>/metrics.json`.

---

## 6. Hardware Target & VRAM Constraints

All specialist training scripts are architecturally targeted for a **single local GPU with ~8–12 GB usable VRAM** (e.g., NVIDIA RTX 3060/4060/4070 or laptop GPU):

| Profile Flag | Target Clock Time | Batch Size | Spatial Resolution | Subset Limit | Epochs | Target Use Case |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `--profile fast` | ~30–45 min | 32 | 128x128 | ~5,000 samples | 5 | Syntax check, pipeline smoke test, rapid sanity check |
| `--profile balanced` | ~1.5–2 hours | 32 | 224x224 | ~20,000 samples | 10 | **Standard Production Default**: High real-data exposure |
| `--profile quality` | ~3–5 hours | 16 | 224x224 | ~50,000+ samples | 20 | Full convergence run for final benchmark reporting |

### VRAM Mitigation Protocols (When Models Exceed Memory)

If CUDA Out Of Memory (OOM) occurs, follow this exact sequence:
1. Enable Automatic Mixed Precision (`--profile balanced` uses AMP FP16 by default).
2. Reduce batch size (e.g., $32 \to 16 \to 8$).
3. Increase gradient accumulation steps (e.g., `--accum_steps 2` or `4`) to maintain the effective batch size.
4. Reduce spatial tile crop size (e.g., $256 \times 256 \to 224 \times 224$).
5. Enable PyTorch activation checkpointing (`torch.utils.checkpoint`).
6. *Never reduce scientific rigor or sample validity merely to fit GPU memory.*

---

## 7. Execution Commands Across All 6 Specialist Modules

### Module 01: BigEarthNet-S2 (Multi-Label Land Cover)
```powershell
# 1. Verify dataset structure and metadata
python backend/training/01_bigearthnet/prepare.py --data_dir "D:\datasets\BigEarthNet-S2" --metadata "D:\datasets\BigEarthNet-S2\metadata.parquet"

# 2. Train with balanced profile and export best checkpoint
python backend/training/01_bigearthnet/train.py --data_dir "D:\datasets\BigEarthNet-S2" --metadata "D:\datasets\BigEarthNet-S2\metadata.parquet" --profile balanced --export

# 3. Evaluate against held-out test split
python backend/training/01_bigearthnet/evaluate.py --checkpoint "backend/training/01_bigearthnet/runs/run_balanced/best_model.pt" --data_dir "D:\datasets\BigEarthNet-S2" --metadata "D:\datasets\BigEarthNet-S2\metadata.parquet"
```

### Module 02: RSVQA (Remote Sensing Visual Question Answering)
```powershell
# 1. Build question/answer vocabulary and verify image paths
python backend/training/02_rsvqa/prepare.py --data_dir "D:\datasets\RSVQA_LR"

# 2. Train multimodal bilinear fusion model
python backend/training/02_rsvqa/train.py --data_dir "D:\datasets\RSVQA_LR" --profile balanced --export

# 3. Evaluate answer accuracy across question categories
python backend/training/02_rsvqa/evaluate.py --checkpoint "backend/training/02_rsvqa/runs/run_balanced/best_model.pt" --data_dir "D:\datasets\RSVQA_LR"
```

### Module 03: DIOR-RSVG (Referring Expression Grounding)
```powershell
# 1. Parse XML bounding box annotations and build spatial splits
python backend/training/03_grounding/prepare.py --data_dir "D:\datasets\DIOR_RSVG"

# 2. Train visual-linguistic grounding encoder
python backend/training/03_grounding/train.py --data_dir "D:\datasets\DIOR_RSVG" --profile balanced --export

# 3. Evaluate IoU@0.5 and IoU@0.75 on test set
python backend/training/03_grounding/evaluate.py --checkpoint "backend/training/03_grounding/runs/run_balanced/best_model.pt" --data_dir "D:\datasets\DIOR_RSVG"
```

### Module 04: LEVIR-CD (Bi-Temporal Change Detection)
```powershell
# 1. Verify temporal image pairs (Time 1, Time 2, and binary label masks)
python backend/training/04_change/prepare.py --data_dir "D:\datasets\LEVIR-CD"

# 2. Train Siamese differential change network
python backend/training/04_change/train.py --data_dir "D:\datasets\LEVIR-CD" --profile balanced --export

# 3. Evaluate change IoU and F1-score against baseline
python backend/training/04_change/evaluate.py --checkpoint "backend/training/04_change/runs/run_balanced/best_model.pt" --data_dir "D:\datasets\LEVIR-CD"
```

### Module 05: SEN12MS / SEN1-2 (Optical + SAR Cross-Modal Fusion)
```powershell
# 1. Verify co-registered Sentinel-1 (SAR) and Sentinel-2 (Optical) pairs
python backend/training/05_optical_sar/prepare.py --data_dir "D:\datasets\SEN1-2"

# 2. Train cross-attention fusion network
python backend/training/05_optical_sar/train.py --data_dir "D:\datasets\SEN1-2" --profile balanced --export

# 3. Run 3-way comparative benchmark (Optical-only vs SAR-only vs Fused)
python backend/training/05_optical_sar/evaluate.py --checkpoint "backend/training/05_optical_sar/runs/run_balanced/best_model.pt" --data_dir "D:\datasets\SEN1-2"
```

### Module 06: Hyperspectral Specialist (Indian Pines / Pavia / Salinas)
```powershell
# 1. Validate hyperspectral cube geometry, band count, and spatial split integrity
python backend/training/06_hyperspectral/validate_dataset.py --dataset indian_pines --data_dir "D:\datasets\hyperspectral"

# 2. Run local or Google Colab fine-tuning for HyperFree-B
python backend/training/06_hyperspectral/train.py --dataset indian_pines --data_dir "D:\datasets\hyperspectral" --epochs 10 --profile balanced

# 3. Evaluate spectral classification accuracy & continuum removal dips
python backend/training/06_hyperspectral/evaluate.py --dataset indian_pines --data_dir "D:\datasets\hyperspectral" --checkpoint "backend/models/checkpoints/hyperfree_model/model.pt"

# 4. Generate failure case analysis and confidence calibration curve
python backend/training/06_hyperspectral/failure_analysis.py --dataset indian_pines --data_dir "D:\datasets\hyperspectral"
```

---

## 8. Summary of Non-Negotiable Prohibitions

| Prohibited Action | Required Standard |
| :--- | :--- |
| Automated background dataset downloading | Developer manual acquisition with verified license |
| Using `torch.randn()` for training / test data | Real GeoTIFF / ENVI raster loading only |
| Random patch splitting on continuous imagery | Scene-level / spatial tile disjoint splitting |
| Test-set checkpoint selection | Validation loss / Validation metric selection only |
| Calling model agreement "ground truth" | Verification against verified real reference labels |
| Silent fallback to synthetic outputs | Fail fast with explicit error and remediation instructions |
| Unreproducible experimental results | Fixed master seed (`seed=42`) and configuration manifests |
