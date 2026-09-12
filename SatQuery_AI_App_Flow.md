# SatQuery AI — Application Flow

**SIH 2026 — Problem Statement 26167**  
**Product:** SatQuery AI  
**Purpose:** End-to-end application/user flow for the proposed agentic remote-sensing AI system.

> This app flow is based on the supplied PS 26167 and the PRD/TRD created for the project. The mandatory flows reflect the PS scope: single-image VQA, one additional single-image capability, bi-temporal change understanding, optical–SAR analysis, input validation, agentic model/tool orchestration, visual evidence, confidence and an observable execution summary.

---

# 1. Product Flow at a Glance

```text
                         ┌─────────────────────┐
                         │      LANDING PAGE   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   START ANALYSIS    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    UPLOAD IMAGE(S)  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  INPUT VALIDATION   │
                         │ Format / Modality   │
                         │ Metadata / Pairing  │
                         └──────────┬──────────┘
                                    │
                        ┌───────────┴───────────┐
                        │                       │
                      INVALID                 VALID
                        │                       │
                        ▼                       ▼
                ┌───────────────┐     ┌─────────────────────┐
                │ Error + Fix   │     │ NATURAL LANGUAGE    │
                │ Instructions  │     │ QUERY               │
                └───────────────┘     └──────────┬──────────┘
                                                 │
                                                 ▼
                                      ┌─────────────────────┐
                                      │   AGENT CONTROLLER  │
                                      │ Query Understanding │
                                      │ Task Classification │
                                      └──────────┬──────────┘
                                                 │
                     ┌───────────────────────────┼──────────────────────────┐
                     │                           │                          │
                     ▼                           ▼                          ▼
              SINGLE IMAGE                 BI-TEMPORAL                OPTICAL + SAR
                     │                           │                          │
             ┌───────┼────────┐                  │                          │
             ▼       ▼        ▼                  ▼                          ▼
            VQA   CAPTION  GROUNDING       CHANGE AI                 FUSION AI
             │       │        │                  │                          │
             └───────┴────────┘                  └──────────┬───────────────┘
                       │                                    │
                       └────────────────┬───────────────────┘
                                        ▼
                              ┌─────────────────────┐
                              │ RESULT INTEGRATION  │
                              └──────────┬──────────┘
                                         │
                       ┌─────────────────┼─────────────────┐
                       ▼                 ▼                 ▼
                    ANSWER            EVIDENCE         CONFIDENCE
                       │                 │                 │
                       └─────────────────┼─────────────────┘
                                         ▼
                              ┌─────────────────────┐
                              │ EXECUTION SUMMARY   │
                              │ Task / Models /     │
                              │ Tools / Parameters  │
                              └──────────┬──────────┘
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                       VIEW RESULTS          DOWNLOAD REPORT
```

---

# 2. Application Navigation

The application should have five primary areas:

```text
┌─────────────────────────────────────────────────────────────┐
│ SATQUERY AI                                                 │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│ Dashboard    │                                              │
│              │                                              │
│ New Analysis │             MAIN WORKSPACE                   │
│              │                                              │
│ History      │                                              │
│              │                                              │
│ Benchmarks   │                                              │
│              │                                              │
│ About        │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

## 2.1 Navigation items

### Dashboard

Overview of the system and recent analyses.

### New Analysis

Primary workspace for uploading imagery and asking questions.

### History

Previous analysis requests and generated reports.

### Benchmarks

Internal benchmark/evaluation workspace.

### About

System capabilities, supported formats, model information and project details.

---

# 3. Screen 1 — Landing Page

## Purpose

Introduce SatQuery AI and immediately communicate what the application does.

## UI

```text
┌─────────────────────────────────────────────────────────────┐
│ SATQUERY AI                                                 │
│ Agentic Remote-Sensing Intelligence                         │
│                                                             │
│ Ask questions about satellite imagery using natural        │
│ language. Analyze single images, changes over time,        │
│ and optical + SAR imagery.                                  │
│                                                             │
│              [ START ANALYSIS ]                             │
│                                                             │
│ Supported                                                  │
│ ✓ GeoTIFF / TIFF                                            │
│ ✓ Optical / Multispectral                                   │
│ ✓ SAR                                                       │
│ ✓ Bi-temporal pairs                                         │
│ ✓ Optical + SAR pairs                                       │
└─────────────────────────────────────────────────────────────┘
```

## User action

**Start Analysis**

→ Navigate to New Analysis.

---

# 4. Screen 2 — New Analysis Workspace

The New Analysis page is the primary product screen.

```text
┌─────────────────────────────────────────────────────────────┐
│ New Analysis                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. INPUT                                                   │
│                                                             │
│ [ Upload Image ] [ Upload Pair ]                            │
│                                                             │
│ Supported: GeoTIFF / TIFF                                  │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │            Drag & Drop Image Here                      │ │
│ │                     or                                  │ │
│ │                 [ Browse Files ]                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Input configuration:                                       │
│ ○ Single Image                                             │
│ ○ Bi-Temporal Pair                                         │
│ ○ Optical + SAR Pair                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 5. Screen 3 — Image Upload Flow

