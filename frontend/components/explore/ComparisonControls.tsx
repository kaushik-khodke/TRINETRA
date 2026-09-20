"use client"

import React from "react"
import {
  useComparisonState,
  comparisonStateManager,
  ActiveComparisonMode,
} from "../../lib/explore/comparison-state"

export const ComparisonControls: React.FC = () => {
  const {
    mode,
    observationA,
    observationB,
    splitPosition,
    opacityA,
    opacityB,
    validation,
    validating,
  } = useComparisonState()

  const hasPair = !!observationA && !!observationB

  return (
    <div className="bg-[#121620]/95 backdrop-blur-md border border-cyan-500/30 rounded-xl p-3 shadow-2xl space-y-2.5 text-xs">
      {/* Header & Pair Summary */}
      <div className="flex items-center justify-between">
        <span className="font-semibold tracking-wider uppercase text-cyan-400 flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="3" width="20" height="18" rx="2" />
            <line x1="12" y1="3" x2="12" y2="21" />
          </svg>
          Observation Comparison
        </span>

        {mode !== "none" && (
          <button
            onClick={() => comparisonStateManager.setMode("none")}
            className="text-[10px] text-slate-400 hover:text-rose-400 transition"
          >
            Exit Compare
          </button>
        )}
      </div>

      {/* Observation Slots A & B */}
      <div className="flex items-center gap-2">
        {/* Slot A */}
        <div
          className={`flex-1 p-2 rounded-lg border ${
            observationA
              ? "bg-cyan-950/40 border-cyan-400/40 text-cyan-200"
              : "bg-white/5 border-dashed border-white/20 text-slate-400"
          }`}
        >
          <div className="flex items-center justify-between text-[10px] font-mono mb-0.5">
            <span className="text-cyan-400 font-bold uppercase">Base (A)</span>
            {observationA && (
              <button
                onClick={() => comparisonStateManager.setObservationA(null)}
                className="text-slate-400 hover:text-rose-400"
              >
                ✕
              </button>
            )}
          </div>
          <p className="truncate font-semibold text-white text-[11px]">
            {observationA ? observationA.datetime.split("T")[0] : "Select observation A"}
          </p>
          <p className="text-[9px] text-slate-400 truncate">
            {observationA ? observationA.id : "Choose from timeline"}
          </p>
        </div>

        {/* Swap Button */}
        <button
          onClick={() => comparisonStateManager.swapObservations()}
          disabled={!hasPair}
          className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 disabled:opacity-30 transition border border-white/10"
          title="Swap Observation A and B"
        >
          ⇄
        </button>

        {/* Slot B */}
        <div
          className={`flex-1 p-2 rounded-lg border ${
            observationB
              ? "bg-amber-950/40 border-amber-400/40 text-amber-200"
              : "bg-white/5 border-dashed border-white/20 text-slate-400"
          }`}
        >
          <div className="flex items-center justify-between text-[10px] font-mono mb-0.5">
            <span className="text-amber-400 font-bold uppercase">Compare (B)</span>
            {observationB && (
              <button
                onClick={() => comparisonStateManager.setObservationB(null)}
                className="text-slate-400 hover:text-rose-400"
              >
                ✕
              </button>
            )}
          </div>
          <p className="truncate font-semibold text-white text-[11px]">
            {observationB ? observationB.datetime.split("T")[0] : "Select observation B"}
          </p>
          <p className="text-[9px] text-slate-400 truncate">
            {observationB ? observationB.id : "Choose from timeline"}
          </p>
        </div>
      </div>

      {/* Validation / Compatibility Badge */}
      {validating ? (
        <div className="text-[10px] text-cyan-400 animate-pulse font-mono flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
          Verifying temporal and spatial alignment...
        </div>
      ) : validation ? (
        <div
          className={`p-2 rounded-lg border text-[11px] font-mono space-y-1 ${
            validation.compatible
              ? "bg-emerald-950/30 border-emerald-500/30 text-emerald-200"
              : "bg-rose-950/30 border-rose-500/30 text-rose-200"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="font-bold">
              {validation.compatible ? "✓ Compatible Pair" : "⚠ Incompatible"}
            </span>
            {validation.temporal_delta_days !== null &&
              validation.temporal_delta_days !== undefined && (
                <span className="text-[10px] text-slate-300">
                  Δ {validation.temporal_delta_days} days
                </span>
              )}
          </div>
          {validation.spatial_overlap_pct !== null &&
            validation.spatial_overlap_pct !== undefined && (
              <p className="text-[10px] text-slate-300">
                Spatial Overlap: {validation.spatial_overlap_pct}%
              </p>
            )}
          {validation.warnings.map((w, i) => (
            <p key={i} className="text-[10px] text-amber-300">
              • {w}
            </p>
          ))}
          {validation.errors.map((e, i) => (
            <p key={i} className="text-[10px] text-rose-300">
              ✕ {e}
            </p>
          ))}
        </div>
      ) : null}

      {/* Mode Selection */}
      <div className="flex items-center gap-1.5 pt-1">
        {(["split", "side_by_side", "opacity"] as const).map((m) => (
          <button
            key={m}
            disabled={!hasPair}
            onClick={() => comparisonStateManager.setMode(m)}
            className={`flex-1 py-1 px-2 rounded-md font-medium text-[11px] capitalize transition disabled:opacity-30 ${
              mode === m
                ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-bold shadow-md shadow-cyan-500/30"
                : "bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10"
            }`}
          >
            {m === "side_by_side" ? "Side by Side" : m}
          </button>
        ))}
      </div>

      {/* Split Slider Control */}
      {mode === "split" && (
        <div className="space-y-1 pt-1">
          <div className="flex justify-between text-[10px] font-mono text-slate-400">
            <span>Split Position</span>
            <span className="text-cyan-300">{Math.round(splitPosition)}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={splitPosition}
            onChange={(e) =>
              comparisonStateManager.setSplitPosition(Number(e.target.value))
            }
            className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-cyan-400"
          />
        </div>
      )}

      {/* Opacity Blend Control */}
      {mode === "opacity" && (
        <div className="space-y-1.5 pt-1">
          <div className="flex justify-between text-[10px] font-mono text-slate-400">
            <span>Blend B Opacity</span>
            <span className="text-amber-300">{Math.round(opacityB * 100)}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={opacityB}
            onChange={(e) =>
              comparisonStateManager.setOpacityB(Number(e.target.value))
            }
            className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-amber-400"
          />
        </div>
      )}
    </div>
  )
}
