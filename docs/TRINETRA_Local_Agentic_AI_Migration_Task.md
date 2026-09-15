# TRINETRA / SatQuery AI — Local Agentic AI Migration Task

## Purpose

This task is for **Antigravity / an AI coding agent** working on the existing **TRINETRA / SatQuery AI** repository for:

> **SIH 26167 — ISRO — SatQuery AI: Interactive Vision-Language Assistant for Multimodal Remote-Sensing Image Analysis**

The objective is to migrate the project from its current mixed/local + cloud LLM architecture to a **local-first, offline-capable, genuinely agentic AI architecture**.

The final system must use:

- **Ollama** for local LLM inference
- **Qwen 3.5:9B**
- **Qwen 3.5:4B**
- **Llama 3.2**
- **LangChain** for agent/tool orchestration and instrumentation
- **Langfuse** for tracing, monitoring, observability, evaluation support, and visualization of local agent executions
- Existing specialist remote-sensing models/tools
- Existing deterministic geospatial processing

## Critical research rule

Antigravity's knowledge may be outdated.

**Before making decisions about any current model, library, package, API, LangChain integration, Langfuse integration, Ollama model capability, or model availability, perform fresh web research.**

Do **not** rely only on pretrained knowledge.

For materially important technology decisions, prioritize current official sources:

1. Official Ollama documentation
2. Official Qwen / Hugging Face model cards
3. Official Meta / Llama documentation or model cards
4. Official LangChain documentation
5. Official Langfuse documentation
6. Official PyPI / npm / GitHub repositories
7. Official ISRO / Government of India material for ISRO-specific claims

Do not assume a model, API, package, or integration is still available merely because an older tutorial, README, blog post, or training example mentions it.

---

# 1. NON-NEGOTIABLE ARCHITECTURE

The final architecture must be:

```text
                         USER
                           |
                           v
                  SATQUERY / TRINETRA UI
                           |
                           v
                      FASTAPI API
                           |
                           v
                 LANGCHAIN AGENT LAYER
                           |
               +-----------+-----------+
               |                       |
               v                       v
       LOCAL LLM ROUTER           TOOL REGISTRY
               |                       |
       +-------+-------+       +-------+----------------+
       |       |       |       |       |       |        |
       v       v       v       v       v       v        v
    Qwen3.5  Qwen3.5 Llama   VQA   Grounding Change Optical+SAR
      9B       4B     3.2     Tool    Tool      Tool      Tool
       \        |      /        \       |        |        /
        \       |     /          +------+--------+-------+
         \      |    /                  |
          +-----+---+                   v
                |                GEOSPATIAL ENGINE
                |               GDAL / Rasterio /
                |               NumPy / OpenCV
                |                      |
                +----------------------+
                           |
                           v
                    EVIDENCE ENGINE
                           |
                           v
                   CONFIDENCE ENGINE
                           |
                           v
                   LOCAL LLM SYNTHESIS
                           |
                           v
                       RESULT
                           |
              +------------+------------+
              |                         |
              v                         v
          FRONTEND                  LANGFUSE
          Evidence                  Traces
          Answer                    Spans
          Confidence                Generations
          Trace                     Tool calls
                                    Latency
                                    Errors
                                    Metadata
```

The system must not depend on an external LLM API for inference.

---

# 2. REMOVE GEMINI COMPLETELY

The old architecture contains a cloud Gemini tier.

Remove it completely.

Search the entire repository for:

```text
Gemini
gemini
GEMINI_API_KEY
GOOGLE_API_KEY
google.generativeai
google-genai
GoogleGenerativeAI
ChatGoogleGenerativeAI
gemini-1.5
gemini-1.5-flash
gemini-2
```

Also inspect:

```text
requirements.txt
pyproject.toml
package.json
package-lock.json
pnpm-lock.yaml
yarn.lock
.env
.env.example
Dockerfile
docker-compose.yml
README.md
docs/
backend/
frontend/
tests/
scripts/
```

Remove:

- Gemini imports
- Gemini providers
- Gemini configuration
- Gemini environment variables
- Gemini fallback code
- Gemini documentation
- Gemini model names
- Gemini-related frontend UI
- Gemini-related telemetry labels

