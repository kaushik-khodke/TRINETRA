"""
TRINETRA Phase 8 — Report Integrity & Claim Validator
Strict claim-to-evidence enforcement and non-causal attribution verification.
"""

from typing import List

try:
    from backend.workspace.models import ReportDocument, ReportSection, ReportClaim
except ImportError:
    from workspace.models import ReportDocument, ReportSection, ReportClaim


class ClaimEvidenceError(Exception):
    """Raised when a claim lacks supporting evidence references."""
    pass


class CausalAttributionWarning(Warning):
    """Warns when an intelligence claim infers human intent or unverified causality."""
    pass


class ReportValidator:
    """
    Ensures that every analytical claim is grounded in verified evidence
    and adheres to strict non-causal observation principles.
    """

    DISALLOWED_CAUSAL_PHRASES = [
        "deliberately",
        "intentional sabotage",
        "malicious intent",
        "criminal activity",
        "hostile operation",
        "intentionally destroyed",
        "maliciously",
    ]

    @classmethod
    def validate_report(cls, report: ReportDocument, strict_claims: bool = True) -> List[str]:
        """
        Validates report claims against evidence grounding rules.
        Returns a list of warnings if non-causal phrases are encountered.
        Raises ClaimEvidenceError if a claim has no evidence citations.
        """
        warnings: List[str] = []

        if not report.title or not report.title.strip():
            raise ValueError("Report must have a valid non-empty title.")

        total_claims = 0

        for section in report.sections:
            # Check text for causal attribution violations
            sec_text = (section.content or "").lower()
            for phrase in cls.DISALLOWED_CAUSAL_PHRASES:
                if phrase in sec_text:
                    warnings.append(
                        f"Section '{section.title}' contains causal attribution phrase: '{phrase}'. "
                        "Earth observation analysis should state physical changes without inferring intent."
                    )

            # Check individual claims
            for claim in section.claims:
                total_claims += 1
                claim_text = (claim.text or "").lower()
                for phrase in cls.DISALLOWED_CAUSAL_PHRASES:
                    if phrase in claim_text:
                        warnings.append(
                            f"Claim '{claim.claim_id}' contains causal attribution phrase: '{phrase}'."
                        )

                if strict_claims:
                    if not claim.evidence_ids or len(claim.evidence_ids) == 0:
                        raise ClaimEvidenceError(
                            f"Claim '{claim.claim_id}' ('{claim.text[:40]}...') lacks supporting evidence IDs. "
                            "Every claim must cite at least one verified evidence source."
                        )

        return warnings
