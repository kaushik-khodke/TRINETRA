/**
 * TRINETRA — Phase 5: Finding Card
 * Interactive card representing an analytically verified finding.
 */

import React from "react"
import { AnalysisFinding } from "@/lib/explore/types"
import { ConfidenceBadge } from "./ConfidenceBadge"
import { MapPin, ChevronRight, Activity } from "lucide-react"

interface Props {
  finding: AnalysisFinding
  isSelected: boolean
  onSelect: (findingId: string) => void
}

export const FindingCard: React.FC<Props> = ({ finding, isSelected, onSelect }) => {
  return (
    <div
      onClick={() => onSelect(finding.finding_id)}
      className={`p-3 rounded-lg border transition-all cursor-pointer ${
        isSelected
          ? "bg-cyan-950/40 border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.15)] ring-1 ring-cyan-500/50"
          : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/90"
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider font-semibold">
            {finding.category || "OBSERVATION"}
          </span>
          <h4 className="text-sm font-semibold text-slate-100 leading-tight">
            {finding.title}
          </h4>
        </div>
        <ConfidenceBadge confidence={finding.confidence} />
      </div>

      <p className="text-xs text-slate-300 leading-relaxed line-clamp-3 mb-2.5">
        {finding.summary}
      </p>

      {finding.metric_highlight && (
        <div className="inline-flex items-center gap-1.5 px-2 py-1 bg-slate-800/80 border border-slate-700 rounded text-[11px] font-mono text-emerald-400 mb-2">
          <Activity className="w-3 h-3 text-emerald-400" />
          <span>{finding.metric_highlight}</span>
        </div>
      )}

      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60 font-mono">
        <span className="flex items-center gap-1 text-slate-400">
          <MapPin className="w-3 h-3 text-cyan-400" />
          {finding.bounding_box ? "Geo-referenced" : "Scene Level"}
        </span>
        <span className="flex items-center gap-0.5 text-cyan-400 hover:text-cyan-300 font-semibold">
          Focus on Map
          <ChevronRight className="w-3 h-3" />
        </span>
      </div>
    </div>
  )
}
