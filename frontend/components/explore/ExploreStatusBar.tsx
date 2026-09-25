"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Operational Status Bar Component
 * Phase 1 Foundation
 */

import React, { useEffect, useState } from "react"
import { Activity, Cpu, ShieldCheck } from "lucide-react"
import { useGlobeState } from "@/lib/explore/globe-state"
import { performanceMonitor } from "@/lib/explore/performance"
import { PerformanceMetrics } from "@/lib/explore/types"

export function ExploreStatusBar() {
  const { rendererStatus, viewMode, webglSupported, errorMessage, sidebarOpen, sidebarWidth } = useGlobeState()
  const [perf, setPerf] = useState<PerformanceMetrics>(performanceMonitor.getMetrics())

  useEffect(() => {
    return performanceMonitor.subscribe((m) => setPerf(m))
  }, [])

  const getStatusText = () => {
    if (!webglSupported) return "WEBGL NOT AVAILABLE"
    if (rendererStatus === "loading") return "INITIALIZING RENDERER..."
    if (rendererStatus === "error") return `RENDERER FAULT: ${errorMessage || "UNKNOWN"}`
    return `${viewMode.toUpperCase()} ${viewMode === "2d" ? "MAPLIBRE" : "CESIUM"} READY`
  }

  return (
    <footer
      className="explore-status-bar"
      role="status"
      aria-live="polite"
      style={{
        left: sidebarOpen ? `${sidebarWidth}px` : "0px",
        transition: "left 0.15s ease-out",
      }}
    >
      {/* Left: Renderer & WebGL readiness */}
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <div className="status-indicator">
          <span className={`status-dot ${rendererStatus === "ready" ? "ready" : rendererStatus === "loading" ? "loading" : "error"}`} />
          <span>{getStatusText()}</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 6, color: webglSupported ? "#94a3b8" : "#f87171" }}>
          <Cpu size={12} />
          <span>{webglSupported ? "GPU WEBGL ACCELERATED" : "GPU ACCELERATION DISABLED"}</span>
        </div>
      </div>

      {/* Right: Telemetry & Air-Gapped Status */}
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Activity size={12} color="#ff6b2b" />
          <span>FPS: {perf.estimatedFps} | INIT: {perf.initTimeMs}ms</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#10b981" }}>
          <ShieldCheck size={12} />
          <span>SHANETRA CLIENT-FIRST</span>
        </div>
      </div>
    </footer>
  )
}
