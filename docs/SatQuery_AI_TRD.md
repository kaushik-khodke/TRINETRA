# SatQuery AI — Technical Requirements Document (TRD)

**SIH 2026 — Problem Statement 26167**  
**Organization:** Indian Space Research Organisation (ISRO)  
**Department:** Department of Space / ISRO  
**Category:** Software  
**Theme:** Space Technology  
**Product:** SatQuery AI  
**Document Type:** Technical Requirements Document  
**Status:** Engineering Baseline

> **Source boundary:** This TRD is based primarily on the supplied SIH 2026 PS 26167 and the PRD derived from it. Requirements marked **MUST** are aligned with the mandatory/required scope in the PS. Architecture, technology choices, APIs, schemas, performance targets and implementation details marked **RECOMMENDED** are engineering decisions proposed for building the solution and are not claimed to be official ISRO requirements.

---

## 1. Purpose

SatQuery AI is an interactive, agentic vision-language system for analysing remote-sensing imagery through natural-language queries.

The technical system must:

1. Accept supported remote-sensing imagery.
2. Validate image count, modality, format, metadata and pair compatibility.
3. Interpret a natural-language query.
4. Identify the requested remote-sensing task.
5. Select the appropriate specialist model/tool(s).
6. Execute the selected workflow.
7. Combine textual and spatial outputs.
8. Return confidence information and visual evidence.
9. Expose an auditable execution summary.
10. Generate a downloadable report.

The architecture must support **single-image analysis**, **bi-temporal change analysis**, and **co-registered optical–SAR analysis**.

---

# 2. Technical Objectives

## 2.1 Primary objectives

- Build a modular remote-sensing AI backend.
- Adapt at least one visual/VLM component to remote-sensing data.
- Provide specialist tools instead of relying only on a generic LLM/VLM.
- Implement an agent/controller for automatic workflow selection.
- Preserve geospatial information throughout processing.
- Provide evidence-grounded outputs.
- Make inference reproducible and auditable.
- Prepare the system for public benchmark and ISRO/SAC evaluation.

## 2.2 Technical principles

The implementation should follow these principles:

- **Modularity:** models and tools should be independently replaceable.
- **Traceability:** every result should identify the workflow and models/tools used.
- **Evidence-first:** answers should be linked to image/spatial evidence where supported.
- **Fail-safe validation:** incompatible inputs must be rejected or clearly flagged.
- **Benchmarkability:** every major capability must have an evaluation path.
- **Extensibility:** new specialist models should be addable through a registry.
- **Geospatial integrity:** coordinates, transforms, resolution and relevant metadata must not be unnecessarily discarded.

---

# 3. System Scope

## 3.1 Supported input configurations

### A. Single image

Supported:

- Optical image
- Multispectral image
- SAR image

Required capabilities:

- Visual Question Answering
- One additional capability:
  - Captioning / scene description, OR
  - Text-guided region grounding

### B. Bi-temporal pair

Two spatially corresponding images acquired at different times.

Required:

- Change understanding
- Change description OR change-based VQA

Recommended:

- Spatial change map
- Change-region overlay
- Date-aware comparison

### C. Optical–SAR pair

Two co-registered observations of the same geographic area:

- Optical/multispectral
- SAR

Required:

- Joint information extraction
- Complementary cross-modal reasoning

---

# 4. Supported File Formats

## 4.1 Primary formats

The system MUST support:

- `.tif`
- `.tiff`
- GeoTIFF

## 4.2 Benchmark formats

PNG/JPEG MAY be accepted for prescribed public benchmark datasets.

## 4.3 File validation

The ingestion layer MUST validate:

- File extension
- File readability
- Raster dimensions
- Band count
- Data type
- CRS where available
- Geotransform
- Spatial bounds
- No-data information where available
- Modality metadata where available
- Pair compatibility

---

# 5. High-Level Architecture

```text
                         ┌───────────────────────────┐
                         │       Web / GUI           │
                         │ Upload + Query + Results  │
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │       API Gateway         │
                         │ Auth / Validation / Jobs  │
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │     Input Validator        │
                         │ Format / Metadata / Pair   │
                         │ Compatibility Checks       │
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │      Agent Controller      │
                         │ Query + Input Understanding│
                         │ Task Classification       │
                         │ Workflow Selection        │
                         └─────────────┬─────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
             ┌────────────┐    ┌──────────────┐   ┌──────────────┐
             │ Single RS  │    │ Change       │   │ Optical-SAR  │
             │ Specialists │    │ Specialist   │   │ Specialist   │
             └──────┬─────┘    └──────┬───────┘   └──────┬───────┘
                    │                 │                  │
                    └─────────────────┼──────────────────┘
                                      ▼
                         ┌───────────────────────────┐
                         │    Evidence & Fusion      │
                         │ Text + Spatial Outputs    │
                         │ Confidence / Validation   │
                         └─────────────┬─────────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         ▼                           ▼
                ┌─────────────────┐        ┌─────────────────┐
                │ Result Renderer │        │ Report Generator│
                │ Answer + Overlay│        │ PDF / HTML /    │
                │ + Trace         │        │ JSON            │
                └─────────────────┘        └─────────────────┘
```

---

# 6. Component Architecture

## 6.1 Frontend

### Responsibility

Provide the interactive application used by analysts and judges.

### Required capabilities

- Image upload
- Multiple-image upload for paired workflows
- Natural-language query input
- Input configuration display
- Validation status
- Task/workflow display
- Image viewer
- Paired image viewer
- Evidence overlays
- Answer display
- Confidence display
- Execution trace
- Report download

### Recommended stack

- React
- Next.js
- TypeScript
- Tailwind CSS
- MapLibre/OpenLayers/Leaflet for map visualization where appropriate

---

# 7. Backend API

## 7.1 Recommended stack

- Python
- FastAPI
- Pydantic
- Uvicorn/Gunicorn

The backend should expose a REST API and optionally WebSocket/SSE updates for long-running inference.

---

# 8. API Requirements

## 8.1 Upload endpoint

### `POST /api/v1/analyze`

Purpose:

Submit an analysis request.

### Multipart fields

```text
files[]
query
input_mode
optional metadata/configuration
```

### Supported input modes

```text
single
bi_temporal
optical_sar
```

### Response

```json
{
  "request_id": "uuid",
  "status": "accepted",
  "input_validation": {
    "valid": true,
    "mode": "bi_temporal"
  }
}
```

---

## 8.2 Job status

### `GET /api/v1/jobs/{request_id}`

Example:

```json
{
  "request_id": "uuid",
  "status": "completed",
  "progress": 100
}
```

Possible states:

```text
queued
validating
planning
executing
integrating
completed
failed
```

---

## 8.3 Result endpoint

### `GET /api/v1/results/{request_id}`

Example:

```json
{
  "request_id": "uuid",
  "task": "change_vqa",
  "answer": "Built-up area increased between the two observations.",
  "confidence": 0.87,
  "models": [
    {
      "name": "change-specialist",
      "version": "1.0"
    }
  ],
  "evidence": [
    {
      "type": "change_overlay",
      "artifact": "change_map.tif"
    }
  ],
  "execution_trace": {
    "validator": "input-validator-v1",
    "task": "change_vqa",
    "tools": [
      "change-specialist"
    ]
  }
}
```

---

# 9. Input Validation Service

## 9.1 Responsibilities

The validator runs before specialist inference.

It must inspect:

- Number of uploaded images
- File formats
- Raster readability
- Dimensions
- Channels/bands
- CRS
- Spatial transform
- Modality
- Pair relationship
- Temporal relationship when metadata is available

## 9.2 Validation result

```json
{
  "valid": true,
  "mode": "optical_sar",
  "images": [
    {
      "modality": "optical",
      "format": "GeoTIFF",
      "width": 2048,
      "height": 2048,
      "bands": 4
    },
    {
      "modality": "sar",
      "format": "GeoTIFF",
      "width": 2048,
      "height": 2048
    }
  ],
  "compatibility": {
    "spatial": true,
    "co_registered": true
  }
}
```

---

# 10. Geospatial Processing Layer

## 10.1 Responsibilities

The geospatial service should provide:

- GeoTIFF reading
- Metadata extraction
- CRS handling
- Spatial bounds
- Pixel-to-coordinate transformation
- Resampling
- Reprojection where justified
- Cropping/tiling
- Raster normalization
- Evidence overlay generation

## 10.2 Recommended libraries

- Rasterio
- GDAL
- NumPy
- PyProj
- Shapely where vector geometry is required

## 10.3 Important requirement

The system must avoid converting GeoTIFFs into ordinary images and permanently losing:

- CRS
- transform
- spatial extent
- resolution
- band information