After migration, the application must have **no active Gemini execution path** and no obsolete Gemini configuration.

---

# 3. REMOVE CLOUD LLM FALLBACKS

Do not replace Gemini with another cloud provider.

There must be:

```text
NO OpenAI API
NO Anthropic API
NO Google Gemini API
NO OpenRouter
NO Hugging Face Inference API
NO external LLM endpoint
NO browser-side cloud model calls
```

The agent's general-purpose LLM inference must be local through Ollama.

---

# 4. LOCAL MODEL SET

The project must support:

```text
qwen3.5:9b
qwen3.5:4b
llama3.2
```

Before implementation, verify with current official sources:

- exact Ollama tags
- current availability
- current context/tool/vision capabilities
- current resource requirements
- current invocation methods
- current LangChain-Ollama compatibility

Do not assume older Qwen naming conventions remain unchanged.

---

# 5. MODEL ROLES

Do not blindly send every request to the largest model.

Create a centralized model registry.

## Qwen 3.5 9B

Primary local reasoning/planning model.

Use for:

- complex query interpretation
- multi-step planning
- multi-tool orchestration
- difficult reasoning
- complex answer synthesis
- cross-modal reasoning
- complex change-analysis questions

Model key:

```text
qwen3.5:9b
```

## Qwen 3.5 4B

Fast local model.

Use for:

- simple intent classification
- lightweight routing
- structured extraction
- simple queries
- low-complexity response generation

Model key:

```text
qwen3.5:4b
```

## Llama 3.2

Secondary local model.

Use for:

- lightweight local language tasks
- local fallback between models
- simple structured classification where useful
- comparison/benchmarking

Model key:

```text
llama3.2
```

Do not assume Llama 3.2 is the preferred model for every workload.

---

# 6. LANGCHAIN IS REQUIRED

Use **LangChain** as the agent/tool/model integration framework.

Before implementation, freshly verify the current official LangChain API.

Do not use deprecated APIs merely because old tutorials use them.

Use current LangChain components for:

- LLM abstraction
- tool definitions
- agent/tool interaction
- structured outputs where appropriate
- callbacks/tracing/instrumentation
- model switching
- agent execution lifecycle

If the current LangChain ecosystem recommends **LangGraph** for explicit stateful agent workflows, evaluate it and use it if it materially improves the implementation.

Do not add unnecessary abstractions.

---

# 7. LANGFUSE IS REQUIRED

Use **Langfuse** for:

- tracing
- monitoring
- observability
- visualization
- latency tracking
- token/usage tracking when supported
- model-call tracing
- tool-call tracing
- agent-execution tracing
- errors
- metadata
- evaluation/debugging support

Important:

> Langfuse is the observability layer. It is not the scientific inference engine.

The source of truth for scientific outputs remains:

- specialist models
- deterministic geospatial operations
- evidence generation
- validated input data

Freshly verify the current official Langfuse integration with LangChain and Ollama before coding.

Do not use obsolete Langfuse callback APIs if the current SDK/integration has changed.

---

# 8. LOCAL / OFFLINE LANGFUSE

If the project requirement is:

> No external cloud services

then run Langfuse locally/self-hosted.

Verify the current official local/self-hosted installation path before implementation.

Target architecture:

```text
TRINETRA
 |
 +--> Ollama localhost:11434
 |
 +--> FastAPI localhost
 |
 +--> Self-hosted/local Langfuse
 |
 +--> Local specialist models
 |
 +--> Local geospatial engine
```

The core inference pipeline must be capable of operating without internet connectivity after required dependencies/models have been downloaded.

---

# 9. LANGCHAIN VS LANGFUSE

Do not describe them as interchangeable.

Use them as:

```text
LangChain
    =
agent / tool / model integration

Langfuse
    =
trace / monitor / observe / visualize / evaluate
```

Example:

```text
User Query
   |
   v
LangChain Agent
   |
   +--> Local Qwen
   |
   +--> Tool
   |
   +--> Specialist
   |
   v
Result

Langfuse observes the process.
```

