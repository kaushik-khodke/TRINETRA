"""
TRINETRA Phase 8 — Report Manifest Generator
Computes cryptographic SHA-256 integrity checksums for reports and export packages.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

try:
    from backend.workspace.models import ReportDocument
except ImportError:
    from workspace.models import ReportDocument


class ReportManifestGenerator:
    """
    Generates a verifiable tamper-evident cryptographic manifest for an intelligence dossier.
    """

    @classmethod
    def generate_manifest(
        cls,
        report: ReportDocument,
        additional_files: Dict[str, bytes] = None,
    ) -> Dict[str, Any]:
        section_hashes: Dict[str, str] = {}
        total_claims = 0

        for sec in report.sections:
            sec_payload = {
                "section_id": sec.section_id,
                "type": sec.type,
                "title": sec.title,
                "content": sec.content,
                "claims": [c.to_dict() for c in sec.claims],
            }
            sec_bytes = json.dumps(sec_payload, sort_keys=True).encode("utf-8")
            section_hashes[sec.section_id] = hashlib.sha256(sec_bytes).hexdigest()
            total_claims += len(sec.claims)

        file_hashes: Dict[str, str] = {}
        if additional_files:
            for fname, bdata in additional_files.items():
                file_hashes[fname] = hashlib.sha256(bdata).hexdigest()

        overall_bytes = json.dumps({
            "report_id": report.report_id,
            "title": report.title,
            "sections": section_hashes,
            "files": file_hashes,
        }, sort_keys=True).encode("utf-8")
        overall_sha256 = hashlib.sha256(overall_bytes).hexdigest()

        return {
            "report_id": report.report_id,
            "title": report.title,
            "version": report.version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_sections": len(report.sections),
            "total_claims": total_claims,
            "overall_sha256": overall_sha256,
            "section_hashes": section_hashes,
            "file_hashes": file_hashes,
        }
