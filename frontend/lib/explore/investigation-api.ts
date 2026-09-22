/**
 * TRINETRA Phase 6 — Investigation API Client
 * Manages HTTP communication with the backend investigation endpoints,
 * supporting job creation, polling, cancellation, and analyst annotations.
 */

import {
  InvestigationRequest,
  InvestigationItem,
  InvestigationValidationResponse,
  EvidenceCardData,
  StructuredFindingData,
  TimelineMilestone,
  InvestigationArtifact,
  AnalystNote,
} from "./investigation-types"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000"

class InvestigationApiClient {
  private activeControllers: Map<string, AbortController> = new Map()

  private getOrSetController(key: string): AbortController {
    if (this.activeControllers.has(key)) {
      this.activeControllers.get(key)!.abort()
    }
    const controller = new AbortController()
    this.activeControllers.set(key, controller)
    return controller
  }

  async startInvestigation(request: InvestigationRequest, customSignal?: AbortSignal): Promise<{ investigation_id: string; status: string }> {
    const controller = this.getOrSetController("start_investigation")
    const signal = customSignal || controller.signal

    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(request),
      signal,
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `Investigation request failed with status ${res.status}`)
    }

    return await res.json()
  }

  async listInvestigations(limit: number = 50, customSignal?: AbortSignal): Promise<any[]> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations?limit=${limit}`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to list investigations: ${res.statusText}`)
    return await res.json()
  }

  async getInvestigationDetails(investigationId: string, customSignal?: AbortSignal): Promise<InvestigationItem> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to fetch investigation ${investigationId}: ${res.statusText}`)
    return await res.json()
  }

  async validateInvestigation(request: InvestigationRequest, customSignal?: AbortSignal): Promise<InvestigationValidationResponse> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(request),
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Investigation validation failed: ${res.statusText}`)
    return await res.json()
  }

  async getInvestigationEvidence(investigationId: string, customSignal?: AbortSignal): Promise<{
    investigation_id: string
    total_evidence_count: number
    evidence_cards: EvidenceCardData[]
    relationships: any[]
    clusters: any[]
    conflicts: any[]
  }> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/evidence`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to fetch evidence for ${investigationId}: ${res.statusText}`)
    return await res.json()
  }

  async getInvestigationFindings(investigationId: string, customSignal?: AbortSignal): Promise<{
    investigation_id: string
    findings: StructuredFindingData[]
  }> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/findings`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to fetch findings for ${investigationId}: ${res.statusText}`)
    return await res.json()
  }

  async getInvestigationTimeline(investigationId: string, customSignal?: AbortSignal): Promise<{
    investigation_id: string
    milestones: TimelineMilestone[]
  }> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/timeline`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to fetch timeline for ${investigationId}: ${res.statusText}`)
    return await res.json()
  }

  async getInvestigationArtifacts(investigationId: string, customSignal?: AbortSignal): Promise<InvestigationArtifact[]> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/artifacts`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to fetch artifacts for ${investigationId}: ${res.statusText}`)
    return await res.json()
  }

  async cancelInvestigation(investigationId: string): Promise<boolean> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/cancel`, {
      method: "POST",
      headers: { Accept: "application/json" },
    })
    return res.ok
  }

  async createAnalystNote(investigationId: string, note: AnalystNote): Promise<AnalystNote> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(note),
    })
    if (!res.ok) throw new Error(`Failed to add note: ${res.statusText}`)
    return await res.json()
  }

  async getAnalystNotes(investigationId: string): Promise<AnalystNote[]> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/notes`, {
      headers: { Accept: "application/json" },
    })
    if (!res.ok) return []
    return await res.json()
  }

  async deleteAnalystNote(investigationId: string, noteId: string): Promise<boolean> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/investigations/${investigationId}/notes/${noteId}`, {
      method: "DELETE",
      headers: { Accept: "application/json" },
    })
    return res.ok
  }
}

export const investigationApi = new InvestigationApiClient()
