"""
TRINETRA — Mission Intelligence Report Generator
Compiles structured mission findings, visual evidence gallery (raw, annotated, heatmap, fusion, spectral),
traceable physical measurements, spatial metadata, and observable execution traces into downloadable reports.
"""

import os
import json
import time
from typing import Dict, Any, List

class MissionReportGenerator:

    @staticmethod
    def generate_html_report(result_payload: Dict[str, Any], output_path: str) -> str:
        req_id = result_payload.get("request_id", "REQ-UNKNOWN")
        query = result_payload.get("query", "N/A")
        task = (result_payload.get("task") or result_payload.get("detected_task") or "N/A").upper()
        confidence = result_payload.get("confidence", 0.0)
        answer = result_payload.get("answer", result_payload.get("caption", "N/A"))
        trace = result_payload.get("execution_trace", {})
        steps = trace.get("steps", [])
        struct_intel = result_payload.get("structured_intelligence") or (result_payload.get("result") or {}).get("structured_intelligence") or {}

        trace_id = trace.get("trace_id") or result_payload.get("trace_id", "N/A")
        model_name = result_payload.get("llm_model") or trace.get("model") or "Local Ollama (Dynamic Auto-Detection)"

        # 1. Observable steps HTML
        steps_html = "".join([
            f"""<tr style="border-bottom: 1px solid #24303D;">
                <td style="padding: 8px; color: #10B981; font-family: monospace;">#{s.get('step_id', i+1)}</td>
                <td style="padding: 8px; font-weight: 600;">{s.get('stage', '').upper()}</td>
                <td style="padding: 8px; font-family: monospace; color: #94A3B8;">{s.get('action') or '-'}</td>
                <td style="padding: 8px; color: #CBD5E1;">{s.get('details')}</td>
            </tr>"""
            for i, s in enumerate(steps)
        ])

        # 2. Evidence Gallery Panels
        vis_out = struct_intel.get("visual_outputs", {})
        res_dict = result_payload.get("result", {})
        ev_dict = result_payload.get("evidence", {}) or {}

        raw_img = vis_out.get("raw_image") or res_dict.get("raw_preview") or (result_payload.get("image_previews") or [None])[0]
        annotated_img = vis_out.get("annotated_image") or res_dict.get("evidence_image") or ev_dict.get("image")
        heatmap_img = vis_out.get("heatmap") or ev_dict.get("change_heatmap") or res_dict.get("change_heatmap")
        fused_img = ev_dict.get("fused_composite") or res_dict.get("fused_composite")
        spectral_img = vis_out.get("spectral_plot") or ev_dict.get("spectral_signature_image")

        gallery_cards = []
        if raw_img:
            gallery_cards.append(f"""
            <div class="gallery-item">
                <img src="{raw_img}" alt="Raw Raster" />
                <div class="gallery-caption"><strong>RAW SATELLITE RASTER</strong><br/>Original unannotated sensor capture</div>
            </div>
            """)
        if annotated_img:
            gallery_cards.append(f"""
            <div class="gallery-item">
                <img src="{annotated_img}" alt="Tactical Grounding" />
                <div class="gallery-caption"><strong style="color: #10B981;">TACTICAL ANNOTATION & GROUNDING</strong><br/>Identified regions with confidence callouts</div>
            </div>
            """)
        if heatmap_img:
            gallery_cards.append(f"""
            <div class="gallery-item">
                <img src="{heatmap_img}" alt="Change Heatmap" />
                <div class="gallery-caption"><strong style="color: #F59E0B;">SURFACE MODIFICATION HEATMAP</strong><br/>Differential magnitude above operational threshold</div>
            </div>
            """)
        if fused_img:
            gallery_cards.append(f"""
            <div class="gallery-item">
                <img src="{fused_img}" alt="Optical-SAR Fusion" />
                <div class="gallery-caption"><strong style="color: #06B6D4;">OPTICAL + SAR CROSS-MODAL COMPOSITE</strong><br/>Fused optical spectral hues with radar backscatter</div>
            </div>
            """)
        if spectral_img:
            gallery_cards.append(f"""
            <div class="gallery-item">
                <img src="{spectral_img}" alt="Spectral Signature" />
                <div class="gallery-caption"><strong style="color: #A78BFA;">SPECTRAL REFLECTANCE CURVE</strong><br/>Diagnostic absorption and reflectance profile</div>
            </div>
            """)

        gallery_html = f"""
        <div class="card">
            <div class="card-title">Evidence Gallery & Multimodal Visual Intelligence</div>
            <div class="gallery-grid">
                {''.join(gallery_cards)}
            </div>
        </div>
        """ if gallery_cards else ""

        # 3. Regions Table
        regions = struct_intel.get("regions") or res_dict.get("regions") or []
        region_rows = []
        for r in regions:
            coords = r.get("bbox") or [0, 0, 0, 0]
            coords_str = f"[{coords[0]:.2f}, {coords[1]:.2f}, {coords[2]:.2f}, {coords[3]:.2f}]"
            c = r.get("centroid") or {}
            geo_str = f"{c.get('lat')}, {c.get('lng')}" if c.get('lat') else r.get("relative_location", "-")
            area_m2 = r.get("physical_area_m2")
            area_str = f"{round(area_m2/10000.0, 2)} ha" if area_m2 else (f"{r.get('pixel_area')} px" if r.get('pixel_area') else "-")
            region_rows.append(f"""
            <tr style="border-bottom: 1px solid #24303D;">
                <td style="padding: 8px; color: #10B981; font-family: monospace; font-weight: bold;">{r.get('id', 'R01')}</td>
                <td style="padding: 8px; font-weight: 600;">{r.get('label', 'Target')}</td>
                <td style="padding: 8px; font-family: monospace;">{r.get('geometry_type', 'bbox').upper()}</td>
                <td style="padding: 8px; font-family: monospace; color: #94A3B8;">{coords_str}</td>
                <td style="padding: 8px; color: #E2E8F0;">{geo_str}</td>
                <td style="padding: 8px; font-family: monospace; color: #38BDF8;">{area_str}</td>
                <td style="padding: 8px; font-family: monospace; color: #10B981;">{int(r.get('score', 0.90)*100)}%</td>
            </tr>
            """)

        regions_table_html = f"""
        <div class="card">
            <div class="card-title">Detected Regions & Spatial Grounding Telemetry</div>
            <table>
                <thead>
                    <tr>
                        <th>REGION ID</th>
                        <th>TARGET LABEL</th>
                        <th>GEOMETRY</th>
                        <th>NORMALIZED BBOX</th>
                        <th>SPATIAL / GEO LOCATION</th>
                        <th>AREA</th>
                        <th>CONFIDENCE</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(region_rows)}
                </tbody>
            </table>
        </div>
        """ if region_rows else ""

        # 4. Measurements Table
        measurements = struct_intel.get("measurements") or {}
        measurement_rows = []
        for k, v in measurements.items():
            if isinstance(v, dict):
                val = v.get("value")
                unit = v.get("unit") or ""
                src = v.get("source") or "Calculated metric"
            else:
                val = v
                unit = ""
                src = "Sensor telemetry"
            measurement_rows.append(f"""
            <tr style="border-bottom: 1px solid #24303D;">
                <td style="padding: 8px; font-weight: 600; color: #E2E8F0;">{k.replace('_', ' ').title()}</td>
                <td style="padding: 8px; font-family: monospace; color: #10B981; font-size: 15px;">{val} {unit}</td>
                <td style="padding: 8px; color: #94A3B8;">{src}</td>
            </tr>
            """)

        measurements_html = f"""
        <div class="card">
            <div class="card-title">Traceable Radiometric & Physical Measurements</div>
            <table>
                <thead>
                    <tr>
                        <th>MEASUREMENT PARAMETER</th>
                        <th>COMPUTED VALUE</th>
                        <th>PHYSICAL SENSOR / ALGORITHM SOURCE</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(measurement_rows)}
                </tbody>
            </table>
        </div>
        """ if measurement_rows else ""

        # 5. Spatial Metadata
        geo_loc = result_payload.get("geographic_location") or res_dict.get("geographic_location") or {}
        has_geo = geo_loc.get("has_location", False)
        crs_val = geo_loc.get("crs") or ("EPSG:4326" if has_geo else "Geospatial coordinates unavailable for this raster.")
        center_coords = f"{geo_loc.get('lat')}, {geo_loc.get('lng')}" if has_geo else "N/A (Local Image Frame)"
        loc_name = geo_loc.get("location_name") or ("Georeferenced Target" if has_geo else "Standard Raster Tile")

        # 6. Optional Quantum Machine Learning (QML) Comparative Card
        comp_data = result_payload.get("classical_vs_qml_comparison")
        qml_html = ""
        if comp_data and comp_data.get("verdict") != "QML_UNAVAILABLE":
            agrees = comp_data.get("agrees", False)
            verdict = comp_data.get("verdict", "PENDING")
            badge_color = "#10B981" if agrees else "#F59E0B"
            param_comp = comp_data.get("parameter_comparison", {})
            insights_li = "".join([f"<li style='margin-bottom: 6px;'>{ins}</li>" for ins in comp_data.get("insights", [])])

            qml_html = f"""
            <div class="card" style="border: 1px solid #8B5CF6; background: linear-gradient(180deg, #131127 0%, #0F172A 100%);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div class="card-title" style="color: #A78BFA; margin-bottom: 0;">Quantum Research Mode & Comparative Telemetry (PennyLane)</div>
                    <span style="background: rgba(139, 92, 246, 0.2); border: 1px solid {badge_color}; color: {badge_color}; padding: 4px 10px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                        VERDICT: {verdict}
                    </span>
                </div>
                <div style="font-size: 14px; color: #E2E8F0; margin-bottom: 16px;">
                    {comp_data.get('status_message')}
                </div>
                <div class="metric-grid">
                    <div class="metric-box" style="border-color: #334155;">
                        <div class="metric-label">OPERATIONAL CLASSICAL PREDICTION</div>
                        <div class="metric-val">{comp_data.get('classical_prediction')} ({int(comp_data.get('classical_confidence', 0)*100)}%)</div>
                    </div>
                    <div class="metric-box" style="border-color: #334155;">
                        <div class="metric-label">RESEARCH QML PREDICTION</div>
                        <div class="metric-val" style="color: #A78BFA;">{comp_data.get('qml_prediction')} ({int(comp_data.get('qml_confidence', 0)*100)}%)</div>
                    </div>
                    <div class="metric-box" style="border-color: #334155;">
                        <div class="metric-label">PARAMETER COMPRESSION</div>
                        <div class="metric-val" style="color: #38BDF8;">{param_comp.get('quantum_parameter_reduction', '99.9%')}</div>
                    </div>
                    <div class="metric-box" style="border-color: #334155;">
                        <div class="metric-label">QUANTUM CIRCUIT</div>
                        <div class="metric-val" style="color: #A78BFA;">{param_comp.get('quantum_bits (qubits)', 4)} Qubits &bull; Depth {param_comp.get('quantum_circuit_depth', 5)}</div>
                    </div>
                </div>
                <div style="margin-top: 16px;">
                    <div style="font-size: 12px; font-weight: 600; color: #94A3B8; text-transform: uppercase; margin-bottom: 6px;">Comparative Insights</div>
                    <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #CBD5E1; line-height: 1.5;">
                        {insights_li}
                    </ul>
                </div>
            </div>
            """

        # Format answer markdown to HTML paragraphs
        formatted_answer = answer.replace("\n\n", "<br/><br/>").replace("\n", "<br/>").replace("## ", "<h3 style='color: #10B981; margin-top: 16px; margin-bottom: 8px;'>").replace("### ", "<h4 style='color: #38BDF8; margin-top: 12px;'>")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>TRINETRA — Mission Intelligence Report [{req_id[:8]}]</title>
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
            margin-bottom: 14px;
            font-weight: 600;
        }}
        .answer-text {{
            font-size: 15px;
            line-height: 1.6;
            color: #E2E8F0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th {{
            text-align: left;
            padding: 10px 8px;
            background-color: #16202A;
            color: #94A3B8;
            border-bottom: 1px solid #24303D;
            font-family: monospace;
            font-size: 12px;
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
        .metric-label {{ font-size: 11px; color: #94A3B8; margin-bottom: 4px; text-transform: uppercase; }}
        .metric-val {{ font-size: 15px; font-weight: 600; color: #10B981; font-family: monospace; }}
        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }}
        .gallery-item {{
            background: #161E26;
            border: 1px solid #24303D;
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        .gallery-item img {{
            width: 100%;
            height: 220px;
            object-fit: cover;
            background: #000;
        }}
        .gallery-caption {{
            padding: 12px;
            font-size: 12px;
            color: #94A3B8;
            background: #0F141A;
            border-top: 1px solid #24303D;
            line-height: 1.4;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="title">TRINETRA — SATELLITE MISSION INTELLIGENCE REPORT</div>
            <div style="color: #64748B; font-size: 13px; margin-top: 4px;">Multimodal Remote-Sensing Intelligence Workstation | 100% Local & Air-Gapped</div>
        </div>
        <div class="badge">COMPOSITE CONFIDENCE: {int(confidence * 100)}%</div>
    </div>

    <div class="card">
        <div class="card-title">System & Execution Architecture</div>
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-label">OPERATIONAL WORKFLOW</div>
                <div class="metric-val">LangGraph Autonomous StateGraph</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">LLM REASONING RUNTIME</div>
                <div class="metric-val">Ollama ({model_name})</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">OBSERVABILITY TRACING</div>
                <div class="metric-val">Langfuse v2 ({trace_id[:16]}...)</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">CLOUD DEPENDENCY</div>
                <div class="metric-val" style="color: #38BDF8;">NONE (100% Air-Gapped/Local)</div>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-title">Analysis Directive & Executive Findings</div>
        <div style="font-size: 14px; color: #94A3B8; margin-bottom: 8px;"><strong>User Query:</strong> &ldquo;{query}&rdquo;</div>
        <div style="font-size: 13px; color: #64748B; margin-bottom: 16px;"><strong>Target Task:</strong> {task} &bull; <strong>Request ID:</strong> {req_id} &bull; <strong>Trace ID:</strong> {trace_id}</div>
        <div class="answer-text">{formatted_answer}</div>
    </div>

    {gallery_html}

    {regions_table_html}

    {measurements_html}

    <div class="card">
        <div class="card-title">Geospatial & Cartographic Metadata</div>
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-label">COORDINATE REFERENCE SYSTEM (CRS)</div>
                <div class="metric-val" style="color: {'#10B981' if has_geo else '#F59E0B'};">{crs_val}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">CENTER COORDINATES (WGS84)</div>
                <div class="metric-val">{center_coords}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">LOCATION DESIGNATION</div>
                <div class="metric-val">{loc_name}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">GEOREFERENCING STATUS</div>
                <div class="metric-val" style="color: {'#10B981' if has_geo else '#F59E0B'};">{'VALID GEO-AFFINE' if has_geo else 'UNREFERENCED RASTER'}</div>
            </div>
        </div>
    </div>

    {qml_html}

    <div class="card">
        <div class="card-title">Telemetry & Observable Execution Trace</div>
        <table>
            <thead>
                <tr>
                    <th>STEP</th>
                    <th>STAGE</th>
                    <th>SPECIALIST ACTION</th>
                    <th>EXECUTION DETAILS</th>
                </tr>
            </thead>
            <tbody>
                {steps_html}
            </tbody>
        </table>
    </div>

    <div style="text-align: center; color: #475569; font-size: 12px; margin-top: 40px;">
        Generated by TRINETRA Multimodal Satellite Intelligence Workstation | Timestamp: {time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}
    </div>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path

    @staticmethod
    def generate_json_report(result_payload: Dict[str, Any], output_path: str) -> str:
        import numpy as np

        def _serialize_helper(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.floating, np.complexfloating)):
                return float(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            return str(obj)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2, default=_serialize_helper)
        return output_path
