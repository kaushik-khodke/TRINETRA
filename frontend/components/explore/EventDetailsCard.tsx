"use client"

/**
 * TRINETRA Phase 7 — Event Details Card & Lifecycle Manager
 * Full inspection panel for a selected canonical EOEvent:
 * - State transition controls with reason validation
 * - Split & Merge operations
 * - Multi-dimensional confidence meter
 * - Provenance and historical transition audit trail
 */

import React, { useState } from "react"
import { EOEvent, EventState } from "@/lib/explore/intelligence-types"
import {
  ShieldCheck,
  MapPin,
  Clock,
  GitBranch,
  Merge,
  ArrowRight,
  Activity,
  Calendar,
  Layers,
  X,
  CheckCircle2,
} from "lucide-react"

interface Props {
  event: EOEvent
  allEvents?: EOEvent[]
  onClose: () => void
  onFocusOnMap: (bbox: number[]) => void
  onTransitionState: (eventId: string, newState: EventState, reason: string) => Promise<any>
  onSplitEvent: (eventId: string, childDefs: any[]) => Promise<any>
  onMergeEvents: (primaryId: string, secondaryId: string) => Promise<any>
}

const STATE_COLORS: Record<EventState, { bg: string; border: string; text: string }> = {
  CANDIDATE: { bg: "bg-amber-950/60", border: "border-amber-700/60", text: "text-amber-400" },
  OBSERVED: { bg: "bg-sky-950/60", border: "border-sky-700/60", text: "text-sky-400" },
  CORROBORATED: { bg: "bg-indigo-950/60", border: "border-indigo-700/60", text: "text-indigo-400" },
  PERSISTENT: { bg: "bg-emerald-950/60", border: "border-emerald-700/60", text: "text-emerald-400" },
  RESOLVED: { bg: "bg-slate-900/80", border: "border-slate-700/60", text: "text-slate-400" },
}

