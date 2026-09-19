# TRINETRA / SatQuery AI — MASTER TRAINING TASK

## Objective

Upgrade the existing TRINETRA / SatQuery AI repository so that **all remote-sensing specialist models can be trained and evaluated locally on my laptop using only REAL, PUBLIC, LEGITIMATE datasets and labels**.

The project is being developed for:

> **SIH 26167 — ISRO — SatQuery AI: Interactive Vision-Language Assistant for Multimodal Remote-Sensing Image Analysis**

I have limited time. Therefore:

- Do **not** fine-tune large general-purpose LLMs.
- Focus on the specialist remote-sensing models.
- Each training job should target approximately **1–2 hours maximum** on the available laptop GPU where realistically possible.
- Use pretrained lightweight backbones where this gives significantly better results per unit of training time.
- Use sufficiently large REAL subsets to make the trained models useful.
- Every training script must perform proper evaluation.
- Every training run must save the trained checkpoint and evaluation results.
- The IDE must **NOT run training files or start long-running jobs**.
- The IDE must only modify code, verify syntax/imports where safe, and then give me the exact commands to run myself.
- The final solution must contain **ZERO synthetic training data**.

---

# 1. HARD RULE — ABSOLUTELY NO SYNTHETIC DATA

This is NON-NEGOTIABLE.

Do NOT use:

```text
torch.randn()
torch.rand()
torch.randint()
randomly generated images
random labels
fake bounding boxes
fake VQA questions
fake answers
fake change labels
fake optical/SAR pairs
```

Do NOT create synthetic data to fill missing samples.

Do NOT create placeholder datasets and call them training data.

Do NOT train on artificial tensors.

Do NOT generate fake labels.

Do NOT silently fall back to synthetic data when a dataset is unavailable.

If a required dataset is missing:

> STOP and print a clear dataset installation/download instruction.

The model must either train on genuine dataset samples or not train.

---

# 2. SECOND HARD RULE — NO FAKE EVALUATION

Do NOT report:

```text
fake accuracy
fake mAP
fake IoU
fake F1
fake benchmark results
```

Metrics must be calculated only from a real held-out validation/test set.

Do not evaluate on training data.

Do not mix train and test samples.

Use the official dataset split when one exists.

If the official split is unavailable, create a deterministic stratified/group-aware split and document it.

---

# 3. THIRD HARD RULE — NO UNPROMPTED TRAINING

The IDE must NOT automatically execute background training or download multi-gigabyte datasets without explicit user command:

```text
python train_*.py
python *_colab.py
python scripts/train/*
```

Do not download multi-gigabyte datasets automatically.
Do not start unprompted GPU training.
Do not start unprompted long-running evaluation.

**Exception / Execution Protocol**:
When the user explicitly instructs or authorizes the IDE to launch, retrain, or evaluate a specific model checkpoint on a local dataset, the IDE may execute the requested training command locally on the GPU, with active validation monitoring and early stopping guards.

You may perform lightweight static checks such as:

```text
python -m py_compile <file>
```

only if harmless and only when necessary.

Your primary output is:

1. Code
2. Dataset setup scripts
3. Training commands
4. Evaluation commands
5. Checkpoint locations
6. Exact expected outputs
7. A README describing how I run everything

I will run the actual commands.

---

# 4. CURRENT REPOSITORY

First inspect the existing TRINETRA repository before modifying anything.

Relevant existing training files currently include:

```text
backend/colab_training/
    01_train_bigearthnet_colab.py
    02_train_vqa_captioning_colab.py
    03_train_grounding_colab.py
    04_train_change_cdvqa_colab.py
    05_train_optical_sar_colab.py
```

The current versions contain synthetic dataset generation and therefore must be replaced with real dataset loaders.

For example, the existing BigEarthNet trainer creates random tensors/labels rather than reading actual imagery and labels. The same problem exists in the existing VQA, grounding, change, and Optical-SAR trainers.