## Step 1

User selects input configuration.

```text
Single Image
Bi-Temporal Pair
Optical + SAR Pair
```

## Step 2

User uploads required files.

### Single image

```text
image.tif
```

### Bi-temporal

```text
image_t1.tif
image_t2.tif
```

### Optical + SAR

```text
optical.tif
sar.tif
```

## Step 3

Frontend sends files to backend.

```text
Frontend
   ↓
POST /api/v1/analyze
   ↓
Backend
```

---

# 6. Screen 4 — Input Validation

After upload, validation happens automatically.

```text
                    INPUT VALIDATOR
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       FORMAT          MODALITY         METADATA
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                     COMPATIBILITY
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
              PASS                 FAIL
                │                   │
                ▼                   ▼
           Continue             Show error
```

## UI

```text
Input Validation

✓ File format
✓ Image readable
✓ Image dimensions
✓ Band information
✓ CRS / geospatial metadata
✓ Modality
✓ Pair compatibility

Status: VALID
```

For paired imagery:

```text
Optical image       ✓
SAR image           ✓
Spatial alignment   ✓
Compatible          ✓
```

---

# 7. Invalid Input Flow

If validation fails:

```text
Upload
  ↓
Validation
  ↓
FAIL
  ↓
Error Screen
```

Example:

```text
⚠ Input validation failed

The uploaded images cannot be used for optical–SAR analysis.

Reason:
The images could not be verified as spatially compatible.

Required:
A co-registered optical + SAR pair.

[ Replace Images ]
```

The system must not silently send invalid input to a specialist model.

---

# 8. Screen 5 — Query Input

Once validation succeeds:

```text
┌─────────────────────────────────────────────────────────────┐
│ ASK SATQUERY AI                                             │
│                                                             │
│ What would you like to know about this imagery?             │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ What changed between these two dates, and where did     │ │
│ │ the change occur?                                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Example queries:                                            │
│ • Describe the land-cover and major objects visible.        │
│ • Highlight the water body referred to in the query.        │
│ • What changed between these two dates?                     │
│ • Use optical and SAR together to identify built-up areas.  │
│                                                             │
│                         [ ANALYZE ]                         │
└─────────────────────────────────────────────────────────────┘
```

---

# 9. Screen 6 — Agent Processing

After the user clicks Analyze:

```text
                 USER QUERY
                     │
                     ▼
             QUERY UNDERSTANDING
                     │
                     ▼
              TASK CLASSIFIER
                     │
                     ▼
              INPUT CONFIGURATION
                     │
                     ▼
              CAPABILITY MATCHING
                     │
                     ▼
                TOOL SELECTOR
                     │
                     ▼
             SPECIALIST MODEL
```

## UI

Show a concise observable workflow:

```text
Analyzing...

✓ Input validated
✓ Query understood
✓ Task identified: Change Analysis
✓ Specialist selected: Change AI
● Running analysis...
○ Generating evidence
○ Preparing result
```

Do not expose internal chain-of-thought.

---

# 10. Agent Routing Flow

## 10.1 Single image

```text
Single Image
     │
     ▼
Query classification
     │
     ├── Question ──────────► RS-VQA
     │
     ├── Describe ─────────► RS-Caption
     │
     └── Highlight/Locate ─► RS-Grounding
```

## 10.2 Bi-temporal pair

