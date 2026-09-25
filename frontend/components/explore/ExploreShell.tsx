"use client"

/**
 * TRINETRA / Shanetra Explore Architecture
 * ExploreShell Component — Main Workstation Layout Coordinator
 * Phase 1 Foundation
 */

import React from "react"
import "@/app/explore/explore.css"
import { ExploreHeader } from "./ExploreHeader"
import { ExploreSidebar } from "./ExploreSidebar"
import { ExploreViewport } from "./ExploreViewport"
import { ExploreStatusBar } from "./ExploreStatusBar"

export function ExploreShell() {
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
