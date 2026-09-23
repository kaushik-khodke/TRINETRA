"use client"

import React from "react"
import { ComparisonControls } from "./ComparisonControls"
import { ObservationCard } from "./ObservationCard"
import { useTemporalState } from "../../lib/explore/temporal-state"

export const ComparisonPanel: React.FC = () => {
  const { observations } = useTemporalState()

  return (
    <div className="space-y-4">
      <ComparisonControls />

      {observations.length > 0 && (
        <div className="space-y-2">
          <span className="text-[11px] uppercase tracking-wider font-mono text-slate-400 block px-1">
            Candidate Acquisitions ({observations.length})
          </span>
          <div className="space-y-2 max-h-[340px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-orange-500/20">
            {observations.map((obs) => (
              <ObservationCard key={obs.id} observation={obs} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
