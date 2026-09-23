"use client"

import React from "react"
import { useTemporalState } from "../../lib/explore/temporal-state"

export const ObservationDetails: React.FC = () => {
  const { selectedObservation, selectedObservationDetails, detailsLoading } =
    useTemporalState()

  if (!selectedObservation) return null

  return (
    <div className="bg-[#121620]/90 border border-orange-500/20 rounded-xl p-3 text-xs">
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/10">
        <span className="font-semibold text-orange-300 flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5 text-orange-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          Observation Details
        </span>
        <span className="text-[10px] font-mono text-slate-400">
          {selectedObservation.collection}
        </span>
      </div>

      <div className="space-y-1.5 font-mono text-[11px]">
        <div className="flex justify-between">
          <span className="text-slate-400">ID:</span>
          <span className="text-white truncate max-w-[180px]" title={selectedObservation.id}>
            {selectedObservation.id}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Date/Time:</span>
          <span className="text-orange-200">{selectedObservation.datetime}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Platform:</span>
          <span className="text-white">{selectedObservation.platform || "N/A"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Cloud Cover:</span>
          <span className="text-orange-300">
            {selectedObservation.cloud_cover !== null && selectedObservation.cloud_cover !== undefined
              ? `${selectedObservation.cloud_cover}%`
              : "0%"}
          </span>
        </div>
        {selectedObservation.bbox && selectedObservation.bbox.length === 4 && (
          <div className="flex justify-between">
            <span className="text-slate-400">BBox:</span>
            <span className="text-slate-300 text-[10px]">
              [{selectedObservation.bbox.map((n) => n.toFixed(2)).join(", ")}]
            </span>
          </div>
        )}
      </div>

      {detailsLoading ? (
        <div className="mt-2 pt-2 border-t border-white/5 text-center text-[10px] text-orange-400 animate-pulse">
          Loading detailed STAC assets...
        </div>
      ) : selectedObservationDetails?.assets ? (
        <div className="mt-2 pt-2 border-t border-white/5">
          <span className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
            Available Assets ({Object.keys(selectedObservationDetails.assets).length})
          </span>
          <div className="flex flex-wrap gap-1">
            {Object.keys(selectedObservationDetails.assets).map((key) => (
              <span
                key={key}
                className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-black/40 text-slate-300 border border-white/10"
              >
                {key}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}