Do not preserve that behavior.

---

# 5. REQUIRED FINAL TRAINING PIPELINE

Create five independent but consistent training pipelines:

```text
1. BigEarthNet Remote-Sensing Encoder
2. RS-VQA / Scene Captioning
3. Text-Guided Region Grounding
4. Bi-Temporal Change Analysis / Change VQA
5. Optical + SAR Cross-Modal Fusion
```

Each pipeline must have:

```text
Dataset preparation
        ↓
Real data loader
        ↓
Train / validation / test split
        ↓
Baseline evaluation
        ↓
Training / fine-tuning
        ↓
Validation after each epoch
        ↓
Best checkpoint selection
        ↓
Final test evaluation
        ↓
Baseline vs trained comparison
        ↓
Metrics + plots + JSON
        ↓
Saved checkpoint
```

---

# 6. DATASET POLICY

Before implementing each downloader/loader:

**Perform fresh web research from official sources.**

Verify:

- current dataset name
- current version
- official download location
- license
- metadata format
- official split
- class/label definitions
- file structure
- modality
- image format
- whether labels are available
- whether there is a benchmark evaluation protocol

Prioritize official sources:

1. Official dataset website
2. Official GitHub repository
3. Official paper/repository
4. Official Hugging Face dataset if it is an authorized mirror
5. Official benchmark documentation

Do not depend on an unofficial random Google Drive or unknown dataset mirror unless the official source explicitly points to it.

---

# 7. DATASETS TO USE

Use the following public benchmark families where their current official access and task suitability are verified:

## Model 1 — BigEarthNet

Use:

> **BigEarthNet v2.0 / BigEarthNet-S2**

Purpose:

- remote-sensing image representation
- land-cover multi-label learning
- domain adaptation

Use real Sentinel-2 GeoTIFF imagery and real BigEarthNet labels.

Prefer the official metadata and official train/validation/test split.

---

## Model 2 — RS-VQA / Scene Understanding

Use real public remote-sensing VQA data such as:

> **RSVQA / EarthVQA / RSVL-VQA (Wuhan University)**

and, where appropriate:

> **VRSBench**

Use genuine:

- images (from real satellite and aerial sensors: INRIA, LoveDA, WHU, iSAID, Sentinel-2)
- questions
- answers

Do not generate artificial VQA questions.

If captioning data is available in the chosen benchmark, use its real captions.

---

## Model 3 — Text-Guided Grounding

Use:

> **VRSBench**

or another officially supported open remote-sensing referring-expression/grounding benchmark.

Use real:

- image
- text query
- bounding box / region annotation

Do not generate random boxes.

---

## Model 4 — Change Analysis

Use genuine public bi-temporal/change datasets appropriate to the task, such as:

> **CDVQA**

and, where appropriate for spatial change learning:

> **LEVIR-CD**

The final model should distinguish between:

- no/unchanged
- increased/new development
- decreased/receded

where the selected benchmark actually provides those labels.

For mask-based change detection, use real change masks.

Do not invent change labels.

---

## Model 5 — Optical + SAR

Use a real co-registered Optical/SAR dataset.

Candidate benchmark families include:

> **SEN1-2**

and/or:

> **SpaceNet 6**

Use genuine aligned optical and SAR data.

Do not independently pair unrelated random optical and SAR images.

If a benchmark is not genuinely co-registered for the intended task, do not claim that it is.

---

# 8. REAL-DATA VERIFICATION

Every dataset loader must contain verification checks.

For example:

```text
dataset exists
metadata exists
sample image exists
label exists
image dimensions valid
required bands exist
file is readable
```

For paired data:

```text
T1 exists
T2 exists
same geographic sample
pair metadata exists
```

For Optical-SAR:

```text
optical exists
SAR exists
same sample ID / geographic correspondence
required channels exist
```

If verification fails:

```text
ERROR: REAL DATASET REQUIREMENT NOT MET
```

and stop.

---

# 9. HARDWARE TARGET

