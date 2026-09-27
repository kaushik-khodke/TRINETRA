"use client"

import React, { useState, useRef, useCallback } from "react"
import {
  useComparisonState,
  comparisonStateManager,
} from "../../lib/explore/comparison-state"
import MapView from "./MapView"

export const SplitView: React.FC = () => {
  const { splitPosition, observationA, observationB } = useComparisonState()
  const containerRef = useRef<HTMLDivElement>(null)
  const isDraggingRef = useRef(false)

  const handleMouseDown = useCallback(() => {
    isDraggingRef.current = true
    document.body.style.cursor = "col-resize"
  }, [])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDraggingRef.current || !containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const pct = Math.max(5, Math.min(95, (x / rect.width) * 100))
    comparisonStateManager.setSplitPosition(pct)
  }, [])

  const handleMouseUp = useCallback(() => {
    isDraggingRef.current = false
    document.body.style.cursor = ""
  }, [])

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      className="relative w-full h-full overflow-hidden select-none"
    >
      {/* Floating Exit Comparison Capsule */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40">
        <button
          type="button"
          onClick={() => comparisonStateManager.setMode("none")}
          className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#0a0e17]/90 hover:bg-rose-950/90 text-white hover:text-rose-200 border border-white/20 hover:border-rose-500/50 backdrop-blur-xl shadow-2xl text-xs font-bold tracking-wider transition-all duration-200 cursor-pointer active:scale-95 group"
          title="Exit Dual Observation Split Comparison"
        >
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
          <span>EXIT COMPARISON</span>
          <span className="text-slate-400 group-hover:text-rose-300 font-mono text-xs ml-1">✕</span>
        </button>
      </div>

      {/* View A Container (Left) */}
      <div
        className="absolute inset-y-0 left-0 overflow-hidden border-r border-orange-500/50"
        style={{ width: `${splitPosition}%` }}
      >
        <div className="w-full h-full relative">
          <MapView />
          {/* Label Badge A */}
          <div className="absolute top-4 left-4 z-20 px-2.5 py-1 rounded bg-[#121620]/90 backdrop-blur-md border border-orange-400/40 text-[11px] font-mono text-orange-300 shadow-xl">
            <strong className="text-orange-400">Layer A:</strong>{" "}
            {observationA ? observationA.datetime.split("T")[0] : "Base"}
          </div>
        </div>
      </div>

      {/* View B Container (Right) */}
      <div
        className="absolute inset-y-0 right-0 overflow-hidden"
        style={{ width: `${100 - splitPosition}%` }}
      >
        <div className="w-full h-full relative">
          <MapView />
          {/* Label Badge B */}
          <div className="absolute top-4 right-4 z-20 px-2.5 py-1 rounded bg-[#121620]/90 backdrop-blur-md border border-amber-400/40 text-[11px] font-mono text-amber-300 shadow-xl">
            <strong className="text-amber-400">Layer B:</strong>{" "}
            {observationB ? observationB.datetime.split("T")[0] : "Compare"}
          </div>
        </div>
      </div>

      {/* Draggable Divider Handle */}
      <div
        onMouseDown={handleMouseDown}
        className="absolute inset-y-0 z-30 w-4 -ml-2 cursor-col-resize flex items-center justify-center group"
        style={{ left: `${splitPosition}%` }}
      >
        <div className="w-1 h-full bg-orange-400 group-hover:bg-orange-300 shadow-lg shadow-orange-500/50 transition-colors" />
        <div className="absolute w-8 h-8 rounded-full bg-[#121620] border-2 border-orange-400 shadow-xl flex items-center justify-center group-hover:scale-110 transition-transform">
          <svg className="w-4 h-4 text-orange-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          <svg className="w-4 h-4 text-orange-300 -ml-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>
      </div>
    </div>
  )
}
