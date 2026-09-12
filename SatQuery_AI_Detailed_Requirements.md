## **SIH 2026 — Problem Statement 26167** 

# **SatQuery AI** 

_Detailed Project Requirements & Evaluation-Oriented Build Specification_ 

|**Problem Statement ID**|26167|
|---|---|
|**Organization**|Indian Space Research Organisation(ISRO)|
|**Category / Theme**|Software / Space Technology|
|**Core objective**|Interactive agentic vision-language assistant for<br>multimodal remote-sensing image analysis through<br>natural-languagequeries|



**Source basis:** This document is derived from the supplied SIH 2026 Problem Statement 26167. Mandatory requirements below are kept aligned with the statement; implementation recommendations are explicitly labelled. 

### **1. What ISRO/SAC is actually asking you to build** 

The project is not simply a satellite-image chatbot. The required product is a software-based, interactive GUI/web application backed by an agentic remote-sensing AI system. A user should be able to upload supported remotesensing imagery, ask a natural-language question, and have the system automatically determine the appropriate specialist workflow, execute the relevant model/tool(s), combine the outputs, and return evidence-grounded textual and visual results. 

The central design idea is: Query → Understand task → Validate inputs → Select specialist model/tool → Execute → Integrate → Show evidence + confidence + execution trace. 

### **2. Problem statement snapshot** 

|**Area**|**Requirement**|**Priority**|
|---|---|---|
|Single image|VQA is mandatory; additionally<br>implement captioning/scene<br>description OR text-guided region<br>grounding.|MANDATORY|
|Bi-temporal pair|Change description OR change-<br>based VQA is mandatory; spatial<br>change map may be added where<br>reference masks are available.|MANDATORY|
|Optical + SAR pair|Extract complementary<br>information from a co-registered<br>optical/multispectral + SARpair.|MANDATORY|
|Remote-sensing adaptation|At least one visual/VLM<br>component must be fne-tuned or<br>otherwise adapted using<br>BigEarthNet.txt or other open-<br>source trainingdata.|MANDATORY|
|Agentic orchestration|Automatically select, sequence<br>and execute suitable specialist<br>models/tools based on query and<br>input confguration.<br>|MANDATORY|
|Evidence & auditability|Return visual evidence, confdence<br>information and an execution<br>summary containing selected task,<br>model/tool names and key<br>parameters.|MANDATORY|
|Interface|Interactive GUI or web application<br>with agentic remote-sensing AI<br>backend.|MANDATORY|
|Reports|Downloadable reports are<br>expected.|EXPECTED|



### **3. Input requirements** 

#### **3.1 Supported input configurations** 

- Single optical/multispectral image. 

- Single SAR image. 

- Co-registered optical/multispectral + SAR pair covering the same geographic area. 

- Bi-temporal pair: two spatially corresponding images of the same geographic area acquired at different times. 

#### **3.2 File formats** 

- GeoTIFF or TIFF for geospatial imagery. 

- PNG/JPEG may be accepted only for the prescribed public benchmark datasets. 

#### **3.3 Input validation is part of the product** 

- Check number of images supplied. 

- Check image modality (optical/multispectral vs SAR). 

- Check file format. 

- Check relevant metadata. 

- Check compatibility between paired images. 

- For paired workflows, ensure the images are spatially corresponding/co-registered as required. 

- Reject or clearly flag incompatible inputs rather than silently producing an answer. 

### **4. Mandatory AI capabilities** 

#### **4.1 Remote-sensing adaptation** 

A generic LLM/VLM alone is explicitly insufficient. At least one visual or vision-language component must be fine- 

tuned or otherwise adapted for remote-sensing imagery using BigEarthNet.txt or other open-source training data. 

- Document the base model/component. 

- Document the adaptation/fine-tuning method. 

- Document the training/adaptation dataset and split used. 

- Record important training parameters and evaluation results. 

- Demonstrate that the adapted component is actually used in the application. 

#### **4.2 Single-image VQA — mandatory** 

The system must accept one optical/multispectral or SAR image plus a natural-language question and return an answer. 

- 

   - Image + question input. 

- Remote-sensing-aware answer generation. 

- Confidence information. 

- Visual evidence where feasible. 

- Execution summary identifying the selected task and model/tool. 

#### **4.3 One additional single-image capability — mandatory** 

The statement requires at least one of the following: 

- Captioning / scene description: generate a meaningful description of land cover and major objects/features. 