Design the pipelines for local training on a laptop-class NVIDIA GPU.

Make these configurable:

```text
batch size
image size
epochs
learning rate
num workers
mixed precision
gradient accumulation
freeze backbone
max samples
```

Do not blindly use settings that exceed GPU memory.

Provide presets:

```text
--profile fast
--profile balanced
--profile quality
```

### Fast

For ~1 hour.

### Balanced

Target ~1–2 hours.

### Quality

Optional longer training.

The default should be **balanced**.

---

# 10. PRETRAINED BACKBONES

Do not train large CNNs from scratch unless there is a strong reason.

Prefer current lightweight pretrained architectures verified from official model repositories.

Examples may include:

- ResNet18
- ResNet50
- EfficientNet
- ConvNeXt-Tiny
- MobileNet where appropriate
- lightweight ViT where hardware allows

For multispectral/SAR tasks, adapt the input layer correctly.

The chosen architecture must be documented with a reason.

Do NOT automatically assume a larger architecture is better.

---

# 11. MODEL 1 — BIGEARTHNET

## Task

19-class multi-label land-cover classification.

Input:

12 Sentinel-2 bands where supported by the official dataset representation.

Output:

19-class multi-hot prediction.

Use:

```text
BCEWithLogitsLoss
```

with class weighting only if statistically justified.

## Baseline

Create an RGB ImageNet-pretrained baseline.

Example:

```text
RGB
→ ImageNet-pretrained ResNet18
→ 19-class head
```

## Proposed model

Use:

```text
12-band Sentinel-2
→ adapted pretrained backbone
→ 19-class head
```

## Metrics

Mandatory:

```text
mAP
Micro F1
Macro F1
Micro Precision
Micro Recall
Per-class AP
```

## Output

```text
bigearthnet_best.pt
bigearthnet_final.pt
evaluation_results.json
training_history.json
baseline_vs_trained.json
per_class_metrics.csv
```

---

# 12. MODEL 2 — RS-VQA

## Task

Answer real remote-sensing questions.

Use real RSVQA/VRSBench samples.

Do not create random questions or answers.

## IMPORTANT DESIGN CHOICE

Do NOT blindly build a tiny CNN + random token IDs.

Use a pretrained visual encoder and a real tokenizer/text encoder where practical.

Possible efficient approach:

```text
Image encoder
+
Question encoder
        ↓
Fusion
        ↓
Answer classifier
```

For classification-style VQA, restrict answer vocabulary to the benchmark's actual answer vocabulary.

## Baseline

Evaluate a non-fine-tuned/pretrained baseline where a legitimate baseline exists.

If no meaningful baseline exists, clearly state:

```text
baseline unavailable
```

Do not invent one.

## Metrics

At minimum:

```text
VQA accuracy
Per-class/per-answer accuracy
Macro F1 where meaningful
```

Also save a confusion matrix where classification formulation permits it.

---

# 13. MODEL 3 — GROUNDING

## Task

Text-guided region grounding.

Input:

```text
satellite image
+
real referring/query expression
```

Output:

```text
bounding box
```

## Model

Use a genuine image-text fusion/grounding architecture appropriate to the benchmark.

It is acceptable to use a lightweight pretrained visual backbone and train the grounding head.

## Loss

Use a sensible combination where appropriate:

```text
L1 / SmoothL1
+
IoU / GIoU loss
```

## Metrics

Mandatory:

```text
IoU
Recall@0.5
Recall@0.75
```

Also output:

```text
mean IoU
median IoU
failure count
```

## Visual evaluation

Save examples:

```text
grounding_examples/
    sample_001.png
    sample_002.png
```

showing:

```text
ground-truth box
predicted box
IoU
query
```

---

# 14. MODEL 4 — CHANGE ANALYSIS

Use real bi-temporal imagery.

Do not create random T1/T2 pairs.

## Input

```text
T1
T2
```

## Output

At minimum:

