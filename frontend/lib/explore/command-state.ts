/**
 * TRINETRA / Shanetra Explore Architecture
 * Command State Reducer & Patch Coordinator
 * Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
 */

import { AIStatePatch } from "./command-types"
import { globeState } from "./globe-state"
import { globeController } from "./globe-controller"

export class CommandStateCoordinator {
  private static lastRequestId: string | null = null
  private static lastTimestamp: number = 0

  /**
   * Applies an AI state patch deterministically to globe state and controller.
   */
  static applyPatch(requestId: string, patch: AIStatePatch): boolean {
    // Prevent stale responses from overwriting newer interactions
    const now = Date.now()
    if (this.lastTimestamp > now) {
      console.warn("[CommandStateCoordinator] Ignored out-of-order state patch.")
      return false
    }

    this.lastRequestId = requestId
    this.lastTimestamp = now

    // 1. Camera Patch
    if (patch.camera) {
      const cam = patch.camera
      if (typeof cam.latitude === "number" && typeof cam.longitude === "number") {
        globeController.flyTo({
          latitude: cam.latitude,
          longitude: cam.longitude,
          zoom: cam.zoom ?? 10,
          heading: cam.heading ?? 0,
          pitch: cam.pitch ?? 0,
          duration: cam.duration ?? 1.5,
        })
      } else if (typeof cam.zoom === "number") {
        const current = globeState.getState().camera
        globeController.flyTo({
          ...current,
          zoom: cam.zoom,
          duration: 1.0,
        })
      }
    }

    // 2. Visible Layers Patch
    if (patch.visible_layer_ids && Array.isArray(patch.visible_layer_ids)) {
      const currentSelected = globeState.getState().selectedLayerIds
      // Deactivate layers removed
      for (const id of currentSelected) {
        if (!patch.visible_layer_ids.includes(id)) {
          globeState.setLayerVisibility(id, false)
          globeController.setLayerVisibility(id, false)
        }
      }
      // Activate layers added
      for (const id of patch.visible_layer_ids) {
        if (!currentSelected.includes(id)) {
          globeState.setLayerVisibility(id, true)
          globeController.setLayerVisibility(id, true)
        }
      }
    }

    // 3. Layer Opacities Patch
    if (patch.layer_opacities && typeof patch.layer_opacities === "object") {
      for (const [layerId, opacity] of Object.entries(patch.layer_opacities)) {
        if (typeof opacity === "number") {
          globeState.setLayerOpacity(layerId, opacity)
          globeController.setLayerOpacity(layerId, opacity)
        }
      }
    }

    // 4. Active Dataset Patch
    if (patch.active_dataset_id) {
      globeState.setActiveDataset(patch.active_dataset_id)
    }

    return true
  }
}
