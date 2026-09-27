/**
 * TRINETRA Phase 6 — Investigation Query Composer
 * Allows analysts to construct high-level scientific enquiries with pre-flight validation,
 * preset enquiry templates, and observation scope selectors.
 */

import React, { useState } from "react"
import { InvestigationValidationResponse } from "@/lib/explore/investigation-types"
import { Sparkles, Play, ShieldAlert, CheckCircle2, Clock, AlertTriangle } from "lucide-react"

interface Props {
  isSubmitting: boolean
  validation: InvestigationValidationResponse | null
  availableObservationIds: string[]
  onSubmit: (question: string, observationIds: string[]) => void
  onValidate: (question: string, observationIds: string[]) => void
}

const PRESET_QUERIES = [
  "What happened in this area?",
  "Explain the major physical surface changes.",
  "Was the change related to built-up expansion?",
  "Which detected changes are corroborated by SAR backscatter?",
  "Track persistent structural footprints across dates.",
]

export const InvestigationComposer: React.FC<Props> = ({
  isSubmitting,
  validation,
  availableObservationIds,
  onSubmit,
  onValidate,
}) => {
  const [question, setQuestion] = useState("")
  const [selectedObsIds, setSelectedObsIds] = useState<string[]>(availableObservationIds)

  const handleTextChange = (text: string) => {
    setQuestion(text)
    if (text.trim().length >= 5) {
      onValidate(text, selectedObsIds)
    }
  }

  const handleToggleObs = (oid: string) => {
    const updated = selectedObsIds.includes(oid)
      ? selectedObsIds.filter((id) => id !== oid)
      : [...selectedObsIds, oid]
    setSelectedObsIds(updated)
    if (question.trim().length >= 5) {
      onValidate(question, updated)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return
    onSubmit(question.trim(), selectedObsIds)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 bg-slate-900/90 border border-slate-800 rounded-lg p-3.5">
      <div className="flex items-center gap-1.5 text-xs text-slate-200 font-bold font-mono">
        <Sparkles className="w-4 h-4 text-orange-400" />
        <span>Semantic Earth-Observation Investigation</span>
      </div>

      <textarea
        value={question}
        onChange={(e) => handleTextChange(e.target.value)}
        placeholder="Ask a scientific investigation enquiry (e.g. 'What happened in this area? Was the change related to built-up expansion?')"
        rows={3}
        className="w-full bg-slate-950 border border-slate-800 rounded-md p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-orange-500 font-sans resize-none"
      />

      {/* Preset enquiry templates */}
      <div className="flex flex-wrap gap-1">
        {PRESET_QUERIES.map((q) => (
          <button
            type="button"
            key={q}
            onClick={() => handleTextChange(q)}
            className="px-2 py-1 rounded-full text-[10px] bg-slate-950 hover:bg-orange-950 border border-slate-800 hover:border-orange-700 text-slate-400 hover:text-orange-300 font-sans transition-all text-left truncate max-w-[280px]"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Observation Scope Selector */}
      {availableObservationIds.length > 0 && (
        <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
            Included Observations ({selectedObsIds.length}/{availableObservationIds.length})
          </span>
          <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
            {availableObservationIds.map((oid) => {
              const isChecked = selectedObsIds.includes(oid)
              return (
                <button
                  type="button"
                  key={oid}
                  onClick={() => handleToggleObs(oid)}
                  className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all ${
                    isChecked
                      ? "bg-orange-950 text-orange-300 border border-orange-700 font-semibold"
                      : "bg-slate-950 text-slate-500 border border-slate-800"
                  }`}
                >
                  {oid}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Pre-flight Validation Badge */}
      {validation && (
        <div className="p-2 rounded bg-slate-950/80 border border-slate-800 text-[11px] font-mono flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-slate-300">
            <Clock className="w-3.5 h-3.5 text-orange-400" />
            <span>Est: ~{validation.estimated_runtime_seconds}s</span>
            <span className="text-slate-600">|</span>
            <span
              className={`font-bold ${
                validation.estimated_compute_cost === "HIGH"
                  ? "text-rose-400"
                  : validation.estimated_compute_cost === "MEDIUM"
                  ? "text-amber-400"
                  : "text-emerald-400"
              }`}
            >
              {validation.estimated_compute_cost} Cost
            </span>
          </div>

          <div className="text-[10px] text-orange-400">
            {validation.planned_specialists.length} specialists planned
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={!question.trim() || isSubmitting}
        className="w-full flex items-center justify-center gap-2 py-2 bg-gradient-to-r from-orange-500 to-blue-600 hover:from-orange-400 hover:to-blue-500 disabled:opacity-50 text-slate-950 font-bold rounded-md text-xs transition-all shadow-md shadow-orange-500/20"
      >
        <Play className="w-3.5 h-3.5 fill-current" />
        <span>{isSubmitting ? "Initiating Investigation..." : "Launch Investigation"}</span>
      </button>
    </form>
  )
}
