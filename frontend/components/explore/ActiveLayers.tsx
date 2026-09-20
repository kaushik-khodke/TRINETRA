"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * ActiveLayers Component
 * Phase 2: Layer management stack with visibility toggles, opacity sliders, and removal.
 */

import React from "react"
import { useGlobeState } from "@/lib/explore/globe-state"
import { layerRegistry } from "@/lib/explore/layer-registry"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"

export default function ActiveLayers() {
  const { selectedLayerIds, layerOpacities } = useGlobeState()
  const allLayers = layerRegistry.getAll()
  const activeLayers = allLayers.filter((l) => selectedLayerIds.includes(l.id))

  const handleToggle = (layerId: string) => {
    globeCommandBus.dispatch({ type: "TOGGLE_LAYER", layerId })
  }

  const handleOpacity = (layerId: string, opacity: number) => {
    globeCommandBus.dispatch({ type: "SET_LAYER_OPACITY", layerId, opacity })
  }

  const handleRemove = (layerId: string) => {
    globeCommandBus.dispatch({ type: "REMOVE_LAYER", layerId })
  }

  return (
    <div className="active-layers-stack">
      <div className="section-label">ACTIVE LAYERS ({activeLayers.length})</div>

      {activeLayers.length === 0 ? (
        <div className="layers-empty">No active layers enabled.</div>
      ) : (
        <div className="layer-items-list">
          {activeLayers.map((layer) => {
            const opacity = layerOpacities[layer.id] ?? layer.opacity ?? 1.0
            const isRemovable = layer.category !== "base"

            return (
              <div key={layer.id} className="active-layer-item">
                <div className="layer-header-row">
                  <label className="layer-checkbox-label">
                    <input
                      type="checkbox"
                      checked={true}
                      onChange={() => handleToggle(layer.id)}
                    />
                    <span className="layer-name">{layer.label}</span>
                  </label>

                  {isRemovable && (
                    <button
                      className="layer-remove-btn"
                      onClick={() => handleRemove(layer.id)}
                      title="Remove layer"
                    >
                      ×
                    </button>
                  )}
                </div>

                <div className="opacity-slider-row">
                  <span className="opacity-label">Opacity</span>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={Math.round(opacity * 100)}
                    onChange={(e) => handleOpacity(layer.id, Number(e.target.value) / 100)}
                    className="opacity-slider"
                  />
                  <span className="opacity-val">{Math.round(opacity * 100)}%</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
