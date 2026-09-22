/**
 * TRINETRA Phase 6 — Investigation Progress Stepper
 * Displays stage-by-stage progression through deterministic investigation nodes.
 */

import React from "react"
import { InvestigationProgress as ProgressType } from "@/lib/explore/investigation-types"
import { CheckCircle2, Clock, Loader2, AlertOctagon, XCircle } from "lucide-react"

interface Props {
  progress: ProgressType
  status: string
}

const STAGES = [
  { key: "planning", label: "Planning" },
  { key: "specialists", label: "Specialists" },
  { key: "fusion", label: "Fusion" },
  { key: "semantics", label: "Semantics" },
  { key: "reasoning", label: "Reasoning" },
  { key: "completed", label: "Concluded" },
]

export const InvestigationProgress: React.FC<Props> = ({ progress, status }) => {
  const currentIdx = STAGES.findIndex((s) => s.key === progress.current_stage)

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 text-xs">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {status === "running" ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
          ) : status === "completed" ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          ) : status === "cancelled" ? (
            <XCircle className="w-3.5 h-3.5 text-amber-400" />
          ) : (
            <Clock className="w-3.5 h-3.5 text-slate-400" />
          )}
          <span className="font-semibold text-slate-200 capitalize">{status}</span>
        </div>
        <span className="font-mono text-cyan-400 font-bold">{progress.percent}%</span>
      </div>

      <p className="text-slate-400 mb-3 truncate">{progress.message}</p>

      {/* Stepper bar */}
      <div className="grid grid-cols-6 gap-1">
        {STAGES.map((s, idx) => {
          const isDone = status === "completed" || idx < currentIdx
          const isCurrent = idx === currentIdx && status === "running"

          return (
            <div key={s.key} className="flex flex-col items-center gap-1">
              <div
                className={`w-full h-1.5 rounded-full transition-all duration-300 ${
                  isDone
                    ? "bg-emerald-500 shadow-sm shadow-emerald-500/50"
                    : isCurrent
                    ? "bg-cyan-400 animate-pulse"
                    : "bg-slate-800"
                }`}
              />
              <span
                className={`text-[9px] font-mono tracking-tighter truncate ${
                  isDone
                    ? "text-slate-300"
                    : isCurrent
                    ? "text-cyan-300 font-semibold"
                    : "text-slate-600"
                }`}
              >
                {s.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
