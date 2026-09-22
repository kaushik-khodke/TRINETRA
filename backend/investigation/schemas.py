"""
TRINETRA Phase 6 — Investigation Schemas
Pydantic schemas for API contracts, findings, hypotheses, evidence, and LLM structured outputs.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000, description="Natural-language analytical enquiry")
    aoi: Optional[Dict[str, Any]] = Field(None, description="GeoJSON Polygon or bounding box geometry")
    observation_ids: List[str] = Field(default_factory=list, description="IDs of target satellite acquisitions")
    temporal_range: Optional[Dict[str, str]] = Field(None, description="ISO datetime start and end bounds")
    temporal_scope: Optional[Dict[str, Any]] = Field(default_factory=dict, description="ISO datetime start and end bounds or scope dictionary")
    options: Dict[str, Any] = Field(default_factory=dict, description="Execution overrides and tuning knobs")


class StructuredFinding(BaseModel):
    finding_id: str = Field(..., description="Finding ID e.g. F01")
    title: str = ""
    statement: str
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_ids: List[str] = Field(default_factory=list, description="Mandatory supporting evidence token IDs")
    bounding_box: Optional[List[float]] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)

    @property
    def quantitative_value(self) -> Dict[str, Any]:
        return self.metrics

    @property
    def supporting_evidence_ids(self) -> List[str]:
        return self.evidence_ids

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "title": self.title,
            "statement": self.statement,
            "category": self.category,
            "confidence": self.confidence,
            "evidence_ids": self.evidence_ids,
            "supporting_evidence_ids": self.evidence_ids,
            "bounding_box": self.bounding_box,
            "metrics": self.metrics,
            "quantitative_value": self.metrics,
        }


class SemanticHypothesis(BaseModel):
    hypothesis_id: str = Field(..., description="Hypothesis ID e.g. H01")
    statement: str
    semantic_class: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    findings_refs: List[str] = Field(default_factory=list)
    status: str = "ACCEPTED"
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict)
    alternative_hypotheses: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def description(self) -> str:
        return self.statement

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "statement": self.statement,
            "description": self.statement,
            "semantic_class": self.semantic_class,
            "confidence": self.confidence,
            "supporting_evidence_ids": self.supporting_evidence_ids,
            "contradicting_evidence_ids": self.contradicting_evidence_ids,
            "findings_refs": self.findings_refs,
            "status": self.status,
            "confidence_breakdown": self.confidence_breakdown,
            "alternative_hypotheses": self.alternative_hypotheses,
        }


class EvidenceConflict(BaseModel):
    conflict_id: str
    modality_a: str = "OPTICAL"
    evidence_a: str = ""
    modality_b: str = "SAR"
    evidence_b: str = ""
    explanation: str = ""
    status: str = "unresolved"
    evidence_a_id: Optional[str] = None
    evidence_b_id: Optional[str] = None
    conflict_type: str = "OPTICAL_SAR_DISCREPANCY"
    severity: str = "medium"
    description: str = ""
    resolution_strategy: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "modality_a": self.modality_a,
            "evidence_a": self.evidence_a,
            "modality_b": self.modality_b,
            "evidence_b": self.evidence_b,
            "explanation": self.explanation,
            "status": self.status,
            "evidence_a_id": self.evidence_a_id,
            "evidence_b_id": self.evidence_b_id,
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "description": self.description or self.explanation,
            "resolution_strategy": self.resolution_strategy or "Preserve both signatures without averaging away discrepancy.",
        }


class InvestigationValidationResponse(BaseModel):
    valid: bool
    intent: str
    estimated_compute_cost: str  # "LOW", "MEDIUM", "HIGH"
    planned_specialists: List[str]
    estimated_runtime_seconds: float
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class InvestigationConclusionSchema(BaseModel):
    """Native JSON schema emitted by local Ollama model."""
    executive_summary: str
    findings: List[StructuredFinding] = Field(default_factory=list)
    hypotheses: List[SemanticHypothesis] = Field(default_factory=list)
    confidence_explanation: str
    limitations: List[str] = Field(default_factory=list)


class InvestigationResult(BaseModel):
    investigation_id: str
    status: str
    question: str
    intent: str
    aoi_bounds: Optional[List[float]] = None
    observation_ids: List[str] = Field(default_factory=list)
    execution_time_seconds: float
    findings: List[StructuredFinding] = Field(default_factory=list)
    hypotheses: List[SemanticHypothesis] = Field(default_factory=list)
    conflicts: List[EvidenceConflict] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    narrative: Dict[str, Any] = Field(default_factory=dict)
    confidence: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