---

# 10. CURRENT TRINETRA ARCHITECTURE TO PRESERVE

Inspect the existing repository before changing it.

Preserve functioning components wherever possible, including:

- FastAPI API
- Agent controller
- Intent classifier
- Tool registry
- Execution trace
- Geospatial reader
- Geospatial normalization
- Evidence overlay engine
- Validator
- VQA specialist
- Grounding specialist
- Captioning specialist
- Change specialist
- Optical-SAR specialist
- Report generator
- Model checkpoint loader
- Frontend
- Existing integration tests

Do not rewrite working scientific processing just to introduce LangChain.

The migration should improve orchestration while preserving remote-sensing functionality.

---

# 11. REFACTOR THE CURRENT LLM ENGINE

Inspect:

```text
backend/services/llm_engine.py
```

The previous architecture contains:

```text
Local Ollama
+
Cloud Gemini
+
fallback path
```

Replace it with:

```text
Local LLM Engine
```

The engine should expose a clean interface such as:

```python
generate()
structured_generate()
classify()
plan()
health_check()
get_model()
```

All general-purpose LLM requests must go through the local Ollama abstraction.

Do not let individual services instantiate random Ollama clients.

---

# 12. CREATE A SINGLE LOCAL LLM PROVIDER

Centralize local model access.

Recommended structure:

```text
backend/
  agent/
    controller.py
    planner.py
    router.py
    registry.py
    trace.py

  llm/
    provider.py
    model_registry.py
    ollama_client.py
    schemas.py
```

The rest of the application should call the provider abstraction rather than directly calling Ollama.

---

# 13. MODEL REGISTRY

Implement a registry similar to:

```python
LOCAL_MODELS = {
    "planner": {
        "provider": "ollama",
        "model": "qwen3.5:9b",
    },
    "fast_router": {
        "provider": "ollama",
        "model": "qwen3.5:4b",
    },
    "lightweight": {
        "provider": "ollama",
        "model": "llama3.2",
    },
}
```

Do not spread model strings throughout the codebase.

Use environment/configuration for model tags.

---

# 14. MAKE THE AGENT GENUINELY AGENTIC

The system must not simply do:

```text
User
 ↓
LLM
 ↓
Answer
```

The agent needs a real loop:

```text
UNDERSTAND
    ↓
PLAN
    ↓
VALIDATE
    ↓
SELECT TOOL(S)
    ↓
EXECUTE
    ↓
OBSERVE RESULT
    ↓
DECIDE NEXT STEP
    ↓
INTEGRATE EVIDENCE
    ↓
SYNTHESIZE
    ↓
RESPOND
```

The system must support multi-step tool use where the query requires it.

Different queries should produce different tool/model workflows.

---

# 15. QUERY ROUTING

Support at least:

```text
vqa
captioning
grounding
change_analysis
optical_sar_fusion
```

Examples:

```text
"What is visible in this image?"
→ vqa/captioning
```

```text
"Highlight the water body."
→ grounding
```

```text
"What changed between these two dates?"
→ change_analysis
```

```text
"Has the built-up area increased?"
→ change_vqa/change_analysis
```

```text
"Use the optical and SAR images together..."
→ optical_sar_fusion
```

The agent should infer task from:

- query
- number of images
- modalities
- image metadata
- temporal relationship
- available tools

---

# 16. DYNAMIC TOOL SELECTION

The agent must choose tools from the existing registry.

Expected tools:

```text
image_validation
metadata
vqa
captioning
grounding
change_analysis
optical_sar_fusion
evidence
report_generation
```

Do not hardwire every query to one fixed workflow when a different workflow is required.

---

# 17. TOOL SAFETY

The LLM must **never execute arbitrary code**.

The flow must be:

```text
LLM
 ↓
Structured tool request
 ↓
Agent Controller
 ↓
Tool Registry
 ↓
Schema validation
 ↓
Allowed parameters
 ↓
Tool execution
```

Reject:

- unknown tools
- invalid parameters
- unauthorized parameters
- arbitrary shell commands
- arbitrary Python generated by the LLM

---

