# TRINETRA / SatQuery AI — QML + PennyLane Implementation Task

## Objective

Add a **real Quantum Machine Learning research branch** to the existing TRINETRA / SatQuery AI system.

Context:

- Existing classical remote-sensing specialist models remain the **primary operational path**.
- QML is an **experimental / research / future-scalability branch**.
- Use **PennyLane** and a local quantum simulator.
- Do **not** replace the classical models with QML.
- Do **not** claim current quantum advantage unless real held-out evaluation proves it.
- Use **real remote-sensing data only**.
- **ZERO synthetic data**.

The QML branch should demonstrate a credible path from today's classical remote-sensing system to future quantum hardware without redesigning the entire application.

---

# 1. FIRST CREATE `backend/qml/TASK.md`

Before writing QML code, create:

```text
backend/qml/TASK.md
```

This file must contain the research and implementation plan.

It must explicitly state:

> Before selecting any QML algorithm, PennyLane device, encoding method, circuit architecture, or current API, perform fresh web research using current official documentation. Do not rely on the IDE's pretrained knowledge because it may be outdated.

Search current official sources for:

- PennyLane
- PennyLane simulator/device documentation
- PennyLane + PyTorch integration
- current quantum autodiff/gradient APIs
- current `default.qubit`
- current `lightning.qubit`
- current GPU-capable simulator options
- current hardware backend abstractions
- current QML examples for classification
- current best practices for hybrid quantum-classical models

Prefer:

1. Official PennyLane docs
2. Official PennyLane GitHub
3. Official Python package information
4. Official benchmark/paper sources

Do not rely on old blog posts/tutorials without checking the current official API.

---

# 2. RESEARCH THE BEST QML ALGORITHM FOR THIS PROJECT

In `TASK.md`, require fresh research comparing at least:

- Variational Quantum Classifier (VQC)
- Quantum Neural Network (QNN)
- Quantum Kernel / QSVM
- Hybrid Quantum-Classical Neural Network
- Data re-uploading approaches where relevant

Evaluate them specifically for:

- remote-sensing classification
- compact learned feature vectors
- 4–8 qubits
- laptop/local simulation
- PennyLane
- PyTorch compatibility
- training stability
- latency
- scalability toward future hardware
- ease of explaining to ISRO judges
- measurable benchmark metrics

Do not choose an algorithm because it is trendy.

At the end of `TASK.md`, make one explicit recommendation and explain it.

---

# 3. RECOMMENDED FIRST USE CASE

Unless fresh research proves a better option, start with:

> **Bi-temporal change classification**

Reason:

- the existing project already has a change-analysis specialist
- real T1/T2 satellite imagery produces compact discriminative features
- classification is much more practical for current quantum simulators than full image segmentation/detection
- it gives straightforward Accuracy, F1, Precision, Recall and confusion-matrix evaluation

Do NOT start with QML bounding-box prediction.

---

# 4. CORE ARCHITECTURE

The QML branch must be:

```text
REAL SATELLITE DATA
        |
        v
EXISTING CLASSICAL REMOTE-SENSING PIPELINE
        |
        v
FEATURE EXTRACTION
        |
        v
NORMALIZATION
        |
        v
PCA / FEATURE SELECTION
        |
        v
4–8 DIMENSIONAL VECTOR
        |
        v
QUANTUM ENCODING
        |
        v
PENNYLANE QML CIRCUIT
        |
        v
MEASUREMENT
        |
        v
QML PREDICTION
        |
        v
CLASSICAL vs QML VALIDATION
        |
        v
AGREEMENT / DISAGREEMENT
        |
        v
EVIDENCE + CONFIDENCE
```

The classical specialist remains the operational source of truth.

---

# 5. ABSOLUTE NO-SYNTHETIC-DATA RULE

NEVER use:

```python
torch.randn()
torch.rand()
torch.randint()
numpy.random.*()
fake labels
fake features
fake satellite images
fake temporal pairs
fake ground-truth
```

Do not generate artificial samples to make training easier.

Do not create fake evaluation data.

Do not create synthetic labels from random rules.

All QML training/evaluation samples must originate from:

- real public remote-sensing datasets
- real specialist-model features generated from real imagery
- real ground truth

If the real dataset is unavailable:

> STOP and provide the exact dataset acquisition instructions.

Never silently substitute synthetic data.

---

# 6. DO NOT TRAIN ON THE LLM

Do not fine-tune:

- Qwen
- Llama
- other general-purpose LLMs

for this QML task.

Use the existing local LLM/agent only for:

