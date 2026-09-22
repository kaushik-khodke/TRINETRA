"""
TRINETRA Phase 8 — Standalone Map Snapshot Generator
Renders deterministic vector SVG / GeoJSON map visual previews without browser dependencies.
"""

from typing import Dict, Any, List, Optional


class MapSnapshotGenerator:
    """
    Renders standalone SVG map previews of Area of Interest (AOI) polygons and finding overlays.
    """

    @classmethod
    def generate_svg_snapshot(
        cls,
        aoi_geojson: Optional[Dict[str, Any]] = None,
        findings: Optional[List[Dict[str, Any]]] = None,
        width: int = 800,
        height: int = 500,
        title: str = "Area of Interest Overview",
    ) -> str:
        """
        Produces clean, standalone SVG vector map markup.
        """
        # Default bounding box if no coordinates provided
        min_x, max_x = 77.0, 77.5
        min_y, max_y = 28.3, 28.8

        coords = []
        if aoi_geojson and "coordinates" in aoi_geojson:
            poly = aoi_geojson["coordinates"]
            if poly and len(poly) > 0 and isinstance(poly[0], list):
                ring = poly[0]
                coords = [(pt[0], pt[1]) for pt in ring if len(pt) >= 2]
                if coords:
                    min_x = min(c[0] for c in coords)
                    max_x = max(c[0] for c in coords)
                    min_y = min(c[1] for c in coords)
                    max_y = max(c[1] for c in coords)

        # Coordinate transformation to SVG viewport
        pad = 60
        span_x = max(1e-5, max_x - min_x)
        span_y = max(1e-5, max_y - min_y)

        def to_svg(x: float, y: float):
            sx = pad + ((x - min_x) / span_x) * (width - 2 * pad)
            sy = height - pad - ((y - min_y) / span_y) * (height - 2 * pad)
            return sx, sy

        poly_points = ""
        if coords:
            svg_pts = [f"{to_svg(x, y)[0]:.1f},{to_svg(x, y)[1]:.1f}" for x, y in coords]
            poly_points = " ".join(svg_pts)
        else:
            p1 = to_svg(min_x + 0.1 * span_x, min_y + 0.1 * span_y)
            p2 = to_svg(max_x - 0.1 * span_x, min_y + 0.1 * span_y)
            p3 = to_svg(max_x - 0.1 * span_x, max_y - 0.1 * span_y)
            p4 = to_svg(min_x + 0.1 * span_x, max_y - 0.1 * span_y)
            poly_points = f"{p1[0]},{p1[1]} {p2[0]},{p2[1]} {p3[0]},{p3[1]} {p4[0]},{p4[1]}"

        # Marker points for findings
        finding_markers = []
        if findings:
            for idx, f in enumerate(findings):
                fx = min_x + 0.2 * span_x + (idx * 0.15 * span_x) % span_x
                fy = min_y + 0.2 * span_y + (idx * 0.2 * span_y) % span_y
                px, py = to_svg(fx, fy)
                finding_markers.append(
                    f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="#ef4444" stroke="#ffffff" stroke-width="2"/>'
                    f'<text x="{px + 10:.1f}" y="{py + 4:.1f}" fill="#f87171" font-size="11" font-family="monospace">'
                    f'{f.get("finding_id", f"F-{idx+1}")}</text>'
                )

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background-color: #0b1120; border-radius: 8px;">
  <!-- Grid -->
  <defs>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#grid)" />

  <!-- Header -->
  <text x="30" y="36" fill="#38bdf8" font-size="16" font-weight="bold" font-family="system-ui, sans-serif">{title}</text>
  <text x="30" y="54" fill="#94a3b8" font-size="11" font-family="monospace">BBOX: [{min_x:.3f}, {min_y:.3f}] to [{max_x:.3f}, {max_y:.3f}]</text>

  <!-- AOI Polygon -->
  <polygon points="{poly_points}" fill="rgba(56, 189, 248, 0.15)" stroke="#38bdf8" stroke-width="2.5" stroke-dasharray="6,3" />

  <!-- Findings -->
  {''.join(finding_markers)}

  <!-- Legend & Scale -->
  <rect x="{width - 190}" y="{height - 50}" width="170" height="35" rx="4" fill="rgba(15, 23, 42, 0.85)" stroke="#334155" />
  <line x1="{width - 180}" y1="{height - 32}" x2="{width - 130}" y2="{height - 32}" stroke="#38bdf8" stroke-width="3" />
  <text x="{width - 120}" y="{height - 28}" fill="#cbd5e1" font-size="10" font-family="sans-serif">5.0 km Scale</text>
</svg>"""
        return svg
