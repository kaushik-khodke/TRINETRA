/**
 * TRINETRA Phase 6 — Deep Research & Earth Observation Intelligence Dossier
 * Comprehensive technical reporting system featuring:
 * 1. Interactive Satellite Image Inspection Modal (Zoom in/out, pan, layer switch, crosshair alignment).
 * 2. Dedicated publication-grade Print / PDF export engine (A4 multi-page formatted, zero clipping).
 * 3. Dual-pass Copernicus Sentinel-2 satellite comparison (T₀ vs T₁) with interactive wipe slider & side-by-side mode.
 * 4. High-resolution optical contextual imagery (Esri World Imagery / Maxar).
 * 5. Dynamic query-tailored SVG charts (Biophysical Differencing, Zonal Partitioning, Temporal Progression).
 * 6. Plain-English yet scientifically rigorous 7-section intelligence dossier.
 */

import React, { useState, useRef, useEffect, useCallback } from "react"
import {
  DeepAnalysisData,
  DeepAnalysisChart,
  DeepAnalysisDossierSection,
} from "@/lib/explore/investigation-types"
import {
  Microscope,
  Layers,
  Calendar,
  Compass,
  Maximize2,
  Minimize2,
  Printer,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Sliders,
  Columns,
  Eye,
  ShieldAlert,
  BarChart3,
  PieChart,
  TrendingUp,
  MapPin,
  ExternalLink,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Crosshair,
  Download,
  X,
  Move,
} from "lucide-react"

interface Props {
  data: DeepAnalysisData
  query: string
}

export const DeepResearchReport: React.FC<Props> = ({ data, query }) => {
  const [viewMode, setViewMode] = useState<"side_by_side" | "slider" | "high_res">("side_by_side")
  const [sliderPosition, setSliderPosition] = useState<number>(50)
  const [isDraggingSlider, setIsDraggingSlider] = useState<boolean>(false)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    executive_summary: true,
    satellite_acquisition: true,
    biophysical_analysis: true,
    radar_scatter: true,
    spatial_zonation: true,
    temporal_trajectory: true,
    uncertainty_boundary: true,
  })
  const [copied, setCopied] = useState<boolean>(false)

  // Interactive Inspection Modal State
  const [inspectModalOpen, setInspectModalOpen] = useState<boolean>(false)
  const [inspectLayer, setInspectLayer] = useState<"t0" | "t1" | "high_res" | "compare">("t0")
  const [zoomLevel, setZoomLevel] = useState<number>(1)
  const [panOffset, setPanOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState<boolean>(false)
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [showGrid, setShowGrid] = useState<boolean>(false)
  const [modalSliderPos, setModalSliderPos] = useState<number>(50)

  const sliderContainerRef = useRef<HTMLDivElement>(null)
  const modalSliderRef = useRef<HTMLDivElement>(null)

  const { target_sector, imagery_comparison, dynamic_charts, technical_dossier_sections } = data
  const t0 = imagery_comparison.baseline_t0
  const t1 = imagery_comparison.monitoring_t1
  const highRes = imagery_comparison.high_resolution_context

  // Close inspection modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && inspectModalOpen) {
        setInspectModalOpen(false)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [inspectModalOpen])

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => ({ ...prev, [sectionId]: !prev[sectionId] }))
  }

  const toggleAllSections = (expand: boolean) => {
    const updated: Record<string, boolean> = {}
    technical_dossier_sections.forEach((s) => {
      updated[s.section_id] = expand
    })
    setExpandedSections(updated)
  }

  const handleCopyReport = () => {
    const header = `=== ${data.dossier_title} ===\nTarget Sector: ${target_sector.label} (${target_sector.centroid.lat}, ${target_sector.centroid.lon})\nArea: ${target_sector.area_hectares} ha (${target_sector.area_sq_km} sq km)\nGenerated: ${data.generated_at}\n\n`
    const body = technical_dossier_sections
      .map((s) => `## ${s.title}\n${s.content}\n`)
      .join("\n")
    navigator.clipboard.writeText(header + body)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Publication-grade Dedicated Print / PDF Window Generator
  const handlePrint = () => {
    const printWindow = window.open("", "_blank", "width=1050,height=920")
    if (!printWindow) {
      window.print()
      return
    }

    const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>${data.dossier_title}</title>
  <style>
    @page {
      size: A4 portrait;
      margin: 14mm 14mm 16mm 14mm;
    }
    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #0f172a;
      background: #ffffff;
      margin: 0;
      padding: 0;
      font-size: 10pt;
      line-height: 1.5;
    }
    .header-banner {
      border-bottom: 2px solid #0284c7;
      padding-bottom: 10px;
      margin-bottom: 14px;
    }
    .badge {
      display: inline-block;
      background: #0284c7;
      color: #ffffff;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 8pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    h1 {
      font-size: 14pt;
      font-weight: 800;
      margin: 6px 0 4px 0;
      color: #0f172a;
    }
    .meta-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 8px 12px;
      margin-bottom: 16px;
      font-size: 8.5pt;
    }
    .meta-item label {
      display: block;
      color: #64748b;
      font-weight: 600;
      font-size: 7.5pt;
      text-transform: uppercase;
    }
    .meta-item strong {
      color: #0f172a;
      font-size: 9pt;
    }
    .section-header {
      font-size: 11pt;
      font-weight: 700;
      color: #0284c7;
      border-bottom: 1.5px solid #e2e8f0;
      padding-bottom: 4px;
      margin: 16px 0 10px 0;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .image-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 16px;
      page-break-inside: avoid;
    }
    .image-box {
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      overflow: hidden;
      background: #f8fafc;
    }
    .image-box img {
      width: 100%;
      height: 210px;
      object-fit: cover;
      display: block;
    }
    .image-info {
      padding: 8px 10px;
      font-size: 8.5pt;
      background: #f1f5f9;
      border-top: 1px solid #e2e8f0;
    }
    .image-info strong {
      display: block;
      font-size: 9.5pt;
      color: #0f172a;
      margin-bottom: 2px;
    }
    .dossier-section {
      margin-bottom: 14px;
      page-break-inside: avoid;
    }
    .dossier-title {
      font-size: 10.5pt;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 4px;
    }
    .dossier-content {
      font-size: 9.5pt;
      color: #334155;
      line-height: 1.55;
      white-space: pre-line;
    }
    .governance-alert {
      background: #fef3c7;
      border-left: 4px solid #f59e0b;
      padding: 8px 12px;
      font-size: 9pt;
      color: #78350f;
      border-radius: 4px;
      margin: 12px 0;
      page-break-inside: avoid;
    }
    .footer {
      border-top: 1px solid #e2e8f0;
      margin-top: 20px;
      padding-top: 8px;
      text-align: center;
      font-size: 8pt;
      color: #94a3b8;
    }
  </style>