- Text-guided region grounding: identify/highlight the region referred to by a natural-language query. 

Implementation recommendation: implement BOTH if time permits. This creates a stronger end-to-end demo and gives the agent more routing choices. 

#### **4.4 Multi-image change analysis — mandatory** 

- Accept two spatially corresponding images acquired at different times. 

- Perform change understanding. 

- Provide either change description OR change-based visual question answering. 

- Optionally generate a spatial change map when reference masks are available. 

- Return interpretable evidence showing where/what changed. 

#### **4.5 Cross-modal optical–SAR analysis — mandatory** 

- Accept a co-registered optical/multispectral and SAR pair. 

- Use both modalities jointly rather than treating them as two unrelated images. 

- Extract complementary information from the two sensors. 

- Support questions such as identifying built-up and water-covered regions. 

### **5. The agentic architecture IS a core requirement** 

The controller should automatically decide which specialist workflow is needed. The problem statement describes the following observable behaviour: 

1. Interpret the user's natural-language query and classify the requested task. 

2. Check the number, modality, format, metadata and compatibility of the supplied image(s). 

3. Select one or more models/tools from a predefined registry. 

4. Configure only permitted task parameters. 

5. Execute the selected workflow. 

6. Combine textual and spatial outputs. 

7. Estimate/return confidence. 

8. Return visual evidence. 

9. Provide an auditable execution summary containing the selected task, model/tool names and key parameters. 

Important: internal chain-of-thought/reasoning text is not required and is not evaluated. What matters is the observable execution trace: task selected, models/tools used, permitted parameters, and outputs. 

#### **6. Recommended specialist tool registry** 

|**Tool**|**Input**|**Output**<br>|**Used when**|
|---|---|---|---|
|RS-VQA|Single image + question|Answer + confdence +<br>evidence|Questions about image<br>content|
|RS-Caption|Single image|Caption/scene<br>description|Describe image/land<br>cover/objects|
|RS-Grounding|Single image + text<br>phrase|Bounding<br>box/region/mask|Highlight a referenced<br>region|
|Change Understanding /<br>Change-VQA|Two dates/images +<br>query|Change<br>answer/description +<br>evidence|Temporal change|
|Optical–SAR Fusion|Co-registered optical +<br>SAR|Joint interpretation|Cross-modal analysis|
|Validation Tool|Files + metadata|Compatibility report|Every request before<br>specialist execution|
|Report Generator|All outputs + trace|Downloadable report|Final response/export|



### **7. End-to-end user flow** 

10. User opens the web application. 

11. User uploads one image, a bi-temporal pair, or an optical–SAR pair. 

12. System validates file type, modality, count, metadata and pair compatibility. 

13. User enters a natural-language query. 

14. Agent classifies the task: VQA, captioning, grounding, change analysis, or optical–SAR analysis. 

15. Agent selects the appropriate specialist model/tool(s) from the registry. 

16. Selected tool(s) execute with permitted parameters. 

17. System integrates textual and spatial outputs. 

18. System presents answer + confidence + visual evidence. 

19. System shows an auditable execution summary. 

20. User can download a report. 

### **8. GUI / web application requirements** 

- Clear image upload area supporting the required input configurations. 

- Modality selection/auto-detection where appropriate. 

- Query text box for natural-language questions. 

- Clear indication of detected task and selected workflow. 

- Image/map viewer for visual evidence. 

- Side-by-side or synchronized viewer for paired images. 

- Overlay support for grounding/change evidence where applicable. 

- Answer panel with confidence information. 

- Execution trace panel showing task, model/tool names and key parameters. 

- Downloadable report action. 

- Clear error messages for unsupported or incompatible inputs. 

### **9. Evaluation datasets and benchmark expectations** 

The supplied problem statement says that BigEarthNet.txt is the primary dataset for adapting image–text representations to multisensor remote-sensing data. VRSBench and RSVQA are used to evaluate single-image captioning, grounding and visual question answering, while CDVQA is used to evaluate multitemporal changebased VQA. 