The visualization representation may be converted for display, but the original geospatial context should remain available to the processing pipeline.

---

# 11. Remote-Sensing Adaptation Pipeline

## 11.1 Mandatory requirement

At least one visual or vision-language component MUST be fine-tuned or otherwise adapted using:

- BigEarthNet.txt, or
- Other open-source training data

## 11.2 Technical pipeline

```text
Dataset
   ↓
Dataset Validation
   ↓
Image/Text Pair Preparation
   ↓
Remote-Sensing Preprocessing
   ↓
Train/Validation Split
   ↓
Model Adaptation
   ↓
Evaluation
   ↓
Checkpoint
   ↓
Model Registry
   ↓
Inference Service
```

## 11.3 Required documentation

Maintain:

```text
model name
base model
dataset
dataset version
training configuration
adaptation method
epochs
learning rate
batch size
hardware
checkpoint
evaluation metrics
```

## 11.4 Model registry entry

```json
{
  "model_id": "rs-vlm-adapted-v1",
  "task": [
    "vqa",
    "captioning"
  ],
  "modalities": [
    "optical",
    "multispectral"
  ],
  "version": "1.0.0",
  "adaptation_dataset": "BigEarthNet",
  "status": "production"
}
```

---

# 12. Specialist Model Services

## 12.1 RS-VQA

### Input

```text
image
question
optional metadata
```

### Output

```json
{
  "answer": "...",
  "confidence": 0.91,
  "evidence": []
}
```

---

## 12.2 RS-Caption

### Input

```text
image
```

### Output

```json
{
  "caption": "...",
  "confidence": 0.84
}
```

---

## 12.3 RS-Grounding

### Input

```text
image
text_query
```

### Output

```json
{
  "regions": [
    {
      "bbox": [x1, y1, x2, y2],
      "score": 0.89
    }
  ]
}
```

The system MAY use masks instead of or in addition to bounding boxes when supported by the model.

---

# 13. Bi-Temporal Change Service

## 13.1 Input

```text
image_t1
image_t2
query
```

## 13.2 Processing

```text
T1
 ↓
Preprocess
 ↓
Spatial compatibility
 ↓
T2
 ↓
Preprocess
 ↓
Change model
 ↓
Change representation
 ↓
Change description / VQA
 ↓
Evidence generation
```

## 13.3 Output

```json
{
  "change_detected": true,
  "description": "Built-up development increased.",
  "confidence": 0.88,
  "regions": [
    {
      "type": "change",
      "geometry": {}
    }
  ]
}
```

## 13.4 Recommended evidence

- Side-by-side T1/T2
- Flicker comparison
- Difference visualization
- Change mask
- Bounding boxes
- Geographic overlay

---

# 14. Optical–SAR Fusion Service

## 14.1 Input

```text
optical_image
sar_image
query
```

## 14.2 Requirements

The service MUST use both modalities for joint analysis.

A valid workflow is:

```text
Optical
   ↓
Optical encoder ──┐
                  ├──> Fusion / Joint Reasoning ──> Answer
SAR               │
   ↓              │
SAR encoder ──────┘
```

## 14.3 Output

```json
{
  "answer": "...",
  "confidence": 0.86,
  "modalities_used": [
    "optical",
    "sar"
  ],
  "evidence": []
}
```

## 14.4 Engineering requirement

The UI should make it clear that the result used both sources.

---

# 15. Agent Controller

## 15.1 Responsibilities

The agent controller is the central orchestration layer.

It must:

1. Parse query.
2. Inspect input configuration.
3. Determine task.
4. Select specialist tool(s).
5. Execute tools.
6. Integrate outputs.
7. Produce confidence/evidence.
8. Produce execution trace.

## 15.2 Routing logic

Example:

```text
IF one image
    IF question → RS-VQA
    IF "describe" → RS-Caption
    IF "highlight/locate/find" → RS-Grounding

IF two temporal images
    → Change Specialist

IF optical + SAR
    → Optical-SAR Specialist
```

For more complex queries:

```text
Query
 ↓
Intent classification
 ↓
Input configuration
 ↓
Capability matching
 ↓
Tool selection
 ↓
Tool execution
 ↓
Result validation
 ↓
Result integration
```

## 15.3 Tool registry

Every tool should declare:

```json
{
  "tool_id": "rs_vqa",
  "version": "1.0",
  "supported_tasks": ["vqa"],
  "supported_modalities": ["optical", "multispectral", "sar"],
  "input_count": 1,
  "requires_geospatial": false,
  "output_types": ["text", "confidence", "evidence"]
}
```

---

# 16. Agent State Machine

```text
RECEIVED
   ↓
VALIDATING
   ↓
VALID
   ↓
CLASSIFYING
   ↓
PLANNING
   ↓
TOOL_SELECTED
   ↓
EXECUTING
   ↓
OUTPUT_VALIDATION
   ↓
INTEGRATION
   ↓
EVIDENCE_GENERATION
   ↓
COMPLETED
```

Failure path:

```text
ANY STATE
   ↓
ERROR
   ↓
USER-FACING ERROR + TRACE
```

---

# 17. Execution Trace

The execution trace is an important technical requirement.

## 17.1 Trace schema

```json
{
  "request_id": "uuid",
  "task": "optical_sar_analysis",
  "input_mode": "optical_sar",
  "tools": [
    {
      "name": "input_validator",
      "version": "1.0"
    },
    {
      "name": "optical_sar_specialist",
      "version": "1.0"
    }
  ],
  "parameters": {
    "confidence_threshold": 0.7
  },
  "status": "completed",
  "duration_ms": 8400
}
```

## 17.2 Do not expose

Internal chain-of-thought is not required.

The application should expose only useful execution information:

- Selected task
- Models/tools
- Key permitted parameters
- Outputs
- Status
- Confidence

---

# 18. Evidence System

## 18.1 Evidence types

The evidence engine should support:

- Bounding boxes
- Segmentation masks
- Change maps
- Region highlights
- Image crops
- Side-by-side comparison
- Modality-specific evidence

## 18.2 Evidence object

```json
{
  "type": "bbox",
  "image_id": "image_01",
  "coordinates": [120, 80, 540, 460],
  "score": 0.91,
  "label": "water"
}
```

## 18.3 Geospatial evidence

Where possible, evidence should retain:

- CRS
- Geographic coordinates
- Raster transform
- Original image reference

---

# 19. Confidence System

## 19.1 Requirement

Every major analysis result should provide confidence information.

## 19.2 Confidence representation

Recommended:

```json
{
  "score": 0.87,
  "level": "high",
  "method": "model_probability"
}
```

Levels:

```text
HIGH
MEDIUM
LOW
```

## 19.3 Low-confidence behaviour

For low-confidence outputs, the UI should:

- Clearly flag uncertainty.
- Avoid presenting speculative information as fact.
- Show available evidence.
- Optionally recommend a narrower query or another supported workflow.

---

# 20. Result Integration Layer

The integration layer receives outputs from specialist tools.

Example:

```text
VQA output
+
Grounding output
+
Change output
+
Metadata
+
Confidence
        ↓
Result Integrator
        ↓
Unified Result
```

Responsibilities:

- Normalize outputs.
- Validate output schema.
- Resolve evidence references.
- Calculate/aggregate confidence where applicable.
- Produce final response object.
- Build execution trace.

---

# 21. Report Generation

## 21.1 Required report contents

Recommended report structure:

```text
SatQuery AI Analysis Report

1. Request
2. User Query
3. Input Images
4. Image Metadata
5. Detected Input Configuration
6. Selected Task
7. Models / Tools Used
8. Key Parameters
9. Analysis Result
10. Confidence
11. Visual Evidence
12. Spatial Evidence
13. Execution Trace
14. Timestamp
```

## 21.2 Formats

Recommended:

- PDF
- HTML
- JSON

---

# 22. Database / Persistence Requirements

A lightweight database should store:

### Analysis request

```text
request_id
created_at
query
input_mode
status
```

### Input image

```text
image_id
request_id
filename
modality
format
width
height
bands
crs
resolution
acquisition_time
```

### Execution

```text
execution_id
request_id
task
tool
model
version
parameters
status
duration
```

### Result

```text
result_id
request_id
answer
confidence
evidence_reference
```

SQLite is suitable for an initial SIH implementation; PostgreSQL is recommended for a larger deployment.

---

# 23. Storage Architecture

Recommended:

```text
Object Storage
├── uploads/
├── processed/
├── evidence/
├── change_maps/
├── reports/
└── models/

Database
├── requests
├── images
├── executions
├── results
└── model_registry
```

For a local/demo deployment, filesystem storage can replace object storage.

---

# 24. Model Serving

