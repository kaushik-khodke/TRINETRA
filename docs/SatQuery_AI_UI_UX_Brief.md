# SatQuery AI — UI/UX Brief

**SIH 2026 — Problem Statement 26167**  
**Product:** SatQuery AI  
**Design Goal:** Create a professional, intuitive and visually impressive interface for an agentic vision-language assistant that allows users to analyze remote-sensing imagery through natural-language queries.

---

# 1. Design Vision

SatQuery AI should feel like a **modern AI command center for satellite imagery**.

The interface must hide the complexity of:

- Remote-sensing preprocessing
- Multispectral/optical imagery
- SAR imagery
- VLMs
- Specialist AI models
- Agent orchestration
- Change detection
- Cross-modal fusion

while still making the important technical information visible.

## Core UX principle

> **Upload → Ask → Agent decides → AI analyzes → Evidence proves → Confidence informs**

The user should not need to select a model manually.

---

# 2. Target Users

## Primary

### Students / Developers

Need an easy way to test remote-sensing AI capabilities without deep GIS expertise.

### Researchers

Need to inspect imagery, model outputs, evidence and execution details.

### Non-Expert Users

Need to ask questions in natural language instead of learning GIS workflows.

### Evaluators / Judges

Need to immediately understand:

- What the system does
- Why it is agentic
- Which model/tool was selected
- What evidence supports the answer
- Whether single-image, bi-temporal and optical-SAR workflows work

---

# 3. UX Objectives

The interface should:

1. Make the product understandable within 5–10 seconds.
2. Make image upload extremely simple.
3. Automatically detect input configuration where possible.
4. Clearly communicate validation status.
5. Make natural-language interaction the primary control.
6. Make agentic orchestration visible.
7. Present AI answers before technical details.
8. Show visual evidence alongside textual results.
9. Show confidence without creating false certainty.
10. Provide an auditable execution summary.
11. Make paired-image analysis visually obvious.
12. Support downloadable reports.
13. Look professional enough for a competition/demo environment.

---

# 4. Visual Direction

## Design personality

**Professional + Scientific + Futuristic + Minimal**

Avoid making it look like:

- A generic chatbot
- A gaming dashboard
- A traditional GIS application
- A cluttered enterprise dashboard

Instead, combine:

```text
AI Interface
     +
Scientific Visualization
     +
Satellite / Geospatial Aesthetic
     +
Clean SaaS UX
```

---

# 5. Recommended Visual Language

## Colors

Use a dark-first interface with restrained accent colors.

### Base

- Deep navy / near-black background
- Dark blue-gray panels
- Light neutral text

### Accent

Use one primary cyan/blue accent for:

- Active states
- AI processing
- Primary buttons
- Selection outlines

Use secondary colors only for semantic states:

- Green → success
- Amber → warning
- Red → error
- Purple → AI/agent activity if needed

Do not overuse gradients.

---

# 6. Typography

Use a modern sans-serif typeface.

Recommended:

- Inter
- Geist
- Manrope
- IBM Plex Sans

## Hierarchy

```text
H1 → 36–48px
H2 → 24–32px
H3 → 18–22px
Body → 14–16px
Metadata → 12–13px
```

The interface should prioritize readability over decorative typography.

---

# 7. Layout System

Use a consistent 12-column responsive grid.

Recommended desktop structure:

```text
┌─────────────────────────────────────────────────────────────┐
│ TOP NAV                                                     │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│ SIDEBAR      │             MAIN CONTENT                     │
│              │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

Recommended spacing system:

```text
4px
8px
12px
16px
24px
32px
48px
64px
```

Use generous spacing around major sections.

---

# 8. Global Navigation

## Header

```text
┌─────────────────────────────────────────────────────────────┐
│ SATQUERY AI     New Analysis   History   Benchmarks   About │
│                                      ● System Ready         │
└─────────────────────────────────────────────────────────────┘
```

### Header elements

- SatQuery AI logo
- Current page
- System status
- Optional user/session information
- Help/about access

---

# 9. Landing Page

## Goal

Immediately communicate:

> **Ask questions about satellite imagery using natural language.**

## Layout

```text
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                       SATQUERY AI                            │
│                                                             │
│              Understand Earth from above.                   │
│                                                             │
│ Ask natural-language questions about remote-sensing        │
│ imagery using an agentic vision-language system.            │
│                                                             │
│                 [ START ANALYSIS ]                          │
│                                                             │
│  Single Image    Change Over Time    Optical + SAR          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Hero visual

