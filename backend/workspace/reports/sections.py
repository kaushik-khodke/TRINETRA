"""
TRINETRA Phase 8 — Report Section Factory
Constructs typed, structured analytical sections for intelligence dossiers.
"""

import uuid
from typing import Dict, Any, List, Optional

try:
    from backend.workspace.models import ReportSection, ReportClaim
except ImportError:
    from workspace.models import ReportSection, ReportClaim


class ReportSectionFactory:
    """
    Builds modular, standardized report sections for intelligence reporting.
    """

    @staticmethod
    def create_title_section(
        title: str,
        classification: str = "UNCLASSIFIED / FOR OFFICIAL USE ONLY",
        author: str = "TRINETRA Analyst Command Center",
    ) -> ReportSection:
        content = f"**Classification**: {classification}\n\n**Prepared by**: {author}\n\n**Report Title**: {title}"
        return ReportSection(
            section_id=f"sec-{uuid.uuid4().hex[:8]}",
            type="TITLE",
            title="Dossier Identification",
            content=content,
            author_type="SYSTEM_GENERATED",
        )

    @staticmethod
    def create_executive_summary(
        summary_text: str,
        claims: Optional[List[ReportClaim]] = None,
    ) -> ReportSection:
        return ReportSection(
            section_id=f"sec-{uuid.uuid4().hex[:8]}",
            type="SUMMARY",
            title="Executive Summary",
            content=summary_text,
            claims=claims or [],
            author_type="ANALYST_AUTHORED",
        )

    @staticmethod
    def create_findings_section(
        findings_markdown: str,
        source_ids: Optional[List[str]] = None,
        claims: Optional[List[ReportClaim]] = None,
    ) -> ReportSection:
        return ReportSection(
            section_id=f"sec-{uuid.uuid4().hex[:8]}",
            type="FINDINGS",
            title="Observed Findings & Detection Metrics",
            content=findings_markdown,
            source_ids=source_ids or [],
            claims=claims or [],
            author_type="MIXED",
        )

    @staticmethod
    def create_evidence_section(
        evidence_markdown: str,
        evidence_ids: Optional[List[str]] = None,
    ) -> ReportSection:
        return ReportSection(
            section_id=f"sec-{uuid.uuid4().hex[:8]}",
            type="EVIDENCE",
            title="Evidence Audit & Source Grounding",
            content=evidence_markdown,
            source_ids=evidence_ids or [],
            author_type="SYSTEM_GENERATED",
        )

    @staticmethod
    def create_limitations_section(
        limitations_text: str,
    ) -> ReportSection:
        return ReportSection(
            section_id=f"sec-{uuid.uuid4().hex[:8]}",
            type="LIMITATIONS",
            title="Analytical Constraints & Sensor Limitations",
            content=limitations_text,
            author_type="SYSTEM_GENERATED",
        )

    @staticmethod
    def create_provenance_section(
        provenance_text: str,
    ) -> ReportSection:
        return ReportSection(
            section_id=f"sec-{uuid.uuid4().hex[:8]}",
            type="PROVENANCE",
            title="Cryptographic Manifest & Processing Provenance",
            content=provenance_text,
            author_type="SYSTEM_GENERATED",
        )
