"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * Query Suggestions Component
 * Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
 * Contextual suggestion chips based on active layers (purely deterministic templates).
 */

import React from "react"
import { Sparkles } from "lucide-react"
import { useGlobeState } from "@/lib/explore/globe-state"

interface QuerySuggestionsProps {
  onSelectSuggestion: (query: string) => void
}

export function QuerySuggestions({ onSelectSuggestion }: QuerySuggestionsProps) {
  const { selectedLayerIds } = useGlobeState()

  const hasSentinel2 = selectedLayerIds.includes("layer-local_sentinel2_nagpur_truecolor")
  const hasRadar = selectedLayerIds.includes("layer-local_sentinel1_mumbai_sar")
  const hasBorders = selectedLayerIds.includes("layer-borders")

  const getSuggestions = (): string[] => {
    const list: string[] = []

    if (!hasSentinel2) {
      list.push("Show Sentinel-2")
    } else {
      list.push("Make Sentinel-2 50% transparent")
    }

    if (!hasBorders) {
      list.push("Show boundaries")
    } else {
      list.push("Hide boundaries")
    }

    if (!hasRadar) {
      list.push("Show radar imagery")
    }

    list.push("Go to Nagpur")
    list.push("Zoom into Mumbai")
    list.push("Reset the globe")

    return list.slice(0, 4)
  }

  const suggestions = getSuggestions()

  return (
    <div className="query-suggestions-container" role="group" aria-label="Suggested natural-language commands">
      <div className="query-suggestions-label">
        <Sparkles size={11} className="suggestion-icon" />
        <span>TRY:</span>
      </div>
      <div className="query-suggestions-chips">
        {suggestions.map((s) => (
          <button
            key={s}
            type="button"
            className="suggestion-chip"
            onClick={() => onSelectSuggestion(s)}
            title={`Run command: "${s}"`}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
