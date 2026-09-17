# TRINETRA — ML Training Best Practices & Experimental Protocol

## Purpose

This document defines the rules for dataset splitting, preprocessing, model selection, training, validation, checkpointing, evaluation and experiment design across TRINETRA.

The objective is **scientifically defensible performance**, not the highest-looking number.

A recommendation must be rejected when it increases leakage, invalidates comparison, reduces generalization, or produces an untrustworthy result. Do not implement a requested technique merely because it is fashionable.

---

# 1. Non-Negotiable Training Principles

1. **Never train and test on overlapping information.**
2. **Never fit preprocessing on the test set.**
3. **Never select a checkpoint using test performance.**
4. **Never tune thresholds using test labels.**
5. **Never choose a model because it is newer; choose it because the task and evidence justify it.**
6. **Always keep a simple baseline.**
7. **Every experiment must have a unique run ID.**
8. **Every experiment must record its exact configuration.**
9. **Every checkpoint must identify the dataset split and preprocessing version used to create it.**
10. **Never overwrite a previous experiment.**
11. **Never report the best run without reporting the selection procedure.**
12. **Do not use synthetic data for benchmark claims unless the claim explicitly concerns synthetic-data behavior.**
13. **Do not fabricate missing labels or metrics.**
14. **Do not silently change the dataset split after seeing results.**
15. **Do not use external benchmark test data for hyperparameter tuning.**
16. **If a technique does not improve validation/generalization without compromising scientific validity, reject it.**

---

# 2. Dataset Splitting — The Most Important Rule

Dataset splitting must follow the **data-generating structure**, not a generic `train_test_split()` by default.

A random split is valid only when samples can reasonably be treated as independent.

Remote-sensing pixels and image patches are often spatially correlated. Randomly splitting neighboring patches can produce leakage.

Therefore:

> **Spatial/scene-level independence takes priority over convenience.**

---

# 3. Change Detection — LEVIR-CD / WHU-CD / SECOND

## Recommended split

Use the dataset's official train/validation/test split whenever an established official split exists.

Do not create a new random pixel split.

For any additional custom split:
- split by scene/geographic region;
- keep corresponding temporal images together;
- never separate patches from the same original scene across train and test;
- document the split manifest.

## Why

Bitemporal images from the same geographic area are strongly correlated.

A random patch split can make the test set artificially easy.

## Training

Recommended structure:

```text
Official Train
     ↓
Training augmentation
     ↓
Model
     ↓
Official Validation
     ↓
Checkpoint + threshold selection
     ↓
FREEZE
     ↓
Official Test
```

## Model strategy

Always implement:

### Baseline
Siamese CNN / encoder-decoder baseline.

### Modern candidate
A transformer/attention-based change-detection model such as a ChangeFormer/BIT-style architecture, provided its implementation and license are acceptable.

The modern model must beat the baseline on the validation protocol or provide another demonstrable benefit.

## Loss

For binary change detection, consider:
- BCE/BCEWithLogits
- Dice loss
- Focal loss
- BCE + Dice

Do not automatically combine every loss.

Select based on validation behavior, class imbalance and error analysis.

## Threshold

Do not blindly use a fixed 0.5 threshold if the evaluation protocol permits threshold tuning.

If threshold tuning is allowed:
- tune on validation only;
- freeze threshold;
- evaluate test once.

If the benchmark protocol specifies a threshold, follow the protocol.

## Augmentation

Safe candidates:
- horizontal/vertical flips where geographically/task appropriate;
- rotations where orientation is not semantically important;
- controlled crops.

Be careful with:
- aggressive color transformations;
- independent transformations between temporal images;
- transformations that create physically unrealistic differences.

For bitemporal change detection, geometric transformations should generally be applied consistently to both temporal images.

---

# 4. Optical + SAR — SEN12MS / BigEarthNet

## Split strategy

Prefer official/geographic splits.

Do not randomly split highly correlated geographic patches when the benchmark provides a more rigorous split.

For paired modalities:
- Sentinel-1 and Sentinel-2 must remain paired;
- labels must remain associated with the same geographic sample;
- never split modalities independently.

## Preprocessing

Preprocessing must be modality-specific.

### Optical

Document:
- reflectance representation;
- valid bands;
- cloud/nodata policy;
- normalization statistics.

Fit learned normalization statistics using training data only.

### SAR

