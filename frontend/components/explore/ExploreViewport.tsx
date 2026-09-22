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
import { Timeline } from "./Timeline"
import { SplitView } from "./SplitView"
import { CoordinateHUD } from "./CoordinateHUD"
import { useComparisonState } from "@/lib/explore/comparison-state"

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
  const { viewMode, sidebarOpen } = useGlobeState()
  const { mode: comparisonMode } = useComparisonState()

  return (
    <main className="explore-viewport relative" role="region" aria-label="Earth Observation Viewport">
      {/* Floating Sidebar Toggle Button */}
      <button
        type="button"
        className="sidebar-toggle-floating"
        onClick={() => globeState.toggleSidebar()}
        aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
      >
        {sidebarOpen ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />}
      </button>

      {/* Floating AOI Toolbar */}
      <div className="absolute top-3.5 left-16 z-20">
        <AOIToolbar />
      </div>

      {/* Active Renderer Isolation (Section 27: Never run both renderers simultaneously) */}
      {comparisonMode === "split" && viewMode === "2d" ? (
        <MapErrorBoundary>
          <Suspense fallback={null}>
            <SplitView />
          </Suspense>
        </MapErrorBoundary>
      ) : viewMode === "2d" ? (
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

      {/* Floating Acquisition Timeline */}
      <div className="absolute bottom-10 left-4 right-4 z-20 pointer-events-auto">
        <Timeline />
      </div>

      {/* Live Geospatial Coordinate & Telemetry HUD */}
      <CoordinateHUD />
    </main>
  )
}

