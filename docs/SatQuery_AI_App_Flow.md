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

---

# 39. Shanetra Exploration Flow (`/explore`)

Phase 1 and Phase 2 introduce the dedicated Earth-observation exploration workstation at `/explore` alongside the existing `/analysis` pipeline.

```text
                           TRINETRA
                              │
             ┌────────────────┴────────────────┐
             │                                 │
         /analysis                          /explore
     (Guided Analysis)                 (Shanetra Workstation)
             │                                 │
     UPLOAD & QUERY                     EARTH VISUALIZATION
             │                         (2D MapLibre / 3D Cesium)
      SPECIALIST AI                            │
             │                         DISCOVER OBSERVATIONS
      EVIDENCE & PDF                   (Local GeoTIFFs / Copernicus)
                                               │
                                        SELECT OBSERVATION
                                               │
                                        + ADD TO MAP
                                               │
                                       WINDOWED TILE SERVICE
                                  (/api/v1/explore/tiles/...png)
                                               │
                                       CONTROLLED LAYERS
                                   (Visibility, Opacity, Limits)
```

### 39.1 Key Workflow Guarantees
1. **Zero Browser Overload**: Full satellite GeoTIFFs are never downloaded to the browser. 256×256 PNG tiles are fetched dynamically on demand.
2. **Deterministic Fallback**: Local indexed fixtures ensure the exploration shell remains 100% functional even in air-gapped or offline environments.
3. **Strict Layer Governance**: Layer limits (`MAX_ACTIVE_IMAGERY_LAYERS = 2`) prevent WebGL context exhaustion and browser crashes.

---

# 40. Explore AI Natural-Language Control Flow (`/explore`)

Phase 3 introduces controlled natural-language interaction to the Shanetra workstation via an air-gapped AI Gateway.

```text
                            USER INPUT
                     ("Go to Nagpur and show S2")
                                 │
                                 ▼
                         QUERY BAR & HUD
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ Fast Fallback Parser  │ ─── [Simple Match: reset, zoom, show] ───┐
                     └───────────┬───────────┘                                          │
                                 │                                                      │
                            [Complex]                                                   │
                                 ▼                                                      │
                     ┌───────────────────────┐                                          │
                     │  Fast Intent Router   │ (fast_router)                            │
                     └───────────┬───────────┘                                          │
                                 │                                                      │
                                 ▼                                                      │
                     ┌───────────────────────┐                                          │
                     │  AI Command Planner   │ (planner + native Ollama JSON Schema)    │
                     └───────────┬───────────┘                                          │
                                 │                                                      │
                                 ▼                                                      │
                        STRUCTURED PLAN ◄───────────────────────────────────────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │      GeoResolver      │ (Gazetteer & Coordinate Parser)
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Command Validator   │ (Enforces Allowlist, Opacities, Bounds)
                     └───────────┬───────────┘
                                 │
                        ┌────────┴────────┐
                        │                 │
                     [Valid]          [Invalid]
                        │                 │
                        ▼                 ▼
                 ┌──────────────┐   ┌────────────┐
                 │   Executor   │   │ Safe Error │
                 └──────┬───────┘   └────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ State Patch  │ (Camera Target & Visible Layers)
                 └──────┬───────┘
                        │
                        ▼
               GLOBE COMMAND BUS & CONTROLLER
                 (MapLibre 2D / Cesium 3D)
```

### 40.1 Flow Guarantees
1. **Sub-millisecond Fast Path**: Obvious commands (`reset`, `zoom in`, `show boundaries`) run deterministically in `< 0.02ms`, preserving GPU resources.
2. **Hard Renderer Isolation**: The LLM outputs typed Pydantic command schemas; it never invokes renderer methods directly or executes arbitrary code.
3. **Zero Coordinate Fabrication**: Place names pass through an embedded gazetteer; explicit coordinates are deterministically parsed and range-checked.
4. **Idempotency & Resilience**: Re-enabling an active layer is a `no_op`. Map remains operational with offline notice if Ollama is unreachable.

---

# 41. Temporal Exploration, AOI Selection & Observation Comparison Flow (`/explore`)

Phase 4 introduces multi-temporal satellite observation discovery, interactive Area of Interest (AOI) drawing, timeline scrubbing, and synchronized dual-observation comparison to Shanetra.

