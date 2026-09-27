"use client"

import React from "react"
import { useAOIState, aoiStateManager } from "../../lib/explore/aoi-state"

export const AOIToolbar: React.FC = () => {
  const { activeAOI, drawMode, isDrawing, validation, validationLoading, areaKm2 } =
    useAOIState()

  return (
    <div
      className="h-9 px-2.5 rounded-xl bg-[#0a0e18]/70 backdrop-blur-xl border border-white/10 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.1),0_8px_24px_rgba(0,0,0,0.45)] flex items-center gap-1.5 text-xs select-none transition-all"
      style={{ zIndex: 30 }}
    >
      <span className="font-semibold tracking-wider uppercase text-orange-400/90 mr-0.5 flex items-center gap-1.5 text-[11px]">
        <svg className="w-3.5 h-3.5 text-orange-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" strokeWidth="2" />
        </svg>
        AOI
      </span>

      {/* Rectangle Mode */}
      <button
        onClick={() =>
          aoiStateManager.setDrawMode(drawMode === "rectangle" ? null : "rectangle")
        }
        className={`h-6 px-2.5 rounded-lg transition-all font-medium flex items-center gap-1.5 text-[11px] ${
          drawMode === "rectangle"
            ? "bg-orange-500/20 text-orange-300 border border-orange-500/50 shadow-[0_0_12px_rgba(249,115,22,0.25)]"
            : "bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 hover:text-white border border-white/[0.06]"
        }`}
        title="Draw Bounding Box / Rectangle AOI"
      >
        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="18" height="18" rx="2" />
        </svg>
        <span>Box</span>
      </button>

      {/* Polygon Mode */}
      <button
        onClick={() =>
          aoiStateManager.setDrawMode(drawMode === "polygon" ? null : "polygon")
        }
        className={`h-6 px-2.5 rounded-lg transition-all font-medium flex items-center gap-1.5 text-[11px] ${
          drawMode === "polygon"
            ? "bg-orange-500/20 text-orange-300 border border-orange-500/50 shadow-[0_0_12px_rgba(249,115,22,0.25)]"
            : "bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 hover:text-white border border-white/[0.06]"
        }`}
        title="Draw Custom Polygon AOI"
      >
        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="12 2 2 22 22 22" />
        </svg>
        <span>Polygon</span>
      </button>

      {/* Clear AOI */}
      {activeAOI && (
        <button
          onClick={() => aoiStateManager.clearAOI()}
          className="h-6 px-2 rounded-lg bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/30 transition-all font-medium flex items-center gap-1 text-[11px]"
          title="Clear active Area of Interest"
        >
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
          Clear
        </button>
      )}

      {/* AOI Status Badge */}
      <div className="border-l border-white/10 pl-2 ml-0.5 flex items-center">
        {validationLoading ? (
          <span className="text-orange-300/70 animate-pulse flex items-center gap-1.5 text-[11px] font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-ping" />
            Validating...
          </span>
        ) : activeAOI ? (
          validation?.valid ? (
            <span className="text-emerald-400 font-mono text-[11px] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              {areaKm2 ? `${areaKm2.toLocaleString()} km²` : "Valid AOI"}
            </span>
          ) : (
            <span
              className="text-rose-400 font-mono text-[11px] flex items-center gap-1.5 cursor-help"
              title={validation?.errors?.join("; ") || "Invalid geometry"}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
              Invalid AOI
            </span>
          )
        ) : (
          <span className="text-slate-400/60 font-mono text-[10.5px]">No AOI</span>
        )}
      </div>
    </div>
  )
}
