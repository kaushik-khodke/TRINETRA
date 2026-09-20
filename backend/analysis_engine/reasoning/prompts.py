"""
TRINETRA Analysis Engine — LLM Grounding Prompts
Enforces strict negative constraints and formats compact evidence summaries.
"""

from typing import Dict, Any, List
from analysis_engine.evidence.models import EvidencePack

SYSTEM_REASONING_PROMPT = """You are TRINETRA's Earth-Observation Scientific Reasoning Engine.
Your sole responsibility is to explain and synthesize verified mathematical and spatial evidence.

ABSOLUTE NEGATIVE CONSTRAINTS:
1. You MUST ONLY state findings directly substantiated by the provided Evidence IDs.
2. DO NOT invent or fabricate:
   - Coordinates, bounding boxes, or geographic extents
   - Dates, orbit numbers, or sensor platforms not in evidence
   - Areas (m², hectares, km²), pixel counts, or change percentages
   - Object counts or hallucinated structures
   - Model confidence ratings
3. Every finding MUST cite at least one valid Evidence ID (e.g. "E_CHG01", "E_XM01").
4. If evidence is insufficient, state explicitly that evidence is inconclusive.
5. Return ONLY a valid JSON object matching the provided schema. No chatter or markdown outside JSON.
"""


def build_compact_evidence_prompt(
    query: str,
    pack: EvidencePack,
    limitations: List[Dict[str, Any]],
) -> str:
    """
    Assembles a token-efficient, compact evidence context string for the LLM.
    """
    lines = [
        f"USER INQUIRY: \"{query}\"",
        f"ANALYSIS MODE: {pack.mode}",
        f"OBSERVATIONS: {', '.join(pack.observation_ids) if pack.observation_ids else 'Local Observation'}",
        "",
        "VERIFIED EVIDENCE ITEMS:",
    ]

    # Change regions
    for r in pack.change_regions[:8]:  # Cap at top 8 ranked regions
        lines.append(
            f"• [{r.id}] {r.label} | Area: {r.area_ha} ha ({r.area_m2} m²) | Pixels: {r.pixel_count} | Confidence: {r.confidence} | Centroid: {r.centroid}"
        )

    # Cross-modal items
    for xm in pack.cross_modal_items:
        lines.append(
            f"• [{xm.id}] {xm.label} | Confidence: {xm.confidence} | Support: SAR={xm.support.sar_confidence}, Optical={xm.support.optical_confidence}, Agreement={xm.support.agreement_score}"
        )

    # Grounding detections
    for g in pack.grounding_detections[:8]:
        lines.append(
            f"• [{g.id}] {g.label} | Confidence: {g.confidence} | BBox: {g.bbox}"
        )

    # Statistics
    stats = pack.statistics
    lines.append("")
    lines.append("QUANTITATIVE METRICS:")
    if "changed_pixels" in stats:
        lines.append(f"• Total Changed Pixels: {stats['changed_pixels']} / {stats.get('total_valid_pixels', 0)} ({stats.get('change_percentage', 0)}%)")
        lines.append(f"• Total Changed Area: {stats.get('area_ha', 0)} hectares ({stats.get('area_m2', 0)} m²)")
        lines.append(f"• Region Count: {len(pack.change_regions)}")

    if limitations:
        lines.append("")
        lines.append("DATA LIMITATIONS:")
        for lim in limitations:
            lines.append(f"• [{lim.get('code')}] {lim.get('description')}")

    lines.append("")
    lines.append("Synthesize these verified facts into the required structured narrative.")
    return "\n".join(lines)