```text
                            EXPLORATION WORKSTATION
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
           INTERACTIVE AOI DRAWING              TEMPORAL SEARCH CONTROLS
        (Rectangle Box / Free Polygon)           (Date Range, Cloud Cover)
                    │                                     │
                    ▼                                     ▼
            GEOJSON VALIDATION                   DISCOVERY QUERY DISPATCH
         (POST /explore/aoi/validate)        (POST /explore/observations/search)
          - Max area: 250,000 km²                         │
          - Max vertices: 500                             ▼
          - Geodesic LAEA area                 STAC SEARCH & NORMALIZATION
          - SHA-256 geometry hash               - Copernicus STAC / Local Cache
                    │                           - ObservationSummary schema
                    │                           - Deterministic sort (DESC)
                    └──────────────────┬──────────────────┘
                                       │
                                       ▼
                             HORIZONTAL TIMELINE
                     (Scrubbing, Step Controls, Playback)
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
           INSPECT OBSERVATION                  SELECT OBSERVATION PAIR
         - Footprint boundary                 - Observation A (e.g. Baseline)
         - Metadata (Platform, Sun, Cloud)    - Observation B (e.g. Recent)
         - Asset preview & band mapping                   │
                                                          ▼
                                                COMPATIBILITY VALIDATOR
                                            (POST /explore/comparison/validate)
                                             - Spatial overlap check (> 0%)
                                             - Temporal delta calculation
                                             - Sensor alignment warnings
                                                          │
                                                          ▼
                                             DUAL-VIEW COMPARISON ENGINE
                                              - Mode: split / side_by_side / opacity
                                              - Draggable divider slider (0-100%)
                                              - cameraSyncBus: Loop-free 2-way sync
```

### 41.1 Detailed Interaction Sequences

#### Sequence A: AOI Selection & Geometry Governance
1. User clicks **"Draw Box"** or **"Draw Polygon"** in the floating `AOIToolbar`.
2. Map switches to draw mode; cursor transforms to crosshair.
3. User drags a rectangle or clicks vertices on the map canvas. Double-click or closing the ring completes the geometry.
4. The frontend calculates initial bounds and automatically submits the GeoJSON polygon to `/api/v1/explore/aoi/validate`.
5. Backend computes exact geodesic area via Lambert Azimuthal Equal Area (LAEA) projection centered on geometry centroid:
   - If area exceeds $250,000\text{ km}^2$, validation fails with actionable error message.
   - If vertices exceed $500$, adaptive Douglas-Peucker simplification reduces vertex count while preserving spatial envelope.
   - Computes deterministic SHA-256 geometry hash for cache deduplication.
6. Frontend updates AOI status pill with computed area (e.g. `1,420.5 km²`) and activates temporal search.

#### Sequence B: Multi-Temporal Observation Discovery
1. User opens the **Temporal Sidebar Tab** or floating `TemporalToolbar`.
2. Sets date range (e.g. `2024-01-01` to `2024-06-30`, max span 730 days) and maximum cloud cover threshold (e.g. `<= 20%`).
3. Clicks **"Discover Observations"**.
4. Backend executes `search_observations`:
   - Checks memory-bounded LRU cache using composite key `(geometry_hash, datetime, collections, max_cloud_cover)`.
   - On cache hit: returns in $< 20\text{ms}$.
   - On cache miss: queries Copernicus STAC API (`stac.dataspace.copernicus.eu/v1`) with fallback to local indexed GeoTIFFs.
   - Normalizes raw STAC items into compact `ObservationSummary` structures (stripping unused assets and properties to conserve bandwidth).
5. Results populate both the horizontal acquisition `Timeline` and the observation catalog list.

#### Sequence C: Timeline Scrubbing & Inspection
1. Horizontal `Timeline` plots observation badges along the time axis, color-coded by cloud cover.
2. Scrubbing or clicking an observation updates active selection state.
3. User can click **Play** to automatically advance through observations sequentially at configured speed (1s, 2s, 5s per step).
4. Clicking **"Inspect"** displays `ObservationDetails`: sensor platform, orbit direction, processing level, cloud cover percentage, and tile availability.

#### Sequence D: Synchronized Observation Comparison
1. User marks first observation as **"Set as Observation A"** (Baseline) and second observation as **"Set as Observation B"** (Comparison).
2. Frontend calls `/api/v1/explore/comparison/validate`:
   - Validates that $A \neq B$.
   - Computes intersection bounding box and spatial overlap percentage.
   - Calculates exact temporal delta (e.g. `+45 days`).
   - Assesses sensor compatibility (e.g. Optical vs Optical, or Sentinel-2 vs Landsat-8).
3. User selects comparison mode:
   - **Split View**: A single viewport divided by a draggable vertical slider. Left side renders Observation A; right side renders Observation B using CSS clip-path or synchronized dual canvas.
   - **Side-by-Side**: Two adjacent viewports for direct parallel inspection.
   - **Opacity Fade**: A single viewport with an opacity slider blending Observation B over Observation A.
4. **Loop-Free Camera Synchronization**:
   - As user pans or zooms either map, `cameraSyncBus` broadcasts `{ center, zoom, bearing, pitch }` accompanied by a unique `originToken`.
   - The opposing map updates its camera only if the event token originated from the other instance, preventing recursive ping-pong loops.

#### Sequence E: AI Temporal Commands
1. User types natural-language commands in the Query Bar:
   - *"Select area around coordinates 79.08, 21.14"* $\rightarrow$ `SET_AOI`
   - *"Show observations from last month with less than 15% clouds"* $\rightarrow$ `SET_DATE_RANGE` + `search`
   - *"Compare latest observation with previous"* $\rightarrow$ `COMPARE_OBSERVATIONS(mode="split")`
2. AI Command Validator checks parameters against strict bounds before invoking the Command Executor.

