"use client"

import React, { createContext, useContext, useEffect, useState, useMemo, useCallback } from "react"

export type SupportedLanguage = "en" | "hi" | "mr"

export interface LanguageOption {
  code: SupportedLanguage
  label: string
  nativeName: string
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: "en", label: "English", nativeName: "English" },
  { code: "hi", label: "Hindi", nativeName: "हिन्दी" },
  { code: "mr", label: "Marathi", nativeName: "मराठी" },
]

export const DEFAULT_LANGUAGE: SupportedLanguage = "en"
export const STORAGE_KEY = "trinetra_lang"

// Complete dictionary of translation keys
export const translations = {
  en: {
    // Header & Brand
    "brand.title": "TRINETRA",
    "brand.ai": "AI",
    "brand.subtitle": "EARTH OBSERVATION / 26167",
    "nav.overview": "Overview",
    "nav.workspace": "Workspace",
    "nav.history": "History",
    "nav.evaluation": "Evaluation",
    "status.checking": "CHECKING...",
    "status.ready": "LOCAL AGENT READY • OLLAMA [{model}]{trace}",
    "status.langfuse_on": " • LANGFUSE ON",
    "status.offline": "OFFLINE DEMO MODE",
    "status.details": "100% Local Air-Gapped Inference",
    "lang.select": "Select language",

    // Landing Page
    "landing.pill": "100% LOCAL AGENTIC VISION-LANGUAGE",
    "landing.hero.title1": "Ask Earth.",
    "landing.hero.title2": "See evidence.",
    "landing.hero.desc": "TRINETRA AI turns complex satellite imagery questions into grounded, inspectable answers — powered by local Ollama models (Qwen 2.5/Llama 3.2), LangChain planning, and Langfuse telemetry without any cloud LLM dependency.",
    "landing.hero.start": "Start Analysis",
    "landing.hero.demo": "Explore Demo",
    "landing.stats.modes": "analysis modes",
    "landing.stats.layer": "evidence layer",
    "landing.stats.scenarios": "guided scenarios",

    // Capabilities
    "cap.single.eyebrow": "01 / Single image",
    "cap.single.title": "Explore one scene",
    "cap.single.desc": "Ask about land use, vegetation, water, infrastructure, or conditions.",
    "cap.temporal.eyebrow": "02 / Bi-temporal",
    "cap.temporal.title": "Detect change over time",
    "cap.temporal.desc": "Compare two dates to surface meaningful change and movement.",
    "cap.fusion.eyebrow": "03 / Optical + SAR",
    "cap.fusion.title": "Fuse complementary sensors",
    "cap.fusion.desc": "Fuse visible context with radar signals for deeper evidence.",

    // Workspace Page
    "workspace.pill": "WORKSPACE / 100% LOCAL",
    "workspace.title": "Analysis workspace",
    "workspace.desc": "Choose a workflow, add imagery, and ask a question. The local agent handles the rest.",
    "workspace.history_btn": "History",

    // Section 1: Workflow
    "section.workflow.eyebrow": "01 / workflow",
    "section.workflow.title": "What are you looking at?",
    "req.single": "1 image required",
    "req.temporal": "2 dated images required",
    "req.fusion": "Optical + SAR pair required",

    // Modes
    "mode.single.label": "Single image",
    "mode.single.desc": "Explore one scene",
    "mode.temporal.label": "Bi-temporal",
    "mode.temporal.desc": "Detect change over time",
    "mode.fusion.label": "Optical + SAR",
    "mode.fusion.desc": "Fuse complementary sensors",

    // Section 2: Imagery & Uploads
    "section.imagery.eyebrow": "02 / imagery",
    "section.imagery.title": "Upload your evidence",
    "upload.accepted": "PNG / JPEG / GeoTIFF / HSI (.mat) · MAX 50MB",
    "upload.drop_prompt": "Drop image or click to browse",
    "upload.formats": "{hint} · PNG, JPEG, GeoTIFF, HSI (.mat)",
    "upload.remove_aria": "Remove image",
    "slot.single.label": "Satellite image",
    "slot.single.hint": "Optical or SAR",
    "slot.temporal.before.label": "Earlier image",
    "slot.temporal.before.hint": "BEFORE",
    "slot.temporal.after.label": "Later image",
    "slot.temporal.after.hint": "AFTER",
    "slot.fusion.opt.label": "Optical image",
    "slot.fusion.opt.hint": "OPTICAL",
    "slot.fusion.sar.label": "Radar image",
    "slot.fusion.sar.hint": "SAR",
    "supported.satellites": "Supports Landsat, Sentinel, MODIS, Planet, and custom image exports.",

    // Section 3: Intent & Query
    "section.intent.eyebrow": "03 / intent",
    "section.intent.title": "What do you want to know?",
    "query.placeholder": "Ask about land use, changes, infrastructure, damage, vegetation, water bodies...",
    "examples.label": "Try asking",
    "btn.analyze": "Analyze",
    "btn.processing": "Processing evidence...",
    "local.note": "Powered by 100% Local Agentic AI: LangChain + Ollama + Langfuse (Zero Cloud LLMs)",

    // Execution Trace
    "trace.eyebrow": "LIVE / OBSERVABLE",
    "trace.title": "Agent execution",
    "trace.step.loading": "Loading imagery",
    "trace.step.preprocess": "Preprocessing imagery",
    "trace.step.mapping": "Mapping visual evidence",
    "trace.step.composing": "Composing answer",
    "trace.step.complete": "Complete",
    "trace.step.working": "Working with visible evidence...",
    "trace.foot": "The agent is selecting the appropriate evidence workflow.",

    // Empty State
    "empty.eyebrow": "READY FOR INPUT",
    "empty.title": "Your next answer\nwill appear here.",
    "empty.desc": "Upload imagery and ask a question to begin an inspectable analysis.",

    // Error State
    "error.eyebrow": "ANALYSIS FAILED",
    "error.title": "Pipeline Error",
    "error.note": "Truthful local error reporting: verify image formats, coordinates, and Ollama connection.",

    // Result View
    "result.eyebrow": "ANALYSIS COMPLETE · {mode}",
    "result.title": "Here is what the imagery shows",
    "confidence.high": "High confidence — verified radiometric evidence",
    "confidence.medium": "Medium confidence — some features uncertain",
    "confidence.low": "Low confidence — requires expert manual inspection",
    "evidence.eyebrow.fused": "VISUAL EVIDENCE / FUSED VIEW",
    "evidence.eyebrow.grounded": "VISUAL EVIDENCE / GROUNDED REGION",
    "evidence.head.title": "Claims connected to imagery",
    "viewer.side_by_side": "Side-by-side",
    "viewer.overlay": "Overlay",
    "legend.connected": "Connected evidence",
    "legend.change": "Change / caution region",
    "legend.active": "GROUNDING ACTIVE",
    "btn.report": "View Mission Intelligence Report (HTML)",
    "meta.eyebrow": "TRACE / METADATA",
    "meta.title": "Technical details",
    "meta.model": "Model",
    "meta.resolution": "Resolution",
    "meta.source": "Source",
    "meta.processing": "Processing",
    "result.disclaimer": "Confidence reflects image quality and evidence alignment, not certainty. Validate findings before operational decisions.",

    // Dashboard / History
    "dash.pill": "COMMAND CENTER",
    "dash.title": "Analysis history",
    "dash.desc": "A concise view of your analysis trail and system signals.",
    "dash.btn_new": "New analysis",
    "metric.analyses": "Analyses run",
    "metric.analyses_delta": "+8 this week",
    "metric.images": "Images processed",
    "metric.images_delta": "Optical & SAR",
    "metric.confidence": "Avg. confidence",
    "metric.confidence_delta": "Across verified runs",
    "hist.eyebrow": "RECENT ACTIVITY",
    "hist.title": "Evidence trail",
    "hist.search": "Filter analyses",
    "hist.empty_desc": "No local analyses yet. Run your first scene interpretation to build a trail of evidence.",
    "hist.demo_btn": "Run guided demo",

    // Evaluation Cockpit
    "eval.pill": "EVALUATION COCKPIT",
    "eval.title": "Make intelligence inspectable.",
    "eval.desc": "Review the behaviors that matter in an agentic vision-language workflow.",
    "eval.workspace_btn": "Open workspace",
    "eval.signals.eyebrow": "SYSTEM SIGNALS",
    "eval.signals.title": "What the judge can inspect",
    "eval.metric1.label": "Grounding coverage",
    "eval.metric1.note": "Claims linked to visible pixel regions",
    "eval.metric2.label": "Workflow routing",
    "eval.metric2.note": "Task correctly routed by agent controller",
    "eval.metric3.label": "Radiometric verification",
    "eval.metric3.note": "Physical indices (NDVI/NDWI/dB) validated",
    "eval.arch.eyebrow": "FRONTEND ARCHITECTURE",
    "eval.arch.title1": "Simple on the surface.",
    "eval.arch.title2": "Ready for real inference.",
    "eval.arch.flow.inputs": "INPUTS",
    "eval.arch.flow.agent": "AGENT",
    "eval.arch.flow.evidence": "EVIDENCE",
    "eval.arch.desc": "Clean service boundaries keep the experience backend-agnostic. Swap the local adapter for a real API without rewriting the analysis workspace.",
    "eval.scenario_btn": "Test a scenario",

    // Footer
    "footer.left": "TRINETRA AI · ISRO SIH 26167",
    "footer.right": "100% LOCAL-FIRST AGENTIC AI · OLLAMA + LANGCHAIN + LANGFUSE · AIR-GAPPED",

    // Query Examples
    "examples.single.0": "What land use types are visible in this image?",
    "examples.single.1": "Describe the water bodies and vegetation coverage.",
    "examples.single.2": "Highlight the water body referred to in the query",
    "examples.temporal.0": "What changes are visible between these two dates?",
    "examples.temporal.1": "Has the built-up area increased, decreased, or remained unchanged?",
    "examples.temporal.2": "Show me areas of significant vegetation loss.",
    "examples.fusion.0": "Identify flooded regions using combined modality data.",
    "examples.fusion.1": "Compare the optical and radar signatures of this area.",

    // Demo Scenarios
    "scenario.urban.title": "Urban growth",
    "scenario.urban.query": "What changes are visible between these two dates?",
    "scenario.urban.response": "The analysis identifies **measurable urban expansion** along the eastern edge of the scene. New built-up surfaces appear as a connected 18% increase, while the central road corridor remains stable. The highlighted evidence regions show where impervious cover replaced mixed vegetation.",
    "scenario.flood.title": "Flood mapping",
    "scenario.flood.query": "Identify flooded regions using combined modality data.",
    "scenario.flood.response": "Fused optical and SAR evidence suggests **standing water across the southern lowlands**. The radar-dark regions align with low-lying agricultural parcels and are distinct from persistent water bodies. Confidence is medium because cloud cover limits optical confirmation.",
    "scenario.landuse.title": "Land use scan",
    "scenario.landuse.query": "What land use types are visible in this image?",
    "scenario.landuse.response": "The scene is predominantly **agricultural**, with rectangular cultivated parcels, a compact settlement cluster, and a riparian vegetation corridor. A paved road network divides the northern fields from denser development in the southwest.",
    "scenario.deforestation.title": "Vegetation loss",
    "scenario.deforestation.query": "Show me areas of significant vegetation loss.",
    "scenario.deforestation.response": "A concentrated vegetation-loss signature appears in the northwest quadrant. The change region covers approximately 6.4 hectares and has a fragmented edge consistent with clearing activity. Validate against seasonal imagery before operational decisions.",

    // Accessibility
    "aria.menu": "Toggle navigation menu",
    "aria.language": "Select language",
    "aria.preview": "Uploaded satellite preview",
    "aria.remove_image": "Remove uploaded image",
  },

  hi: {
    // Header & Brand
    "brand.title": "TRINETRA",
    "brand.ai": "AI",
    "brand.subtitle": "भू-अवलोकन / इसरो 26167",
    "nav.overview": "अवलोकन",
    "nav.workspace": "कार्यस्थान",
    "nav.history": "इतिहास",
    "nav.evaluation": "मूल्यांकन",
    "status.checking": "जाँच जारी...",
    "status.ready": "स्थानीय एजेंट तैयार • OLLAMA [{model}]{trace}",
    "status.langfuse_on": " • LANGFUSE सक्रिय",
    "status.offline": "ऑफ़लाइन डेमो मोड",
    "status.details": "100% स्थानीय एयर-गैप्ड इन्फेरेंस",
    "lang.select": "भाषा चुनें",

    // Landing Page
    "landing.pill": "100% स्थानीय एजेंटिक दृष्टि-भाषा एआई",
    "landing.hero.title1": "पृथ्वी से पूछें।",
    "landing.hero.title2": "साक्ष्य देखें।",
    "landing.hero.desc": "TRINETRA AI जटिल उपग्रह छवियों से जुड़े प्रश्नों को प्रत्यक्ष, सत्यापन योग्य उत्तरों में बदलता है — स्थानीय Ollama मॉडल (Qwen 2.5/Llama 3.2), LangChain योजना और बिना किसी क्लाउड निर्भरता के Langfuse टेलीमेट्री द्वारा संचालित।",
    "landing.hero.start": "विश्लेषण शुरू करें",
    "landing.hero.demo": "डेमो देखें",
    "landing.stats.modes": "विश्लेषण मोड",
    "landing.stats.layer": "साक्ष्य परत",
    "landing.stats.scenarios": "निर्देशित परिदृश्य",

    // Capabilities
    "cap.single.eyebrow": "01 / एकल छवि",
    "cap.single.title": "एक दृश्य का अन्वेषण",
    "cap.single.desc": "भूमि उपयोग, वनस्पति, जल निकायों, बुनियादी ढांचे या स्थितियों के बारे में पूछें।",
    "cap.temporal.eyebrow": "02 / द्वि-कालिक (Bi-temporal)",
    "cap.temporal.title": "समय के साथ परिवर्तन पहचानें",
    "cap.temporal.desc": "महत्वपूर्ण परिवर्तन और गतिविधियों को उजागर करने के लिए दो तिथियों की तुलना करें।",
    "cap.fusion.eyebrow": "03 / ऑप्टिकल + SAR",
    "cap.fusion.title": "पूरक सेंसरों का संलयन",
    "cap.fusion.desc": "गहरे साक्ष्य के लिए दृश्य संदर्भ को रडार संकेतों के साथ जोड़ें।",

    // Workspace Page
    "workspace.pill": "कार्यस्थान / 100% स्थानीय",
    "workspace.title": "विश्लेषण कार्यस्थान",
    "workspace.desc": "वर्कफ़्लो चुनें, उपग्रह छवि जोड़ें और प्रश्न पूछें। स्थानीय एजेंट शेष कार्य संभालता है।",
    "workspace.history_btn": "इतिहास",

    // Section 1: Workflow
    "section.workflow.eyebrow": "01 / वर्कफ़्लो",
    "section.workflow.title": "आप क्या देखना चाहते हैं?",
    "req.single": "1 उपग्रह छवि आवश्यक",
    "req.temporal": "2 अलग तिथियों की छवियाँ आवश्यक",
    "req.fusion": "ऑप्टिकल + SAR जोड़ी आवश्यक",

    // Modes
    "mode.single.label": "एकल छवि",
    "mode.single.desc": "एक दृश्य का अन्वेषण",
    "mode.temporal.label": "द्वि-कालिक (Bi-temporal)",
    "mode.temporal.desc": "समय के साथ परिवर्तन खोजें",
    "mode.fusion.label": "ऑप्टिकल + SAR",
    "mode.fusion.desc": "पूरक सेंसरों का संलयन",

    // Section 2: Imagery & Uploads
    "section.imagery.eyebrow": "02 / उपग्रह छवियाँ",
    "section.imagery.title": "अपना साक्ष्य अपलोड करें",
    "upload.accepted": "PNG / JPEG / GeoTIFF / HSI (.mat) · अधिकतम 50MB",
    "upload.drop_prompt": "छवि यहाँ छोड़ें या ब्राउज़ करने के लिए क्लिक करें",
    "upload.formats": "{hint} · PNG, JPEG, GeoTIFF, HSI (.mat)",
    "upload.remove_aria": "छवि हटाएं",
    "slot.single.label": "उपग्रह छवि",
    "slot.single.hint": "ऑप्टिकल या SAR",
    "slot.temporal.before.label": "पूर्व छवि",
    "slot.temporal.before.hint": "पहले (BEFORE)",
    "slot.temporal.after.label": "पश्चात छवि",
    "slot.temporal.after.hint": "बाद में (AFTER)",
    "slot.fusion.opt.label": "ऑप्टिकल छवि",
    "slot.fusion.opt.hint": "ऑप्टिकल (OPTICAL)",
    "slot.fusion.sar.label": "रडार छवि",
    "slot.fusion.sar.hint": "SAR",
    "supported.satellites": "Landsat, Sentinel, MODIS, Planet और कस्टम छवि एक्सपोर्ट समर्थित हैं।",

    // Section 3: Intent & Query
    "section.intent.eyebrow": "03 / प्रश्न व उद्देश्य",
    "section.intent.title": "आप क्या जानना चाहते हैं?",
    "query.placeholder": "भूमि उपयोग, परिवर्तन, बुनियादी ढांचे, क्षति, वनस्पति, जल निकायों के बारे में पूछें...",
    "examples.label": "पूछ कर देखें",
    "btn.analyze": "विश्लेषण करें",
    "btn.processing": "साक्ष्य संसाधित हो रहा है...",
    "local.note": "100% स्थानीय एजेंटिक एआई द्वारा संचालित: LangChain + Ollama + Langfuse (क्लाउड LLM मुक्त)",

    // Execution Trace
    "trace.eyebrow": "लाइव / अवलोकन योग्य",
    "trace.title": "एजेंट निष्पादन",
    "trace.step.loading": "छवि लोड हो रही है",
    "trace.step.preprocess": "छवि प्री-प्रोसेसिंग",
    "trace.step.mapping": "दृश्य साक्ष्य प्रतिचित्रण",
    "trace.step.composing": "उत्तर तैयार किया जा रहा है",
    "trace.step.complete": "पूर्ण",
    "trace.step.working": "दृश्य साक्ष्य पर कार्य जारी...",
    "trace.foot": "एजेंट उपयुक्त साक्ष्य वर्कफ़्लो का चयन कर रहा है।",

    // Empty State
    "empty.eyebrow": "इनपुट के लिए तैयार",
    "empty.title": "आपका अगला उत्तर\nयहाँ प्रदर्शित होगा।",
    "empty.desc": "निरीक्षण योग्य विश्लेषण शुरू करने के लिए उपग्रह छवि अपलोड करें और प्रश्न पूछें।",

    // Error State
    "error.eyebrow": "विश्लेषण विफल",
    "error.title": "पाइपलाइन त्रुटि",
    "error.note": "सत्यनिष्ठ स्थानीय त्रुटि रिपोर्टिंग: छवि प्रारूप, निर्देशांक और Ollama कनेक्शन की जाँच करें।",

    // Result View
    "result.eyebrow": "विश्लेषण पूर्ण · {mode}",
    "result.title": "उपग्रह छवि के प्रमुख निष्कर्ष",
    "confidence.high": "उच्च विश्वसनीयता — सत्यापित रेडियोमेट्रिक साक्ष्य",
    "confidence.medium": "मध्यम विश्वसनीयता — कुछ विशेषताएं अनिश्चित",
    "confidence.low": "निम्न विश्वसनीयता — विशेषज्ञ मानवीय निरीक्षण आवश्यक",
    "evidence.eyebrow.fused": "दृश्य साक्ष्य / संयुक्त दृश्य",
    "evidence.eyebrow.grounded": "दृश्य साक्ष्य / भू-संदर्भित क्षेत्र",
    "evidence.head.title": "छवि से जुड़े साक्ष्य दावे",
    "viewer.side_by_side": "पास-पास देखें",
    "viewer.overlay": "ओवरले",
    "legend.connected": "संबद्ध साक्ष्य",
    "legend.change": "परिवर्तन / चेतावनी क्षेत्र",
    "legend.active": "ग्राउंडिंग सक्रिय",
    "btn.report": "मिशन इंटेलिजेंस रिपोर्ट देखें (HTML)",
    "meta.eyebrow": "ट्रेस / मेटाडेटा",
    "meta.title": "तकनीकी विवरण",
    "meta.model": "मॉडल",
    "meta.resolution": "रिज़ॉल्यूशन",
    "meta.source": "स्रोत",
    "meta.processing": "प्रसंस्करण समय",
    "result.disclaimer": "विश्वसनीयता छवि गुणवत्ता और साक्ष्य संरेखण दर्शाती है, पूर्ण निश्चितता नहीं। परिचालन निर्णयों से पहले निष्कर्ष सत्यापित करें।",

    // Dashboard / History
    "dash.pill": "कमांड सेंटर",
    "dash.title": "विश्लेषण इतिहास",
    "dash.desc": "आपके विश्लेषण ट्रैक और सिस्टम संकेतों का संक्षिप्त दृश्य।",
    "dash.btn_new": "नया विश्लेषण",
    "metric.analyses": "कुल विश्लेषण",
    "metric.analyses_delta": "+8 इस सप्ताह",
    "metric.images": "संसाधित छवियाँ",
    "metric.images_delta": "ऑप्टिकल व SAR",
    "metric.confidence": "औसत विश्वसनीयता",
    "metric.confidence_delta": "सत्यापित रनों के आधार पर",
    "hist.eyebrow": "हाल की गतिविधि",
    "hist.title": "साक्ष्य शृंखला",
    "hist.search": "विश्लेषण फ़िल्टर करें",
    "hist.empty_desc": "अभी तक कोई स्थानीय विश्लेषण नहीं हुआ है। साक्ष्य शृंखला बनाने के लिए अपना पहला दृश्य विश्लेषण चलाएं।",
    "hist.demo_btn": "निर्देशित डेमो चलाएं",

    // Evaluation Cockpit
    "eval.pill": "मूल्यांकन कॉकपिट",
    "eval.title": "खुफिया जानकारी को निरीक्षण योग्य बनाएं।",
    "eval.desc": "एजेंटिक दृष्टि-भाषा वर्कफ़्लो के महत्वपूर्ण व्यवहारों की समीक्षा करें।",
    "eval.workspace_btn": "कार्यस्थान खोलें",
    "eval.signals.eyebrow": "सिस्टम सिग्नल",
    "eval.signals.title": "निरीक्षक क्या जांच सकते हैं",
    "eval.metric1.label": "ग्राउंडिंग कवरेज",
    "eval.metric1.note": "दृश्य पिक्सेल क्षेत्रों से जुड़े दावे",
    "eval.metric2.label": "वर्कफ़्लो रूटिंग",
    "eval.metric2.note": "एजेंट नियंत्रक द्वारा कार्य का सही रूटिंग",
    "eval.metric3.label": "रेडियोमेट्रिक सत्यापन",
    "eval.metric3.note": "भौतिक सूचकांक (NDVI/NDWI/dB) सत्यापित",
    "eval.arch.eyebrow": "फ़्रंटएंड आर्किटेक्चर",
    "eval.arch.title1": "सतह पर सरल।",
    "eval.arch.title2": "वास्तविक इन्फेरेंस के लिए तैयार।",
    "eval.arch.flow.inputs": "इनपुट",
    "eval.arch.flow.agent": "एजेंट",
    "eval.arch.flow.evidence": "साक्ष्य",
    "eval.arch.desc": "स्पष्ट सेवा सीमाएं अनुभव को बैकएंड-अज्ञेयवादी रखती हैं। विश्लेषण कार्यस्थान को दोबारा लिखे बिना स्थानीय एडाप्टर को वास्तविक एपीआई से बदलें।",
    "eval.scenario_btn": "परिदृश्य का परीक्षण करें",

    // Footer
    "footer.left": "TRINETRA AI · इसरो SIH 26167",
    "footer.right": "100% स्थानीय-प्रथम एजेंटिक एआई · OLLAMA + LANGCHAIN + LANGFUSE · एयर-गैप्ड",

    // Query Examples
    "examples.single.0": "इस छवि में किस प्रकार के भूमि उपयोग दिखाई दे रहे हैं?",
    "examples.single.1": "जल निकायों और वनस्पति आवरण का विवरण दें।",
    "examples.single.2": "क्वेरी में उल्लिखित जल निकाय को हाइलाइट करें",
    "examples.temporal.0": "इन दो तिथियों के बीच क्या परिवर्तन दिखाई दे रहे हैं?",
    "examples.temporal.1": "क्या निर्मित क्षेत्र में वृद्धि हुई है, कमी आई है या कोई बदलाव नहीं हुआ है?",
    "examples.temporal.2": "वनस्पति में उल्लेखनीय कमी वाले क्षेत्र दिखाएं।",
    "examples.fusion.0": "संयुक्त मोडैलिटी डेटा का उपयोग करके बाढ़ प्रभावित क्षेत्रों की पहचान करें।",
    "examples.fusion.1": "इस क्षेत्र के ऑप्टिकल और रडार संकेतों की तुलना करें।",

    // Demo Scenarios
    "scenario.urban.title": "शहरी विस्तार",
    "scenario.urban.query": "इन दो तिथियों के बीच क्या परिवर्तन दिखाई दे रहे हैं?",
    "scenario.urban.response": "विश्लेषण दृश्य के पूर्वी किनारे पर **मापने योग्य शहरी विस्तार** की पहचान करता है। नई निर्मित सतहें 18% की वृद्धि के रूप में दिखाई देती हैं, जबकि केंद्रीय सड़क गलियारा स्थिर रहता है। हाइलाइट किए गए साक्ष्य क्षेत्र दिखाते हैं कि अभेद्य आवरण ने मिश्रित वनस्पति का स्थान ले लिया है।",
    "scenario.flood.title": "बाढ़ मानचित्रण",
    "scenario.flood.query": "संयुक्त मोडैलिटी डेटा का उपयोग करके बाढ़ प्रभावित क्षेत्रों की पहचान करें।",
    "scenario.flood.response": "संयुक्त ऑप्टिकल और SAR साक्ष्य **दक्षिणी निचले इलाकों में खड़े पानी** की पुष्टि करते हैं। रडार-डार्क क्षेत्र निचले कृषि भूखंडों के साथ संरेखित हैं और स्थायी जल निकायों से भिन्न हैं। क्लाउड कवर ऑप्टिकल पुष्टि को सीमित करता है इसलिए विश्वसनीयता मध्यम है।",
    "scenario.landuse.title": "भूमि उपयोग स्कैन",
    "scenario.landuse.query": "इस छवि में किस प्रकार के भूमि उपयोग दिखाई दे रहे हैं?",
    "scenario.landuse.response": "दृश्य मुख्य रूप से **कृषि प्रधान** है, जिसमें आयताकार खेती वाले भूखंड, एक सघन बस्ती समूह और एक नदी तटीय वनस्पति गलियारा शामिल है। एक पक्की सड़क उत्तर के खेतों को दक्षिण-पश्चिम में घने विकास से अलग करती है।",
    "scenario.deforestation.title": "वनस्पति की हानि",
    "scenario.deforestation.query": "वनस्पति में उल्लेखनीय कमी वाले क्षेत्र दिखाएं।",
    "scenario.deforestation.response": "उत्तर-पश्चिम चतुर्थांश में एक केंद्रित वनस्पति-हानि संकेत दिखाई देता है। परिवर्तन क्षेत्र लगभग 6.4 हेक्टेयर में फैला है और इसकी खंडित सीमाएं कटाई गतिविधि के अनुरूप हैं। परिचालन निर्णयों से पहले मौसमी इमेजरी से सत्यापित करें।",

    // Accessibility
    "aria.menu": "नेविगेशन मेनू खोलें/बंद करें",
    "aria.language": "भाषा का चयन करें",
    "aria.preview": "अपलोड की गई उपग्रह छवि पूर्वावलोकन",
    "aria.remove_image": "अपलोड की गई छवि हटाएं",
  },

  mr: {
    // Header & Brand
    "brand.title": "TRINETRA",
    "brand.ai": "AI",
    "brand.subtitle": "भू-निरीक्षण / इस्रो 26167",
    "nav.overview": "आढावा",
    "nav.workspace": "कार्यक्षेत्र",
    "nav.history": "इतिहास",
    "nav.evaluation": "मूल्यांकन",
    "status.checking": "तपासणी सुरू...",
    "status.ready": "स्थानिक एजंट सज्ज • OLLAMA [{model}]{trace}",
    "status.langfuse_on": " • LANGFUSE चालू",
    "status.offline": "ऑफलाइन डेमो मोड",
    "status.details": "100% स्थानिक एअर-गॅप केलेले इन्फेरन्स",
    "lang.select": "भाषा निवडा",

    // Landing Page
    "landing.pill": "100% स्थानिक एजंटिक दृष्टी-भाषा एआय",
    "landing.hero.title1": "पृथ्वीला विचारा.",
    "landing.hero.title2": "पुरावे पहा.",
    "landing.hero.desc": "TRINETRA AI क्लिष्ट उपग्रह प्रतिमांवरील प्रश्नांचे प्रत्यक्ष, तपासणीयोग्य उत्तरांमध्ये रूपांतर करते — स्थानिक Ollama मॉडेल्स (Qwen 2.5/Llama 3.2), LangChain नियोजन आणि क्लाउड LLM शिवाय Langfuse टेलिमेट्रीद्वारे समर्थित.",
    "landing.hero.start": "विश्लेषण सुरू करा",
    "landing.hero.demo": "डेमो पहा",
    "landing.stats.modes": "विश्लेषण पद्धती",
    "landing.stats.layer": "पुरावा स्तर",
    "landing.stats.scenarios": "मार्गदर्शित परिस्थिती",

    // Capabilities
    "cap.single.eyebrow": "01 / एकल प्रतिमा",
    "cap.single.title": "एका दृश्याचा अभ्यास",
    "cap.single.desc": "जमीन वापर, वनस्पती, जलसाठे, पायाभूत सुविधा किंवा परिस्थितीबद्दल विचारा.",
    "cap.temporal.eyebrow": "02 / द्वि-कालिक (Bi-temporal)",
    "cap.temporal.title": "काळानुसार बदल ओळखा",
    "cap.temporal.desc": "महत्त्वाचे बदल आणि हालचाली शोधण्यासाठी दोन तारखांची तुलना करा.",
    "cap.fusion.eyebrow": "03 / ऑप्टिकल + SAR",
    "cap.fusion.title": "पूरक सेन्सर्सचे एकत्रीकरण",
    "cap.fusion.desc": "सखोल पुराव्यासाठी दृश्यमान संदर्भ रडार सिग्नलसह एकत्र करा.",

    // Workspace Page
    "workspace.pill": "कार्यक्षेत्र / 100% स्थानिक",
    "workspace.title": "विश्लेषण कार्यक्षेत्र",
    "workspace.desc": "वर्कफ्लो निवडा, उपग्रह प्रतिमा जोडा आणि प्रश्न विचारा. उर्वरित काम स्थानिक एजंट सांभाळतो.",
    "workspace.history_btn": "इतिहास",

    // Section 1: Workflow
    "section.workflow.eyebrow": "01 / वर्कफ्लो",
    "section.workflow.title": "तुम्ही काय पाहू इच्छिता?",
    "req.single": "1 उपग्रह प्रतिमा आवश्यक",
    "req.temporal": "2 वेगवेगळ्या तारखांच्या प्रतिमा आवश्यक",
    "req.fusion": "ऑप्टिकल + SAR जोडी आवश्यक",

    // Modes
    "mode.single.label": "एकल प्रतिमा",
    "mode.single.desc": "एका दृश्याचा अभ्यास",
    "mode.temporal.label": "द्वि-कालिक (Bi-temporal)",
    "mode.temporal.desc": "काळानुसार बदल ओळखा",
    "mode.fusion.label": "ऑप्टिकल + SAR",
    "mode.fusion.desc": "पूरक सेन्सर्सचे एकत्रीकरण",

    // Section 2: Imagery & Uploads
    "section.imagery.eyebrow": "02 / उपग्रह प्रतिमा",
    "section.imagery.title": "तुमचा पुरावा अपलोड करा",
    "upload.accepted": "PNG / JPEG / GeoTIFF / HSI (.mat) · कमाल 50MB",
    "upload.drop_prompt": "प्रतिमा येथे टाका किंवा ब्राउझ करण्यासाठी क्लिक करा",
    "upload.formats": "{hint} · PNG, JPEG, GeoTIFF, HSI (.mat)",
    "upload.remove_aria": "प्रतिमा काढा",
    "slot.single.label": "उपग्रह प्रतिमा",
    "slot.single.hint": "ऑप्टिकल किंवा SAR",
    "slot.temporal.before.label": "मागील प्रतिमा",
    "slot.temporal.before.hint": "आधीची (BEFORE)",
    "slot.temporal.after.label": "नंतरची प्रतिमा",
    "slot.temporal.after.hint": "नंतरची (AFTER)",
    "slot.fusion.opt.label": "ऑप्टिकल प्रतिमा",
    "slot.fusion.opt.hint": "ऑप्टिकल (OPTICAL)",
    "slot.fusion.sar.label": "रडार प्रतिमा",
    "slot.fusion.sar.hint": "SAR",
    "supported.satellites": "Landsat, Sentinel, MODIS, Planet आणि सानुकूल प्रतिमा निर्यात समर्थित आहेत.",

    // Section 3: Intent & Query
    "section.intent.eyebrow": "03 / हेतू व प्रश्न",
    "section.intent.title": "तुम्हाला काय जाणून घ्यायचे आहे?",
    "query.placeholder": "जमीन वापर, बदल, पायाभूत सुविधा, नुकसान, वनस्पती, जलसाठे याबद्दल विचारा...",
    "examples.label": "विचारून पहा",
    "btn.analyze": "विश्लेषण करा",
    "btn.processing": "पुरावा प्रक्रिया होत आहे...",
    "local.note": "100% स्थानिक एजंटिक एआय द्वारे समर्थित: LangChain + Ollama + Langfuse (शून्य क्लाउड LLM)",

    // Execution Trace
    "trace.eyebrow": "थेट / निरीक्षणक्षम",
    "trace.title": "एजंट अंमलबजावणी",
    "trace.step.loading": "प्रतिमा लोड होत आहे",
    "trace.step.preprocess": "प्रतिमा पूर्व-प्रक्रिया",
    "trace.step.mapping": "दृश्य पुरावा मॅपिंग",
    "trace.step.composing": "उत्तर तयार केले जात आहे",
    "trace.step.complete": "पूर्ण",
    "trace.step.working": "दृश्य पुराव्यावर काम सुरू आहे...",
    "trace.foot": "एजंट योग्य पुरावा वर्कफ्लो निवडत आहे.",

    // Empty State
    "empty.eyebrow": "इनपुटसाठी सज्ज",
    "empty.title": "तुमचे पुढील उत्तर\nयेथे दिसेल.",
    "empty.desc": "तपासणीयोग्य विश्लेषण सुरू करण्यासाठी उपग्रह प्रतिमा अपलोड करा आणि प्रश्न विचारा.",

    // Error State
    "error.eyebrow": "विश्लेषण अयशस्वी",
    "error.title": "पाइपलाइन त्रुटी",
    "error.note": "स्थानिक त्रुटी अहवाल: प्रतिमा स्वरूप, निर्देशांक आणि Ollama कनेक्शन तपासा.",

    // Result View
    "result.eyebrow": "विश्लेषण पूर्ण · {mode}",
    "result.title": "उपग्रह प्रतिमेचे मुख्य निष्कर्ष",
    "confidence.high": "उच्च विश्वासार्हता — सत्यापित रेडिओमेट्रिक पुरावा",
    "confidence.medium": "मध्यम विश्वासार्हता — काही वैशिष्ट्ये अनिश्चित",
    "confidence.low": "कमी विश्वासार्हता — तज्ञांच्या मॅन्युअल तपासणीची आवश्यकता",
    "evidence.eyebrow.fused": "दृश्य पुरावा / संयुक्त दृश्य",
    "evidence.eyebrow.grounded": "दृश्य पुरावा / भू-संदर्भित भाग",
    "evidence.head.title": "प्रतिमेस जोडलेले पुराव्याचे दावे",
    "viewer.side_by_side": "शेजारी-शेजारी",
    "viewer.overlay": "ओव्हरले",
    "legend.connected": "जोडलेला पुरावा",
    "legend.change": "बदल / खबरदारीचा भाग",
    "legend.active": "ग्राउंडिंग सक्रिय",
    "btn.report": "मिशन इंटेलिजन्स अहवाल पहा (HTML)",
    "meta.eyebrow": "ट्रेस / मेटाडेटा",
    "meta.title": "तांत्रिक तपशील",
    "meta.model": "मॉडेल",
    "meta.resolution": "रिझोल्यूशन",
    "meta.source": "स्रोत",
    "meta.processing": "प्रक्रिया वेळ",
    "result.disclaimer": "विश्वासार्हता प्रतिमेची गुणवत्ता आणि पुराव्याचे संरेखन दर्शवते, पूर्ण निश्चितता नाही. ऑपरेशनल निर्णयांपूर्वी निष्कर्षांची पडताळणी करा.",

    // Dashboard / History
    "dash.pill": "कमांड सेंटर",
    "dash.title": "विश्लेषण इतिहास",
    "dash.desc": "तुमच्या विश्लेषण ट्रेल आणि सिस्टीम सिग्नल्सचे संक्षिप्त दृश्य.",
    "dash.btn_new": "नवीन विश्लेषण",
    "metric.analyses": "एकूण विश्लेषणे",
    "metric.analyses_delta": "+8 या आठवड्यात",
    "metric.images": "प्रक्रिया केलेल्या प्रतिमा",
    "metric.images_delta": "ऑप्टिकल आणि SAR",
    "metric.confidence": "सरासरी विश्वासार्हता",
    "metric.confidence_delta": "सत्यापित रन्सच्या आधारे",
    "hist.eyebrow": "अलीकडील क्रियाकलाप",
    "hist.title": "पुरावा ट्रेल",
    "hist.search": "विश्लेषण फिल्टर करा",
    "hist.empty_desc": "अद्याप कोणतेही स्थानिक विश्लेषण नाही. पुराव्याची शृंखला तयार करण्यासाठी तुमचे पहिले दृश्य विश्लेषण चालवा.",
    "hist.demo_btn": "मार्गदर्शित डेमो चालवा",

    // Evaluation Cockpit
    "eval.pill": "मूल्यांकन कॉकपिट",
    "eval.title": "गुप्तचर माहिती तपासणीयोग्य बनवा.",
    "eval.desc": "एजंटिक दृष्टी-भाषा वर्कफ्लोमधील महत्त्वाच्या वर्तनांचे पुनरावलोकन करा.",
    "eval.workspace_btn": "कार्यक्षेत्र उघडा",
    "eval.signals.eyebrow": "सिस्टीम सिग्नल्स",
    "eval.signals.title": "परीक्षक काय तपासू शकतात",
    "eval.metric1.label": "ग्राउंडिंग कव्हरेज",
    "eval.metric1.note": "दृश्यमान पिक्सेल क्षेत्रांशी जोडलेले दावे",
    "eval.metric2.label": "वर्कफ्लो रूटिंग",
    "eval.metric2.note": "एजंट कंट्रोलरद्वारे कार्याचे योग्य रूटिंग",
    "eval.metric3.label": "रेडिओमेट्रिक पडताळणी",
    "eval.metric3.note": "भौतिक निर्देशांक (NDVI/NDWI/dB) सत्यापित",
    "eval.arch.eyebrow": "फ्रंटएंड आर्किटेक्चर",
    "eval.arch.title1": "वरवर साधे.",
    "eval.arch.title2": "वास्तविक इन्फेरन्ससाठी सज्ज.",
    "eval.arch.flow.inputs": "इनपुट",
    "eval.arch.flow.agent": "एजंट",
    "eval.arch.flow.evidence": "पुरावा",
    "eval.arch.desc": "स्वच्छ सेवा सीमा अनुभव बॅकएंड-अज्ञेयवादी ठेवतात. विश्लेषण कार्यक्षेत्र पुन्हा न लिहिता स्थानिक अ‍ॅडॉप्टरला वास्तविक एपीआयने बदला.",
    "eval.scenario_btn": "परिस्थितीची चाचणी घ्या",

    // Footer
    "footer.left": "TRINETRA AI · इस्रो SIH 26167",
    "footer.right": "100% स्थानिक-प्रथम एजंटिक एआय · OLLAMA + LANGCHAIN + LANGFUSE · एअर-गॅप केलेले",

    // Query Examples
    "examples.single.0": "या प्रतिमेमध्ये कोणत्या प्रकारचे जमीन वापर दिसत आहेत?",
    "examples.single.1": "जलसाठे आणि वनस्पतींच्या आच्छादनाचे वर्णन करा.",
    "examples.single.2": "क्वेरीमध्ये उल्लेख केलेला जलसाठा हायलाइट करा",
    "examples.temporal.0": "या दोन तारखांमध्ये कोणते बदल दिसून येत आहेत?",
    "examples.temporal.1": "बांधकाम क्षेत्रात वाढ झाली आहे, घट झाली आहे की ते अपरिवर्तित राहिले आहे?",
    "examples.temporal.2": "वनस्पतींचे लक्षणीय नुकसान झालेले भाग दाखवा.",
    "examples.fusion.0": "संयुक्त मोडॅलिटी डेटा वापरून पूरग्रस्त भाग ओळखा.",
    "examples.fusion.1": "या भागाच्या ऑप्टिकल आणि रडार स्वाक्षऱ्यांची तुलना करा.",

    // Demo Scenarios
    "scenario.urban.title": "शहरी वाढ",
    "scenario.urban.query": "या दोन तारखांमध्ये कोणते बदल दिसून येत आहेत?",
    "scenario.urban.response": "विश्लेषण दृश्याच्या पूर्व सीमेवर **मोजता येण्याजोग्या नागरी विस्ताराची** नोंद करते. नवीन बांधकाम पृष्ठभागामध्ये 18% वाढ दिसून येते, तर मध्यवर्ती रस्ता स्थिर राहतो. हायलाइट केलेले पुरावा भाग दर्शवतात की पक्क्या बांधकामाने मिश्र वनस्पतींची जागा घेतली आहे.",
    "scenario.flood.title": "पूर मॅपिंग",
    "scenario.flood.query": "संयुक्त मोडॅलिटी डेटा वापरून पूरग्रस्त भाग ओळखा.",
    "scenario.flood.response": "एकत्रित ऑप्टिकल आणि SAR पुरावा **दक्षिण सखल भागात साचलेले पाणी** दर्शवतो. रडार-डार्क भाग सखल शेतजमिनींशी जुळतात आणि ते बारमाही जलसाठ्यांपेक्षा वेगळे आहेत. ढगाळ वातावरणामुळे ऑप्टिकल पुष्टी मर्यादित असल्याने विश्वासार्हता मध्यम आहे.",
    "scenario.landuse.title": "जमीन वापर स्कॅन",
    "scenario.landuse.query": "या प्रतिमेमध्ये कोणत्या प्रकारचे जमीन वापर दिसत आहेत?",
    "scenario.landuse.response": "हे दृश्य प्रामुख्याने **शेतीप्रधान** आहे, ज्यामध्ये आयताकृती शेतीचे भूखंड, एक लहान वस्ती आणि नदीकाठची वनस्पती आढळते. एक पक्का रस्ता उत्तरेकडील शेतांना नैऋत्येकडील घनदाट वस्तीपासून वेगळा करतो.",
    "scenario.deforestation.title": "वनस्पती नुकसान",
    "scenario.deforestation.query": "वनस्पतींचे लक्षणीय नुकसान झालेले भाग दाखवा.",
    "scenario.deforestation.response": "वायव्य भागात वनस्पतींचे लक्षणीय नुकसान दिसून येते. बदल झालेला भाग अंदाजे 6.4 हेक्टर व्यापतो आणि तो वृक्षतोडीच्या हालचालींशी सुसंगत आहे. कारवाई करण्यापूर्वी हंगामी उपग्रह प्रतिमांद्वारे पडताळणी करा.",

    // Accessibility
    "aria.menu": "नेव्हिगेशन मेनू उघडा/बंद करा",
    "aria.language": "भाषा निवडा",
    "aria.preview": "अपलोड केलेली उपग्रह प्रतिमा पूर्वावलोकन",
    "aria.remove_image": "अपलोड केलेली प्रतिमा काढा",
  }
} as const