# 18. STRUCTURED AGENT OUTPUT

Use typed/Pydantic schemas.

Example:

```json
{
  "intent": "change_analysis",
  "complexity": "medium",
  "required_tools": [
    "image_validation",
    "change_analysis",
    "evidence"
  ]
}
```

Validate every model-generated plan.

If structured output is invalid:

```text
Do not execute.
Record error.
Retry safely if configured.
Otherwise return truthful failure.
```

---

# 19. MULTI-STEP AGENT EXAMPLE

Input:

> “Compare these images, identify where vegetation decreased, and tell me whether built-up area expanded.”

Expected:

```text
Query Understanding
        ↓
Input Validation
        ↓
Plan
        ↓
Change Analysis
        ↓
Vegetation Analysis
        ↓
Built-up Analysis
        ↓
Evidence Integration
        ↓
Confidence
        ↓
Local LLM Synthesis
```

Langfuse must show each actual stage.

---

# 20. SINGLE-IMAGE VQA

Example:

> “What major objects are visible?”

Expected:

```text
Query
 ↓
Intent = VQA
 ↓
VQA Specialist
 ↓
Evidence
 ↓
Local LLM synthesis
 ↓
Answer
```

The result must be grounded in actual image-derived outputs.

---

# 21. TEXT-GUIDED GROUNDING

Example:

> “Highlight the water body.”

Expected:

```text
Query
 ↓
Intent = Grounding
 ↓
Grounding Specialist
 ↓
Bounding box / mask
 ↓
Evidence
 ↓
Answer
```

The LLM must not invent bounding boxes or masks.

---

# 22. BI-TEMPORAL CHANGE ANALYSIS

Example:

> “What changed between these two dates?”

Expected:

```text
Query
 ↓
Bi-temporal detected
 ↓
Input compatibility validation
 ↓
Change Specialist
 ↓
Change map / hotspots
 ↓
Evidence
 ↓
Local LLM synthesis
```

---

# 23. OPTICAL + SAR

Example:

> “Use the optical and SAR images together to identify built-up and water-covered regions.”

Expected:

```text
Query
 ↓
Optical + SAR detected
 ↓
Compatibility validation
 ↓
Optical-SAR specialist
 ↓
Optical processing
 ↓
SAR processing
 ↓
Cross-modal fusion
 ↓
Evidence
 ↓
Confidence
 ↓
Local LLM synthesis
```

Do not merely concatenate two independent responses.

---

# 24. REMOTE-SENSING MODELS REMAIN SPECIALISTS

Do not replace the remote-sensing specialist layer with a general-purpose LLM.

Keep:

```text
LLM
=
language + planning + orchestration
```

```text
Remote-Sensing Models
=
image understanding / domain inference
```

```text
Geospatial Engine
=
deterministic scientific computation
```

This separation must remain visible in architecture and documentation.

---

# 25. BIGEARTHNET / DOMAIN ADAPTATION

Preserve the remote-sensing adaptation work.

The generic local LLM does not replace the requirement for a domain-adapted vision-language component.

Inspect the existing training/checkpoint architecture and ensure the final pipeline still supports:

- BigEarthNet-based adaptation
- VQA
- captioning
- grounding
- change understanding
- optical-SAR analysis

Do not claim that Qwen/Llama is remote-sensing-adapted unless the repository contains actual fine-tuning/adaptation evidence.

---

# 26. EVIDENCE-FIRST RESULTS

The final answer must be based on evidence generated by specialist processing.

Correct flow:

```text
Specialist
 ↓
prediction
 ↓
evidence generation
 ↓
confidence
 ↓
LLM explanation
```

Not:

```text
LLM guesses
 ↓
fake evidence
```

The LLM is responsible for expressing the result, not fabricating scientific evidence.

---

# 27. CONFIDENCE

Do not allow the LLM to arbitrarily output confidence.

Confidence should derive from available evidence such as:

- specialist prediction confidence
- input validity
- evidence availability
- agreement between relevant signals
- quality of spatial alignment
- model-specific confidence

The LLM may explain the confidence, but should not invent it.

---

# 28. OBSERVABLE EXECUTION TRACE

