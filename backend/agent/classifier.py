"""
SatQuery AI — Intent & Task Classifier
Interprets natural-language queries and input configurations to classify requested remote-sensing tasks.
"""

import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ClassificationResult(BaseModel):
    task: str
    confidence: float
    target_entities: List[str] = []
    reasoning: str
    recommended_tools: List[str]

class TaskClassifier:
    """Deterministic, rule-guided & semantic classifier for remote-sensing queries."""

    # Keywords patterns
    CHANGE_PATTERNS = [
        r"\b(change|changed|changes|changing)\b",
        r"\b(between (these|the) (two|dates|images|observations))\b",
        r"\b(increase|increased|decrease|decreased|remained unchanged)\b",
        r"\b(before and after|difference|temporal|shift|expansion|urban sprawl|deforestation)\b",
        r"\b(what happened|what changed)\b"
    ]

    OPTICAL_SAR_PATTERNS = [
        r"\b(optical and sar|sar and optical|multimodal|cross-modal)\b",
        r"\b(both sensors|radar and optical|synthetic aperture radar)\b",
        r"\b(penetrat|cloud cover|all-weather|day.?and.?night|backscatter)\b",
        r"\b(complementary|fused|fusion|co-registered)\b"
    ]

    GROUNDING_PATTERNS = [
        r"\b(highlight|locate|find|detect|point out|pinpoint|mark|outline|show me where)\b",
        r"\b(where is|where are|bounding box|segment|localize|region of)\b"
    ]

    CAPTION_PATTERNS = [
        r"\b(describe|description|summarize|overview|scene summary|caption)\b",
        r"\b(what is in this (image|scene)|land.?cover overview|general appearance)\b",
        r"\b(list major objects|detail the scene|tell me about this satellite image)\b"
    ]

    def classify(self, query: str, input_mode: str, num_images: int, image_modalities: Optional[List[str]] = None) -> ClassificationResult:
        clean_query = query.strip().lower()
        image_modalities = [m.lower() for m in (image_modalities or [])]

        # 1. Optical + SAR Cross-Modal check
        is_optical_sar_input = (
            input_mode == "optical_sar" or 
            (num_images == 2 and "optical" in image_modalities and "sar" in image_modalities)
        )
        optical_sar_match = any(re.search(p, clean_query) for p in self.OPTICAL_SAR_PATTERNS)

        if is_optical_sar_input or (optical_sar_match and num_images >= 2):
            return ClassificationResult(
                task="optical_sar_fusion",
                confidence=0.96 if is_optical_sar_input else 0.88,
                target_entities=self._extract_entities(clean_query),
                reasoning="Optical + SAR multimodal configuration detected with cross-modal query intent.",
                recommended_tools=["validator", "optical_sar", "report_gen"]
            )

        # 2. Bi-Temporal Change check
        is_temporal_input = (input_mode == "bi_temporal" or num_images == 2)
        change_match = any(re.search(p, clean_query) for p in self.CHANGE_PATTERNS)

        if is_temporal_input and (change_match or input_mode == "bi_temporal"):
            return ClassificationResult(
                task="change_analysis",
                confidence=0.95 if change_match else 0.85,
                target_entities=self._extract_entities(clean_query),
                reasoning="Bi-temporal image pair detected with temporal change analysis query.",
                recommended_tools=["validator", "change_ai", "report_gen"]
            )

        # 3. Grounding / Localization check
        grounding_match = any(re.search(p, clean_query) for p in self.GROUNDING_PATTERNS)
        if grounding_match and num_images == 1:
            entities = self._extract_entities(clean_query)
            return ClassificationResult(
                task="grounding",
                confidence=0.92,
                target_entities=entities,
                reasoning="Single-image text-guided grounding query requesting feature localization.",
                recommended_tools=["validator", "rs_ground", "report_gen"]
            )

        # 4. Captioning / Scene Description check
        caption_match = any(re.search(p, clean_query) for p in self.CAPTION_PATTERNS)
        if caption_match and num_images == 1:
            return ClassificationResult(
                task="captioning",
                confidence=0.90,
                target_entities=self._extract_entities(clean_query),
                reasoning="Single-image scene description / captioning query intent.",
                recommended_tools=["validator", "rs_caption", "report_gen"]
            )

        # 5. Default Single-Image VQA
        return ClassificationResult(
            task="vqa",
            confidence=0.88,
            target_entities=self._extract_entities(clean_query),
            reasoning="Single-image natural-language question answering intent.",
            recommended_tools=["validator", "rs_vqa", "report_gen"]
        )

    def _extract_entities(self, query: str) -> List[str]:
        target_features = [
            "water body", "water", "river", "lake", "ocean", "reservoir",
            "built-up", "buildings", "urban", "settlement", "residential", "infrastructure",
            "vegetation", "forest", "trees", "crop", "agricultural land", "farmland",
            "runway", "airport", "aircraft", "road", "highway", "bridge",
            "barren", "soil", "sand", "wetland", "clouds", "vessel", "ship"
        ]
        found = []
        for feature in target_features:
            if feature in query:
                found.append(feature)
        return found
