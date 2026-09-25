"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Live Telemetry & Coordinate HUD Component
 * Displays real-time Latitude, Longitude, Altitude, Zoom, Heading, and Pitch
 * positioned discreetly in the corner of the active viewport.
 */

import React, { useState } from "react"
import { useGlobeState } from "@/lib/explore/globe-state"
import { Compass, Copy, Check, Navigation } from "lucide-react"

export const CoordinateHUD: React.FC = () => {
  const { camera, viewMode } = useGlobeState()
  const [copied, setCopied] = useState(false)

  const lat = camera?.latitude ?? 0
  const lng = camera?.longitude ?? 0
  const zoom = camera?.zoom ?? 4
  const heading = Math.round(camera?.heading ?? 0)
  const pitch = Math.round(camera?.pitch ?? (viewMode === "2d" ? -90 : -45))

  // Estimate camera altitude from zoom level if not directly provided
  const estAltitudeMeters = Math.round(15000000 / Math.pow(2, zoom - 2))
  const formattedAlt = estAltitudeMeters >= 10000
    ? `${(estAltitudeMeters / 1000).toFixed(1)} km`
    : `${estAltitudeMeters.toLocaleString()} m`

  const latFormatted = `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? "N" : "S"}`
  const lngFormatted = `${Math.abs(lng).toFixed(4)}° ${lng >= 0 ? "E" : "W"}`

  const handleCopy = () => {
    const text = `${lat.toFixed(5)}, ${lng.toFixed(5)}`
    navigator.clipboard?.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  return (
    <div
      className="absolute bottom-9 right-3 z-20 h-9 px-3 rounded-xl bg-[#0a0e18]/70 backdrop-blur-xl border border-white/10 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.1),0_8px_24px_rgba(0,0,0,0.45)] flex items-center gap-2.5 font-mono text-[11px] text-slate-300 pointer-events-auto select-none transition-all hover:border-white/20 hover:bg-[#0a0e18]/85"
      style={{ letterSpacing: "0.02em" }}
      title="Active Camera Center Coordinates & Telemetry"
    >
      {/* Target indicator icon */}
      <div className="flex items-center gap-1.5 text-orange-400">
        <Navigation
          className="w-3.5 h-3.5 transition-transform duration-300"
          style={{ transform: `rotate(${heading}deg)` }}
        />
        <span className="font-bold text-[10px] text-orange-400/90 uppercase tracking-wider">GEO</span>
      </div>

      {/* Lat / Lon */}
      <div className="flex items-center gap-2 border-l border-white/10 pl-2">
        <span className="text-slate-100 font-semibold">{latFormatted}</span>
        <span className="text-slate-600">|</span>
        <span className="text-slate-100 font-semibold">{lngFormatted}</span>
      </div>

      {/* Altitude & Zoom */}
      <div className="hidden sm:flex items-center gap-2 border-l border-white/10 pl-2 text-slate-400">
        <span>ALT <strong className="text-orange-300 font-medium">{formattedAlt}</strong></span>
        <span className="text-slate-600">·</span>
        <span>Z <strong className="text-orange-300 font-medium">{zoom.toFixed(1)}</strong></span>
      </div>

      {/* 3D Attitude (Pitch / Heading) */}
      {viewMode === "3d" && (
        <div className="hidden md:flex items-center gap-1.5 border-l border-white/10 pl-2 text-slate-400 text-[10px]">
          <span>HDG {heading}°</span>
          <span className="text-slate-600">·</span>
          <span>PIT {pitch}°</span>
        </div>
      )}

      {/* Quick Copy Coordinates Button */}
      <button
        onClick={handleCopy}
        className="ml-0.5 h-6 w-6 rounded-lg flex items-center justify-center hover:bg-white/10 text-slate-400 hover:text-orange-300 transition-colors"
        title="Copy coordinates (lat, lon) to clipboard"
      >
        {copied ? (
          <Check className="w-3.5 h-3.5 text-emerald-400" />
        ) : (
          <Copy className="w-3.5 h-3.5" />
        )}
      </button>
    </div>
  )
}