Preserve the existing execution trace mechanism and connect it with LangChain/Langfuse.

Every analysis should record:

```text
analysis_id
query
task
input_type
models_used
tools_used
parameters
status
latency
errors
confidence
evidence
```

Example:

```text
Analysis: abc123

1. Query Interpretation
   Model: qwen3.5:4b
   Status: completed

2. Planning
   Model: qwen3.5:9b
   Status: completed

3. Validation
   Tool: image_validation
   Status: completed

4. Specialist
   Tool: change_analysis
   Status: completed

5. Evidence
   Tool: evidence
   Status: completed

6. Synthesis
   Model: qwen3.5:9b
   Status: completed
```

---

# 29. LANGFUSE TRACE DESIGN

Create one top-level trace per user analysis.

Suggested hierarchy:

```text
Trace: satquery_analysis_<id>

├── query_interpretation
│   └── qwen3.5:4b
│
├── agent_plan
│   └── qwen3.5:9b
│
├── validation
│
├── tool_execution
│   ├── vqa
│   ├── grounding
│   ├── change_analysis
│   └── optical_sar_fusion
│
├── evidence_generation
│
├── confidence_calculation
│
└── final_synthesis
    └── qwen3.5:9b
```

Only create spans relevant to the actual workflow.

Do not create fake spans.

---

# 30. LANGFUSE METADATA

Capture useful metadata:

```text
project = TRINETRA
analysis_id
task
input_type
model
model_version/tag
tool
tool_version
duration_ms
status
error_type
confidence
```

Where supported, capture:

```text
input tokens
output tokens
total tokens
generation latency
```

Do not store unnecessary secrets or personal information.

---

# 31. LANGCHAIN / LANGFUSE INTEGRATION

Before implementation:

1. Search current official LangChain docs.
2. Search current official Langfuse docs.
3. Confirm current LangChain-Langfuse integration.
4. Confirm current LangChain-Ollama integration.
5. Confirm current tracing/callback APIs.
6. Implement according to the current API, not an old tutorial.

Do not copy an outdated blog implementation without verification.

---

# 32. FRONTEND TRACE DISPLAY

The frontend must not show chain-of-thought.

It should show observable system events:

```text
✓ Query received
✓ Task identified
✓ Local model selected
✓ Input validated
✓ Specialist selected
● Running analysis
✓ Evidence generated
✓ Response synthesized
```

Optional technical metadata:

```text
Model:
Qwen3.5 9B

Tool:
Change Specialist

Runtime:
1.27 s

Status:
Completed
```

---

# 33. SYSTEM STATUS

Implement/update:

```text
GET /api/v1/llm-status
```

Example response:

```json
{
  "ollama": {
    "connected": true
  },
  "models": {
    "qwen3.5:9b": true,
    "qwen3.5:4b": true,
    "llama3.2": true
  },
  "langfuse": {
    "connected": true
  },
  "cloud_llm": false
}
```

Use actual runtime status.

---

# 34. STARTUP CHECKS

At startup verify:

```text
FastAPI
Ollama
Required models
LangChain
Langfuse
Geospatial dependencies
Specialist registry
Checkpoint availability
```

Example:

```text
TRINETRA AI SYSTEM

✓ FastAPI
✓ Ollama connected
✓ Qwen3.5 9B
✓ Qwen3.5 4B
✓ Llama 3.2
✓ LangChain
✓ Langfuse
✓ Geospatial engine
✓ Specialist registry

LOCAL AI SYSTEM READY
```

Do not report a dependency as ready if it is unavailable.

---

# 35. OLLAMA MODEL MANAGEMENT

After verifying current official model tags, document commands such as:

```bash
ollama pull qwen3.5:9b
ollama pull qwen3.5:4b
ollama pull llama3.2
```

Also provide:

```bash
ollama list
ollama ps
```

Use verified current syntax.

---

# 36. HARDWARE-AWARE DESIGN

The development environment may have limited GPU/RAM.

Do not assume every model can be loaded simultaneously.

Design the system so that:

- only necessary models are invoked
- routing is deliberate
- heavy specialist models can run sequentially
- generation parameters are configurable
- timeouts are explicit
- out-of-memory errors are surfaced honestly

Do not hide memory failures.

---

# 37. NO FAKE FALLBACK

If:

```text
Ollama unavailable
```

return:

```text
Local AI backend unavailable.
```

If:

```text
model missing
```

return:

```text
Required local model is unavailable.
```

If:

```text
specialist fails
```

return:

```text
Required specialist analysis could not be completed.
```

Do not fabricate satellite-analysis answers.

---

# 38. REMOVE DEMO FALLBACKS FROM PRODUCTION PATH

Inspect the frontend/backend behavior that currently falls back to interactive scenario demos when the backend is unavailable.

The production analysis path must clearly distinguish:

```text
LIVE ANALYSIS
```

from:

```text
DEMO MODE
```

A failed real analysis request must not silently return a mock answer.

If a demo mode remains for presentations, it must be explicitly selected and clearly labeled.

---

# 39. FRONTEND STATUS

Replace cloud/Gemini wording with:

```text
LOCAL AI READY
```

Optional status details:

```text
Ollama
Connected

Qwen3.5 9B
Ready

Qwen3.5 4B
Ready

Llama 3.2
Ready

Langfuse
Connected
```

Never expose secrets.

---

# 40. REPORT CONTENT

Mission intelligence reports should display:

```text
AI Architecture

Agent Framework:
LangChain

LLM Runtime:
Ollama

Planner:
Qwen3.5 9B

Fast Router:
Qwen3.5 4B

Secondary Local Model:
Llama 3.2

Observability:
Langfuse

Specialist:
<actual specialist used>

Evidence:
<actual evidence generated>

Confidence:
<actual confidence>

Execution:
<actual trace>
```

Do not mention Gemini.

Do not claim a model/tool was used if it was not actually used.

---

# 41. API CONTRACT

Maintain clean boundaries.

Example request:

```json
{
  "query": "What changed between these two dates?",
  "input_type": "bi_temporal",
  "images": [
    {
      "id": "image-t1",
      "name": "image_t1.tif",
      "modality": "optical"
    },
    {
      "id": "image-t2",
      "name": "image_t2.tif",
      "modality": "optical"
    }
  ]
}
```

Example response:

```json
{
  "analysis_id": "abc123",
  "status": "completed",
  "task": "change_analysis",
  "answer": "Built-up area increased in the northern region.",
  "confidence": {
    "score": 0.88,
    "label": "high"
  },
  "evidence": [],
  "execution_trace": [],
  "models_used": [],
  "tools_used": []
}
```

Update actual schemas to match the repository where needed, avoiding unnecessary breaking changes.

---

# 42. TESTING

Create/modify tests for:

## Model routing

```text
simple query → qwen3.5:4b
complex query → qwen3.5:9b
lightweight path → llama3.2
```

## Tool routing

```text
VQA → VQA tool
Grounding → grounding tool
Change → change tool
Optical+SAR → fusion tool
```

## Local-only requirement

Verify that no cloud provider can be selected.

## Invalid tool selection

Reject unknown tools.

## Invalid structured plan

Reject invalid plans.

## Ollama unavailable

Return truthful failure.

## Missing model

Return truthful failure.

## Langfuse instrumentation

Verify traces are generated for agent analysis flows.

## Frontend

Verify all four major workflows.

---

# 43. REQUIRED DEMO SCENARIOS

The final application must support:

## Scenario 1 — Single-image VQA

> “What major objects are visible in this image?”

## Scenario 2 — Grounding

> “Highlight the water body.”

## Scenario 3 — Bi-temporal

> “What changed between these two dates, and where did the change occur?”

## Scenario 4 — Optical + SAR

> “Use the optical and SAR images together to identify built-up and water-covered regions.”

For each scenario verify:

```text
Local LLM
 ↓
LangChain agent
 ↓
Tool selection
 ↓
Specialist execution
 ↓
Evidence
 ↓
Confidence
 ↓
Final answer
 ↓
Langfuse trace
```

---

# 44. MULTI-MODEL ROUTING POLICY