```text
Bi-Temporal Pair
       │
       ▼
Change Intent
       │
       ▼
Change Specialist
       │
       ▼
Change Description / Change VQA
```

## 10.3 Optical + SAR

```text
Optical + SAR
      │
      ▼
Cross-Modal Intent
      │
      ▼
Optical–SAR Specialist
      │
      ▼
Joint Analysis
```

---

# 11. Single-Image VQA Flow

```text
UPLOAD SINGLE IMAGE
        ↓
VALIDATE
        ↓
USER QUESTION
        ↓
AGENT
        ↓
RS-VQA MODEL
        ↓
ANSWER
        ↓
CONFIDENCE
        ↓
EVIDENCE
        ↓
EXECUTION TRACE
        ↓
RESULT
```

## Result UI

```text
┌─────────────────────────────────────────────────────────────┐
│ ANSWER                                                      │
│                                                             │
│ The image contains predominantly agricultural land with    │
│ several built-up regions.                                  │
│                                                             │
│ Confidence: 89%                                             │
│                                                             │
│ Evidence                                                    │
│ [ Image with highlighted regions ]                          │
│                                                             │
│ Execution                                                   │
│ Task: Remote-Sensing VQA                                    │
│ Model: RS-VQA                                                │
│ Status: Completed                                           │
└─────────────────────────────────────────────────────────────┘
```

---

# 12. Captioning / Scene Description Flow

```text
Single Image
     ↓
Query: "Describe this image"
     ↓
Agent
     ↓
Caption Specialist
     ↓
Scene Description
     ↓
Confidence
     ↓
Result
```

Example output:

```text
Scene Description

The scene contains agricultural fields, a built-up settlement,
road networks and a nearby water feature.

Confidence: 86%
```

---

# 13. Grounding Flow

```text
Single Image
     ↓
Query:
"Highlight the water body"
     ↓
Agent
     ↓
Grounding Specialist
     ↓
Bounding Box / Mask
     ↓
Evidence Overlay
     ↓
Result
```

UI:

```text
┌─────────────────────────────────────────────────────────────┐
│ GROUNDING RESULT                                            │
│                                                             │
│                ┌──────────────────┐                         │
│                │                  │                         │
│       IMAGE    │    WATER BODY    │                         │
│                │                  │                         │
│                └──────────────────┘                         │
│                                                             │
│ Detected regions: 1                                        │
│ Confidence: 91%                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 14. Bi-Temporal Change Analysis Flow

```text
IMAGE T1
   │
   ├──────────────┐
   │              │
   ▼              ▼
PREPROCESS     PREPROCESS
   │              │
   └──────┬───────┘
          ▼
   SPATIAL COMPATIBILITY
          │
          ▼
    CHANGE SPECIALIST
          │
          ▼
     CHANGE OUTPUT
          │
      ┌───┴────┐
      ▼        ▼
  DESCRIPTION  MAP
      │        │
      └───┬────┘
          ▼
       EVIDENCE
          │
          ▼
        RESULT
```

## Result screen

```text
┌─────────────────────────────────────────────────────────────┐
│ TEMPORAL CHANGE ANALYSIS                                    │
├───────────────────────┬─────────────────────────────────────┤
│ DATE 1                │ DATE 2                              │
│                       │                                     │
│ [ IMAGE T1 ]          │ [ IMAGE T2 ]                        │
│                       │                                     │
├───────────────────────┴─────────────────────────────────────┤
│                                                             │
│ CHANGE MAP                                                  │
│ [ Change overlay ]                                          │
│                                                             │
│ SUMMARY                                                     │
│ Built-up area increased in the highlighted region.          │
│                                                             │
│ Confidence: 88%                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 15. Optical–SAR Analysis Flow

```text
OPTICAL IMAGE
      │
      ▼
OPTICAL ENCODER
      │
      ├──────────────┐
      │              │
      │           FUSION
      │              │
SAR IMAGE            │
      │              │
      ▼              │
SAR ENCODER ─────────┘
             ↓
       JOINT REASONING
             ↓
           ANSWER
             ↓
          EVIDENCE
             ↓
         CONFIDENCE
```

## UI