Document:
- polarization;
- calibration state;
- linear vs dB representation;
- speckle handling;
- terrain correction status;
- normalization.

Do not treat SAR as another RGB image.

## Fusion experiments

Use an ablation sequence:

```text
Optical only
SAR only
Early fusion
Late fusion
Cross-attention / gated fusion
```

This is more scientifically useful than presenting only the most complex architecture.

## Why

The judges can then see whether multimodal fusion actually contributes.

If optical-only performs as well as fusion, do not claim fusion is beneficial.

---

# 5. Hyperspectral — Indian Pines / Salinas / Pavia University

## Critical rule

Do NOT use a random pixel split as the main scientific result.

Hyperspectral pixels have strong spatial and spectral correlation.

## Preferred approach

Use explicit spatial blocks/regions:

```text
Full scene
   ↓
Spatial blocks
   ├── Train blocks
   ├── Validation blocks
   └── Test blocks
```

Keep neighboring pixels from the same spatial region together.

Store the split mask and checksum.

## Preprocessing

Fit:
- scaling;
- normalization;
- dimensionality reduction;
- feature selection

using training data only.

Apply the fitted transformation to validation/test.

## Model progression

Start with:

1. classical baseline;
2. spectral-only baseline;
3. spectral-spatial CNN;
4. modern spectral-spatial architecture if justified.

Potential architectures include:
- 3D CNN;
- HybridSN-style spectral-spatial networks;
- attention/transformer-based hyperspectral models.

Do not automatically select a transformer simply because it is modern.

## Metrics

Report:
- Overall Accuracy;
- Average Accuracy;
- Macro-F1;
- per-class F1;
- Cohen's Kappa;
- confusion matrix;
- class support.

Accuracy alone is insufficient, especially under class imbalance.

---

# 6. Remote-Sensing VQA — RSVQA

## Split strategy

Use the dataset's official split.

If questions derived from the same geographic image can appear in both train and test, check whether this creates image-level leakage for your intended evaluation.

Where possible, evaluate both:
- official benchmark performance;
- image/scene-disjoint generalization.

## Architecture

Separate:

```text
Vision Encoder
      ↓
Visual Features
      ↓
Question Encoder
      ↓
Fusion
      ↓
Answer Head
```

The LLM should not be used as a replacement for the ground-truth VQA evaluation.

## Important TRINETRA rule

The language model can explain a prediction, but it must not invent remote-sensing measurements.

Preferred:

```text
Image
 ↓
Remote-sensing computation
 ↓
Model
 ↓
Evidence
 ↓
LLM explanation
```

Not:

```text
Image
 ↓
LLM guess
 ↓
invented NDVI / area / confidence
```

---

# 7. Baseline-First Strategy

Every specialist should have a baseline.

Example:

```text
Baseline
   ↓
Validation
   ↓
Modern architecture
   ↓
Validation
   ↓
Ablation
   ↓
Final model
```

## Why

Without a baseline, an impressive model score does not demonstrate that the architecture contributed.

A baseline also catches:
- data leakage;
- broken labels;
- preprocessing mistakes;
- metric bugs;
- overfitting.

---

# 8. Model Selection

Model selection must be task-driven.

Use this decision order:

### Step 1 — Task requirements

Determine:
- classification;
- segmentation;
- change detection;
- regression;
- VQA;
- multimodal fusion.

### Step 2 — Dataset characteristics

Determine:
- sample count;
- spatial resolution;
- spectral bands;
- modality count;
- class imbalance;
- geographic diversity;
- label quality.

### Step 3 — Compute constraints

Your target hardware is approximately **12 GB GPU VRAM**.

Therefore test:
- mixed precision;
- batch size;
- gradient accumulation;
- gradient checkpointing;
- image tiling/cropping.

Do not automatically choose the largest architecture that fits.

### Step 4 — Baseline

Establish a reproducible reference.

### Step 5 — Modern architecture

Introduce complexity only when justified.

---

# 9. Hyperparameter Tuning

## Recommended order

Do not tune everything simultaneously.

### First
Learning rate.

### Second
Batch size / effective batch size.

### Third
Weight decay.

### Fourth
Scheduler.

### Fifth
Architecture-specific parameters.

Use validation data only.

## Search strategy

For expensive deep-learning models:
- start with a small controlled search;
- use random/Bayesian search only when the search space justifies it;
- avoid enormous brute-force grids.

