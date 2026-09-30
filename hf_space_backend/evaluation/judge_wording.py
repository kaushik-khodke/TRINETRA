"""
TRINETRA Judge-Facing Wording & Claim Compliance Engine (Stage 11)
Governed by 11_STAGE_11_FINAL_VALIDATION.md and NON_NEGOTIABLE_PRINCIPLES.md.

Ensures that all judge-facing reports, metrics, executive summaries, and APIs
comply strictly with scientific standards and avoid unbacked marketing claims:

FORBIDDEN:
- "Our AI is always correct." / "100% accurate" / "foolproof" / "error-free"
- "ISRO-certified" / "ISRO approved" / "certified by ISRO"
- "SOTA" / "State of the art" unless the exact protocol supports the claim
- "Ground truth" for datasets that are not authoritative ground truth
- "94% confidence means 94% correct" unless calibration demonstrates it

MANDATORY APPROVED FORMULATIONS:
- "Independently benchmarked against published ground-truth datasets using reproducible evaluation protocols."
- "Empirically evaluated on canonical test partitions with 95% bootstrap confidence intervals."
- "Calibrated predictive uncertainty measured via Expected Calibration Error (ECE)."
- "Unannotated sensor reference data (not certified ground truth)."
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class WordingViolation(BaseModel):
    """Represents a detected forbidden claim or non-compliant phrase."""
    forbidden_pattern: str
    matched_snippet: str
    line_number: Optional[int] = None
    reason: str
    suggested_replacement: str


class ComplianceAuditResult(BaseModel):
    """Structured report of judge-facing wording compliance audit."""
    is_compliant: bool
    total_violations: int
    violations: List[WordingViolation] = Field(default_factory=list)
    compliance_score: float = 1.0
    audit_summary: str = "Compliant"


class JudgeFacingGlossary:
    """
    Automated inspector and sanitizer enforcing scientific communication standards
    for SIH 2026 / ISRO evaluation.
    """

    # Approved canonical statements
    CANONICAL_STATEMENTS = {
        "benchmark_grounding": (
            "Independently benchmarked against published ground-truth datasets "
            "using reproducible evaluation protocols."
        ),
        "calibration": (
            "Predictive uncertainty quantified via Expected Calibration Error (ECE) "
            "and post-hoc temperature scaling."
        ),
        "indian_eo": (
            "Evaluated on Indian Earth Observation rasters for geometric and radiometric consistency; "
            "unannotated sensor data is not labeled as authoritative ground truth."
        ),
        "limitations": (
            "Predictions are subject to sensor resolution boundaries, atmospheric interference, "
            "and coregistration tolerances."
        ),
        "statistical_rigor": (
            "All empirical metrics reported with 95% bootstrap confidence intervals."
        ),
    }

    # Forbidden patterns with rationale and suggested replacement
    FORBIDDEN_RULES: List[Dict[str, str]] = [
        {
            "pattern": r"(?i)\b(always\s+correct|100%\s+accurate|foolproof|error[-\s]?free|flawless|infallible|bulletproof)\b",
            "reason": "Absolute accuracy claims violate scientific integrity and probabilistic reality.",
            "replacement": "empirically characterized with documented failure boundaries"
        },
        {
            "pattern": r"(?i)\b(isro[-\s]?certified|certified\s+by\s+isro|isro[-\s]?approved|nrsc[-\s]?approved)\b",
            "reason": "TRINETRA is a competitive submission for SIH 2026, not an officially certified ISRO production system.",
            "replacement": "designed in alignment with ISRO Problem Statement 26167 guidelines"
        },
        {
            "pattern": r"(?i)\b(sota|state[-\s]?of[-\s]?the[-\s]?art)\b(?!\s+(?:on|under|according to)\s+[A-Za-z0-9_\-]+(?:\s+protocol)?)",
            "reason": "Unqualified SOTA claims without specifying the exact benchmark protocol are forbidden.",
            "replacement": "competitive with published literature on canonical benchmarks"
        },
        {
            "pattern": r"(?i)(?:unannotated|raw|bhuvan|cartosat|liss|risat)[\w\s]{0,30}\bground\s+truth\b",
            "reason": "Unannotated satellite rasters or derived proxy labels cannot be called ground truth.",
            "replacement": "sensor reference data (unannotated)"
        },
        {
            "pattern": r"(?i)\b\d{1,3}%\s+confidence\s+(?:means|equals|guarantees)\s+\d{1,3}%\s+correct\b",
            "reason": "Confidence cannot be equated with correctness without explicit empirical calibration curves.",
            "replacement": "calibrated expectation with measured ECE"
        },
        {
            "pattern": r"(?i)\b(unmatched|unbeatable|superior\s+to\s+all|unrivaled)\b",
            "reason": "Subjective superlative claims without empirical statistical comparisons are disallowed.",
            "replacement": "demonstrating measurable empirical advantages on benchmark test splits"
        },
    ]

    @classmethod
    def audit_text(cls, text: str) -> ComplianceAuditResult:
        """
        Scans a text or markdown document for non-compliant claims.
        Returns a structured ComplianceAuditResult.
        """
        if not text or not text.strip():
            return ComplianceAuditResult(
                is_compliant=True,
                total_violations=0,
                violations=[],
                compliance_score=1.0,
                audit_summary="Empty or clean document."
            )

        violations: List[WordingViolation] = []
        lines = text.split("\n")

        for line_idx, line in enumerate(lines, start=1):
            for rule in cls.FORBIDDEN_RULES:
                regex = re.compile(rule["pattern"])
                for match in regex.finditer(line):
                    # Check context: If the line explicitly says "Avoid:" or "Forbidden:" (e.g. documentation), skip
                    prefix = line[:match.start()]
                    if re.search(r"(?i)\b(avoid|forbidden|disallow|rule|warning|do\s+not)\b", prefix):
                        continue

                    violations.append(
                        WordingViolation(
                            forbidden_pattern=rule["pattern"],
                            matched_snippet=match.group(0),
                            line_number=line_idx,
                            reason=rule["reason"],
                            suggested_replacement=rule["replacement"]
                        )
                    )

        total_v = len(violations)
        is_compliant = (total_v == 0)
        # Score decreases per violation with lower bound of 0.0
        score = max(0.0, round(1.0 - (total_v * 0.2), 2))

        summary = (
            "Audited: 100% compliant with judge-facing scientific standards."
            if is_compliant
            else f"Audited: Found {total_v} forbidden marketing or uncalibrated claim(s)."
        )

        return ComplianceAuditResult(
            is_compliant=is_compliant,
            total_violations=total_v,
            violations=violations,
            compliance_score=score,
            audit_summary=summary
        )

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Performs safe automated substitutions of forbidden phrases with approved
        scientific wording.
        """
        sanitized = text
        for rule in cls.FORBIDDEN_RULES:
            regex = re.compile(rule["pattern"])
            sanitized = regex.sub(rule["replacement"], sanitized)
        return sanitized

    @classmethod
    def get_canonical_statement(cls, key: str) -> str:
        """Returns verified approved statements for inclusion in reports."""
        return cls.CANONICAL_STATEMENTS.get(
            key,
            "Independently benchmarked against published ground-truth datasets."
        )
