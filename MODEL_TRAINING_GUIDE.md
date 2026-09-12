# SatQuery AI — Machine Learning Model Training & Google Colab Guide
**SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)**

This guide explains **what models to train**, **what datasets to use**, **how to train them on Google Colab with GPU**, and **the exact filename and destination path** where you paste the trained weights into this project.

---

## Model Checkpoint Quick Reference Table

When your training finishes in Google Colab, download the resulting `model.pt` file and paste it into the exact folder specified below:

| # | Specialist Model | Colab Script in `backend/colab_training/` | Official Dataset | Exact Path to Paste Trained Weights in Project |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **BigEarthNet Adaptation** | `01_train_bigearthnet_colab.py` | [BigEarthNet](https://bigearth.net/) (Sentinel-2 & Sentinel-1) | `backend/models/checkpoints/bigearthnet_adapted/model.pt` |
| **2** | **RS-VQA Specialist** | `02_train_vqa_captioning_colab.py` | [RSVQA](https://rsvqa.sylvainlobry.com/) / [VRSBench](https://github.com/Chen-Z-Y/VRSBench) | `backend/models/checkpoints/rs_vqa_model/model.pt` |
| **3** | **RS-Grounding Specialist** | `03_train_grounding_colab.py` | [VRSBench Grounding](https://github.com/Chen-Z-Y/VRSBench) | `backend/models/checkpoints/rs_grounding_model/model.pt` |
| **4** | **Bi-Temporal Change Specialist** | `04_train_change_cdvqa_colab.py` | [CDVQA](https://github.com/Chen-Z-Y/CDVQA) / [LEVIR-CD](https://justchenhao.github.io/LEVIR/) | `backend/models/checkpoints/change_specialist_model/model.pt` |
| **5** | **Optical–SAR Fusion Specialist** | `05_train_optical_sar_colab.py` | [SpaceNet 6](https://spacenet.ai/sn6-challenge/) / [SEN1-2](https://mediatum.ub.tum.de/1436651) | `backend/models/checkpoints/optical_sar_model/model.pt` |

> **Automated Detection**: As soon as you paste `model.pt` into any of these folders, SatQuery AI immediately switches from the algorithmic heuristic engine to your trained PyTorch neural weights!

---

## General Google Colab Workflow

All 5 training scripts are located in `backend/colab_training/`. They are 100% self-contained, automatically detect Colab's GPU (`cuda`), and include data preparation and model saving.

### Steps to Train Any Model on Google Colab:
1. Open [Google Colab](https://colab.research.google.com/).
2. Enable GPU: Click **Runtime** → **Change runtime type** → Select **T4 GPU** → Click **Save**.
3. In the left sidebar of Colab, click the **Files** icon (folder icon) and click **Upload to session storage**.
4. Upload the corresponding script from your local `backend/colab_training/` folder.
5. In a Colab code cell, execute the script with the commands listed below.
6. When training finishes, refresh Colab's Files panel, find the generated `model.pt` in the output folder, right-click, and select **Download**.
7. Paste the downloaded `model.pt` into your local project at the destination path shown in the table above.

---

## 1. Model 1: BigEarthNet Remote-Sensing Adaptation
- **Purpose**: Adapts the visual representation backbone to multispectral (Sentinel-2) and SAR (Sentinel-1) remote-sensing data to predict Corine land-cover classes.
- **Dataset**: [BigEarthNet](https://bigearth.net/) (or `BigEarthNet.txt` benchmark index).
- **Colab Script**: `backend/colab_training/01_train_bigearthnet_colab.py`

### Run Command in Colab:
```bash
!python 01_train_bigearthnet_colab.py --epochs 10 --batch_size 32 --channels 4 --output_dir ./output_bigearthnet
```
- **Output File**: `output_bigearthnet/model.pt`
- **Destination in Project**:
  ```text
  TRINETRA/backend/models/checkpoints/bigearthnet_adapted/model.pt
  ```

---

## 2. Model 2: Remote-Sensing VQA (RS-VQA) Specialist
- **Purpose**: Answers natural-language questions about remote-sensing image features (water bodies, land use, infrastructure, vegetation).
- **Dataset**: [RSVQA (High Resolution & Low Resolution)](https://rsvqa.sylvainlobry.com/) or [VRSBench VQA subset](https://github.com/Chen-Z-Y/VRSBench).
- **Colab Script**: `backend/colab_training/02_train_vqa_captioning_colab.py`

### Run Command in Colab:
```bash
!python 02_train_vqa_captioning_colab.py --epochs 8 --batch_size 16 --output_dir ./output_vqa
```
- **Output File**: `output_vqa/model.pt`
- **Destination in Project**:
  ```text
  TRINETRA/backend/models/checkpoints/rs_vqa_model/model.pt
  ```

---

## 3. Model 3: Text-Guided Region Grounding Specialist
- **Purpose**: Localizes objects and areas referenced in queries (e.g., *"highlight the runway"*, *"find the water body"*) into normalized bounding boxes `[ymin, xmin, ymax, xmax]`.
- **Dataset**: [VRSBench Grounding split](https://github.com/Chen-Z-Y/VRSBench) or DIOR-RSVG.
- **Colab Script**: `backend/colab_training/03_train_grounding_colab.py`

### Run Command in Colab:
```bash
!python 03_train_grounding_colab.py --epochs 10 --batch_size 16 --output_dir ./output_grounding
```
- **Output File**: `output_grounding/model.pt`
- **Destination in Project**:
  ```text
  TRINETRA/backend/models/checkpoints/rs_grounding_model/model.pt
  ```

---

## 4. Model 4: Bi-Temporal Change & CDVQA Specialist
- **Purpose**: Jointly analyzes two temporal observations (T1 baseline vs T2 monitoring) to describe changes, answer change questions, and highlight modified regions.
- **Dataset**: [CDVQA](https://github.com/Chen-Z-Y/CDVQA) or [LEVIR-CD](https://justchenhao.github.io/LEVIR/).
- **Colab Script**: `backend/colab_training/04_train_change_cdvqa_colab.py`

### Run Command in Colab:
```bash
!python 04_train_change_cdvqa_colab.py --epochs 8 --batch_size 16 --output_dir ./output_change
```
- **Output File**: `output_change/model.pt`
- **Destination in Project**:
  ```text
  TRINETRA/backend/models/checkpoints/change_specialist_model/model.pt
  ```

---

## 5. Model 5: Optical–SAR Cross-Modal Fusion Specialist
- **Purpose**: Cross-attention network fusing Optical spectral channels (RGB/NIR) with SAR microwave radar backscatter (VV/VH) to resolve structures through clouds and shadows.
- **Dataset**: [SpaceNet 6 Multi-Sensor](https://spacenet.ai/sn6-challenge/) or [SEN1-2](https://mediatum.ub.tum.de/1436651).
- **Colab Script**: `backend/colab_training/05_train_optical_sar_colab.py`

### Run Command in Colab:
```bash
!python 05_train_optical_sar_colab.py --epochs 8 --batch_size 16 --output_dir ./output_optical_sar
```
- **Output File**: `output_optical_sar/model.pt`
- **Destination in Project**:
  ```text
  TRINETRA/backend/models/checkpoints/optical_sar_model/model.pt
  ```

---

## How to Verify Your Trained Models in SatQuery AI

Once you paste any `model.pt` into its respective checkpoint folder:
1. Start or refresh the backend:
   ```bash
   python -m uvicorn backend.app.main:app --reload --port 8000
   ```
2. Open `http://localhost:8000/api/v1/registry` in your browser.
3. You will see `"engine": "PyTorch Neural Checkpoint"` and `"checkpoint_file": "model.pt"` listed for that tool!
4. The web dashboard will now use your trained neural network forward passes for all inferences!