## Reproducibility

Every trial records:
- seed;
- configuration;
- validation metrics;
- training duration;
- checkpoint;
- hardware;
- software version.

---

# 10. Class Imbalance

First measure the class distribution.

Do not automatically use:
- class weights;
- focal loss;
- oversampling;
- undersampling

just because imbalance exists.

Choose an intervention only if validation evidence shows that minority-class performance requires it.

For change detection, report precision/recall/F1/IoU rather than accuracy alone because unchanged pixels can dominate.

---

# 11. Data Augmentation

Augmentation should preserve the physical meaning of the task.

## Generally useful

- geometric transformations;
- controlled crops;
- appropriate flips/rotations.

## Use carefully

- spectral perturbations;
- brightness/contrast;
- noise injection;
- modality dropout.

## Never

Use augmentation that changes the ground-truth semantic relationship.

For bitemporal data, independently changing one temporal image can create artificial change.

---

# 12. Early Stopping and Checkpointing

Checkpoint selection must use validation performance.

Recommended stored information:

```text
checkpoint
├── model weights
├── architecture ID
├── optimizer state
├── scheduler state
├── epoch
├── global step
├── dataset ID
├── split ID
├── preprocessing version
├── tokenizer ID if applicable
├── configuration hash
├── git commit
└── training metrics
```

Do not select the final checkpoint based on test performance.

---

# 13. Cross-Validation

Cross-validation is useful when the dataset is small.

But do NOT blindly use ordinary random K-fold CV for spatial remote-sensing data.

Prefer:
- spatial K-fold;
- scene-level K-fold;
- geographic-group K-fold

when samples are spatially correlated.

For large official benchmark datasets with fixed official splits, preserve the official protocol rather than replacing it with arbitrary K-fold validation.

---

# 14. Data Leakage Audit

Before every final benchmark run, run an automated leakage check.

Check:
- duplicate files;
- duplicate hashes;
- near-duplicate images where feasible;
- same scene across splits;
- overlapping spatial regions;
- temporal pair leakage;
- preprocessing fitted on test;
- labels accidentally included as features;
- cached features crossing split boundaries.

The benchmark should fail rather than continue if a serious leakage condition is detected.

---

# 15. Evaluation Metrics

## Binary change detection
- Precision
- Recall
- F1
- IoU
- confusion matrix

## Multiclass change
- per-class Precision/Recall/F1
- Macro-F1
- mIoU
- confusion matrix

## Hyperspectral classification
- OA
- AA
- Macro-F1
- Kappa
- per-class F1

## Multimodal classification
- Accuracy
- Macro-F1
- per-class metrics

## Regression
- MAE
- RMSE
- R² where meaningful

Never select metrics because they make the result look better.

Use the metrics expected by the benchmark protocol.

---

# 16. Statistical Reliability

For final benchmark results, where sample size permits:

- bootstrap confidence intervals;
- per-image/per-scene metric distributions;
- mean and median;
- worst-case examples.

Do not report only:

> F1 = 94.7%

Prefer:

> F1 = 94.7%, with a 95% bootstrap confidence interval of [X, Y].

The values must be computed from the actual final run.

---

# 17. Ablation Studies

For important TRINETRA claims, use ablations.

Example:

```text
Baseline
   ↓
+ preprocessing
   ↓
+ attention
   ↓
+ multimodal fusion
   ↓
+ postprocessing
```

For each addition measure the change in:
- primary benchmark metric;
- runtime;
- memory;
- parameter count.

If a component does not help, consider removing it.

---

# 18. Generalization Testing

A model that performs well only on its training distribution is not sufficient evidence.

Use:

```text
Train → Benchmark A
Test  → Benchmark A

Train → Benchmark A
Test  → Benchmark B
```

The second experiment is especially valuable.

Do not fine-tune on Benchmark B before calling it an external generalization test.

---

# 19. Repeated Runs

For stochastic models, a single run can be misleading.

For development:
- use multiple seeds when computationally practical.

For the final benchmark:
- report the predefined protocol;
- if multiple seeds are used, report mean and variation;
- never cherry-pick the best seed.

---

# 20. Model Efficiency

Record:

- parameter count;
- trainable parameter count;
- model size;
- peak GPU memory;
- inference latency;
- throughput;
- input resolution;
- batch size.

Do not claim a model is “efficient” simply because it has fewer parameters.