```text
change category
```

If masks are available:

```text
change map
```

## Architecture

Prefer a Siamese/shared-weight pretrained visual encoder:

```text
T1 ──┐
     ├── Shared encoder
T2 ──┘
       ↓
Difference / feature fusion
       ↓
Change head
```

Do not use a trivial raw-pixel classifier if a pretrained approach gives substantially better results within the time budget.

## Metrics

For classification:

```text
Accuracy
Macro F1
Confusion Matrix
```

For masks where ground truth exists:

```text
IoU
F1 / Dice
Precision
Recall
```

Save example change visualizations.

---

# 15. MODEL 5 — OPTICAL + SAR

## Task

Use co-registered Optical + SAR data jointly.

Input:

```text
Optical
+
SAR
```

## Architecture

Use two encoders or two input branches:

```text
Optical encoder
       \
        → Feature fusion → prediction head
       /
SAR encoder
```

Cross-attention or gated fusion is preferred when practical.

Do not merely concatenate the final textual answers of two separate models.

## Metrics

Use metrics appropriate to the real dataset task:

```text
Accuracy
Macro F1
Precision
Recall
Confusion Matrix
```

If the benchmark provides spatial masks/detections, add appropriate IoU/Dice metrics.

Also compare:

```text
Optical-only baseline
SAR-only baseline
Optical+SAR trained model
```

This comparison is especially valuable for demonstrating that fusion actually contributes.

---

# 16. BASELINE-FIRST REQUIREMENT

Every task must evaluate its baseline before reporting trained performance.

Output:

```text
BASELINE
mAP = ...

TRAINED
mAP = ...

IMPROVEMENT
+X.X%
```

If the trained model is worse:

```text
WARNING:
trained model did not outperform baseline
```

Do not manipulate thresholds or test sets to force a better result.

---

# 17. TEST SET INTEGRITY

Never tune hyperparameters using the final test set.

Correct:

```text
Train
 ↓
Validation
 ↓
Choose best checkpoint
 ↓
ONE final test evaluation
```

Do not repeatedly tune against the test set.

---

# 18. EARLY STOPPING

Implement early stopping using validation metric/loss.

Example:

```text
patience = 2
```

This helps stay within the 1–2 hour window.

Save:

```text
best checkpoint
```

based on the correct validation metric.

---

# 19. TRAINING CHECKPOINTS

During training save:

```text
checkpoint_epoch_01.pt
checkpoint_epoch_02.pt
...
best_model.pt
last_model.pt
```

At minimum save:

```text
best_model.pt
last_model.pt
```

Also save:

```text
config.json
```

containing:

- dataset version
- subset size
- random seed
- architecture
- optimizer
- learning rate
- batch size
- image size
- epochs
- training time
- software versions where practical

---

# 20. EVALUATION VISUALIZATION

Every trainer should produce:

```text
training_loss.png
validation_loss.png
metric_curve.png
```

Where meaningful also:

```text
confusion_matrix.png
per_class_metrics.png
prediction_examples/
```

Use matplotlib or another appropriate visualization library.

Do not use plots to hide poor results.

---

# 21. TRAINING REPORT

Each training run should produce:

```text
run/
├── config.json
├── training_history.json
├── evaluation_results.json
├── baseline_results.json
├── baseline_vs_trained.json
├── best_model.pt
├── last_model.pt
├── training_loss.png
├── validation_loss.png
└── examples/
```

---

# 22. COMMAND-LINE INTERFACE

Every trainer must be runnable from the terminal.

Example:

```bash
python training/01_bigearthnet/train.py \
  --data_dir "D:\datasets\BigEarthNet-S2" \
  --metadata "D:\datasets\BigEarthNet-S2\metadata.parquet" \
  --profile balanced
```

The actual commands must match the final repository.

Do NOT make me edit Python source code just to change dataset paths.

---

# 23. DATASET PREPARATION SCRIPTS

Create separate preparation commands where needed.

Example:

