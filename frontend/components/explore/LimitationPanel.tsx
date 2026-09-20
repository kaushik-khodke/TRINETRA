/**
 * TRINETRA — Phase 5: Limitation Panel
 * Displays honest caveats, resolution constraints, and analytical limitations.
 */

import React from "react"
import { AnalysisLimitation } from "@/lib/explore/types"
import { AlertTriangle, Info, AlertOctagon } from "lucide-react"

interface Props {
  limitations: AnalysisLimitation[]
}

export const LimitationPanel: React.FC<Props> = ({ limitations }) => {
  if (!limitations || limitations.length === 0) {
    return (
      <div className="p-3 bg-slate-900/40 border border-slate-800 rounded-lg text-center text-xs text-slate-400">
        No analytical limitations flagged for this run.
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 font-mono">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
        <span>Analytical Constraints & Limitations ({limitations.length})</span>
      </div>

      <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
        {limitations.map((lim, idx) => {
          const isHigh = lim.severity === "high"
          const isMed = lim.severity === "medium"

          return (
            <div
              key={lim.code || idx}
              className={`p-2.5 rounded-lg border text-xs font-mono space-y-1 ${
                isHigh
                  ? "bg-rose-950/20 border-rose-500/30 text-rose-300"
                  : isMed
                  ? "bg-amber-950/20 border-amber-500/30 text-amber-300"
                  : "bg-slate-900/60 border-slate-800 text-slate-300"
              }`}
            >
              <div className="flex items-center justify-between text-[11px] font-semibold">
                <span className="flex items-center gap-1.5">
                  {isHigh ? (
                    <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
                  ) : (
                    <Info className="w-3.5 h-3.5 text-amber-400" />
                  )}
                  {lim.code}
                </span>
                <span className="uppercase text-[9px] px-1.5 py-0.2 rounded bg-black/40 border border-white/10">
                  {lim.severity} severity
                </span>
              </div>
              <p className="text-[11px] text-slate-300 leading-snug">{lim.message}</p>
              {lim.impact && (
                <p className="text-[10px] text-slate-400 italic">
                  Impact: {lim.impact}
                </p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
