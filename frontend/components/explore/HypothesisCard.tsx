/**
 * TRINETRA Phase 6 — Semantic Hypothesis Card
 * Displays interpreted event hypotheses, confidence breakdown, and runner-up alternative explanations.
 */

import React from "react"
import { SemanticHypothesisData } from "@/lib/explore/investigation-types"
import { Sparkles, HelpCircle, Layers, CheckCircle2 } from "lucide-react"

interface Props {
  hypothesis: SemanticHypothesisData
  isPrimary?: boolean
}

export const HypothesisCard: React.FC<Props> = ({ hypothesis, isPrimary = false }) => {
  const confPct = Math.round(hypothesis.confidence * 100)

  return (
    <div
      className={`rounded-lg border p-4 transition-all ${
        isPrimary
          ? "bg-gradient-to-b from-cyan-950/40 to-slate-900/90 border-cyan-500/60 shadow-lg shadow-cyan-950/30"
          : "bg-slate-900/80 border-slate-800"
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <div
            className={`p-1.5 rounded-md ${
              isPrimary ? "bg-cyan-500/20 text-cyan-400" : "bg-slate-800 text-slate-400"
            }`}
          >
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-bold">
                {isPrimary ? "Primary Hypothesis" : "Alternative Hypothesis"}
              </span>
              {isPrimary && (
                <span className="px-1.5 py-0.2 rounded text-[9px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">
                  ACCEPTED
                </span>
              )}
            </div>
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-tight">
              {hypothesis.semantic_class.replace(/_/g, " ")}
            </h3>
          </div>
        </div>

        <div className="flex flex-col items-end">
          <span className="text-base font-bold font-mono text-cyan-400">{confPct}%</span>
          <span className="text-[9px] text-slate-500">Posterior</span>
        </div>
      </div>

      <p className="text-xs text-slate-300 leading-relaxed mb-3">
        {hypothesis.description}
      </p>

      {/* Alternative hypotheses */}
      {hypothesis.alternative_hypotheses && hypothesis.alternative_hypotheses.length > 0 && (
        <div className="pt-2.5 border-t border-slate-800/80">
          <div className="flex items-center gap-1 text-[10px] font-mono text-slate-400 mb-1.5">
            <Layers className="w-3 h-3 text-slate-500" />
            <span>Alternative Interpretations Evaluated:</span>
          </div>
          <div className="space-y-1.5">
            {hypothesis.alternative_hypotheses.map((alt) => (
              <div
                key={alt.semantic_class}
                className="flex items-center justify-between text-[11px] bg-slate-950/60 px-2 py-1 rounded border border-slate-800/50"
              >
                <span className="text-slate-300 capitalize">
                  {alt.semantic_class.replace(/_/g, " ").toLowerCase()}
                </span>
                <span className="font-mono text-slate-400 font-medium">
                  {Math.round(alt.probability * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
