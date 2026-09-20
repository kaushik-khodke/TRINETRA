/**
 * TRINETRA / Shanetra Explore Architecture
 * Area of Interest (AOI) State Manager
 * Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
 */

import { useEffect, useState } from "react"
import { AOIValidationResult } from "./types"
import { TemporalApiClient } from "./temporal-api"
import { globeCommandBus } from "./globe-command-bus"

export type AOIDrawMode = "rectangle" | "polygon" | null

export interface AOIState {
  activeAOI: any | null
  drawMode: AOIDrawMode
  isDrawing: boolean
  validation: AOIValidationResult | null
  validationLoading: boolean
  vertexCount: number
  areaKm2: number | null
}

class AOIStateManager {
  private state: AOIState = {
    activeAOI: null,
    drawMode: null,
    isDrawing: false,
    validation: null,
    validationLoading: false,
    vertexCount: 0,
    areaKm2: null,
  }

  private listeners: Set<(state: AOIState) => void> = new Set()
  private abortController: AbortController | null = null

  getState(): AOIState {
    return { ...this.state }
  }

  setState(partial: Partial<AOIState>): void {
    this.state = { ...this.state, ...partial }
    this.notify()
  }

  setDrawMode(drawMode: AOIDrawMode): void {
    this.setState({
      drawMode,
      isDrawing: drawMode !== null,
    })
  }

  setDrawing(isDrawing: boolean): void {
    this.setState({ isDrawing })
  }

  async setAOI(geometry: any): Promise<AOIValidationResult | null> {
    if (!geometry) {
      this.clearAOI()
      return null
    }

    // Cancel in-flight validation
    if (this.abortController) {
      this.abortController.abort()
    }
    this.abortController = new AbortController()

    this.setState({
      activeAOI: geometry,
      drawMode: null,
      isDrawing: false,
      validationLoading: true,
      validation: null,
    })

    // Broadcast to renderers
    globeCommandBus.dispatch({ type: "SET_AOI", geometry })

    try {
      const validation = await TemporalApiClient.validateAOI(
        geometry,
        this.abortController.signal
      )
      this.setState({
        validation,
        validationLoading: false,
        vertexCount: validation.vertex_count || 0,
        areaKm2: validation.area_km2 || null,
      })
      return validation
    } catch (e: any) {
      if (e.name === "AbortError") return null
      const fallbackVal: AOIValidationResult = {
        valid: false,
        errors: [`Validation error: ${e.message}`],
        warnings: [],
      }
      this.setState({
        validation: fallbackVal,
        validationLoading: false,
      })
      return fallbackVal
    }
  }

  clearAOI(): void {
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }

    this.setState({
      activeAOI: null,
      drawMode: null,
      isDrawing: false,
      validation: null,
      validationLoading: false,
      vertexCount: 0,
      areaKm2: null,
    })

    // Broadcast to renderers
    globeCommandBus.dispatch({ type: "CLEAR_AOI" })
  }

  subscribe(listener: (state: AOIState) => void): () => void {
    this.listeners.add(listener)
    listener(this.getState())
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notify(): void {
    const s = this.getState()
    this.listeners.forEach((l) => l(s))
  }
}

export const aoiStateManager = new AOIStateManager()

export function useAOIState(): AOIState {
  const [state, setState] = useState<AOIState>(aoiStateManager.getState())

  useEffect(() => {
    return aoiStateManager.subscribe(setState)
  }, [])

  return state
}
