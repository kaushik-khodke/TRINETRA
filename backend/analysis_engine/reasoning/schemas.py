"""
TRINETRA Analysis Engine — Reasoning Schemas
Strict structured output schemas used for Ollama native JSON schema constrained generation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FindingSchema(BaseModel):
    id: str = Field(..., description="Finding identifier (e.g., F01, F02)")
    title: str = Field(..., description="Concise title describing the verified finding")
    statement: str = Field(..., description="Factual explanation citing only verified metrics")
    evidence_ids: List[str] = Field(..., description="List of evidence IDs that support this finding (e.g. ['E_CHG01'])")
    confidence: str = Field(..., description="HIGH | MEDIUM | LOW | INSUFFICIENT")
    limitation_ids: List[str] = Field(default_factory=list, description="Associated limitation codes (e.g. ['CLOUD_CONTAMINATION'])")


class AnalysisNarrativeSchema(BaseModel):
    executive_summary: str = Field(..., description="High-level synthesis of verified observations and evidence")
    findings: List[FindingSchema] = Field(..., description="List of evidence-grounded findings")
    interpretation: str = Field(..., description="Physical/domain interpretation grounded strictly in the data")
    overall_confidence: str = Field(..., description="HIGH | MEDIUM | LOW | INSUFFICIENT")
    limitations_summary: Optional[str] = Field(default=None, description="Discussion of sensor limitations, clouds, or noise")