- deciding whether QML is applicable
- invoking the QML tool
- explaining results

Focus training compute on the QML specialist.

---

# 7. DO NOT FEED RAW IMAGES INTO THE QUANTUM CIRCUIT

Do NOT do:

```text
224×224 image → hundreds/thousands of qubits
```

Instead:

```text
image
 ↓
classical remote-sensing encoder
 ↓
feature vector
 ↓
PCA
 ↓
4–8 features
 ↓
4–8 qubits
```

Use the classical feature extractor because current quantum simulation is constrained by qubit count and circuit complexity.

The feature reduction pipeline must be fit on **training data only**.

Then apply it to validation/test data.

---

# 8. CLASSICAL BASELINE

Before QML training, train/evaluate a legitimate classical baseline using the **same reduced feature vectors**.

Candidate baselines:

- Logistic Regression
- SVM
- Random Forest
- small MLP

Research/choose the most appropriate simple baseline.

Comparison must be fair:

```text
same samples
same train/validation/test split
same feature vectors
same preprocessing
```

Do not compare QML trained on one representation against a classical model trained on an unrelated representation.

---

# 9. DATA SPLITS

Use official benchmark train/validation/test splits whenever available.

Otherwise create deterministic splits with a documented rule.

Verify:

```text
Train ∩ Validation = ∅
Train ∩ Test = ∅
Validation ∩ Test = ∅
```

Also verify no geographic/temporal leakage where the dataset requires grouped splitting.

Never use the final test set for hyperparameter tuning.

---

# 10. FEATURE PIPELINE

Create:

```text
backend/qml/feature_pipeline.py
```

Responsibilities:

1. Receive real classical feature vectors.
2. Clean missing/invalid values.
3. Fit normalization on training set only.
4. Fit PCA/feature reduction on training set only.
5. Transform validation/test.
6. Save the fitted transform.
7. Reproduce exactly during inference.

Save:

```json
{
  "input_features": 128,
  "reduced_features": 6,
  "normalization": "...",
  "pca": "...",
  "seed": 42
}
```

---

# 11. PENNYLANE SIMULATOR

Research current PennyLane simulator options first.

Evaluate:

```text
default.qubit
lightning.qubit
```

and current GPU-capable options if appropriate.

Select the simulator based on:

- local hardware
- circuit size
- latency
- stability
- current support
- future hardware portability

Do not assume a simulator is GPU-enabled simply because the laptop has a CUDA GPU.

Document the actual device used.

---

# 12. QUANTUM CIRCUIT

After current research, choose an appropriate encoding and ansatz.

Candidate structure:

```text
feature vector
 ↓
AngleEmbedding
 ↓
trainable rotations
 ↓
entanglement
 ↓
trainable rotations
 ↓
measurement
```

But do not assume this is automatically best.

`TASK.md` must document why the final encoding and ansatz were selected.

Start with:

```text
4 qubits
```

then test:

```text
6 qubits
```

and optionally:

```text
8 qubits
```

Keep the circuit shallow.

Do not maximize circuit depth.

---

# 13. QML MODEL

Implement a reusable class such as:

```text
QuantumChangeClassifier
```

It should support:

- configurable qubits
- configurable layers
- configurable simulator
- configurable shots
- configurable feature dimension
- reproducible initialization

Integrate with PyTorch where beneficial.

---

# 14. TRAINING

Implement:

```text
backend/qml/training/train_vqc.py
```

Training flow:

```text
real train features
 ↓
quantum encoding
 ↓
QNode
 ↓
measurement
 ↓
loss
 ↓
gradient
 ↓
optimizer
 ↓
update parameters
```

Use early stopping.

Make epochs, learning rate and circuit depth configurable.

Do not run the training automatically from the IDE.

---

# 15. TIME / LATENCY TARGET

QML should be a **small research model**.

Target:

> seconds/minutes rather than hours

Use:

- compact feature vectors
- shallow circuits
- small qubit count
- efficient simulator
- early stopping
- reasonable evaluation subset

Do not sacrifice data authenticity to improve speed.

---

# 16. LIVE SYSTEM LATENCY

Do not force the QML simulator into every live request.

Implement:

```text
                 AGENT
                   |
            QML supported?
              /                   NO         YES
            |            |
     classical only   QML branch
```

The preferred runtime strategy is:

```text
CLASSICAL RESULT
      |
      +----> operational response
      |
      +----> asynchronous QML research validation
```

The QML branch can run asynchronously when practical.

If QML exceeds a configured latency budget:

```text
QML research result unavailable
```

and keep the valid classical result.

