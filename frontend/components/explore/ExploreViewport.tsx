"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * ExploreViewport Component — Renderer Lifecycle & Viewport Coordinator
 * Phase 1 Foundation
 */

import React, { Suspense } from "react"
import dynamic from "next/dynamic"
import { PanelLeftClose, PanelLeftOpen } from "lucide-react"
import { useGlobeState, globeState } from "@/lib/explore/globe-state"
import { MapErrorBoundary } from "./MapErrorBoundary"
import { GlobeErrorBoundary } from "./GlobeErrorBoundary"
import { ViewStatePanel } from "./ViewStatePanel"

import { AOIToolbar } from "./AOIToolbar"
import { SpectralPresetBar } from "./SpectralPresetBar"
import { CoordinateHUD } from "./CoordinateHUD"

// Dynamic client-side only renderer loading with zero SSR overhead
const MapView = dynamic(() => import("./MapView"), {
  ssr: false,
  loading: () => (
    <div className="renderer-fallback">
      <div className="status-dot loading" style={{ width: 12, height: 12, marginBottom: 12 }} />
      <span>INITIALIZING 2D MAPLIBRE ENGINE...</span>
    </div>
  ),
})

const GlobeView = dynamic(() => import("./GlobeView"), {
  ssr: false,
  loading: () => (
    <div className="renderer-fallback">
      <div className="status-dot loading" style={{ width: 12, height: 12, marginBottom: 12 }} />
      <span>INITIALIZING 3D CESIUM GLOBE ENGINE...</span>
    </div>
  ),
})

export function ExploreViewport() {
  const { viewMode, sidebarOpen, sidebarWidth } = useGlobeState()

  return (
    <main className="explore-viewport relative" role="region" aria-label="Earth Observation Viewport">
      {/* Top Floating Glass Dock: Sidebar Toggle + AOI Selection + Copernicus Multi-Spectral Presets */}
      <div
        className="absolute top-16 z-20 flex items-center gap-2 pointer-events-auto flex-wrap"
        style={{
          left: sidebarOpen ? `${sidebarWidth + 14}px` : "14px",
          transition: "left 0.15s ease-out",
        }}
      >
        <button
          type="button"
          className="sidebar-toggle-floating"
          onClick={() => globeState.toggleSidebar()}
          aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          {sidebarOpen ? <PanelLeftClose size={15} /> : <PanelLeftOpen size={15} />}
        </button>
        <AOIToolbar />
        <SpectralPresetBar />
      </div>

      {/* Active Renderer Isolation (Section 27: Never run both renderers simultaneously) */}
      {viewMode === "2d" ? (
        <MapErrorBoundary>
          <Suspense fallback={null}>
            <MapView />
          </Suspense>
        </MapErrorBoundary>
      ) : (
        <GlobeErrorBoundary>
          <Suspense fallback={null}>
            <GlobeView />
          </Suspense>
        </GlobeErrorBoundary>
      )}

      {/* Live Geospatial Coordinate & Telemetry HUD */}
      <CoordinateHUD />
    </main>
  )
}

