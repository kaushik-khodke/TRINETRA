"use client"

/**
 * TRINETRA Phase 7 — Persistent EO Intelligence Root Workspace
 * Integrates canonical event feeds, natural-language semantic discovery,
 * statistical anomaly detection, regional hotspot clusters, continuous monitoring,
 * and repeatable investigation templates.
 */

import React from "react"
import { useIntelligenceState } from "@/lib/explore/intelligence-state"
import { IntelligenceDashboard } from "./IntelligenceDashboard"
import { IntelligenceEventsFeed } from "./IntelligenceEventsFeed"
import { EventDetailsCard } from "./EventDetailsCard"
import { IntelligenceSearchWorkspace } from "./IntelligenceSearchWorkspace"
import { AnomalyDiscoveryPanel } from "./AnomalyDiscoveryPanel"
import { HotspotListPanel } from "./HotspotListPanel"
import { MonitoringPanel } from "./MonitoringPanel"
import { InvestigationTemplatesPanel } from "./InvestigationTemplatesPanel"
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react"

interface Props {
  availableObservationIds?: string[]
}

export const IntelligenceWorkspace: React.FC<Props> = ({
  availableObservationIds = [],
}) => {
  const {
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
    regionalSummary,
    summaryLoading,

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
    refreshTemplates,
    runTemplate,
  } = useIntelligenceState()

  const handleRefreshAll = () => {
    refreshEvents()
    refreshAnomalies()
    refreshHotspots()
    refreshMonitors()
    refreshTemplates()
  }

  return (
    <div className="flex flex-col h-full bg-slate-950/80 text-slate-100 overflow-hidden">
      {/* 1. Header & KPI Dashboard */}
      <IntelligenceDashboard
        activeSubTab={activeSubTab}
        onSelectSubTab={setActiveSubTab}
        eventsCount={events.length}
        anomaliesCount={anomalies.length}
        hotspotsCount={hotspots.length}
        monitorsCount={monitors.length}
        onRefreshAll={handleRefreshAll}
      />

      {/* 2. Reactive Status Toast Banner */}
      {statusMessage && (
        <div
          className={`flex items-center justify-between px-3 py-1.5 text-xs font-mono border-b ${
            statusMessage.type === "success"
              ? "bg-emerald-950/80 border-emerald-800/80 text-emerald-300"
              : statusMessage.type === "error"
              ? "bg-rose-950/80 border-rose-800/80 text-rose-300"
              : "bg-orange-950/80 border-orange-800/80 text-orange-300"
          }`}
        >
          <div className="flex items-center gap-1.5">
            {statusMessage.type === "success" ? (
              <CheckCircle2 className="w-3.5 h-3.5" />
            ) : statusMessage.type === "error" ? (
              <AlertCircle className="w-3.5 h-3.5" />
            ) : (
              <Info className="w-3.5 h-3.5" />
            )}
            <span>{statusMessage.text}</span>
          </div>
          <button onClick={clearMessage} className="hover:opacity-80">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 3. Main Workspace Area */}
      <div className="flex-1 p-2.5 overflow-y-auto space-y-3">
        {/* If an event is selected, render inspection card above or instead */}
        {selectedEvent && (
          <EventDetailsCard
            event={selectedEvent}
            allEvents={events}
            onClose={() => selectEvent(null)}
            onFocusOnMap={focusOnBoundingBox}
            onTransitionState={transitionEventState}
            onSplitEvent={splitEvent}
            onMergeEvents={mergeEvents}
          />
        )}

        {/* Subtab Contents */}
        {activeSubTab === "events" && (
          <IntelligenceEventsFeed
            events={events}
            selectedEvent={selectedEvent}
            isLoading={eventsLoading}
            filterState={eventFilterState}
            onFilterStateChange={setEventFilterState}
            onSelectEvent={selectEvent}
            onRefresh={refreshEvents}
          />
        )}

        {activeSubTab === "search" && (
          <IntelligenceSearchWorkspace
            searchQuery={searchQuery}
            onQueryChange={setSearchQuery}
            onExecuteSearch={executeSearch}
            results={searchResults}
            totalResults={searchTotal}
            isLoading={searchLoading}
            similarItems={similarItems}
            isSimilarLoading={similarLoading}
            onFindSimilar={findSimilar}
            onFocusOnMap={focusOnBoundingBox}
          />
        )}

        {activeSubTab === "anomalies" && (
          <AnomalyDiscoveryPanel
            anomalies={anomalies}
            selectedAnomaly={selectedAnomaly}
            isLoading={anomaliesLoading}
            onSelectAnomaly={(anom) => {
              setSelectedAnomaly(anom)
            }}
            onRefresh={refreshAnomalies}
            onFocusOnMap={focusOnBoundingBox}
          />
        )}

        {activeSubTab === "hotspots" && (
          <HotspotListPanel
            hotspots={hotspots}
            selectedHotspot={selectedHotspot}
            isLoading={hotspotsLoading}
            regionalSummary={regionalSummary}
            isSummaryLoading={summaryLoading}
            onSelectHotspot={(spot) => {
              setSelectedHotspot(spot)
              if (spot.bounding_box) focusOnBoundingBox(spot.bounding_box)
            }}
            onRefresh={refreshHotspots}
            onFocusOnMap={focusOnBoundingBox}
          />
        )}

        {activeSubTab === "monitoring" && (
          <MonitoringPanel
            monitors={monitors}
            alerts={alerts}
            isLoadingMonitors={monitorsLoading}
            isLoadingAlerts={alertsLoading}
            onToggleMonitor={toggleMonitor}
            onDeleteMonitor={deleteMonitor}
            onAcknowledgeAlert={acknowledgeAlert}
            onCreateMonitor={createMonitor}
            onRefresh={refreshMonitors}
          />
        )}

        {activeSubTab === "templates" && (
          <InvestigationTemplatesPanel
            templates={templates}
            isLoading={templatesLoading}
            availableObservationIds={availableObservationIds}
            onRunTemplate={runTemplate}
            onRefresh={refreshTemplates}
          />
        )}
      </div>
    </div>
  )
}
