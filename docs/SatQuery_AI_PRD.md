PRODUCT REQUIREMENTS DOCUMENT

SatQuery AI

SIH 2026 • Problem Statement 26167
Agentic Vision-Language Assistant for Multimodal Remote-Sensing Image Analysis

| Product | SatQuery AI |
| --- | --- |
| Problem Statement | 26167 |
| Organization | Indian Space Research Organisation (ISRO) |
| Department | Department of Space / ISRO |
| Category / Theme | Software / Space Technology |
| Document purpose | Build specification, acceptance criteria, evaluation readiness and implementation roadmap |

## 1. Executive Summary

SatQuery AI is an interactive web/GUI application that lets users analyse remote-sensing imagery using natural-language queries. The product must go beyond a generic LLM/VLM: it must contain at least one remote-sensing-adapted visual or vision-language component and an agentic controller that automatically selects and executes specialist models/tools based on the query and input image configuration.

The product must support four input situations: a single optical/multispectral or SAR image; a co-registered optical–SAR pair; a bi-temporal pair; and approved benchmark image formats. The system must demonstrate single-image VQA, one additional single-image task, multitemporal change understanding, optical–SAR joint analysis, and agentic orchestration.

## 2. Product Scope & Source of Truth

This PRD is based on the supplied SIH 2026 Problem Statement 26167. Requirements marked MUST/SHALL are treated as mandatory because they are stated as mandatory or required in the PS. Items marked SHOULD/RECOMMENDED are product/engineering recommendations added to make the implementation stronger; they are not claimed to be official ISRO requirements.

## 3. Product Goals

- Enable non-expert users to ask meaningful remote-sensing questions in natural language.

- Automatically route each request to the appropriate specialist remote-sensing workflow.

- Support reliable reasoning over single-image, bi-temporal and optical–SAR multimodal imagery.

- Provide evidence-grounded answers rather than unsupported text-only responses.

- Make model/tool execution auditable through an observable execution summary.

- Produce a reproducible, benchmark-ready system suitable for public benchmark and ISRO/SAC evaluation.

## 4. Non-Goals

- Replacing a full GIS platform.

- Supporting arbitrary sensor types beyond the declared scope without a corresponding model/workflow.

- Using a generic LLM/VLM as the only intelligence layer.

- Exposing internal chain-of-thought as a product feature; the PS evaluates observable execution information instead.

- Building a system dependent on hidden evaluation annotations.

## 5. Target Users

| Persona | Need | Success |
| --- | --- | --- |
| Non-expert analyst | Ask satellite-image questions without knowing model/GIS terminology. | Receives understandable answer + evidence. |
| Remote-sensing researcher | Run specialist analysis across modalities and time. | Gets reproducible outputs and execution metadata. |
| Evaluator/judge | Verify required capabilities quickly. | Can test every mandatory workflow from the UI. |
| Developer/admin | Add or replace specialist models. | Can register tools/models without rewriting the controller. |

## 6. Core Use Cases

### UC-01 Single-image VQA

User uploads one optical/multispectral or SAR image, asks a question, and receives an answer with confidence and evidence.

### UC-02 Scene description

User asks the system to describe land cover and major objects/features in an image.

### UC-03 Text-guided grounding

User asks to highlight a named/referred region such as a water body; system returns spatial evidence.

### UC-04 Temporal change

User uploads two corresponding dates and asks what changed and where; system returns a change answer/description and spatial evidence where supported.

### UC-05 Optical–SAR joint analysis

User uploads co-registered optical and SAR images and asks for complementary information such as built-up/water interpretation.

### UC-06 Agentic routing

User submits different queries and the system automatically selects different specialist tools.

### UC-07 Export

User downloads a report containing query, inputs, selected workflow/models, result, evidence and confidence.

## 7. Functional Requirements — Inputs

- FR-IN-01 MUST accept a single optical/multispectral image.

- FR-IN-02 MUST accept a single SAR image.

