"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Layer Panel Component — Consumes Centralized Layer Registry
 * Phase 1 Foundation
 */

import React from "react"
import { Eye, EyeOff, Globe, Layers, ShieldCheck, Sparkles } from "lucide-react"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { useGlobeState } from "@/lib/explore/globe-state"
import { layerRegistry } from "@/lib/explore/layer-registry"
import { ExploreLayerDefinition } from "@/lib/explore/types"

export function LayerPanel() {
  const { selectedLayerIds, viewMode } = useGlobeState()
  const layers = layerRegistry.getSupportedForMode(viewMode)

  const handleToggle = (layer: ExploreLayerDefinition) => {
    if (!layer.userControllable) return
    globeCommandBus.dispatch({ type: "TOGGLE_LAYER", layerId: layer.id })
  }

  const handleMakeBasemap = (layer: ExploreLayerDefinition) => {
    if (!layer.tileTemplate) return
    globeCommandBus.dispatch({
      type: "SET_BASEMAP",
      basemapId: layer.id,
      tileUrl: layer.tileTemplate,
      label: layer.label,
    })
  }

  const baseLayers = layers.filter((l: ExploreLayerDefinition) => l.category === "base")
  const imageryLayers = layers.filter((l: ExploreLayerDefinition) => l.category === "imagery")
  const systemLayers = layers.filter((l: ExploreLayerDefinition) => l.category === "system")
  const analysisLayers = layers.filter((l: ExploreLayerDefinition) => l.category === "analysis")

  const renderLayerItem = (layer: ExploreLayerDefinition) => {
    const isVisible = selectedLayerIds.includes(layer.id)
    const isFuture = layer.description?.includes("Coming in Phase 2")

    return (
      <div key={layer.id} className="layer-item">
        <div className="layer-info">
          <span className="layer-label">{layer.label}</span>
          <span className="layer-badge">
            {isFuture ? (
              <span style={{ color: "#f59e0b" }}>Phase 2 Catalog</span>
            ) : (
              <span>{layer.attribution}</span>
            )}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {layer.tileTemplate && (
            <button
              type="button"
              onClick={() => handleMakeBasemap(layer)}
              className="layer-toggle-btn"
              aria-label={`Set ${layer.label} as Basemap`}
              title="Replace globe basemap with this dataset"
            >
              <Globe size={13} />
            </button>
          )}

          <button
            type="button"
            disabled={isFuture}
            onClick={() => handleToggle(layer)}
            className={`layer-toggle-btn ${isVisible ? "active" : ""}`}
            aria-label={`${isVisible ? "Hide" : "Show"} ${layer.label}`}
            title={isFuture ? "Available in Phase 2" : isVisible ? "Hide Layer" : "Show Layer"}
          >
            {isVisible ? <Eye size={15} /> : <EyeOff size={15} />}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="sidebar-section">
      <div className="sidebar-section-header">
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Layers size={13} color="#38bdf8" />
          <span>VISUALIZATION LAYERS</span>
        </span>
      </div>

      {/* Base Layer */}
      {baseLayers.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 9, fontWeight: 700, color: "#64748b", marginBottom: 6, textTransform: "uppercase" }}>
            Base References
          </div>
          {baseLayers.map(renderLayerItem)}
        </div>
      )}

      {/* Satellite Imagery (Phase 2 preview) */}
      {imageryLayers.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 9, fontWeight: 700, color: "#64748b", marginBottom: 6, textTransform: "uppercase" }}>
            Multispectral & Radar
          </div>
          {imageryLayers.map(renderLayerItem)}
        </div>
      )}

      {/* System / Boundaries */}
      {systemLayers.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 9, fontWeight: 700, color: "#64748b", marginBottom: 6, textTransform: "uppercase" }}>
            System & Geometry
          </div>
          {systemLayers.map(renderLayerItem)}
        </div>
      )}

      {/* AI Evidence */}
      {analysisLayers.length > 0 && (
        <div>
          <div style={{ fontSize: 9, fontWeight: 700, color: "#64748b", marginBottom: 6, textTransform: "uppercase" }}>
            AI Neural Evidence
          </div>
          {analysisLayers.map(renderLayerItem)}
        </div>
      )}
    </div>
  )
}