For example, comparing a compressed classical feature model to a QML parameter count is not by itself evidence that QML is more efficient.

---

# 21. Reproducible Experiment Directory

Use a structure similar to:

```text
experiments/
└── change_detection/
    └── levir_cd/
        └── run_YYYYMMDD_HHMMSS/
            ├── config.yaml
            ├── dataset_manifest.json
            ├── split_manifest.json
            ├── preprocessing.json
            ├── model.json
            ├── train.log
            ├── metrics.json
            ├── confusion_matrix.json
            ├── curves/
            ├── predictions/
            ├── failures/
            ├── checkpoint/
            └── provenance.json
```

Never overwrite previous runs.

---

# 22. What the IDE Must Generate

For each model/dataset combination, create separate files rather than one giant training script.

Recommended structure:

```text
training/
├── datasets/
│   ├── levir_cd.py
│   ├── whu_cd.py
│   ├── sen12ms.py
│   ├── hyperspectral.py
│   └── rsvqa.py
│
├── models/
│   ├── baselines/
│   ├── change_detection/
│   ├── optical_sar/
│   ├── hyperspectral/
│   └── vqa/
│
├── preprocessing/
├── losses/
├── metrics/
├── calibration/
├── evaluation/
├── experiments/
└── configs/
```

The dataset adapter, model, loss, preprocessing and evaluator should be independently testable.

---

# 23. What NOT to Do

The IDE must actively reject these patterns:

### ❌ Random split for spatially correlated remote-sensing pixels
Unless independence has been established.

### ❌ Fit scaler on complete dataset
This leaks test information.

### ❌ Tune threshold on test set
Invalid final evaluation.

### ❌ Select best checkpoint from test score
Invalid.

### ❌ Train on benchmark test images
Invalid.

### ❌ Add every available augmentation
More augmentation is not automatically better.

### ❌ Use a transformer because it is “modern”
Architecture must be justified experimentally.

### ❌ Use focal loss automatically
Only use it when class imbalance/error analysis supports it.

### ❌ Use synthetic benchmark data to claim real-world performance
Invalid.

### ❌ Report the best random seed
Cherry-picking.

### ❌ Mix benchmark scores from incompatible papers
Potentially misleading.

### ❌ Call model agreement “accuracy”
Agreement is not ground-truth correctness.

---

# 24. Final Training Decision Rule

For every proposed technique ask:

1. Does it address a real problem in this dataset?
2. Does it preserve the benchmark protocol?
3. Can it be evaluated without leakage?
4. Does validation/generalization improve?
5. Does the added complexity have measurable benefit?
6. Does it fit the available hardware?
7. Can another person reproduce it?

If the answer to the scientific questions is no:

> **Reject the technique.**

This rule overrides a request to use a particular technique merely because it sounds advanced.

---

# 25. Recommended TRINETRA Dataset → Training Strategy Matrix

| Dataset | Primary task | Split principle | Model progression |
|---|---|---|---|
| LEVIR-CD | Binary change detection | Official scene/split | Siamese baseline → transformer/attention |
| WHU-CD | External change validation | Official/geographic | Frozen model evaluation |
| SECOND | Semantic change | Official split | Semantic baseline → modern architecture |
| SEN12MS | Optical/SAR | Geographic/official-compatible | Optical → SAR → fusion |
| BigEarthNet v2.0 | Multimodal EO | Geographic split | Baseline → multimodal fusion |
| Indian Pines | Hyperspectral | Spatial blocks | Classical → spectral-spatial CNN |
| Salinas | Hyperspectral | Spatial blocks | Classical → spectral-spatial CNN |
| Pavia University | Hyperspectral | Spatial blocks | Classical → spectral-spatial CNN |
| RSVQA | EO VQA | Official split + leakage audit | VQA baseline → fusion/LLM explanation |

---

# 26. Final Rule for TRINETRA

The objective is not:

> “Make TRINETRA use every modern technique.”

The objective is:

> **“Find the simplest scientifically valid system that demonstrates measurable, reproducible improvement on independent remote-sensing benchmarks.”**

If a simpler model performs equally well, prefer the simpler model.

If a modern model improves generalization, document why.

If a technique improves the test score but violates the protocol, reject it.

If a result cannot be reproduced, do not present it as validated.

If evidence contradicts our assumption, update the architecture rather than manipulating the experiment.
