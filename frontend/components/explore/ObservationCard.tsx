"use client"

import React from "react"
import { ObservationSummary } from "../../lib/explore/types"
import {
  useComparisonState,
  comparisonStateManager,
} from "../../lib/explore/comparison-state"
import { temporalStateManager } from "../../lib/explore/temporal-state"

interface ObservationCardProps {
  observation: ObservationSummary
  isSelected?: boolean
}

export const ObservationCard: React.FC<ObservationCardProps> = ({
  observation,
  isSelected = false,
}) => {
  const { observationA, observationB } = useComparisonState()

  const isA = observationA?.id === observation.id
  const isB = observationB?.id === observation.id

  const dateObj = new Date(observation.datetime)
  const formattedDate = dateObj.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })

  return (
    <div
      className={`p-3 rounded-xl border transition-all ${
        isSelected
          ? "bg-cyan-500/10 border-cyan-400 shadow-md shadow-cyan-500/20"
          : "bg-white/5 hover:bg-white/10 border-white/10"
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Thumbnail */}
        <div className="w-14 h-14 rounded-lg bg-black/40 border border-white/10 flex-shrink-0 overflow-hidden flex items-center justify-center">
          {observation.thumbnail ? (
            <img
              src={observation.thumbnail}
              alt={observation.id}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <svg className="w-6 h-6 text-cyan-400/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-1">
            <span className="font-semibold text-xs text-white truncate" title={observation.id}>
              {observation.platform || "Satellite"}
            </span>
            {observation.cloud_cover !== null && observation.cloud_cover !== undefined && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/50 text-cyan-300 border border-white/5">
                ☁ {Math.round(observation.cloud_cover)}%
              </span>
            )}
          </div>

          <p className="text-[11px] font-mono text-slate-300 mt-0.5">{formattedDate}</p>

          <p className="text-[10px] text-slate-400 truncate mt-0.5" title={observation.id}>
            {observation.id}
          </p>

          {/* Action Row */}
          <div className="flex items-center gap-1.5 mt-2">
            <button
              onClick={() => temporalStateManager.selectObservation(observation)}
              className="px-2 py-0.5 rounded bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-[10px] font-medium border border-cyan-500/30 transition"
            >
              Inspect
            </button>

            <button
              onClick={() =>
                isA
                  ? comparisonStateManager.setObservationA(null)
                  : comparisonStateManager.setObservationA(observation)
              }
              className={`px-2 py-0.5 rounded text-[10px] font-medium border transition ${
                isA
                  ? "bg-cyan-500 text-black border-cyan-400 font-bold"
                  : "bg-white/5 hover:bg-white/10 text-slate-300 border-white/10"
              }`}
            >
              {isA ? "✓ Base (A)" : "+ Set A"}
            </button>

            <button
              onClick={() =>
                isB
                  ? comparisonStateManager.setObservationB(null)
                  : comparisonStateManager.setObservationB(observation)
              }
              className={`px-2 py-0.5 rounded text-[10px] font-medium border transition ${
                isB
                  ? "bg-amber-400 text-black border-amber-300 font-bold"
                  : "bg-white/5 hover:bg-white/10 text-slate-300 border-white/10"
              }`}
            >
              {isB ? "✓ Compare (B)" : "+ Set B"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