Implement a configurable routing policy rather than arbitrary permanent hardcoding.

Example:

```python
if complexity == "simple":
    model = fast_model

elif complexity == "complex":
    model = planner_model
```

The actual routing policy must be benchmarked.

Benchmark the three models on representative SatQuery tasks.

Record:

- latency
- success rate
- structured-output reliability
- tool-call reliability
- answer quality
- memory usage

Use evidence from these benchmarks to refine routing.

---

# 45. MODEL BENCHMARK VIEW

Retain/create a developer evaluation view showing:

```text
Model
Task
Latency
Success Rate
Tool-call Reliability
Structured Output Success
```

Do not hardcode performance claims before benchmarking.

---

# 46. LOGGING

Use structured logs.

Example:

```text
analysis_id=abc123
event=tool_selected
task=change_analysis
tool=change_analysis
model=qwen3.5:9b
status=selected
```

Avoid duplicating huge amounts of telemetry unnecessarily when Langfuse already captures it.

---

# 47. ERROR HANDLING

Implement explicit errors for:

- Ollama connection failure
- missing model
- malformed model response
- invalid tool arguments
- unavailable specialist
- unsupported input
- incompatible image pair
- Langfuse connection failure

A Langfuse outage should not corrupt a valid scientific analysis.

---

# 48. LANGFUSE FAILURE POLICY

Important:

```text
Scientific analysis
    should NOT depend on Langfuse availability.
```

If Langfuse is unavailable:

```text
Analysis may continue
+
local application trace remains available
+
warning is logged
```

Do not make a valid remote-sensing analysis fail solely because observability is unavailable.

---

# 49. LOCAL TRACE + LANGFUSE

Maintain both:

```text
Application ExecutionTrace
+
Langfuse Trace
```

Reason:

- frontend needs a compact application-level trace
- Langfuse needs deeper observability
- reports may consume the application trace
- scientific audit data should not depend entirely on telemetry UI semantics

Keep both synchronized where practical.

---

# 50. DOCUMENTATION UPDATE

Update:

```text
README.md
.env.example
architecture docs
TRD
PRD
deployment docs
model docs
```

The documentation must describe:

```text
Local LLMs:
Qwen3.5 9B
Qwen3.5 4B
Llama 3.2

Runtime:
Ollama

Agent framework:
LangChain

Observability:
Langfuse

Cloud LLM:
None
```

Remove outdated Gemini documentation.

---

# 51. ARCHITECTURE DIAGRAM

Add a final architecture diagram similar to:

```text
User
 |
 v
SatQuery UI
 |
 v
FastAPI
 |
 v
LangChain Agent
 |
 +--> Qwen3.5 4B
 |
 +--> Qwen3.5 9B
 |
 +--> Llama 3.2
 |
 v
Tool Registry
 |
 +--> Validator
 +--> VQA
 +--> Captioning
 +--> Grounding
 +--> Change
 +--> Optical-SAR
 |
 v
Geospatial / ML Specialists
 |
 v
Evidence
 |
 v
Confidence
 |
 v
Final Local LLM Synthesis
 |
 +----------------------+
 |                      |
 v                      v
UI Result             Langfuse
                      Trace
                      Monitor
                      Visualize
```

---

# 52. CURRENT-INFORMATION RESEARCH WORKFLOW

Before coding any changing dependency:

```text
1. Search current official documentation
2. Confirm version
3. Confirm API
4. Confirm current model name/tag
5. Confirm integration method
6. Implement
7. Run tests
8. Record exact version in docs
```

This is mandatory for:

```text
Ollama
Qwen 3.5
LangChain
Langfuse
LangChain-Langfuse integration
LangChain-Ollama integration
```

Do not treat old examples as current truth.

---

# 53. DO NOT TRUST OLD CODE BLINDLY

For every relevant existing component ask:

```text
Is this still supported?
Is this API current?
Is this package current?
Is this model tag current?
Does this integration still work?
```

Use fresh web research whenever the answer could have changed.

---

# 54. FINAL VALIDATION CHECKLIST

## Cloud removal

