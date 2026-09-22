"""
TRINETRA Phase 8 — Standalone HTML & Presentation Report Renderer
Generates presentation-mode and publication-ready HTML intelligence briefings with embedded vector maps.
"""

import html
from typing import Dict, Any, Optional

try:
    from backend.workspace.models import ReportDocument
    from backend.workspace.reports.map_snapshot import MapSnapshotGenerator
except ImportError:
    from workspace.models import ReportDocument
    from workspace.reports.map_snapshot import MapSnapshotGenerator


class ReportPresentationRenderer:
    """
    Renders ReportDocument instances into self-contained HTML documents.
    """

    @classmethod
    def render_html(
        cls,
        report: ReportDocument,
        aoi_geojson: Optional[Dict[str, Any]] = None,
    ) -> str:
        safe_title = html.escape(report.title)
        map_svg = MapSnapshotGenerator.generate_svg_snapshot(aoi_geojson, title=f"AOI Overview — {safe_title}")

        sections_html = []
        for sec in report.sections:
            sec_title = html.escape(sec.title)
            sec_content = html.escape(sec.content).replace("\n", "<br/>")

            claims_html = []
            if sec.claims:
                claims_html.append("<div class='claims-container'><h4 class='claims-heading'>Verified Claims & Evidence Links</h4><ul class='claims-list'>")
                for c in sec.claims:
                    c_text = html.escape(c.text)
                    ev_badges = "".join([f"<span class='badge badge-evidence'>{html.escape(eid)}</span>" for eid in c.evidence_ids])
                    claims_html.append(
                        f"<li class='claim-item'>"
                        f"<div class='claim-text'>{c_text}</div>"
                        f"<div class='claim-sources'><span class='label'>Grounding:</span> {ev_badges}</div>"
                        f"</li>"
                    )
                claims_html.append("</ul></div>")

            sections_html.append(f"""
            <section class="report-section" id="{html.escape(sec.section_id)}">
                <div class="section-badge">{html.escape(sec.type)}</div>
                <h2 class="section-title">{sec_title}</h2>
                <div class="section-body">{sec_content}</div>
                {''.join(claims_html)}
            </section>
            """)

        manifest_hash = report.manifest.get("overall_sha256", "UNVERIFIED") if report.manifest else "UNVERIFIED"

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRINETRA Dossier: {safe_title}</title>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #182234;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #0284c7;
            --accent-glow: #38bdf8;
            --border: #334155;
            --success: #10b981;
        }}
        body {{
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }}
        .header {{
            background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
            border-bottom: 1px solid var(--border);
            padding: 2.5rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header-left h1 {{
            margin: 0;
            font-size: 1.8rem;
            color: var(--accent-glow);
            letter-spacing: -0.02em;
        }}
        .header-meta {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-top: 0.5rem;
            font-family: monospace;
        }}
        .controls {{
            display: flex;
            gap: 1rem;
        }}
        .btn-presentation {{
            background: var(--accent);
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-presentation:hover {{
            background: var(--accent-glow);
        }}
        .container {{
            max-width: 900px;
            margin: 2rem auto;
            padding: 0 1.5rem;
        }}
        .map-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 2rem;
        }}
        .report-section {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.8rem;
            margin-bottom: 1.5rem;
        }}
        .section-badge {{
            display: inline-block;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--accent-glow);
            background: rgba(2, 132, 199, 0.15);
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            margin-bottom: 0.75rem;
            font-family: monospace;
        }}
        .section-title {{
            margin-top: 0;
            font-size: 1.3rem;
            color: var(--text-primary);
        }}
        .section-body {{
            color: #cbd5e1;
            font-size: 0.95rem;
        }}
        .claims-container {{
            margin-top: 1.5rem;
            padding-top: 1.2rem;
            border-top: 1px dashed var(--border);
        }}
        .claims-heading {{
            margin: 0 0 0.8rem 0;
            font-size: 0.9rem;
            color: var(--text-secondary);
            text-transform: uppercase;
        }}
        .claims-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .claim-item {{
            background: rgba(15, 23, 42, 0.6);
            border-left: 3px solid var(--success);
            padding: 0.75rem 1rem;
            margin-bottom: 0.6rem;
            border-radius: 0 4px 4px 0;
        }}
        .claim-text {{
            font-weight: 500;
            color: #f1f5f9;
        }}
        .claim-sources {{
            margin-top: 0.4rem;
            font-size: 0.8rem;
        }}
        .badge-evidence {{
            display: inline-block;
            background: #334155;
            color: #38bdf8;
            padding: 0.1rem 0.4rem;
            border-radius: 3px;
            font-family: monospace;
            margin-right: 0.3rem;
        }}
        .footer {{
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.8rem;
            padding: 3rem 0;
            border-top: 1px solid var(--border);
            font-family: monospace;
        }}
        /* Presentation Mode Fullscreen Styling */
        body.presentation-mode {{
            font-size: 1.3rem;
        }}
        body.presentation-mode .container {{
            max-width: 1200px;
        }}
        body.presentation-mode .report-section {{
            min-height: 70vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 3rem;
            margin-bottom: 4rem;
        }}
        body.presentation-mode .section-title {{
            font-size: 2.2rem;
        }}
        @media print {{
            .controls {{ display: none; }}
            body {{ background: white; color: black; }}
            .report-section {{ border: 1px solid #ccc; page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-left">
            <h1>{safe_title}</h1>
            <div class="header-meta">REPORT ID: {html.escape(report.report_id)} | VERSION {report.version} | SHA-256: {manifest_hash[:16]}...</div>
        </div>
        <div class="controls">
            <button class="btn-presentation" onclick="togglePresentation()">Presentation Mode</button>
        </div>
    </header>

    <main class="container">
        <div class="map-card">
            {map_svg}
        </div>

        {''.join(sections_html)}
    </main>

    <footer class="footer">
        TRINETRA ANALYST WORKBENCH &bull; DETERMINISTIC CRYPTOGRAPHIC MANIFEST: {manifest_hash}
    </footer>

    <script>
        function togglePresentation() {{
            document.body.classList.toggle('presentation-mode');
            const btn = document.querySelector('.btn-presentation');
            btn.textContent = document.body.classList.contains('presentation-mode') ? 'Exit Presentation' : 'Presentation Mode';
        }}
    </script>
</body>
</html>"""
        return html_template
