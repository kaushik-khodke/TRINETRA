/**
 * TRINETRA / Shanetra Explore Architecture
 * Globe Command Bus — Validated Event/Command Pipeline
 * Phase 1 Foundation
 */

import { GlobeCommand } from "./types"
import { globeController } from "./globe-controller"
import { globeState } from "./globe-state"
import { layerRegistry } from "./layer-registry"

export class GlobeCommandBus {
  private commandHistory: GlobeCommand[] = []
  private listeners: Set<(cmd: GlobeCommand) => void> = new Set()

  subscribe(listener: (cmd: GlobeCommand) => void): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  dispatch(cmd: GlobeCommand): boolean {
    // 1. Validation phase
    if (!this.validate(cmd)) {
      console.warn("[GlobeCommandBus] Invalid command rejected:", cmd)
      return false
    }

    this.commandHistory.push(cmd)

    // 2. Execution phase via GlobeController & GlobeState
    switch (cmd.type) {
      case "SET_VIEW_MODE":
        globeState.setViewMode(cmd.mode)
        globeController.setViewMode(cmd.mode)
        break

      case "FLY_TO":
        globeController.flyTo({
          latitude: cmd.latitude,
          longitude: cmd.longitude,
          zoom: cmd.zoom,
          heading: cmd.heading,
          pitch: cmd.pitch,
          duration: cmd.duration,
        })
        break

      case "RESET_VIEW":
        globeController.resetView()
        break

      case "SHOW_LAYER":
        globeState.setLayerVisibility(cmd.layerId, true)
        globeController.setLayerVisibility(cmd.layerId, true)
        break

      case "HIDE_LAYER":
        globeState.setLayerVisibility(cmd.layerId, false)
        globeController.setLayerVisibility(cmd.layerId, false)
        break

      case "TOGGLE_LAYER":
        const currentVis = globeState.getState().selectedLayerIds.includes(cmd.layerId)
        globeState.setLayerVisibility(cmd.layerId, !currentVis)
        globeController.setLayerVisibility(cmd.layerId, !currentVis)
        break

      case "SET_LAYER_OPACITY":
        globeState.setLayerOpacity(cmd.layerId, cmd.opacity)
        globeController.setLayerOpacity(cmd.layerId, cmd.opacity)
        break

      case "ADD_LAYER":
        layerRegistry.registerLayer(cmd.layer)
        globeController.addLayerSource(cmd.layer)
        globeState.setLayerVisibility(cmd.layer.id, true)
        globeState.setLayerOpacity(cmd.layer.id, cmd.layer.opacity ?? 1.0)
        break

      case "REMOVE_LAYER":
        globeState.setLayerVisibility(cmd.layerId, false)
        globeController.removeLayerSource(cmd.layerId)
        layerRegistry.removeLayer(cmd.layerId)
        break

      case "SET_AOI":
        globeController.setAOI(cmd.geometry)
        break

      case "CLEAR_AOI":
        globeController.clearAOI()
        break

      case "SELECT_OBSERVATION":
        if (cmd.observation?.bbox && cmd.observation.bbox.length === 4) {
          const [minX, minY, maxX, maxY] = cmd.observation.bbox
          globeController.flyTo({
            latitude: (minY + maxY) / 2,
            longitude: (minX + maxX) / 2,
            zoom: 10,
          })
        }
        break

      case "SET_COMPARISON":
        break

      case "SET_BASEMAP":
        globeState.setActiveBasemap(cmd.basemapId)
        globeController.setBasemap(cmd.basemapId, cmd.tileUrl)
        break
    }

    this.listeners.forEach((l) => {
      try {
        l(cmd)
      } catch (err) {
        console.warn("[GlobeCommandBus] Listener error:", err)
      }
    })

    return true
  }


  private validate(cmd: GlobeCommand): boolean {
    if (!cmd || typeof cmd !== "object") return false

    switch (cmd.type) {
      case "SET_VIEW_MODE":
        return cmd.mode === "2d" || cmd.mode === "3d"

      case "FLY_TO":
        return (
          typeof cmd.latitude === "number" &&
          isFinite(cmd.latitude) &&
          cmd.latitude >= -90 &&
          cmd.latitude <= 90 &&
          typeof cmd.longitude === "number" &&
          isFinite(cmd.longitude) &&
          cmd.longitude >= -180 &&
          cmd.longitude <= 180 &&
          typeof cmd.zoom === "number" &&
          isFinite(cmd.zoom) &&
          cmd.zoom >= 0 &&
          cmd.zoom <= 24
        )

      case "RESET_VIEW":
        return true

      case "SHOW_LAYER":
      case "HIDE_LAYER":
      case "TOGGLE_LAYER":
        return typeof cmd.layerId === "string" && cmd.layerId.trim().length > 0

      case "SET_LAYER_OPACITY":
        return (
          typeof cmd.layerId === "string" &&
          cmd.layerId.trim().length > 0 &&
          typeof cmd.opacity === "number" &&
          cmd.opacity >= 0 &&
          cmd.opacity <= 1
        )

      case "ADD_LAYER":
        return Boolean(cmd.layer && typeof cmd.layer.id === "string")

      case "REMOVE_LAYER":
        return typeof cmd.layerId === "string" && cmd.layerId.trim().length > 0

      case "SET_AOI":
        return Boolean(cmd.geometry)

      case "CLEAR_AOI":
        return true

      case "SELECT_OBSERVATION":
        return Boolean(cmd.observation && typeof cmd.observation.id === "string")

      case "SET_COMPARISON":
        return Boolean(cmd.mode && cmd.observationA && cmd.observationB)

      case "SET_BASEMAP":
        return typeof cmd.basemapId === "string" && cmd.basemapId.trim().length > 0

      default:
        return false
    }

  }

  getRecentCommands(): GlobeCommand[] {
    return [...this.commandHistory.slice(-20)]
  }
}

export const globeCommandBus = new GlobeCommandBus()
