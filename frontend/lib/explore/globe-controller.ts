/**
 * TRINETRA / Shanetra Explore Architecture
 * Globe Controller — Unified Renderer-Agnostic Abstraction
 * Phase 1 Foundation
 */

import { DEFAULT_CAMERA_STATE } from "./constants"
import { ExploreViewMode, GlobeCameraState, RendererAdapter } from "./types"

export class GlobeController {
  private activeMode: ExploreViewMode = "2d"
  private adapters: Map<ExploreViewMode, RendererAdapter> = new Map()

  registerAdapter(mode: ExploreViewMode, adapter: RendererAdapter): void {
    this.adapters.set(mode, adapter)
  }

  unregisterAdapter(mode: ExploreViewMode): void {
    const existing = this.adapters.get(mode)
    if (existing) {
      try {
        existing.destroy()
      } catch (err) {
        console.warn(`[GlobeController] Error during adapter cleanup for ${mode}:`, err)
      }
      this.adapters.delete(mode)
    }
  }

  getActiveAdapter(): RendererAdapter | undefined {
    return this.adapters.get(this.activeMode)
  }

  setViewMode(mode: ExploreViewMode): void {
    this.activeMode = mode
  }

  flyTo(target: {
    latitude: number
    longitude: number
    zoom?: number
    heading?: number
    pitch?: number
    duration?: number
    bounds?: [number, number, number, number]
  }): void {
    const adapter = this.getActiveAdapter()
    if (adapter) {
      adapter.flyTo(target)
    } else {
      console.warn(`[GlobeController] No active adapter registered for mode: ${this.activeMode}`)
    }
  }

  resetView(): void {
    const adapter = this.getActiveAdapter()
    if (adapter) {
      adapter.resetView()
    } else {
      this.flyTo(DEFAULT_CAMERA_STATE)
    }
  }

  setLayerVisibility(layerId: string, visible: boolean): void {
    const adapter = this.getActiveAdapter()
    if (adapter) {
      adapter.setLayerVisibility(layerId, visible)
    }
  }

  setLayerOpacity(layerId: string, opacity: number): void {
    const adapter = this.getActiveAdapter()
    if (adapter && adapter.setLayerOpacity) {
      adapter.setLayerOpacity(layerId, opacity)
    }
  }

  addLayerSource(layer: any): void {
    this.adapters.forEach((adapter) => {
      if (adapter.addLayerSource) {
        adapter.addLayerSource(layer)
      }
    })
  }

  removeLayerSource(layerId: string): void {
    this.adapters.forEach((adapter) => {
      if (adapter.removeLayerSource) {
        adapter.removeLayerSource(layerId)
      }
    })
  }

  setAOI(geometry: any): void {
    this.adapters.forEach((adapter) => {
      if (adapter.setAOI) {
        adapter.setAOI(geometry)
      }
    })
  }

  clearAOI(): void {
    this.adapters.forEach((adapter) => {
      if (adapter.clearAOI) {
        adapter.clearAOI()
      }
    })
  }

  setBasemap(basemapId: string, tileUrl?: string): void {
    this.adapters.forEach((adapter) => {
      if (adapter.setBasemap) {
        adapter.setBasemap(basemapId, tileUrl)
      }
    })
  }

  getCameraState(): GlobeCameraState {

    const adapter = this.getActiveAdapter()
    if (adapter) {
      return adapter.getCameraState()
    }
    return { ...DEFAULT_CAMERA_STATE }
  }

  destroy(): void {
    this.adapters.forEach((adapter) => {
      try {
        adapter.destroy()
      } catch (e) {
        // Safe cleanup
      }
    })
    this.adapters.clear()
  }
}

export const globeController = new GlobeController()