```text
┌─────────────────────────────────────────────────────────────┐
│ CROSS-MODAL ANALYSIS                                       │
├───────────────────────┬─────────────────────────────────────┤
│ OPTICAL               │ SAR                                 │
│                       │                                     │
│ [ Optical image ]     │ [ SAR image ]                       │
│                       │                                     │
├───────────────────────┴─────────────────────────────────────┤
│                                                             │
│ QUERY                                                       │
│ Use optical and SAR together to identify built-up and       │
│ water-covered regions.                                      │
│                                                             │
│ RESULT                                                      │
│ Built-up regions are concentrated in...                     │
│                                                             │
│ Modalities used: Optical + SAR                              │
│ Confidence: 86%                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 16. Result Integration Flow

Specialist outputs are normalized before reaching the UI.

```text
Specialist Output
       │
       ▼
Output Validation
       │
       ▼
Evidence Resolver
       │
       ▼
Confidence Processing
       │
       ▼
Result Integrator
       │
       ├──────────► Answer
       ├──────────► Evidence
       ├──────────► Confidence
       ├──────────► Metadata
       └──────────► Execution Trace
```

---

# 17. Result Screen

Every completed analysis should use a consistent result layout.

```text
┌─────────────────────────────────────────────────────────────┐
│ ANALYSIS RESULT                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ QUERY                                                       │
│ "What changed between these two dates?"                     │
│                                                             │
│ ANSWER                                                      │
│ Built-up area increased in the northern region.             │
│                                                             │
│ CONFIDENCE                                                  │
│ ██████████████████░░ 88%                                    │
│                                                             │
│ VISUAL EVIDENCE                                             │
│ [ Interactive map / image / overlay ]                       │
│                                                             │
│ EXECUTION SUMMARY                                           │
│ Task: Change Analysis                                       │
│ Model: Change Specialist v1                                 │
│ Tools: Input Validator → Change AI → Evidence Generator    │
│ Status: Completed                                           │
│                                                             │
│ [ Download Report ]   [ New Analysis ]                      │
└─────────────────────────────────────────────────────────────┘
```

---

# 18. Execution Summary

The execution summary should be visible but concise.

Example:

```text
Execution Summary

Input:
Bi-temporal pair

Task:
Change-based VQA

Tools:
1. Input Validator v1.0
2. Change Specialist v1.0
3. Evidence Generator v1.0

Parameters:
Confidence threshold: 0.70

Status:
Completed

Duration:
12.4 seconds
```

The system should not expose internal chain-of-thought.

---

# 19. Evidence Viewer

The evidence viewer changes depending on the workflow.

## Single image

```text
Original Image
      +
Bounding Box / Mask / Region
```

## Bi-temporal

```text
T1 + T2 + Change Overlay
```

## Optical–SAR

```text
Optical + SAR + Joint Evidence
```

Controls:

```text
[ Zoom In ]
[ Zoom Out ]
[ Reset ]
[ Toggle Evidence ]
[ Opacity ]
[ Full Screen ]
```

---

# 20. Confidence UI

Use a simple and understandable representation.

```text
Confidence

88%

HIGH
```

Suggested levels:

```text
80–100% → HIGH
60–79%  → MEDIUM
<60%    → LOW
```

> The exact threshold should be configurable and calibrated against the selected model. The above values are a product recommendation, not an official PS specification.

For low confidence:

```text
⚠ Low confidence

The model is uncertain about this result.

Evidence is shown below for review.
```

---

# 21. Report Flow

```text
RESULT COMPLETED
       ↓
USER CLICKS
"DOWNLOAD REPORT"
       ↓
REPORT GENERATOR
       ↓
COLLECT
├── Query
├── Inputs
├── Metadata
├── Task
├── Models
├── Tools
├── Parameters
├── Answer
├── Confidence
└── Evidence
       ↓
GENERATE REPORT
       ↓
DOWNLOAD
```

Recommended formats:

```text
PDF
HTML
JSON
```

---

# 22. Analysis History Flow

```text
Dashboard
    ↓
History
    ↓
┌────────────────────────────────────────────────────────────┐
│ Request ID │ Date │ Task │ Input │ Confidence │ Status    │
├────────────────────────────────────────────────────────────┤
│ 1001       │ ...  │ VQA  │ Image │ 91%        │ Complete  │
│ 1002       │ ...  │ Change│ Pair │ 88%        │ Complete  │
│ 1003       │ ...  │ SAR  │ Pair │ 86%        │ Complete  │
└────────────────────────────────────────────────────────────┘
```

Selecting a request:

```text
History Item
    ↓
