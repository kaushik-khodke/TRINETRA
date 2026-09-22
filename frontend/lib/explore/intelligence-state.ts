/**
 * TRINETRA Phase 7 — Intelligence State Hook & Reactive State Manager
 * Coordinates persistent intelligence views, event lifecycle mutations,
 * semantic queries, similarity evaluation, anomaly discovery, and real-time monitoring.
 */

import { useState, useEffect, useCallback, useRef } from "react"
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
  IntelligenceSearchResultItem,
  SimilarityResultItem,
} from "./intelligence-types"
import { intelligenceApi } from "./intelligence-api"
import { globeCommandBus } from "./globe-command-bus"

export type IntelSubTab = "events" | "search" | "anomalies" | "hotspots" | "monitoring" | "templates"

export function useIntelligenceState() {
  const [activeSubTab, setActiveSubTab] = useState<IntelSubTab>("events")

  // 1. Events State
  const [events, setEvents] = useState<EOEvent[]>([])
  const [selectedEvent, setSelectedEvent] = useState<EOEvent | null>(null)
  const [eventsLoading, setEventsLoading] = useState<boolean>(false)
  const [eventFilterState, setEventFilterState] = useState<string | null>(null)
  const [eventFilterClass, setEventFilterClass] = useState<string | null>(null)

  // 2. Search & Similarity State
  const [searchQuery, setSearchQuery] = useState<string>("")
  const [searchResults, setSearchResults] = useState<IntelligenceSearchResultItem[]>([])
  const [searchTotal, setSearchTotal] = useState<number>(0)
  const [searchLoading, setSearchLoading] = useState<boolean>(false)
  const [selectedResult, setSelectedResult] = useState<IntelligenceSearchResultItem | null>(null)
  const [similarItems, setSimilarItems] = useState<SimilarityResultItem[]>([])
  const [similarLoading, setSimilarLoading] = useState<boolean>(false)

  // 3. Anomalies State
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([])
  const [selectedAnomaly, setSelectedAnomaly] = useState<AnomalyRecord | null>(null)
  const [anomaliesLoading, setAnomaliesLoading] = useState<boolean>(false)

  // 4. Hotspots & Regional State
  const [hotspots, setHotspots] = useState<HotspotCluster[]>([])
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotCluster | null>(null)
  const [hotspotsLoading, setHotspotsLoading] = useState<boolean>(false)
  const [regions, setRegions] = useState<CanonicalRegion[]>([])
  const [regionalSummary, setRegionalSummary] = useState<RegionalSummary | null>(null)
  const [summaryLoading, setSummaryLoading] = useState<boolean>(false)

  // 5. Monitoring & Alerts State
  const [monitors, setMonitors] = useState<MonitorDefinition[]>([])
  const [alerts, setAlerts] = useState<MonitorAlert[]>([])
  const [monitorsLoading, setMonitorsLoading] = useState<boolean>(false)
  const [alertsLoading, setAlertsLoading] = useState<boolean>(false)

  // 6. Templates State
  const [templates, setTemplates] = useState<InvestigationTemplate[]>([])
  const [templatesLoading, setTemplatesLoading] = useState<boolean>(false)
  const [selectedTemplate, setSelectedTemplate] = useState<InvestigationTemplate | null>(null)

  // Feedback / Error
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null)

  const clearMessage = useCallback(() => setStatusMessage(null), [])

  // -------------------------------------------------------------------------
  // Focus helper: flies globe to bbox
  // -------------------------------------------------------------------------
  const focusOnBoundingBox = useCallback((bbox?: number[]) => {
    if (!bbox || bbox.length < 4) return
    const minLon = bbox[0]
    const minLat = bbox[1]
    const maxLon = bbox[2]
    const maxLat = bbox[3]

    const centerLat = (minLat + maxLat) / 2
    const centerLon = (minLon + maxLon) / 2

    // Estimate zoom based on bbox delta
    const delta = Math.max(Math.abs(maxLat - minLat), Math.abs(maxLon - minLon))
    let zoom = 12
    if (delta > 2.0) zoom = 8
    else if (delta > 0.5) zoom = 10
    else if (delta > 0.1) zoom = 13
    else zoom = 15

    globeCommandBus.dispatch({
      type: "FLY_TO",
      latitude: centerLat,
      longitude: centerLon,
      zoom,
      duration: 1.5,
    })
  }, [])

  // -------------------------------------------------------------------------
  // Event Loaders & Actions
  // -------------------------------------------------------------------------
  const refreshEvents = useCallback(async () => {
    setEventsLoading(true)
    try {
      const data = await intelligenceApi.listEvents({
        state: eventFilterState || undefined,
        semantic_class: eventFilterClass || undefined,
        limit: 50,
      })
      setEvents(data)
    } catch (e: any) {
      console.warn("Failed to load events", e)
      setStatusMessage({ type: "error", text: e.message || "Failed to load events" })
    } finally {
      setEventsLoading(false)
    }
  }, [eventFilterState, eventFilterClass])

  const selectEvent = useCallback((evt: EOEvent | null) => {
    setSelectedEvent(evt)
    if (evt?.bounding_box) {
      focusOnBoundingBox(evt.bounding_box)
    }
  }, [focusOnBoundingBox])

  const transitionEventState = useCallback(async (eventId: string, targetState: EventState, reason: string) => {
    try {
      const updated = await intelligenceApi.updateEventState(eventId, targetState, reason)
      setEvents((prev) => prev.map((e) => (e.event_id === eventId ? updated : e)))
      if (selectedEvent?.event_id === eventId) {
        setSelectedEvent(updated)
      }
      setStatusMessage({ type: "success", text: `Event updated to ${targetState}` })
      return updated
    } catch (e: any) {
      setStatusMessage({ type: "error", text: e.message || "State transition rejected" })
      throw e
    }
  }, [selectedEvent])

  const splitEvent = useCallback(async (eventId: string, childDefs: any[]) => {
    try {
      const children = await intelligenceApi.splitEvent(eventId, childDefs)
      await refreshEvents()
      setStatusMessage({ type: "success", text: `Event split into ${children.length} child events` })
      return children
    } catch (e: any) {
      setStatusMessage({ type: "error", text: e.message || "Failed to split event" })
      throw e
    }
  }, [refreshEvents])

  const mergeEvents = useCallback(async (primaryId: string, secondaryId: string) => {
    try {
      const merged = await intelligenceApi.mergeEvents(primaryId, secondaryId)
      await refreshEvents()
      setSelectedEvent(merged)
      setStatusMessage({ type: "success", text: `Event ${secondaryId} merged into ${primaryId}` })
      return merged
    } catch (e: any) {
      setStatusMessage({ type: "error", text: e.message || "Failed to merge events" })
      throw e
    }
  }, [refreshEvents])

  // -------------------------------------------------------------------------
  // Search & Similarity Actions
  // -------------------------------------------------------------------------
  const executeSearch = useCallback(async (overrideQuery?: string) => {
    const q = overrideQuery !== undefined ? overrideQuery : searchQuery
    setSearchLoading(true)
    try {
      const res = await intelligenceApi.searchIntelligence({
        query: q || undefined,
        limit: 25,
      })
      setSearchResults(res.results || [])
      setSearchTotal(res.total || 0)
    } catch (e: any) {
      console.warn("Search failed", e)
      setStatusMessage({ type: "error", text: e.message || "Search failed" })
    } finally {
      setSearchLoading(false)
    }
  }, [searchQuery])

  const findSimilar = useCallback(async (entityId: string, entityType: "finding" | "event" = "finding") => {
    setSimilarLoading(true)
    try {
      const res = await intelligenceApi.findSimilar({ entity_id: entityId, entity_type: entityType, limit: 8 })
      setSimilarItems(res.matches || [])
    } catch (e: any) {
      console.warn("Similarity evaluation failed", e)
    } finally {
      setSimilarLoading(false)
    }
  }, [])

  // -------------------------------------------------------------------------
  // Anomalies & Hotspots Loaders
  // -------------------------------------------------------------------------
  const refreshAnomalies = useCallback(async () => {
    setAnomaliesLoading(true)
    try {
      const data = await intelligenceApi.listAnomalies({ limit: 40 })
      setAnomalies(data)
    } catch (e: any) {
      console.warn("Failed to load anomalies", e)
    } finally {
      setAnomaliesLoading(false)
    }
  }, [])

  const refreshHotspots = useCallback(async () => {
    setHotspotsLoading(true)
    try {
      const data = await intelligenceApi.listHotspots(2)
      setHotspots(data)
    } catch (e: any) {
      console.warn("Failed to load hotspots", e)
    } finally {
      setHotspotsLoading(false)
    }
  }, [])

  const loadRegionalSummary = useCallback(async (regionId: string) => {
    setSummaryLoading(true)
    try {
      const sum = await intelligenceApi.getRegionalSummary(regionId)
      setRegionalSummary(sum)
    } catch (e: any) {
      console.warn("Failed to load regional summary", e)
    } finally {
      setSummaryLoading(false)
    }
  }, [])

  // -------------------------------------------------------------------------
  // Monitoring & Alerts
  // -------------------------------------------------------------------------
  const refreshMonitors = useCallback(async () => {
    setMonitorsLoading(true)
    try {
      const [mons, alrts] = await Promise.all([
        intelligenceApi.listMonitors(),
        intelligenceApi.listAlerts({ limit: 30 }),
      ])
      setMonitors(mons)
      setAlerts(alrts)
    } catch (e: any) {
      console.warn("Failed to load monitors/alerts", e)
    } finally {
      setMonitorsLoading(false)
    }
  }, [])

  const toggleMonitor = useCallback(async (monitorId: string) => {
    try {
      const res = await intelligenceApi.toggleMonitor(monitorId)
      setMonitors((prev) =>
        prev.map((m) => (m.monitor_id === monitorId ? { ...m, enabled: res.enabled } : m))
      )
      setStatusMessage({
        type: "success",
        text: `Monitor ${res.enabled ? "enabled" : "disabled"}`,
      })
    } catch (e: any) {
      setStatusMessage({ type: "error", text: e.message || "Failed to toggle monitor" })
    }
  }, [])

  const acknowledgeAlert = useCallback(async (alertId: string) => {
    try {
      await intelligenceApi.acknowledgeAlert(alertId)
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? { ...a, acknowledged: true } : a))
      )
      setStatusMessage({ type: "success", text: "Alert acknowledged" })
    } catch (e: any) {
      setStatusMessage({ type: "error", text: e.message || "Failed to acknowledge alert" })
    }
  }, [])

  const createMonitor = useCallback(async (data: any) => {
    try {
      const created = await intelligenceApi.createMonitor(data)
      setMonitors((prev) => [created, ...prev])
      setStatusMessage({ type: "success", text: `Monitor '${created.name}' created successfully` })
      return created
    } catch (e: any) {
      setStatusMessage({ type: "error", text: e.message || "Failed to create monitor" })
      throw e
    }
  }, [])

  const deleteMonitor = useCallback(async (monitorId: string) => {
    try {
      await intelligenceApi.deleteMonitor(monitorId)
      setMonitors((prev) => prev.filter((m) => m.monitor_id !== monitorId))
      setStatusMessage({ type: "info", text: "Monitor removed" })
    } catch (e: any) {
      setStatusMessage({ type: "error", text: e.message || "Failed to delete monitor" })
    }
  }, [])

  // -------------------------------------------------------------------------
  // Templates
  // -------------------------------------------------------------------------
  const refreshTemplates = useCallback(async () => {
    setTemplatesLoading(true)
    try {
      const list = await intelligenceApi.listTemplates()
      setTemplates(list)
    } catch (e: any) {
      console.warn("Failed to load templates", e)
    } finally {
      setTemplatesLoading(false)
    }
  }, [])

  const runTemplate = useCallback(async (templateId: string, observationIds: string[], aoi?: any) => {
    try {
      const res = await intelligenceApi.runTemplate(templateId, observationIds, aoi)
      setStatusMessage({ type: "success", text: `Template job initiated: ${res.investigation_id || "running"}` })
      return res
    } catch (e: any) {
      setStatusMessage({ type: "error", text: e.message || "Failed to run template" })
      throw e
    }
  }, [])

  // Initial load based on subtab
  useEffect(() => {
    if (activeSubTab === "events") {
      refreshEvents()
    } else if (activeSubTab === "anomalies") {
      refreshAnomalies()
    } else if (activeSubTab === "hotspots") {
      refreshHotspots()
    } else if (activeSubTab === "monitoring") {
      refreshMonitors()
    } else if (activeSubTab === "templates") {
      refreshTemplates()
    }
  }, [activeSubTab, refreshEvents, refreshAnomalies, refreshHotspots, refreshMonitors, refreshTemplates])

  return {
    // Nav
    activeSubTab,
    setActiveSubTab,
    statusMessage,
    clearMessage,
    focusOnBoundingBox,

    // Events
    events,
    selectedEvent,
    eventsLoading,
    eventFilterState,
    setEventFilterState,
    eventFilterClass,
    setEventFilterClass,
    refreshEvents,
    selectEvent,
    transitionEventState,
    splitEvent,
    mergeEvents,

    // Search & Sim
    searchQuery,
    setSearchQuery,
    searchResults,
    searchTotal,
    searchLoading,
    selectedResult,
    setSelectedResult,
    similarItems,
    similarLoading,
    executeSearch,
    findSimilar,

    // Anomalies
    anomalies,
    selectedAnomaly,
    setSelectedAnomaly,
    anomaliesLoading,
    refreshAnomalies,

    // Hotspots
    hotspots,
    selectedHotspot,
    setSelectedHotspot,
    hotspotsLoading,
    refreshHotspots,
    regions,
    regionalSummary,
    summaryLoading,
    loadRegionalSummary,

    // Monitors
    monitors,
    alerts,
    monitorsLoading,
    alertsLoading,
    refreshMonitors,
    toggleMonitor,
    acknowledgeAlert,
    createMonitor,
    deleteMonitor,

    // Templates
    templates,
    templatesLoading,
    selectedTemplate,
    setSelectedTemplate,
    refreshTemplates,
    runTemplate,
  }
}