Never fabricate a QML response.

---

# 17. QML CACHE

To reduce latency:

Implement caching for:

- already extracted feature vectors
- QML predictions for identical feature/model versions
- fitted PCA/normalization
- loaded QML model

Cache key should include appropriate version information.

Do not reuse stale QML outputs after the model/feature pipeline changes.

---

# 18. QML SHOULD NOT OVERRIDE CLASSICAL RESULTS

Default policy:

```text
Classical model
=
primary operational result

QML
=
experimental corroboration
```

If:

```text
Classical = Changed
QML = Changed
```

show:

```text
Agreement: YES
```

If:

```text
Classical = Changed
QML = Unchanged
```

show:

```text
Agreement: NO
Quantum branch requires review.
```

Do not silently replace the classical result.

---

# 19. AGREEMENT ANALYSIS

Create:

```text
backend/qml/comparison/agreement.py
```

Calculate a defined agreement measure.

At minimum:

- class agreement
- probability/confidence difference where meaningful

Optionally include a calibrated agreement score.

Document the formula.

Do not invent arbitrary values such as "87% agreement" without a reproducible calculation.

---

# 20. QML LEARNING / IMPROVEMENT LOOP

Do NOT implement naive self-training:

```text
QML prediction
 ↓
QML creates its own label
 ↓
QML retrains on its own prediction
```

This can reinforce mistakes.

Instead use a **verified learning loop**:

```text
Real sample
      ↓
Classical prediction
      ↓
Ground truth / benchmark verification
      ↓
Verified sample
      ↓
QML training buffer
      ↓
Periodic retraining
```

Best innovation:

```text
Classical ≠ QML
       ↓
Disagreement sample
       ↓
Ground-truth verification
       ↓
Hard-example buffer
       ↓
Periodic QML retraining
```

This makes QML improvement measurable and scientifically defensible.

---

# 21. QML RESEARCH BUFFER

Store:

```text
sample_id
dataset
task
feature_vector reference
ground_truth
classical_prediction
classical_confidence
qml_prediction
qml_confidence
agreement
verified
model_version
timestamp
```

Only verified real samples may enter the training buffer.

---

# 22. PERIODIC RETRAINING

Do not retrain after every user request.

Provide:

```bash
python backend/qml/training/train_vqc.py --retrain
```

The retraining process should:

```text
load verified data
 ↓
train
 ↓
evaluate
 ↓
compare to current QML checkpoint
 ↓
save new model only if justified
```

Never silently replace a better checkpoint with a worse one.

---

# 23. MODEL VERSIONING

Use:

```text
qml_change_v001.pt
qml_change_v002.pt
...
```

Each version should have associated:

```text
config.json
metrics.json
feature_pipeline.json
dataset manifest
```

---

# 24. EVALUATION

Create:

```text
backend/qml/training/evaluate_vqc.py
```

Mandatory classification metrics:

```text
Accuracy
Macro F1
Precision
Recall
Confusion Matrix
```

Where applicable also:

```text
ROC-AUC
```

Also record:

```text
training time
inference latency
number of qubits
circuit depth
simulator
shots
```

Evaluate only on held-out real samples.

---

# 25. CLASSICAL VS QML COMPARISON

Create:

```text
backend/qml/comparison/compare_classical_qml.py
```

It should compare the exact same test IDs.

Output:

```text
| Metric | Classical | QML | Delta |
|--------|-----------|-----|-------|
| Accuracy | ... | ... | ... |
| Macro F1 | ... | ... | ... |
| Precision | ... | ... | ... |
| Recall | ... | ... | ... |
| Latency | ... | ... | ... |
```

Also report:

```text
Agreement Rate
```

If QML is worse, report it honestly.

The project should demonstrate:

```text
today:
classical operational path

future:
quantum-ready path
```

not a false current quantum advantage claim.

---

# 26. LANGCHAIN INTEGRATION

The existing TRINETRA system uses LangChain.

Expose the QML branch as a controlled tool:

```text
QuantumValidationTool
```

The agent can decide whether QML is supported for the current task.

Possible supported tasks:

```text
change_analysis
optical_sar_fusion
```

depending on validated implementations.

Do NOT allow the LLM to generate arbitrary quantum code.

Tool parameters must be validated.

---

# 27. LANGFUSE INTEGRATION

The current project uses Langfuse observability.

Add QML spans to the existing trace:

```text
satquery_analysis_<id>

├── query_interpretation
├── classical_specialist
├── feature_extraction
├── qml_capability_check
├── qml_simulation
├── qml_prediction
├── agreement_analysis
└── final_synthesis
```

