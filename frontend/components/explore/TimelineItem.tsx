"use client"

import React from "react"
import { ObservationSummary } from "../../lib/explore/types"

interface TimelineItemProps {
  observation: ObservationSummary
  isSelected: boolean
  onClick: () => void
}

export const TimelineItem: React.FC<TimelineItemProps> = ({
  observation,
  isSelected,
  onClick,
}) => {
  const dateObj = new Date(observation.datetime)
  const dateStr = dateObj.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  })
  const yearStr = dateObj.getFullYear()

  const cloud = observation.cloud_cover
  const cloudColor =
    cloud === null || cloud === undefined
      ? "bg-slate-400"
      : cloud < 10
      ? "bg-emerald-400"
      : cloud < 30
      ? "bg-amber-400"
      : "bg-rose-400"

  return (
    <button
      onClick={onClick}
      className={`group relative flex flex-col items-center p-2 rounded-lg transition-all min-w-[76px] ${
        isSelected
          ? "bg-cyan-500/20 border-2 border-cyan-400 shadow-lg shadow-cyan-500/30 -translate-y-1"
          : "bg-white/5 hover:bg-white/10 border border-white/10 hover:border-cyan-500/40"
      }`}
    >
      {/* Cloud Indicator Dot */}
      <div className="flex items-center gap-1 mb-1">
        <span className={`w-2 h-2 rounded-full ${cloudColor}`} />
        {cloud !== null && cloud !== undefined && (
          <span className="text-[10px] font-mono text-slate-300">
            {Math.round(cloud)}%
          </span>
        )}
      </div>

      {/* Date */}
      <span className="font-semibold text-xs text-white group-hover:text-cyan-200 tracking-tight">
        {dateStr}
      </span>
      <span className="text-[10px] font-mono text-slate-400">{yearStr}</span>

      {/* Platform Chip */}
      <span className="mt-1 text-[9px] font-mono uppercase bg-black/50 px-1 rounded text-cyan-300/80 border border-white/5">
        {observation.platform?.replace("Sentinel-", "S") || "SAT"}
      </span>

      {/* Bottom marker */}
      <div
        className={`absolute -bottom-1.5 w-2 h-2 rotate-45 transition-colors ${
          isSelected ? "bg-cyan-400" : "bg-transparent"
        }`}
      />
    </button>
  )
}
