/**
 * TRINETRA Phase 6 — Object Tracking & Lifecycle Panel
 * Displays cross-temporal object tracks, matching candidate states, and area evolution.
 */

import React from "react"
import { Box, ArrowRight, ShieldCheck, Sparkles } from "lucide-react"

interface Props {
  tracksData?: any[]
  onFocusTrack?: (track: any) => void
}

export const ObjectTrackPanel: React.FC<Props> = ({ tracksData, onFocusTrack }) => {
  // Fallback demo tracks if not present in evidence
  const tracks = tracksData && tracksData.length > 0 ? tracksData : [
    {
      track_id: "trk_01",
      category: "structure",
      status: "NEW_OBJECT_CANDIDATE",
      confidence: 0.89,
      area_delta_m2: "+420 m²",
      first_seen: "2026-01-10",
      notes: "Emerging rectangular foundation footprint with sharp perimeter boundaries.",
    },
    {
      track_id: "trk_02",
      category: "structure",
      status: "NEW_OBJECT_CANDIDATE",
      confidence: 0.82,
      area_delta_m2: "+380 m²",
      first_seen: "2026-01-10",
      notes: "Secondary ancillary structure adjacent to primary site.",
    },
    {
      track_id: "trk_03",
      category: "structure",
      status: "PERSISTENT",
      confidence: 0.94,
      area_delta_m2: "+0 m²",
      first_seen: "2025-06-15",
      notes: "Pre-existing compound structure unchanged across baseline and evaluation epochs.",
    },
  ]

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "NEW_OBJECT_CANDIDATE":
        return "bg-emerald-950 text-emerald-300 border-emerald-800"
      case "REMOVAL_CANDIDATE":
        return "bg-rose-950 text-rose-300 border-rose-800"
      case "EXPANDED":
        return "bg-cyan-950 text-cyan-300 border-cyan-800"
      default:
        return "bg-slate-800 text-slate-300 border-slate-700"
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Box className="w-4 h-4 text-amber-400" />
          <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
            Tracked Object Lifecycles ({tracks.length})
          </h4>
        </div>
        <span className="text-[10px] font-mono text-slate-500">IoU threshold: 0.25</span>
      </div>

      <div className="space-y-2">
        {tracks.map((trk) => (
          <div
            key={trk.track_id}
            onClick={() => onFocusTrack?.(trk)}
            className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 cursor-pointer transition-all space-y-1.5"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-cyan-400">{trk.track_id}</span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-semibold border ${getStatusBadge(
                    trk.status
                  )}`}
                >
                  {trk.status.replace(/_/g, " ")}
                </span>
              </div>
              <span className="font-mono text-xs text-slate-300 font-semibold">
                {Math.round(trk.confidence * 100)}%
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">{trk.notes}</p>

            <div className="flex items-center justify-between pt-1.5 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              <span>First detected: {trk.first_seen}</span>
              <span className="text-emerald-400 font-bold">{trk.area_delta_m2}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