Analysis Details
    ↓
Previous Result
    ↓
Evidence
    ↓
Execution Trace
    ↓
Report
```

---

# 23. Benchmark Flow

This is primarily for the development/evaluation team.

```text
Benchmark Dashboard
       ↓
Select Dataset
       ↓
Select Task
       ↓
Select Test Split
       ↓
Run Evaluation
       ↓
SatQuery AI Pipeline
       ↓
Metric Evaluation
       ↓
Results
```

Potential datasets in scope:

```text
BigEarthNet
VRSBench
RSVQA
CDVQA
```

The prescribed public benchmark test subsets and ISRO/SAC evaluation dataset should be treated according to the official evaluation protocol.

---

# 24. Complete Backend Flow

```text
                HTTP REQUEST
                     │
                     ▼
               API Gateway
                     │
                     ▼
             Request Creation
                     │
                     ▼
             Input Validator
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
       Invalid                 Valid
          │                     │
          ▼                     ▼
       Error              Query Parser
                                │
                                ▼
                         Task Classifier
                                │
                                ▼
                         Agent Planner
                                │
                                ▼
                         Tool Registry
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                  ▼
            VQA             CHANGE             OPTICAL-SAR
              │                 │                  │
              └─────────────────┼──────────────────┘
                                ▼
                         Output Validator
                                │
                                ▼
                       Evidence Generator
                                │
                                ▼
                       Confidence Layer
                                │
                                ▼
                       Result Integrator
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
                API Result             Report Generator
                    │                       │
                    ▼                       ▼
                 FRONTEND                DOWNLOAD
```

---

# 25. Complete User Journey

```text
LANDING
  ↓
START ANALYSIS
  ↓
SELECT INPUT TYPE
  ↓
UPLOAD IMAGE(S)
  ↓
VALIDATE
  ↓
VALIDATION PASS?
  ├── NO → FIX INPUT → VALIDATE AGAIN
  │
  └── YES
        ↓
     ENTER QUERY
        ↓
    SUBMIT ANALYSIS
        ↓
    AGENT PROCESSING
        ↓
    TASK IDENTIFICATION
        ↓
    TOOL/MODEL SELECTION
        ↓
    MODEL EXECUTION
        ↓
    EVIDENCE GENERATION
        ↓
    CONFIDENCE
        ↓
    RESULT INTEGRATION
        ↓
    SHOW RESULT
        ↓
    SHOW EXECUTION SUMMARY
        ↓
    DOWNLOAD REPORT
        ↓
    NEW ANALYSIS / HISTORY
```

---

# 26. Example Journey 1 — VQA

```text
User
 ↓
Upload satellite image
 ↓
Validation ✓
 ↓
Ask:
"What major objects are visible?"
 ↓
Agent identifies VQA intent
 ↓
RS-VQA selected
 ↓
Inference
 ↓
Answer + confidence
 ↓
Visual evidence
 ↓
Execution summary
 ↓
Report
```

---

# 27. Example Journey 2 — Grounding

```text
User
 ↓
Upload image
 ↓
Ask:
"Highlight the water body."
 ↓
Agent → Grounding
 ↓
Grounding model
 ↓
Bounding box / mask
 ↓
Overlay
 ↓
Confidence
 ↓
Result
```

---

# 28. Example Journey 3 — Change Detection

```text
User
 ↓
Upload T1 + T2
 ↓
Validation
 ↓
Spatial compatibility
 ↓
Ask:
"What changed and where?"
 ↓
Agent → Change Specialist
 ↓
Change analysis
 ↓
Change description
 ↓
Change map
 ↓
Confidence
 ↓
Execution trace
 ↓
Report
```

---

# 29. Example Journey 4 — Optical + SAR

```text
User
 ↓
Upload Optical + SAR
 ↓
Validation
 ↓
Co-registration check
 ↓
Ask:
"Identify built-up and water-covered regions."
 ↓
Agent → Optical-SAR Specialist
 ↓
Joint multimodal analysis
 ↓