- FR-IN-03 MUST accept a co-registered optical/multispectral + SAR pair.

- FR-IN-04 MUST accept a bi-temporal pair of spatially corresponding images.

- FR-IN-05 MUST support GeoTIFF/TIFF for geospatial imagery.

- FR-IN-06 MAY accept PNG/JPEG only for prescribed public benchmark datasets.

- FR-IN-07 MUST validate image count, modality, format, metadata and compatibility before specialist execution.

- FR-IN-08 MUST clearly report invalid/incompatible inputs rather than silently continuing.

## 8. Functional Requirements — AI Capabilities

### 8.1 Remote-Sensing Adaptation

- FR-AI-01 MUST fine-tune or otherwise adapt at least one visual/VLM component using BigEarthNet.txt or other open-source training data.

- FR-AI-02 MUST document the base model, adaptation method, data, configuration and evaluation.

- FR-AI-03 MUST integrate the adapted component into the live product.

### 8.2 Single-Image VQA

- FR-AI-04 MUST support visual question answering on a single optical/multispectral or SAR image.

- FR-AI-05 MUST return an answer and confidence information.

- FR-AI-06 SHOULD provide visual evidence when the selected model supports spatial evidence.

### 8.3 Additional Single-Image Task

- FR-AI-07 MUST implement at least one of captioning/scene description OR text-guided region grounding.

- FR-AI-08 RECOMMENDED: implement both to strengthen coverage and agent routing.

### 8.4 Bi-Temporal Change

- FR-AI-09 MUST support change description OR change-based VQA from a bi-temporal pair.

- FR-AI-10 SHOULD generate a spatial change map/overlay when reference masks or an appropriate model output are available.

- FR-AI-11 MUST make the location of change interpretable through visual evidence where supported.

### 8.5 Optical–SAR

- FR-AI-12 MUST jointly analyse co-registered optical/multispectral and SAR imagery.

- FR-AI-13 MUST extract complementary information rather than treating the two images as unrelated single-image requests.

## 9. Functional Requirements — Agentic Orchestration

The controller is a first-class product component.

1. FR-AG-01 Interpret the natural-language query.

1. FR-AG-02 Classify the requested task.

1. FR-AG-03 Inspect the supplied input configuration.

1. FR-AG-04 Select one or more specialist models/tools from a predefined registry.

1. FR-AG-05 Configure only permitted task parameters.

1. FR-AG-06 Execute the selected workflow.

1. FR-AG-07 Combine textual and spatial outputs.

1. FR-AG-08 Estimate/return confidence.

1. FR-AG-09 Produce visual evidence.

1. FR-AG-10 Produce an auditable execution summary containing selected task, model/tool names, key parameters and outputs.

Acceptance principle: a judge should be able to observe the routing outcome without needing access to hidden reasoning.

## 10. Specialist Tool Registry

| Tool ID | Capability | Input | Output | Trigger |
| --- | --- | --- | --- | --- |
| validator | Input compatibility | Files + metadata | Validation result | Always first |
| rs_vqa | Remote-sensing VQA | Single image + question | Answer + confidence + evidence | Question/answer intent |
| rs_caption | Scene description | Single image | Caption/scene summary | Description intent |
| rs_ground | Text-guided grounding | Single image + phrase | Box/mask/region | Highlight/locate intent |
| change_ai | Change understanding | Bi-temporal pair + query | Change answer/description + evidence | Temporal intent |
| optical_sar | Cross-modal analysis | Optical + SAR pair | Joint interpretation + evidence | Multimodal intent |
| report | Report generation | Final result + trace | Downloadable report | User export |

## 11. UX / UI Requirements

- UX-01 Landing screen clearly explains supported input types and example queries.

- UX-02 Upload component supports single image and paired-image workflows.

- UX-03 Query box accepts natural-language requests.

- UX-04 UI shows detected input configuration and validation status.

- UX-05 UI shows selected task/workflow.