|**Dataset**|**Purpose stated in PS**|**What your system should be**<br>**ready to demonstrate**<br>|
|---|---|---|
|BigEarthNet.txt|Adapt image–text representations<br>to multisensor remote-sensing<br>data.|Adapt/fne-tune at least one<br>visual/VLM component and<br>document theprocess.|
|VRSBench|Evaluate single-image captioning,<br>groundingand VQA.|Keep the corresponding task<br>pipelines benchmark-ready.|
|RSVQA|Evaluate single-image captioning,<br>groundingand VQA.|Support reproducible single-image<br>evaluation.|
|CDVQA|Evaluate multitemporal change-<br>based VQA.|Support paired temporal inputs<br>and change-basedquestions.|
|ISRO/SAC evaluation set|Final evaluation using pre-<br>georeferenced/co-registered<br>Cartosat-2S optical and RISAT SAR|Ensure optical–SAR pipeline works<br>on co-registered geospatial pairs<br>and does not depend on disclosed|



<u>pairs plus task-specific references.</u> labels. 

### **10. ISRO/SAC evaluation: what you should assume** 

The statement says the ISRO/SAC evaluation set will contain pre-georeferenced and co-registered Cartosat-2S optical and RISAT SAR image pairs, with task-specific reference answers, labels, bounding boxes or masks as applicable. The evaluation annotations will not be disclosed to participating teams. 

- Do not build the solution around manually prepared answers for the evaluation set. 

- Design the pipeline to generalize to unseen image pairs and task types within the declared scope. 

- Make geospatial pairing and modality handling robust. 

- Keep model/tool selection configurable through a registry rather than hard-coded to one demo case. 

### **11. Deliverables explicitly expected** 

- Interactive GUI or web application. 

- Agentic remote-sensing AI backend. 

- Code and models. 

- Test and demonstration material. 

- Working demonstrations of all mandatory capabilities. 

- Downloadable reports as part of the expected solution. 

### **12. Minimum Viable Product (MUST HAVE)** 

|**Component**|**Minimum implementation**|**Status**|
|---|---|---|
|Frontend|Web/GUI for upload + natural-<br>languagequery+ results.|MUST|
|Input validation|Format, modality, image count,<br>metadata and pair compatibility<br>checks.|MUST|
|RS adaptation|At least one fne-tuned/adapted<br>visual/VLM component.|MUST|
|Single-image VQA|WorkingVQApipeline.|MUST|
|Additional single-image task|CaptioningORgrounding.|MUST|
|Bi-temporal analysis|Change description OR change-<br>based VQA.|MUST|
|Optical–SAR analysis|Joint analysis of co-registeredpair.|MUST|
|Agent|Automatic task routing + specialist<br>tool selection/execution.|MUST|
|Evidence|Visual evidence + confdence.|MUST|
|Audit|<br>Observable execution summary.|MUST|
|Report|Downloadable output report.|EXPECTED|



### **13. Stronger / competition-ready implementation (recommended)** 

- Implement both captioning AND grounding rather than choosing only one. 

- Generate change maps/overlays where masks or appropriate evaluation references are available. 

- Use synchronized image viewers for optical–SAR and bi-temporal pairs. 

- Show exactly why a tool was selected through a concise, user-facing execution trace. 

- Use a model registry with version, task, modality, input constraints and output schema. 

- Add confidence calibration/quality checks and flag low-confidence answers. 

- Preserve geospatial metadata and make evidence overlays spatially meaningful. 

- Provide reproducible benchmark evaluation scripts and metrics. 

- Package the complete system so a judge can run a clean demo with minimal setup. 

- Add report export containing input summary, query, selected task, tools/models, result, evidence and confidence. 

### **14. Suggested technical architecture** 

This is an implementation recommendation, not a verbatim requirement from the PS. 

- Frontend: React/Next.js or equivalent web UI. 

- API layer: FastAPI or equivalent backend. 

- Agent/controller: deterministic task classifier + tool registry + workflow executor. 

- Model layer: remote-sensing-adapted VLM plus specialist VQA/captioning/grounding/change/fusion models. 

- Geospatial layer: raster reading, metadata inspection, reprojection/compatibility checks and visualization. 

- Evidence layer: boxes/masks/change overlays/attention or other model-supported evidence. 

- Evaluation layer: benchmark runners and metric computation. 

- Report layer: structured JSON + downloadable PDF/HTML report. 

- Deployment: containerized services with a reproducible setup. 

### **15. Data/model engineering checklist** 

- Define supported sensor/modality assumptions. 

- Normalize/prepare optical or multispectral imagery appropriately. 

- Handle SAR-specific preprocessing consistently with the selected model. 

- Keep image dimensions, channels and expected preprocessing explicit per model. 

- Maintain train/validation/test separation for any adaptation work. 

- Record model checkpoints and configuration. 

- Avoid silently changing task parameters outside the permitted configuration. 