## 24.1 Recommended approach

Separate inference from API orchestration:

```text
FastAPI
   ↓
Agent
   ↓
Model Service
   ↓
GPU
```

Possible implementations:

- PyTorch
- Transformers
- ONNX Runtime
- TorchServe or custom inference service

The exact model should be selected after benchmarking candidate remote-sensing models.

---

# 25. Model Registry

Each production model must have:

```text
model_id
name
version
task
modalities
input_constraints
output_schema
checkpoint
preprocessing
postprocessing
hardware_requirements
evaluation_metrics
status
```

Example:

```yaml
model_id: rs-vqa-001
version: 1.0.0
task:
  - vqa
modalities:
  - optical
input:
  count: 1
output:
  - text
  - confidence
status: production
```

---

# 26. Preprocessing Pipeline

## 26.1 Optical/multispectral

Potential stages:

```text
GeoTIFF
 ↓
Read raster
 ↓
Band selection
 ↓
NoData handling
 ↓
Normalization
 ↓
Resize / tile
 ↓
Model preprocessing
```

## 26.2 SAR

Potential stages:

```text
SAR GeoTIFF
 ↓
Read raster
 ↓
NoData handling
 ↓
SAR-specific normalization
 ↓
Resize / tile
 ↓
Model preprocessing
```

The precise preprocessing must match the selected specialist model and its documented training procedure.

---

# 27. Large Image Strategy

Satellite images may exceed model input dimensions.

The system should support:

- Tiling
- Sliding windows
- Overlap
- Region-of-interest cropping
- Multi-tile inference
- Result merging

Example:

```text
Large Raster
     ↓
┌─────┬─────┬─────┐
│ T1  │ T2  │ T3  │
├─────┼─────┼─────┤
│ T4  │ T5  │ T6  │
└─────┴─────┴─────┘
     ↓
Parallel inference
     ↓
Spatial result merging
```

---

# 28. Security Requirements

Even though the PS is primarily an AI application, the deployed system should implement:

- File type validation
- File size limits
- Safe filename handling
- Temporary-file cleanup
- API input validation
- No execution of uploaded files
- Access control for administrative/model-management endpoints
- Secure secrets management
- Error messages without sensitive filesystem details

---

# 29. Observability

The system should log:

```text
request_id
timestamp
task
model
tool
execution status
duration
errors
confidence
```

Logs should make it possible to diagnose:

- Incorrect routing
- Model failures
- Invalid inputs
- Slow inference
- Failed report generation
- Evidence-generation errors

---

# 30. Error Handling

## 30.1 Error categories

```text
INVALID_FILE
UNSUPPORTED_FORMAT
INVALID_MODALITY
INVALID_IMAGE_COUNT
INCOMPATIBLE_PAIR
MISSING_METADATA
MODEL_UNAVAILABLE
MODEL_INFERENCE_ERROR
LOW_CONFIDENCE
EVIDENCE_GENERATION_ERROR
REPORT_GENERATION_ERROR
INTERNAL_ERROR
```

## 30.2 User-facing error

Example:

```text
The uploaded images cannot be used for optical–SAR analysis.

Reason:
The two images could not be verified as spatially compatible.

Please upload a co-registered optical and SAR pair.
```

---

# 31. Testing Strategy

## 31.1 Unit testing

Test:

- File validation
- Metadata parsing
- Modality detection
- Tool registry
- Agent routing
- Output schemas
- Confidence handling
- Report generation

## 31.2 Integration testing

Test:

```text
Upload
 → Validation
 → Agent
 → Model
 → Evidence
 → Result
 → Report
```

## 31.3 End-to-end testing

Mandatory scenarios:

- Single optical VQA
- Single SAR VQA
- Captioning
- Grounding if implemented
- Bi-temporal change
- Optical–SAR analysis
- Invalid file
- Invalid image pair
- Low-confidence response
- Report generation

---

# 32. Benchmark Evaluation Architecture

```text
Benchmark Dataset
       ↓
Dataset Adapter
       ↓
Preprocessing
       ↓
SatQuery AI
       ↓
Task Output
       ↓
Metric Evaluator
       ↓
Results
       ↓
Evaluation Report
```

## 32.1 Dataset readiness

The implementation should provide adapters/runners for:

- BigEarthNet.txt
- VRSBench
- RSVQA
- CDVQA

The exact metrics should follow the prescribed evaluation protocol for each benchmark.

---

# 33. ISRO/SAC Evaluation Readiness

The PS states that the ISRO/SAC evaluation set will contain:

- Pre-georeferenced imagery
- Co-registered Cartosat-2S optical imagery
- RISAT SAR imagery
- Task-specific reference answers, labels, bounding boxes or masks as applicable

The annotations will not be disclosed.

Therefore the system must:

- Work without hidden labels.
- Handle optical–SAR pairs robustly.
- Preserve geospatial information.
- Generalize beyond demo examples.
- Avoid hard-coded responses.
- Keep preprocessing configurable.
- Keep specialist models replaceable.

---

# 34. Performance Requirements

The PS does not specify fixed latency targets.

Recommended engineering targets for the SIH demo:

| Operation | Recommended UX target |
|---|---:|
| Upload validation | < 5 sec for normal demo files |
| Query classification | < 2 sec |
| Simple VQA after model warm-up | < 15 sec |
| Captioning | < 15 sec |
| Grounding | < 20 sec |
| Change analysis | < 60 sec |
| Optical–SAR analysis | < 60 sec |
| Report generation | < 10 sec |

These are **engineering targets**, not official PS limits.

For long inference, show:

```text
Validating → Planning → Running model → Generating evidence → Complete
```

---

# 35. Deployment Architecture

## 35.1 Recommended SIH deployment

```text
                Internet / LAN
                     │
                     ▼
               Reverse Proxy
                     │
             ┌───────┴────────┐
             ▼                ▼
         Frontend          Backend API
                              │
                         Agent Controller
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
         VQA Service     Change Service   Optical-SAR
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                           GPU Node
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                Storage             Database
```

## 35.2 Containerization

Recommended services:

```text
frontend
backend
agent
model-vqa
model-change
model-optical-sar
worker
database
storage
```

For a constrained SIH deployment, multiple services may be combined into fewer containers.

---

# 36. Recommended Repository Structure

```text
satquery-ai/
│
├── apps/
│   ├── frontend/
│   └── backend/
│
├── agent/
│   ├── controller.py
│   ├── planner.py
│   ├── router.py
│   ├── registry.py
│   └── trace.py
│
├── services/
│   ├── validator/
│   ├── vqa/
│   ├── captioning/
│   ├── grounding/
│   ├── change/
│   ├── optical_sar/
│   ├── evidence/
│   └── reports/
│
├── models/
│   ├── adapters/
│   ├── checkpoints/
│   └── configs/
│
├── geospatial/
│   ├── raster.py
│   ├── metadata.py
│   ├── projection.py
│   ├── tiling.py
│   └── overlays.py
│
├── datasets/
│   ├── bigearthnet/
│   ├── vrsbench/
│   ├── rsvqa/
│   └── cdvqa/
│
├── evaluation/
│   ├── runners/
│   ├── metrics/
│   └── reports/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/
│
├── scripts/
│
├── docker/
│
├── requirements/
│
├── docker-compose.yml
└── README.md
```

---

# 37. Configuration Management

Avoid hard-coding model and workflow configuration.

Recommended:

```yaml
environment: production

models:
  vqa:
    id: rs-vqa-001
    version: 1.0.0

  captioning:
    id: rs-caption-001
    version: 1.0.0

  grounding:
    id: rs-ground-001
    version: 1.0.0

  change:
    id: rs-change-001
    version: 1.0.0

  optical_sar:
    id: optical-sar-001
    version: 1.0.0
```

---

# 38. Observability Dashboard

Recommended internal dashboard:

```text
Requests
├── Total
├── Successful
├── Failed
└── Low confidence

Tasks
├── VQA
├── Caption
├── Grounding
├── Change
└── Optical-SAR

Models
├── Calls
├── Latency
└── Errors
```

This is optional for the SIH demo but useful during development.

---

# 39. Acceptance Criteria

## AC-01 Remote-sensing adaptation

**Given:** adapted model  
**When:** user runs a supported workflow  
**Then:** the adapted component is actually invoked.

## AC-02 VQA

**Given:** single supported image  
**When:** user asks a visual question  
**Then:** system returns answer + confidence.

## AC-03 Additional single-image capability

**Given:** single image  
**When:** user asks for description/grounding  
**Then:** selected specialist executes successfully.

## AC-04 Change

**Given:** two corresponding temporal images  
**When:** user asks what changed  
**Then:** system returns change description or change-VQA answer.

