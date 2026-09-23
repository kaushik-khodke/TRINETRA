"use client"

import React, { useRef, useEffect } from "react"
import {
  useTemporalState,
  temporalStateManager,
} from "../../lib/explore/temporal-state"
import { TimelineItem } from "./TimelineItem"

export const Timeline: React.FC = () => {
  const { observations, selectedObservation, isPlaying, loading } =
    useTemporalState()
  const trackRef = useRef<HTMLDivElement>(null)

  // Scroll active item into view
  useEffect(() => {
    if (!selectedObservation || !trackRef.current) return
    const activeEl = trackRef.current.querySelector(
      `[data-obs-id="${selectedObservation.id}"]`
    )
    if (activeEl) {
      activeEl.scrollIntoView({
        behavior: "smooth",
        inline: "center",
        block: "nearest",
      })
    }
  }, [selectedObservation?.id])

  if (observations.length === 0 && !loading) {
    return null
  }

  return (
    <div className="bg-[#10141e]/95 backdrop-blur-md border border-orange-500/30 rounded-xl p-3 shadow-2xl">
      <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/10">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-xs text-orange-400 tracking-wider uppercase flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            Acquisition Timeline
          </span>
          <span className="text-[11px] font-mono text-slate-400">
            ({observations.length} acquisitions)
          </span>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center gap-1.5 bg-black/40 border border-white/10 rounded-lg p-1">
          {/* Step Prev */}
          <button
            onClick={() => temporalStateManager.stepPrev()}
            className="p-1 hover:bg-white/10 rounded text-slate-300 hover:text-white transition"
            title="Previous Acquisition"
          >
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="19 20 9 12 19 4 19 20" />
              <line x1="5" y1="19" x2="5" y2="5" />
            </svg>
          </button>

          {/* Play/Pause */}
          <button
            onClick={() =>
              isPlaying
                ? temporalStateManager.pause()
                : temporalStateManager.play()
            }
            className={`px-2 py-0.5 rounded text-xs font-semibold flex items-center gap-1 transition ${
              isPlaying
                ? "bg-amber-500 text-black shadow-lg shadow-amber-500/30"
                : "bg-orange-500 hover:bg-orange-400 text-black shadow-lg shadow-orange-500/30"
            }`}
            title={isPlaying ? "Pause Timeline Player" : "Play Sequence"}
          >
            {isPlaying ? (
              <>
                <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="4" width="4" height="16" />
                  <rect x="14" y="4" width="4" height="16" />
                </svg>
                <span>Pause</span>
              </>
            ) : (
              <>
                <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
                <span>Play</span>
              </>
            )}
          </button>

          {/* Step Next */}
          <button
            onClick={() => temporalStateManager.stepNext()}
            className="p-1 hover:bg-white/10 rounded text-slate-300 hover:text-white transition"
            title="Next Acquisition"
          >
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="5 4 15 12 5 20 5 4" />
              <line x1="19" y1="5" x2="19" y2="19" />
            </svg>
          </button>
        </div>
      </div>

      {/* Horizontal Carousel Track */}
      <div
        ref={trackRef}
        className="flex items-center gap-2 overflow-x-auto py-1 scrollbar-thin scrollbar-thumb-orange-500/30 scrollbar-track-transparent"
        style={{ scrollSnapType: "x mandatory" }}
      >
        {observations.map((obs) => (
          <div key={obs.id} data-obs-id={obs.id} style={{ scrollSnapAlign: "center" }}>
            <TimelineItem
              observation={obs}
              isSelected={selectedObservation?.id === obs.id}
              onClick={() => temporalStateManager.selectObservation(obs)}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
