/**
 * TRINETRA Phase 6 — Contradiction & Discrepancy Panel
 * Highlights explicit cross-modal conflicts (e.g., Optical change vs SAR stability)
 * ensuring discrepancies are never averaged away.
 */

import React from "react"
import { EvidenceConflictData } from "@/lib/explore/investigation-types"
import { AlertTriangle, HelpCircle, ShieldAlert, ArrowRight } from "lucide-react"

interface Props {
  conflicts: EvidenceConflictData[]
  onSelectEvidence?: (id: string) => void
}

export const ContradictionPanel: React.FC<Props> = ({ conflicts, onSelectEvidence }) => {
  if (!conflicts || conflicts.length === 0) {
    return null
  }

  return (
    <div className="bg-amber-950/20 border border-amber-500/40 rounded-lg p-3 space-y-2.5">
      <div className="flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-400" />
        <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wide">
          Multi-Sensor Discrepancies ({conflicts.length})
        </h4>
      </div>

      <div className="space-y-2">
        {conflicts.map((c, idx) => (
          <div
            key={idx}
            className="p-2.5 rounded bg-slate-900/90 border border-amber-900/50 text-xs space-y-1.5"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] font-bold text-amber-400 uppercase">
                {c.conflict_type.replace(/_/g, " ")}
              </span>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase font-semibold bg-amber-950 text-amber-300 border border-amber-800">
                {c.severity} severity
              </span>
            </div>

            <p className="text-slate-300 text-xs leading-relaxed">{c.description}</p>

            {/* Conflicting pair link */}
            <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400 pt-1 border-t border-slate-800">
              <span
                onClick={() => onSelectEvidence?.(c.evidence_a_id)}
                className="text-orange-400 hover:underline cursor-pointer"
              >
                {c.evidence_a_id}
              </span>
              <span className="text-slate-600">vs</span>
              <span
                onClick={() => onSelectEvidence?.(c.evidence_b_id)}
                className="text-orange-400 hover:underline cursor-pointer"
              >
                {c.evidence_b_id}
              </span>
            </div>

            <div className="text-[10px] text-amber-400/90 italic bg-amber-950/30 p-1.5 rounded border border-amber-900/30">
              <strong>Resolution:</strong> {c.resolution_strategy}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