Use a subtle satellite-image/grid visualization rather than a stock space illustration.

The visual should communicate:

- Earth observation
- Data
- AI
- Analysis

without distracting from the CTA.

---

# 10. Dashboard

The dashboard should be lightweight.

```text
┌─────────────────────────────────────────────────────────────┐
│ Welcome to SatQuery AI                                      │
│                                                             │
│ [ + New Analysis ]                                          │
│                                                             │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│ │ Analyses   │ │ Completed │ │ Avg. Conf. │               │
│ │     24     │ │     21     │ │    87%     │               │
│ └────────────┘ └────────────┘ └────────────┘               │
│                                                             │
│ Recent Analyses                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ VQA       Completed       91%                            │ │
│ │ Change    Completed       88%                            │ │
│ │ Optical+SAR Completed     86%                            │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

For the competition MVP, this page is secondary to the analysis workspace.

---

# 11. New Analysis — Primary Screen

This is the most important screen in the application.

## Recommended structure

```text
┌─────────────────────────────────────────────────────────────┐
│ New Analysis                                                │
├──────────────────────────┬──────────────────────────────────┤
│ INPUTS                   │ ASK SATQUERY AI                  │
│                          │                                  │
│ [ Upload ]               │ What do you want to know?        │
│                          │                                  │
│ Input Type               │ ┌──────────────────────────────┐ │
│ ○ Single Image           │ │ Type your question...        │ │
│ ○ Bi-Temporal            │ └──────────────────────────────┘ │
│ ○ Optical + SAR          │                                  │
│                          │ [ Analyze ]                       │
│ Uploaded Files           │                                  │
│ ✓ optical.tif            │ Example queries                  │
│ ✓ sar.tif                │                                  │
└──────────────────────────┴──────────────────────────────────┘
```

---

# 12. Upload Component

The upload area should be large and obvious.

```text
┌──────────────────────────────────────────┐
│                                          │
│              ↑                           │
│        Drop imagery here                 │
│                                          │
│        or [ Browse Files ]               │
│                                          │
│ GeoTIFF / TIFF supported                 │
│                                          │
└──────────────────────────────────────────┘
```

## Interaction

After selecting a file:

```text
image.tif
├── 4096 × 4096
├── GeoTIFF
├── Optical
└── ✓ Valid
```

For pairs, visually group the files.

---

# 13. Input Configuration Cards

Instead of plain radio buttons, use cards.

```text
┌───────────────────┐
│ 🛰 Single Image   │
│                   │
│ Ask about one     │
│ remote-sensing    │
│ image             │
└───────────────────┘

┌───────────────────┐
│ ↔ Change Over Time│
│                   │
│ Compare two dates │
└───────────────────┘

┌───────────────────┐
│ ◉ Optical + SAR   │
│                   │
│ Combine modalities│
└───────────────────┘
```

Selected card should have a clear border and background state.

---

# 14. Validation UX

Validation should appear directly below the uploaded images.

```text
INPUT CHECK

✓ File readable
✓ Supported format
✓ Metadata detected
✓ Modality detected
✓ Spatial compatibility
✓ Pair compatibility

STATUS: READY
```

Avoid showing technical logs by default.

Allow users to expand:

```text
[ View validation details ]
```

---

# 15. Query Composer

The query box is the heart of the UX.

## Design

Large input field:

```text
┌─────────────────────────────────────────────────────────────┐
│ Ask SatQuery AI anything about this imagery...              │
│                                                             │
│ "What changed between these two dates, and where?"          │
│                                                             │
│                                     [ Analyze → ]            │
└─────────────────────────────────────────────────────────────┘
```

## Suggested queries

Show contextual examples based on input type.

### Single image

- “What major objects are visible?”
- “Describe the land-cover.”
- “Highlight the water body.”

### Bi-temporal

- “What changed between these two dates?”
- “Has the built-up area increased?”
- “Where did the change occur?”

### Optical + SAR

- “Identify built-up regions.”
- “Identify water-covered regions.”
- “Use both images to describe the scene.”

---

# 16. Agent Processing Screen

The processing screen is important for demonstrating the agentic architecture.

Do not display chain-of-thought.

Instead show an **observable execution trace**.

```text
ANALYZING