- UX-06 Results screen shows answer, confidence and visual evidence.

- UX-07 Paired workflows provide side-by-side/synchronized visualization where practical.

- UX-08 Grounding/change outputs are rendered as overlays where available.

- UX-09 Execution trace shows selected task, model/tool names and key parameters.

- UX-10 User can download a report.

- UX-11 Errors are actionable and understandable.

## 12. Output Contract

Every successful analysis should return a structured result with at least:

- request_id

- input summary: files, modality, temporal/cross-modal configuration

- validated metadata/compatibility status

- selected task

- models/tools executed

- key permitted parameters

- answer/description

- confidence or quality information

- spatial evidence: bounding boxes, masks, change maps or overlays where applicable

- execution status and timing

- report/export reference

## 13. Data & Benchmark Requirements

| Dataset / Set | PS role | PRD requirement |
| --- | --- | --- |
| BigEarthNet.txt | Primary dataset for adapting image–text representations. | Use it or other open-source training data for at least one adaptation component. |
| VRSBench | Evaluate single-image captioning, grounding and VQA. | Keep evaluation pipeline ready for prescribed test subset. |
| RSVQA | Evaluate single-image captioning, grounding and VQA. | Support reproducible evaluation. |
| CDVQA | Evaluate multitemporal change-based VQA. | Support paired temporal evaluation. |
| ISRO/SAC evaluation dataset | Pre-georeferenced/co-registered Cartosat-2S optical and RISAT SAR pairs with task-specific references; annotations not disclosed. | System must generalize to unseen evaluation data and robustly handle optical–SAR pairs. |

## 14. Recommended System Architecture

Recommended implementation architecture; this section is engineering guidance rather than an official PS specification.

- Frontend: React/Next.js or equivalent.

- Backend API: FastAPI or equivalent.

- Agent controller: deterministic intent/task classifier + workflow planner + tool registry + executor.

- Model services: remote-sensing-adapted VLM plus specialist VQA, captioning, grounding, change and optical–SAR components.

- Geospatial service: raster loading, metadata inspection, compatibility/co-registration checks and visualization.

- Evidence service: converts model outputs into overlays, boxes, masks and map-ready artifacts.

- Evaluation service: benchmark runner, metrics and experiment logging.

- Report service: structured JSON + PDF/HTML export.

- Deployment: containerized and reproducible.

## 15. Non-Functional Requirements

| Area | Requirement | Acceptance target |
| --- | --- | --- |
| Reliability | Invalid inputs must not produce silently misleading outputs. | Deterministic validation + clear errors. |
| Auditability | Every result must expose execution information. | Task/model/tool/parameter trace present. |
| Reproducibility | Same inputs/config should be reproducible. | Versioned model/config and recorded parameters. |
| Extensibility | Specialists can be added independently. | Registry-based tool interface. |
| Usability | A judge can run core workflows without developer assistance. | Simple guided UI. |
| Geospatial integrity | Paired imagery must remain spatially meaningful. | Metadata/compatibility validation. |
| Generalization | System should not depend on hidden evaluation labels. | No hard-coded evaluation answers. |
| Performance | Interactive use should be practical. | Show progress/status for long-running inference; exact latency target to be established during implementation. |

## 16. Product Acceptance & Evaluation Matrix

| Requirement | Pass condition | Demo evidence | Severity |
| --- | --- | --- | --- |
| Remote-sensing adaptation | At least one visual/VLM component demonstrably adapted. | Model card/training log + live inference. | BLOCKER |
| Single-image VQA | Correct workflow executes on single image. | Live query + result. | BLOCKER |
| Additional single-image task | Captioning or grounding works. | Live demo. | BLOCKER |
| Bi-temporal change | Change description or change-VQA works. | Two-date demo + evidence. | BLOCKER |
| Optical–SAR | Joint analysis works on co-registered pair. | Paired demo. | BLOCKER |
| Agentic orchestration | Controller selects specialist workflow based on query/input. | Execution trace. | BLOCKER |
| Input validation | Bad inputs are caught. | Invalid-input demo. | BLOCKER |
| Visual evidence | Evidence shown when supported. | Overlay/map/image evidence. | HIGH |
| Confidence | Confidence information returned. | Result UI. | HIGH |
| Downloadable report | Report generated from result. | Export demo. | HIGH |
| Benchmark readiness | Prescribed test subsets can be evaluated. | Evaluation command/report. | HIGH |

