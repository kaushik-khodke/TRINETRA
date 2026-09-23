"use client"

import React from "react"
import { DateRangePicker } from "./DateRangePicker"
import {
  useTemporalState,
  temporalStateManager,
} from "../../lib/explore/temporal-state"

export const TemporalToolbar: React.FC = () => {
  const { cloudCoverMax, collections, loading, observations } = useTemporalState()

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 bg-[#121620]/90 backdrop-blur-md border border-orange-500/20 rounded-lg p-2.5 shadow-xl text-xs">
      <div className="flex flex-wrap items-center gap-3">
        {/* Date Range */}
        <DateRangePicker />

        {/* Cloud Cover Slider */}
        <div className="flex items-center gap-2 bg-black/40 border border-white/10 rounded px-2.5 py-1">
          <span className="text-slate-400 text-[10px] uppercase font-mono">
            Cloud Max: <span className="text-orange-300 font-bold">{cloudCoverMax}%</span>
          </span>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={cloudCoverMax}
            onChange={(e) =>
              temporalStateManager.setCloudCoverMax(Number(e.target.value))
            }
            className="w-16 h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-orange-400"
          />
        </div>

        {/* Collection Selector */}
        <div className="flex items-center gap-1.5 bg-black/40 border border-white/10 rounded px-2 py-1">
          <span className="text-slate-400 text-[10px] uppercase font-mono">Mission:</span>
          <select
            value={collections[0] || "sentinel-2-l2a"}
            onChange={(e) => temporalStateManager.setCollections([e.target.value])}
            className="bg-transparent text-orange-200 text-xs focus:outline-none cursor-pointer font-mono"
          >
            <option value="sentinel-2-l2a" className="bg-[#121620] text-orange-200">
              Sentinel-2 (Optical L2A)
            </option>
            <option value="sentinel-1-grd" className="bg-[#121620] text-orange-200">
              Sentinel-1 (Radar SAR)
            </option>
          </select>
        </div>
      </div>

      {/* Action: Search */}
      <div className="flex items-center gap-3">
        {observations.length > 0 && (
          <span className="text-slate-400 font-mono text-[11px]">
            <strong className="text-orange-300">{observations.length}</strong> acquisitions
          </span>
        )}

        <button
          onClick={() => temporalStateManager.search()}
          disabled={loading}
          className="px-3 py-1.5 rounded-md bg-gradient-to-r from-orange-500 to-blue-600 hover:from-orange-400 hover:to-blue-500 text-black font-semibold tracking-wide transition shadow-lg shadow-orange-500/20 disabled:opacity-50 flex items-center gap-1.5"
        >
          {loading ? (
            <>
              <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Searching...</span>
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <span>Discover</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}
