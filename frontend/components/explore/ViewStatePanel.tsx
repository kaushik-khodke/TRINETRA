"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * View State Telemetry Panel (Camera Observability)
 * Phase 1 Foundation
 */

import React, { useState } from "react"
import { ChevronDown, ChevronUp, Compass } from "lucide-react"
import { useGlobeState } from "@/lib/explore/globe-state"

export function ViewStatePanel() {
  const { camera, viewMode } = useGlobeState()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="viewstate-panel" role="region" aria-label="Camera Geospatial Coordinates">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
          marginBottom: collapsed ? 0 : 8,
          borderBottom: collapsed ? "none" : "1px solid rgba(255, 255, 255, 0.08)",
          paddingBottom: collapsed ? 0 : 6,
        }}
        onClick={() => setCollapsed(!collapsed)}
      >
        <span style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 600, color: "#cbd5e1" }}>
          <Compass size={13} color="#ff6b2b" />
          <span>VIEW TELEMETRY</span>
        </span>
        <button
          type="button"
          style={{ background: "transparent", border: "none", color: "#64748b", cursor: "pointer", padding: 0 }}
          aria-label={collapsed ? "Expand view telemetry" : "Collapse view telemetry"}
        >
          {collapsed ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {!collapsed && (
        <>
          <div className="viewstate-row">
            <span>LAT:</span>
            <span className="viewstate-val">{camera.latitude.toFixed(4)}° N</span>
          </div>
          <div className="viewstate-row">
            <span>LNG:</span>
            <span className="viewstate-val">{camera.longitude.toFixed(4)}° E</span>
          </div>
          <div className="viewstate-row">
            <span>ZOOM:</span>
            <span className="viewstate-val">{camera.zoom.toFixed(2)}</span>
          </div>
          <div className="viewstate-row">
            <span>MODE:</span>
            <span className="viewstate-val">{viewMode.toUpperCase()}</span>
          </div>
          <div className="viewstate-row">
            <span>HEADING:</span>
            <span className="viewstate-val">{Math.round(camera.heading)}°</span>
          </div>
          <div className="viewstate-row">
            <span>PITCH:</span>
            <span className="viewstate-val">{Math.round(camera.pitch)}°</span>
          </div>
        </>
      )}
    </div>
  )
}