## AC-05 Optical–SAR

**Given:** co-registered optical and SAR pair  
**When:** user asks a joint analysis question  
**Then:** system uses both modalities.

## AC-06 Agent

**Given:** different queries/input configurations  
**When:** user submits analysis  
**Then:** controller selects appropriate specialist workflow.

## AC-07 Validation

**Given:** incompatible input  
**When:** user uploads it  
**Then:** system rejects/flags it before invalid specialist execution.

## AC-08 Evidence

**Given:** specialist supports spatial evidence  
**When:** analysis completes  
**Then:** UI displays the evidence.

## AC-09 Audit trace

**Given:** completed request  
**When:** user opens execution details  
**Then:** selected task, model/tool names and key parameters are visible.

## AC-10 Report

**Given:** completed request  
**When:** user selects export  
**Then:** downloadable report is generated.

---

# 40. Critical Technical Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Generic VLM performs poorly on satellite data | High | Remote-sensing adaptation + specialist models |
| Agent only appears agentic | High | Real registry-based routing and execution trace |
| SAR preprocessing mismatch | High | Model-specific preprocessing and validation |
| GeoTIFF metadata lost | High | Dedicated geospatial processing layer |
| Large images exceed model context | High | Tiling/ROI strategy |
| Change model produces weak localization | High | Evidence overlays + confidence |
| Optical–SAR alignment errors | Critical | Compatibility/co-registration checks |
| GPU memory limits | High | Quantization, tiling, model serving optimization |
| Hidden evaluation annotations unavailable | Critical | Build generalized inference, not hard-coded examples |
| Model latency too high | Medium | Warm models, caching, optimized inference |

---

# 41. Technical Definition of Done

The technical implementation is complete when:

- [ ] Web/GUI is functional.
- [ ] GeoTIFF/TIFF ingestion works.
- [ ] Single optical/multispectral image works.
- [ ] Single SAR image works.
- [ ] Bi-temporal pair works.
- [ ] Optical–SAR pair works.
- [ ] Input validation is implemented.
- [ ] At least one remote-sensing visual/VLM component is adapted.
- [ ] Single-image VQA works.
- [ ] Captioning or grounding works.
- [ ] Change description/change-VQA works.
- [ ] Optical–SAR joint analysis works.
- [ ] Agent automatically routes requests.
- [ ] Specialist model registry works.
- [ ] Evidence rendering works.
- [ ] Confidence information is returned.
- [ ] Execution trace is visible.
- [ ] Downloadable report works.
- [ ] Unit tests pass.
- [ ] Integration tests pass.
- [ ] End-to-end demo passes.
- [ ] Benchmark evaluation pipeline exists.
- [ ] Clean deployment works.

---

# 42. Recommended SIH Demo Architecture

For the final demonstration, optimize for clarity rather than showing every internal implementation detail.

### Demo flow

```text
1. Upload image
       ↓
2. Validation
       ↓
3. Enter natural-language query
       ↓
4. Agent identifies task
       ↓
5. Specialist model executes
       ↓
6. Evidence generated
       ↓
7. Answer + confidence
       ↓
8. Execution trace
       ↓
9. Download report
```

Then repeat using:

```text
Single Image
      ↓
Bi-Temporal Pair
      ↓
Optical + SAR Pair
```

This demonstrates the breadth of the required system in a short time.

---

# 43. Priority Classification

## P0 — Must work

- Remote-sensing adaptation
- Single-image VQA
- Additional single-image task
- Bi-temporal change
- Optical–SAR analysis
- Agentic routing
- Input validation
- Evidence
- Confidence
- Execution trace
- GeoTIFF/TIFF support

## P1 — Strongly recommended

- Both captioning and grounding
- Change maps
- Rich geospatial overlays
- Benchmark automation
- PDF reports
- Model registry UI
- Detailed evaluation dashboard

## P2 — Optional enhancement

- Advanced GIS tools
- User accounts
- Collaboration
- Large-scale cloud deployment
- Historical analysis
- Automated dataset ingestion
- Advanced analytics dashboards

---

# 44. Final Technical Blueprint

The final product should implement the following technical chain:

```text
                         USER
                           │
                           ▼
                 Natural Language Query
                           │
                           ▼
                 ┌───────────────────┐
                 │   Web Application  │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Input Validator    │
                 │ GeoTIFF / Metadata │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Agent Controller   │
                 │ Intent + Routing   │
                 └─────────┬─────────┘
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
      Single Image    Bi-Temporal       Optical + SAR
          │                │                 │
          ▼                ▼                 ▼
     VQA/Caption/      Change Model     Fusion Model
      Grounding             │                 │
          │                │                 │
          └────────────────┼─────────────────┘
                           ▼
                 ┌───────────────────┐
                 │ Result Integration│
                 └─────────┬─────────┘
                           │
              ┌────────────┼─────────────┐
              ▼            ▼             ▼
           Answer       Evidence      Confidence
              │            │             │
              └────────────┼─────────────┘
                           ▼
                 ┌───────────────────┐
                 │ Execution Summary │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Report Generator  │
                 └───────────────────┘
```

---

# 45. Final Engineering Principle

**SatQuery AI should not be implemented as “LLM + satellite image.”**

The core technical product should be:

> **Remote-sensing-adapted models + specialist tools + intelligent orchestration + geospatial processing + evidence + confidence + auditability.**

The agent is the coordinator, not the only model.

The specialist models provide domain capability.

The geospatial layer preserves spatial meaning.

The evidence layer makes results inspectable.

The execution trace makes the system auditable.

Together, these components form the technical implementation required to satisfy the SatQuery AI problem statement.

---

# 46. Exploration & Shanetra Architecture (Phase 1 & Phase 2 Verified Implementation)

The TRINETRA system integrates an isolated Earth-observation exploration workstation at `/explore` without altering existing `/analysis` workflows.

### 46.1 Dual-Renderer Controlled Architecture
* **2D Vector/Raster Map**: Powered by MapLibre GL JS with watermark-free Esri Dark Gray canvas tiles and dynamic Web Mercator raster tile layers.
* **3D Earth Globe**: Powered by CesiumJS with `requestRenderMode` conservatism, dynamic client-side module loading, and multi-layer imagery providers.
* **Centralized Controller & Command Bus**: Unified `GlobeController` and `GlobeCommandBus` preventing direct map state mutations and eliminating memory leaks.

### 46.2 Backend Exploration Engine (`backend/exploration/`)
* **Local Provider**: In-memory metadata index of curated GeoTIFF fixtures, supporting spatial bounding-box searches and deterministic local testing.
* **STAC Provider**: SpatioTemporal Asset Catalog client for Copernicus Data Space (`https://stac.dataspace.copernicus.eu/v1/`) with normalized item parsing, request field minimization, and explicit 5s/10s connect/read timeouts.
* **Windowed Raster Service**: Extracts pixel windows (`rasterio.windows.from_bounds`) directly from source files, preventing massive raster loads into memory.
* **Slippy Tile Service**: Dynamically generates 256×256 PNG tiles at `/api/v1/explore/tiles/{layer_id}/{z}/{x}/{y}.png` with ETag and Cache-Control headers.
* **Bounded LRU/TTL Cache**: Thread-safe in-memory cache for tile bytes (1000 items, 900s TTL), raster metadata (300 items, 3600s TTL), and STAC queries (100 items, 300s TTL).
* **Layer Policy Engine**: Security and rendering governance enforcing:
  - `MAX_ACTIVE_BASE_LAYERS = 1`
  - `MAX_ACTIVE_IMAGERY_LAYERS = 2`
  - `MAX_ACTIVE_ANALYTICAL_LAYERS = 4`
  - Zoom gating and strict path traversal protection (`^[a-zA-Z0-9_\-\.:]{1,128}$`).

### 46.3 Verified Performance Baseline (`outputs/performance/explore_phase2_tiles.json`)
* Cold tile generation latency: ~20.48ms
* Cached tile latency: ~0.0036ms (p50: 0.0033ms, p95: 0.0036ms)
* Cache hit ratio: 99.0%
* All 56 regression and unit tests passing 100%.

---

# 47. Phase 3 Natural-Language Exploration Engine & AI Command Gateway

Phase 3 introduces the first operational natural-language command capability to `/explore`, establishing a strictly validated, typed command gateway between local LLMs (Ollama) and the map/globe renderers.

