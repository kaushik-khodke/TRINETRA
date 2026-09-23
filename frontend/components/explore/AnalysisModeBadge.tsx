/**
 * TRINETRA — Phase 5: Analysis Mode Badge
 */

import React from "react"
import { AnalysisMode } from "@/lib/explore/types"
import { Layers, Radio, Image as ImageIcon } from "lucide-react"

interface Props {
  mode: AnalysisMode | string
  className?: string
}

export const AnalysisModeBadge: React.FC<Props> = ({ mode, className = "" }) => {
  switch (mode) {
    case "BI_TEMPORAL":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 ${className}`}
        >
          <Layers className="w-3 h-3" />
          BI-TEMPORAL
        </span>
      )
    case "SAR_OPTICAL":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-orange-500/10 text-orange-400 border border-orange-500/30 ${className}`}
        >
          <Radio className="w-3 h-3" />
          SAR + OPTICAL
        </span>
      )
    case "SINGLE_IMAGE":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-purple-500/10 text-purple-400 border border-purple-500/30 ${className}`}
        >
          <ImageIcon className="w-3 h-3" />
          SINGLE IMAGE
        </span>
      )
    default:
      return (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700 ${className}`}
        >
          {mode}
        </span>
      )
  }
}
