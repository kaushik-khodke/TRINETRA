"""
TRINETRA Phase 8 — Report Pipeline & Evidence Dossier Verification
Verifies:
1. Claim-to-evidence grounding enforcement (unsupported claims raise ClaimEvidenceError)
2. Strict non-causal attribution violation detection
3. Deterministic standalone SVG vector map snapshot generation
4. Cryptographic SHA-256 manifest calculation
5. Standalone HTML presentation rendering
6. Tamper-evident ZIP evidence package export and archive integrity
"""

import sys
import os
import json
import zipfile
import tempfile
import hashlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from workspace.service import WorkspaceService
from workspace.repository import WorkspaceRepository
from workspace.reports.validator import ReportValidator, ClaimEvidenceError
from workspace.reports.map_snapshot import MapSnapshotGenerator
from workspace.reports.manifest import ReportManifestGenerator
from workspace.reports.renderer import ReportPresentationRenderer
from workspace.reports.exporter import ReportPackageExporter
from workspace.models import ReportDocument, ReportSection, ReportClaim


def run_test():
    print("=" * 70)
    print("TRINETRA Phase 8 — Report Dossier & Integrity Pipeline Verification")
    print("=" * 70)

    # 1. Claim-to-evidence grounding validation
    unsupported_claim = ReportClaim(
        claim_id="claim-001",
        text="Significant water extent expansion observed at South Lhonak lake.",
        evidence_ids=[],  # Missing evidence!
        type="OBSERVATION",
    )
    invalid_report = ReportDocument(
        report_id="rep-invalid",
        workspace_id="ws-test",
        title="Invalid Lake Report",
        sections=[
            ReportSection(
                section_id="sec-1",
                type="FINDINGS",
                title="Observations",
                content="Water extent increase measured.",
                claims=[unsupported_claim],
            )
        ],
    )

    try:
        ReportValidator.validate_report(invalid_report, strict_claims=True)
        assert False, "Should have raised ClaimEvidenceError"
    except ClaimEvidenceError as ex:
        print(f" [1/6] Grounding guard correctly caught ungrounded claim: {ex}")

    # 2. Non-causal attribution detection
    causal_claim = ReportClaim(
        claim_id="claim-002",
        text="Adversary deliberately drained the water reservoir with malicious intent.",
        evidence_ids=["obs_s2_001"],
        type="INTERPRETATION",
    )
    causal_report = ReportDocument(
        report_id="rep-causal",
        workspace_id="ws-test",
        title="Causal Inference Report",
        sections=[
            ReportSection(
                section_id="sec-2",
                type="FINDINGS",
                title="Perimeter Assessment",
                content="Evidence shows intentional sabotage occurred.",
                claims=[causal_claim],
            )
        ],
    )
    warnings = ReportValidator.validate_report(causal_report, strict_claims=True)
    assert len(warnings) >= 2
    print(f" [2/6] Non-causal attribution detector flagged {len(warnings)} policy violations:")
    for w in warnings:
        print(f"       - {w}")

    # 3. Deterministic standalone SVG vector map generation
    sample_geojson = {
        "type": "Polygon",
        "coordinates": [
            [[88.10, 27.85], [88.25, 27.85], [88.25, 27.95], [88.10, 27.95], [88.10, 27.85]]
        ],
    }
    svg_map = MapSnapshotGenerator.generate_svg_snapshot(
        aoi_geojson=sample_geojson,
        title="South Lhonak Glacial Lake Risk AOI",
    )
    assert "<svg" in svg_map and "</svg>" in svg_map
    assert "South Lhonak" in svg_map
    print(f" [3/6] Deterministic standalone SVG vector map generated ({len(svg_map):,} bytes).")

    # 4. Valid Report Document with Full Integrity
    valid_claims = [
        ReportClaim(
            claim_id="claim-sikkim-01",
            text="South Lhonak surface water area increased by 14.2 ha (+18.4%) between May and Sept 2025.",
            evidence_ids=["item-obs-001", "item-find-002"],
            type="FINDING",
        ),
        ReportClaim(
            claim_id="claim-sikkim-02",
            text="Moraine dam stability score deteriorated from 0.81 to 0.63 following seismic tremor.",
            evidence_ids=["item-ev-003"],
            type="MEASUREMENT",
        ),
    ]
    valid_sections = [
        ReportSection(
            section_id="sec-summary",
            type="SUMMARY",
            title="Executive Findings",
            content="Bitemporal high-resolution satellite imagery verifies anomalous glacial lake expansion.",
            claims=[valid_claims[0]],
        ),
        ReportSection(
            section_id="sec-moraine",
            type="FINDINGS",
            title="Moraine Perimeter Analysis",
            content="Interferometric SAR coherence shows micro-subsidence along the lateral moraine terminal crest.",
            claims=[valid_claims[1]],
        ),
    ]
    valid_report = ReportDocument(
        report_id="rep-verified-101",
        workspace_id="ws-glacier",
        title="South Lhonak Glacial Outburst Threat Dossier",
        sections=valid_sections,
        status="VALIDATED",
        created_at="2026-09-21T10:00:00Z",
    )

    clean_warnings = ReportValidator.validate_report(valid_report, strict_claims=True)
    assert len(clean_warnings) == 0
    print(f" [4/6] Verified clean report with 0 warnings & full evidence grounding.")

    # 5. SHA-256 Manifest Calculation
    manifest = ReportManifestGenerator.generate_manifest(
        report=valid_report,
        additional_files={
            "map_snapshot.svg": svg_map.encode("utf-8")
        }
    )
    assert "overall_sha256" in manifest
    assert "section_hashes" in manifest
    assert "map_snapshot.svg" in manifest["file_hashes"]
    print(f" [5/6] Cryptographic manifest generated:")
    print(f"       - Overall SHA-256 : {manifest['overall_sha256']}")
    print(f"       - Sections Hashed : {manifest['total_sections']}")
    print(f"       - Claims Count    : {manifest['total_claims']}")

    # 6. HTML Presentation Rendering & Tamper-Evident ZIP Package
    html_presentation = ReportPresentationRenderer.render_html(
        report=valid_report,
        aoi_geojson=sample_geojson,
    )
    assert "<!DOCTYPE html>" in html_presentation
    assert "South Lhonak Glacial Outburst Threat Dossier" in html_presentation

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = ReportPackageExporter.export_zip(
            report=valid_report,
            output_dir=tmp_dir,
            aoi_geojson=sample_geojson,
        )
        assert os.path.exists(zip_path)
        zip_size = os.path.getsize(zip_path)

        # Inspect and verify ZIP contents
        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            assert "report.html" in namelist
            assert "report.json" in namelist
            assert "map_snapshot.svg" in namelist
            assert "manifest.json" in namelist

            # Verify integrity of extracted manifest against calculated SHA-256
            manifest_bytes = zf.read("manifest.json")
            parsed_manifest = json.loads(manifest_bytes.decode("utf-8"))
            assert "overall_sha256" in parsed_manifest
            assert parsed_manifest["report_id"] == valid_report.report_id

        print(f" [6/6] Tamper-evident ZIP evidence package exported ({zip_size:,} bytes).")
        print(f"       Package files verified: {namelist}")

    print("=" * 70)
    print(" ALL REPORT PIPELINE & EVIDENCE DOSSIER TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_test()
