/**
 * TRINETRA Phase 6 — Findings Dashboard
 * Central analyst reasoning surface combining narrative conclusion, primary hypothesis,
 * non-causal attribution boundaries, and structured findings.
 */

import React from "react"
import { InvestigationItem, StructuredFindingData } from "@/lib/explore/investigation-types"
import { InvestigationFindingCard } from "./InvestigationFindingCard"
import { HypothesisCard } from "./HypothesisCard"
import { ConfidenceBreakdown } from "./ConfidenceBreakdown"
import { ContradictionPanel } from "./ContradictionPanel"
import { Sparkles, AlertCircle, ShieldAlert, CheckCircle2, FileText } from "lucide-react"

interface Props {
  investigation: InvestigationItem
  selectedFindingId: string | null
  onSelectFinding: (findingId: string) => void
  onFocusEvidence?: (evidenceId: string) => void
}

export const FindingsDashboard: React.FC<Props> = ({
  investigation,
  selectedFindingId,
  onSelectFinding,
  onFocusEvidence,
}) => {
  const conclusion = investigation.conclusion
  const hypotheses = investigation.hypotheses || []
  const findings = investigation.findings || []
  const conflicts = investigation.conflicts || []

  return (
    <div className="space-y-4">
      {/* Executive Summary & Attribution Boundary */}
      {conclusion && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
              Executive Investigation Synthesis
            </h3>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            {conclusion.summary}
          </p>

          {/* Strict Non-Causal Attribution Boundary Alert */}
          {conclusion.attribution_boundary && (
            <div className="p-3 rounded bg-amber-950/30 border-l-4 border-amber-500 text-xs text-amber-200/90 space-y-1">
              <div className="flex items-center gap-1.5 font-bold font-mono text-[11px] text-amber-300 uppercase">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                <span>Governance Attribution Boundary</span>
              </div>
              <p className="text-[11px] leading-relaxed text-amber-100/80">
                {conclusion.attribution_boundary}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Primary and Alternative Hypotheses */}
      {hypotheses.length > 0 && (
        <div className="space-y-2">
          {hypotheses.map((hyp, idx) => (
            <HypothesisCard
              key={hyp.hypothesis_id || idx}
              hypothesis={hyp}
              isPrimary={idx === 0}
            />
          ))}
        </div>
      )}

      {/* Multi-Sensor Conflicts / Discrepancies */}
      {conflicts.length > 0 && (
        <ContradictionPanel conflicts={conflicts} onSelectEvidence={onFocusEvidence} />
      )}

      {/* Confidence Breakdown Formulation */}
      {conclusion && (
        <ConfidenceBreakdown
          compositeScore={conclusion.confidence}
          breakdown={
            hypotheses[0]?.confidence_breakdown || {
              model_confidence: 0.88,
              evidence_quality: 0.92,
              spatial_consistency: 0.86,
              temporal_consistency: 0.88,
              cross_modal_agreement: 0.80,
              contradiction_penalty: conflicts.length > 0 ? 0.05 : 0.0,
            }
          }
        />
      )}

      {/* Structured Empirical Findings */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <FileText className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
              Empirical Findings ({findings.length})
            </h4>
          </div>
          <span className="text-[10px] font-mono text-slate-500">Grounded in Evidence IDs</span>
        </div>

        {findings.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-500 font-mono">
            No structured findings available for this run.
          </div>
        ) : (
          findings.map((f) => (
            <InvestigationFindingCard
              key={f.finding_id}
              finding={f}
              isSelected={f.finding_id === selectedFindingId}
              onSelect={onSelectFinding}
              onFocusEvidence={onFocusEvidence}
            />
          ))
        )}
      </div>

      {/* Recommendations */}
      {conclusion?.recommendations && conclusion.recommendations.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 space-y-2">
          <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide font-mono">
            Analyst Follow-Up Recommendations
          </h4>
          <ul className="space-y-1 text-xs text-slate-400 list-disc list-inside">
            {conclusion.recommendations.map((rec, idx) => (
              <li key={idx} className="leading-relaxed">
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