- Validate outputs against expected schemas before presenting them. 

- Log enough information to reproduce the selected workflow. 

### **16. Testing checklist before SIH evaluation** 

- ☐ Single optical/multispectral image + VQA query 

- ☐ Single SAR image + VQA query 

- ☐ Single image + caption/scene-description query 

- ☐ Single image + grounding query 

- ☐ Bi-temporal pair + change question 

- ☐ Bi-temporal pair + change description 

- ☐ Optical–SAR pair + joint analysis query 

- ☐ Wrong file format 

- ☐ Wrong number of images 

- ☐ Mismatched modalities 

- ☐ Non-compatible pair 

- ☐ Missing/invalid metadata 

- ☐ Low-confidence result handling 

- ☐ Visual evidence rendering 

- ☐ Execution trace rendering 

- ☐ Report generation/download 

- ☐ Benchmark test execution 

- ☐ Clean installation/restart test 

### **17. Demo scenarios judges should be able to see** 

#### **Scenario A — Single-image VQA** 

Upload one satellite image → ask a natural-language question → show answer, confidence, evidence and execution trace. 

#### **Scenario B — Scene description** 

Upload one image → request land-cover/major-object description → show caption/structured scene summary. 

#### **Scenario C — Grounding** 

Upload one image → ask to highlight a water body/built-up region → show spatial region overlay. 

#### **Scenario D — Change understanding** 

Upload two dates → ask what changed and where → show change answer plus spatial evidence/overlay. 

#### **Scenario E — Optical + SAR** 

Upload co-registered optical and SAR images → ask about built-up/water regions → show joint result and bothsource evidence. 

#### **Scenario F — Agent routing** 

Repeat different query types and visibly show that the controller selects different specialist tools automatically. 

### **18. Common ways a solution could fail the stated scope** 

- Only building a generic ChatGPT/VLM image chatbot without remote-sensing adaptation. 

- Supporting only single images while ignoring paired temporal and optical–SAR analysis. 

- Hard-coding one model instead of demonstrating agentic model/tool selection. 

- Returning only text with no visual evidence. 

- Skipping input compatibility/metadata checks. 

- Showing a hidden or undocumented workflow with no observable execution summary. 

- Using JPEG/PNG as the general geospatial input format instead of supporting GeoTIFF/TIFF. 

- Demonstrating a polished UI while the backend capabilities are missing or mocked. 

- Training/adapting a model but failing to demonstrate that the adapted component is integrated into the actual system. 

- Optimizing only for a few hand-picked examples rather than benchmark/generalization readiness. 

### **19. Final compliance matrix** 

|**PS requirement**|**Your implementation**|**Evidence to show**<br>**judges**|**Priority**|
|---|---|---|---|
|Remote-sensing<br>adaptation|Adapted RS visual/VLM<br>component|Training/adaptation<br>record + live model usage|Critical|
|Single-image VQA|VQA specialist|Live demo + benchmark<br>metrics|Critical|
|One additional single-<br>image task|Captioning and/or<br>grounding|Live demo + output<br>visualization|Critical|
|Bi-temporal change|Change specialist|Two-date demo +<br>evidence|Critical|
|Optical–SAR joint<br>analysis|Fusion/information-<br>extraction specialist|Paired demo|Critical|
|Agentic orchestration|Controller + tool registry|Execution trace|Critical|
|Input validation<br>|Validator<br>|Intentional invalid-input<br>demo|Critical|
|Confdence|Confdence/qualitylayer|Resultpanel|Critical|
|Visual evidence|Map/image overlays|Grounding/change/fusion<br>evidence|Critical|
|Downloadable reports|Reportgenerator|Exported report|High|
|Public benchmark<br>readiness|Evaluation scripts|Reproducible results|High|
|ISRO/SAC generalization|Robust geospatial paired-<br>imagepipeline|Unseen-style demo|Critical|



### **20. One-line definition of the winning product** 

**SatQuery AI should behave like an** intelligent remote-sensing analyst rather than a generic chatbot: it understands the query, understands the image configuration, chooses the right specialist model/tool, performs the analysis, validates and integrates the result, and returns an evidence-grounded answer with confidence and an auditable execution summary. 

### **Source note** 

All mandatory requirements in this document are based on the supplied Problem Statement 26167. Where this document uses phrases such as “recommended”, “stronger”, “competition-ready”, or “suggested architecture”, those are implementation recommendations and should not be treated as additional official PS requirements. 