```bash
python training/01_bigearthnet/prepare.py
```

Preparation should:

- verify dataset
- verify metadata
- build index/cache
- report dataset counts
- avoid copying data unnecessarily
- never generate fake samples

For very large datasets, support a **real-data subset manifest**:

```text
20,000 real training IDs
4,000 real validation IDs
4,000 real test IDs
```

These IDs must point to actual benchmark samples.

Do not create synthetic replacements.

---

# 24. LARGE DATASET / STORAGE STRATEGY

My laptop has limited local storage.

Implement dataset indexing so we don't duplicate huge datasets.

Prefer:

```text
original dataset
      ↓
metadata/index
      ↓
training loader reads required samples
```

Use cache only when necessary.

Do not create another full copy of a dataset.

---

# 25. TIME BUDGET

The priority is:

```text
REAL DATA
>
CORRECT EVALUATION
>
USEFUL MODEL
>
FAST TRAINING
```

Do NOT sacrifice data authenticity for speed.

Instead speed up using:

- pretrained backbone
- mixed precision
- reasonable image resolution
- subset manifests
- worker tuning
- frozen early layers
- early stopping
- gradient accumulation
- efficient dataloading

---

# 26. DO NOT CLAIM “BETTER THAN CORE MODEL” AUTOMATICALLY

The goal is to make trained specialist models useful and preferably better.

But only say:

```text
improved over baseline
```

when the evaluation actually proves it.

If not:

```text
trained model did not improve this run
```

Then provide likely causes and next experiment.

No fabricated success.

---

# 27. REPRODUCIBILITY

Every training run must record:

```text
seed
dataset version
dataset subset IDs
model architecture
pretrained weights
learning rate
batch size
epochs
hardware
software versions
timestamp
```

Set deterministic seeds where practical.

Save the exact subset manifest used.

---

# 28. GPU / CPU MEMORY MANAGEMENT

Implement:

```text
mixed precision
pin_memory
num_workers
persistent_workers where appropriate
gradient accumulation
batch-size fallback
```

But do not silently reduce batch size without reporting it.

If OOM occurs, print:

```text
CUDA OUT OF MEMORY

Suggested:
--batch_size 8
--profile fast
```

Do not switch silently to fake data or CPU unless explicitly requested.

---

# 29. INFERENCE TEST

After training, provide a separate command:

```bash
python .../predict.py ...
```

It must load the saved checkpoint and run on a real sample.

The result should show:

```text
input
prediction
confidence
ground truth where available
```

This is necessary to verify that the checkpoint actually works.

---

# 30. CHECKPOINT COMPATIBILITY

The saved checkpoints must be compatible with the existing TRINETRA backend model loader.

Inspect:

```text
backend/models/loader.py
backend/models/architectures.py
```

Update the loader/architecture only as required.

Document exactly where each trained checkpoint should be placed:

```text
backend/models/checkpoints/
```

Do not silently change checkpoint formats.

---

# 31. EXISTING TRAINING FILE MIGRATION

Replace the current files with real-data implementations:

```text
01_train_bigearthnet_colab.py
02_train_vqa_captioning_colab.py
03_train_grounding_colab.py
04_train_change_cdvqa_colab.py
05_train_optical_sar_colab.py
```

Prefer renaming or creating proper local training modules if the old names are misleading.

Do not remove the old files until the new pipeline is clearly documented or migrated.

---

# 32. WINDOWS LAPTOP SUPPORT

I am training locally on a Windows laptop.

Commands must work with Windows paths.

Support:

```text
D:\datasets\...
C:\datasets\...
```

Avoid shell syntax that only works on Linux unless you also provide the Windows equivalent.

Use Python's `pathlib`.

---

# 33. COMMANDS ONLY — DO NOT RUN THEM

At the end provide commands for:

### Dataset verification

```bash
python ... verify ...
```

### Training

```bash
python ... train ...
```

### Evaluation

```bash
python ... evaluate ...
```

