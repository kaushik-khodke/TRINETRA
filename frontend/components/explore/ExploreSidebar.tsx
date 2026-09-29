"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Explore Sidebar Component
 * Phase 2: Live EO discovery catalog, active layer management, workstation bulk uploads & mosaic datasets.
 */

import React, { useState, useCallback, useEffect } from "react"
import Link from "next/link"
import { ArrowLeft, Compass, FolderUp, Layers, MapPin, Navigation, PanelLeftClose, Satellite, Sparkles } from "lucide-react"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { useGlobeState, globeState } from "@/lib/explore/globe-state"
import { DEFAULT_CAMERA_STATE, ISRO_HQ_LOCATION } from "@/lib/explore/constants"
import DataSourcePanel from "./DataSourcePanel"
import CatalogResults from "./CatalogResults"
import ActiveLayers from "./ActiveLayers"
import { InvestigationPanel } from "./InvestigationPanel"
import { useAOIState } from "@/lib/explore/aoi-state"
import { WorkstationDataRail } from "@/components/workstation/WorkstationDataRail"
import { useWorkstationLayers, workstationLayersState } from "@/lib/explore/workstation-layers-state"

export function ExploreSidebar() {
  const { sidebarOpen, sidebarWidth } = useGlobeState()
  const { activeAOI } = useAOIState()
  const { layers, assets } = useWorkstationLayers()
  const [activeTab, setActiveTab] = useState<"data" | "catalog" | "layers" | "investigate" | "waypoints">("data")
  const [isResizing, setIsResizing] = useState(false)

  // Auto-load uploaded assets & mosaics on mount
  useEffect(() => {
    workstationLayersState.loadAssets()
  }, [])

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

      {/* 1. Section Navigation Tabs */}
      <div className="sidebar-tabs">
        <button
          className={`tab-btn ${activeTab === "data" ? "active" : ""}`}
          onClick={() => setActiveTab("data")}
          title="Workstation Datasets & Bulk Uploads"
        >
          <FolderUp size={12} />
          <span>Uploads</span>
          {assets.length > 0 && (
            <span className="text-[10px] font-mono px-1 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800/50">
              {assets.length}
            </span>
          )}
        </button>
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
          className={`tab-btn ${activeTab === "investigate" ? "active" : ""}`}
          onClick={() => setActiveTab("investigate")}
          title="Semantic EO Intelligence & Evidence Fusion"
        >
          <Sparkles size={12} />
          <span>Investigate</span>
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
      <div className={`tab-content-container ${activeTab === "investigate" || activeTab === "data" ? "!p-0 !overflow-hidden !gap-0" : ""}`}>
        {activeTab === "data" && (
          <div className="workstation-data-pane h-full w-full flex flex-col min-h-0 overflow-hidden">
            <WorkstationDataRail
              assets={assets}
              aois={[]}
              activeAOI={null}
              onSelectAOI={() => {}}
              hideAoiTab={true}
              layers={layers}
              onUpdateLayer={(id, updates) => workstationLayersState.updateLayer(id, updates)}
              onDeloadLayer={(id) => workstationLayersState.deloadLayer(id)}
              onReloadLayer={(id) => workstationLayersState.reloadLayer(id)}
              onDeloadAllLayers={() => workstationLayersState.deloadAllLayers()}
              onReloadAllLayers={() => workstationLayersState.reloadAllLayers()}
              onDeleteLayer={(id) => workstationLayersState.deleteLayer(id)}
              onDeleteAsset={(id) => workstationLayersState.deleteAsset(id)}
              onDeleteCollection={(id) => workstationLayersState.deleteCollection(id)}
              onUploadFile={(file, title, onProgress, colId) =>
                workstationLayersState.uploadFile(file, title, onProgress, colId)
              }
              onSearchCatalog={async () => []}
              onFitBounds={(bbox) => workstationLayersState.fitBounds(bbox)}
            />
          </div>
        )}

        {activeTab === "catalog" && (
          <div className="catalog-tab-pane">
            <DataSourcePanel />
            <CatalogResults />
          </div>
        )}

        {activeTab === "investigate" && (
          <div className="investigation-tab-pane h-full w-full flex flex-col min-h-0 overflow-hidden">
            <InvestigationPanel
              aoiGeometry={activeAOI ? (activeAOI.geometry || activeAOI) : null}
            />
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
                onClick={() =>
                  handleFlyTo({
                    latitude: ISRO_HQ_LOCATION.latitude,
                    longitude: ISRO_HQ_LOCATION.longitude,
                    zoom: 14,
                    heading: 0,
                    pitch: 0,
                    roll: 0,
                  })
                }
              >
                <div className="layer-info">
                  <span className="layer-label">ISRO Headquarters (Bengaluru)</span>
                  <span className="layer-badge">12.9716° N, 77.5946° E • Zoom 14</span>
                </div>
                <Navigation size={13} color="#ff6b2b" />
              </button>

              <button
                type="button"
                className="layer-item"
                onClick={() =>
                  handleFlyTo({
                    latitude: 13.7199,
                    longitude: 80.2304,
                    zoom: 12,
                    heading: 0,
                    pitch: 0,
                    roll: 0,
                  })
                }
              >
                <div className="layer-info">
                  <span className="layer-label">Satish Dhawan Space Centre (Sriharikota)</span>
                  <span className="layer-badge">13.7199° N, 80.2304° E • Zoom 12</span>
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