✓ Input validated
✓ Query interpreted
✓ Task identified: Change Analysis
✓ Specialist selected: Change AI
● Running model
○ Generating evidence
○ Preparing response
```

This gives judges a clear view of orchestration.

---

# 17. Agent Trace Component

Use a compact vertical timeline.

```text
● Query received
│
● Input validated
│
● Task: Change Analysis
│
● Tool: Change Specialist
│
● Inference completed
│
● Evidence generated
│
✓ Result ready
```

Each item can optionally expand to show:

- Tool/model name
- Version
- Key permitted parameters
- Status
- Runtime

---

# 18. Result Page

The result page should prioritize the answer.

Recommended hierarchy:

```text
1. Answer
2. Evidence
3. Confidence
4. Input imagery
5. Execution summary
6. Metadata
7. Report/export
```

## Layout

```text
┌─────────────────────────────────────────────────────────────┐
│ ANALYSIS RESULT                                             │
├─────────────────────────────────────────────────────────────┤
│ QUERY                                                       │
│ What changed between these two dates?                       │
│                                                             │
│ ANSWER                                                      │
│ Built-up area increased in the northern region.             │
│                                                             │
│ Confidence: 88%  █████████████████░░                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ VISUAL EVIDENCE                                             │
│                                                             │
│                [ IMAGE / MAP VIEW ]                         │
│                                                             │
├──────────────────────────────┬──────────────────────────────┤
│ EXECUTION SUMMARY            │ INPUT INFORMATION             │
│ Change Specialist            │ T1 / T2                       │
│ Evidence Generator           │ GeoTIFF                       │
│ Completed                    │ Spatially aligned             │
└──────────────────────────────┴──────────────────────────────┘
```

---

# 19. Evidence-First Visualization

Evidence should be visually connected to the answer.

For example:

```text
Answer:
"Built-up area increased in the northern region."

            ↓

Image
┌──────────────────────────────────────────┐
│                                          │
│       █████ Change Region                │
│                                          │
│                         Built-up         │
│                                          │
└──────────────────────────────────────────┘
```

If bounding boxes or masks are available, show them directly.

---

# 20. Single Image UI

For a single image:

```text
┌───────────────────────────────────────────────┐
│ IMAGE VIEWER                                  │
│                                               │
│             [ Satellite Image ]               │
│                                               │
│     + Zoom     − Zoom     Reset     Evidence  │
└───────────────────────────────────────────────┘
```

Optional side panel:

```text
Detected Evidence

• Water body
• Built-up region
• Agricultural area
```

---

# 21. Bi-Temporal UI

The comparison experience should make the two dates visually comparable.

Recommended layout:

```text
┌──────────────────────┬─────────────────────────┐
│ DATE 1               │ DATE 2                  │
│                      │                         │
│ [ IMAGE T1 ]         │ [ IMAGE T2 ]            │
│                      │                         │
└──────────────────────┴─────────────────────────┘

                 CHANGE MAP

┌────────────────────────────────────────────────┐
│                                                │
│              [ Change Overlay ]                │
│                                                │
└────────────────────────────────────────────────┘
```

Controls:

```text
[ Side-by-Side ]
[ Swipe ]
[ Flicker ]
[ Change Overlay ]
```

The swipe/flicker interaction is especially useful for judge demonstrations.

---

# 22. Optical + SAR UI

Make modality differences visually obvious.

```text
┌──────────────────────┬─────────────────────────┐
│ OPTICAL              │ SAR                     │
│                      │                         │
│ [ Optical Image ]    │ [ SAR Image ]           │
│                      │                         │
└──────────────────────┴─────────────────────────┘

                    ↓

              JOINT ANALYSIS

                    ↓

┌────────────────────────────────────────────────┐
│ Combined Evidence                              │
│                                                │
│ [ Fusion / annotated result ]                  │
└────────────────────────────────────────────────┘
```

Add small modality labels directly on image cards.

---

# 23. Confidence Design

Confidence should be understandable, not intimidating.

```text
Confidence

88%

HIGH CONFIDENCE
```

Use a progress indicator or compact badge.

Avoid suggesting that a confidence score is equivalent to factual certainty.

For low confidence:

```text
⚠ Low confidence