export type TranslationKey = keyof typeof translations.en

interface I18nContextType {
  language: SupportedLanguage
  setLanguage: (lang: SupportedLanguage) => void
  t: (key: TranslationKey, params?: Record<string, string | number>) => string
  languages: LanguageOption[]
}

const I18nContext = createContext<I18nContextType | null>(null)

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<SupportedLanguage>(DEFAULT_LANGUAGE)
  const [isClient, setIsClient] = useState(false)

  // Initialize from localStorage or navigator
  useEffect(() => {
    setIsClient(true)
    try {
      const saved = (localStorage.getItem(STORAGE_KEY) || localStorage.getItem("satquery_lang")) as SupportedLanguage | null
      if (saved && (saved === "en" || saved === "hi" || saved === "mr")) {
        setLanguageState(saved)
        document.documentElement.lang = saved
      } else {
        // Check browser language
        const navLang = navigator.language.slice(0, 2).toLowerCase()
        if (navLang === "hi" || navLang === "mr") {
          setLanguageState(navLang)
          document.documentElement.lang = navLang
        } else {
          document.documentElement.lang = "en"
        }
      }
    } catch {
      // Fallback to default
    }
  }, [])

  const setLanguage = useCallback((lang: SupportedLanguage) => {
    setLanguageState(lang)
    try {
      localStorage.setItem(STORAGE_KEY, lang)
      document.documentElement.lang = lang
    } catch {
      // Storage unavailable
    }
  }, [])

  const t = useCallback((key: TranslationKey, params?: Record<string, string | number>): string => {
    const langDict = translations[language] || translations.en
    let text: string = (langDict as any)[key] || (translations.en as any)[key] || key

    if (params) {
      Object.entries(params).forEach(([paramKey, paramVal]) => {
        text = text.replace(new RegExp(`\\{${paramKey}\\}`, "g"), String(paramVal))
      })
    }

    return text
  }, [language])

  const contextValue = useMemo(() => ({
    language,
    setLanguage,
    t,
    languages: SUPPORTED_LANGUAGES
  }), [language, setLanguage, t])

  return React.createElement(I18nContext.Provider, { value: contextValue }, children)
}

export function useTranslation() {
  const context = useContext(I18nContext)
  if (!context) {
    // Fallback safe implementation if used outside provider
    return {
      language: DEFAULT_LANGUAGE,
      setLanguage: () => {},
      t: (key: TranslationKey, params?: Record<string, string | number>) => {
        let text: string = (translations.en as any)[key] || key
        if (params) {
          Object.entries(params).forEach(([k, v]) => {
            text = text.replace(new RegExp(`\\{${k}\\}`, "g"), String(v))
          })
        }
        return text
      },
      languages: SUPPORTED_LANGUAGES
    }
  }
  return context
}