Record:

```text
qml_enabled
task
device
qubits
layers
qml_model_version
latency
prediction
confidence
agreement
```

Do not record chain-of-thought.

Only observable execution information should be shown.

---

# 28. FRONTEND / QUANTUM RESEARCH MODE

Add a clearly labeled UI section:

> **Quantum Research Mode**

Example:

```text
PRIMARY RESULT
Built-up area increased
Confidence: 89%

QUANTUM RESEARCH
PennyLane Simulator
Prediction: Increased
Confidence: 71%

Agreement:
✓ Classical and QML agree
```

If disagreement:

```text
⚠ Quantum branch disagrees with operational model
```

Do not visually imply that the QML result is the production answer.

---

# 29. QUANTUM DASHBOARD

Add a research/developer panel showing actual calculated values:

```text
Quantum Research Engine

Simulator: PennyLane
Device: <actual device>
Qubits: 6
Circuit Depth: 3
Model Version: qml_change_v001

Accuracy: ...
Macro F1: ...
Latency: ...
Classical Agreement: ...
```

Do not hardcode any metric.

---

# 30. FUTURE-HARDWARE ABSTRACTION

Design the code:

```text
QuantumBackend
     |
     +--- SimulatorBackend
     |
     +--- FutureHardwareBackend
```

The current implementation uses PennyLane simulation.

Future physical quantum hardware should be able to replace the backend without changing:

- the agent
- the tool interface
- the feature pipeline
- the evidence pipeline

Do not claim a specific future hardware timeline or quantum advantage.

---

# 31. 15–20 YEAR VISION

Document the architecture as:

```text
TODAY

Classical RS Specialists
        +
PennyLane Quantum Simulation
        ↓
Benchmark + Research
```

Future:

```text
Mature Quantum Hardware
        ↓
Same QML model/interface
        ↓
larger or more capable quantum execution
```

The innovation is the **quantum-ready architecture and accumulated research/training path**, not a claim that today's simulator beats heavy classical models.

---

# 32. QML CONFIGURATION

Create configurable settings such as:

```env
QML_ENABLED=true
QML_MODE=research
QML_TASKS=change_analysis,optical_sar_fusion

QML_DEVICE=default.qubit
QML_QUBITS=4
QML_LAYERS=2
QML_SHOTS=0
QML_TIMEOUT_SECONDS=2
```

Use current PennyLane semantics after fresh documentation research.

Do not hardcode these values.

---

# 33. ERROR HANDLING

If PennyLane/device/model is unavailable:

```text
Operational classical result remains available.
Quantum research result unavailable.
```

If simulation times out:

```text
QML timeout
```

Do not fabricate output.

A QML failure must not break the main SatQuery analysis.

---

# 34. PERFORMANCE MEASUREMENT

Measure separately:

```text
feature preparation
PCA/normalization
quantum simulation
post-processing
total QML latency
```

Compare:

```text
classical inference latency
QML simulation latency
```

Do not claim "quantum speedup" from a simulator.

---

# 35. RESEARCH EXPERIMENTS

Initially run only a small set of experiments:

```text
Experiment A
4 qubits / shallow circuit

Experiment B
6 qubits / shallow circuit

Experiment C
8 qubits / shallow circuit
```

Only continue if evidence shows value.

Record every experiment.

Do not spend excessive time on hyperparameter sweeps.

---

# 36. FILE STRUCTURE

Create:

```text
backend/qml/
├── TASK.md
├── README.md
├── config.py
├── datasets.py
├── feature_pipeline.py
├── preprocessing.py
├── models/
│   ├── __init__.py
│   └── vqc.py
├── backends/
│   ├── __init__.py
│   └── simulator.py
├── training/
│   ├── train_vqc.py
│   └── evaluate_vqc.py
├── comparison/
│   ├── compare_classical_qml.py
│   └── agreement.py
├── integration/
│   └── qml_service.py
└── results/
```

Adapt to the existing repository where equivalent components already exist.

Do not duplicate existing functionality unnecessarily.

---

# 37. CHECKPOINT OUTPUT

Every successful training run must save:

```text
best_model.pt
last_model.pt
config.json
metrics.json
feature_pipeline.json
dataset_manifest.json
```

Optional:

```text
confusion_matrix.png
training_curve.png
prediction_examples/
```

---

# 38. NO DATA LEAKAGE IN FEATURE REDUCTION

This is critical.

For PCA/normalization:

```text
TRAIN
 ↓
fit transform
 ↓
VALIDATION / TEST
apply only
```

