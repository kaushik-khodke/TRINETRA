/**
 * TRINETRA — Phase 5: Confidence Badge & Meter
 * Displays calibrated confidence percentage with color tiers and tooltip detail.
 */

import React from "react"
import { ShieldCheck, AlertTriangle } from "lucide-react"

interface Props {
  confidence: number // 0.0 to 1.0
  label?: string
  showBar?: boolean
  className?: string
}

export const ConfidenceBadge: React.FC<Props> = ({
  confidence,
  label = "CONFIDENCE",
  showBar = false,
  className = "",
}) => {
  const pct = Math.round(confidence * 100)

  let colorClasses = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
  let barColor = "bg-emerald-500"
  let icon = <ShieldCheck className="w-3 h-3" />

  if (pct < 50) {
    colorClasses = "bg-rose-500/10 text-rose-400 border-rose-500/30"
    barColor = "bg-rose-500"
    icon = <AlertTriangle className="w-3 h-3" />
  } else if (pct < 75) {
    colorClasses = "bg-amber-500/10 text-amber-400 border-amber-500/30"
    barColor = "bg-amber-500"
    icon = <ShieldCheck className="w-3 h-3" />
  }

  return (
    <div className={`inline-flex flex-col gap-1 ${className}`}>
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${colorClasses}`}
      >
        {icon}
        {label}: {pct}%
      </span>
      {showBar && (
        <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full ${barColor} transition-all duration-500`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
    </div>
  )
}
