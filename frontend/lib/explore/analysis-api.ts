/**
 * TRINETRA — Phase 5: EO Analytical Intelligence Engine API Client
 * Centralized client for job creation, polling, evidence retrieval, cancellation, and validation.
 */

import {
  AnalysisRequest,
  AnalysisRun,
  AnalysisValidationResponse,
} from "./types"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000"

class AnalysisApiClient {
  private activeControllers: Map<string, AbortController> = new Map()

  private getOrSetController(key: string): AbortController {
    if (this.activeControllers.has(key)) {
      this.activeControllers.get(key)!.abort()
    }
    const controller = new AbortController()
    this.activeControllers.set(key, controller)
    return controller
  }

  async startAnalysis(request: AnalysisRequest, customSignal?: AbortSignal): Promise<AnalysisRun> {
    const controller = this.getOrSetController("start_analysis")
    const signal = customSignal || controller.signal

    const res = await fetch(`${BACKEND_URL}/api/v1/explore/analysis`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(request),
      signal,
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `Analysis request failed with status ${res.status}`)
    }

    return await res.json()
  }

  async getAnalysisRun(runId: string, customSignal?: AbortSignal): Promise<AnalysisRun> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/analysis/${runId}`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })

    if (!res.ok) {
      throw new Error(`Failed to fetch run ${runId}: ${res.statusText}`)
    }

    return await res.json()
  }

  async getEvidencePack(runId: string, customSignal?: AbortSignal): Promise<Record<string, any>> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/analysis/${runId}/evidence`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })

    if (!res.ok) {
      throw new Error(`Failed to fetch evidence for run ${runId}: ${res.statusText}`)
    }

    return await res.json()
  }

  async cancelAnalysis(runId: string): Promise<AnalysisRun> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/analysis/${runId}/cancel`, {
      method: "POST",
      headers: { Accept: "application/json" },
    })

    if (!res.ok) {
      throw new Error(`Failed to cancel run ${runId}: ${res.statusText}`)
    }

    return await res.json()
  }

  async validateAnalysis(request: AnalysisRequest): Promise<AnalysisValidationResponse> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/analysis/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(request),
    })

    if (!res.ok) {
      throw new Error(`Validation failed: ${res.statusText}`)
    }

    return await res.json()
  }

  getArtifactUrl(runId: string, filename: string): string {
    return `${BACKEND_URL}/api/v1/explore/analysis/artifacts/${runId}/${filename}`
  }
}

export const analysisApi = new AnalysisApiClient()
