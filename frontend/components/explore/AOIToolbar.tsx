"use client"

import React from "react"
import { useAOIState, aoiStateManager } from "../../lib/explore/aoi-state"

export const AOIToolbar: React.FC = () => {
  const { activeAOI, drawMode, isDrawing, validation, validationLoading, areaKm2 } =
    useAOIState()

  return (
    <div
      className="flex items-center gap-2 bg-[#121620]/90 backdrop-blur-md border border-cyan-500/30 rounded-lg px-3 py-1.5 shadow-xl text-xs"
      style={{ zIndex: 30 }}
    >
      <span className="font-semibold tracking-wider uppercase text-cyan-400/80 mr-1 flex items-center gap-1.5">
        <svg className="w-3.5 h-3.5 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" strokeWidth="2" />
        </svg>
        AOI
      </span>

      {/* Rectangle Mode */}
      <button
        onClick={() =>
          aoiStateManager.setDrawMode(drawMode === "rectangle" ? null : "rectangle")
        }
        className={`px-2.5 py-1 rounded transition font-medium flex items-center gap-1.5 ${
          drawMode === "rectangle"
            ? "bg-cyan-500 text-black shadow-lg shadow-cyan-500/40"
            : "bg-white/5 hover:bg-white/10 text-cyan-200 border border-white/10"
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
        className={`px-2.5 py-1 rounded transition font-medium flex items-center gap-1.5 ${
          drawMode === "polygon"
            ? "bg-cyan-500 text-black shadow-lg shadow-cyan-500/40"
            : "bg-white/5 hover:bg-white/10 text-cyan-200 border border-white/10"
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
          className="px-2 py-1 rounded bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/40 transition font-medium flex items-center gap-1"
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
      <div className="border-l border-white/10 pl-2 ml-1 flex items-center">
        {validationLoading ? (
          <span className="text-cyan-300/70 animate-pulse flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
            Validating...
          </span>
        ) : activeAOI ? (
          validation?.valid ? (
            <span className="text-emerald-400 font-mono flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              {areaKm2 ? `${areaKm2.toLocaleString()} km²` : "Valid AOI"}
            </span>
          ) : (
            <span
              className="text-rose-400 font-mono flex items-center gap-1 cursor-help"
              title={validation?.errors?.join("; ") || "Invalid geometry"}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
              Invalid AOI
            </span>
          )
        ) : (
          <span className="text-slate-400/60 font-mono">No AOI</span>
        )}
      </div>
    </div>
  )
}