### 47.1 AI Command Gateway Architecture
* **Strict Command Boundary**: The LLM outputs an abstract `ExploreCommandPlan` and never has direct access to DOM or renderer APIs (`map.flyTo`, `viewer.camera`).
* **Fast-Path Deterministic Parser (`fallback_parser.py`)**: Sub-millisecond string and regex parser (`< 0.02ms` p50) that executes simple, predictable operations (`reset`, `zoom in`, `zoom out`, `show/hide boundaries`) while completely bypassing GPU inference.
* **Two-Stage Model Inference**:
  1. **Stage A: Fast Intent Router (`fast_router`)**: Classifies query into `navigation`, `layer_control`, `dataset_search`, `view_control`, `reset`, `combined`, or `unsupported`. Deferrals for deep scientific analysis (VQA, change detection, NDVI) are safely filtered out before planning.
  2. **Stage B: Structured Command Planner (`planner`)**: Emits typed command plans via Ollama's native JSON Schema-constrained format (`OllamaProvider.generate_structured_native`) with temperature 0.0.
* **Discriminated Command Models (`ai_schemas.py`)**:
  - `FLY_TO`, `ZOOM_IN`, `ZOOM_OUT`, `RESET_VIEW`
  - `SHOW_LAYER`, `HIDE_LAYER`, `SET_LAYER_OPACITY`, `REMOVE_LAYER`
  - `SEARCH_DATASETS`, `ADD_DATASET_LAYER`
  - Maximum limit enforced: `MAX_AI_COMMANDS_PER_REQUEST = 6`.
* **Zero Coordinate / Dataset Hallucination**:
  - Places are resolved via offline gazetteer and deterministic coordinate parser (`GeoResolver`), with LRU memory caching (bounded at 256 items).
  - Ambiguous place names (`Springfield`) trigger `EXPLORE_LOCATION_AMBIGUOUS` and halt navigation.
  - Dataset discovery delegates to the Phase 2 `DataBroker`; the model cannot fabricate observation IDs.
* **Sequential Execution & Idempotency (`command_executor.py`)**:
  - Duplicate layer activations produce `no_op`.
  - Partial failure handling halts execution at failing command, marking subsequent commands `cancelled`.
  - Compact `state_patch` and deterministic user summaries (no redundant 3rd LLM call).
* **Workstation UI Components**:
  - `QueryBar.tsx`: Floating tactical query bar with `AbortController` request cancellation.
  - `QuerySuggestions.tsx`: Contextual suggestion chips based on active layer state.
  - `CommandActivity.tsx`: Live execution progress HUD.
  - `AIStatus.tsx`: Telemetry badge reporting local model readiness.

### 47.2 Verified Phase 3 Performance Baseline (`outputs/performance/explore_phase3_ai.json`)
* Fast-Path p50 latency: **0.0151 ms** (Target: < 0.5 ms)
* Fast-Path p95 latency: **0.0210 ms** (Target: < 1.0 ms)
* Mocked AI Path p50 latency: **0.215 ms**
* Prompt estimated token budget: **178 tokens** (Bounded < 1000 tokens)
* Complete Test Suite: **91 exploration tests + 21 system tests = 112 passed 100%**.

---

# 48. Phase 4 Temporal Exploration, AOI Selection & Observation Comparison Architecture

Phase 4 completes the multi-temporal discovery, geographic selection, and comparative observation foundations of the `/explore` workstation, enabling multi-temporal satellite querying and visual side-by-side analysis without triggering full raster downloads or modifying the `/analysis` workflows.

### 48.1 Server-Authoritative Area of Interest (AOI) Governance (`backend/exploration/aoi/`)
* **Strict Policy Engine (`validator.py`, `AOIPolicy`)**:
  - Validates all user and AI polygons server-side prior to query execution.
  - Limits maximum surface area to **250,000 km²** (`exploration_max_aoi_area_km2`).
  - Limits vertex count to **500 vertices** (`exploration_max_aoi_vertices`).
  - Rejects NaN/Inf coordinates, self-intersections, and unclosed polygon rings.
* **Geodesic Calculations (`geometry.py`)**:
  - Uses `pyproj` local Lambert Azimuthal Equal Area (`laea`) projections centered on polygon centroids for sub-meter area estimation.
  - Normalizes antimeridian crossings into `[-180, 180]` longitude bounds.
  - Computes deterministic SHA-256 geometry hashes (`geometry_hash`) to power stable query caching across sessions.
* **Adaptive Douglas-Peucker Simplification (`simplifier.py`)**:
  - Downsamples overly complex vector geometries while preserving topological validity (`shapely.simplify(preserve_topology=True)`).

### 48.2 Multi-Temporal Observation Discovery (`backend/exploration/temporal/`)
* **Capability-Aware STAC Client (`stac_provider.py`)**:
  - Discovers Sentinel-2 and Sentinel-1 acquisitions from the Copernicus Data Space (`https://stac.dataspace.copernicus.eu/v1/`).
  - Employs spatial intersection queries (`intersects`), temporal interval spans (`datetime`), and cloud-cover filtering (`query: {"eo:cloud_cover": {"lte": max}}`).
  - Enforces strict 5s connect and 10s read timeouts with graceful offline fallback.
* **Bounded Normalization (`normalizer.py`)**:
  - Strips extensive STAC metadata payloads down to compact, lightweight `ObservationSummary` models (ID, platform, datetime, cloud cover %, bbox, thumbnail URL, asset keys).
  - Protects browser memory from bloating across long temporal sequence queries.
* **Deterministic Sorting & Resolving (`sorter.py`, `resolver.py`)**:
  - Sorts acquisitions deterministically (`datetime_desc`, `datetime_asc`, `cloud_asc`) with duplicate identification across providers.
  - Exposes natural-language resolution helpers (`resolve_latest`, `resolve_previous`, `resolve_pair`).
* **Multi-Dimensional Temporal Cache (`cache.py`)**:
  - Dedicated `temporal_search_cache` keyed by `(aoi_hash, start_dt, end_dt, collections, cloud_max, sort, limit)`.
  - Cache hits execute in **~15ms** (a **261x speedup** over live external catalog discovery).

### 48.3 Dual-Observation Comparison Subsystem (`backend/exploration/comparison/`)
* **Pair Compatibility Engine (`validator.py`, `ComparisonValidator`)**:
  - Enforces self-comparison prevention ($A \neq B$).
  - Calculates temporal delta in days between acquisition timestamps.
  - Computes spatial overlap percentage via Shapely bounding-box intersection; rejects pairs with $< 10\%$ overlap as disjoint footprints, and flags partial overlap ($10\% - 50\%$) with warnings.
* **Comparison Modes & Controls**:
  - **Split View (`split`)**: Real-time draggable vertical divider with dual synchronized map panes.
  - **Side-by-Side (`side_by_side`)**: Simultaneous dual-viewport layout.
  - **Opacity Blend (`opacity`)**: Alpha blending slider for layer B overlay.
* **Loop-Free Camera Synchronization (`camera-sync.ts`, `cameraSyncBus`)**:
  - Token-based origin tracking (`view-a`, `view-b`, `system`) preventing infinite feedback loops during interactive panning and zooming.

### 48.4 AI Gateway Temporal Extensions (`ai_schemas.py`, `command_validator.py`, `command_executor.py`)
* Five new typed, validated explore commands:
  - `SET_AOI`: Establishes validated polygon boundary.
  - `CLEAR_AOI`: Clears active AOI.
  - `SET_DATE_RANGE`: Constrains temporal search window.
  - `SELECT_OBSERVATION`: Selects observation for inspection or primary slot.
  - `COMPARE_OBSERVATIONS`: Initiates dual comparison mode with validation.
* Zero URL or coordinate hallucination: All commands validate against catalog and policy boundaries.

### 48.5 Verified Phase 4 Performance Baseline (`outputs/performance/explore_phase4_temporal.json`)
* AOI Geodesic Validation Latency: **41.44 ms**
* Full Exploration Backend Test Suite: **120 tests passing 100%**.

---

## 49. Phase 5: EO Analytical Intelligence Engine Architecture

### 49.1 Core Analytical Principle
> **"Models generate evidence. The language model explains evidence."**

The TRINETRA EO Analytical Intelligence Engine (`backend/analysis_engine/`) upgrades `/explore` from a visualization viewer into an authentic Earth-observation analytical intelligence workstation. The LLM is strictly prohibited from declaring conceptual observations (e.g., "construction occurred") without a measurable, model-backed, mathematical evidence trail.

### 49.2 Three Specialized Analytical Modes
1. **`BI_TEMPORAL` Mode**:
   - Compares two observations from the same/similar optical modality across time.
   - Sub-pipeline: Windowed spatial alignment $\to$ Radiometric surface reflectance normalization $\to$ Differential Siamese feature fusion (`change_specialist_model/model.pt`) $\to$ Continuous change probability map $\to$ Connected-component vector region extraction ($>20\text{px}$ threshold) $\to$ Numerical area/pixel statistics ($m^2$, hectares, change ratio) $\to$ Mathematical consistency gating.
