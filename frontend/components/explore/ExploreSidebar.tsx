"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Explore Sidebar Component
 * Phase 2: Live EO discovery catalog, active layer management, and telemetry status.
 */

import React, { useState, useCallback } from "react"
import Link from "next/link"
import { ArrowLeft, BrainCircuit, Briefcase, Calendar, Compass, Database, GitCompare, Layers, MapPin, Navigation, PanelLeftClose, Satellite, Sparkles } from "lucide-react"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { useGlobeState, globeState } from "@/lib/explore/globe-state"
import { DEFAULT_CAMERA_STATE, ISRO_HQ_LOCATION } from "@/lib/explore/constants"
import { ViewModeSwitcher } from "./ViewModeSwitcher"
import DataSourcePanel from "./DataSourcePanel"
import CatalogResults from "./CatalogResults"
import ActiveLayers from "./ActiveLayers"
import { TemporalToolbar } from "./TemporalToolbar"
import { ObservationCard } from "./ObservationCard"
import { ObservationDetails } from "./ObservationDetails"
import { ComparisonPanel } from "./ComparisonPanel"
import { AnalysisPanel } from "./AnalysisPanel"
import { InvestigationPanel } from "./InvestigationPanel"
import { IntelligenceWorkspace } from "./IntelligenceWorkspace"
import { WorkspaceShell } from "@/components/workspace/WorkspaceShell"
import { useTemporalState } from "@/lib/explore/temporal-state"
import { useComparisonState } from "@/lib/explore/comparison-state"
import { useAOIState } from "@/lib/explore/aoi-state"

