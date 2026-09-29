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
  return (
    <div
      className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-cyan-950/40 border border-cyan-500/30 text-[11px] font-mono text-cyan-300 select-none shadow-sm"
      title="Cesium 3D Earth Globe Engine Active"
      role="status"
      aria-label="3D Earth Globe Active"
    >
      <Globe size={13} className="text-cyan-400" />
      <span>3D GLOBE</span>
    </div>
  )
}