Answer
 ↓
Evidence
 ↓
Confidence
 ↓
Execution trace
 ↓
Report
```

---

# 30. Agent Decision Tree

```text
                    INPUT
                      │
                      ▼
              How many images?
                      │
        ┌─────────────┼──────────────┐
        │             │              │
        ▼             ▼              ▼
        1             2              2
     Single       Bi-Temporal    Optical + SAR
        │             │              │
        ▼             ▼              ▼
     Query?        Change?        Joint Query?
        │             │              │
   ┌────┼────┐        │              │
   ▼    ▼    ▼        ▼              ▼
 VQA Caption Ground  Change       Fusion
```

---

# 31. Error Recovery Flow

```text
                  ERROR
                    │
          ┌─────────┼──────────┐
          ▼         ▼          ▼
      Validation  Model      Report
          │       Failure     Failure
          ▼         │          │
     Fix Inputs     ▼          ▼
                   Retry      Retry
                     │
              ┌──────┴───────┐
              ▼              ▼
           Success          Fail
              │              │
              ▼              ▼
           Result        User Error
```

For model failures, the system should show a useful error rather than hallucinating a result.

---

# 32. Loading / Progress States

Long-running remote-sensing inference should never appear frozen.

Use:

```text
● Validating input
✓ Input validated

● Understanding query
✓ Task identified: Optical–SAR analysis

● Selecting specialist
✓ Optical–SAR Specialist selected

● Running inference
████████████░░░░ 75%

● Generating evidence
○ Pending

○ Preparing final response
```

---

# 33. Recommended Main Workspace Layout

```text
┌──────────────────────────────────────────────────────────────────┐
│ SATQUERY AI                         New Analysis   History       │
├───────────────────────┬──────────────────────────────────────────┤
│ INPUTS                │ QUERY                                    │
│                       │                                          │
│ [Image T1]            │ "What changed between these dates?"      │
│                       │                                          │
│ [Image T2]            │                    [ ANALYZE ]            │
│                       │                                          │
├───────────────────────┴──────────────────────────────────────────┤
│ VALIDATION                                                     ✓ │
├──────────────────────────────────────────────────────────────────┤
│                                                                │
│                       EVIDENCE VIEWER                          │
│                                                                │
│                    [ Interactive Map ]                         │
│                                                                │
├───────────────────────────────┬──────────────────────────────────┤
│ ANSWER                       │ EXECUTION SUMMARY                │
│                              │                                  │
│ Built-up area increased...   │ Task: Change Analysis            │
│ Confidence: 88%              │ Model: Change Specialist         │
│                              │ Tools: Validator → Change AI     │
│                              │                                  │
└───────────────────────────────┴──────────────────────────────────┘
```

---

# 34. Mobile/Responsive Behaviour

The primary SIH demonstration should target desktop/laptop because remote-sensing imagery and paired-image visualization benefit from a larger display.

For smaller screens:

```text
Desktop:
Inputs + Evidence + Result side-by-side

Tablet:
Inputs
↓
Evidence
↓
Result

Mobile:
Input
↓
Query
↓
Result
↓
Evidence
↓
Execution Trace
```

---

# 35. Recommended UX Rules

1. Never make users understand which AI model to select manually.
2. Let the agent choose the specialist workflow.
3. Always show validation status.
4. Always show the selected task.
5. Show confidence with the answer.
6. Show visual evidence whenever available.
7. Keep execution details available but not overwhelming.
8. Never expose internal chain-of-thought.
9. Make paired-image workflows visually obvious.
10. Keep “New Analysis” accessible from every result screen.
11. Provide useful errors.
12. Never silently substitute an unsupported workflow.

---

# 36. SIH Judge Flow

The final demo should be optimized around the mandatory requirements.

## Demo 1 — Single-image VQA

```text
Upload image
 ↓
Ask VQA question
 ↓
Agent selects VQA
 ↓
Answer
 ↓
Evidence
 ↓
Confidence
```

## Demo 2 — Additional single-image capability

```text
Ask:
"Describe this scene"
OR
"Highlight the water body"
 ↓
Agent selects Captioning / Grounding
 ↓
Result
```

## Demo 3 — Bi-temporal

```text
Upload T1 + T2
 ↓