## 17. Judge Demo Script

1. Upload a single remote-sensing image and ask: “Describe the land-cover and major objects visible in this image.”

1. Ask a VQA question against the same image and show the selected VQA specialist.

1. Ask: “Highlight the water body referred to in the query.” and show grounding evidence if implemented.

1. Upload two dates and ask: “What changed between these two dates, and where did the change occur?” Show change evidence.

1. Upload optical + SAR pair and ask: “Use the optical and SAR images together to identify built-up and water-covered regions.”

1. Open the execution summary and show task selection, model/tool names and key parameters.

1. Download the final report.

## 18. Development Roadmap

### Phase 1 — Foundation

Repository, architecture, GeoTIFF/TIFF ingestion, metadata validation, UI skeleton, tool registry.

### Phase 2 — Single-image baseline

Remote-sensing adaptation + VQA + captioning/grounding.

### Phase 3 — Paired analysis

Bi-temporal change workflow + optical–SAR workflow.

### Phase 4 — Agent

Query classifier, routing, execution, integration and trace.

### Phase 5 — Evidence & reports

Overlays, confidence, report generation, polished UI.

### Phase 6 — Evaluation

Benchmark runners, test cases, robustness tests, ISRO/SAC-style unseen-data testing.

### Phase 7 — SIH hardening

Containerization, demo script, documentation, fallback paths, performance and reliability testing.

## 19. Key Risks & Mitigations

Generic-model risk: Ensure at least one genuine remote-sensing adaptation component is trained/adapted and integrated.

Agent is cosmetic: Make routing observable and actually execute different specialists.

Paired-image mismatch: Validate modality, metadata, spatial correspondence and configuration before inference.

Hallucinated answers: Use evidence, confidence and specialist models; flag low-confidence outputs.

Demo-only system: Run prescribed benchmark tests and unseen-style evaluation before SIH.

Hardware constraints: Use modular model services, quantization where appropriate, caching and configurable inference backends.

Model dependency: Maintain registry metadata and at least one fallback path per critical workflow where feasible.

## 20. Definition of Done

- All mandatory PS capabilities pass end-to-end tests.

- At least one remote-sensing visual/VLM component is adapted and integrated.

- Single-image VQA is functional.

- At least one additional single-image task is functional.

- Bi-temporal change analysis is functional.

- Optical–SAR joint analysis is functional.

- Agentic controller routes and executes specialist tools.

- Input validation is operational.

- Results include confidence and visual evidence where supported.

- Execution summary is visible and auditable.

- Downloadable report is functional.

- Benchmark evaluation scripts/results are reproducible.

- System can be deployed and demonstrated from a clean environment.

## 21. Product Vision

SatQuery AI should feel like a remote-sensing analyst, not a chatbot. It should understand what the user is asking, understand what imagery has been supplied, select the right specialist analysis, combine the resulting evidence, communicate uncertainty, and explain what was executed. The product succeeds when a judge can move from natural-language query to scientifically meaningful, visually supported remote-sensing insight through one coherent interface.

## 22. Traceability to the Supplied PS

The supplied PS identifies the problem as SatQuery AI, owned by ISRO/Department of Space, in the Software category and Space Technology theme. It explicitly defines the supported image configurations, mandatory functional scope, representative queries, agentic orchestration behaviour, expected GUI/backend solution, deliverables and evaluation approach. This PRD operationalizes those statements into product requirements, acceptance criteria and an implementation plan.
