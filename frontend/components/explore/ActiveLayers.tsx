"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * ActiveLayers Component
 * Real Earth Basemap Swapping, Multi-Layer Overlays, Custom Tile Additions & Provider Key Config.
 */

import React, { useState } from "react"
import { Globe, Key, Layers, Plus, Shield, Sliders, Sparkles, Trash2, Check, RefreshCw } from "lucide-react"
import { useGlobeState } from "@/lib/explore/globe-state"
import { layerRegistry } from "@/lib/explore/layer-registry"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { BASEMAP_PRESETS, BasemapPreset } from "@/lib/explore/constants"
import { ExploreLayerDefinition } from "@/lib/explore/types"

export default function ActiveLayers() {
  const { selectedLayerIds, layerOpacities, activeBasemap } = useGlobeState()
  const allLayers = layerRegistry.getAll()
  const activeLayers = allLayers.filter((l) => selectedLayerIds.includes(l.id))
  const inactiveLayers = allLayers.filter((l) => !selectedLayerIds.includes(l.id) && l.category !== "base")

  // Modal dialog states
  const [showAddModal, setShowAddModal] = useState(false)
  const [showKeysModal, setShowKeysModal] = useState(false)

  // Custom layer form
  const [customName, setCustomName] = useState("")
  const [customUrl, setCustomUrl] = useState("")
  const [customAttribution, setCustomAttribution] = useState("")
  const [customAsBasemap, setCustomAsBasemap] = useState(false)

  // API Keys form
  const [cesiumTokenInput, setCesiumTokenInput] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("trinetra_cesium_ion_token") || ""
    }
    return ""
  })
  const [googleKeyInput, setGoogleKeyInput] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("trinetra_google_maps_api_key") || ""
    }
    return ""
  })
  const [keysSavedMessage, setKeysSavedMessage] = useState<string | null>(null)

  const handleSelectBasemap = (preset: BasemapPreset) => {
    globeCommandBus.dispatch({
      type: "SET_BASEMAP",
      basemapId: preset.id,
      tileUrl: preset.tileUrl,
      label: preset.label,
    })
  }

  const handleToggle = (layerId: string) => {
    globeCommandBus.dispatch({ type: "TOGGLE_LAYER", layerId })
  }

  const handleOpacity = (layerId: string, opacity: number) => {
    globeCommandBus.dispatch({ type: "SET_LAYER_OPACITY", layerId, opacity })
  }

  const handleRemove = (layerId: string) => {
    globeCommandBus.dispatch({ type: "REMOVE_LAYER", layerId })
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

  const handleAddCustomLayer = (e: React.FormEvent) => {
    e.preventDefault()
    if (!customName.trim() || !customUrl.trim()) return

    const newLayerId = `layer-custom-${Date.now()}`
    const newLayer: ExploreLayerDefinition = {
      id: newLayerId,
      label: customName.trim(),
      category: "imagery",
      rendererSupport: ["2d", "3d"],
      sourceType: "raster",
      tileTemplate: customUrl.trim(),
      defaultVisible: true,
      userControllable: true,
      aiControllable: true,
      expensive: false,
      opacity: 1.0,
      description: "User-defined custom raster tile layer.",
      attribution: customAttribution.trim() || "Custom Tile Provider",
    }

    // Register & Add to Active
    globeCommandBus.dispatch({ type: "ADD_LAYER", layer: newLayer })

    // If requested, set as active basemap immediately
    if (customAsBasemap) {
      globeCommandBus.dispatch({
        type: "SET_BASEMAP",
        basemapId: newLayerId,
        tileUrl: customUrl.trim(),
        label: customName.trim(),
      })
    }

    setCustomName("")
    setCustomUrl("")
    setCustomAttribution("")
    setCustomAsBasemap(false)
    setShowAddModal(false)
  }

  const handleSaveKeys = () => {
    if (typeof window !== "undefined") {
      if (cesiumTokenInput.trim()) {
        localStorage.setItem("trinetra_cesium_ion_token", cesiumTokenInput.trim())
      } else {
        localStorage.removeItem("trinetra_cesium_ion_token")
      }

      if (googleKeyInput.trim()) {
        localStorage.setItem("trinetra_google_maps_api_key", googleKeyInput.trim())
      } else {
        localStorage.removeItem("trinetra_google_maps_api_key")
      }

      setKeysSavedMessage("Credentials saved. Reloading 3D engine...")
      setTimeout(() => {
        window.location.reload()
      }, 800)
    }
  }

  const handleClearKeys = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("trinetra_cesium_ion_token")
      localStorage.removeItem("trinetra_google_maps_api_key")
      setCesiumTokenInput("")
      setGoogleKeyInput("")
      setKeysSavedMessage("Credentials cleared.")
      setTimeout(() => setKeysSavedMessage(null), 2000)
    }
  }

  return (
    <div className="active-layers-stack space-y-4">
      {/* 1. Basemap Selector Console */}
      <div className="basemap-section bg-slate-900/60 p-3 rounded-lg border border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400 tracking-wider uppercase">
            <Globe size={13} />
            <span>Globe Basemap Data</span>
          </span>
          <button
            onClick={() => setShowKeysModal(true)}
            className="text-[10px] text-slate-400 hover:text-cyan-300 flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/60 transition-colors"
            title="Configure Cesium Ion or Google 3D Credentials"
          >
            <Key size={10} />
            <span>API Keys</span>
          </button>
        </div>

        <div className="grid grid-cols-3 gap-1.5 mb-2">
          {Object.values(BASEMAP_PRESETS).map((preset) => {
            const isSelected = activeBasemap === preset.id
            return (
              <button
                key={preset.id}
                onClick={() => handleSelectBasemap(preset)}
                className={`flex flex-col items-center justify-center p-2 rounded text-center transition-all border ${
                  isSelected
                    ? "bg-cyan-950/70 border-cyan-500 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.25)]"
                    : "bg-slate-800/50 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800 hover:border-slate-600"
                }`}
              >
                <span className="text-[11px] font-bold leading-tight">{preset.shortLabel}</span>
                <span className="text-[9px] text-slate-400/80 truncate w-full mt-0.5">{preset.label.split(" ")[0]}</span>
              </button>
            )
          })}
        </div>

        <div className="text-[10px] text-slate-400/90 italic px-1">
          {BASEMAP_PRESETS[activeBasemap]?.description || "Custom active basemap provider."}
        </div>
      </div>

      {/* 2. Layer Operations Toolbar */}
      <div className="flex items-center justify-between px-1">
        <span className="text-[11px] font-semibold tracking-wider uppercase text-slate-300 flex items-center gap-1.5">
          <Layers size={12} className="text-cyan-400" />
          <span>Active Overlays ({activeLayers.length})</span>
        </span>
        <button
          onClick={() => setShowAddModal(true)}
          className="text-[10px] flex items-center gap-1 px-2 py-1 rounded bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 transition-all font-medium"
        >
          <Plus size={11} />
          <span>Add Layer / URL</span>
        </button>
      </div>

      {/* 3. Inactive Available Layers Quick-Pills */}
      {inactiveLayers.length > 0 && (
        <div className="px-1">
          <span className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1.5">Quick Add Overlay:</span>
          <div className="flex flex-wrap gap-1.5">
            {inactiveLayers.map((layer) => (
              <button
                key={layer.id}
                onClick={() => handleToggle(layer.id)}
                className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 hover:border-cyan-500/40 transition-colors flex items-center gap-1"
              >
                <Plus size={9} className="text-cyan-400" />
                <span>{layer.label.split(" (")[0]}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 4. Active Layer Stack */}
      {activeLayers.length === 0 ? (
        <div className="p-4 rounded border border-dashed border-slate-800 text-center text-slate-500 text-xs">
          No overlay layers enabled. The basemap displays the full globe.
        </div>
      ) : (
        <div className="space-y-2">
          {activeLayers.map((layer) => {
            const opacity = layerOpacities[layer.id] ?? layer.opacity ?? 1.0
            const isBase = layer.category === "base"

            return (
              <div
                key={layer.id}
                className="p-2.5 rounded bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-all space-y-2"
              >
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={true}
                      onChange={() => handleToggle(layer.id)}
                      className="rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer"
                    />
                    <span className="text-xs font-medium text-slate-200">{layer.label}</span>
                  </label>

                  <div className="flex items-center gap-1.5">
                    {layer.tileTemplate && (
                      <button
                        onClick={() => handleMakeBasemap(layer)}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 hover:bg-cyan-900/60 text-slate-400 hover:text-cyan-300 border border-slate-700/60 transition-colors flex items-center gap-1"
                        title="Replace whole globe basemap with this dataset"
                      >
                        <Globe size={10} />
                        <span>Make Base</span>
                      </button>
                    )}

                    {!isBase && (
                      <button
                        onClick={() => handleRemove(layer.id)}
                        className="text-slate-500 hover:text-rose-400 p-0.5 rounded transition-colors"
                        title="Remove layer"
                      >
                        <Trash2 size={12} />
                      </button>
                    )}
                  </div>
                </div>

                {/* Opacity Slider */}
                <div className="flex items-center gap-2 text-[10px] text-slate-400 pl-6">
                  <span className="w-11 text-slate-500">Opacity</span>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={Math.round(opacity * 100)}
                    onChange={(e) => handleOpacity(layer.id, Number(e.target.value) / 100)}
                    className="flex-1 accent-cyan-400 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
                  />
                  <span className="w-7 text-right font-mono text-slate-300">{Math.round(opacity * 100)}%</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* MODAL 1: Add Custom Layer */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-semibold text-cyan-300 flex items-center gap-2">
                <Layers size={15} />
                <span>Add Custom Satellite / Raster Layer</span>
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-200 text-lg leading-none"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleAddCustomLayer} className="space-y-3">
              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Layer Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sentinel-2 NDVI Composite"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  className="w-full text-xs bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Tile URL Template (XYZ)</label>
                <input
                  type="text"
                  required
                  placeholder="https://server.com/tiles/{z}/{x}/{y}.png"
                  value={customUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                  className="w-full text-xs font-mono bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">Supports standard `{`{z}`}`, `{`{x}`}`, `{`{y}`}` raster tile servers.</span>
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Attribution (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. European Space Agency / USGS"
                  value={customAttribution}
                  onChange={(e) => setCustomAttribution(e.target.value)}
                  className="w-full text-xs bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="pt-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={customAsBasemap}
                    onChange={(e) => setCustomAsBasemap(e.target.checked)}
                    className="rounded bg-slate-800 border-slate-700 text-cyan-500 cursor-pointer"
                  />
                  <span className="text-xs text-slate-300">Replace whole globe basemap with this dataset</span>
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="text-xs px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="text-xs px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium"
                >
                  Add Layer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Provider API Keys */}
      {showKeysModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-semibold text-cyan-300 flex items-center gap-2">
                <Key size={15} />
                <span>Geospatial Provider Credentials</span>
              </h3>
              <button
                onClick={() => setShowKeysModal(false)}
                className="text-slate-400 hover:text-slate-200 text-lg leading-none"
              >
                ×
              </button>
            </div>

            <div className="space-y-3">
              <p className="text-xs text-slate-400 leading-relaxed">
                By default, TRINETRA uses keyless Esri World Satellite, Copernicus Sentinel-1 & 2, and Re:Earth 3D terrain. You can optionally supply credentials below to enable Google Photorealistic 3D Tiles and Cesium World Terrain.
              </p>

              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Cesium Ion Access Token</label>
                <input
                  type="password"
                  placeholder="eyJhbGciOi..."
                  value={cesiumTokenInput}
                  onChange={(e) => setCesiumTokenInput(e.target.value)}
                  className="w-full text-xs font-mono bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500 mt-0.5 block">Stored locally in your browser.</span>
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Google Maps API Key (Photorealistic 3D)</label>
                <input
                  type="password"
                  placeholder="AIzaSy..."
                  value={googleKeyInput}
                  onChange={(e) => setGoogleKeyInput(e.target.value)}
                  className="w-full text-xs font-mono bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500 mt-0.5 block">Enables direct Google Photorealistic 3D Tiles.</span>
              </div>

              {keysSavedMessage && (
                <div className="p-2 rounded bg-cyan-950/60 border border-cyan-700 text-cyan-300 text-xs text-center">
                  {keysSavedMessage}
                </div>
              )}

              <div className="flex justify-between items-center pt-2">
                <button
                  type="button"
                  onClick={handleClearKeys}
                  className="text-xs px-2.5 py-1.5 rounded bg-slate-800/80 hover:bg-rose-950/60 text-slate-400 hover:text-rose-300 transition-colors"
                >
                  Clear Saved
                </button>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setShowKeysModal(false)}
                    className="text-xs px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                  >
                    Close
                  </button>
                  <button
                    type="button"
                    onClick={handleSaveKeys}
                    className="text-xs px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium flex items-center gap-1"
                  >
                    <Check size={12} />
                    <span>Save & Apply</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
