/**
 * TRINETRA / Shanetra Explore Architecture
 * Dual-Observation Comparison State Manager
 * Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
 */

import { useEffect, useState } from "react"
import {
  ComparisonMode,
  ComparisonValidationResponse,
  ObservationSummary,
} from "./types"
import { TemporalApiClient } from "./temporal-api"
import { globeCommandBus } from "./globe-command-bus"

export type ActiveComparisonMode = ComparisonMode | "none"

export interface ComparisonState {
  mode: ActiveComparisonMode
  observationA: ObservationSummary | null
  observationB: ObservationSummary | null
  splitPosition: number // 0 to 100
  opacityA: number // 0.0 to 1.0
  opacityB: number // 0.0 to 1.0
  validation: ComparisonValidationResponse | null
  validating: boolean
  syncCamera: boolean
}

class ComparisonStateManager {
  private state: ComparisonState = {
    mode: "none",
    observationA: null,
    observationB: null,
    splitPosition: 50,
    opacityA: 1.0,
    opacityB: 1.0,
    validation: null,
    validating: false,
    syncCamera: true,
  }

  private listeners: Set<(state: ComparisonState) => void> = new Set()

  getState(): ComparisonState {
    return { ...this.state }
  }

  setState(partial: Partial<ComparisonState>): void {
    this.state = { ...this.state, ...partial }
    this.notify()
  }

  setMode(mode: ActiveComparisonMode): void {
    this.setState({ mode })
    if (mode !== "none" && this.state.observationA && this.state.observationB) {
      this.validatePair()
      globeCommandBus.dispatch({
        type: "SET_COMPARISON",
        mode: mode as ComparisonMode,
        observationA: this.state.observationA,
        observationB: this.state.observationB,
      })
    }
  }

  setObservationA(obs: ObservationSummary | null): void {
    this.setState({ observationA: obs })
    if (obs && this.state.observationB) {
      this.validatePair()
    }
  }

  setObservationB(obs: ObservationSummary | null): void {
    this.setState({ observationB: obs })
    if (this.state.observationA && obs) {
      this.validatePair()
    }
  }

  setSplitPosition(splitPosition: number): void {
    this.setState({ splitPosition: Math.max(0, Math.min(100, splitPosition)) })
  }

  setOpacityA(opacityA: number): void {
    this.setState({ opacityA: Math.max(0, Math.min(1, opacityA)) })
  }

  setOpacityB(opacityB: number): void {
    this.setState({ opacityB: Math.max(0, Math.min(1, opacityB)) })
  }

  setSyncCamera(syncCamera: boolean): void {
    this.setState({ syncCamera })
  }

  swapObservations(): void {
    const temp = this.state.observationA
    this.setState({
      observationA: this.state.observationB,
      observationB: temp,
    })
    if (this.state.observationB && temp && this.state.mode !== "none") {
      this.validatePair()
    }
  }

  async validatePair(): Promise<ComparisonValidationResponse | null> {
    const { observationA, observationB, mode } = this.state
    if (!observationA || !observationB) return null

    this.setState({ validating: true })
    try {
      const activeMode = mode === "none" ? "split" : mode
      const res = await TemporalApiClient.validateComparison(
        observationA.id,
        observationB.id,
        activeMode
      )
      this.setState({
        validation: res,
        validating: false,
      })
      return res
    } catch (e: any) {
      const fallback: ComparisonValidationResponse = {
        compatible: false,
        warnings: [],
        errors: [`Validation request failed: ${e.message}`],
      }
      this.setState({
        validation: fallback,
        validating: false,
      })
      return fallback
    }
  }

  clearComparison(): void {
    this.setState({
      mode: "none",
      observationA: null,
      observationB: null,
      validation: null,
      validating: false,
    })
  }

  subscribe(listener: (state: ComparisonState) => void): () => void {
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

export const comparisonStateManager = new ComparisonStateManager()

export function useComparisonState(): ComparisonState {
  const [state, setState] = useState<ComparisonState>(
    comparisonStateManager.getState()
  )

  useEffect(() => {
    return comparisonStateManager.subscribe(setState)
  }, [])

  return state
}
