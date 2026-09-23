"use client"

/**
 * TRINETRA Phase 7 — Intelligence Events Feed
 * Filterable feed of canonical Earth Observation events with state badges,
 * confidence meters, and click-to-focus map integration.
 */

import React from "react"
import { EOEvent, EventState } from "@/lib/explore/intelligence-types"
import {
  Database,
  Filter,
  RefreshCw,
  MapPin,
  ShieldCheck,
  ChevronRight,
  Layers,
} from "lucide-react"

interface Props {
  events: EOEvent[]
  selectedEvent: EOEvent | null
  isLoading: boolean
  filterState: string | null
  onFilterStateChange: (state: string | null) => void
  onSelectEvent: (event: EOEvent) => void
  onRefresh: () => void
}

const STATE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CANDIDATE: { bg: "bg-amber-950/60", border: "border-amber-700/60", text: "text-amber-400" },
  OBSERVED: { bg: "bg-sky-950/60", border: "border-sky-700/60", text: "text-sky-400" },
  CORROBORATED: { bg: "bg-indigo-950/60", border: "border-indigo-700/60", text: "text-indigo-400" },
  PERSISTENT: { bg: "bg-emerald-950/60", border: "border-emerald-700/60", text: "text-emerald-400" },
  RESOLVED: { bg: "bg-slate-900/80", border: "border-slate-700/60", text: "text-slate-400" },
}

export const IntelligenceEventsFeed: React.FC<Props> = ({
  events,
  selectedEvent,
  isLoading,
  filterState,
  onFilterStateChange,
  onSelectEvent,
  onRefresh,
}) => {
  const states: Array<{ id: string | null; label: string }> = [
    { id: null, label: "All" },
    { id: "CANDIDATE", label: "Candidate" },
    { id: "OBSERVED", label: "Observed" },
    { id: "CORROBORATED", label: "Corroborated" },
    { id: "PERSISTENT", label: "Persistent" },
    { id: "RESOLVED", label: "Resolved" },
  ]

  return (
    <div className="flex flex-col gap-2.5 font-mono text-xs">
      {/* Filters & Actions Bar */}
      <div className="flex items-center justify-between gap-1 pb-1 border-b border-slate-800">
        <div className="flex items-center gap-1 overflow-x-auto scrollbar-none py-0.5">
          <Filter className="w-3 h-3 text-slate-500 shrink-0" />
          {states.map((s) => (
            <button
              key={s.label}
              onClick={() => onFilterStateChange(s.id)}
              className={`px-1.5 py-0.5 rounded text-[10px] whitespace-nowrap transition-colors ${
                filterState === s.id
                  ? "bg-orange-500/20 text-orange-300 border border-orange-500/50"
                  : "bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          title="Reload Events"
          className="p-1 rounded text-slate-400 hover:text-orange-300 hover:bg-slate-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-orange-400" : ""}`} />
        </button>
      </div>

      {/* Events List */}
      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-orange-500/20">
        {events.length === 0 && !isLoading && (
          <div className="text-center py-8 text-slate-500 text-xs">
            <Database className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            <p>No canonical events matching criteria.</p>
            <p className="text-[10px] mt-1 text-slate-600">
              Run investigations or temporal analysis to ingest observations.
            </p>
          </div>
        )}

        {events.map((evt) => {
          const isSelected = selectedEvent?.event_id === evt.event_id
          const stateTheme = STATE_COLORS[evt.state] || STATE_COLORS.OBSERVED

          return (
            <div
              key={evt.event_id}
              onClick={() => onSelectEvent(evt)}
              className={`p-2.5 rounded-lg border transition-all cursor-pointer flex flex-col gap-1.5 ${
                isSelected
                  ? "bg-slate-900 border-orange-500/70 shadow-md shadow-orange-950/40"
                  : "bg-slate-950/60 border-slate-800/80 hover:bg-slate-900/80 hover:border-slate-700"
              }`}
            >
              <div className="flex items-start justify-between gap-1.5">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span
                      className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${stateTheme.bg} ${stateTheme.border} ${stateTheme.text}`}
                    >
                      {evt.state}
                    </span>
                    <span className="text-[9px] text-orange-400 bg-orange-950/60 border border-orange-800/60 px-1 py-0.5 rounded">
                      {evt.semantic_class}
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-slate-200 line-clamp-1">{evt.title}</h4>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500 shrink-0" />
              </div>

              {/* Confidence & Supporting Stats */}
              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-900">
                <div className="flex items-center gap-1 text-emerald-400">
                  <ShieldCheck className="w-3 h-3" />
                  <span className="font-bold">{(evt.confidence * 100).toFixed(0)}%</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-slate-400">
                    <Layers className="w-2.5 h-2.5 text-indigo-400" />
                    <span>{evt.supporting_findings.length} findings</span>
                  </span>
                  <span className="text-[9px] text-slate-500">
                    {new Date(evt.last_seen).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
