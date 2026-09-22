/**
 * TRINETRA Phase 6 — Structured Finding Card
 * Displays an empirical finding with quantitative measurements, confidence, and linked evidence items.
 */

import React from "react"
import { StructuredFindingData } from "@/lib/explore/investigation-types"
import { ShieldCheck, Tag, AlertTriangle, ArrowUpRight } from "lucide-react"

interface Props {
  finding: StructuredFindingData
  isSelected: boolean
  onSelect: (findingId: string) => void
  onFocusEvidence?: (evidenceId: string) => void
}

export const InvestigationFindingCard: React.FC<Props> = ({
  finding,
  isSelected,
  onSelect,
  onFocusEvidence,
}) => {
  const confPct = Math.round(finding.confidence * 100)

  return (
    <div
      onClick={() => onSelect(finding.finding_id)}
      className={`p-3.5 rounded-lg border transition-all cursor-pointer ${
        isSelected
          ? "bg-cyan-950/40 border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.15)] ring-1 ring-cyan-500/50"
          : "bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-900/90"
      }`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950 border border-cyan-800 text-cyan-300 uppercase tracking-wide">
          {finding.category.replace(/_/g, " ")}
        </span>
        <div className="flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="font-mono text-xs font-semibold text-emerald-400">{confPct}%</span>
        </div>
      </div>

      <p className="text-xs text-slate-200 leading-relaxed font-medium mb-2.5">
        {finding.statement}
      </p>

      {/* Quantitative measurement values */}
      {finding.quantitative_value && Object.keys(finding.quantitative_value).length > 0 && (
        <div className="bg-slate-950/80 border border-slate-800/80 rounded p-2 mb-2.5 grid grid-cols-2 gap-2 text-[11px] font-mono">
          {Object.entries(finding.quantitative_value).map(([k, v]) => (
            <div key={k} className="flex flex-col">
              <span className="text-slate-500 text-[9px] uppercase truncate">{k.replace(/_/g, " ")}</span>
              <span className="text-cyan-400 font-bold truncate">{String(v)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Supporting Evidence IDs */}
      {finding.supporting_evidence_ids && finding.supporting_evidence_ids.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap pt-2 border-t border-slate-800/80">
          <Tag className="w-3 h-3 text-slate-500" />
          <span className="text-[10px] text-slate-500">Evidence:</span>
          {finding.supporting_evidence_ids.map((eid) => (
            <button
              key={eid}
              onClick={(e) => {
                e.stopPropagation()
                onFocusEvidence?.(eid)
              }}
              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-slate-800 hover:bg-cyan-900 border border-slate-700 hover:border-cyan-600 text-[10px] font-mono text-cyan-300 transition-colors"
            >
              <span>{eid}</span>
              <ArrowUpRight className="w-2.5 h-2.5 opacity-70" />
            </button>
          ))}
        </div>
      )}

      {finding.limitations && finding.limitations.length > 0 && (
        <div className="mt-2 text-[10px] text-amber-400/90 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />
          <span className="truncate">{finding.limitations[0]}</span>
        </div>
      )}
    </div>
  )
}
