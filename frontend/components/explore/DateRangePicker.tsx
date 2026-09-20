"use client"

import React from "react"
import { useTemporalState, temporalStateManager } from "../../lib/explore/temporal-state"

export const DateRangePicker: React.FC = () => {
  const { startDate, endDate } = useTemporalState()

  return (
    <div className="flex items-center gap-2 text-xs">
      <div className="flex items-center gap-1 bg-black/40 border border-white/10 rounded px-2 py-1">
        <span className="text-slate-400 font-mono text-[10px] uppercase">From</span>
        <input
          type="date"
          value={startDate}
          onChange={(e) =>
            temporalStateManager.setDateRange(e.target.value, endDate)
          }
          className="bg-transparent text-cyan-200 focus:outline-none font-mono text-xs cursor-pointer"
        />
      </div>

      <span className="text-slate-500 font-mono">→</span>

      <div className="flex items-center gap-1 bg-black/40 border border-white/10 rounded px-2 py-1">
        <span className="text-slate-400 font-mono text-[10px] uppercase">To</span>
        <input
          type="date"
          value={endDate}
          onChange={(e) =>
            temporalStateManager.setDateRange(startDate, e.target.value)
          }
          className="bg-transparent text-cyan-200 focus:outline-none font-mono text-xs cursor-pointer"
        />
      </div>
    </div>
  )
}
