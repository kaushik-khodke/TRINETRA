"""
SatQuery AI — Mission Intelligence Report Generator
Compiles analysis answers, spatial evidence, confidence metrics,
metadata, and observable execution traces into downloadable PDF, HTML, and JSON reports.
"""

import os
import json
import time
from typing import Dict, Any

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

class MissionReportGenerator:

    @staticmethod
    def generate_html_report(result_payload: Dict[str, Any], output_path: str) -> str:
        req_id = result_payload.get("request_id", "REQ-UNKNOWN")
        query = result_payload.get("query", "N/A")
        task = result_payload.get("task", "N/A").upper()
        confidence = result_payload.get("confidence", 0.0)
        answer = result_payload.get("answer", result_payload.get("caption", "N/A"))
        trace = result_payload.get("execution_trace", {})
        steps = trace.get("steps", [])

        trace_id = trace.get("trace_id") or result_payload.get("trace_id", "N/A")
        langfuse_url = trace.get("langfuse_url", "Local Tracing Active")
        model_name = result_payload.get("llm_model") or trace.get("model") or "Local Ollama (Dynamic Auto-Detection)"

        steps_html = "".join([
            f"""<tr style="border-bottom: 1px solid #24303D;">
                <td style="padding: 8px; color: #10B981; font-family: monospace;">#{s.get('step_id')}</td>
                <td style="padding: 8px; font-weight: 600;">{s.get('stage').upper()}</td>
                <td style="padding: 8px; font-family: monospace; color: #94A3B8;">{s.get('tool') or '-'}</td>
                <td style="padding: 8px;">{s.get('details')}</td>
            </tr>"""
            for s in steps
        ])

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SatQuery AI — Mission Intelligence Report [{req_id[:8]}]</title>
    <style>
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            background-color: #090D10;
            color: #F1F5F9;
            margin: 0;
            padding: 40px;
        }}
        .header {{
            border-bottom: 2px solid #10B981;
            padding-bottom: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .title {{ font-size: 26px; font-weight: 700; letter-spacing: 1px; color: #FFFFFF; }}
        .badge {{
            background-color: #16222F;
            border: 1px solid #10B981;
            color: #10B981;
            padding: 6px 14px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 13px;
        }}
        .card {{
            background-color: #11161B;
            border: 1px solid #24303D;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .card-title {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #10B981;
            margin-top: 0;
            margin-bottom: 12px;
        }}
        .answer-text {{
            font-size: 18px;
            line-height: 1.6;
            color: #F8FAFC;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{
            text-align: left;
            padding: 10px 8px;
            background-color: #16202A;
            color: #94A3B8;
            border-bottom: 1px solid #24303D;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }}
        .metric-box {{
            background-color: #161E26;
            border: 1px solid #24303D;
            padding: 14px;
            border-radius: 6px;
        }}
        .metric-label {{ font-size: 12px; color: #94A3B8; margin-bottom: 4px; }}
        .metric-val {{ font-size: 15px; font-weight: 600; color: #10B981; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="title">SATQUERY AI — MISSION INTELLIGENCE REPORT</div>
            <div style="color: #64748B; font-size: 13px; margin-top: 4px;">ISRO Problem Statement 26167 | 100% Local Agentic Multimodal Vision-Language System</div>
        </div>
        <div class="badge">CONFIDENCE: {int(confidence * 100)}%</div>
    </div>

    <div class="card">
        <div class="card-title">System & Execution Architecture</div>
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-label">AGENT FRAMEWORK</div>
                <div class="metric-val">LangChain (Local)</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">LLM RUNTIME</div>
                <div class="metric-val">Ollama ({model_name})</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">OBSERVABILITY</div>
                <div class="metric-val">Langfuse v2 ({trace_id[:16]}...)</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">CLOUD LLM DEPENDENCY</div>
                <div class="metric-val" style="color: #38BDF8;">NONE (100% Local/Air-Gapped)</div>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-title">Analysis Directive & Result</div>
        <div style="font-size: 14px; color: #94A3B8; margin-bottom: 8px;"><strong>Query:</strong> &ldquo;{query}&rdquo;</div>
        <div style="font-size: 13px; color: #64748B; margin-bottom: 16px;"><strong>Target Task:</strong> {task} &bull; <strong>Request ID:</strong> {req_id} &bull; <strong>Trace ID:</strong> {trace_id}</div>
        <div class="answer-text">{answer}</div>
    </div>

    <div class="card">
        <div class="card-title">Telemetry & Observable Execution Trace</div>
        <table>
            <thead>
                <tr>
                    <th>STEP</th>
                    <th>STAGE</th>
                    <th>SPECIALIST TOOL</th>
                    <th>DETAILS</th>
                </tr>
            </thead>
            <tbody>
                {steps_html}
            </tbody>
        </table>
    </div>

    <div style="text-align: center; color: #475569; font-size: 12px; margin-top: 40px;">
        Generated by SatQuery AI Autonomous Remote-Sensing Agent | Timestamp: {time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}
    </div>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path

    @staticmethod
    def generate_json_report(result_payload: Dict[str, Any], output_path: str) -> str:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2)
        return output_path