Ask:
"What changed and where?"
 ↓
Agent selects Change Specialist
 ↓
Answer + Change Evidence
```

## Demo 4 — Optical + SAR

```text
Upload Optical + SAR
 ↓
Ask:
"Identify built-up and water-covered regions."
 ↓
Agent selects Optical–SAR Specialist
 ↓
Joint result
```

## Demo 5 — Agentic orchestration

Show:

```text
Query 1 → VQA
Query 2 → Grounding
Query 3 → Change
Query 4 → Optical–SAR
```

This makes the agentic nature immediately visible.

---

# 37. Final Application Flow

```text
                         SATQUERY AI
                              │
                              ▼
                        USER OPENS APP
                              │
                              ▼
                        NEW ANALYSIS
                              │
                              ▼
                     SELECT INPUT CONFIG
                              │
             ┌────────────────┼─────────────────┐
             ▼                ▼                 ▼
          SINGLE          BI-TEMPORAL       OPTICAL-SAR
             │                │                 │
             └────────────────┼─────────────────┘
                              ▼
                         UPLOAD FILES
                              │
                              ▼
                      INPUT VALIDATION
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                  FAIL                 PASS
                    │                   │
                    ▼                   ▼
              FIX / REUPLOAD       ENTER QUERY
                                        │
                                        ▼
                                AGENT CONTROLLER
                                        │
                                        ▼
                                TASK CLASSIFIER
                                        │
                                        ▼
                                TOOL REGISTRY
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
                  VQA               CHANGE              FUSION
                    │                   │                   │
                    ▼                   ▼                   ▼
               SPECIALIST          SPECIALIST          SPECIALIST
                    │                   │                   │
                    └───────────────────┼───────────────────┘
                                        ▼
                                  OUTPUT VALIDATION
                                        │
                                        ▼
                                  EVIDENCE ENGINE
                                        │
                                        ▼
                                  CONFIDENCE ENGINE
                                        │
                                        ▼
                                  RESULT INTEGRATOR
                                        │
                         ┌──────────────┼───────────────┐
                         ▼              ▼               ▼
                       ANSWER        EVIDENCE        CONFIDENCE
                         │              │               │
                         └──────────────┼───────────────┘
                                        ▼
                                  EXECUTION TRACE
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
                    VIEW RESULT                 DOWNLOAD REPORT
                         │
                         ▼
                   NEW ANALYSIS
                         │
                         ▼
                      HISTORY
```

---

# 38. Product North Star

The ideal SatQuery AI interaction is:

> **Upload → Ask → Agent decides → Specialist analyses → Evidence proves → Confidence informs → Report preserves.**

The user should never need to understand which AI model performs the task.

The system should make the intelligence visible through the **workflow outcome**, not through exposed internal reasoning.

---

# 39. Minimum Screens Required for MVP

| Screen | Priority | Purpose |
|---|---|---|
| Landing | P0 | Introduce product |
| New Analysis | P0 | Main workspace |
| Upload | P0 | Image ingestion |
| Validation | P0 | Compatibility checking |
| Query | P0 | Natural-language input |
| Agent Processing | P0 | Show workflow progress |
| Result | P0 | Answer + confidence |
| Evidence Viewer | P0 | Visual evidence |
| Execution Summary | P0 | Auditability |
| Report | P0 | Downloadable result |
| History | P1 | Previous analyses |
| Benchmark | P1 | Evaluation |
| About | P2 | Documentation |

---

# 40. Final UX Goal

SatQuery AI should feel like a single intelligent workspace:

```text
               "I have satellite imagery.
                I want an answer."

                         ↓

                    SATQUERY AI

                         ↓

              "What are you asking?"

                         ↓

                 AGENT UNDERSTANDS

                         ↓

              "Which analysis is needed?"

                         ↓

                SPECIALIST SELECTED

                         ↓

                 "What does the data say?"

                         ↓

              ANALYSIS + EVIDENCE + CONFIDENCE

                         ↓

                 "How was it obtained?"

                         ↓

                  EXECUTION SUMMARY

                         ↓

                  "Can I preserve it?"

                         ↓

                    REPORT EXPORT
```

**The application should hide technical complexity from the user while making the important technical evidence and execution trace visible to the evaluator.**
