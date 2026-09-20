/**
 * TRINETRA — Phase 5: Evidence Item
 * Renders individual mathematical evidence tokens with verifiable numerical fields.
 */

import React from "react"
import { CheckCircle2, Sigma, Hash, Globe2 } from "lucide-react"

interface Props {
  title: string
  type: "region" | "spectral" | "cross_modal" | "grounding" | "proof"
  data: Record<string, any>
}

export const EvidenceItem: React.FC<Props> = ({ title, type, data }) => {
  return (
    <div className="p-2.5 bg-slate-900/50 border border-slate-800/80 rounded-md text-xs font-mono space-y-1.5 hover:border-slate-700 transition-colors">
      <div className="flex items-center justify-between text-slate-300">
        <span className="font-semibold text-slate-200 flex items-center gap-1.5">
          {type === "region" && <Globe2 className="w-3.5 h-3.5 text-cyan-400" />}
          {type === "spectral" && <Sigma className="w-3.5 h-3.5 text-purple-400" />}
          {type === "proof" && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
          {type === "grounding" && <Hash className="w-3.5 h-3.5 text-amber-400" />}
          {title}
        </span>
        <span className="text-[10px] uppercase text-slate-500">{type}</span>
      </div>

      <div className="grid grid-cols-2 gap-x-2 gap-y-1 pt-1 border-t border-slate-800/60 text-[11px]">
        {Object.entries(data).map(([k, v]) => {
          if (typeof v === "object" && v !== null) return null
          const displayKey = k.replace(/_/g, " ")
          const displayVal = typeof v === "number" ? (Number.isInteger(v) ? v.toString() : v.toFixed(3)) : String(v)
          return (
            <div key={k} className="flex items-center justify-between text-slate-400">
              <span className="text-slate-500 capitalize">{displayKey}:</span>
              <span className="text-slate-200 font-bold">{displayVal}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
