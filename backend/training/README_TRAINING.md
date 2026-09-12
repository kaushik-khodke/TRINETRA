# SatQuery AI — Machine Learning Model Training Manual
**SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)**

This manual contains the exact CLI commands, dataset links, recommended hyperparameters, and checkpoint locations for training each of the specialist remote-sensing AI models.

---

## Overview of Model Checkpoints

When your training completes, save or copy your `.pt` or `.safetensors` files into the designated subdirectory inside `models/checkpoints/`:

| Specialist Model | Target Checkpoint Subdirectory | Training Script |
| :--- | :--- | :--- |
| **BigEarthNet Adaptation** | `models/checkpoints/bigearthnet_adapted/` | `training/train_bigearthnet.py` |
| **RS-VQA Specialist** | `models/checkpoints/rs_vqa_model/` | `training/train_vqa_captioning.py` |
| **RS-Grounding Specialist** | `models/checkpoints/rs_grounding_model/` | `training/train_grounding.py` |
| **Bi-Temporal Change Specialist** | `models/checkpoints/change_specialist_model/` | `training/train_change_cdvqa.py` |
| **Optical–SAR Fusion Specialist** | `models/checkpoints/optical_sar_model/` | `training/train_optical_sar.py` |

> **Note**: The backend automatically detects when checkpoints exist in `models/checkpoints/`. While models are training, SatQuery AI runs in high-fidelity Remote-Sensing heuristic mode (using NDVI, NDWI, SAR radar backscatter, and differential change matrices) so the full application is immediately testable.

---

## 1. Remote-Sensing Adaptation (BigEarthNet)
*Mandatory requirement:* Fine-tunes a vision encoder on Sentinel-2 multispectral (4 to 12 channels) or Sentinel-1 SAR imagery.

### Dataset Source
- [BigEarthNet Official Archive](https://bigearth.net/)
- Benchmark text index: `BigEarthNet.txt`

### Training Command
```bash
python training/train_bigearthnet.py \
  --data_dir ./datasets/bigearthnet \
  --epochs 10 \
  --batch_size 32 \
  --channels 4 \
  --lr 1e-4 \
  --output_dir ./models/checkpoints/bigearthnet_adapted
```

---

## 2. Remote-Sensing VQA & Captioning (RSVQA / VRSBench)
*Mandatory baseline:* Answers natural language questions on single optical, multispectral, or SAR imagery.

### Dataset Sources
- RSVQA: [Remote Sensing Visual Question Answering (RSVQA-LR / RSVQA-HR)](https://rsvqa.sylvainlobry.com/)
- VRSBench: [Vision-Language Remote Sensing Benchmark](https://github.com/Chen-Z-Y/VRSBench)

### Training Command
```bash
python training/train_vqa_captioning.py \
  --dataset rsvqa \
  --data_dir ./datasets/rsvqa \
  --epochs 8 \
  --batch_size 16 \
  --lr 2e-4 \
  --output_dir ./models/checkpoints/rs_vqa_model
```

---

## 3. Text-Guided Region Grounding (VRSBench Grounding)
*Additional single-image capability:* Localizes referenced spatial features (e.g. airport runway, water body, built-up clusters) into normalized bounding boxes `[ymin, xmin, ymax, xmax]`.

### Training Command
```bash
python training/train_grounding.py \
  --data_dir ./datasets/vrsbench \
  --epochs 10 \
  --batch_size 16 \
  --lr 3e-4 \
  --output_dir ./models/checkpoints/rs_grounding_model
```

---

## 4. Bi-Temporal Change Understanding (CDVQA / LEVIR-CD)
*Multi-image change requirement:* Joint reasoning over two temporal observations of the same geographic area to answer change questions and generate change maps.

### Dataset Sources
- CDVQA: Change Detection Visual Question Answering
- LEVIR-CD / WHU-CD: High-resolution building change detection

### Training Command
```bash
python training/train_change_cdvqa.py \
  --data_dir ./datasets/cdvqa \
  --epochs 8 \
  --batch_size 16 \
  --lr 2e-4 \
  --output_dir ./models/checkpoints/change_specialist_model
```

---

## 5. Optical–SAR Cross-Modal Fusion
*Cross-modal requirement:* Jointly reasons over co-registered optical/multispectral + SAR imagery, combining optical spectral reflectance with SAR microwave radar structural penetration.

### Dataset Sources
- SpaceNet 6: Multi-sensor Optical and SAR imagery over Rotterdam
- SEN1-2: Co-registered Sentinel-1 and Sentinel-2 dataset

### Training Command
```bash
python training/train_optical_sar.py \
  --data_dir ./datasets/optical_sar \
  --epochs 8 \
  --batch_size 16 \
  --lr 2e-4 \
  --output_dir ./models/checkpoints/optical_sar_model
```

---

## Google Colab / Remote GPU Quickstart
If you wish to train on a free Google Colab T4 GPU:
1. Zip the `training/` folder and upload it to your Colab workspace.
2. Mount Google Drive for persistent checkpoint storage.
3. Run any of the commands above directly in a Colab notebook cell by prefixing with `!`.
4. Download the resulting `best_model.pt` file and place it in the corresponding `models/checkpoints/<subfolder>` on your local machine!
