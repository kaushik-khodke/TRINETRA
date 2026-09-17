# TRINETRA Model Inventory & Checkpoint Audit (Stage 1)

## 1. Registered Neural Architectures

The table below lists all model architectures defined in `backend/models/architectures.py` and `backend/qml/models/`:

| Model Identifier | Architecture Class | Modalities / Inputs | Output Dimensions / Schema | Checkpoint Directory | Checkpoint Found on Disk? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `bigearthnet_adapted` | `BigEarthNetAdaptedResNet` | 4-channel multispectral / SAR | 19 classes (CORINE Land Cover) | `checkpoints/bigearthnet_adapted/` | **No** (`.gitkeep` only) |
| `change_specialist_model` | `SiameseChangeDiffNet` | Bi-temporal optical pairs ($T_1, T_2$) | 3 classes (Unchanged, Increased, Decreased) | `checkpoints/change_specialist_model/` | **Yes** (`model.pt`, 2.4 MB) |
| `optical_sar_model` | `OpticalSARCrossAttentionNet` | Optical RGB/NIR + SAR VV/VH | Fused features & joint classification | `checkpoints/optical_sar_model/` | **Yes** (`model.pt`, 4.8 MB) |
| `rs_vqa_model` | `RSVqaFusionNetwork` | Optical RGB + Question Token IDs | Answer vocabulary logits (1000 classes) | `checkpoints/rs_vqa_model/` | **Yes** (`model.pt`, 5.1 MB, `rsvqa_vocab.json`) |
| `rs_grounding_model` | `RSGroundingDetector` | Optical RGB + Text prompt query | Bounding box coordinates $[x_1, y_1, x_2, y_2]$ | `checkpoints/rs_grounding_model/` | **Yes** (`model.pt`, 3.2 MB) |
| `hyperfree_model` | `HyperFreeB` | Hyperspectral data cube ($B$ bands) | 16 land-cover classes | `checkpoints/hyperfree_model/` | **Yes** (`model.pt`, 8.1 MB) |
| `qml_change_vqc` | `QuantumChangeClassifier` | 4 to 8 PCA features from bi-temporal pairs | 3 classes (Unchanged, Increased, Decreased) | `backend/qml/results/qml_change_levir10k/` | **Yes** (`best_model.pt`, 12 KB) |

---

## 2. Checkpoint Validation Policy (Stage 1 Standard)

For any checkpoint to be considered **production-valid**:
1. **File Exists**: A valid `.pt`, `.bin`, or `.safetensors` file is present in the target directory.
2. **SHA-256 Checksum**: The file hash must be computed and recorded upon loading.
3. **Architecture Match**: Weights must load cleanly with `strict=True` or with verified, documented parameter key sets.
4. **Metadata Attached**: Accompanying training metadata (dataset identifier, split name, training timestamp, metric scores) must exist alongside the checkpoint.
5. **No Blind Fallback**: If checkpoint verification fails, the model is marked unmounted and the system reports `fallback_used: True`.

---

## 3. Heuristic / Radiometric Fallback Engines

When neural checkpoints are absent (e.g. `bigearthnet_adapted` currently):
- **Engine Type**: `Heuristic / Algorithmic CV Engine (Fallback)`
- **Mechanism**:
  - Normalized Difference Spectral Indices ($\text{NDVI}$, $\text{NDWI}$, $\text{NDBI}$)
  - Threshold-based optical luminance change masking
  - Microwave SAR double-bounce vs specular attenuation thresholding
- **Scientific Requirement**: Never disguise these heuristics as neural network outputs. Clearly flag them with `fallback_used: true` and `fallback_reason: "Model weights not present on disk"`.
