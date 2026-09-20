/**
 * TRINETRA — Phase 5: Change Legend Component
 */

import React from "react"

export const ChangeLegend: React.FC = () => {
  return (
    <div className="p-2.5 bg-slate-900/60 border border-slate-800 rounded-lg text-xs font-mono space-y-1.5">
      <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
        Change Detection Colormap
      </span>
      <div className="flex items-center gap-2">
        <div className="h-2 flex-1 rounded bg-gradient-to-r from-blue-900 via-yellow-400 to-rose-600" />
      </div>
      <div className="flex items-center justify-between text-[10px] text-slate-400">
        <span>0.0 (Unchanged)</span>
        <span>0.5 (Moderate)</span>
        <span>1.0 (High Delta)</span>
      </div>
    </div>
  )
}