export const EventDetailsCard: React.FC<Props> = ({
  event,
  allEvents = [],
  onClose,
  onFocusOnMap,
  onTransitionState,
  onSplitEvent,
  onMergeEvents,
}) => {
  // State transition local state
  const [selectedTargetState, setSelectedTargetState] = useState<EventState | "">("")
  const [transitionReason, setTransitionReason] = useState<string>("")
  const [isTransitioning, setIsTransitioning] = useState<boolean>(false)

  // Split modal local state
  const [showSplitModal, setShowSplitModal] = useState<boolean>(false)
  const [splitCount, setSplitCount] = useState<number>(2)
  const [isSplitting, setIsSplitting] = useState<boolean>(false)

  // Merge modal local state
  const [showMergeModal, setShowMergeModal] = useState<boolean>(false)
  const [mergeSecondaryId, setMergeSecondaryId] = useState<string>("")
  const [isMerging, setIsMerging] = useState<boolean>(false)

  const stateTheme = STATE_COLORS[event.state] || STATE_COLORS.OBSERVED

  const handleStateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTargetState || !transitionReason.trim()) return
    setIsTransitioning(true)
    try {
      await onTransitionState(event.event_id, selectedTargetState as EventState, transitionReason)
      setSelectedTargetState("")
      setTransitionReason("")
    } catch {
      // Handled in state hook
    } finally {
      setIsTransitioning(false)
    }
  }

  const handleSplitSubmit = async () => {
    setIsSplitting(true)
    try {
      const childDefs = Array.from({ length: splitCount }).map((_, i) => ({
        title: `${event.title} (Segment ${i + 1})`,
        semantic_class: event.semantic_class,
        confidence: event.confidence,
        bounding_box: event.bounding_box,
      }))
      await onSplitEvent(event.event_id, childDefs)
      setShowSplitModal(false)
    } catch {
      // Handled in state hook
    } finally {
      setIsSplitting(false)
    }
  }

  const handleMergeSubmit = async () => {
    if (!mergeSecondaryId) return
    setIsMerging(true)
    try {
      await onMergeEvents(event.event_id, mergeSecondaryId)
      setShowMergeModal(false)
      setMergeSecondaryId("")
    } catch {
      // Handled in state hook
    } finally {
      setIsMerging(false)
    }
  }

  const candidateMergePartners = allEvents.filter(
    (e) => e.event_id !== event.event_id && e.state !== "RESOLVED"
  )

  return (
    <div className="flex flex-col gap-3 p-3 bg-slate-900/95 border border-slate-700/80 rounded-lg shadow-xl text-xs font-mono">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 border-b border-slate-800 pb-2">
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${stateTheme.bg} ${stateTheme.border} ${stateTheme.text}`}
            >
              {event.state}
            </span>
            <span className="text-[10px] text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-1.5 py-0.5 rounded">
              {event.semantic_class}
            </span>
            <span className="text-[9px] text-slate-500 font-mono">v{event.version}</span>
          </div>
          <h3 className="font-semibold text-sm text-slate-100">{event.title}</h3>
          <div className="text-[10px] text-slate-400">ID: {event.event_id}</div>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-200 p-1 hover:bg-slate-800 rounded transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Confidence & Spatial Quick Stats */}
      <div className="grid grid-cols-2 gap-2 bg-slate-950/70 p-2 rounded border border-slate-800/80">
        <div>
          <div className="text-[10px] text-slate-400 uppercase flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            <span>Confidence</span>
          </div>
          <div className="text-base font-bold text-emerald-300">
            {(event.confidence * 100).toFixed(1)}%
          </div>
          {/* Progress bar */}
          <div className="w-full bg-slate-800 h-1 rounded overflow-hidden mt-1">
            <div
              className="bg-emerald-400 h-full rounded transition-all"
              style={{ width: `${Math.min(100, event.confidence * 100)}%` }}
            />
          </div>
        </div>

        <div>
          <div className="text-[10px] text-slate-400 uppercase flex items-center gap-1">
            <MapPin className="w-3 h-3 text-cyan-400" />
            <span>Geospatial</span>
          </div>
          <button
            onClick={() => onFocusOnMap(event.bounding_box)}
            className="mt-1 flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-cyan-950 hover:bg-cyan-900 border border-cyan-700/60 text-cyan-300 transition-colors"
          >
            <MapPin className="w-3 h-3" />
            <span>Center on Map</span>
          </button>
        </div>
      </div>

      {/* Confidence Dimensions */}
      {event.confidence_dimensions && Object.keys(event.confidence_dimensions).length > 0 && (
        <div className="space-y-1.5 bg-slate-950/40 p-2 rounded border border-slate-800/50">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">
            Confidence Dimensions
          </span>
          <div className="grid grid-cols-2 gap-1.5 text-[10px]">
            {Object.entries(event.confidence_dimensions).map(([dim, val]) => (
              <div key={dim} className="flex justify-between items-center text-slate-300 bg-slate-900/60 px-1.5 py-0.5 rounded">
                <span className="capitalize">{dim.replace("_", " ")}</span>
                <span className="font-bold text-cyan-300">{(val * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Temporal Extent */}
      <div className="flex items-center justify-between text-[10px] text-slate-400 bg-slate-950/40 px-2 py-1 rounded border border-slate-800/50">
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3 text-slate-500" />
          <span>First: {new Date(event.first_seen).toLocaleDateString()}</span>
        </span>
        <span className="flex items-center gap-1">
          <Calendar className="w-3 h-3 text-slate-500" />
          <span>Last: {new Date(event.last_seen).toLocaleDateString()}</span>
        </span>
      </div>

      {/* Supporting Evidence Chips */}
      <div className="space-y-1">
        <span className="text-[10px] text-slate-400 uppercase flex items-center gap-1 font-semibold">
          <Layers className="w-3 h-3 text-indigo-400" />
          <span>Supporting Evidence ({event.supporting_findings.length} findings, {event.supporting_analyses.length} analyses)</span>
        </span>
        <div className="flex flex-wrap gap-1">
          {event.supporting_findings.map((fid) => (
            <span
              key={fid}
              className="text-[9px] bg-indigo-950/50 border border-indigo-800/50 text-indigo-300 px-1.5 py-0.5 rounded font-mono"
            >
              {fid}
            </span>
          ))}
          {event.supporting_analyses.map((aid) => (
            <span
              key={aid}
              className="text-[9px] bg-slate-800 border border-slate-700 text-slate-300 px-1.5 py-0.5 rounded font-mono"
            >
              {aid}
            </span>
          ))}
        </div>
      </div>

      {/* Lifecycle State Transition Action Form */}
      {event.state !== "RESOLVED" && (
        <form onSubmit={handleStateSubmit} className="space-y-2 bg-slate-950/80 p-2.5 rounded border border-slate-800">
          <div className="text-[10px] uppercase font-semibold text-slate-300 flex items-center gap-1">
            <ArrowRight className="w-3 h-3 text-cyan-400" />
            <span>Transition Event State</span>
          </div>

          <div className="flex gap-1.5">
            <select
              value={selectedTargetState}
              onChange={(e) => setSelectedTargetState(e.target.value as EventState)}
              className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs flex-1 focus:outline-none focus:border-cyan-500"
            >
              <option value="">Select target state...</option>
              {(["CANDIDATE", "OBSERVED", "CORROBORATED", "PERSISTENT", "RESOLVED"] as EventState[])
                .filter((s) => s !== event.state)
                .map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
            </select>
          </div>

          <input
            type="text"
            placeholder="Mandatory analyst justification..."
            value={transitionReason}
            onChange={(e) => setTransitionReason(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs focus:outline-none focus:border-cyan-500 placeholder:text-slate-600"
          />

          <button
            type="submit"
            disabled={!selectedTargetState || !transitionReason.trim() || isTransitioning}
            className="w-full py-1 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-slate-950 font-semibold rounded text-xs transition-colors flex items-center justify-center gap-1"
          >
            {isTransitioning ? (
              <span>Transitioning...</span>
            ) : (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Apply Transition</span>
              </>
            )}
          </button>
        </form>
      )}

      {/* Split & Merge Operation Triggers */}
      {event.state !== "RESOLVED" && (
        <div className="flex gap-2">
          <button
            onClick={() => setShowSplitModal(true)}
            className="flex-1 flex items-center justify-center gap-1 py-1 px-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[11px] transition-colors"
          >
            <GitBranch className="w-3 h-3 text-amber-400" />
            <span>Split Event</span>
          </button>
          <button
            onClick={() => setShowMergeModal(true)}
            className="flex-1 flex items-center justify-center gap-1 py-1 px-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[11px] transition-colors"
          >
            <Merge className="w-3 h-3 text-cyan-400" />
            <span>Merge Into...</span>
          </button>
        </div>
      )}

      {/* Split Modal Overlay */}
      {showSplitModal && (
        <div className="p-2.5 bg-slate-950 border border-amber-800/80 rounded space-y-2">
          <div className="text-[11px] font-bold text-amber-300 flex items-center gap-1">
            <GitBranch className="w-3.5 h-3.5" />
            <span>Split Divergent Event</span>
          </div>
          <p className="text-[10px] text-slate-400">
            This will mark current event as RESOLVED and fork into child events.
          </p>
          <div className="flex items-center gap-2">
            <label className="text-[10px] text-slate-300">Child count:</label>
            <select
              value={splitCount}
              onChange={(e) => setSplitCount(Number(e.target.value))}
              className="bg-slate-900 border border-slate-700 text-xs rounded px-2 py-0.5 text-slate-200"
            >
              <option value={2}>2 Children</option>
              <option value={3}>3 Children</option>
              <option value={4}>4 Children</option>
            </select>
          </div>
          <div className="flex justify-end gap-1.5 pt-1">
            <button
              onClick={() => setShowSplitModal(false)}
              className="px-2 py-0.5 text-[10px] text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              onClick={handleSplitSubmit}
              disabled={isSplitting}
              className="px-2 py-0.5 text-[10px] bg-amber-600 hover:bg-amber-500 font-semibold text-slate-950 rounded"
            >
              {isSplitting ? "Splitting..." : "Confirm Split"}
            </button>
          </div>
        </div>
      )}

      {/* Merge Modal Overlay */}
      {showMergeModal && (
        <div className="p-2.5 bg-slate-950 border border-cyan-800/80 rounded space-y-2">
          <div className="text-[11px] font-bold text-cyan-300 flex items-center gap-1">
            <Merge className="w-3.5 h-3.5" />
            <span>Merge Compatible Event</span>
          </div>
          <p className="text-[10px] text-slate-400">
            Select an adjacent compatible event to absorb into this primary event.
          </p>
          <select
            value={mergeSecondaryId}
            onChange={(e) => setMergeSecondaryId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 text-xs rounded px-2 py-1 text-slate-200"
          >
            <option value="">Select secondary event to absorb...</option>
            {candidateMergePartners.map((cand) => (
              <option key={cand.event_id} value={cand.event_id}>
                {cand.title} ({cand.state} • {cand.event_id})
              </option>
            ))}
          </select>
          <div className="flex justify-end gap-1.5 pt-1">
            <button
              onClick={() => setShowMergeModal(false)}
              className="px-2 py-0.5 text-[10px] text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              onClick={handleMergeSubmit}
              disabled={!mergeSecondaryId || isMerging}
              className="px-2 py-0.5 text-[10px] bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 font-semibold text-slate-950 rounded"
            >
              {isMerging ? "Merging..." : "Confirm Merge"}
            </button>
          </div>
        </div>
      )}

      {/* Audit History Timeline */}
      <div className="space-y-1.5 border-t border-slate-800/80 pt-2">
        <span className="text-[10px] uppercase font-semibold text-slate-400 flex items-center gap-1">
          <Activity className="w-3 h-3 text-cyan-400" />
          <span>Audit Trail ({event.history?.length || 0} transitions)</span>
        </span>
        <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-slate-800">
          {event.history?.map((h, idx) => (
            <div
              key={idx}
              className="p-1.5 rounded bg-slate-950/60 border border-slate-800/60 text-[10px] space-y-0.5"
            >
              <div className="flex justify-between items-center text-slate-400">
                <span className="font-semibold text-slate-300">
                  {h.from_state || "INIT"} → {h.to_state}
                </span>
                <span className="text-[9px] text-slate-500">
                  {new Date(h.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
              <p className="text-slate-400 italic font-mono text-[9px]">{h.reason}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
