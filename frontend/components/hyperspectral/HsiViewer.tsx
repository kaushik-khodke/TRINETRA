"use client"

import React, { useState } from "react"
import { Layers, Activity, Sparkles, Sliders, Eye, FileText, CheckCircle2 } from "lucide-react"

export interface HsiViewerProps {
  cubeMetadata?: {
    height: number
    width: number
    bands: number
    wavelengthRange?: [number, number]
    sensor?: string
    crs?: string
  }
  rgbComposite?: string
  cirComposite?: string
  evidenceImage?: string
  spectralSignature?: {
    wavelengths: number[]
    meanCurve: number[]
    stdCurve: number[]
    absorptionFeatures?: Array<{
      wavelength_nm: number
      reflectance?: number
      dip_depth: number
      diagnostic_feature: string
    }>
  }
  topClasses?: Array<{ class_name: string; confidence: number }>
}

export function HsiViewer({
  cubeMetadata,
  rgbComposite,
  cirComposite,
  evidenceImage,
  spectralSignature,
  topClasses,
}: HsiViewerProps) {
  const [activeView, setActiveView] = useState<"evidence" | "rgb" | "cir">("evidence")
  const [hoveredWavelength, setHoveredWavelength] = useState<number | null>(null)

  const displayImage =
    activeView === "rgb"
      ? rgbComposite || evidenceImage
      : activeView === "cir"
      ? cirComposite || evidenceImage
      : evidenceImage || rgbComposite

  const wavelengths = spectralSignature?.wavelengths || []
  const meanCurve = spectralSignature?.meanCurve || []
  const stdCurve = spectralSignature?.stdCurve || []

  // Compute SVG viewBox coordinates for spectral plot
  const minWl = wavelengths.length ? Math.min(...wavelengths) : 400
  const maxWl = wavelengths.length ? Math.max(...wavelengths) : 2400
  const minRef = 0.0
  const maxRef = 1.0

  const svgWidth = 540
  const svgHeight = 200
  const padding = { top: 20, right: 25, bottom: 35, left: 45 }
  const plotW = svgWidth - padding.left - padding.right
  const plotH = svgHeight - padding.top - padding.bottom

  const getX = (wl: number) => padding.left + ((wl - minWl) / (maxWl - minWl || 1)) * plotW
  const getY = (ref: number) => padding.top + (1.0 - (ref - minRef) / (maxRef - minRef || 1)) * plotH

  // Generate SVG path for mean curve
  const pathD = wavelengths
    .map((wl, i) => {
      const x = getX(wl)
      const y = getY(meanCurve[i] ?? 0)
      return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(" ")

  // Generate SVG polygon for std deviation envelope
  const upperPoints = wavelengths.map((wl, i) => `${getX(wl).toFixed(1)},${getY(Math.min(1.0, (meanCurve[i] ?? 0) + (stdCurve[i] ?? 0))).toFixed(1)}`)
  const lowerPoints = wavelengths.slice().reverse().map((wl, revI) => {
    const i = wavelengths.length - 1 - revI
    return `${getX(wl).toFixed(1)},${getY(Math.max(0.0, (meanCurve[i] ?? 0) - (stdCurve[i] ?? 0))).toFixed(1)}`
  })
  const areaD = upperPoints.length ? `M ${upperPoints.join(" L ")} L ${lowerPoints.join(" L ")} Z` : ""

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "16px" }}>
      {/* 1. Hyperspectral Sensor Metadata Badge Banner */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "12px",
          padding: "12px 16px",
          background: "rgba(16, 185, 129, 0.08)",
          border: "1px solid rgba(16, 185, 129, 0.25)",
          borderRadius: "8px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#10B981", fontWeight: 600, fontSize: "13px" }}>
          <Layers size={16} />
          <span>HYPERSPECTRAL CUBE PRESERVED</span>
        </div>
        <div style={{ height: "14px", width: "1px", background: "rgba(255,255,255,0.15)" }} />
        <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>
          Sensor: <strong style={{ color: "#FFF" }}>{cubeMetadata?.sensor || "Hyperspectral Spec"}</strong>
        </span>
        <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>
          Spectral Bands: <strong style={{ color: "#10B981" }}>{cubeMetadata?.bands || 224} Channels</strong>
        </span>
        {cubeMetadata?.wavelengthRange && (
          <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.75)" }}>
            Wavelengths: <strong style={{ color: "#FFF" }}>{cubeMetadata.wavelengthRange[0]}nm – {cubeMetadata.wavelengthRange[1]}nm</strong>
          </span>
        )}
        {cubeMetadata?.crs && (
          <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)", marginLeft: "auto" }}>
            CRS: {cubeMetadata.crs}
          </span>
        )}
      </div>

      {/* 2. Dual-Column Visualization (Raster View + Spectral Curve) */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px" }}>
        {/* Left: Composite Selector & Image Display */}
        <div
          style={{
            background: "rgba(255, 255, 255, 0.03)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "8px",
            padding: "12px",
            display: "flex",
            flexDirection: "column",
            gap: "10px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "12px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", color: "rgba(255,255,255,0.8)" }}>
              Spectral Composite View
            </span>
            <div style={{ display: "flex", gap: "4px" }}>
              <button
                type="button"
                onClick={() => setActiveView("evidence")}
                style={{
                  padding: "4px 8px",
                  fontSize: "11px",
                  fontWeight: 500,
                  borderRadius: "4px",
                  border: "none",
                  cursor: "pointer",
                  background: activeView === "evidence" ? "#10B981" : "rgba(255,255,255,0.06)",
                  color: activeView === "evidence" ? "#000" : "rgba(255,255,255,0.7)",
                }}
              >
                Specialist Overlay
              </button>
              <button
                type="button"
                onClick={() => setActiveView("rgb")}
                style={{
                  padding: "4px 8px",
                  fontSize: "11px",
                  fontWeight: 500,
                  borderRadius: "4px",
                  border: "none",
                  cursor: "pointer",
                  background: activeView === "rgb" ? "#10B981" : "rgba(255,255,255,0.06)",
                  color: activeView === "rgb" ? "#000" : "rgba(255,255,255,0.7)",
                }}
              >
                True Color RGB
              </button>
              <button
                type="button"
                onClick={() => setActiveView("cir")}
                style={{
                  padding: "4px 8px",
                  fontSize: "11px",
                  fontWeight: 500,
                  borderRadius: "4px",
                  border: "none",
                  cursor: "pointer",
                  background: activeView === "cir" ? "#10B981" : "rgba(255,255,255,0.06)",
                  color: activeView === "cir" ? "#000" : "rgba(255,255,255,0.7)",
                }}
              >
                False-Color CIR
              </button>
            </div>
          </div>

          <div
            style={{
              position: "relative",
              width: "100%",
              aspectRatio: "1/1",
              background: "#0a0c10",
              borderRadius: "6px",
              overflow: "hidden",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {displayImage ? (
              <img
                src={displayImage.startsWith("data:") ? displayImage : `data:image/png;base64,${displayImage}`}
                alt="Hyperspectral Composite"
                style={{ width: "100%", height: "100%", objectFit: "contain" }}
              />
            ) : (
              <span style={{ color: "rgba(255,255,255,0.4)", fontSize: "12px" }}>Composite generating...</span>
            )}
            <div
              style={{
                position: "absolute",
                bottom: "8px",
                left: "8px",
                padding: "3px 8px",
                background: "rgba(0,0,0,0.75)",
                backdropFilter: "blur(4px)",
                borderRadius: "4px",
                fontSize: "10px",
                color: "rgba(255,255,255,0.8)",
              }}
            >
              {activeView === "rgb" ? "True Color (640/550/470 nm)" : activeView === "cir" ? "Color-Infrared (850/650/550 nm)" : "Perception Overlay"}
            </div>
          </div>
        </div>

        {/* Right: Continuous Spectral Reflectance Signature Plot */}
        <div
          style={{
            background: "rgba(255, 255, 255, 0.03)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "8px",
            padding: "12px",
            display: "flex",
            flexDirection: "column",
            gap: "10px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "12px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", color: "rgba(255,255,255,0.8)" }}>
              Continuous Spectral Signature (λ vs. Reflectance)
            </span>
            <span style={{ fontSize: "11px", color: "#10B981" }}>Real HSI Pixels</span>
          </div>

          {wavelengths.length > 0 ? (
            <div style={{ position: "relative", width: "100%" }}>
              <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ width: "100%", height: "auto", display: "block" }}>
                {/* Axes grid lines */}
                <line x1={padding.left} y1={padding.top} x2={padding.left} y2={svgHeight - padding.bottom} stroke="rgba(255,255,255,0.15)" />
                <line x1={padding.left} y1={svgHeight - padding.bottom} x2={svgWidth - padding.right} y2={svgHeight - padding.bottom} stroke="rgba(255,255,255,0.15)" />

                {/* Y-axis labels (Reflectance 0.0, 0.5, 1.0) */}
                <text x={padding.left - 8} y={getY(0.0) + 4} fill="rgba(255,255,255,0.4)" fontSize="10" textAnchor="end">0.0</text>
                <text x={padding.left - 8} y={getY(0.5) + 4} fill="rgba(255,255,255,0.4)" fontSize="10" textAnchor="end">0.5</text>
                <text x={padding.left - 8} y={getY(1.0) + 4} fill="rgba(255,255,255,0.4)" fontSize="10" textAnchor="end">1.0</text>

                {/* X-axis labels (Wavelengths) */}
                <text x={getX(minWl)} y={svgHeight - padding.bottom + 16} fill="rgba(255,255,255,0.4)" fontSize="10" textAnchor="middle">{minWl.toFixed(0)}nm</text>
                <text x={getX((minWl + maxWl) / 2)} y={svgHeight - padding.bottom + 16} fill="rgba(255,255,255,0.4)" fontSize="10" textAnchor="middle">{((minWl + maxWl) / 2).toFixed(0)}nm</text>
                <text x={getX(maxWl)} y={svgHeight - padding.bottom + 16} fill="rgba(255,255,255,0.4)" fontSize="10" textAnchor="middle">{maxWl.toFixed(0)}nm</text>

                {/* Std Dev Uncertainty Shading */}
                {areaD && <path d={areaD} fill="rgba(16, 185, 129, 0.15)" />}

                {/* Mean Spectral Curve */}
                <path d={pathD} fill="none" stroke="#10B981" strokeWidth="2.5" strokeLinecap="round" />

                {/* Absorption Dip Annotations */}
                {spectralSignature?.absorptionFeatures?.map((f, idx) => {
                  const dipX = getX(f.wavelength_nm)
                  const dipY = getY(f.reflectance ?? 0.2)
                  return (
                    <g key={idx}>
                      <circle cx={dipX} cy={dipY} r="4" fill="#EF4444" stroke="#FFF" strokeWidth="1.5" />
                      <line x1={dipX} y1={dipY} x2={dipX} y2={dipY - 18} stroke="#EF4444" strokeWidth="1" strokeDasharray="2,2" />
                      <text x={dipX} y={dipY - 22} fill="#EF4444" fontSize="9" textAnchor="middle" fontWeight="bold">
                        {f.wavelength_nm}nm
                      </text>
                    </g>
                  )
                })}
              </svg>
            </div>
          ) : (
            <div style={{ padding: "40px 0", textAlign: "center", color: "rgba(255,255,255,0.4)", fontSize: "12px" }}>
              Awaiting spectral signature data...
            </div>
          )}

          {/* Diagnostic Features Card */}
          {spectralSignature?.absorptionFeatures && spectralSignature.absorptionFeatures.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "4px" }}>
              <span style={{ fontSize: "11px", fontWeight: 600, color: "rgba(255,255,255,0.6)", textTransform: "uppercase" }}>
                Identified Absorption Dip Features
              </span>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                {spectralSignature.absorptionFeatures.map((f, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      fontSize: "11px",
                      padding: "4px 8px",
                      background: "rgba(255,255,255,0.02)",
                      borderRadius: "4px",
                    }}
                  >
                    <span style={{ color: "#EF4444", fontWeight: 600 }}>{f.wavelength_nm} nm</span>
                    <span style={{ color: "rgba(255,255,255,0.7)" }}>{f.diagnostic_feature}</span>
                    <span style={{ color: "rgba(255,255,255,0.4)" }}>Dip Depth: {f.dip_depth}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 3. Top Land-Cover Classification Badges (HyperFree-B) */}
      {topClasses && topClasses.length > 0 && (
        <div
          style={{
            background: "rgba(255, 255, 255, 0.02)",
            border: "1px solid rgba(255, 255, 255, 0.06)",
            borderRadius: "8px",
            padding: "12px",
          }}
        >
          <div style={{ fontSize: "11px", fontWeight: 600, textTransform: "uppercase", color: "rgba(255,255,255,0.6)", marginBottom: "8px" }}>
            HyperFree-B Multi-Class Land-Cover Predictions
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {topClasses.map((c, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "4px 10px",
                  background: "rgba(16, 185, 129, 0.12)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  borderRadius: "6px",
                  fontSize: "12px",
                }}
              >
                <CheckCircle2 size={13} color="#10B981" />
                <span style={{ color: "#FFF" }}>{c.class_name}</span>
                <strong style={{ color: "#10B981" }}>{Math.round(c.confidence * 100)}%</strong>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
