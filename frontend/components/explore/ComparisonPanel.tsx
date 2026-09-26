"use client"

import React from "react"
import { ComparisonControls } from "./ComparisonControls"
import { ObservationCard } from "./ObservationCard"
import { useTemporalState, temporalStateManager } from "../../lib/explore/temporal-state"
import { comparisonStateManager } from "../../lib/explore/comparison-state"
import { Satellite, Search, Loader2, Sparkles } from "lucide-react"

export const ComparisonPanel: React.FC = () => {
  const { observations, loading } = useTemporalState()

  return (
    <div className="space-y-4">
      <ComparisonControls />

      {observations.length === 0 ? (
        <div className="p-3.5 rounded-xl bg-white/[0.04] border border-white/10 space-y-3">
          <div className="flex items-center gap-2 text-white font-semibold text-xs">
            <Satellite size={15} className="text-orange-400" />
            <span>Step 1: Load Satellite Acquisitions</span>
          </div>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            Observation comparison requires at least 2 satellite passes to compare before/after changes (e.g. floods, drought, urban growth).
          </p>
          <button
            onClick={() => temporalStateManager.search()}
            disabled={loading}
            className="w-full py-2.5 px-3 rounded-lg bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-400 hover:to-amber-400 text-black font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-orange-500/25 transition-all active:scale-[0.98] disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                <span>Querying satellite passes...</span>
              </>
            ) : (
              <>
                <Search size={14} />
                <span>Search Satellite Passes for Region</span>
              </>
            )}
          </button>
        </div>
      ) : (
        <div className="space-y-2.5">
          <div className="flex items-center justify-between px-1">
            <span className="text-[11px] uppercase tracking-wider font-mono text-slate-300 font-semibold block">
              Candidate Acquisitions ({observations.length})
            </span>
            {observations.length >= 2 && (
              <button
                onClick={() => {
                  comparisonStateManager.setObservationA(observations[1])
                  comparisonStateManager.setObservationB(observations[0])
                  comparisonStateManager.setMode("split")
                }}
                className="text-[10px] font-semibold text-orange-400 hover:text-orange-300 flex items-center gap-1 bg-orange-500/10 hover:bg-orange-500/20 px-2 py-0.5 rounded border border-orange-500/30 transition cursor-pointer"
                title="Quickly pair the latest 2 acquisitions in split view"
              >
                <Sparkles size={11} />
                <span>Auto-Compare Latest 2</span>
              </button>
            )}
          </div>
          <p className="text-[10px] text-slate-400 px-1">
            Click <strong className="text-orange-400">+ Set A</strong> on an earlier pass, and <strong className="text-amber-400">+ Set B</strong> on a newer pass.
          </p>
          <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-orange-500/20">
            {observations.map((obs) => (
              <ObservationCard key={obs.id} observation={obs} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