```text
[ ] No Gemini imports
[ ] No Gemini environment variables
[ ] No Gemini API calls
[ ] No Google LLM dependency
[ ] No other external LLM provider
```

## Local models

```text
[ ] qwen3.5:9b available
[ ] qwen3.5:4b available
[ ] llama3.2 available
```

## Agentic behavior

```text
[ ] Query interpretation
[ ] Planning
[ ] Dynamic tool selection
[ ] Tool execution
[ ] Observation
[ ] Multi-step workflow
[ ] Result synthesis
```

## Frameworks

```text
[ ] LangChain integrated
[ ] Langfuse integrated
[ ] Local/self-hosted Langfuse verified
```

## Scientific pipeline

```text
[ ] Validation
[ ] VQA
[ ] Captioning
[ ] Grounding
[ ] Change analysis
[ ] Optical-SAR analysis
[ ] Evidence
[ ] Confidence
```

## Frontend

```text
[ ] Local AI status
[ ] Execution trace
[ ] Result
[ ] Evidence
[ ] Confidence
[ ] No Gemini UI
[ ] No silent mock fallback
```

---

# 55. FINAL ACCEPTANCE TEST

Run:

```bash
ollama list
```

Confirm the required models.

Start the backend.

Start local/self-hosted Langfuse if required.

Run all four mandatory workflows.

For every workflow confirm:

```text
User
 ↓
FastAPI
 ↓
LangChain
 ↓
Local Ollama model
 ↓
Tool
 ↓
Remote-sensing specialist
 ↓
Evidence
 ↓
Confidence
 ↓
Local LLM synthesis
 ↓
Result
```

Then inspect Langfuse and confirm the trace is visible and correctly structured.

---

# 56. FINAL COMMANDS / README

At the end of the migration, provide an exact verified setup section.

Include current verified commands for:

```bash
# Ollama
ollama pull qwen3.5:9b
ollama pull qwen3.5:4b
ollama pull llama3.2

# Verify
ollama list

# Backend
<actual command>

# Frontend
<actual command>

# Langfuse
<verified current self-hosted command/process>
```

Do not invent commands. Verify them against current official documentation.

---

# 57. FINAL RESPONSE FROM THE CODING AGENT

After implementation, report:

## Changed

- Gemini removed
- Cloud inference removed
- Local model registry added
- LangChain integrated
- Langfuse integrated
- Agent routing upgraded
- Tool orchestration upgraded
- Local-only health checks added

## Models

List actual installed/verified models.

## Agent Flow

Describe actual execution flow.

## Langfuse

Describe actual trace structure.

## Tests

List tests run and their results.

## Known Limitations

Be honest.

## Current Status

State whether:

```text
LOCAL
OFFLINE-CAPABLE
AGENTIC
OBSERVABLE
```

is actually verified.

---

# 58. CORE PRINCIPLE

The final system must not be presented as:

> “A chatbot using Qwen.”

It must be presented as:

> **“A local agentic remote-sensing intelligence system where LangChain orchestrates local LLM reasoning and specialist tools, Ollama provides local model inference, Langfuse provides complete agent observability and visualization, and deterministic geospatial/remote-sensing engines provide evidence-grounded scientific analysis.”**

---

# 59. FINAL INSTRUCTION TO ANTIGRAVITY

Start by inspecting the existing TRINETRA repository.

Then perform fresh web research on current official documentation for:

- Qwen 3.5 models
- Ollama
- LangChain
- Langfuse
- LangChain + Langfuse
- LangChain + Ollama

Do not assume old model names, APIs, package versions, or cloud-provider availability.

Then:

1. Produce an implementation plan.
2. Migrate the repository.
3. Run tests.
4. Perform the four mandatory SatQuery flows.
5. Verify Langfuse traces.
6. Verify frontend/backend integration.
7. Search the repository one final time for Gemini references.
8. Remove remaining obsolete Gemini/cloud code.
9. Record verified package/model versions.
10. Provide a concise migration report.

The final application must be **local-first, genuinely agentic, LangChain-orchestrated, Langfuse-observable, evidence-grounded, and free of Gemini/cloud LLM inference dependencies.**
