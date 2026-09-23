/**
 * TRINETRA — Phase 5: Pipeline Progress Visualizer
 * Real-time 7-stage analytical pipeline execution display.
 */

import React from "react"
import { AnalysisProgress as ProgressData } from "@/lib/explore/types"
import { CheckCircle2, Loader2, AlertCircle } from "lucide-react"

interface Props {
  progress: ProgressData
  status: string
  onCancel?: () => void
}

const STAGES = [
  { key: "validating", label: "Validation" },
  { key: "resolving_assets", label: "Assets" },
  { key: "preprocessing", label: "Preprocessing" },
  { key: "inference", label: "Inference" },
  { key: "evidence", label: "Evidence" },
  { key: "reasoning", label: "Reasoning" },
  { key: "completed", label: "Finalize" },
]

export const AnalysisProgress: React.FC<Props> = ({ progress, status, onCancel }) => {
  const isFailed = status === "failed"
  const isCancelled = status === "cancelled"

  const safeProgress = progress || {}
  const stepIndex = safeProgress.step_index ?? (safeProgress as any).step_number ?? 1
  const totalSteps = safeProgress.total_steps || 7
  const percent = typeof safeProgress.percent === "number"
    ? safeProgress.percent
    : Math.min(100, Math.round((stepIndex / totalSteps) * 100))

  return (
    <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg space-y-3">
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          {status === "running" ? (
            <Loader2 className="w-3.5 h-3.5 text-orange-400 animate-spin" />
          ) : isFailed ? (
            <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          )}
          Pipeline: Stage {stepIndex} / {totalSteps}
        </span>
        <span className="font-mono text-orange-400 font-bold">{percent}%</span>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            isFailed ? "bg-rose-500" : isCancelled ? "bg-amber-500" : "bg-gradient-to-r from-orange-500 to-emerald-400"
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Stage Dots */}
      <div className="grid grid-cols-7 gap-1 text-[9px] font-mono text-center">
        {STAGES.map((s, idx) => {
          const isDone = stepIndex > idx + 1 || (stepIndex === idx + 1 && percent === 100)
          const isCurrent = stepIndex === idx + 1 && percent < 100
          return (
            <div key={s.key} className="flex flex-col items-center gap-0.5">
              <div
                className={`w-2 h-2 rounded-full transition-colors ${
                  isDone
                    ? "bg-emerald-400"
                    : isCurrent
                    ? "bg-orange-400 animate-pulse ring-2 ring-orange-400/30"
                    : "bg-slate-700"
                }`}
              />
              <span className={isCurrent ? "text-orange-300 font-bold" : isDone ? "text-slate-400" : "text-slate-600"}>
                {s.label}
              </span>
            </div>
          )
        })}
      </div>

      {/* Current Message */}
      <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
        <span className="truncate max-w-[240px]">{progress.message || "Processing..."}</span>
        {status === "running" && onCancel && (
          <button
            onClick={onCancel}
            className="text-rose-400 hover:text-rose-300 underline text-[10px] uppercase font-bold tracking-wider"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  )
}