### Inference

```bash
python ... predict ...
```

### Export checkpoint

```bash
python ... export ...
```

Do not execute these commands yourself.

---

# 34. EXPECTED TERMINAL OUTPUT

The training command should make progress obvious:

```text
============================================================
TRINETRA — BigEarthNet Training
============================================================

Dataset:
BigEarthNet-S2 v2.0

Real samples:
Train: 20,000
Validation: 4,000
Test: 4,000

GPU:
NVIDIA ...

------------------------------------------------------------
BASELINE
------------------------------------------------------------
mAP: 0.XXXX
Micro F1: 0.XXXX
Macro F1: 0.XXXX

------------------------------------------------------------
TRAINING
------------------------------------------------------------
Epoch 1/3
Train Loss: ...
Val Loss: ...
Val mAP: ...

Epoch 2/3
...

------------------------------------------------------------
FINAL TEST
------------------------------------------------------------
mAP: ...
Micro F1: ...
Macro F1: ...

------------------------------------------------------------
COMPARISON
------------------------------------------------------------
Baseline mAP: ...
Trained mAP: ...
Delta: +...
============================================================
```

---

# 35. FINAL DIRECTORY STRUCTURE

Create a clean structure such as:

```text
training/
│
├── common/
│   ├── metrics.py
│   ├── seed.py
│   ├── checkpoint.py
│   ├── reporting.py
│   ├── profiling.py
│   └── dataset_utils.py
│
├── 01_bigearthnet/
│   ├── prepare.py
│   ├── dataset.py
│   ├── model.py
│   ├── train.py
│   ├── evaluate.py
│   └── predict.py
│
├── 02_rsvqa/
│   ├── prepare.py
│   ├── dataset.py
│   ├── model.py
│   ├── train.py
│   ├── evaluate.py
│   └── predict.py
│
├── 03_grounding/
│   ├── prepare.py
│   ├── dataset.py
│   ├── model.py
│   ├── train.py
│   ├── evaluate.py
│   └── predict.py
│
├── 04_change/
│   ├── prepare.py
│   ├── dataset.py
│   ├── model.py
│   ├── train.py
│   ├── evaluate.py
│   └── predict.py
│
└── 05_optical_sar/
    ├── prepare.py
    ├── dataset.py
    ├── model.py
    ├── train.py
    ├── evaluate.py
    └── predict.py
```

---

# 36. SHARED EVALUATION LIBRARY

Create reusable evaluation utilities.

For example:

```text
training/common/metrics.py
```

with:

```text
multilabel_metrics()
classification_metrics()
vqa_accuracy()
box_iou()
recall_at_iou()
segmentation_metrics()
```

This avoids five different implementations of the same metric.

---

# 37. DATASET MANIFEST

Every training run should save the exact real sample IDs used.

Example:

```text
manifests/
    bigearthnet_train.txt
    bigearthnet_val.txt
    bigearthnet_test.txt
```

For paired datasets:

```text
change_train.csv
optical_sar_train.csv
```

These files must contain real dataset identifiers.

---

# 38. NO DATA LEAKAGE

Explicitly verify that:

```text
train IDs ∩ validation IDs = empty
train IDs ∩ test IDs = empty
validation IDs ∩ test IDs = empty
```

For spatial/temporal paired datasets, use the dataset's official grouping/split to prevent leakage whenever documented.

---

# 39. MODEL CARD / TRAINING REPORT

For each trained model create a small Markdown report:

```text
Model
Dataset
Dataset version
Training subset
Validation subset
Test subset
Architecture
Pretrained weights
Training time
Hardware
Metrics
Baseline
Improvement
Known limitations
```

Never claim production readiness from a small subset alone.

---

# 40. FINAL INTEGRATION WITH SATQUERY

After model training, the trained checkpoint must be usable by:

```text
SatQuery Agent
     ↓
Specialist Tool
     ↓
Trained Checkpoint
     ↓
Evidence
     ↓
Answer
```

