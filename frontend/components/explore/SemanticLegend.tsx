/**
 * TRINETRA Phase 6 — Semantic Taxonomy & Confidence Legend
 * Renders standardized class palettes and confidence threshold indicators.
 */

import React from "react"
import { Palette, ShieldCheck } from "lucide-react"

export const SemanticLegend: React.FC = () => {
  const classes = [
    { name: "Built-up Expansion", color: "bg-amber-500", desc: "New structures & foundations" },
    { name: "Vegetation Loss", color: "bg-rose-500", desc: "Canopy clearance or clearing" },
    { name: "Water Expansion", color: "bg-cyan-500", desc: "Inundation or reservoir fill" },
    { name: "Road Development", color: "bg-purple-500", desc: "Linear transport corridors" },
    { name: "Agricultural Alteration", color: "bg-emerald-500", desc: "Crop cycle / harvest" },
  ]

  const confidenceTiers = [
    { label: "High Confidence (≥85%)", color: "text-emerald-400 border-emerald-500/40 bg-emerald-950/30" },
    { label: "Moderate (65–84%)", color: "text-amber-400 border-amber-500/40 bg-amber-950/30" },
    { label: "Low / Degraded (<65%)", color: "text-rose-400 border-rose-500/40 bg-rose-950/30" },
  ]

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 space-y-3 text-xs">
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <Palette className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-mono font-bold text-slate-200 uppercase tracking-wide">
            Semantic Land-Cover Taxonomy
          </span>
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {classes.map((c) => (
            <div key={c.name} className="flex items-center gap-2 p-1.5 rounded bg-slate-950/60 border border-slate-800/60">
              <span className={`w-2.5 h-2.5 rounded-full ${c.color} shrink-0`} />
              <span className="text-[11px] text-slate-300 truncate">{c.name}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="pt-2 border-t border-slate-800">
        <div className="flex items-center gap-1.5 mb-2">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="font-mono font-bold text-slate-200 uppercase tracking-wide">
            Confidence Tiers
          </span>
        </div>
        <div className="flex flex-col gap-1">
          {confidenceTiers.map((t) => (
            <div
              key={t.label}
              className={`px-2 py-1 rounded border text-[10px] font-mono ${t.color}`}
            >
              {t.label}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
