/**
 * TRINETRA / Shanetra Explore Architecture
 * Bidirectional Camera Synchronizer
 * Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
 * Enforces loop-free camera synchronization across comparison views using origin tokens.
 */

import { GlobeCameraState } from "./types"

export type SyncOrigin = "view-a" | "view-b" | "system"

export interface CameraSyncEvent {
  origin: SyncOrigin
  camera: GlobeCameraState
}

class CameraSyncBus {
  private activeOrigin: SyncOrigin | null = null
  private listeners: Set<(event: CameraSyncEvent) => void> = new Set()
  private resetTimeout: any = null

  /**
   * Dispatches a camera update event from a specific origin view.
   * Silently ignores updates originating from feedback loops.
   */
  dispatch(origin: SyncOrigin, camera: GlobeCameraState): void {
    if (this.activeOrigin && this.activeOrigin !== origin) {
      // Loop prevented: This view is currently receiving an update from another origin
      return
    }

    this.activeOrigin = origin

    // Notify registered views
    this.listeners.forEach((listener) => {
      listener({ origin, camera })
    })

    // Release origin lock after current event frame
    if (this.resetTimeout) {
      clearTimeout(this.resetTimeout)
    }
    this.resetTimeout = setTimeout(() => {
      this.activeOrigin = null
    }, 50)
  }

  subscribe(listener: (event: CameraSyncEvent) => void): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }
}

export const cameraSyncBus = new CameraSyncBus()
