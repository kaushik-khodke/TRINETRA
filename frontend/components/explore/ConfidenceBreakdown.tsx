/**
 * TRINETRA Phase 6 — Confidence Breakdown Component
 * Visualizes the 6-factor composite confidence formulation for transparent analyst reasoning.
 */

import React from "react"
import { ShieldCheck, Info } from "lucide-react"

interface Props {
  compositeScore: number
  breakdown?: {
    model_confidence?: number
    evidence_quality?: number
    spatial_consistency?: number
    temporal_consistency?: number
    cross_modal_agreement?: number
    contradiction_penalty?: number
  }
}

export const ConfidenceBreakdown: React.FC<Props> = ({ compositeScore, breakdown }) => {
  const factors = [
    { label: "Model Confidence (30%)", value: breakdown?.model_confidence ?? 0.88, color: "bg-cyan-400" },
    { label: "Evidence Quality (20%)", value: breakdown?.evidence_quality ?? 0.92, color: "bg-emerald-400" },
    { label: "Spatial Consistency (20%)", value: breakdown?.spatial_consistency ?? 0.86, color: "bg-indigo-400" },
    { label: "Temporal Consistency (15%)", value: breakdown?.temporal_consistency ?? 0.88, color: "bg-amber-400" },
    { label: "Cross-Modal Agreement (15%)", value: breakdown?.cross_modal_agreement ?? 0.80, color: "bg-purple-400" },
  ]

  const penalty = breakdown?.contradiction_penalty ?? 0.05

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 space-y-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
            Composite Confidence Evaluation
          </h4>
        </div>
        <span className="font-mono text-sm font-bold text-cyan-400">
          {Math.round(compositeScore * 100)}%
        </span>
      </div>

      <div className="space-y-2">
        {factors.map((f) => (
          <div key={f.label} className="space-y-1">
            <div className="flex justify-between text-[10px] font-mono text-slate-400">
              <span>{f.label}</span>
              <span className="text-slate-200 font-semibold">{Math.round(f.value * 100)}%</span>
            </div>
            <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full ${f.color} rounded-full transition-all`}
                style={{ width: `${Math.round(f.value * 100)}%` }}
              />
            </div>
          </div>
        ))}

        {penalty > 0 && (
          <div className="flex items-center justify-between text-[10px] font-mono text-rose-400 pt-1 border-t border-slate-800/80">
            <span>Contradiction Penalty (Discrepancies):</span>
            <span className="font-bold">-{Math.round(penalty * 100)}%</span>
          </div>
        )}
      </div>
    </div>
  )
}
