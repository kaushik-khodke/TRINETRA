"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Explore Sidebar Component
 * Phase 2: Live EO discovery catalog, active layer management, and telemetry status.
 */

import React, { useState } from "react"
import { BrainCircuit, Briefcase, Calendar, Compass, Database, GitCompare, Layers, MapPin, Navigation, Satellite, Sparkles } from "lucide-react"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { useGlobeState } from "@/lib/explore/globe-state"
import { DEFAULT_CAMERA_STATE, ISRO_HQ_LOCATION } from "@/lib/explore/constants"
import { ViewModeSwitcher } from "./ViewModeSwitcher"
import DataSourcePanel from "./DataSourcePanel"
import CatalogResults from "./CatalogResults"
import ActiveLayers from "./ActiveLayers"
import DataStatus from "./DataStatus"
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
  const { sidebarOpen } = useGlobeState()
  const { observations, selectedObservation } = useTemporalState()
  const comparisonState = useComparisonState()
  const { activeAOI } = useAOIState()
  const [activeTab, setActiveTab] = useState<"catalog" | "temporal" | "compare" | "analysis" | "investigate" | "intelligence" | "workspace" | "layers" | "waypoints">("catalog")

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
      className={`explore-sidebar ${!sidebarOpen ? "collapsed" : ""}`}
      role="complementary"
      aria-label="Exploration Controls and Layers"
    >
      {/* 1. Dimension / View Mode Switcher */}
      <div className="sidebar-section">
        <div className="sidebar-section-header">
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Compass size={13} color="#38bdf8" />
            <span>DIMENSION / VIEW</span>
          </span>
        </div>
        <ViewModeSwitcher />
      </div>

      {/* 2. Operational Data Status */}
      <div className="sidebar-section">
        <DataStatus />
      </div>

      {/* 3. Section Navigation Tabs */}
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
          className={`tab-btn ${activeTab === "layers" ? "active" : ""}`}
          onClick={() => setActiveTab("layers")}
          title="Active Layers"
        >
          <Layers size={12} />
          <span>Layers</span>
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
                <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-cyan-500/20">
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
                <Navigation size={13} color="#38bdf8" />
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
                <Navigation size={13} color="#38bdf8" />
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
                <Navigation size={13} color="#38bdf8" />
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