</head>
<body>
  <div class="header-banner">
    <span class="badge">TRINETRA Scientific Earth-Observation Intelligence Dossier</span>
    <h1>${data.dossier_title}</h1>
    <div style="font-size: 8.5pt; color: #64748b;">
      Generated: ${new Date(data.generated_at).toLocaleString()} • Sensor: Copernicus Sentinel-2 MSI & Sentinel-1 SAR
    </div>
  </div>

  <div class="meta-grid">
    <div class="meta-item">
      <label>Target Sector</label>
      <strong>${target_sector.label}</strong>
    </div>
    <div class="meta-item">
      <label>Centroid Coordinates</label>
      <strong>${target_sector.centroid.lat.toFixed(5)}°N, ${target_sector.centroid.lon.toFixed(5)}°E</strong>
    </div>
    <div class="meta-item">
      <label>Analyzed Envelope</label>
      <strong>${target_sector.area_hectares} ha (${target_sector.area_sq_km} km²)</strong>
    </div>
    <div class="meta-item">
      <label>Satellite Tile</label>
      <strong>Zoom 16 [X:${target_sector.tile_coords_z16.x}, Y:${target_sector.tile_coords_z16.y}]</strong>
    </div>
  </div>

  <div class="section-header">Dual-Pass Satellite Image Comparison (T₀ Baseline vs T₁ Monitoring)</div>
  <div class="image-grid">
    <div class="image-box">
      <img src="${t0.tile_url}" alt="Sentinel-2 T0 Baseline" />
      <div class="image-info">
        <strong>${t0.layer_name}</strong>
        <div>Sensor: ${t0.satellite} • Resolution: ${t0.resolution} • Cloud: ${t0.cloud_cover_percent}%</div>
        <div style="color: #64748b; font-size: 8pt; margin-top: 2px;">${t0.description}</div>
      </div>
    </div>
    <div class="image-box">
      <img src="${t1.tile_url}" alt="Sentinel-2 T1 Monitoring" />
      <div class="image-info">
        <strong>${t1.layer_name}</strong>
        <div>Sensor: ${t1.satellite} • Resolution: ${t1.resolution} • Cloud: ${t1.cloud_cover_percent}%</div>
        <div style="color: #64748b; font-size: 8pt; margin-top: 2px;">${t1.description}</div>
      </div>
    </div>
  </div>

  <div class="section-header">Technical Intelligence Dossier & Scientific Evaluation</div>
  ${technical_dossier_sections
    .map(
      (s) => `
    <div class="dossier-section ${s.section_id === "uncertainty_boundary" ? "governance-alert" : ""}">
      <div class="dossier-title">${s.title}</div>
      <div class="dossier-content">${s.content}</div>
    </div>
  `
    )
    .join("")}

  <div class="footer">
    TRINETRA Controlled Geospatial Intelligence System • Confidential Technical Analyst Dossier • Certified Authentic Earth Observation Data
  </div>
