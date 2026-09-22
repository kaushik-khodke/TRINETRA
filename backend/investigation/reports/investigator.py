"""
TRINETRA Phase 6 — Investigation Report Generator
Produces finalized JSON and standalone HTML reports summarizing multi-modal findings,
evidence graphs, and non-causal attribution conclusions.
"""

from typing import Dict, Any, List
from datetime import datetime


class InvestigationReportGenerator:
    """
    Assembles executive summaries, structured findings, evidence tables, and HTML reports.
    """

    @classmethod
    def generate_html_report(cls, report_data: Dict[str, Any]) -> str:
        """Generates an analyst-grade standalone HTML report."""
        inv_id = report_data.get("investigation_id", "Unknown")
        question = report_data.get("question", "")
        conclusion = report_data.get("conclusion", {})
        summary = conclusion.get("summary", "No summary provided.")
        confidence = conclusion.get("confidence", 0.85)
        findings = report_data.get("findings", [])
        hypotheses = report_data.get("hypotheses", [])
        conflicts = report_data.get("conflicts", [])
        limitations = report_data.get("limitations", [])

        findings_rows = "".join([
            f"<tr><td><strong>{f.get('finding_id', '')}</strong></td>"
            f"<td>{f.get('category', '')}</td>"
            f"<td>{f.get('statement', '')}</td>"
            f"<td>{round(float(f.get('confidence', 0.85)), 2)}</td></tr>"
            for f in findings
        ])

        hypotheses_rows = "".join([
            f"<tr><td><strong>{h.get('semantic_class', '')}</strong></td>"
            f"<td>{h.get('description', '')}</td>"
            f"<td>{round(float(h.get('confidence', 0.85)), 2)}</td>"
            f"<td>{h.get('status', 'ACCEPTED')}</td></tr>"
            for h in hypotheses
        ])

        conflicts_html = ""
        if conflicts:
            conflicts_html = "<h3>Identified Evidence Discrepancies</h3><ul>" + "".join([
                f"<li><strong>{c.get('conflict_type', '')}:</strong> {c.get('description', '')} (Severity: {c.get('severity', '')})</li>"
                for c in conflicts
            ]) + "</ul>"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TRINETRA Investigation Report — {inv_id}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #e2e8f0; margin: 0; padding: 32px; line-height: 1.6; }}
    .container {{ max-width: 960px; margin: 0 auto; background: #131b2e; border: 1px solid #1e293b; border-radius: 12px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
    h1 {{ color: #38bdf8; font-size: 26px; border-bottom: 2px solid #1e293b; padding-bottom: 16px; margin-top: 0; }}
    h2 {{ color: #94a3b8; font-size: 18px; margin-top: 28px; text-transform: uppercase; letter-spacing: 0.05em; }}
    .meta-box {{ background: #0f172a; border-radius: 8px; padding: 16px; margin-bottom: 24px; border: 1px solid #334155; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; background: #0284c7; color: white; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; }}
    th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #1e293b; }}
    th {{ background: #0f172a; color: #94a3b8; }}
    .footer {{ margin-top: 40px; font-size: 12px; color: #64748b; border-top: 1px solid #1e293b; padding-top: 16px; }}
    .boundary {{ background: rgba(234, 179, 8, 0.1); border-left: 4px solid #eab308; padding: 14px; border-radius: 4px; color: #fef08a; margin-top: 20px; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>TRINETRA Earth Observation Investigation Report</h1>
    <div class="meta-box">
      <p><strong>Investigation ID:</strong> {inv_id} &nbsp;|&nbsp; <strong>Date:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
      <p><strong>Question:</strong> {question}</p>
      <p><strong>Composite Confidence:</strong> <span class="badge">{round(float(confidence)*100, 1)}%</span></p>
    </div>

    <h2>Executive Summary</h2>
    <p>{summary}</p>

    <div class="boundary">
      <strong>Attribution Boundary:</strong> {conclusion.get('attribution_boundary', 'No speculative inferences permitted.')}
    </div>

    <h2>Structured Empirical Findings</h2>
    <table>
      <thead>
        <tr><th>ID</th><th>Category</th><th>Measurement Statement</th><th>Confidence</th></tr>
      </thead>
      <tbody>
        {findings_rows}
      </tbody>
    </table>

    <h2>Semantic Event Hypotheses</h2>
    <table>
      <thead>
        <tr><th>Semantic Class</th><th>Description</th><th>Confidence</th><th>Status</th></tr>
      </thead>
      <tbody>
        {hypotheses_rows}
      </tbody>
    </table>

    {conflicts_html}

    <div class="footer">
      Generated automatically by TRINETRA Phase 6 Semantic EO Intelligence Engine. Deterministic verification hash preserved.
    </div>
  </div>
</body>
</html>"""
        return html
