/**
 * TRINETRA Phase 7 — Intelligence API Client
 * Comprehensive HTTP client for Persistent EO Intelligence, Semantic Search,
 * Event Lifecycle, Regional Clusters, Continuous Monitoring, and Templates.
 */

import {
  EOEvent,
  EventState,
  PersistentFinding,
  CanonicalRegion,
  RegionalSummary,
  HotspotCluster,
  AnomalyRecord,
  MonitorDefinition,
  MonitorAlert,
  InvestigationTemplate,
  IntelligenceSearchResponse,
  SimilarityResponse,
} from "./intelligence-types"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000"

export interface SearchIntelligenceParams {
  query?: string
  semantic_class?: string
  state?: string
  aoi?: any
  bounding_box?: number[]
  temporal_range?: { start_date?: string; end_date?: string }
  min_confidence?: number
  modality?: string
  page?: number
  limit?: number
}

export interface SimilarityQueryParams {
  entity_id: string
  entity_type?: "finding" | "event"
  limit?: number
  threshold?: number
}

class IntelligenceApiClient {
  private activeControllers: Map<string, AbortController> = new Map()

  private getOrSetController(key: string): AbortController {
    if (this.activeControllers.has(key)) {
      this.activeControllers.get(key)!.abort()
    }
    const controller = new AbortController()
    this.activeControllers.set(key, controller)
    return controller
  }

  // =========================================================================
  // 1. Events
  // =========================================================================

  async listEvents(
    params?: { state?: string; semantic_class?: string; region_id?: string; limit?: number },
    customSignal?: AbortSignal
  ): Promise<EOEvent[]> {
    const query = new URLSearchParams()
    if (params?.state) query.set("state", params.state)
    if (params?.semantic_class) query.set("semantic_class", params.semantic_class)
    if (params?.region_id) query.set("region_id", params.region_id)
    if (params?.limit) query.set("limit", params.limit.toString())

    const url = `${BACKEND_URL}/api/v1/explore/intelligence/events${query.toString() ? `?${query.toString()}` : ""}`
    const res = await fetch(url, { headers: { Accept: "application/json" }, signal: customSignal })
    if (!res.ok) throw new Error(`Failed to list events: ${res.statusText}`)
    return await res.json()
  }

