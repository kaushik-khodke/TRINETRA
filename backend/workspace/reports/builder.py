"""
TRINETRA Phase 8 — Report Builder
Assembles structured intelligence reports, validates claims, computes manifests, and updates storage.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from backend.workspace.models import ReportDocument, ReportSection, ReportStatus
    from backend.workspace.reports.validator import ReportValidator
    from backend.workspace.reports.manifest import ReportManifestGenerator
except ImportError:
    from workspace.models import ReportDocument, ReportSection, ReportStatus
    from workspace.reports.validator import ReportValidator
    from workspace.reports.manifest import ReportManifestGenerator


class ReportBuilder:
    """
    Coordinates report creation, claim validation, manifest signing, and persistence.
    """

    def __init__(self, repository=None, activity_tracker=None):
        self.repository = repository
        self.activity_tracker = activity_tracker

    def create_report(
        self,
        workspace_id: str,
        title: str,
        sections: List[ReportSection],
        strict_claims: bool = True,
    ) -> ReportDocument:
        report_id = f"rep-{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        report = ReportDocument(
            report_id=report_id,
            workspace_id=workspace_id,
            title=title,
            status=ReportStatus.DRAFT,
            sections=sections,
            version=1,
            manifest={},
            created_at=now_str,
            updated_at=now_str,
        )

        # Validate claims and text
        warnings = ReportValidator.validate_report(report, strict_claims=strict_claims)

        # Generate cryptographic manifest
        manifest = ReportManifestGenerator.generate_manifest(report)
        report.manifest = manifest
        report.status = ReportStatus.VALIDATED

        if self.repository:
            self.repository.save_report(report)

        if self.activity_tracker:
            self.activity_tracker.log(
                workspace_id=workspace_id,
                activity_type="REPORT_GENERATED",
                entity_type="REPORT",
                entity_id=report.report_id,
                details={
                    "title": title,
                    "sections_count": len(sections),
                    "claims_count": manifest.get("total_claims", 0),
                    "warnings_count": len(warnings),
                    "sha256": manifest.get("overall_sha256"),
                },
            )

        return report