The agent itself does not need LLM fine-tuning.

The general-purpose LLM stays separate from these specialist models.

---

# 41. IMPORTANT: NO LLM FINE-TUNING

Do NOT spend time fine-tuning:

```text
Qwen
Llama
other general-purpose LLMs
```

For the current deadline.

Use local LLMs only for:

```text
query understanding
planning
tool selection
response synthesis
```

Focus training compute on the remote-sensing specialists.

---

# 42. RESEARCH-BEFORE-CODING REQUIREMENT

Before implementing each dataset pipeline, the IDE MUST fresh-search current official sources and verify:

```text
dataset version
download method
file structure
labels
official splits
license
recommended preprocessing
benchmark metrics
```

Do not rely on outdated training data in the IDE's model.

Record the verified source links in each training README.

---

# 43. WHAT THE IDE MUST NOT DO

Do NOT:

- run full training
- download huge datasets automatically
- invent data
- invent labels
- fabricate evaluation scores
- use random tensors
- use random bounding boxes
- use fake VQA
- create fake temporal pairs
- silently use an unrelated dataset
- silently substitute another dataset
- claim a model beats a baseline without evidence
- change the final test set after seeing results
- hide OOM or data errors
- leave synthetic fallback code in production training
- make me edit source code just to change paths

---

# 44. FINAL VALIDATION

Before finishing, perform only safe/static validation.

Check for synthetic-data anti-patterns:

```text
torch.randn
torch.rand
torch.randint
random labels
synthetic
fake dataset
dummy dataset
mock training data
```

Any occurrence in the actual training data pipeline must be removed.

Search the entire training directory.

Also verify:

```text
[ ] all datasets are real
[ ] all labels are real
[ ] official splits are used where available
[ ] no test leakage
[ ] metrics are real
[ ] checkpoints are saved
[ ] commands are documented
[ ] no training was executed
```

---

# 45. FINAL OUTPUT REQUIRED FROM THE IDE

After modifying the repository, do NOT run training.

Return:

## 1. Files changed

List every created/modified file.

## 2. Dataset setup

For each model:

```text
Dataset:
Official source:
Required files:
Approx storage:
Command:
```

## 3. Training command

Give the exact command I should run.

## 4. Evaluation command

Give the exact command I should run.

## 5. Checkpoint location

Tell me exactly where the resulting `.pt` or equivalent file will be saved.

## 6. Expected metrics

Do NOT invent expected scores.

Instead tell me:

```text
metric names
what constitutes a good result
what the baseline represents
```

## 7. Hardware profile

Tell me the recommended default command for my laptop and approximately what settings it uses.

## 8. Time-saving options

Tell me how to use:

```text
--profile fast
--profile balanced
```

and what each changes.

## 9. Validation

Report only static/safe checks actually performed.

---

# 46. SUCCESS CRITERION

The project is successful when I can personally run:

```text
dataset preparation
→ training
→ evaluation
→ inference
→ checkpoint export
```

for all five specialist models on **real public remote-sensing datasets**, without synthetic data, and obtain:

```text
trained model
+
real test metrics
+
baseline comparison
+
visual evaluation
+
reproducible checkpoint
```

The final system must provide credible evidence that the trained specialist models improve remote-sensing capabilities rather than merely producing plausible-looking outputs.

---

# 47. FINAL INSTRUCTION

**Do not run the training scripts.**

**Do not download the datasets yourself.**

**Do not fabricate any dataset, labels, samples, metrics, or outputs.**

**Do not use synthetic data under any circumstances.**

First research the current official dataset/model documentation, then inspect the existing TRINETRA training code, replace the synthetic loaders with genuine dataset loaders, implement efficient pretrained-model fine-tuning/training, implement proper benchmark evaluation, implement baseline-vs-trained comparison, save checkpoints and reports, and finally provide me with the exact commands I need to execute manually on my laptop.

I will run the commands myself.