Never fit PCA on the entire dataset before splitting.

Never fit normalization using test data.

---

# 39. INFERENCE

Create:

```text
backend/qml/integration/qml_service.py
```

It must:

```text
receive real feature vector
 ↓
load correct feature transform
 ↓
load correct checkpoint
 ↓
run PennyLane
 ↓
return prediction
confidence
metadata
```

Return structured output.

---

# 40. TRAINING COMMANDS

The IDE must NOT run these.

Provide exact Windows commands such as:

```powershell
python backend/qml/training/train_vqc.py `
  --dataset "D:\datasets\..." `
  --features "..." `
  --profile balanced
```

Evaluation:

```powershell
python backend/qml/training/evaluate_vqc.py `
  --checkpoint "backend/qml/results/qml_change_v001/best_model.pt" `
  --dataset "D:\datasets\..."
```

Comparison:

```powershell
python backend/qml/comparison/compare_classical_qml.py `
  --classical "..." `
  --qml "..."
```

Use commands that match the final repository.

Do not invent paths.

---

# 41. IDE MUST NOT RUN LONG JOBS

Do NOT:

- download datasets
- launch training
- run large quantum simulations
- consume the GPU for hours
- start background experiments

The IDE may perform safe/static checks.

I will run the actual commands.

---

# 42. README REQUIREMENTS

Update:

```text
backend/qml/README.md
```

Include:

- QML purpose
- selected algorithm
- why it was selected
- dataset
- dataset version
- feature pipeline
- number of qubits
- circuit architecture
- simulator
- training command
- evaluation command
- inference command
- checkpoint location
- classical baseline
- limitations
- latency strategy
- future hardware migration

---

# 43. FINAL ACCEPTANCE TEST

The implementation is complete only when the following are possible:

```text
REAL DATA
   ↓
CLASSICAL FEATURE EXTRACTION
   ↓
FEATURE REDUCTION
   ↓
CLASSICAL BASELINE
   ↓
QML TRAINING
   ↓
HELD-OUT TEST
   ↓
METRICS
   ↓
CLASSICAL vs QML
   ↓
CHECKPOINT
   ↓
LANGCHAIN TOOL
   ↓
LANGFUSE TRACE
   ↓
QUANTUM RESEARCH UI
```

And:

```text
[ ] ZERO synthetic data
[ ] ZERO fake labels
[ ] ZERO fake metrics
[ ] official split or documented deterministic split
[ ] no train/test leakage
[ ] PennyLane simulator works
[ ] QML checkpoint saved
[ ] evaluation saved
[ ] classical baseline saved
[ ] comparison saved
[ ] agreement metric saved
[ ] LangChain integration works
[ ] Langfuse trace works
[ ] QML failure does not break classical analysis
[ ] latency measured
[ ] future hardware abstraction documented
```

---

# 44. FINAL POSITIONING

The finished feature should be described as:

> **TRINETRA includes a quantum-ready research layer. The current operational intelligence remains powered by validated classical remote-sensing models, while a PennyLane-based QML branch operates on compact features extracted from real satellite data. The system compares classical and quantum predictions, tracks agreement and disagreement, records experiments, and creates a migration path from today's quantum simulation to future quantum hardware.**

Do not claim current quantum advantage unless the held-out benchmark proves it.

---

# 45. FINAL INSTRUCTION TO ANTIGRAVITY

Do this in order:

1. Inspect the current TRINETRA repository.
2. Create `backend/qml/TASK.md`.
3. Fresh-web-search current PennyLane/QML documentation and current algorithm choices.
4. Research and recommend the best QML algorithm for this project.
5. Identify a real dataset/task suitable for the first QML experiment.
6. Reuse existing real classical feature extraction where possible.
7. Implement the feature-reduction pipeline with zero leakage.
8. Implement the classical baseline.
9. Implement the PennyLane simulator backend.
10. Implement the QML model.
11. Implement training and evaluation.
12. Implement classical-vs-QML comparison.
13. Implement agreement/disagreement analysis.
14. Integrate QML as a controlled LangChain tool.
15. Add Langfuse tracing.
16. Add Quantum Research Mode to the UI.
17. Add checkpoint/version/report generation.
18. Update documentation.
19. Perform only static/safe verification.
20. **DO NOT run training or large simulations.**
21. Give me the exact commands to download/prepare datasets, train, evaluate, compare, infer, and integrate the checkpoint.

The implementation must be **real-data-only, scientifically honest, low-latency where possible, locally executable, reproducible, and future-ready for quantum hardware.**