### 41.2 Performance & Boundary Guarantees
- **Zero Full-Raster Download**: Browser never loads full Multi-spectral GeoTIFFs; imagery is rendered through 256×256 WebP/PNG dynamic windowed tiles.
- **Cache Acceleration**: Multi-temporal searches for repeated AOIs achieve $200\times+$ speedups via SHA-256 hash caching.
- **Strict Separation from `/analysis`**: All temporal exploration, AOI drawing, and split comparison workflows operate entirely within `/explore`. Zero changes, zero state leakage, and zero regressions to existing `/analysis` specialist pipelines.

---

## 42. Phase 5: EO Analytical Intelligence Workstation User Flow

```text
  ┌──────────────────┐
  │   AOI Polygon    │
  │        +         │
  │ Observation A/B  │
  │        +         │
  │   User Query     │
  └────────┬─────────┘
           ▼
  ┌──────────────────┐
  │ Pre-flight Check │ ──── (Bounds, Cloud Mask, Memory Headroom)
  └────────┬─────────┘
           ▼
  ┌──────────────────┐
  │  7-Stage Pipeline│ ──── (Windowed Preprocessing → Model Inference → Evidence Extraction)
  └────────┬─────────┘
           ▼
  ┌────────────────────────────────────────────────────────────┐
  │          Interactive Analytical Workstation UI             │
  ├──────────────┬──────────────┬──────────────┬──────────────┤
  │   Findings   │   Evidence   │  Narrative   │  Artifacts   │
  │  (Map Focus) │  (Gate Math) │  (Executive) │  (GeoJSON)   │
  └──────────────┴──────────────┴──────────────┴──────────────┘
```

### 42.1 Workflow Steps

#### Step 1: Input Definition & Context Selection
- User selects an AOI on the 2D/3D map using the polygon drawing tool or uses full scene bounds.
- User selects Observation A (Baseline) and Observation B (Comparison) from the catalog or temporal acquisitions.
- In the sidebar's **Analysis** tab, user types an analytical objective or selects a quick preset:
  - *"Detect built-up change and new construction between observations"* (`BI_TEMPORAL`)
  - *"Evaluate flood water extent using radar penetration and optical reflectance"* (`SAR_OPTICAL`)
  - *"Detect and count all aircraft on the runway"* (`SINGLE_IMAGE`)

#### Step 2: Pre-flight Feasibility Validation
- User clicks the validation check button (`POST /api/v1/explore/analysis/validate`).
- Backend inspects spatial intersection, resolution matching, estimated pixel count, and estimated runtime.
- Pre-flight banner displays validation status (e.g., `Feasibility Check Passed • ~4.5s`).

#### Step 3: Asynchronous Pipeline Execution
- User clicks **"Execute Analytical Engine"** (`POST /api/v1/explore/analysis`).
- Job is enqueued (HTTP 202 Accepted) and assigned a unique `run_id`.
- Frontend state manager begins polling `/api/v1/explore/analysis/{run_id}` every 1.5 seconds.
- The **AnalysisProgress** component displays a live multi-stage tracker:
  1. `Validation` $\to$ 2. `Assets` $\to$ 3. `Preprocessing` $\to$ 4. `Inference` $\to$ 5. `Evidence` $\to$ 6. `Reasoning` $\to$ 7. `Finalize`.
- User can cancel the job at any point via the **Cancel** button (`POST /api/v1/explore/analysis/{run_id}/cancel`).

#### Step 4: Analytical Findings & Interactive Map Focus
- Upon completion, the console switches to the results view.
- Under the **Findings** tab, structured finding cards appear sorted by confidence and significance.
- Each finding card displays title, category, calibrated confidence meter, summary statement, and key quantitative metrics (e.g. `25.0 ha changed`).
- Clicking **"Focus on Map"** on any finding dispatches `FOCUS_ANALYSIS_REGION` through `globeCommandBus`:
  - MapLibre (2D) smoothly zooms and pans to the exact bounding box of the finding using `fitBounds`.
  - Cesium (3D) flies the camera to the geographic rectangle with a 1.5s transition.

#### Step 5: Raw Numerical Evidence Inspection
- Under the **Evidence** tab, user reviews the verifiable mathematical proofs:
  - Vector change regions with exact pixel counts and centroid coordinates.
  - Spectral index distributions ($\Delta \text{NDVI}$, baseline vs comparison mean).
  - Cross-modal joint agreement scores (Optical support score vs SAR support score).
  - Mathematical verification proofs passed by the consistency gatekeeper.

#### Step 6: Structured Report & Narrative
- Under the **Report** tab, user reads the Ollama-generated narrative (or deterministic fallback):
  - Executive Summary outlining the primary analytical conclusion.
  - Methodology documenting the model and preprocessing path.
  - Confidence Explanation contextualizing data quality vs model confidence.

#### Step 7: Artifact Downloads & Vector GeoJSON Export
- Under the **Files** tab, user can download:
  - `regions.geojson`: Polygon vectors of all detected change regions with feature properties for GIS import (QGIS, ArcGIS).
  - `manifest.json`: Full provenance audit trail with deterministic SHA-256 processing hash.
  - `annotated_preview.png`: High-resolution visual inspection image with marked detections.
  - Copy URL buttons allow sharing artifact links directly.



