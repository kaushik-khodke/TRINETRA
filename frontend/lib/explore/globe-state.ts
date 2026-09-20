/**
 * TRINETRA / Shanetra Explore Architecture
 * Globe State — Canonical Single Source of Truth for Explore Session
 * Phase 2: Integrated data discovery state, layer opacities, and separate data/layer lifecycle.
 */

import { useEffect, useState } from "react"
import { DEFAULT_CAMERA_STATE } from "./constants"
import { layerRegistry } from "./layer-registry"
import { ExploreDataset, ExploreState, ExploreViewMode, GlobeCameraState } from "./types"

class GlobeStateManager {
  private state: ExploreState = {
    viewMode: "2d",
    sidebarOpen: true,
    camera: { ...DEFAULT_CAMERA_STATE },
    selectedLayerIds: layerRegistry.getDefaultVisibleIds(),
    layerOpacities: { "layer-base-dark": 1.0, "layer-borders": 0.8 },
    activeDatasetId: null,
    catalogItems: [],
    catalogLoading: false,
    catalogProvider: "all",
    rendererStatus: "idle",
    webglSupported: true,
    errorMessage: null,
  }

  private listeners: Set<(state: ExploreState) => void> = new Set()

  getState(): ExploreState {
    return { ...this.state }
  }

  setState(partial: Partial<ExploreState>): void {
    this.state = { ...this.state, ...partial }
    this.notify()
  }

  setViewMode(viewMode: ExploreViewMode): void {
    if (this.state.viewMode !== viewMode) {
      this.setState({ viewMode, rendererStatus: "loading" })
    }
  }

  toggleSidebar(): void {
    this.setState({ sidebarOpen: !this.state.sidebarOpen })
  }

  setSidebarOpen(sidebarOpen: boolean): void {
    this.setState({ sidebarOpen })
  }

  setCamera(camera: GlobeCameraState): void {
    const c = this.state.camera
    const latDiff = Math.abs(c.latitude - camera.latitude)
    const lngDiff = Math.abs(c.longitude - camera.longitude)
    const zoomDiff = Math.abs(c.zoom - camera.zoom)
    const headingDiff = Math.abs(c.heading - camera.heading)
    const pitchDiff = Math.abs(c.pitch - camera.pitch)

    if (latDiff > 0.0001 || lngDiff > 0.0001 || zoomDiff > 0.01 || headingDiff > 0.5 || pitchDiff > 0.5) {
      this.state.camera = { ...camera }
      this.notify()
    }
  }

  setRendererStatus(status: ExploreState["rendererStatus"], errorMessage: string | null = null): void {
    this.setState({ rendererStatus: status, errorMessage })
  }

  setWebglSupported(supported: boolean): void {
    this.setState({ webglSupported: supported })
  }

  setLayerVisibility(layerId: string, visible: boolean): void {
    const current = new Set(this.state.selectedLayerIds)
    if (visible) {
      current.add(layerId)
    } else {
      current.delete(layerId)
    }
    this.setState({ selectedLayerIds: Array.from(current) })
  }

  setLayerOpacity(layerId: string, opacity: number): void {
    const clamped = Math.max(0.0, Math.min(1.0, isNaN(opacity) ? 1.0 : opacity))
    this.setState({
      layerOpacities: {
        ...this.state.layerOpacities,
        [layerId]: clamped,
      },
    })
  }

  setActiveDataset(activeDatasetId: string | null): void {
    this.setState({ activeDatasetId })
  }

  setCatalogItems(catalogItems: ExploreDataset[]): void {
    this.setState({ catalogItems })
  }

  setCatalogLoading(catalogLoading: boolean): void {
    this.setState({ catalogLoading })
  }

  setCatalogProvider(catalogProvider: "all" | "local" | "copernicus"): void {
    this.setState({ catalogProvider })
  }

  subscribe(listener: (state: ExploreState) => void): () => void {
    this.listeners.add(listener)
    listener(this.getState())
    return () => this.listeners.delete(listener)
  }

  private notify(): void {
    const snapshot = this.getState()
    this.listeners.forEach((fn) => fn(snapshot))
  }
}

export const globeState = new GlobeStateManager()

/**
 * Custom React Hook for components subscribing to Globe State
 */
export function useGlobeState(): ExploreState {
  const [state, setLocalState] = useState<ExploreState>(globeState.getState())

  useEffect(() => {
    return globeState.subscribe((newState) => {
      setLocalState(newState)
    })
  }, [])

  return state
}