  async getEvent(eventId: string, customSignal?: AbortSignal): Promise<EOEvent> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/intelligence/events/${eventId}`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Event '${eventId}' not found: ${res.statusText}`)
    return await res.json()
  }

  async updateEventState(
    eventId: string,
    newState: EventState,
    reason: string,
    customSignal?: AbortSignal
  ): Promise<EOEvent> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/intelligence/events/${eventId}/state`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ new_state: newState, reason }),
      signal: customSignal,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `Failed to update event state: ${res.statusText}`)
    }
    return await res.json()
  }

  async splitEvent(
    eventId: string,
    childDefinitions: any[],
    customSignal?: AbortSignal
  ): Promise<EOEvent[]> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/intelligence/events/${eventId}/split`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ child_definitions: childDefinitions }),
      signal: customSignal,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `Failed to split event: ${res.statusText}`)
    }
    return await res.json()
  }

  async mergeEvents(
    primaryEventId: string,
    secondaryEventId: string,
    customSignal?: AbortSignal
  ): Promise<EOEvent> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/intelligence/events/${primaryEventId}/merge`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ secondary_event_id: secondaryEventId }),
      signal: customSignal,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `Failed to merge events: ${res.statusText}`)
    }
    return await res.json()
  }

  // =========================================================================
  // 2. Findings
  // =========================================================================

  async listFindings(
    params?: { investigation_id?: string; semantic_class?: string; limit?: number },
    customSignal?: AbortSignal
  ): Promise<PersistentFinding[]> {
    const query = new URLSearchParams()
    if (params?.investigation_id) query.set("investigation_id", params.investigation_id)
    if (params?.semantic_class) query.set("semantic_class", params.semantic_class)
    if (params?.limit) query.set("limit", params.limit.toString())

    const url = `${BACKEND_URL}/api/v1/explore/intelligence/findings${query.toString() ? `?${query.toString()}` : ""}`
    const res = await fetch(url, { headers: { Accept: "application/json" }, signal: customSignal })
    if (!res.ok) throw new Error(`Failed to list findings: ${res.statusText}`)
    return await res.json()
  }

  async getFinding(findingId: string, customSignal?: AbortSignal): Promise<PersistentFinding> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/intelligence/findings/${findingId}`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Finding '${findingId}' not found: ${res.statusText}`)
    return await res.json()
  }

  // =========================================================================
  // 3. Search & Similarity
  // =========================================================================

  async searchIntelligence(
    params: SearchIntelligenceParams,
    customSignal?: AbortSignal
  ): Promise<IntelligenceSearchResponse> {
    const controller = this.getOrSetController("intel_search")
    const signal = customSignal || controller.signal

    const res = await fetch(`${BACKEND_URL}/api/v1/explore/intelligence/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(params),
      signal,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `Search failed: ${res.statusText}`)
    }
    return await res.json()
  }

  async findSimilar(
    params: SimilarityQueryParams,
    customSignal?: AbortSignal
  ): Promise<SimilarityResponse> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/intelligence/similar`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        entity_id: params.entity_id,
        entity_type: params.entity_type || "finding",
        limit: params.limit || 10,
        threshold: params.threshold !== undefined ? params.threshold : 0.4,
      }),
      signal: customSignal,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `Similarity query failed: ${res.statusText}`)
    }
    return await res.json()
  }

  // =========================================================================
  // 4. Regional Intelligence & Hotspots
  // =========================================================================

  async listRegions(limit: number = 50, customSignal?: AbortSignal): Promise<CanonicalRegion[]> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/intelligence/regions?limit=${limit}`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to list regions: ${res.statusText}`)
    return await res.json()
  }

  async getRegionalSummary(regionId: string, customSignal?: AbortSignal): Promise<RegionalSummary> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/intelligence/regions/${regionId}`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Regional summary failed: ${res.statusText}`)
    return await res.json()
  }

  async listHotspots(minEvents: number = 2, customSignal?: AbortSignal): Promise<HotspotCluster[]> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/intelligence/hotspots?min_events=${minEvents}`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to list hotspots: ${res.statusText}`)
    return await res.json()
  }

  // =========================================================================
  // 5. Anomalies
  // =========================================================================

  async listAnomalies(
    params?: { status?: string; region_id?: string; limit?: number },
    customSignal?: AbortSignal
  ): Promise<AnomalyRecord[]> {
    const query = new URLSearchParams()
    if (params?.status) query.set("status", params.status)
    if (params?.region_id) query.set("region_id", params.region_id)
    if (params?.limit) query.set("limit", params.limit.toString())

    const url = `${BACKEND_URL}/api/v1/explore/intelligence/anomalies${query.toString() ? `?${query.toString()}` : ""}`
    const res = await fetch(url, { headers: { Accept: "application/json" }, signal: customSignal })
    if (!res.ok) throw new Error(`Failed to list anomalies: ${res.statusText}`)
    return await res.json()
  }

  // =========================================================================
  // 6. Monitoring & Alerts
  // =========================================================================

  async listMonitors(enabledOnly: boolean = false, customSignal?: AbortSignal): Promise<MonitorDefinition[]> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/monitoring?enabled_only=${enabledOnly}`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to list monitors: ${res.statusText}`)
    return await res.json()
  }

  async getMonitor(monitorId: string, customSignal?: AbortSignal): Promise<MonitorDefinition> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/monitoring/${monitorId}`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Monitor '${monitorId}' not found: ${res.statusText}`)
    return await res.json()
  }

  async createMonitor(
    data: {
      name: string
      aoi?: any
      bounding_box?: number[]
      observation_collection?: string
      schedule_cadence?: string
      template_id?: string
      trigger_condition?: any
      cooldown_hours?: number
    },
    customSignal?: AbortSignal
  ): Promise<MonitorDefinition> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/monitoring`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(data),
      signal: customSignal,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `Failed to create monitor: ${res.statusText}`)
    }
    return await res.json()
  }

  async enableMonitor(monitorId: string, customSignal?: AbortSignal): Promise<{ monitor_id: string; enabled: boolean }> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/monitoring/${monitorId}/enable`, {
      method: "POST",
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to enable monitor: ${res.statusText}`)
    return await res.json()
  }

  async disableMonitor(monitorId: string, customSignal?: AbortSignal): Promise<{ monitor_id: string; enabled: boolean }> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/monitoring/${monitorId}/disable`, {
      method: "POST",
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to disable monitor: ${res.statusText}`)
    return await res.json()
  }

  async toggleMonitor(monitorId: string, customSignal?: AbortSignal): Promise<{ monitor_id: string; enabled: boolean }> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/intelligence/monitors/${monitorId}/toggle`, {
      method: "POST",
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to toggle monitor: ${res.statusText}`)
    return await res.json()
  }

  async deleteMonitor(monitorId: string, customSignal?: AbortSignal): Promise<{ monitor_id: string; deleted: boolean }> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/monitoring/${monitorId}`, {
      method: "DELETE",
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to delete monitor: ${res.statusText}`)
    return await res.json()
  }

  async listAlerts(
    params?: { monitor_id?: string; limit?: number },
    customSignal?: AbortSignal
  ): Promise<MonitorAlert[]> {
    const query = new URLSearchParams()
    if (params?.monitor_id) query.set("monitor_id", params.monitor_id)
    if (params?.limit) query.set("limit", params.limit.toString())

    const url = `${BACKEND_URL}/api/v1/explore/monitoring/alerts${query.toString() ? `?${query.toString()}` : ""}`
    const res = await fetch(url, { headers: { Accept: "application/json" }, signal: customSignal })
    if (!res.ok) throw new Error(`Failed to list alerts: ${res.statusText}`)
    return await res.json()
  }

  async acknowledgeAlert(alertId: string, customSignal?: AbortSignal): Promise<{ alert_id: string; acknowledged: boolean }> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/monitoring/alerts/${alertId}/acknowledge`, {
      method: "POST",
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to acknowledge alert: ${res.statusText}`)
    return await res.json()
  }

  // =========================================================================
  // 7. Investigation Templates & Execution
  // =========================================================================

  async listTemplates(customSignal?: AbortSignal): Promise<InvestigationTemplate[]> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/templates`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Failed to list templates: ${res.statusText}`)
    return await res.json()
  }

  async getTemplate(templateId: string, customSignal?: AbortSignal): Promise<InvestigationTemplate> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/templates/${templateId}`, {
      headers: { Accept: "application/json" },
      signal: customSignal,
    })
    if (!res.ok) throw new Error(`Template '${templateId}' not found: ${res.statusText}`)
    return await res.json()
  }

  async runTemplate(
    templateId: string,
    observationIds: string[],
    aoi?: any,
    customSignal?: AbortSignal
  ): Promise<{ template_id: string; status: string; investigation_id?: string }> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/templates/${templateId}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ observation_ids: observationIds, aoi }),
      signal: customSignal,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `Failed to run template: ${res.statusText}`)
    }
    return await res.json()
  }

  // =========================================================================
  // 8. Saved Searches & Regions
  // =========================================================================

  async saveSearch(name: string, query: string, filters?: any): Promise<{ search_id: string; name: string; created: boolean }> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/searches`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ name, query, filters: filters || {} }),
    })
    if (!res.ok) throw new Error(`Failed to save search: ${res.statusText}`)
    return await res.json()
  }

  async listSavedSearches(): Promise<any[]> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/searches`, {
      headers: { Accept: "application/json" },
    })
    if (!res.ok) throw new Error(`Failed to list saved searches: ${res.statusText}`)
    return await res.json()
  }

  async deleteSavedSearch(searchId: string): Promise<{ search_id: string; deleted: boolean }> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/searches/${searchId}`, {
      method: "DELETE",
      headers: { Accept: "application/json" },
    })
    if (!res.ok) throw new Error(`Failed to delete saved search: ${res.statusText}`)
    return await res.json()
  }

  async saveRegion(name: string, aoi: any, boundingBox?: number[], description?: string, tags?: string[]): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/saved-regions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ name, aoi, bounding_box: boundingBox, description: description || "", tags: tags || [] }),
    })
    if (!res.ok) throw new Error(`Failed to save region: ${res.statusText}`)
    return await res.json()
  }

  async listSavedRegions(): Promise<any[]> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/saved-regions`, {
      headers: { Accept: "application/json" },
    })
    if (!res.ok) throw new Error(`Failed to list saved regions: ${res.statusText}`)
    return await res.json()
  }

  async deleteSavedRegion(savedRegionId: string): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/api/v1/explore/saved-regions/${savedRegionId}`, {
      method: "DELETE",
      headers: { Accept: "application/json" },
    })
    if (!res.ok) throw new Error(`Failed to delete saved region: ${res.statusText}`)
    return await res.json()
  }
}

export const intelligenceApi = new IntelligenceApiClient()