2. **`SAR_OPTICAL` Mode**:
   - Cross-modal joint reasoning combining microwave radar (Sentinel-1 SAR) and multispectral optical (Sentinel-2).
   - Sub-pipeline: Modality-aware preprocessing (amplitude to dB conversion for SAR, surface reflectance scaling for Optical) $\to$ Coregistration verification $\to$ Backscatter delta and spectral index fusion $\to$ Independent per-modality support scores $\to$ Cross-modal agreement matrix.
3. **`SINGLE_IMAGE` Mode**:
   - Single acquisition spatial inspection and feature grounding.
   - Sub-pipeline: Windowed bounds extraction $\to$ Text-guided region grounding (`rs_ground`) $\to$ Scene captioning (`rs_caption`) $\to$ Visual Question Answering (`rs_vqa`) $\to$ Geo-referenced bounding box validation.

### 49.3 Subsystem Architecture & Directory Structure
```text
backend/analysis_engine/
├── __init__.py
├── models.py                   # AnalysisRun, AnalysisProgress, AnalysisArtifact, RunStatus
├── schemas.py                  # Pydantic schemas (AnalysisRequest, AnalysisResult, AnalysisFinding)
├── errors.py                   # Structured error taxonomy (Input, Data, Preprocessing, Model, Resource, Reasoning)
├── context.py                  # Raw numerical context decoupled from prompt strings
├── provenance.py               # Deterministic SHA-256 provenance tracking (processing_hash)
├── planner.py                  # Deterministic intent routing & observation assignment
├── router.py                   # Execution routing to specialist services
├── service.py                  # Async queue, semaphore concurrency control, lifecycle manager
├── preprocessing/              # Windowed raster bounds, reprojection, grid alignment, radiometric norm
├── change/                     # Bi-temporal change map, connected components, area calculation
├── sar_optical/                # SAR dB conversion, spectral indices, cross-modal support scoring
├── single_image/               # VQA, captioning, region grounding coordinate validation
├── evidence/                   # EvidencePack, mathematical ranking, statistics, consistency validator
├── reasoning/                  # Ollama native JSON schema constrained reasoning + deterministic fallback
├── reports/                    # Vector GeoJSON, provenance manifest, annotated preview generation
└── graph/                      # Compiled LangGraph StateGraph workflow
```

### 49.4 Strict Architectural Constraints Enforced
- **Untouched Guided Workflow**: Strictly zero modifications to `/analysis` guided workflow or `langgraph_orchestrator.py`.
- **Windowed Raster Reading**: All raster ingestion is strictly windowed via `rasterio.windows.Window` bounds calculations. Full multi-gigabyte rasters are never loaded in their entirety into memory.
- **Strict Concurrency Limits**: `analysis_max_concurrent_jobs = 2` governed by `asyncio.Semaphore` and mutex locking to prevent GPU/CPU OOM.
- **Deterministic Provenance**: SHA-256 hash computed over model weights, software versions, input raster fingerprints, and preprocessing hyperparameters.
- **Structured LLM Output**: Local Ollama model (`llama3.2`) is constrained by native JSON schema (`temperature=0.0`, compact token-budgeted prompts).
- **Graceful Deterministic Fallback**: In the event Ollama is offline or unavailable, the engine generates 100% verified, hallucination-free analytical reports directly from raw evidence tokens.

### 49.5 Test & Build Verification Baseline
- **Analytical Engine Backend Tests**: **32 tests passing 100%** (`backend/tests/analysis_engine/`).
- **Exploration Backend Tests**: **120 tests passing 100%** (`backend/tests/exploration/`).
- **End-to-End Pipeline Scripts**: All 6 verification gates passed (`scripts/test_explore_analysis_flow.py`, `scripts/test_change_pipeline.py`, `scripts/test_sar_optical_pipeline.py`, `scripts/test_single_image_pipeline.py`).
- **Frontend Architecture**: TypeScript strict validation clean (**0 errors**), Turbopack build optimized (**0 warnings**).

---

## 50. Phase 6: Semantic EO Intelligence & Evidence Fusion Architecture

### 50.1 High-Level Objective & Evolution
Phase 6 connects individual specialist model outputs (bi-temporal change maps, optical-SAR backscatter deltas, single-image groundings, spectral indices) into a higher-level reasoning and evidence fusion architecture. TRINETRA transitions from point-wise visual task execution into an AI-assisted Earth-Observation Investigation System.

```text
MULTIPLE OBSERVATIONS
        +
MULTIPLE SPECIALISTS (Optical, SAR, Spectral, Grounding)
        +
GEOSPATIAL EVIDENCE (Bounding Boxes, Polygons, Coordinates)
        +
TEMPORAL EVIDENCE (Timelines, Trajectories, Recurrence)
        +
OBJECT EVIDENCE (Detected Objects, Spatial Overlaps, IoU Tracks)
        ↓
   EVIDENCE FUSION ENGINE
        ↓
SEMANTIC EVENT HYPOTHESES (Categorized, Composite Scored, Ranked)
        ↓
EVIDENCE CONFLICT VALIDATION (Optical vs SAR Discrepancies Preserved)
        ↓
ANALYST REASONING & NOTES (Persistent Storage, Export)
        ↓
INVESTIGATION REPORT (HTML + JSON Artifacts)
```

### 50.2 Core Architectural Principles

1. **Empirical Findings vs. Semantic Hypotheses**:
   - **Empirical Findings**: Factual observations directly measured from sensor data (e.g. "Cluster C1 contains 14.8 hectares of optical reflectance change"). Every finding strictly references valid evidence token IDs (`supporting_evidence_ids`).
   - **Semantic Hypotheses**: High-level semantic interpretations (e.g. `BUILT_UP_EXPANSION`, `VEGETATION_LOSS`) scored with composite confidence, accompanied by alternative runner-up interpretations.

2. **Strict Non-Causal Attribution Boundary**:
   - The engine operates strictly within physical land-cover and reflectance reality.
   - It **NEVER** speculates on commercial motives, contractor identities, illegal activity, or property ownership without ground truth.

3. **Explicit Conflict Preservation**:
   - When sensors disagree (e.g., optical reflectance reveals clearing while SAR shows zero backscatter delta), the engine refuses to average out the discrepancy.
   - It surfaces an explicit `OPTICAL_SAR_DISCREPANCY` conflict, recording conflicting token IDs and explaining physical reasons (e.g. low-profile clearing without vertical structure).

4. **Multi-Observation Object Lifecycle Tracking**:
   - Cross-observation object matching via 2D bounding-box Intersection-over-Union (IoU).
   - Lifecycle classification: `NEW`, `PERSISTENT`, `VANISHED`, `MODIFIED`.

5. **Multi-Dimensional Non-Averaged Evidence Scoring**:
   - Transparent composite formula:
     $$\text{Composite} = 0.30 \cdot C_{\text{model}} + 0.20 \cdot Q_{\text{evidence}} + 0.20 \cdot S_{\text{spatial}} + 0.15 \cdot T_{\text{temporal}} + 0.15 \cdot X_{\text{cross-modal}} - 0.25 \cdot P_{\text{contradiction}}$$
   - Bounded in $[0.05, 1.00]$, with qualitative ratings `HIGH`, `MEDIUM`, `LOW` and human-readable narrative explanation.

### 50.3 Subsystem Directory Layout
```text
backend/investigation/
├── __init__.py
├── models.py                  # Investigation, InvestigationProgress, InvestigationArtifact, InvestigationStatus
├── schemas.py                 # StructuredFinding, SemanticHypothesis, EvidenceConflict, InvestigationRequest
├── errors.py                  # Structured investigation error hierarchy
├── context.py                 # Investigation numerical context decoupled from prompt text
├── provenance.py              # SHA-256 computation across inputs, specialist versions, and graph state
├── planner.py                 # Intent classification (BUILT_UP_CHANGE, VEGETATION_LOSS, etc.) & specialist selection
├── executor.py                # Concurrent specialist execution with ThreadPoolExecutor
├── service.py                 # InvestigationService coordinator with concurrency limiting & async semaphore
├── notes.py                   # AnalystNoteStore (JSON persistence)
├── evidence/                  # EvidenceItem, EvidenceGraph, EvidenceClusterer, EvidenceScorer, ConflictValidator, FusionEngine
├── semantics/                 # SemanticTaxonomy, SemanticClassifier, EventSemanticsEngine, ConfidenceExplainer
├── temporal/                  # TemporalTrajectoryAnalyzer, PersistenceEvaluator, RecurrenceDetector, LandCoverTransitionEngine
├── objects/                   # DetectedObject, ObjectMatcher (IoU), ObjectChangeDetector, ObjectTracker
├── reports/                   # HTML & JSON investigation report generators, evidence cards, timeline builder
└── graph/                      # Compiled LangGraph investigation workflow (build_investigation_graph)
```

