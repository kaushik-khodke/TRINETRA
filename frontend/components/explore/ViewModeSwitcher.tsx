"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * View Mode Switcher Component (2D / 3D)
 * Phase 1 Foundation
 */

import React from "react"
import { Map, Globe } from "lucide-react"
import { globeCommandBus } from "@/lib/explore/globe-command-bus"
import { useGlobeState } from "@/lib/explore/globe-state"
import { ExploreViewMode } from "@/lib/explore/types"

export function ViewModeSwitcher() {
  const { viewMode } = useGlobeState()

  const handleSwitch = (mode: ExploreViewMode) => {
    if (mode !== viewMode) {
      globeCommandBus.dispatch({ type: "SET_VIEW_MODE", mode })
    }
  }

  return (
    <div className="view-mode-switcher" role="radiogroup" aria-label="Earth Visualization Dimension">
      <button
        type="button"
        role="radio"
        aria-checked={viewMode === "2d"}
        className={`view-mode-btn ${viewMode === "2d" ? "active" : ""}`}
        onClick={() => handleSwitch("2d")}
      >
        <Map size={13} />
        <span>2D Map</span>
      </button>

      <button
        type="button"
        role="radio"
        aria-checked={viewMode === "3d"}
        className={`view-mode-btn ${viewMode === "3d" ? "active" : ""}`}
        onClick={() => handleSwitch("3d")}
      >
        <Globe size={13} />
        <span>3D Globe</span>
      </button>
    </div>
  )
}
