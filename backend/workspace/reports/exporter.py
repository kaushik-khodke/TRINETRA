"""
TRINETRA Phase 8 — Report Package Exporter
Packages standalone HTML, JSON, vector SVG maps, and manifest into a tamper-evident ZIP archive.
"""

import os
import io
import zipfile
import json
from typing import Dict, Any, Optional

try:
    from backend.config.settings import settings
except ImportError:
    from config.settings import settings

try:
    from backend.workspace.models import ReportDocument
    from backend.workspace.reports.renderer import ReportPresentationRenderer
    from backend.workspace.reports.map_snapshot import MapSnapshotGenerator
    from backend.workspace.reports.manifest import ReportManifestGenerator
except ImportError:
    from workspace.models import ReportDocument
    from workspace.reports.renderer import ReportPresentationRenderer
    from workspace.reports.map_snapshot import MapSnapshotGenerator
    from workspace.reports.manifest import ReportManifestGenerator


class ReportPackageExporter:
    """
    Creates standalone ZIP archives containing the complete dossier evidence package.
    """

    @classmethod
    def export_zip(
        cls,
        report: ReportDocument,
        output_dir: Optional[str] = None,
        aoi_geojson: Optional[Dict[str, Any]] = None,
    ) -> str:
        target_dir = output_dir or getattr(settings, "workspace_artifacts_dir", getattr(settings, "reports_dir", "outputs/reports"))
        os.makedirs(target_dir, exist_ok=True)

        zip_filename = f"{report.report_id}_evidence_package.zip"
        zip_path = os.path.join(target_dir, zip_filename)

        html_content = ReportPresentationRenderer.render_html(report, aoi_geojson=aoi_geojson)
        svg_map = MapSnapshotGenerator.generate_svg_snapshot(aoi_geojson, title=report.title)
        report_json = json.dumps(report.to_dict(), indent=2)

        additional_files = {
            "report.html": html_content.encode("utf-8"),
            "report.json": report_json.encode("utf-8"),
            "map_snapshot.svg": svg_map.encode("utf-8"),
        }

        # Update and sign manifest with file hashes
        manifest = ReportManifestGenerator.generate_manifest(report, additional_files=additional_files)
        manifest_json = json.dumps(manifest, indent=2)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("report.html", html_content)
            zf.writestr("report.json", report_json)
            zf.writestr("map_snapshot.svg", svg_map)
            zf.writestr("manifest.json", manifest_json)

        # Verify max package size limit
        file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        max_size_mb = getattr(settings, "workspace_max_report_size_mb", 50)
        if file_size_mb > max_size_mb:
            os.remove(zip_path)
            raise ValueError(f"Report export size ({file_size_mb:.1f} MB) exceeds maximum allowed ({max_size_mb} MB).")

        return zip_path
