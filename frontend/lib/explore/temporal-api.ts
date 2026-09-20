/**
 * TRINETRA / Shanetra Explore Architecture
 * Temporal Exploration & AOI API Client
 * Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
 */

import {
  AOIValidationResult,
  ComparisonMode,
  ComparisonValidationResponse,
  ObservationDetails,
  ObservationSummary,
} from "./types"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface TemporalSearchRequestParams {
  aoi?: any
  start_datetime: string
  end_datetime: string
  collections?: string[]
  cloud_cover_max?: number
  sort?: "datetime_desc" | "datetime_asc" | "cloud_asc"
  limit?: number
}

export interface TemporalSearchResponse {
  request_id: string
  observations: ObservationSummary[]
  total: number
  has_more: boolean
  query: Record<string, any>
  execution_time_ms: number
  cache_hit: boolean
}

export class TemporalApiClient {
  /**
   * Validates an AOI geometry with server-authoritative polygon policies.
   */
  static async validateAOI(
    geometry: any,
    signal?: AbortSignal
  ): Promise<AOIValidationResult> {
    try {
      const resp = await fetch(`${API_BASE}/api/v1/explore/aoi/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ aoi: geometry }),
        signal,
      })
      if (!resp.ok) {
        const errorText = await resp.text()
        return {
          valid: false,
          errors: [`Server validation error (${resp.status}): ${errorText}`],
          warnings: [],
        }
      }
      return await resp.json()
    } catch (e: any) {
      if (e.name === "AbortError") throw e
      return {
        valid: false,
        errors: [`Network error: ${e.message}`],
        warnings: [],
      }
    }
  }

  /**
   * Queries multi-temporal observations matching AOI, date span, and cloud filters.
   */
  static async searchObservations(
    params: TemporalSearchRequestParams,
    signal?: AbortSignal
  ): Promise<TemporalSearchResponse> {
    const resp = await fetch(`${API_BASE}/api/v1/explore/observations/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
      signal,
    })

    if (!resp.ok) {
      const errorText = await resp.text()
      throw new Error(`Observation search failed (${resp.status}): ${errorText}`)
    }

    return await resp.json()
  }

  /**
   * Fetches full metadata and asset specifications for a specific observation item.
   */
  static async getObservationDetails(
    observationId: string,
    signal?: AbortSignal
  ): Promise<ObservationDetails> {
    const resp = await fetch(
      `${API_BASE}/api/v1/explore/observations/${encodeURIComponent(observationId)}`,
      {
        headers: { Accept: "application/json" },
        signal,
      }
    )

    if (!resp.ok) {
      throw new Error(`Failed to load observation details (${resp.status})`)
    }

    return await resp.json()
  }

  /**
   * Validates compatibility between two observations for dual-observation comparison.
   */
  static async validateComparison(
    observationAId: string,
    observationBId: string,
    mode: ComparisonMode = "split",
    signal?: AbortSignal
  ): Promise<ComparisonValidationResponse> {
    const resp = await fetch(`${API_BASE}/api/v1/explore/comparison/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        observation_a_id: observationAId,
        observation_b_id: observationBId,
        mode,
      }),
      signal,
    })

    if (!resp.ok) {
      return {
        compatible: false,
        warnings: [],
        errors: [`Comparison validation failed (${resp.status})`],
      }
    }

    return await resp.json()
  }
}