export function ExploreSidebar() {
  const { sidebarOpen, sidebarWidth } = useGlobeState()
  const { observations, selectedObservation } = useTemporalState()
  const comparisonState = useComparisonState()
  const { activeAOI } = useAOIState()
  const [activeTab, setActiveTab] = useState<"catalog" | "temporal" | "compare" | "analysis" | "investigate" | "intelligence" | "workspace" | "layers" | "waypoints">("catalog")
  const [isResizing, setIsResizing] = useState(false)

  const startResizing = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    document.body.style.cursor = "col-resize"
    document.body.style.userSelect = "none"

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newWidth = Math.max(280, Math.min(window.innerWidth * 0.7, moveEvent.clientX))
      globeState.setSidebarWidth(newWidth)
    }

    const onMouseUp = () => {
      setIsResizing(false)
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
      window.removeEventListener("mousemove", onMouseMove)
      window.removeEventListener("mouseup", onMouseUp)
    }

    window.addEventListener("mousemove", onMouseMove)
    window.addEventListener("mouseup", onMouseUp)
  }, [])

  const handleFlyTo = (target: typeof DEFAULT_CAMERA_STATE) => {
    globeCommandBus.dispatch({
      type: "FLY_TO",
      latitude: target.latitude,
      longitude: target.longitude,
      zoom: target.zoom,
      heading: target.heading,
      pitch: target.pitch,
    })
  }

  return (
    <aside
      className={`explore-sidebar ${!sidebarOpen ? "collapsed" : ""} ${isResizing ? "resizing" : ""}`}
      style={{
        width: !sidebarOpen ? undefined : `${sidebarWidth}px`,
      }}
      role="complementary"
      aria-label="Exploration Controls and Layers"
    >
      {/* Draggable Resize Handle */}
      {sidebarOpen && (
        <div
          className={`sidebar-resize-handle ${isResizing ? "active" : ""}`}
          onMouseDown={startResizing}
          onDoubleClick={() => globeState.setSidebarWidth(380)}
          title="Drag to resize sidebar width (double-click to reset)"
          aria-label="Drag to resize sidebar"
        />
      )}
      {/* 0. Top Sidebar Header Bar */}
      <div className="flex items-center justify-between px-3.5 h-[50px] border-b border-white/10 shrink-0">
        <div className="flex items-center gap-2">
          <Link
            href="/analysis"
            className="btn-tactical-icon !h-7 !px-2 text-xs"
            title="Return to Tactical Analysis Workspace"
          >
            <ArrowLeft size={13} />
            <span>Workspace</span>
          </Link>
          <span className="font-extrabold tracking-wider text-white text-xs uppercase">
            TRI•NETRA
          </span>
        </div>
        <button
          type="button"
          onClick={() => globeState.toggleSidebar()}
          className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
          title="Collapse Sidebar"
          aria-label="Collapse Sidebar"
        >
          <PanelLeftClose size={15} />
        </button>
      </div>

      {/* 1. Dimension / View Mode Switcher */}
      <div className="sidebar-section">
        <div className="sidebar-section-header">
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Compass size={13} color="#ff8c42" />
            <span>DIMENSION / VIEW</span>
          </span>
        </div>
        <ViewModeSwitcher />
      </div>

      {/* 2. Section Navigation Tabs */}
      <div className="sidebar-tabs">
        <button
          className={`tab-btn ${activeTab === "catalog" ? "active" : ""}`}
          onClick={() => setActiveTab("catalog")}
          title="Catalog Search"
        >
          <Satellite size={12} />
          <span>Catalog</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "layers" ? "active" : ""}`}
          onClick={() => setActiveTab("layers")}
          title="Active Layers & Basemaps"
        >
          <Layers size={12} />
          <span>Layers</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "temporal" ? "active" : ""}`}
          onClick={() => setActiveTab("temporal")}
          title="Temporal Observations"
        >
          <Calendar size={12} />
          <span>Temporal</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "compare" ? "active" : ""}`}
          onClick={() => setActiveTab("compare")}
          title="Dual Observation Comparison"
        >
          <GitCompare size={12} />
          <span>Compare</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "analysis" ? "active" : ""}`}
          onClick={() => setActiveTab("analysis")}
          title="EO Analytical Intelligence Engine"
        >
          <BrainCircuit size={12} />
          <span>Analysis</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "investigate" ? "active" : ""}`}
          onClick={() => setActiveTab("investigate")}
          title="Semantic EO Intelligence & Evidence Fusion"
        >
          <Sparkles size={12} />
          <span>Investigate</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "intelligence" ? "active" : ""}`}
          onClick={() => setActiveTab("intelligence")}
          title="Persistent EO Intelligence, Semantic Search & Monitoring"
        >
          <Database size={12} />
          <span>Intel</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "workspace" ? "active" : ""}`}
          onClick={() => setActiveTab("workspace")}
          title="Analyst Command Center & Multi-Region Workflows"
        >
          <Briefcase size={12} />
          <span>Workspace</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "waypoints" ? "active" : ""}`}
          onClick={() => setActiveTab("waypoints")}
          title="Waypoints"
        >
          <MapPin size={12} />
          <span>Points</span>
        </button>
      </div>


      {/* 4. Tab Contents */}
      <div className="tab-content-container">
        {activeTab === "catalog" && (
          <div className="catalog-tab-pane">
            <DataSourcePanel />
            <CatalogResults />
          </div>
        )}

        {activeTab === "temporal" && (
          <div className="temporal-tab-pane space-y-3">
            <TemporalToolbar />
            <ObservationDetails />
            {observations.length > 0 && (
              <div className="space-y-2">
                <span className="text-[11px] uppercase tracking-wider font-mono text-slate-400 block px-1">
                  Acquisitions ({observations.length})
                </span>
                <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-orange-500/20">
                  {observations.map((obs) => (
                    <ObservationCard key={obs.id} observation={obs} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "compare" && (
          <div className="compare-tab-pane">
            <ComparisonPanel />
          </div>
        )}

        {activeTab === "analysis" && (
          <div className="analysis-tab-pane h-full">
            <AnalysisPanel
              selectedObservation={selectedObservation}
              comparisonObservationA={comparisonState.observationA}
              comparisonObservationB={comparisonState.observationB}
              aoiGeometry={activeAOI?.geometry}
            />
          </div>
        )}

        {activeTab === "investigate" && (
          <div className="investigation-tab-pane h-full">
            <InvestigationPanel
              availableObservationIds={observations.map((o) => o.id)}
              aoiGeometry={activeAOI?.geometry}
            />
          </div>
        )}

        {activeTab === "intelligence" && (
          <div className="intelligence-tab-pane h-full">
            <IntelligenceWorkspace
              availableObservationIds={observations.map((o) => o.id)}
            />
          </div>
        )}

        {activeTab === "workspace" && (
          <div className="workspace-tab-pane h-full">
            <WorkspaceShell />
          </div>
        )}

        {activeTab === "layers" && (
          <div className="layers-tab-pane">
            <ActiveLayers />
          </div>
        )}


        {activeTab === "waypoints" && (
          <div className="waypoints-tab-pane">
            <div className="sidebar-section-header" style={{ marginBottom: 8 }}>
              <span>STRATEGIC WAYPOINTS</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <button
                type="button"
                className="layer-item"
                onClick={() => handleFlyTo(DEFAULT_CAMERA_STATE)}
              >
                <div className="layer-info">
                  <span className="layer-label">Central India (Nagpur)</span>
                  <span className="layer-badge">21.1458° N, 79.0882° E • Zoom 4.8</span>
                </div>
                <Navigation size={13} color="#ff6b2b" />
              </button>

              <button
                type="button"
                className="layer-item"
                onClick={() => handleFlyTo(ISRO_HQ_LOCATION)}
              >
                <div className="layer-info">
                  <span className="layer-label">ISRO HQ (Bengaluru)</span>
                  <span className="layer-badge">12.9716° N, 77.5946° E • Zoom 11.5</span>
                </div>
                <Navigation size={13} color="#ff6b2b" />
              </button>

              <button
                type="button"
                className="layer-item"
                onClick={() =>
                  handleFlyTo({
                    latitude: 18.922,
                    longitude: 72.8347,
                    zoom: 10.5,
                    heading: 0,
                    pitch: -45,
                  })
                }
              >
                <div className="layer-info">
                  <span className="layer-label">Mumbai Harbor (West Coast)</span>
                  <span className="layer-badge">18.9220° N, 72.8347° E • Zoom 10.5</span>
                </div>
                <Navigation size={13} color="#ff6b2b" />
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