The system is uncertain about this result.
Review the highlighted evidence before relying on it.
```

---

# 24. Empty States

## No analysis

```text
No analyses yet

Upload remote-sensing imagery and ask your
first question.

[ Start Analysis ]
```

## No history

```text
Your previous analyses will appear here.
```

## No evidence

```text
No visual evidence was generated for this task.
```

---

# 25. Error States

Errors should be actionable.

Bad:

```text
Error 500
```

Good:

```text
Unable to analyze the uploaded pair.

The two images could not be verified as spatially
compatible.

[ Replace Images ]
```

Possible errors:

### Unsupported file

```text
Unsupported file format.
Please upload GeoTIFF/TIFF imagery.
```

### Missing pair

```text
This workflow requires two corresponding images.
```

### Invalid optical-SAR pair

```text
The optical and SAR inputs could not be verified
as compatible for cross-modal analysis.
```

### Model failure

```text
The selected specialist could not complete the analysis.

[ Retry ]
[ Choose New Query ]
```

The system should never fabricate an answer after a failed specialist execution.

---

# 26. Loading States

Every long-running action needs a visible state.

```text
Validating imagery...
██████████░░░░░░

Preparing analysis...
████████████░░░░

Generating evidence...
██████████████░░

Finalizing result...
████████████████
```

Prefer meaningful stage names over a generic spinner.

---

# 27. Report / Export UX

Place export controls near the completed result.

```text
[ Download Report ↓ ]
```

Optional menu:

```text
Download Report
├── PDF
├── HTML
└── JSON
```

The report should contain:

- Query
- Input information
- Task
- Selected model/tool
- Key parameters
- Answer
- Confidence
- Evidence
- Execution summary

---

# 28. History UX

Use a clean table/card hybrid.

```text
RECENT ANALYSES

┌────────┬───────────────┬────────────┬────────────┐
│ TASK   │ INPUT         │ CONFIDENCE │ STATUS     │
├────────┼───────────────┼────────────┼────────────┤
│ VQA    │ Single Image  │ 91%        │ Completed  │
│ Change │ T1 + T2       │ 88%        │ Completed  │
│ Fusion │ Optical + SAR │ 86%        │ Completed  │
└────────┴───────────────┴────────────┴────────────┘
```

Clicking an item opens the complete result.

---

# 29. Benchmark UI

Benchmark functionality should look more technical than the user-facing analysis screen.

```text
BENCHMARKS

Dataset:
[ Select Dataset ]

Task:
[ Select Task ]

Split:
[ Test ]

[ RUN EVALUATION ]

Results

Accuracy / Task Metric
████████████████░░ 82%

Execution failures
2%

Average runtime
...
```

This page is primarily for the development/evaluation workflow.

---

# 30. Component Library

Create reusable components.

## Core

- Button
- Icon Button
- Badge
- Tooltip
- Modal
- Toast
- Tabs
- Dropdown
- Card
- Progress bar

## AI-specific

- Agent Trace
- Model Badge
- Confidence Badge
- Evidence Panel
- Analysis Status
- Query Composer
- Tool Execution Card

## Geospatial

- Image Viewer
- Map Viewer
- Layer Toggle
- Bounding Box
- Mask Overlay
- Compare Slider
- Opacity Control

---

# 31. Button Hierarchy

## Primary

Use for:

- Start Analysis
- Analyze
- Upload
- Download Report

Example:

```text
[ Analyze → ]
```

## Secondary

Use for:

- View Details
- Replace Image
- Retry

## Tertiary

Use for:

- Reset
- Close
- View Metadata

Avoid having multiple visually dominant buttons competing on one screen.

---

# 32. Interaction Principles

## Progressive disclosure

Show important information first.

```text
Answer
  ↓
Evidence
  ↓
Confidence
  ↓
