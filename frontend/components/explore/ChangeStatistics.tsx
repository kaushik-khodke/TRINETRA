/**
 * TRINETRA — Phase 5: Change Statistics
 */

import React from "react"
import { Layers, Percent, Square, Shield } from "lucide-react"

interface Props {
  statistics: {
    changed_pixels?: number
    changed_area_m2?: number
    changed_area_hectares?: number
    change_ratio_pct?: number
    mean_confidence?: number
    total_aoi_pixels?: number
  }
}

export const ChangeStatistics: React.FC<Props> = ({ statistics }) => {
  if (!statistics || Object.keys(statistics).length === 0) return null

  return (
    <div className="grid grid-cols-2 gap-2 text-xs font-mono">
      <div className="p-2 bg-slate-900/60 border border-slate-800 rounded flex flex-col">
        <span className="text-[10px] text-slate-500 flex items-center gap-1 uppercase">
          <Layers className="w-3 h-3 text-orange-400" /> Changed Pixels
        </span>
        <span className="text-slate-100 font-bold text-sm mt-0.5">
          {statistics.changed_pixels?.toLocaleString() || "0"}
        </span>
      </div>

      <div className="p-2 bg-slate-900/60 border border-slate-800 rounded flex flex-col">
        <span className="text-[10px] text-slate-500 flex items-center gap-1 uppercase">
          <Square className="w-3 h-3 text-emerald-400" /> Area (ha)
        </span>
        <span className="text-slate-100 font-bold text-sm mt-0.5">
          {statistics.changed_area_hectares != null
            ? statistics.changed_area_hectares.toFixed(2)
            : "0.00"}{" "}
          ha
        </span>
      </div>

      <div className="p-2 bg-slate-900/60 border border-slate-800 rounded flex flex-col">
        <span className="text-[10px] text-slate-500 flex items-center gap-1 uppercase">
          <Percent className="w-3 h-3 text-amber-400" /> Change Ratio
        </span>
        <span className="text-slate-100 font-bold text-sm mt-0.5">
          {statistics.change_ratio_pct != null
            ? `${statistics.change_ratio_pct.toFixed(2)}%`
            : "0.0%"}
        </span>
      </div>

      <div className="p-2 bg-slate-900/60 border border-slate-800 rounded flex flex-col">
        <span className="text-[10px] text-slate-500 flex items-center gap-1 uppercase">
          <Shield className="w-3 h-3 text-purple-400" /> Confidence
        </span>
        <span className="text-slate-100 font-bold text-sm mt-0.5">
          {statistics.mean_confidence != null
            ? `${Math.round(statistics.mean_confidence * 100)}%`
            : "N/A"}
        </span>
      </div>
    </div>
  )
}