### 50.4 Quality Assurance & Performance Metrics
- **Pytest Suite**: 22 unit & integration tests passing 100% across 7 test suites (`backend/tests/investigation/`).
- **Full Graph Execution**: End-to-end LangGraph state machine validated in under 1.5 seconds.
- **Frontend Architecture**: Next.js production build (`npm run build`) completed with 0 errors, TypeScript strict type-checking passing with 0 errors.

---

# 51. Persistent EO Intelligence, Semantic Search & Anomaly Discovery (Phase 7)

```text
OBSERVATIONS ──> ANALYSES ──> INVESTIGATIONS ──> FINDINGS ──> EVENTS ──> INTELLIGENCE STORE ──> SEARCH / DISCOVERY / MONITORING
```

### 51.1 Architectural Overview
Phase 7 elevates TRINETRA from isolated, per-session analytical runs into a cumulative, longitudinal intelligence engine. Every completed investigation automatically indexes its spatial findings, builds canonical Earth Observation events, constructs regional activity baselines, detects statistical anomalies, and provides automated continuous monitoring against incoming satellite passes.

### 51.2 Database Engine & Storage Layer
- **Storage Substrate**: Embedded SQLite repository (`IntelligenceRepository`) configured with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) and synchronized shared in-memory anchor connections for testing.
- **Data Model Schema**:
  1. `investigations`: Canonical records of analyst enquiries and spatial footprints.
  2. `findings`: Persistent findings with 2D geometries, bounding boxes, sensor metrics, and cryptographic SHA-256 fingerprints.
  3. `events`: Deduplicated canonical EO events with multi-dimensional confidence (`evidence_strength`, `temporal_persistence`, `spatial_consistency`, `cross_modal_support`, `model_quality`, `contradiction_penalty`).
  4. `regions`: Canonical geographic cluster envelopes computed through spatial clustering and IoU.
  5. `event_relationships`: Graph edges capturing split and merge lineage (`MERGED_FROM`, `SPLIT_FROM`, `CAUSAL_SEQUENCE`, `CORROBORATING`).
  6. `baselines`: Historical statistical distributions containing sample count, empirical mean, standard deviation, median, Median Absolute Deviation (MAD), and 90th percentile values.
  7. `anomalies`: Flagged statistical outliers exceeding $\pm 2.0\sigma$ deviations from historical baseline with deterministic plain-language explanations.
  8. `monitor_definitions`: Configured scheduled watchers with polygon AOIs, target collections, and schema-defined predicate condition trees.
  9. `monitor_runs` & `monitor_alerts`: Run execution telemetry and duplicate-suppressed analyst alerts.
  10. `investigation_templates`: Standardized audit patterns for repeatable multi-temporal workflows.

### 51.3 Canonical Event State Machine
Events progress through a deterministic, strictly enforced state transition graph:
```text
CANDIDATE  ──[Single observation / unverified finding]──>  OBSERVED
    │                                                          │
    │                                          [Multi-evidence / cross-modal]
    │                                                          ↓
    └──────────────────────────────────────────────>  CORROBORATED
                                                               │
                                               [3+ epochs / >60 days persistent]
                                                               ↓
                                                          PERSISTENT
                                                               │
                                               [Reversal / resolved / split / merged]
                                                               ↓
                                                           RESOLVED
```
- **Splitting**: When divergent spatial or semantic change occurs, `EventSplitter` marks the parent event as `RESOLVED` and instantiates lineage-linked child events.
- **Merging**: When overlapping adjacent events represent a singular physical phenomenon, `EventMerger` expands the bounding envelope, inherits findings, and archives the secondary event.

### 51.4 Natural Language Semantic Search & Fingerprint Similarity
- **Deterministic Fast-Path Parser**: `SearchQueryParser` safely extracts semantic targets, lifecycle states, confidence thresholds, and temporal windows without LLM hallucination risks.
- **Hybrid Search Ranking**: Multi-factor scoring:
  $$\text{Score} = 0.35 \cdot S_{\text{semantic}} + 0.25 \cdot S_{\text{text}} + 0.20 \cdot S_{\text{confidence}} + 0.10 \cdot S_{\text{persistence}} + 0.10 \cdot S_{\text{spatial\_overlap}}$$
- **Mathematical Fingerprinting**: Each finding and event maps to an explainable 5D normalized feature vector:
  $$\mathbf{v} = \left[ \frac{\log_{10}(\text{Area} + 1)}{3}, \frac{\text{AspectRatio}}{5}, \frac{\min(1.0, \text{Magnitude})}{20}, \text{Confidence}, \text{Persistence} \right]$$
- **Similarity Scoring**: `SimilarityScorer` evaluates cosine similarity combined with semantic taxonomy alignment, generating transparent match factors.

### 51.5 Statistical Anomaly Detection & Non-Causal Explanation
- Requires at least 4 historical acquisitions to construct a valid statistical baseline.
- Evaluates both parametric standard deviation ($Z$-score) and robust non-parametric MAD.
- Flags anomalies when $|Z| \ge 2.0\sigma$ or $|Z_{\text{robust}}| \ge 2.5\text{MAD}$.
- **Non-Causal Diagnostic Explanation**: Automatically contextualizes observed deviations relative to historical ranges while strictly avoiding speculation regarding motive, ownership, or human intent.

### 51.6 Continuous Monitoring & Duplicate Alert Suppression
- Evaluates new satellite acquisitions against registered spatial bounding boxes.
- Evaluates condition trees safely without arbitrary code execution.
- Computes deterministic SHA-256 alert fingerprints over `(monitor_id, event_id, semantic_class, date)`:
  - If a matching fingerprint already exists within the configured cooldown window, duplicate notifications are automatically suppressed.
  - New alerts are dispatched to the analyst workspace with acknowledgement tracking.

---

# 52. Phase 8 — Analyst Command Center, Multi-Region Workflows & Evidence Reporting Architecture

Phase 8 elevates TRINETRA from discrete image-by-image evaluation into a full-fledged **Analyst Command Center**. It organizes investigations around persistent analytical questions, multi-sensor Directed Acyclic Graphs (DAGs), multi-region comparisons with area normalization and sensitivity analysis, structured claim-grounded evidence dossiers, and tamper-evident cryptographic exports.

```text
DISCOVER ──► INVESTIGATE ──► COMPARE ──► SYNTHESIZE ──► VERIFY ──► BUILD EVIDENCE PACKAGE ──► EXPORT / SHARE
```

---

### 52.1 Core Architectural Principles
1. **Workspace-Centric Analytical Scaffolding**: Every investigation is bound to an isolated `Workspace` session preserving active AOIs, selected observations, events, findings, DAG plans, evidence board items, notes, and dossier reports.
2. **Deterministic DAG Execution**: Multi-step workflows are structured as Directed Acyclic Graphs with Kahn's algorithm cycle detection, topological ordering, and automated tiered concurrency scheduling.
3. **Rigorous Comparative Intelligence**: Multi-region and multi-event comparisons enforce spatial normalization (metrics scaled per 100 km²), evaluate detection stability curves across varied thresholds, and trigger automated disparity warnings (cloud cover disparity, resolution ratio, sensor modality mismatch, area scale ratio).
4. **Claim-Grounded Evidence Reporting & Non-Causal Attribution**: Every analytical report claim must be grounded in verified evidence IDs. The system enforces strict non-causal attribution rules, rejecting speculative statements regarding human intent, hostile motives, or criminal sabotage.
5. **Cryptographic Tamper-Evident Dossiers**: Dossiers generate deterministic standalone SVG vector maps (zero headless browser dependency), compute comprehensive SHA-256 manifests across report sections and embedded files, and package standalone HTML briefs and JSON artifacts into validated ZIP archives.
6. **Unified Priority Task Scheduling**: High-throughput and long-running operations are coordinated through a thread-safe task queue with priority tiers (`INTERACTIVE > NORMAL > BACKGROUND`), SHA-256 idempotency key deduplication, and stage cancellation.

---

### 52.2 Database Schema & Durable Storage
All Phase 8 data is persisted in a thread-safe SQLite engine (`workspace.db`) configured with Write-Ahead Logging (`WAL`) mode and busy timeout handling:

