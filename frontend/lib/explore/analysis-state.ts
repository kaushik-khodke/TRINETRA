/**
 * TRINETRA — Phase 5: EO Analytical Intelligence Engine State Manager
 * Manages run polling, active result state, selected findings, validation, and globe integration.
 */

import { useEffect, useState } from "react"
import {
  AnalysisFinding,
  AnalysisRequest,
  AnalysisResult,
  AnalysisRun,
  AnalysisValidationResponse,
} from "./types"
import { analysisApi } from "./analysis-api"
import { globeCommandBus } from "./globe-command-bus"

export interface AnalysisState {
  activeRun: AnalysisRun | null
  activeResult: AnalysisResult | null
  selectedFindingId: string | null
  activeFinding: AnalysisFinding | null
  isAnalyzing: boolean
  validation: AnalysisValidationResponse | null
  isValidating: boolean
  error: string | null
  evidencePack: Record<string, any> | null
}

class AnalysisStateManager {
  private state: AnalysisState = {
    activeRun: null,
    activeResult: null,
    selectedFindingId: null,
    activeFinding: null,
    isAnalyzing: false,
    validation: null,
    isValidating: false,
    error: null,
    evidencePack: null,
  }

  private listeners: Set<(state: AnalysisState) => void> = new Set()
  private pollInterval: any = null

  getState(): AnalysisState {
    return { ...this.state }
  }

  setState(partial: Partial<AnalysisState>): void {
    this.state = { ...this.state, ...partial }
    this.notify()
  }

  subscribe(listener: (state: AnalysisState) => void): () => void {
    this.listeners.add(listener)
    listener(this.getState())
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notify(): void {
    const currentState = this.getState()
    this.listeners.forEach((fn) => {
      try {
        fn(currentState)
      } catch (err) {
        console.error("AnalysisState listener error:", err)
      }
    })
  }

  async validateRequest(req: AnalysisRequest): Promise<AnalysisValidationResponse | null> {
    this.setState({ isValidating: true, error: null })
    try {
      const resp = await analysisApi.validateAnalysis(req)
      this.setState({ validation: resp, isValidating: false })
      return resp
    } catch (err: any) {
      this.setState({ isValidating: false, error: err.message || "Validation failed" })
      return null
    }
  }

  async startAnalysis(req: AnalysisRequest): Promise<void> {
    this.stopPolling()
    this.setState({
      isAnalyzing: true,
      error: null,
      activeResult: null,
      activeFinding: null,
      selectedFindingId: null,
      evidencePack: null,
    })

    try {
      const run = await analysisApi.startAnalysis(req)
      this.setState({ activeRun: run })
      this.startPolling(run.run_id)
    } catch (err: any) {
      this.setState({
        isAnalyzing: false,
        error: err.message || "Failed to start analysis run",
      })
    }
  }

  private startPolling(runId: string): void {
    this.stopPolling()

    const checkStatus = async () => {
      try {
        const run = await analysisApi.getAnalysisRun(runId)
        this.setState({ activeRun: run })

        if (run.status === "completed") {
          this.stopPolling()
          const result = run.result_data || null
          this.setState({
            activeResult: result,
            isAnalyzing: false,
            selectedFindingId: result?.findings?.[0]?.finding_id || null,
            activeFinding: result?.findings?.[0] || null,
          })

          // Fetch full evidence pack
          this.fetchEvidence(runId)
        } else if (run.status === "failed") {
          this.stopPolling()
          this.setState({
            isAnalyzing: false,
            error: run.error?.message || "Analysis execution failed",
          })
        } else if (run.status === "cancelled") {
          this.stopPolling()
          this.setState({ isAnalyzing: false })
        }
      } catch (err: any) {
        console.warn("Polling error for run", runId, err)
      }
    }

    // Initial check
    checkStatus()
    this.pollInterval = setInterval(checkStatus, 1500)
  }

  private stopPolling(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
      this.pollInterval = null
    }
  }

  private async fetchEvidence(runId: string): Promise<void> {
    try {
      const evidence = await analysisApi.getEvidencePack(runId)
      this.setState({ evidencePack: evidence })
    } catch (err) {
      console.warn("Could not fetch evidence pack:", err)
    }
  }

  async cancelCurrentRun(): Promise<void> {
    const { activeRun } = this.state
    if (!activeRun) return

    try {
      const cancelledRun = await analysisApi.cancelAnalysis(activeRun.run_id)
      this.stopPolling()
      this.setState({ activeRun: cancelledRun, isAnalyzing: false })
    } catch (err: any) {
      console.error("Failed to cancel run:", err)
    }
  }

  selectFinding(findingId: string | null): void {
    const { activeResult } = this.state
    if (!findingId || !activeResult) {
      this.setState({ selectedFindingId: null, activeFinding: null })
      return
    }

    const finding = activeResult.findings.find((f) => f.finding_id === findingId) || null
    this.setState({ selectedFindingId: findingId, activeFinding: finding })

    if (finding && finding.bounding_box) {
      globeCommandBus.dispatch({
        type: "FOCUS_ANALYSIS_REGION",
        bounds: finding.bounding_box,
        findingId: finding.finding_id,
      })
    }
  }

  reset(): void {
    this.stopPolling()
    this.state = {
      activeRun: null,
      activeResult: null,
      selectedFindingId: null,
      activeFinding: null,
      isAnalyzing: false,
      validation: null,
      isValidating: false,
      error: null,
      evidencePack: null,
    }
    this.notify()
  }
}

export const analysisStateManager = new AnalysisStateManager()

export function useAnalysisState(): AnalysisState & {
  startAnalysis: (req: AnalysisRequest) => Promise<void>
  cancelCurrentRun: () => Promise<void>
  validateRequest: (req: AnalysisRequest) => Promise<AnalysisValidationResponse | null>
  selectFinding: (findingId: string | null) => void
  reset: () => void
} {
  const [state, setState] = useState<AnalysisState>(analysisStateManager.getState())

  useEffect(() => {
    return analysisStateManager.subscribe((s) => setState(s))
  }, [])

  return {
    ...state,
    startAnalysis: (req) => analysisStateManager.startAnalysis(req),
    cancelCurrentRun: () => analysisStateManager.cancelCurrentRun(),
    validateRequest: (req) => analysisStateManager.validateRequest(req),
    selectFinding: (id) => analysisStateManager.selectFinding(id),
    reset: () => analysisStateManager.reset(),
  }
}