Technical details
```

## Immediate feedback

Every upload, click and processing stage should produce visible feedback.

## No unnecessary configuration

The user should not have to choose:

- VQA model
- Captioning model
- Change model
- SAR model

The agent should select the appropriate specialist.

---

# 33. Accessibility

Minimum requirements:

- Sufficient text/background contrast
- Keyboard navigable controls
- Visible focus states
- Descriptive button labels
- Icons paired with text where ambiguity exists
- Do not communicate status by color alone
- Readable font sizes
- Clear error messages
- Alt text for non-decorative UI imagery

---

# 34. Responsive Design

## Desktop

Primary target.

```text
Sidebar + Workspace
```

## Tablet

```text
Collapsible sidebar
Stacked result panels
```

## Mobile

```text
Header
↓
Inputs
↓
Query
↓
Result
↓
Evidence
↓
Execution Summary
```

Remote-sensing comparison views should preserve usability even on smaller screens.

---

# 35. Judge-Optimized UX

The UI should make the mandatory PS capabilities obvious without explanation.

On the main screen, include three capability indicators:

```text
┌─────────────────┐
│ SINGLE IMAGE    │
│ VQA + GROUNDING │
└─────────────────┘

┌─────────────────┐
│ CHANGE ANALYSIS │
│ T1 ↔ T2         │
└─────────────────┘

┌─────────────────┐
│ OPTICAL + SAR   │
│ MULTIMODAL      │
└─────────────────┘
```

During processing, the agent trace should make the routing visible.

Example:

```text
Query
 ↓
Intent: Change Analysis
 ↓
Selected: Change Specialist
 ↓
Evidence: Change Map
 ↓
Result
```

This is much stronger for evaluation than a generic chatbot screen.

---

# 36. Recommended First-Time Demo Flow

The best live demonstration should require very few clicks.

```text
OPEN APP
  ↓
START ANALYSIS
  ↓
DROP IMAGE(S)
  ↓
VALIDATION ✓
  ↓
TYPE QUESTION
  ↓
ANALYZE
  ↓
AGENT TRACE
  ↓
RESULT
  ↓
SHOW EVIDENCE
  ↓
SHOW CONFIDENCE
  ↓
SHOW EXECUTION SUMMARY
```

The evaluator should understand the product without needing a long explanation.

---

# 37. Suggested UI Copy

## Hero

**Understand Earth from above.**

Supporting copy:

**Ask natural-language questions about remote-sensing imagery. SatQuery AI automatically selects the right specialist analysis and returns evidence-grounded results.**

## Main CTA

**Start Analysis**

## Query placeholder

**Ask anything about this imagery...**

## Processing

**SatQuery AI is analyzing your imagery**

## Result

**Analysis Complete**

## Evidence

**Visual Evidence**

## Trace

**Execution Summary**

## Report

**Download Analysis Report**

---

# 38. Do / Don't

## DO

- Keep the interface clean.
- Prioritize the imagery.
- Make the query box prominent.
- Show agent routing.
- Show evidence.
- Show confidence.
- Use meaningful loading states.
- Make paired-image analysis easy to understand.
- Keep technical details expandable.

## DON'T

- Turn the product into a generic chatbot.
- Force users to select models.
- Fill every screen with charts.
- Hide the evidence.
- Show internal chain-of-thought.
- Use excessive sci-fi decoration.
- Use too many colors.
- Overload the first screen with technical terms.
- Make judges search for the agentic workflow.

---

# 39. MVP Priority

| UI/UX Feature | Priority |
|---|---|
| Landing page | P0 |
| New Analysis workspace | P0 |
| Image upload | P0 |
| Input validation | P0 |
| Natural-language query | P0 |
| Agent processing trace | P0 |
| Single-image result | P0 |
| Bi-temporal result | P0 |
| Optical + SAR result | P0 |
| Evidence viewer | P0 |
| Confidence | P0 |
| Execution summary | P0 |
| Report download | P0 |
| History | P1 |
| Benchmark dashboard | P1 |
| Advanced settings | P2 |
| User profile/account | P2 |

---

# 40. Final UI/UX North Star

SatQuery AI should communicate one simple idea:

```text
                 SATQUERY AI

              "Upload your imagery."

                       ↓

               "Ask your question."

                       ↓

               "Let the agent decide."

                       ↓

               "See the evidence."

                       ↓

              "Understand the result."

                       ↓

               "Audit the workflow."
```

The winning interface is **not the one with the most features**.

It is the one where a judge can look at the screen and immediately understand:

> **This is an agentic remote-sensing AI system that accepts different satellite-image configurations, understands a natural-language query, automatically chooses the appropriate specialist workflow, performs the analysis, and returns an evidence-grounded result with confidence and an auditable execution summary.**