| Table | Primary Key | Key Attributes & Foreign References |
|---|---|---|
| `workspaces` | `workspace_id` | `name`, `description`, `status` (`CREATED`, `ACTIVE`, `PAUSED`, `COMPLETED`, `ARCHIVED`), `current_aoi_json`, timestamps |
| `workspace_contexts` | `workspace_id` | Active AOI, `active_regions`, `selected_observations`, `selected_events`, `selected_findings`, active pointers |
| `workspace_activities` | `activity_id` | `workspace_id`, `activity_type`, `entity_type`, `entity_id`, `details_json`, `timestamp` |
| `investigation_plans` | `plan_id` | `workspace_id`, `title`, `question`, `steps_json`, `constraints_json`, `status` (`DRAFT`, `READY`, `RUNNING`, `COMPLETED`, `FAILED`) |
| `investigation_plan_runs` | `run_id` | `plan_id`, `execution_index`, `status`, `step_results_json`, `started_at`, `completed_at` |
| `batch_jobs` | `batch_id` | `workspace_id`, `template_id`, `targets_json`, `status`, `concurrency`, `results_json` |
| `region_comparisons` | `comparison_id` | `workspace_id`, `region_a_id`, `region_b_id`, `period`, `metrics_json`, `differences_json`, `warnings_json` |
| `evidence_board_items` | `item_id` | `workspace_id`, `type` (`OBSERVATION`, `FINDING`, `EVENT`, `MAP_LAYER`, `NOTE`), `source_id`, `position_json`, `title`, `annotation` |
| `evidence_board_relations`| `relation_id` | `workspace_id`, `source_item_id`, `target_item_id`, `relation_type` (`supports`, `contradicts`, `related_to`, `follow_up`), metadata |
| `workspace_annotations`| `annotation_id` | `workspace_id`, `geometry_json`, `text`, `type`, `linked_entity_type`, `linked_entity_id` |
| `workspace_reviews` | `review_id` | `workspace_id`, `entity_type`, `entity_id`, `status` (`UNREVIEWED`, `REVIEWED`, `NEEDS_FOLLOWUP`, `RESOLVED_BY_ANALYST`), `analyst_id`, `note` |
| `workspace_follow_ups` | `follow_up_id` | `workspace_id`, `linked_entity_type`, `linked_entity_id`, `note`, `status` (`OPEN`, `RESOLVED`) |
| `workspace_reports` | `report_id` | `workspace_id`, `title`, `status` (`DRAFT`, `VALIDATED`, `FINAL`), `sections_json`, `version`, `manifest_sha256` |
| `workspace_tasks` | `task_id` | `workspace_id`, `type`, `priority` (`INTERACTIVE`, `NORMAL`, `BACKGROUND`), `status`, `progress`, `stage`, `result_json`, `error` |
| `workspace_snapshots` | `snapshot_id` | `workspace_id`, `snapshot_name`, `state_json`, `created_at` |

---

### 52.3 DAG Investigation Task Graph
`TaskGraph` handles multi-step dependency resolution for analytical plans:
- **Cycle Detection**: Kahn's algorithm calculates vertex in-degrees. If the topological visited count does not match total step count, a `CycleDetectedError` is raised identifying the cycle.
- **Invalid Dependency Guard**: Validates that all items in `depends_on` exist in the plan; otherwise raises `InvalidDependencyError`.
- **Concurrent Execution Tiers**: `get_execution_batches()` groups independent nodes into parallel layers:
  $$\text{Layer } 0 \implies \{ v \mid \text{in-degree}(v) = 0 \}$$
  $$\text{Layer } k+1 \implies \{ v \mid \text{dependencies satisfied by } \bigcup_{i=0}^k \text{Layer } i \}$$

---

### 52.4 Resource Limits & Batch Enforcer
`BatchLimitsEnforcer` enforces safe computation bounds:
- **Target Quota**: $1 \le N \le 50$ targets per batch job.
- **Pixel Budget**: Total estimated workload $\le 50{,}000{,}000$ pixels.
- **Concurrency Clamping**: Automatic clamping to $C \le 4$ parallel workers.
- **Aggregate Synthesis**: Cross-regional summary calculating average change %, max/min change %, average confidence, and total findings.

---

### 52.5 Comparative Metrics & Sensitivity Analysis
The comparative engine ensures equitable cross-geographic evaluations:
1. **Area Normalization**: Raw counts scaled per 100 $\text{km}^2$:
   $$\text{Metric}_{\text{norm}} = \frac{\text{Metric}_{\text{raw}}}{\text{Area}_{\text{km}^2}} \times 100$$
2. **Coverage Disparity Warnings**:
   - Cloud cover difference $> 15\%$.
   - Resolution ratio $\ge 2.0\times$.
   - Modality mismatch (e.g. SAR vs Optical).
   - Geographic area ratio $\ge 3.0\times$.
3. **Stability Sensitivity Curves**: Detection thresholds evaluated at $[0.10, 0.15, \dots, 0.40]$:
   $$\text{Area}(t) = \text{BaseArea} \cdot e^{-\lambda (t - t_0)}$$
   $$\text{Rate of Change} = \frac{\Delta \text{Area}}{\Delta t}$$
   - $|\text{RoC}| \le 15 \implies \text{STABLE}$
   - $15 < |\text{RoC}| \le 30 \implies \text{MODERATELY\_SENSITIVE}$
   - $|\text{RoC}| > 30 \implies \text{HYPERSENSITIVE}$

---

### 52.6 Report Dossier Pipeline & Cryptographic Manifest
1. **Claim Grounding Validator**:
   - Every `ReportClaim` must reference at least one valid evidence item ID (`evidence_ids`).
   - Rejects ungrounded claims with `ClaimEvidenceError`.
2. **Non-Causal Attribution Guard**:
   - Inspects section narratives and claim text for speculative intent phrases (`deliberately`, `intentional sabotage`, `malicious intent`, `hostile operation`).
   - Flags policy violations to preserve objective Earth Observation reporting standards.
3. **Deterministic Vector Map Snapshot**:
   - Standalone SVG generator computes Mercator bounding box coordinate transformations, drawing grid lines, geographic scale bars, north arrows, and polygon boundary paths without external web dependencies.
4. **Cryptographic SHA-256 Manifest**:
   - Generates deterministic hash over each individual section payload:
     $$H_{\text{sec}} = \text{SHA-256}(\text{JSON}(\text{section}))$$
   - Calculates overall dossier hash over all sections, map SVGs, and exported files:
     $$H_{\text{overall}} = \text{SHA-256}(\text{JSON}(H_{\text{sec\_1}}, H_{\text{sec\_2}}, \dots, H_{\text{files}}))$$
5. **Tamper-Evident ZIP Package Export**:
   - Emits self-contained ZIP archive containing `report.html` (presentation view), `report.json`, `map_snapshot.svg`, and `manifest.json`.

---

### 52.7 REST API Endpoints (`/api/v1/workspace`)
The workspace router exposes 44 typed endpoints:
- **Workspaces**: `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`, `POST /{id}/snapshot`, `GET /{id}/snapshots`
- **Context**: `GET /{id}/context`, `PATCH /{id}/context`
- **Evidence Board**: `GET /{id}/board/items`, `POST /{id}/board/items`, `DELETE /{id}/board/items/{item_id}`, `GET /{id}/board/relations`, `POST /{id}/board/relations`, `DELETE /{id}/board/relations/{rel_id}`
- **Planning**: `GET /{id}/plans`, `POST /{id}/plans`, `GET /{id}/plans/{p_id}`, `POST /{id}/plans/{p_id}/execute`, `GET /{id}/plans/{p_id}/runs`
- **Comparison**: `POST /{id}/compare/regions`, `GET /{id}/compare/regions`, `POST /{id}/compare/events`, `POST /{id}/compare/findings`
- **Batch**: `POST /{id}/batch`, `GET /{id}/batch`, `GET /{id}/batch/{batch_id}`
- **Synthesis**: `POST /{id}/synthesis`
- **Annotations & Reviews**: `GET /{id}/annotations`, `POST /{id}/annotations`, `DELETE /{id}/annotations/{a_id}`, `GET /{id}/reviews`, `POST /{id}/reviews`, `GET /{id}/follow-ups`, `POST /{id}/follow-ups`, `PATCH /{id}/follow-ups/{f_id}`
- **Reports**: `GET /{id}/reports`, `POST /{id}/reports`, `GET /{id}/reports/{r_id}`, `GET /{id}/reports/{r_id}/presentation`, `GET /{id}/reports/{r_id}/manifest`, `GET /{id}/reports/{r_id}/export`
- **Task Queue**: `GET /{id}/tasks`, `POST /{id}/tasks`, `GET /{id}/tasks/{t_id}`, `POST /{id}/tasks/{t_id}/cancel`
- **Activity**: `GET /{id}/activities`





