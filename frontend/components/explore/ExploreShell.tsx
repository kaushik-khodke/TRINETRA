"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * ExploreShell Component — Main Workstation Layout Coordinator
 * Phase 1 Foundation
 */

import React, { useEffect, useState } from "react"
import "@/app/explore/explore.css"
import { ExploreHeader } from "./ExploreHeader"
import { ExploreSidebar } from "./ExploreSidebar"
import { ExploreViewport } from "./ExploreViewport"
import { ExploreStatusBar } from "./ExploreStatusBar"

export function ExploreShell() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="explore-root w-screen h-screen bg-[#030712] flex items-center justify-center text-slate-400 font-mono text-xs select-none">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-ping" />
          <span className="tracking-wider uppercase">INITIALIZING SHANETRA EXPLORE WORKSTATION...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="explore-root" id="shanetra-explore-root">
      {/* 1. Underlying 3D Globe / 2D Map Viewport spanning 100% of the screen */}
      <ExploreViewport />

      {/* 2. Frosted Glass Top Header */}
      <ExploreHeader />

      {/* 3. Frosted Glass Left Sidebar Drawer */}
      <ExploreSidebar />

      {/* 4. Frosted Glass Bottom Telemetry Status Bar */}
      <ExploreStatusBar />
    </div>
  )
}