</body>
</html>
    `

    printWindow.document.open()
    printWindow.document.write(htmlContent)
    printWindow.document.close()
    printWindow.focus()
    setTimeout(() => {
      printWindow.print()
    }, 450)
  }

  // Open Inspection Modal Handler
  const openInspector = (layer: "t0" | "t1" | "high_res" | "compare") => {
    setInspectLayer(layer)
    setZoomLevel(1)
    setPanOffset({ x: 0, y: 0 })
    setInspectModalOpen(true)
  }

  // Inspection Canvas Drag & Pan Handlers
  const handleInspectMouseDown = (e: React.MouseEvent) => {
    setIsPanning(true)
    setDragStart({ x: e.clientX - panOffset.x, y: e.clientY - panOffset.y })
  }

  const handleInspectMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return
    setPanOffset({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    })
  }

  const handleInspectMouseUp = () => {
    setIsPanning(false)
  }

  const handleInspectWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    const zoomDelta = e.deltaY < 0 ? 0.2 : -0.2
    setZoomLevel((prev) => Math.min(4.5, Math.max(0.75, prev + zoomDelta)))
  }

  // Split-slider drag handlers for inline view
  const handleSliderMove = (clientX: number) => {
    if (!sliderContainerRef.current) return
    const rect = sliderContainerRef.current.getBoundingClientRect()
    const pos = ((clientX - rect.left) / rect.width) * 100
    setSliderPosition(Math.max(0, Math.min(100, pos)))
  }

  // Modal slider drag handlers
  const handleModalSliderMove = (clientX: number) => {
    if (!modalSliderRef.current) return
    const rect = modalSliderRef.current.getBoundingClientRect()
    const pos = ((clientX - rect.left) / rect.width) * 100
    setModalSliderPos(Math.max(0, Math.min(100, pos)))
  }

  // Active layer metadata for inspector
  const activeInspectItem =
    inspectLayer === "t0" ? t0 : inspectLayer === "t1" ? t1 : highRes

  return (
    <div className="space-y-5 text-slate-100 font-sans print:bg-white print:text-black">
      {/* Dossier Header */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 border border-slate-800 rounded-xl p-4 shadow-lg print:border-none print:shadow-none">
        <div className="flex flex-wrap items-start justify-between gap-3 pb-3 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-950 border border-cyan-700 text-cyan-300 font-bold uppercase tracking-wider">
                <Microscope className="w-3 h-3 text-cyan-400" />
                Deep Research Intelligence Dossier
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                {new Date(data.generated_at).toLocaleString()}
              </span>
            </div>
            <h1 className="text-base font-bold text-slate-100 font-mono tracking-tight">
              {data.dossier_title}
            </h1>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 print:hidden">
            <button
              onClick={handleCopyReport}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-200 border border-slate-700 transition-colors"
              title="Copy dossier text"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400 font-semibold">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  <span>Copy Text</span>
                </>
              )}
            </button>
            <button
              onClick={handlePrint}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-indigo-900/60 hover:bg-indigo-800 text-xs font-mono text-indigo-200 border border-indigo-700/80 transition-colors shadow-sm"
              title="Print publication-ready full document or save as PDF"
            >
              <Printer className="w-3.5 h-3.5 text-indigo-300" />
              <span>Print / Save PDF</span>
            </button>
          </div>
        </div>

        {/* Spatial Target Sector Metadata Card */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 mt-3 pt-1 text-xs font-mono">
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80">
            <span className="text-[10px] text-slate-400 block mb-0.5">ADMINISTRATIVE SECTOR</span>
            <span className="font-semibold text-slate-200 text-[11px] truncate block" title={target_sector.label}>
              {target_sector.label}
            </span>
          </div>
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80">
            <span className="text-[10px] text-slate-400 block mb-0.5">CENTROID COORDINATES</span>
            <span className="font-semibold text-orange-400 text-[11px]">
              {target_sector.centroid.lat.toFixed(5)}°N, {target_sector.centroid.lon.toFixed(5)}°E
            </span>
          </div>
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80">
            <span className="text-[10px] text-slate-400 block mb-0.5">TOTAL FOOTPRINT AREA</span>
            <span className="font-semibold text-cyan-300 text-[11px]">
              {target_sector.area_hectares} ha ({target_sector.area_sq_km} km²)
            </span>
          </div>
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80">
            <span className="text-[10px] text-slate-400 block mb-0.5">SATELLITE TILE (Z16)</span>
            <span className="font-semibold text-slate-300 text-[11px]">
              X:{target_sector.tile_coords_z16.x} Y:{target_sector.tile_coords_z16.y}
            </span>
          </div>
        </div>
      </div>

      {/* DUAL-PASS SATELLITE IMAGERY COMPARISON */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h2 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
              Copernicus Sentinel-2 Dual-Pass Multi-Spectral Comparison
            </h2>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-md border border-slate-800 text-[11px] font-mono">
            <button
              onClick={() => setViewMode("side_by_side")}
              className={`flex items-center gap-1 px-2 py-0.5 rounded transition-all ${
                viewMode === "side_by_side"
                  ? "bg-slate-800 text-cyan-300 font-bold border border-cyan-600/40"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Columns className="w-3 h-3" />
              <span>Side-by-Side</span>
            </button>
            <button
              onClick={() => setViewMode("slider")}
              className={`flex items-center gap-1 px-2 py-0.5 rounded transition-all ${
                viewMode === "slider"
                  ? "bg-slate-800 text-cyan-300 font-bold border border-cyan-600/40"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Sliders className="w-3 h-3" />
              <span>Split Slider</span>
            </button>
            <button
              onClick={() => setViewMode("high_res")}
              className={`flex items-center gap-1 px-2 py-0.5 rounded transition-all ${
                viewMode === "high_res"
                  ? "bg-slate-800 text-cyan-300 font-bold border border-cyan-600/40"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Eye className="w-3 h-3" />
              <span>Sub-Meter Optical</span>
            </button>
          </div>
        </div>

        {/* View 1: Side-by-Side View */}
        {viewMode === "side_by_side" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* T0 Baseline Card */}
            <div className="space-y-2 bg-slate-950/70 p-3 rounded-lg border border-slate-800/80">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-950/80 text-blue-300 border border-blue-800 font-bold">
                  INITIAL BASELINE (T₀)
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  {new Date(t0.timestamp).toLocaleDateString()}
                </span>
              </div>

              {/* Clickable Image Container */}
              <div
                onClick={() => openInspector("t0")}
                className="relative aspect-video rounded-md overflow-hidden border border-slate-800 bg-slate-950 group cursor-pointer"
                title="Click to inspect this image in full-screen zoom viewer"
              >
                <img
                  src={t0.tile_url}
                  alt="Sentinel-2 Baseline T0"
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  loading="lazy"
                />
                <div className="absolute top-2 left-2 bg-slate-950/80 backdrop-blur px-2 py-1 rounded text-[10px] font-mono text-slate-300 border border-slate-800">
                  {t0.satellite} • {t0.resolution}
                </div>
                <div className="absolute bottom-2 right-2 bg-slate-950/85 backdrop-blur px-2 py-0.5 rounded text-[9px] font-mono text-emerald-400 border border-emerald-900">
                  Cloud: {t0.cloud_cover_percent}%
                </div>

                {/* Hover overlay hint */}
                <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1.5 text-xs font-mono text-white font-bold backdrop-blur-[1px]">
                  <Maximize2 className="w-4 h-4 text-cyan-400" />
                  <span>Click to Inspect & Zoom</span>
                </div>
              </div>

              <div className="space-y-1 text-[11px]">
                <p className="font-semibold text-slate-200 font-mono text-xs">{t0.layer_name}</p>
                <p className="text-slate-400 text-[10px] leading-relaxed">{t0.description}</p>
                <div className="text-[9px] font-mono text-slate-500 pt-0.5">
                  Bands: {t0.optical_band_combination}
                </div>
              </div>
            </div>

            {/* T1 Monitoring Scene Card */}
            <div className="space-y-2 bg-slate-950/70 p-3 rounded-lg border border-slate-800/80">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-orange-950/80 text-orange-300 border border-orange-800 font-bold">
                  CURRENT OBSERVATION (T₁)
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  {new Date(t1.timestamp).toLocaleDateString()}
                </span>
              </div>

              {/* Clickable Image Container */}
              <div
                onClick={() => openInspector("t1")}
                className="relative aspect-video rounded-md overflow-hidden border border-slate-800 bg-slate-950 group cursor-pointer"
                title="Click to inspect this image in full-screen zoom viewer"
              >
                <img
                  src={t1.tile_url}
                  alt="Sentinel-2 Monitoring T1"
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  loading="lazy"
                />
                <div className="absolute top-2 left-2 bg-slate-950/80 backdrop-blur px-2 py-1 rounded text-[10px] font-mono text-slate-300 border border-slate-800">
                  {t1.satellite} • {t1.resolution}
                </div>
                <div className="absolute bottom-2 right-2 bg-slate-950/85 backdrop-blur px-2 py-0.5 rounded text-[9px] font-mono text-emerald-400 border border-emerald-900">
                  Cloud: {t1.cloud_cover_percent}%
                </div>

                {/* Hover overlay hint */}
                <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1.5 text-xs font-mono text-white font-bold backdrop-blur-[1px]">
                  <Maximize2 className="w-4 h-4 text-orange-400" />
                  <span>Click to Inspect & Zoom</span>
                </div>
              </div>

              <div className="space-y-1 text-[11px]">
                <p className="font-semibold text-slate-200 font-mono text-xs">{t1.layer_name}</p>
                <p className="text-slate-400 text-[10px] leading-relaxed">{t1.description}</p>
                <div className="text-[9px] font-mono text-slate-500 pt-0.5">
                  Bands: {t1.optical_band_combination}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* View 2: Split Slider View */}
        {viewMode === "slider" && (
          <div className="space-y-2">
            <div
              ref={sliderContainerRef}
              onMouseDown={() => setIsDraggingSlider(true)}
              onMouseUp={() => setIsDraggingSlider(false)}
              onMouseLeave={() => setIsDraggingSlider(false)}
              onMouseMove={(e) => isDraggingSlider && handleSliderMove(e.clientX)}
              onTouchMove={(e) => e.touches.length > 0 && handleSliderMove(e.touches[0].clientX)}
              className="relative aspect-video md:aspect-[21/9] w-full rounded-lg overflow-hidden border border-slate-800 cursor-ew-resize select-none bg-slate-950"
            >
              {/* Background: Monitoring T1 */}
              <img
                src={t1.tile_url}
                alt="Sentinel-2 T1"
                className="absolute inset-0 w-full h-full object-cover"
              />

              {/* Foreground: Baseline T0 clipped by slider position */}
              <div
                className="absolute inset-0 overflow-hidden"
                style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
              >
                <img
                  src={t0.tile_url}
                  alt="Sentinel-2 T0"
                  className="absolute inset-0 w-full h-full object-cover"
                />
                <div className="absolute top-3 left-3 bg-slate-950/90 backdrop-blur px-2.5 py-1 rounded text-xs font-mono text-blue-300 font-bold border border-blue-800 shadow">
                  T₀ Baseline ({new Date(t0.timestamp).getFullYear()})
                </div>
              </div>

              {/* T1 Label on right */}
              <div className="absolute top-3 right-3 bg-slate-950/90 backdrop-blur px-2.5 py-1 rounded text-xs font-mono text-orange-300 font-bold border border-orange-800 shadow">
                T₁ Monitoring ({new Date(t1.timestamp).getFullYear()})
              </div>

              {/* Divider Line & Drag Handle */}
              <div
                className="absolute top-0 bottom-0 w-1 bg-white shadow-2xl cursor-ew-resize"
                style={{ left: `${sliderPosition}%` }}
              >
                <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-slate-950/90 border-2 border-white flex items-center justify-center text-white shadow-lg">
                  <Sliders className="w-3.5 h-3.5 text-cyan-300" />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-1">
              <button
                onClick={() => openInspector("compare")}
                className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold"
              >
                <Maximize2 className="w-3.5 h-3.5" />
                <span>Open in Full-Screen Inspector</span>
              </button>
              <span>Position: {Math.round(sliderPosition)}%</span>
            </div>
          </div>
        )}

        {/* View 3: Sub-Meter Optical High-Resolution Context */}
        {viewMode === "high_res" && (
          <div className="space-y-2 bg-slate-950/70 p-3 rounded-lg border border-slate-800/80">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-950/80 text-purple-300 border border-purple-800 font-bold">
                SUB-METER COMMERCIAL OPTICAL (ESRI / MAXAR)
              </span>
              <span className="text-[10px] font-mono text-slate-400">{highRes.resolution}</span>
            </div>

            <div
              onClick={() => openInspector("high_res")}
              className="relative aspect-video rounded-md overflow-hidden border border-slate-800 bg-slate-950 cursor-pointer group"
              title="Click to inspect sub-meter optical scene"
            >
              <img
                src={highRes.tile_url}
                alt="Esri High-Resolution Optical"
                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                loading="lazy"
              />
              <div className="absolute bottom-2 left-2 bg-slate-950/85 backdrop-blur px-2.5 py-1 rounded text-[10px] font-mono text-slate-300 border border-slate-800">
                Provider: {highRes.provider}
              </div>
              <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1.5 text-xs font-mono text-white font-bold backdrop-blur-[1px]">
                <Maximize2 className="w-4 h-4 text-purple-400" />
                <span>Click to Inspect Sub-Meter Aerial Details</span>
              </div>
            </div>

            <p className="text-slate-300 text-xs leading-relaxed font-sans">{highRes.description}</p>
          </div>
        )}
      </div>

      {/* DYNAMIC QUERY-TAILORED QUANTITATIVE CHARTS */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-800/80">
          <BarChart3 className="w-4 h-4 text-orange-400" />
          <h2 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
            Dynamic Quantitative Analytics & Biophysical Charts
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {dynamic_charts.map((chart) => (
            <div
              key={chart.chart_id}
              className="bg-slate-950/80 border border-slate-800/90 rounded-lg p-3.5 flex flex-col justify-between"
            >
              <div>
                <h3 className="text-xs font-bold text-slate-200 font-mono mb-2 pb-1 border-b border-slate-800">
                  {chart.title}
                </h3>

                {/* Chart 1: Bar Chart (Biophysical Differencing) */}
                {chart.chart_type === "bar" && chart.series && (
                  <div className="space-y-3 my-2">
                    {chart.series.map((item) => {
                      const isPositive = item.delta >= 0
                      const barWidthPercent = Math.min(100, Math.abs(item.delta) * 120)

                      return (
                        <div key={item.metric} className="space-y-1">
                          <div className="flex items-center justify-between text-[11px] font-mono">
                            <span className="text-slate-300 font-medium">{item.metric}</span>
                            <div className="flex items-center gap-1.5">
                              <span
                                className={`font-bold ${
                                  isPositive ? "text-amber-400" : "text-blue-400"
                                }`}
                              >
                                {isPositive ? `+${item.delta.toFixed(3)}` : item.delta.toFixed(3)} {item.unit}
                              </span>
                              <span
                                className={`text-[9px] px-1 py-0.2 rounded font-mono ${
                                  item.significance === "CRITICAL"
                                    ? "bg-rose-950 text-rose-300 border border-rose-800"
                                    : item.significance === "HIGH"
                                    ? "bg-amber-950 text-amber-300 border border-amber-800"
                                    : "bg-slate-800 text-slate-300"
                                }`}
                              >
                                {item.significance}
                              </span>
                            </div>
                          </div>

                          {/* Zero-centered horizontal bar */}
                          <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden flex items-center relative">
                            <div className="w-1/2 h-full border-r border-slate-700/80" />
                            {isPositive ? (
                              <div
                                className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-r"
                                style={{ width: `${barWidthPercent / 2}%` }}
                              />
                            ) : (
                              <div
                                className="h-full bg-gradient-to-l from-blue-500 to-cyan-500 rounded-l absolute right-1/2"
                                style={{ width: `${barWidthPercent / 2}%` }}
                              />
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}

                {/* Chart 2: Donut Chart (Land Partitioning) */}
                {chart.chart_type === "donut" && chart.segments && (
                  <div className="space-y-3 my-2">
                    {/* SVG Donut Visual */}
                    <div className="flex items-center justify-center py-1">
                      <svg width="150" height="150" viewBox="0 0 150 150" className="rotate-[-90deg]">
                        {(() => {
                          let accumulatedPercent = 0
                          const circumference = 2 * Math.PI * 45 // r = 45
                          return chart.segments.map((seg) => {
                            const strokeDasharray = `${(seg.percent / 100) * circumference} ${circumference}`
                            const strokeDashoffset = -((accumulatedPercent / 100) * circumference)
                            accumulatedPercent += seg.percent

                            return (
                              <circle
                                key={seg.class_name}
                                cx="75"
                                cy="75"
                                r="45"
                                fill="transparent"
                                stroke={seg.color}
                                strokeWidth="22"
                                strokeDasharray={strokeDasharray}
                                strokeDashoffset={strokeDashoffset}
                                className="transition-all duration-300 hover:opacity-85"
                              />
                            )
                          })
                        })()}
                      </svg>
                    </div>

                    {/* Breakdown List */}
                    <div className="space-y-1.5 pt-1">
                      {chart.segments.map((seg) => (
                        <div
                          key={seg.class_name}
                          className="flex items-center justify-between text-[11px] font-mono"
                        >
                          <div className="flex items-center gap-1.5">
                            <span
                              className="w-2.5 h-2.5 rounded-sm inline-block shrink-0"
                              style={{ backgroundColor: seg.color }}
                            />
                            <span className="text-slate-300 truncate max-w-[130px]" title={seg.class_name}>
                              {seg.class_name}
                            </span>
                          </div>
                          <span className="font-semibold text-slate-200">
                            {seg.area_ha} ha ({seg.percent}%)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Chart 3: Line Chart (Multi-Temporal Disturbance Progression) */}
                {chart.chart_type === "line" && chart.points && (
                  <div className="space-y-3 my-2">
                    {/* SVG Line Chart */}
                    <div className="w-full h-32 pt-2">
                      <svg viewBox="0 0 300 120" className="w-full h-full overflow-visible">
                        {/* Grid lines */}
                        <line x1="20" y1="20" x2="290" y2="20" stroke="#1e293b" strokeDasharray="3 3" />
                        <line x1="20" y1="60" x2="290" y2="60" stroke="#1e293b" strokeDasharray="3 3" />
                        <line x1="20" y1="100" x2="290" y2="100" stroke="#334155" />

                        {/* Plotted Path */}
                        {(() => {
                          const maxVal = Math.max(...chart.points.map((p) => p.value), 1)
                          const coords = chart.points.map((p, i) => {
                            const x = 30 + (i / (chart.points!.length - 1)) * 250
                            const y = 95 - (p.value / maxVal) * 75
                            return { x, y, point: p }
                          })
                          const pathStr = coords.reduce((acc, curr, idx) => {
                            return idx === 0 ? `M ${curr.x} ${curr.y}` : `${acc} L ${curr.x} ${curr.y}`
                          }, "")

                          return (
                            <>
                              <path
                                d={pathStr}
                                fill="none"
                                stroke="#f97316"
                                strokeWidth="2.5"
                                strokeLinecap="round"
                              />
                              {coords.map((c, i) => (
                                <g key={i}>
                                  <circle
                                    cx={c.x}
                                    cy={c.y}
                                    r="4"
                                    className="fill-orange-500 stroke-slate-950 stroke-2"
                                  />
                                  <text
                                    x={c.x}
                                    y={c.y - 8}
                                    textAnchor="middle"
                                    className="text-[9px] fill-orange-300 font-mono font-bold"
                                  >
                                    {c.point.value} ha
                                  </text>
                                  <text
                                    x={c.x}
                                    y="115"
                                    textAnchor="middle"
                                    className="text-[8px] fill-slate-500 font-mono"
                                  >
                                    {c.point.date.slice(2, 7)}
                                  </text>
                                </g>
                              ))}
                            </>
                          )
                        })()}
                      </svg>
                    </div>

                    {/* Timeline Event Notes */}
                    <div className="space-y-1 pt-2 border-t border-slate-800 text-[10px] font-mono">
                      {chart.points.slice(-3).map((p, idx) => (
                        <div key={idx} className="flex items-center gap-1.5 text-slate-400">
                          <span className="text-orange-400 font-bold">{p.date}:</span>
                          <span className="truncate">{p.event_note}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {chart.total_area_ha && (
                <div className="text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800/80">
                  Total Evaluated Envelope: {chart.total_area_ha} hectares
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* COMPREHENSIVE 7-SECTION TECHNICAL INTELLIGENCE DOSSIER */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-cyan-400" />
            <h2 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
              Technical Earth-Observation Intelligence Dossier
            </h2>
          </div>

          <div className="flex items-center gap-2 text-[11px] font-mono">
            <button
              onClick={() => toggleAllSections(true)}
              className="text-slate-400 hover:text-slate-200 px-1.5 py-0.5"
            >
              Expand All
            </button>
            <span className="text-slate-700">|</span>
            <button
              onClick={() => toggleAllSections(false)}
              className="text-slate-400 hover:text-slate-200 px-1.5 py-0.5"
            >
              Collapse All
            </button>
          </div>
        </div>

        {/* Sections Accordion */}
        <div className="space-y-2.5">
          {technical_dossier_sections.map((section, idx) => {
            const isOpen = !!expandedSections[section.section_id]
            const isGovernance = section.section_id === "uncertainty_boundary"

            return (
              <div
                key={section.section_id}
                className={`rounded-lg border transition-all ${
                  isGovernance
                    ? "bg-amber-950/20 border-amber-900/60"
                    : "bg-slate-950/70 border-slate-800/80"
                }`}
              >
                <button
                  onClick={() => toggleSection(section.section_id)}
                  className="w-full flex items-center justify-between p-3 text-left font-mono text-xs font-bold transition-colors hover:bg-slate-900/40 rounded-lg"
                >
                  <div className="flex items-center gap-2">
                    {isGovernance ? (
                      <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
                    ) : (
                      <span className="w-5 h-5 rounded-full bg-slate-900 border border-slate-800 text-[10px] text-cyan-400 flex items-center justify-center shrink-0">
                        {idx + 1}
                      </span>
                    )}
                    <span className={isGovernance ? "text-amber-300" : "text-slate-200"}>
                      {section.title}
                    </span>
                  </div>
                  {isOpen ? (
                    <ChevronUp className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  )}
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 pt-1 border-t border-slate-800/50">
                    <div className="text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-line space-y-2">
                      {section.content}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* FULL-SCREEN INTERACTIVE SATELLITE INSPECTION MODAL */}
      {inspectModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex flex-col p-4 md:p-6 animate-in fade-in duration-200">
          {/* Modal Header */}
          <div className="shrink-0 flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800 text-xs font-mono">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-cyan-300 font-bold">
                <Microscope className="w-4 h-4 text-cyan-400" />
                <span>Interactive Satellite Scene Inspector</span>
              </span>

              {/* Layer Selection Pills */}
              <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-md border border-slate-800">
                <button
                  onClick={() => setInspectLayer("t0")}
                  className={`px-2 py-0.5 rounded text-[11px] transition-all ${
                    inspectLayer === "t0"
                      ? "bg-blue-900/80 text-blue-200 font-bold border border-blue-700"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  🔵 Baseline (T₀ 2021)
                </button>
                <button
                  onClick={() => setInspectLayer("t1")}
                  className={`px-2 py-0.5 rounded text-[11px] transition-all ${
                    inspectLayer === "t1"
                      ? "bg-orange-900/80 text-orange-200 font-bold border border-orange-700"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  🟠 Monitoring (T₁ 2024)
                </button>
                <button
                  onClick={() => setInspectLayer("high_res")}
                  className={`px-2 py-0.5 rounded text-[11px] transition-all ${
                    inspectLayer === "high_res"
                      ? "bg-purple-900/80 text-purple-200 font-bold border border-purple-700"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  🟣 Sub-Meter Optical
                </button>
                <button
                  onClick={() => setInspectLayer("compare")}
                  className={`px-2 py-0.5 rounded text-[11px] transition-all ${
                    inspectLayer === "compare"
                      ? "bg-emerald-900/80 text-emerald-200 font-bold border border-emerald-700"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  🌓 Dual Wipe Slider
                </button>
              </div>
            </div>

            {/* Inspection Controls & Close */}
            <div className="flex items-center gap-2">
              {/* Zoom Controls */}
              <div className="flex items-center gap-1 bg-slate-900 px-2 py-1 rounded-md border border-slate-800 text-slate-300">
                <button
                  onClick={() => setZoomLevel((z) => Math.max(0.75, z - 0.25))}
                  className="p-1 hover:text-white"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="w-12 text-center text-[10px] font-bold">
                  {Math.round(zoomLevel * 100)}%
                </span>
                <button
                  onClick={() => setZoomLevel((z) => Math.min(4.5, z + 0.25))}
                  className="p-1 hover:text-white"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => {
                    setZoomLevel(1)
                    setPanOffset({ x: 0, y: 0 })
                  }}
                  className="p-1 hover:text-white border-l border-slate-700 pl-1.5 ml-0.5"
                  title="Reset 100%"
                >
                  <RotateCcw className="w-3 h-3 text-slate-400" />
                </button>
              </div>

              {/* Toggle Alignment Crosshair */}
              <button
                onClick={() => setShowGrid(!showGrid)}
                className={`flex items-center gap-1 px-2 py-1 rounded-md border transition-all ${
                  showGrid
                    ? "bg-cyan-950 text-cyan-300 border-cyan-700"
                    : "bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200"
                }`}
                title="Toggle Geographic Crosshair Alignment"
              >
                <Crosshair className="w-3.5 h-3.5" />
                <span className="text-[10px]">Crosshair</span>
              </button>

              {/* Open in New Tab */}
              <a
                href={activeInspectItem.tile_url}
                target="_blank"
                rel="noreferrer"
                className="p-1.5 rounded-md bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition-colors"
                title="Open raw full-resolution tile in new tab"
              >
                <ExternalLink className="w-4 h-4" />
              </a>

              {/* Close Button */}
              <button
                onClick={() => setInspectModalOpen(false)}
                className="p-1.5 rounded-md bg-rose-950/80 hover:bg-rose-900 border border-rose-800 text-rose-300 transition-colors"
                title="Close Inspector (Esc)"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Modal Interactive Canvas Body */}
          <div
            onWheel={handleInspectWheel}
            onMouseDown={handleInspectMouseDown}
            onMouseMove={handleInspectMouseMove}
            onMouseUp={handleInspectMouseUp}
            onMouseLeave={handleInspectMouseUp}
            className={`flex-1 relative overflow-hidden rounded-lg mt-3 bg-slate-950 border border-slate-800 flex items-center justify-center select-none ${
              isPanning ? "cursor-grabbing" : "cursor-grab"
            }`}
          >
            {/* Standard Single Layer Inspection */}
            {inspectLayer !== "compare" && (
              <div
                style={{
                  transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${zoomLevel})`,
                  transition: isPanning ? "none" : "transform 0.15s ease-out",
                }}
                className="relative max-w-full max-h-full"
              >
                <img
                  src={activeInspectItem.tile_url}
                  alt={activeInspectItem.layer_name}
                  className="max-h-[75vh] w-auto object-contain rounded shadow-2xl pointer-events-none"
                />

                {/* Alignment Crosshair Overlay */}
                {showGrid && (
                  <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    <div className="w-full h-[1px] bg-cyan-400/60 shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
                    <div className="absolute h-full w-[1px] bg-cyan-400/60 shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
                    <div className="absolute w-12 h-12 rounded-full border border-cyan-400/60" />
                  </div>
                )}
              </div>
            )}

            {/* Interactive Wipe Slider Comparison inside Modal */}
            {inspectLayer === "compare" && (
              <div
                ref={modalSliderRef}
                onMouseMove={(e) => isDraggingSlider && handleModalSliderMove(e.clientX)}
                className="relative w-full h-full max-h-[75vh] max-w-5xl rounded overflow-hidden cursor-ew-resize border border-slate-800 bg-slate-950"
              >
                <img
                  src={t1.tile_url}
                  alt="T1 Monitoring"
                  className="absolute inset-0 w-full h-full object-contain"
                />

                <div
                  className="absolute inset-0 overflow-hidden"
                  style={{ clipPath: `inset(0 ${100 - modalSliderPos}% 0 0)` }}
                >
                  <img
                    src={t0.tile_url}
                    alt="T0 Baseline"
                    className="absolute inset-0 w-full h-full object-contain"
                  />
                  <div className="absolute top-4 left-4 bg-slate-950/90 backdrop-blur px-3 py-1.5 rounded-md text-xs font-mono text-blue-300 font-bold border border-blue-800 shadow-lg">
                    T₀ Baseline ({new Date(t0.timestamp).getFullYear()})
                  </div>
                </div>

                <div className="absolute top-4 right-4 bg-slate-950/90 backdrop-blur px-3 py-1.5 rounded-md text-xs font-mono text-orange-300 font-bold border border-orange-800 shadow-lg">
                  T₁ Monitoring ({new Date(t1.timestamp).getFullYear()})
                </div>

                {/* Slider divider */}
                <div
                  className="absolute top-0 bottom-0 w-1 bg-white shadow-2xl cursor-ew-resize"
                  style={{ left: `${modalSliderPos}%` }}
                  onMouseDown={() => setIsDraggingSlider(true)}
                  onMouseUp={() => setIsDraggingSlider(false)}
                >
                  <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-slate-950 border-2 border-white flex items-center justify-center text-white shadow-xl">
                    <Sliders className="w-3.5 h-3.5 text-cyan-300" />
                  </div>
                </div>
              </div>
            )}

            {/* Bottom Overlay Instructions */}
            <div className="absolute bottom-3 left-3 right-3 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
              <div className="bg-slate-950/85 backdrop-blur px-3 py-1.5 rounded-md border border-slate-800 text-[11px] font-mono text-slate-300">
                <span className="font-bold text-white">{activeInspectItem.layer_name}</span> •{" "}
                <span>{activeInspectItem.resolution}</span> •{" "}
                <span className="text-cyan-400">
                  {new Date(activeInspectItem.timestamp).toLocaleDateString()}
                </span>
              </div>

              <div className="bg-slate-950/85 backdrop-blur px-3 py-1.5 rounded-md border border-slate-800 text-[10px] font-mono text-slate-400 flex items-center gap-2">
                <Move className="w-3 h-3 text-cyan-400" />
                <span>Click & drag to pan • Mouse wheel to zoom • Press Esc to close</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
