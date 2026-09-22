"""
TRINETRA Phase 8 Tests — Reporting & Evidence Packages
Verifies claim-to-evidence enforcement, non-causal attribution checks,
cryptographic SHA-256 manifests, vector map generation, and tamper-evident ZIP export.
"""

import os
import zipfile
import pytest
from workspace.models import ReportClaim, ReportSection, ReportDocument, ReportStatus
from workspace.reports.sections import ReportSectionFactory
from workspace.reports.validator import ReportValidator, ClaimEvidenceError
from workspace.reports.manifest import ReportManifestGenerator
from workspace.reports.map_snapshot import MapSnapshotGenerator
from workspace.reports.renderer import ReportPresentationRenderer
from workspace.reports.builder import ReportBuilder
from workspace.reports.exporter import ReportPackageExporter
from workspace.repository import WorkspaceRepository


@pytest.fixture
def repo():
    return WorkspaceRepository(":memory:")


@pytest.fixture
def builder(repo):
    return ReportBuilder(repository=repo)


def test_claim_to_evidence_enforcement(builder):
    # Claim with evidence passes
    sec = ReportSectionFactory.create_findings_section(
        findings_markdown="Glacial lake expanded by 14.8 hectares",
        claims=[ReportClaim("c-1", "Water surface expanded by 14.8 ha", evidence_ids=["ev-obs-1"])],
    )
    report = builder.create_report("ws-1", "Glacial Lake Dossier", [sec], strict_claims=True)
    assert report.status == ReportStatus.VALIDATED
    assert report.manifest["total_claims"] == 1

    # Claim without evidence strictly rejected
    bad_sec = ReportSectionFactory.create_findings_section(
        findings_markdown="Unbacked claim",
        claims=[ReportClaim("c-bad", "Water expanded without proof", evidence_ids=[])],
    )
    with pytest.raises(ClaimEvidenceError) as exc:
        builder.create_report("ws-1", "Bad Dossier", [bad_sec], strict_claims=True)
    assert "lacks supporting evidence IDs" in str(exc.value)


def test_non_causal_attribution_warning():
    sec = ReportSectionFactory.create_findings_section(
        findings_markdown="The dam was intentionally destroyed by downstream forces.",
        claims=[ReportClaim("c-1", "Physical breach observed", evidence_ids=["ev-1"])],
    )
    rep = ReportDocument(report_id="r-causal", workspace_id="ws-1", title="Causal Test", sections=[sec])
    warnings = ReportValidator.validate_report(rep, strict_claims=True)

    assert len(warnings) > 0
    assert any("causal attribution phrase" in w for w in warnings)


def test_manifest_sha256_reproducibility():
    sec1 = ReportSectionFactory.create_title_section("Title Test")
    sec2 = ReportSectionFactory.create_limitations_section("No high-res SAR available.")
    rep = ReportDocument(report_id="rep-hash", workspace_id="ws-1", title="Manifest Dossier", sections=[sec1, sec2])

    m1 = ReportManifestGenerator.generate_manifest(rep)
    m2 = ReportManifestGenerator.generate_manifest(rep)

    assert m1["overall_sha256"] == m2["overall_sha256"]
    assert len(m1["overall_sha256"]) == 64


def test_map_snapshot_generator_svg():
    aoi = {
        "type": "Polygon",
        "coordinates": [[[77.1, 28.5], [77.3, 28.5], [77.3, 28.7], [77.1, 28.7], [77.1, 28.5]]],
    }
    findings = [{"finding_id": "F-01"}, {"finding_id": "F-02"}]

    svg = MapSnapshotGenerator.generate_svg_snapshot(aoi, findings=findings, title="Delhi Ridge AOI")
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Delhi Ridge AOI" in svg
    assert "F-01" in svg
    assert "polygon" in svg


def test_presentation_renderer_html():
    sec = ReportSectionFactory.create_executive_summary(
        "Severe glacial retreat observed.",
        claims=[ReportClaim("c-1", "Retreat rate 20m/year", evidence_ids=["ev-1", "ev-2"])],
    )
    rep = ReportDocument(report_id="rep-html", workspace_id="ws-1", title="Glacier Briefing", sections=[sec])
    rep.manifest = {"overall_sha256": "abcdef0123456789" * 4}

    html = ReportPresentationRenderer.render_html(rep)
    assert "<!DOCTYPE html>" in html
    assert "Glacier Briefing" in html
    assert "Presentation Mode" in html
    assert "Retreat rate 20m/year" in html
    assert "ev-1" in html


def test_zip_evidence_package_export(tmp_path):
    sec = ReportSectionFactory.create_executive_summary(
        "Final Intelligence Dossier.",
        claims=[ReportClaim("c-1", "Validated fact", evidence_ids=["ev-1"])],
    )
    rep = ReportDocument(report_id="rep-pkg", workspace_id="ws-1", title="Package Dossier", sections=[sec])

    zip_path = ReportPackageExporter.export_zip(rep, output_dir=str(tmp_path))
    assert os.path.exists(zip_path)
    assert zip_path.endswith(".zip")

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert "report.html" in namelist
        assert "report.json" in namelist
        assert "map_snapshot.svg" in namelist
        assert "manifest.json" in namelist
